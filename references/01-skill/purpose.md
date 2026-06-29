# Purpose

Use this file to understand the skill's product objective before running or
maintaining it.

## Core Purpose

GTM Cleanup Intelligence is a GTM cleanup intelligence system. It turns GTM
evidence into a deep, practical cleanup plan by independently finding
deterministic hygiene issues, semantic business-logic issues, and technical
custom-code risks.

## North Star

Answer this question:

```text
What should be fixed, simplified, consolidated, migrated, hardened, deleted, or
deferred so this GTM container measures the right business actions with the
right data and right business logic, for the right platforms, in a maintainable
and privacy-aware structure?
```

## Working Principle

Build a source model first, then run three cleanup lenses:

- deterministic hygiene: mechanical cleanup opportunities;
- semantic business hygiene: event meaning, trigger context, source data,
  business logic, payload shape, consent, and platform expectation;
- technical custom-code optimization: code safety, simplicity,
  maintainability, and replacement opportunities.

The source model is a navigation map, not the evidence source. The cleanup
lenses use it to traverse dependencies, then verify findings against raw
export/API/config/code/runtime evidence before recommending keep, fix,
consolidate, delete candidate, defer, or document exception.
