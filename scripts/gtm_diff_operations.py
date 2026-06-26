#!/usr/bin/env python3
"""Diff two GTM exports and emit structured cleanup operations."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from gtm_lib import ID_KEYS, apply_patch, comparable, load_container_version, object_id, sort_ids

LAYER_LABELS = {
    "tag": "Tag",
    "trigger": "Trigger",
    "variable": "Variable",
    "folder": "Folder",
    "customTemplate": "Template",
    "builtInVariable": "Built-in variable",
}

CSV_COLUMNS = [
    "Change ID",
    "Layer",
    "Action",
    "Status",
    "Before name",
    "After name",
    "Object ID(s)",
    "Change category",
    "Plain-language summary",
    "Reason / decision",
    "Functional impact",
    "Consent / privacy impact",
    "QA priority",
    "QA status",
    "Owner",
    "Evidence / notes",
]


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


def operations(before_cv: dict[str, Any], after_cv: dict[str, Any], route: str, aggressiveness: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    change_number = 1
    for layer, key in ID_KEYS.items():
        before_by_id = {
            object_id(obj, key): obj
            for obj in before_cv.get(layer, []) or []
            if object_id(obj, key)
        }
        after_by_id = {
            object_id(obj, key): obj
            for obj in after_cv.get(layer, []) or []
            if object_id(obj, key)
        }
        for oid in sort_ids(set(before_by_id) | set(after_by_id)):
            before = before_by_id.get(oid)
            after = after_by_id.get(oid)
            action = action_for(before, after)
            if action == "No-op / Documented exception":
                continue
            before_name = (before or {}).get("name", "")
            after_name = (after or {}).get("name", "")
            layer_label = LAYER_LABELS[layer]
            rows.append(
                {
                    "change_id": f"GTM-OP-{change_number:03d}",
                    "aggressiveness": aggressiveness,
                    "route": route,
                    "layer": layer_label,
                    "action": action,
                    "object_id": oid,
                    "before_name": before_name,
                    "after_name": after_name,
                    "semantic_role": "",
                    "reason": "Generated from export diff; analyst must attach finding or decision.",
                    "official_doc_basis": "",
                    "dependencies": "",
                    "risk": "",
                    "qa_method": "Export diff and GTM Preview/debug where behavior changes.",
                    "rollback": "Restore from original export or reverse this operation.",
                    "status": "Proposed",
                    "blocker": "",
                    "change_category": default_category(layer, action),
                    "functional_impact": "",
                    "consent_privacy_impact": "",
                    "qa_priority": "P2 Planned cleanup",
                    "qa_status": "Not started",
                    "owner": "",
                    "evidence_notes": "",
                }
            )
            change_number += 1
    return rows


def csv_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "Change ID": row["change_id"],
        "Layer": row["layer"],
        "Action": row["action"],
        "Status": row["status"],
        "Before name": row["before_name"],
        "After name": row["after_name"],
        "Object ID(s)": row["object_id"],
        "Change category": row["change_category"],
        "Plain-language summary": f"{row['action']} {row['layer']} {row['object_id']}",
        "Reason / decision": row["reason"],
        "Functional impact": row["functional_impact"],
        "Consent / privacy impact": row["consent_privacy_impact"],
        "QA priority": row["qa_priority"],
        "QA status": row["qa_status"],
        "Owner": row["owner"],
        "Evidence / notes": row["evidence_notes"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path, help="Original GTM export JSON")
    parser.add_argument("after", type=Path, help="Cleanup draft or post-change export JSON")
    parser.add_argument("--patch", action="store_true", help="Treat the after file as a same-container patch applied to the before export")
    parser.add_argument("--route", default="Direct GTM/MCP/API", help="Execution route label")
    parser.add_argument("--aggressiveness", default="Standard", help="Cleanup aggressiveness")
    parser.add_argument("--csv", type=Path, help="Optional change-log-shaped CSV output")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    before_cv = load_container_version(args.before)
    after_cv = load_container_version(args.after)
    if args.patch:
        after_cv = apply_patch(before_cv, after_cv)
    rows = operations(before_cv, after_cv, args.route, args.aggressiveness)
    payload = {"operationCount": len(rows), "operations": rows}

    if args.csv:
        with args.csv.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for row in rows:
                writer.writerow(csv_row(row))

    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
