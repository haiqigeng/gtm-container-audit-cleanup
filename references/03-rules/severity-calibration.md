# Severity Calibration

Use this reference when assigning severity and priority. Severity describes
impact. Priority describes when to act.

## Severity Scale

| Severity | Use when |
| --- | --- |
| Critical | Clear consent/legal violation, major analytics/conversion collection broken, production mutation can cause immediate data loss, or revenue-critical events are unusable. |
| High | Material data quality, privacy, attribution, or revenue risk that is likely to affect decisions or media optimization. |
| Medium | Functional but fragile, duplicated, inconsistent, hard to maintain, or likely to cause future errors. |
| Low | Minor hygiene, naming, documentation, or low-risk maintainability issue. |
| Info | Observation, context, or verified correct behavior with no change recommended. |

Priority values:

- `P0 Now`
- `P1 This sprint`
- `P2 Planned cleanup`
- `P3 Backlog`
- `Decision needed`

## Calibration Examples

| Finding | Suggested severity | Suggested priority |
| --- | --- | --- |
| A direct browser marketing/vendor request is initiated before its required consent. | Critical | P0 Now |
| A first-party server transporter fires without a client blocker but forwards a complete consent contract for server enforcement. | Info; no client-side defect by itself | No action unless the forwarding contract is incomplete |
| Purchase event does not fire or is blocked for all users. | Critical | P0 Now |
| GA4 purchase value/currency/item payload materially wrong. | High | P1 This sprint |
| Ads/Floodlight/Meta purchase conversion missing order ID or value. | High | P1 This sprint |
| Active GA4 ecommerce uses UA Enhanced Ecommerce paths without mapper proof. | High | P1 This sprint |
| CMP-ready/pageview gating is inconsistent across same vendor pageview tags. | High or Medium depending on observed leakage/duplication | P1 or Decision needed |
| Custom HTML injects third-party script without consent or origin rationale. | High | P1 This sprint |
| Custom JS fixed-index item variables power multi-item product payloads. | High or Medium depending on consumer importance | P1 or P2 |
| Duplicate page_view or PageView hits for analytics/media. | High if used for billing/optimization, otherwise Medium | P1 or P2 |
| Trigger group has one member and adds no behavior. | Medium | P2 Planned cleanup |
| Unused trigger/variable with no consumers after dependency sweep. | Low or Medium if confusing/risky | P2 or P3 |
| Duplicate names obscure maintenance but behavior is correct. | Low or Medium depending on release risk | P2 or P3 |
| Missing folder organization. | Low | P3 Backlog |
| External behavior is not verifiable from a container-only audit. | Info or More info needed; severity follows the configured risk | Decision needed |

## Escalation Rules

Escalate when:

- consent/privacy risk is involved;
- revenue/conversion or paid-media optimization is affected;
- a shared helper or trigger powers many tags;
- a custom-code error can break several vendors;
- a server-bound route has missing, partial, swapped, stale, or inconsistent
  consent forwarding and the affected destination risk is high;
- an issue affects all pageviews or all purchases.

Downgrade when:

- object is paused and has no consumers;
- stronger container or owner evidence proves no impact;
- issue is naming-only with no behavior risk;
- issue is inside a user-excluded scope.

## Confidence

Always pair severity with confidence:

- `High`: complete export/API evidence and the official contract agree.
- `Medium`: export/API evidence is strong but external behavior is not
  verifiable from the container.
- `Low`: inference from names, old evidence, partial screenshots, or missing
  official documentation.

Do not hide low confidence by lowering severity. Use severity for possible
impact and confidence for evidentiary strength.
