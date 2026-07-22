# Cleanup Workbook Architecture

The cleanup plan is a decision document for web analysts and marketing teams,
not a dump of agent internals.

## Canonical Tabs

| Tab | Visibility | Purpose |
| --- | --- | --- |
| `01 Summary` | Visible | Source, scope, counts, status, route, level, next step. |
| `02 Cleanup Plan` | Visible | Concise actionable issues and proposed operations. |
| `03 Operational Review` | Hidden | Run 1 findings, evidence, disposition, action. |
| `04 Configuration Review` | Hidden | Run 2 literal behavior, branches, traces, contracts, defects. |
| `05 Architecture Review` | Hidden | Run 3 families, chains, comparisons, target state. |
| `06 Custom Code Review` | Hidden | Code behavior, effects, health, findings, decision. |
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
2. Level
3. Area / problem type
4. Affected object(s)
5. Problem / evidence
6. Action / priority / QA

Keep one row per distinct actionable issue. A summary row may precede detailed
rows only when visual hierarchy makes the relationship clear. Homogeneous exact
duplicates, unused objects, naming, or folder work may remain one batch row.

Also show operations deferred by the selected aggressiveness, unresolved owner
questions, and container-evidence limits. The Summary status must reflect these
states and must not say `Ready for human approval` while an owner decision is
outstanding.

Order visible rows by decision impact without changing operation IDs,
dependency-aware execution order, or hidden proof order. Lead with Critical and
High proposed actions and continue through lower-priority proposals before
unresolved owner/evidence decisions and deferred work. For each action state
the root problem, measurement or operational impact, exact target state/action,
readiness, and QA. The Summary also counts retained/no-change decisions and
names a concise set of retained business families so the target architecture is
not described only through defects.

## Wording

State the business or operational problem first, then enough technical detail to
debug it. Avoid internal terms such as run gate, source hash, candidate score,
branch ledger, or parser trace in visible rows. Avoid vague text such as
`review configuration`, `fix tracking`, or `custom code inspected`.

The visible plan and hidden proof must agree. The plan may consolidate wording,
but cannot blend unrelated problem types or hide a material object-level defect.
Hidden proof uses separate rows for the object contract, each D3 cross-check,
each configuration branch, each recursive trace and node, each official
contract, each code behavior block/finding, and each architecture member or
comparison. Do not collapse these obligations into one repeated summary cell.

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
