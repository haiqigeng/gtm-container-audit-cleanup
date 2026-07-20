# Mutation Playbook

Never mutate or publish from an audit request alone.

## Contents

- Approval sequence
- Source-integrity and layer-complete readback
- Direct GTM/API/MCP
- Import JSON
- Custom code
- Consent and server routing
- Validation and stop conditions

## Approval Sequence

1. Deliver audit and cleanup plan.
2. Ask for route: direct GTM/API/MCP or import JSON.
3. Ask for aggressiveness.
4. Confirm approved operation IDs, rollback export, and blockers.
5. Execute only approved operations.

Audit depth is independent of this choice.

Each approved operation carries a minimum safe aggressiveness. Operations above
the selected level stay visible as deferred and must not be sent to GTM or the
generated import container.

## Direct GTM/API/MCP

Preferred when human-readable GTM View Changes matters.

- Create a new dedicated workspace before mutation.
- Free GTM accounts may permit only three total workspaces, including the
  default. Warn and stop before cleanup when quota prevents creation.
- Modify existing objects in place when possible; preserve IDs and history.
- Create a new object only when the target architecture genuinely needs one;
  this includes first-class Zone and Google tag configuration entities when an
  approved target design requires them.
- Batch changes by dependency-safe operation, then read back and validate.
- Delete only after every consumer is remapped and read back.
- Never work in or publish the default/live workspace without explicit request.

Recommended dependency order:

1. confirm canonical objects and business-specific names;
2. create approved terminal variables, tags, triggers, or templates;
3. add missing fields/list members and apply exact logic changes;
4. update tags and triggers that consume them;
5. flatten groups and sequencing safely;
6. apply final naming and folders;
7. delete obsolete objects;
8. full readback and future-state validation.

## Import JSON

Create a real GTM container import JSON, never Markdown JSON or a partial object
list presented as importable.

Generate it from the simulated complete future export, then validate the full
effective container before delivery.

Import behavior may delete/recreate templates, tags, triggers, or variables and
can pollute View Changes. Same-container identity matching is not a reliable
substitute for direct in-place mutation. Choose overwrite/merge behavior
explicitly and explain the route.

Preserve:

- export wrapper and required metadata;
- enabled built-in variables;
- all referenced custom templates;
- clients, transformations, Zones, and Google tag configurations;
- folders and parent IDs;
- setup/teardown references;
- system trigger references;
- complete effective object graph.

For user-requested same-container review artifacts, validate the merged effective
container and warn that GTM may still recreate objects. Do not promise clean View
Changes from JSON.

## Custom Code

- Preserve exact GTM variable references unless the approved operation remaps them.
- Never replace a custom-JavaScript reference with an unrelated hardcoded value.
- Recheck escaping, output type, consent, DOM/storage/network behavior, and
  consumers after any edit.
- Prefer a native GTM feature or maintained template only when behavior and
  permissions remain equivalent.

## Consent And Server Routing

Consent, conversion value, transaction IDs, user data, media payloads, and
browser/server routing are high-impact. Require official-contract evidence,
challenge review, and exact readback. Do not change a web Google tag solely
because its measurement ID is absent when the export proves server-managed routing.
Do not add client blocking solely because transporter tags fire on every event
when the approved design forwards complete consent state for server-side
enforcement. Preserve and read back the forwarding parameter/variable chain;
change it only when the approved operation identifies a concrete gap.

## Validation And Stop Conditions

After each batch:

- verify that the readback is still a complete ContainerVersion with no
  malformed or unmodeled entity layer and no missing or duplicate object ID;
- fetch/read back changed objects;
- compare exact fields with approved structured actions;
- check references, names, templates, groups, built-ins, Zones, Google tag
  configurations, and consumers;
- update the field-level change record;
- preserve rollback instructions.

Stop immediately on workspace drift, unexpected object recreation, missing
reference, template mismatch, unapproved consent/value change, unknown business
token, API partial failure, or future-state gate failure.

Never publish or create a version unless separately and explicitly requested.
