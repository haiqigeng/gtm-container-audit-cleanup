# Acceptance Criteria

An audit and cleanup plan is complete only when all criteria below pass.

## Contents

- Source and scope integrity
- Independent run acceptance
- Reconciliation and cleanup safety
- Human output and automatic failure

## Source And Scope

- The source export hash is locked and every in-scope source object is inventoried.
- Provided and inferred context is persisted with unresolved questions and a
  stable context hash.
- Context and shared-fact content are deterministically reconstructed at the
  package gate; copied matching hash strings cannot hide changed content.
- One judgment-free deterministic fact artifact contains object identity,
  references, consumers, raw leaves, terminal sources, trigger logic, formula
  signals, consent routes, and behavior signatures.
- All three reviews bind to the same source, context, and shared-fact hashes.
- Built-in/system references are distinguished from missing references.
- Web, server, consent, ecommerce, and business scope are stated without
  claiming evidence from an unseen container or live website.

## Run 1: Operational Sanitation

- Every mandatory module records findings or a source-counted zero result.
- Broken references, active/paused lifecycle, unused objects, exact duplicates,
  duplicate paths/code, trigger groups, trigger lint, folders, built-ins,
  naming, legacy setup, templates, sequencing, and destination inventory are
  covered.
- Every finding has one explicit disposition. No finding disappears because a
  later run did not mention it.
- A nonzero deterministic finding is resolved by cleanup, a visible owner
  decision, or a source-locked owner exception that identifies the finding,
  signature, or object and whose reason is preserved. It is never dismissed as
  not applicable or as a container-evidence limit.
- One-member trigger groups identify the child, every consumer remap, and the
  safe deletion order; they cannot be absorbed into a generic trigger batch.
- Unresolved references remain operational findings while the rest of the
  scannable container continues through all runs.

## Run 2: Configuration Correctness

- Every tag, trigger, variable, custom template, server client, and
  transformation has one source-bound review.
- Every semantic statement cites only the generated source paths relevant to
  that field and names source-derived behavior facts; citations plus generic
  prose fail.
- Every object completes the exact generated D3 cross-check set for
  purpose/output, execution/scope, input/output/consumer, consent/sequence, and,
  when applicable, custom-code behavior and official-vendor-contract alignment.
  Every failed check links to a concrete defect.
- Every exported logic leaf is covered exactly once by path, value hash, logic
  role, configured effect, and correctness verdict.
- Every variable reference is recursively traced node by node and hop by hop to a dataLayer path, built-in,
  constant, URL/cookie/DOM source, lookup, code branch, missing reference, or
  cycle. Each node states literal function, output type/shape,
  availability/fallback, and consumer compatibility.
- Every custom-code nonblank line is covered exactly once in concrete behavior
  blocks. Static parser/security findings are each resolved explicitly.
- Vendor-facing objects and their consumed variables complete every generated,
  current official documentation topic for event, destination, fields, value
  types, payload shape, consent, route, and deduplication where applicable.
- Unclassified external scripts, hosts, and templates create mandatory
  vendor-identification and official-source research obligations.
- The purpose is literal and object-specific. `Returns Date.now()` is acceptable;
  `outputs a value` is not. `Maps ecommerce.items[].item_id to Meta content_ids`
  is acceptable; `payload transformer` is not.
- A confirmed branch, code, or vendor-contract issue is linked to a concrete
  defect and exact operation or one precise unresolved decision.
- Formula and output-shape signals are resolved explicitly. Fixed numbered-slot
  aggregation cannot be marked correct without a specific business rule and
  cardinality proof.
- Consent is assessed as one effective route across native settings,
  additional checks, firing/blocking logic, variables, sequence, and visible
  server routing. Distinct consent purposes using the same logic are reviewed.
  A server-enforced transport is not failed for missing client blocking when
  the export proves the endpoint, forwarded consent parameter/variable chain,
  event-time source, purpose coverage, and transporter coverage. The review
  distinguishes an aligned web-side forwarding contract from the separate,
  unseen server-enforcement boundary.

