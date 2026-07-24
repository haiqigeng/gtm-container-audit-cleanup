#!/usr/bin/env python3
"""Compile three independently validated GTM reviews into cleanup operations."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from gtm_architecture_review import validate_review as validate_architecture_review
from gtm_configuration_review import validate_review as validate_configuration_review
from gtm_lib import ID_KEYS, container_version, source_integrity_findings, stable_hash
from gtm_operational_review import validate_review as validate_operational_review
from gtm_review_common import as_list, specific_text, validate_review_provenance

ACTION_FIELDS = (
    "creations",
    "additions",
    "changes",
    "remaps",
    "deletions",
    "renames",
)
TEXT_FIELDS = (
    "title",
    "area",
    "problem_type",
    "problem",
    "why_it_matters",
    "expected_clean_state",
    "exact_proposed_action",
    "preconditions",
    "qa_steps",
    "rollback",
    "priority",
    "confidence",
    "execution_readiness",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_object_catalog(export_path: Path) -> dict[str, dict[str, str]]:
    data = load_json(export_path)
    blocking_integrity = [
        row for row in source_integrity_findings(data) if row.get("blocking")
    ]
    if blocking_integrity:
        raise ValueError(
            "source integrity gate blocked operation compilation: "
            + ", ".join(
                sorted(
                    str(row.get("finding_type") or "source_integrity_error")
                    for row in blocking_integrity
                )
            )
        )
    cv = container_version(data)
    catalog: dict[str, dict[str, str]] = {}
    for layer, id_key in ID_KEYS.items():
        for obj in as_list(cv.get(layer)):
            object_id = str(obj.get(id_key) or obj.get("name") or "")
            if not object_id:
                continue
            key = f"{layer}:{object_id}"
            catalog[key] = {
                "object_key": key,
                "layer": layer,
                "object_id": object_id,
                "object_name": str(obj.get("name") or ""),
                "config_hash": stable_hash(
                    {
                        name: value
                        for name, value in obj.items()
                        if name not in {"path", "fingerprint", "accountId", "containerId"}
                    }
                ),
            }
    return catalog


def operational_object_keys(row: dict[str, Any]) -> list[str]:
    layer = str(row.get("object_type") or "")
    return [f"{layer}:{value}" for value in as_list(row.get("object_ids")) if value]


def action_object_keys(operation: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for creation in as_list(operation.get("creations")):
        layer = str(creation.get("layer") or "")
        obj = creation.get("object") or {}
        id_key = ID_KEYS.get(layer, "")
        object_id = str(obj.get(id_key) or obj.get("name") or "")
        if layer and object_id:
            keys.add(f"{layer}:{object_id}")
    for addition in as_list(operation.get("additions")):
        keys.add(str(addition.get("object_key") or ""))
    for change in as_list(operation.get("changes")):
        keys.add(str(change.get("object_key") or ""))
    for remap in as_list(operation.get("remaps")):
        keys.add(str(remap.get("from_object_key") or ""))
        keys.add(str(remap.get("to_object_key") or ""))
        keys.update(str(value) for value in as_list(remap.get("consumer_object_keys")))
    for field in ("deletions", "renames"):
        keys.update(str(item.get("object_key") or "") for item in as_list(operation.get(field)))
    canonical = str(operation.get("canonical_object_key") or "")
    if canonical:
        keys.add(canonical)
    return {key for key in keys if key}


def structural_action_item(field: str, item: Any) -> Any:
    """Return the mutation identity, excluding explanatory prose.

    A deletion reason and a declared canonical key make an operation easier for
    an analyst to read, but neither changes the JSON mutation.  The remap
    endpoint itself remains part of the structural identity, so two different
    canonical targets cannot be silently merged.
    """
    if not isinstance(item, dict):
        return copy.deepcopy(item)
    result = copy.deepcopy(item)
    if field in {"creations", "deletions"}:
        result.pop("reason", None)
    return result


def normalized_action_payload(operation: dict[str, Any]) -> dict[str, Any]:
    return {
        field: sorted(
            [
                structural_action_item(field, item)
                for item in as_list(operation.get(field))
            ],
            key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False),
        )
        for field in ACTION_FIELDS
    }


def normalized_operation(
    operation: dict[str, Any],
    source_run: str,
    source_reference: str,
    source_keys: list[str],
) -> dict[str, Any]:
    row = {field: copy.deepcopy(operation.get(field)) for field in TEXT_FIELDS}
    row.update(normalized_action_payload(operation))
    row["canonical_object_key"] = str(operation.get("canonical_object_key") or "")
    row["operation_key"] = str(operation.get("operation_key") or "").strip()
    row["source_runs"] = [source_run]
    row["source_references"] = [source_reference]
    row["source_object_keys"] = sorted(set(source_keys))
    row["affected_object_keys"] = sorted(action_object_keys(operation))
    row["challenge_review"] = copy.deepcopy(operation.get("challenge_review") or {})
    return row


def collect_operations(
    operational: dict[str, Any],
    configuration: dict[str, Any],
    architecture: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for finding in as_list(operational.get("findings")):
        if finding.get("disposition") != "cleanup_operation":
            continue
        rows.append(
            normalized_operation(
                finding,
                "operational_sanitation",
                str(finding.get("finding_id") or ""),
                operational_object_keys(finding),
            )
        )
    for review in as_list(configuration.get("rows")):
        if review.get("disposition") != "cleanup_operation":
            continue
        rows.append(
            normalized_operation(
                review.get("operation") or {},
                "configuration_correctness",
                str(review.get("review_id") or review.get("object_key") or ""),
                [str(review.get("object_key") or "")],
            )
        )
    for family in as_list(architecture.get("families")):
        for index, operation in enumerate(as_list(family.get("operations")), start=1):
            rows.append(
                normalized_operation(
                    operation,
                    "business_architecture",
                    f"{family.get('family_id')}:operation:{index}",
                    [str(value) for value in as_list(family.get("chain_object_keys"))],
                )
            )
    for comparison in as_list(architecture.get("comparisons")):
        for index, operation in enumerate(as_list(comparison.get("operations")), start=1):
            rows.append(
                normalized_operation(
                    operation,
                    "business_architecture",
                    f"{comparison.get('comparison_id')}:operation:{index}",
                    [str(value) for value in as_list(comparison.get("candidate_object_keys"))],
                )
            )
    return rows


def _selected_text(rows: list[dict[str, Any]], field: str) -> Any:
    values = [row.get(field) for row in rows if row.get(field) not in {None, ""}]
    if not values:
        return ""
    if field == "priority":
        order = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
        return max(values, key=lambda value: order.get(str(value), 0))
    if field == "confidence":
        order = {"Low": 1, "Medium": 2, "High": 3}
        return min(values, key=lambda value: order.get(str(value), 0))
    if field == "execution_readiness":
        order = {"approval_required": 1, "owner_blocked": 2, "not_actionable": 3}
        return max(values, key=lambda value: order.get(str(value), 0))
    return max(values, key=lambda value: (len(str(value)), str(value)))


def _operation_group_key(operation: dict[str, Any]) -> str:
    return json.dumps(normalized_action_payload(operation), sort_keys=True, ensure_ascii=False)


def merge_compatible_operations(
    operations: list[dict[str, Any]], errors: list[str]
) -> list[dict[str, Any]]:
    key_actions: dict[str, set[str]] = defaultdict(set)
    for operation in operations:
        key_actions[operation["operation_key"]].add(_operation_group_key(operation))
    for operation_key, signatures in sorted(key_actions.items()):
        if len(signatures) > 1:
            errors.append(
                f"operation_key {operation_key!r} is reused for different structured mutations"
            )

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        groups[_operation_group_key(operation)].append(operation)
    merged: list[dict[str, Any]] = []
    for action_signature, rows in sorted(groups.items()):
        areas = {str(row.get("area") or "") for row in rows}
        problem_types = {str(row.get("problem_type") or "") for row in rows}
        if len(areas) > 1 or len(problem_types) > 1:
            errors.append(
                "independent reviews agree on a mutation but classify its area/problem type "
                f"differently: areas={sorted(areas)!r}, problem_types={sorted(problem_types)!r}"
            )
            continue
        first = copy.deepcopy(rows[0])
        source_operation_keys = sorted({str(row.get("operation_key") or "") for row in rows})
        first["operation_key"] = (
            source_operation_keys[0]
            if len(source_operation_keys) == 1
            else f"reconciled-{stable_hash(action_signature, 12)}"
        )
        first["source_operation_keys"] = source_operation_keys
        for field in TEXT_FIELDS:
            first[field] = _selected_text(rows, field)
        first["lens_rationales"] = [
            {
                "source_run": str(row.get("source_runs", ["unknown"])[0]),
                "source_reference": str(row.get("source_references", [""])[0]),
                "operation_key": row.get("operation_key"),
                "problem": row.get("problem"),
                "why_it_matters": row.get("why_it_matters"),
                "expected_clean_state": row.get("expected_clean_state"),
            }
            for row in sorted(
                rows,
                key=lambda item: (
                    str(item.get("source_runs", [""])[0]),
                    str(item.get("source_references", [""])[0]),
                ),
            )
        ]
        first["source_runs"] = sorted(
            {value for row in rows for value in as_list(row.get("source_runs"))}
        )
        first["source_references"] = sorted(
            {value for row in rows for value in as_list(row.get("source_references"))}
        )
        first["source_object_keys"] = sorted(
            {value for row in rows for value in as_list(row.get("source_object_keys"))}
        )
        first["affected_object_keys"] = sorted(
            {value for row in rows for value in as_list(row.get("affected_object_keys"))}
        )
        merged.append(first)
    return merged


def normalized_mutation_path(object_key: str, json_path: str) -> str:
    layer = object_key.split(":", 1)[0]
    match = re.match(
        rf"^\$\.(?:containerVersion\.)?{re.escape(layer)}\[\d+\](.*)$",
        json_path,
    )
    return "$" + match.group(1) if match else json_path


def paths_overlap(left: str, right: str) -> bool:
    if left == right:
        return True
    return left.startswith(right + ".") or left.startswith(right + "[") or right.startswith(
        left + "."
    ) or right.startswith(left + "[")


def mutation_state() -> dict[str, Any]:
    return {
        "field_targets": {},
        "rename_targets": {},
        "remap_targets": {},
        "deleted_by": {},
        "created_by": {},
        "addition_targets": defaultdict(list),
        "changed_by": defaultdict(set),
        "writes": [],
    }


def record_creation(
    creation: dict[str, Any], key: str, state: dict[str, Any]
) -> list[str]:
    layer = str(creation.get("layer") or "")
    obj = creation.get("object") or {}
    id_key = ID_KEYS.get(layer, "")
    object_id = str(obj.get(id_key) or obj.get("name") or "")
    target = f"{layer}:{object_id}" if layer and object_id else ""
    if not target:
        return []
    previous = state["created_by"].get(target)
    state["created_by"][target] = key
    state["changed_by"][target].add(key)
    if previous:
        return [f"{target} is created more than once in {previous!r} and {key!r}"]
    return []


def record_addition(
    addition: dict[str, Any], key: str, state: dict[str, Any]
) -> list[str]:
    object_key = str(addition.get("object_key") or "")
    path = normalized_mutation_path(object_key, str(addition.get("json_path") or ""))
    target = (object_key, path, str(addition.get("mode") or ""), addition.get("index"))
    value = json.dumps(addition.get("value"), sort_keys=True, ensure_ascii=False)
    previous_rows = state["addition_targets"][target]
    errors: list[str] = []
    if target[2] in {"set", "insert"} and previous_rows:
        errors.append(
            f"ambiguous {target[2]} additions for {object_key} {path} in "
            f"{previous_rows[0][1]!r} and {key!r}"
        )
    if any(previous_value == value for previous_value, _ in previous_rows):
        errors.append(f"duplicate addition for {object_key} {path} in {key!r}")
    previous_rows.append((value, key))
    state["writes"].append((object_key, path, "addition", value, key))
    state["changed_by"][object_key].add(key)
    return errors


def record_change(change: dict[str, Any], key: str, state: dict[str, Any]) -> list[str]:
    object_key = str(change.get("object_key") or "")
    path = normalized_mutation_path(object_key, str(change.get("json_path") or ""))
    target = (object_key, path)
    value = json.dumps(change.get("after"), sort_keys=True, ensure_ascii=False)
    previous = state["field_targets"].get(target)
    state["field_targets"][target] = (value, key)
    state["writes"].append((object_key, path, "change", value, key))
    state["changed_by"][object_key].add(key)
    if previous:
        return [
            f"duplicate or conflicting field changes for {object_key} {path} in "
            f"{previous[1]!r} and {key!r}"
        ]
    return []


def record_rename(rename: dict[str, Any], key: str, state: dict[str, Any]) -> list[str]:
    target = str(rename.get("object_key") or "")
    value = str(rename.get("after") or "")
    previous = state["rename_targets"].get(target)
    state["rename_targets"][target] = (value, key)
    state["writes"].append((target, "$.name", "rename", json.dumps(value), key))
    state["changed_by"][target].add(key)
    if previous:
        return [
            f"duplicate or conflicting rename targets for {target} in "
            f"{previous[1]!r} and {key!r}"
        ]
    return []


def record_remap(remap: dict[str, Any], key: str, state: dict[str, Any]) -> list[str]:
    source = str(remap.get("from_object_key") or "")
    target = str(remap.get("to_object_key") or "")
    previous = state["remap_targets"].get(source)
    state["remap_targets"][source] = (target, key)
    if previous:
        return [
            f"duplicate or conflicting remap targets for {source} in "
            f"{previous[1]!r} and {key!r}"
        ]
    return []


def record_deletion(
    deletion: dict[str, Any], key: str, state: dict[str, Any]
) -> list[str]:
    target = str(deletion.get("object_key") or "")
    previous = state["deleted_by"].get(target)
    state["deleted_by"][target] = key
    if previous:
        return [f"{target} is deleted more than once in {previous!r} and {key!r}"]
    return []


def record_operation_mutations(
    operation: dict[str, Any], state: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    key = str(operation.get("operation_key") or "")
    handlers = (
        ("creations", record_creation),
        ("additions", record_addition),
        ("changes", record_change),
        ("renames", record_rename),
        ("remaps", record_remap),
        ("deletions", record_deletion),
    )
    for field, handler in handlers:
        for item in as_list(operation.get(field)):
            errors.extend(handler(item, key, state))
    return errors


def overlapping_write_errors(writes: list[tuple[str, str, str, str, str]]) -> list[str]:
    errors: list[str] = []
    for index, left in enumerate(writes):
        for right in writes[index + 1 :]:
            if left[0] != right[0] or not paths_overlap(left[1], right[1]):
                continue
            if left[2] == right[2] == "addition" and left[1] == right[1]:
                continue
            errors.append(
                f"overlapping writes for {left[0]} at {left[1]} and {right[1]} "
                f"in {left[4]!r} and {right[4]!r}"
            )
    return errors


def deletion_conflict_errors(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for target, delete_key in sorted(state["deleted_by"].items()):
        for change_key in sorted(state["changed_by"].get(target, set()) - {delete_key}):
            errors.append(
                f"{target} is deleted by {delete_key!r} but also changed by {change_key!r}"
            )
        if target in state["created_by"]:
            errors.append(
                f"{target} is both created by {state['created_by'][target]!r} "
                f"and deleted by {delete_key!r}"
            )
    for source, (target, operation_key) in sorted(state["remap_targets"].items()):
        if target in state["deleted_by"]:
            errors.append(
                f"{operation_key!r} remaps {source} to {target}, but {target} is also deleted"
            )
    return errors


def validate_mutation_conflicts(operations: list[dict[str, Any]]) -> list[str]:
    state = mutation_state()
    errors: list[str] = []
    for operation in operations:
        errors.extend(record_operation_mutations(operation, state))
    errors.extend(overlapping_write_errors(state["writes"]))
    errors.extend(deletion_conflict_errors(state))
    return errors


def destructive_object_keys(operation: dict[str, Any]) -> set[str]:
    return {
        str(item.get("object_key") or "")
        for item in as_list(operation.get("deletions"))
    } | {
        str(item.get("from_object_key") or "")
        for item in as_list(operation.get("remaps"))
    }


NON_BEHAVIOR_PATHS = {
    "$.accountId",
    "$.containerId",
    "$.workspaceId",
    "$.fingerprint",
    "$.path",
    "$.tagManagerUrl",
    "$.name",
    "$.notes",
    "$.parentFolderId",
}


def behavior_impact_keys(operation: dict[str, Any]) -> set[str]:
    """Return existing objects whose execution, data, or routing can change."""
    # Folder removal is organizational metadata. Folder-member moves are
    # represented separately through parentFolderId changes and remain visible
    # exact mutations without pretending that an empty folder has runtime
    # behavior.
    keys = {
        key
        for key in destructive_object_keys(operation)
        if not key.startswith("folder:")
    }
    for field in ("additions", "changes"):
        for item in as_list(operation.get(field)):
            object_key = str(item.get("object_key") or "")
            path = normalized_mutation_path(
                object_key,
                str(item.get("json_path") or ""),
            )
            if object_key and path not in NON_BEHAVIOR_PATHS:
                keys.add(object_key)
    for remap in as_list(operation.get("remaps")):
        # Architecture must prove the equivalence/consolidation of the remap
        # endpoints. The exact consumer list remains mutation evidence and is
        # revalidated in the projected graph, but those consumers should not
        # be recast as architecture conflicts when their dependency is merely
        # switched to the approved canonical equivalent. Folder remaps only
        # update parentFolderId metadata and do not change runtime behavior.
        keys.update(
            str(value)
            for value in [
                remap.get("from_object_key"),
                remap.get("to_object_key"),
            ]
            if value and not str(value).startswith("folder:")
        )
    return keys


def architecture_family_support(
    behavior_keys: set[str], families: list[dict[str, Any]]
) -> set[str]:
    """Return completed architecture families that cover each edited object.

    Source-bound field repairs preserve object identity and do not resolve or
    remove a cross-object relationship.  They still need architecture evidence,
    but duplicating the exact same operation into a family adds no safety.  A
    completed family that includes the object supplies that evidence.
    """
    support_by_key: dict[str, set[str]] = defaultdict(set)
    for family in families:
        if family.get("review_status") != "complete":
            continue
        family_id = str(family.get("family_id") or "")
        if not family_id:
            continue
        family_keys = {
            str(value)
            for value in [
                *as_list(family.get("member_object_keys")),
                *as_list(family.get("chain_object_keys")),
            ]
            if str(value)
        }
        for key in behavior_keys & family_keys:
            support_by_key[key].add(family_id)
    if not behavior_keys <= set(support_by_key):
        return set()
    return set().union(*(support_by_key[key] for key in behavior_keys))


def architecture_cleanup_destructive_keys(
    comparisons: list[dict[str, Any]], families: list[dict[str, Any]]
) -> set[str]:
    """Return source keys explicitly removed or remapped by Run 3 cleanup.

    Such an architecture decision resolves lesser name/scope candidates that
    disappear with the approved object.  Requiring a duplicate operation in
    every one of those candidate rows creates contradictory machinery without
    increasing regression protection.
    """
    keys: set[str] = set()
    for row in [*comparisons, *families]:
        if row.get("disposition") != "cleanup_operation":
            continue
        for operation in as_list(row.get("operations")):
            keys.update(destructive_object_keys(operation))
    return keys


def architecture_cleanup_action_signatures(
    comparisons: list[dict[str, Any]], families: list[dict[str, Any]]
) -> set[str]:
    """Return exact mutation signatures declared by Run 3 cleanup decisions.

    A generic candidate relationship cannot veto the architecture decision that
    explicitly removes or remaps the same member.  The exemption is deliberately
    tied to the complete structured mutation, rather than merely to object
    overlap, so an unrelated deletion cannot borrow another decision's cover.
    """
    signatures: set[str] = set()
    for row in [*comparisons, *families]:
        if row.get("disposition") != "cleanup_operation":
            continue
        for operation in as_list(row.get("operations")):
            signatures.add(_operation_group_key(operation))
    return signatures


RUNTIME_NEUTRAL_LIFECYCLE_FINDINGS = {
    "paused_objects_for_lifecycle_review",
    "unused_built_in_variable",
    "unused_object",
    "used_only_by_paused_tags",
}


def runtime_neutral_operational_deletions(
    operation: dict[str, Any], operational_by_id: dict[str, dict[str, Any]]
) -> set[str]:
    """Return deletions proven outside the active execution graph by Run 1.

    These removals do not alter current execution and therefore do not need a
    fabricated Run 3 relationship. Reference/remap validation and future-state
    simulation remain mandatory.
    """
    if any(
        as_list(operation.get(field))
        for field in ("creations", "additions", "changes", "remaps")
    ):
        return set()
    lifecycle_keys: set[str] = set()
    # A paused tag has no active execution path in this export regardless of
    # which review first proposes its retirement. This implements the explicit
    # lifecycle exception without requiring a duplicate Run 3 relationship.
    paused_tag_keys = {
        key
        for finding in operational_by_id.values()
        if finding.get("finding_type") == "paused_objects_for_lifecycle_review"
        for key in operational_object_keys(finding)
    }
    for reference in as_list(operation.get("source_references")):
        finding = operational_by_id.get(str(reference))
        if not finding or finding.get("finding_type") not in RUNTIME_NEUTRAL_LIFECYCLE_FINDINGS:
            continue
        lifecycle_keys.update(operational_object_keys(finding))
    return {
        str(item.get("object_key") or "")
        for item in as_list(operation.get("deletions"))
        if str(item.get("object_key") or "") in lifecycle_keys | paused_tag_keys
    }


def operational_source_bound_repair(
    operation: dict[str, Any], operational_by_id: dict[str, dict[str, Any]]
) -> bool:
    """Whether Run 1 supplies a deterministic, exact repair rationale."""
    for reference in as_list(operation.get("source_references")):
        finding = operational_by_id.get(str(reference))
        if not finding:
            continue
        if (
            finding.get("finding_class") == "deterministic_defect"
            and finding.get("disposition") == "cleanup_operation"
        ):
            return True
    return False


def creation_keys(operation: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for creation in as_list(operation.get("creations")):
        layer = str(creation.get("layer") or "")
        obj = creation.get("object") or {}
        id_key = ID_KEYS.get(layer, "")
        object_id = str(obj.get(id_key) or obj.get("name") or "")
        if layer and object_id:
            keys.add(f"{layer}:{object_id}")
    return keys


def consolidation_alignment_errors(
    operation: dict[str, Any], operational_by_id: dict[str, dict[str, Any]]
) -> list[str]:
    references = set(as_list(operation.get("source_references")))
    findings = [operational_by_id[key] for key in references if key in operational_by_id]
    requires_architecture = any(
        finding.get("deterministic_action_candidate") == "consolidate_candidate"
        for finding in findings
    )
    if requires_architecture and "business_architecture" not in as_list(
        operation.get("source_runs")
    ):
        return [
            f"{operation.get('operation_key')!r}: deterministic consolidation lacks an "
            "aligned business-architecture operation"
        ]
    return []


def comparison_reconciliation_errors(
    operation_key: str,
    destructive_keys: set[str],
    behavior_keys: set[str],
    comparisons: list[dict[str, Any]],
    architecture_cleanup: bool = False,
) -> list[str]:
    errors: list[str] = []
    for comparison in comparisons:
        candidate_keys = {
            str(value) for value in as_list(comparison.get("candidate_object_keys"))
        }
        destructive = sorted(candidate_keys & destructive_keys)
        behavior = sorted(candidate_keys & behavior_keys)
        # Non-destructive corrections (consent, regex, references, blockers)
        # can preserve a cross-object relationship. Only removal/remap of a
        # candidate contradicts a decision that retains or leaves that exact
        # candidate relationship unresolved.
        if not destructive:
            continue
        # This exact mutation is itself a validated Run 3 cleanup decision.
        # It resolves lower-strength candidate rows involving the member;
        # requiring the same deletion/remap to be copied into every such row
        # creates contradictory duplicate operations without extra safety.
        if architecture_cleanup:
            continue
        disposition = comparison.get("disposition")
        verdict = comparison.get("relationship_verdict")
        comparison_id = comparison.get("comparison_id")
        if destructive and disposition == "keep" and verdict in {
            "Intentional variant",
            "Complementary",
            "Unrelated",
        }:
            errors.append(
                f"{operation_key!r} removes or remaps {destructive!r}, but architecture "
                f"comparison {comparison_id} says to keep them"
            )
        if disposition in {"owner_decision_needed", "container_evidence_limit"}:
            errors.append(
                f"{operation_key!r} changes {behavior!r} while architecture "
                f"comparison {comparison_id} is unresolved"
            )
    return errors


def family_reconciliation_errors(
    operation_key: str,
    destructive_keys: set[str],
    behavior_keys: set[str],
    families: list[dict[str, Any]],
    architecture_cleanup: bool = False,
) -> list[str]:
    errors: list[str] = []
    for family in families:
        # Dependency consolidation is governed by its own relationship. It
        # should not force every consuming business family to become a fake
        # conflict. A family contradiction exists when a root member that the
        # family retains is itself removed or remapped.
        family_keys = {str(value) for value in as_list(family.get("member_object_keys"))}
        destructive = sorted(destructive_keys & family_keys)
        behavior = sorted(behavior_keys & family_keys)
        if not destructive:
            continue
        if architecture_cleanup:
            continue
        disposition = family.get("disposition")
        verdict = family.get("relationship_verdict")
        family_id = family.get("family_id")
        if disposition in {"owner_decision_needed", "container_evidence_limit"}:
            errors.append(
                f"{operation_key!r} changes {behavior!r} while architecture "
                f"family {family_id} remains unresolved"
            )
        elif destructive and disposition == "keep" and verdict in {
            "Intentional variant",
            "Complementary",
            "Unrelated",
        }:
            errors.append(
                f"{operation_key!r} removes or remaps {destructive!r} but architecture "
                f"family {family_id} says to keep the chain"
            )
    return errors


def validate_cross_run_reconciliation(
    operational: dict[str, Any],
    architecture: dict[str, Any],
    operations: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    operational_by_id = {
        str(row.get("finding_id") or ""): row for row in as_list(operational.get("findings"))
    }
    comparison_rows = as_list(architecture.get("comparisons"))
    family_rows = as_list(architecture.get("families"))
    architecture_cleanup_actions = architecture_cleanup_action_signatures(
        comparison_rows, family_rows
    )
    for operation in operations:
        operation_key = str(operation.get("operation_key") or "")
        destructive_keys = destructive_object_keys(operation)
        behavior_keys = behavior_impact_keys(operation)
        runtime_neutral_keys = runtime_neutral_operational_deletions(
            operation, operational_by_id
        )
        behavior_keys -= runtime_neutral_keys
        reconciliation_destructive_keys = destructive_keys - runtime_neutral_keys
        created_keys = {
            key for key in creation_keys(operation) if not key.startswith("folder:")
        }
        architecture_cleanup = (
            bool(reconciliation_destructive_keys)
            and "business_architecture" in as_list(operation.get("source_runs"))
            and _operation_group_key(operation) in architecture_cleanup_actions
        )
        if not destructive_keys or not destructive_keys <= runtime_neutral_keys:
            errors.extend(consolidation_alignment_errors(operation, operational_by_id))
        if behavior_keys and "business_architecture" not in as_list(
            operation.get("source_runs")
        ):
            supporting_family_ids = architecture_family_support(behavior_keys, family_rows)
            source_bound_direct_repair = (
                not destructive_keys
                and not created_keys
                and (
                    "configuration_correctness" in as_list(operation.get("source_runs"))
                    or operational_source_bound_repair(operation, operational_by_id)
                )
                and bool(supporting_family_ids)
            )
            if source_bound_direct_repair:
                operation["architecture_supporting_family_ids"] = sorted(
                    supporting_family_ids
                )
            else:
                errors.append(
                    f"{operation_key!r} changes behavior of {sorted(behavior_keys)!r} "
                    "without an aligned business-architecture operation"
                )
        if created_keys and "business_architecture" not in as_list(
            operation.get("source_runs")
        ):
            errors.append(
                f"{operation_key!r} creates {sorted(created_keys)!r} without an aligned "
                "business-architecture operation"
            )
        errors.extend(
            comparison_reconciliation_errors(
                operation_key,
                reconciliation_destructive_keys,
                behavior_keys,
                comparison_rows,
                architecture_cleanup,
            )
        )
        errors.extend(
            family_reconciliation_errors(
                operation_key,
                reconciliation_destructive_keys,
                behavior_keys,
                family_rows,
                architecture_cleanup,
            )
        )
    return errors


def affected_objects(operation: dict[str, Any], catalog: dict[str, dict[str, str]]) -> str:
    labels = []
    for key in as_list(operation.get("affected_object_keys")):
        item = catalog.get(str(key))
        labels.append(
            f"{key} - {item['object_name']}" if item and item["object_name"] else str(key)
        )
    return "; ".join(labels)


def configuration_taxonomy(review: dict[str, Any]) -> tuple[str, str]:
    text = json.dumps(
        {
            "name": review.get("object_name"),
            "vendor": review.get("detected_vendor"),
            "category": review.get("vendor_category"),
            "consent": review.get("effective_consent_route_facts"),
            "defects": review.get("defects"),
            "basis": review.get("correctness_basis"),
        },
        ensure_ascii=False,
    ).lower()
    if re.search(r"consent|storage|cmp|personalization|ad_user_data", text):
        return "Consent & compliance", "Consent mismatch"
    if review.get("layer") == "customTemplate" or review.get("required_code_line_hashes"):
        return "Custom code & templates", "Custom code risk"
    if re.search(r"purchase|ecommerce|items|currency|quantity|transaction", text):
        return "Ecommerce payload quality", "Wrong value or formula logic"
    if str(review.get("vendor_category") or "") in {"media", "affiliate"}:
        return "Media platform tracking", "Incomplete payload"
    if re.search(r"server|transport_url|first.party|routing", text):
        return "Server-side tracking", "Server-side routing unclear"
    if review.get("layer") == "trigger":
        return "Event firing logic", "Wrong trigger timing"
    return "Tracking plan / dataLayer", "Unclear business purpose"


def architecture_taxonomy(row: dict[str, Any]) -> tuple[str, str]:
    comparison_types = set(as_list(row.get("comparison_types")))
    text = json.dumps(row.get("candidate_basis") or [], ensure_ascii=False).lower()
    if "different_consent_purposes_same_logic" in comparison_types or "consent" in text:
        return "Consent & compliance", "Consent mismatch"
    if "exact_configuration" in comparison_types:
        return "GTM hygiene", "Exact duplicate"
    if comparison_types & {
        "equivalent_trigger_conditions",
        "near_equivalent_trigger_conditions",
        "trigger_condition_subset",
        "shared_business_scope",
        "multi_firing_route_consolidation_review",
    }:
        return "Event firing logic", "Functional overlap"
    if comparison_types & {
        "same_vendor_destination_event",
        "same_vendor_event_family",
        "cross_vendor_event_family",
    }:
        return "Data quality / reporting", "Duplicate firing"
    if "server" in text:
        return "Server-side tracking", "Server-side routing unclear"
    return "Stack & architecture", "Functional overlap"


def context_taxonomy(question: str) -> tuple[str, str]:
    lowered = question.lower()
    if "cmp" in lowered or "consent" in lowered:
        return "Consent & compliance", "Consent mismatch"
    if "server" in lowered or "route" in lowered:
        return "Server-side tracking", "Server-side routing unclear"
    return "Governance / ownership", "Unclear business purpose"


def context_recommendation(question: str) -> str:
    lowered = question.lower()
    if "cmp" in lowered or "consent" in lowered:
        return (
            "Confirm the CMP and consent owner, then apply the strictest source-supported "
            "consent route until the intended purpose mapping is documented."
        )
    if "server" in lowered or "route" in lowered:
        return (
            "Confirm the browser-to-server route owner and inspect the receiving container "
            "before approving any cleanup that depends on unseen server behavior."
        )
    return (
        "Provide the named business or scope decision, then use it to choose the simplest "
        "configuration that preserves the required measurement outcome."
    )


def context_decisions(operational: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, question_value in enumerate(
        as_list(operational.get("unresolved_context_questions")), start=1
    ):
        question = str(question_value)
        area, problem_type = context_taxonomy(question)
        rows.append(
            {
                "decision_id": f"CONTEXT-{index:03d}",
                "source_run": "audit_context",
                "source_object_keys": [],
                "verdict": "Context required",
                "disposition": "owner_decision_needed",
                "title": "Audit context confirmation",
                "area": area,
                "problem_type": problem_type,
                "affected_objects": "Container scope",
                "summary": question,
                "owner_question": question,
                "recommended_action": context_recommendation(question),
                "confidence": "High",
                "operation_keys": [],
            }
        )
    return rows


def operational_decisions(operational: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for finding in as_list(operational.get("findings")):
        rows.append(
            {
                "decision_id": str(finding.get("finding_id") or ""),
                "source_run": "operational_sanitation",
                "source_object_keys": operational_object_keys(finding),
                "verdict": str(finding.get("finding_type") or ""),
                "disposition": str(finding.get("disposition") or ""),
                "finding_class": str(finding.get("finding_class") or ""),
                "title": str(
                    finding.get("title")
                    or str(finding.get("finding_type") or "").replace("_", " ").title()
                ),
                "area": str(finding.get("area") or "GTM hygiene"),
                "problem_type": str(
                    finding.get("problem_type") or "Unnecessary complexity"
                ),
                "affected_objects": "; ".join(
                    f"{object_id} - {name}"
                    for object_id, name in zip(
                        as_list(finding.get("object_ids")),
                        as_list(finding.get("object_names")),
                        strict=False,
                    )
                ),
                "summary": str(
                    finding.get("problem")
                    or finding.get("rationale")
                    or finding.get("deterministic_evidence")
                    or ""
                ),
                "owner_question": str(finding.get("owner_question") or ""),
                "recommended_action": str(finding.get("recommended_action") or ""),
                "confidence": str(finding.get("confidence") or ""),
                "operation_keys": [str(finding.get("operation_key") or "")]
                if finding.get("disposition") == "cleanup_operation"
                else [],
            }
        )
    return rows


def configuration_decisions(configuration: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for review in as_list(configuration.get("rows")):
        operation = review.get("operation") or {}
        area, problem_type = configuration_taxonomy(review)
        rows.append(
            {
                "decision_id": str(review.get("review_id") or review.get("object_key") or ""),
                "source_run": "configuration_correctness",
                "source_object_keys": [str(review.get("object_key") or "")],
                "verdict": str(review.get("correctness_verdict") or ""),
                "disposition": str(review.get("disposition") or ""),
                "title": str(
                    review.get("object_name")
                    or review.get("object_key")
                    or "Configuration decision"
                ),
                "area": area,
                "problem_type": problem_type,
                "affected_objects": f"{review.get('object_key')} - {review.get('object_name')}",
                "summary": str(
                    review.get("correctness_basis")
                    or review.get("configured_output_or_side_effect")
                    or ""
                ),
                "owner_question": str(review.get("owner_question") or ""),
                "recommended_action": str(review.get("recommended_action") or ""),
                "confidence": str(review.get("confidence") or ""),
                "operation_keys": [str(operation.get("operation_key") or "")]
                if review.get("disposition") == "cleanup_operation"
                else [],
            }
        )
    return rows


def architecture_decision_row(
    row: dict[str, Any], id_field: str, key_field: str
) -> dict[str, Any]:
    area, problem_type = architecture_taxonomy(row)
    return {
        "decision_id": str(row.get(id_field) or ""),
        "source_run": "business_architecture",
        "source_object_keys": [str(value) for value in as_list(row.get(key_field))],
        "verdict": str(row.get("relationship_verdict") or ""),
        "disposition": str(row.get("disposition") or ""),
        "title": str(
            row.get("family_label")
            or row.get("comparison_id")
            or row.get(id_field)
            or "Architecture decision"
        ),
        "area": area,
        "problem_type": problem_type,
        "affected_objects": "; ".join(str(value) for value in as_list(row.get(key_field))),
        "summary": str(
            row.get("analyst_rationale")
            or row.get("architecture_effect")
            or row.get("family_purpose")
            or ""
        ),
        "owner_question": str(row.get("owner_question") or ""),
        "recommended_action": str(row.get("recommended_action") or ""),
        "comparison_types": [
            str(value) for value in as_list(row.get("comparison_types")) if str(value)
        ],
        "confidence": str(row.get("confidence") or ""),
        "operation_keys": [
            str(operation.get("operation_key") or "")
            for operation in as_list(row.get("operations"))
        ],
    }


def architecture_decisions(architecture: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for collection, id_field, key_field in (
        (as_list(architecture.get("families")), "family_id", "chain_object_keys"),
        (
            as_list(architecture.get("comparisons")),
            "comparison_id",
            "candidate_object_keys",
        ),
    ):
        rows.extend(
            architecture_decision_row(row, id_field, key_field) for row in collection
        )
    return rows


def decision_ledger(
    operational: dict[str, Any],
    configuration: dict[str, Any],
    architecture: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = [
        *context_decisions(operational),
        *operational_decisions(operational),
        *configuration_decisions(configuration),
        *architecture_decisions(architecture),
    ]
    return sorted(rows, key=lambda row: (row["source_run"], row["decision_id"]))


def projected_object_counts(
    catalog: dict[str, dict[str, str]], operations: list[dict[str, Any]]
) -> dict[str, dict[str, int]]:
    layers = sorted({item.get("layer", "") for item in catalog.values() if item.get("layer")})
    deleted = {
        str(item.get("object_key") or "")
        for operation in operations
        for item in as_list(operation.get("deletions"))
    }
    created: set[str] = set()
    for operation in operations:
        for creation in as_list(operation.get("creations")):
            layer = str(creation.get("layer") or "")
            obj = creation.get("object")
            if layer not in ID_KEYS or not isinstance(obj, dict):
                continue
            object_id = str(obj.get(ID_KEYS[layer]) or obj.get("name") or "")
            if object_id:
                created.add(f"{layer}:{object_id}")
    layers = sorted(
        set(layers)
        | {key.split(":", 1)[0] for key in created if ":" in key}
    )
    rows: dict[str, dict[str, int]] = {}
    for layer in layers:
        before = sum(1 for item in catalog.values() if item.get("layer") == layer)
        deletion_count = sum(
            1
            for key in deleted
            if key in catalog and catalog[key].get("layer") == layer
        )
        creation_count = sum(1 for key in created if key.startswith(layer + ":"))
        rows[layer] = {
            "before": before,
            "after": before - deletion_count + creation_count,
            "delta": creation_count - deletion_count,
        }
    return rows


def measurement_preservation_summary(
    architecture: dict[str, Any],
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Project how the cleanup plan treats every source-confirmed business family."""
    families: list[dict[str, Any]] = []
    for family in as_list(architecture.get("families")):
        family_id = str(family.get("family_id") or "")
        family_keys = {
            str(value)
            for value in [
                *as_list(family.get("member_object_keys")),
                *as_list(family.get("chain_object_keys")),
            ]
            if str(value)
        }
        related = [
            operation
            for operation in operations
            if (
                family_keys
                & {
                    str(value)
                    for value in [
                        *as_list(operation.get("affected_object_keys")),
                        *as_list(operation.get("source_object_keys")),
                    ]
                    if str(value)
                }
            )
            or any(
                str(reference).startswith(f"{family_id}:operation:")
                for reference in as_list(operation.get("source_references"))
            )
        ]
        disposition = str(family.get("disposition") or "")
        if disposition == "owner_decision_needed":
            status = "owner_confirmation_required"
        elif disposition == "container_evidence_limit":
            status = "container_evidence_boundary"
        elif related:
            status = "planned_change"
        elif disposition == "keep":
            status = "retained_unchanged"
        else:
            status = "reviewed_no_operation"
        families.append(
            {
                "family_id": family_id,
                "family_label": str(
                    family.get("family_label")
                    or family.get("family_key")
                    or family.get("family_id")
                    or ""
                ),
                "preservation_status": status,
                "source_object_keys": sorted(family_keys),
                "related_operation_ids": sorted(
                    {
                        str(operation.get("operation_id") or "")
                        for operation in related
                        if operation.get("operation_id")
                    }
                ),
                "required_business_behavior": str(
                    family.get("business_action")
                    or family.get("family_purpose")
                    or family.get("analyst_rationale")
                    or ""
                ),
                "execution_path": str(family.get("execution_path_summary") or ""),
                "consent_and_routing": str(
                    family.get("consent_and_sequence_coherence") or ""
                ),
                "target_state": str(
                    family.get("target_architecture")
                    or family.get("recommended_action")
                    or ""
                ),
                "owner_question": str(family.get("owner_question") or ""),
            }
        )
    counts = {
        status: sum(
            1 for family in families if family.get("preservation_status") == status
        )
        for status in (
            "retained_unchanged",
            "planned_change",
            "owner_confirmation_required",
            "container_evidence_boundary",
            "reviewed_no_operation",
        )
    }
    unresolved = counts["owner_confirmation_required"] + counts[
        "container_evidence_boundary"
    ]
    return {
        "status": "owner_confirmation_required" if unresolved else "complete",
        "scope": (
            "Container-visible preservation of configured measurement families, "
            "dependencies, consent controls, and routing. Live delivery, dataLayer values, "
            "CMP behavior, vendor acceptance, and unseen server behavior remain outside "
            "this container-only projection."
        ),
        "counts": counts,
        "families": families,
    }


