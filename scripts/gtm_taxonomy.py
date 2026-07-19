#!/usr/bin/env python3
"""Shared human-facing cleanup-plan taxonomy."""

from __future__ import annotations

from typing import Any

AREAS = {
    "Stack & architecture",
    "GTM hygiene",
    "Tracking plan / dataLayer",
    "Event firing logic",
    "Ecommerce payload quality",
    "Media platform tracking",
    "Consent & compliance",
    "Server-side tracking",
    "Data quality / reporting",
    "Web performance",
    "Custom code & templates",
    "Governance / ownership",
}

PROBLEM_TYPES = {
    "Broken reference",
    "Unused object",
    "Exact duplicate",
    "Functional overlap",
    "Unnecessary complexity",
    "Naming inconsistency",
    "Folder organization",
    "Missing tracking",
    "Wrong trigger timing",
    "Over-firing",
    "Under-firing",
    "Duplicate firing",
    "Wrong product, market, or page scope",
    "Incomplete payload",
    "Wrong data format",
    "Wrong value or formula logic",
    "Obsolete or legacy setup",
    "Unclear business purpose",
    "Consent mismatch",
    "Server-side routing unclear",
    "Custom code risk",
    "Performance overhead",
    "Naming or ownership unclear",
    "Generic hygiene batch",
}


def taxonomy_errors(area: Any, problem_type: Any, label: str) -> list[str]:
    errors: list[str] = []
    if str(area or "") not in AREAS:
        errors.append(f"{label}: unsupported human area {area!r}")
    if str(problem_type or "") not in PROBLEM_TYPES:
        errors.append(f"{label}: unsupported human problem type {problem_type!r}")
    return errors
