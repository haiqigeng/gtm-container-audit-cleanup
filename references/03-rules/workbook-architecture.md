# Cleanup Workbook Architecture

The cleanup plan is a decision document for web analysts and marketing teams,
not a dump of agent internals.

## Canonical Tabs

| Tab | Visibility | Purpose |
| --- | --- | --- |
| `01 Summary` | Visible | Source, scope, counts, status, route, and next step. |
| `02 Cleanup Plan` | Visible | Concise actionable issues and proposed operations. |
| `03 Operational Review` | Hidden | Run 1 findings, evidence, disposition, action. |
| `04 Configuration Review` | Hidden | Run 2 object-level behavior, verdict, defects, and action. |
| `05 Architecture Review` | Hidden | Run 3 families, chains, comparisons, target state. |
| `06 Custom Code Review` | Hidden | Object-level code coverage, behavior, effects, findings, decision. |
| `07 Reconciled Operations` | Hidden | Exact structured mutation packets. |
| `08 Source & Gates` | Hidden | Source hash and completion statuses. |

Hidden tabs remain available by unhiding. Do not password-protect them.

## Limits

- maximum eight tabs;
- maximum six columns per tab;
- only Summary and Cleanup Plan visible;
- wrapped top-aligned text;
- stable column widths, capped at 92;
- content-aware row heights, capped at 120;
- filters and frozen header row;
- no exact duplicate columns;
- no raw full export or full source code in visible tabs.
- no silent truncation in visible or hidden tabs. Hidden proof that exceeds one
  cell is continued losslessly on adjacent rows; overlong visible prose fails
  the build and must be rewritten more concisely.

## Cleanup Plan Columns

1. ID
2. Status
3. Area / problem type
4. Affected object(s)
5. Problem / evidence
6. Action / priority / QA

Keep one row per distinct actionable issue. A summary row may precede detailed
rows only when visual hierarchy makes the relationship clear. Homogeneous exact
duplicates, unused objects, naming, or folder work may remain one batch row,
but every atomic operation ID, action, affected object, approval choice, and QA
must be explicit. The workbook gate requires every operation ID exactly once.

Show every proposed operation and every unresolved owner question with the
analyst's recommended action. Consolidate nonblocking container-evidence limits
into one visible scope-boundary row; preserve every per-object boundary and
exact next action in the hidden reviews and machine-readable package. Do not
turn out-of-scope runtime certification into hundreds of visible cleanup tasks.
The Summary must distinguish operations ready for scoped approval from the
specific objects still blocked by owner decisions, and must expose any action-
completeness failure.

Order visible rows by decision impact without changing operation IDs,
dependency-aware execution order, or hidden proof order. Lead with Critical and
High proposed actions and continue through lower-priority proposals before
unresolved owner/evidence decisions. For each action state
the root problem, measurement or operational impact, exact target state/action,
readiness, and QA. The Summary also counts retained/no-change decisions and
names a concise set of retained business families so the target architecture is
not described only through defects. It exposes measurement-family preservation,
the target-state architecture, and the container-only proof boundary.

## Wording

State the business or operational problem first, then enough technical detail to
debug it. Avoid internal terms such as run gate, source hash, candidate score,
branch ledger, or parser trace in visible rows. Avoid vague text such as
`review configuration`, `fix tracking`, or `custom code inspected`.

The visible plan and hidden proof must agree. The plan may consolidate wording,
but cannot blend unrelated problem types or hide a material object-level defect.
Hidden workbook proof uses one decision-oriented row per object, family,
comparison, and code object, with defects and unresolved contracts called out.
The machine-readable package remains the lossless source for every D3 check,
configuration branch, recursive trace/node, official contract, code line, and
member assessment. Do not duplicate that evidence into thousands of workbook
rows merely to prove it exists.

All cell content derived from container or analyst input must be literal text;
escape spreadsheet-formula prefixes. Privacy scanning covers hidden and visible
tabs by default.

## Separation From Change Log

Never add a change-log tab to the cleanup plan. The cleanup plan records proposed
work; the separate change log records executed/generated differences.

Validate with:

```powershell
python -B scripts/gtm_audit_gate_check.py cleanup_plan.xlsx --operations reconciled_operations.json --pretty
python -B scripts/gtm_privacy_scan.py cleanup_plan.xlsx
```
