from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_skill_package import build as build_skill_bundle  # noqa: E402
from check_release import check_repository_layout, git_ls_files  # noqa: E402
from gtm_architecture_review import (  # noqa: E402
    scaffold_review as scaffold_architecture,
)
from gtm_architecture_review import (  # noqa: E402
    validate_review as validate_architecture,
)
from gtm_audit_gate_check import validate_workbook  # noqa: E402
from gtm_audit_package_build import build_package  # noqa: E402
from gtm_baseline_audit import audit_export  # noqa: E402
from gtm_change_log_build import build_change_log  # noqa: E402
from gtm_configuration_review import (  # noqa: E402
    scaffold_review as scaffold_configuration,
)
from gtm_configuration_review import (  # noqa: E402
    validate_review as validate_configuration,
)
from gtm_consent_model import tag_consent_route  # noqa: E402
from gtm_context_model import build_context_model  # noqa: E402
from gtm_custom_code_extract import extract_export  # noqa: E402
from gtm_diff_operations import operations as diff_operations  # noqa: E402
from gtm_future_state_check import apply_operations, check_future_state  # noqa: E402
from gtm_human_rows import build_rows  # noqa: E402
from gtm_lib import container_version  # noqa: E402
from gtm_operation_compile import compile_operations, source_object_catalog  # noqa: E402
from gtm_operational_review import (  # noqa: E402
    scaffold_review as scaffold_operational,
)
from gtm_operational_review import (  # noqa: E402
    validate_review as validate_operational,
)
from gtm_privacy import (  # noqa: E402
    privacy_findings,
    redact_text,
    sanitize_url,
    spreadsheet_safe_text,
)
from gtm_privacy_scan import scan_xlsx  # noqa: E402
from gtm_relationships import object_records, relationship_candidates  # noqa: E402
from gtm_review_common import (  # noqa: E402
    object_consumer_map,
    object_keys,
    validate_structured_actions,
)
from gtm_review_shards import merge_review, split_review  # noqa: E402
from gtm_shared_facts import build_shared_facts  # noqa: E402
from gtm_source_model import build_model  # noqa: E402
from gtm_three_run_gate import run_gate  # noqa: E402
from gtm_validate_artifact import missing_references  # noqa: E402
from gtm_vendor_registry import (  # noqa: E402
    load_registry,
    official_url_error,
    validate_registry,
    vendor_record,
)
from gtm_workbook_build import (  # noqa: E402
    CANONICAL_SHEETS,
    MAX_CELL_TEXT,
    add_table,
    build_workbook,
)


def condition(operator: str, left: str, right: str) -> dict:
    return {
        "type": operator,
        "parameter": [
            {"type": "TEMPLATE", "key": "arg0", "value": left},
            {"type": "TEMPLATE", "key": "arg1", "value": right},
        ],
    }


def sample_export() -> dict:
    return {
        "exportFormatVersion": 2,
        "containerVersion": {
            "accountId": "100",
            "containerId": "200",
            "containerVersionId": "1",
            "container": {"publicId": "GTM-TEST", "usageContext": ["WEB"]},
            "tag": [
                {
                    "tagId": "1",
                    "name": "GA4 - Purchase - All",
                    "type": "gaawe",
                    "parameter": [
                        {"type": "TEMPLATE", "key": "eventName", "value": "purchase"},
                        {"type": "TEMPLATE", "key": "measurementId", "value": "G-TEST123"},
                        {
                            "type": "MAP",
                            "key": "eventParameters",
                            "map": [
                                {
                                    "type": "TEMPLATE",
                                    "key": "value",
                                    "value": "{{DLV - Value}}",
                                }
                            ],
                        },
                    ],
                    "firingTriggerId": ["10"],
                    "blockingTriggerId": ["13"],
                    "setupTag": [{"tagName": "Utility - Consent Defaults"}],
                },
                {
                    "tagId": "2",
                    "name": "Meta - Purchase - All",
                    "type": "html",
                    "parameter": [
                        {
                            "type": "TEMPLATE",
                            "key": "html",
                            "value": (
                                "<script>\n"
                                "var items = {{DLV - Items}} || [];\n"
                                "fbq('track', 'Purchase', {contents: items});\n"
                                "</script>"
                            ),
                        }
                    ],
                    "firingTriggerId": ["12"],
                },
                {
                    "tagId": "3",
                    "name": "Utility - Consent Defaults",
                    "type": "html",
                    "parameter": [
                        {
                            "type": "TEMPLATE",
                            "key": "html",
                            "value": "<script>\nwindow.consentDefault = 'denied';\n</script>",
                        }
                    ],
                    "parentFolderId": "101",
                },
                {
                    "tagId": "4",
                    "name": "Paused - Helper Consumer",
                    "type": "html",
                    "paused": True,
                    "parameter": [
                        {
                            "type": "TEMPLATE",
                            "key": "html",
                            "value": "<script>void({{CJS - Paused Only}});</script>",
                        }
                    ],
                    "firingTriggerId": ["10"],
                },
            ],
            "trigger": [
                {
                    "triggerId": "10",
                    "name": "Purchase",
                    "type": "CUSTOM_EVENT",
                    "customEventFilter": [condition("EQUALS", "{{_event}}", "purchase")],
                },
                {
                    "triggerId": "11",
                    "name": "Purchase copy",
                    "type": "CUSTOM_EVENT",
                    "customEventFilter": [condition("EQUALS", "{{_event}}", "purchase")],
                },
                {
                    "triggerId": "12",
                    "name": "TG - Purchase only",
                    "type": "TRIGGER_GROUP",
                    "parameter": [
                        {
                            "type": "LIST",
                            "key": "triggerIds",
                            "list": [{"type": "TEMPLATE", "value": "10"}],
                        }
                    ],
                },
                {
                    "triggerId": "13",
                    "name": "Block - Page view",
                    "type": "CUSTOM_EVENT",
                    "customEventFilter": [condition("EQUALS", "{{_event}}", "page_view")],
                },
                {
                    "triggerId": "14",
                    "name": "Click - Invalid regex",
                    "type": "LINK_CLICK",
                    "filter": [condition("MATCH_REGEX", "{{Click URL}}", "(")],
                },
                {
                    "triggerId": "15",
                    "name": "Funnel question 1",
                    "type": "CUSTOM_EVENT",
                    "customEventFilter": [condition("EQUALS", "{{_event}}", "funnel_question_1")],
                },
                {
                    "triggerId": "16",
                    "name": "Funnel step impression Q1",
                    "type": "CUSTOM_EVENT",
                    "customEventFilter": [
                        condition("EQUALS", "{{_event}}", "funnel_step_impression")
                    ],
                },
            ],
            "variable": [
                {
                    "variableId": "20",
                    "name": "DLV - Items",
                    "type": "v",
                    "parameter": [
                        {"type": "INTEGER", "key": "dataLayerVersion", "value": "2"},
                        {"type": "TEMPLATE", "key": "name", "value": "ecommerce.items"},
                    ],
                },
                {
                    "variableId": "21",
                    "name": "DLV - Items copy",
                    "type": "v",
                    "parameter": [
                        {"type": "INTEGER", "key": "dataLayerVersion", "value": "2"},
                        {"type": "TEMPLATE", "key": "name", "value": "ecommerce.items"},
                    ],
                },
                {
                    "variableId": "22",
                    "name": "CJS - Page URL Mirror",
                    "type": "jsm",
                    "parameter": [
                        {
                            "type": "TEMPLATE",
                            "key": "javascript",
                            "value": "function() {\n  return {{Page URL}};\n}",
                        }
                    ],
                },
                {
                    "variableId": "23",
                    "name": "CJS - Paused Only",
                    "type": "jsm",
                    "parameter": [
                        {
                            "type": "TEMPLATE",
                            "key": "javascript",
                            "value": "function() {\n  return 'paused-value';\n}",
                        }
                    ],
                },
                {
                    "variableId": "24",
                    "name": "DLV - Value",
                    "type": "v",
                    "parameter": [
                        {"type": "INTEGER", "key": "dataLayerVersion", "value": "2"},
                        {"type": "TEMPLATE", "key": "name", "value": "ecommerce.value"},
                    ],
                },
            ],
            "folder": [
                {"folderId": "100", "name": "Unused folder"},
                {"folderId": "101", "name": "Utilities"},
            ],
            "builtInVariable": [
                {"name": "Page URL", "type": "PAGE_URL"},
                {"name": "Click URL", "type": "CLICK_URL"},
            ],
        },
    }


def fixed_slot_formula_export() -> dict:
    data = sample_export()
    variables = data["containerVersion"]["variable"]
    for variable_id, index in (("30", 1), ("31", 2), ("32", 3)):
        variables.append(
            {
                "variableId": variable_id,
                "name": f"DLV - Product Price {index}",
                "type": "v",
                "parameter": [
                    {"type": "INTEGER", "key": "dataLayerVersion", "value": "2"},
                    {
                        "type": "TEMPLATE",
                        "key": "name",
                        "value": f"ecommerce.product_price_{index}",
                    },
                ],
            }
        )
    variables.append(
        {
            "variableId": "33",
            "name": "CJS - Total Price",
            "type": "jsm",
            "parameter": [
                {
                    "type": "TEMPLATE",
                    "key": "javascript",
                    "value": (
                        "function() {\n"
                        "  return Number({{DLV - Product Price 1}} || 0) + "
                        "Number({{DLV - Product Price 2}} || 0) + "
                        "Number({{DLV - Product Price 3}} || 0);\n"
                        "}"
                    ),
                }
            ],
        }
    )
    event_parameters = data["containerVersion"]["tag"][0]["parameter"][2]["map"]
    event_parameters[0]["value"] = "{{CJS - Total Price}}"
    return data