## Run 3: Business Architecture

- Every tag and exported server client/transformation root belongs to a business
  family, including singleton families.
- Every family contains its source-derived tag, firing/blocking trigger,
  trigger-group, sequenced-tag, template, and recursive variable chain.
- Every generated exact, near, shared-source, shared-route, shared-event,
  destination, code, condition-subset, and business-step candidate has an
  explicit source-bound relationship verdict.
- Each family member and every tag/trigger/variable/template/client/
  transformation in its chain has active/paused state, configured role,
  necessity, distinguishing configuration, and source evidence assessed.
- The family verdict explains execution path, payload, consent/sequence,
  necessity, ownership, and target architecture.
- Similar names or a numeric similarity score never prove duplication.
- Generated candidates are the minimum queue, not the discovery boundary. The
  completed review contains an open-discovery attestation covering every source
  object across semantic names, conditions/routes, terminal sources/formulas,
  consumers/destinations/events, consent/sequence/server paths, and business
  scopes. Newly found candidates appear as source-bound `DISC-*` rows.
- Sharded architecture reviews complete and merge the dedicated discovery shard
  and its attestation under the same source, context, and shared-fact locks.
- Every open-discovery method preserves its generated candidate IDs,
  all-object scope, and source-scope hash, and its conclusion names
  source-derived objects or comparisons rather than self-attesting coverage.

## Reconciliation And Cleanup Safety

- All three runs have status `complete` against the same source hash.
- Contradictory decisions block compilation. Operational consolidation requires
  an aligned architecture operation on the same objects.
- Operations with identical complete structured mutations may reconcile despite
  independent wording or keys; every lens rationale remains preserved. One key
  reused for different mutations fails.
- Every creation, missing-field/list addition, change, remap, deletion, and
  rename names exact source or planned objects and consumers; consolidation
  names one canonical object.
- Future-state simulation creates no new missing reference, duplicate ID,
  orphan, folder, trigger, or naming finding and resolves every operational
  finding selected for cleanup.
- Audit depth never changes with mutation aggressiveness.
- Every operation declares a mechanically validated minimum aggressiveness;
  operations above the selected level remain visible as deferred and do not
  enter future-state execution.
- The decision ledger contains every source obligation exactly once and links
  every cleanup disposition to a compiled operation.
- Projected before/after/delta counts exist for every GTM object layer and do
  not show unexplained broad deletion or recreation.

## Human Output

- The cleanup workbook has at most eight tabs and six columns per tab.
- Only `01 Summary` and `02 Cleanup Plan` are visible; hidden proof tabs remain
  available by unhiding.
- Each distinct actionable issue has its own row. Exact duplicate, unused,
  naming, and other homogeneous hygiene batches may share one row.
- Deferred operations, owner decisions, and container-evidence limits remain
  visible, and Summary does not claim readiness while owner action is pending.
- Visible text states problem, affected objects, impact, exact action, priority,
  readiness, and QA in web-analyst language without raw dumps or internal gates.
- Cleanup plan and change log remain separate.
- Every change-log tab uses six or fewer columns and preserves one field-level
  row per actual difference without duplicating the same payload under aliases.
- Every completed stage ends with one concrete next action.
- Formula-like cells are escaped as literal text, and privacy checks cover
  hidden as well as visible proof tabs.
- No visible or hidden proof cell is silently truncated. Overlong proof is
  continued losslessly in adjacent hidden rows; overlong visible text fails the
  workbook build until it is rewritten concisely.
- Executed change-log rows link to approved operations only when exact object,
  field, action, before, and after values match.

## Automatic Failure

Mark the result `Incomplete / blocked` if any required object, logic leaf, code
line, recursive trace, family, candidate, open-discovery method, operational
finding, official contract, decision-ledger row, or three-run gate remains
pending while its source evidence is available.
External behavior outside the container may be stated as a container-evidence
limit, but it cannot excuse unreviewed exported configuration.
