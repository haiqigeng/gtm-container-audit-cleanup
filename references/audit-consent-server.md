# Consent And Server-Side Audit

Use this reference for consent/CMP, consent mode, browser-to-server transport,
and server-side GTM caution checks. Apply `POL-004`, `POL-008`, `POL-108`, and
`POL-106` from `policy-register.md`.

## Contents

- Consent And Privacy
- Consent Timing Patterns
- Client-To-Server Google Tag Patterns
- Server-Side GTM Checks

## Consent And Privacy

Check:

- CMP presence, vendor categories, and region handling;
- Consent Initialization behavior and default consent state;
- native Google consent settings and Consent Mode updates;
- firing and blocking triggers by vendor category;
- base/pageview/event consistency inside each vendor family;
- cross-region behavior for EEA/UK/Brazil/California/internal policy zones;
- whether legal/privacy owner approval is required before mutation.

Flag mixed pageview consent patterns inside the same vendor family unless the
timing rationale is documented.

## Consent Timing Patterns

| Pattern | Use when | Watch out for |
| --- | --- | --- |
| Firing trigger plus blocking trigger | Consent state is reliable before the event fires. | Early pageviews may slip through if CMP is late. |
| Trigger group: pageview/event plus consent-ready/granted | Event can happen before CMP resolves. | More objects to maintain. |
| Native consent settings | Google tags with correctly initialized consent mode. | Does not replace a consent banner or legal decision. |
| Direct CMP-ready firing | The tag intentionally fires once at consent resolution with stable page context. | Can miss original event context or duplicate pageviews. |

## Client-To-Server Google Tag Patterns

In a web container that sends events to a server-side container, a browser
Google tag or Google event tag can be a transport mechanism rather than the
final analytics or media destination. Do not classify it as broken only because
the client-side tag has a placeholder-looking ID, a non-final measurement ID, a
media-oriented name, or no client-side blocking trigger.

Treat the tag as `server-container validation needed` when any of these signals
exist:

- `server_container_url`, `transport_url`, first-party tagging endpoint, or an
  S2S/gateway naming pattern;
- Google tag or Google event tag type used with media/vendor naming;
- placeholder-like destination such as `G-XXXXXX` together with a server
  endpoint or routing parameters;
- event parameters or settings that forward consent, CMP groups, cookie consent,
  `ad_storage`, `analytics_storage`, `ad_user_data`, `ad_personalization`,
  `event_id`, click IDs, user data, or vendor identifiers;
- evidence that destination routing, consent checks, enrichment, or vendor
  forwarding happens in the server container.

Before recommending mutation, verify the browser-to-server payload, server
container client, tags, transformations, consent logic, destination mapping,
consent enforcement location, and deduplication/event IDs.

Without server-container export/API evidence, network traces, or platform logs,
do not replace placeholder-looking IDs, add or remove blocking triggers, pause
the tag, or classify the route as definitively broken.

## Server-Side GTM Checks

Only audit server-side GTM when in scope or visible in evidence. Check:

- tagging server URL and first-party custom domain where appropriate;
- endpoint reachability and browser event receipt;
- CSP, firewall, or ad-blocking behavior;
- production mode, server count/redundancy, monitoring, and alerting;
- clients, tags, transformations, and forwarding rules;
- consent/privacy configuration across browser-to-server and server-to-vendor;
- exclusion or transformation of non-GA4/vendor-specific parameters before GA4;
- template/client/runtime currency.

Treat Google Optimize/server-side mixed checks as obsolete; Optimize is sunset
and belongs in deprecated-tag cleanup, not current endpoint validation.
