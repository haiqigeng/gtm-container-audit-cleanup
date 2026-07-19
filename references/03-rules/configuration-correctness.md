# Configuration Correctness Run

Review every in-scope object independently from the sanitation and architecture
verdicts. The goal is literal functionality and correctness, not a summary of
parameters.

Use `shared_facts.json` to avoid extraction drift, while deriving correctness
verdicts independently. Shared behavior signatures are evidence coordinates,
not conclusions.

## Contents

- Required object and branch proof
- Recursive variables and standard business values
- Template and custom-code inspection
- Topic-specific official contracts

## Required Object Proof

For each tag, trigger, variable, template, client, and transformation state:

1. exact purpose;
2. execution logic and timing;
3. inputs and recursive terminal sources;
4. configured output, payload, state change, or side effect and data type;
5. consumers and their expected meaning;
6. consent, blocking, sequencing, and server-routing context;
7. correctness verdict and source-bound basis;
8. concrete defects and cleanup operation, or a precise non-action disposition.

Each of the seven semantic statements cites the generated source paths allowed
for that claim. It must also name at least two relevant source-derived facts
when available, such as the event, trigger, condition, dataLayer path, return
expression, destination, consumer, or consent control. A valid citation attached
to reusable prose does not pass.

Use the object's actual event, path, identifier, formula, selector, cookie,
endpoint, return value, or vendor field. Do not use broad substitutes such as
`computed value`, `helper`, `loader`, or `payload mapper` without first stating
literal behavior.

Complete every generated D3 logic cross-check exactly once:

- purpose versus configured output or side effect;
- intended scope versus firing, blocking, conditions, and sequencing;
- recursive terminal inputs versus output type/shape and consumer meaning;
- effective consent route versus execution and sequence;
- custom-code behavior versus configured output or side effect, when present;
- exported vendor fields, route, values, types, and consent versus the official
  contract, when present.

Each cross-check has a source-specific conclusion, verdict, and only the
generated evidence anchors allowed for that object. An Issue must link to a
concrete defect and force the object's overall Issue verdict. An Unclear result
must remain a precise owner decision, container-evidence limit, or Issue; it
cannot be converted to Correct through generic prose.

## Branch Coverage

Every non-metadata exported leaf must be covered exactly once with:

- JSON path and source value hash;
- logic role: Input, Condition, Transformation, Output, Routing, Consent, or
  Execution control;
- concrete interpretation;
- concrete configured effect;
- Correct, Issue, Unclear, Metadata, or Not applicable.

An Issue branch must link to a defect using the same evidence path. Unclear
branches cannot support a Correct verdict.

## Recursive Variables

Trace every `{{Variable}}` reference recursively. Record all objects and source
branches in the chain and terminate at:

- dataLayer variable path and version;
- GTM built-in/system value;
- constant, lookup, regex, URL, cookie, DOM, or auto-event source;
- custom JavaScript return behavior and output type;
- missing reference or cycle.

Then compare the terminal value to the consumer contract. A similar variable
name is not proof. Check null/undefined handling, arrays versus scalars, numeric
coercion, event-time availability, fallback values, and multi-item behavior.

For each node in the recursive chain, state its literal configured function,
configured output, output type/shape, availability/fallback, and compatibility
with the current consumer. Explain every variable-to-variable hop. Reviewing a
variable elsewhere in the matrix does not replace this consumer-context check.

## Standard Business Values

When present, always inspect transaction ID, currency, order/revenue/value,
total price, quantity, item count, items/products, product ID/category/price,
tax, shipping, coupons, lead value, user data, and consent state. Check formulas
for business sense. Examples of defects include summing fixed product slots,
counting array length instead of quantities, adding formatted currency strings,
or sourcing purchase values from a pre-purchase event.

Every source-derived formula signal must receive an explicit verdict. For a
fixed-slot aggregation such as `price1 + price2 + price3`, identify each input,
operator, fallback/coercion, output type, consumer, and expected cardinality.
Accept it only with a specific container-supported business rule; otherwise
record a defect or owner decision.

## Effective Consent Route

For every vendor-facing route, evaluate native consent settings, additional
consent checks, firing and blocking triggers, consent variables, setup/teardown
sequence, and visible browser-to-server routing together. Flag distinct consent
purposes that resolve through the same condition unless the export proves an
intentional shared policy. Do not assume that missing client-side blocking is a
defect when a native or server-bound control is visible.

For a server-enforced transport route, inspect the complete exported contract:

- first-party transport endpoint and the tags that inherit or use it;
- consent parameter, settings variable, or native Google consent signal sent
  with the request;
- recursive source of that signal, including CMP group/purpose mapping and
  default/update timing;
- purpose coverage and value shape expected by the server contract;
- every transporter covered by the shared configuration;
- any direct browser vendor tag that bypasses the server decision.

When those web-side facts align, mark the client route aligned and state that
server enforcement is not audited. Do not create a client blocker merely to
replace an intentional server-enforcement design. A missing, partial, swapped,
stale, or route-specific consent signal is a concrete configuration issue;
absence of the unseen server export alone is not.

## Template Objects

Judge event name, template mode, configured fields, variable outputs, trigger
context, consent, destination, and official vendor contract together. Copying a
parameter table is not an audit.

## Custom Code

Review all exported nonblank lines in source-bound behavior blocks of at most 30
lines. Every line hash appears exactly once. Each block states:

- purpose and control flow;
- inputs and GTM references;
- returned/sent/pushed output;
- DOM, cookie, storage, dataLayer, network, script, listener, or global effects;
- code-health and safety judgment.

Resolve each static parser/security/optimization finding. Check unsafe eval,
HTML injection, message origin, HTTP endpoints, dynamic scripts, repeated
listeners, global state, storage, fixed product indexes, parse errors, missing
returns, output type, exceptions, and replaceability by native GTM features.

Container-only evidence can judge exported code behavior and health. It cannot
prove DOM presence, endpoint response, or vendor acceptance; state that limit
without deferring the code review itself.

## Official Contracts

Vendor-facing objects require an official HTTPS source and checks for the
specific generated event/feature topics involved. Variables inherit obligations
from downstream vendor consumers. Compare configured value, expected rule, data
type/shape, evidence path, and verdict for every topic exactly once. A
non-compliant check must become a defect. An unproven contract cannot be marked
Correct.

When no registry entry matches an external host, script, or custom template,
create an unknown-vendor research obligation. Identify the integration, cite a
current official vendor source, explain why that source is official, and then
complete the same event, destination, payload, consent, and deduplication checks.
Do not classify generic words such as `activity` or `contents` as a vendor.
Placeholder, example, test, or non-HTTPS URLs are invalid. Use the bundled
registry first; otherwise search the current official vendor site and record
the exact page used.
