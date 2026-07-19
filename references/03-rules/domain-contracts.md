# Domain And Vendor Contracts

Use the versioned `vendor-registry.toml` first. When a detected vendor or feature
has no suitable current entry, search the internet and use the vendor's official
documentation. Record the exact official HTTPS URL in the configuration review.

## Contents

- Topic-specific contract obligations
- Google Analytics 4 and ecommerce
- Consent and CMP
- Browser-to-server and server containers
- Media, affiliate, publisher, and GTM mechanics

## Topic-Specific Obligations

The source scaffold generates one contract topic per applicable object and
downstream vendor context. Complete every topic exactly once. A single generic
`vendor setup checked` statement never satisfies the contract.

Typical obligations are:

- GA4: event name, destination/server route, event parameter names and types,
  consent/timing, and event-specific ecommerce/item/value rules;
- media/affiliate: event, destination ID, payload names/shapes/types,
  consent/timing, and event-ID or deduplication behavior;
- CMP: consent mapping, default/update timing, and downstream gating;
- variables consumed by vendor tags: terminal value shape/type and availability
  at the consuming event, plus consent semantics where relevant;
- custom templates, clients, and transformations: permissions/behavior,
  request claiming/routing, payload/consent handling, transformation scope, and
  allowlist/redaction behavior.

Each topic records the configured value, expected official rule, exact source
anchor, official URL, and verdict. A non-compliant topic becomes a defect. An
unproven topic cannot support a Correct object verdict.

An unrecognized external host, loaded script, or custom template is not a
reason to skip vendor validation. Record the detection cue, identify the vendor
or integration, cite a current official HTTPS setup/reference page, explain the
official ownership of that source, and complete the generated contract topics.
Avoid broad vendor detection from generic parameter words.

## Google Analytics 4

Treat Google event tags as GA4/current Google tag unless the export proves
Universal Analytics through native UA type, `UA-` property, UA parameters, or
old ecommerce paths. When UA is proven, classify it explicitly as legacy and
use the official sunset/migration source rather than applying a GA4 event
contract silently.

Primary sources:

- events: https://developers.google.com/analytics/devguides/collection/ga4/reference/events
- recommended events: https://developers.google.com/analytics/devguides/collection/ga4/reference/recommended-events
- ecommerce: https://developers.google.com/analytics/devguides/collection/ga4/ecommerce
- event naming: https://support.google.com/analytics/answer/13316687

For every GA4 event check event name, firing event, event parameters, ecommerce
mode, item parameters, data types, user data, consent, destination/configuration,
and duplicate routes.

For standard ecommerce, prefer the official website/dataLayer `ecommerce`
contract. Typical checks include:

- `view_item`, `add_to_cart`, `remove_from_cart`, `view_cart`, and
  `begin_checkout`: appropriate `items`; currency/value when revenue value is sent;
- `add_shipping_info` and `add_payment_info`: items and relevant method field;
- `purchase`: unique `transaction_id`, currency, numeric value, tax/shipping,
  coupon when used, and complete `items`;
- item arrays use item objects and appropriate item-level fields;
- value and quantity come from event-time ecommerce data, not fixed product
  positions or unrelated custom formulas.

Do not create custom JavaScript merely because the audit agent did not inspect
the official dataLayer path. First verify the event's official ecommerce object
and the exported dataLayer variables.

Missing standard events may be proposed as an optional tracking-plan/dataLayer
improvement. Do not create tags when the required website dataLayer event is absent.

## Consent And CMP

Primary Google setup source:
https://developers.google.com/tag-platform/security/guides/consent

Check:

- default and update timing;
- `analytics_storage`, `ad_storage`, `ad_user_data`, and
  `ad_personalization` independently;
- CMP purpose/group mapping and sibling variables with identical conditions;
- native consent requirements and trigger-level blocking;
- external scripts loading before consent;
- consent values forwarded to server routes;
- duplicate CMP listeners or consent-update tags.

Do not make legal decisions. A mapping that cannot be identified from container
evidence requires one precise owner/legal question.

## Browser-To-Server And Server Containers

Primary source:
https://developers.google.com/tag-platform/tag-manager/server-side/intro

Classify web tags that route through a server endpoint before flagging missing
measurement IDs or consent blockers. A web Google configuration/event tag may
rely on a server-managed destination, and consent may be forwarded as event or
settings parameters. Inspect transport/server URL, tag settings, event
parameters, client-to-server role, and deduplication fields.

Two client-side consent-control models are valid when their exported contract is
internally coherent:

1. **Client-enforced control:** native Consent Mode, additional consent checks,
   or firing/blocking logic controls browser-side vendor execution.
2. **Server-enforced transport:** transporter tags may send every event to the
   first-party server endpoint without a client-side blocking trigger, while a
   Google tag/configuration setting, event-settings variable, event parameter,
   or equivalent inherited variable forwards the consent state needed by the
   server container to decide downstream vendor delivery.

For the server-enforced model, trace the forwarding parameter and every
referenced variable to the CMP/default/update source. Check that the required
consent purposes or an approved complete CMP-state object are available at
event time, inherited by every transporter in the route, and not contradicted
by direct browser-to-vendor tags. Missing client blocking is not itself a
defect. Record a defect only for a missing, partial, stale, swapped, or
inconsistently applied forwarding contract. When the web-side contract is
coherent, use a disposition such as `client transport contract aligned; server
enforcement not audited`, not a privacy alert or unresolved owner decision
solely because the receiving container is unseen.

The web export cannot prove what the server container forwards, transforms,
redacts, blocks, or deduplicates. Audit those claims only when the complete
server-container export is supplied. For server exports, include clients,
transformations, request claiming, outgoing tags, permissions, consent, and
event-data transformations.

## Google Tag Gateway For Advertisers

Primary sources:

- setup guide: https://developers.google.com/tag-platform/tag-manager/gateway/setup-guide
- GTM/CDN setup and status: https://support.google.com/tagmanager/answer/16222402

Identify explicit gateway fields or first-party Google transport hosts when they
are exported. Distinguish Google tag gateway from a custom server-side GTM
transport because their ownership and forwarding behavior differ. Record
`not_visible_in_container_export` when the export has no evidence: active-domain
status can live in GTM Admin/CDN configuration and must not be invented from an
ordinary Google tag alone. Consent review remains mandatory because first-party
routing changes the request path, not the visitor's consent choice.

## Media, Affiliate, And Publisher Vendors

For Meta, TikTok, Snapchat, Pinterest, LinkedIn, Microsoft Ads, Criteo, Awin,
Floodlight, Google Ads, GAM, and other detected vendors, resolve the current
official event documentation before judging the tag.

Check:

- base/config loader versus event tag and duplicate loaders;
- pixel/account/advertiser/conversion IDs and labels;
- standard versus custom event name;
- event-time trigger and business action;
- product/content identifiers, category/content type, contents/items arrays,
  quantity, currency, numeric value, order/transaction ID, hashed user data,
  and deduplication ID in the vendor-required format;
- scalar, array, and object shapes through recursive variable output review;
- consent before external script or request initiation;
- browser/server duplicate paths and event-ID consistency.

A dataLayer variable is valid when it already returns the required array/object.
Custom JavaScript is justified only for a real documented transformation, and
its output must be inspected line by line.

## Official GTM Mechanics

- tag sequencing: https://support.google.com/tagmanager/answer/6238868
- firing priority: https://support.google.com/tagmanager/answer/2772421
- import/export: https://support.google.com/tagmanager/answer/6106997

Use these mechanics when judging setup/teardown dependencies, priority, and JSON
routes. They do not replace business-purpose review.
