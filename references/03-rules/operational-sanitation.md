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
- variable references, including code and template fields;
- firing/blocking trigger IDs and trigger-group members;
- setup/teardown tag names;
- folder IDs and custom-template IDs;
- built-in and GTM system references distinguished from missing objects;
- clients and transformations included for server containers.

## Lifecycle And Usage

- active tags versus paused tags;
- every paused tag retained for rollback, migration, or decommission review;
- objects consumed only by paused tags;
- unused variables, triggers, templates, and folders;
- server-client and transformation status, filter scope, and exported reachability
  signals without labelling server roots "unused" merely because they have no
  browser-style consumer edge;
- tags with no firing trigger, excluding tags genuinely invoked through setup or
  teardown sequencing;
- scheduled, paused, rollback, and owner-exception status where exported;
- no deletion based only on age or lack of a visible firing trigger.

After every consolidation design, recompute consumers and unused objects.

## Exact And Structural Duplication

- duplicate names within each GTM layer;
- exact configurations after removing identity/export metadata;
- same tag payload with different routes;
- identical dataLayer paths;
- identical normalized custom code;
- duplicate custom templates, clients, and transformations;
- built-in wrapper variables;
- duplicate destination/event configurations recorded for architecture review.

An exact signature proves sameness of exported configuration, not sameness of
business purpose. Architecture must confirm consolidation.

## Trigger Structure And Lint

- empty, one-member, duplicate-member, nested, and cyclic trigger groups;
- invalid regular expressions and universally permissive patterns;
- duplicate conditions inside one trigger;
- contradictory equals/not-equals logic;
- complex condition sets needing simplification review;
- blocking triggers whose exact event cannot occur on the firing route;
- exact, normalized, near-equivalent, and subset conditions supplied to the
  architecture candidate queue.

For one-member groups, remap every consuming tag/group to the child before
deleting the group.

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

## Legacy And Destination Inventory

- Universal Analytics tag types, property IDs, parameters, event names, and old
  ecommerce paths;
- fixed product positions and old product-array assumptions;
- vendor, destination/account/pixel IDs, endpoints, and external script hosts;
- web-to-server transport endpoints and exported consent-forwarding variables
  identified without judging unseen server behavior or treating an absent
  client blocker as a defect by itself;
- fixed numbered-slot formulas and aggregate expressions inventoried for
  configuration review;
- distinct consent-purpose variables or routes sharing identical logic queued
  for configuration and architecture review.

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
