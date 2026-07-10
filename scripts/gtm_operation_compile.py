#!/usr/bin/env python3
"""Compile validated semantic review rows into execution-ready operation packets."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from gtm_semantic_review import (
    VALID_READINESS,
    VALID_RESOLUTIONS,
    VALID_RISK_CLASSES,
    as_list,
    validate_review,
)

VALID_AGGRESSIVENESS = {"Conservative", "Standard", "Deep", "Transformational"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_ids(row: dict[str, Any]) -> set[str]:
    value = row.get("source_finding_ids")
    if isinstance(value, list):
        return {str(item).strip() for item in value if str(item).strip()}
    return {part.strip() for part in str(value or "").replace(";", ",").split(",") if part.strip()}


def baseline_findings(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    return [
        row
        for row in as_list(load_json(path).get("findings"))
        if row.get("finding_type") != "zero_findings"
    ]


def technical_rows(path: Path | None) -> list[dict[str, Any]]:
    return as_list(load_json(path).get("rows")) if path else []


def technical_key(row: dict[str, Any]) -> str:
    return f"{row.get('layer') or ''}:{row.get('object_id') or ''}"


def group_consistent(rows: list[dict[str, Any]], field: str) -> bool:
    values = {str(row.get(field) or "").strip() for row in rows}
    values.discard("")
    return len(values) <= 1


def compile_operations(
    review: dict[str, Any],
    baseline: list[dict[str, Any]],
    technical: list[dict[str, Any]],
    route: str,
    aggressiveness: str,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not route.strip():
        errors.append("execution route must not be blank")
    if aggressiveness not in VALID_AGGRESSIVENESS:
        errors.append("invalid cleanup aggressiveness")
    review_rows = as_list(review.get("rows"))
    baseline_ids = {str(row.get("finding_id") or "") for row in baseline}
    linked_ids = set().union(*(source_ids(row) for row in review_rows)) if review_rows else set()
    missing_baseline = sorted(baseline_ids - linked_ids)
    if missing_baseline:
        errors.append(
            "semantic review does not resolve deterministic finding IDs: "
            + ", ".join(missing_baseline)
        )

    technical_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in technical:
        technical_by_key[technical_key(row)].append(row)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in review_rows:
        key = str(row.get("object_key") or "")
        related_technical = technical_by_key.get(key, [])
        nonkeep_technical = [
            item
            for item in related_technical
            if str(item.get("technical_action_candidate") or "") != "keep"
        ]
        if nonkeep_technical and row.get("semantic_status") == "Keep":
            errors.append(
                f"{key}: technical cleanup exists but semantic review says Keep without an operation"
            )
        row["_technical_rows"] = related_technical

        needs_packet = row.get("semantic_status") not in {"Keep", "Not applicable"}
        needs_packet = needs_packet or bool(source_ids(row)) or bool(nonkeep_technical)
        if not needs_packet:
            continue
        group_key = str(row.get("operation_group") or key)
        grouped[group_key].append(row)

    packets: list[dict[str, Any]] = []
    consistency_fields = (
        "area",
        "problem_type",
        "problem",
        "why_it_matters",
        "expected_clean_state",
        "exact_proposed_action",
        "preconditions",
        "qa_steps",
        "rollback",
        "blocker",
        "priority",
        "resolution_status",
        "execution_readiness",
        "risk_class",
    )
    for number, (group_key, rows) in enumerate(sorted(grouped.items()), start=1):
        for field in consistency_fields:
            if not group_consistent(rows, field):
                errors.append(f"operation group {group_key!r} has conflicting {field} values")
        first = rows[0]
        resolution = str(first.get("resolution_status") or "")
        readiness = str(first.get("execution_readiness") or "")
        if resolution not in VALID_RESOLUTIONS:
            errors.append(f"operation group {group_key!r} has invalid resolution_status")
        if readiness not in VALID_READINESS:
            errors.append(f"operation group {group_key!r} has invalid execution_readiness")
        if str(first.get("risk_class") or "") not in VALID_RISK_CLASSES:
            errors.append(f"operation group {group_key!r} has invalid risk_class")

        technical_group = [item for row in rows for item in row.get("_technical_rows", [])]
        finding_ids = set().union(*(source_ids(row) for row in rows))
        finding_ids.update(
            str(item.get("technical_finding_id"))
            for item in technical_group
            if item.get("technical_finding_id")
        )
        source_lenses = {"semantic"}
        if finding_ids.intersection(baseline_ids):
            source_lenses.add("deterministic")
        if technical_group:
            source_lenses.add("technical")

        packet = {
            "operation_id": f"OP-{number:04d}",
            "operation_group": group_key,
            "area": first.get("area"),
            "problem_type": first.get("problem_type"),
            "affected_objects": "; ".join(
                f"{row.get('layer')} {row.get('object_id')} - {row.get('object_name')}"
                for row in rows
            ),
            "object_identity": "; ".join(
                f"{row.get('object_key')}|{row.get('config_hash')}" for row in rows
            ),
            "source_lenses": ", ".join(sorted(source_lenses)),
            "current_behavior": " ".join(str(row.get("literal_behavior") or "") for row in rows),
            "problem": first.get("problem"),
            "why_it_matters": first.get("why_it_matters"),
            "expected_clean_state": first.get("expected_clean_state"),
            "exact_proposed_action": first.get("exact_proposed_action"),
            "preconditions": first.get("preconditions"),
            "qa_steps": first.get("qa_steps"),
            "rollback": first.get("rollback"),
            "confidence": first.get("confidence"),
            "blocker": first.get("blocker"),
            "priority": first.get("priority"),
            "resolution_status": resolution,
            "source_finding_ids": sorted(finding_ids),
            "route": route,
            "aggressiveness": aggressiveness,
            "execution_readiness": readiness,
            "risk_class": first.get("risk_class"),
            "technical_handoff_packet": " ".join(
                str(item.get("technical_handoff_packet") or "") for item in technical_group
            ),
        }
        packets.append(packet)

    return {
        "kind": "gtm_reconciled_operations",
        "schema_version": 1,
        "source_file": review.get("source_file"),
        "source_sha256": review.get("source_sha256"),
        "route": route,
        "aggressiveness": aggressiveness,
        "operations": packets,
    }, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("semantic_review", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--technical", type=Path)
    parser.add_argument("--route", default="Manual same-container merge")
    parser.add_argument(
        "--aggressiveness", default="Standard", choices=sorted(VALID_AGGRESSIVENESS)
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    review_errors, review_warnings = validate_review(args.export, args.semantic_review)
    for warning in review_warnings:
        print(f"WARNING: {warning}")
    if review_errors:
        for error in review_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    review = load_json(args.semantic_review)
    payload, errors = compile_operations(
        review,
        baseline_findings(args.baseline),
        technical_rows(args.technical),
        args.route,
        args.aggressiveness,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(args.output), "operations": len(payload["operations"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
