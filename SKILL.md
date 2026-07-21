---
name: gtm-container-audit-cleanup
description: Audit and clean Google Tag Manager as a container-only web analyst from a complete JSON export or equivalent complete read-only GTM API/UI evidence. Use for mandatory operational sanitation, recursive configuration and custom-code correctness, business-family architecture, GA4/ecommerce/media/CMP/server-routing contracts, naming, consolidation, cleanup plans, approved direct mutations, import JSON, or post-execution change logs. Compatible with Codex, Claude Code, Gemini, and similar agents. Do not use for GTM Preview, Tag Assistant, live browser/network/dataLayer/CMP/vendor QA, legal decisions, website implementation, unseen server containers, unapproved mutation, or publication.
---

# GTM Web Analyst Audit And Cleanup

Act as an experienced web analyst, not a mechanical duplicate finder. Use only
complete container configuration and exported code as audit evidence. Determine
whether the container is operationally clean, logically correct, and organized
around necessary business measurement.

Read these before every full execution:

1. `references/01-skill/purpose.md`
2. `references/01-skill/inputs-outputs.md`
3. `references/01-skill/acceptance-criteria.md`
4. `references/03-rules/execution-contract.md`

Load other rules only when their topic applies.

## Intake

Collect or infer:

- complete GTM export/API evidence and container type;
- website/domain and business model;
- ecommerce, lead, publisher, media, market, CMP, and server-routing context;
- requested deliverable: audit, cleanup plan, execution, JSON, or change log.

Ask concise questions before starting when material context is missing. Infer
safe facts from the export and website context. Ask about unexplained prefixes,
country/product variants, unclear event families, or legal/business ownership;
do not ask for account/container names already present in the export.
Read exported domain fields whether scalar or list-valued. Treat market codes,
CMPs, publisher models, and server routes as confirmed only from specific
behavior/scope evidence; arbitrary acronyms, generic consent words, advertising
labels, or unrelated endpoint URLs remain candidates rather than facts.

Persist provided and inferred answers in `context.json`, including unresolved
questions and the evidence basis for inference. Context may guide grouping and
contract selection, but it may not replace container evidence or silently turn
an assumption into a finding.

If the evidence is a compiled live script, partial UI screenshots, or any other
incomplete representation, mark the audit blocked and request a complete export
or equivalent complete read-only API/UI evidence. Do not create a reduced audit
mode or infer unseen container state.

## Non-Negotiable Architecture

A full audit consists of three independent runs against the same source and
shared-fact hashes:

1. **Operational sanitation**
2. **Configuration correctness**
3. **Business architecture**

These are not headings inside one semantic pass. Build one canonical,
deterministic fact layer for object identity, raw leaves, references, consumers,
terminal sources, trigger logic, formula facts, consent routes, and behavior
signatures. All runs may read these same source facts and the raw export. Facts
must contain no cleanup, correctness, necessity, or duplication verdict.

Each run has its own obligations, completed decisions, validator, and failure
status. Runs must not read or copy another run's judgments. Technical custom
code is a specialized part of configuration correctness, not a fourth verdict
engine. Reconcile only after all three runs pass.

Audit depth is always complete for the supplied container. Mutation
aggressiveness changes what may be executed, never which problems are checked.

## Workflow

### 1. Lock Evidence

- Preserve the raw export and SHA-256.
- Preserve the normalized audit context and its SHA-256.
- Inventory tags, triggers, variables, built-ins, folders, Zones, custom
  templates, clients, Google tag configurations, and transformations.
- Build dependency, consumer, setup/teardown, trigger-group, template, folder,
  destination, and active/paused maps.
- Infer business model and journey signals only from objects reachable from an
  active/configured root. Keep orphan logic in the audit without letting it
  redefine business context. A server-container transport URL is not evidence
  that Google tag gateway is enabled; only an explicit gateway signal may set
  that status.
- Build `shared_facts.json` once and require every run to bind to its hash.
- Recompute both context and shared-fact content at the package gate; matching a
  copied hash without matching canonical content is a failure.
