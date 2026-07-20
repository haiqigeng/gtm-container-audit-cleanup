# Acceptance Criteria

An audit and cleanup plan is complete only when all criteria below pass.

## Contents

- Source and scope integrity
- Independent run acceptance
- Reconciliation and cleanup safety
- Human output and automatic failure

## Source And Scope

- The source export hash is locked and every in-scope source object is inventoried.
- The source is a valid ContainerVersion (wrapped or direct), every recognized
  entity layer is an array, every object has a unique layer ID, and no unknown
  entity-like top-level layer is silently ignored. A failure blocks all three
  semantic reviews and mutation compilation.
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
- Business/journey inference uses reachable behavior; orphan logic remains
  auditable but cannot redefine context. A server-routing host does not imply
  Google tag gateway without an explicit exported gateway signal.

## Run 1: Operational Sanitation

- All 48 locked mandatory modules record findings or a source-counted zero
  result; the validator uses an independent fixed module registry.
- Broken references, active/paused lifecycle, unused objects, exact duplicates,
  duplicate paths/code, trigger groups, trigger lint, folders, built-ins,
  naming, legacy setup, templates, sequencing, schedules/firing controls,
  Zones, consent shape/enums, and destination inventory are covered.
- Payload-equivalence signatures exclude route, consent, sequence, schedule,
  priority, pause, and firing controls; equal payloads on different routes and
  same event/destination contracts with different consent controls remain
  mandatory candidates.
- Reachability starts at active direct tags and configured Zone/client/Google-
  tag/transformation roots and traverses recursive variable, trigger-group,
  tag-sequence, template, and built-in dependencies. An orphan cycle does not
  make itself used.
- Every finding has one explicit disposition. No finding disappears because a
  later run did not mention it.
- A nonzero deterministic finding is resolved by cleanup, a visible owner
  decision, or a source-locked owner exception that identifies the finding,
  signature, or object and whose reason is preserved. It is never dismissed as
  not applicable or as a container-evidence limit.
- One-member trigger groups identify the child, every consumer remap, and the
  safe deletion order; they cannot be absorbed into a generic trigger batch.
  A nested/cyclic dependency is resolved before any flattening, and malformed
  scalar values remain invalid even when they resemble a valid member.
- Unresolved references remain operational findings while the rest of the
  scannable container continues through all runs.
- A consumed object cannot be deleted unless accepted remaps cover every
  surviving consumer, including coverage spread across several remap records.
- Remaps cannot cross layers, target an object selected for deletion, or create
  a dependency cycle. The accepted operation set introduces no duplicate final
  object name within a GTM layer.

## Run 2: Configuration Correctness

- Every tag, trigger, variable, Zone, custom template, server client, Google tag
  configuration, and transformation has one source-bound review.
- Every semantic statement cites only the generated source paths relevant to
  that field and names source-derived behavior facts; citations plus generic
  prose fail.
- Every object completes the exact generated D3 cross-check set for
  purpose/output, execution/scope, input/output/consumer, consent/sequence, and,
  when applicable, custom-code behavior and official-vendor-contract alignment.
  Every failed check links to a concrete defect.
- Every exported logic leaf is covered exactly once by path, value hash, logic
  role, configured effect, and correctness verdict.
- Object rows, branch paths, D3 keys, contract topics, technical findings,
  recursive trace identities, and parser segment hashes are unique, nonblank,
  well-formed, and covered exactly once; duplicate rows cannot overwrite.
- Empty dictionaries/lists remain explicit leaves. Trigger and sequence routes
  expose recursive target conditions, paused/missing/ambiguous/cyclic states,
  and downstream consumer-contract facts when D3 depends on them.
- Dependency rows preserve exact consumer event/destination contexts and
  configured-destination peers, including peer type/absence, server route,
  consent, and execution controls without assuming inheritance. Visible
  malformed, missing, cyclic,
  invalid-control, opaque, and unproven-contract states create locked
  verdict/branch/D3/defect/official-topic obligations that a completion cannot
  contradict; affected D3 conclusions name the exact obligation.
- Every variable reference is recursively traced node by node and hop by hop to a dataLayer path, built-in,
  constant, URL/cookie/DOM source, lookup, code branch, missing reference, or
  cycle. Each node states literal function, output type/shape,
  availability/fallback, and consumer compatibility.
- Duplicate custom-variable names and custom/built-in name collisions retain
  every candidate and terminate as `ambiguous`; a Correct verdict cannot pass.
- Every custom-code nonblank line is covered exactly once in concrete behavior
  blocks. Static parser/security findings are each resolved explicitly.
- Missing or failed optional JavaScript parsing creates a mandatory coverage
  limit that cannot be dismissed as a false positive. Any accepted exception
  identifies the substitute line-by-line review and does not claim AST coverage.
  Any GTM-substitution normalization used for structural parsing is disclosed,
  and a bare `{{Variable}}` return never acquires an invented output type.
- Parser fallback attests every exported code-segment hash and source-specific
  per-segment behavior, so one segment's identifiers cannot attest another.
  Source-visible behavior is polarity-locked: token-rich prose that denies a
  proved send, request, DOM/script effect, dataLayer/storage action, listener,
  read, or return fails. Source-proven health/security signals cannot be
  dismissed as false positives or relabeled generically: cleanup, exception,
  and owner-decision verdicts require their source-bound action, exception
  basis, or question respectively.
  Metadata-only custom-template resources remain opaque and
  cannot be marked Correct by inferred implementation behavior.
