#!/usr/bin/env python3
"""Translate reconciled GTM operations into compact human cleanup-plan rows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from gtm_privacy import redact_text
from gtm_taxonomy import AREAS, PROBLEM_TYPES

PRIORITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
STATUS_ORDER = {
    "Proposed action": 0,
    "Conditional action": 1,
    "Owner confirmation": 2,
    "Evidence boundary": 3,
}
BATCHABLE_PROBLEM_TYPES = {
    "Unused object",
    "Exact duplicate",
    "Naming inconsistency",
    "Folder organization",
    "Generic hygiene batch",
}
MAX_VISIBLE_BATCH_OPERATIONS = 8


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def build_rows(payload: dict[str, Any]) -> tuple[list[dict[str, str]], list[str]]:
    staged_rows: list[tuple[tuple[int, int, str], dict[str, str]]] = []
    operation_entries: list[dict[str, Any]] = []
    errors: list[str] = []

    def stage_row(row: dict[str, str], status: str, priority: str, identifier: str) -> None:
        staged_rows.append(
            (
                (
                    STATUS_ORDER.get(status, 99),
                    PRIORITY_ORDER.get(priority, 4),
                    identifier,
                ),
                row,
            )
        )

    def append_operation(operation: dict[str, Any], index: int) -> None:
        area = str(operation.get("area") or "")
        problem_type = str(operation.get("problem_type") or "")
        if area not in AREAS:
            errors.append(f"operation {operation.get('operation_id')}: unsupported area {area!r}")
        if problem_type not in PROBLEM_TYPES:
            errors.append(
                f"operation {operation.get('operation_id')}: unsupported problem type {problem_type!r}"
            )
        problem = redact_text(operation.get("problem"))
        impact = redact_text(operation.get("why_it_matters"))
        action = redact_text(operation.get("exact_proposed_action"))
        qa = redact_text(operation.get("qa_steps"))
        blocker = redact_text(operation.get("blocker"))
        operation_id = str(operation.get("operation_id") or f"OP-{index:04d}")
        execution_order = operation.get("execution_order")
        status = (
            "Conditional action"
            if operation.get("approval_status") == "pending_owner_decision"
            else "Proposed action"
        )
        family_ids = ", ".join(
            str(value)
            for value in as_list(operation.get("affected_measurement_family_ids"))
            if str(value)
        )
        retained_behavior = redact_text(operation.get("retained_behavior"))
        row = {
                "ID": operation_id,
                "Status": status,
                "Area / problem type": f"{area} / {problem_type}",
                "Affected object(s)": redact_text(operation.get("affected_objects")),
                "Problem / evidence": (
                    f"Root problem: {problem} Business impact: {impact}"
                    + (
                        f" Preserved business behavior: {retained_behavior}"
                        if retained_behavior
                        else ""
                    )
                ).strip(),
                "Action / priority / QA": (
                    f"Target state / exact action: {action} "
                    f"Priority: {operation.get('priority')}. "
                    + (
                        f"Execution order: {execution_order}. "
                        if execution_order is not None
                        else ""
                    )
                    + f"Readiness: {operation.get('execution_readiness')}. QA: {qa}"
                    + (f" Measurement families: {family_ids}." if family_ids else "")
                    + (f" Blocker: {blocker}" if blocker else "")
                ).strip(),
            }
        operation_entries.append(
            {
                "row": row,
                "status": status,
                "priority": str(operation.get("priority") or ""),
                "identifier": operation_id,
                "area": area,
                "problem_type": problem_type,
            }
        )

    active = as_list(payload.get("operations"))
    for index, operation in enumerate(active, start=1):
        append_operation(operation, index)

    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for entry in operation_entries:
        if entry["problem_type"] not in BATCHABLE_PROBLEM_TYPES:
            stage_row(
                entry["row"],
                entry["status"],
                entry["priority"],
                entry["identifier"],
            )
            continue
        key = (
            entry["status"],
            entry["priority"],
            entry["area"],
            entry["problem_type"],
        )
        grouped.setdefault(key, []).append(entry)

    batch_number = 0
    for (status, priority, area, problem_type), entries in sorted(
        grouped.items(), key=lambda item: item[0]
    ):
        entries.sort(key=lambda entry: entry["identifier"])
        for start in range(0, len(entries), MAX_VISIBLE_BATCH_OPERATIONS):
            chunk = entries[start : start + MAX_VISIBLE_BATCH_OPERATIONS]
            if len(chunk) == 1:
                entry = chunk[0]
                stage_row(
                    entry["row"],
                    entry["status"],
                    entry["priority"],
                    entry["identifier"],
                )
                continue
            batch_number += 1
            operation_ids = [entry["identifier"] for entry in chunk]
            batch_id = (
                f"BATCH-{batch_number:03d} [" + ", ".join(operation_ids) + "]"
            )
            stage_row(
                {
                    "ID": batch_id,
                    "Status": status,
                    "Area / problem type": f"{area} / {problem_type}",
                    "Affected object(s)": " ".join(
                        f"[{entry['identifier']}] {entry['row']['Affected object(s)']}"
                        for entry in chunk
                    ),
                    "Problem / evidence": (
                        f"Homogeneous batch of {len(chunk)} {problem_type.lower()} "
                        "operations. "
                        + " ".join(
                            f"[{entry['identifier']}] "
                            f"{entry['row']['Problem / evidence']}"
                            for entry in chunk
                        )
                    ),
                    "Action / priority / QA": (
                        "Approve, reject, or amend each atomic operation ID independently. "
                        + " ".join(
                            f"[{entry['identifier']}] "
                            f"{entry['row']['Action / priority / QA']}"
                            for entry in chunk
                        )
                    ),
                },
                status,
                priority,
                chunk[0]["identifier"],
            )

    unresolved = [
        decision
        for decision in as_list(payload.get("decision_ledger"))
        if decision.get("disposition")
        in {"owner_decision_needed", "container_evidence_limit"}
    ]
    owner_decisions = [
        decision
        for decision in unresolved
        if decision.get("disposition") == "owner_decision_needed"
    ]
    evidence_limits = [
        decision
        for decision in unresolved
        if decision.get("disposition") == "container_evidence_limit"
    ]
    for decision in owner_decisions:
        area = str(decision.get("area") or "Governance / ownership")
        problem_type = str(decision.get("problem_type") or "Unclear business purpose")
        if area not in AREAS:
            errors.append(
                f"decision {decision.get('decision_id')}: unsupported area {area!r}"
            )
        if problem_type not in PROBLEM_TYPES:
            errors.append(
                f"decision {decision.get('decision_id')}: unsupported problem type "
                f"{problem_type!r}"
            )
        recommendation = redact_text(decision.get("recommended_action"))
        question = redact_text(decision.get("owner_question"))
        decision_id = str(decision.get("decision_id") or "DECISION")
        status = "Owner confirmation"
        stage_row(
            {
                "ID": decision_id,
                "Status": status,
                "Area / problem type": f"{area} / {problem_type}",
                "Affected object(s)": redact_text(decision.get("affected_objects")),
                "Problem / evidence": "Decision required: "
                + redact_text(decision.get("summary")),
                "Action / priority / QA": (
                    f"Recommended action: {recommendation} "
                    f"Question: {question} "
                    "Readiness: blocked only for changes to the listed object(s) until "
                    "the owner answers this question."
                ),
            },
            status,
            "",
            decision_id,
        )
    if evidence_limits:
        evidence_count = len(evidence_limits)
        status = "Evidence boundary"
        stage_row(
            {
                "ID": "SCOPE-001",
                "Status": status,
                "Area / problem type": (
                    "Governance / ownership / Container-only evidence boundary"
                ),
                "Affected object(s)": (
                    f"{evidence_count} retained review decision(s); complete object list "
                    "in hidden Configuration and Architecture Review tabs"
                ),
                "Problem / evidence": (
                    f"Scope boundary: {evidence_count} reviewed decisions depend on live "
                    "dataLayer values, page/CMP state, vendor responses, or downstream runtime "
                    "behavior that a GTM container export cannot prove. These are not "
                    "source-visible cleanup defects and do not block unrelated cleanup. "
                    "Every per-object boundary remains lossless in the hidden reviews and "
                    "machine-readable audit package."
                ),
                "Action / priority / QA": (
                    "Scope treatment: retain the affected objects unchanged in this "
                    "container-only plan. Commission GTM Preview, network/dataLayer/CMP, or "
                    "vendor-contract verification only when runtime certification is needed; "
                    "create an exact corrective operation if that evidence proves a defect. "
                    "Readiness: nonblocking for unrelated proposed operations."
                ),
            },
            status,
            "",
            "SCOPE-001",
        )
    return [
        row for _sort_key, row in sorted(staged_rows, key=lambda item: item[0])
    ], errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operations", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.operations.read_text(encoding="utf-8"))
    rows, errors = build_rows(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    output = {
        "kind": "gtm_human_cleanup_rows",
        "source_file": payload.get("source_file"),
        "source_sha256": payload.get("source_sha256"),
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(args.output), "rows": len(rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
