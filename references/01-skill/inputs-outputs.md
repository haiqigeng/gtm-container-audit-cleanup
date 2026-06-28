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
- measurement diagnosis evidence;
- semantic object matrix;
- custom code semantic review;
- official docs and vendor coverage map;
- QA plan;
- deferred blocker list;
- importable GTM JSON when explicitly requested;
- post-cleanup change log.

## Change Log Granularity

The change log must be granular enough for an end user to understand what was
modified without opening GTM View Changes.

Each applied or generated change should include:

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
