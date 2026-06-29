# Semantic Logic Checks

Use this reference as an internal reasoning pass before writing findings,
cleanup operations, generated JSON, or a change log. The goal is not to add more
report volume. The goal is to understand whether the container configuration
makes business and data sense as a whole.

## Contents

- Principle
- Recursive Semantic Graph
- Formula Sanity
- Context Consistency
- Contradiction Patterns
- Cross-Consumer Checks
- Media Signal Quality
- Cleanup Plan And Change Log Coherence

## Principle

A GTM object can be syntactically valid and still be analytically wrong. Do not
stop at "tag exists", "trigger fires", "variable resolves", or "vendor field is
filled". Check whether the object meaning, source data, formula, event context,
payload shape, and consumers agree with each other.

Only surface the result when it changes a finding, operation, blocker, or QA
step. Keep scratch reasoning internal or in a technical workbook tab when the
user asks for traceability.

When a semantic logic check finds an issue, write it as an operation seed:
current behavior, why the logic is wrong or risky, expected clean behavior,
exact proposed action or blocker, and QA. Do not leave it as `validate logic`,
`check variable`, or `review event context`.

## Recursive Semantic Graph

Build the graph only after D3 literal behavior facts are extracted for every
tag, trigger, variable, custom template, and referenced configuration branch in
a full audit. The graph should connect exact behavior, not broad categories.
For example, connect `returns Date.now()` to the consuming `device_local_hour`
field; do not connect only `computed value` to `Piano`.

Build a graph for tags, triggers, variables, folders, templates, and custom
code:

```text
business action -> trigger/event context -> tag -> vendor field
                                      -> variable/helper -> source path/formula
                                      -> custom code side effect
                                      -> consent/server routing
```

For each edge, infer:

- meaning: purchase value, item price, total quantity, form type, lead ID,
  product/category, consent group, market, page type, or audience;
- source of truth: current dataLayer event, previous dataLayer history, DOM,
  URL, cookie, constant, lookup table, server container, or vendor platform;
- output type: number, numeric string, scalar ID, array, object, array of
  objects, JSON string, boolean, URL, or side effect;
- consumer expectation: vendor field, GA4 parameter, trigger condition, custom
  HTML placeholder, setup/teardown reference, or report-only metadata.

Trace recursively:

```text
tag field -> referenced variable -> variable config/code/source path
trigger filter -> referenced variable -> variable config/code/source path
custom HTML/CJS placeholder -> referenced variable -> source path/code
lookup/regex table -> input variable -> terminal source
```

Stop only at a terminal source, such as a dataLayer path, URL component,
built-in value, cookie, DOM selector, constant, external endpoint, or a D4
runtime-only availability question. Do not stop at the variable name.

Do not create a cleanup operation from an isolated object row when the relevant
graph path is unknown. A cleanup decision must be supported by one of these:

- complete graph path from business action to destination field;
- complete graph path from trigger to code/side effect and consumer;
- complete graph path proving an object is unused, duplicated, or replaced;
- explicit blocker explaining which graph edge cannot be proven.

Use the graph to detect synergy issues:

- same business action sent to the same vendor with different payloads;
- same source variable consumed by incompatible vendor fields;
- client and server events duplicated without deduplication evidence;
- consent state mapped differently inside the same vendor family;
- different semantic fields using the same source condition without a documented
  reason, such as `ad_storage` and `analytics_storage` both granted by the same
  CMP purpose;
- loader tags that can overlap on the same route;
- trigger names that imply a context not enforced by filters or downstream
  parameters;
- naming/consolidation proposals that would hide different business meanings.

## Formula Sanity

For every variable or custom code block that computes a business value, test the
logic against its name, source fields, event context, and consumers.

Flag as suspect when:

- total price sums fixed item prices such as `product_price_1 + product_price_2
  + product_price_3` instead of iterating current items, multiplying unit price
  by quantity where required, or using the official order value;
- total quantity reads price fields, value fields, or fixed product indexes
  instead of item quantities;
- order value reads a product unit price, first item price, subtotal from a
  different event, stale product-detail data, or DOM text unrelated to the
  conversion event;
- discount, tax, shipping, coupon, or currency are missing from the value model
  when the destination or business reporting expects them;
- item arrays are built from scalar IDs, comma-joined strings, fixed indexes, or
  `[object Object]` output where the vendor expects an array/object shape;
- lead value is static or copied across all form types when names/triggers imply
  materially different lead value;
