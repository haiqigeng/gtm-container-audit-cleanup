#!/usr/bin/env python3
"""Generate source-bound GTM cross-object comparison candidates.

The candidates are deterministic review obligations, not findings. Architecture
review must decide whether similar objects are duplicates, intentional variants,
complementary implementations, conflicting logic, or unrelated.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from itertools import combinations
from pathlib import Path
from typing import Any

from gtm_configuration_facts import parameter_static_values
from gtm_consent_model import consent_variable_conflicts
from gtm_lib import (
    ID_KEYS,
    SEMANTIC_LAYERS,
    comparable,
    container_version,
    is_system_trigger_reference,
    object_id,
    refs,
    source_descriptor,
    stable_hash,
    walk_json_fields,
)
from gtm_vendor_registry import vendor_record

COMMON_IGNORED = {"accountId", "containerId", "fingerprint", "path"}
IDENTITY_IGNORED = {
    **{layer: COMMON_IGNORED | {ID_KEYS[layer], "name"} for layer in SEMANTIC_LAYERS},
}
TAG_ROUTE_FIELDS = {
    "firingTriggerId",
    "blockingTriggerId",
    "parentFolderId",
    "notes",
    "scheduleStartMs",
    "scheduleEndMs",
}
DESTINATION_KEY_RE = re.compile(
    r"(?:measurement|property|pixel|advertiser|conversion|destination|tag|account).*id$",
    re.I,
)
PRIMARY_EVENT_KEYS = {"event", "eventname", "event_name", "action"}
SECONDARY_EVENT_KEYS = {"eventtype", "event_type", "tracktype"}
GENERIC_EVENT_VALUES = {
    "config",
    "custom",
    "custom_event",
    "event",
    "set",
    "standard",
    "standard_event",
    "track",
}
GENERIC_CONFIG_TOKENS = {
    "boolean",
    "false",
    "integer",
    "list",
    "map",
    "metadata",
    "parameter",
    "template",
    "true",
    "value",
}
GENERIC_NAME_TOKENS = {
    "all",
    "block",
    "cjs",
    "consent",
    "copy",
    "dlv",
    "event",
    "global",
    "gtm",
    "tag",
    "test",
    "tg",
    "trigger",
    "variable",
}
NAME_SYNONYMS = {
    "achat": "purchase",
    "commande": "purchase",
    "order": "purchase",
    "transaction": "purchase",
    "view": "impression",
    "display": "impression",
    "affichage": "impression",
    "etape": "step",
    "q": "question",
    "devis": "quote",
    "quotation": "quote",
    "basket": "cart",
    "panier": "cart",
}
DIMENSIONS_BY_LAYER = {
    "tag": [
        "purpose",
        "configuration",
        "execution_scope",
        "consumers",
        "output_payload",
        "consent_sequence",
    ],
    "trigger": ["purpose", "configuration", "execution_scope", "consumers"],
    "variable": ["purpose", "configuration", "consumers", "output_payload"],
    "customTemplate": [
        "purpose",
        "configuration",
        "consumers",
        "output_payload",
        "consent_sequence",
    ],
    "client": [
        "purpose",
        "configuration",
        "execution_scope",
        "consumers",
        "output_payload",
        "consent_sequence",
    ],
    "transformation": [
        "purpose",
        "configuration",
        "execution_scope",
        "consumers",
        "output_payload",
        "consent_sequence",
    ],
}
DISCOVERY_METHOD_BY_COMPARISON_TYPE = {
    "exact_configuration": "normalized_condition_and_route_variants",
    "duplicate_name": "semantic_name_and_business_term_variants",
    "same_tag_payload_different_route": "normalized_condition_and_route_variants",
    "same_vendor_destination_event": "consumer_destination_and_event_overlap",
    "same_vendor_event_family": "consumer_destination_and_event_overlap",
    "cross_vendor_event_family": "consumer_destination_and_event_overlap",
    "shared_execution_trigger": "normalized_condition_and_route_variants",
    "related_trigger_scope_tag_family": "funnel_question_market_and_product_families",
    "multi_firing_route_consolidation_review": "normalized_condition_and_route_variants",
    "semantic_name_family_candidate": "semantic_name_and_business_term_variants",
    "shared_terminal_source": "terminal_source_formula_and_output_overlap",
    "shared_input_variable_logic": "terminal_source_formula_and_output_overlap",
    "different_consent_purposes_same_logic": "consent_sequence_and_server_route_conflicts",
    "equivalent_custom_code": "terminal_source_formula_and_output_overlap",
    "equivalent_trigger_conditions": "normalized_condition_and_route_variants",
    "near_equivalent_trigger_conditions": "normalized_condition_and_route_variants",
    "trigger_condition_subset": "normalized_condition_and_route_variants",
    "shared_business_scope": "funnel_question_market_and_product_families",
}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def normalized_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text).strip().lower()


def parameter_value(obj: dict[str, Any], key: str) -> Any:
    for parameter in as_list(obj.get("parameter")):
        if str(parameter.get("key") or "") != key:
            continue
        for value_key in ("value", "list", "map"):
            if value_key in parameter:
                return parameter.get(value_key)
    return None


def object_key(layer: str, obj: dict[str, Any]) -> str:
    return f"{layer}:{object_id(obj, ID_KEYS[layer])}"


def object_hash(obj: dict[str, Any]) -> str:
    return stable_hash(comparable(obj, COMMON_IGNORED))


def logic_anchors(obj: dict[str, Any], source_path: str) -> list[str]:
    ignored_suffixes = tuple(
        f".{field}"
        for field in (
            "accountId",
            "containerId",
            "fingerprint",
            "path",
            "tagId",
            "triggerId",
            "variableId",
            "templateId",
            "clientId",
            "transformationId",
            "name",
        )
    )
    facts = walk_json_fields(obj, source_path)
    anchors = [
        fact["json_path"] for fact in facts if not fact["json_path"].endswith(ignored_suffixes)
    ]
    return anchors or [fact["json_path"] for fact in facts]


def config_specificity_tokens(obj: dict[str, Any]) -> list[str]:
    tokens = {
        normalized_text(reference)
        for reference in refs(obj)
        if len(normalized_text(reference)) >= 4
    }
    for parameter in as_list(obj.get("parameter")):
        key = normalized_text(parameter.get("key"))
        if len(key) >= 4 and key not in GENERIC_CONFIG_TOKENS:
            tokens.add(key)
    for fact in walk_json_fields(obj):
        preview = str(fact.get("value_preview") or "")
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_.-]{3,}", preview):
            normalized = normalized_text(token)
            if normalized not in GENERIC_CONFIG_TOKENS and "@" not in normalized:
                tokens.add(normalized)
    if not tokens:
        tokens.update(
            normalized_text(token)
            for token in re.findall(r"[A-Za-z][A-Za-z0-9_.-]{3,}", str(obj.get("name") or ""))
        )
    return sorted(token for token in tokens if token)[:60]


def object_records(cv: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    records: dict[str, list[dict[str, Any]]] = {}
    for layer in SEMANTIC_LAYERS:
        layer_records = []
        for index, obj in enumerate(as_list(cv.get(layer))):
            source_path = f"$.containerVersion.{layer}[{index}]"
            layer_records.append(
                {
                    "layer": layer,
                    "index": index,
                    "object": obj,
                    "object_key": object_key(layer, obj),
                    "object_id": object_id(obj, ID_KEYS[layer]),
                    "object_name": str(obj.get("name") or ""),
                    "object_type": str(
                        obj.get("type") or ("customTemplate" if layer == "customTemplate" else "")
                    ),
                    "paused": bool(obj.get("paused")) if layer == "tag" else False,
                    "config_hash": object_hash(obj),
                    "source_json_path": source_path,
                    "evidence_anchors": logic_anchors(obj, source_path),
                    "specificity_tokens": config_specificity_tokens(obj),
                    "resolved_event_values": (
                        parameter_static_values(cv, obj, "eventName")
                        if layer == "tag"
                        else []
                    ),
                }
            )
        records[layer] = layer_records
    return records


def keyed_record_groups(
    records: Iterable[dict[str, Any]], key_fn: Any
) -> list[tuple[str, list[dict[str, Any]]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = key_fn(record)
        if key:
            groups[str(key)].append(record)
    return [(key, group) for key, group in sorted(groups.items()) if len(group) >= 2]


def group_records(records: Iterable[dict[str, Any]], key_fn: Any) -> list[list[dict[str, Any]]]:
    return [group for _, group in keyed_record_groups(records, key_fn)]


def nested_key_values(value: Any) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    if isinstance(value, dict):
        key = str(value.get("key") or "")
        scalar = value.get("value")
        if key and scalar is not None and not isinstance(scalar, (dict, list)):
            pairs.append((key, str(scalar)))
        for child in value.values():
            pairs.extend(nested_key_values(child))
    elif isinstance(value, list):
        for child in value:
            pairs.extend(nested_key_values(child))
    return pairs


def tag_contract(record: dict[str, Any]) -> dict[str, Any]:
    obj = record["object"]
    pairs = nested_key_values(obj.get("parameter", []))
    destinations = sorted(
        normalized_text(value)
        for key, value in pairs
        if (
            DESTINATION_KEY_RE.search(normalized_text(key))
            or normalized_text(key) == "conversionlabel"
        )
        and str(value).strip()
    )
    primary_events = sorted(
        normalized_text(value)
        for key, value in pairs
        if normalized_text(key) in PRIMARY_EVENT_KEYS
        and normalized_text(value) not in GENERIC_EVENT_VALUES
        and str(value).strip()
    )
    secondary_events = sorted(
        normalized_text(value)
        for key, value in pairs
        if normalized_text(key) in SECONDARY_EVENT_KEYS
        and normalized_text(value) not in GENERIC_EVENT_VALUES
        and str(value).strip()
    )
    resolved_events = sorted(
        {
            normalized_text(value)
            for value in as_list(record.get("resolved_event_values"))
            if normalized_text(value) not in GENERIC_EVENT_VALUES
        }
    )
    events = resolved_events or primary_events or secondary_events
    if not events:
        return {}
    vendor = str(vendor_record(json.dumps(obj, ensure_ascii=False)).get("name") or "")
    return {
        "vendor": vendor,
        "type": record["object_type"],
        "destinations": destinations,
        "events": events,
    }


def tag_contract_key(record: dict[str, Any]) -> str:
    contract = tag_contract(record)
    return json.dumps(contract, sort_keys=True) if contract else ""


def tag_event_family_key(record: dict[str, Any]) -> str:
    contract = tag_contract(record)
    if not contract:
        return ""
    return json.dumps(
        {
            "vendor": contract["vendor"],
            "type": contract["type"],
            "events": contract["events"],
        },
        sort_keys=True,
    )


def tag_business_event_key(record: dict[str, Any]) -> str:
    contract = tag_contract(record)
    return json.dumps(contract.get("events"), sort_keys=True) if contract else ""


def custom_code(obj: dict[str, Any]) -> str:
    for key in ("html", "javascript"):
        value = parameter_value(obj, key)
        if value is not None:
            return re.sub(r"\s+", " ", str(value)).strip()
    return ""


def condition_parameters(node: dict[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    for parameter in as_list(node.get("parameter")):
        key = str(parameter.get("key") or "")
        if key and parameter.get("value") is not None:
            values[key] = str(parameter.get("value"))
    return values


def regex_literal(pattern: str) -> tuple[str, str] | None:
    value = pattern
    if value.startswith("^") and value.endswith("$"):
        inner = value[1:-1]
        if not re.search(r"[.\\+*?\[\](){}|]", inner):
            return "EQUALS", inner
    if value.startswith(".*") and value.endswith(".*"):
        inner = value[2:-2]
        if inner and not re.search(r"[.\\+*?\[\](){}|]", inner):
            return "CONTAINS", inner
    return None


def normalized_condition(node: dict[str, Any]) -> str:
    operator = str(node.get("type") or "").upper()
    values = condition_parameters(node)
    left = normalized_text(values.get("arg0"))
    right = normalized_text(values.get("arg1"))
    if operator == "MATCH_REGEX":
        normalized = regex_literal(str(values.get("arg1") or ""))
        if normalized:
            operator, right = normalized[0], normalized_text(normalized[1])
    modifiers = sorted(
        [
            f"{key}={normalized_text(value)}"
            for key, value in values.items()
            if key not in {"arg0", "arg1"}
        ]
        + [
            f"{key}={normalized_text(value)}"
            for key, value in node.items()
            if key not in {"type", "parameter"} and not isinstance(value, (dict, list))
        ]
    )
    return f"{operator}|{left}|{right}|{'&'.join(modifiers)}"


def trigger_conditions(value: Any) -> list[str]:
    conditions: list[str] = []
    if isinstance(value, dict):
        operator = str(value.get("type") or "").upper()
        parameters = condition_parameters(value)
        if operator and "arg0" in parameters and "arg1" in parameters:
            conditions.append(normalized_condition(value))
        for child in value.values():
            conditions.extend(trigger_conditions(child))
    elif isinstance(value, list):
        for child in value:
            conditions.extend(trigger_conditions(child))
    return sorted(set(conditions))


def business_scope_tokens(record: dict[str, Any]) -> set[str]:
    obj = record["object"]
    text = normalized_text(
        " ".join(
            [
                record["object_name"],
                *trigger_conditions(obj),
            ]
        )
    )
    separated = re.sub(r"[_/.-]+", " ", text)
    tokens = {
        f"step:{int(match.group(1))}"
        for match in re.finditer(
            r"\b(?:q|question|step|etape|funnel\s+step)\s*0*(\d{1,3})\b",
            separated,
        )
    }
    for condition in trigger_conditions(obj):
        operator, left, right, _modifiers = condition.split("|", 3)
        del operator
        if left in {"{{_event}}", "_event"} and right:
            tokens.add(f"event:{right}")
    return tokens


def semantic_name_tokens(record: dict[str, Any]) -> set[str]:
    text = re.sub(r"[^a-z0-9]+", " ", normalized_text(record["object_name"]))
    values = []
    for token in text.split():
        canonical = NAME_SYNONYMS.get(token, token)
        if canonical in GENERIC_NAME_TOKENS or len(canonical) < 2:
            continue
        values.append(canonical)
    tokens = set(values)
    for match in re.finditer(r"\b(?:q|question|step|etape)\s*0*(\d{1,3})\b", text):
        tokens.add(f"step:{int(match.group(1))}")
    return tokens


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


class CandidateBuilder:
    def __init__(self) -> None:
        self._candidates: dict[tuple[str, ...], dict[str, Any]] = {}

    def add(
        self,
        comparison_type: str,
        records: Iterable[dict[str, Any]],
        basis: str,
        similarity_score: float,
    ) -> None:
        unique = {record["object_key"]: record for record in records}
        if len(unique) < 2:
            return
        members = [unique[key] for key in sorted(unique)]
        member_keys = tuple(record["object_key"] for record in members)
        current = self._candidates.get(member_keys)
        if current is None:
            layer_values = {record["layer"] for record in members}
            layer = next(iter(layer_values)) if len(layer_values) == 1 else "mixed"
            current = {
                "comparison_id": f"REL-{stable_hash(member_keys, 12).upper()}",
                "comparison_origin": "deterministic",
                "layer": layer,
                "candidate_object_keys": list(member_keys),
                "candidate_object_ids": [record["object_id"] for record in members],
                "candidate_object_names": [record["object_name"] for record in members],
                "candidate_object_types": [record["object_type"] for record in members],
                "candidate_config_hashes": {
                    record["object_key"]: record["config_hash"] for record in members
                },
                "candidate_source_paths": {
                    record["object_key"]: record["source_json_path"] for record in members
                },
                "candidate_paused_status": {
                    record["object_key"]: record["paused"] for record in members
                },
                "available_member_evidence_anchors": {
                    record["object_key"]: record["evidence_anchors"] for record in members
                },
                "candidate_specificity_tokens": {
                    record["object_key"]: record["specificity_tokens"] for record in members
                },
                "comparison_types": [],
                "candidate_basis": [],
                "similarity_score": 0.0,
                "required_comparison_dimensions": DIMENSIONS_BY_LAYER.get(
                    layer,
                    ["purpose", "configuration", "execution_scope", "consumers"],
                ),
            }
            self._candidates[member_keys] = current
        if comparison_type not in current["comparison_types"]:
            current["comparison_types"].append(comparison_type)
        if basis not in current["candidate_basis"]:
            current["candidate_basis"].append(basis)
        current["similarity_score"] = max(current["similarity_score"], similarity_score)

    def rows(self) -> list[dict[str, Any]]:
        rows = []
        for candidate in self._candidates.values():
            candidate["comparison_types"] = sorted(candidate["comparison_types"])
            candidate["comparison_type"] = candidate["comparison_types"][0]
            candidate["discovery_methods"] = sorted(
                {
                    DISCOVERY_METHOD_BY_COMPARISON_TYPE[comparison_type]
                    for comparison_type in candidate["comparison_types"]
                    if comparison_type in DISCOVERY_METHOD_BY_COMPARISON_TYPE
                }
            )
            candidate["candidate_basis"] = sorted(candidate["candidate_basis"])
            candidate["similarity_score"] = round(candidate["similarity_score"], 3)
            rows.append(candidate)
        return sorted(rows, key=lambda row: row["comparison_id"])


def add_exact_candidates(
    builder: CandidateBuilder, records: dict[str, list[dict[str, Any]]]
) -> None:
    for layer, layer_records in records.items():
        for group in group_records(
            layer_records,
            lambda record, current_layer=layer: stable_hash(
                comparable(record["object"], IDENTITY_IGNORED[current_layer])
            ),
        ):
            builder.add(
                "exact_configuration",
                group,
                "Objects share the same configuration after identity and export metadata are removed.",
                1.0,
            )
        for group in group_records(
            layer_records,
            lambda record: normalized_text(record["object_name"]),
        ):
            builder.add(
                "duplicate_name",
                group,
                "Objects share the same normalized name and require configuration comparison.",
                1.0,
            )

    for group in group_records(
        records.get("tag", []),
        lambda record: stable_hash(
            comparable(
                record["object"],
                IDENTITY_IGNORED["tag"] | TAG_ROUTE_FIELDS,
            )
        ),
    ):
        builder.add(
            "same_tag_payload_different_route",
            group,
            "Tag payload configuration matches after trigger, schedule, folder, and note fields are removed.",
            1.0,
        )


def add_tag_family_candidates(builder: CandidateBuilder, tags: list[dict[str, Any]]) -> None:
    for key, group in keyed_record_groups(tags, tag_contract_key):
        contract = json.loads(key)
        builder.add(
            "same_vendor_destination_event",
            group,
            "Tags expose the same configured vendor "
            f"{contract['vendor']!r}, destination values {contract['destinations']!r}, "
            f"and event or action values {contract['events']!r}.",
            0.95,
        )
    for key, group in keyed_record_groups(tags, tag_event_family_key):
        contract = json.loads(key)
        builder.add(
            "same_vendor_event_family",
            group,
            "Tags expose the same configured vendor "
            f"{contract['vendor']!r} and event or action values {contract['events']!r}, "
            "including destination variants.",
            0.85,
        )
    for key, group in keyed_record_groups(tags, tag_business_event_key):
        vendors = {str(tag_contract(record).get("vendor") or "") for record in group}
        if len(vendors) < 2:
            continue
        builder.add(
            "cross_vendor_event_family",
            group,
            "Tags expose the same configured event or action values "
            f"{json.loads(key)!r} across vendor implementations.",
            0.75,
        )

    tags_by_trigger: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in tags:
        for trigger_id in sorted(
            {
                str(value)
                for value in as_list(record["object"].get("firingTriggerId"))
                if not is_system_trigger_reference(str(value))
            }
        ):
            tags_by_trigger[trigger_id].append(record)
    for trigger_id, group in sorted(tags_by_trigger.items()):
        if len(group) < 2:
            continue
        builder.add(
            "shared_execution_trigger",
            group,
            f"Tags share non-system firing trigger {trigger_id} and overlap on that execution path.",
            0.8,
        )


def add_tag_trigger_scope_candidates(
    builder: CandidateBuilder,
    tags: list[dict[str, Any]],
    triggers: list[dict[str, Any]],
) -> None:
    trigger_tokens: dict[str, set[str]] = {}
    for trigger in triggers:
        trigger_id = str(trigger["object_id"])
        tokens = {token for token in business_scope_tokens(trigger) if token.startswith("step:")}
        conditions = trigger_conditions(trigger["object"])
        if conditions:
            tokens.add(f"conditions:{trigger['object_type']}:{stable_hash(conditions)}")
        trigger_tokens[trigger_id] = tokens

    tags_by_scope: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for tag in tags:
        tag_tokens: set[str] = set()
        for trigger_id in as_list(tag["object"].get("firingTriggerId")):
            tag_tokens.update(trigger_tokens.get(str(trigger_id), set()))
        for token in tag_tokens:
            tags_by_scope[token].append(tag)
    for token, group in sorted(tags_by_scope.items()):
        if len({record["object_key"] for record in group}) < 2:
            continue
        builder.add(
            "related_trigger_scope_tag_family",
            group,
            f"Tags fire through triggers sharing normalized scope {token!r}.",
            0.75,
        )


def add_multi_firing_route_candidates(
    builder: CandidateBuilder,
    tags: list[dict[str, Any]],
    triggers: list[dict[str, Any]],
) -> None:
    triggers_by_id = {str(record["object_id"]): record for record in triggers}
    for tag in tags:
        trigger_ids = sorted(
            {
                str(value)
                for value in as_list(tag["object"].get("firingTriggerId"))
                if not is_system_trigger_reference(str(value))
            }
        )
        members = [triggers_by_id[value] for value in trigger_ids if value in triggers_by_id]
        if len(members) < 2:
            continue
        builder.add(
            "multi_firing_route_consolidation_review",
            members,
            (
                f"Tag {tag['object_key']} fires through {len(members)} non-system triggers "
                f"{trigger_ids!r}; compare their event types, predicates, exclusions, and "
                "readability before deciding whether one canonical route can preserve the OR logic."
            ),
            0.7,
        )


def add_semantic_name_candidates(
    builder: CandidateBuilder,
    records: dict[str, list[dict[str, Any]]],
) -> None:
    for layer, layer_records in records.items():
        by_key = {record["object_key"]: record for record in layer_records}
        token_sets = {
            record["object_key"]: semantic_name_tokens(record) for record in layer_records
        }
        inverted: dict[str, set[str]] = defaultdict(set)
        for key, tokens in token_sets.items():
            for token in tokens:
                inverted[token].add(key)
        pairs: set[tuple[str, str]] = set()
        for keys in inverted.values():
            pairs.update(combinations(sorted(keys), 2))
        for left_key, right_key in sorted(pairs):
            left_tokens = token_sets[left_key]
            right_tokens = token_sets[right_key]
            if not left_tokens or not right_tokens:
                continue
            score = jaccard(left_tokens, right_tokens)
            shared_scope = {
                token for token in left_tokens & right_tokens if token.startswith("step:")
            }
            if score < 0.67 and not shared_scope:
                continue
            builder.add(
                "semantic_name_family_candidate",
                (by_key[left_key], by_key[right_key]),
                (
                    f"{layer} names normalize to related business tokens "
                    f"{sorted(left_tokens & right_tokens)!r}; names are only a discovery signal, "
                    "so compare complete configuration chains before any consolidation."
                ),
                max(0.6, score),
            )


def add_variable_candidates(builder: CandidateBuilder, variables: list[dict[str, Any]]) -> None:
    for key, group in keyed_record_groups(
        variables,
        lambda record: (
            f"{record['object_type']}|{parameter_value(record['object'], 'name')}"
            if parameter_value(record["object"], "name")
            else ""
        ),
    ):
        builder.add(
            "shared_terminal_source",
            group,
            "Variables share configured type and terminal source "
            f"{key!r} and require consumer comparison.",
            1.0,
        )

    def shared_input_key(record: dict[str, Any]) -> str:
        references = sorted(refs(record["object"]))
        if not references or record["object_type"] == "v":
            return ""
        return json.dumps({"type": record["object_type"], "references": references}, sort_keys=True)

    for key, group in keyed_record_groups(variables, shared_input_key):
        shared = json.loads(key)
        builder.add(
            "shared_input_variable_logic",
            group,
            "Variables of type "
            f"{shared['type']!r} consume the same GTM inputs {shared['references']!r} "
            "but may map them differently.",
            0.85,
        )

    records_by_id = {str(record["object_id"]): record for record in variables}
    source_variables = [record["object"] for record in variables]
    for conflict in consent_variable_conflicts(source_variables):
        members = [
            records_by_id.get(str(variable.get("variableId") or variable.get("name") or ""))
            for variable in conflict["variables"]
        ]
        builder.add(
            "different_consent_purposes_same_logic",
            [member for member in members if member],
            (
                f"Consent purposes {conflict['purposes']!r} share exported logic signature "
                f"{conflict['logic_hash']}; compare CMP category semantics before retaining "
                "or separating the variables."
            ),
            1.0,
        )


def add_code_candidates(
    builder: CandidateBuilder, records: dict[str, list[dict[str, Any]]]
) -> None:
    for layer in ("tag", "variable"):
        for code_hash, group in keyed_record_groups(
            records.get(layer, []),
            lambda record: (
                stable_hash(custom_code(record["object"])) if custom_code(record["object"]) else ""
            ),
        ):
            builder.add(
                "equivalent_custom_code",
                group,
                "Custom code is identical after whitespace normalization "
                f"under signature {code_hash}.",
                1.0,
            )


def add_trigger_candidates(builder: CandidateBuilder, triggers: list[dict[str, Any]]) -> None:
    for key, group in keyed_record_groups(
        triggers,
        lambda record: (
            json.dumps(
                {
                    "type": record["object_type"],
                    "conditions": trigger_conditions(record["object"]),
                },
                sort_keys=True,
            )
            if trigger_conditions(record["object"])
            else ""
        ),
    ):
        condition_count = len(json.loads(key)["conditions"])
        builder.add(
            "equivalent_trigger_conditions",
            group,
            "Trigger conditions normalize to the same operator, variable, value, and "
            f"modifier set with {condition_count} condition(s) under signature "
            f"{stable_hash(key)}.",
            1.0,
        )

    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in triggers:
        by_type[record["object_type"]].append(record)
    for type_records in by_type.values():
        records_by_key = {record["object_key"]: record for record in type_records}
        condition_sets = {
            record["object_key"]: set(trigger_conditions(record["object"]))
            for record in type_records
        }
        inverted: dict[str, set[str]] = defaultdict(set)
        for record_key, conditions in condition_sets.items():
            for condition in conditions:
                inverted[condition].add(record_key)
        candidate_pairs: set[tuple[str, str]] = set()
        for keys in inverted.values():
            candidate_pairs.update(combinations(sorted(keys), 2))

        for left_key, right_key in sorted(candidate_pairs):
            left = records_by_key[left_key]
            right = records_by_key[right_key]
            left_conditions = condition_sets[left_key]
            right_conditions = condition_sets[right_key]
            if left_conditions == right_conditions:
                continue
            score = jaccard(left_conditions, right_conditions)
            if score >= 0.8:
                builder.add(
                    "near_equivalent_trigger_conditions",
                    (left, right),
                    "Trigger condition sets reach at least 80 percent Jaccard similarity after normalization.",
                    score,
                )
            shared_scope = business_scope_tokens(left) & business_scope_tokens(right)
            if shared_scope and (
                left_conditions < right_conditions or right_conditions < left_conditions
            ):
                builder.add(
                    "trigger_condition_subset",
                    (left, right),
                    "One trigger condition set is a strict subset of another within a shared event or step scope.",
                    len(left_conditions & right_conditions)
                    / max(len(left_conditions), len(right_conditions)),
                )

    scoped_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in triggers:
        for token in business_scope_tokens(record):
            if not token.startswith("step:"):
                continue
            scoped_groups[f"{record['object_type']}|{token}"].append(record)
    for scope_key, group in sorted(scoped_groups.items()):
        if len({record["object_key"] for record in group}) < 2:
            continue
        builder.add(
            "shared_business_scope",
            group,
            f"Triggers share canonical scope {scope_key.split('|', 1)[1]!r} despite differing names or conditions.",
            0.7,
        )


def relationship_candidates(cv: dict[str, Any]) -> list[dict[str, Any]]:
    records = object_records(cv)
    builder = CandidateBuilder()
    add_exact_candidates(builder, records)
    add_tag_family_candidates(builder, records.get("tag", []))
    add_variable_candidates(builder, records.get("variable", []))
    add_code_candidates(builder, records)
    add_trigger_candidates(builder, records.get("trigger", []))
    add_tag_trigger_scope_candidates(
        builder,
        records.get("tag", []),
        records.get("trigger", []),
    )
    add_multi_firing_route_candidates(
        builder,
        records.get("tag", []),
        records.get("trigger", []),
    )
    add_semantic_name_candidates(builder, records)
    return builder.rows()


def scan_export(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = relationship_candidates(container_version(data))
    return {
        **source_descriptor(path),
        "kind": "gtm_relationship_comparison_candidates",
        "schema_version": 1,
        "candidate_count": len(rows),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            scan_export(args.export),
            ensure_ascii=False,
            indent=2 if args.pretty else None,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
