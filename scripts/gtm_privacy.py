#!/usr/bin/env python3
"""Privacy helpers for generated GTM evidence and user-facing artifacts."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SENSITIVE_KEY_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|"
    r"authorization|email|phone|user[_-]?id|client[_-]?id)"
)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
WINDOWS_USER_PATH_RE = re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+")
POSIX_USER_PATH_RE = re.compile(r"(?i)(?:^|\s)/(?:home|Users)/[^/\s]+")


def sanitize_url(value: str) -> str:
    try:
        split = urlsplit(value)
    except ValueError:
        return "<invalid-url>"
    hostname = split.hostname or ""
    port = f":{split.port}" if split.port else ""
    netloc = hostname + port
    query = urlencode(
        [
            (key, "<redacted>" if SENSITIVE_KEY_RE.search(key) else "<value>")
            for key, _ in parse_qsl(split.query, keep_blank_values=True)
        ]
    )
    return urlunsplit((split.scheme, netloc, split.path, query, ""))


def redact_text(value: Any) -> str:
    text = str(value or "")
    text = EMAIL_RE.sub("<redacted-email>", text)
    text = WINDOWS_USER_PATH_RE.sub(r"C:\\Users\\<redacted>", text)
    text = POSIX_USER_PATH_RE.sub(" /home/<redacted>", text)
    text = re.sub(
        r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|authorization)"
        r"\s*[:=]\s*[^&\s,;]+",
        r"\1=<redacted>",
        text,
    )
    return text


def privacy_findings(value: Any) -> list[str]:
    text = str(value or "")
    findings = []
    if EMAIL_RE.search(text):
        findings.append("email_address")
    if WINDOWS_USER_PATH_RE.search(text) or POSIX_USER_PATH_RE.search(text):
        findings.append("local_user_path")
    if SENSITIVE_KEY_RE.search(text) and re.search(r"[:=]\s*[^&\s,;]+", text):
        findings.append("possible_secret_or_identifier")
    return sorted(set(findings))
