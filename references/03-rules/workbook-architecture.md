# Workbook Architecture

Use this reference when producing XLSX cleanup plans, audit workbooks, change
logs with proof tabs, or any stakeholder-facing spreadsheet.

## Contents

- Audience Layers
- Default Visible Tabs
- Hidden Proof Tabs
- Column Discipline
- Validation

## Audience Layers

Treat workbook presentation as part of deliverable quality:

- `Visible decision layer`: what the user needs to approve, assign, debug, or QA.
- `Hidden proof layer`: inventories, semantic evidence, official docs maps,
  technical reconciliation, and validator evidence.
- `Traceability`: IDs that connect visible decisions to hidden proof.

Use normal Excel `hidden` sheets for proof tabs. Do not use `veryHidden` unless
the user explicitly asks for locked-down technical evidence. Do not delete proof
tabs merely to simplify the user view; validators and expert reviewers need
them.

## Default Visible Tabs

A normal cleanup-plan workbook should open on two visible tabs and should not
exceed 7-8 total tabs, hidden tabs included, unless the user requests a
technical appendix or the validator explicitly requires an expanded artifact.

- `01 Summary`: overall status, top risks, recommended
  route, cleanup level, safe-now work, blocked work, owner decisions, validation
  status, and next step.
- `02 Cleanup Plan`: one operational table that consolidates findings,
  roadmap, operations, deferred blockers, runtime QA, route, and naming into
  actionable rows.

Default `02 Cleanup Plan` columns:

- `ID`
- `Affected object(s)`
- `Issue / opportunity`
- `Recommended action`
- `QA / blocker`
- `Status`

Add extra visible tabs only when the user asks, the execution route needs a
separate working tracker, or merging unrelated audiences would make the visible
table harder to use.

## Hidden Proof Tabs

Recommended compact hidden/supporting tabs:

- `03 D3 Evidence`
- `04 Inventory & Dependencies`
- `05 Synergy & Consolidation`
- `06 QA & Blockers`
- `07 References & Validation`

Split these tabs only when the user asks for a technical workbook, a validator
requires the older schema, or a container is too large for readable compact
tabs. Even hidden tabs must remain human-readable when unhidden.

Hidden proof tabs must also be information-clean:

- remove duplicate columns when the schema allows it;
- if a validator requires both fields, make their content distinct;
- use observed-evidence columns for source/input/side effects;
- use judgment columns for expectation, decision, owner question, or QA impact;
- hide constant, blank, validator-only, or raw-proof columns when humans may
  unhide the sheet;
- keep required reconciliation fields even when counts/statuses naturally match,
  but hide duplicate proof columns and add a compact phase summary when useful.

## Column Discipline

Visible columns must earn their place for real human use. Keep a column visible
only when it supports approval, debugging, assignment, QA, impact understanding,
or next action.

Before delivery:

- scan visible and hidden tabs for exact duplicate column contents;
- merge columns that answer the same human question;
- hide or remove blank and constant columns unless a validator requires them;
- keep operation IDs and finding IDs visible when they trace to proof rows;
- keep raw code, raw template fields, hashes, full dependency graphs, and
  validator traces out of user-facing tabs.
- keep visible and hidden tabs around 5-6 useful columns by default. If more
  columns are required for a technical appendix, hide or move the appendix out
  of the main user-facing workbook.
- consolidate columns that answer the same question. For example, merge D3
  source, logic, output, consumer, and decision fields into `Literal behavior`,
  `Consumer / context`, `Analyst judgment`, `Cleanup implication`, and
  `Evidence / QA blocker`.

## Validation

For completed full-audit or cleanup-plan workbooks, run when Python is
available:

```powershell
python scripts/gtm_audit_gate_check.py --strict-evidence workbook.xlsx
python scripts/gtm_audit_package_check.py export.json workbook.xlsx
```

If either gate fails, label the deliverable `Incomplete / blocked` and list the
failed workstream, affected objects, blocker, risk, required evidence, and next
step.
