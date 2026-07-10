# Acceptance Criteria

Use this file to decide whether a skill execution is good enough to deliver.

## Contents

- Complete Result Criteria
- Configuration Logic Clarity
- Change Log Criteria
- Failure Criteria

## Complete Result Criteria

A complete audit or cleanup plan must show:

- scope, source evidence, and evidence freshness;
- a source model navigation map for in-scope objects, including inventory,
  dependency edges, field mappings, consumers, custom-code references, and
  unresolved edges;
- source model coverage gate status before deterministic, semantic, or
  technical cleanup lenses are trusted;
- deterministic cleanup baseline modules with zero-finding proof rows and
  nonzero finding IDs;
- recognized GTM system/internal references excluded from missing-reference
  anomalies;
- naming and route architecture standardization policy included in the cleanup
  plan, even when detailed rename candidates stay in hidden proof tabs;
- technical custom-code findings that include exact action, preconditions, QA,
  rollback, and handoff fields for every non-keep object;
- reconciliation of every deterministic finding into a cleanup operation,
  documented exception, runtime blocker, owner decision, or not-applicable row;
- measurement diagnosis for meaningful object families;
- a D1-D3 proof queue closed before findings and cleanup operations are
  finalized;
- recursive D1-D3 semantic review from available export/API/source evidence for
  every tag, trigger, variable, custom template, server client,
  transformation, and referenced configuration branch in a full audit;
- source-bound object keys, configuration hashes, source paths, branch hashes,
  code-line hashes, variable-chain requirements, and consumer keys that pass
  `gtm_semantic_review.py validate`;
- official documentation basis for material GA4, CMP, vendor, ecommerce, and
  server-side judgments;
- cleanup decisions for each material family: keep, fix, consolidate, delete
  candidate, defer, document exception, not applicable, or user-excluded;
- user-facing output that is concise, actionable, and coherent with proof tabs;
- next step that names the required approval, evidence, QA, or execution route.

## Configuration Logic Clarity

D1-D3 review is acceptable only when it demonstrates the object's actual
functionality. Generic proof that an object was checked does not count.

For every tag, trigger, variable, custom template, and referenced configuration
branch in a full audit, the review must explain:

- what the object is supposed to do;
- what input or source it uses;
- what condition, formula, mapping, trigger, template setting, or code logic it
  applies;
- what output, side effect, vendor payload, consent state, or firing behavior it
  produces;
- which tags, triggers, variables, custom code, or templates consume or depend
  on it;
- whether the functionality is coherent with the name, event context, business
  role, platform role, and official documentation.

Every exported configuration leaf must have its own source hash, logic role,
and object-specific interpretation. Every nonblank exported custom-code line
must have its own line hash, line number, and interpretation. Copying the list
of hashes or paths without those interpretations is a failed D3 review.

The source model may guide this review, but it does not replace source evidence.
Every cleanup finding must be checked against the raw export/API/config/code or
runtime evidence that supports it.

The review must recursively trace references. A tag field or trigger condition
that points to a GTM variable is not reviewed until the variable's source path,
code/configuration, return value, output type, and consumer expectation are
also reviewed. A variable that points to another variable, lookup table,
dataLayer path, built-in, URL/cookie/DOM source, or custom code must be traced
to that terminal source or to a D4-only runtime blocker.

The review must compare sibling fields and sibling objects. If two different
semantic outputs use identical or near-identical logic, such as two Consent Mode
signals using the same CMP purpose condition, the audit must surface it as a
finding, documented exception, or owner/D4 blocker.

The D1-D3 proof is not acceptable unless another analyst can read the matrix or
custom-code review row and understand the exact object functionality without
opening GTM. Each D3 row must state:

- literal behavior, such as `returns Date.now()` or `pushes e.data.payload to
  dataLayer when e.data.type is cta_tracking`;
- actual inputs and source paths;
- actual logic, formula, condition, template mapping, or code action;
- actual output or side effect and output type;
- actual consumers and expected consumer meaning;
- analyst judgment and cleanup implication.

A completed status with generic text is a failed execution. Categories such as
`payload transformer`, `computed value`, `vendor loader`, or `browser side
effect` may be used only after the literal behavior is stated.

For template-based tags and variables, the review must judge configuration
logic, not copy parameters. It must connect event name, trigger context,
template fields, variable values, expected data type or payload shape, consent
state, and vendor/platform purpose. If the template is a Google, CMP, media,
affiliate, publisher, or server-forwarding object, the review must compare the
configuration with the relevant official contract or document the missing
official source.

For custom code, the review must explain:

- what the code reads;
- what it writes, returns, pushes, loads, mutates, or calls;
- which variables or GTM objects it references;
- whether it interacts with DOM, cookies, storage, network calls, dataLayer,
  CMP, or vendor scripts;
- whether the behavior is safe, obsolete, duplicated, risky, or unclear;
- the exact technical cleanup action when action is `fix_required` or
  `consolidate_candidate`, such as replacing fixed ecommerce positions with
  item-array logic or replacing a helper with a lookup table;
- the preconditions, QA steps, rollback note, and handoff evidence needed for
  another analyst or agent to continue the work;
- what runtime QA is still needed when behavior cannot be proven from export
  evidence.

Unacceptable summaries include:

- `custom code inspected`;
- `configuration reviewed`;
- `no issue found`;
- `external URL detected`;
- `no obvious browser side effect`;
- `see config`;
- `static scan completed`;
- `D3 required`;
- `review later`.

## Change Log Criteria

A post-cleanup change log is acceptable only when:

- every applied/generated change has a row;
- a summary section or tab reports counts, validation status, blockers, rollback
  source, and next step;
- a detailed section or tab lists one modified object, field, dependency,
  trigger route, variable source, folder move, code/template change, rename,
  deletion, creation, documented exception, or route-limited no-op per row;
- each row explains what changed in human terms;
- before/after values are shown when they affect behavior, names, routing,
  dependencies, QA, or rollback;
- each row maps to a cleanup-plan operation ID;
- the user can understand what changed, why, and how to validate it without
  opening GTM View Changes.

Do not produce a real change log before cleanup execution. If the user requests
a hypothetical or test artifact, label it as a `planned change preview` or
`simulated post-cleanup change log`.

## Failure Criteria

Mark the deliverable `Incomplete / blocked` when:

- D1-D3 work is missing while source evidence is available;
- a full audit lacks D3 rows for tags, triggers, variables, or custom
  templates;
- the D1-D3 queue is unresolved or missing before cleanup operations are
  compiled;
- D3 stops at a variable/reference name instead of recursively tracing source
  logic and consumer meaning;
- sibling fields with duplicated or near-duplicated logic are not compared;
- measurement diagnosis is missing for meaningful affected families;
- source model coverage is missing, shallow, or treated as the evidence source
  instead of a navigation map;
- custom code is not inspected at export/config level;
- custom-code rows say only `simplify`, `harden`, or `review` without exact
  action, QA, rollback, and handoff evidence;
- deterministic cleanup findings are missing, unreconciled, or silently omitted
  from the cleanup plan;
- naming convention and route architecture are not represented in the cleanup
  plan;
- cleanup actions require future audit work to decide correctness;
- user-facing outputs are too generic to explain functionality or impact;
- D3 rows categorize objects without stating literal behavior and actual
  consumer context.
