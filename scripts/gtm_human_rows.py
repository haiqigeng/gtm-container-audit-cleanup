#!/usr/bin/env python3
"""Translate reconciled GTM operations into compact human cleanup-plan rows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from gtm_privacy import redact_text

AREAS = {
    "Stack & architecture",
    "GTM hygiene",
    "Tracking plan / dataLayer",
    "Event firing logic",
    "Ecommerce payload quality",
    "Media platform tracking",
    "Consent & compliance",
    "Server-side tracking",
    "Data quality / reporting",
    "Web performance",
    "Governance / ownership",
}
PROBLEM_TYPES = {
    "Missing tracking",
    "Wrong trigger timing",
    "Over-firing",
    "Under-firing",
    "Duplicate firing",
    "Wrong product, market, or page scope",
    "Incomplete payload",
    "Wrong data format",
    "Wrong value or formula logic",
    "Obsolete or legacy setup",
    "Unclear business purpose",
    "Consent mismatch",
    "Server-side routing unclear",
    "Performance overhead",
    "Naming or ownership unclear",
    "Generic hygiene batch",
}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def build_rows(payload: dict[str, Any]) -> tuple[list[dict[str, str]], list[str]]:
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for index, operation in enumerate(as_list(payload.get("operations")), start=1):
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
        rows.append(
            {
                "ID": str(operation.get("operation_id") or f"OP-{index:04d}"),
                "Level": "Single",
                "Area / problem type": f"{area} / {problem_type}",
                "Affected object(s)": redact_text(operation.get("affected_objects")),
                "Problem / evidence": f"{problem} Impact: {impact}".strip(),
                "Action / priority / QA": (
                    f"{action} Priority: {operation.get('priority')}. "
                    f"Readiness: {operation.get('execution_readiness')}. QA: {qa}"
                    + (f" Blocker: {blocker}" if blocker else "")
                ).strip(),
            }
        )
    return rows, errors


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
