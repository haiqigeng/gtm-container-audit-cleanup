#!/usr/bin/env python3
"""Diff two GTM exports and emit structured cleanup operations."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

from gtm_lib import ID_KEYS, apply_patch, comparable, load_container_version, object_id, sort_ids
from gtm_privacy import redact_text

LAYER_LABELS = {
    "tag": "Tag",
    "trigger": "Trigger",
    "variable": "Variable",
    "folder": "Folder",
    "customTemplate": "Template",
    "builtInVariable": "Built-in variable",
    "client": "Server client",
    "transformation": "Server transformation",
}

CSV_COLUMNS = [
    "Change ID",
    "Area / object",
    "Change made",
    "Before",
    "After",
    "Reason / QA / status",
]

DIFF_IGNORED_FIELDS = {"path", "fingerprint", "accountId", "containerId"}


def action_for(before: dict[str, Any] | None, after: dict[str, Any] | None) -> str:
    if before is None:
        return "Added"
    if after is None:
        return "Removed"
    renamed = before.get("name") != after.get("name")
    modified = comparable(before) != comparable(after)
    if renamed and modified:
        return "Renamed + Modified"
    if renamed:
        return "Renamed"
    if modified:
        return "Modified"
    return "No-op / Documented exception"


def compact_value(value: Any, limit: int = 500) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value if value is not None else "")
    text = redact_text(text)
    return text if len(text) <= limit else text[: limit - 1] + "..."


def field_diffs(before: Any, after: Any, path: str = "$") -> list[dict[str, Any]]:
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict):
        rows = []
        for key in sorted(set(before) | set(after)):
            if key in DIFF_IGNORED_FIELDS:
                continue
            rows.extend(field_diffs(before.get(key), after.get(key), f"{path}.{key}"))
        return rows
    if isinstance(before, list) and isinstance(after, list):
        rows = []
        for index in range(max(len(before), len(after))):
            left = before[index] if index < len(before) else None
            right = after[index] if index < len(after) else None
            rows.extend(field_diffs(left, right, f"{path}[{index}]"))
        return rows
    return [{"field_path": path, "before": before, "after": after}]


def operation_lookup(payload: dict[str, Any] | None) -> dict[tuple[str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    if not payload:
        return lookup
    for operation in payload.get("operations", []) or []:
        identity = str(operation.get("object_identity") or "")
        for match in re.finditer(
            r"(?:^|;\s*)(tag|trigger|variable|folder|customTemplate|builtInVariable|client|transformation):([^|;]+)",
            identity,
        ):
            lookup[(match.group(1), match.group(2))] = operation
    return lookup


def category_for_path(layer: str, field_path: str, action: str) -> str:
    lowered = field_path.lower()
    if action == "Deleted":
        return "Deletion"
    if action == "Created":
        return "Creation"
    if lowered.endswith(".name"):
        return "Naming"
    if "firingtriggerid" in lowered or "blockingtriggerid" in lowered or "triggerids" in lowered:
        return "Trigger routing"
    if "setuptag" in lowered or "teardowntag" in lowered:
        return "Dependency remap"
    if "parentfolderid" in lowered:
        return "Folder move"
    if "consent" in lowered or "storage" in lowered:
        return "Consent configuration"
    if "parameter" in lowered:
        return "Configuration field"
    if layer == "builtInVariable":
        return "Built-in variable set"
    return "Configuration"


def default_category(layer: str, action: str) -> str:
    if action == "Removed":
        return "Deletion"
    if action == "Added":
        return "Creation"
    if action == "Renamed":
        return "Naming"
    if "Renamed" in action:
        return "Naming + configuration"
    if layer == "builtInVariable":
        return "Built-in variable set"
    return "Configuration"


def operations(
    before_cv: dict[str, Any],
    after_cv: dict[str, Any],
    route: str,
    aggressiveness: str,
    approved_operations: dict[str, Any] | None = None,
    execution_mode: str = "planned",
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    change_number = 1
    approved_lookup = operation_lookup(approved_operations)
    for layer, key in ID_KEYS.items():
        before_by_id = {
            object_id(obj, key): obj
            for obj in before_cv.get(layer, []) or []
            if object_id(obj, key)
        }
        after_by_id = {
            object_id(obj, key): obj for obj in after_cv.get(layer, []) or [] if object_id(obj, key)
        }
        for oid in sort_ids(set(before_by_id) | set(after_by_id)):
            before = before_by_id.get(oid)
            after = after_by_id.get(oid)
            object_action = action_for(before, after)
            if object_action == "No-op / Documented exception":
                continue
            before_name = (before or {}).get("name", "")
            after_name = (after or {}).get("name", "")
            layer_label = LAYER_LABELS[layer]
            approved = approved_lookup.get((layer, oid))
            if before is None or after is None:
                changes = [{"field_path": "$", "before": before, "after": after}]
            else:
                changes = field_diffs(comparable(before), comparable(after))
            for change in changes:
                field_path = change["field_path"]
                action = (
                    "Created"
                    if before is None
                    else "Deleted"
                    if after is None
                    else "Renamed"
                    if field_path.endswith(".name")
                    else "Updated"
                )
                linked_operation_id = str((approved or {}).get("operation_id") or "")
                reason = str((approved or {}).get("why_it_matters") or "")
                if not reason:
                    reason = (
                        "Unlinked export difference; reconcile this field with an approved cleanup operation "
                        "before treating it as executed."
                    )
                status = "Applied" if execution_mode == "executed" and approved else "Proposed"
                if execution_mode == "executed" and not approved:
                    status = "Blocked: missing approved operation link"
                row = {
                    "change_id": f"GTM-OP-{change_number:03d}",
                    "aggressiveness": aggressiveness,
                    "route": route,
                    "layer": layer_label,
                    "action": action,
                    "object_id": oid,
                    "before_name": before_name,
                    "after_name": after_name,
                    "field_path": field_path,
                    "before_value": compact_value(change["before"]),
                    "after_value": compact_value(change["after"]),
                    "operation_id": linked_operation_id,
                    "reason": reason,
                    "functional_impact": str((approved or {}).get("why_it_matters") or ""),
                    "qa_method": str(
                        (approved or {}).get("qa_steps")
                        or "Compare the field in GTM Preview/readback and verify expected tag behavior."
                    ),
                    "rollback": "Restore from original export or reverse this operation.",
                    "status": status,
                    "blocker": str((approved or {}).get("blocker") or ""),
                    "change_category": category_for_path(layer, field_path, action),
                    "qa_status": "Not started"
                    if execution_mode == "planned"
                    else "Requires verification",
                }
                rows.append(row)
                change_number += 1
    return rows


def csv_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "Change ID": row["change_id"],
        "Area / object": f"{row['change_category']} / {row['layer']} {row['object_id']}",
        "Change made": f"{row['action']} {row['field_path']}",
        "Before": row["before_value"],
        "After": row["after_value"],
        "Reason / QA / status": (
            f"{row['reason']} Operation: {row['operation_id'] or 'unlinked'}. "
            f"QA: {row['qa_method']} Status: {row['status']}"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path, help="Original GTM export JSON")
    parser.add_argument("after", type=Path, help="Cleanup draft or post-change export JSON")
    parser.add_argument(
        "--patch",
        action="store_true",
        help="Treat the after file as a same-container patch applied to the before export",
    )
    parser.add_argument("--route", default="Direct GTM/MCP/API", help="Execution route label")
    parser.add_argument("--aggressiveness", default="Standard", help="Cleanup aggressiveness")
    parser.add_argument("--operations", type=Path, help="Approved reconciled_operations.json")
    parser.add_argument("--execution-mode", choices=("planned", "executed"), default="planned")
    parser.add_argument("--json", type=Path, help="Optional JSON output file")
    parser.add_argument("--csv", type=Path, help="Optional change-log-shaped CSV output")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    before_cv = load_container_version(args.before)
    after_cv = load_container_version(args.after)
    if args.patch:
        after_cv = apply_patch(before_cv, after_cv)
    approved = json.loads(args.operations.read_text(encoding="utf-8")) if args.operations else None
    if args.execution_mode == "executed" and not approved:
        raise SystemExit("--operations is required for an executed change log")
    rows = operations(
        before_cv,
        after_cv,
        args.route,
        args.aggressiveness,
        approved,
        args.execution_mode,
    )
    payload = {
        "kind": "gtm_field_level_change_log",
        "execution_mode": args.execution_mode,
        "changeCount": len(rows),
        "changes": rows,
        "operationCount": len(rows),
        "operations": rows,
    }

    if args.csv:
        with args.csv.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for row in rows:
                writer.writerow(csv_row(row))

    rendered = json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
