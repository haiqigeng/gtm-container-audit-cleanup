# Semantic Object Matrix

Use this reference after inventory and dependency mapping. It turns semantic
review into a scalable gate: every meaningful object is classified, high-impact
objects are traced deeply, and the stakeholder report shows decisions instead of
raw GTM configuration dumps.

## Contents

- Principle
- Depth Tiers
- Required Depth Rule
- D1-D3 Proof Queue
- D1-D3 Proof Contract
- Required Matrix Columns
- Execution Guarantee
- Status Vocabulary
- Reporting Rule
- Completion Gate

## Principle

Do not audit by copying tag parameters. Audit whether configuration expresses
the intended measurement logic.

For template tags, inspect meaningful fields, trigger context, variable sources,
consent/server routing, and official/vendor contract. Infer the likely outgoing
behavior and judge whether it fits the event name and business role.

For custom HTML or Custom JavaScript, first understand code inputs, logic,
outputs, and side effects. Then judge it by the same semantic chain as a
template object.

The semantic chain is:

```text
business intent -> decision outcome -> platform role -> trigger context
-> configuration/code logic -> inferred output or side effect
-> destination/platform expectation -> correctness decision
```

## Depth Tiers

Assign the minimum depth needed for each object or object family.

| Tier | Use for | Required work |
| --- | --- | --- |
| D1 Classification | Low-risk helpers, folders, obvious constants, low-risk unused objects. | Identify role, family, consumers, and semantic status. |
| D2 Configuration logic | Active template tags, triggers, DLVs, lookup/regex tables, standard variables. | Check event name, trigger context, meaningful fields, variable paths, output type, and consumer expectation. |
| D3 Source/code logic | Consent, conversion, ecommerce, lead, media, identity, server-side, pageview, ad revenue, and any risky/shared/custom-code object. | Inspect source DLV path, formula, lookup, custom JS, custom HTML, storage/cookie/DOM/network side effects, and type compatibility. |
| D4 Runtime proof | Async pages, SPA/infinite scroll, DOM scraping, CMP timing, server routing, ad slots, vendor acceptance, and any context not provable from export/API. | Define exact Tag Assistant, browser/network, vendor-platform, or owner evidence required. |

Depth is cumulative. A D3 object must also satisfy D1 and D2.

## Required Depth Rule

Required depth is an execution requirement. If an object requires D1, D2, or D3
and the export, API, custom template configuration, or supplied evidence contains
the needed information, complete that depth during the audit. Do not report it
as required-but-not-done.

Only D4 runtime proof may be deferred. D4 covers behavior that cannot be proven
from export/API evidence, such as browser timing, DOM availability, CMP order,
ad-slot rendering, server-container routing, or vendor-platform acceptance.

If D3 is required, `depth_completed` must say that D3 was completed and the row
must prove it with source/code evidence. Phrases such as `D3/D4 blocked`,
`static scan only`, `review later`, `full code walkthrough required`, or
`D3 required` do not count as D3 completion. If D3 cannot be done because the
source/config is genuinely unavailable, mark the workstream `Incomplete /
blocked` and identify the missing source. In a normal GTM export, Custom HTML,
Custom JavaScript, DLV paths, lookup/regex tables, trigger filters, and tag
parameters are scannable.

## D1-D3 Proof Queue

Before writing findings, operations, cleanup plans, or change logs, build an
internal queue of every object or object family that requires D1, D2, or D3.
The queue must include object ID/name, layer, required depth, reason for depth,
consumer count or family coverage, and queue status.

Do not compile cleanup operations for a meaningful object while its D1-D3 queue
row is unresolved. Queue rows may be closed only as:

- `Complete`: D1-D3 evidence is recorded in the matrix or custom-code review.
- `Not applicable`: the object is outside the business/scope and documented.
- `User-excluded`: the user explicitly limited the scope.
- `Incomplete / blocked`: source evidence is missing or unreadable.

D4 runtime uncertainty is not a D1-D3 blocker. If runtime proof is needed, first
complete D1-D3 from export/API/config/code evidence, then mark only the runtime
proof as required.

## D1-D3 Proof Contract

