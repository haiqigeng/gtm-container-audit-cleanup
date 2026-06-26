#!/usr/bin/env python3
"""Validate GTM audit completion-gate reconciliation rows.

Input may be:
- CSV exported from the Workstream Reconciliation tab.
- JSON list of row objects, or {"rows": [...]}.
- XLSX workbook with a sheet named "18b Workstream Reconciliation" or any
  sheet whose name contains "Reconciliation".
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from xml.etree import ElementTree


COUNT_FIELDS = [
    "total_source_count",
    "inventoried_count",
    "dependency_mapped_count",
    "semantically_validated_count",
    "cleanup_decision_count",
    "deferred_count",
    "not_applicable_count",
    "user_excluded_count",
    "unresolved_count",
]

REQUIRED_FIELDS = ["workstream", "object_family"] + COUNT_FIELDS

ALIASES = {
    "total": "total_source_count",
    "total_count": "total_source_count",
    "source_count": "total_source_count",
    "total_source_objects": "total_source_count",
    "dependency_mapped": "dependency_mapped_count",
    "semantically_validated": "semantically_validated_count",
    "semantic_validated_count": "semantically_validated_count",
    "cleanup_decided_count": "cleanup_decision_count",
    "cleanup_decisioned_count": "cleanup_decision_count",
    "cleanup_decision_objects": "cleanup_decision_count",
    "not_applicable": "not_applicable_count",
    "user_excluded": "user_excluded_count",
    "unresolved": "unresolved_count",
}


def normalize_header(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return ALIASES.get(text, text)


def to_int(row: Dict[str, Any], field: str) -> Tuple[int, str | None]:
    raw = row.get(field, "")
    if raw is None or raw == "":
        return 0, f"missing count '{field}'"
    try:
        return int(float(str(raw).strip())), None
    except ValueError:
        return 0, f"invalid count '{field}'={raw!r}"


def load_csv(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for raw in reader:
            rows.append({normalize_header(k): v for k, v in raw.items()})
        return rows


def load_json(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        data = data["rows"]
    if not isinstance(data, list):
        raise ValueError("JSON input must be a list of rows or {'rows': [...]}")
    return [{normalize_header(k): v for k, v in row.items()} for row in data]


def column_index(cell_ref: str) -> int:
    letters = re.sub(r"[^A-Z]", "", cell_ref.upper())
    value = 0
    for char in letters:
        value = value * 26 + (ord(char) - ord("A") + 1)
    return max(value - 1, 0)


def xml_text(node: ElementTree.Element | None) -> str:
    if node is None:
        return ""
    return "".join(node.itertext())


def load_xlsx_stdlib(path: Path) -> List[Dict[str, Any]]:
    ns = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
    }

    with zipfile.ZipFile(path) as archive:
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        rels = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))

        rel_targets = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall("pkgrel:Relationship", ns)
        }

        sheet_target = None
        for sheet in workbook.findall("main:sheets/main:sheet", ns):
            name = sheet.attrib.get("name", "")
            rel_id = sheet.attrib.get(f"{{{ns['rel']}}}id")
            if name == "18b Workstream Reconciliation" or "reconciliation" in name.lower():
                target = rel_targets.get(rel_id or "")
                if not target:
                    continue
                sheet_target = target if target.startswith("xl/") else f"xl/{target.lstrip('/')}"
                break
        if not sheet_target:
            raise ValueError("No reconciliation sheet found")

        shared_strings: List[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("main:si", ns):
                shared_strings.append(xml_text(item))

        sheet_root = ElementTree.fromstring(archive.read(sheet_target))
        parsed_rows: List[List[str]] = []
        for row in sheet_root.findall("main:sheetData/main:row", ns):
            values: List[str] = []
            for cell in row.findall("main:c", ns):
                ref = cell.attrib.get("r", "")
                index = column_index(ref) if ref else len(values)
                while len(values) <= index:
                    values.append("")
                cell_type = cell.attrib.get("t", "")
                if cell_type == "s":
                    raw = xml_text(cell.find("main:v", ns))
                    values[index] = shared_strings[int(raw)] if raw else ""
                elif cell_type == "inlineStr":
                    values[index] = xml_text(cell.find("main:is", ns))
                else:
                    values[index] = xml_text(cell.find("main:v", ns))
            if any(value != "" for value in values):
                parsed_rows.append(values)

    if not parsed_rows:
        return []
    headers = [normalize_header(value) for value in parsed_rows[0]]
    rows = []
    for values in parsed_rows[1:]:
        rows.append({headers[i]: values[i] for i in range(min(len(headers), len(values)))})
    return rows


def load_xlsx_openpyxl(path: Path) -> List[Dict[str, Any]]:
    try:
        import openpyxl  # type: ignore
    except ImportError as exc:
        raise RuntimeError("openpyxl is unavailable") from exc

    workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
    sheet_name = None
    if "18b Workstream Reconciliation" in workbook.sheetnames:
        sheet_name = "18b Workstream Reconciliation"
    else:
        for candidate in workbook.sheetnames:
            if "reconciliation" in candidate.lower():
                sheet_name = candidate
                break
    if not sheet_name:
        raise ValueError("No reconciliation sheet found")

    sheet = workbook[sheet_name]
    rows_iter = sheet.iter_rows(values_only=True)
    headers = [normalize_header(v) for v in next(rows_iter, [])]
    rows = []
    for values in rows_iter:
        if not values or all(v in (None, "") for v in values):
            continue
        rows.append({headers[i]: values[i] for i in range(min(len(headers), len(values)))})
    return rows


def load_xlsx(path: Path) -> List[Dict[str, Any]]:
    try:
        return load_xlsx_openpyxl(path)
    except Exception as first_exc:  # noqa: BLE001 - fallback should cover missing optional deps.
        try:
            return load_xlsx_stdlib(path)
        except Exception as second_exc:  # noqa: BLE001 - preserve both failure reasons.
            raise RuntimeError(
                f"Unable to read XLSX with openpyxl or stdlib fallback. "
                f"openpyxl error: {first_exc}; fallback error: {second_exc}"
            ) from second_exc


def load_rows(path: Path) -> List[Dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_csv(path)
    if suffix == ".json":
        return load_json(path)
    if suffix == ".xlsx":
        return load_xlsx(path)
    raise ValueError("Unsupported file type. Use .csv, .json, or .xlsx")


def validate_rows(rows: Iterable[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    row_list = list(rows)
    if not row_list:
        return ["no reconciliation rows found"], warnings

    for index, row in enumerate(row_list, start=2):
        label = f"row {index}"
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            errors.append(f"{label}: missing required fields: {', '.join(missing)}")
            continue

        counts: Dict[str, int] = {}
        for field in COUNT_FIELDS:
            value, problem = to_int(row, field)
            counts[field] = value
            if problem:
                errors.append(f"{label}: {problem}")

        semantic_total = (
            counts["semantically_validated_count"]
            + counts["deferred_count"]
            + counts["not_applicable_count"]
            + counts["user_excluded_count"]
        )
        if counts["total_source_count"] != semantic_total:
            errors.append(
                f"{label}: semantic coverage mismatch: total_source_count="
                f"{counts['total_source_count']} but semantically_validated + deferred "
                f"+ not_applicable + user_excluded = {semantic_total}"
            )
        if counts["unresolved_count"] != 0:
            errors.append(f"{label}: unresolved_count is {counts['unresolved_count']}")
        if counts["inventoried_count"] < counts["total_source_count"]:
            warnings.append(f"{label}: inventoried_count is below total_source_count")
        if counts["dependency_mapped_count"] < counts["semantically_validated_count"]:
            warnings.append(f"{label}: dependency_mapped_count is below semantically_validated_count")
        if counts["cleanup_decision_count"] < counts["semantically_validated_count"]:
            warnings.append(f"{label}: cleanup_decision_count is below semantically_validated_count")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="CSV, JSON, or XLSX reconciliation file")
    args = parser.parse_args()

    try:
        rows = load_rows(args.input)
        errors, warnings = validate_rows(rows)
    except Exception as exc:  # noqa: BLE001 - CLI should report any loading problem.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Gate status: FAIL ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1

    print(f"Gate status: PASS ({len(rows)} row(s), {len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
