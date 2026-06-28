# Optimization Patterns

Use this reference after building the semantic model. It helps the agent move
from low-effort cleanup to scalable GTM/TMS optimization without flattening
business meaning.

## Contents

- Pattern Evaluation Rule
- Low-Complexity Patterns
- Medium-Complexity Patterns
- Advanced Patterns
- Missing-Business-Logic Ideas
- Complexity Levels
- Operation Output

## Pattern Evaluation Rule

A pattern is valid only if it preserves:

- business objective and event meaning;
- trigger timing and scope;
- consent/privacy behavior;
- vendor-required payload shape;
- source-of-truth contract;
- QA observability and rollback.

If consolidation makes the result harder to understand, hides owner/business
differences, or weakens QA, do not consolidate. Document why similar objects
remain separate.

## Low-Complexity Patterns

Use when evidence is strong and blast radius is low:

- exact duplicate triggers, variables, and tags with identical semantics;
- unused objects after dependency sweep;
- paused/obsolete objects with owner-confirmed decommission;
- single-member trigger groups remapped to the child trigger;
- inconsistent naming/folders after behavior decisions;
- unused constants, duplicated dataLayer variables, and dead custom JS helpers.

These are cleanup opportunities, not the whole audit.

## Medium-Complexity Patterns

Use when objects are similar but not identical:

- combine repeated triggers with one reusable trigger plus lookup/regex/helper
  conditions;
- replace hardcoded country, hostname, product, or campaign conditions with
  lookup/regex tables when the scope remains clear;
- replace repeated vendor IDs, conversion IDs, or market IDs with lookup tables;
- centralize repeated payload helpers, such as item arrays, content IDs, event
  IDs, value normalization, and consent category mapping;
- split one ambiguous shared variable into explicit helpers when consumers need
  different output shapes;
- migrate custom HTML to native tags or maintained templates when feature parity
  and consent behavior are preserved.

Preferred dynamic controls:

- lookup table for stable one-to-one mappings;
- regex table for pattern families;
- custom JS only for typed transformations, guards, or object/array construction
  that cannot be expressed safely with native variables;
- trigger exceptions only when timing and consent state are reliable;
- server-side transformations only when server evidence exists.

## Advanced Patterns

Use only after semantic model and runtime/owner evidence support the design:

- event-family consolidation where multiple vendor tags share one business event
  but need vendor-specific payload mappers;
- one-tag gateway or dispatcher with explicit event, consent, vendor, and
  payload routing;
- media signal restructuring, such as separating micro-conversions from bidding
  conversions or differentiating lead quality/value;
- cross-vendor parity correction for value, currency, item IDs, event IDs,
  lead type, form type, product scope, and deduplication;
- ecommerce data contract redesign when GTM is compensating for missing
  website/dataLayer fields;
- server-side routing validation or migration when browser tags only transport
  events to a server container;
- consent model normalization across pageview/base/event tags and server-side
  forwarding;
- multi-market or multi-language architecture using clear lookup tables and
  scoped triggers instead of hardcoded duplicated tags.

Advanced patterns require staged operations, owner decisions, QA, and rollback.

## Missing-Business-Logic Ideas

When the semantic model implies a business flow but the implementation lacks
important fields, propose the missing piece as a blocker or future operation:

- lead type, form name, funnel step, program, campus, B2B/B2C, or customer type;
- product category, product line, margin class, bundle, subscription status, or
  inventory state;
- transaction ID, order value, discount, tax, shipping, currency, item array, or
  quantity;
- event ID, click ID, consent state, user-data eligibility, server route, or
  deduplication ID;
- audience exclusion rules, existing-customer detection, employee/test traffic
  exclusion, or logged-in state;
- platform objective distinction: reporting-only, audience-only, bidding
  conversion, or attribution helper.

Do not fabricate these fields in GTM unless the source data exists and the
transformation is defensible.

## Complexity Levels

Use these internal levels to decide how far to go:

| Level | Typical work |
| --- | --- |
| Hygiene | Exact duplicates, unused objects, naming, folders, dead references. |
| Structural | Near-duplicate consolidation, reusable triggers/variables, lookup/regex tables, custom-code reduction. |
| Semantic | Business objective mapping, formula sanity, event context, payload shape, cross-consumer consistency. |
| Strategic | Media signal quality, value model, cross-vendor parity, missing data contracts, server-side/consent architecture. |

The default audit should consider all levels. Execution aggressiveness can still
be Conservative, Standard, Deep, or Transformational according to evidence and
approval.

## Operation Output

Keep output concise:

- convert each valid pattern into operations only when it changes something or
  creates a real blocker;
- keep repeated examples grouped;
- use operation IDs consistently across cleanup plan and change log;
- avoid separate "idea dump" sections unless the user asks for strategic
  roadmap ideas.