def object_specific_text(row: dict, subject: str, field: str = "") -> str:
    field_terms = [
        str(value)
        for value in (row.get("field_evidence_requirements") or {}).get(field, [])[:3]
    ]
    if not field_terms:
        field_terms = [row["object_name"] or row["object_key"], row["object_type"]]
    field_terms.extend(
        str(value)
        for value in row.get("specificity_tokens", [])[:2]
        if str(value) not in field_terms
    )
    evidence = " and ".join(field_terms)
    return (
        f"{row['object_name'] or row['object_key']} is a {row['object_type']} that {subject}; "
        f"the exported configuration specifically names {evidence}."
    )


def concrete_purpose_subject(row: dict) -> str:
    return {
        "tag": "sends, loads, routes, or records the configured measurement action",
        "trigger": "matches and activates the configured event or condition scope",
        "variable": "reads, calculates, maps, or returns its configured value",
        "customTemplate": "defines and executes the exported template behavior",
        "client": "claims, parses, and routes the configured request",
        "transformation": "transforms, allows, or redacts the configured fields",
    }.get(row.get("layer"), "implements its concrete exported action")


def branch_role(path: str) -> str:
    lowered = path.lower()
    if "consent" in lowered or "storage" in lowered:
        return "Consent"
    if "filter" in lowered or "condition" in lowered or "operator" in lowered:
        return "Condition"
    if any(value in lowered for value in ("firingtriggerid", "blockingtriggerid", "triggerids")):
        return "Routing"
    if any(value in lowered for value in ("setuptag", "teardowntag", "tagfiringoption")):
        return "Execution control"
    return "Input"


def complete_configuration(export_path: Path) -> dict:
    review = scaffold_configuration(export_path)
    for row in review["rows"]:
        row.update(
            {
                "review_status": "complete",
                "purpose": object_specific_text(
                    row, concrete_purpose_subject(row), "purpose"
                ),
                "execution_logic": object_specific_text(
                    row, "runs under the named trigger, condition, or call route", "execution_logic"
                ),
                "inputs_and_terminal_sources": object_specific_text(
                    row,
                    "reads the listed GTM references and terminal configuration",
                    "inputs_and_terminal_sources",
                ),
                "configured_output_or_side_effect": object_specific_text(
                    row,
                    "produces the named event, return value, or browser side effect",
                    "configured_output_or_side_effect",
                ),
                "consumer_contract": object_specific_text(
                    row,
                    "supplies the listed consumer objects with that configured value",
                    "consumer_contract",
                ),
                "consent_and_sequence": object_specific_text(
                    row,
                    "uses the listed blocking, consent, and sequencing controls",
                    "consent_and_sequence",
                ),
                "correctness_verdict": "Correct",
                "correctness_basis": object_specific_text(
                    row,
                    "has matching inputs, route, output, and consumers in this source",
                    "correctness_basis",
                ),
                "defects": [],
                "contract_checks": [],
                "code_behavior_blocks": [],
                "technical_facts_assessment": "",
                "technical_finding_reviews": [],
                "configuration_branch_reviews": [
                    {
                        "json_path": branch["json_path"],
                        "value_hash": branch["value_hash"],
                        "logic_role": branch_role(branch["json_path"]),
                        "interpretation": (
                            f"At {branch['json_path']}, value {branch.get('value_preview')} is the "
                            f"{branch_role(branch['json_path']).lower()} branch for "
                            f"{row['object_name'] or row['object_key']}."
                        ),
                        "configured_effect": (
                            f"The {branch_role(branch['json_path']).lower()} setting "
                            f"{branch.get('value_preview')} at {branch['json_path']} is read, "
                            "matched, routed, or applied when that configured branch executes for "
                            f"{row['object_name'] or row['object_key']}."
                        ),
                        "correctness": "Correct",
                    }
                    for branch in row["required_branch_reviews"]
                ],
                "evidence_anchors": list(row["required_logic_anchors"]),
                "consumer_evidence_keys": [
                    item["consumer_key"] for item in row["export_consumers"]
                ],
                "reference_traces": [
                    {
                        "reference": item["reference"],
                        "object_chain": item["required_object_keys"],
                        "evidence_anchors": item["required_evidence_anchors"],
                        "terminal_states": item["terminal_states"],
                        "terminal_source": (
                            f"Reference {item['reference']} terminates in the source states "
                            f"{', '.join(item['terminal_states'])} after the listed variable chain."
                        ),
                        "node_reviews": [
                            {
                                "object_key": node["object_key"],
                                "object_name": node["object_name"],
                                "object_type": node["object_type"],
                                "config_hash": node["config_hash"],
                                "source_json_path": node["source_json_path"],
                                "referenced_variables": node["referenced_variables"],
                                "configured_parameters": node["configured_parameters"],
                                "semantic_role": node["semantic_role"],
                                "evidence_anchors": node["required_evidence_anchors"],
                                "configured_function": (
                                    f"{node['object_name']} ({node['object_type']}) reads "
                                    f"{' and '.join(node['specificity_tokens'][:3])} from its parameters."
                                ),
                                "configured_output": (
                                    f"{node['object_name']} ({node['object_type']}) returns the value "
                                    f"selected by {' and '.join(node['specificity_tokens'][:3])}."
                                ),
                                "output_type_and_shape": (
                                    f"{node['object_name']} keeps the {node['object_type']} output "
                                    f"shape associated with {' and '.join(node['specificity_tokens'][:2])}."
                                ),
                                "availability_and_fallback": (
                                    f"{node['object_name']} makes {' and '.join(node['specificity_tokens'][:2])} "
                                    "available only where its listed source exists, with no extra fallback."
                                ),
                                "consumer_compatibility": (
                                    f"{node['object_name']} supplies its {node['object_type']} and "
                                    f"{' and '.join(node['specificity_tokens'][:2])} value to "
                                    f"{row['object_name'] or row['object_key']}."
                                ),
                            }
                            for node in item["required_nodes"]
                        ],
                        "edge_reviews": [
                            {
                                **edge,
                                "dependency_meaning": (
                                    f"{edge['from_object_key']} reads {edge['reference']} from "
                                    f"{edge['to_object_key']} before returning its configured result."
                                ),
                            }
                            for edge in item["required_edges"]
                        ],
                        "terminal_reviews": [
                            {
                                **terminal,
                                "terminal_meaning": (
                                    f"{terminal['reference']} resolves to {terminal['configured_source']} "
                                    f"as the final {terminal['state']} source."
                                ),
                                "consumer_compatibility": (
                                    f"The {terminal['reference']} {terminal['state']} source supplies "
                                    f"the configured value to {row['object_name'] or row['object_key']}."
                                ),
                            }
                            for terminal in item["terminal_requirements"]
                        ],
                    }
                    for item in row["reference_trace_requirements"]
                ],
                "related_operational_finding_ids": [],
                "logic_cross_checks": [
                    {
                        "check_key": check["check_key"],
                        "verdict": "Aligned",
                        "conclusion": (
                            f"For {row['object_name'] or row['object_key']}, "
                            f"{check['question']} The exported facts "
                            f"{' and '.join(check['required_terms'][:2])} remain aligned in this "
                            "controlled fixture configuration."
                        ),
                        "evidence_anchors": list(check["allowed_evidence_anchors"][:2]),
                    }
                    for check in row["required_logic_cross_checks"]
                ],
                "disposition": "keep",
                "owner_question": "",
                "operation": {},
                "confidence": "High",
                "evidence_citations": {
                    field: list((row.get("field_evidence_paths") or {}).get(field, []))[
                        : 2 if field == "correctness_basis" else 1
                    ]
                    for field in (
                        "purpose",
                        "execution_logic",
                        "inputs_and_terminal_sources",
                        "configured_output_or_side_effect",
                        "consumer_contract",
                        "consent_and_sequence",
                        "correctness_basis",
                    )
                },
            }
        )
        if row["required_contract_topics"]:
            fact_by_path = {
                fact["json_path"]: fact for fact in row.get("source_facts", [])
            }
            contract_anchor = row["required_logic_anchors"][0]
            row["contract_checks"] = [
                {
                    "contract_topic": topic["topic_key"],
                    "contract_field": (f"{topic['vendor']} {topic['topic']} exported contract"),
                    "configured_value": (
                        f"At {contract_anchor}, the exported value "
                        f"{fact_by_path[contract_anchor].get('value_preview')} configures "
                        f"{topic['topic']} for {row['object_name']}"
                    ),
                    "expected_rule": (
                        f"The official {topic['vendor']} documentation defines the required "
                        f"{topic['topic']} behavior and value types"
                    ),
                    "source": (
                        topic["official_doc_candidates"][0]
                        if topic["official_doc_candidates"]
                        else "https://vendor.example.com/official/setup"
                    ),
                    "identified_vendor": topic["vendor"],
                    "official_source_basis": (
                        f"The cited HTTPS page is presented as the official {topic['vendor']} "
                        "implementation and parameter reference."
                    ),
                    "verdict": "Compliant",
                    "evidence_anchors": row["required_logic_anchors"][:1],
                }
                for topic in row["required_contract_topics"]
            ]
        if row["required_code_line_hashes"]:
            previews = " ".join(
                str(item.get("line_preview") or "") for item in row["code_line_facts"]
            )
            markers = [
                token
                for token in re.findall(r"[A-Za-z_$][A-Za-z0-9_.$:/-]{3,}", previews)
                if token.lower() not in {"function", "return", "const", "false", "true", "script"}
            ]
            marker = markers[0] if markers else row["object_name"]
            row["code_behavior_blocks"] = [
                {
                    "line_hashes": list(row["required_code_line_hashes"]),
                    "start_line": min(item["line_number"] for item in row["code_line_facts"]),
                    "end_line": max(item["line_number"] for item in row["code_line_facts"]),
                    "purpose": f"The {marker} block implements the exact exported helper behavior.",
                    "inputs": f"The {marker} block reads only the variables and literals visible here.",
                    "outputs": f"The {marker} block returns or sends the output shown by these lines.",
                    "side_effects": f"The {marker} block has the browser effects identified in static facts.",
                    "health_assessment": f"The {marker} implementation is coherent for this controlled fixture.",
                }
            ]
            row["technical_facts_assessment"] = (
                f"The {marker} code facts, parser result, side effects, and line behavior are "
                "accounted for in this container-only assessment."
            )
            row["technical_finding_reviews"] = [
                {
                    "finding_key": item["finding_key"],
                    "source_statement": item["statement"],
                    "verdict": "False positive",
                    "rationale": (
                        f"The {marker} fixture intentionally exercises this static signal while "
                        "keeping its exported behavior controlled and explicit."
                    ),
                }
                for item in row["required_technical_findings"]
            ]
    review["run_status"] = "complete"
    return review


