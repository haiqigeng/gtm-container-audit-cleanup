# Validation Commands

Run commands from the repository root. Use Python 3.11 or newer.

## Contents

- Audit evidence and D1-D3 validation
- Operation compilation and cleanup workbook
- JSON and post-execution change logs
- Vendor, repository, and release checks

## Build Audit Evidence

```powershell
python -B scripts/gtm_audit_package_build.py container.json --out-dir audit-package --pretty
```

This creates the source model, deterministic baseline, semantic coverage tasks,
technical custom-code facts, semantic review scaffold, and manifest. Coverage
tasks are not findings.

For individual debugging:

```powershell
python -B scripts/gtm_source_model.py container.json --pretty
python -B scripts/gtm_baseline_audit.py container.json --pretty
python -B scripts/gtm_custom_code_extract.py container.json --pretty
python -B scripts/gtm_semantic_source_scan.py container.json --pretty
```

## Complete And Validate D1-D3

Complete every row in `audit-package/semantic_review.json`, including exact
configuration-branch, code-line, consumer, sibling, and recursive-reference
proof. Then run:

```powershell
python -B scripts/gtm_semantic_review.py validate container.json audit-package/semantic_review.json
```

To reuse only source-identical completed rows from an earlier review:

```powershell
python -B scripts/gtm_semantic_review.py scaffold container.json audit-package/semantic_review.json --reuse-review previous-review.json --pretty
```

## Compile Cleanup Operations

```powershell
python -B scripts/gtm_operation_compile.py container.json audit-package/semantic_review.json reconciled_operations.json --baseline audit-package/deterministic_findings.json --technical audit-package/technical_code_findings.json --route "Direct GTM workspace" --aggressiveness Standard --pretty
python -B scripts/gtm_findings_reconcile.py audit-package/deterministic_findings.json reconciled_operations.json --operation-packets --technical audit-package/technical_code_findings.json
```

Every deterministic finding must be resolved. Operations must use a valid
readiness, risk class, route, and cleanup level.

## Build And Validate Cleanup Plan

```powershell
python -B scripts/gtm_human_rows.py reconciled_operations.json human_rows.json --pretty
python -B scripts/gtm_workbook_build.py audit-package audit-package/semantic_review.json reconciled_operations.json human_rows.json cleanup_plan.xlsx
python -B scripts/gtm_audit_gate_check.py --strict-evidence cleanup_plan.xlsx
python -B scripts/gtm_audit_package_check.py container.json cleanup_plan.xlsx
python -B scripts/gtm_privacy_scan.py cleanup_plan.xlsx --all-sheets
```

Any failed gate makes the deliverable `Incomplete / blocked`.

## Validate JSON Artifacts

Choose the import route before generating JSON.

```powershell
python -B scripts/gtm_validate_artifact.py artifact.json --mode overwrite
python -B scripts/gtm_validate_artifact.py artifact.json --original original.json --mode same-container-view
```

Do not call an artifact import-ready when validation fails.

## Build A Post-Execution Change Log

Link executed differences to approved operation packets:

```powershell
python -B scripts/gtm_diff_operations.py original.json cleaned.json --operations reconciled_operations.json --execution-mode executed --json field_diff.json
python -B scripts/gtm_change_log_build.py field_diff.json change_log.xlsx
python -B scripts/gtm_privacy_scan.py change_log.xlsx --all-sheets
```

Without real execution, use `planned` mode and label the output planned or
simulated.

## Official Documentation Registry

```powershell
python -B scripts/gtm_vendor_registry.py
python -B scripts/gtm_vendor_registry.py --online
```

Use the online check when current vendor behavior materially affects a formal
audit and network access is available.

## Repository And Release Checks

```powershell
python -m ruff check --no-cache .
python -m unittest discover -s tests -v
python -B scripts/gtm_self_test.py
python -B scripts/gtm_vendor_registry.py
python -B scripts/check_release.py --tag vYYYY.MM.DD.N
python -B scripts/build_skill_package.py dist\gtm-cleanup-intelligence-vYYYY.MM.DD.N
git diff --check
git status --short
```