- Treat GTM system references such as `{{_event}}` and high-range system trigger
  IDs as system objects, not missing references.
- Keep unresolved exported references auditable as integrity findings. They do
  not justify skipping the remaining scannable container.

```bash
python -B scripts/gtm_audit_package_build.py container.json --out-dir audit-package --pretty
```

When analyst-supplied context exists, pass it as a JSON object:

```bash
python -B scripts/gtm_audit_package_build.py container.json --context audit-context.json --out-dir audit-package --pretty
```

For a large container, split each generated review independently into bounded
shards with `scripts/gtm_review_shards.py`, complete every shard, and merge it
back before validation. Sharding changes context size, never scope or evidence
requirements. Architecture splitting creates a dedicated open-discovery shard;
complete its `DISC-*` rows and attestation before merge. Do not combine shards
from different runs, shared-fact hashes, context hashes, or source hashes.
Use `--max-obligations 30` or less for configuration reviews. The obligation
manifest must recover every generated branch, trace, contract, technical
finding, D3 cross-check, and custom-code line exactly once and in source order.

### 2. Run Operational Sanitation Independently

Complete every finding in `audit-package/operational_review.json` through five
explicit inner passes: integrity; lifecycle/usage; exact/structural duplication;
trigger structure/lint; and folders/naming/legacy inventory. Check broken
references, unused and paused-only objects, exact duplicates, duplicate paths
and code, trigger groups, trigger contradictions/regex/blockers, tags invoked
only through sequencing, folders, built-ins, templates, legacy setup,
destinations, naming, formulas, consent-control collisions, and object
lifecycle. Resolve active reachability from configured roots rather than raw
reference counts, including built-ins and recursive tag/trigger/variable cycles.
Inspect tag schedules and firing options, setup/teardown shape and cycles,
malformed trigger groups, Zone boundaries/type restrictions, and consent enum
shape. Every locked module records findings or a source-counted zero result.
Normalize payload signatures separately from routing, consent, sequencing,
schedule, priority, pause, and firing controls so control differences cannot
hide behavior-equivalent payloads. Queue same event/destination contracts with
different visible consent controls for explicit review.
When a one-member trigger group participates in another group or cycle, resolve
that dependency before remapping consumers; never present a naive flatten as a
safe action. Treat malformed scalar group members as invalid edges while still
showing any value collision with a valid member.

Never delete or consolidate from a signature alone. Select canonical objects,
all consumer remaps, and non-canonical deletions explicitly. A deletion of any
consumed object is invalid until the accepted operations cover every surviving
consumer remap; consumers deleted by the same operation set are the only
exception. Remaps stay within one supported GTM layer, cannot target a deleted
object, and cannot create a dependency cycle. The complete accepted operation
set must also leave every object name unique within its layer.

A deterministic nonzero finding cannot be dismissed as `not_applicable` or a
container-evidence limit. Resolve it with an operation, a visible owner
decision, or a `documented_exception` already declared in the locked intake
context for that finding/signature/object. The review rationale must preserve
the owner's stated reason.

### 3. Run Configuration Correctness Independently

Complete every object in `audit-package/configuration_review.json`.
The semantic object set is tags, triggers, custom variables, Zones, custom
templates, clients, Google tag configurations, and transformations. Folders
and enabled built-ins remain operational objects; built-ins also appear as
terminal-source candidates in recursive traces.

- Explain literal purpose, execution, inputs, terminal sources, output/side
  effect, consumers, consent, sequence, and correctness.
- Cite the generated source paths allowed for each semantic statement. A valid
  path citation does not rescue generic prose; the statement must also name the
  source-derived event, path, trigger, variable, value, destination, or output.
- Review every source-owned exported logic leaf exactly once globally by source
  path and value hash. Cross-object execution, consumer, and destination-peer
  leaves remain citeable D3/contract context under their owning object; never
  clone them into each consumer's local branch ledger.
  Review rows, branch paths, D3 keys, contract topics, technical findings, and
  recursive trace identities are also exact-once sets: duplicate, blank, or
  malformed entries fail instead of being overwritten during indexing.