D1-D3 proof must be evidence-first. Do not start D3 by categorizing the object.
Start by stating the exact literal behavior visible in the export, API,
template parameters, trigger filters, or custom code.

For D3, record this sequence:

```text
literal behavior -> actual inputs -> actual logic/action
-> actual output or side effect -> actual consumers and expected meaning
-> analyst judgment -> cleanup implication
```

Examples of acceptable literal behavior:

- `Returns Date.now(), a millisecond timestamp.`
- `Reads {{Click URL}} and extracts split('vertex_doc_id=')[1].split('&')[0].`
- `Listens to window message events and pushes e.data.payload to dataLayer when
  e.data.type equals cta_tracking.`
- `Loads https://sdk.mrf.io/statics/marfeel-sdk.js?id=2152 and sets
  window.marfeel.config.accountId to 2152.`
- `Injects CSS that changes .tp-modal and .tp-backdrop z-index values.`

Use categories only after literal behavior is stated. `Payload transformer`,
`vendor loader`, `computed value`, `browser side effect`, or `server enrichment`
are not D3 proof by themselves.

Use this contract by object type:

- **Template tag or variable**: record the concrete event name, trigger context,
  template fields, variable sources, outgoing value/behavior, destination field,
  official/vendor expectation, and judgment.
- **Custom HTML / Custom JavaScript**: record exact reads, conditions, function
  calls, returns, writes, pushes, loaded URLs, cookie/storage/DOM/network
  effects, consumers, expected consumer meaning, and judgment.
- **Trigger**: record the GTM event, exact filters, variables used in
  conditions, firing/blocking role, consuming tags, expected page/user-action
  context, and judgment.
- **Lookup / regex / table / formula helper**: record source key, mapping rows
  or formula, fallback behavior, output type, consumers, expected consumer
  meaning, and judgment.
- **Custom template**: record exposed fields, permissions, destination behavior,
  template consumers, risk/maintenance judgment, and whether official/vendor
  documentation supports the pattern.

Generic statements such as `custom code inspected`, `configuration reviewed`,
`returns computed value`, `browser side effect`, `according to configured type`,
`static scan completed`, or `no issue found` are not proof. A row may mention
that a scan happened, but it still needs literal behavior, consumers, judgment,
and cleanup implication.

## Required Matrix Columns

For full audits, create a `semantic_object_matrix` table or workbook tab. For
limited audits, create it for the sampled scope.

Minimum columns:

- `object_id`
- `object_name`
- `layer`
- `vendor_or_family`
- `inferred_business_role`
- `decision_outcome`
- `conversion_hierarchy`
- `platform_role`
- `expected_data_contract`
- `depth_required`
- `depth_completed`
- `trigger_context_status`
- `configuration_logic_status`
- `source_or_code_logic_status`
- `consent_or_server_status`
- `evidence_level`
- `semantic_status`
- `confidence`
- `finding_or_operation_id`
- `runtime_qa_required`
- `blocker_or_next_evidence`

For any row where `depth_required` includes `D3`, prefer compact columns:

- `literal_behavior`
- `consumer_context`
- `analyst_judgment`
- `cleanup_implication`
- `evidence_or_qa_blocker`

Legacy matrix columns such as `d3_inputs_or_sources`,
`d3_logic_summary`, `d3_output_or_side_effect`,
`d3_consumer_expectation`, and `d3_correctness_decision` may still be used by
older validators, but user-facing or expert-review workbooks should consolidate
them into the compact five-column format when possible.

Use short judgment values, not parameter dumps. Follow `summary-quality.md`:
each D2/D3 proof summary should state exact behavior, consumer context,
judgment, and cleanup implication. Put raw extracted parameters, code snippets,
or full payloads in separate technical artifacts only when truly needed.

## Execution Guarantee

The matrix is a completion artifact, not an optional appendix. An audit or
cleanup plan that claims complete semantic coverage must be able to point to a
matrix row or explicit workstream blocker for every meaningful object family.

For high-impact active objects, use object-level rows. High-impact includes
consent, GA4/current Google tags, ecommerce, conversion, lead, media, ad revenue,
server-side routing, identity, shared variables, custom code, and any tag whose
name implies a business outcome. Repeated low-risk helpers may use family rows,
but anomalies and cleanup candidates need object-level rows.

