#!/usr/bin/env python3
"""Validate the compact GTM cleanup-plan workbook structure and content."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from gtm_workbook import load_xlsx_workbook
from gtm_workbook_build import CANONICAL_SHEETS

PLACEHOLDER_PATTERNS = (
    re.compile(r"\b(?:tbd|to" r"do|lorem ipsum)\b", re.I),
    re.compile(r"\b(?:configuration|code) (?:reviewed|inspected)\b", re.I),
    re.compile(r"\b(?:review|check) (?:later|in gtm)\b", re.I),
)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def duplicate_columns(sheet_name: str, rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    headers = list(rows[0])
    columns = {
        header: tuple(str(row.get(header, "") or "").strip() for row in rows) for header in headers
    }
    errors = []
    for index, left in enumerate(headers):
        if not any(columns[left]):
            continue
        for right in headers[index + 1 :]:
            if columns[left] == columns[right]:
                errors.append(f"{sheet_name}: duplicate column content in {left!r} and {right!r}")
    return errors


def placeholder_errors(sheet_name: str, rows: list[dict[str, Any]]) -> list[str]:
    errors = []
    for row_number, row in enumerate(rows, start=2):
        for header, value in row.items():
            text = str(value or "")
            if any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS):
                errors.append(
                    f"{sheet_name}!{header} row {row_number}: generic or deferred wording"
                )
    return errors


def workbook_structure_errors(
    workbook_rows: dict[str, list[dict[str, Any]]]
) -> list[str]:
    errors: list[str] = []
    if list(workbook_rows) != CANONICAL_SHEETS:
        errors.append("workbook tabs do not match the canonical eight-tab order")
    if len(workbook_rows) > 8:
        errors.append("workbook has more than eight tabs")
    for name, rows in workbook_rows.items():
        headers = list(rows[0]) if rows else []
        if len(headers) > 6:
            errors.append(f"{name}: more than six columns")
        errors.extend(duplicate_columns(name, rows))
        errors.extend(placeholder_errors(name, rows))
    if "Change Log" in workbook_rows:
        errors.append("cleanup plan must not contain a change-log tab")
    return errors


def rendered_cell_errors(sheet: Any) -> list[str]:
    errors: list[str] = []
    for row in sheet.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and "[truncated]" in cell.value.lower():
                errors.append(f"{sheet.title}!{cell.coordinate}: proof text was truncated")
            if cell.data_type == "f":
                errors.append(f"{sheet.title}!{cell.coordinate}: formulas are not allowed")
            elif (
                isinstance(cell.value, str)
                and cell.value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n"))
                and not cell.value.startswith("'")
            ):
                errors.append(
                    f"{sheet.title}!{cell.coordinate}: formula-like text is not escaped"
                )
    return errors


def rendered_sheet_errors(sheet: Any) -> list[str]:
    errors: list[str] = []
    if sheet.max_column > 6:
        errors.append(f"{sheet.title}: rendered workbook exceeds six columns")
    if any((dimension.width or 0) > 92 for dimension in sheet.column_dimensions.values()):
        errors.append(f"{sheet.title}: column width exceeds 92")
    if any((dimension.height or 0) > 120 for dimension in sheet.row_dimensions.values()):
        errors.append(f"{sheet.title}: row height exceeds 120")
    errors.extend(rendered_cell_errors(sheet))
    return errors


def rendered_workbook_errors(workbook_path: Path) -> list[str]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        return [f"openpyxl is required for workbook state validation: {exc}"]
    workbook = load_workbook(workbook_path, read_only=False, data_only=False)
    errors: list[str] = []
    visible = [sheet.title for sheet in workbook if sheet.sheet_state == "visible"]
    if visible != CANONICAL_SHEETS[:2]:
        errors.append("only Summary and Cleanup Plan may be visible")
    for sheet in workbook:
        errors.extend(rendered_sheet_errors(sheet))
    workbook.close()
    return errors


def operations_alignment_errors(
    workbook_rows: dict[str, list[dict[str, Any]]], operations: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    operation_count = len(as_list(operations.get("operations"))) + len(
        as_list(operations.get("deferred_operations"))
    )
    unresolved_count = sum(
        1
        for row in as_list(operations.get("decision_ledger"))
        if row.get("disposition") in {"owner_decision_needed", "container_evidence_limit"}
    )
    cleanup_rows = workbook_rows.get("02 Cleanup Plan", [])
    expected_rows = operation_count + unresolved_count
    if len(cleanup_rows) != expected_rows:
        errors.append(
            f"Cleanup Plan has {len(cleanup_rows)} rows but {expected_rows} operation or "
            "decision rows are required"
        )
    summary_values = {
        str(row.get("decision") or ""): str(row.get("value") or "")
        for row in workbook_rows.get("01 Summary", [])
    }
    overall_status = summary_values.get("Overall status", "").lower()
    owner_count = sum(
        1
        for row in as_list(operations.get("decision_ledger"))
        if row.get("disposition") == "owner_decision_needed"
    )
    if owner_count and "owner decisions required" not in overall_status:
        errors.append("Summary status does not expose unresolved owner decisions")
    if operations.get("aggressiveness") == "Undecided" and (
        "cleanup level decision required" not in overall_status
    ):
        errors.append("Summary status does not expose undecided cleanup aggressiveness")
    if set((operations.get("run_statuses") or {}).values()) != {"complete"}:
        errors.append("operations do not record three complete review runs")
    return errors


def validate_workbook(
    workbook_path: Path, operations_path: Path | None = None
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not workbook_path.is_file():
        return [f"workbook does not exist: {workbook_path}"], warnings
    workbook_rows = load_xlsx_workbook(workbook_path)
    errors.extend(workbook_structure_errors(workbook_rows))
    errors.extend(rendered_workbook_errors(workbook_path))

    if operations_path:
        operations = json.loads(operations_path.read_text(encoding="utf-8"))
        errors.extend(operations_alignment_errors(workbook_rows, operations))
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--operations", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    errors, warnings = validate_workbook(args.workbook, args.operations)
    report = {
        "kind": "gtm_cleanup_workbook_gate",
        "status": "pass" if not errors else "fail",
        "workbook": str(args.workbook),
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(report, indent=2 if args.pretty else None))
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
