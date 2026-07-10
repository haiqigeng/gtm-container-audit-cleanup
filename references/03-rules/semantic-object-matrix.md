# Semantic Object Matrix

Use this reference after inventory and dependency mapping. It turns semantic
review into a scalable gate: every configurable GTM object is traced deeply in a
full audit, and the stakeholder report shows decisions instead of raw GTM
configuration dumps.

## Contents

- Principle
- Depth Tiers
- Required Depth Rule
- Recursive D3 Trace
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

For a full audit, assign D3 to every configurable/executable object: tags,
triggers, variables, custom templates, consent settings, and any referenced
template field or custom-code/configuration branch. D1/D2 are still recorded,
but they are not a stopping point. Only metadata-only objects with no execution
logic, such as folders, may remain D1/D2 unless naming, dependency, or cleanup
logic depends on them.

For an explicitly limited audit, assign the minimum depth needed for the limited
scope and label the deliverable limited.

| Tier | Use for | Required work |
| --- | --- | --- |
| D1 Classification | Every object. | Identify role, family, consumers, and semantic status. |
| D2 Configuration logic | Every tag, trigger, variable, template, and consent/server configuration. | Check event name, trigger context, meaningful fields, variable paths, output type, and consumer expectation. |
| D3 Source/code/configuration logic | Every tag, trigger, variable, custom template, custom HTML, custom JavaScript, lookup/regex table, DLV, URL/DOM/cookie variable, consent helper, and referenced configuration branch in a full audit. | Recursively inspect source DLV path, formula, lookup rows, custom JS, custom HTML, trigger filters, template fields, storage/cookie/DOM/network side effects, and type compatibility until terminal sources are reached. |
| D4 Runtime proof | Async pages, SPA/infinite scroll, DOM scraping, CMP timing, server routing, ad slots, vendor acceptance, and any context not provable from export/API. | Define exact Tag Assistant, browser/network, vendor-platform, or owner evidence required. |

Depth is cumulative. A D3 object must also satisfy D1 and D2.

## Required Depth Rule

Required depth is an execution requirement. In a full audit, every tag, trigger,
variable, and custom template requires D3 when the export, API, custom template
configuration, or supplied evidence contains its configuration. Complete that
depth during the audit. Do not report it as required-but-not-done.

Only D4 runtime proof may be deferred. D4 covers behavior that cannot be proven
from export/API evidence, such as browser timing, DOM availability, CMP order,
ad-slot rendering, server-container routing, or vendor-platform acceptance.

If D3 is required, `depth_completed` must say that D3 was completed and the row
must prove it with source/code evidence. Phrases such as `D3/D4 blocked`,
`static scan only`, `review later`, `full code walkthrough required`, or
`D3 required` do not count as D3 completion. If D3 cannot be done because the
source/config is genuinely unavailable, mark the workstream `Incomplete /
blocked` and identify the missing source. In a normal GTM export, Custom HTML,
Custom JavaScript, DLV paths, lookup/regex tables, trigger filters, tag
parameters, template fields, and variable references are scannable.

## Recursive D3 Trace

D3 is not complete when the row stops at "tag uses variable X" or "trigger uses
condition Y". For each object, recursively trace every referenced object until
the source reaches a terminal value or a D4 runtime-only blocker.

Required trace by layer:

- **Tag**: tag type/template, event name or command, firing and blocking
  triggers, setup/teardown references, every meaningful template field, every
  variable reference inside parameters or custom HTML, outgoing vendor/server
  fields, and expected destination meaning.
- **Trigger**: GTM event type, custom event name, every filter variable, filter
  operator/value, trigger-group children, consuming tags, firing/blocking role,
  and expected page/action context.
- **Variable**: variable type, source path or code/config, lookup/regex input
  and rows, default/fallback, returned value type, every consumer field or
  trigger condition, and whether the variable name matches its source and
  consumers.
- **Variable configuration**: if a variable reads another variable, dataLayer
  path, built-in, cookie, DOM, URL component, table, constant, or custom code,
  continue the trace into that source. Stop only at a terminal source such as a
  concrete dataLayer path, built-in value, URL/cookie/DOM source, constant, or
  custom-code return/side effect.
