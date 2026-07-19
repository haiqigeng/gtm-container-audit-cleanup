#!/usr/bin/env python3
"""Scaffold and validate GTM business-family and target-architecture review."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from gtm_lib import (
    container_version,
    custom_template_id,
    is_system_trigger_reference,
    refs,
    source_descriptor,
    stable_hash,
    trigger_group_members,
)
from gtm_relationships import (
    object_records,
    relationship_candidates,
    tag_business_event_key,
    tag_contract,
)
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

VALID_RELATIONSHIP_VERDICTS = {
    "Exact duplicate",
    "Functional overlap",
    "Consolidation candidate",
    "Intentional variant",
    "Complementary",
    "Conflict",
    "Unrelated",
    "Owner decision needed",
    "Container evidence limit",
}
ACTIONABLE_VERDICTS = {
    "Exact duplicate",
    "Functional overlap",
    "Consolidation candidate",
    "Conflict",
}
VALID_DISPOSITIONS = {
    "keep",
    "cleanup_operation",
    "owner_decision_needed",
    "container_evidence_limit",
    "not_applicable",
}
OPEN_DISCOVERY_METHODS = [
    "semantic_name_and_business_term_variants",
    "normalized_condition_and_route_variants",
    "terminal_source_formula_and_output_overlap",
    "consumer_destination_and_event_overlap",
    "consent_sequence_and_server_route_conflicts",
    "funnel_question_market_and_product_families",
]


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def compact_terms(values: list[Any], limit: int = 40) -> list[str]:
    terms: list[str] = []
    for value in values:
        text = " ".join(str(value or "").split()).strip().lower()
        if len(text) < 2 or text in terms:
            continue
        terms.append(text[:160])
    return terms[:limit]


def object_evidence_terms(shared: dict[str, Any]) -> list[str]:
    contract = shared.get("vendor_event_contract") or {}
    consent = shared.get("effective_consent_route") or {}
    return compact_terms(
        [
            shared.get("object_name"),
            shared.get("object_key"),
            shared.get("object_type"),
            *as_list(shared.get("referenced_variables")),
            *as_list(shared.get("firing_trigger_ids")),
            *as_list(shared.get("blocking_trigger_ids")),
            *as_list(shared.get("business_scope_tokens")),
            *as_list(contract.get("events")),
            *as_list(contract.get("destinations")),
            *as_list(consent.get("consent_variable_references")),
            *as_list(consent.get("server_consent_forwarding_variables")),
            *as_list(consent.get("forwarded_consent_purposes")),
            *as_list(consent.get("server_routing_hosts")),
            consent.get("consent_status"),
            consent.get("effective_control_status"),
        ]
    )


def terms_for_keys(
    keys: list[str], shared_by_key: dict[str, dict[str, Any]]
) -> list[str]:
    return compact_terms(
        [
            term
            for key in keys
            for term in object_evidence_terms(shared_by_key.get(key, {}))
        ],
        120,
    )


def field_evidence_requirements(
    keys: list[str], shared_by_key: dict[str, dict[str, Any]]
) -> dict[str, list[str]]:
    identities = compact_terms(
        [
            shared_by_key.get(key, {}).get("object_name") or key
            for key in keys
        ]
    )
    execution = compact_terms(
        [
            value
            for key in keys
            for value in (
                *as_list(shared_by_key.get(key, {}).get("firing_trigger_ids")),
                *as_list(shared_by_key.get(key, {}).get("blocking_trigger_ids")),
                *as_list(shared_by_key.get(key, {}).get("trigger_group_member_ids")),
                *[
                    part
                    for condition in as_list(
                        shared_by_key.get(key, {}).get("trigger_conditions")
                    )
                    for part in str(condition).split("|")
                    if part
                ],
            )
        ]
    )
    payload = compact_terms(
        [
            value
            for key in keys
            for value in (
                *as_list(shared_by_key.get(key, {}).get("referenced_variables")),
                *as_list(
                    (shared_by_key.get(key, {}).get("vendor_event_contract") or {}).get(
                        "events"
                    )
                ),
                *as_list(
                    (shared_by_key.get(key, {}).get("vendor_event_contract") or {}).get(
                        "destinations"
                    )
                ),
            )
        ]
    )
    consent = compact_terms(
        [
            value
            for key in keys
            for value in (
                *as_list(shared_by_key.get(key, {}).get("blocking_trigger_ids")),
                *as_list(
                    (
                        shared_by_key.get(key, {}).get("effective_consent_route") or {}
                    ).get("consent_variable_references")
                ),
                *as_list(
                    (
                        shared_by_key.get(key, {}).get("effective_consent_route") or {}
                    ).get("server_consent_forwarding_variables")
                ),
                *as_list(
                    (
                        shared_by_key.get(key, {}).get("effective_consent_route") or {}
                    ).get("forwarded_consent_purposes")
                ),
                *as_list(
                    (
                        shared_by_key.get(key, {}).get("effective_consent_route") or {}
                    ).get("server_routing_hosts")
                ),
                (
                    shared_by_key.get(key, {}).get("effective_consent_route") or {}
                ).get("consent_status"),
                (
                    shared_by_key.get(key, {}).get("effective_consent_route") or {}
                ).get("effective_control_status"),
            )
        ]
    )
    all_terms = terms_for_keys(keys, shared_by_key)

    def complete(values: list[str]) -> list[str]:
        return compact_terms([*values, *identities, *all_terms])

    return {
        "business_action": complete([*payload, *identities]),
        "family_purpose": complete([*payload, *identities]),
        "execution_path_summary": complete([*execution, *identities]),
        "payload_coherence": complete([*payload, *identities]),
        "consent_and_sequence_coherence": complete([*consent, *execution, *identities]),
        "necessity_and_ownership": complete(identities),
        "analyst_rationale": complete([*payload, *execution, *identities]),
        "target_architecture": complete(identities),
        "architecture_effect": complete([*payload, *execution, *identities]),
    }


def family_key(record: dict[str, Any]) -> str:
    business_key = tag_business_event_key(record)
    if business_key:
        return "event:" + business_key
    triggers = sorted(
        str(value)
        for value in as_list(record["object"].get("firingTriggerId"))
        if not is_system_trigger_reference(str(value))
    )
    if triggers:
        return "route:" + ",".join(triggers)
    contract = tag_contract(record)
    vendor = str(contract.get("vendor") or "unclassified")
    if record["layer"] == "client":
        return "server-client:" + vendor + ":" + record["object_type"]
    if record["layer"] == "transformation":
        return "server-transformation:" + vendor + ":" + record["object_type"]
    return "vendor-type:" + vendor + ":" + record["object_type"]


def family_label(key: str) -> str:
    if key.startswith("event:"):
        try:
            events = json.loads(key.split(":", 1)[1])
            return " / ".join(str(value) for value in events)
        except json.JSONDecodeError:
            pass
    return key.replace(":", " - ")


def dependency_graph(
    cv: dict[str, Any], records: dict[str, list[dict[str, Any]]]
) -> tuple[dict[str, list[dict[str, str]]], dict[str, dict[str, Any]]]:
    by_key = {
        record["object_key"]: record
        for layer_records in records.values()
        for record in layer_records
    }
    variables = {
        str(record["object"].get("name") or ""): record["object_key"]
        for record in records.get("variable", [])
    }
    triggers = {
        str(record["object_id"]): record["object_key"] for record in records.get("trigger", [])
    }
    tags = {
        str(record["object"].get("name") or ""): record["object_key"]
        for record in records.get("tag", [])
    }
    templates = {
        str(record["object_id"]): record["object_key"]
        for record in records.get("customTemplate", [])
    }
    graph: dict[str, list[dict[str, str]]] = defaultdict(list)
    for key, record in by_key.items():
        obj = record["object"]
        for reference in sorted(refs(obj)):
            target = variables.get(reference)
            if target:
                graph[key].append(
                    {"from_object_key": key, "to_object_key": target, "relation": "variable"}
                )
        if record["layer"] == "tag":
            for relation in ("firingTriggerId", "blockingTriggerId"):
                for trigger_id in as_list(obj.get(relation)):
                    target = triggers.get(str(trigger_id))
                    if target:
                        graph[key].append(
                            {
                                "from_object_key": key,
                                "to_object_key": target,
                                "relation": relation,
                            }
                        )
            for relation in ("setupTag", "teardownTag"):
                for reference in as_list(obj.get(relation)):
                    target = tags.get(str(reference.get("tagName") or ""))
                    if target:
                        graph[key].append(
                            {
                                "from_object_key": key,
                                "to_object_key": target,
                                "relation": relation,
                            }
                        )
        if record["layer"] == "trigger":
            for trigger_id in trigger_group_members(obj):
                target = triggers.get(str(trigger_id))
                if target:
                    graph[key].append(
                        {
                            "from_object_key": key,
                            "to_object_key": target,
                            "relation": "trigger_group_member",
                        }
                    )
        template_id = custom_template_id(obj)
        if template_id and template_id in templates:
            graph[key].append(
                {
                    "from_object_key": key,
                    "to_object_key": templates[template_id],
                    "relation": "custom_template",
                }
            )
    return dict(graph), by_key


def family_chain(
    member_keys: list[str],
    graph: dict[str, list[dict[str, str]]],
) -> tuple[list[str], list[dict[str, str]]]:
    visited = set(member_keys)
    edges: list[dict[str, str]] = []
    queue = list(member_keys)
    while queue:
        current = queue.pop(0)
        for edge in graph.get(current, []):
            if edge not in edges:
                edges.append(edge)
            target = edge["to_object_key"]
            if target not in visited:
                visited.add(target)
                queue.append(target)
    return sorted(visited), sorted(
        edges,
        key=lambda row: (row["from_object_key"], row["relation"], row["to_object_key"]),
    )


def scaffold_families(cv: dict[str, Any]) -> list[dict[str, Any]]:
    records = object_records(cv)
    roots = records.get("tag", []) + records.get("client", []) + records.get("transformation", [])
    graph, records_by_key = dependency_graph(cv, records)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in roots:
        groups[family_key(record)].append(record)
    rows: list[dict[str, Any]] = []
    for number, (key, members) in enumerate(sorted(groups.items()), start=1):
        members = sorted(members, key=lambda item: item["object_key"])
        member_keys = [item["object_key"] for item in members]
        chain_keys, chain_edges = family_chain(member_keys, graph)
        chain_records = [records_by_key[key] for key in chain_keys if key in records_by_key]
        rows.append(
            {
                "family_id": f"FAM-{number:04d}",
                "family_key": key,
                "family_label": family_label(key),
                "member_object_keys": member_keys,
                "member_object_names": [item["object_name"] for item in members],
                "member_config_hashes": {
                    item["object_key"]: item["config_hash"] for item in members
                },
                "member_source_paths": {
                    item["object_key"]: item["source_json_path"] for item in members
                },
                "available_member_evidence_anchors": {
                    item["object_key"]: item["evidence_anchors"] for item in members
                },
                "member_paused_status": {
                    item["object_key"]: bool(item["object"].get("paused")) for item in members
                },
                "chain_object_keys": chain_keys,
                "chain_object_names": {
                    item["object_key"]: item["object_name"] for item in chain_records
                },
                "chain_config_hashes": {
                    item["object_key"]: item["config_hash"] for item in chain_records
                },
                "chain_source_paths": {
                    item["object_key"]: item["source_json_path"] for item in chain_records
                },
                "available_chain_evidence_anchors": {
                    item["object_key"]: item["evidence_anchors"] for item in chain_records
                },
                "chain_paused_status": {
                    item["object_key"]: bool(item["object"].get("paused"))
                    if item["layer"] == "tag"
                    else False
                    for item in chain_records
                },
                "chain_edges": chain_edges,
                "chain_specificity_tokens": sorted(
                    {token for item in chain_records for token in item["specificity_tokens"]}
                )[:120],
                "review_status": "pending",
                "business_action": "",
                "family_purpose": "",
                "member_assessments": [],
                "chain_assessments": [],
                "execution_path_summary": "",
                "payload_coherence": "",
                "consent_and_sequence_coherence": "",
                "necessity_and_ownership": "",
                "relationship_verdict": "",
                "analyst_rationale": "",
                "target_architecture": "",
                "disposition": "",
                "owner_question": "",
                "operations": [],
                "confidence": "",
            }
        )
    return rows


def scaffold_comparisons(cv: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for candidate in relationship_candidates(cv):
        rows.append(
            {
                **candidate,
                "review_status": "pending",
                "member_assessments": [],
                "relationship_verdict": "",
                "analyst_rationale": "",
                "architecture_effect": "",
                "disposition": "",
                "owner_question": "",
                "operations": [],
                "confidence": "",
            }
        )
    return rows


def scaffold_review(
    export_path: Path,
    shared_facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = json.loads(export_path.read_text(encoding="utf-8"))
    cv = container_version(data)
    shared_facts = shared_facts or build_shared_facts(export_path)
    shared_by_key = {
        str(row.get("object_key") or ""): row
        for row in as_list(shared_facts.get("objects"))
    }
    families = scaffold_families(cv)
    for family in families:
        family["member_evidence_terms"] = {
            key: object_evidence_terms(shared_by_key.get(key, {}))
            for key in family["member_object_keys"]
        }
        family["chain_evidence_terms"] = {
            key: object_evidence_terms(shared_by_key.get(key, {}))
            for key in family["chain_object_keys"]
        }
        family["field_evidence_requirements"] = field_evidence_requirements(
            family["chain_object_keys"], shared_by_key
        )
        family["member_behavior_signatures"] = {
            key: shared_by_key.get(key, {}).get("behavior_signatures", {})
            for key in family["member_object_keys"]
        }
        family["chain_behavior_signatures"] = {
            key: shared_by_key.get(key, {}).get("behavior_signatures", {})
            for key in family["chain_object_keys"]
        }
    comparisons = scaffold_comparisons(cv)
    for comparison in comparisons:
        comparison["candidate_evidence_terms"] = {
            key: object_evidence_terms(shared_by_key.get(key, {}))
            for key in comparison["candidate_object_keys"]
        }
        comparison["field_evidence_requirements"] = field_evidence_requirements(
            comparison["candidate_object_keys"], shared_by_key
        )
        comparison["candidate_behavior_signatures"] = {
            key: shared_by_key.get(key, {}).get("behavior_signatures", {})
            for key in comparison["candidate_object_keys"]
        }
    all_record_keys = sorted(shared_by_key)
    method_coverage = []
    for method in OPEN_DISCOVERY_METHODS:
        method_comparisons = [
            comparison
            for comparison in comparisons
            if method in as_list(comparison.get("discovery_methods"))
        ]
        candidate_keys = sorted(
            {
                str(key)
                for comparison in method_comparisons
                for key in as_list(comparison.get("candidate_object_keys"))
            }
        )
        method_coverage.append(
            {
                "method": method,
                "scan_status": "deterministic_complete",
                "comparison_ids": sorted(
                    str(comparison.get("comparison_id") or "")
                    for comparison in method_comparisons
                ),
                "candidate_object_keys": candidate_keys,
                "review_scope_object_keys": all_record_keys,
                "source_scope_sha256": stable_hash(
                    {
                        "method": method,
                        "objects": {
                            key: shared_by_key.get(key, {}).get("behavior_signatures", {})
                            for key in all_record_keys
                        },
                    },
                    32,
                ),
            }
        )
    return {
        **source_descriptor(export_path),
        "kind": "gtm_business_architecture_review",
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
        "families": families,
        "comparisons": comparisons,
        "discovery_method_coverage": method_coverage,
        "discovery_contract": (
            "All deterministic comparisons are mandatory. Add source-grounded DISC-* rows "
            "when complete-chain review reveals a relationship outside that candidate set."
        ),
        "open_discovery_attestation": {
            "review_status": "pending",
            "reviewed_object_keys": [],
            "discovered_comparison_ids": [],
            "zero_discovery_rationale": "",
            "method_reviews": [
                {
                    **coverage,
                    "review_status": "pending",
                    "reviewed_comparison_ids": [],
                    "reviewed_object_keys": [],
                    "additional_discovery_ids": [],
                    "conclusion": "",
                }
                for coverage in method_coverage
            ],
        },
    }


def validate_member_assessments(
    assessments: list[dict[str, Any]],
    member_keys: list[str],
    available_by_key: dict[str, list[str]],
    paused_by_key: dict[str, bool],
    evidence_terms_by_key: dict[str, list[str]],
    label: str,
) -> list[str]:
    errors: list[str] = []
    by_key = {
        str(item.get("object_key") or ""): item for item in assessments if isinstance(item, dict)
    }
    if set(by_key) != set(member_keys):
        errors.append(f"{label}: member assessments must cover every member exactly once")
    for key in member_keys:
        assessment = by_key.get(key)
        if not assessment:
            continue
        for field in ("configured_role", "necessity", "distinguishing_configuration"):
            if not specific_text(assessment.get(field), 5):
                errors.append(f"{label}: {key} has incomplete {field}")
                continue
            terms = [
                str(value).lower()
                for value in as_list(evidence_terms_by_key.get(key))
                if str(value).strip()
            ]
            required_hits = min(
                2 if field in {"configured_role", "distinguishing_configuration"} else 1,
                len(terms),
            )
            text = str(assessment.get(field) or "").lower()
            if required_hits and sum(term in text for term in terms) < required_hits:
                errors.append(f"{label}: {key} {field} is not tied to source facts")
        expected_status = "paused" if paused_by_key.get(key, False) else "active"
        if assessment.get("status") != expected_status:
            errors.append(f"{label}: {key} status must be {expected_status}")
        anchors = {str(value) for value in as_list(assessment.get("evidence_anchors"))}
        available = {str(value) for value in available_by_key.get(key, [])}
        if not anchors:
            errors.append(f"{label}: {key} has no evidence anchors")
        for anchor in sorted(anchors - available):
            errors.append(f"{label}: {key} references unknown evidence anchor {anchor!r}")
    return errors


def validate_field_evidence_text(
    row: dict[str, Any], fields: tuple[str, ...], label: str
) -> list[str]:
    errors: list[str] = []
    requirements = row.get("field_evidence_requirements") or {}
    for field in fields:
        if not specific_text(row.get(field), 6):
            errors.append(f"{label}: {field} lacks a concrete assessment")
            continue
        terms = [
            str(value).lower()
            for value in as_list(requirements.get(field))
            if str(value).strip()
        ]
        required_hits = min(2, len(terms))
        text = str(row.get(field) or "").lower()
        if required_hits and sum(term in text for term in terms) < required_hits:
            errors.append(f"{label}: {field} is not tied to source facts")
    return errors


def validate_operation(
    operation: dict[str, Any],
    valid_keys: set[str],
    label: str,
    expected_consumers: dict[str, set[str]],
) -> list[str]:
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


def validate_decision(
    row: dict[str, Any],
    valid_keys: set[str],
    label: str,
    expected_consumers: dict[str, set[str]],
) -> list[str]:
    errors: list[str] = []
    verdict = row.get("relationship_verdict")
    disposition = row.get("disposition")
    if verdict not in VALID_RELATIONSHIP_VERDICTS:
        errors.append(f"{label}: relationship_verdict is invalid")
    if disposition not in VALID_DISPOSITIONS:
        errors.append(f"{label}: disposition is invalid")
    if row.get("confidence") not in VALID_CONFIDENCE:
        errors.append(f"{label}: confidence is invalid")
    operations = as_list(row.get("operations"))
    if verdict in ACTIONABLE_VERDICTS and disposition != "cleanup_operation":
        errors.append(f"{label}: actionable verdict requires cleanup_operation disposition")
    if disposition == "cleanup_operation" and not operations:
        errors.append(f"{label}: cleanup disposition requires at least one operation")
    if disposition != "cleanup_operation" and operations:
        errors.append(f"{label}: non-operation disposition cannot contain operations")
    if disposition == "owner_decision_needed" and not specific_text(row.get("owner_question"), 5):
        errors.append(f"{label}: owner decision requires one precise question")
    for index, operation in enumerate(operations, start=1):
        errors.extend(
            validate_operation(
                operation,
                valid_keys,
                f"{label} operation {index}",
                expected_consumers,
            )
        )
        if verdict in {"Exact duplicate", "Consolidation candidate"}:
            if not str(operation.get("canonical_object_key") or ""):
                errors.append(f"{label} operation {index}: consolidation lacks canonical object")
            if not as_list(operation.get("deletions")):
                errors.append(f"{label} operation {index}: consolidation lacks deletion action")
    return errors


def validate_discovered_comparison(
    row: dict[str, Any],
    records_by_key: dict[str, dict[str, Any]],
    valid_keys: set[str],
    expected_consumers: dict[str, set[str]],
) -> list[str]:
    comparison_id = str(row.get("comparison_id") or "")
    label = f"comparison {comparison_id or '<missing>'}"
    errors: list[str] = []
    if not comparison_id.startswith("DISC-"):
        errors.append(f"{label}: analyst-discovered comparison ID must start with DISC-")
    if row.get("comparison_origin") != "analyst_discovered":
        errors.append(f"{label}: unknown comparison must declare analyst_discovered origin")
    candidate_keys = [str(value) for value in as_list(row.get("candidate_object_keys"))]
    if len(candidate_keys) < 2 or len(set(candidate_keys)) != len(candidate_keys):
        errors.append(f"{label}: discovery requires at least two unique source objects")
    unknown = sorted(set(candidate_keys) - set(records_by_key))
    if unknown:
        errors.append(f"{label}: discovery references unknown objects {unknown!r}")
    basis = " ".join(str(value) for value in as_list(row.get("candidate_basis")))
    if not specific_text(basis, 6):
        errors.append(f"{label}: discovery basis must explain the source-grounded relationship")
    if row.get("review_status") != "complete":
        errors.append(f"{label}: review_status must be complete")
    available = {
        key: records_by_key[key]["evidence_anchors"]
        for key in candidate_keys
        if key in records_by_key
    }
    paused = {
        key: bool(records_by_key[key]["paused"])
        for key in candidate_keys
        if key in records_by_key
    }
    evidence_terms = {
        key: compact_terms(
            [
                records_by_key[key].get("object_name"),
                records_by_key[key].get("object_key"),
                records_by_key[key].get("object_type"),
                *as_list(records_by_key[key].get("specificity_tokens")),
            ]
        )
        for key in candidate_keys
        if key in records_by_key
    }
    comparison_terms = compact_terms(
        [term for key in candidate_keys for term in evidence_terms.get(key, [])]
    )
    validation_row = {
        **row,
        "field_evidence_requirements": {
            "analyst_rationale": comparison_terms,
            "architecture_effect": comparison_terms,
        },
    }
    errors.extend(
        validate_field_evidence_text(
            validation_row,
            ("analyst_rationale", "architecture_effect"),
            label,
        )
    )
    errors.extend(
        validate_member_assessments(
            as_list(row.get("member_assessments")),
            candidate_keys,
            available,
            paused,
            evidence_terms,
            label,
        )
    )
    errors.extend(validate_decision(row, valid_keys, label, expected_consumers))
    return errors


def validate_review_identity(
    supplied: dict[str, Any],
    expected: dict[str, Any],
    expected_context: dict[str, Any],
    source_sha256: str,
) -> list[str]:
    checks = (
        ("source_sha256", source_sha256, "source_sha256 does not match the export"),
        ("kind", "gtm_business_architecture_review", "kind is invalid"),
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
        f"architecture review {message}"
        for field, expected_value, message in checks
        if supplied.get(field) != expected_value
    ]


def family_source_specificity_errors(
    row: dict[str, Any], expected_row: dict[str, Any], label: str
) -> list[str]:
    family_fields = (
        "business_action",
        "family_purpose",
        "execution_path_summary",
        "payload_coherence",
        "consent_and_sequence_coherence",
        "necessity_and_ownership",
        "analyst_rationale",
        "target_architecture",
    )
    errors = validate_field_evidence_text(row, family_fields, label)
    family_text = " ".join(str(row.get(field) or "") for field in family_fields).lower()
    source_tokens = [
        str(token).lower() for token in as_list(expected_row["chain_specificity_tokens"])
    ]
    required_hits = min(3, len(source_tokens))
    if required_hits and sum(token in family_text for token in source_tokens) < required_hits:
        errors.append(f"{label}: assessment does not name enough chain-specific source facts")
    return errors


def validate_families(
    supplied: dict[str, Any],
    expected: dict[str, Any],
    valid_keys: set[str],
    expected_consumers: dict[str, set[str]],
) -> list[str]:
    errors: list[str] = []
    expected_rows = {row["family_id"]: row for row in expected["families"]}
    supplied_rows = {
        str(row.get("family_id") or ""): row for row in as_list(supplied.get("families"))
    }
    if set(expected_rows) != set(supplied_rows):
        errors.append("architecture family set does not match the source export")
    generated_fields = (
        "family_key",
        "family_label",
        "member_object_keys",
        "member_object_names",
        "member_config_hashes",
        "member_source_paths",
        "available_member_evidence_anchors",
        "member_paused_status",
        "member_behavior_signatures",
        "member_evidence_terms",
        "chain_object_keys",
        "chain_object_names",
        "chain_config_hashes",
        "chain_source_paths",
        "available_chain_evidence_anchors",
        "chain_paused_status",
        "chain_behavior_signatures",
        "chain_evidence_terms",
        "chain_edges",
        "chain_specificity_tokens",
        "field_evidence_requirements",
    )
    for family_id, expected_row in expected_rows.items():
        row = supplied_rows.get(family_id)
        if not row:
            continue
        label = f"family {family_id}"
        errors.extend(
            f"{label}: generated field {field} differs from source"
            for field in generated_fields
            if row.get(field) != expected_row.get(field)
        )
        if row.get("review_status") != "complete":
            errors.append(f"{label}: review_status must be complete")
        errors.extend(family_source_specificity_errors(row, expected_row, label))
        errors.extend(
            validate_member_assessments(
                as_list(row.get("member_assessments")),
                expected_row["member_object_keys"],
                expected_row["available_member_evidence_anchors"],
                expected_row["member_paused_status"],
                expected_row["member_evidence_terms"],
                label,
            )
        )
        errors.extend(
            validate_member_assessments(
                as_list(row.get("chain_assessments")),
                expected_row["chain_object_keys"],
                expected_row["available_chain_evidence_anchors"],
                expected_row["chain_paused_status"],
                expected_row["chain_evidence_terms"],
                f"{label} chain",
            )
        )
        errors.extend(validate_decision(row, valid_keys, label, expected_consumers))
    return errors


GENERATED_COMPARISON_FIELDS = {
    "comparison_id",
    "comparison_origin",
    "layer",
    "candidate_object_keys",
    "candidate_object_ids",
    "candidate_object_names",
    "candidate_object_types",
    "candidate_config_hashes",
    "candidate_source_paths",
    "candidate_paused_status",
    "available_member_evidence_anchors",
    "candidate_specificity_tokens",
    "candidate_behavior_signatures",
    "candidate_evidence_terms",
    "field_evidence_requirements",
    "comparison_types",
    "comparison_type",
    "candidate_basis",
    "similarity_score",
    "required_comparison_dimensions",
    "discovery_methods",
}


def deterministic_comparison_policy_errors(
    row: dict[str, Any], expected_row: dict[str, Any], label: str
) -> list[str]:
    errors: list[str] = []
    comparison_types = as_list(expected_row.get("comparison_types"))
    verdict = row.get("relationship_verdict")
    disposition = row.get("disposition")
    if "exact_configuration" in comparison_types:
        if verdict not in {"Exact duplicate", "Owner decision needed"}:
            errors.append(
                f"{label}: identical source configuration must be resolved as an exact "
                "duplicate or a visible owner decision"
            )
        if verdict == "Owner decision needed" and disposition != "owner_decision_needed":
            errors.append(f"{label}: unresolved exact duplicate requires owner_decision_needed")
    if "different_consent_purposes_same_logic" in comparison_types:
        if verdict not in {"Conflict", "Owner decision needed"}:
            errors.append(
                f"{label}: different consent purposes with the same exported logic must "
                "be treated as a conflict or a visible owner decision"
            )
        if verdict == "Owner decision needed" and disposition != "owner_decision_needed":
            errors.append(
                f"{label}: unresolved consent-purpose collision requires owner decision"
            )
    return errors


def validate_deterministic_comparisons(
    supplied_rows: dict[str, dict[str, Any]],
    expected_rows: dict[str, dict[str, Any]],
    valid_keys: set[str],
    expected_consumers: dict[str, set[str]],
) -> list[str]:
    errors: list[str] = []
    for comparison_id, expected_row in expected_rows.items():
        row = supplied_rows.get(comparison_id)
        if not row:
            continue
        label = f"comparison {comparison_id}"
        errors.extend(
            f"{label}: generated field {field} differs from source"
            for field in GENERATED_COMPARISON_FIELDS
            if row.get(field) != expected_row.get(field)
        )
        if row.get("review_status") != "complete":
            errors.append(f"{label}: review_status must be complete")
        errors.extend(
            validate_field_evidence_text(
                row, ("analyst_rationale", "architecture_effect"), label
            )
        )
        errors.extend(
            validate_member_assessments(
                as_list(row.get("member_assessments")),
                expected_row["candidate_object_keys"],
                expected_row["available_member_evidence_anchors"],
                expected_row["candidate_paused_status"],
                expected_row["candidate_evidence_terms"],
                label,
            )
        )
        errors.extend(validate_decision(row, valid_keys, label, expected_consumers))
        errors.extend(deterministic_comparison_policy_errors(row, expected_row, label))
    return errors


def comparison_sets(
    supplied: dict[str, Any], expected: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[str], list[str]]:
    expected_rows = {row["comparison_id"]: row for row in expected["comparisons"]}
    supplied_list = as_list(supplied.get("comparisons"))
    supplied_rows = {
        str(row.get("comparison_id") or ""): row for row in supplied_list
    }
    errors = []
    if len(supplied_rows) != len(supplied_list):
        errors.append("architecture comparison IDs must be unique and nonblank")
    missing = sorted(set(expected_rows) - set(supplied_rows))
    if missing:
        errors.append(
            "architecture review is missing deterministic comparisons: " + ", ".join(missing)
        )
    discovered_ids = sorted(set(supplied_rows) - set(expected_rows))
    return expected_rows, supplied_rows, discovered_ids, errors


def validate_method_reviews(
    attestation: dict[str, Any],
    expected: dict[str, Any],
    records_by_key: dict[str, dict[str, Any]],
    discovered_ids: list[str],
) -> list[str]:
    errors: list[str] = []
    expected_rows = {
        str(row.get("method") or ""): row
        for row in as_list(expected.get("open_discovery_attestation", {}).get("method_reviews"))
    }
    supplied_rows = {
        str(row.get("method") or ""): row
        for row in as_list(attestation.get("method_reviews"))
        if isinstance(row, dict)
    }
    if set(supplied_rows) != set(expected_rows):
        errors.append("open discovery method reviews must cover every method exactly once")
    locked_fields = (
        "method",
        "scan_status",
        "comparison_ids",
        "candidate_object_keys",
        "review_scope_object_keys",
        "source_scope_sha256",
    )
    for method, expected_row in expected_rows.items():
        review = supplied_rows.get(method)
        if not review:
            continue
        errors.extend(
            f"open discovery method {method}: generated field {field} changed"
            for field in locked_fields
            if review.get(field) != expected_row.get(field)
        )
        if review.get("review_status") != "complete":
            errors.append(f"open discovery method {method}: review is incomplete")
        if set(as_list(review.get("reviewed_comparison_ids"))) != set(
            as_list(expected_row.get("comparison_ids"))
        ):
            errors.append(f"open discovery method {method}: not every candidate was reviewed")
        if set(as_list(review.get("reviewed_object_keys"))) != set(records_by_key):
            errors.append(f"open discovery method {method}: source object coverage is incomplete")
        additional = {str(value) for value in as_list(review.get("additional_discovery_ids"))}
        if not additional <= set(discovered_ids):
            errors.append(f"open discovery method {method}: unknown added comparison ID")
        conclusion = str(review.get("conclusion") or "")
        method_terms = compact_terms(
            [
                *(expected_row.get("comparison_ids") or []),
                *[
                    records_by_key[key].get("object_name")
                    for key in as_list(expected_row.get("candidate_object_keys"))
                    if key in records_by_key
                ],
                str(len(records_by_key)),
                method.replace("_", " "),
            ]
        )
        if not specific_text(conclusion, 8) or not any(
            term in conclusion.lower() for term in method_terms
        ):
            errors.append(
                f"open discovery method {method}: conclusion is not tied to its source scan"
            )
    return errors


def validate_zero_discovery(
    attestation: dict[str, Any], records_by_key: dict[str, dict[str, Any]]
) -> list[str]:
    rationale = str(attestation.get("zero_discovery_rationale") or "")
    source_terms = compact_terms(
        [
            value
            for record in records_by_key.values()
            for value in (
                record.get("object_name"),
                record.get("object_key"),
                *as_list(record.get("specificity_tokens")),
            )
        ]
    )
    if specific_text(rationale, 8) and sum(
        term in rationale.lower() for term in source_terms
    ) >= min(2, len(source_terms)):
        return []
    return ["zero open discoveries require a source-specific rationale"]


def validate_discovery(
    supplied: dict[str, Any],
    expected: dict[str, Any],
    supplied_comparisons: dict[str, dict[str, Any]],
    discovered_ids: list[str],
    records_by_key: dict[str, dict[str, Any]],
    valid_keys: set[str],
    expected_consumers: dict[str, set[str]],
) -> list[str]:
    errors: list[str] = []
    for comparison_id in discovered_ids:
        errors.extend(
            validate_discovered_comparison(
                supplied_comparisons[comparison_id],
                records_by_key,
                valid_keys,
                expected_consumers,
            )
        )
    attestation = supplied.get("open_discovery_attestation") or {}
    if attestation.get("review_status") != "complete":
        errors.append("open relationship discovery attestation must be complete")
    if set(as_list(attestation.get("reviewed_object_keys"))) != set(records_by_key):
        errors.append("open relationship discovery did not review every source object")
    if set(as_list(attestation.get("discovered_comparison_ids"))) != set(discovered_ids):
        errors.append("open relationship discovery IDs do not match added comparisons")
    if supplied.get("discovery_method_coverage") != expected.get("discovery_method_coverage"):
        errors.append("deterministic discovery method coverage differs from source")
    errors.extend(
        validate_method_reviews(attestation, expected, records_by_key, discovered_ids)
    )
    if not discovered_ids:
        errors.extend(validate_zero_discovery(attestation, records_by_key))
    return errors


def validate_review(export_path: Path, review_path: Path) -> tuple[list[str], list[str]]:
    supplied = json.loads(review_path.read_text(encoding="utf-8"))
    expected_context, expected_shared = canonical_review_facts(export_path, supplied)
    expected = scaffold_review(export_path, expected_shared)
    errors: list[str] = []
    warnings: list[str] = []
    descriptor = source_descriptor(export_path)
    valid_keys = object_keys(export_path)
    expected_consumers = object_consumer_map(export_path)
    cv = container_version(json.loads(export_path.read_text(encoding="utf-8")))
    source_records = object_records(cv)
    records_by_key = {
        record["object_key"]: record
        for layer_records in source_records.values()
        for record in layer_records
    }
    errors.extend(
        validate_review_identity(
            supplied, expected, expected_context, descriptor["source_sha256"]
        )
    )
    errors.extend(validate_families(supplied, expected, valid_keys, expected_consumers))
    expected_comparisons, supplied_comparisons, discovered_ids, set_errors = (
        comparison_sets(supplied, expected)
    )
    errors.extend(set_errors)
    errors.extend(
        validate_deterministic_comparisons(
            supplied_comparisons,
            expected_comparisons,
            valid_keys,
            expected_consumers,
        )
    )
    errors.extend(
        validate_discovery(
            supplied,
            expected,
            supplied_comparisons,
            discovered_ids,
            records_by_key,
            valid_keys,
            expected_consumers,
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
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "families": len(payload["families"]),
                    "comparisons": len(payload["comparisons"]),
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
        return 1
    print(json.dumps({"status": "pass", "review": str(args.review)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
