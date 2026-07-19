#!/usr/bin/env python3
"""Build deterministic effective-consent route facts from a GTM export."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any
from urllib.parse import urlsplit

from gtm_lib import refs, stable_hash, walk_json_fields
from gtm_vendor_registry import detect_vendor_text

CONSENT_PURPOSES = (
    "analytics_storage",
    "ad_storage",
    "ad_user_data",
    "ad_personalization",
    "functionality_storage",
    "personalization_storage",
    "security_storage",
)
MEDIA_CATEGORIES = {"media", "affiliate", "publisher"}
GOOGLE_NATIVE_CONSENT_TYPES = {
    "awct",
    "flc",
    "gaawe",
    "gaawc",
    "gclidw",
    "googtag",
    "sp",
}
SERVER_ROUTE_KEY_RE = re.compile(
    r"transport_url|server_container_url|endpoint|first.party|server.side",
    re.I,
)
CONSENT_SIGNAL_RE = re.compile(
    r"consent|optanon|onetrust|didomi|cookiebot|\bcmp\b",
    re.I,
)
URL_RE = re.compile(r"https?://[^\s\"'<>\\)]+", re.I)
FORWARDING_METADATA_SUFFIXES = (
    ".accountId",
    ".containerId",
    ".fingerprint",
    ".path",
    ".tagId",
    ".triggerId",
    ".variableId",
    ".name",
    ".type",
)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def consent_purpose(name: str) -> str:
    normalized = re.sub(r"[\s.-]+", "_", name.lower())
    return next((purpose for purpose in CONSENT_PURPOSES if purpose in normalized), "")


def consent_values(obj: dict[str, Any], source_path: str = "$") -> list[dict[str, str]]:
    rows = []
    for fact in walk_json_fields(obj, source_path):
        searchable = f"{fact['json_path']} {fact.get('value_preview') or ''}"
        if not any(purpose in searchable.lower() for purpose in CONSENT_PURPOSES) and not re.search(
            r"consent|optanon|didomi", searchable, re.I
        ):
            continue
        rows.append(
            {
                "json_path": fact["json_path"],
                "value_hash": fact["value_hash"],
                "value_preview": str(fact.get("value_preview") or ""),
            }
        )
    return rows


def server_route_hosts(obj: dict[str, Any]) -> list[str]:
    text = json.dumps(obj, ensure_ascii=False)
    if not SERVER_ROUTE_KEY_RE.search(text):
        return []
    hosts = set()
    for match in URL_RE.finditer(text):
        try:
            host = urlsplit(match.group(0).rstrip(".,);\"")).hostname
        except ValueError:
            host = None
        if host:
            hosts.add(host.lower())
    return sorted(hosts)


def referenced_variables(
    obj: dict[str, Any], variables: list[dict[str, Any]]
) -> list[tuple[int, dict[str, Any]]]:
    """Resolve the exported variable chain without interpreting its business meaning."""
    by_name = {
        str(variable.get("name") or ""): (index, variable)
        for index, variable in enumerate(variables)
        if variable.get("name")
    }
    queue = sorted(refs(obj))
    visited: set[str] = set()
    resolved: list[tuple[int, dict[str, Any]]] = []
    while queue:
        reference = queue.pop(0)
        if reference in visited:
            continue
        visited.add(reference)
        target = by_name.get(reference)
        if not target:
            continue
        index, variable = target
        resolved.append((index, variable))
        queue.extend(sorted(refs(variable) - visited))
    return resolved


def forwarding_consent_values(
    obj: dict[str, Any], source_path: str, via_variable: str = ""
) -> list[dict[str, str]]:
    """Return consent-like payload evidence, excluding local consentSettings metadata."""
    rows = []
    for fact in consent_values(obj, source_path):
        json_path = str(fact.get("json_path") or "")
        if ".consentSettings" in json_path or json_path.endswith(FORWARDING_METADATA_SUFFIXES):
            continue
        searchable = f"{json_path} {fact.get('value_preview') or ''} {via_variable}"
        if not consent_purpose(searchable) and not CONSENT_SIGNAL_RE.search(searchable):
            continue
        rows.append({**fact, "via_variable": via_variable})
    return rows


def tag_consent_route(
    tag: dict[str, Any],
    source_path: str = "$",
    variables: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    vendor, category = detect_vendor_text(json.dumps(tag, ensure_ascii=False))
    settings = tag.get("consentSettings") or {}
    status = str(settings.get("consentStatus") or "").upper() or "MISSING"
    additional_checks = status not in {"MISSING", "NOT_SET"}
    blockers = sorted(str(value) for value in as_list(tag.get("blockingTriggerId")))
    consent_references = sorted(
        reference
        for reference in refs(tag)
        if consent_purpose(reference) or re.search(r"consent|optanon|didomi", reference, re.I)
    )
    tag_type = str(tag.get("type") or "").lower()
    native_capability = tag_type in GOOGLE_NATIVE_CONSENT_TYPES
    variable_chain = referenced_variables(tag, variables or [])
    forwarding_evidence = forwarding_consent_values(tag, source_path)
    server_hosts = set(server_route_hosts(tag))
    forwarding_variables: set[str] = set()
    for index, variable in variable_chain:
        variable_name = str(variable.get("name") or "")
        variable_path = f"$.containerVersion.variable[{index}]"
        variable_evidence = forwarding_consent_values(
            variable,
            variable_path,
            via_variable=variable_name,
        )
        if variable_evidence:
            forwarding_variables.add(variable_name)
            forwarding_evidence.extend(variable_evidence)
        server_hosts.update(server_route_hosts(variable))

    forwarded_purposes = sorted(
        {
            purpose
            for row in forwarding_evidence
            for purpose in [
                consent_purpose(
                    f"{row.get('json_path') or ''} {row.get('value_preview') or ''} "
                    f"{row.get('via_variable') or ''}"
                )
            ]
            if purpose
        }
    )
    forwarded_cmp_signal = any(
        CONSENT_SIGNAL_RE.search(
            f"{row.get('json_path') or ''} {row.get('value_preview') or ''} "
            f"{row.get('via_variable') or ''}"
        )
        for row in forwarding_evidence
    )
    if additional_checks or blockers:
        control_status = "explicit_export_control"
    elif server_hosts and forwarding_evidence:
        control_status = "server_forwarded_consent_contract"
    elif server_hosts:
        control_status = "server_contract_unproven"
    elif native_capability:
        control_status = "native_consent_contract"
    elif consent_references:
        control_status = "consent_signal_review"
    else:
        control_status = "unproven_export_control"
    return {
        "vendor": vendor,
        "vendor_category": category,
        "consent_status": status,
        "additional_consent_checks_visible": additional_checks,
        "blocking_trigger_ids": blockers,
        "consent_variable_references": consent_references,
        "native_consent_capability": native_capability,
        "server_routing_hosts": sorted(server_hosts),
        "server_consent_forwarding_variables": sorted(forwarding_variables),
        "server_consent_forwarding_evidence": forwarding_evidence,
        "forwarded_consent_purposes": forwarded_purposes,
        "forwarded_cmp_signal_visible": forwarded_cmp_signal,
        "server_enforcement_visibility": (
            "not_visible_in_web_export" if server_hosts else "not_applicable"
        ),
        "consent_source_values": consent_values(tag, source_path),
        "effective_control_status": control_status,
        "requires_media_consent_review": category in MEDIA_CATEGORIES,
    }


def consent_variable_conflicts(variables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[tuple[dict[str, Any], str]]] = defaultdict(list)
    for variable in variables:
        purpose = consent_purpose(str(variable.get("name") or ""))
        if not purpose:
            continue
        payload = {
            key: value
            for key, value in variable.items()
            if key not in {"variableId", "name", "accountId", "containerId", "fingerprint", "path"}
        }
        groups[stable_hash(payload)].append((variable, purpose))
    conflicts = []
    for logic_hash, group in sorted(groups.items()):
        purposes = sorted({purpose for _variable, purpose in group})
        if len(group) < 2 or len(purposes) < 2:
            continue
        conflicts.append(
            {
                "logic_hash": logic_hash,
                "purposes": purposes,
                "variables": [variable for variable, _purpose in group],
            }
        )
    return conflicts
