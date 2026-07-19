# Business Architecture Run

This run asks whether complete object chains form the simplest useful
measurement architecture. It starts from source evidence and does not inherit
the other runs' conclusions.

## Contents

- Family construction
- Deterministic and open relationship discovery
- Family and comparison judgments
- Invisible defects and target architecture

## Family Construction

Create one family per configured event/business action when available. Otherwise
group by non-system execution route, then vendor/destination/type. Keep
singletons. Enrich families with source-derived scope tokens such as funnel
step, question, country, product range, consent state, or page/market condition.

For every family traverse recursively:

- member tags and active/paused state;
- firing and blocking triggers;
- trigger-group members;
- setup and teardown tags;
- custom templates;
- directly and indirectly referenced variables;
- destinations, endpoints, event names, and consent settings.

Create families for exported server clients and transformations as architecture
roots even when they do not connect to an outgoing tag through an explicit GTM
reference.

Assess every object in the resulting chain, not only the root tags. State its
configured chain role, business contribution, distinguishing logic, necessity,
status, and source anchors. Configuration Run 2 cannot be copied as this Run 3
business judgment.

Every member statement and every family/comparison conclusion must name the
generated evidence terms for that object or chain. Generic necessity or
architecture prose that could be reused for another container is incomplete.

Grouping by a name token alone is prohibited.

## Relationship Candidate Queue

Review every generated candidate:

- exact configuration or duplicate name;
- same tag payload with different routes;
- same vendor, destination, and event;
- same vendor/event with destination variants;
- cross-vendor implementation of one business event;
- shared firing trigger or related trigger scope;
- shared terminal variable source or shared inputs;
- identical custom code;
- normalized equivalent, near-equivalent, subset, or shared-step trigger logic;
- canonical funnel/question scope such as `Q1`, `question 1`, and `step 1`.

Candidate generation must preserve source paths, hashes, active/paused state,
and each member's evidence anchors.

The generated queue is a deterministic minimum, not a closed list. After it is
reviewed, perform one open discovery pass across every source object using:

- semantic name and business-term variants;
- normalized trigger conditions and execution routes;
- terminal source, formula, and output-shape overlap;
- shared consumers, destination, vendor, or event intent;
- consent, sequencing, and browser/server-route conflicts;
- funnel, question, journey, market, country, and product scopes.

Add every newly plausible relationship as a `DISC-*` comparison with source
object keys and evidence anchors. Record a source-complete discovery attestation
for all six methods. A zero-new-candidate result requires a concrete method and
coverage rationale, not `none found`.

The scaffold locks, for each method, its deterministic comparison IDs,
candidate objects, all-object review scope, and source-scope hash. The completed
method review must reproduce those fields, mark every candidate and source
object reviewed, and name source-derived comparisons, objects, or scope facts in
its conclusion. Do not substitute a subjective checklist or self-attested
coverage.

For sharded execution, complete deterministic family/comparison shards and the
separate open-discovery shard. The latter owns analyst-added `DISC-*` rows and
the final attestation. Merge must preserve source, context, and shared-fact
locks and cannot mark the run complete while the discovery shard is pending.

## Required Family Judgment

For each family and candidate, assess each member separately and then compare:

- literal role and business action;
- route and timing;
- trigger scope and exclusions;
- terminal input sources and formulas;
- output type, payload, destination, and deduplication key;
- consent, blocking, sequence, and browser/server role;
- consumers and downstream reporting/bidding use;
- product, market, country, page, funnel, or owner distinction;
- active, paused, rollback, and migration status;
- necessity and target architecture.

Choose one verdict: Exact duplicate, Functional overlap, Consolidation
candidate, Intentional variant, Complementary, Conflict, Unrelated, Owner
decision needed, or Container evidence limit.

## Common Invisible Defects

- several triggers represent the same funnel question through different names
  or event paths;
- a shared trigger causes two tags to send the same conversion;
- standard and custom purchase events duplicate revenue;
- one loader is repeated across tags or custom code;
- analytics and advertising consent outputs use the same condition by mistake;
- two variables share a source but transform or type it inconsistently;
- market/product variants differ only because naming drift hides one canonical rule;
- browser and server paths both send the same event without a deduplication key;
- individually correct objects are no longer needed by any current measurement objective.

## Target Architecture

Define canonical tags, triggers, variables, templates, consent helpers, and
folders. Preserve meaningful variants. Consolidation operations must identify
the canonical object, every consumer remap, non-canonical deletions, QA, and
rollback. Architecture decisions must align with sanitation before compilation.
