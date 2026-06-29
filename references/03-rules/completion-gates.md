# Completion Gates

Use this reference for every audit, cleanup plan, cleanup execution, importable
JSON artifact, final handoff, or change log. The gates are mandatory unless the
user explicitly limits scope; limited scope must follow
`limited-audit-protocol.md`.

## Contents

- Mandatory Workstreams
- Phase Model
- Definition Of Done
- Semantic Status Values
- Reconciliation Counts
- Final Coverage Check

## Mandatory Workstreams

Every deliverable must account for:

- scope and evidence freshness;
- full inventory for tags, triggers, variables, folders, templates, built-in
  variables, consent settings, and relevant workspaces/versions;
- dependency map, including firing/blocking triggers, trigger groups,
  setup/teardown tags, folders, custom templates, and custom HTML/JavaScript
  references;
- measurement diagnosis: business model, decision outcomes, conversion
  hierarchy, vendor/platform roles, and expected data contracts for meaningful
  object families;
- semantic validation status for every tag, trigger, variable, custom template,
  and meaningful object family;
- D1-D3 proof queue status for every tag, trigger, variable, custom template,
  and referenced configuration branch in full audits;
- semantic model coverage for meaningful conversion, media, ecommerce, lead,
  custom-code, server-side, and multi-market object families;
- semantic logic consistency for conversion, media, ecommerce, lead, shared
  variable, value/quantity, and custom-code logic;
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
- optimization pattern review across hygiene, structural, semantic, and
  strategic levels when cleanup or optimization is requested;
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
| Measurement diagnosis | Business model, decision outcome, conversion hierarchy, platform role, expected data contract, and intent blockers recorded for meaningful families. |
| Semantic validation | Purpose, expected behavior, evidence, risk, confidence, and semantic status assigned. |
| Cleanup decision | Keep/fix/consolidate/delete/defer/no-change decision recorded with route, aggressiveness options, dependencies, QA, and blocker where applicable. |
| Report reconciliation | Counts reconcile and the report/workbook contains required rows or explicit blockers. |

Do not collapse phases into one status. A workstream is `Done` only when every
required phase is `Done`, `Not applicable`, or `User-excluded`.

## Definition Of Done

- `Full inventory`: source counts reconcile to object rows, and every object has
  an ID/path and name or a documented missing identifier.
- `Dependency map`: every trigger, variable, folder, setup/teardown, template,
  and custom-code reference is mapped or explicitly blocked.
- `Measurement diagnosis`: every meaningful conversion, media, ecommerce, lead,
  server-side, custom-code, multi-market, gateway, or consolidation candidate has
  a business model or family context, decision outcome, conversion hierarchy,
  vendor/platform role, expected event/payload contract, and intent blocker when
  ambiguous. Cleanup operations are not ready when this diagnosis is missing.
- `Semantic validation`: every tag, trigger, variable, custom template, and
  meaningful family has purpose, expected behavior, evidence, risk, confidence,
  semantic status, and affected consumers. Custom code also requires role
  category, consent assumption, side effects, runtime risk, and export-level
  code/config inspection evidence. Required D1-D3 depth must be completed when
  the source evidence is available; only D4 runtime proof may remain deferred.
  D2/D3 summaries must follow `summary-quality.md`: literal behavior, actual
  source/input, logic/action, output or side effect, consumer/context, judgment,
  and cleanup implication. D3 is incomplete when it categorizes the object
  without stating exact behavior, such as `returns Date.now()` or `pushes
  e.data.payload to dataLayer`.
- `Recursive D3`: every tag field, trigger filter, variable reference, lookup
  input, custom-code variable reference, and template field needed to understand
  an object has been traced to its terminal source or to a D4-only runtime
  blocker. A row that stops at "uses variable X" is not complete. Sibling fields
  with identical or near-identical logic must be compared for semantic
  compatibility and surfaced as findings or documented exceptions.
- `Semantic model`: meaningful object families have inferred business
  objective, user action, event/context, GTM implementation, data source,
  payload contract, platform use, and evidence/blockers where applicable.
- `Semantic logic consistency`: formulas, source paths, output shapes, trigger
  contexts, and consumers have been checked for contradictions or explicitly
  marked incomplete. Runtime/business proof can be deferred only after D1-D3
  semantic logic was completed from available evidence.
- `Official documentation`: every meaningful vendor/event/CMP family has an
  official source checked or a documented failed official-source lookup.
- `Ecommerce/dataLayer`: every standard ecommerce event and frequently reused
  ecommerce variable has source path, expected output shape, consumer fields,
  and GA4/vendor contract status.
- `Cleanup plan`: every material family has operations, no-change evidence
  after semantic validation, `Not applicable`, `User-excluded`, or `Deferred`
  with D4/runtime/owner blocker. A plan cannot defer D1-D3 audit work itself as
  cleanup work; for example, "review custom code", "check variable config", or
  "validate trigger logic" is a failed semantic-validation phase unless the user
  explicitly asked for a pre-audit inventory only.
