# Official Documentation Sources

Use official platform documentation as the default contract for event names,
required and recommended parameters, value types, payload structures, consent,
deduplication, routing, and validation.

## Registry First

`vendor-registry.toml` is the maintained machine-readable index for common
vendors. Validate it before a formal audit:

```powershell
python -B scripts/gtm_vendor_registry.py
python -B scripts/gtm_vendor_registry.py --online
```

The registry currently covers Google Analytics/Tag/Ads/Floodlight, Meta,
TikTok, Snapchat, Pinterest, LinkedIn, Microsoft Advertising, Criteo, Awin,
Didomi, OneTrust, Cookiebot, Piano Analytics, Google Ad Manager, Outbrain, and
Marfeel.

## Source Selection

For every implemented vendor or event family:

1. Detect the vendor from tag type, template public ID, endpoint, code, or
   configuration, not from the object name alone.
2. Use the matching registry entries.
3. Open the exact event, payload, consent, or setup page needed for the
   judgment; a vendor home page is insufficient when field correctness matters.
4. If the vendor or contract is absent, search the current official vendor
   documentation.
5. Record the official URL and access date in the semantic review.
6. If no official source can be found, document the failed search, lower
   confidence, and avoid inventing a contract.

Blogs and community posts may explain behavior but cannot be the sole basis for
a confirmed cleanup finding.

## Google Defaults

- Treat ambiguous current Google Analytics event tags as GA4/current Google tag
  unless export evidence proves a Universal Analytics exception.
- For GA4 standard, recommended, and ecommerce events, use the official event
  name and documented event/dataLayer parameter shape. Do not reconstruct a
  field in Custom JavaScript when the website's documented ecommerce payload
  should already provide it.
- Keep Universal Analytics and Google Optimize only as deprecated-technology
  detection rules.
- For consent, use official Google consent-mode and GTM consent APIs together
  with the CMP vendor's official integration guidance.
- For browser-to-server tagging, use the official send-data and server-side
  routing documentation, but do not infer the receiving server container's
  client, transformation, consent, or vendor behavior without that evidence.

Core Google entry points:

- GTM API: <https://developers.google.com/tag-platform/tag-manager/api/v2>
- dataLayer: <https://developers.google.com/tag-platform/tag-manager/datalayer>
- GA4 events: <https://developers.google.com/analytics/devguides/collection/ga4/reference/events>
- GA4 ecommerce: <https://developers.google.com/analytics/devguides/collection/ga4/ecommerce>
- consent mode: <https://developers.google.com/tag-platform/security/concepts/consent-mode>
- server-side tagging: <https://developers.google.com/tag-platform/tag-manager/server-side>

## Freshness

Recheck official sources when:

- the user requests current or latest guidance;
- consent, privacy-sensitive configuration, or vendor payload correctness is a
  material finding;
- a native template, event schema, or server-routing capability may have
  changed;
- a deprecation or sunset determines deletion or migration;
- the audit is a formal client deliverable.

The registry `reviewed_on` date is a maintenance signal, not proof that every
linked page is unchanged. Update the registry instead of copying URL tables
into additional references.
