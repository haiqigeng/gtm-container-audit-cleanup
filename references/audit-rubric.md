# Audit Rubric

Use this reference for the complete human and technical audit. It is designed to
work from exported GTM JSON, GTM API reads, GTM UI screenshots, Tag Assistant,
page source, crawl output, or stakeholder-provided evidence.

## Contents

- Severity Model
- Evidence Sources
- Inventory Checklist
- Audit Completeness Contract
- Official Documentation Contract
- Deep Object Semantics
- Semantic Model Protocol
- Semantic Logic Consistency
- Name-Based Scope Inference
- Mandatory Naming Standardization
- One Tag Gateway Detection
- Governance
- Web Container Implementation
- Security And Custom Code
- Architecture And Organization
- Setup Hygiene
- Consent And Privacy
- Google Event Classification Baseline
- Server-Side GTM
- Vendor Pixels And Marketing Tags
- Cleanup Heuristics
- Scenario-Specific Intelligence
- Cleanup Completeness
- Consolidation Review Order

## Severity Model

Use the highest applicable severity:

| Severity | Use when |
| --- | --- |
| Critical | Tags fire in clear violation of consent/legal requirements, major conversion/analytics collection is broken, or production mutation could cause immediate data loss. |
| High | Data quality, privacy, attribution, or revenue tracking is materially wrong or highly likely to become wrong. |
| Medium | Setup works but is fragile, duplicated, inconsistent, hard to maintain, or likely to cause future implementation mistakes. |
| Low | Minor hygiene, naming, documentation, or operational improvement. |
| Info | Observation with no recommended change, or evidence retained for context. |

Use priority separately from severity when planning work:

`P0 Now`, `P1 This sprint`, `P2 Planned cleanup`, `P3 Backlog`, `Decision needed`.

For examples and edge-case calibration, read `severity-calibration.md`. Keep
severity, priority, and confidence separate; do not lower severity merely
because evidence confidence is low.

## Evidence Sources

Record source freshness for each audit:

- Exported container JSON: export time, container/version/workspace.
- GTM API/UI: account, container, workspace/version, read time.
- Website evidence: URLs, environment, browser, consent state, Tag Assistant or
  network observations, crawl date.
- Stakeholder evidence: owner, date, and confidence.

If evidence conflicts, prefer the freshest source for the exact object and note
the conflict.

## Inventory Checklist

Inventory and count:

- accounts, containers, workspaces, versions, and user permissions when access
  permits;
- tags, tag types/vendors, firing triggers, blocking triggers, setup/teardown
  relationships, consent settings, and sequencing;
- triggers, event types, filters, trigger groups, exceptions, and connected tags;
- variables, variable types, dataLayer keys, lookup tables, custom JS bodies, and
  consumers;
- templates and template update state;
- folders, notes, and naming patterns;
- website/container installation evidence;
- server-side GTM clients, tags, transformations, endpoints, and monitoring when
  in scope.

## Audit Completeness Contract

Default to a complete audit unless the user explicitly asks for a reduced scope.
Large containers still require complete coverage; use normalized tables,
clustering, hashes, and grouped findings to scale the work rather than skipping
object families.

The checklist is a minimum floor, not a ceiling. Agents may do more when the
evidence supports it, but must not do less than the mandatory checks. If a
required check cannot be completed from the available evidence, record it as
`Deferred` or `More info needed` with the exact blocker, affected objects, risk,
required evidence, and next action.

For every audit, cover:

- all tags, triggers, variables, folders, templates, consent settings, and
  built-in variables;
- exact duplicates and near duplicates across tags, triggers, variables, custom
  code, templates, folders, and naming patterns;
- currently unused objects and objects that become obsolete after consolidation;
- object semantics, consumer dependencies, output shape, and trigger context for
  every high-risk or shared object;
- standard ecommerce variables and all consuming tags;
- custom HTML/JavaScript reference safety;
- gateway and consolidation opportunities where repeated patterns exist.

