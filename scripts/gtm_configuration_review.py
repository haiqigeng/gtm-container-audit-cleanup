#!/usr/bin/env python3
"""Scaffold and validate source-bound GTM configuration-correctness reviews."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from gtm_configuration_facts import (
    build_consumers,
    code_line_facts,
    layer_objects,
    logic_anchors,
    object_consumers,
    object_hash,
    object_key,
    object_type,
    parameter_static_values,
    reference_trace_requirements,
    specific_tokens,
    validate_reference_traces,
)
from gtm_custom_code_extract import extract_export
from gtm_lib import ID_KEYS, container_version, refs, source_descriptor, walk_json_fields
from gtm_review_common import (
    VALID_CONFIDENCE,
    VALID_PRIORITIES,
    VALID_READINESS,
    canonical_review_facts,
    object_consumer_map,
    object_keys,
    specific_text,
    validate_challenge,
    validate_structured_actions,
)
from gtm_shared_facts import build_shared_facts
from gtm_taxonomy import taxonomy_errors
from gtm_vendor_registry import vendor_record

VALID_VERDICTS = {
    "Correct",
    "Issue",
    "Owner decision needed",
    "Container evidence limit",
    "Not applicable",
}
VALID_DISPOSITIONS = {
    "keep",
    "cleanup_operation",
    "owner_decision_needed",
    "container_evidence_limit",
    "not_applicable",
}
VALID_CONTRACT_VERDICTS = {"Compliant", "Non-compliant", "Not applicable", "Unproven"}
VALID_BRANCH_VERDICTS = {"Correct", "Issue", "Unclear", "Metadata", "Not applicable"}
GA4_ECOMMERCE_EVENTS = {
    "add_payment_info",
    "add_shipping_info",
    "add_to_cart",
    "add_to_wishlist",
    "begin_checkout",
    "generate_lead",
    "purchase",
    "refund",
    "remove_from_cart",
    "select_item",
    "select_promotion",
    "view_cart",
    "view_item",
    "view_item_list",
    "view_promotion",
}
CONTRACT_RULE_TERMS = {
    "vendor_identity_and_official_setup": ["vendor", "official", "setup"],
    "event_name": ["event", "name"],
    "action_or_event_name": ["action", "event", "name"],
    "destination_or_server_routing": ["destination", "server", "routing"],
    "destination_or_account_id": ["destination", "account", "id"],
    "event_parameter_names_and_types": ["parameter", "name", "type"],
    "payload_names_shapes_and_types": ["payload", "shape", "type"],
    "consent_and_timing": ["consent", "timing"],
    "deduplication_or_event_id": ["deduplication", "event", "id"],
    "ecommerce_event_contract": ["ecommerce", "event", "items"],
    "item_scope_names_and_types": ["item", "name", "type"],
    "transaction_value_currency_and_quantity": [
        "transaction",
        "value",
        "currency",
        "quantity",
    ],
    "consumer_value_shape_and_type": ["consumer", "value", "shape", "type"],
    "availability_at_consumer_event": ["availability", "consumer", "event"],
    "consent_state_semantics": ["consent", "state", "semantics"],
}
GENERATED_FIELDS = {
    "review_id",
    "object_key",
    "layer",
    "object_id",
    "object_name",
    "object_type",
    "paused",
    "config_hash",
    "source_json_path",
    "source_facts",
    "available_evidence_anchors",
    "required_logic_anchors",
    "required_branch_reviews",
    "code_line_facts",
    "required_code_line_hashes",
    "referenced_variables",
    "reference_trace_requirements",
    "export_consumers",
    "specificity_tokens",
    "detected_vendor",
    "vendor_category",
    "vendor_contexts",
    "official_doc_candidates",
    "required_contract_topics",
    "technical_code_facts",
    "required_technical_findings",
    "shared_behavior_signatures",
    "field_evidence_requirements",
    "field_evidence_paths",
    "effective_consent_route_facts",
    "required_logic_cross_checks",
}
SEMANTIC_TEXT_FIELDS = (
    "purpose",
    "execution_logic",
    "inputs_and_terminal_sources",
    "configured_output_or_side_effect",
    "consumer_contract",
    "consent_and_sequence",
    "correctness_basis",
)
VALID_LOGIC_CHECK_VERDICTS = {"Aligned", "Issue", "Unclear"}
PURPOSE_VERBS = {
    "tag": ("send", "load", "set", "route", "record", "fire", "inject", "configure"),
    "trigger": ("match", "listen", "block", "allow", "fire", "activate"),
    "variable": ("read", "return", "calculate", "map", "format", "extract", "look up"),
    "customTemplate": ("define", "execute", "load", "send", "expose", "permit"),
    "client": ("claim", "parse", "route", "receive"),
    "transformation": ("transform", "allow", "redact", "exclude", "rewrite"),
}
BRANCH_EFFECT_TERMS = {
    "Input": ("read", "pass", "use", "source", "input"),
    "Condition": ("match", "compare", "when", "allow", "block"),
    "Transformation": ("transform", "map", "rewrite", "convert"),
    "Output": ("send", "return", "write", "output"),
    "Routing": ("fire", "block", "route", "trigger"),
    "Consent": ("consent", "grant", "deny", "storage", "permission"),
    "Execution control": ("before", "after", "once", "setup", "teardown", "execute"),
}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def compact_evidence_terms(values: list[Any], limit: int = 10) -> list[str]:
    terms = []
    for value in values:
        text = re.sub(r"\s+", " ", str(value or "")).strip().lower()
        if len(text) < 2 or text in terms:
            continue
        terms.append(text[:160])
    return terms[:limit]


def field_evidence_requirements(shared: dict[str, Any]) -> dict[str, list[str]]:
    contract = shared.get("vendor_event_contract") or {}
    traces = as_list(shared.get("reference_trace_requirements"))
    terminal_values = [
        terminal.get("configured_source")
        for trace in traces
        for terminal in as_list(trace.get("terminal_requirements"))
    ]
    code = shared.get("custom_code_facts") or {}
    expressions = [
        row.get("expression") for row in as_list(code.get("return_expressions"))
    ]
    consumers = as_list(shared.get("consumers"))
    consent = as_list(shared.get("consent_facts"))
    consent_route = shared.get("effective_consent_route") or {}
    audit_context = shared.get("audit_context") or {}
    requirements = {
        "purpose": compact_evidence_terms(
            [
                shared.get("object_name"),
                shared.get("object_type"),
                *as_list(contract.get("events")),
            ]
        ),
        "execution_logic": compact_evidence_terms(
            [
                *as_list(shared.get("firing_trigger_ids")),
                *as_list(shared.get("blocking_trigger_ids")),
                *[
                    part
                    for condition in as_list(shared.get("trigger_conditions"))
                    for part in str(condition).split("|")
                    if part
                ],
            ]
        ),
        "inputs_and_terminal_sources": compact_evidence_terms(
            [*as_list(shared.get("referenced_variables")), *terminal_values]
        ),
        "configured_output_or_side_effect": compact_evidence_terms(
            [
                *as_list(contract.get("events")),
                *as_list(contract.get("destinations")),
                *expressions,
                code.get("returned_value_type"),
                *as_list(code.get("side_effects")),
            ]
        ),
        "consumer_contract": compact_evidence_terms(
            [
                value
                for consumer in consumers
                for value in (consumer.get("consumer_key"), consumer.get("consumer_name"))
            ]
        ),
        "consent_and_sequence": compact_evidence_terms(
            [
                *as_list(shared.get("blocking_trigger_ids")),
                *[item.get("value_preview") for item in consent],
                consent_route.get("consent_status"),
                consent_route.get("effective_control_status"),
                *as_list(consent_route.get("consent_variable_references")),
                *as_list(consent_route.get("server_consent_forwarding_variables")),
                *as_list(consent_route.get("forwarded_consent_purposes")),
                *as_list(consent_route.get("server_routing_hosts")),
            ]
        ),
    }
    identity_terms = compact_evidence_terms(
        [
            shared.get("object_name"),
            shared.get("object_key"),
            shared.get("object_type"),
            shared.get("layer"),
        ]
    )
    if len(requirements["purpose"]) < 2:
        requirements["purpose"] = compact_evidence_terms(
            [*requirements["purpose"], *identity_terms]
        )
    if not requirements["execution_logic"]:
        requirements["execution_logic"] = [
            "not directly event-triggered",
            str(shared.get("object_type") or "configured object"),
        ]
    if not requirements["inputs_and_terminal_sources"]:
        requirements["inputs_and_terminal_sources"] = [
            "no referenced gtm variable",
            str(shared.get("object_type") or "configured source"),
        ]
    if not requirements["configured_output_or_side_effect"]:
        requirements["configured_output_or_side_effect"] = [
            str(shared.get("object_type") or "configured output"),
            str(shared.get("object_name") or "source object"),
        ]
    if not requirements["consumer_contract"]:
        requirements["consumer_contract"] = [
            "no export consumer",
            str(shared.get("object_name") or "source object"),
        ]
    if not requirements["consent_and_sequence"]:
        requirements["consent_and_sequence"] = [
            "no explicit consent control",
            str(shared.get("object_type") or "configured object"),
        ]
    cmp_values = as_list(audit_context.get("cmp"))
    if cmp_values and shared.get("layer") == "tag":
        requirements["consent_and_sequence"] = compact_evidence_terms(
            [*requirements["consent_and_sequence"], *cmp_values]
        )
    requirements["correctness_basis"] = compact_evidence_terms(
        [
            shared.get("object_name"),
            shared.get("object_type"),
            *as_list(contract.get("events")),
            *as_list(contract.get("destinations")),
        ]
    )
    if len(requirements["correctness_basis"]) < 2:
        requirements["correctness_basis"] = compact_evidence_terms(
            [*requirements["correctness_basis"], *identity_terms]
        )
    return requirements


def logic_cross_check_requirements(
    shared: dict[str, Any],
    requirements: dict[str, list[str]],
    paths: dict[str, list[str]],
    has_code: bool,
    has_vendor_contract: bool,
) -> list[dict[str, Any]]:
    definitions = [
        (
            "purpose_output_alignment",
            "Does the configured output or side effect implement the object's stated purpose?",
            ("purpose", "configured_output_or_side_effect"),
        ),
        (
            "execution_scope_alignment",
            "Do firing, blocking, conditions, and sequencing execute only in the intended scope?",
            ("purpose", "execution_logic", "consent_and_sequence"),
        ),
        (
            "input_output_consumer_alignment",
            "Do recursive terminal inputs produce the type and shape consumed downstream?",
            (
                "inputs_and_terminal_sources",
                "configured_output_or_side_effect",
                "consumer_contract",
            ),
        ),
        (
            "consent_sequence_alignment",
            "Is the effective consent and setup or teardown sequence coherent with this object?",
            ("consent_and_sequence", "execution_logic"),
        ),
    ]
    if has_code:
        definitions.append(
            (
                "custom_code_behavior_alignment",
                "Does every custom-code behavior block implement the configured return or side effect safely?",
                ("inputs_and_terminal_sources", "configured_output_or_side_effect"),
            )
        )
    if has_vendor_contract:
        definitions.append(
            (
                "vendor_contract_alignment",
                "Do the exported names, values, types, route, and consent match the official vendor contract?",
                (
                    "configured_output_or_side_effect",
                    "inputs_and_terminal_sources",
                    "consent_and_sequence",
                ),
            )
        )
    rows = []
    for check_key, question, fields in definitions:
        rows.append(
            {
                "check_key": check_key,
                "question": question,
                "required_terms": compact_evidence_terms(
                    [value for field in fields for value in requirements.get(field, [])],
                    20,
                ),
                "allowed_evidence_anchors": list(
                    dict.fromkeys(
                        path for field in fields for path in paths.get(field, [])
                    )
                )[:160],
                "object_key": str(shared.get("object_key") or ""),
            }
        )
    return rows


def field_evidence_paths(shared: dict[str, Any]) -> dict[str, list[str]]:
    facts = as_list(shared.get("source_leaf_facts"))
    all_paths = [str(fact.get("json_path") or "") for fact in facts]

    def matching(*tokens: str, references: bool = False) -> list[str]:
        result = []
        for fact in facts:
            path = str(fact.get("json_path") or "")
            lowered = path.lower()
            if any(token in lowered for token in tokens) or (
                references and as_list(fact.get("referenced_variables"))
            ):
                result.append(path)
        return result

    identity = matching(".name", ".type")
    logic = [
        path
        for path in all_paths
        if not path.lower().endswith(
            (
                ".accountid",
                ".containerid",
                ".fingerprint",
                ".path",
                ".tagid",
                ".triggerid",
                ".variableid",
                ".templateid",
                ".clientid",
                ".transformationid",
                ".name",
            )
        )
    ]
    mapping = {
        "purpose": matching(
            ".name",
            ".type",
            "eventname",
            "action",
            "destination",
            "measurementid",
            "pixel",
        ),
        "execution_logic": matching(
            "firingtriggerid",
            "blockingtriggerid",
            "triggerids",
            "filter",
            "condition",
            "setuptag",
            "teardowntag",
            "tagfiringoption",
        ),
        "inputs_and_terminal_sources": matching(
            "parameter", "javascript", "templatedata", references=True
        ),
        "configured_output_or_side_effect": matching(
            "eventname",
            "destination",
            "measurementid",
            "pixel",
            "html",
            "javascript",
            "templatedata",
            "currency",
            "value",
        ),
        "consumer_contract": matching(".name", ".type", "parameter", references=True),
        "consent_and_sequence": matching(
            "consent",
            "storage",
            "blockingtriggerid",
            "setuptag",
            "teardowntag",
        ),
        "correctness_basis": logic,
    }
    fallback = identity or logic or all_paths
    for field, paths in mapping.items():
        unique = list(dict.fromkeys(paths or fallback))
        mapping[field] = unique[:80]
    return mapping


def vendor_contexts_for_objects(
    cv: dict[str, Any], consumers: dict[str, list[dict[str, str]]]
) -> dict[str, list[dict[str, Any]]]:
    objects = {object_key(layer, obj): obj for layer, _, obj in layer_objects(cv)}
    direct_consumers = {
        key: {
            str(item.get("consumer_key") or "")
            for item in object_consumers(key.split(":", 1)[0], obj, consumers)
        }
        for key, obj in objects.items()
    }
    own_vendors = {}
    for key, obj in objects.items():
        serialized = json.dumps(obj, ensure_ascii=False)
        vendor = vendor_record(serialized)
        if vendor.get("name") == "Unclassified":
            hosts = sorted(
                {
                    urlparse(match).netloc.lower()
                    for match in re.findall(r"https?://[^\s\"'<>\\)]+", serialized, re.I)
                    if urlparse(match).netloc
                }
            )
            layer = key.split(":", 1)[0]
            if hosts or layer == "customTemplate":
                cue = hosts[0] if hosts else str(obj.get("name") or obj.get("type") or key)
                vendor = {
                    "name": f"Unclassified external integration ({cue})",
                    "category": "unknown_vendor",
                    "official_docs": [],
                    "detection_evidence": hosts or [cue],
                }
        own_vendors[key] = vendor
    result: dict[str, list[dict[str, Any]]] = {}
    for source_key in objects:
        queue = [source_key]
        seen: set[str] = set()
        contexts: dict[str, dict[str, Any]] = {}
        while queue:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.add(current)
            vendor = own_vendors.get(current, {})
            name = str(vendor.get("name") or "Unclassified")
            if name != "Unclassified":
                contexts[name] = {
                    "vendor": name,
                    "category": str(vendor.get("category") or "unclassified"),
                    "official_docs": list(vendor.get("official_docs") or []),
                    "research_required": not bool(vendor.get("official_docs")),
                    "detection_evidence": list(vendor.get("detection_evidence") or []),
                    "context_object_keys": sorted(
                        key
                        for key in seen
                        if str(own_vendors.get(key, {}).get("name") or "") == name
                    ),
                }
            queue.extend(sorted(direct_consumers.get(current, set()) - seen))
        result[source_key] = [contexts[name] for name in sorted(contexts)]
    return result


def required_contract_topics(
    cv: dict[str, Any],
    layer: str,
    obj: dict[str, Any],
    contexts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if layer not in {"tag", "variable", "customTemplate", "client", "transformation"}:
        return []
    event_names = {
        value.strip().lower()
        for value in parameter_static_values(cv, obj, "eventName")
        if value.strip()
    }
    obligations: list[dict[str, Any]] = []
    for context in contexts:
        vendor = str(context.get("vendor") or "")
        category = str(context.get("category") or "unclassified")
        topics: list[str]
        if layer == "customTemplate":
            topics = ["template_behavior_and_permissions", "vendor_contract_surface"]
        elif layer == "client":
            topics = ["request_claiming_and_routing", "payload_and_consent_handling"]
        elif layer == "transformation":
            topics = ["transformation_scope", "field_allowlist_or_redaction"]
        elif layer == "variable":
            topics = ["consumer_value_shape_and_type", "availability_at_consumer_event"]
            if re.search(r"consent|storage|ad_user_data|personalization", json.dumps(obj), re.I):
                topics.append("consent_state_semantics")
        elif category == "unknown_vendor":
            topics = [
                "vendor_identity_and_official_setup",
                "action_or_event_name",
                "destination_or_account_id",
                "payload_names_shapes_and_types",
                "consent_and_timing",
            ]
        elif category == "cmp":
            topics = ["consent_mapping", "default_and_update_timing", "downstream_gating"]
        elif vendor == "GA4 / Google tag":
            topics = [
                "event_name",
                "destination_or_server_routing",
                "event_parameter_names_and_types",
                "consent_and_timing",
            ]
            if event_names & GA4_ECOMMERCE_EVENTS:
                topics.extend(
                    [
                        "ecommerce_event_contract",
                        "item_scope_names_and_types",
                        "transaction_value_currency_and_quantity",
                    ]
                )
        elif category in {"media", "affiliate"}:
            topics = [
                "event_name",
                "destination_or_account_id",
                "payload_names_shapes_and_types",
                "consent_and_timing",
                "deduplication_or_event_id",
            ]
        else:
            topics = [
                "action_or_event_name",
                "destination_or_account_id",
                "payload_names_shapes_and_types",
                "consent_and_timing",
            ]
        for topic in topics:
            obligations.append(
                {
                    "topic_key": f"{vendor}:{topic}",
                    "vendor": vendor,
                    "category": category,
                    "topic": topic,
                    "required_rule_terms": CONTRACT_RULE_TERMS.get(
                        topic,
                        [part for part in topic.split("_") if part not in {"and", "or"}],
                    ),
                    "official_doc_candidates": list(context.get("official_docs") or []),
                    "research_required": bool(context.get("research_required")),
                    "detection_evidence": list(context.get("detection_evidence") or []),
                }
            )
    unique = {item["topic_key"]: item for item in obligations}
    return [unique[key] for key in sorted(unique)]


def scaffold_review(
    export_path: Path,
    technical_payload: dict[str, Any] | None = None,
    shared_facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = json.loads(export_path.read_text(encoding="utf-8"))
    cv = container_version(data)
    consumers = build_consumers(cv)
    downstream_vendor_contexts = vendor_contexts_for_objects(cv, consumers)
    technical_by_key = {
        f"{row.get('layer')}:{row.get('object_id')}": row
        for row in as_list((technical_payload or extract_export(export_path)).get("rows"))
    }
    shared_facts = shared_facts or build_shared_facts(
        export_path,
        technical=technical_payload,
    )
    shared_by_key = {
        str(row.get("object_key") or ""): row
        for row in as_list(shared_facts.get("objects"))
    }
    rows: list[dict[str, Any]] = []
    for number, (layer, index, obj) in enumerate(layer_objects(cv), start=1):
        base_path = f"$.containerVersion.{layer}[{index}]"
        current_key = object_key(layer, obj)
        shared = shared_by_key.get(current_key, {})
        facts = as_list(shared.get("source_leaf_facts")) or walk_json_fields(obj, base_path)
        required_paths = logic_anchors(facts)
        required_path_set = set(required_paths)
        lines = code_line_facts(layer, obj)
        vendor = vendor_record(json.dumps(obj, ensure_ascii=False))
        contexts = downstream_vendor_contexts.get(current_key, [])
        topics = required_contract_topics(cv, layer, obj, contexts)
        official_docs = sorted(
            {
                str(url)
                for context in contexts
                for url in as_list(context.get("official_docs"))
                if str(url)
            }
        )
        technical = technical_by_key.get(current_key, {})
        evidence_requirements = field_evidence_requirements(shared)
        evidence_paths = field_evidence_paths(shared)
        required_technical_findings = []
        for category, field in (
            ("health", "technical_code_health_findings"),
            ("security", "technical_code_security_findings"),
            ("optimization", "technical_code_optimization_findings"),
        ):
            for position, statement in enumerate(as_list(technical.get(field)), start=1):
                required_technical_findings.append(
                    {
                        "finding_key": f"{category}:{position}",
                        "category": category,
                        "statement": str(statement),
                    }
                )
        rows.append(
            {
                "review_id": f"CFG-{number:05d}",
                "object_key": current_key,
                "layer": layer,
                "object_id": str(shared.get("object_id") or obj.get(ID_KEYS[layer]) or ""),
                "object_name": str(shared.get("object_name") or obj.get("name") or ""),
                "object_type": str(shared.get("object_type") or object_type(layer, obj)),
                "paused": bool(shared.get("paused")),
                "config_hash": str(shared.get("configuration_hash") or object_hash(obj)),
                "source_json_path": str(shared.get("source_json_path") or base_path),
                "source_facts": facts,
                "available_evidence_anchors": [item["json_path"] for item in facts],
                "required_logic_anchors": required_paths,
                "required_branch_reviews": [
                    fact for fact in facts if fact["json_path"] in required_path_set
                ],
                "code_line_facts": lines,
                "required_code_line_hashes": [item["line_hash"] for item in lines],
                "referenced_variables": as_list(shared.get("referenced_variables"))
                or sorted(refs(obj)),
                "reference_trace_requirements": as_list(
                    shared.get("reference_trace_requirements")
                )
                or reference_trace_requirements(cv, obj),
                "export_consumers": as_list(shared.get("consumers"))
                or object_consumers(layer, obj, consumers),
                "specificity_tokens": as_list(shared.get("specificity_tokens"))
                or specific_tokens(obj),
                "detected_vendor": vendor.get("name"),
                "vendor_category": vendor.get("category"),
                "vendor_contexts": contexts,
                "official_doc_candidates": official_docs,
                "required_contract_topics": topics,
                "technical_code_facts": technical,
                "required_technical_findings": required_technical_findings,
                "shared_behavior_signatures": shared.get("behavior_signatures", {}),
                "field_evidence_requirements": evidence_requirements,
                "field_evidence_paths": evidence_paths,
                "effective_consent_route_facts": shared.get("effective_consent_route", {}),
                "required_logic_cross_checks": logic_cross_check_requirements(
                    shared,
                    evidence_requirements,
                    evidence_paths,
                    bool(lines),
                    bool(topics),
                ),
                "review_status": "pending",
                "purpose": "",
                "execution_logic": "",
                "inputs_and_terminal_sources": "",
                "configured_output_or_side_effect": "",
                "consumer_contract": "",
                "consent_and_sequence": "",
                "correctness_verdict": "",
                "correctness_basis": "",
                "defects": [],
                "contract_checks": [],
                "code_behavior_blocks": [],
                "technical_facts_assessment": "",
                "technical_finding_reviews": [],
                "logic_cross_checks": [],
                "configuration_branch_reviews": [],
                "evidence_anchors": [],
                "consumer_evidence_keys": [],
                "reference_traces": [],
                "related_operational_finding_ids": [],
                "disposition": "",
                "owner_question": "",
                "operation": {},
                "confidence": "",
                "evidence_citations": {},
            }
        )
    return {
        **source_descriptor(export_path),
        "kind": "gtm_configuration_correctness_review",
        "schema_version": 2,
        "shared_facts_sha256": shared_facts["shared_facts_sha256"],
        "context_sha256": shared_facts["context_sha256"],
        "audit_context": shared_facts.get("audit_context", {}),
        "inferred_context": shared_facts.get("inferred_context", {}),
        "provided_context": shared_facts.get("provided_context", {}),
        "provided_context_fields": shared_facts.get("provided_context_fields", []),
        "unresolved_context_questions": shared_facts.get(
            "unresolved_context_questions", []
        ),
        "run_status": "pending",
        "rows": rows,
    }


def semantic_text_errors(row: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for field in SEMANTIC_TEXT_FIELDS:
        if not specific_text(row.get(field), 6):
            errors.append(f"{label}: {field} lacks object-specific analysis")
        requirements = [
            str(value).lower()
            for value in as_list(
                (row.get("field_evidence_requirements") or {}).get(field)
            )
            if str(value).strip()
        ]
        field_text = str(row.get(field) or "").lower()
        required_hits = min(2, len(requirements))
        if required_hits and sum(value in field_text for value in requirements) < required_hits:
            errors.append(
                f"{label}: {field} does not name enough source-derived behavior facts"
            )
    combined = " ".join(
        str(row.get(field) or "") for field in SEMANTIC_TEXT_FIELDS
    ).lower()
    tokens = [str(token).lower() for token in as_list(row.get("specificity_tokens"))]
    required_hits = min(2, len(tokens))
    hits = sum(1 for token in tokens if token and token in combined)
    if required_hits and hits < required_hits:
        errors.append(f"{label}: analysis does not use enough source-specific tokens")
    purpose_text = str(row.get("purpose") or "").lower()
    purpose_verbs = PURPOSE_VERBS.get(str(row.get("layer") or ""), ())
    if purpose_verbs and not any(verb in purpose_text for verb in purpose_verbs):
        errors.append(f"{label}: purpose does not state the concrete {row.get('layer')} action")
    return errors


def citation_errors(row: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    citations = row.get("evidence_citations") or {}
    if set(citations) != set(SEMANTIC_TEXT_FIELDS):
        errors.append(f"{label}: evidence_citations must cover every semantic field")
    available = set(as_list(row.get("available_evidence_anchors")))
    allowed_by_field = row.get("field_evidence_paths") or {}
    for field in SEMANTIC_TEXT_FIELDS:
        field_citations = {str(value) for value in as_list(citations.get(field))}
        allowed = {str(value) for value in as_list(allowed_by_field.get(field))}
        minimum = min(2, len(allowed)) if field == "correctness_basis" else min(1, len(allowed))
        if len(field_citations) < minimum:
            errors.append(f"{label}: {field} lacks source-path citations")
        for anchor in sorted(field_citations - available):
            errors.append(f"{label}: {field} cites unknown source path {anchor!r}")
        for anchor in sorted(field_citations - allowed):
            errors.append(
                f"{label}: {field} cites source path {anchor!r}, which is unrelated to that claim"
            )
    return errors


def review_text_errors(row: dict[str, Any], label: str) -> list[str]:
    return [*semantic_text_errors(row, label), *citation_errors(row, label)]


def branch_required_role(path: str) -> str | None:
    lowered = path.lower()
    if any(token in lowered for token in ("consent", "storage")):
        return "Consent"
    if any(token in lowered for token in ("filter", "condition", "operator")):
        return "Condition"
    if any(token in lowered for token in ("firingtriggerid", "blockingtriggerid", "triggerids")):
        return "Routing"
    if any(token in lowered for token in ("setuptag", "teardowntag", "tagfiringoption")):
        return "Execution control"
    return None


def branch_specificity_tokens(source: dict[str, Any]) -> list[str]:
    ignored = {
        "containerVersion",
        "parameter",
        "value",
        "type",
        "list",
        "map",
        "tag",
        "trigger",
        "variable",
    }
    values = " ".join([str(source.get("json_path") or ""), str(source.get("value_preview") or "")])
    return sorted(
        {
            token.lower()
            for token in re.findall(r"[A-Za-z_][A-Za-z0-9_.:/{}\[\]-]{2,}", values)
            if token not in ignored and not token.isdigit()
        }
    )


def contract_topic_maps(
    row: dict[str, Any], checks: list[dict[str, Any]], label: str
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    required = {
        str(item.get("topic_key") or ""): item
        for item in as_list(row.get("required_contract_topics"))
    }
    supplied = {
        str(item.get("contract_topic") or ""): item
        for item in checks
        if isinstance(item, dict)
    }
    errors = []
    if set(supplied) != set(required):
        errors.append(
            f"{label}: official contract checks must cover every generated topic exactly once"
        )
    return required, supplied, errors


def validate_contract_text(
    check: dict[str, Any], topic: dict[str, Any], prefix: str
) -> list[str]:
    errors: list[str] = []
    for field in ("contract_field", "configured_value", "expected_rule", "source"):
        minimum = 1 if field == "configured_value" else 2
        if not specific_text(check.get(field), minimum):
            errors.append(f"{prefix} has incomplete {field}")
    if topic.get("research_required"):
        if not specific_text(check.get("identified_vendor"), 2):
            errors.append(f"{prefix} must identify the external vendor or integration")
        if not specific_text(check.get("official_source_basis"), 5):
            errors.append(
                f"{prefix} must explain why the cited page is the vendor's official source"
            )
    expected_rule = str(check.get("expected_rule") or "").lower()
    required_terms = [
        str(value).lower() for value in as_list(topic.get("required_rule_terms"))
    ]
    required_hits = min(2, len(required_terms))
    if required_hits and sum(term in expected_rule for term in required_terms) < required_hits:
        errors.append(f"{prefix} expected_rule does not state the topic-specific contract")
    if check.get("verdict") not in VALID_CONTRACT_VERDICTS:
        errors.append(f"{prefix} has invalid verdict")
    return errors


def validate_contract_source(
    check: dict[str, Any], topic: dict[str, Any], prefix: str
) -> list[str]:
    source_url = str(check.get("source") or "")
    official_domains = {
        urlparse(str(url)).netloc.lower()
        for url in as_list(topic.get("official_doc_candidates"))
        if str(url).startswith("https://")
    }
    errors: list[str] = []
    if not source_url.startswith("https://"):
        errors.append(f"{prefix} source must be an official HTTPS documentation URL")
    elif official_domains and urlparse(source_url).netloc.lower() not in official_domains:
        errors.append(f"{prefix} source domain is not registered for the detected vendor")
    if topic.get("research_required") and urlparse(source_url).hostname in {
        "example.com",
        "example.invalid",
        "vendor.example.com",
    }:
        errors.append(f"{prefix} uses a placeholder instead of vendor documentation")
    return errors


def validate_contract_evidence(
    row: dict[str, Any], check: dict[str, Any], available: set[str], prefix: str
) -> tuple[set[str], list[str]]:
    anchors = {str(value) for value in as_list(check.get("evidence_anchors"))}
    errors: list[str] = []
    if not anchors:
        errors.append(f"{prefix} has no configuration evidence")
    errors.extend(
        f"{prefix} references unknown evidence anchor {anchor!r}"
        for anchor in sorted(anchors - available)
    )
    configured_tokens = {
        token
        for fact in as_list(row.get("source_facts"))
        if str(fact.get("json_path") or "") in anchors
        for token in branch_specificity_tokens(fact)
    }
    configured_text = str(check.get("configured_value") or "").lower()
    if configured_tokens and not any(token in configured_text for token in configured_tokens):
        errors.append(f"{prefix} does not state the actual exported configuration value")
    return anchors, errors


def validate_contract_outcomes(
    row: dict[str, Any], noncompliant_anchors: set[str], unproven: bool, label: str
) -> list[str]:
    errors: list[str] = []
    if noncompliant_anchors and row.get("correctness_verdict") != "Issue":
        errors.append(f"{label}: non-compliant vendor contract requires overall Issue verdict")
    defect_anchors = {
        str(anchor)
        for defect in as_list(row.get("defects"))
        for anchor in as_list(defect.get("evidence_anchors"))
    }
    if noncompliant_anchors - defect_anchors:
        errors.append(f"{label}: vendor contract failures must be linked to concrete defects")
    if unproven and row.get("correctness_verdict") not in {
        "Owner decision needed",
        "Container evidence limit",
        "Issue",
    }:
        errors.append(f"{label}: unproven vendor contract cannot be marked Correct")
    return errors


def validate_contract_checks(row: dict[str, Any], label: str) -> list[str]:
    checks = as_list(row.get("contract_checks"))
    required_topics, _supplied_topics, errors = contract_topic_maps(row, checks, label)
    available = set(as_list(row.get("available_evidence_anchors")))
    noncompliant_anchors: set[str] = set()
    unproven = False
    for index, check in enumerate(checks, start=1):
        prefix = f"{label}: contract check {index}"
        topic_key = str(check.get("contract_topic") or "")
        topic = required_topics.get(topic_key)
        if topic is None:
            errors.append(f"{prefix} references an unknown contract topic")
            topic = {}
        errors.extend(validate_contract_text(check, topic, prefix))
        errors.extend(validate_contract_source(check, topic, prefix))
        anchors, evidence_errors = validate_contract_evidence(row, check, available, prefix)
        errors.extend(evidence_errors)
        if check.get("verdict") == "Non-compliant":
            noncompliant_anchors.update(anchors)
        if check.get("verdict") == "Unproven":
            unproven = True
    errors.extend(validate_contract_outcomes(row, noncompliant_anchors, unproven, label))
    return errors


CODE_BLOCK_TEXT_FIELDS = (
    "purpose",
    "inputs",
    "outputs",
    "side_effects",
    "health_assessment",
)
CODE_TOKEN_IGNORES = {
    "function",
    "return",
    "const",
    "false",
    "true",
    "undefined",
    "script",
}


def code_block_source_tokens(
    hashes: list[str], required_facts: dict[str, dict[str, Any]]
) -> set[str]:
    return {
        token.lower()
        for line_hash in hashes
        if line_hash in required_facts
        for token in re.findall(
            r"[A-Za-z_$][A-Za-z0-9_.$:/-]{3,}",
            str(required_facts[line_hash].get("line_preview") or ""),
        )
        if token.lower() not in CODE_TOKEN_IGNORES
    }


def validate_code_block(
    block: dict[str, Any],
    index: int,
    required_facts: dict[str, dict[str, Any]],
    label: str,
) -> tuple[list[str], list[str]]:
    prefix = f"{label}: code block {index}"
    hashes = [str(value) for value in as_list(block.get("line_hashes"))]
    errors: list[str] = []
    if not hashes:
        return hashes, [f"{prefix} covers no code lines"]
    if len(hashes) > 30:
        errors.append(f"{prefix} covers more than 30 nonblank lines")
    errors.extend(
        f"{prefix} references unknown line hash {line_hash!r}"
        for line_hash in hashes
        if line_hash not in required_facts
    )
    errors.extend(
        f"{prefix} has incomplete {field}"
        for field in CODE_BLOCK_TEXT_FIELDS
        if not specific_text(block.get(field), 4)
    )
    block_text = " ".join(
        str(block.get(field) or "") for field in CODE_BLOCK_TEXT_FIELDS
    ).lower()
    source_tokens = code_block_source_tokens(hashes, required_facts)
    if source_tokens and not any(token in block_text for token in source_tokens):
        errors.append(f"{prefix} does not name any identifier or endpoint from its code lines")
    line_numbers = [
        required_facts[value]["line_number"] for value in hashes if value in required_facts
    ]
    if line_numbers and (
        block.get("start_line") != min(line_numbers)
        or block.get("end_line") != max(line_numbers)
    ):
        errors.append(f"{prefix} start/end lines do not match covered hashes")
    return hashes, errors


def validate_code_blocks(row: dict[str, Any], label: str) -> list[str]:
    required_rows = as_list(row.get("code_line_facts"))
    required_facts = {item["line_hash"]: item for item in required_rows}
    required_order = [str(item.get("line_hash") or "") for item in required_rows]
    blocks = as_list(row.get("code_behavior_blocks"))
    if not required_facts:
        return [f"{label}: non-code object must not contain code blocks"] if blocks else []
    errors: list[str] = []
    if not blocks:
        return [f"{label}: custom code requires behavior blocks"]
    expected_minimum = math.ceil(len(required_facts) / 30)
    if len(blocks) < expected_minimum:
        errors.append(
            f"{label}: {len(required_facts)} code lines require at least {expected_minimum} behavior blocks"
        )
    covered: list[str] = []
    for index, block in enumerate(blocks, start=1):
        hashes, block_errors = validate_code_block(block, index, required_facts, label)
        covered.extend(hashes)
        errors.extend(block_errors)
    if covered != required_order:
        errors.append(
            f"{label}: code behavior blocks must cover every exported nonblank line exactly "
            "once and in source order"
        )
    return errors


def validate_logic_cross_checks(row: dict[str, Any], label: str) -> list[str]:
    required = {
        str(item.get("check_key") or ""): item
        for item in as_list(row.get("required_logic_cross_checks"))
    }
    supplied = {
        str(item.get("check_key") or ""): item
        for item in as_list(row.get("logic_cross_checks"))
        if isinstance(item, dict)
    }
    errors: list[str] = []
    if set(supplied) != set(required):
        errors.append(f"{label}: D3 logic checks must cover every required cross-check exactly once")
    issue_anchors: set[str] = set()
    unclear = False
    for check_key, requirement in required.items():
        review = supplied.get(check_key)
        if not review:
            continue
        verdict = review.get("verdict")
        if verdict not in VALID_LOGIC_CHECK_VERDICTS:
            errors.append(f"{label}: D3 logic check {check_key} has an invalid verdict")
        conclusion = str(review.get("conclusion") or "")
        terms = [
            str(value).lower()
            for value in as_list(requirement.get("required_terms"))
            if str(value).strip()
        ]
        if not specific_text(conclusion, 8) or sum(term in conclusion.lower() for term in terms) < min(
            2, len(terms)
        ):
            errors.append(
                f"{label}: D3 logic check {check_key} lacks a source-specific functional conclusion"
            )
        anchors = {str(value) for value in as_list(review.get("evidence_anchors"))}
        allowed = {
            str(value) for value in as_list(requirement.get("allowed_evidence_anchors"))
        }
        if allowed and not anchors:
            errors.append(f"{label}: D3 logic check {check_key} has no configuration evidence")
        if anchors - allowed:
            errors.append(f"{label}: D3 logic check {check_key} cites unrelated evidence")
        if verdict == "Issue":
            issue_anchors.update(anchors)
        elif verdict == "Unclear":
            unclear = True
    defect_anchors = {
        str(anchor)
        for defect in as_list(row.get("defects"))
        for anchor in as_list(defect.get("evidence_anchors"))
    }
    if issue_anchors - defect_anchors:
        errors.append(f"{label}: every failed D3 logic check must be linked to a defect")
    if issue_anchors and row.get("correctness_verdict") != "Issue":
        errors.append(f"{label}: failed D3 logic check requires overall Issue verdict")
    if unclear and row.get("correctness_verdict") not in {
        "Owner decision needed",
        "Container evidence limit",
        "Issue",
    }:
        errors.append(f"{label}: unclear D3 logic requires an unresolved overall verdict")
    return errors


def validate_technical_findings(row: dict[str, Any], label: str) -> list[str]:
    required = {
        str(item.get("finding_key") or ""): item
        for item in as_list(row.get("required_technical_findings"))
    }
    supplied = {
        str(item.get("finding_key") or ""): item
        for item in as_list(row.get("technical_finding_reviews"))
        if isinstance(item, dict)
    }
    errors: list[str] = []
    if set(supplied) != set(required):
        errors.append(f"{label}: static technical findings must be resolved exactly once")
    if row.get("required_code_line_hashes") and not specific_text(
        row.get("technical_facts_assessment"), 6
    ):
        errors.append(f"{label}: custom code lacks a concrete technical assessment")
    confirmed: list[str] = []
    for key, source in required.items():
        review = supplied.get(key)
        if not review:
            continue
        if review.get("source_statement") != source["statement"]:
            errors.append(f"{label}: technical finding {key} source statement changed")
        if review.get("verdict") not in {
            "Confirmed issue",
            "Cleanup opportunity",
            "False positive",
            "Documented exception",
            "Owner decision needed",
        }:
            errors.append(f"{label}: technical finding {key} has invalid verdict")
        if not specific_text(review.get("rationale"), 5):
            errors.append(f"{label}: technical finding {key} lacks concrete rationale")
        fixed_formula = "fixed numbered value slots" in str(source.get("statement") or "").lower()
        if fixed_formula and review.get("verdict") not in {
            "Confirmed issue",
            "Documented exception",
            "Owner decision needed",
        }:
            errors.append(
                f"{label}: fixed-slot business formula must be confirmed, explicitly excepted, "
                "or sent to the owner"
            )
        if fixed_formula and review.get("verdict") == "Documented exception":
            rationale = str(review.get("rationale") or "").lower()
            if not any(
                token in rationale
                for token in ("fixed cardinality", "maximum item", "consumer contract", "business rule")
            ):
                errors.append(
                    f"{label}: fixed-slot exception must name the proven cardinality or consumer rule"
                )
        if review.get("verdict") == "Confirmed issue":
            confirmed.append(key)
    if confirmed and row.get("correctness_verdict") != "Issue":
        errors.append(f"{label}: confirmed technical issues require overall Issue verdict")
    return errors


def validate_defects(row: dict[str, Any], label: str) -> list[str]:
    defects = as_list(row.get("defects"))
    verdict = row.get("correctness_verdict")
    if verdict == "Issue" and not defects:
        return [f"{label}: Issue verdict requires at least one concrete defect"]
    if verdict == "Correct" and defects:
        return [f"{label}: Correct verdict cannot contain defects"]
    errors: list[str] = []
    available = set(as_list(row.get("available_evidence_anchors")))
    line_hashes = set(as_list(row.get("required_code_line_hashes")))
    seen: set[str] = set()
    for index, defect in enumerate(defects, start=1):
        defect_id = str(defect.get("defect_id") or "")
        prefix = f"{label}: defect {index}"
        if not defect_id or defect_id in seen:
            errors.append(f"{prefix} requires a unique defect_id")
        seen.add(defect_id)
        for field in ("statement", "configured_effect", "expected_behavior"):
            if not specific_text(defect.get(field), 5):
                errors.append(f"{prefix} has incomplete {field}")
        anchors = {str(value) for value in as_list(defect.get("evidence_anchors"))}
        code_evidence = {str(value) for value in as_list(defect.get("code_line_hashes"))}
        if not anchors and not code_evidence:
            errors.append(f"{prefix} has no source evidence")
        for anchor in sorted(anchors - available):
            errors.append(f"{prefix} references unknown anchor {anchor!r}")
        for line_hash in sorted(code_evidence - line_hashes):
            errors.append(f"{prefix} references unknown code line hash {line_hash!r}")
    return errors


VALID_LOGIC_ROLES = {
    "Input",
    "Condition",
    "Transformation",
    "Output",
    "Routing",
    "Consent",
    "Execution control",
    "Metadata",
    "Not applicable",
}


def validate_configuration_branch(
    path: str, source: dict[str, Any], review: dict[str, Any], label: str
) -> tuple[str, list[str]]:
    errors: list[str] = []
    if review.get("value_hash") != source["value_hash"]:
        errors.append(f"{label}: branch value hash differs from source at {path}")
    logic_role = str(review.get("logic_role") or "")
    if logic_role not in VALID_LOGIC_ROLES:
        errors.append(f"{label}: invalid logic role at {path}")
    required_role = branch_required_role(path)
    if required_role and logic_role != required_role:
        errors.append(f"{label}: branch {path} must be classified as {required_role}")
    for field in ("interpretation", "configured_effect"):
        if not specific_text(review.get(field), 5):
            errors.append(f"{label}: {field} is not concrete at {path}")
    branch_text = " ".join(
        str(review.get(field) or "") for field in ("interpretation", "configured_effect")
    ).lower()
    tokens = branch_specificity_tokens(source)
    if tokens and not any(token in branch_text for token in tokens):
        errors.append(
            f"{label}: branch explanation does not identify its configured value at {path}"
        )
    effect_terms = BRANCH_EFFECT_TERMS.get(logic_role, ())
    configured_effect = str(review.get("configured_effect") or "").lower()
    if effect_terms and not any(term in configured_effect for term in effect_terms):
        errors.append(
            f"{label}: configured effect at {path} does not explain its {logic_role} behavior"
        )
    verdict = str(review.get("correctness") or "")
    if verdict not in VALID_BRANCH_VERDICTS:
        errors.append(f"{label}: invalid branch correctness at {path}")
    return verdict, errors


def branch_outcome_errors(
    row: dict[str, Any], issue_paths: set[str], unclear_paths: set[str], label: str
) -> list[str]:
    errors: list[str] = []
    if issue_paths and row.get("correctness_verdict") != "Issue":
        errors.append(f"{label}: branch issues require an overall Issue verdict")
    if unclear_paths and row.get("correctness_verdict") not in {
        "Owner decision needed",
        "Container evidence limit",
        "Issue",
    }:
        errors.append(f"{label}: unclear branches require an unresolved overall verdict")
    defect_anchors = {
        str(anchor)
        for defect in as_list(row.get("defects"))
        for anchor in as_list(defect.get("evidence_anchors"))
    }
    if issue_paths - defect_anchors:
        errors.append(f"{label}: each branch issue must be linked to a concrete defect")
    return errors


def validate_configuration_branches(
    row: dict[str, Any], expected: dict[str, Any], label: str
) -> list[str]:
    required = {
        item["json_path"]: item for item in as_list(expected.get("required_branch_reviews"))
    }
    supplied = {
        str(item.get("json_path") or ""): item
        for item in as_list(row.get("configuration_branch_reviews"))
        if isinstance(item, dict)
    }
    errors: list[str] = []
    if set(supplied) != set(required):
        errors.append(f"{label}: branch reviews must cover every logic leaf exactly once")
    issue_paths: set[str] = set()
    unclear_paths: set[str] = set()
    for path, source in required.items():
        review = supplied.get(path)
        if not review:
            continue
        verdict, branch_errors = validate_configuration_branch(path, source, review, label)
        errors.extend(branch_errors)
        if verdict == "Issue":
            issue_paths.add(path)
        elif verdict == "Unclear":
            unclear_paths.add(path)
    errors.extend(branch_outcome_errors(row, issue_paths, unclear_paths, label))
    return errors


def validate_operation(
    row: dict[str, Any],
    valid_keys: set[str],
    label: str,
    expected_consumers: dict[str, set[str]],
) -> list[str]:
    operation = row.get("operation")
    if row.get("disposition") != "cleanup_operation":
        return (
            [f"{label}: non-operation disposition cannot contain operation data"]
            if operation
            else []
        )
    if not isinstance(operation, dict):
        return [f"{label}: cleanup disposition requires a structured operation"]
    errors: list[str] = []
    if not str(operation.get("operation_key") or "").strip():
        errors.append(f"{label}: operation_key is incomplete")
    for field in (
        "title",
        "area",
        "problem_type",
        "problem",
        "why_it_matters",
        "expected_clean_state",
        "exact_proposed_action",
        "qa_steps",
        "rollback",
    ):
        minimum = 2 if field in {"area", "problem_type"} else 3
        if not specific_text(operation.get(field), minimum):
            errors.append(f"{label}: operation field {field} is incomplete")
    if operation.get("priority") not in VALID_PRIORITIES:
        errors.append(f"{label}: operation priority is invalid")
    if operation.get("confidence") not in VALID_CONFIDENCE:
        errors.append(f"{label}: operation confidence is invalid")
    if operation.get("execution_readiness") not in VALID_READINESS:
        errors.append(f"{label}: operation execution_readiness is invalid")
    errors.extend(taxonomy_errors(operation.get("area"), operation.get("problem_type"), label))
    flattened = {**operation, "deterministic_action_candidate": ""}
    errors.extend(
        validate_structured_actions(
            flattened,
            valid_keys,
            label,
            expected_consumers,
        )
    )
    errors.extend(validate_challenge(flattened, label))
    return errors


def validate_review_identity(
    supplied: dict[str, Any],
    expected: dict[str, Any],
    expected_context: dict[str, Any],
    source_sha256: str,
) -> list[str]:
    checks = (
        ("source_sha256", source_sha256, "source_sha256 does not match the export"),
        ("kind", "gtm_configuration_correctness_review", "kind is invalid"),
        ("schema_version", 2, "schema_version must be 2"),
        (
            "shared_facts_sha256",
            expected.get("shared_facts_sha256"),
            "does not use the canonical shared facts",
        ),
        (
            "context_sha256",
            expected.get("context_sha256"),
            "does not use the canonical audit context",
        ),
        (
            "audit_context",
            expected.get("audit_context"),
            "audit_context differs from the canonical context",
        ),
        (
            "inferred_context",
            expected_context.get("inferred_context"),
            "inferred_context differs from source inference",
        ),
        (
            "provided_context",
            expected_context.get("provided_context"),
            "provided_context differs from its locked provenance",
        ),
        (
            "provided_context_fields",
            expected_context.get("provided_fields"),
            "provided context fields changed",
        ),
        (
            "unresolved_context_questions",
            expected.get("unresolved_context_questions"),
            "unresolved context questions changed",
        ),
        ("run_status", "complete", "run_status must be complete"),
    )
    return [
        f"configuration review {message}"
        for field, expected_value, message in checks
        if supplied.get(field) != expected_value
    ]


def configuration_row_sets(
    supplied: dict[str, Any], expected: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    expected_by_key = {row["object_key"]: row for row in expected["rows"]}
    supplied_by_key = {
        str(row.get("object_key") or ""): row for row in as_list(supplied.get("rows"))
    }
    errors: list[str] = []
    missing = sorted(set(expected_by_key) - set(supplied_by_key))
    unknown = sorted(set(supplied_by_key) - set(expected_by_key))
    if missing:
        errors.append("missing configuration rows: " + ", ".join(missing))
    if unknown:
        errors.append("unknown configuration rows: " + ", ".join(unknown))
    return expected_by_key, supplied_by_key, errors


def validate_row_identity_and_evidence(
    row: dict[str, Any], expected_row: dict[str, Any], label: str
) -> list[str]:
    errors = [
        f"{label}: generated field {field} differs from source"
        for field in GENERATED_FIELDS
        if row.get(field) != expected_row.get(field)
    ]
    for field, valid, message in (
        ("review_status", {"complete"}, "review_status must be complete"),
        ("correctness_verdict", VALID_VERDICTS, "correctness_verdict is invalid"),
        ("disposition", VALID_DISPOSITIONS, "disposition is invalid"),
        ("confidence", VALID_CONFIDENCE, "confidence is invalid"),
    ):
        if row.get(field) not in valid:
            errors.append(f"{label}: {message}")
    errors.extend(review_text_errors(row, label))
    available = set(expected_row["available_evidence_anchors"])
    anchors = {str(value) for value in as_list(row.get("evidence_anchors"))}
    if not anchors:
        errors.append(f"{label}: no source evidence anchors")
    errors.extend(
        f"{label}: unknown evidence anchor {anchor!r}"
        for anchor in sorted(anchors - available)
    )
    missing_logic = set(expected_row["required_logic_anchors"]) - anchors
    if missing_logic:
        errors.append(f"{label}: {len(missing_logic)} logic branches lack evidence")
    expected_consumers = {
        str(item.get("consumer_key") or "") for item in expected_row["export_consumers"]
    }
    supplied_consumers = {
        str(value) for value in as_list(row.get("consumer_evidence_keys"))
    }
    if supplied_consumers != expected_consumers:
        errors.append(f"{label}: consumer evidence must exactly match the source graph")
    return errors


def validate_row_outcome(row: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    if row.get("disposition") == "owner_decision_needed" and not specific_text(
        row.get("owner_question"), 5
    ):
        errors.append(f"{label}: owner decision requires one precise question")
    if row.get("correctness_verdict") == "Issue" and row.get("disposition") not in {
        "cleanup_operation",
        "owner_decision_needed",
        "container_evidence_limit",
    }:
        errors.append(f"{label}: Issue verdict has incompatible disposition")
    return errors


def validate_configuration_row(
    row: dict[str, Any],
    expected_row: dict[str, Any],
    valid_keys: set[str],
    source_consumer_map: dict[str, set[str]],
) -> list[str]:
    label = f"configuration {expected_row['object_key']}"
    errors = validate_row_identity_and_evidence(row, expected_row, label)
    validators = (
        lambda: validate_reference_traces(row, expected_row, label),
        lambda: validate_configuration_branches(row, expected_row, label),
        lambda: validate_contract_checks(row, label),
        lambda: validate_code_blocks(row, label),
        lambda: validate_technical_findings(row, label),
        lambda: validate_logic_cross_checks(row, label),
        lambda: validate_defects(row, label),
        lambda: validate_operation(row, valid_keys, label, source_consumer_map),
        lambda: validate_row_outcome(row, label),
    )
    for validator in validators:
        errors.extend(validator())
    return errors


def validate_review(export_path: Path, review_path: Path) -> tuple[list[str], list[str]]:
    supplied = json.loads(review_path.read_text(encoding="utf-8"))
    expected_context, expected_shared = canonical_review_facts(export_path, supplied)
    expected = scaffold_review(export_path, shared_facts=expected_shared)
    errors: list[str] = []
    warnings: list[str] = []
    descriptor = source_descriptor(export_path)
    valid_keys = object_keys(export_path)
    source_consumer_map = object_consumer_map(export_path)
    errors.extend(
        validate_review_identity(
            supplied, expected, expected_context, descriptor["source_sha256"]
        )
    )
    expected_by_key, supplied_by_key, set_errors = configuration_row_sets(
        supplied, expected
    )
    errors.extend(set_errors)
    for key, expected_row in expected_by_key.items():
        row = supplied_by_key.get(key)
        if not row:
            continue
        errors.extend(
            validate_configuration_row(
                row, expected_row, valid_keys, source_consumer_map
            )
        )
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
    scaffold = subparsers.add_parser("scaffold")
    scaffold.add_argument("export", type=Path)
    scaffold.add_argument("output", type=Path)
    scaffold.add_argument("--pretty", action="store_true")
    validate = subparsers.add_parser("validate")
    validate.add_argument("export", type=Path)
    validate.add_argument("review", type=Path)
    args = parser.parse_args()

    if args.command == "scaffold":
        payload = scaffold_review(args.export)
        write_json(args.output, payload, args.pretty)
        print(json.dumps({"output": str(args.output), "objects": len(payload["rows"])}))
        return 0

    errors, warnings = validate_review(args.export, args.review)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "pass", "review": str(args.review)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
