# Execution Contract

Read this file for every full audit, cleanup plan, cleanup execution, importable
JSON artifact, or change log. It is the canonical completion contract. Domain
references may add checks, but they may not lower these requirements.

## Contents

- Product decision and evidence hierarchy
- Protected pipeline and full-audit coverage
- Source-bound D1-D3 and three independent lenses
- Official documentation and operation gates
- Mutation, human output, and completion boundaries

## Product Decision

The skill answers whether a GTM container implements the intended measurement
and activation logic accurately, coherently, and maintainably. Object deletion,
deduplication, naming, and folder hygiene are supporting outcomes. They do not
replace business-logic review.

## Evidence Hierarchy

Use the strongest evidence available and label its limits:

1. exported/API configuration and complete exported custom code;
2. official vendor and platform documentation;
3. runtime dataLayer, browser, network, CMP, and server observations;
4. verified business or implementation-owner statements;
5. inference from names or common patterns.

Names may guide scope but never prove behavior. Separate `Observed`, `Derived`,
`Documented`, `Runtime verified`, and `Inferred` claims. Never promote an
inference to a defect without contradictory source evidence or runtime proof.

## Required Pipeline

For export-based work, preserve these stages and artifacts:

```text
container JSON
-> source_model.json
-> deterministic_findings.json
-> semantic_coverage_tasks.json
-> technical_code_findings.json
-> semantic_review.json
-> reconciled_operations.json
-> human_rows.json
-> cleanup_plan.xlsx
-> approved execution or validated import JSON
-> field_diff.json
-> change_log.xlsx
```

The source model is a navigation map. Semantic coverage tasks are questions to
answer. Technical code findings are facts and risks. None is a cleanup finding
or operation until the source-bound semantic review makes and evidences the
judgment.

## Full-Audit Coverage

A full web-container audit covers every exported tag, trigger, user-defined
variable, custom template, built-in dependency, setup/teardown reference,
folder dependency, consent setting, and referenced configuration branch.

A full server-container audit additionally covers every client and
transformation. A web export with browser-to-server routing supports only a web
container audit plus routing observations. Do not claim the receiving server
container was audited without its clients, transformations, tags, triggers,
variables, and runtime or preview evidence.

Object coverage uses stable layer plus object ID. Names are fallback identity
only when the source has no ID. One matching name must not hide a missing object
with another ID.

## D1-D3 Contract

Depth is cumulative and mandatory for every configurable object in a full
audit:

- `D1`: identify layer, type, status, references, consumers, and firing scope.
- `D2`: state the object's specific business or technical role in this
  container and the contract expected by its consumers or vendor.
- `D3`: inspect every exported configuration branch and complete custom-code
  line; recursively trace references to terminal sources; state literal input,
  condition or transformation, output or side effect, actual consumers,
  sibling comparison, correctness judgment, and cleanup implication.

D3 must preserve object-specific functionality. `Returns a value`, `custom code
inspected`, `payload helper`, a hash, a URL list, or a category is not D3 proof.
For example, say that a variable reads the purchase event's `ecommerce.items`,
maps every `item_id` to a string array, and feeds Meta Purchase `content_ids`.

Every semantic row must be bound to:

- `object_key` as `layer:id`;
- exact source path and configuration hash;
- every configuration-branch anchor;
- every recursive reference trace;
- every actual consumer or explicit no-consumer evidence;
- every nonblank exported custom-code line hash for code objects.

The validator must reject generic prose, missing anchors, incomplete code-line
coverage, unresolved references, or D3 marked complete without source proof.
Only D4 runtime, vendor-platform, server-container, legal-owner, or
business-owner proof may remain deferred after D1-D3 is complete.

## Three Independent Lenses

Run and reconcile all three lenses:

1. `Deterministic hygiene`: exact/normalized duplicates, unused objects,
   missing references, invalid groups, naming/folder issues, outdated types.
2. `Semantic business logic`: event purpose, terminal values, timing, trigger
   scope, consent, official contract, sibling consistency, and object synergy.
3. `Technical code`: syntax/AST facts where available, complete line review,
   side effects, APIs, storage, network calls, dataLayer writes, asynchronous
   behavior, errors, security, and maintainability.

Every deterministic finding ID must receive a semantic resolution. Technical
facts must be linked where relevant. When technical and semantic results
conflict, block the operation until the conflict is explicitly resolved.

## Mandatory Semantic Comparisons

