from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tests.test_pipeline import (
    complete_architecture,
    complete_configuration,
    complete_operational,
    sample_export,
)

from gtm_architecture_review import validate_review as validate_architecture
from gtm_audit_package_build import build_package
from gtm_baseline_audit import audit_export
from gtm_configuration_facts import code_line_facts
from gtm_configuration_review import scaffold_review as scaffold_configuration
from gtm_configuration_review import validate_review as validate_configuration
from gtm_future_state_check import prior_finding_covers
from gtm_operation_compile import (
    decision_ledger,
    validate_cross_run_reconciliation,
    validate_mutation_conflicts,
)
from gtm_operational_review import validate_review as validate_operational
from gtm_relationships import relationship_candidates
from gtm_review_shards import merge_review, split_review
from gtm_three_run_gate import run_gate
from gtm_vendor_registry import vendor_records


class AdversarialAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.export = self.root / "container.json"
        self.export.write_text(json.dumps(sample_export()), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_json(self, name: str, payload: dict) -> Path:
        path = self.root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_fixture_manifest_covers_every_regression_family(self) -> None:
        manifest = json.loads(
            (Path(__file__).parent / "fixtures" / "analyst_cases.json").read_text(
                encoding="utf-8"
            )
        )
        case_ids = {row["id"] for row in manifest["cases"]}
        self.assertEqual(51, len(case_ids))
        self.assertIn("single_member_trigger_group", case_ids)
        self.assertIn("dynamic_ga4_purchase_contract", case_ids)
        self.assertIn("worsened_future_finding", case_ids)
        self.assertIn("ambiguous_source_identity", case_ids)
        self.assertIn("zone_and_google_tag_config_coverage", case_ids)
        self.assertIn("behavior_change_architecture_conflict", case_ids)
        self.assertIn("duplicate_reference_name_ambiguity", case_ids)
        self.assertIn("nested_control_shape_corruption", case_ids)
        self.assertIn("mixed_route_blocker_conservatism", case_ids)
        self.assertIn("zone_gtag_change_log", case_ids)
        self.assertIn("javascript_parser_fallback_visibility", case_ids)
        self.assertIn("mixed_vendor_unknown_host", case_ids)
        self.assertIn("export_metadata_duplicate_resilience", case_ids)
        self.assertIn("consent_control_evidence_boundaries", case_ids)
        self.assertIn("dependency_trace_cross_object_coverage", case_ids)
        self.assertIn("reachability_context_and_gateway_separation", case_ids)
        self.assertIn("architecture_verdict_coherence", case_ids)
        self.assertIn("transaction_id_contract_presence", case_ids)
        self.assertIn("custom_code_representation_safety", case_ids)
        self.assertIn("same_payload_different_route", case_ids)
        self.assertIn("same_contract_consent_collision", case_ids)
        self.assertIn("consumed_delete_remap_coverage", case_ids)
        self.assertIn("deterministic_configuration_contradiction", case_ids)
        self.assertIn("exact_parser_fallback_attestation", case_ids)
        self.assertIn("opaque_custom_template_boundary", case_ids)
        self.assertIn("browser_server_consent_dedup_family", case_ids)
        self.assertIn("unsafe_architecture_retention", case_ids)
        self.assertIn("visible_relationship_evidence_boundary", case_ids)
        self.assertIn("dependency_safe_remap_semantics", case_ids)
        self.assertIn("final_layer_name_uniqueness", case_ids)
        self.assertIn("configuration_obligation_identity_and_polarity", case_ids)
        self.assertIn("exact_once_configuration_rows", case_ids)
        self.assertIn("parser_segment_semantic_coverage", case_ids)
        self.assertIn("unknown_vendor_source_registry_boundary", case_ids)
        self.assertIn("destination_peer_inheritance_boundary", case_ids)
        self.assertIn("architecture_operation_candidate_binding", case_ids)
        self.assertIn("discovered_unsafe_policy_attribution", case_ids)
        self.assertIn("architecture_negative_runtime_claims", case_ids)

    def test_provided_context_is_reproducible_and_tamper_evident(self) -> None:
        context_path = self.write_json(
            "context-input.json",
            {
                "website_url": "https://example.test/",
                "business_model": "lead_generation",
                "cmp": ["OneTrust"],
            },
        )
        package = self.root / "package"
        build_package(self.export, package, pretty=True, context_path=context_path)
        packaged_review = json.loads(
            (package / "operational_review.json").read_text(encoding="utf-8")
        )
        completed = complete_operational(self.export)
        for field in (
            "shared_facts_sha256",
            "context_sha256",
            "audit_context",
            "inferred_context",
            "provided_context",
            "provided_context_fields",
            "unresolved_context_questions",
        ):
            completed[field] = copy.deepcopy(packaged_review[field])
        review_path = self.write_json("contextual-operational.json", completed)
        errors, _ = validate_operational(self.export, review_path)
        self.assertEqual([], errors)

        context = json.loads((package / "context.json").read_text(encoding="utf-8"))
        context["unresolved_questions"].append("Fabricated question")
        (package / "context.json").write_text(json.dumps(context), encoding="utf-8")
        report = run_gate(self.export, package, audit_only=True)
        self.assertEqual("fail", report["status"])
        self.assertTrue(any("context" in error for error in report["errors"]))

    def test_repeated_custom_code_lines_keep_distinct_source_identity(self) -> None:
        variable = {
            "variableId": "900",
            "name": "CJS - Nested closures",
            "type": "jsm",
            "parameter": [
                {
                    "key": "javascript",
                    "type": "TEMPLATE",
                    "value": "function() {\nif (true) {\nreturn 1;\n}\n}\n}",
                }
            ],
        }
        facts = code_line_facts("variable", variable)
        closing_hashes = [row["line_hash"] for row in facts if row["line_preview"] == "}"]
        self.assertEqual(3, len(closing_hashes))
        self.assertEqual(3, len(set(closing_hashes)))

    def test_dynamic_purchase_name_requires_ga4_ecommerce_contract(self) -> None:
        data = sample_export()
        data["containerVersion"]["variable"].append(
            {
                "variableId": "901",
                "name": "Const - Purchase",
                "type": "c",
                "parameter": [{"key": "value", "type": "TEMPLATE", "value": "purchase"}],
            }
        )
        data["containerVersion"]["tag"][0]["parameter"][0]["value"] = (
            "{{Const - Purchase}}"
        )
        export = self.write_json("dynamic-purchase.json", data)
        scaffold = scaffold_configuration(export)
        tag = next(row for row in scaffold["rows"] if row["object_key"] == "tag:1")
        topics = {row["topic"] for row in tag["required_contract_topics"]}
        self.assertIn("ecommerce_event_contract", topics)
        self.assertIn("transaction_value_currency_and_quantity", topics)

    def test_basic_and_semantic_overlap_scans_find_known_cases(self) -> None:
        findings = audit_export(self.export)["findings"]
        self.assertTrue(
            any(row.get("finding_type") == "single_member_trigger_group" for row in findings)
        )
        candidates = relationship_candidates(sample_export()["containerVersion"])
        funnel = next(
            row
            for row in candidates
            if set(row["candidate_object_names"])
            == {"Funnel question 1", "Funnel step impression Q1"}
        )
        self.assertIn("shared_business_scope", funnel["comparison_types"])

    def test_same_logic_for_different_consent_purposes_is_mandatory_comparison(self) -> None:
        data = sample_export()
        logic = {
            "type": "jsm",
            "parameter": [
                {
                    "key": "javascript",
                    "type": "TEMPLATE",
                    "value": "function() { return {{OneTrust Groups}}.indexOf('2') >= 0; }",
                }
            ],
        }
        data["containerVersion"]["variable"].extend(
            [
                {"variableId": "910", "name": "CJS - analytics_storage", **logic},
                {"variableId": "911", "name": "CJS - ad_storage", **logic},
            ]
        )
        candidates = relationship_candidates(data["containerVersion"])
        collision = next(
            row
            for row in candidates
            if "different_consent_purposes_same_logic" in row["comparison_types"]
        )
        self.assertEqual({"variable:910", "variable:911"}, set(collision["candidate_object_keys"]))

    def test_undeclared_exception_and_missing_d3_checks_are_rejected(self) -> None:
        operational = complete_operational(self.export)
        operational["findings"][0].update(
            {
                "disposition": "documented_exception",
                "rationale": "This source-specific configuration is intentionally retained by its owner.",
                "owner_question": "",
            }
        )
        errors, _ = validate_operational(
            self.export, self.write_json("bad-exception.json", operational)
        )
        self.assertTrue(any("known_owner_exceptions" in error for error in errors))

        configuration = complete_configuration(self.export)
        configuration["rows"][0]["logic_cross_checks"] = []
        errors, _ = validate_configuration(
            self.export, self.write_json("missing-d3.json", configuration)
        )
        self.assertTrue(any("D3 logic checks" in error for error in errors))

    def test_declared_owner_exception_is_accepted_only_with_its_locked_reason(self) -> None:
        baseline = complete_operational(self.export)
        finding = baseline["findings"][0]
        reason = "The measurement owner approved this retained legacy route until migration."
        context_path = self.write_json(
            "exception-context.json",
            {
                "known_owner_exceptions": [
                    {"finding_id": finding["finding_id"], "reason": reason}
                ]
            },
        )
        package = self.root / "exception-package"
        build_package(self.export, package, context_path=context_path)
        contextual = json.loads(
            (package / "operational_review.json").read_text(encoding="utf-8")
        )
        for field in (
            "shared_facts_sha256",
            "context_sha256",
            "audit_context",
            "inferred_context",
            "provided_context",
            "provided_context_fields",
            "unresolved_context_questions",
        ):
            baseline[field] = copy.deepcopy(contextual[field])
        baseline["findings"][0].update(
            {
                "disposition": "documented_exception",
                "rationale": (
                    f"{reason} The source evidence "
                    f"{' and '.join(finding['rationale_evidence_terms'][:2])} is retained."
                ),
                "owner_question": "",
            }
        )
        errors, _ = validate_operational(
            self.export, self.write_json("declared-exception.json", baseline)
        )
        self.assertEqual([], errors)

    def test_unknown_vendor_placeholder_documentation_is_rejected(self) -> None:
        data = sample_export()
        data["containerVersion"]["tag"].append(
            {
                "tagId": "920",
                "name": "Unknown partner loader",
                "type": "html",
                "parameter": [
                    {
                        "key": "html",
                        "type": "TEMPLATE",
                        "value": '<script src="https://unknown-cdn.example/widget.js"></script>',
                    }
                ],
                "firingTriggerId": ["10"],
            }
        )
        export = self.write_json("unknown-vendor-placeholder.json", data)
        review = complete_configuration(export)
        partner = next(row for row in review["rows"] if row["object_key"] == "tag:920")
        research_check = next(
            check
            for check, topic in zip(
                partner["contract_checks"],
                partner["required_contract_topics"],
                strict=True,
            )
            if topic.get("research_required")
        )
        research_check["source"] = "https://vendor.example.com/official/setup"
        errors, _ = validate_configuration(
            export, self.write_json("placeholder-contract.json", review)
        )
        self.assertTrue(any("placeholder" in error for error in errors))

        research_check["source"] = "https://metricsvendor.unrelated.org/official/setup"
        errors, _ = validate_configuration(
            export, self.write_json("spoofed-contract.json", review)
        )
        self.assertTrue(any("unregistered vendor source" in error for error in errors))

    def test_mixed_vendor_tag_keeps_every_vendor_and_unknown_host_obligation(self) -> None:
        data = sample_export()
        data["containerVersion"]["tag"][1]["tagManagerUrl"] = (
            "https://metadata.example/container/tag/2"
        )
        html_parameter = data["containerVersion"]["tag"][1]["parameter"][0]
        html_parameter["value"] = (
            "<script src='https://mystery.example/sdk.js'></script>"
            "<script>fbq('track', 'Purchase'); ttq.track('CompletePayment');</script>"
        )
        export = self.write_json("mixed-vendor.json", data)
        scaffold = scaffold_configuration(export)
        row = next(item for item in scaffold["rows"] if item["object_key"] == "tag:2")
        context_names = {item["vendor"] for item in row["vendor_contexts"]}
        self.assertTrue({"Meta", "TikTok"}.issubset(context_names))
        self.assertIn(
            "Unclassified external integration (mystery.example)", context_names
        )
        self.assertNotIn(
            "Unclassified external integration (metadata.example)", context_names
        )
        self.assertNotIn("metadata.example", scaffold["audit_context"]["external_hosts"])
        unknown_topics = [
            item
            for item in row["required_contract_topics"]
            if item["category"] == "unknown_vendor"
        ]
        self.assertTrue(unknown_topics)
        self.assertTrue(all(item["research_required"] for item in unknown_topics))
        self.assertEqual(
            {"Meta", "TikTok"},
            {item["name"] for item in vendor_records(html_parameter["value"])},
        )

    def test_exact_duplicate_cannot_be_silently_kept(self) -> None:
        architecture = complete_architecture(self.export)
        duplicate = next(
            row
            for row in architecture["comparisons"]
            if "exact_configuration" in row.get("comparison_types", [])
        )
        duplicate.update(
            {
                "relationship_verdict": "Intentional variant",
                "disposition": "keep",
                "owner_question": "",
            }
        )
        errors, _ = validate_architecture(
            self.export, self.write_json("silent-duplicate.json", architecture)
        )
        self.assertTrue(any("identical source configuration" in error for error in errors))

    def test_mutation_conflicts_cover_rename_overlap_and_allow_distinct_appends(self) -> None:
        rename = {
            "operation_key": "rename",
            "creations": [],
            "additions": [],
            "changes": [],
            "remaps": [],
            "renames": [{"object_key": "tag:1", "before": "A", "after": "B"}],
            "deletions": [],
        }
        name_change = {
            "operation_key": "change",
            "creations": [],
            "additions": [],
            "changes": [
                {"object_key": "tag:1", "json_path": "$.name", "before": "A", "after": "C"}
            ],
            "remaps": [],
            "renames": [],
            "deletions": [],
        }
        self.assertTrue(validate_mutation_conflicts([rename, name_change]))

        first = copy.deepcopy(rename)
        first.update(
            {
                "operation_key": "append-a",
                "renames": [],
                "additions": [
                    {
                        "object_key": "tag:1",
                        "json_path": "$.parameter",
                        "mode": "append",
                        "value": {"key": "a"},
                    }
                ],
            }
        )
        second = copy.deepcopy(first)
        second["operation_key"] = "append-b"
        second["additions"][0]["value"] = {"key": "b"}
        self.assertEqual([], validate_mutation_conflicts([first, second]))

        parent = copy.deepcopy(name_change)
        parent["operation_key"] = "parent-write"
        parent["changes"][0]["json_path"] = "$.parameter"
        child = copy.deepcopy(parent)
        child["operation_key"] = "child-write"
        child["changes"][0]["json_path"] = "$.parameter[0].value"
        self.assertTrue(validate_mutation_conflicts([parent, child]))

        duplicate_rename = copy.deepcopy(rename)
        duplicate_rename["operation_key"] = "rename-again"
        self.assertTrue(validate_mutation_conflicts([rename, duplicate_rename]))

        remap = copy.deepcopy(rename)
        remap.update(
            {
                "operation_key": "remap-a",
                "renames": [],
                "remaps": [
                    {
                        "from_object_key": "trigger:10",
                        "to_object_key": "trigger:11",
                        "consumer_object_keys": ["tag:1"],
                    }
                ],
            }
        )
        remap_again = copy.deepcopy(remap)
        remap_again["operation_key"] = "remap-b"
        self.assertTrue(validate_mutation_conflicts([remap, remap_again]))

    def test_keep_or_unresolved_architecture_blocks_single_destructive_mutation(self) -> None:
        architecture = {
            "comparisons": [
                {
                    "comparison_id": "REL-KEEP",
                    "candidate_object_keys": ["tag:1", "tag:2"],
                    "relationship_verdict": "Intentional variant",
                    "disposition": "keep",
                }
            ],
            "families": [],
        }
        operation = {
            "operation_key": "delete-one",
            "source_references": [],
            "source_runs": ["configuration_correctness"],
            "creations": [],
            "additions": [],
            "changes": [],
            "remaps": [],
            "renames": [],
            "deletions": [{"object_key": "tag:1"}],
        }
        errors = validate_cross_run_reconciliation(
            {"findings": []}, architecture, [operation]
        )
        self.assertTrue(any("says to keep" in error for error in errors))

    def test_architecture_keep_blocks_behavior_change_but_not_metadata_maintenance(self) -> None:
        architecture = {
            "comparisons": [],
            "families": [
                {
                    "family_id": "FAM-KEEP",
                    "chain_object_keys": ["tag:1", "trigger:10"],
                    "relationship_verdict": "Intentional variant",
                    "disposition": "keep",
                }
            ],
        }
        operation = {
            "operation_key": "change-event",
            "source_references": [],
            "source_runs": ["configuration_correctness"],
            "creations": [],
            "additions": [],
            "changes": [
                {
                    "object_key": "tag:1",
                    "json_path": "$.containerVersion.tag[0].parameter[0].value",
                    "before": "purchase",
                    "after": "generate_lead",
                }
            ],
            "remaps": [],
            "renames": [],
            "deletions": [],
        }
        errors = validate_cross_run_reconciliation(
            {"findings": []}, architecture, [operation]
        )
        self.assertTrue(any("changes behavior" in error for error in errors))

        uncovered_errors = validate_cross_run_reconciliation(
            {"findings": []}, {"comparisons": [], "families": []}, [operation]
        )
        self.assertTrue(
            any("without an aligned business-architecture" in error for error in uncovered_errors)
        )

        aligned = copy.deepcopy(operation)
        aligned["source_runs"].append("business_architecture")
        self.assertEqual(
            [],
            validate_cross_run_reconciliation(
                {"findings": []}, {"comparisons": [], "families": []}, [aligned]
            ),
        )

        metadata = copy.deepcopy(operation)
        metadata["operation_key"] = "update-notes"
        metadata["changes"][0].update(
            {
                "json_path": "$.containerVersion.tag[0].notes",
                "before": "old owner note",
                "after": "current owner note",
            }
        )
        metadata_errors = validate_cross_run_reconciliation(
            {"findings": []}, architecture, [metadata]
        )
        self.assertEqual([], metadata_errors)

        creation = copy.deepcopy(operation)
        creation["operation_key"] = "create-helper"
        creation["changes"] = []
        creation["creations"] = [
            {
                "layer": "variable",
                "object": {"variableId": "999", "name": "Constant - EUR", "type": "c"},
            }
        ]
        creation_errors = validate_cross_run_reconciliation(
            {"findings": []}, architecture, [creation]
        )
        self.assertTrue(any("without an aligned" in error for error in creation_errors))

    def test_future_state_does_not_hide_a_worsened_numeric_finding(self) -> None:
        before = {
            "module_name": "trigger_condition_lint",
            "finding_type": "excessive_conditions",
            "object_type": "trigger",
            "object_ids": ["10"],
            "deterministic_evidence": "Trigger has 5 conditions.",
        }
        after = {**before, "deterministic_evidence": "Trigger has 10 conditions."}
        improved = {**before, "deterministic_evidence": "Trigger has 3 conditions."}
        self.assertFalse(prior_finding_covers(before, after))
        self.assertTrue(prior_finding_covers(before, improved))

    def test_context_questions_are_visible_owner_decisions(self) -> None:
        operational = complete_operational(self.export)
        configuration = complete_configuration(self.export)
        architecture = complete_architecture(self.export)
        ledger = decision_ledger(operational, configuration, architecture)
        context_rows = [row for row in ledger if row["source_run"] == "audit_context"]
        self.assertEqual(
            len(operational["unresolved_context_questions"]), len(context_rows)
        )
        self.assertTrue(all(row["disposition"] == "owner_decision_needed" for row in context_rows))

    def test_large_code_object_is_split_below_the_obligation_limit(self) -> None:
        data = sample_export()
        body = "function() {\n" + "\n".join(
            f"var value{i} = {i};" for i in range(75)
        ) + "\nreturn value74;\n}"
        data["containerVersion"]["variable"].append(
            {
                "variableId": "999",
                "name": "CJS - Large deterministic fixture",
                "type": "jsm",
                "parameter": [{"key": "javascript", "type": "TEMPLATE", "value": body}],
            }
        )
        export = self.write_json("large-code.json", data)
        review = scaffold_configuration(export)
        review_path = self.write_json("large-review.json", review)
        shard_dir = self.root / "shards"
        manifest = split_review(
            review_path,
            shard_dir,
            max_items=20,
            max_obligations=10,
        )
        code_shards = [
            row
            for row in manifest["obligation_shards"]
            if row["object_key"] == "variable:999"
            and row["source_field"] == "code_line_facts"
        ]
        self.assertGreaterEqual(len(code_shards), 8)
        self.assertTrue(all(len(row["source_ids"]) <= 10 for row in code_shards))

    def test_shard_manifest_cannot_escape_its_directory(self) -> None:
        review = complete_operational(self.export)
        review_path = self.write_json("safe-review.json", review)
        shard_dir = self.root / "safe-shards"
        split_review(review_path, shard_dir, max_items=10)
        manifest_path = shard_dir / "shard_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["shards"][0]["filename"] = "../outside.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unsafe shard filename"):
            merge_review(review_path, shard_dir, self.root / "merged.json")


if __name__ == "__main__":
    unittest.main()
