#!/usr/bin/env python3
"""Build immutable deterministic GTM facts shared by all verdict engines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from gtm_configuration_facts import (
    build_consumers,
    object_consumers,
    reference_trace_requirements,
)
from gtm_consent_model import consent_values, tag_consent_route
from gtm_context_model import build_context_model
from gtm_custom_code_extract import extract_export
from gtm_lib import (
    ID_KEYS,
    comparable,
    container_version,
    object_id,
    refs,
    source_descriptor,
    stable_hash,
    trigger_group_members,
    walk_json_fields,
)
from gtm_relationships import (
    business_scope_tokens,
    object_records,
    tag_contract,
    trigger_conditions,
)
from gtm_source_model import build_model


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def source_leaf_facts(obj: dict[str, Any], source_path: str) -> list[dict[str, Any]]:
    return [
        {
            "json_path": fact["json_path"],
            "value_hash": fact["value_hash"],
            "value_type": fact["value_type"],
            "value_preview": fact.get("value_preview"),
            "referenced_variables": fact["referenced_variables"],
        }
        for fact in walk_json_fields(obj, source_path)
    ]


def behavior_signatures(
    record: dict[str, Any],
    trace_requirements: list[dict[str, Any]],
    technical: dict[str, Any],
    consent: dict[str, Any],
) -> dict[str, str]:
    obj = record["object"]
    route = {
        "firing": sorted(str(value) for value in as_list(obj.get("firingTriggerId"))),
        "blocking": sorted(str(value) for value in as_list(obj.get("blockingTriggerId"))),
        "setup": as_list(obj.get("setupTag")),
        "teardown": as_list(obj.get("teardownTag")),
    }
    terminals = [
        {
            "reference": row["reference"],
            "states": row["terminal_states"],
            "terminals": row["terminal_requirements"],
        }
        for row in trace_requirements
    ]
    formulas = {
        "return_expressions": technical.get("return_expressions", []),
        "fixed_slot_groups": technical.get("fixed_slot_groups", []),
        "returned_value_type": technical.get("returned_value_type", ""),
    }
    return {
        "configuration": record["config_hash"],
        "execution_route": stable_hash(route),
        "trigger_logic": stable_hash(trigger_conditions(obj)),
        "terminal_sources": stable_hash(terminals),
        "formula": stable_hash(formulas),
        "consent": stable_hash(consent),
        "business_scope": stable_hash(sorted(business_scope_tokens(record))),
    }


def shared_content_hash(payload: dict[str, Any]) -> str:
    return stable_hash(
        {
            "source_sha256": payload.get("source_sha256"),
            "context_sha256": payload.get("context_sha256"),
            "audit_context": payload.get("audit_context", {}),
            "inferred_context": payload.get("inferred_context", {}),
            "provided_context": payload.get("provided_context", {}),
            "provided_context_fields": payload.get("provided_context_fields", []),
            "unresolved_context_questions": payload.get(
                "unresolved_context_questions", []
            ),
            "objects": payload.get("objects", []),
            "integrity_findings": payload.get("integrity_findings", []),
        },
        32,
    )


def build_shared_facts(
    export_path: Path,
    context: dict[str, Any] | None = None,
    technical: dict[str, Any] | None = None,
    navigation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = json.loads(export_path.read_text(encoding="utf-8"))
    cv = container_version(data)
    context = context or build_context_model(export_path)
    technical = technical or extract_export(export_path)
    navigation = navigation or build_model(export_path)
    consumers = build_consumers(cv)
    records = object_records(cv)
    semantic_by_key = {
        record["object_key"]: record
        for layer_records in records.values()
        for record in layer_records
    }
    technical_by_key = {
        f"{row['layer']}:{row['object_id']}": row for row in as_list(technical.get("rows"))
    }
    variables = as_list(cv.get("variable"))
    object_rows: list[dict[str, Any]] = []
    for layer, id_key in ID_KEYS.items():
        for index, obj in enumerate(as_list(cv.get(layer))):
            key = f"{layer}:{object_id(obj, id_key)}"
            source_path = f"$.containerVersion.{layer}[{index}]"
            record = semantic_by_key.get(
                key,
                {
                    "layer": layer,
                    "index": index,
                    "object": obj,
                    "object_key": key,
                    "object_id": object_id(obj, id_key),
                    "object_name": str(obj.get("name") or ""),
                    "object_type": str(obj.get("type") or layer),
                    "paused": bool(obj.get("paused")) if layer == "tag" else False,
                    "config_hash": stable_hash(comparable(obj)),
                    "source_json_path": source_path,
                    "evidence_anchors": [
                        fact["json_path"] for fact in walk_json_fields(obj, source_path)
                    ],
                    "specificity_tokens": [],
                },
            )
            obj = record["object"]
            key = record["object_key"]
            technical_row = technical_by_key.get(key, {})
            traces = reference_trace_requirements(cv, obj) if layer in records else []
            consent_values_for_object = consent_values(obj, record["source_json_path"])
            consent = (
                tag_consent_route(
                    obj,
                    record["source_json_path"],
                    variables=variables,
                )
                if record["layer"] == "tag"
                else {"consent_source_values": consent_values_for_object}
            )
            contract = tag_contract(record) if record["layer"] == "tag" else {}
            formula_facts = {
                field: technical_row.get(field)
                for field in (
                    "logical_line_count",
                    "return_expressions",
                    "fixed_slot_groups",
                    "fixed_slot_aggregation",
                    "returned_value_type",
                    "ast_branch_count",
                    "ast_return_count",
                    "side_effects",
                )
                if field in technical_row
            }
            row = {
                "object_key": key,
                "layer": record["layer"],
                "object_id": record["object_id"],
                "object_name": record["object_name"],
                "object_type": record["object_type"],
                "paused": record["paused"],
                "source_json_path": record["source_json_path"],
                "configuration_hash": record["config_hash"],
                "source_leaf_facts": source_leaf_facts(obj, record["source_json_path"]),
                "referenced_variables": sorted(refs(obj)),
                "consumers": (
                    object_consumers(record["layer"], obj, consumers)
                    if layer in records
                    else []
                ),
                "firing_trigger_ids": sorted(
                    str(value) for value in as_list(obj.get("firingTriggerId"))
                ),
                "blocking_trigger_ids": sorted(
                    str(value) for value in as_list(obj.get("blockingTriggerId"))
                ),
                "trigger_group_member_ids": sorted(trigger_group_members(obj)),
                "setup_tags": as_list(obj.get("setupTag")),
                "teardown_tags": as_list(obj.get("teardownTag")),
                "trigger_conditions": trigger_conditions(obj),
                "business_scope_tokens": sorted(business_scope_tokens(record)),
                "specificity_tokens": as_list(record.get("specificity_tokens")),
                "vendor_event_contract": contract,
                "reference_trace_requirements": traces,
                "consent_facts": consent_values_for_object,
                "effective_consent_route": consent,
                "custom_code_facts": formula_facts,
            }
            row["behavior_signatures"] = behavior_signatures(
                record,
                traces,
                technical_row,
                consent,
            )
            object_rows.append(row)

    payload = {
        **source_descriptor(export_path),
        "kind": "gtm_shared_deterministic_facts",
        "schema_version": 1,
        "context_sha256": context["context_sha256"],
        "audit_context": context.get("context", {}),
        "inferred_context": context.get("inferred_context", {}),
        "provided_context": context.get("provided_context", {}),
        "provided_context_fields": context.get("provided_fields", []),
        "unresolved_context_questions": context.get("unresolved_questions", []),
        "fact_contract": (
            "Immutable source-derived facts shared across verdict engines; no cleanup verdicts."
        ),
        "counts": {
            "objects": len(object_rows),
            "source_leaves": sum(len(row["source_leaf_facts"]) for row in object_rows),
            "unresolved_edges": navigation["counts"]["unresolved_edges"],
            "custom_code_objects": navigation["counts"]["custom_code_objects"],
        },
        "integrity_findings": navigation["unresolved_edges"],
        "coverage_gate": (
            "pass_with_integrity_findings"
            if navigation["counts"]["unresolved_edges"]
            else "pass"
        ),
        "objects": sorted(object_rows, key=lambda row: row["object_key"]),
    }
    payload["shared_facts_sha256"] = shared_content_hash(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--context", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    context = (
        json.loads(args.context.read_text(encoding="utf-8")) if args.context else None
    )
    result = build_shared_facts(args.export, context=context)
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
