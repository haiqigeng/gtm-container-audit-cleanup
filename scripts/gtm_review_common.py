#!/usr/bin/env python3
"""Shared mechanics for independent GTM review validators.

This module owns only source lookup and validation primitives. It must never
produce an operational, configuration, or architecture verdict.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from gtm_configuration_facts import build_consumers, object_consumers
from gtm_context_model import build_context_model
from gtm_lib import ID_KEYS, container_version
from gtm_shared_facts import build_shared_facts

VALID_PRIORITIES = {"Critical", "High", "Medium", "Low"}
VALID_CONFIDENCE = {"High", "Medium", "Low"}
VALID_READINESS = {"approval_required", "owner_blocked", "not_actionable"}
VALID_MUTATION_LEVELS = {"Conservative", "Standard", "Deep", "Transformational"}
MUTATION_LEVEL_RANK = {
    "Conservative": 1,
    "Standard": 2,
    "Deep": 3,
    "Transformational": 4,
}
MUTATION_FIELDS = (
    "creations",
    "additions",
    "changes",
    "remaps",
    "renames",
    "deletions",
)

GENERIC_PHRASES = {
    "review configuration",
    "configuration reviewed",
    "choose a canonical object",
    "check in gtm",
    "code inspected",
    "code reviewed",
    "custom code inspected",
    "static scan completed",
    "needs review",
    "optimize as needed",
    "serves one concrete measurement purpose",
    "executes through its configured route",
    "reads the named inputs",
    "produces its configured output",
    "feeds the exact exported consumers",
    "uses the exported consent",
    "internally coherent for this container configuration",
    "fixture value",
    "fixture family",
    "source-bound route, payload, and dependency configuration",
}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def canonical_review_facts(
    export_path: Path,
    supplied: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Rebuild the exact contextual and deterministic facts claimed by a review."""
    provided = supplied.get("provided_context")
    if not isinstance(provided, dict):
        provided = {}
    context = build_context_model(export_path, provided_context=provided)
    return context, build_shared_facts(export_path, context=context)


def words(value: Any) -> int:
    return len(re.findall(r"\b[\w{}.-]+\b", str(value or "")))


def specific_text(value: Any, minimum: int = 5) -> bool:
    text = str(value or "").strip().lower()
    return words(text) >= minimum and not any(phrase in text for phrase in GENERIC_PHRASES)


