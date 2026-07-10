from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from check_release import check_repository_layout  # noqa: E402
from gtm_audit_gate_check import validate_rows, validate_strict_evidence  # noqa: E402
from gtm_audit_package_check import row_matches, validate_package  # noqa: E402
from gtm_baseline_audit import audit_export  # noqa: E402
from gtm_diff_operations import operations  # noqa: E402
from gtm_human_rows import build_rows  # noqa: E402
from gtm_lib import container_version  # noqa: E402
from gtm_operation_compile import compile_operations  # noqa: E402
from gtm_privacy import privacy_findings, redact_text, sanitize_url  # noqa: E402
from gtm_semantic_review import scaffold_review, validate_review  # noqa: E402
from gtm_semantic_source_scan import scan_export  # noqa: E402
from gtm_source_model import build_model  # noqa: E402
from gtm_validate_artifact import missing_references  # noqa: E402
from gtm_vendor_registry import load_registry, validate_registry  # noqa: E402
from gtm_workbook import expand_structured_rows, load_xlsx_workbook  # noqa: E402
from gtm_workbook_build import CANONICAL_SHEETS, build_workbook  # noqa: E402


def sample_export() -> dict:
    return {
        "exportFormatVersion": 2,
        "containerVersion": {
            "accountId": "100",
            "containerId": "200",
            "containerVersionId": "1",
            "container": {"publicId": "GTM-TEST", "usageContext": ["WEB"]},
            "tag": [
                {
                    "tagId": "1",
                    "name": "Meta - Purchase",
                    "type": "html",
                    "parameter": [
                        {
                            "type": "TEMPLATE",
                            "key": "html",
                            "value": "<script>\nvar items = {{DLV - Items}};\ndataLayer.push({event: 'purchase_ready'});\n</script>",
                        },
                        {
                            "type": "MAP",
                            "key": "payload",
                            "map": [
                                {
                                    "type": "TEMPLATE",
                                    "key": "currency",
                                    "value": "EUR",
                                }
                            ],
                        },
                    ],
                    "firingTriggerId": ["10", "2147479553"],
                }
            ],
            "trigger": [
                {
                    "triggerId": "10",
                    "name": "Purchase",
                    "type": "CUSTOM_EVENT",
                    "customEventFilter": [
                        {
                            "type": "EQUALS",
                            "parameter": [
                                {"type": "TEMPLATE", "key": "arg0", "value": "{{_event}}"},
                                {"type": "TEMPLATE", "key": "arg1", "value": "purchase"},
                            ],
                        }
                    ],
                }
            ],
            "variable": [
                {
                    "variableId": "20",
                    "name": "DLV - Items",
                    "type": "v",
                    "parameter": [
                        {"type": "INTEGER", "key": "dataLayerVersion", "value": "2"},
                        {"type": "TEMPLATE", "key": "name", "value": "ecommerce.items"},
                    ],
                },
                {
                    "variableId": "21",
                    "name": "CJS - Item Count",
                    "type": "jsm",
                    "parameter": [
                        {
                            "type": "TEMPLATE",
                            "key": "javascript",
                            "value": "function() {\n  var items = {{DLV - Items}} || [];\n  return items.length;\n}",
                        }
                    ],
                },
            ],
            "customTemplate": [
                {
                    "templateId": "30",
                    "name": "Custom Vendor Template",
                    "templateData": "const log = require('logToConsole');\nlog('template');",
                }
            ],
            "client": [
                {
                    "clientId": "40",
                    "name": "Server - GA4 Client",
                    "type": "gaawc",
                    "parameter": [
                        {"type": "BOOLEAN", "key": "activateDefaultPaths", "value": "true"}
                    ],
                }
            ],
            "transformation": [
                {
                    "transformationId": "50",
                    "name": "Server - Redact Email",
                    "type": "tf",
                    "parameter": [{"type": "TEMPLATE", "key": "field", "value": "user_data.email"}],
                }
            ],
            "builtInVariable": [{"name": "Page URL", "type": "PAGE_URL"}],
        },
    }


