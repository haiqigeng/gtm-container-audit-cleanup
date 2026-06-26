# Completion Gates

Use this reference for every audit, cleanup plan, cleanup execution, importable
JSON artifact, final handoff, or change log. The gates are mandatory unless the
user explicitly limits scope; limited scope must follow
`limited-audit-protocol.md`.

## Mandatory Workstreams

Every deliverable must account for:

- scope and evidence freshness;
- full inventory for tags, triggers, variables, folders, templates, built-in
  variables, consent settings, and relevant workspaces/versions;
- dependency map, including firing/blocking triggers, trigger groups,
  setup/teardown tags, folders, custom templates, and custom HTML/JavaScript
  references;
- semantic validation status for every meaningful object family;
- Custom HTML, Custom JavaScript, and custom-template semantic review;
- official documentation map for GA4 and every meaningful vendor/event/CMP
  family;
- Google event classification, with ambiguous Google analytics/ecommerce
  objects treated as GA4/current Google tag unless proven UA;
- official GA4 and vendor dataLayer/event payload contracts;
- standard ecommerce variables and all consuming tags;
- missing standard events and dataLayer readiness blockers;
- naming convention and naming standardization;
- one-tag gateway and consolidation review;
- currently unused, consolidation-obsolete, and deferred objects;
- tag, trigger, variable, folder, template, consent, custom-code, payload, and
  naming cleanup decisions;
- mutation route, rollback source, import conflict strategy, and validation
  results when cleanup is requested;
- generated JSON self-QA when an importable container is produced;
- change log and deferred blocker summary when requested or applicable.

## Phase Model

Track each mandatory workstream through these phases:

| Phase | Definition |
| --- | --- |
| Inventory | Objects or evidence enumerated with IDs/names/counts. |
| Dependency map | Consumers, references, firing/blocking relationships, setup/teardown, folders, templates, and custom-code references mapped. |
| Semantic validation | Purpose, expected behavior, evidence, risk, confidence, and semantic status assigned. |
| Cleanup decision | Keep/fix/consolidate/delete/defer/no-change decision recorded with route, aggressiveness options, dependencies, QA, and blocker where applicable. |
| Report reconciliation | Counts reconcile and the report/workbook contains required rows or explicit blockers. |

Do not collapse phases into one status. A workstream is `Done` only when every
required phase is `Done`, `Not applicable`, or `User-excluded`.

## Definition Of Done

- `Full inventory`: source counts reconcile to object rows, and every object has
  an ID/path and name or a documented missing identifier.
- `Dependency map`: every relevant trigger, variable, folder, setup/teardown,
  template, and custom-code reference is mapped or explicitly blocked.
- `Semantic validation`: every meaningful object or family has purpose,
  expected behavior, evidence, risk, confidence, semantic status, and affected
  consumers. Custom code also requires role category, consent assumption, side
  effects, and runtime risk.
- `Official documentation`: every meaningful vendor/event/CMP family has an
  official source checked or a documented failed official-source lookup.
- `Ecommerce/dataLayer`: every standard ecommerce event and frequently reused
  ecommerce variable has source path, expected output shape, consumer fields,
  and GA4/vendor contract status.
- `Cleanup plan`: every material family has operations, no-change evidence
  after semantic validation, `Not applicable`, `User-excluded`, or `Deferred`
  with blocker.
- `Report reconciliation`: counts reconcile before final delivery.

Script output, code hashes, external URL extraction, duplicate grouping, and
dependency maps are evidence inputs. They do not satisfy semantic validation.

## Semantic Status Values

Use these values for meaningful objects and object families:

- `Keep`
- `Fix`
- `Consolidate`
- `Delete candidate`
- `More info needed`
- `Not applicable`

Do not use plain `Delete` unless deletion was explicitly approved and verified.

## Reconciliation Counts

For each meaningful object family, report:

- `total`
- `inventoried`
- `dependency_mapped`
- `semantically_validated`
- `cleanup_decided`
- `deferred`
- `not_applicable`
- `user_excluded`
- `unresolved`

The semantic coverage formula must reconcile:

```text
total = semantically_validated + deferred + not_applicable + user_excluded
```

Any nonzero `unresolved` count blocks a completed-audit or cleanup-ready claim.

Run `scripts/gtm_audit_gate_check.py` against the reconciliation CSV, JSON, or
XLSX whenever a workbook/report contains the reconciliation table. If it fails,
deliver `Incomplete / blocked` with the failed rows.

## Final Coverage Check

Before final delivery, verify:

- no mandatory workstream is blank or silently skipped;
- every layer has changes, findings, or a documented reason for no change;
- no meaningful object family is inventory-only or dependency-only;
- Custom HTML, Custom JavaScript, and custom templates have object-level purpose,
  role category, consent assumption, side effects, consumers, risk, semantic
  status, cleanup decision, and blocker where applicable;
- official documentation was checked for each material vendor/event/CMP family;
- GA4/current Google vs UA exceptions are explicit;
- standard ecommerce variables and consumers were reviewed;
- names match actual logic and scope;
- proposed/applied final names are unique within each layer;
- single-member trigger groups are flattened or route-limited with deletion
  instructions;
- rename/delete/update operations have dependency sweeps;
- generated importable JSON has no new missing references and no undocumented
  residual duplicate/unused/name/logic issues;
- same-container JSON respects import conflict constraints, folder dependencies,
  custom-template dependencies, and built-in variable preservation;
- change-log columns match `report-templates.md` when a change log is produced.

If any check fails, do not present the deliverable as complete. Deliver
`Incomplete / blocked` with failed workstream, affected objects, missing phase,
blocker, risk, required evidence, and next action.
