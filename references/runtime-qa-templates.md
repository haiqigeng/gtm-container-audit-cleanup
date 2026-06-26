# Runtime QA Templates

Use this reference when website behavior, consent timing, duplicate hits,
network payloads, SPA routing, server-side routing, or vendor platform
acceptance matters. Exported GTM JSON cannot prove these checks.

## QA Evidence Header

```text
QA date:
Environment: production | staging | preview | local
Browser/device:
URL(s):
Consent state(s):
GTM container/workspace/version:
Tag Assistant session:
Network capture:
Vendor platform/debug tool:
Known limitations:
```

## Consent QA Matrix

Run each relevant page/event under these states:

| State | Required checks |
| --- | --- |
| Before consent choice | Consent defaults set before tags; no prohibited vendor hits; CMP-ready timing observed. |
| Refused all | Marketing/analytics tags blocked or sent only with allowed cookieless/consent-mode behavior; no storage writes outside allowed categories. |
| Analytics only | Analytics tags behave as intended; marketing tags blocked; Google consent state matches policy. |
| Marketing accepted | Marketing tags fire only after consent; consent update precedes dependent tags; payloads include required consent signals where applicable. |
| Change preference | Tags react to consent update without duplicate pageview/conversion hits unless documented. |

Record CMP event name, GTM event name, tag firing time, consent state, network
request, cookies/storage writes, and blocker.

## Pageview And SPA QA

For pageview/base/config tags:

- initial page load fires exactly as intended;
- CMP-ready and trigger-group patterns are coherent within each vendor family;
- SPA route change fires virtual pageviews where expected;
- stale page title/path/referrer values are not reused after route change;
- pageview tags do not duplicate on back/forward navigation unless intentional;
- server-side endpoint receives the expected pageview payload when applicable.

## Ecommerce QA

For each funnel event in scope:

- `view_item`
- `add_to_cart`
- `begin_checkout`
- `add_shipping_info`
- `add_payment_info`
- `purchase`
- vendor-specific equivalents

Check:

- dataLayer event name and timing;
- event-level fields: value, currency, transaction ID, coupon, tax, shipping;
- `items` array and item fields;
- one-item and multi-item behavior;
- empty/missing/null behavior;
- outgoing GA4/vendor payload shape;
- duplicate event risk;
- vendor/debug platform acceptance.

## Network QA Columns

```text
URL:
Action:
Consent state:
GTM event:
Tag name:
Request host:
Request path:
Status:
Payload fields observed:
Expected fields:
Missing / unexpected fields:
Cookies or storage written:
Duplicate count:
Evidence link / screenshot:
Result: Pass | Fail | Blocked | Not applicable
```

## Server-Side QA

When server-side routing is visible or in scope:

- verify browser-to-server request endpoint and status;
- verify first-party/custom-domain endpoint configuration;
- verify consent, click IDs, event IDs, and user data forwarding;
- verify server clients/tags/transformations;
- verify server-to-vendor destinations and exclusions;
- verify browser/server deduplication IDs;
- verify monitoring/logging expectations.

Without server-container export/API evidence, network traces, or platform logs,
classify server-side conclusions as `More info needed`.

## Vendor Platform QA

Use vendor/debug tools when available:

- GA4 DebugView and Tag Assistant;
- Google Ads/Floodlight diagnostics;
- Meta Pixel Helper and Events Manager;
- TikTok Pixel Helper / Events Manager;
- Pinterest Tag Helper;
- Microsoft UET Tag Helper;
- LinkedIn Insight Tag diagnostics;
- Criteo/affiliate platform diagnostics;
- Piano Analytics debugger or collection validation where available;
- CMP debug panel or consent log.

If platform validation is unavailable, record the missing access as a blocker
and lower confidence.