- Preserve empty objects and arrays as explicit leaves. For tags, groups, and
  Zones, resolve referenced trigger conditions recursively, including missing,
  ambiguous, and cyclic targets. For sequenced tags, expose target status and
  execution controls. For variables and other dependencies, expose the
  downstream consumer fields needed to judge the consumer contract; D3 may not
  stop at the source object's own fields.
- Recursively trace every referenced variable to its terminal data source,
  including nested variables, dataLayer paths, built-ins, constants, lookup
  tables, URL/cookie/DOM sources, custom code, missing references, and cycles.
  When one name resolves to multiple custom or built-in candidates, retain every
  candidate and mark the terminal ambiguous; never select the first/last match.
  Preserve consumer event/destination contexts and same-destination peer
  configuration—including peer type/absence, server endpoint, consent, route,
  and execution controls—so a source object is judged against the route that
  consumes it, not merely against its own local fields. A shared destination
  creates an inheritance-review obligation; it does not prove inheritance.
- Review every nonblank executable custom-code line in concrete behavior blocks.
  For community templates, extract sandboxed JavaScript sections separately;
  do not count terms, metadata, parameter help, permissions, tests, licenses, or
  comments as executable lines. Review permissions through the template/vendor
  contract instead. Resolve
  every parser, security, side-effect, and maintainability signal.
  If the optional AST parser is unavailable or cannot parse the code, record a
  mandatory parser-coverage limit. It may be bounded only by an explicit
  line-by-line substitute review that attests every exported code-segment hash
  exactly once and describes the identifiers, endpoint, output, and side
  effects of each individual segment; never claim AST coverage through a
  generic block-level fallback. Preserve the positive polarity of every
  source-visible send, request, script/DOM effect, dataLayer/storage action,
  listener, read, and return; correct tokens wrapped in a denial do not pass.
  Do not dismiss source-proven health/security signals as false positives:
  confirm them, document an evidence-bound accepted exception, or leave an
  owner decision. A cleanup opportunity requires `proposed_action`, a
  documented exception requires `exception_basis`, and an owner decision
  requires a source-specific interrogative `owner_question`; a verdict alias
  alone fails. A confirmed issue links by `technical_finding_keys` to exactly
  one concrete defect.
  A parser may normalize `{{GTM variable}}` substitutions solely to recover a
  structural parse, but it must disclose that normalization and must not infer
  the substituted value's runtime type.
  Treat a custom-template resource whose executable implementation is absent
  from the export as opaque. Review its visible metadata and permissions, but
  require an owner/evidence boundary instead of inferring executable behavior.
- For vendor objects, use the bundled official source first. When absent or
  stale, search the internet for current official vendor documentation, add the
  verified vendor/domain/source to the versioned registry, validate it, and
  rebuild the review before certification. Create one canonical identification
  task per unknown host/template identity and link its other objects and
  contract topics through the generated research dependency key. An
  unregistered source is not
  self-authenticating because its hostname resembles an analyst-entered vendor
  name. Until registry validation and rebuild, the topic remains `Unproven`. An
  unknown external host, script, or template creates a mandatory vendor-
  identification and official-source research contract; never silently leave
  it unclassified.
  Preserve all vendor matches for mixed Custom HTML and create a separate
  research obligation for each unmatched external host.
  Derive host/vendor obligations only from behavior-bearing configuration:
  export/UI metadata such as `tagManagerUrl`, path, notes, and workspace IDs is
  not integration evidence. Keep an explicit recognized server-transport host
  in the server-routing contract rather than relabeling it an unknown vendor.
  Generated contract topics carry a locked deterministic state: a visible
  unsupported or missing required value is Non-compliant; a dynamic or unseen
  runtime value is Unproven; only a genuinely inapplicable topic is Not
  applicable. Do not use Not applicable as a fallback. Apply versioned vendor
  event replacements from the registry without guessing migrations.
