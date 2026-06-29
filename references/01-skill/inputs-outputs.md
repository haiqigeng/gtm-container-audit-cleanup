# Inputs And Outputs

Use this file to define what the skill needs and what it should produce.

## Inputs

Required or inferred inputs:

- GTM export JSON, GTM API evidence, GTM UI evidence, or screenshots;
- website domain and business model;
- web GTM, server-side GTM, or combined scope;
- CMP and consent assumptions when known;
- ecommerce, lead generation, media, publisher, SaaS, school, marketplace, or
  other business context;
- runtime evidence when available, such as Tag Assistant, browser/network
  traces, consent-state tests, screenshots, or vendor-platform diagnostics;
- requested mode: audit only, cleanup plan, direct cleanup, importable JSON,
  runtime QA, or change log.

## Outputs

Possible outputs:

- audit summary;
- cleanup action plan;
- source model coverage proof;
- planned change preview when requested before execution;
- measurement diagnosis evidence;
- semantic object matrix;
- custom code semantic review;
- official docs and vendor coverage map;
- QA plan;
- deferred blocker list;
- importable GTM JSON when explicitly requested;
- post-cleanup change log.

Lifecycle rules:

- `audit_cleanup_plan`: produced after the audit. It is a decision document for
  proposed changes, blockers, QA, and execution route.
- `planned_change_preview`: optional, produced only when the user asks to see
  what would change before execution.
- `change_log`: produced after cleanup execution or generated cleanup artifact
  creation. It is an execution record of what actually changed.

Do not integrate the change log into the cleanup plan by default. When the user
asks for both, produce separate deliverables. If no real cleanup was executed
but the user asks to act "as if" cleanup happened, label the file and status as
simulated or virtual, not as a verified GTM change log.

## Change Log Granularity

The change log must be granular enough for an end user to understand what was
modified without opening GTM View Changes.

After real cleanup execution or generated cleanup artifact creation, produce a
summary plus a detailed change log. The summary may group counts and outcomes;
the detailed change log must list one row per modified object, field,
dependency, trigger route, variable source, folder move, code/template change,
rename, deletion, creation, documented exception, or route-limited no-op.

Each applied or generated change detail row should include:

- change ID and linked operation ID;
- layer and object name/ID;
- action performed;
- before name, state, value, behavior, or dependency when relevant;
- after name, state, value, behavior, or dependency when relevant;
- reason for the change;
- business, measurement, consent, or maintainability impact;
- dependencies updated or affected;
- QA method and QA status;
- rollback note;
- owner, blocker, and status when incomplete.

Do not dump raw JSON or full configuration unless the change cannot be
understood without it. Put raw proof in technical tabs or appendices.