def created_object_keys(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for creation in as_list(row.get("creations")):
        layer = str(creation.get("layer") or "")
        obj = creation.get("object")
        id_key = ID_KEYS.get(layer)
        if not id_key or not isinstance(obj, dict):
            continue
        object_id = str(obj.get(id_key) or obj.get("name") or "")
        if object_id:
            keys.add(f"{layer}:{object_id}")
    return keys


def _validate_creations(
    row: dict[str, Any], valid_keys: set[str], label: str
) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    created: set[str] = set()
    for index, creation in enumerate(as_list(row.get("creations")), start=1):
        prefix = f"{label}: creation {index}"
        layer = str(creation.get("layer") or "")
        obj = creation.get("object")
        id_key = ID_KEYS.get(layer)
        if not id_key or not isinstance(obj, dict):
            errors.append(f"{prefix} requires a supported layer and complete object")
            continue
        object_id = str(obj.get(id_key) or obj.get("name") or "")
        key = f"{layer}:{object_id}" if object_id else ""
        if not key:
            errors.append(f"{prefix} requires the layer identity field {id_key}")
        elif key in valid_keys or key in created:
            errors.append(f"{prefix} duplicates existing or planned object {key!r}")
        else:
            created.add(key)
        if not specific_text(creation.get("reason"), 4):
            errors.append(f"{prefix} requires a specific reason")
    return errors, created


def _validate_additions(
    row: dict[str, Any], allowed_keys: set[str], label: str
) -> list[str]:
    errors: list[str] = []
    for index, addition in enumerate(as_list(row.get("additions")), start=1):
        prefix = f"{label}: addition {index}"
        key = str(addition.get("object_key") or "")
        if key not in allowed_keys:
            errors.append(f"{prefix} references unknown object {key!r}")
        if not str(addition.get("json_path") or "").startswith("$"):
            errors.append(f"{prefix} requires an exact parent json_path")
        if "value" not in addition:
            errors.append(f"{prefix} requires a value")
        if addition.get("mode") not in {"set", "append", "insert"}:
            errors.append(f"{prefix} mode must be set, append, or insert")
        if addition.get("mode") == "insert" and not isinstance(addition.get("index"), int):
            errors.append(f"{prefix} insert mode requires an integer index")
        if not specific_text(addition.get("reason"), 4):
            errors.append(f"{prefix} requires a specific reason")
    return errors


def _validate_changes(
    row: dict[str, Any], allowed_keys: set[str], label: str
) -> list[str]:
    errors: list[str] = []
    for change in as_list(row.get("changes")):
        key = str(change.get("object_key") or "")
        if key not in allowed_keys:
            errors.append(f"{label}: change references unknown object {key!r}")
        if not str(change.get("json_path") or "").startswith("$"):
            errors.append(f"{label}: field change requires an exact source json_path")
        if "before" not in change or "after" not in change:
            errors.append(f"{label}: field change requires before and after values")
    return errors


def _validate_remaps(
    row: dict[str, Any],
    allowed_keys: set[str],
    label: str,
    expected_consumers: dict[str, set[str]] | None,
) -> list[str]:
    errors: list[str] = []
    for remap in as_list(row.get("remaps")):
        source = str(remap.get("from_object_key") or "")
        target = str(remap.get("to_object_key") or "")
        if source not in allowed_keys or target not in allowed_keys:
            errors.append(f"{label}: remap must reference existing or planned objects")
        if source == target:
            errors.append(f"{label}: remap source and target cannot be identical")
        consumers = [str(value) for value in as_list(remap.get("consumer_object_keys"))]
        if not consumers:
            errors.append(f"{label}: remap must list every affected consumer")
        for consumer in consumers:
            if consumer not in allowed_keys:
                errors.append(f"{label}: remap references unknown consumer {consumer!r}")
        if (
            expected_consumers is not None
            and source in expected_consumers
            and set(consumers) != expected_consumers[source]
        ):
            errors.append(
                f"{label}: remap consumers must exactly match every source-graph consumer"
            )
    return errors


def _validate_deletions_and_renames(
    row: dict[str, Any], allowed_keys: set[str], label: str
) -> list[str]:
    errors: list[str] = []
    for deletion in as_list(row.get("deletions")):
        key = str(deletion.get("object_key") or "")
        if key not in allowed_keys:
            errors.append(f"{label}: deletion references unknown object {key!r}")
        if not specific_text(deletion.get("reason"), 3):
            errors.append(f"{label}: deletion requires a specific reason")
    for rename in as_list(row.get("renames")):
        key = str(rename.get("object_key") or "")
        if key not in allowed_keys:
            errors.append(f"{label}: rename references unknown object {key!r}")
        if not str(rename.get("before") or "").strip() or not str(
            rename.get("after") or ""
        ).strip():
            errors.append(f"{label}: rename requires before and after names")
    return errors


def object_keys(export_path: Path) -> set[str]:
    data = json.loads(export_path.read_text(encoding="utf-8"))
    cv = container_version(data)
    keys: set[str] = set()
    for layer, id_key in ID_KEYS.items():
        for obj in as_list(cv.get(layer)):
            value = obj.get(id_key) or obj.get("name")
            if value is not None:
                keys.add(f"{layer}:{value}")
    return keys


def object_consumer_map(export_path: Path) -> dict[str, set[str]]:
    data = json.loads(export_path.read_text(encoding="utf-8"))
    cv = container_version(data)
    consumers = build_consumers(cv)
    result: dict[str, set[str]] = {}
    for layer, id_key in ID_KEYS.items():
        for obj in as_list(cv.get(layer)):
            object_id = str(obj.get(id_key) or obj.get("name") or "")
            if not object_id:
                continue
            result[f"{layer}:{object_id}"] = {
                str(item.get("consumer_key") or "")
                for item in object_consumers(layer, obj, consumers)
                if item.get("consumer_key")
            }
    return result


def validate_structured_actions(
    row: dict[str, Any],
    valid_keys: set[str],
    label: str,
    expected_consumers: dict[str, set[str]] | None = None,
) -> list[str]:
    errors: list[str] = []
    action_count = sum(len(as_list(row.get(field))) for field in MUTATION_FIELDS)
    if action_count == 0:
        errors.append(f"{label}: cleanup operation has no structured change")
    creation_errors, created = _validate_creations(row, valid_keys, label)
    errors.extend(creation_errors)
    allowed_keys = valid_keys | created
    errors.extend(_validate_additions(row, allowed_keys, label))
    errors.extend(_validate_changes(row, allowed_keys, label))
    errors.extend(_validate_remaps(row, allowed_keys, label, expected_consumers))
    errors.extend(_validate_deletions_and_renames(row, allowed_keys, label))

    declared_level = row.get("minimum_aggressiveness")
    if declared_level not in VALID_MUTATION_LEVELS:
        errors.append(f"{label}: minimum_aggressiveness is invalid")
    else:
        required_rank = 1
        if as_list(row.get("creations")) or as_list(row.get("additions")):
            required_rank = max(required_rank, 2)
        if as_list(row.get("remaps")):
            required_rank = max(required_rank, 2)
        sensitive_path = re.compile(
            r"(?:html|javascript|templateData|eventName|measurement|destination|"
            r"consent|storage|user_data|ecommerce|currency|value)",
            re.I,
        )
        if any(
            sensitive_path.search(str(change.get("json_path") or ""))
            for change in as_list(row.get("changes"))
        ):
            required_rank = max(required_rank, 3)
        if expected_consumers is not None and any(
            expected_consumers.get(str(deletion.get("object_key") or ""), set())
            for deletion in as_list(row.get("deletions"))
        ):
            required_rank = max(required_rank, 3)
        if str(row.get("problem_type") or "") in {
            "Functional overlap",
            "Wrong trigger timing",
            "Over-firing",
            "Under-firing",
            "Duplicate firing",
            "Wrong product, market, or page scope",
            "Incomplete payload",
            "Wrong data format",
            "Wrong value or formula logic",
            "Consent mismatch",
            "Custom code risk",
        }:
            required_rank = max(required_rank, 3)
        declared_rank = MUTATION_LEVEL_RANK[str(declared_level)]
        if declared_rank < required_rank:
            required_level = next(
                level for level, rank in MUTATION_LEVEL_RANK.items() if rank == required_rank
            )
            errors.append(
                f"{label}: minimum_aggressiveness must be at least {required_level} "
                "for the proposed mutation risk"
            )

    canonical = str(row.get("canonical_object_key") or "")
    if canonical and canonical not in allowed_keys:
        errors.append(f"{label}: canonical_object_key is unknown")
    deleted_keys = {str(item.get("object_key") or "") for item in as_list(row.get("deletions"))}
    if canonical and canonical in deleted_keys:
        errors.append(f"{label}: canonical object cannot also be deleted")
    if row.get("deterministic_action_candidate") == "consolidate_candidate":
        if not canonical:
            errors.append(f"{label}: consolidation requires an explicit canonical object")
        if not as_list(row.get("deletions")):
            errors.append(f"{label}: consolidation requires deletion of non-canonical objects")
    return errors


def validate_challenge(row: dict[str, Any], label: str) -> list[str]:
    if row.get("priority") not in {"Critical", "High"}:
        return []
    challenge = row.get("challenge_review")
    if not isinstance(challenge, dict):
        return [f"{label}: High/Critical operation requires a challenge review"]
    errors = []
    for field in (
        "source_recheck",
        "status_and_scope_check",
        "alternative_explanation",
    ):
        if not specific_text(challenge.get(field), 5):
            errors.append(f"{label}: challenge review field {field} is incomplete")
    if challenge.get("challenge_verdict") not in {
        "confirmed",
        "downgraded",
        "rejected",
        "blocked",
    }:
        errors.append(f"{label}: challenge_verdict is invalid")
    return errors
