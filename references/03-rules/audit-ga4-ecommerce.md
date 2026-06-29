# GA4 And Ecommerce Audit

Use this reference for GA4/current Google tag, Google ecommerce, ecommerce
dataLayer, and standard ecommerce variable checks. Apply `POL-004`, `POL-006`,
`POL-007`, and `POL-109` from `policy-register.md`.

## Contents

- Google Event Classification
- GA4 DataLayer Contract
- GA4 And Google Tag Checks
- Standard Ecommerce Variable Checks
- Missing Events And Readiness

## Google Event Classification

Universal Analytics is sunset. Treat ambiguous Google analytics events, Google
ecommerce variables, and Google event tags as GA4/current Google tag tracking
unless evidence proves a UA exception:

- UA tag type;
- `UA-` property ID;
- explicit legacy requirement from the user;
- verified mapper that intentionally converts old UA Enhanced Ecommerce pushes
  to GA4 payloads.

Treat legacy events such as `productDetailImpression`, `purchaseImpression`,
`addToCart`, `removeFromCart`, `checkout`, or `checkoutOption` as migration
candidates, not proof that the target should remain UA.

Treat active paths such as `ecommerce.purchase.actionField.*`,
`ecommerce.purchase.products.*`, `ecommerce.add.products.*`,
`ecommerce.detail.products.*`, `ecommerce.checkout.products.*`, and
`ecommerce.impressions` as high-risk legacy sources when they feed GA4 or media
payloads without a verified mapper.

## GA4 DataLayer Contract

For every GA4 standard or ecommerce event, review both:

- GTM tag/event configuration;
- website event payload or dataLayer format that feeds the tag.

Create a schema map with:

- implemented event and GTM firing trigger event;
- official GA4 event name;
- website/dataLayer event name or runtime event source;
- official event-level parameters such as `value`, `currency`,
  `transaction_id`, `tax`, `shipping`, `coupon`, `payment_type`,
  `shipping_tier`, `item_list_id`, and `item_list_name`;
- official `items` array and item-scoped fields such as `item_id`, `item_name`,
  `item_brand`, `item_category`, `item_category2`-`item_category5`,
  `item_variant`, `price`, `quantity`, `discount`, `coupon`, `index`,
  `item_list_id`, and `item_list_name`;
- GTM source paths and helper variables;
- legacy UA-path risk;
- fixed product-position risk such as `products.0`, `products[0]`, or
  separately hardcoded product 1/product 2/product 3 fields;
- outcome: correct, GTM mapping fix, website/dataLayer fix, or blocked pending
  Preview/debug evidence.

Do not create custom JavaScript to invent missing GA4 fields that the website
should send. Helpers are acceptable only when they transform a complete current
event payload, normalize known fields, add guards, or reduce duplicated logic.

## GA4 And Google Tag Checks

Check:

- Google-event classification: GA4/current Google tag by default, UA only as a
  documented exception;
- Google tag / GA4 configuration path and sequencing;
- official GA4 recommended/ecommerce documentation before judging event names,
  dataLayer format, variables, and payloads;
- schema map for every standard/ecommerce event;
- transaction IDs, item arrays, currency, value, coupon, and affiliation;
- PII risk in custom dimensions/parameters;
- duplicate page_view or ecommerce events;
- deprecated UA tags, UA variables, and UA-only ecommerce logic;
- Google Ads conversion linker and Ads conversion tags when in scope;
- consent mode behavior for Google tags in relevant regions.

Legacy starter map, only after dataLayer validation:

| Legacy event | GA4 candidate |
| --- | --- |
| productDetailImpression | view_item |
| product listing | view_item_list |
| addToCart | add_to_cart |
| removeFromCart | remove_from_cart |
| purchaseImpression | purchase |

## Standard Ecommerce Variable Checks

Always review standard and frequently reused ecommerce variables:

- transaction ID, order ID, affiliation, coupon, currency, revenue, value, tax,
  shipping, discount, subtotal, and total price;
- total quantity, item count, cart size, and product quantity;
- product/item IDs, SKUs, names, brands, categories, variants, prices,
  quantities, images, URLs, and list positions;
- `items`, `products`, checkout products, purchase products, add-to-cart
  products, remove-from-cart products, and impression products;
- derived helper variables used by media, affiliate, feed, or custom HTML tags.

For each variable, check:

- current event source path versus stale dataLayer history;
- output type: number, numeric string, scalar ID, array, object, array of
  objects, JSON string, joined string, or boolean;
- logical formula correctness, including total quantity reading quantity fields
  and total price covering all items without duplicated indexes;
- whether a total/order value is incorrectly derived from one product unit
  price or a fixed set of product positions instead of the current transaction
  value or item array;
- multi-item support and destination-specific single-item limitations;
- null, missing value, empty array, parsing, and `NaN` handling;
- currency/value consistency and unit-price times quantity behavior;
- every consuming tag field and whether that destination expects the same shape.

Surface concrete logic errors as findings when they affect revenue, conversion,
or remarketing quality.

## Missing Events And Readiness

Identify missing useful GA4 or vendor standard events only after checking whether
the website/dataLayer can already provide the event context and required fields.
If the dataLayer is not ready, report the website/dataLayer contract as the
prerequisite instead of creating tags that cannot send valid data.