def complete_operational(export_path: Path) -> dict:
    review = scaffold_operational(export_path)
    for row in review["findings"]:
        row.update(
            {
                "review_status": "complete",
                "disposition": "owner_decision_needed",
                "rationale": (
                    f"The source evidence {' and '.join(row['rationale_evidence_terms'][:2])} "
                    "requires an explicit retained-versus-cleaned decision before this controlled "
                    "fixture can claim a completed cleanup."
                ),
                "owner_question": (
                    f"Should the source objects for {row['finding_type']} be retained for a "
                    "documented business reason, or approved for the proposed cleanup?"
                ),
            }
        )
    review["run_status"] = "complete"
    return review


def member_assessments(
    item: dict,
    keys_field: str,
    anchors_field: str,
    paused_field: str,
    terms_field: str,
) -> list:
    return [
        {
            "object_key": key,
            "configured_role": (
                f"{key} uses {' and '.join(item[terms_field][key][:2])} to perform its "
                "specific role in this measurement chain."
            ),
            "necessity": (
                f"{key} remains necessary while {item[terms_field][key][0]} has a distinct "
                "consumer, route, or terminal source."
            ),
            "distinguishing_configuration": (
                f"{key} is distinguished by {' and '.join(item[terms_field][key][:2])} "
                "in its route, payload, or dependency configuration."
            ),
            "status": "paused" if item[paused_field].get(key, False) else "active",
            "evidence_anchors": item[anchors_field][key][:1],
        }
        for key in item[keys_field]
    ]


def architecture_text(row: dict, field: str, statement: str) -> str:
    terms = (row.get("field_evidence_requirements") or {}).get(field, [])[:3]
    return f"{statement}; the source specifically includes {' and '.join(terms)}."


def complete_architecture(export_path: Path) -> dict:
    review = scaffold_architecture(export_path)
    for row in review["families"]:
        basis = row["family_label"] or row["family_key"]
        row.update(
            {
                "review_status": "complete",
                "business_action": architecture_text(
                    row, "business_action", f"The {basis} family records one named business action"
                ),
                "family_purpose": architecture_text(
                    row, "family_purpose", f"The {basis} family serves one destination outcome"
                ),
                "member_assessments": member_assessments(
                    row,
                    "member_object_keys",
                    "available_member_evidence_anchors",
                    "member_paused_status",
                    "member_evidence_terms",
                ),
                "chain_assessments": member_assessments(
                    row,
                    "chain_object_keys",
                    "available_chain_evidence_anchors",
                    "chain_paused_status",
                    "chain_evidence_terms",
                ),
                "execution_path_summary": architecture_text(
                    row, "execution_path_summary", f"The {basis} route connects its tag and dependencies"
                ),
                "payload_coherence": architecture_text(
                    row, "payload_coherence", f"The {basis} payload matches its event and destination"
                ),
                "consent_and_sequence_coherence": architecture_text(
                    row,
                    "consent_and_sequence_coherence",
                    f"The {basis} route uses its listed consent and sequence controls",
                ),
                "necessity_and_ownership": architecture_text(
                    row,
                    "necessity_and_ownership",
                    f"The {basis} members retain distinct chain ownership",
                ),
                "relationship_verdict": "Complementary",
                "analyst_rationale": architecture_text(
                    row,
                    "analyst_rationale",
                    f"The {basis} members have no proven duplicate firing in this export",
                ),
                "target_architecture": architecture_text(
                    row,
                    "target_architecture",
                    f"Keep the {basis} chain minimal while preserving these distinct roles",
                ),
                "disposition": "keep",
                "owner_question": "",
                "operations": [],
                "confidence": "High",
            }
        )
    for row in review["comparisons"]:
        exact = "exact_configuration" in row.get("comparison_types", [])
        row.update(
            {
                "review_status": "complete",
                "member_assessments": member_assessments(
                    row,
                    "candidate_object_keys",
                    "available_member_evidence_anchors",
                    "candidate_paused_status",
                    "candidate_evidence_terms",
                ),
                "relationship_verdict": "Owner decision needed" if exact else "Intentional variant",
                "analyst_rationale": architecture_text(
                    row,
                    "analyst_rationale",
                    f"{row['comparison_id']} candidates retain distinct roles after route and source comparison",
                ),
                "architecture_effect": architecture_text(
                    row,
                    "architecture_effect",
                    f"{row['comparison_id']} keeps separate paths because no common target is proven",
                ),
                "disposition": "owner_decision_needed" if exact else "keep",
                "owner_question": (
                    "Is this source-identical configuration intentionally duplicated for a "
                    "documented owner requirement, or should one canonical object remain?"
                    if exact
                    else ""
                ),
                "operations": [],
                "confidence": "High",
            }
        )
    source_records = object_records(container_version(json.loads(export_path.read_text(encoding="utf-8"))))
    reviewed_keys = sorted(
        record["object_key"]
        for layer_records in source_records.values()
        for record in layer_records
    )
    attestation = review["open_discovery_attestation"]
    source_terms = [
        term
        for family in review["families"]
        for terms in family["chain_evidence_terms"].values()
        for term in terms
    ]
    attestation.update(
        {
            "review_status": "complete",
            "reviewed_object_keys": reviewed_keys,
            "discovered_comparison_ids": [],
            "zero_discovery_rationale": (
                f"Every object, including {source_terms[0]} and {source_terms[1]}, was compared "
                "by name, route, terminal source, consumer, consent, and business-step evidence "
                "without finding another relationship."
            ),
            "method_reviews": [
                {
                    **row,
                    "review_status": "complete",
                    "reviewed_comparison_ids": list(row["comparison_ids"]),
                    "reviewed_object_keys": reviewed_keys,
                    "additional_discovery_ids": [],
                    "conclusion": (
                        f"The {row['method'].replace('_', ' ')} scan reviewed "
                        f"{len(reviewed_keys)} source objects and candidates "
                        f"{', '.join(row['comparison_ids']) or 'with no generated comparison'}; "
                        "no additional source-grounded relationship was found in this fixture."
                    ),
                }
                for row in review["discovery_method_coverage"]
            ],
        }
    )
    review["run_status"] = "complete"
    return review


def value_discovery_row(export_path: Path) -> dict:
    records = object_records(
        container_version(json.loads(export_path.read_text(encoding="utf-8")))
    )
    by_key = {
        record["object_key"]: record
        for layer_records in records.values()
        for record in layer_records
    }
    keys = ["variable:22", "variable:24"]
    return {
        "comparison_id": "DISC-VALUE-001",
        "comparison_origin": "analyst_discovered",
        "candidate_object_keys": keys,
        "candidate_basis": [
            "Recursive chain review found two differently named value helpers that require "
            "consumer-level comparison outside deterministic similarity groups."
        ],
        "review_status": "complete",
        "member_assessments": [
            {
                "object_key": key,
                "configured_role": (
                    f"{by_key[key]['object_name']} ({by_key[key]['object_type']}) returns "
                    f"{' and '.join(by_key[key]['specificity_tokens'][:2])} to its consumers."
                ),
                "necessity": (
                    f"{by_key[key]['object_name']} remains necessary while "
                    f"{by_key[key]['specificity_tokens'][0]} serves a distinct consumer."
                ),
                "distinguishing_configuration": (
                    f"{by_key[key]['object_name']} differs as a {by_key[key]['object_type']} "
                    f"through {' and '.join(by_key[key]['specificity_tokens'][:2])}."
                ),
                "status": "paused" if by_key[key]["paused"] else "active",
                "evidence_anchors": by_key[key]["evidence_anchors"][:1],
            }
            for key in keys
        ],
        "relationship_verdict": "Intentional variant",
        "analyst_rationale": (
            "CJS - Page URL Mirror mirrors Page URL while DLV - Value reads "
            "ecommerce.value, so shared value wording does not establish duplication."
        ),
        "architecture_effect": (
            "Keep CJS - Page URL Mirror and DLV - Value as separate variable roles while "
            "Page URL and ecommerce.value consumers remain distinct."
        ),
        "disposition": "keep",
        "owner_question": "",
        "operations": [],
        "confidence": "High",
    }


