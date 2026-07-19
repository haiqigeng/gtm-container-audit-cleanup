# GTM Container JSON Guide

Use structured JSON parsing. Never audit a GTM export by regular-expression
search alone.

## Contents

- Root shapes and typed parameters
- References, edges, and source-bound facts
- Tags, triggers, variables, code, and templates
- Web/server scope and import artifacts

## Root Shapes

A standard export normally stores objects under `containerVersion`. Some API or
test artifacts expose the version object directly. Normalize both shapes before
analysis and preserve the original wrapper for generated artifacts.

Common layers:

| Layer | ID field |
| --- | --- |
| tag | `tagId` |
| trigger | `triggerId` |
| variable | `variableId` |
| folder | `folderId` |
| custom template | `templateId` |
| built-in variable | `name` |
| server client | `clientId` |
| transformation | `transformationId` |

Read account/container IDs, public ID, usage context, export/version metadata,
and custom-template references from the export instead of asking the user when
already available.

## Parameters

GTM parameters are typed trees, not a flat dictionary. Values may appear in:

- `value` for scalar/template values;
- `list` for ordered items;
- `map` for key-value entries;
- nested parameters inside list/map values.

Preserve type, key, order, and nested shape. A list of item objects is not
equivalent to a scalar string containing JSON.

## References And Edges

Extract `{{Variable Name}}` from every string field, including code and nested
maps. Build edges for:

- tag/trigger/variable/template references;
- firing and blocking triggers;
- trigger-group members;
- setup and teardown tag names;
- parent folders;
- custom-template type IDs;
- clients and transformations where exported.

Recognize GTM internal references such as `{{_event}}` and high-range system
trigger IDs. Built-in variables terminate a recursive trace and are not missing
custom variables.

## Source-Bound Facts

For every configurable object retain:

- `layer:id` object key;
- name, type, active/paused status;
- stable configuration hash after removing export metadata;
- exact source JSON path;
- leaf paths, value hashes, safe previews, and referenced variables;
- consumers and relation paths;
- code line number/hash/preview where applicable.

These fields are immutable in completed reviews. A changed value or source hash
invalidates reuse.

## Tag Routes

Do not label a tag triggerless until checking:

- `firingTriggerId` and system routes;
- whether another tag invokes it through `setupTag` or `teardownTag`;
- paused/scheduled state;
- server-container semantics when the object is a server tag.

Blocking triggers, setup/teardown sequence, priority, consent settings, and
event parameters all contribute to execution logic.

## Trigger Conditions

Read all filter families and nested parameter nodes. Normalize operator, left
input, right value, case/modifier flags, and regex literals. Convert only
provably equivalent anchored/contains regex patterns for comparison; keep the
raw source as evidence.

Trigger groups require member expansion and cycle checks. A group is not a
simple OR: preserve GTM group semantics when designing cleanup.

## Variables

Inspect variable type and all fields. For data-layer variables record path and
dataLayer version. For lookup/regex tables retain every row, default, matching
mode, and input variable. For URL/cookie/DOM/auto-event variables record the
exact source and output expectation. For custom JavaScript inspect all code.

Recursion ends at a concrete configured terminal or explicit missing/cycle
state, never at another variable's name.

For every recursive node retain its configuration hash, source branches,
downstream hop, literal configured function, output type/shape, fallback and
event availability, and compatibility with the consuming object.

## Custom Code And Templates

Custom HTML code usually lives in parameter `html`; Custom JavaScript in
`javascript`; custom-template source in `templateData`. Preserve all nonblank
lines and hashes. Extract URLs, scripts, GTM references, dataLayer use, browser
storage, cookies, DOM operations, listeners, network calls, globals, return
shape, and parser facts without treating static signals as final judgments.

## Web And Server Containers

Use `usageContext` and object layers to classify scope. In web exports identify
transport/server container URLs and consent parameters but do not infer unseen
server forwarding. In server exports include clients, transformations,
request-claiming configuration, server tags, event-data mappings, permissions,
and outgoing endpoints.

## Full Exports And Patches

A cleanup plan operates on a full source graph. Same-container import patches
have special identity/template/built-in behavior and may recreate objects.
Validate the effective merged container, not the patch fragment alone. Never
call a JSON import-ready until IDs, references, templates, built-ins, groups,
folders, and route-specific churn pass validation.