- `Optimization patterns`: exact duplicates, unused candidates, reusable
  trigger/variable opportunities, dynamic lookup/regex/helper opportunities,
  semantic consolidation, and strategic data-contract blockers were considered
  where applicable.
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
- `measurement_diagnosed`
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
- the D1-D3 proof queue is closed or explicitly marked incomplete before
  cleanup operations are compiled;
- the D1-D3 proof queue covers every tag, trigger, variable, custom template,
  and referenced configuration branch in full audits;
- every layer has changes, findings, or a documented reason for no change;
- no meaningful object family is inventory-only or dependency-only;
- no cleanup-ready claim exists for a meaningful family missing measurement
  diagnosis;
- no cleanup operation exists for a D3 object unless literal behavior and the
  full trigger/tag/variable/source/destination graph path are complete or
  explicitly blocked at D4 only;
- semantic model checks have been completed or deferred for conversion, media,
  ecommerce, lead, server-side, and complex consolidation candidates;
- Custom HTML, Custom JavaScript, and custom templates have object-level purpose,
  role category, consent assumption, side effects, consumers, risk, semantic
  status, cleanup decision, and blocker where applicable;
- active, referenced, risky, or cleanup-relevant custom-code rows show that
  exported code/config was inspected before delivery; missing runtime proof is
  allowed only as a runtime QA blocker before mutation;
- all tags, triggers, variables, and custom templates have Semantic Object
  Matrix rows with depth tier, trigger-context or consumer-context status,
  configuration/source logic status, consent/server status where applicable,
  evidence level, and semantic status;
- every row whose required depth includes D3 has D3 completion evidence:
  literal behavior, actual inputs, logic/action, output or side effect,
  consumer/context, analyst judgment, and cleanup implication;
- every D3 row that references another GTM object has a child trace or linked
  evidence row for that referenced object; stopping at the reference name fails
  the gate;
- sibling fields or sibling objects with identical/near-identical logic have
  been compared and either surfaced as a finding, marked as an explicit
  documented exception, or justified by official/business evidence;
- proof summaries do not rely on generic evidence signals such as `custom code
  inspected`, `configuration reviewed`, `external URL found`, `dataLayer push
  detected`, `no obvious browser side effect`, `see config`, or `see export`;
- no row counts as semantically validated when required D1-D3 work is missing;
  such rows are unresolved/incomplete, not deferred;
- plausible but unproven runtime assumptions are marked `Runtime QA required`
  or `Owner decision required`, not reported as confirmed issues or as clean
  without proof;
- official documentation was checked for each material vendor/event/CMP family;
- GA4/current Google vs UA exceptions are explicit;
- standard ecommerce variables and consumers were reviewed;
- names match actual logic and scope;
- value, quantity, item, lead, product, category, and media payload variables
  make logical sense for their names, source events, formulas, output types, and
  consumers, or are deferred with blockers;
- proposed/applied final names are unique within each layer;
- single-member trigger groups are flattened or route-limited with deletion
  instructions;
- cleanup did not stop at low-effort hygiene when structural, semantic, or
  strategic optimization evidence exists;
- rename/delete/update operations have dependency sweeps;
- generated importable JSON has no new missing references and no undocumented
  residual duplicate/unused/name/logic issues;
- same-container JSON respects import conflict constraints, folder dependencies,
  custom-template dependencies, and built-in variable preservation;
- change-log columns match `change-log-template.md` when a change log is produced.
- cleanup plan and change log rows use the same operation IDs and do not contain
  conflicting object, reason, impact, QA, or status information.
- cleanup plans and change logs expose decisions, impact, QA/debug steps,
  blockers, owners, and status, while raw D1-D3 proof, code bodies, parameter
  dumps, dependency graphs, hashes, validator traces, and normal no-action rows
  stay in backing proof tabs or technical appendices.
- compact cleanup plans preserve every actionable object-level anomaly. Family
  summary rows may be used, but each detailed object finding must appear
  directly beneath its family row or as its own row; do not merge away distinct
  object findings into a single vague category row.
- XLSX cleanup plans open on a compact human decision view by default: one
  executive decision summary tab and one cleanup action plan tab. Inventories,
  semantic matrices, custom-code proof, full rename maps, completion ledgers,
  and reconciliation tabs remain present but normally hidden with Excel
  `hidden` state when they are not part of the stakeholder decision flow.
- visible workbook columns do not repeat the same value or same decision across
  multiple columns unless the distinction is necessary for approval, debugging,
  assignment, QA, impact, or next action.
- cleanup operations do not use deferred-review placeholders as the main action,
  including `review custom code`, `perform line-level review`, `check variables`,
  or `validate trigger logic`.

If any check fails, do not present the deliverable as complete. Deliver
`Incomplete / blocked` with failed workstream, affected objects, missing phase,
blocker, risk, required evidence, and next action.