def duplicate_variable_operation() -> dict:
    return {
        "operation_key": "consolidate-ecommerce-items-dlv",
        "title": "Consolidate duplicate ecommerce items variables",
        "area": "GTM hygiene",
        "problem_type": "Exact duplicate",
        "problem": "Two data-layer variables read the same ecommerce.items source with identical settings.",
        "why_it_matters": "Maintaining both variables creates needless ambiguity and duplicate ownership work.",
        "expected_clean_state": "One canonical ecommerce.items variable serves every existing consumer.",
        "exact_proposed_action": "Keep variable 20 and delete unused duplicate variable 21.",
        "canonical_object_key": "variable:20",
        "changes": [],
        "remaps": [],
        "deletions": [
            {
                "object_key": "variable:21",
                "reason": "Variable 21 duplicates variable 20 and has no active consumer.",
            }
        ],
        "renames": [],
        "preconditions": "Confirm variable 21 still has no export-visible consumer before execution.",
        "qa_steps": "Re-export the workspace and confirm every ecommerce.items reference resolves to variable 20.",
        "rollback": "Restore variable 21 from the original container export if a missed dependency appears.",
        "priority": "Medium",
        "confidence": "High",
        "execution_readiness": "approval_required",
        "minimum_aggressiveness": "Standard",
        "challenge_review": {},
    }


def align_duplicate_operation(operational: dict, architecture: dict) -> None:
    operation = duplicate_variable_operation()
    for finding in operational["findings"]:
        if finding.get("module_name") not in {
            "duplicate_variable_logic",
            "duplicate_variable_paths",
        }:
            continue
        if set(finding.get("object_ids", [])) != {"20", "21"}:
            continue
        finding.update(copy.deepcopy(operation))
        finding["disposition"] = "cleanup_operation"
        finding["rationale"] = (
            "Variables 20 and 21 have identical data-layer settings, and variable 21 has no "
            "consumer, so one canonical variable is sufficient."
        )
    for comparison in architecture["comparisons"]:
        if set(comparison.get("candidate_object_keys", [])) != {"variable:20", "variable:21"}:
            continue
        comparison.update(
            {
                "relationship_verdict": "Exact duplicate",
                "analyst_rationale": (
                    "DLV - Items and DLV - Items Copy read ecommerce.items with identical type "
                    "and settings, while only DLV - Items has an active consumer."
                ),
                "architecture_effect": (
                    "Keeping DLV - Items and DLV - Items Copy adds maintenance work because both "
                    "use ecommerce.items without a distinct route, payload, or consumer contract."
                ),
                "disposition": "cleanup_operation",
                "operations": [copy.deepcopy(operation)],
            }
        )


class PipelineTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.export_path = self.root / "container.json"
        self.export_path.write_text(json.dumps(sample_export()), encoding="utf-8")

    def completed_reviews(self) -> tuple[dict, dict, dict]:
        return (
            complete_operational(self.export_path),
            complete_configuration(self.export_path),
            complete_architecture(self.export_path),
        )

    def write_review(self, name: str, payload: dict) -> Path:
        path = self.root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_system_and_builtin_references_are_not_missing(self) -> None:
        report = missing_references(container_version(sample_export()))
        self.assertEqual([], report["undefinedVariableReferences"])
        configuration = scaffold_configuration(self.export_path)
        mirror = next(row for row in configuration["rows"] if row["object_id"] == "22")
        trace = next(
            item
            for item in mirror["reference_trace_requirements"]
            if item["reference"] == "Page URL"
        )
        self.assertEqual(["built_in"], trace["terminal_states"])

    def test_container_only_contract_has_no_d4_or_runtime_gate(self) -> None:
        paths = [ROOT / "SKILL.md", ROOT / "README.md"]
        paths.extend((ROOT / "scripts").glob("*.py"))
        paths.extend((ROOT / "references").rglob("*.md"))
        for path in paths:
            content = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("d4_required", content, str(path))
            self.assertNotIn("runtime_qa_required", content, str(path))
        removed_runtime_reference = (
            ROOT / "references" / "02-commands" / ("runtime-qa-" + "templates.md")
        )
        self.assertFalse(removed_runtime_reference.exists())

    def test_operational_scan_catches_basic_cleanup_failures(self) -> None:
        findings = [
            row
            for row in audit_export(self.export_path)["findings"]
            if row["finding_type"] != "zero_findings"
        ]
        types = {row["finding_type"] for row in findings}
        self.assertIn("duplicate_configuration", types)
        self.assertIn("duplicate_variable_path", types)
        self.assertIn("single_member_trigger_group", types)
        self.assertIn("invalid_trigger_regex", types)
        self.assertIn("ineffective_blocking_trigger", types)
        self.assertIn("variable_mirrors_builtin", types)
        paused = [row for row in findings if row["module_name"] == "used_only_by_paused_tags"]
        self.assertTrue(any("23" in row["object_ids"] for row in paused))
        triggerless = [
            row for row in findings if row["module_name"] == "tags_without_firing_triggers"
        ]
        self.assertFalse(any("3" in row["object_ids"] for row in triggerless))

    def test_fixed_slot_business_formula_cannot_pass_as_generic_false_positive(self) -> None:
        path = self.root / "fixed-slot-formula.json"
        path.write_text(json.dumps(fixed_slot_formula_export()), encoding="utf-8")
        findings = [
            row for row in audit_export(path)["findings"] if row["finding_type"] != "zero_findings"
        ]
        formula = next(
            row for row in findings if row["finding_type"] == "fixed_slot_business_formula"
        )
        self.assertEqual(["33"], formula["object_ids"])
        technical = extract_export(path)
        technical_row = next(row for row in technical["rows"] if row["object_id"] == "33")
        self.assertTrue(technical_row["fixed_slot_aggregation"])
        self.assertEqual([1, 2, 3], technical_row["fixed_slot_groups"][0]["indexes"])

        review = complete_configuration(path)
        total = next(row for row in review["rows"] if row["object_key"] == "variable:33")
        fixed_review = next(
            row
            for row in total["technical_finding_reviews"]
            if "fixed numbered value slots" in row["source_statement"].lower()
        )
        fixed_review["verdict"] = "False positive"
        fixed_review["rationale"] = "The code was inspected and appears acceptable."
        errors, _ = validate_configuration(
            path,
            self.write_review("fixed-slot-generic-dismissal.json", review),
        )
        self.assertTrue(any("fixed-slot business formula" in error for error in errors))

    def test_consent_purposes_with_same_logic_are_compared(self) -> None:
        data = sample_export()
        shared_config = [
            {"type": "TEMPLATE", "key": "name", "value": "OnetrustActiveGroups"},
        ]
        data["containerVersion"]["variable"].extend(
            [
                {
                    "variableId": "40",
                    "name": "CJS - analytics_storage",
                    "type": "jsm",
                    "parameter": [
                        {
                            "type": "TEMPLATE",
                            "key": "javascript",
                            "value": "function(){ return {{OnetrustActiveGroups}}.indexOf(',2,') > -1; }",
                        },
                        *shared_config,
                    ],
                },
                {
                    "variableId": "41",
                    "name": "CJS - ad_storage",
                    "type": "jsm",
                    "parameter": [
                        {
                            "type": "TEMPLATE",
                            "key": "javascript",
                            "value": "function(){ return {{OnetrustActiveGroups}}.indexOf(',2,') > -1; }",
                        },
                        *shared_config,
                    ],
                },
            ]
        )
        path = self.root / "consent-shared-logic.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        findings = audit_export(path)["findings"]
        consent = [
            row
            for row in findings
            if row["finding_type"] == "different_consent_purposes_share_logic"
        ]
        self.assertEqual(1, len(consent))
        self.assertEqual({"40", "41"}, set(consent[0]["object_ids"]))

    def test_server_forwarded_consent_is_distinct_from_missing_client_control(self) -> None:
        variable = {
            "variableId": "50",
            "name": "DLV - Server consent state",
            "type": "v",
            "parameter": [
                {
                    "type": "TEMPLATE",
                    "key": "name",
                    "value": "consent_state",
                }
            ],
        }
        tag = {
            "tagId": "51",
            "name": "Google tag - Server transport",
            "type": "googtag",
            "parameter": [
                {
                    "type": "TEMPLATE",
                    "key": "transport_url",
                    "value": "https://collect.example.test",
                },
                {
                    "type": "TEMPLATE",
                    "key": "server_consent",
                    "value": "{{DLV - Server consent state}}",
                },
            ],
        }
        route = tag_consent_route(
            tag,
            "$.containerVersion.tag[0]",
            variables=[variable],
        )
        self.assertEqual("server_forwarded_consent_contract", route["effective_control_status"])
        self.assertEqual(["collect.example.test"], route["server_routing_hosts"])
        self.assertEqual(
            ["DLV - Server consent state"],
            route["server_consent_forwarding_variables"],
        )
        self.assertTrue(route["forwarded_cmp_signal_visible"])
        self.assertEqual("not_visible_in_web_export", route["server_enforcement_visibility"])

        data = sample_export()
        data["containerVersion"]["variable"].append(variable)
        media_transport = {
            **tag,
            "tagId": "53",
            "name": "Meta - Lead server transporter",
            "type": "html",
            "firingTriggerId": ["10"],
        }
        data["containerVersion"]["tag"].append(media_transport)
        export = self.root / "server-forwarded-consent.json"
        export.write_text(json.dumps(data), encoding="utf-8")
        findings = audit_export(export)["findings"]
        self.assertFalse(
            any(
                row["finding_type"] == "media_consent_route_requires_review"
                and "53" in row["object_ids"]
                for row in findings
            )
        )

    def test_server_route_without_forwarded_consent_remains_unproven(self) -> None:
        tag = {
            "tagId": "52",
            "name": "Google tag - Incomplete server transport",
            "type": "googtag",
            "parameter": [
                {
                    "type": "TEMPLATE",
                    "key": "transport_url",
                    "value": "https://collect.example.test",
                }
            ],
        }
        route = tag_consent_route(tag)
        self.assertEqual("server_contract_unproven", route["effective_control_status"])
        self.assertEqual([], route["server_consent_forwarding_evidence"])

    def test_operational_scan_covers_paused_groups_and_template_duplicates(self) -> None:
        data = sample_export()
        data["containerVersion"]["tag"][3].pop("firingTriggerId")
        data["containerVersion"]["trigger"].extend(
            [
                {
                    "triggerId": "30",
                    "name": "TG - Empty",
                    "type": "TRIGGER_GROUP",
                    "parameter": [],
                },
                {
                    "triggerId": "31",
                    "name": "TG - Duplicate members",
                    "type": "TRIGGER_GROUP",
                    "parameter": [
                        {
                            "type": "LIST",
                            "key": "triggerIds",
                            "list": [
                                {"type": "TEMPLATE", "value": "10"},
                                {"type": "TEMPLATE", "value": "10"},
                            ],
                        }
                    ],
                },
                {
                    "triggerId": "32",
                    "name": "TG - Cycle A",
                    "type": "TRIGGER_GROUP",
                    "parameter": [
                        {
                            "type": "LIST",
                            "key": "triggerIds",
                            "list": [{"type": "TEMPLATE", "value": "33"}],
                        }
                    ],
                },
                {
                    "triggerId": "33",
                    "name": "TG - Cycle B",
                    "type": "TRIGGER_GROUP",
                    "parameter": [
                        {
                            "type": "LIST",
                            "key": "triggerIds",
                            "list": [{"type": "TEMPLATE", "value": "32"}],
                        }
                    ],
                },
            ]
        )
        data["containerVersion"]["customTemplate"] = [
            {"templateId": "tpl-1", "name": "Template one", "templateData": "same"},
            {"templateId": "tpl-2", "name": "Template two", "templateData": "same"},
        ]
        path = self.root / "operational-adversary.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        findings = [
            row for row in audit_export(path)["findings"] if row["finding_type"] != "zero_findings"
        ]
        types = {row["finding_type"] for row in findings}
        self.assertIn("paused_objects_for_lifecycle_review", types)
        self.assertIn("empty_trigger_group", types)
        self.assertIn("duplicate_trigger_group_members", types)
        self.assertIn("cyclic_trigger_groups", types)
        self.assertTrue(
            any(
                row["module_name"] == "duplicate_custom_template_configurations" for row in findings
            )
        )
        triggerless = [
            row for row in findings if row["module_name"] == "tags_without_firing_triggers"
        ]
        self.assertFalse(any("4" in row["object_ids"] for row in triggerless))

    def test_relationship_run_detects_scope_and_status_without_names_only(self) -> None:
        rows = relationship_candidates(container_version(sample_export()))
        q1 = [
            row
            for row in rows
            if "shared_business_scope" in row["comparison_types"]
            and {"trigger:15", "trigger:16"}.issubset(row["candidate_object_keys"])
        ]
        self.assertEqual(1, len(q1))
        duplicate = next(
            row
            for row in rows
            if {"variable:20", "variable:21"} == set(row["candidate_object_keys"])
        )
        self.assertIn("exact_configuration", duplicate["comparison_types"])
        self.assertEqual(False, duplicate["candidate_paused_status"]["variable:20"])

    def test_relationship_run_reviews_multiple_firing_routes(self) -> None:
        data = sample_export()
        data["containerVersion"]["tag"][0]["firingTriggerId"] = ["15", "16"]
        rows = relationship_candidates(container_version(data))
        route = [
            row
            for row in rows
            if "multi_firing_route_consolidation_review" in row["comparison_types"]
            and set(row["candidate_object_keys"]) == {"trigger:15", "trigger:16"}
        ]
        self.assertEqual(1, len(route))

    def test_architecture_accepts_source_grounded_open_discovery(self) -> None:
        review = complete_architecture(self.export_path)
        review["comparisons"].append(value_discovery_row(self.export_path))
        review["open_discovery_attestation"]["discovered_comparison_ids"] = [
            "DISC-VALUE-001"
        ]
        review["open_discovery_attestation"]["zero_discovery_rationale"] = ""
        errors, _ = validate_architecture(
            self.export_path,
            self.write_review("open-discovery.json", review),
        )
        self.assertEqual([], errors)

    def test_configuration_scaffold_requires_every_object_branch_code_and_trace(self) -> None:
        review = scaffold_configuration(self.export_path)
        source_count = sum(
            len(sample_export()["containerVersion"].get(layer, []))
            for layer in (
                "tag",
                "trigger",
                "variable",
                "customTemplate",
                "client",
                "transformation",
            )
        )
        self.assertEqual(source_count, len(review["rows"]))
        meta = next(
            row for row in review["rows"] if row["object_id"] == "2" and row["layer"] == "tag"
        )
        self.assertTrue(meta["required_branch_reviews"])
        self.assertTrue(meta["required_code_line_hashes"])
        self.assertTrue(meta["reference_trace_requirements"])
        self.assertTrue(meta["technical_code_facts"])

    def test_configuration_gate_rejects_missing_branch_and_generic_code(self) -> None:
        review = complete_configuration(self.export_path)
        custom = next(
            row for row in review["rows"] if row["object_id"] == "2" and row["layer"] == "tag"
        )
        custom["configuration_branch_reviews"].pop()
        custom["code_behavior_blocks"][0]["purpose"] = "Code inspected and reviewed"
        path = self.write_review("bad-config.json", review)
        errors, _ = validate_configuration(self.export_path, path)
        self.assertTrue(any("branch reviews" in error for error in errors))
        self.assertTrue(any("incomplete purpose" in error for error in errors))

    def test_configuration_gate_rejects_generic_semantic_prose_with_valid_citations(self) -> None:
        review = complete_configuration(self.export_path)
        purchase = next(row for row in review["rows"] if row["object_key"] == "tag:1")
        purchase["purpose"] = (
            "GA4 - Purchase - All serves one concrete measurement purpose through its tag setup."
        )
        errors, _ = validate_configuration(
            self.export_path,
            self.write_review("generic-semantic-prose.json", review),
        )
        self.assertTrue(any("purpose lacks object-specific analysis" in error for error in errors))

    def test_review_context_is_content_locked_not_hash_only(self) -> None:
        review = complete_configuration(self.export_path)
        review["audit_context"]["business_model"] = "publisher"
        errors, _ = validate_configuration(
            self.export_path,
            self.write_review("tampered-context.json", review),
        )
        self.assertTrue(any("audit_context differs" in error for error in errors))

    def test_unknown_external_vendor_creates_official_research_contract(self) -> None:
        data = sample_export()
        data["containerVersion"]["tag"].append(
            {
                "tagId": "90",
                "name": "Partner widget",
                "type": "html",
                "parameter": [
                    {
                        "type": "TEMPLATE",
                        "key": "html",
                        "value": (
                            '<script src="https://unknown-cdn.example/widget.js"></script>'
                        ),
                    }
                ],
                "firingTriggerId": ["10"],
            }
        )
        path = self.root / "unknown-vendor.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        review = scaffold_configuration(path)
        partner = next(row for row in review["rows"] if row["object_key"] == "tag:90")
        self.assertTrue(
            any(context["category"] == "unknown_vendor" for context in partner["vendor_contexts"])
        )
        self.assertTrue(any(topic["research_required"] for topic in partner["required_contract_topics"]))
        context = build_context_model(path)
        self.assertIn("unknown-cdn.example", context["context"]["external_hosts"])
        self.assertNotIn("unknown-cdn.example", context["context"]["server_routing_hosts"])
        self.assertEqual("Unclassified", vendor_record('{"key":"contents"}')["name"])
        self.assertEqual("Unclassified", vendor_record('{"key":"activity"}')["name"])

    def test_configuration_requires_contract_topics_and_recursive_node_meaning(self) -> None:
        scaffold = scaffold_configuration(self.export_path)
        purchase = next(row for row in scaffold["rows"] if row["object_key"] == "tag:1")
        topics = {item["topic"] for item in purchase["required_contract_topics"]}
        self.assertIn("ecommerce_event_contract", topics)
        self.assertIn("transaction_value_currency_and_quantity", topics)
        value_variable = next(row for row in scaffold["rows"] if row["object_key"] == "variable:24")
        self.assertTrue(
            any(
                context["vendor"] == "GA4 / Google tag"
                for context in value_variable["vendor_contexts"]
            )
        )
        self.assertTrue(value_variable["required_contract_topics"])

        review = complete_configuration(self.export_path)
        completed_purchase = next(row for row in review["rows"] if row["object_key"] == "tag:1")
        completed_purchase["contract_checks"].pop()
        errors, _ = validate_configuration(
            self.export_path,
            self.write_review("missing-contract-topic.json", review),
        )
        self.assertTrue(any("every generated topic" in error for error in errors))

        review = complete_configuration(self.export_path)
        completed_purchase = next(row for row in review["rows"] if row["object_key"] == "tag:1")
        completed_purchase["contract_checks"][0]["expected_rule"] = (
            "The official vendor documentation was reviewed for this configuration."
        )
        errors, _ = validate_configuration(
            self.export_path,
            self.write_review("generic-contract-rule.json", review),
        )
        self.assertTrue(any("topic-specific contract" in error for error in errors))

        review = complete_configuration(self.export_path)
        meta = next(row for row in review["rows"] if row["object_key"] == "tag:2")
        trace = next(
            item for item in meta["reference_traces"] if item["reference"] == "DLV - Items"
        )
        trace["node_reviews"].clear()
        errors, _ = validate_configuration(
            self.export_path,
            self.write_review("missing-trace-node.json", review),
        )
        self.assertTrue(any("every variable node" in error for error in errors))

    def test_complete_configuration_and_architecture_reviews_validate(self) -> None:
        configuration = complete_configuration(self.export_path)
        architecture = complete_architecture(self.export_path)
        config_errors, _ = validate_configuration(
            self.export_path, self.write_review("configuration.json", configuration)
        )
        architecture_errors, _ = validate_architecture(
            self.export_path, self.write_review("architecture.json", architecture)
        )
        self.assertEqual([], config_errors)
        self.assertEqual([], architecture_errors)
        purchase_family = next(
            row for row in architecture["families"] if "tag:1" in row["member_object_keys"]
        )
        self.assertIn("trigger:10", purchase_family["chain_object_keys"])
        self.assertIn("trigger:13", purchase_family["chain_object_keys"])
        self.assertIn("variable:24", purchase_family["chain_object_keys"])
        self.assertIn("tag:3", purchase_family["chain_object_keys"])
        self.assertEqual(
            set(purchase_family["chain_object_keys"]),
            {item["object_key"] for item in purchase_family["chain_assessments"]},
        )

    def test_architecture_requires_every_chain_object_and_server_root(self) -> None:
        review = complete_architecture(self.export_path)
        family = next(row for row in review["families"] if "tag:1" in row["member_object_keys"])
        family["chain_assessments"].pop()
        errors, _ = validate_architecture(
            self.export_path,
            self.write_review("missing-chain-assessment.json", review),
        )
        self.assertTrue(any("chain" in error and "every member" in error for error in errors))

        data = sample_export()
        data["containerVersion"]["client"] = [
            {"clientId": "50", "name": "GA4 client", "type": "gaaw_client"}
        ]
        data["containerVersion"]["transformation"] = [
            {
                "transformationId": "60",
                "name": "Redact user data",
                "type": "exclude_parameters",
            }
        ]
        server_path = self.root / "server.json"
        server_path.write_text(json.dumps(data), encoding="utf-8")
        server_review = scaffold_architecture(server_path)
        root_keys = {
            key
            for family_row in server_review["families"]
            for key in family_row["member_object_keys"]
        }
        self.assertIn("client:50", root_keys)
        self.assertIn("transformation:60", root_keys)

    def test_operational_validator_requires_all_findings(self) -> None:
        review = complete_operational(self.export_path)
        review["findings"].pop()
        errors, _ = validate_operational(
            self.export_path, self.write_review("bad-operational.json", review)
        )
        self.assertTrue(any("missing operational findings" in error for error in errors))

    def test_compiler_blocks_unaligned_basic_consolidation(self) -> None:
        operational, configuration, architecture = self.completed_reviews()
        operation = duplicate_variable_operation()
        finding = next(
            row
            for row in operational["findings"]
            if row["module_name"] == "duplicate_variable_paths"
        )
        finding.update(copy.deepcopy(operation))
        finding["disposition"] = "cleanup_operation"
        payload, errors = compile_operations(
            operational,
            configuration,
            architecture,
            "Direct GTM/MCP/API",
            "Deep",
            source_object_catalog(self.export_path),
        )
        self.assertEqual([], payload["operations"])
        self.assertTrue(any("lacks an aligned business-architecture" in error for error in errors))

    def test_three_runs_reconcile_and_future_state_passes(self) -> None:
        operational, configuration, architecture = self.completed_reviews()
        align_duplicate_operation(operational, architecture)
        for name, review, validator in (
            ("operational.json", operational, validate_operational),
            ("configuration.json", configuration, validate_configuration),
            ("architecture.json", architecture, validate_architecture),
        ):
            errors, _ = validator(self.export_path, self.write_review(name, review))
            self.assertEqual([], errors)
        payload, errors = compile_operations(
            operational,
            configuration,
            architecture,
            "Direct GTM/MCP/API",
            "Deep",
            source_object_catalog(self.export_path),
        )
        self.assertEqual([], errors)
        self.assertEqual(1, len(payload["operations"]))
        self.assertEqual(
            ["business_architecture", "operational_sanitation"],
            payload["operations"][0]["source_runs"],
        )
        self.assertTrue(payload["shared_facts_sha256"])
        self.assertTrue(payload["decision_ledger"])
        self.assertEqual(-1, payload["projected_object_counts"]["variable"]["delta"])
        self.assertEqual(
            ["delete"],
            payload["operations"][0]["execution_phases"],
        )
        report, future_errors = check_future_state(self.export_path, payload)
        self.assertEqual([], future_errors)
        self.assertEqual("pass", report["status"])
        self.assertEqual(-1, report["object_counts"]["variable"]["delta"])

    def test_compiler_rejects_same_key_with_different_mutations(self) -> None:
        operational, configuration, architecture = self.completed_reviews()
        align_duplicate_operation(operational, architecture)
        comparison = next(
            row
            for row in architecture["comparisons"]
            if set(row["candidate_object_keys"]) == {"variable:20", "variable:21"}
        )
        comparison["operations"][0]["canonical_object_key"] = "variable:21"
        comparison["operations"][0]["deletions"] = [
            {
                "object_key": "variable:20",
                "reason": "Use variable 21 as the conflicting canonical object in this test.",
            }
        ]
        _, errors = compile_operations(operational, configuration, architecture, "Manual", "Deep")
        self.assertTrue(
            any("reused for different structured mutations" in error for error in errors)
        )

    def test_compiler_merges_wording_variants_for_the_same_mutation(self) -> None:
        operational, configuration, architecture = self.completed_reviews()
        align_duplicate_operation(operational, architecture)
        comparison = next(
            row
            for row in architecture["comparisons"]
            if set(row["candidate_object_keys"]) == {"variable:20", "variable:21"}
        )
        comparison["operations"][0]["problem"] = (
            "DLV - Items Copy repeats the canonical ecommerce.items variable without consumers."
        )
        payload, errors = compile_operations(
            operational,
            configuration,
            architecture,
            "Manual",
            "Deep",
        )
        self.assertEqual([], errors)
        self.assertEqual(1, len(payload["operations"]))
        self.assertEqual(3, len(payload["operations"][0]["lens_rationales"]))
        self.assertEqual(
            {"operational_sanitation", "business_architecture"},
            {
                row["source_run"]
                for row in payload["operations"][0]["lens_rationales"]
            },
        )

    def test_future_state_blocks_deletion_that_breaks_a_consumer(self) -> None:
        operational, configuration, architecture = self.completed_reviews()
        align_duplicate_operation(operational, architecture)
        payload, errors = compile_operations(
            operational, configuration, architecture, "Manual", "Deep"
        )
        self.assertEqual([], errors)
        payload["operations"][0]["deletions"] = [
            {"object_key": "variable:20", "reason": "Intentional broken test deletion."}
        ]
        payload["operations"][0]["affected_object_keys"] = ["variable:20"]
        report, future_errors = check_future_state(self.export_path, payload)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any("missing references" in error for error in future_errors))

    def test_future_state_rejects_stale_before_value(self) -> None:
        operational, configuration, architecture = self.completed_reviews()
        align_duplicate_operation(operational, architecture)
        payload, errors = compile_operations(
            operational, configuration, architecture, "Manual", "Deep"
        )
        self.assertEqual([], errors)
        payload["operations"][0]["changes"] = [
            {
                "object_key": "tag:1",
                "json_path": "$.containerVersion.tag[0].name",
                "before": "A stale tag name",
                "after": "GA4 - Purchase - Global",
            }
        ]
        report, future_errors = check_future_state(self.export_path, payload)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any("before value does not match" in error for error in future_errors))

    def test_structured_operations_support_creation_and_missing_field_addition(self) -> None:
        operation = {
            "problem_type": "Missing tracking",
            "minimum_aggressiveness": "Standard",
            "creations": [
                {
                    "layer": "variable",
                    "object": {
                        "variableId": "99",
                        "name": "Constant - Test Value",
                        "type": "c",
                        "parameter": [
                            {"type": "TEMPLATE", "key": "value", "value": "test"}
                        ],
                    },
                    "reason": "Create the missing constant required by the approved test tag.",
                }
            ],
            "additions": [
                {
                    "object_key": "tag:1",
                    "json_path": "$.containerVersion.tag[0].parameter",
                    "mode": "append",
                    "value": {
                        "type": "TEMPLATE",
                        "key": "testParameter",
                        "value": "{{Constant - Test Value}}",
                    },
                    "reason": "Add the approved parameter to the existing purchase tag.",
                }
            ],
            "changes": [],
            "remaps": [],
            "renames": [],
            "deletions": [],
        }
        validation_errors = validate_structured_actions(
            operation,
            object_keys(self.export_path),
            "creation test",
            object_consumer_map(self.export_path),
        )
        self.assertEqual([], validation_errors)
        future, apply_errors = apply_operations(
            sample_export(),
            {"operations": [operation]},
        )
        self.assertEqual([], apply_errors)
        future_cv = container_version(future)
        self.assertTrue(any(row.get("variableId") == "99" for row in future_cv["variable"]))
        self.assertEqual(
            "testParameter",
            future_cv["tag"][0]["parameter"][-1]["key"],
        )

    def test_aggressiveness_defers_operations_below_their_minimum_level(self) -> None:
        operational, configuration, architecture = self.completed_reviews()
        align_duplicate_operation(operational, architecture)
        conservative, errors = compile_operations(
            operational,
            configuration,
            architecture,
            "Manual",
            "Conservative",
        )
        self.assertEqual([], errors)
        self.assertEqual([], conservative["operations"])
        self.assertEqual(1, len(conservative["deferred_operations"]))
        self.assertEqual(
            "deferred_by_aggressiveness",
            conservative["deferred_operations"][0]["resolution_status"],
        )
        human, human_errors = build_rows(conservative)
        self.assertEqual([], human_errors)
        self.assertEqual("Deferred", human[0]["Level"])

    def test_human_plan_exposes_owner_decisions_without_internal_proof_columns(self) -> None:
        payload = {
            "operations": [],
            "deferred_operations": [],
            "decision_ledger": [
                {
                    "decision_id": "CFG-001",
                    "disposition": "owner_decision_needed",
                    "area": "Governance / ownership",
                    "problem_type": "Unclear business purpose",
                    "affected_objects": "tag:1 - Legacy lead",
                    "summary": "Legacy lead sends a second conversion for the same form submit.",
                    "owner_question": (
                        "Should Legacy lead remain a separate paid-media conversion?"
                    ),
                }
            ],
        }
        rows, errors = build_rows(payload)
        self.assertEqual([], errors)
        self.assertEqual(1, len(rows))
        self.assertEqual("Owner decision", rows[0]["Level"])
        self.assertEqual(6, len(rows[0]))

    def test_remap_requires_the_exact_source_consumer_set(self) -> None:
        review = complete_configuration(self.export_path)
        row = next(item for item in review["rows"] if item["object_key"] == "variable:20")
        operation = duplicate_variable_operation()
        operation.update(
            {
                "operation_key": "remap-items-variable",
                "canonical_object_key": "variable:21",
                "changes": [],
                "deletions": [],
                "remaps": [
                    {
                        "from_object_key": "variable:20",
                        "to_object_key": "variable:21",
                        "consumer_object_keys": ["tag:1"],
                    }
                ],
                "exact_proposed_action": (
                    "Remap the items variable to the selected canonical variable."
                ),
            }
        )
        row["disposition"] = "cleanup_operation"
        row["operation"] = operation
        errors, _ = validate_configuration(
            self.export_path,
            self.write_review("bad-remap-consumers.json", review),
        )
        self.assertTrue(
            any("exactly match every source-graph consumer" in error for error in errors)
        )

    def test_package_build_contains_three_independent_review_artifacts(self) -> None:
        package_dir = self.root / "package"
        manifest = build_package(self.export_path, package_dir, pretty=True)
        self.assertEqual("pass", manifest["status"])
        for filename in (
            "context.json",
            "shared_facts.json",
            "operational_review.json",
            "configuration_review.json",
            "architecture_review.json",
            "operational_scan.json",
        ):
            self.assertTrue((package_dir / filename).is_file())
        self.assertNotIn("semantic_review", manifest["files"])
        shared = json.loads((package_dir / "shared_facts.json").read_text(encoding="utf-8"))
        context = json.loads((package_dir / "context.json").read_text(encoding="utf-8"))
        self.assertEqual(shared["shared_facts_sha256"], manifest["shared_facts_sha256"])
        self.assertEqual(context["context_sha256"], manifest["context_sha256"])
        for filename in (
            "operational_review.json",
            "configuration_review.json",
            "architecture_review.json",
        ):
            review = json.loads((package_dir / filename).read_text(encoding="utf-8"))
            self.assertEqual(shared["shared_facts_sha256"], review["shared_facts_sha256"])

    def test_package_gate_rejects_shared_fact_content_with_a_copied_hash(self) -> None:
        package_dir = self.root / "tampered-package"
        build_package(self.export_path, package_dir, pretty=True)
        shared_path = package_dir / "shared_facts.json"
        shared = json.loads(shared_path.read_text(encoding="utf-8"))
        shared["objects"][0]["object_name"] = "Fabricated object name"
        shared_path.write_text(json.dumps(shared), encoding="utf-8")
        report = run_gate(self.export_path, package_dir, audit_only=True)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any("recorded hash" in error for error in report["errors"]))

    def test_broken_references_remain_auditable_integrity_findings(self) -> None:
        data = sample_export()
        data["containerVersion"]["tag"][0]["firingTriggerId"] = ["999"]
        path = self.root / "broken-reference.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        model = build_model(path)
        self.assertEqual("pass_with_integrity_findings", model["coverage_gate"])
        package_dir = self.root / "broken-package"
        manifest = build_package(path, package_dir, pretty=True)
        self.assertEqual("pass", manifest["status"])
        shared = build_shared_facts(path, context=build_context_model(path))
        self.assertEqual("pass_with_integrity_findings", shared["coverage_gate"])
        findings = audit_export(path)["findings"]
        self.assertTrue(
            any(row["finding_type"] == "missing_trigger_reference" for row in findings)
        )

    def test_verdict_engines_share_only_neutral_review_helpers(self) -> None:
        configuration_source = (SCRIPTS / "gtm_configuration_review.py").read_text(encoding="utf-8")
        architecture_source = (SCRIPTS / "gtm_architecture_review.py").read_text(encoding="utf-8")
        self.assertNotIn("from gtm_operational_review import", configuration_source)
        self.assertNotIn("from gtm_operational_review import", architecture_source)
        self.assertIn("from gtm_review_common import", configuration_source)
        self.assertIn("from gtm_review_common import", architecture_source)

    def test_large_review_shards_merge_only_with_complete_exact_coverage(self) -> None:
        completed = complete_configuration(self.export_path)
        base_path = self.write_review("configuration-complete.json", completed)
        shard_dir = self.root / "configuration-shards"
        manifest = split_review(base_path, shard_dir, max_items=3)
        self.assertGreater(len(manifest["shards"]), 1)
        output = self.root / "configuration-merged.json"
        merged = merge_review(base_path, shard_dir, output)
        self.assertEqual(completed["rows"], merged["rows"])
        self.assertEqual("complete", merged["run_status"])

        shard_manifest_path = shard_dir / "shard_manifest.json"
        broken_manifest = json.loads(shard_manifest_path.read_text(encoding="utf-8"))
        broken_manifest["shards"][0]["filename"] = "missing-shard.json"
        shard_manifest_path.write_text(json.dumps(broken_manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing review shard"):
            merge_review(base_path, shard_dir, self.root / "must-not-exist.json")

    def test_architecture_shards_merge_discovery_rows_and_attestation(self) -> None:
        completed = complete_architecture(self.export_path)
        completed["comparisons"] = [
            row
            for row in completed["comparisons"]
            if row.get("comparison_origin") != "analyst_discovered"
        ]
        completed["open_discovery_attestation"]["discovered_comparison_ids"] = []
        base_path = self.write_review("architecture-complete.json", completed)
        shard_dir = self.root / "architecture-shards"
        manifest = split_review(base_path, shard_dir, max_items=2)
        discovery_path = shard_dir / manifest["discovery_shard"]
        discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
        discovery["discovered_comparisons"] = [value_discovery_row(self.export_path)]
        discovery["open_discovery_attestation"].update(
            {
                "review_status": "complete",
                "discovered_comparison_ids": ["DISC-VALUE-001"],
                "zero_discovery_rationale": "",
            }
        )
        discovery_path.write_text(json.dumps(discovery), encoding="utf-8")
        merged_path = self.root / "architecture-merged.json"
        merged = merge_review(base_path, shard_dir, merged_path)
        self.assertIn(
            "DISC-VALUE-001",
            {row["comparison_id"] for row in merged["comparisons"]},
        )
        errors, _ = validate_architecture(self.export_path, merged_path)
        self.assertEqual([], errors)

    def test_three_run_gate_rejects_scaffolds_and_passes_completed_reviews(self) -> None:
        package_dir = self.root / "package"
        build_package(self.export_path, package_dir, pretty=True)
        pending = run_gate(self.export_path, package_dir)
        self.assertEqual("fail", pending["status"])
        operational, configuration, architecture = self.completed_reviews()
        align_duplicate_operation(operational, architecture)
        (package_dir / "operational_review.json").write_text(
            json.dumps(operational), encoding="utf-8"
        )
        (package_dir / "configuration_review.json").write_text(
            json.dumps(configuration), encoding="utf-8"
        )
        (package_dir / "architecture_review.json").write_text(
            json.dumps(architecture), encoding="utf-8"
        )
        payload, compile_errors = compile_operations(
            operational,
            configuration,
            architecture,
            "Direct GTM/MCP/API",
            "Deep",
            source_object_catalog(self.export_path),
        )
        self.assertEqual([], compile_errors)
        operations_path = self.write_review("operations.json", payload)
        completed = run_gate(self.export_path, package_dir, operations_path)
        self.assertEqual("pass", completed["status"], completed["errors"])

        tampered = copy.deepcopy(payload)
        tampered["operations"][0]["exact_proposed_action"] = (
            "A hand-edited action that was not compiled from the reviews."
        )
        tampered_path = self.write_review("tampered-operations.json", tampered)
        rejected = run_gate(self.export_path, package_dir, tampered_path)
        self.assertEqual("fail", rejected["status"])
        self.assertTrue(any("deterministic recompilation" in error for error in rejected["errors"]))

    def test_human_rows_and_workbook_are_compact_and_separate_from_change_log(self) -> None:
        try:
            from openpyxl import load_workbook
        except ImportError:
            self.skipTest("openpyxl is not installed")
        operational, configuration, architecture = self.completed_reviews()
        align_duplicate_operation(operational, architecture)
        payload, errors = compile_operations(
            operational,
            configuration,
            architecture,
            "Direct GTM/MCP/API",
            "Deep",
            source_object_catalog(self.export_path),
        )
        self.assertEqual([], errors)
        human, human_errors = build_rows(payload)
        self.assertEqual([], human_errors)
        self.assertEqual(6, len(human[0]))
        workbook_path = self.root / "cleanup-plan.xlsx"
        manifest = {"source_file": self.export_path.name, "source_sha256": payload["source_sha256"]}
        source = build_model(self.export_path)
        build_workbook(
            manifest,
            source,
            operational,
            configuration,
            architecture,
            payload,
            {"rows": human},
            workbook_path,
        )
        workbook = load_workbook(workbook_path)
        self.assertEqual(CANONICAL_SHEETS, workbook.sheetnames)
        self.assertEqual(
            ["01 Summary", "02 Cleanup Plan"],
            [s.title for s in workbook if s.sheet_state == "visible"],
        )
        for sheet in workbook:
            self.assertLessEqual(sheet.max_column, 6)
            self.assertLessEqual(
                max(sheet.column_dimensions[col].width or 0 for col in sheet.column_dimensions), 92
            )
            self.assertLessEqual(
                max(sheet.row_dimensions[row].height or 0 for row in sheet.row_dimensions), 120
            )
        self.assertNotIn("Change Log", workbook.sheetnames)
        gate_errors, gate_warnings = validate_workbook(
            workbook_path,
            self.write_review("workbook-operations.json", payload),
        )
        self.assertEqual([], gate_errors)
        self.assertEqual([], gate_warnings)

    def test_hidden_proof_is_split_losslessly_and_visible_text_is_not_truncated(self) -> None:
        try:
            from openpyxl import Workbook
        except ImportError:
            self.skipTest("openpyxl is not installed")
        proof = "source-bound-proof-" + ("x" * (MAX_CELL_TEXT + 41))
        workbook = Workbook()
        hidden = workbook.active
        hidden.title = "Hidden"
        add_table(hidden, [{"Evidence": proof}], ["Evidence"], split_long_cells=True)
        rendered = "".join(str(hidden.cell(row, 1).value or "") for row in range(2, hidden.max_row + 1))
        self.assertEqual(proof, rendered)
        self.assertNotIn("[truncated]", rendered.lower())

        visible = workbook.create_sheet("Visible")
        with self.assertRaisesRegex(ValueError, "summarize the user-facing row"):
            add_table(visible, [{"Problem": proof}], ["Problem"])

    def test_source_model_contains_nested_facts_and_dependency_edges(self) -> None:
        model = build_model(self.export_path)
        self.assertEqual("pass", model["coverage_gate"])
        self.assertGreater(model["counts"]["field_edges"], 0)
        self.assertGreater(model["counts"]["trigger_edges"], 0)

    def test_change_log_diff_is_field_level(self) -> None:
        before = container_version(sample_export())
        after = copy.deepcopy(before)
        after["tag"][0]["name"] = "GA4 - Purchase - Global"
        rows = diff_operations(before, after, "Direct", "Deep")
        self.assertEqual(1, len(rows))
        self.assertEqual("$.name", rows[0]["field_path"])
        change_log_path = self.root / "change-log.xlsx"
        build_change_log(
            {"kind": "gtm_field_level_change_log", "execution_mode": "planned", "changes": rows},
            change_log_path,
        )
        try:
            from openpyxl import load_workbook
        except ImportError:
            self.skipTest("openpyxl is not installed")
        workbook = load_workbook(change_log_path)
        self.assertLessEqual(len(workbook.sheetnames), 3)
        for sheet in workbook:
            self.assertLessEqual(sheet.max_column, 6)

    def test_executed_change_log_links_only_exact_approved_fields(self) -> None:
        operational, configuration, architecture = self.completed_reviews()
        align_duplicate_operation(operational, architecture)
        approved, errors = compile_operations(
            operational,
            configuration,
            architecture,
            "Direct GTM/MCP/API",
            "Deep",
            source_object_catalog(self.export_path),
        )
        self.assertEqual([], errors)
        future, apply_errors = apply_operations(sample_export(), approved)
        self.assertEqual([], apply_errors)
        after = container_version(future)
        after["tag"][0]["name"] = "Unexpected unapproved rename"
        rows = diff_operations(
            container_version(sample_export()),
            after,
            "Direct GTM/MCP/API",
            "Deep",
            approved,
            "executed",
        )
        deletion = next(row for row in rows if row["object_id"] == "21")
        unexpected = next(
            row
            for row in rows
            if row["object_id"] == "1" and row["field_path"] == "$.name"
        )
        self.assertTrue(deletion["operation_id"])
        self.assertEqual("Applied", deletion["status"])
        self.assertEqual("", unexpected["operation_id"])
        self.assertEqual("Blocked: missing approved operation link", unexpected["status"])

    def test_workbook_escapes_formula_text_and_privacy_scans_hidden_tabs(self) -> None:
        try:
            from openpyxl import Workbook, load_workbook
        except ImportError:
            self.skipTest("openpyxl is not installed")
        self.assertEqual("'=1+1", spreadsheet_safe_text("=1+1"))

        operational, configuration, architecture = self.completed_reviews()
        align_duplicate_operation(operational, architecture)
        payload, errors = compile_operations(
            operational,
            configuration,
            architecture,
            "Direct GTM/MCP/API",
            "Deep",
            source_object_catalog(self.export_path),
        )
        self.assertEqual([], errors)
        human, human_errors = build_rows(payload)
        self.assertEqual([], human_errors)
        human[0]["Problem / evidence"] = '=HYPERLINK("https://example.test","open")'
        workbook_path = self.root / "formula-safe.xlsx"
        build_workbook(
            {"source_file": self.export_path.name},
            build_model(self.export_path),
            operational,
            configuration,
            architecture,
            payload,
            {"rows": human},
            workbook_path,
        )
        rendered = load_workbook(workbook_path, data_only=False)
        formula_cell = rendered["02 Cleanup Plan"]["E2"]
        self.assertEqual("s", formula_cell.data_type)
        self.assertTrue(str(formula_cell.value).startswith("'="))
        rendered.close()

        privacy_path = self.root / "hidden-privacy.xlsx"
        raw = Workbook()
        raw.active.title = "Visible"
        hidden = raw.create_sheet("Hidden proof")
        hidden.sheet_state = "hidden"
        hidden["A1"] = "@".join(("analyst", "example.test"))
        raw.save(privacy_path)
        self.assertTrue(
            any("Hidden proof!A1" in finding for finding in scan_xlsx(privacy_path))
        )

    def test_privacy_helpers_redact_identity_and_sensitive_urls(self) -> None:
        address = "@".join(("jane.doe", "example.test"))
        text = f"Contact {address} or +33 6 12 34 56 78 token=secret-value"
        redacted = redact_text(text)
        self.assertNotIn(address, redacted)
        self.assertNotIn("secret-value", redacted)
        url_address = "@".join(("jane", "example.test"))
        url = sanitize_url(f"https://example.test/path?email={url_address}&utm_source=test")
        self.assertNotIn(url_address, url)
        self.assertIn("utm_source=%3Cvalue%3E", url)
        self.assertTrue(privacy_findings(text))

    def test_vendor_registry_is_current_and_structurally_valid(self) -> None:
        registry_path = ROOT / "references/03-rules/vendor-registry.toml"
        errors, warnings = validate_registry(registry_path, online=False, max_age_days=365)
        self.assertEqual([], errors)
        self.assertEqual([], warnings)
        self.assertGreaterEqual(len(load_registry(registry_path)["vendors"]), 15)
        self.assertEqual(
            "Universal Analytics (legacy)",
            vendor_record('{"type": "ua", "trackingId": "UA-123"}')["name"],
        )
        self.assertEqual(
            "Google Ads",
            vendor_record('{"type": "googtag", "tagId": "AW-123"}')["name"],
        )
        self.assertEqual(
            "GA4 / Google tag",
            vendor_record('{"type": "gaawe", "eventName": "purchase"}')["name"],
        )

    def test_vendor_url_check_falls_back_to_get_when_head_is_rejected(self) -> None:
        head_error = urllib.error.HTTPError(
            "https://example.invalid", 404, "HEAD rejected", {}, None
        )
        get_response = MagicMock()
        get_response.status = 200
        get_response.__enter__.return_value = get_response
        with patch(
            "gtm_vendor_registry.urllib.request.urlopen",
            side_effect=[head_error, get_response],
        ) as urlopen:
            self.assertIsNone(official_url_error("https://example.invalid"))
        self.assertEqual("HEAD", urlopen.call_args_list[0].args[0].method)
        self.assertEqual("GET", urlopen.call_args_list[1].args[0].method)

    def test_release_layout_allows_ignored_editable_install_metadata(self) -> None:
        errors = check_repository_layout(ROOT)
        self.assertEqual([], errors)

    def test_release_check_does_not_hide_git_tracking_failure(self) -> None:
        (self.root / ".git").mkdir()
        with patch(
            "check_release.subprocess.check_output",
            side_effect=subprocess.CalledProcessError(1, ["git", "ls-files"]),
        ), self.assertRaisesRegex(RuntimeError, "tracked release resources"):
            git_ls_files(self.root)

    def test_runtime_bundle_is_self_installable_and_excludes_repo_only_files(self) -> None:
        bundle = self.root / "runtime-bundle"
        build_skill_bundle(ROOT, bundle)
        for filename in ("SKILL.md", "LICENSE", "pyproject.toml"):
            self.assertTrue((bundle / filename).is_file())
        self.assertFalse((bundle / "README.md").exists())
        metadata = tomllib.loads((bundle / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertIsInstance(metadata["project"]["readme"], dict)
        self.assertNotIn("README.md", json.dumps(metadata["project"]["readme"]))
        for relative in (
            "scripts/gtm_operational_review.py",
            "scripts/gtm_configuration_review.py",
            "scripts/gtm_architecture_review.py",
            "scripts/gtm_review_common.py",
            "scripts/gtm_review_shards.py",
            "scripts/gtm_three_run_gate.py",
        ):
            self.assertTrue((bundle / relative).is_file())
        self.assertFalse((bundle / "tests").exists())
        self.assertFalse((bundle / ".github").exists())
        self.assertFalse((bundle / "scripts/check_release.py").exists())
        self.assertFalse((bundle / "scripts/gtm_self_test.py").exists())


if __name__ == "__main__":
    unittest.main()
