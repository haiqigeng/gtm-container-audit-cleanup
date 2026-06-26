# Vendor Playbooks

Use this reference after identifying vendor/event families in a container. It is
not a substitute for official documentation. Start with `source-map.md`, reopen
official sources when current behavior matters, and record the official source
used in the report.

For every vendor family, separate:

- base/config/loader tags;
- event/conversion tags;
- consent/CMP gates;
- ecommerce/dataLayer contracts;
- browser vs server-side destinations;
- deduplication IDs where browser and server events coexist;
- runtime QA method.

## Google Tag, GA4, Google Ads, And Floodlight

Check:

- classify ambiguous Google analytics objects as GA4/current Google tag unless
  tag type, property ID, or explicit evidence proves UA;
- identify Google tag/config vs event tags;
- verify consent mode default/update timing;
- verify conversion linker where Ads conversions need it;
- verify server container URL/transport URL before judging placeholder-looking
  IDs or missing client-side blocking triggers;
- map every GA4 standard/ecommerce event to the official event schema;
- verify event-level parameters, `items`, item fields, value/currency, and
  transaction IDs;
- check Floodlight activity/group parameters and custom variables against
  official setup.

Common findings:

- UA Enhanced Ecommerce paths feeding GA4 without mapper proof;
- duplicate page_view from config plus event tag;
- Ads/Floodlight conversions missing value/currency/order ID;
- consent mode update firing after dependent tags;
- client-to-server transport misclassified as broken client-side tag.

## Meta Pixel And Conversions API

Check:

- base/init and PageView sequencing;
- event names against official standard events;
- content IDs, contents, value, currency, event ID, and user-data handling;
- browser/server deduplication;
- consent gating before Pixel/CAPI event dispatch;
- PII hashing and legal-owner assumptions.

Prefer template/native implementations when they preserve feature parity and
reduce custom HTML risk.

## TikTok

Check:

- base code vs event code separation;
- standard event names and parameter names;
- content IDs, contents, value, currency, quantity, and event ID;
- enhanced matching fields and hashing/consent;
- duplicate events in Events Manager.

## Pinterest

Check:

- base tag and PageVisit/event sequencing;
- product IDs/items, value, currency, order ID, and event IDs;
- Pinterest Tag Helper results;
- consent gating for advertising storage.

## Microsoft Advertising UET

Check:

- UET base tag presence and sequencing;
- custom events/conversion goals;
- revenue/value/currency/order ID fields;
- UET Tag Helper and Ads diagnostics;
- consent mode or CMP gating when applicable.

## LinkedIn Insight Tag

Check:

- base Insight Tag and conversion event setup;
- partner ID and conversion ID consistency;
- conversion deduplication when CAPI exists;
- PII/user-data handling;
- campaign/platform validation.

## Criteo

Check:

- OneTag loader and event tags;
- event names and item arrays against official OneTag events;
- product IDs, prices, quantities, currency, transaction ID, and email/hash
  handling;
- consent and retargeting rules;
- duplicate product-event hits.

## Affiliate Platforms Such As Awin

Check:

- sale/lead tracking contract;
- order ID, amount, currency, voucher, commission group, product feed IDs, and
  deduplication;
- cookie/attribution dependencies;
- consent/legal basis and advertiser program rules.

## Piano Analytics

Use the Piano Analytics playbook when tags, templates, variables, or custom code
reference Piano, AT Internet, SmartTag, PA SDK, `pa.*`, `pianoAnalytics`,
`ATInternet`, or Piano collection endpoints.

Check:

- implementation path: PA SDK GTM template, SmartTag template, custom HTML, or
  server-side routing;
- site/collect domain configuration and environment;
- page display/event naming and property mapping;
- default fed properties vs custom properties;
- privacy mode, consent exemption configuration, and contains-personal-data
  flags;
- consent state timing and whether exempted events are intentionally exempt;
- campaign/source properties and user identifiers;
- ecommerce events, product properties, and transaction properties when present;
- server-side Stape/GTM server setup when visible;
- runtime collection requests and Piano debugger/platform validation.

Common findings:

- SmartTag and PA SDK patterns mixed without rationale;
- consent exemption used as a shortcut for non-exempt analytics;
- personal data flags missing on identifier-like properties;
- page/event properties built from stale URL/title variables in SPAs;
- custom HTML loader duplicated by a maintained Piano GTM template.

## CMPs: Didomi, OneTrust, Cookiebot, Axeptio, Consentmanager.net

Check:

- CMP vendor and implementation path;
- Consent Initialization default state before any dependent tags;
- CMP-ready and consent-update events;
- Google Consent Mode v2 fields where applicable;
- tag firing/blocking triggers vs native consent settings vs trigger groups;
- pageview/base tag coherence inside each vendor family;
- regional rules and legal-owner blockers;
- storage/cookie writes before consent.

For consentmanager.net specifically, check:

- GTM integration mode: automatic, semi-automatic, manual blocking, or consent
  mode integration;
- Google Consent Mode v2 setup and update timing;
- Google Ad Manager/GPT consent integration if publisher tags exist;
- whether CMP events are used consistently across pageview-level tags.

## Google Publisher Tag And Google Ad Manager

Use this playbook when tags/custom code reference `googletag`, GPT, GAM, ad
slots, ad personalization settings, or publisher ad requests.

Check:

- GPT library load and command queue sequencing;
- slot definition, targeting, and refresh behavior;
- consent/privacy settings before ad requests;
- limited ads/non-personalized ads configuration where applicable;
- duplicate GPT library loads or duplicate slot refreshes;
- CMP/GAM integration, especially with consentmanager.net or Google Consent
  Mode;
- performance impact of repeated ad-refresh tags.

## Marfeel

Check:

- Marfeel SDK loader path and GTM implementation;
- pageview/article-view event timing;
- SPA or infinite-scroll refresh logic;
- consent gating for analytics/personalization categories;
- duplicate SDK load or duplicate pageview events.

## Outbrain

Check:

- base pixel and event pixel separation;
- event names and conversion parameters;
- order ID/value/currency for conversions;
- consent gating for advertising storage;
- duplicate conversion/pageview hits.

## Logora

Check:

- JavaScript SDK vs server-side SDK implementation path;
- widget/community feature initialization context;
- user identifier and authentication data handling;
- consent/legal basis for community or personalization features;
- duplicate SDK load and DOM-ready timing.

## Unknown Or Unlisted Vendors

For vendors not covered here:

- search official vendor documentation first;
- identify base/event/sequencing, payload contract, consent, identifiers, and
  validation method;
- document failed official-source search and lower confidence if no official
  source is found;
- avoid creating GTM-side guesses for missing source-site/dataLayer fields.