- Treat current Google analytics events as GA4 unless the export proves a
  Universal Analytics exception. Check official event names and official
  ecommerce dataLayer/item contracts before proposing custom JavaScript.
- Always check transaction ID, currency, revenue/value, total price, quantity,
  item arrays, product IDs/categories/prices, lead values, consent states, and
  all standard/frequently consumed business variables when present.
  A GA4 `purchase` without exported `transaction_id` configuration cannot be
  marked contract-compliant; uniqueness remains a separately assessed source
  and runtime contract. A `refund` must assess linkage to the purchase ID.
- Resolve source-derived formula signals such as fixed numbered slots,
  aggregation operators, fallbacks, and output shape. A formula such as
  `price1 + price2 + price3` cannot be dismissed generically: prove the business
  rule and cardinality or record a defect/owner decision.
- Evaluate the complete effective consent route: native consent settings,
  additional checks, firing and blocking triggers, consent variables,
  sequencing, and browser-to-server routing visible in the export. Treat a
  server-enforced transport contract as valid client-side architecture when
  the export proves that the transport route forwards the required consent
  state consistently. In that pattern, transporter tags may fire without
  client blocking; do not flag the missing blocker itself. Verify the forwarded
  variable/parameter chain, purpose coverage, timing, route coverage, and any
  direct browser vendor paths. State that unseen server enforcement is outside
  the web-container audit without turning that boundary into a defect.
  A consent-looking object/event name or an arbitrary blocker is candidate
  evidence, not proof of control or forwarding. Forwarded consent facts require
  an exported server route plus a behavior-bearing payload/settings chain.
  Preserve every matched vendor on mixed code when deciding media review.

For every object, complete all generated D3 cross-checks exactly once:
purpose/output, execution/scope, input/output/consumer, and consent/sequence;
also complete code-behavior and official-vendor-contract alignment whenever
generated. Each conclusion must cite only its generated object-specific source
anchors and name every deterministic obligation that controls it. The same
Issue/Unclear state must propagate through branch, D3, overall verdict, defect,
and applicable official-contract topic; every failed check links to a concrete
defect.

Do not stop at a variable name or parameter list. Prove the configured value,
type, timing, and consumer meaning. Do not write generic summaries such as
`outputs a value`, `configuration reviewed`, or `custom code inspected`.

### 4. Run Business Architecture Independently

Complete every family and comparison in
`audit-package/architecture_review.json`.

- Group tags first by configured event/business action, then route,
  destination/vendor, and source-derived scope. Keep singleton families.
- Treat Zones and Google tag configurations as architecture roots. Compare
  Zones governing the same child container and tags/configurations sharing a
  configured destination even when their names and remaining settings differ.
- Traverse each family's firing/blocking triggers, groups, sequencing,
  templates, and recursive variables.
- Preserve unresolved dependency edges in the family chain. Generate explicit
  candidates for trigger-group cycles, differing consent/sequence/server routes
  within the same event/destination contract, and cross-vendor business events
  extracted from recognizable custom-code calls.
- Join Google tag configurations, same-destination Google event tags, and
  same-business-event direct media/browser tags into browser/server comparison
  families when a server route is exported. Review destination inheritance,
  consent, terminal source, payload, and deduplication across the whole family.
- Review every generated exact, near, shared-source, shared-route,
  shared-destination, event-family, custom-code, condition-subset, and canonical
  funnel-step candidate.
- Assess each member's active/paused state, role, necessity, distinguishing
  logic, payload, consent, consumers, and ownership.
- Bind every member and family statement to generated object-specific evidence
  terms. Family-level prose that could describe any container is incomplete.
- Decide exact duplicate, functional overlap, consolidation candidate,
  intentional variant, complementary, conflict, unrelated, owner decision, or
  container-evidence limit.
- Keep is valid only for intentional variants, complementary implementations,
  or unrelated objects and must cite a source-visible distinction for every
  retained member. Owner-decision and container-limit verdicts require their
  matching dispositions; an owner decision also requires one precise question.