def complete_review(export_path: Path) -> dict:
    review = scaffold_review(export_path)
    for row in review["rows"]:
        name = row["object_name"] or row["object_key"]
        row.update(
            {
                "review_status": "complete",
                "depth_completed": "D1, D2, D3",
                "business_role": f"The {name} object supports the exported measurement routing shown here.",
                "expected_contract": f"The {name} configuration must preserve its documented input and consumer contract.",
                "official_doc_basis": (
                    row["official_doc_candidates"][0]
                    if row["official_doc_candidates"]
                    else "No external vendor contract applies to this local GTM helper."
                ),
                "actual_inputs_or_sources": f"The {name} object reads the exact exported fields and referenced variables listed in proof.",
                "literal_behavior": f"The {name} object evaluates its exported conditions and produces the configured result.",
                "output_or_side_effect": f"The {name} object returns or routes the specific output described by its exported configuration.",
                "consumer_context": (
                    f"The {name} result is consumed by "
                    + ", ".join(item["consumer_key"] for item in row["export_consumers"])
                    if row["export_consumers"]
                    else f"The {name} object has no export-visible consumer in this container."
                ),
                "analyst_judgment": f"The {name} source logic is internally coherent for this static export review.",
                "cleanup_implication": f"Keep the {name} behavior unchanged unless runtime evidence contradicts this exported contract.",
                "evidence_or_qa_blocker": f"The {name} source export proves static logic; runtime output still requires Preview verification.",
                "semantic_status": "Keep",
                "confidence": "High",
                "evidence_anchors": list(row["required_logic_anchors"]),
                "configuration_branch_reviews": [
                    {
                        "json_path": item["json_path"],
                        "value_hash": item["value_hash"],
                        "logic_role": "Metadata",
                        "interpretation": f"This {name} source leaf contributes to the exported object configuration.",
                    }
                    for item in row["required_branch_reviews"]
                ],
                "code_line_reviews": [
                    {
                        "line_number": item["line_number"],
                        "line_hash": item["line_hash"],
                        "interpretation": f"This {name} line performs one explicit step in the exported code path.",
                    }
                    for item in row["code_line_facts"]
                ],
                "consumer_evidence_keys": [
                    item["consumer_key"] for item in row["export_consumers"]
                ],
                "reference_traces": [
                    {
                        "reference": item["reference"],
                        "object_chain": item["required_object_keys"],
                        "evidence_anchors": item["required_evidence_anchors"],
                        "terminal_states": item["terminal_states"],
                        "terminal_source": f"The {item['reference']} chain terminates at its exported GTM source configuration.",
                    }
                    for item in row["reference_trace_requirements"]
                ],
            }
        )
        if row["sibling_comparison_required"]:
            row["sibling_comparison"] = (
                f"The sibling fields on {name} use distinct exported roles and compatible values."
            )
            row["sibling_evidence_anchors"] = row["required_logic_anchors"][:2]
    review["review_status"] = "complete"
    return review


class PipelineTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.export_path = self.root / "container.json"
        self.export_path.write_text(json.dumps(sample_export()), encoding="utf-8")

    def test_system_references_are_not_reported_missing(self) -> None:
        report = missing_references(container_version(sample_export()))
        self.assertEqual([], report["undefinedVariableReferences"])
        self.assertEqual([], report["missingTriggerReferences"])

    def test_same_name_different_id_does_not_count_as_covered(self) -> None:
        row = {"layer": "tag", "object_id": "1", "object_name": "Same Name"}
        self.assertTrue(row_matches(row, "tag", "1", "Same Name"))
        self.assertFalse(row_matches(row, "tag", "2", "Same Name"))

    def test_source_model_contains_nested_leaf_facts_and_server_objects(self) -> None:
        model = build_model(self.export_path)
        paths = {edge["json_path"] for edge in model["field_edges"]}
        self.assertTrue(any(".parameter[1].map[0].value" in path for path in paths))
        self.assertEqual(1, model["counts"]["clients"])
        self.assertEqual(1, model["counts"]["transformations"])

    def test_coverage_scan_rows_are_tasks_not_findings(self) -> None:
        scan = scan_export(self.export_path)
        self.assertEqual("gtm_semantic_coverage_tasks", scan["kind"])
        self.assertTrue(scan["rows"])
        self.assertTrue(all(row["record_kind"] == "coverage_task" for row in scan["rows"]))
        self.assertTrue(all(not row["operation_packet_required"] for row in scan["rows"]))

    def test_semantic_review_requires_every_branch_code_line_and_trace(self) -> None:
        review = complete_review(self.export_path)
        review_path = self.root / "review.json"
        review_path.write_text(json.dumps(review), encoding="utf-8")
        errors, _ = validate_review(self.export_path, review_path)
        self.assertEqual([], errors)

        review["rows"][0]["configuration_branch_reviews"].pop()
        review["rows"][0]["code_line_reviews"].pop()
        review_path.write_text(json.dumps(review), encoding="utf-8")
        errors, _ = validate_review(self.export_path, review_path)
        self.assertTrue(any("branch reviews" in error for error in errors))
        self.assertTrue(any("code-line reviews" in error for error in errors))

    def test_generic_d3_text_is_rejected(self) -> None:
        review = complete_review(self.export_path)
        review["rows"][0]["literal_behavior"] = "Custom code inspected"
        review_path = self.root / "generic.json"
        review_path.write_text(json.dumps(review), encoding="utf-8")
        errors, _ = validate_review(self.export_path, review_path)
        self.assertTrue(any("generic D3 wording" in error for error in errors))

    def test_change_log_is_field_level(self) -> None:
        before = container_version(sample_export())
        after = json.loads(json.dumps(before))
        after["tag"][0]["name"] = "Meta - Purchase - Web"
        after["tag"][0]["tagFiringOption"] = "ONCE_PER_EVENT"
        rows = operations(before, after, "Direct GTM workspace", "Standard")
        paths = {row["field_path"] for row in rows}
        self.assertIn("$.name", paths)
        self.assertIn("$.tagFiringOption", paths)
        self.assertEqual(2, len(rows))

    def test_privacy_helpers_redact_identity_and_url_values(self) -> None:
        email = "client" + "@" + "example.com"
        local_path = "C:" + "\\Users\\" + "ExampleUser\\Downloads"
        secret_label = "api" + "_key"
        text = f"{local_path} {email} {secret_label}=secret123"
        redacted = redact_text(text)
        self.assertNotIn("ExampleUser", redacted)
        self.assertNotIn(email, redacted)
        self.assertNotIn("secret123", redacted)
        authority = "user:pass" + "@" + "example.com"
        sanitized = sanitize_url(f"https://{authority}/p?email={email}&id=42#frag")
        self.assertNotIn("user", sanitized)
        self.assertNotIn(email, sanitized)
        self.assertEqual(
            ["email_address", "local_user_path", "possible_secret_or_identifier"],
            privacy_findings(text),
        )

    def test_vendor_registry_is_structurally_valid(self) -> None:
        registry = load_registry(ROOT / "references" / "03-rules" / "vendor-registry.toml")
        self.assertTrue(registry.get("vendors"))
        errors, warnings = validate_registry(
            ROOT / "references" / "03-rules" / "vendor-registry.toml",
            max_age_days=400,
        )
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_release_layout_allows_ignored_editable_install_metadata(self) -> None:
        layout = self.root / "release-layout"
        (layout / ".github" / "workflows").mkdir(parents=True)
        (layout / "gtm_container_audit_cleanup.egg-info").mkdir()
        (layout / "LICENSE").write_text("MIT", encoding="utf-8")
        (layout / ".github" / "workflows" / "ci.yml").write_text("name: test\n", encoding="utf-8")
        self.assertEqual([], check_repository_layout(layout))

    def test_workbook_has_canonical_tabs_and_six_column_proof_tables(self) -> None:
        review = complete_review(self.export_path)
        output = self.root / "plan.xlsx"
        manifest = {"status": "pass", "source_model_coverage_gate": "pass"}
        source = {"counts": {"tags": 1}, "unresolved_edges": {"variables": []}}
        baseline = {"findings": []}
        technical = {"rows": []}
        operations_payload = {
            "route": "Direct GTM workspace",
            "aggressiveness": "Standard",
            "operations": [],
        }
        human = {"rows": []}
        build_workbook(
            manifest,
            source,
            baseline,
            technical,
            review,
            operations_payload,
            human,
            output,
        )
        workbook = load_xlsx_workbook(output)
        self.assertEqual(list(CANONICAL_SHEETS), list(workbook))
        for name, rows in workbook.items():
            if rows:
                self.assertLessEqual(len(rows[0]), 6, name)
        semantic = expand_structured_rows(workbook["05 Semantic Object Matrix"])
        self.assertEqual(review["rows"][0]["object_key"], semantic[0]["object_key"])

    def test_complete_workbook_passes_source_and_strict_gates(self) -> None:
        baseline = audit_export(self.export_path)
        real_findings = [
            row for row in baseline["findings"] if row["finding_type"] != "zero_findings"
        ]
        review = complete_review(self.export_path)
        actionable = review["rows"][0]
        actionable.update(
            {
                "semantic_status": "Fix",
                "analyst_judgment": "The Meta Purchase setup is incorrect until its confirmed hygiene findings are resolved.",
                "cleanup_implication": "Fix the Meta Purchase setup by setting the specified configuration and preserving all mapped dependencies.",
                "source_finding_ids": [row["finding_id"] for row in real_findings],
                "area": "GTM hygiene",
                "problem_type": "Generic hygiene batch",
                "problem": "The deterministic baseline confirms cleanup work linked to this reviewed object graph.",
                "why_it_matters": "Leaving confirmed hygiene findings unresolved makes ownership and future GTM debugging less reliable.",
                "expected_clean_state": "The affected objects retain intended behavior with all confirmed hygiene findings resolved.",
                "exact_proposed_action": "Set the reviewed object graph to the baseline-defined clean state and preserve every dependency.",
                "preconditions": "Approve the Standard cleanup route in a dedicated GTM workspace.",
                "qa_steps": "Use GTM Preview to verify the purchase event, payload, consent state, and firing count.",
                "rollback": "Restore the original export in the dedicated workspace if any validation fails.",
                "blocker": "No export-level blocker remains; runtime QA is still required.",
                "priority": "P1 - High",
                "resolution_status": "cleanup_operation",
                "execution_readiness": "approval_required",
                "risk_class": "Medium",
            }
        )
        review_path = self.root / "review.json"
        review_path.write_text(json.dumps(review), encoding="utf-8")
        review_errors, _ = validate_review(self.export_path, review_path)
        self.assertEqual([], review_errors)

        technical = []
        for row in review["rows"]:
            if not row["code_line_facts"]:
                continue
            technical.append(
                {
                    "layer": row["layer"],
                    "object_id": row["object_id"],
                    "technical_action_candidate": "keep",
                    "technical_handoff_packet": "Preserve the reviewed code and verify its output in GTM Preview.",
                    "referenced_gtm_variables": row["referenced_variables"],
                    "technical_plain_language_summary": "The exported code has complete line-level semantic evidence in the review.",
                    "external_scripts_loaded": [],
                    "localStorage_use": [],
                    "sessionStorage_use": [],
                    "side_effects": [],
                    "javascript_parser": "test fixture",
                }
            )

        operation_payload, compile_errors = compile_operations(
            review,
            real_findings,
            technical,
            "Direct GTM workspace",
            "Standard",
        )
        self.assertEqual([], compile_errors)
        human_rows, human_errors = build_rows(operation_payload)
        self.assertEqual([], human_errors)

        manifest = {
            "status": "pass",
            "source_model_coverage_gate": "pass",
        }
        source = build_model(self.export_path)
        output = self.root / "complete-plan.xlsx"
        build_workbook(
            manifest,
            source,
            baseline,
            {"rows": technical},
            review,
            operation_payload,
            {"rows": human_rows},
            output,
        )

        package_errors, _ = validate_package(self.export_path, output, limited=False)
        self.assertEqual([], package_errors)
        workbook = load_xlsx_workbook(output)
        reconciliation = expand_structured_rows(workbook["03 Workstream Reconciliation"])
        reconciliation_errors, _ = validate_rows(reconciliation)
        self.assertEqual([], reconciliation_errors)
        strict_errors, _ = validate_strict_evidence(output, reconciliation)
        self.assertEqual([], strict_errors)


if __name__ == "__main__":
    unittest.main()