def annotate_operation_preservation(
    operations: list[dict[str, Any]],
    preservation: dict[str, Any],
) -> None:
    for operation in operations:
        relevant_keys = {
            str(value)
            for value in [
                *as_list(operation.get("affected_object_keys")),
                *as_list(operation.get("source_object_keys")),
            ]
            if str(value)
        }
        source_references = {
            str(value)
            for value in as_list(operation.get("source_references"))
            if str(value)
        }
        families = [
            family
            for family in as_list(preservation.get("families"))
            if (
                relevant_keys
                & {
                    str(value)
                    for value in as_list(family.get("source_object_keys"))
                    if str(value)
                }
            )
            or any(
                reference.startswith(f"{family.get('family_id')}:operation:")
                for reference in source_references
            )
        ]
        operation["affected_measurement_family_ids"] = sorted(
            {
                str(family.get("family_id") or "")
                for family in families
                if family.get("family_id")
            }
        )
        operation["retained_behavior"] = " ".join(
            dict.fromkeys(
                str(family.get("required_business_behavior") or "")
                for family in families
                if specific_text(family.get("required_business_behavior"), 5)
            )
        )


def validate_review_bundle(
    operational: dict[str, Any],
    configuration: dict[str, Any],
    architecture: dict[str, Any],
    route: str,
) -> tuple[list[str], set[str], set[str], set[str]]:
    errors: list[str] = []
    if not route.strip():
        errors.append("execution route must not be blank")
    expected_kinds = {
        "operational": "gtm_operational_sanitation_review",
        "configuration": "gtm_configuration_correctness_review",
        "architecture": "gtm_business_architecture_review",
    }
    expected_runs = {
        "operational": "operational_sanitation",
        "configuration": "configuration_correctness",
        "architecture": "business_architecture",
    }
    supplied = {
        "operational": operational,
        "configuration": configuration,
        "architecture": architecture,
    }
    hashes: set[str] = set()
    fact_hashes: set[str] = set()
    context_hashes: set[str] = set()
    hash_targets = (
        ("source_sha256", hashes),
        ("shared_facts_sha256", fact_hashes),
        ("context_sha256", context_hashes),
    )
    for label, payload in supplied.items():
        if payload.get("kind") != expected_kinds[label]:
            errors.append(f"{label} review kind is invalid")
        if payload.get("run_status") != "complete":
            errors.append(f"{label} review is not complete")
        if (payload.get("input_contract") or {}).get("review_run") != expected_runs[label]:
            errors.append(f"{label} review input contract is invalid")
        errors.extend(validate_review_provenance(payload, payload, f"{label} review"))
        for field, target in hash_targets:
            if payload.get(field):
                target.add(str(payload.get(field)))
    for values, message in (
        (hashes, "the three reviews do not share one source export hash"),
        (fact_hashes, "the three reviews do not share one canonical fact hash"),
        (context_hashes, "the three reviews do not share one audit context hash"),
    ):
        if len(values) != 1:
            errors.append(message)
    return errors, hashes, fact_hashes, context_hashes


