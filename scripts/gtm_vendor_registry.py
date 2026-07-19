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
from functools import lru_cache
from pathlib import Path
from typing import Any

REGISTRY_PATH = (
    Path(__file__).resolve().parents[1] / "references" / "03-rules" / "vendor-registry.toml"
)
URL_CHECK_USER_AGENT = "Mozilla/5.0 (compatible; gtm-skill-doc-check/1.0)"


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


@lru_cache(maxsize=8)
def _compiled_vendors(path_text: str, modified_ns: int) -> tuple[dict[str, Any], ...]:
    del modified_ns
    path = Path(path_text)
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
    return tuple(vendors)


def compiled_vendors(path: Path = REGISTRY_PATH) -> tuple[dict[str, Any], ...]:
    resolved = path.resolve()
    return _compiled_vendors(str(resolved), resolved.stat().st_mtime_ns)


def detect_vendor_text(text: str) -> tuple[str, str]:
    entry = vendor_record(text)
    return str(entry.get("name", "Unclassified")), str(entry.get("category", "unclassified"))


def vendor_record(text: str) -> dict[str, Any]:
    entries = compiled_vendors()
    preferred_names: list[str] = []
    if re.search(r"\bUA-\d|universal analytics|\"type\"\s*:\s*\"ua\"", text, re.I):
        preferred_names.append("Universal Analytics (legacy)")
    elif re.search(r"\bAW-[A-Z0-9-]+|google ads|adwords|conversion linker", text, re.I):
        preferred_names.append("Google Ads")
    for preferred_name in preferred_names:
        for entry in entries:
            if entry.get("name") == preferred_name:
                return entry
    for entry in entries:
        if any(pattern.search(text) for pattern in entry["compiled_patterns"]):
            return entry
    return {"name": "Unclassified", "category": "unclassified", "official_docs": []}


def official_url_error(url: str, timeout: int = 12) -> str | None:
    """Return an error only when both lightweight HEAD and GET checks fail."""
    last_error = "unknown response"
    for method in ("HEAD", "GET"):
        headers = {"User-Agent": URL_CHECK_USER_AGENT}
        if method == "GET":
            headers["Range"] = "bytes=0-0"
        request = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status < 400:
                    return None
                last_error = f"HTTP {response.status}"
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            last_error = str(exc)
    return last_error


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
                url_error = official_url_error(url)
                if url_error:
                    warnings.append(f"{name}: official URL check failed: {url}: {url_error}")
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