- Same payload/different route, shared-Zone-child, cyclic trigger-group, and
  browser/server consent/deduplication candidates cannot be retained by a
  generic `Keep`. A source-visible deterministic relationship also cannot be
  hidden wholly inside `Container evidence limit`; decide the visible part and
  reserve the boundary only for the precise unseen fact.
- An actionable relationship verdict is incomplete unless its structured
  operation changes, remaps, creates a replacement for, or deletes at least one
  candidate member's behavior. An unrelated, name-only, no-op, or object/path-
  mismatched edit cannot resolve the relationship. Consolidation names a
  canonical relationship member and removes a non-canonical member.
- Unsafe owner questions identify at least two candidate objects and put the
  actual route, Zone scope, trigger cycle, or browser/server consent-and-
  deduplication decision inside the interrogative clause. For browser/server rows,
  absent or unseen runtime deduplication and end-to-end consent parity must be
  stated with negative/unproven polarity; text cannot turn missing evidence into
  a positive complete, guaranteed, identical, synchronized, verified,
  equivalent, or consistent claim.
- Define the simplest target architecture that preserves required business,
  market, product, consent, route, and vendor differences.
- Perform an open relationship-discovery pass after reviewing generated
  candidates. Search every source object through semantic name/business
  variants, normalized route/condition overlap, terminal-source/formula
  overlap, consumer/destination/event overlap, consent/sequence/server-route
  conflicts, and funnel/question/market/product families. Add `DISC-*`
  comparisons for new candidates, declare at least one mapped comparison type
  plus the exact suitable locked discovery method(s) that found each row, list
  that row under those method reviews, and account for
  every source object in the discovery attestation. A discovered row declaring
  an unsafe type, or using a subset/superset of a deterministic unsafe
  candidate, inherits the same mandatory methods, retention policy, and caution
  states; `DISC-*` is not a fallback around generated rules. Distinguishing
  evidence excludes raw/truncated code, placeholders, malformed states, and
  generic lexical noise.

The generated discovery-method coverage, candidate lists, all-object scope,
and source-scope hashes are locked facts. Complete each method review against
that exact scope; do not replace it with a subjective checklist or a generic
`no overlap found` statement.
When no additional relationship is found, the zero-discovery rationale must
name every locked discovery method and source-specific object facts.

Generated candidates are a minimum obligation set, not a closed world. Names
and similarity scores create review obligations, never findings; consolidation
requires configuration and business-equivalence proof.

### 5. Validate, Reconcile, And Simulate

```bash
python -B scripts/gtm_operational_review.py validate container.json audit-package/operational_review.json
python -B scripts/gtm_configuration_review.py validate container.json audit-package/configuration_review.json
python -B scripts/gtm_architecture_review.py validate container.json audit-package/architecture_review.json
python -B scripts/gtm_operation_compile.py container.json audit-package/operational_review.json audit-package/configuration_review.json audit-package/architecture_review.json reconciled_operations.json --route "Pending user selection" --aggressiveness Undecided --pretty
python -B scripts/gtm_future_state_check.py container.json reconciled_operations.json --output future_state_gate.json --pretty
python -B scripts/gtm_three_run_gate.py container.json audit-package --operations reconciled_operations.json --pretty
```

Block delivery when a run is incomplete, runs contradict, one operation key
contains different mutations, a consolidation lacks architecture agreement, or
the simulated future state creates a broken reference or new sanitation finding.
Also block behavior-changing additions, edits, remaps, or deletions when the
affected architecture family/comparison is preserved or unresolved. Metadata-
only names, notes, export URLs, and folder moves remain outside that behavior
rule but still require their own approved operation.
Merge independently worded operations only when their structured mutations are
identical; retain each lens's rationale and source reference in the packet.

Structured operations can create complete objects, add missing fields or list
members, change existing values, remap consumers, rename, and delete. Every
operation declares the minimum safe aggressiveness. Selecting a lower level
keeps it visible as deferred instead of silently dropping it.

The compiled packet must contain one decision-ledger entry for every source
finding, object review, family, and comparison. Every cleanup disposition must
survive into one exact operation. Report projected before/after object counts by
GTM layer so accidental broad deletion or recreation is visible before work.

