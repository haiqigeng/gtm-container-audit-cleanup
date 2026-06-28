# Media And Vendor Audit

Use this reference for media pixels, affiliate tags, publisher tags, vendor
templates, and cross-vendor payload quality. Apply `POL-004`, `POL-005`,
`POL-007`, `POL-008`, and `POL-108` from `policy-register.md`.

## Contents

- Vendor Tag Families
- Payload Shape
- Media Signal Quality
- Vendor-Specific Routing

## Vendor Tag Families

For Meta, LinkedIn, TikTok, Pinterest, Reddit, X/Twitter, affiliates, publisher
ads, and other vendors:

- identify base/config/loaders separately from event-specific conversion tags;
- check that base tags fire before dependent events when required;
- check duplicate pageview/conversion events;
- do not preserve page-specific duplicate `PageView` tags as substitutes for
  real funnel/conversion events;
- prefer native tags or maintained templates where feature parity and consent
  behavior are preserved;
- verify consent gating and regional rules;
- inspect payload fields for PII, incorrect value/currency, missing IDs, or
  hardcoded product assumptions;
- validate event ordering with Tag Assistant/network evidence when possible.

For each vendor, compare event names, base/event sequencing, required
parameters, recommended parameters, and data types against official
documentation when available.

## Payload Shape

For media/vendor payloads, verify field-level shape:

- product IDs, content IDs, item IDs, categories, and item lists often need
  arrays or objects, not one scalar dataLayer variable;
- when the vendor expects an array/object, require a helper/template field that
  builds that shape from the current event's products/items;
- verify helper output for empty, one-item, and multi-item payloads, missing
  fields, and special characters;
- confirm IDs, names, categories, values, quantities, and currency all come from
  the same event context;
- check that custom JS does not return `undefined`, `NaN`, `[object Object]`,
  comma-joined values where arrays are expected, or stale data from a previous
  dataLayer push.

## Media Signal Quality

Infer the platform optimization role:

- final conversion;
- micro-conversion;
- audience or exclusion event;
- attribution helper;
- enhanced matching;
- browser-to-server forwarding event.

Flag invisible business issues when the setup likely trains media platforms on
the wrong action, value, lead type, product/category, market, or funnel step.
Surface them as operations, blockers, owner questions, or QA needs rather than a
strategy essay.

## Vendor-Specific Routing

Use `vendor-playbooks.md` for vendor-specific checks, including GA4, Google Ads,
Floodlight, Meta, TikTok, Pinterest, Microsoft, LinkedIn, Criteo, affiliate,
Piano Analytics, CMPs, Google Publisher Tag/Google Ad Manager, Marfeel,
Outbrain, and Logora.

Use `source-map.md` for official documentation entry points. If a vendor is not
listed, search for official vendor documentation before judging the setup.
