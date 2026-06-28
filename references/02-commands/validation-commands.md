# Validation Commands

Use this file to decide which local checks to run and when.

## Release And Repo Checks

Run before committing or releasing:

```powershell
python scripts/check_release.py --tag vYYYY.MM.DD
python scripts/check_release.py --tag vYYYY.MM.DD.N --release-notes release-notes.md
git diff --check
git status --short
```

If Python is unavailable, run the non-Python checks and state the Python blocker
in the release notes.

## GTM JSON Checks

Run when producing or validating importable JSON:

```powershell
python scripts/gtm_validate_artifact.py artifact.json --mode overwrite
python scripts/gtm_validate_artifact.py artifact.json --original original.json --mode same-container-view
python scripts/gtm_diff_operations.py original.json cleaned.json
```

## Workbook And Audit Gates

Run when delivering an XLSX audit or cleanup plan:

```powershell
python scripts/gtm_audit_gate_check.py --strict-evidence workbook.xlsx
python scripts/gtm_audit_package_check.py export.json workbook.xlsx
```

These gates should verify inventory, dependency mapping, measurement diagnosis,
semantic validation, custom-code review, and cleanup-decision coverage.

## Export Inspection

Use for scalable first-pass inventory and dependency facts:

```powershell
python scripts/gtm_export_inspect.py container.json
```

Script output is evidence input. It does not replace analyst judgment,
measurement diagnosis, or semantic validation.
