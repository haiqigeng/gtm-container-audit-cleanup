#!/usr/bin/env python3
"""Source-bound facts used by the independent configuration review."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from gtm_lib import (
    ID_KEYS,
    SEMANTIC_LAYERS,
    comparable,
    custom_template_id,
    is_system_variable_reference,
    object_id,
    refs,
    safe_scalar_preview,
    stable_hash,
    trigger_group_members,
    walk_json_fields,
)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def word_count(value: Any) -> int:
    return len(re.findall(r"\b[\w{}.-]+\b", str(value or "")))


TRACE_GENERIC_PHRASES = (
    "fixture",
    "exact exported",
    "configured result",
    "declared by its exported variable type",
    "source value listed here",
    "consumer expects",
)


def concrete_trace_text(
    value: Any,
    minimum: int = 5,
    required_terms: list[str] | None = None,
    required_hits: int = 1,
) -> bool:
    text = str(value or "").strip().lower()
    if word_count(text) < minimum or any(phrase in text for phrase in TRACE_GENERIC_PHRASES):
        return False
    terms = [str(term).strip().lower() for term in required_terms or [] if str(term).strip()]
    return not terms or sum(term in text for term in terms) >= min(required_hits, len(terms))


def layer_objects(cv: dict[str, Any]) -> list[tuple[str, int, dict[str, Any]]]:
    return [
        (layer, index, obj)
        for layer in SEMANTIC_LAYERS
        for index, obj in enumerate(as_list(cv.get(layer)))
    ]


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

    for tag_index, tag in enumerate(as_list(cv.get("tag"))):
        tag_key = object_key("tag", tag)
        tag_name = str(tag.get("name") or "")
        for relation in ("firingTriggerId", "blockingTriggerId"):
            for trigger_id in as_list(tag.get(relation)):
                consumers[f"trigger-id:{trigger_id}"].append(
                    {
                        "consumer_key": tag_key,
                        "consumer_name": tag_name,
                        "relation": relation,
                        "source_json_path": f"$.containerVersion.tag[{tag_index}].{relation}",
                    }
                )
        for relation in ("setupTag", "teardownTag"):
            for reference_index, reference in enumerate(as_list(tag.get(relation))):
                referenced_name = str(reference.get("tagName") or "")
                if referenced_name:
                    consumers[f"tag-name:{referenced_name}"].append(
                        {
                            "consumer_key": tag_key,
                            "consumer_name": tag_name,
                            "relation": relation,
                            "source_json_path": (
                                f"$.containerVersion.tag[{tag_index}].{relation}"
                                f"[{reference_index}].tagName"
                            ),
                        }
                    )

    trigger_indexes = {
        str(trigger.get("triggerId") or ""): index
        for index, trigger in enumerate(as_list(cv.get("trigger")))
    }
    for trigger_index, trigger in enumerate(as_list(cv.get("trigger"))):
        group_key = object_key("trigger", trigger)
        for member_id in trigger_group_members(trigger):
            if str(member_id) not in trigger_indexes:
                continue
            consumers[f"trigger-id:{member_id}"].append(
                {
                    "consumer_key": group_key,
                    "consumer_name": str(trigger.get("name") or ""),
                    "relation": "trigger_group_member",
                    "source_json_path": (f"$.containerVersion.trigger[{trigger_index}].parameter"),
                }
            )

    for layer, index, obj in layer_objects(cv):
        folder_id = str(obj.get("parentFolderId") or "")
        if folder_id:
            consumers[f"folder-id:{folder_id}"].append(
                {
                    "consumer_key": object_key(layer, obj),
                    "consumer_name": str(obj.get("name") or ""),
                    "relation": "parent_folder",
                    "source_json_path": (f"$.containerVersion.{layer}[{index}].parentFolderId"),
                }
            )

    for layer in ("tag", "variable", "client", "transformation"):
        for index, obj in enumerate(as_list(cv.get(layer))):
            template_id = custom_template_id(obj)
            if template_id:
                consumers[f"template-id:{template_id}"].append(
                    {
                        "consumer_key": object_key(layer, obj),
                        "consumer_name": str(obj.get("name") or ""),
                        "relation": "custom_template",
                        "source_json_path": f"$.containerVersion.{layer}[{index}].type",
                    }
                )
    return dict(consumers)


def object_consumers(
    layer: str, obj: dict[str, Any], consumers: dict[str, list[dict[str, str]]]
) -> list[dict[str, str]]:
    keys = {
        "variable": f"variable-name:{obj.get('name') or ''}",
        "trigger": f"trigger-id:{obj.get('triggerId') or ''}",
        "customTemplate": f"template-id:{obj.get('templateId') or ''}",
        "tag": f"tag-name:{obj.get('name') or ''}",
        "folder": f"folder-id:{obj.get('folderId') or ''}",
    }
    return consumers.get(keys.get(layer, ""), [])


def specific_tokens(obj: dict[str, Any]) -> list[str]:
    tokens: set[str] = {
        token.lower() for token in re.findall(r"[A-Za-z0-9_.-]{4,}", str(obj.get("name") or ""))
    }
    for parameter in as_list(obj.get("parameter")):
        key = str(parameter.get("key") or "")
        if len(key) >= 4:
            tokens.add(key.lower())
    tokens.update(reference.lower() for reference in refs(obj) if len(reference) >= 4)
    for trigger_id in as_list(obj.get("firingTriggerId")) + as_list(obj.get("blockingTriggerId")):
        tokens.add(str(trigger_id).lower())
    for fact in walk_json_fields(obj):
        for token in re.findall(
            r"(?:ecommerce|eventModel|items?|products?|consent|storage)"
            r"[A-Za-z0-9_.\[\]-]*",
            str(fact.get("value_preview") or ""),
            re.I,
        ):
            if len(token) >= 4:
                tokens.add(token.lower())
    return sorted(tokens)[:80]


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


def static_reference_values(
    cv: dict[str, Any],
    reference: str,
    active: tuple[str, ...] = (),
) -> list[str]:
    """Resolve source-visible scalar outcomes without inventing runtime values."""
    if reference in active:
        return []
    variable = next(
        (
            item
            for item in as_list(cv.get("variable"))
            if str(item.get("name") or "") == reference
        ),
        None,
    )
    if not variable:
        return []
    variable_type = str(variable.get("type") or "")
    if variable_type == "c":
        value = parameter_value(variable, "value").strip()
        return [value] if value else []
    if variable_type == "jsm":
        code = parameter_value(variable, "javascript")
        match = re.fullmatch(
            r"\s*function\s*\(\s*\)\s*\{\s*return\s+(['\"])(.*?)\1\s*;?\s*\}\s*",
            code,
            re.S,
        )
        return [match.group(2)] if match else []
    values: list[str] = []
    for parameter in as_list(variable.get("parameter")):
        key = str(parameter.get("key") or "").lower()
        if key not in {"defaultvalue", "output", "value"}:
            continue
        raw = parameter.get("value")
        if not isinstance(raw, str):
            continue
        values.extend(static_scalar_values(cv, raw, (*active, reference)))
    return list(dict.fromkeys(value for value in values if value))


def static_scalar_values(
    cv: dict[str, Any],
    raw_value: str,
    active: tuple[str, ...] = (),
) -> list[str]:
    """Return only literal or recursively source-resolved scalar outcomes."""
    value = str(raw_value or "").strip()
    references = re.findall(r"\{\{([^{}]+)\}\}", value)
    if not references:
        return [value] if value else []
    if value != f"{{{{{references[0]}}}}}" or len(references) != 1:
        return []
    return static_reference_values(cv, references[0], active)


def parameter_static_values(
    cv: dict[str, Any], obj: dict[str, Any], key: str
) -> list[str]:
    return static_scalar_values(cv, parameter_value(obj, key))


def code_body(layer: str, obj: dict[str, Any]) -> str:
    if layer == "tag":
        return parameter_value(obj, "html")
    if layer == "variable":
        return parameter_value(obj, "javascript")
    if layer == "customTemplate":
        return str(obj.get("templateData") or "")
    return ""


def code_line_facts(layer: str, obj: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "line_number": line_number,
            "line_hash": stable_hash({"line_number": line_number, "line": line.strip()}),
            "line_preview": safe_scalar_preview(line.strip(), 120),
        }
        for line_number, line in enumerate(code_body(layer, obj).splitlines(), start=1)
        if line.strip()
    ]


def reference_trace_requirements(cv: dict[str, Any], obj: dict[str, Any]) -> list[dict[str, Any]]:
    variables = {
        str(variable.get("name") or ""): (index, variable)
        for index, variable in enumerate(as_list(cv.get("variable")))
        if variable.get("name")
    }
    builtins = {
        str(variable.get("name") or "")
        for variable in as_list(cv.get("builtInVariable"))
        if variable.get("name")
    }

    def visit(
        reference: str,
        active: tuple[str, ...],
        parent_key: str,
        object_keys: set[str],
        anchors: set[str],
        terminal_states: set[str],
        nodes: dict[str, dict[str, Any]],
        edges: set[tuple[str, str, str]],
        terminals: dict[str, dict[str, str]],
    ) -> None:
        if is_system_variable_reference(reference):
            terminal_states.add("system")
            terminal_key = f"system:{reference}"
            terminals[terminal_key] = {
                "terminal_key": terminal_key,
                "state": "system",
                "reference": reference,
                "source_object_key": "",
                "configured_source": f"GTM system variable {reference}",
            }
            return
        if reference in builtins:
            terminal_states.add("built_in")
            terminal_key = f"built_in:{reference}"
            terminals[terminal_key] = {
                "terminal_key": terminal_key,
                "state": "built_in",
                "reference": reference,
                "source_object_key": "",
                "configured_source": f"Enabled GTM built-in variable {reference}",
            }
            return
        if reference in active:
            terminal_states.add("cycle")
            terminal_key = f"cycle:{reference}"
            terminals[terminal_key] = {
                "terminal_key": terminal_key,
                "state": "cycle",
                "reference": reference,
                "source_object_key": parent_key,
                "configured_source": " -> ".join((*active, reference)),
            }
            return
        target = variables.get(reference)
        if not target:
            terminal_states.add("missing")
            terminal_key = f"missing:{reference}"
            terminals[terminal_key] = {
                "terminal_key": terminal_key,
                "state": "missing",
                "reference": reference,
                "source_object_key": parent_key,
                "configured_source": f"Missing GTM variable named {reference}",
            }
            return
        index, variable = target
        current_key = object_key("variable", variable)
        object_keys.add(current_key)
        facts = walk_json_fields(variable, f"$.containerVersion.variable[{index}]")
        variable_anchors = logic_anchors(facts)
        anchors.update(variable_anchors)
        children = sorted(
            child for child in refs(variable) if not is_system_variable_reference(child)
        )
        nodes[current_key] = {
            "object_key": current_key,
            "object_name": str(variable.get("name") or ""),
            "object_type": object_type("variable", variable),
            "config_hash": object_hash(variable),
            "source_json_path": f"$.containerVersion.variable[{index}]",
            "required_evidence_anchors": variable_anchors,
            "referenced_variables": children,
            "specificity_tokens": specific_tokens(variable),
            "configured_parameters": [
                {
                    "key": str(parameter.get("key") or ""),
                    "type": str(parameter.get("type") or ""),
                    "value_preview": safe_scalar_preview(parameter.get("value"), 160),
                }
                for parameter in as_list(variable.get("parameter"))
            ],
            "semantic_role": {
                "v": "data_layer_read",
                "c": "constant_value",
                "jsm": "custom_javascript_computation",
                "smm": "lookup_or_mapping",
            }.get(object_type("variable", variable), "configured_variable_transformation"),
        }
        if parent_key:
            edges.add((parent_key, current_key, reference))
        if not children:
            terminal_states.add("resolved")
            terminal_key = f"resolved:{current_key}"
            configured_source = "; ".join(
                f"{parameter.get('key')}={safe_scalar_preview(parameter.get('value'), 80)}"
                for parameter in as_list(variable.get("parameter"))
                if parameter.get("key") and parameter.get("value") is not None
            )
            terminals[terminal_key] = {
                "terminal_key": terminal_key,
                "state": "resolved",
                "reference": reference,
                "source_object_key": current_key,
                "configured_source": configured_source
                or f"Terminal GTM variable type {object_type('variable', variable)}",
            }
            return
        for child in children:
            visit(
                child,
                (*active, reference),
                current_key,
                object_keys,
                anchors,
                terminal_states,
                nodes,
                edges,
                terminals,
            )

    requirements = []
    for reference in sorted(refs(obj)):
        if is_system_variable_reference(reference):
            continue
        object_keys: set[str] = set()
        anchors: set[str] = set()
        terminal_states: set[str] = set()
        nodes: dict[str, dict[str, Any]] = {}
        edges: set[tuple[str, str, str]] = set()
        terminals: dict[str, dict[str, str]] = {}
        visit(
            reference,
            (),
            "",
            object_keys,
            anchors,
            terminal_states,
            nodes,
            edges,
            terminals,
        )
        requirements.append(
            {
                "reference": reference,
                "required_object_keys": sorted(object_keys),
                "required_evidence_anchors": sorted(anchors),
                "terminal_states": sorted(terminal_states),
                "required_nodes": [nodes[key] for key in sorted(nodes)],
                "required_edges": [
                    {
                        "from_object_key": source,
                        "to_object_key": target,
                        "reference": child_reference,
                    }
                    for source, target, child_reference in sorted(edges)
                ],
                "terminal_requirements": [terminals[key] for key in sorted(terminals)],
            }
        )
    return requirements


TRACE_NODE_LOCK_FIELDS = (
    "object_name",
    "object_type",
    "config_hash",
    "source_json_path",
    "referenced_variables",
    "configured_parameters",
    "semantic_role",
)
TRACE_NODE_SEMANTIC_FIELDS = (
    "configured_function",
    "configured_output",
    "output_type_and_shape",
    "availability_and_fallback",
    "consumer_compatibility",
)
TRACE_ROLE_TERMS = {
    "data_layer_read": ("data layer", "datalayer", "path", "key"),
    "constant_value": ("constant", "fixed", "literal"),
    "custom_javascript_computation": (
        "javascript",
        "return",
        "calculate",
        "map",
        "format",
    ),
    "lookup_or_mapping": ("lookup", "map", "match", "default"),
    "configured_variable_transformation": ("read", "return", "transform", "select"),
}


def validate_trace_header(
    trace: dict[str, Any], requirement: dict[str, Any], label: str
) -> list[str]:
    reference = str(requirement.get("reference") or "")
    checks = (
        ("object_chain", "required_object_keys", "has the wrong object chain"),
        ("evidence_anchors", "required_evidence_anchors", "misses source branches"),
        ("terminal_states", "terminal_states", "has wrong terminal states"),
    )
    errors = [
        f"{label}: trace for {reference!r} {message}"
        for supplied_field, required_field, message in checks
        if set(as_list(trace.get(supplied_field)))
        != set(as_list(requirement.get(required_field)))
    ]
    if not concrete_trace_text(
        trace.get("terminal_source"),
        5,
        [reference, *as_list(requirement.get("terminal_states"))],
    ):
        errors.append(f"{label}: trace for {reference!r} lacks terminal-source meaning")
    return errors


def validate_trace_node(
    node: dict[str, Any], source_node: dict[str, Any], node_key: str, label: str
) -> list[str]:
    errors = [
        f"{label}: trace node {node_key} generated field {field} changed"
        for field in TRACE_NODE_LOCK_FIELDS
        if node.get(field) != source_node.get(field)
    ]
    if set(as_list(node.get("evidence_anchors"))) != set(
        as_list(source_node.get("required_evidence_anchors"))
    ):
        errors.append(f"{label}: trace node {node_key} must cover all source branches")
    source_terms = [
        str(source_node.get("object_name") or ""),
        str(source_node.get("object_type") or ""),
        *[str(value) for value in as_list(source_node.get("specificity_tokens"))],
        *[str(value) for value in as_list(source_node.get("referenced_variables"))],
    ]
    for field in TRACE_NODE_SEMANTIC_FIELDS:
        hits = 2 if field in {"configured_function", "configured_output"} else 1
        if not concrete_trace_text(node.get(field), 5, source_terms, hits):
            errors.append(f"{label}: trace node {node_key} lacks concrete {field}")
    node_text = " ".join(
        str(node.get(field) or "") for field in TRACE_NODE_SEMANTIC_FIELDS
    ).lower()
    tokens = [
        str(token).lower() for token in as_list(source_node.get("specificity_tokens"))
    ]
    required_hits = min(2, len(tokens))
    if required_hits and sum(token in node_text for token in tokens) < required_hits:
        errors.append(f"{label}: trace node {node_key} lacks source-specific variable meaning")
    role = str(source_node.get("semantic_role") or "")
    role_terms = TRACE_ROLE_TERMS.get(role, ())
    if role_terms and not any(term in node_text for term in role_terms):
        errors.append(f"{label}: trace node {node_key} does not explain its {role} behavior")
    return errors


def validate_trace_nodes(
    trace: dict[str, Any], requirement: dict[str, Any], label: str
) -> list[str]:
    reference = str(requirement.get("reference") or "")
    required = {
        str(node.get("object_key") or ""): node
        for node in as_list(requirement.get("required_nodes"))
    }
    supplied = {
        str(node.get("object_key") or ""): node
        for node in as_list(trace.get("node_reviews"))
        if isinstance(node, dict)
    }
    errors: list[str] = []
    if set(supplied) != set(required):
        errors.append(
            f"{label}: trace for {reference!r} must review every variable node exactly once"
        )
    for node_key, source_node in required.items():
        if node_key in supplied:
            errors.extend(validate_trace_node(supplied[node_key], source_node, node_key, label))
    return errors


def trace_edge_key(edge: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(edge.get("from_object_key") or ""),
        str(edge.get("to_object_key") or ""),
        str(edge.get("reference") or ""),
    )


def validate_trace_edges(
    trace: dict[str, Any], requirement: dict[str, Any], label: str
) -> list[str]:
    reference = str(requirement.get("reference") or "")
    required = {trace_edge_key(edge) for edge in as_list(requirement.get("required_edges"))}
    supplied = {
        trace_edge_key(edge): edge
        for edge in as_list(trace.get("edge_reviews"))
        if isinstance(edge, dict)
    }
    errors: list[str] = []
    if set(supplied) != required:
        errors.append(
            f"{label}: trace for {reference!r} must explain every variable hop exactly once"
        )
    for edge_key in required & set(supplied):
        if not concrete_trace_text(
            supplied[edge_key].get("dependency_meaning"), 5, list(edge_key), 2
        ):
            errors.append(f"{label}: trace edge {edge_key!r} lacks dependency meaning")
    return errors


def validate_terminal_review(
    terminal: dict[str, Any], source: dict[str, Any], terminal_key: str, label: str
) -> list[str]:
    locked_fields = ("state", "reference", "source_object_key", "configured_source")
    errors = [
        f"{label}: terminal {terminal_key} generated field {field} changed"
        for field in locked_fields
        if terminal.get(field) != source.get(field)
    ]
    source_terms = [
        str(source.get("reference") or ""),
        *re.findall(
            r"[A-Za-z_$][A-Za-z0-9_.$:/-]{3,}",
            str(source.get("configured_source") or ""),
        ),
    ]
    for field in ("terminal_meaning", "consumer_compatibility"):
        if not concrete_trace_text(terminal.get(field), 5, source_terms):
            errors.append(f"{label}: terminal {terminal_key} lacks concrete {field}")
    return errors


def validate_trace_terminals(
    trace: dict[str, Any], requirement: dict[str, Any], label: str
) -> list[str]:
    reference = str(requirement.get("reference") or "")
    required = {
        str(item.get("terminal_key") or ""): item
        for item in as_list(requirement.get("terminal_requirements"))
    }
    supplied = {
        str(item.get("terminal_key") or ""): item
        for item in as_list(trace.get("terminal_reviews"))
        if isinstance(item, dict)
    }
    errors: list[str] = []
    if set(supplied) != set(required):
        errors.append(
            f"{label}: trace for {reference!r} must assess every terminal exactly once"
        )
    for terminal_key, source in required.items():
        if terminal_key in supplied:
            errors.extend(
                validate_terminal_review(supplied[terminal_key], source, terminal_key, label)
            )
    return errors


def validate_reference_traces(
    row: dict[str, Any], expected: dict[str, Any], label: str
) -> list[str]:
    traces = {
        str(trace.get("reference") or ""): trace
        for trace in as_list(row.get("reference_traces"))
        if isinstance(trace, dict)
    }
    requirements = as_list(expected.get("reference_trace_requirements"))
    required_references = {str(item.get("reference") or "") for item in requirements}
    errors: list[str] = []
    if set(traces) != required_references:
        errors.append(f"{label}: recursive traces must cover every reference exactly once")
    for requirement in requirements:
        reference = str(requirement.get("reference") or "")
        trace = traces.get(reference)
        if not trace:
            continue
        errors.extend(validate_trace_header(trace, requirement, label))
        errors.extend(validate_trace_nodes(trace, requirement, label))
        errors.extend(validate_trace_edges(trace, requirement, label))
        errors.extend(validate_trace_terminals(trace, requirement, label))
    return errors
