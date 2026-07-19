#!/usr/bin/env python3
"""Run the maintained GTM skill regression and repository checks."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run(root: Path, name: str, command: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "name": name,
        "status": "pass" if result.returncode == 0 else "fail",
        "return_code": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--allow-untracked",
        action="store_true",
        help="Allow newly created referenced files during local development.",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    python = sys.executable
    release_command = [python, "-B", "scripts/check_release.py"]
    if args.allow_untracked:
        release_command.append("--allow-untracked")
    checks = [
        run(
            root,
            "unittest",
            [python, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
        ),
        run(root, "release_layout", release_command),
        run(
            root,
            "vendor_registry",
            [python, "-B", "scripts/gtm_vendor_registry.py", "--max-age-days", "365"],
        ),
    ]
    if importlib.util.find_spec("ruff") is not None:
        checks.append(
            run(root, "ruff", [python, "-m", "ruff", "check", "--no-cache", "scripts", "tests"])
        )
    report = {
        "kind": "gtm_skill_self_test",
        "status": "pass" if all(item["status"] == "pass" for item in checks) else "fail",
        "checks": checks,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
