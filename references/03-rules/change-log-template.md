# Change Log Template

Use this reference when producing a post-cleanup change log or a generated-JSON
review log.

## Contents

- Purpose
- Required Tabs
- Detailed Change Columns
- Coherence Rules
- Output Boundary

## Purpose

The cleanup plan is the decision source. The change log is the execution record.
Do not make the change log a second audit or a place for new analysis.

Produce a real change log only after direct GTM cleanup, importable JSON
generation, or another concrete cleanup execution has occurred. Before
execution, use `planned change preview`. When the user explicitly asks for a
test artifact "as if cleanup was done", label it `simulated post-cleanup change
log` and mark rows as simulated/not verified.

The change log should contain only what changed, why it changed, impact, QA,
owner/status, and rollback/evidence notes needed for review. It must be
granular enough for the user to understand every applied change without opening
GTM View Changes, while still avoiding raw JSON, code dumps, and proof matrices.

## Required Tabs

A real post-cleanup change log must have two user-facing tabs or sections:

1. `Change Log Summary`: compact counts, scope, execution route, validation
   status, unresolved blockers, QA status, rollback source, and next step.
2. `Change Log Details`: one row per modified object, field, dependency,
   trigger route, variable source, folder move, template/code update, deletion,
   creation, rename, documented exception, or route-limited no-op.

Do not deliver only grouped summaries after cleanup execution. A grouped
summary is acceptable only as the summary tab; the detail tab must list every
modification element per line.

## Detailed Change Columns

Use this detailed end-user schema by default for `Change Log Details`:

```text
Change ID
Operation ID
Layer
Object ID
Before name
After name
Action
Before state/value/dependency
After state/value/dependency
Why / linked finding
Impact
QA status
Rollback note
Status
```

Each row must describe the human-visible before/after behavior, name,
dependency, trigger routing, payload field, variable source, consent setting,
folder relationship, template state, or code behavior that actually changed.
Do not fill any row with generic text such as `updated`, `reviewed`, or
`see GTM`.

`Why / impact` must include the linked operation ID when available and explain
the business, measurement, consent, privacy, or maintainability consequence.

Use hidden proof tabs only for raw JSON, operation packets, validator evidence,
and source finding IDs. The detail change log itself is user-facing because it
is the review record of the executed cleanup.

Recommended action values:

- `Created`
- `Updated`
- `Renamed`
- `Paused`
- `Deleted`
- `Moved folder`
- `Dependency remapped`
- `Documented exception`
- `No-op / Route-limited`

## Coherence Rules

Before delivering both cleanup plan and change log:

- every change-log row maps to a cleanup operation ID, except explicit
  `No-op / Documented exception` rows;
- object IDs/names, before/after behavior, action, reason/decision, impact,
  QA, owner/blocker, and status do not contradict the cleanup plan;
- if semantic checks discover a bad setup after the plan was drafted, update the
  cleanup operation first, then mirror the executed/generated change in the
  change log;
- deferred semantic issues appear as deferred/blocker operations, not as changed
  rows;
- naming, JSON route, and rollback notes match the selected execution route.
- the row can be understood on its own by an analytics or business owner who
  has not opened GTM View Changes.

## Output Boundary

Do not expose raw JSON, full semantic matrices, raw code/config, validator
traces, scratch reasoning, or full dependency graphs in the change log. Put that
evidence in hidden proof tabs or technical appendices when needed.

The row should be understandable to a business or analytics owner without
reading proof tabs, while still linking to operation/finding IDs for expert
review.
