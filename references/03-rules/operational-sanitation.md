# Operational Sanitation Run

This run is mechanical, exhaustive, and independent. It creates review
obligations, not automatic deletions.

## Contents

- Integrity
- Lifecycle and usage
- Exact and structural duplication
- Trigger structure and lint
- Folders and naming
- Legacy and destination inventory
- Mandatory result

## Integrity

- valid GTM export shape and unique object IDs;
- wrapped or direct ContainerVersion identity, locked current entity layers,
  array/object shape, and no silently ignored future entity-like layer;
- variable references, including code and template fields;
- firing/blocking trigger IDs and trigger-group members;
- setup/teardown tag names;
- folder IDs and custom-template IDs;
- built-in and GTM system references distinguished from missing objects;
- Zones, Google tag configurations, clients, and transformations included when
  exported.

## Lifecycle And Usage

- active tags versus paused tags;
- every paused tag retained for rollback, migration, or decommission review;
- objects consumed only by paused tags;
- unused custom and enabled built-in variables, triggers, templates, and folders;
- active-root reachability through recursive variables, built-ins, trigger
  groups, setup/teardown tags, templates, and Zone boundary triggers; an orphan
  cycle remains unused;
- server-client and transformation status, filter scope, and exported reachability
  signals without labelling server roots "unused" merely because they have no
  browser-style consumer edge;
- tags with no firing trigger, excluding tags genuinely invoked through setup or
  teardown sequencing;
- scheduled, paused, rollback, and owner-exception status where exported;
- malformed/reversed schedules, unknown firing options, malformed or ambiguous
  sequence targets, sequence role conflicts, paused targets, and cycles;
- no deletion based only on age or lack of a visible firing trigger.

After every consolidation design, recompute consumers and unused objects.

## Exact And Structural Duplication

- duplicate names within each GTM layer;
- exact configurations after removing identity/export metadata;
- export/workspace URLs, notes, and folder placement excluded from behavioral
  duplicate signatures so UI metadata cannot hide equal logic;
- same tag payload with different routes;
- payload normalization excludes firing/blocking routes, setup/teardown,
  schedule, firing option, priority, pause, consent, monitoring, and related
  controls so those differences do not suppress the candidate;
- identical dataLayer paths;
- identical normalized custom code;
- duplicate custom templates, clients, and transformations;
- built-in wrapper variables;
- duplicate destination/event configurations recorded for architecture review.
- identical event/destination contracts with different visible consent-control
  shapes recorded for configuration and architecture review.

An exact signature proves sameness of exported configuration, not sameness of
business purpose. Architecture must confirm consolidation.

## Trigger Structure And Lint

- malformed, empty, one-member, duplicate-member, nested, and cyclic trigger
  groups;
- invalid regular expressions and universally permissive patterns;
- duplicate conditions inside one trigger;
- contradictory equals/not-equals logic;
- complex condition sets needing simplification review;
- blocking triggers whose exact event cannot occur only when every firing route
  has a provable exact event constraint; mixed/unknown routes are not inferred;
- exact, normalized, near-equivalent, and subset conditions supplied to the
  architecture candidate queue.

For one-member groups, name every consuming tag/group/Zone and the exact child.
When the child is another group or participates in a cycle, resolve that
dependency first; only an acyclic route may be remapped before deletion.
Malformed scalar members remain invalid edges, while collisions with valid
member values stay visible as likely authoring mistakes.

The one-member-group finding must survive reconciliation as its own decision
ledger entry. It is complete only when every consumer is remapped before the
group deletion.

## Folders And Naming

- empty, singleton, overloaded, and unfiled structures;
- dominant local naming order and meaningful acronyms;
- inconsistent object-type prefixes, case, separators, scope, country/product,
  consent-blocking roles, and duplicate proposed names;
- unique final names within each GTM layer.

Naming proposals remain provisional until behavior, canonical objects, and
business-specific prefixes are understood.
When neither an approved policy nor a reliable dominant local convention
exists, create one visible naming-policy owner decision instead of declaring
every object nonconforming to an invented default. Generate the complete rename
set only after that decision and after consolidation/remaps are settled.

## Legacy And Destination Inventory

- Universal Analytics tag types, property IDs, active UA parameters, corroborated
  event names, and old ecommerce paths; a media event such as `AddToCart` or an
  unrelated false-valued `enhancedEcommerce` field is not UA evidence alone;
- fixed product positions and old product-array assumptions;
- vendor, destination/account/pixel IDs, endpoints, and external script hosts;
- export/UI metadata URLs excluded from destination and vendor inference, and
  every matched vendor retained for mixed custom code;
- web-to-server transport endpoints and exported consent-forwarding variables
  identified without judging unseen server behavior or treating an absent
  client blocker as a defect by itself;
- fixed numbered-slot formulas and aggregate expressions inventoried for
  configuration review;
- distinct consent-purpose variables or routes sharing identical logic queued
  for configuration and architecture review.
- Zone child containers, boundary/type-restriction shapes, duplicate children,
  unbounded scope, and empty enabled allowlists;
- manual-consent setting shape and official `notSet`/`notNeeded`/`needed` enum
  semantics, with unknown values kept as findings rather than normalized away.
- blockers recorded as control candidates until trigger overlap proves that
  they can affect the tag; consent-looking names/events do not prove forwarding.

## Mandatory Result

Each module records object count, zero/findings status, stable finding ID,
source objects, deterministic evidence, and one explicit disposition. A later
run may justify an exception but cannot remove the record.

A nonzero deterministic finding must be resolved by a cleanup operation, a
visible owner decision, or a documented owner exception already present in the
source-locked intake context. The exception must identify the finding ID,
signature, or affected object and provide a specific reason; the review
rationale must preserve that reason. `not_applicable` and
`container_evidence_limit` are not valid ways to dismiss a nonzero sanitation
finding.

Deleting a consumed object requires the accepted remap set to cover every
surviving consumer. Several remap records may jointly provide that coverage;
consumers deleted in the same accepted operation set do not require remapping.
Every remap stays within its supported GTM layer, targets an object that
survives the accepted operation set, and is rejected when the resulting
consumer graph introduces a cycle. Apply all accepted renames, creations, and
deletions as one name model and reject any newly duplicated final name within a
layer.
