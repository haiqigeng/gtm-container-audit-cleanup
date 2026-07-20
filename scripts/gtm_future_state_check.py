#!/usr/bin/env python3
"""Simulate approved GTM cleanup operations and validate the future-state graph."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

from gtm_baseline_audit import audit_export
from gtm_lib import ID_KEYS, container_version, source_descriptor, source_integrity_findings
from gtm_validate_artifact import duplicate_ids, missing_references

PATH_TOKEN_RE = re.compile(r"\.([^.[\]]+)|\[(\d+)\]")


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def object_catalog(cv: dict[str, Any]) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for layer, id_key in ID_KEYS.items():
        for obj in as_list(cv.get(layer)):
            object_id = str(obj.get(id_key) or obj.get("name") or "")
            if object_id:
                catalog[f"{layer}:{object_id}"] = obj
    return catalog


def layer_counts(cv: dict[str, Any]) -> dict[str, int]:
    return {
        layer: len(as_list(cv.get(layer)))
        for layer in ID_KEYS
        if as_list(cv.get(layer))
    }


def object_name(catalog: dict[str, dict[str, Any]], key: str) -> str:
    return str(catalog.get(key, {}).get("name") or "")


def deep_replace(value: Any, before: str, after: str) -> Any:
    if isinstance(value, dict):
        return {key: deep_replace(child, before, after) for key, child in value.items()}
    if isinstance(value, list):
        return [deep_replace(child, before, after) for child in value]
    if isinstance(value, str):
        return value.replace(before, after)
    return value


def replace_in_place(target: dict[str, Any], before: str, after: str) -> None:
    updated = deep_replace(target, before, after)
    target.clear()
    target.update(updated)


def relative_path(path: str, object_key: str) -> str:
    if not path.startswith("$"):
        raise ValueError("JSON path must start with $")
    layer = object_key.split(":", 1)[0]
    match = re.match(
        rf"^\$\.(?:containerVersion\.)?{re.escape(layer)}\[\d+\](.*)$",
        path,
    )
    if match:
        return "$" + match.group(1)
    return path


def set_json_path(target: Any, path: str, value: Any) -> None:
    tokens: list[str | int] = []
    for match in PATH_TOKEN_RE.finditer(path[1:]):
        tokens.append(match.group(1) if match.group(1) is not None else int(match.group(2)))
    if not tokens:
        if not isinstance(value, dict) or not isinstance(target, dict):
            raise ValueError("root replacement requires a mapping")
        target.clear()
        target.update(copy.deepcopy(value))
        return
    current = target
    for token in tokens[:-1]:
        current = current[token]
    current[tokens[-1]] = copy.deepcopy(value)


def get_json_path(target: Any, path: str) -> Any:
    tokens: list[str | int] = []
    for match in PATH_TOKEN_RE.finditer(path[1:]):
        tokens.append(match.group(1) if match.group(1) is not None else int(match.group(2)))
    current = target
    for token in tokens:
        current = current[token]
    return current


def add_json_value(
    target: Any,
    path: str,
    value: Any,
    mode: str,
    index: int | None = None,
) -> None:
    if mode in {"append", "insert"}:
        destination = get_json_path(target, path)
        if not isinstance(destination, list):
            raise TypeError(f"addition target {path} is not a list")
        if mode == "append":
            destination.append(copy.deepcopy(value))
        else:
            if index is None or index < 0 or index > len(destination):
                raise IndexError(f"addition index {index!r} is outside {path}")
            destination.insert(index, copy.deepcopy(value))
        return

    tokens: list[str | int] = []
    for match in PATH_TOKEN_RE.finditer(path[1:]):
        tokens.append(match.group(1) if match.group(1) is not None else int(match.group(2)))
    if not tokens:
        raise ValueError("set addition requires a non-root path")
    current = target
    for token in tokens[:-1]:
        current = current[token]
    final = tokens[-1]
    if isinstance(current, dict):
        if final in current:
            raise ValueError(f"addition target {path} already exists")
        current[final] = copy.deepcopy(value)
    else:
        raise TypeError(f"set addition parent for {path} is not an object")


def apply_creations(
    cv: dict[str, Any], operations: list[dict[str, Any]], errors: list[str]
) -> None:
    catalog = object_catalog(cv)
    for operation in operations:
        for creation in as_list(operation.get("creations")):
            layer = str(creation.get("layer") or "")
            obj = creation.get("object")
            id_key = ID_KEYS.get(layer)
            if not id_key or not isinstance(obj, dict):
                errors.append("creation requires a supported GTM layer and complete object")
                continue
            object_id = str(obj.get(id_key) or obj.get("name") or "")
            key = f"{layer}:{object_id}" if object_id else ""
            if not key:
                errors.append(f"creation in {layer!r} has no {id_key}")
                continue
            if key in catalog:
                errors.append(f"creation duplicates existing object {key!r}")
                continue
            cv.setdefault(layer, []).append(copy.deepcopy(obj))
            catalog[key] = cv[layer][-1]


def remap_trigger(source: str, target: str, consumer: dict[str, Any]) -> None:
    for field in ("firingTriggerId", "blockingTriggerId"):
        consumer[field] = [
            target if str(value) == source else value for value in as_list(consumer.get(field))
        ]
    for parameter in as_list(consumer.get("parameter")):
        if not isinstance(parameter, dict):
            continue
        if parameter.get("key") != "triggerIds":
            continue
        for item in as_list(parameter.get("list")):
            if not isinstance(item, dict):
                continue
            if str(item.get("value") or "") == source:
                item["value"] = target
    boundary = consumer.get("boundary")
    if isinstance(boundary, dict) and "customEvaluationTriggerId" in boundary:
        boundary["customEvaluationTriggerId"] = [
            target if str(value) == source else value
            for value in as_list(boundary.get("customEvaluationTriggerId"))
        ]


def remap_folder(source: str, target: str, consumer: dict[str, Any]) -> None:
    if str(consumer.get("parentFolderId") or "") == source:
        consumer["parentFolderId"] = target


def apply_remap(
    remap: dict[str, Any], catalog: dict[str, dict[str, Any]], errors: list[str]
) -> None:
    source_key = str(remap.get("from_object_key") or "")
    target_key = str(remap.get("to_object_key") or "")
    source = catalog.get(source_key)
    target = catalog.get(target_key)
    if not source or not target:
        errors.append(f"cannot simulate remap {source_key!r} to {target_key!r}")
        return
    source_layer = source_key.split(":", 1)[0]
    target_layer = target_key.split(":", 1)[0]
    if source_layer != target_layer:
        errors.append(f"remap crosses GTM layers: {source_key!r} to {target_key!r}")
        return
    source_id = source_key.split(":", 1)[1]
    target_id = target_key.split(":", 1)[1]
    before_name = object_name(catalog, source_key)
    after_name = object_name(catalog, target_key)
    for consumer_key in as_list(remap.get("consumer_object_keys")):
        consumer = catalog.get(str(consumer_key))
        if not consumer:
            errors.append(f"remap references missing consumer {consumer_key!r}")
            continue
        if source_layer == "trigger":
            remap_trigger(source_id, target_id, consumer)
        elif source_layer == "variable":
            replace_in_place(consumer, "{{" + before_name + "}}", "{{" + after_name + "}}")
        elif source_layer == "tag":
            for field in ("setupTag", "teardownTag"):
                for ref in as_list(consumer.get(field)):
                    if not isinstance(ref, dict):
                        continue
                    if str(ref.get("tagName") or "") == before_name:
                        ref["tagName"] = after_name
        elif source_layer == "folder":
            remap_folder(source_id, target_id, consumer)
        else:
            errors.append(f"future-state remap is unsupported for layer {source_layer!r}")


def apply_additions(
    operation_rows: list[dict[str, Any]],
    catalog: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    for operation in operation_rows:
        for addition in as_list(operation.get("additions")):
            key = str(addition.get("object_key") or "")
            target = catalog.get(key)
            if not target:
                errors.append(f"addition references missing object {key!r}")
                continue
            path = relative_path(str(addition.get("json_path") or ""), key)
            try:
                add_json_value(
                    target,
                    path,
                    addition.get("value"),
                    str(addition.get("mode") or ""),
                    addition.get("index"),
                )
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                errors.append(f"cannot apply addition to {key} at {path}: {exc}")


def apply_changes(
    operation_rows: list[dict[str, Any]],
    catalog: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    for operation in operation_rows:
        for change in as_list(operation.get("changes")):
            key = str(change.get("object_key") or "")
            target = catalog.get(key)
            if not target:
                errors.append(f"change references missing object {key!r}")
                continue
            path = relative_path(str(change.get("json_path") or ""), key)
            try:
                current_value = get_json_path(target, path)
                if current_value != change.get("before"):
                    errors.append(f"change before value does not match {key} at {path}")
                    continue
                set_json_path(target, path, change.get("after"))
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                errors.append(f"cannot apply change to {key} at {path}: {exc}")


def apply_remaps(
    operation_rows: list[dict[str, Any]],
    catalog: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    for operation in operation_rows:
        for remap in as_list(operation.get("remaps")):
            apply_remap(remap, catalog, errors)


def rename_references(
    layer: str,
    before: str,
    after: str,
    catalog: dict[str, dict[str, Any]],
) -> None:
    if layer == "variable":
        marker_before, marker_after = "{{" + before + "}}", "{{" + after + "}}"
        for consumer in catalog.values():
            replace_in_place(consumer, marker_before, marker_after)
    elif layer == "tag":
        for consumer in catalog.values():
            for field in ("setupTag", "teardownTag"):
                for ref in as_list(consumer.get(field)):
                    if not isinstance(ref, dict):
                        continue
                    if str(ref.get("tagName") or "") == before:
                        ref["tagName"] = after


def apply_renames(
    operation_rows: list[dict[str, Any]],
    catalog: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    for operation in operation_rows:
        for rename in as_list(operation.get("renames")):
            key = str(rename.get("object_key") or "")
            target = catalog.get(key)
            if not target:
                errors.append(f"rename references missing object {key!r}")
                continue
            before = str(rename.get("before") or "")
            after = str(rename.get("after") or "")
            if str(target.get("name") or "") != before:
                errors.append(f"rename before value does not match {key!r}")
                continue
            target["name"] = after
            rename_references(key.split(":", 1)[0], before, after, catalog)


def apply_deletions(
    cv: dict[str, Any],
    operation_rows: list[dict[str, Any]],
    catalog: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    deletions = {
        str(item.get("object_key") or "")
        for operation in operation_rows
        for item in as_list(operation.get("deletions"))
    }
    for key in sorted(deletions):
        if key not in catalog:
            errors.append(f"deletion references missing object {key!r}")
            continue
        layer, object_id = key.split(":", 1)
        id_key = ID_KEYS[layer]
        cv[layer] = [
            obj
            for obj in as_list(cv.get(layer))
            if str(obj.get(id_key) or obj.get("name") or "") != object_id
        ]


def apply_operations(
    source: dict[str, Any], operations: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    result = copy.deepcopy(source)
    cv = container_version(result)
    errors: list[str] = []
    operation_rows = as_list(operations.get("operations"))

    apply_creations(cv, operation_rows, errors)
    catalog = object_catalog(cv)
    apply_additions(operation_rows, catalog, errors)
    apply_changes(operation_rows, catalog, errors)
    apply_remaps(operation_rows, catalog, errors)
    apply_renames(operation_rows, catalog, errors)
    apply_deletions(cv, operation_rows, catalog, errors)
    return result, errors


def finding_signature(finding: dict[str, Any]) -> tuple[Any, ...]:
    return (
        finding.get("module_name"),
        finding.get("finding_type"),
        finding.get("signature_key"),
        tuple(sorted(str(value) for value in as_list(finding.get("object_ids")))),
        str(finding.get("deterministic_evidence") or ""),
    )


def evidence_shape(finding: dict[str, Any]) -> str:
    text = str(finding.get("deterministic_evidence") or "").lower()
    text = re.sub(r"\b[0-9a-f]{8,}\b", "<hash>", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\b", "<number>", text)
    return " ".join(text.split())


def evidence_numbers(finding: dict[str, Any]) -> list[float]:
    text = str(finding.get("deterministic_evidence") or "").lower()
    text = re.sub(r"\b[0-9a-f]{8,}\b", "", text)
    return [float(value) for value in re.findall(r"\b\d+(?:\.\d+)?\b", text)]


def prior_finding_covers(
    before: dict[str, Any], after: dict[str, Any]
) -> bool:
    if (
        before.get("module_name") != after.get("module_name")
        or before.get("finding_type") != after.get("finding_type")
        or before.get("object_type") != after.get("object_type")
        or evidence_shape(before) != evidence_shape(after)
    ):
        return False
    before_ids = {str(value) for value in as_list(before.get("object_ids"))}
    after_ids = {str(value) for value in as_list(after.get("object_ids"))}
    if (before_ids or after_ids) and not after_ids <= before_ids:
        return False
    before_numbers = evidence_numbers(before)
    after_numbers = evidence_numbers(after)
    if len(before_numbers) != len(after_numbers):
        return not after_numbers
    return all(after <= prior for prior, after in zip(before_numbers, after_numbers, strict=True))


def nonzero_findings(scan: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row for row in as_list(scan.get("findings")) if row.get("finding_type") != "zero_findings"
    ]


def missing_reference_values(report: dict[str, Any]) -> set[tuple[str, str]]:
    values: set[tuple[str, str]] = set()
    for category, items in report.items():
        if category == "referencedCustomTemplateIds":
            continue
        values.update((category, str(value)) for value in as_list(items))
    return values


def future_integrity_results(
    before_cv: dict[str, Any], future_cv: dict[str, Any]
) -> tuple[dict[str, Any], list[tuple[str, str]], list[str]]:
    before_missing = missing_reference_values(missing_references(before_cv))
    after_report = missing_references(future_cv)
    new_missing = sorted(missing_reference_values(after_report) - before_missing)
    errors = []
    if new_missing:
        errors.append("future state creates missing references: " + repr(new_missing))
    duplicates = duplicate_ids(future_cv)
    if duplicates:
        errors.append("future state contains duplicate IDs: " + repr(duplicates))
    return after_report, new_missing, errors


def scan_future_payload(
    export_path: Path, future: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    before_scan = audit_export(export_path)
    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory) / "future-state.json"
        temporary_path.write_text(json.dumps(future, ensure_ascii=False), encoding="utf-8")
        after_scan = audit_export(temporary_path)
    return before_scan, after_scan


def newly_created_findings(
    before_rows: list[dict[str, Any]], after_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return [
        row
        for row in after_rows
        if not any(prior_finding_covers(before, row) for before in before_rows)
    ]


def requested_operational_cleanup_ids(operations: dict[str, Any]) -> set[str]:
    return {
        str(reference)
        for operation in as_list(operations.get("operations"))
        if "operational_sanitation" in as_list(operation.get("source_runs"))
        for reference in as_list(operation.get("source_references"))
        if str(reference).startswith("BASE-")
    }


def finding_persists(
    before: dict[str, Any], after_rows: list[dict[str, Any]]
) -> bool:
    before_ids = {str(value) for value in as_list(before.get("object_ids"))}
    return any(
        after.get("module_name") == before.get("module_name")
        and after.get("finding_type") == before.get("finding_type")
        and (
            bool(before_ids & {str(value) for value in as_list(after.get("object_ids"))})
            or not before_ids
            and evidence_shape(after) == evidence_shape(before)
        )
        for after in after_rows
    )


def unresolved_cleanup_ids(
    before_rows: list[dict[str, Any]],
    after_rows: list[dict[str, Any]],
    cleanup_ids: set[str],
) -> list[str]:
    return sorted(
        str(row.get("finding_id") or "")
        for row in before_rows
        if str(row.get("finding_id") or "") in cleanup_ids
        and finding_persists(row, after_rows)
    )


def count_deltas(
    before_cv: dict[str, Any], future_cv: dict[str, Any]
) -> dict[str, dict[str, int]]:
    before_counts = layer_counts(before_cv)
    after_counts = layer_counts(future_cv)
    return {
        layer: {
            "before": before_counts.get(layer, 0),
            "after": after_counts.get(layer, 0),
            "delta": after_counts.get(layer, 0) - before_counts.get(layer, 0),
        }
        for layer in sorted(set(before_counts) | set(after_counts))
    }


def check_future_state(
    export_path: Path, operations: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    source = load_json(export_path)
    blocking_integrity = [
        row for row in source_integrity_findings(source) if row.get("blocking")
    ]
    if blocking_integrity:
        errors = [
            "source integrity gate blocked future-state simulation: "
            + ", ".join(
                sorted(
                    str(row.get("finding_type") or "source_integrity_error")
                    for row in blocking_integrity
                )
            )
        ]
        return (
            {
                **source_descriptor(export_path),
                "kind": "gtm_future_state_validation",
                "schema_version": 1,
                "status": "blocked_source_integrity",
                "operation_count": len(as_list(operations.get("operations"))),
                "source_integrity_findings": blocking_integrity,
                "errors": errors,
            },
            errors,
        )
    before_cv = container_version(source)
    future, errors = apply_operations(source, operations)
    future_cv = container_version(future)
    after_missing_report, new_missing, integrity_errors = future_integrity_results(
        before_cv, future_cv
    )
    errors.extend(integrity_errors)
    before_scan, after_scan = scan_future_payload(export_path, future)
    before_rows = nonzero_findings(before_scan)
    before_signatures = {finding_signature(row) for row in before_rows}
    after_rows = nonzero_findings(after_scan)
    after_signatures = {finding_signature(row) for row in after_rows}
    new_findings = newly_created_findings(before_rows, after_rows)
    if new_findings:
        errors.append(
            "future state creates new operational findings: "
            + ", ".join(sorted(str(row.get("finding_type") or "") for row in new_findings))
        )
    operational_cleanup_ids = requested_operational_cleanup_ids(operations)
    unresolved = unresolved_cleanup_ids(before_rows, after_rows, operational_cleanup_ids)
    if unresolved:
        errors.append(
            "future state does not resolve operational cleanup findings: "
            + ", ".join(sorted(unresolved))
        )
    report = {
        **source_descriptor(export_path),
        "kind": "gtm_future_state_validation",
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "operation_count": len(as_list(operations.get("operations"))),
        "object_counts": count_deltas(before_cv, future_cv),
        "before_operational_findings": len(before_signatures),
        "after_operational_findings": len(after_signatures),
        "resolved_operational_cleanup_ids": sorted(operational_cleanup_ids - set(unresolved)),
        "unresolved_operational_cleanup_ids": sorted(unresolved),
        "new_operational_findings": new_findings,
        "new_missing_references": new_missing,
        "after_missing_references": after_missing_report,
        "errors": errors,
    }
    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("operations", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--future-export", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    operations = load_json(args.operations)
    report, errors = check_future_state(args.export, operations)
    if args.future_export and not errors:
        future, apply_errors = apply_operations(load_json(args.export), operations)
        errors.extend(apply_errors)
        args.future_export.parent.mkdir(parents=True, exist_ok=True)
        args.future_export.write_text(
            json.dumps(future, ensure_ascii=False, indent=2 if args.pretty else None) + "\n",
            encoding="utf-8",
        )
    rendered = json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