Sampling is allowed only to explain repeated low-risk hygiene patterns in the
report. It is not a reason to skip dependency mapping or cleanup eligibility
checks for the full container.

Semantic completion gate: a workstream is not complete until semantic
validation is complete or explicitly deferred with a blocker. Inventory,
dependency coverage, hashes, URL extraction, duplicate grouping, script output,
and reference maps are evidence inputs, not semantic validation. Do not mark any
meaningful object family `Done` when the only completed work is inventory or
dependency mapping.

Reconcile counts before delivery for each meaningful object family:

- total source objects;
- inventoried objects;
- dependency-mapped objects;
- semantically validated objects;
- cleanup-decision objects;
- deferred objects;
- not applicable objects;
- user-excluded objects;
- unresolved objects.

The semantic coverage formula must reconcile:
`total = semantically validated + deferred + not applicable + user-excluded`.
Any nonzero unresolved count means the audit or cleanup plan is incomplete until
the row is resolved or explicitly deferred with a blocker.

If any mandatory gate fails, deliver the result as `Incomplete / blocked`. Do
not soften the failure into a normal limitation, and do not omit the affected
family from the cleanup plan.

## Official Documentation Contract

For every meaningful tag family, identify the official implementation, website
event payload, dataLayer, or event documentation before judging payload
correctness. Treat official docs as the default source of truth for standard
events, required parameters, recommended parameters, data types, value formats,
base/event sequencing, deduplication, and validation methods unless the user
explicitly provides a different business rule.

Use `source-map.md` as the starting index for frequently consulted official
documentation URLs, then re-open or re-search the official source when current
product behavior matters. If the vendor, CMP, template, or event family is not
listed in the skill references, search the internet for that vendor's official
documentation before judging the tag, trigger, variable, or payload. Do not skip
documentation lookup just because the vendor is uncommon or absent from the
reference map.

Apply this especially to:

- GA4 recommended events, ecommerce events, official website/dataLayer payload
  format, item arrays, event-level value and currency, transaction IDs, and
  item-scoped parameters;
- Google Ads, Floodlight, Microsoft UET, and server-side Google tagging;
- Meta Pixel/CAPI, TikTok Pixel/Events API, Snapchat Pixel/CAPI, Pinterest Tag,
  LinkedIn Insight Tag/CAPI, Reddit, X/Twitter, affiliate pixels, and other
  media tags when official docs are available;
- CMP and consent documentation when consent routing depends on a vendor or CMP
  contract.

For each vendor/event family, record:

- official source checked, access date, and confidence;
- standard event name expected by the platform;
- required and recommended parameters;
- expected website/dataLayer payload structure and expected GTM Data Layer
  Variable paths when GTM reads those parameters;
- expected data types and shapes, such as number, string, ISO currency code,
  array of IDs, array of item objects, or hashed identifier;
- expected source of truth: website dataLayer/current event, tag template field,
  server event, first-party cookie, or vendor API;
- validation method, such as Tag Assistant, vendor helper, network request, event
  manager, or platform diagnostics.

Do not fill documentation gaps with guesswork. If official documentation is
unavailable or blocked after checking bundled references and searching the
internet, say so, record the search path or failed official-source lookup, use
current export/runtime evidence carefully, and lower confidence.

Do not create custom JavaScript as a shortcut when the official implementation
expects the website/dataLayer to already send the parameter. For example, if an
official ecommerce event requires an item array, value, currency, price, or
quantity from the current ecommerce action, the correct finding may be
"dataLayer event is incomplete" rather than "create a GTM variable that guesses
the value." Helper variables are appropriate only to transform a complete source
payload into the vendor-required shape, add guards, normalize names, or avoid
duplication without changing the source-of-truth contract.

For Google Analytics/event/ecommerce tracking, default to GA4/current Google tag
documentation. Classify an object as Universal Analytics only when the tag type,
property ID, explicit user instruction, or verified migration evidence proves a
UA exception.

## Deep Object Semantics

