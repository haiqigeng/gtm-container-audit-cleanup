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
LEVEL_ORDER = {
    "Proposed": 0,
    "Owner decision": 1,
    "Evidence limit": 2,
    "Deferred": 3,
}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def build_rows(payload: dict[str, Any]) -> tuple[list[dict[str, str]], list[str]]:
    staged_rows: list[tuple[tuple[int, int, str], dict[str, str]]] = []
    errors: list[str] = []

    def stage_row(row: dict[str, str], level: str, priority: str, identifier: str) -> None:
        staged_rows.append(
            (
                (
                    LEVEL_ORDER.get(level, 99),
                    PRIORITY_ORDER.get(priority, 4),
                    identifier,
                ),
                row,
            )
        )

    def append_operation(operation: dict[str, Any], index: int, level: str) -> None:
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
        stage_row(
            {
                "ID": operation_id,
                "Level": level,
                "Area / problem type": f"{area} / {problem_type}",
                "Affected object(s)": redact_text(operation.get("affected_objects")),
                "Problem / evidence": (
                    f"Root problem: {problem} Business impact: {impact}"
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
                    + (f" Blocker: {blocker}" if blocker else "")
                ).strip(),
            },
            level,
            str(operation.get("priority") or ""),
            operation_id,
        )

    active = as_list(payload.get("operations"))
    deferred = as_list(payload.get("deferred_operations"))
    for index, operation in enumerate(active, start=1):
        append_operation(operation, index, "Proposed")
    for index, operation in enumerate(deferred, start=1):
        append_operation(operation, index, "Deferred")

    unresolved = [
        decision
        for decision in as_list(payload.get("decision_ledger"))
        if decision.get("disposition")
        in {"owner_decision_needed", "container_evidence_limit"}
    ]
    for decision in unresolved:
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
        evidence_limit = decision.get("disposition") == "container_evidence_limit"
        action = (
            "Record the container evidence limit and keep the object unchanged."
            if evidence_limit
            else redact_text(decision.get("owner_question"))
        )
        decision_id = str(decision.get("decision_id") or "DECISION")
        level = "Evidence limit" if evidence_limit else "Owner decision"
        stage_row(
            {
                "ID": decision_id,
                "Level": level,
                "Area / problem type": f"{area} / {problem_type}",
                "Affected object(s)": redact_text(decision.get("affected_objects")),
                "Problem / evidence": (
                    "Evidence boundary: " if evidence_limit else "Decision required: "
                )
                + redact_text(decision.get("summary")),
                "Action / priority / QA": (
                    f"Required next action: {action} "
                    + (
                        "Readiness: blocked until the owner answers this question."
                        if not evidence_limit
                        else "Readiness: retain unchanged unless new evidence is supplied."
                    )
                ),
            },
            level,
            "",
            decision_id,
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
