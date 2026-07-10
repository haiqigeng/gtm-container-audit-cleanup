# Workbook Architecture

Use this reference for stakeholder-facing cleanup plans and change logs. The
canonical completion rules remain in `execution-contract.md`.

## Cleanup Plan Workbook

Use exactly these tabs by default:

| Tab | Visibility | Purpose |
| --- | --- | --- |
| `01 Summary` | Visible | Status, route, cleanup level, counts, blockers, validation, next step. |
| `02 Cleanup Plan` | Visible | Decisions requiring approval, assignment, or QA. |
| `03 Workstream Reconciliation` | Hidden | Source, review, decision, and unresolved counts by object family. |
| `04 Reconciled Operations` | Hidden | Complete operation packets behind visible rows. |
| `05 Semantic Object Matrix` | Hidden | Source-bound D1-D3 purpose, logic, consumers, judgment, and proof. |
| `06 Deterministic Baseline` | Hidden | Mechanical findings and zero-finding module evidence. |
| `07 Custom Code Review` | Hidden | Line-level behavior, side effects, technical facts, judgment, and QA. |
| `08 Source Model & QA` | Hidden | Source coverage, unresolved edges, and gate status. |

Use normal Excel `hidden`, not `veryHidden`. A reviewer must be able to unhide
proof without special tooling.

## Visible Cleanup Plan

Use no more than six columns:

1. `ID`
2. `Level`
3. `Area / problem type`
4. `Affected object(s)`
5. `Problem / evidence`
6. `Action / priority / QA`

Use one `Single` row per distinct semantic problem. A `Summary` row may
introduce adjacent `Detail` rows for a related family. Group exact duplicates,
unused objects, naming batches, or identical folder moves only when evidence,
action, QA, rollback, and dependency risk are the same.

Visible text must explain the concrete GTM problem in language a web analyst or
marketing owner can use. Avoid internal categories such as `semantic issue`,
`technical finding`, or `payload problem` without the actual behavior.

## Consolidated Proof Columns

Every tab should normally use six or fewer purposeful columns. Consolidate
related machine fields into structured cells rather than spreading one decision
across twenty columns. The canonical builder uses these proof groups:

- semantic: object identity; purpose and contract; configuration logic; output
  and consumers; judgment; proof and trace;
- operations: operation; objects and behavior; problem and impact; expected
  state and action; QA and rollback; governance;
- custom code: object; purpose; code behavior; side effects and output;
  judgment; context and QA;
- baseline: finding; objects; evidence; action; source; status.

Structured cells keep their JSON keys so validators can recover exact fields.
Do not repeat the same content in several groups. Raw code, complete exports,
secrets, local paths, and scratch reasoning do not belong in a workbook.

## Formatting

- Open on `01 Summary`.
- Freeze the header row and enable filters on every table.
- Wrap text and align it at the top.
- Use stable widths: compact IDs/statuses, wider problem/action/proof columns.
- Use a readable fixed row height that does not produce empty poster-sized rows.
- Keep all text selectable; do not use screenshots as tables.
- Preserve unique operation and object IDs for debugging.

## Separate Change Log

Create the change log only after execution or generated-artifact creation. It
is a separate workbook with:

- `01 Change Log Summary` visible;
- `02 Change Log Details` visible;
- `03 Field Diff Proof` hidden.

Use six detail columns: Change ID, Area/object, Change made, Before, After, and
Reason/QA/status. Every field or dependency change gets its own row and links
to an approved operation ID. Planned or simulated output must say so.

## Validation

```powershell
python -B scripts/gtm_audit_gate_check.py --strict-evidence cleanup_plan.xlsx
python -B scripts/gtm_audit_package_check.py container.json cleanup_plan.xlsx
python -B scripts/gtm_privacy_scan.py cleanup_plan.xlsx --all-sheets
```

Delivery fails when a tab exceeds eight columns without a documented technical
exception, source-bound proof cannot be recovered, visible rows lack operation
links, privacy scanning fails, or either audit gate fails.