- Vendor-facing objects and their consumed variables complete every generated,
  current official documentation topic for event, destination, fields, value
  types, payload shape, consent, route, and deduplication where applicable.
- Each applicable vendor topic distinguishes known non-compliance, unproven
  container/runtime state, and current-source review; `Not applicable` cannot
  replace missing proof. Versioned unsupported events and replacements are
  registry-validated review cues, never guessed automatic migrations.
- Unclassified external scripts, hosts, and templates create mandatory
  vendor-identification and official-source research obligations. A found
  source/domain must be added to the versioned registry, validated, and the
  review rebuilt; the topic remains Unproven before that binding.
- Mixed-integration objects retain every matched vendor context, and each
  unmatched external host creates its own research obligation.
- Vendor and host inference excludes export/UI metadata, while explicit
  recognized server-transport endpoints remain in the server-routing contract
  rather than becoming false unknown-vendor obligations.
- The purpose is literal and object-specific. `Returns Date.now()` is acceptable;
  `outputs a value` is not. `Maps ecommerce.items[].item_id to Meta content_ids`
  is acceptable; `payload transformer` is not.
- A confirmed branch, code, or vendor-contract issue is linked to a concrete
  defect and exact operation or one precise unresolved decision.
- Formula and output-shape signals are resolved explicitly. Fixed numbered-slot
  aggregation cannot be marked correct without a specific business rule and
  cardinality proof.
- GA4 purchase/refund reviews contain explicit transaction-ID obligations. A
  missing exported `transaction_id` cannot validate as contract-compliant.
- Consent is assessed as one effective route across native settings,
  additional checks, firing/blocking logic, variables, sequence, and visible
  server routing. Distinct consent purposes using the same logic are reviewed.
  A server-enforced transport is not failed for missing client blocking when
  the export proves the endpoint, forwarded consent parameter/variable chain,
  event-time source, purpose coverage, and transporter coverage. The review
  distinguishes an aligned web-side forwarding contract from the separate,
  unseen server-enforcement boundary.
  Consent-looking names/events and arbitrary blockers remain candidates, not
  proof. Forwarding requires an exported server route plus payload/settings
  evidence, and mixed code retains every detected vendor.

## Run 3: Business Architecture

- Every tag, Zone, Google tag configuration, and exported server client/
  transformation root belongs to a business family, including singletons.
- Every family contains its source-derived tag, firing/blocking trigger,
  trigger-group, sequenced-tag, template, and recursive variable chain.
- Every generated exact, near, shared-source, shared-route, shared-event,
  destination, code, condition-subset, and business-step candidate has an
  explicit source-bound relationship verdict.
- Zones sharing child-container public IDs and tags/Google tag configurations
  sharing destination values are deterministic comparison obligations.
- Trigger-group cycles, cross-vendor business events visible in custom code,
  same-contract consent/sequence/server-route variants, and unresolved family
  dependency edges remain explicit comparison or chain evidence.
- A routed Google tag configuration, same-destination Google event tag, and
  same-business-event direct media/browser tag form a browser/server consent,
  terminal-source, payload, and deduplication comparison when source facts
  support the join.
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
- Every `DISC-*` row declares at least one mapped comparison type plus its exact
  discovery method(s), is attributed in exactly those method reviews, uses
  methods suitable for its relationship class, and inherits deterministic
  unsafe-class policy and negative caution
  states across candidate subsets and supersets or from its own declared type.
- Retention verdicts cite a source-visible distinction for every member.
  Verdict/disposition pairs are coherent, owner decisions contain one precise
  interrogative question, and zero-discovery rationales name every method plus
  source facts.
- Unsafe same-payload/different-route, shared-Zone-child, trigger-cycle, and
  browser/server consent/deduplication candidates cannot receive a generic
  `Keep`. Visible deterministic relationships cannot be hidden wholly behind a
  container-evidence limit.
- An actionable verdict contains a structured operation that affects a
  relationship member's behavior; unrelated, name-only, no-op, or object/path-
  mismatched changes do not count. Unsafe owner questions identify at least two
  actual members and put the route/scope/cycle/consent/deduplication decision in
  the question itself. Absent runtime deduplication or consent parity is stated
  with unresolved/negative polarity rather than claimed complete, guaranteed,
  identical, synchronized, verified, equivalent, or otherwise proven.

## Reconciliation And Cleanup Safety

- All three runs have status `complete` against the same source hash.
- Contradictory decisions block compilation. Operational consolidation requires
  an aligned architecture operation on the same objects.
- Behavior-changing edits, additions, remaps, deletions, and creations are
  blocked when their architecture family/comparison is preserved or unresolved;
  names, notes, export metadata, and folder placement are treated separately as
  metadata operations.
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
- Import/readback and change-log sources pass the same unique-ID/entity-layer
  integrity checks, including Zones and Google tag configurations, before a
  field-level diff is trusted.

## Automatic Failure

Mark the result `Incomplete / blocked` if any required object, logic leaf, code
line, recursive trace, family, candidate, open-discovery method, operational
finding, official contract, decision-ledger row, or three-run gate remains
pending while its source evidence is available.
External behavior outside the container may be stated as a container-evidence
limit, but it cannot excuse unreviewed exported configuration.