- custom JavaScript searches historical `dataLayer` pushes and may return stale
  product, cart, user, or consent values.

Do not replace a nonsensical formula with another guess. If the website or
dataLayer should provide the source field, mark website/dataLayer work as the
blocker.

For fixed-index ecommerce logic, the expected clean state is normally one of:
use the current event's complete `items` array, use the official order value
sent by the website, or document a single-item business exception. A cleanup row
must name which state is intended or state the dataLayer/runtime blocker.

## Context Consistency

Check whether each variable is valid at the moment each consuming tag fires:

- Does the trigger event carry the source data the variable reads?
- Does the variable read the current event or an older event?
- Does the same variable serve incompatible contexts, such as product detail,
  add-to-cart, checkout, and purchase?
- Does the tag fire before consent, dataLayer, product, lead, or transaction
  fields are available?
- Does a pageview tag consume form/product variables that are only available
  later?
- Does a thank-you page trigger represent one form type, several form types, or
  an unknown backend outcome?

If the export cannot prove the runtime context, classify the check as runtime
QA required rather than assuming correctness.

Runtime QA required is not permission to skip export-level logic checks. Still
inspect source paths, formulas, lookup rows, custom code/config, output shape,
and consumers before marking only the runtime proof as blocked.

## Contradiction Patterns

Actively search for contradictions:

- name says `purchase`, `lead`, `qualified lead`, `appointment`, `FR`,
  `product range`, or `consent granted`, but trigger/filter/payload does not
  enforce that meaning;
- tag event name is final conversion but trigger is a click, form start,
  generic pageview, or shared thank-you page;
- trigger is reused by tags with different business meanings and no downstream
  parameter distinguishes those meanings;
- variable name says total/order/quantity/items/category but formula reads a
  narrower, unrelated, stale, or differently typed value;
- vendor field expects array/object but receives scalar DLV, joined string,
  fixed index, or unguarded custom JS;
- same business action sends different values, currencies, IDs, item sets,
  event IDs, or lead types to different vendors without a documented reason;
- cleanup/naming would make two semantically different objects look identical.

## Cross-Consumer Checks

A variable can be correct for one tag and wrong for another. For shared
variables:

- list all consuming tags and fields;
- compare each consumer's expected type and business meaning;
- split, rename, or defer when one helper is serving incompatible semantics;
- avoid "fixing" a shared variable for one vendor in a way that breaks another.

## Sibling Logic Checks

For every tag or template with multiple meaningful fields, compare sibling
fields after resolving their referenced variables:

- field name and expected semantic meaning;
- referenced variable or constant;
- terminal dataLayer/cookie/URL/DOM/source path;
- custom-code condition or lookup rows;
- returned value and output type;
- official/vendor expectation or business meaning.

Flag as a finding, documented exception, or owner blocker when:

- two different semantic fields use identical or near-identical logic;
- fields that should be distinct use the same source path or CMP purpose;
- one field combines multiple conditions while a sibling uses only one without
  a clear reason;
- a variable name says one meaning while the consuming field expects another;
- a family-level pattern is mostly consistent but one object deviates.

This check is mandatory for consent, GA4/current Google, ecommerce, lead,
media, affiliate, server-side transport, publisher ads, and any vendor template
with configurable event/payload fields. It is also useful for simple tags
because it reveals consolidation opportunities.

## Media Signal Quality

For media and conversion tags, infer the platform optimization signal:

- final conversion, micro-conversion, audience event, exclusion, remarketing,
  attribution helper, enhanced matching, or server-forwarding event;
- high-intent vs low-intent action;
- value/currency/source ID quality;
- event ID/deduplication and browser/server relationship;
- whether the signal is likely to train bidding toward the intended business
  outcome.

Only report media-signal concerns when they produce an actionable operation,
blocker, or owner question. Do not expand the cleanup plan with a strategy
essay.

## Cleanup Plan And Change Log Coherence

The cleanup plan is the decision source. The change log is the execution record.

- Every change-log row must map to a cleanup operation ID or explicitly state
  that it is a no-op/documented exception.
- Do not introduce new findings, new reasoning, or different risk wording in the
  change log.
- If semantic logic checks discover a bad setup, create or update the cleanup
  operation first; then the change-log row mirrors that operation after it is
  executed or generated.
- Keep the plan and change log aligned on object IDs, before/after names,
  action, reason, impact, QA, owner, and status.
- When no mutation is made because evidence is missing, use a deferred/blocker
  operation; do not create a misleading "changed" log row.