- **Custom template**: fields exposed to tags/variables, permissions, external
  destinations, consumers, and whether configured fields match official/vendor
  expectations.

For each traced edge, compare meaning, not just syntax:

```text
consumer field meaning -> referenced object -> source logic
-> returned value/side effect -> output type -> sibling/peer fields
-> official/vendor/business expectation
```

Actively detect:

- different semantic fields using identical or near-identical source logic
  without a documented reason, such as two Consent Mode signals using the same
  CMP purpose;
- one variable reused by consumers with incompatible expected types or business
  meanings;
- triggers with similar filters that can be merged, or triggers whose names
  imply a context not enforced by filters/source variables;
- variables whose names imply totals, quantities, prices, consent, country,
  product, lead type, or page type but whose source logic returns another
  meaning;
- duplicate or similar custom-code branches, DLV paths, lookup rows, trigger
  conditions, or vendor payload mappings that can be consolidated after
  dependency QA.

## D1-D3 Proof Queue

Before writing findings, operations, cleanup plans, or change logs, build an
internal queue of every tag, trigger, variable, custom template, and referenced
configuration branch that requires D1, D2, or D3. The queue must include object
ID/name, layer, required depth, reason for depth, consumer count, parent/child
references, and queue status.

Do not compile cleanup operations for an object while its own D1-D3 queue row or
any referenced child row required to judge it is unresolved. Queue rows may be
closed only as:

- `Complete`: D1-D3 evidence is recorded in the matrix or custom-code review,
  including the recursive source/consumer trace.
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

Bind the review to the exact source: layer and ID, configuration hash, JSON
path, every configuration-leaf hash, every nonblank code-line hash, every
consumer key, and the complete generated variable-chain requirement. A list of
anchors or hashes without a specific interpretation does not count as review.

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

The source artifact is `semantic_review.json`, with one row per tag, trigger,
variable, custom template, server client, and transformation. It preserves
object key, ID, name, layer, type, config hash, source path, role, contract,
literal behavior, inputs, output, consumers, sibling comparison, judgment,
cleanup implication, confidence, exact evidence anchors, branch reviews,
code-line reviews, and recursive reference traces.

The XLSX matrix consolidates those fields into six structured columns:

- `Object identity`
- `Purpose & contract`
- `Configuration logic`
- `Output & consumers`
- `Judgment`
- `Proof & trace`

This consolidation is presentation only. The structured cells retain source
keys for validation. Do not discard branch, code-line, trace, or consumer proof
to make the sheet narrower.

## Execution Guarantee

The matrix is a completion artifact, not an optional appendix. An audit or
cleanup plan that claims complete semantic coverage must be able to point to a
matrix row or explicit workstream blocker for every meaningful object family.

Use object-level rows for every tag, trigger, variable, and custom template in a
full audit. Family rows may summarize repeated patterns only after the
underlying object-level D3 rows exist. Repeated low-risk helpers may be grouped
in the user-facing summary, but their proof rows must still exist in the matrix
or package.

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

Do not over-expand purely mechanical hygiene buckets. Straightforward unused
object deletion candidates, exact duplicate removals, one naming-convention
batch, and folder organization can stay as one cleanup-plan row when every
object in the bucket has the same evidence, action, QA, and rollback. Semantic
or business-logic findings must stay object-level or use a parent `Summary` row
with immediate child `Detail` rows.

## Completion Gate

A semantic review is incomplete when:

- any tag, trigger, variable, or custom template in a full audit has no D3
  matrix/proof row or explicit limited-scope exclusion;
- `depth_required` includes D1, D2, or D3 but `depth_completed` does not include
  the same tier;
- `depth_required` includes D3 but the D3 proof fields are missing, blank, or
  generic;
- D2/D3 proof uses generic evidence wording instead of explaining source/input,
  logic/action, output or side effect, consumer expectation, and judgment;
- a tag is called semantically validated but its trigger context, key payload
  fields, variable/source logic, or consent/server status are blank;
- a tag field, trigger filter, or variable consumer is called semantically
  validated while a referenced variable/configuration source was not recursively
  traced;
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