Do not treat the audit as a count-and-status exercise. For every tag, trigger,
and variable that affects consent, ecommerce, media, conversion, custom code, or
shared routing, record:

- intended business role;
- event/page context where it should run;
- vendor or destination platform;
- market, language, hostname, product line, campaign, or model scope;
- consumed variables and dataLayer paths;
- output shape: scalar, array, object, boolean, joined string, URL, ID list, or
  vendor payload object;
- expected downstream consumer and field format;
- consent/privacy dependency;
- evidence that the object is correct, questionable, or redundant.

For low-risk hygiene objects, sample then expand when patterns repeat. For
high-risk objects, inspect individually.

Every meaningful object family must have semantic status: `Keep`, `Fix`,
`Consolidate`, `Delete candidate`, `More info needed`, or `Not applicable`.
Do not mark a family complete when it has only inventory rows, dependency rows,
or code hashes.

## Semantic Model Protocol

Use `semantic-model-protocol.md` after dependency mapping for conversion,
media, ecommerce, lead, server-side, multi-market, custom-code, or complex
cleanup tasks. Build the model internally before judging optimization patterns.

At minimum, infer business objective, user action, event/context, GTM
implementation, data source, destination payload, platform use, and evidence or
blocker. Use the model to find missing business logic, such as lead type,
product category, value model, item array, deduplication ID, consent forwarding,
or market scope that the container appears to need but does not reliably
provide.

## Semantic Logic Consistency

Use `semantic-logic-checks.md` before finalizing findings or cleanup operations
for media, ecommerce, lead, conversion, custom-code, shared-variable, value, or
quantity logic.

At minimum, verify that:

- variable names, source paths, formulas, output types, event context, and
  consumers agree;
- totals, quantities, values, item arrays, content IDs, lead types, and product
  categories are not built from fixed indexes, stale dataLayer history, wrong
  field types, or unrelated events;
- a variable reused across vendors is valid for every consuming vendor field;
- trigger and tag names do not promise a business action, country, product,
  lead type, or consent state that the configuration does not enforce.

Only report the result when it changes a finding, blocker, operation, or QA
requirement. Do not expand stakeholder reports with scratch reasoning.

## Name-Based Scope Inference

Use object names as evidence of intended scope, then verify whether the
configuration enforces that scope.

Look for:

- country, market, or language codes such as `FR`, `DE`, `UK`, `CH`, `AT`,
  `BE`, `IT`, or `NL`;
- hostnames, domains, regions, currencies, or store names;
- product range, model, brand, or client-specific acronym tokens;
- campaign, audience, vendor, agency, or test suffixes;
- prefixes that may describe ownership, deployment phase, or legacy migration.

For each scoped object, compare the name to the actual trigger filters,
variables, lookup table rows, custom code conditions, and vendor payload. Flag
names that imply a country, product range, or audience that is not enforced by
the object.

When a token is unclear, do not invent the meaning. Ask the user whether it is a
product range, campaign, market, internal audience, legacy label, or something
else before treating the object as wrong or safe to consolidate.

## Mandatory Naming Standardization

Naming standardization is a mandatory cleanup step. Perform it after
semantic fixes, consolidation design, and deletion decisions are known, so the
remaining objects receive stable final names and do not need a second rename.

If the user has a house convention, follow it. Otherwise use this default:

| Layer | Required pattern | Examples |
| --- | --- | --- |
| Tags | `Vendor - Event/role - Scope/detail` | `GA4 - purchase`, `GA4 - Config`, `Meta - AddToCart - Product line`, `Google Ads - Purchase - FR`, `Pinterest - Base` |
| Triggers | `Utility/type - Event or condition - Scope/detail` | `CE - purchase`, `PV - All Pages`, `Consent - Meta Granted`, `Block - No Marketing Consent`, `Group - purchase + Google Consent` |
| Variables | `Type acronym - Variable name/source` | `DLV - ecommerce.purchase.products`, `CJS - Purchase total quantity`, `LT - Hostname to currency`, `RT - Product range from path`, `URL - Hostname` |
| Folders | `Vendor` or `Domain / Function` | `GA4`, `Meta`, `Google Ads`, `Ecommerce helpers`, `Consent` |

