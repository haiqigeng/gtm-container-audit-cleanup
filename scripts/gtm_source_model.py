#!/usr/bin/env python3
"""Build a GTM source-model navigation map from an export.

The source model is not a replacement for the raw GTM export/API evidence. It is
the cross-reference map used by cleanup lenses to navigate back to object
configuration, fields, variables, triggers, custom code, and unresolved edges.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from gtm_lib import (
    SEMANTIC_LAYERS,
    container_version,
    custom_template_id,
    is_system_trigger_reference,
    is_system_variable_reference,
    refs,
    source_descriptor,
    system_reference_description,
    trigger_group_members,
    walk_json_fields,
)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def stable_payload(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def code_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16] if normalized else ""


def param_value(obj: dict[str, Any], key: str) -> Any:
    for param in as_list(obj.get("parameter")):
        if param.get("key") != key:
            continue
        if "value" in param:
            return param.get("value")
        if "list" in param:
            return param.get("list")
        if "map" in param:
            return param.get("map")
    return None


def object_id(obj: dict[str, Any], layer: str) -> str:
    keys = {
        "tag": "tagId",
        "trigger": "triggerId",
        "variable": "variableId",
        "folder": "folderId",
        "customTemplate": "templateId",
        "builtInVariable": "name",
        "client": "clientId",
        "transformation": "transformationId",
    }
    value = obj.get(keys[layer]) or obj.get("name")
    return "" if value is None else str(value)


def object_summary(obj: dict[str, Any], layer: str) -> dict[str, str]:
    return {
        "layer": layer,
        "object_id": object_id(obj, layer),
        "object_name": str(obj.get("name") or ""),
        "type": str(obj.get("type") or ("customTemplate" if layer == "customTemplate" else "")),
    }


def parameter_edges(layer: str, obj: dict[str, Any], object_index: int) -> list[dict[str, Any]]:
    edges = []
    for parameter_index, param in enumerate(as_list(obj.get("parameter"))):
        base_path = f"$.containerVersion.{layer}[{object_index}].parameter[{parameter_index}]"
        for fact in walk_json_fields(param, base_path):
            edges.append(
                {
                    "source_layer": layer,
                    "source_id": object_id(obj, layer),
                    "source_name": str(obj.get("name") or ""),
                    "field_key": str(param.get("key") or ""),
                    "field_type": str(param.get("type") or ""),
                    **fact,
                }
            )
    return edges


def build_variable_consumers(cv: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    consumers: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for layer in SEMANTIC_LAYERS:
        if layer == "customTemplate":
            continue
        for obj in as_list(cv.get(layer)):
            for ref in sorted(refs(obj)):
                if layer == "variable" and ref == obj.get("name"):
                    continue
                consumers[ref].append(object_summary(obj, layer))
    return dict(consumers)


def recognized_system_references(
    variable_consumers: dict[str, list[dict[str, str]]],
    trigger_consumers: dict[str, list[dict[str, str]]],
) -> dict[str, list[dict[str, Any]]]:
    return {
        "variable_references": [
            {
                "reference": ref,
                "description": system_reference_description("variable", ref),
                "consumers": consumers,
            }
            for ref, consumers in sorted(variable_consumers.items())
            if is_system_variable_reference(ref)
        ],
        "trigger_references": [
            {
                "reference": ref,
                "description": system_reference_description("trigger", ref),
                "consumers": consumers,
            }
            for ref, consumers in sorted(trigger_consumers.items())
            if is_system_trigger_reference(ref)
        ],
    }


def custom_code_body(layer: str, obj: dict[str, Any]) -> str:
    if layer == "tag":
        return str(param_value(obj, "html") or "")
    if layer == "variable":
        return str(param_value(obj, "javascript") or "")
    return str(obj.get("templateData") or "")


def build_model(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cv = container_version(data)
    tags = as_list(cv.get("tag"))
    triggers = as_list(cv.get("trigger"))
    variables = as_list(cv.get("variable"))
    folders = as_list(cv.get("folder"))
    templates = as_list(cv.get("customTemplate"))
    builtins = as_list(cv.get("builtInVariable"))
    clients = as_list(cv.get("client"))
    transformations = as_list(cv.get("transformation"))

    variable_consumers = build_variable_consumers(cv)
    variable_names = {obj.get("name") for obj in variables} | {obj.get("name") for obj in builtins}
    trigger_ids = {str(obj.get("triggerId")) for obj in triggers}
    folder_ids = {str(obj.get("folderId")) for obj in folders}
    template_ids = {str(obj.get("templateId")) for obj in templates}
    tag_names = {obj.get("name") for obj in tags}

    trigger_edges = []
    trigger_consumers: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for tag in tags:
        for relation in ("firingTriggerId", "blockingTriggerId"):
            for trigger_id in as_list(tag.get(relation)):
                edge = {
                    "source_layer": "tag",
                    "source_id": object_id(tag, "tag"),
                    "source_name": str(tag.get("name") or ""),
                    "relation": relation,
                    "target_trigger_id": str(trigger_id),
                }
                trigger_edges.append(edge)
                trigger_consumers[str(trigger_id)].append(object_summary(tag, "tag"))
    for trigger in triggers:
        for member_id in trigger_group_members(trigger):
            trigger_edges.append(
                {
                    "source_layer": "trigger",
                    "source_id": object_id(trigger, "trigger"),
                    "source_name": str(trigger.get("name") or ""),
                    "relation": "trigger_group_member",
                    "target_trigger_id": str(member_id),
                }
            )
            trigger_consumers[str(member_id)].append(object_summary(trigger, "trigger"))

    field_edges = []
    field_layers = (
        ("tag", tags),
        ("trigger", triggers),
        ("variable", variables),
        ("client", clients),
        ("transformation", transformations),
    )
    for layer, items in field_layers:
        for index, obj in enumerate(items):
            field_edges.extend(parameter_edges(layer, obj, index))

    variable_sources = [
        {
            **object_summary(variable, "variable"),
            "data_layer_path": param_value(variable, "name"),
            "javascript_hash": code_hash(str(param_value(variable, "javascript") or "")),
            "referenced_variables": sorted(refs(variable)),
            "consumers": variable_consumers.get(variable.get("name"), []),
        }
        for variable in variables
    ]

    custom_code_objects = []
    for layer, items in (("tag", tags), ("variable", variables), ("customTemplate", templates)):
        for obj in items:
            body = custom_code_body(layer, obj)
            is_custom_code = bool(body) and (
                layer == "customTemplate"
                or str(obj.get("type") or "").lower() in {"html", "jsm"}
                or param_value(obj, "html")
                or param_value(obj, "javascript")
            )
            if not is_custom_code:
                continue
            custom_code_objects.append(
                {
                    **object_summary(obj, layer),
                    "code_hash": code_hash(body),
                    "code_length": len(body),
                    "referenced_variables": sorted(refs(obj)),
                    "consumers": variable_consumers.get(obj.get("name"), [])
                    if layer == "variable"
                    else [],
                }
            )

    system_refs = recognized_system_references(variable_consumers, trigger_consumers)
    unresolved_edges = {
        "undefined_variable_references": sorted(
            ref
            for ref in variable_consumers
            if ref not in variable_names and not is_system_variable_reference(ref)
        ),
        "missing_trigger_references": sorted(
            ref
            for ref in trigger_consumers
            if ref not in trigger_ids and not is_system_trigger_reference(ref)
        ),
        "missing_folder_references": sorted(
            {
                str(obj.get("parentFolderId"))
                for obj in tags + triggers + variables + clients + transformations
                if obj.get("parentFolderId") and str(obj.get("parentFolderId")) not in folder_ids
            }
        ),
        "missing_custom_template_references": sorted(
            {
                template_id
                for obj in tags + variables + clients + transformations
                for template_id in [custom_template_id(obj)]
                if template_id and template_id not in template_ids
            }
        ),
        "missing_setup_teardown_references": sorted(
            {
                ref.get("tagName")
                for tag in tags
                for relation in ("setupTag", "teardownTag")
                for ref in as_list(tag.get(relation))
                if ref.get("tagName") and ref.get("tagName") not in tag_names
            }
        ),
    }
    unresolved_count = sum(len(values) for values in unresolved_edges.values())

    return {
        **source_descriptor(path),
        "kind": "gtm_source_model_navigation_map",
        "source_model_role": "navigation_map_not_evidence_source",
        "raw_evidence_must_be_rechecked_for_findings": True,
        "counts": {
            "tags": len(tags),
            "triggers": len(triggers),
            "variables": len(variables),
            "folders": len(folders),
            "customTemplates": len(templates),
            "clients": len(clients),
            "transformations": len(transformations),
            "builtInVariables": len(builtins),
            "field_edges": len(field_edges),
            "trigger_edges": len(trigger_edges),
            "custom_code_objects": len(custom_code_objects),
            "unresolved_edges": unresolved_count,
            "recognized_system_references": sum(len(values) for values in system_refs.values()),
        },
        "objects": {
            "tags": [object_summary(obj, "tag") for obj in tags],
            "triggers": [object_summary(obj, "trigger") for obj in triggers],
            "variables": [object_summary(obj, "variable") for obj in variables],
            "customTemplates": [object_summary(obj, "customTemplate") for obj in templates],
            "clients": [object_summary(obj, "client") for obj in clients],
            "transformations": [object_summary(obj, "transformation") for obj in transformations],
        },
        "field_edges": field_edges,
        "trigger_edges": trigger_edges,
        "variable_sources": variable_sources,
        "custom_code_objects": custom_code_objects,
        "trigger_consumers": dict(trigger_consumers),
        "variable_consumers": variable_consumers,
        "recognized_system_references": system_refs,
        "unresolved_edges": unresolved_edges,
        "coverage_gate": "blocked_unresolved_edges" if unresolved_count else "pass",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path, help="Path to a GTM container export JSON")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    result = build_model(args.export)
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
