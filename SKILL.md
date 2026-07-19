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

Persist provided and inferred answers in `context.json`, including unresolved
questions and the evidence basis for inference. Context may guide grouping and
contract selection, but it may not replace container evidence or silently turn
an assumption into a finding.

If evidence is limited to a compiled live script or partial UI screenshots, use
`references/03-rules/limited-audit-protocol.md` and label the result limited.

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

Audit depth is always complete unless the user narrows scope. Mutation
aggressiveness changes what may be executed, never which problems are checked.

## Workflow

### 1. Lock Evidence

- Preserve the raw export and SHA-256.
- Preserve the normalized audit context and its SHA-256.
- Inventory tags, triggers, variables, built-ins, folders, custom templates,
  clients, and transformations.
- Build dependency, consumer, setup/teardown, trigger-group, template, folder,
  destination, and active/paused maps.
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
lifecycle. Every module records findings or a source-counted zero result.

Never delete or consolidate from a signature alone. Select canonical objects,
all consumer remaps, and non-canonical deletions explicitly.

A deterministic nonzero finding cannot be dismissed as `not_applicable` or a
container-evidence limit. Resolve it with an operation, a visible owner
decision, or a `documented_exception` already declared in the locked intake
context for that finding/signature/object. The review rationale must preserve
the owner's stated reason.

### 3. Run Configuration Correctness Independently

Complete every object in `audit-package/configuration_review.json`.

- Explain literal purpose, execution, inputs, terminal sources, output/side
  effect, consumers, consent, sequence, and correctness.
- Cite the generated source paths allowed for each semantic statement. A valid
  path citation does not rescue generic prose; the statement must also name the
  source-derived event, path, trigger, variable, value, destination, or output.
- Review every exported logic leaf exactly once by source path and value hash.
- Recursively trace every referenced variable to its terminal data source,
  including nested variables, dataLayer paths, built-ins, constants, lookup
  tables, URL/cookie/DOM sources, custom code, missing references, and cycles.
- Review every nonblank custom-code line in concrete behavior blocks. Resolve
  every parser, security, side-effect, and maintainability signal.
- For vendor objects, use the bundled official source first. When absent or
  stale, search the internet for current official vendor documentation. An
  unknown external host, script, or template creates a mandatory vendor-
  identification and official-source research contract; never silently leave
  it unclassified.
- Treat current Google analytics events as GA4 unless the export proves a
  Universal Analytics exception. Check official event names and official
  ecommerce dataLayer/item contracts before proposing custom JavaScript.
- Always check transaction ID, currency, revenue/value, total price, quantity,
  item arrays, product IDs/categories/prices, lead values, consent states, and
  all standard/frequently consumed business variables when present.
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

For every object, complete all generated D3 cross-checks exactly once:
purpose/output, execution/scope, input/output/consumer, and consent/sequence;
also complete code-behavior and official-vendor-contract alignment whenever
generated. Each conclusion must cite only its generated object-specific source
anchors, and every failed check must link to a concrete defect.

Do not stop at a variable name or parameter list. Prove the configured value,
type, timing, and consumer meaning. Do not write generic summaries such as
`outputs a value`, `configuration reviewed`, or `custom code inspected`.

### 4. Run Business Architecture Independently

Complete every family and comparison in
`audit-package/architecture_review.json`.

- Group tags first by configured event/business action, then route,
  destination/vendor, and source-derived scope. Keep singleton families.
- Traverse each family's firing/blocking triggers, groups, sequencing,
  templates, and recursive variables.
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
- Define the simplest target architecture that preserves required business,
  market, product, consent, route, and vendor differences.
- Perform an open relationship-discovery pass after reviewing generated
  candidates. Search every source object through semantic name/business
  variants, normalized route/condition overlap, terminal-source/formula
  overlap, consumer/destination/event overlap, consent/sequence/server-route
  conflicts, and funnel/question/market/product families. Add `DISC-*`
  comparisons for new candidates and account for every source object in the
  discovery attestation.

The generated discovery-method coverage, candidate lists, all-object scope,
and source-scope hashes are locked facts. Complete each method review against
that exact scope; do not replace it with a subjective checklist or a generic
`no overlap found` statement.

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
An agent may provide a clearly labelled limited advisory only when the user
explicitly accepts that reduced deliverable. Never label it a complete audit or
silently reduce scope.