Do not count a row as complete when it only contains inventory facts such as
name, ID, type, hash, duplicate group, or connected trigger. A complete row must
contain a judgment about the semantic chain:

```text
business intent -> decision outcome -> platform role -> trigger context
-> configuration/code logic -> inferred output or side effect
-> destination/platform expectation -> correctness decision
```

The row is not cleanup-ready until `decision_outcome`, `conversion_hierarchy`,
`platform_role`, and `expected_data_contract` are filled or the row has an
explicit owner/runtime/server/dataLayer blocker.

For custom code, export-level inspection is mandatory before the row can be
called semantically reviewed. Record what the code reads, writes, calls, pushes,
loads, returns, or mutates. If runtime behavior cannot be proven, mark runtime
QA as required; do not use that as a reason to skip code inspection.

Generic evidence signals are not semantic summaries. Do not use phrases such as
`custom code inspected`, `configuration reviewed`, `external URL found`,
`dataLayer push detected`, `no obvious browser side effect`, `see config`, or
`see export` as the main D2/D3 proof. Replace them with the object's source,
logic, inferred output/side effect, consumer expectation, and correctness
decision.

## Status Vocabulary

Use these statuses consistently:

- `OK`: available evidence supports the semantic chain.
- `Issue`: configuration contradicts business logic, official docs, expected
  type, trigger context, or destination payload.
- `Likely issue`: strong evidence points to a problem, but runtime or owner
  proof is still needed before mutation.
- `Runtime QA required`: setup is plausible, but export/API cannot prove timing,
  data availability, DOM, server, CMP, or vendor behavior.
- `Owner decision required`: the blocker is business, legal, privacy, or vendor
  ownership rather than GTM mechanics.
- `Consolidate`: same role/output can be safely combined after dependency QA.
- `Delete candidate`: no valid purpose or consumer is found after dependency and
  semantic review.
- `Not applicable`: the object family does not apply to the business/scope.

Avoid "wrong" when the export only shows missing proof. For example, a click
trigger without a page-path condition is not automatically wrong if the button
only exists in the intended context; mark runtime QA or owner evidence required.

## Reporting Rule

The cleanup plan is not a configuration encyclopedia. It should report:

- confirmed issues;
- likely issues with strong evidence;
- material runtime blockers;
- consolidation/delete/update operations;
- documented exceptions for high-risk objects that are intentionally kept.

Do not report every parameter that looked normal. Summarize families such as:
"15 Piano click.action tags reviewed; 12 OK by shared pattern, 3 anomalies
listed." Keep the matrix as evidence that the review happened.

Cleanup plan rows should surface only the decision-relevant result: what is
wrong or changing, affected objects, impact, recommendation, QA/debug method,
blocker/owner, status, and next action. Keep raw D3 proof in the matrix or
Custom Code Review tab.

## Completion Gate

A semantic review is incomplete when:

- high-impact active tags have no matrix row;
- `depth_required` includes D1, D2, or D3 but `depth_completed` does not include
  the same tier;
- `depth_required` includes D3 but the D3 proof fields are missing, blank, or
  generic;
- D2/D3 proof uses generic evidence wording instead of explaining source/input,
  logic/action, output or side effect, consumer expectation, and judgment;
- a tag is called semantically validated but its trigger context, key payload
  fields, variable/source logic, or consent/server status are blank;
- a custom-code object is only risk-flagged and has no purpose, output/side
  effect, consumer context, semantic status, or blocker;
- a custom-code row says that line-level/config review still needs to be done
  during cleanup execution;
- a runtime-only assumption is reported as an issue or as OK without proof;
- the cleanup plan contains a finding that is not backed by a matrix row,
  operation row, or documented exception.

Forbidden final-plan placeholders include `review custom code`, `perform
line-level review`, `check variables`, `validate trigger logic`, and equivalent
wording when used as the main cleanup action. Those phrases describe audit work.
Finish the review, or mark the affected workstream `Incomplete / blocked` with
the exact missing evidence.

When the full matrix would be too large for the user-facing deliverable, provide
the matrix as CSV/XLSX and show only exemplar rows or material findings in the
cleanup plan.
