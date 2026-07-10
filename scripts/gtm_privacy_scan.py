#!/usr/bin/env python3
"""Scan generated GTM deliverables for local paths, emails, or probable secrets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from gtm_privacy import privacy_findings


def walk_values(value: Any, path: str = "$") -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            rows.extend(walk_values(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            rows.extend(walk_values(item, f"{path}[{index}]"))
    elif value is not None:
        rows.append((path, str(value)))
    return rows


def scan_json(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    errors = []
    for location, value in walk_values(payload):
        for finding in privacy_findings(value):
            errors.append(f"{location}: {finding}")
    return errors


def scan_text(path: Path) -> list[str]:
    errors = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        for finding in privacy_findings(line):
            errors.append(f"line {line_number}: {finding}")
    return errors


def scan_xlsx(path: Path, all_sheets: bool) -> list[str]:
    try:
        import openpyxl
    except ImportError as exc:
        raise RuntimeError("openpyxl is required to privacy-scan XLSX files") from exc
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    errors = []
    for sheet in workbook.worksheets:
        if not all_sheets and sheet.sheet_state != "visible":
            continue
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                for finding in privacy_findings(cell.value):
                    errors.append(f"{sheet.title}!{cell.coordinate}: {finding}")
    workbook.close()
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--all-sheets", action="store_true")
    args = parser.parse_args()
    suffix = args.artifact.suffix.lower()
    if suffix == ".json":
        errors = scan_json(args.artifact)
    elif suffix == ".xlsx":
        errors = scan_xlsx(args.artifact, args.all_sheets)
    else:
        errors = scan_text(args.artifact)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Privacy scan: FAIL ({len(errors)} finding(s))")
        return 1
    print("Privacy scan: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