def ledger_link_errors(
    ledger: list[dict[str, Any]], operations: list[dict[str, Any]]
) -> list[str]:
    compiled_keys = {
        key
        for row in operations
        for key in [
            str(row.get("operation_key") or ""),
            *[str(value) for value in as_list(row.get("source_operation_keys"))],
        ]
        if key
    }
    errors: list[str] = []
    for decision in ledger:
        if decision.get("disposition") != "cleanup_operation":
            continue
        operation_keys = {key for key in as_list(decision.get("operation_keys")) if key}
        if not operation_keys:
            errors.append(
                f"decision {decision.get('decision_id')!r} is marked cleanup_operation "
                "without an operation key"
            )
            continue
        missing_keys = sorted(operation_keys - compiled_keys)
        if missing_keys:
            errors.append(
                f"decision {decision.get('decision_id')!r} is missing from compiled "
                "operations: " + ", ".join(missing_keys)
            )
    return errors


EXECUTION_PHASES = (
    ("create", "creations"),
    ("add", "additions"),
    ("change", "changes"),
    ("remap", "remaps"),
    ("rename", "renames"),
    ("delete", "deletions"),
)


def packetize_operations(
    rows: list[dict[str, Any]],
    route: str,
    catalog: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for number, operation in enumerate(rows, start=1):
        packet = copy.deepcopy(operation)
        readiness = str(operation.get("execution_readiness") or "")
        blocked = readiness in {"owner_blocked", "not_actionable"}
        packet.update(
            {
                "operation_id": f"OP-{number:04d}",
                "affected_objects": affected_objects(operation, catalog),
                "object_identity": "; ".join(
                    f"{key}|{catalog.get(key, {}).get('config_hash', '')}"
                    for key in as_list(operation.get("affected_object_keys"))
                ),
                "source_lenses": ", ".join(as_list(operation.get("source_runs"))),
                "resolution_status": "proposed",
                "approval_status": (
                    "pending_owner_decision" if blocked else "pending_approval"
                ),
                "risk_class": operation.get("priority"),
                "blocker": operation.get("preconditions") if blocked else "",
                "route": route,
                "execution_order": number,
                "execution_phases": [
                    phase for phase, field in EXECUTION_PHASES if as_list(operation.get(field))
                ],
            }
        )
        packets.append(packet)
    return packets


def action_completeness_report(
    ledger: list[dict[str, Any]],
) -> dict[str, Any]:
    """Judge whether the audit has become a usable cleanup plan.

    Review validators prove coverage. This compact outcome check prevents a
    completed audit from substituting owner questions for source-visible fixes.
    """

    errors: list[str] = []
    for decision in ledger:
        decision_id = str(decision.get("decision_id") or "<missing>")
        source_run = str(decision.get("source_run") or "")
        disposition = str(decision.get("disposition") or "")
        verdict = str(decision.get("verdict") or "")
        linked = [str(value) for value in as_list(decision.get("compiled_operation_ids"))]

        if disposition == "cleanup_operation" and not linked:
            errors.append(f"{decision_id}: cleanup decision has no compiled operation")
        finding_class = str(decision.get("finding_class") or "deterministic_defect")
        if (
            source_run == "operational_sanitation"
            and disposition == "owner_decision_needed"
            and finding_class not in {"review_candidate", "business_decision"}
        ):
            errors.append(
                f"{decision_id}: deterministic operational finding must become an exact "
                "cleanup operation or an intake-locked documented exception"
            )
        if (
            source_run == "operational_sanitation"
            and disposition == "keep"
            and finding_class != "review_candidate"
        ):
            errors.append(
                f"{decision_id}: only a source-locked review candidate may be retained "
                "without a cleanup operation"
            )
        if (
            source_run == "configuration_correctness"
            and verdict == "Issue"
            and disposition != "cleanup_operation"
        ):
            errors.append(
                f"{decision_id}: source-proven configuration Issue requires an exact "
                "cleanup operation"
            )
        if disposition in {"owner_decision_needed", "container_evidence_limit"} and not specific_text(
            decision.get("recommended_action"), 6
        ):
            errors.append(
                f"{decision_id}: unresolved decision lacks a concrete recommended action"
            )

    counts = {
        disposition: sum(
            1 for decision in ledger if decision.get("disposition") == disposition
        )
        for disposition in (
            "cleanup_operation",
            "keep",
            "documented_exception",
            "owner_decision_needed",
            "container_evidence_limit",
            "not_applicable",
        )
    }
    return {
        "status": "pass" if not errors else "incomplete",
        "counts": counts,
        "errors": errors,
    }


def packet_index(packets: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for packet in packets:
        keys = {
            str(packet.get("operation_key") or ""),
            *{
                str(value)
                for value in as_list(packet.get("source_operation_keys"))
                if str(value)
            },
        }
        for key in keys - {""}:
            index[key] = packet
    return index


def link_ledger_packets(
    ledger: list[dict[str, Any]], packets: list[dict[str, Any]]
) -> None:
    by_key = packet_index(packets)
    for decision in ledger:
        linked = [
            by_key[key]
            for key in as_list(decision.get("operation_keys"))
            if key in by_key
        ]
        decision["compiled_operation_ids"] = sorted(
            {str(packet.get("operation_id") or "") for packet in linked}
        )
        decision["execution_selection"] = sorted(
            {str(packet.get("resolution_status") or "") for packet in linked}
        )


def compile_operations(
    operational: dict[str, Any],
    configuration: dict[str, Any],
    architecture: dict[str, Any],
    route: str,
    catalog: dict[str, dict[str, str]] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    errors, hashes, fact_hashes, context_hashes = validate_review_bundle(
        operational, configuration, architecture, route
    )
    collected = collect_operations(operational, configuration, architecture)
    merged = merge_compatible_operations(collected, errors)
    ledger = decision_ledger(operational, configuration, architecture)
    errors.extend(ledger_link_errors(ledger, merged))
    errors.extend(validate_cross_run_reconciliation(operational, architecture, merged))
    errors.extend(validate_mutation_conflicts(merged))
    catalog = catalog or {}
    packets = packetize_operations(
        merged,
        route,
        catalog,
    )
    link_ledger_packets(ledger, packets)
    action_completeness = action_completeness_report(ledger)
    if errors:
        packets = []
        link_ledger_packets(ledger, packets)
        action_completeness = action_completeness_report(ledger)
        action_completeness["status"] = "incomplete"
        action_completeness["errors"].append(
            "operation compilation has unresolved validation errors"
        )
    measurement_preservation = measurement_preservation_summary(
        architecture, packets
    )
    annotate_operation_preservation(packets, measurement_preservation)
    return {
        "kind": "gtm_reconciled_operations",
        "schema_version": 3,
        "source_file": operational.get("source_file"),
        "source_sha256": next(iter(hashes), ""),
        "shared_facts_sha256": next(iter(fact_hashes), ""),
        "context_sha256": next(iter(context_hashes), ""),
        "run_statuses": {
            "operational_sanitation": operational.get("run_status"),
            "configuration_correctness": configuration.get("run_status"),
            "business_architecture": architecture.get("run_status"),
        },
        "route": route,
        "plan_status": (
            "complete" if action_completeness["status"] == "pass" else "incomplete_actions"
        ),
        "action_completeness": action_completeness,
        "projected_object_counts": projected_object_counts(catalog, packets),
        "measurement_preservation": measurement_preservation,
        "decision_ledger": ledger,
        "operations": packets,
    }, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("operational_review", type=Path)
    parser.add_argument("configuration_review", type=Path)
    parser.add_argument("architecture_review", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--route", default="Pending user selection")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    validators = (
        ("operational", validate_operational_review, args.operational_review),
        ("configuration", validate_configuration_review, args.configuration_review),
        ("architecture", validate_architecture_review, args.architecture_review),
    )
    failed = False
    for label, validator, path in validators:
        review_errors, review_warnings = validator(args.export, path)
        for warning in review_warnings:
            print(f"WARNING [{label}]: {warning}")
        for error in review_errors:
            print(f"ERROR [{label}]: {error}", file=sys.stderr)
            failed = True
    if failed:
        return 1

    operational = load_json(args.operational_review)
    configuration = load_json(args.configuration_review)
    architecture = load_json(args.architecture_review)
    payload, errors = compile_operations(
        operational,
        configuration,
        architecture,
        args.route,
        source_object_catalog(args.export),
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(args.output), "operations": len(payload["operations"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