Use these variable type acronyms unless a house style exists:

- `DLV`: Data Layer Variable.
- `CJS`: Custom JavaScript variable.
- `LT`: Lookup Table.
- `RT`: Regex Table.
- `URL`: URL variable.
- `1P`: first-party cookie.
- `JS`: JavaScript variable.
- `Const`: constant.
- `Util`: utility/helper when the source is mixed or abstract.

Rules:

- Put the vendor/platform first for tags, because tags are destination-owned.
- Put the trigger utility/type first for triggers, because triggers are reused by
  firing mechanics: `CE`, `PV`, `Click`, `Form`, `Timer`, `Consent`, `Block`,
  `Group`, or another clear utility.
- Put the variable implementation/source type first for variables, because
  users need to know whether they are reading dataLayer, transforming data,
  looking up a value, or parsing the URL.
- Use the official event name for standard events where applicable, such as
  `purchase`, `add_to_cart`, `ViewContent`, `AddToCart`, or `Purchase`.
- Put market, country, language, product range, campaign, pixel ID suffix, or
  consent detail after the event/role, not before it.
- Every proposed final name must be unique inside its GTM layer. Before
  delivering an audit plan, cleanup operation table, rename map, or generated
  JSON, group proposed names by layer and resolve collisions. Do not propose the
  same final tag name for multiple tags just because they share a vendor and
  event role.
- When a base naming pattern collides, add the smallest meaningful suffix that
  explains why the object remains separate: trigger event, page type, form type,
  market, language, product range, campaign, destination ID suffix, pixel/account
  role, consent category, sequence role such as `Base`, `Config`, `PageView`,
  `Setup`, `Lead Event`, `Standard Event`, or lifecycle status such as
  `Legacy`, `Paused`, or `Decommission candidate`.
- Use an object ID suffix only as a temporary audit placeholder when the real
  business distinction is unknown. Mark that row as blocked for owner
  clarification instead of treating the ID-suffixed name as a preferred final
  production name.
- Keep ambiguous business tokens such as `ProductLineA`, `CampaignX`, `SegmentY`, or agency
  acronyms only when the user confirms their meaning or the configuration proves
  the scope.
- Do not rename a variable unless all `{{Variable Name}}` references in tags,
  triggers, variables, templates, custom HTML, and custom JavaScript have been
  mapped and validated.
- Record every rename as `before name`, `after name`, object ID, reason,
  expected behavior impact, and QA status.
- If standardization is deferred, list the exact object names, blocker, and
  proposed final pattern.

## One Tag Gateway Detection

When applicable, identify whether the container uses a gateway pattern:

- a single custom HTML or template tag dispatches many vendors/events;
- one Google tag, Floodlight tag, or server-side endpoint forwards many event
  types;
- a lookup-table-driven tag chooses vendor IDs, event names, or payload fields;
- one shared loader/base tag supports many event tags;
- one server-side GTM endpoint or first-party tagging URL acts as a collection
  gateway.

For each gateway candidate, document:

- trigger coverage and consent gate;
- how event type, market, product line, vendor ID, and payload are selected;
- whether the gateway preserves vendor-required payload shape;
- whether gateway failures would break many downstream tags;
- observability and QA method;
- whether consolidation into a gateway would make current tags/triggers/variables
  obsolete.

Prefer gateway patterns only when they reduce real duplication without hiding
ownership, consent logic, QA responsibility, or vendor-specific payload rules.

## Governance

Check:

- account and container user counts;
- whether users, agencies, vendors, and service accounts have appropriate
  permissions;
- whether risky roles are limited to owners who need them;
- 2-step verification and organization security controls;
- workspace/release process and whether default workspace is used for normal
  work;
- version names/descriptions and rollback clarity.

Flag:

- unknown users or broad agency access;
- excessive publish/admin permissions;
- no descriptive version history;
- repeated work in default workspace without process controls.