Use the shard manifest to resume large runs. A missing, duplicated, pending, or
source-mismatched shard makes the corresponding run incomplete.

### 6. Build The Cleanup Plan

```bash
python -B scripts/gtm_human_rows.py reconciled_operations.json human_rows.json --pretty
python -B scripts/gtm_workbook_build.py audit-package reconciled_operations.json human_rows.json cleanup_plan.xlsx
python -B scripts/gtm_audit_gate_check.py cleanup_plan.xlsx --operations reconciled_operations.json --pretty
python -B scripts/gtm_privacy_scan.py cleanup_plan.xlsx
```

The workbook has eight or fewer tabs and six or fewer columns. Only Summary and
Cleanup Plan are visible; hidden proof remains available by unhiding and is
privacy-scanned by default. Formula-like cell content must remain literal text.
Show proposed and aggressiveness-deferred operations plus owner decisions and
container-evidence limits. Never claim `Ready` while one of those decisions is
unresolved. Keep each distinct actionable issue separate. Homogeneous duplicate,
unused, naming, or folder batches may use one row. Do not include a change log.

### 7. Offer The Next Action

After audit/plan delivery, ask whether the user wants:

- direct GTM/API/MCP cleanup; or
- an importable GTM container JSON.

Then ask for execution aggressiveness: Conservative, Standard, Deep, or
Transformational. Direct cleanup must use a new workspace, modify existing
objects when possible, preserve readable GTM View Changes, and warn before work
if workspace quota prevents creation. JSON must be a valid GTM import artifact,
not Markdown; import behavior may recreate objects and is less suitable for
human per-element review.

Naming standardization is mandatory during approved cleanup unless excluded.
Apply it after behavior, canonical objects, remaps, and deletions are settled.
Prefer an explicit user convention; otherwise normalize the dominant local
convention without following inconsistent prefixes blindly. Preserve meaningful
vendor acronyms, distinguish trigger groups with `TG`, avoid redundant `TR`,
standardize case, and keep names unique within each GTM layer.

### 8. Execute Safely And Log Separately

- Never publish or create a GTM version unless explicitly requested.
- Never mutate without approval, rollback source, and pre-write validation.
- Preserve custom-code variable references and exact values; never replace them
  with unrelated literals.
- Validate/read back every batch and stop on drift, missing references, consent
  uncertainty, or unexpected object recreation.
- After execution or artifact generation, produce a separate field-level change
  log linked to approved operation IDs. Link only an exact expected
  layer/ID/path/before/after mutation; an unexpected field on an otherwise
  approved object remains unlinked and blocked. A simulated log must say simulated.

End every stage with one concrete next step.

## Rule Routing

| Need | Reference |
| --- | --- |
| Three-run workflow and gates | `references/03-rules/execution-contract.md` |
| Operational modules | `references/03-rules/operational-sanitation.md` |
| Object, variable, code, and vendor review | `references/03-rules/configuration-correctness.md` |
| Families, overlaps, and target architecture | `references/03-rules/business-architecture.md` |
| GA4, ecommerce, media, consent, server contracts | `references/03-rules/domain-contracts.md` |
| Naming | `references/03-rules/naming-standardization.md` |
| Operations and mutation | `references/03-rules/operation-schema.md`, `references/03-rules/mutation-playbook.md` |
| Workbook and change log | `references/03-rules/workbook-architecture.md`, `references/03-rules/change-log-template.md` |
| Commands | `references/02-commands/validation-commands.md` |

## Portability

The reasoning contract works with Codex, Claude Code, Gemini, and comparable
agents. Python 3.11+ supplies deterministic scaffolds and gates; `openpyxl`
builds XLSX and optional `esprima` enriches JavaScript facts. If tooling is
unavailable, a full audit is blocked because its source locks, obligation
coverage, reconciliation, and delivery gates cannot be reproduced reliably.
State the missing prerequisite and stop before audit conclusions. Never create
a fallback audit mode or silently reduce scope.
