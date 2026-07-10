#!/usr/bin/env python3
"""Build the canonical eight-tab GTM cleanup-plan workbook."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

CANONICAL_SHEETS = (
    "01 Summary",
    "02 Cleanup Plan",
    "03 Workstream Reconciliation",
    "04 Reconciled Operations",
    "05 Semantic Object Matrix",
    "06 Deterministic Baseline",
    "07 Custom Code Review",
    "08 Source Model & QA",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def cell_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def packed(fields: dict[str, Any]) -> str:
    return json.dumps(fields, ensure_ascii=False, sort_keys=True)


def semantic_workbook_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packed_rows = []
    for row in rows:
        packed_rows.append(
            {
                "Object identity": packed(
                    {
                        key: row.get(key)
                        for key in (
                            "object_key",
                            "object_id",
                            "object_name",
                            "object_type",
                            "layer",
                            "config_hash",
                            "source_json_path",
                        )
                    }
                ),
                "Purpose & contract": packed(
                    {
                        key: row.get(key)
                        for key in ("business_role", "expected_contract", "official_doc_basis")
                    }
                ),
                "Configuration logic": packed(
                    {
                        key: row.get(key)
                        for key in (
                            "actual_inputs_or_sources",
                            "literal_behavior",
                            "configuration_branch_reviews",
                            "code_line_reviews",
                        )
                    }
                ),
                "Output & consumers": packed(
                    {
                        key: row.get(key)
                        for key in (
                            "output_or_side_effect",
                            "consumer_context",
                            "consumer_evidence_keys",
                        )
                    }
                ),
                "Judgment": packed(
                    {
                        key: row.get(key)
                        for key in (
                            "sibling_comparison",
                            "analyst_judgment",
                            "cleanup_implication",
                            "evidence_or_qa_blocker",
                            "semantic_status",
                            "confidence",
                        )
                    }
                ),
                "Proof & trace": packed(
                    {
                        key: row.get(key)
                        for key in (
                            "depth_required",
                            "depth_completed",
                            "evidence_anchors",
                            "sibling_evidence_anchors",
                            "reference_traces",
                        )
                    }
                ),
            }
        )
    return packed_rows


def reconciliation_rows(
    review_rows: list[dict[str, Any]], custom_count: int
) -> list[dict[str, Any]]:
    by_layer = Counter(str(row.get("layer") or "") for row in review_rows)
    status_by_layer: dict[str, Counter[str]] = {}
    for layer in by_layer:
        status_by_layer[layer] = Counter(
            str(row.get("semantic_status") or "")
            for row in review_rows
            if row.get("layer") == layer
        )

    rows = []
    labels = {
        "tag": "Tags",
        "trigger": "Triggers",
        "variable": "Variables",
        "customTemplate": "Custom templates",
        "client": "Server clients",
        "transformation": "Server transformations",
    }
    for layer, total in by_layer.items():
        statuses = status_by_layer[layer]
        deferred = statuses.get("More info needed", 0)
        not_applicable = statuses.get("Not applicable", 0)
        validated = total - deferred - not_applicable
        rows.append(
            {
                "Workstream": "D1-D3 semantic review",
                "Object family": labels.get(layer, layer),
                "Source count": total,
                "Review counts": packed(
                    {
                        "total_source_count": total,
                        "inventoried_count": total,
                        "dependency_mapped_count": total,
                        "measurement_diagnosed_count": total,
                        "semantically_validated_count": validated,
                    }
                ),
                "Decision counts": packed(
                    {
                        "cleanup_decision_count": total,
                        "deferred_count": deferred,
                        "not_applicable_count": not_applicable,
                        "user_excluded_count": 0,
                        "unresolved_count": 0,
                    }
                ),
                "Status": "Complete" if not deferred else "Blocked",
            }
        )
    if custom_count:
        rows.append(
            {
                "Workstream": "Custom code review",
                "Object family": "Custom code and templates",
                "Source count": custom_count,
                "Review counts": packed(
                    {
                        "total_source_count": custom_count,
                        "inventoried_count": custom_count,
                        "dependency_mapped_count": custom_count,
                        "measurement_diagnosed_count": custom_count,
                        "semantically_validated_count": custom_count,
                    }
                ),
                "Decision counts": packed(
                    {
                        "cleanup_decision_count": custom_count,
                        "deferred_count": 0,
                        "not_applicable_count": 0,
                        "user_excluded_count": 0,
                        "unresolved_count": 0,
                    }
                ),
                "Status": "Complete",
            }
        )
    return rows


def custom_review_rows(
    review_rows: list[dict[str, Any]], technical_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    technical_by_key = {f"{row.get('layer')}:{row.get('object_id')}": row for row in technical_rows}
    rows = []
    for review in review_rows:
        key = str(review.get("object_key") or "")
        technical = technical_by_key.get(key)
        if not technical:
            continue
        effect_parts = []
        for field in (
            "external_scripts_loaded",
            "localStorage_use",
            "sessionStorage_use",
            "side_effects",
        ):
            values = technical.get(field)
            if values:
                effect_parts.append(f"{field}: {cell_value(values)}")
        rows.append(
            {
                "Object": packed(
                    {
                        "layer": review.get("layer"),
                        "object_id": review.get("object_id"),
                        "object_name": review.get("object_name"),
                        "type": review.get("object_type"),
                    }
                ),
                "Purpose": packed(
                    {
                        "role_category": review.get("business_role"),
                        "purpose": review.get("literal_behavior"),
                        "export_review_completed": "Yes",
                    }
                ),
                "Code behavior": packed(
                    {
                        "code_line_reviews": review.get("code_line_reviews"),
                        "variable_references": technical.get("referenced_gtm_variables", []),
                        "javascript_parser": technical.get("javascript_parser"),
                        "ast_summary": {
                            "calls": technical.get("ast_calls", []),
                            "branches": technical.get("ast_branch_count", 0),
                            "returns": technical.get("ast_return_count", 0),
                            "errors": technical.get("ast_parse_errors", []),
                        },
                    }
                ),
                "Side effects & output": packed(
                    {
                        "external_urls_storage_cookie_dom_datalayer_side_effects": "; ".join(
                            effect_parts
                        )
                        or "The extractor found no matching side-effect signal; use the line review as the authority.",
                        "expected_output_or_side_effect": review.get("output_or_side_effect"),
                    }
                ),
                "Judgment": packed(
                    {
                        "runtime_risks": technical.get("technical_plain_language_summary"),
                        "semantic_status": review.get("semantic_status"),
                        "cleanup_recommendation": review.get("cleanup_implication"),
                    }
                ),
                "Context & QA": packed(
                    {
                        "trigger_or_consumer_context": review.get("consumer_context"),
                        "consent_assumption": review.get("evidence_or_qa_blocker"),
                        "qa_method": review.get("qa_steps"),
                        "blocker": review.get("blocker"),
                    }
                ),
            }
        )
    return rows


def operation_workbook_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "Operation": packed(
                {
                    key: row.get(key)
                    for key in (
                        "operation_id",
                        "operation_group",
                        "area",
                        "problem_type",
                        "source_lenses",
                        "source_finding_ids",
                    )
                }
            ),
            "Objects & behavior": packed(
                {
                    key: row.get(key)
                    for key in ("affected_objects", "object_identity", "current_behavior")
                }
            ),
            "Problem & impact": packed(
                {key: row.get(key) for key in ("problem", "why_it_matters")}
            ),
            "Expected state & action": packed(
                {
                    key: row.get(key)
                    for key in ("expected_clean_state", "exact_proposed_action", "preconditions")
                }
            ),
            "QA & rollback": packed(
                {
                    key: row.get(key)
                    for key in (
                        "qa_steps",
                        "rollback",
                        "blocker",
                        "technical_handoff_packet",
                    )
                }
            ),
            "Governance": packed(
                {
                    key: row.get(key)
                    for key in (
                        "confidence",
                        "priority",
                        "resolution_status",
                        "route",
                        "aggressiveness",
                        "execution_readiness",
                        "risk_class",
                    )
                }
            ),
        }
        for row in rows
    ]


def baseline_workbook_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "Finding": packed(
                {
                    key: row.get(key)
                    for key in ("finding_id", "finding_type", "module_name", "module_status")
                }
            ),
            "Objects": packed(
                {
                    key: row.get(key)
                    for key in ("object_type", "object_ids", "object_names", "objects_scanned")
                }
            ),
            "Evidence": packed(
                {key: row.get(key) for key in ("signature_key", "deterministic_evidence")}
            ),
            "Action": packed(
                {key: row.get(key) for key in ("default_action", "required_resolution")}
            ),
            "Source": packed(
                {key: row.get(key) for key in ("source_file", "source_sha256") if key in row}
            ),
            "Status": row.get("module_status"),
        }
        for row in rows
    ]


def source_qa_rows(source: dict[str, Any], manifest: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for key, value in (source.get("counts") or {}).items():
        rows.append({"Area": "Source model", "Check": key, "Result": str(value), "Status": "Info"})
    for key, values in (source.get("unresolved_edges") or {}).items():
        rows.append(
            {
                "Area": "Source model",
                "Check": key,
                "Result": cell_value(values),
                "Status": "Pass" if not values else "Blocked",
            }
        )
    rows.append(
        {
            "Area": "Audit package",
            "Check": "source_model_coverage_gate",
            "Result": str(manifest.get("source_model_coverage_gate") or ""),
            "Status": str(manifest.get("status") or ""),
        }
    )
    return rows


def add_table(sheet: Any, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill

    if columns is None:
        columns = list(rows[0]) if rows else ["Status"]
    for column_index, column in enumerate(columns, start=1):
        cell = sheet.cell(row=1, column=column_index, value=column)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="244A5A")
        cell.alignment = Alignment(vertical="top", wrap_text=True)
    for row_index, row in enumerate(rows, start=2):
        for column_index, column in enumerate(columns, start=1):
            cell = sheet.cell(
                row=row_index, column=column_index, value=cell_value(row.get(column, ""))
            )
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        sheet.row_dimensions[row_index].height = 54
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for index, column in enumerate(columns, start=1):
        header = column.lower()
        if header in {"id", "level", "object_id", "layer", "confidence", "status"}:
            width = 16
        elif "problem" in header or "action" in header or "behavior" in header:
            width = 58
        elif "evidence" in header or "trace" in header or "anchor" in header:
            width = 48
        else:
            width = 32
        sheet.column_dimensions[sheet.cell(1, index).column_letter].width = width


def build_workbook(
    manifest: dict[str, Any],
    source: dict[str, Any],
    baseline: dict[str, Any],
    technical: dict[str, Any],
    review: dict[str, Any],
    operations: dict[str, Any],
    human_rows: dict[str, Any],
    output: Path,
) -> None:
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RuntimeError("openpyxl is required to build XLSX output") from exc

    workbook = Workbook()
    workbook.remove(workbook.active)
    sheets = {name: workbook.create_sheet(name) for name in CANONICAL_SHEETS}

    operation_rows = as_list(operations.get("operations"))
    review_rows = as_list(review.get("rows"))
    technical_rows = as_list(technical.get("rows"))
    custom_rows = custom_review_rows(review_rows, technical_rows)
    blocked = sum(
        1
        for row in operation_rows
        if row.get("execution_readiness") in {"d4_required", "owner_blocked"}
    )
    safe_now = sum(1 for row in operation_rows if row.get("execution_readiness") == "safe_now")
    summary = [
        {
            "Decision": "Overall status",
            "Value": "Ready for review" if not blocked else "Review with blockers",
        },
        {"Decision": "Source", "Value": review.get("source_file")},
        {"Decision": "Proposed operations", "Value": len(operation_rows)},
        {"Decision": "Safe now", "Value": safe_now},
        {"Decision": "Blocked or D4-dependent", "Value": blocked},
        {"Decision": "Execution route", "Value": operations.get("route")},
        {"Decision": "Cleanup level", "Value": operations.get("aggressiveness")},
        {"Decision": "Validation", "Value": "Run both workbook gates before delivery"},
        {
            "Decision": "Next step",
            "Value": "Approve operations, resolve blockers, then execute in a dedicated GTM workspace or approved JSON route.",
        },
    ]
    add_table(sheets["01 Summary"], summary, ["Decision", "Value"])
    sheets["01 Summary"].column_dimensions["A"].width = 30
    sheets["01 Summary"].column_dimensions["B"].width = 90
    add_table(sheets["02 Cleanup Plan"], as_list(human_rows.get("rows")))
    add_table(
        sheets["03 Workstream Reconciliation"],
        reconciliation_rows(review_rows, len(custom_rows)),
    )
    add_table(sheets["04 Reconciled Operations"], operation_workbook_rows(operation_rows))
    add_table(sheets["05 Semantic Object Matrix"], semantic_workbook_rows(review_rows))
    add_table(
        sheets["06 Deterministic Baseline"],
        baseline_workbook_rows(as_list(baseline.get("findings"))),
    )
    add_table(sheets["07 Custom Code Review"], custom_rows)
    add_table(sheets["08 Source Model & QA"], source_qa_rows(source, manifest))

    for name in CANONICAL_SHEETS[2:]:
        sheets[name].sheet_state = "hidden"
    workbook.active = 0
    output.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("semantic_review", type=Path)
    parser.add_argument("operations", type=Path)
    parser.add_argument("human_rows", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    build_workbook(
        load_json(args.package_dir / "audit_package_manifest.json"),
        load_json(args.package_dir / "source_model.json"),
        load_json(args.package_dir / "deterministic_findings.json"),
        load_json(args.package_dir / "technical_code_findings.json"),
        load_json(args.semantic_review),
        load_json(args.operations),
        load_json(args.human_rows),
        args.output,
    )
    print(json.dumps({"output": str(args.output), "tabs": list(CANONICAL_SHEETS)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