## Web Container Implementation

Check representative page types and environments:

- GTM script placement in the page `<head>`;
- `noscript` placement immediately after opening `<body>` where applicable;
- missing GTM on important page templates;
- multiple GTM containers and whether each has an owner/purpose;
- duplicate container loads, with SPA/PWA caveats;
- CSP or browser/security controls blocking `gtm.js`, preview mode, vendor
  scripts, or server-side endpoints;
- dataLayer initialization order and whether important events fire before GTM is
  ready.

Flag implementation checks as `More info needed` when the export alone cannot
prove website behavior.

Use `runtime-qa-templates.md` when browser, Tag Assistant, network, CMP, SPA, or
vendor-platform evidence is needed.

## Security And Custom Code

Check:

- custom HTML tags, custom JavaScript variables, and custom templates;
- non-script/image pixels implemented through custom HTML instead of safer
  native/image/template options;
- outdated templates or unreviewed community templates;
- hardcoded credentials, tokens, PII, user identifiers, or endpoints;
- code that injects scripts without consent or origin checks;
- code that assumes array positions such as `items[0]` when multi-item orders
  are possible;
- code that only defines a function, listener, or helper without invoking it,
  registering it, or proving another tag/page calls it;
- brittle DOM selectors, regexes, and URL matching.

Prefer template/native tag types over custom HTML when feature parity exists and
the migration risk is acceptable.

For each custom HTML tag under review:

- identify every `{{variable}}` reference and the expected value format;
- distinguish intentional hardcoded constants from accidental hardcoding;
- confirm script/image/noscript behavior and whether it is appropriate inside
  GTM;
- confirm that a defined conversion function is actually called or registered;
  otherwise classify the tag as probable no-op/deferred-delete until runtime or
  owner evidence proves external use;
- verify escaping, quoting, JSON serialization, URL encoding, array joining, and
  null handling;
- verify that any proposed replacement preserves the original dynamic reference
  unless a semantic change is explicitly approved.

For every active Custom HTML tag and every referenced, risky, or cleanup-relevant
Custom JavaScript variable, record an object-level semantic row with:

- purpose;
- role category, such as vendor loader, event dispatcher, listener, DOM helper,
  storage/cookie helper, consent/CMP UI, identity helper, payload transformer,
  obsolete/paused, or other;
- trigger or consumer context;
- consent assumption;
- side effects, including external URLs, dataLayer pushes, cookies, storage,
  DOM writes, listeners, and network calls;
- variable references and expected output or side effect;
- runtime risks;
- recommended action;
- semantic status.

Paused or unused custom-code objects still require a decommission rationale
before they become delete candidates. Custom templates require the same semantic
review when they are present or consumed by tags/variables.

## Architecture And Organization

Assess whether the account/container structure fits:

- brands, markets, domains, apps, and environments;
- ownership boundaries and agency/vendor access;
- web vs server-side tagging separation;
- release cadence and QA process;
- naming conventions and folders.

Use the mandatory naming convention above unless a house style exists. Flag
mixed leading axes, unclear abbreviations, duplicated scopes, and names that
encode a scope not enforced by the trigger.

## Setup Hygiene

Check:

- tags without firing triggers;
- triggers with no connected tags;
- paused tags older than 5 months;
- objects edited more than 12 months ago that still power important flows;
- duplicate or near-duplicate tags, triggers, variables, templates, or folders;
- redundant objects with no known consumer;
- broken regex/CSS selectors and overly broad conditions;
- tags attached to non-pageview/non-custom-event triggers without conditions;
- stale Universal Analytics, Google Optimize, or other sunset/deprecated vendor
  tags;
- tags implemented with custom HTML where native GTM tags or maintained
  templates are safer.

Do not recommend deletion solely because an object is old or paused. Classify as
`Needs improvement` or `More info needed` until usage and ownership are clear.

Use three cleanup buckets:

- **Currently unused**: no current consumers after a full dependency sweep.
- **Consolidation obsolete**: currently used, but would be replaced by an
  approved consolidation/refactor.
- **Deferred validation**: appears redundant or fragile, but business ownership,
  runtime evidence, or vendor platform validation is missing.

Report currently unused candidates early, but do not finalize deletion until the
consolidation design has been reviewed. A broad refactor can make many more
objects obsolete than the first orphan scan reveals.

## Consent And Privacy

Read `audit-consent-server.md` for CMP, consent mode, regional consent,
pageview/base consistency, and browser-to-server consent checks. Use this rubric
section to mark the workstream status and link findings back to the evidence.

Minimum outcome: every meaningful vendor family has consent status, evidence,
risk, and blocker or no-change decision.

## Google Event Classification Baseline

Read `audit-ga4-ecommerce.md` for Google-event classification, official GA4
website/dataLayer contracts, GA4 tag checks, ecommerce variable checks, and
missing-event readiness. Treat ambiguous Google analytics/ecommerce objects as
GA4/current Google tag candidates unless evidence proves a UA exception.

Minimum outcome: GA4/current Google versus UA exceptions are explicit, official
dataLayer payload shape is checked, and ecommerce value/item/quantity logic is
validated before cleanup decisions.

## Server-Side GTM

Read `audit-consent-server.md` when server-side GTM, browser-to-server Google
tags, first-party endpoints, media-named Google event tags, or server forwarding
signals appear. Without server-container export/API evidence, network traces, or
platform logs, classify uncertain transport tags as `server-container validation
needed` rather than mutating IDs, consent triggers, or paused state.

Minimum outcome: client-side container risks are separated from server-side
validation blockers.

## Vendor Pixels And Marketing Tags

Read `audit-media-vendors.md` for media/vendor base tags, conversion events,
payload shape, cross-vendor parity, and media signal quality. Read
`vendor-playbooks.md` for vendor-specific details and `source-map.md` for
official documentation entry points.

Minimum outcome: event role, consent, sequencing, payload shape, value/currency,
IDs, deduplication, and platform optimization use are checked or deferred with
blockers.

## Cleanup Heuristics

Prioritize changes that improve:

- privacy compliance and consent consistency;
- revenue/conversion accuracy;
- GA4 ecommerce payload correctness;
- maintainability through reusable variables and triggers;
- performance by reducing duplicate vendors, redundant loaders, and custom HTML;
- release safety through naming, folders, workspaces, and version descriptions.

Prefer consolidation when:

- multiple tags differ only by ID, market, or vendor parameter and can use lookup
  tables safely;
- repeated custom JS logic appears in several tags;
- trigger conditions can be represented by a reusable helper variable;
- multiple consent triggers express the same rule with slightly different names.
- many market/page/event triggers share the same event plus one hostname, path,
  language, or product-line condition;
- several variables read sibling paths from the same ecommerce array and could be
  replaced by one typed helper object or item-array transformer;
- vendor tags repeat the same payload construction and differ only by event name
  or vendor ID.

Avoid over-consolidation when it hides business ownership, creates a single risky
mega-tag, or makes QA harder.

## Scenario-Specific Intelligence

Before finalizing findings, decide whether any of these scenarios apply. If yes,
load `operation-schema.md` and include the scenario in the cleanup plan.

