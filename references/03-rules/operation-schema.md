# Cleanup Operation Schema

Compile operations only from three validated reviews. Audit findings describe a
problem; operations describe an exact proposed mutation.

The packet carries the source, context, and shared-fact hashes. It also carries
a decision ledger covering every source obligation, execution phases, and
projected object counts by layer.

## Contents

- Dispositions and human fields
- Structured creations, additions, field changes, remaps, deletions, and renames
- Consolidation and challenge review
- Merge/conflict rules and aggressiveness

## Dispositions

Use one:

- `cleanup_operation`
- `keep`
- `documented_exception`
- `owner_decision_needed`
- `container_evidence_limit`
- `not_applicable`

Operational findings use `documented_exception` rather than `keep` so every
mechanical anomaly remains visible. For a nonzero deterministic operational
finding, only `cleanup_operation`, `owner_decision_needed`, or a
source-locked `documented_exception` is valid. Configuration and architecture
may use `container_evidence_limit` or `not_applicable` only where their own
validators and evidence boundary allow it.

## Required Human Fields

Each operation contains:

- unique `operation_key` and generated `operation_id`;
- title, area, and supported problem type;
- concrete problem and why it matters;
- expected clean state;
- exact proposed action;
- preconditions, QA steps, and rollback;
- priority, confidence, and execution readiness;
- source run(s), source review IDs, and evidence object keys;
- affected mutation objects.

Use the shared taxonomy in `scripts/gtm_taxonomy.py`. Do not combine unrelated
issues under `Generic hygiene batch` merely to reduce rows.

## Structured Mutations

### Field Change

```json
{
  "object_key": "tag:123",
  "json_path": "$.containerVersion.tag[4].parameter[2].value",
  "before": "{{Old Variable}}",
  "after": "{{Canonical Variable}}"
}
```

### Object Creation

```json
{
  "layer": "variable",
  "object": {
    "variableId": "99",
    "name": "Constant - Currency",
    "type": "c",
    "parameter": [{"type": "TEMPLATE", "key": "value", "value": "EUR"}]
  },
  "reason": "Create the missing source required by the approved target state."
}
```

The object must be complete and use an identity that does not already exist.

### Missing Field Or List Addition

```json
{
  "object_key": "tag:123",
  "json_path": "$.containerVersion.tag[4].parameter",
  "mode": "append",
  "value": {"type": "TEMPLATE", "key": "currency", "value": "{{Currency}}"},
  "reason": "Add the approved currency parameter to the existing event tag."
}
```

Use `set` for one missing object field, `append` for a list tail, and `insert`
with an exact index for a list position. Do not represent a missing field as a
change with a fabricated `before` value.

### Consumer Remap

```json
{
  "from_object_key": "trigger:10",
  "to_object_key": "trigger:20",
  "consumer_object_keys": ["tag:5", "tag:8"]
}
```

List the exact complete source-graph consumer set. A partial consumer move is a
field change, not a source-object remap. Variable remaps update `{{Name}}`; trigger
remaps update firing/blocking/group IDs; tag remaps update setup/teardown names;
folder remaps update parent IDs.

### Deletion

```json
{
  "object_key": "variable:21",
  "reason": "Duplicates variable 20 after all consumers are remapped."
}
```

### Rename

```json
{
  "object_key": "variable:20",
  "before": "Items",
  "after": "DLV - ecommerce.items"
}
```

Renames must remain unique within the GTM layer and update name-based references.

## Decision Ledger And Execution Order

The decision ledger contains one row for every operational finding,
configuration object, architecture family, and relationship comparison. Each
row states its originating review ID, disposition, and linked operation ID when
cleanup is selected. No source obligation may disappear during reconciliation.

Apply approved operations in dependency-safe phases: create objects; add missing
fields/list members; apply logic correction; remap consumers; flatten trigger
groups and sequencing; rename; delete; then readback validation. The simulated
packet records before/after/delta counts for tags, triggers, variables,
templates, folders, clients, transformations, and built-ins where applicable.

## Consolidation

Every consolidation identifies:

- `canonical_object_key`;
- why variants are equivalent at configuration and architecture level;
- every consumer remap;
- every non-canonical deletion;
- expected post-remap unused objects;
- QA and rollback.

An unused duplicate may require no remap, but still requires canonical selection
and deletion. Sanitation consolidation must align with an architecture operation.

## Challenge Review

High/Critical operations require source recheck, active/paused and scope check,
plausible alternative explanation, and confirmed/downgraded/rejected/blocked
verdict. This protects consent, revenue, paid-media, server-routing, and
multi-market changes from over-inference.

## Merge And Conflict Rules

- Reconcile operations when their complete structured mutations are identical,
  even if independent lenses use different wording or operation keys.
- Preserve every lens rationale and source reference in the reconciled packet.
- Reject one operation key reused for different structured mutations.
- Reject different targets for one field, rename, or remap source.
- Reject deleting an object that is changed elsewhere.
- Reject remapping to an object selected for deletion.
- Reject mutation of an unresolved or intentional-variant architecture comparison.

## Aggressiveness

Audit and plan contain all confirmed findings. Execution selection controls which
approved operations proceed:

Each operation declares its minimum safe level. A selected level below that
minimum moves the operation to `deferred_operations`; it remains visible in the
plan and is excluded from future-state execution.

- Conservative: broken references and very low-risk hygiene;
- Standard: clear duplicates, unused objects, groups, folders, and naming;
- Deep: behavior-preserving consolidation and logic corrections with strong evidence;
- Transformational: target-architecture redesign requiring explicit owner approval.

`Undecided` is valid only before route/aggressiveness approval.
