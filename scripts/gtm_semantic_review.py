#!/usr/bin/env python3
"""Scaffold and validate source-bound GTM D1-D3 semantic reviews."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from gtm_lib import (
    ID_KEYS,
    SEMANTIC_LAYERS,
    comparable,
    container_version,
    custom_template_id,
    is_system_variable_reference,
    object_id,
    refs,
    safe_scalar_preview,
    source_descriptor,
    stable_hash,
    trigger_group_members,
    walk_json_fields,
)
from gtm_vendor_registry import vendor_record

REVIEW_TEXT_FIELDS = (
    "business_role",
    "expected_contract",
    "actual_inputs_or_sources",
    "literal_behavior",
    "output_or_side_effect",
    "consumer_context",
    "analyst_judgment",
    "cleanup_implication",
    "evidence_or_qa_blocker",
)
GENERIC_PHRASES = (
    "custom code inspected",
    "configuration reviewed",
    "no issue found",
    "see config",
    "see export",
    "static scan completed",
    "returns computed value",
    "payload transformer",
    "browser side effect",
    "review later",
    "d3 required",
)
VALID_STATUSES = {
    "Keep",
    "Fix",
    "Consolidate",
    "Delete candidate",
    "More info needed",
    "Not applicable",
}
VALID_CONFIDENCE = {"High", "Medium", "Low"}
VALID_RESOLUTIONS = {
    "cleanup_operation",
    "documented_exception",
    "runtime_blocker",
    "owner_decision_needed",
    "not_applicable",
}
VALID_READINESS = {
    "safe_now",
    "approval_required",
    "d4_required",
    "owner_blocked",
    "no_change",
}
VALID_RISK_CLASSES = {"Low", "Medium", "High", "Critical"}
GENERATED_FIELDS = {
    "review_id",
    "object_key",
    "layer",
    "object_id",
    "object_name",
    "object_type",
    "config_hash",
    "source_json_path",
    "source_facts",
    "available_evidence_anchors",
    "required_logic_anchors",
    "required_branch_reviews",
    "code_line_facts",
    "required_code_line_hashes",
    "reference_trace_requirements",
    "referenced_variables",
    "export_consumers",
    "specificity_tokens",
    "sibling_comparison_required",
    "detected_vendor",
    "vendor_category",
    "official_doc_candidates",
}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def layer_objects(cv: dict[str, Any]) -> list[tuple[str, int, dict[str, Any]]]:
    rows: list[tuple[str, int, dict[str, Any]]] = []
    for layer in SEMANTIC_LAYERS:
        for index, obj in enumerate(as_list(cv.get(layer))):
            rows.append((layer, index, obj))
    return rows


def object_key(layer: str, obj: dict[str, Any]) -> str:
    return f"{layer}:{object_id(obj, ID_KEYS[layer])}"


def object_type(layer: str, obj: dict[str, Any]) -> str:
    return str(obj.get("type") or ("customTemplate" if layer == "customTemplate" else ""))


def object_hash(obj: dict[str, Any]) -> str:
    return stable_hash(comparable(obj, {"path", "fingerprint", "accountId", "containerId"}))


def build_consumers(cv: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    consumers: dict[str, list[dict[str, str]]] = defaultdict(list)
    for layer, index, obj in layer_objects(cv):
        key = object_key(layer, obj)
        name = str(obj.get("name") or "")
        for fact in walk_json_fields(obj, f"$.containerVersion.{layer}[{index}]"):
            for reference in fact["referenced_variables"]:
                consumers[f"variable-name:{reference}"].append(
                    {
                        "consumer_key": key,
                        "consumer_name": name,
                        "relation": "variable_reference",
                        "source_json_path": fact["json_path"],
                    }
                )

    trigger_by_id = {
        str(trigger.get("triggerId")): trigger
        for trigger in as_list(cv.get("trigger"))
        if trigger.get("triggerId") is not None
    }
    for tag_index, tag in enumerate(as_list(cv.get("tag"))):
        tag_key = object_key("tag", tag)
        for relation in ("firingTriggerId", "blockingTriggerId"):
            for trigger_id in as_list(tag.get(relation)):
                consumers[f"trigger-id:{trigger_id}"].append(
                    {
                        "consumer_key": tag_key,
                        "consumer_name": str(tag.get("name") or ""),
                        "relation": relation,
                        "source_json_path": f"$.containerVersion.tag[{tag_index}].{relation}",
                    }
                )
    for trigger in as_list(cv.get("trigger")):
        group_key = object_key("trigger", trigger)
        for member_id in trigger_group_members(trigger):
            if str(member_id) in trigger_by_id:
                consumers[f"trigger-id:{member_id}"].append(
                    {
                        "consumer_key": group_key,
                        "consumer_name": str(trigger.get("name") or ""),
                        "relation": "trigger_group_member",
                        "source_json_path": "$.containerVersion.trigger.parameter.triggerIds",
                    }
                )

    for layer in ("tag", "variable", "client", "transformation"):
        for obj in as_list(cv.get(layer)):
            template_id = custom_template_id(obj)
            if template_id:
                consumers[f"template-id:{template_id}"].append(
                    {
                        "consumer_key": object_key(layer, obj),
                        "consumer_name": str(obj.get("name") or ""),
                        "relation": "custom_template",
                        "source_json_path": f"$.containerVersion.{layer}.type",
                    }
                )
    return dict(consumers)


def object_consumers(
    layer: str, obj: dict[str, Any], consumers: dict[str, list[dict[str, str]]]
) -> list[dict[str, str]]:
    if layer == "variable":
        return consumers.get(f"variable-name:{obj.get('name') or ''}", [])
    if layer == "trigger":
        return consumers.get(f"trigger-id:{obj.get('triggerId') or ''}", [])
    if layer == "customTemplate":
        return consumers.get(f"template-id:{obj.get('templateId') or ''}", [])
    return []


def specific_tokens(obj: dict[str, Any]) -> list[str]:
    tokens: set[str] = set()
    for token in re.findall(r"[A-Za-z0-9_.-]{4,}", str(obj.get("name") or "")):
        tokens.add(token.lower())
    for parameter in as_list(obj.get("parameter")):
        key = str(parameter.get("key") or "")
        if len(key) >= 4:
            tokens.add(key.lower())
    for reference in refs(obj):
        if len(reference) >= 4:
            tokens.add(reference.lower())
    for trigger_id in as_list(obj.get("firingTriggerId")) + as_list(obj.get("blockingTriggerId")):
        tokens.add(str(trigger_id).lower())
    for fact in walk_json_fields(obj):
        preview = str(fact.get("value_preview") or "")
        for token in re.findall(
            r"(?:ecommerce|eventModel|items?|products?|consent|storage)[A-Za-z0-9_.\[\]-]*",
            preview,
            re.I,
        ):
            if len(token) >= 4:
                tokens.add(token.lower())
    return sorted(tokens)[:80]


def sibling_review_required(obj: dict[str, Any]) -> bool:
    parameters = as_list(obj.get("parameter"))
    keys = {str(parameter.get("key") or "") for parameter in parameters}
    text = json.dumps(obj, ensure_ascii=False).lower()
    consent_fields = {
        "ad_storage",
        "analytics_storage",
        "ad_user_data",
        "ad_personalization",
        "personalization_storage",
    }
    return (
        len(keys) >= 2 or len(consent_fields.intersection(set(re.findall(r"[a-z_]+", text)))) >= 2
    )


def logic_anchors(facts: list[dict[str, Any]]) -> list[str]:
    ignored_suffixes = (
        ".accountId",
        ".containerId",
        ".fingerprint",
        ".path",
        ".tagId",
        ".triggerId",
        ".variableId",
        ".templateId",
        ".clientId",
        ".transformationId",
        ".name",
    )
    return [fact["json_path"] for fact in facts if not fact["json_path"].endswith(ignored_suffixes)]


def parameter_value(obj: dict[str, Any], key: str) -> str:
    for parameter in as_list(obj.get("parameter")):
        if parameter.get("key") == key and parameter.get("value") is not None:
            return str(parameter["value"])
    return ""


def code_body(layer: str, obj: dict[str, Any]) -> str:
    if layer == "tag":
        return parameter_value(obj, "html")
    if layer == "variable":
        return parameter_value(obj, "javascript")
    if layer == "customTemplate":
        return str(obj.get("templateData") or "")
    return ""


def code_line_facts(layer: str, obj: dict[str, Any]) -> list[dict[str, Any]]:
    facts = []
    for line_number, line in enumerate(code_body(layer, obj).splitlines(), start=1):
        if not line.strip():
            continue
        facts.append(
            {
                "line_number": line_number,
                "line_hash": stable_hash(line.strip()),
                "line_preview": safe_scalar_preview(line.strip(), 120),
            }
        )
    return facts


def reference_trace_requirements(cv: dict[str, Any], obj: dict[str, Any]) -> list[dict[str, Any]]:
    variables = {
        str(variable.get("name") or ""): (index, variable)
        for index, variable in enumerate(as_list(cv.get("variable")))
        if variable.get("name")
    }

    def visit(
        reference: str,
        active: tuple[str, ...],
        object_keys: set[str],
        anchors: set[str],
        terminal_states: set[str],
    ) -> None:
        if is_system_variable_reference(reference):
            terminal_states.add("system")
            return
        if reference in active:
            terminal_states.add("cycle")
            return
        target = variables.get(reference)
        if not target:
            terminal_states.add("missing")
            return
        index, variable = target
        object_keys.add(object_key("variable", variable))
        facts = walk_json_fields(variable, f"$.containerVersion.variable[{index}]")
        anchors.update(logic_anchors(facts))
        children = sorted(
            child for child in refs(variable) if not is_system_variable_reference(child)
        )
        if not children:
            terminal_states.add("resolved")
            return
        for child in children:
            visit(
                child,
                (*active, reference),
                object_keys,
                anchors,
                terminal_states,
            )

    requirements = []
    for reference in sorted(refs(obj)):
        if is_system_variable_reference(reference):
            continue
        object_keys: set[str] = set()
        anchors: set[str] = set()
        terminal_states: set[str] = set()
        visit(reference, (), object_keys, anchors, terminal_states)
        requirements.append(
            {
                "reference": reference,
                "required_object_keys": sorted(object_keys),
                "required_evidence_anchors": sorted(anchors),
                "terminal_states": sorted(terminal_states),
            }
        )
    return requirements


def scaffold_review(export_path: Path) -> dict[str, Any]:
    data = json.loads(export_path.read_text(encoding="utf-8"))
    cv = container_version(data)
    consumers = build_consumers(cv)
    rows: list[dict[str, Any]] = []

    for number, (layer, index, obj) in enumerate(layer_objects(cv), start=1):
        base_path = f"$.containerVersion.{layer}[{index}]"
        facts = walk_json_fields(obj, base_path)
        line_facts = code_line_facts(layer, obj)
        required_anchors = logic_anchors(facts)
        vendor = vendor_record(json.dumps(obj, ensure_ascii=False))
        current_consumers = object_consumers(layer, obj, consumers)
        rows.append(
            {
                "review_id": f"D3-{number:05d}",
                "object_key": object_key(layer, obj),
                "layer": layer,
                "object_id": object_id(obj, ID_KEYS[layer]),
                "object_name": str(obj.get("name") or ""),
                "object_type": object_type(layer, obj),
                "config_hash": object_hash(obj),
                "source_json_path": base_path,
                "source_facts": facts,
                "available_evidence_anchors": [fact["json_path"] for fact in facts],
                "required_logic_anchors": required_anchors,
                "required_branch_reviews": [
                    {
                        "json_path": fact["json_path"],
                        "value_hash": fact["value_hash"],
                        "value_type": fact["value_type"],
                        "value_preview": fact["value_preview"],
                    }
                    for fact in facts
                    if fact["json_path"] in required_anchors
                ],
                "code_line_facts": line_facts,
                "required_code_line_hashes": [fact["line_hash"] for fact in line_facts],
                "referenced_variables": sorted(refs(obj)),
                "reference_trace_requirements": reference_trace_requirements(cv, obj),
                "export_consumers": current_consumers,
                "specificity_tokens": specific_tokens(obj),
                "sibling_comparison_required": sibling_review_required(obj),
                "detected_vendor": vendor.get("name"),
                "vendor_category": vendor.get("category"),
                "official_doc_candidates": vendor.get("official_docs", []),
                "review_status": "pending",
                "depth_required": "D1, D2, D3",
                "depth_completed": "",
                "business_role": "",
                "expected_contract": "",
                "official_doc_basis": "",
                "actual_inputs_or_sources": "",
                "literal_behavior": "",
                "output_or_side_effect": "",
                "consumer_context": "",
                "analyst_judgment": "",
                "cleanup_implication": "",
                "evidence_or_qa_blocker": "",
                "semantic_status": "",
                "confidence": "",
                "evidence_anchors": [],
                "configuration_branch_reviews": [],
                "code_line_reviews": [],
                "consumer_evidence_keys": [],
                "reference_traces": [],
                "sibling_comparison": "",
                "sibling_evidence_anchors": [],
                "source_finding_ids": [],
                "operation_group": "",
                "area": "",
                "problem_type": "",
                "problem": "",
                "why_it_matters": "",
                "expected_clean_state": "",
                "exact_proposed_action": "",
                "preconditions": "",
                "qa_steps": "",
                "rollback": "",
                "blocker": "",
                "priority": "",
                "resolution_status": "",
                "execution_readiness": "",
                "risk_class": "",
            }
        )

    return {
        **source_descriptor(export_path),
        "kind": "gtm_source_bound_semantic_review",
        "schema_version": 1,
        "review_status": "pending",
        "rows": rows,
    }


def reuse_completed_rows(scaffold: dict[str, Any], previous: dict[str, Any]) -> int:
    previous_by_key = {
        str(row.get("object_key") or ""): row for row in as_list(previous.get("rows"))
    }
    reused = 0
    for row in scaffold["rows"]:
        old = previous_by_key.get(row["object_key"])
        if not old or str(old.get("review_status") or "").lower() != "complete":
            continue
        stable_fields = (
            "config_hash",
            "source_json_path",
            "referenced_variables",
            "export_consumers",
            "required_logic_anchors",
            "required_code_line_hashes",
            "reference_trace_requirements",
        )
        if any(old.get(field) != row.get(field) for field in stable_fields):
            continue
        for field, value in old.items():
            if field not in GENERATED_FIELDS:
                row[field] = value
        reused += 1
    scaffold["review_status"] = "in_progress" if reused else "pending"
    scaffold["reused_completed_rows"] = reused
    return reused


def merge_review_files(export_path: Path, paths: list[Path]) -> dict[str, Any]:
    scaffold = scaffold_review(export_path)
    total_reused = 0
    for path in paths:
        total_reused += reuse_completed_rows(scaffold, json.loads(path.read_text(encoding="utf-8")))
    scaffold["reused_completed_rows"] = total_reused
    return scaffold


def word_count(value: Any) -> int:
    return len(re.findall(r"\b[\w{}.-]+\b", str(value or "")))


def text_quality_errors(row: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []
    combined = " ".join(str(row.get(field) or "") for field in REVIEW_TEXT_FIELDS)
    lowered = combined.lower()
    for field in REVIEW_TEXT_FIELDS:
        value = str(row.get(field) or "").strip()
        if word_count(value) < 5:
            errors.append(f"row {index}: {field} is too short for source-bound D3 proof")
        if any(phrase in value.lower() for phrase in GENERIC_PHRASES):
            errors.append(f"row {index}: {field} contains generic D3 wording")

    tokens = [str(token).lower() for token in as_list(row.get("specificity_tokens"))]
    if tokens and not any(token in lowered for token in tokens):
        errors.append(f"row {index}: D3 text contains no object-specific source token")
    return errors


def expected_rows(export_path: Path) -> dict[str, dict[str, Any]]:
    return {row["object_key"]: row for row in scaffold_review(export_path)["rows"]}


def validate_reference_traces(
    row: dict[str, Any], expected: dict[str, Any], index: int
) -> list[str]:
    errors: list[str] = []
    traces = {
        str(trace.get("reference") or ""): trace
        for trace in as_list(row.get("reference_traces"))
        if isinstance(trace, dict)
    }
    for requirement in expected["reference_trace_requirements"]:
        reference = requirement["reference"]
        trace = traces.get(reference)
        if not trace:
            errors.append(f"row {index}: missing recursive trace for variable {reference!r}")
            continue
        required_keys = set(requirement["required_object_keys"])
        actual_keys = set(str(value) for value in as_list(trace.get("object_chain")))
        if actual_keys != required_keys:
            errors.append(
                f"row {index}: trace for {reference!r} does not match the source object chain"
            )
        required_anchors = set(requirement["required_evidence_anchors"])
        trace_anchors = set(str(value) for value in as_list(trace.get("evidence_anchors")))
        if trace_anchors != required_anchors:
            errors.append(
                f"row {index}: trace for {reference!r} does not cover its source branches"
            )
        required_states = set(requirement["terminal_states"])
        actual_states = set(str(value) for value in as_list(trace.get("terminal_states")))
        if actual_states != required_states:
            errors.append(f"row {index}: trace for {reference!r} has incorrect terminal states")
        if word_count(trace.get("terminal_source")) < 5:
            errors.append(
                f"row {index}: trace for {reference!r} lacks a specific terminal-source explanation"
            )
    return errors


def review_text_valid(value: Any, minimum_words: int = 5) -> bool:
    text = str(value or "").strip().lower()
    return word_count(text) >= minimum_words and not any(
        phrase in text for phrase in GENERIC_PHRASES
    )


def validate_branch_reviews(row: dict[str, Any], expected: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []
    required = {item["json_path"]: item for item in expected["required_branch_reviews"]}
    supplied = {
        str(item.get("json_path") or ""): item
        for item in as_list(row.get("configuration_branch_reviews"))
        if isinstance(item, dict)
    }
    if set(supplied) != set(required):
        errors.append(
            f"row {index}: configuration branch reviews do not exactly cover the source branches"
        )
    for path, source in required.items():
        item = supplied.get(path)
        if not item:
            continue
        if item.get("value_hash") != source["value_hash"]:
            errors.append(f"row {index}: branch review hash mismatch for {path}")
        if not review_text_valid(item.get("interpretation")):
            errors.append(f"row {index}: branch review lacks specific interpretation for {path}")
        if str(item.get("logic_role") or "") not in {
            "Input",
            "Condition",
            "Transformation",
            "Output",
            "Routing",
            "Consent",
            "Execution control",
            "Metadata",
            "Not applicable",
        }:
            errors.append(f"row {index}: branch review has invalid logic_role for {path}")
    return errors


def validate_code_line_reviews(
    row: dict[str, Any], expected: dict[str, Any], index: int
) -> list[str]:
    errors: list[str] = []
    required = {item["line_hash"]: item for item in expected["code_line_facts"]}
    supplied = {
        str(item.get("line_hash") or ""): item
        for item in as_list(row.get("code_line_reviews"))
        if isinstance(item, dict)
    }
    if set(supplied) != set(required):
        errors.append(
            f"row {index}: code-line reviews do not exactly cover the exported nonblank lines"
        )
    for line_hash, source in required.items():
        item = supplied.get(line_hash)
        if not item:
            continue
        if item.get("line_number") != source["line_number"]:
            errors.append(f"row {index}: code-line review number mismatch for hash {line_hash}")
        if not review_text_valid(item.get("interpretation")):
            errors.append(
                f"row {index}: code line {source['line_number']} lacks specific interpretation"
            )
    return errors


def validate_review(export_path: Path, review_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    review = json.loads(review_path.read_text(encoding="utf-8"))
    expected = expected_rows(export_path)
    descriptor = source_descriptor(export_path)

    if review.get("source_sha256") != descriptor["source_sha256"]:
        errors.append("semantic review source_sha256 does not match the export")
    if review.get("kind") != "gtm_source_bound_semantic_review":
        errors.append("semantic review kind is invalid")

    rows = as_list(review.get("rows"))
    by_key: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows, start=2):
        key = str(row.get("object_key") or "")
        if key in by_key:
            errors.append(f"row {index}: duplicate object_key {key!r}")
        by_key[key] = row

    for key in sorted(set(expected) - set(by_key)):
        errors.append(f"missing semantic review row for {key}")
    for key in sorted(set(by_key) - set(expected)):
        errors.append(f"semantic review contains unknown object_key {key}")

    for index, (key, expected_row) in enumerate(expected.items(), start=2):
        row = by_key.get(key)
        if not row:
            continue
        for field in ("layer", "object_id", "object_name", "object_type", "config_hash"):
            if row.get(field) != expected_row[field]:
                errors.append(f"row {index}: {field} does not match source export for {key}")
        if str(row.get("review_status") or "").lower() != "complete":
            errors.append(f"row {index}: review_status must be complete for {key}")
        completed_depths = set(re.findall(r"D[1-3]", str(row.get("depth_completed") or ""), re.I))
        if {"D1", "D2", "D3"} - {value.upper() for value in completed_depths}:
            errors.append(f"row {index}: depth_completed must include D1, D2, and D3 for {key}")
        errors.extend(text_quality_errors(row, index))

        available = set(expected_row["available_evidence_anchors"])
        anchors = set(str(value) for value in as_list(row.get("evidence_anchors")))
        if not anchors:
            errors.append(f"row {index}: no source evidence_anchors for {key}")
        for anchor in sorted(anchors - available):
            errors.append(f"row {index}: unknown evidence anchor {anchor!r} for {key}")
        missing_logic = set(expected_row["required_logic_anchors"]) - anchors
        if missing_logic:
            errors.append(
                f"row {index}: {len(missing_logic)} configuration branch(es) lack D3 evidence anchors for {key}"
            )
        errors.extend(validate_branch_reviews(row, expected_row, index))
        errors.extend(validate_code_line_reviews(row, expected_row, index))

        expected_consumer_keys = {
            consumer["consumer_key"] for consumer in expected_row["export_consumers"]
        }
        consumer_keys = set(str(value) for value in as_list(row.get("consumer_evidence_keys")))
        if expected_consumer_keys and not consumer_keys:
            errors.append(f"row {index}: consumer evidence is missing for {key}")
        for consumer_key in sorted(consumer_keys - expected_consumer_keys):
            errors.append(f"row {index}: unknown consumer evidence key {consumer_key!r} for {key}")
        if (
            not expected_consumer_keys
            and "no export-visible consumer" not in str(row.get("consumer_context") or "").lower()
        ):
            warnings.append(
                f"row {index}: {key} has no mapped consumer; state 'no export-visible consumer' when applicable"
            )

        errors.extend(validate_reference_traces(row, expected_row, index))

        if expected_row["sibling_comparison_required"]:
            if word_count(row.get("sibling_comparison")) < 6:
                errors.append(f"row {index}: sibling comparison is required for {key}")
            sibling_anchors = set(
                str(value) for value in as_list(row.get("sibling_evidence_anchors"))
            )
            if len(sibling_anchors) < 2:
                errors.append(
                    f"row {index}: sibling comparison needs at least two anchors for {key}"
                )
            for anchor in sorted(sibling_anchors - available):
                errors.append(f"row {index}: unknown sibling anchor {anchor!r} for {key}")

        if row.get("semantic_status") not in VALID_STATUSES:
            errors.append(f"row {index}: invalid semantic_status for {key}")
        if row.get("confidence") not in VALID_CONFIDENCE:
            errors.append(f"row {index}: invalid confidence for {key}")
        if expected_row.get("detected_vendor") != "Unclassified":
            basis = str(row.get("official_doc_basis") or "")
            candidates = [str(value) for value in expected_row.get("official_doc_candidates", [])]
            if (
                not any(candidate in basis for candidate in candidates)
                and "failed official" not in basis.lower()
            ):
                errors.append(
                    f"row {index}: official_doc_basis must cite a registry URL or document a failed official search for {key}"
                )
        elif word_count(row.get("official_doc_basis")) < 3:
            errors.append(
                f"row {index}: official_doc_basis must state why no vendor contract applies for {key}"
            )
        if row.get("semantic_status") != "Keep":
            for field in (
                "area",
                "problem_type",
                "problem",
                "why_it_matters",
                "expected_clean_state",
                "exact_proposed_action",
                "qa_steps",
                "rollback",
                "priority",
            ):
                if word_count(row.get(field)) < 2:
                    errors.append(f"row {index}: {field} is incomplete for actionable {key}")
            if row.get("resolution_status") not in VALID_RESOLUTIONS:
                errors.append(f"row {index}: resolution_status is invalid for actionable {key}")
            if row.get("execution_readiness") not in VALID_READINESS:
                errors.append(f"row {index}: execution_readiness is invalid for actionable {key}")
            if row.get("risk_class") not in VALID_RISK_CLASSES:
                errors.append(f"row {index}: risk_class is invalid for actionable {key}")

    return errors, warnings


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold_parser = subparsers.add_parser("scaffold", help="Create the source-bound D3 queue")
    scaffold_parser.add_argument("export", type=Path)
    scaffold_parser.add_argument("output", type=Path)
    scaffold_parser.add_argument("--pretty", action="store_true")
    scaffold_parser.add_argument("--reuse-review", type=Path)

    merge_parser = subparsers.add_parser("merge", help="Merge unchanged completed review rows")
    merge_parser.add_argument("export", type=Path)
    merge_parser.add_argument("output", type=Path)
    merge_parser.add_argument("reviews", type=Path, nargs="+")
    merge_parser.add_argument("--pretty", action="store_true")

    validate_parser = subparsers.add_parser("validate", help="Validate a completed D3 review")
    validate_parser.add_argument("export", type=Path)
    validate_parser.add_argument("review", type=Path)

    args = parser.parse_args()
    if args.command == "scaffold":
        payload = scaffold_review(args.export)
        if args.reuse_review:
            previous = json.loads(args.reuse_review.read_text(encoding="utf-8"))
            reuse_completed_rows(payload, previous)
        write_json(args.output, payload, args.pretty)
        print(json.dumps({"output": str(args.output), "rows": len(payload["rows"])}))
        return 0
    if args.command == "merge":
        payload = merge_review_files(args.export, args.reviews)
        write_json(args.output, payload, args.pretty)
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "rows": len(payload["rows"]),
                    "reused": payload.get("reused_completed_rows", 0),
                }
            )
        )
        return 0

    errors, warnings = validate_review(args.export, args.review)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Semantic review: FAIL ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1
    print(f"Semantic review: PASS ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