Compare values and conditions by terminal behavior, not variable name. Always
check:

- consent state pairs and sibling mappings, including analytics/ad storage;
- transaction ID, currency, order value, item arrays, item price, quantity,
  category, and product identifiers for ecommerce;
- media event names, IDs, values, currency, item formats, deduplication IDs,
  user data, and consent context against current official documentation;
- fixed-index arithmetic or product access, stale UA paths, and unnecessary
  GTM-side reconstruction of fields the dataLayer contract should supply;
- duplicate loaders, duplicate event tags, equivalent trigger conditions,
  equivalent variables, consolidation candidates, and newly obsolete objects;
- browser-to-server routing, transport URL, consent parameters, event routing,
  and browser/server duplicate risk;
- one-member trigger groups and all tags that must be remapped before deletion.

For every multi-field object, compare sibling fields. For every shared helper,
compare all consumers. Do not stop after each object is individually plausible;
evaluate whether the object graph is coherent as a whole.

## Official Documentation

Use `vendor-registry.toml` and `source-map.md` first. Validate registry freshness.
If a detected vendor/event family is absent or stale, search the current
official vendor documentation. Use official event names, required and
recommended fields, data types, payload structure, consent behavior, and
deduplication guidance as the default contract. Treat Google analytics events
as GA4/current Google tag unless the source proves a Universal Analytics case.

Document unsupported or undocumented vendor logic as a blocker or inference;
do not invent a platform contract.

## Operation Gate

Create an operation only when D1-D3 passes for the affected object graph and the
issue is confirmed. Each operation must include current behavior, concrete
problem, expected state, exact action, dependencies, preconditions, QA, rollback,
priority, confidence, blocker, route, aggressiveness, risk class, and execution
readiness.

Use `Standard` mutation by default. `Conservative` changes only low-risk hygiene.
`Deep` may consolidate or repair confirmed logic. `Transformational` may redesign
measurement architecture and requires explicit approval plus stronger QA. Audit
depth never becomes conservative.

Apply behavioral and dependency decisions before final naming. Adapt to the
dominant valid local convention, preserve understood acronyms, normalize
semantically equivalent prefixes, distinguish single triggers from trigger
groups, and keep every name unique within its object layer.

## Mutation Boundary

Never mutate without explicit approval. Ask whether the user wants direct GTM
API/MCP execution or importable container JSON.

For direct execution, create a dedicated workspace first. Warn and stop when the
workspace quota prevents safe isolation. Prefer in-place updates and real
deletions so GTM View Changes remains useful. Never publish, submit, or create a
version unless explicitly requested.

For JSON, generate a real GTM import artifact, not a Markdown plan. Choose the
route before editing. Preserve built-ins, folders, templates, object IDs where
the route supports them, setup/teardown links, and all references. Validate the
artifact and label it non-importable if any gate fails.

## Human Output

The cleanup plan and change log are separate deliverables produced at different
stages. The cleanup plan is post-audit and pre-execution. The change log is
post-execution or post-artifact generation; simulated changes must say
`Planned` or `Simulated`.

Cleanup plan workbooks use at most eight tabs by default, two visible tabs, and
no more than six useful columns per tab unless a concrete human task requires
more. Visible rows explain the problem, affected objects, impact, action,
priority, and QA in language usable by web analysts and marketing teams.
Detailed proofs remain available in consolidated hidden tabs, without repeated
columns, raw code, secrets, local paths, or machine-only scaffolding.

Use one detail row per distinct semantic problem. A summary row may introduce a
family, with visually adjacent detail rows. Exact duplicates, unused objects,
naming, and identical low-risk hygiene actions may be grouped when action, QA,
and rollback are the same.

Change logs use field-level evidence and approved operation IDs. They must let a
user understand what changed without opening GTM: object, field/dependency,
before, after, reason, QA/status, and operation link. Do not include unchanged
objects or templates.

## Completion Gate

Call a full audit or cleanup plan complete only when:

- source-model reference and coverage gates pass;
- every source object has a completed, source-bound D1-D3 row;
- all exported code lines and configuration branches are covered;
- every deterministic finding is reconciled;
- every operation is backed by a confirmed semantic judgment;
- official documentation gaps and D4-only blockers are explicit;
- workbook source coverage, strict evidence, formatting, and privacy gates pass;
- the final response states the concrete next action.

Otherwise label the execution `Incomplete / blocked` and name the exact failed
gate. Never replace missing work with confident wording.