| Scenario | Signals | Extra audit checks |
| --- | --- | --- |
| Ecommerce accuracy | GA4 ecommerce, Ads conversions, Meta/TikTok/Pinterest/Criteo/affiliate product fields. | Current event payload, item arrays, value/currency, transaction IDs, multi-item handling, vendor field shape. |
| Consent/CMP | Didomi, OneTrust, Cookiebot, Axeptio, Commanders Act, native consent settings, Consent Initialization triggers. | Default/update timing, regional rules, pageview/base consistency, legal-owner blockers. |
| SPA/PWA | History triggers, route variables, virtual pageview tags, frontend framework URLs. | Runtime route changes, duplicate pageviews, stale dataLayer state, async ecommerce pushes. |
| Multi-market/language | Country codes, hostnames, currencies, language folders, market-specific IDs. | Whether scope is enforced by triggers/variables, unclear token clarification, lookup/regex consolidation feasibility. |
| One-tag gateway | Dispatcher custom HTML, lookup-table routing, shared loaders, server endpoint. | Blast radius, observability, consent routing, vendor-specific payload preservation. |
| Server-side GTM | Server container, first-party endpoint, GA4 client, transformations, CAPI tags. | Browser-to-server payload, server-to-vendor payload, consent forwarding, deduplication IDs, monitoring. |
| Emergency fix | User asks for fast repair or production breakage. | Limit mutation scope, record skipped cleanup, recommend full follow-up audit. |

Do not force every scenario into every audit. Select scenarios from evidence and
state `Not applicable` when the pattern is absent.

## Cleanup Completeness

When the user asks for cleanup, standardization, or cleanup JSON,
apply the full cleanup workflow. Do not limit the output to a small correction
patch unless the user explicitly asked for a minimal fix.

For each layer, decide what is evidence-safe to change now, what is safe only
after consolidation, and what must be deferred:

- **Tags**: payload corrections, consent routing, duplicate vendor loaders,
  repeated event tags, native/template migration candidates, sequencing, paused
  or orphaned tags, and naming/folder consistency.
- **Triggers**: exact duplicates, near duplicates, repeated country/hostname/path
  filters, repeated CMP/vendor consent rules, unused triggers, trigger groups,
  exceptions, and trigger naming.
- **Variables**: duplicate dataLayer paths, duplicate custom JS, fixed-index
  ecommerce variables, output-shape helpers, lookup/regex table candidates,
  unused variables, and variables made obsolete by tag/trigger consolidation.
- **Custom code**: repeated snippets, missing guards, unsafe hardcoding,
  incorrect serialization/escaping, stale dataLayer reads, and custom HTML that
  should become native/template tags.
- **Folders and naming**: unused or misleading folders, mixed naming axes,
  names that encode a scope not enforced by configuration, and final names for
  new reusable helpers. Naming standardization is not optional in a cleanup; if
  it is not applied, document why and provide the target convention.

For importable GTM JSON, the generated file should include all evidence-safe
cleanup from these layers. The change log must separately list
deferred items with the exact blocker, such as unclear business scope, missing
CMP/legal decision, missing runtime evidence, or vendor-platform validation
needed.

Custom code cleanup cannot be reduced to one generic row when custom-code
objects exist. The plan must include object-level semantic review and cleanup
decisions, or explicitly defer the affected objects with blockers.

Before delivery, self-audit the generated cleanup artifact as a fresh container
export. The self-audit must confirm:

- every layer has changes, findings, or a documented reason for no change;
- no active GA4/current Google mapping relies on UA Enhanced Ecommerce paths
  without verified mapper evidence;
- naming standardization is applied or object-level blockers are listed;
- trigger/tag/variable names match actual logic and scope;
- references resolve, IDs are unique, and no new missing references exist;
- exact duplicates, unused objects, and consolidation-obsolete objects are
  resolved or documented as intentional residuals;
- residual blockers are listed before calling the JSON import-ready.

## Consolidation Review Order

Use this order before proposing cleanup:

1. Map current dependencies and exact consumers.
2. Understand dataLayer event schemas and vendor payload expectations.
3. Identify exact duplicates.
4. Identify similar objects that can be consolidated without changing semantics.
5. Design final helper variables, trigger patterns, and tag payload contracts.
6. Decide final naming before new objects are proposed.
7. Recompute obsolete triggers and variables after the consolidation design.
8. Split deletion candidates into currently unused and consolidation-obsolete.
9. Validate final names against final logic so a `form_submit`, `purchase`,
   country, product-range, or consent-vendor name cannot point to unrelated
   conditions.

Do not start by deleting every unused object if those objects may help explain
the existing pattern or serve as references for the consolidation design.
