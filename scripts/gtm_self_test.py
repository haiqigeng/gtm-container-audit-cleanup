#!/usr/bin/env python3
"""Run synthetic regression checks for GTM cleanup helper scripts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def export(cv: dict) -> dict:
    return {"exportFormatVersion": 2, "exportTime": "2026-01-01 00:00:00", "containerVersion": cv}


def base_cv() -> dict:
    return {
        "accountId": "1",
        "containerId": "2",
        "containerVersionId": "0",
        "tag": [
            {
                "tagId": "1",
                "name": "Meta - PageView",
                "type": "cvt_2_10",
                "firingTriggerId": ["1"],
                "parentFolderId": "1",
                "parameter": [
                    {"type": "TEMPLATE", "key": "value", "value": "{{DLV - value}}"}
                ],
            }
        ],
        "trigger": [{"triggerId": "1", "name": "PV - All Pages", "type": "PAGEVIEW"}],
        "variable": [
            {
                "variableId": "1",
                "name": "DLV - value",
                "type": "v",
                "parameter": [{"type": "TEMPLATE", "key": "name", "value": "value"}],
            }
        ],
        "folder": [{"folderId": "1", "name": "Meta"}],
        "customTemplate": [{"templateId": "10", "name": "Meta Pixel", "templateData": "x"}],
        "builtInVariable": [{"name": "Page URL", "type": "PAGE_URL"}],
    }


def process_cv() -> dict:
    html = "<script>dataLayer.push({event:'bridge_event', value:'{{DLV - value}}'});</script>"
    cjs = "function() { return {{DLV - value}} || ''; }"
    bad_total_cjs = "function() { return Number({{DLV - product price 1}}) + Number({{DLV - product price 2}}); }"
    return {
        "accountId": "1",
        "containerId": "2",
        "containerVersionId": "0",
        "tag": [
            {
                "tagId": "1",
                "name": "Vendor - Event A",
                "type": "cvt_2_10",
                "firingTriggerId": ["1"],
                "parameter": [{"type": "TEMPLATE", "key": "value", "value": "{{DLV - value}}"}],
            },
            {
                "tagId": "2",
                "name": "Vendor - Event B",
                "type": "cvt_2_10",
                "firingTriggerId": ["2"],
                "parameter": [{"type": "TEMPLATE", "key": "value", "value": "{{DLV - value}}"}],
            },
            {
                "tagId": "3",
                "name": "HTML - Bridge 1",
                "type": "html",
                "firingTriggerId": ["1"],
                "parameter": [{"type": "TEMPLATE", "key": "html", "value": html}],
            },
            {
                "tagId": "4",
                "name": "HTML - Bridge 2",
                "type": "html",
                "firingTriggerId": ["1"],
                "parameter": [{"type": "TEMPLATE", "key": "html", "value": html}],
            },
            {
                "tagId": "5",
                "name": "GA4 - checkout_step_1 legacy",
                "type": "gaawe",
                "firingTriggerId": ["4"],
                "parameter": [
                    {"type": "TEMPLATE", "key": "eventName", "value": "checkout_step_1"},
                    {
                        "type": "TEMPLATE",
                        "key": "item_id",
                        "value": "{{DLV - UA fixed product ID}}",
                    },
                ],
            },
        ],
        "trigger": [
            {"triggerId": "1", "name": "PV - All Pages", "type": "PAGEVIEW"},
            {"triggerId": "2", "name": "PV - All Pages Copy", "type": "PAGEVIEW"},
            {
                "triggerId": "3",
                "name": "Group - Single",
                "type": "TRIGGER_GROUP",
                "parameter": [
                    {
                        "type": "LIST",
                        "key": "triggerIds",
                        "list": [{"type": "TEMPLATE", "value": "1"}],
                    }
                ],
            },
            {"triggerId": "4", "name": "CE - checkout_step_1", "type": "CUSTOM_EVENT"},
        ],
        "variable": [
            {
                "variableId": "1",
                "name": "DLV - value",
                "type": "v",
                "parameter": [{"type": "TEMPLATE", "key": "name", "value": "value"}],
            },
            {
                "variableId": "2",
                "name": "DLV - value copy",
                "type": "v",
                "parameter": [{"type": "TEMPLATE", "key": "name", "value": "value"}],
            },
            {
                "variableId": "3",
                "name": "CJS - value",
                "type": "jsm",
                "parameter": [{"type": "TEMPLATE", "key": "javascript", "value": cjs}],
            },
            {
                "variableId": "4",
                "name": "CJS - value copy",
                "type": "jsm",
                "parameter": [{"type": "TEMPLATE", "key": "javascript", "value": cjs}],
            },
            {
                "variableId": "5",
                "name": "DLV - UA fixed product ID",
                "type": "v",
                "parameter": [
                    {
                        "type": "TEMPLATE",
                        "key": "name",
                        "value": "ecommerce.checkout.products.0.id",
                    }
                ],
            },
            {
                "variableId": "6",
                "name": "DLV - product price 1",
                "type": "v",
                "parameter": [{"type": "TEMPLATE", "key": "name", "value": "ecommerce.checkout.products.0.price"}],
            },
            {
                "variableId": "7",
                "name": "DLV - product price 2",
                "type": "v",
                "parameter": [{"type": "TEMPLATE", "key": "name", "value": "ecommerce.checkout.products.1.price"}],
            },
            {
                "variableId": "8",
                "name": "CJS - total price bad fixed indexes",
                "type": "jsm",
                "parameter": [{"type": "TEMPLATE", "key": "javascript", "value": bad_total_cjs}],
            },
        ],
        "customTemplate": [{"templateId": "10", "name": "Vendor Template", "templateData": "x"}],
        "builtInVariable": [{"name": "Page URL", "type": "PAGE_URL"}],
    }


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        original = tmpdir / "original.json"
        valid = tmpdir / "valid.json"
        missing_builtins = tmpdir / "missing-builtins.json"
        renamed = tmpdir / "renamed.json"
        process_export = tmpdir / "process.json"
        baseline_json = tmpdir / "baseline.json"
        partial_resolution = tmpdir / "partial-resolution.json"
        full_resolution = tmpdir / "full-resolution.json"

        cv = base_cv()
        original.write_text(json.dumps(export(cv)), encoding="utf-8")
        valid.write_text(json.dumps(export(cv)), encoding="utf-8")

        bad_cv = json.loads(json.dumps(cv))
        bad_cv.pop("builtInVariable")
        missing_builtins.write_text(json.dumps(export(bad_cv)), encoding="utf-8")

        renamed_cv = json.loads(json.dumps(cv))
        renamed_cv["tag"][0]["name"] = "Meta - page_view"
        renamed.write_text(json.dumps(export(renamed_cv)), encoding="utf-8")
        process_export.write_text(json.dumps(export(process_cv())), encoding="utf-8")

        checks = [
            ("valid_view", run("gtm_validate_artifact.py", str(valid), "--original", str(original), "--mode", "same-container-view")),
            ("missing_builtins", run("gtm_validate_artifact.py", str(missing_builtins), "--original", str(original), "--mode", "same-container-view")),
            ("rename_churn", run("gtm_validate_artifact.py", str(renamed), "--original", str(original), "--mode", "same-container-view")),
            ("diff_ops", run("gtm_diff_operations.py", str(original), str(renamed))),
            ("source_model", run("gtm_source_model.py", str(process_export))),
            ("baseline_audit", run("gtm_baseline_audit.py", str(process_export))),
            ("custom_code_extract", run("gtm_custom_code_extract.py", str(process_export))),
            ("semantic_source_scan", run("gtm_semantic_source_scan.py", str(process_export))),
        ]

        failures = []
        for name, proc in checks:
            should_pass = name in {
                "valid_view",
                "diff_ops",
                "source_model",
                "baseline_audit",
                "custom_code_extract",
                "semantic_source_scan",
            }
            passed = proc.returncode == 0
            if passed != should_pass:
                failures.append(
                    {
                        "check": name,
                        "returncode": proc.returncode,
                        "stdout": proc.stdout,
                        "stderr": proc.stderr,
                    }
                )

        baseline_proc = dict(checks)["baseline_audit"]
        source_model_proc = dict(checks)["source_model"]
        custom_proc = dict(checks)["custom_code_extract"]
        semantic_proc = dict(checks)["semantic_source_scan"]
        if source_model_proc.returncode == 0:
            source_model = json.loads(source_model_proc.stdout)
            counts = source_model.get("counts", {})
            if (
                source_model.get("kind") != "gtm_source_model_navigation_map"
                or source_model.get("coverage_gate") != "pass"
                or counts.get("field_edges", 0) == 0
                or counts.get("trigger_edges", 0) == 0
                or not source_model.get("raw_evidence_must_be_rechecked_for_findings")
            ):
                failures.append(
                    {
                        "check": "source_model_expected_map",
                        "kind": source_model.get("kind"),
                        "coverage_gate": source_model.get("coverage_gate"),
                        "counts": counts,
                    }
                )
        if baseline_proc.returncode == 0:
            baseline = json.loads(baseline_proc.stdout)
            baseline_json.write_text(baseline_proc.stdout, encoding="utf-8")
            finding_types = {
                finding["finding_type"]
                for finding in baseline["findings"]
                if finding["finding_type"] != "zero_findings"
            }
            required_types = {
                "normalized_duplicate_tag_signature",
                "duplicate_configuration",
                "duplicate_variable_path",
                "duplicate_custom_code",
                "single_member_trigger_group",
                "outdated_ua_styled_setup_object",
            }
            missing_types = sorted(required_types - finding_types)
            if missing_types:
                failures.append(
                    {
                        "check": "baseline_expected_finding_types",
                        "missing": missing_types,
                        "finding_types": sorted(finding_types),
                    }
                )

            real_findings = [
                finding for finding in baseline["findings"]
                if finding["finding_type"] != "zero_findings"
            ]
            partial_resolution.write_text(
                json.dumps(
                    [
                        {
                            "finding_id": real_findings[0]["finding_id"],
                            "resolution_status": "cleanup_operation",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            full_resolution.write_text(
                json.dumps(
                    [
                        {
                            "finding_id": finding["finding_id"],
                            "resolution_status": "cleanup_operation",
                        }
                        for finding in real_findings
                    ]
                ),
                encoding="utf-8",
            )
            reconcile_partial = run(
                "gtm_findings_reconcile.py", str(baseline_json), str(partial_resolution)
            )
            reconcile_full = run(
                "gtm_findings_reconcile.py", str(baseline_json), str(full_resolution)
            )
            if reconcile_partial.returncode == 0:
                failures.append(
                    {
                        "check": "reconcile_partial_should_fail",
                        "stdout": reconcile_partial.stdout,
                        "stderr": reconcile_partial.stderr,
                    }
                )
            if reconcile_full.returncode != 0:
                failures.append(
                    {
                        "check": "reconcile_full_should_pass",
                        "stdout": reconcile_full.stdout,
                        "stderr": reconcile_full.stderr,
                    }
                )

        if custom_proc.returncode == 0:
            extracted = json.loads(custom_proc.stdout)
            rows = extracted.get("rows", [])
            if extracted.get("custom_code_count", 0) < 4 or not any(
                row.get("dataLayer_pushes_or_writes") for row in rows
            ) or not all("technical_code_health_status" in row for row in rows):
                failures.append(
                    {
                        "check": "custom_code_expected_extraction",
                        "custom_code_count": extracted.get("custom_code_count"),
                        "has_datalayer_push": any(
                            row.get("dataLayer_pushes_or_writes") for row in rows
                        ),
                        "has_technical_status": all(
                            "technical_code_health_status" in row for row in rows
                        ),
                    }
                )

        if semantic_proc.returncode == 0:
            semantic = json.loads(semantic_proc.stdout)
            topics = {row.get("semantic_scan_topic") for row in semantic.get("rows", [])}
            required_topics = {
                "legacy_universal_analytics_setup",
                "fixed_index_ecommerce_logic",
                "business_logic_sanity",
                "custom_code_semantic_review",
            }
            missing_topics = sorted(required_topics - topics)
            if missing_topics:
                failures.append(
                    {
                        "check": "semantic_source_scan_expected_topics",
                        "missing": missing_topics,
                        "topics": sorted(topic for topic in topics if topic),
                    }
                )

        if failures:
            print(json.dumps({"status": "fail", "failures": failures}, indent=2))
            return 1
        print(json.dumps({"status": "pass", "checks": [name for name, _ in checks]}, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
