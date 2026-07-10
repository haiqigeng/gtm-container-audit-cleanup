#!/usr/bin/env python3
"""Load and validate the versioned official vendor-documentation registry."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

REGISTRY_PATH = (
    Path(__file__).resolve().parents[1] / "references" / "03-rules" / "vendor-registry.toml"
)


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def compiled_vendors(path: Path = REGISTRY_PATH) -> list[dict[str, Any]]:
    vendors = []
    for entry in load_registry(path).get("vendors", []):
        vendors.append(
            {
                **entry,
                "compiled_patterns": [
                    re.compile(pattern, re.I) for pattern in entry.get("patterns", [])
                ],
            }
        )
    return vendors


def detect_vendor_text(text: str) -> tuple[str, str]:
    entry = vendor_record(text)
    return str(entry.get("name", "Unclassified")), str(entry.get("category", "unclassified"))


def vendor_record(text: str) -> dict[str, Any]:
    for entry in compiled_vendors():
        if any(pattern.search(text) for pattern in entry["compiled_patterns"]):
            return entry
    return {"name": "Unclassified", "category": "unclassified", "official_docs": []}


def validate_registry(
    path: Path, online: bool = False, max_age_days: int = 180
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    registry = load_registry(path)
    try:
        reviewed = date.fromisoformat(str(registry.get("reviewed_on") or ""))
        age = (date.today() - reviewed).days
        if age > max_age_days:
            warnings.append(f"registry review is {age} days old; refresh official sources")
    except ValueError:
        errors.append("reviewed_on must use YYYY-MM-DD")

    seen_names = set()
    for index, vendor in enumerate(registry.get("vendors", []), start=1):
        name = str(vendor.get("name") or "")
        if not name:
            errors.append(f"vendor {index}: missing name")
        if name in seen_names:
            errors.append(f"vendor {index}: duplicate name {name!r}")
        seen_names.add(name)
        if not vendor.get("patterns"):
            errors.append(f"vendor {name!r}: missing patterns")
        for pattern in vendor.get("patterns", []):
            try:
                re.compile(pattern, re.I)
            except re.error as exc:
                errors.append(f"vendor {name!r}: invalid pattern {pattern!r}: {exc}")
        docs = vendor.get("official_docs", [])
        if not docs:
            errors.append(f"vendor {name!r}: missing official_docs")
        if online:
            for url in docs:
                request = urllib.request.Request(
                    url, method="HEAD", headers={"User-Agent": "gtm-skill-doc-check/1.0"}
                )
                try:
                    with urllib.request.urlopen(request, timeout=12) as response:
                        if response.status >= 400:
                            warnings.append(
                                f"{name}: official URL returned {response.status}: {url}"
                            )
                except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                    warnings.append(f"{name}: official URL check failed: {url}: {exc}")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--online", action="store_true")
    parser.add_argument("--max-age-days", type=int, default=120)
    args = parser.parse_args()
    errors, warnings = validate_registry(args.registry, args.online, args.max_age_days)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "pass", "warnings": len(warnings)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
