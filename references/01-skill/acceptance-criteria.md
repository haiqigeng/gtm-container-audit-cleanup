# Acceptance Criteria

Use this file to decide whether a skill execution is good enough to deliver.

## Complete Result Criteria

A complete audit or cleanup plan must show:

- scope, source evidence, and evidence freshness;
- inventory and dependency mapping for in-scope objects;
- measurement diagnosis for meaningful object families;
- D1-D3 semantic review from available export/API/source evidence;
- official documentation basis for material GA4, CMP, vendor, ecommerce, and
  server-side judgments;
- cleanup decisions for each material family: keep, fix, consolidate, delete
  candidate, defer, document exception, not applicable, or user-excluded;
- user-facing output that is concise, actionable, and coherent with proof tabs;
- next step that names the required approval, evidence, QA, or execution route.

## Configuration Logic Clarity

D1-D3 review is acceptable only when it demonstrates the object's actual
functionality. Generic proof that an object was checked does not count.

For every meaningful object, the review must explain:

- what the object is supposed to do;
- what input or source it uses;
- what condition, formula, mapping, trigger, template setting, or code logic it
  applies;
- what output, side effect, vendor payload, consent state, or firing behavior it
  produces;
- which tags, triggers, variables, custom code, or templates consume or depend
  on it;
- whether the functionality is coherent with the name, event context, business
  role, platform role, and official documentation.

For template-based tags and variables, the review must judge configuration
logic, not copy parameters. It must connect event name, trigger context,
template fields, variable values, expected data type or payload shape, consent
state, and vendor/platform purpose. If the template is a Google, CMP, media,
affiliate, publisher, or server-forwarding object, the review must compare the
configuration with the relevant official contract or document the missing
official source.

For custom code, the review must explain:

- what the code reads;
- what it writes, returns, pushes, loads, mutates, or calls;
- which variables or GTM objects it references;
- whether it interacts with DOM, cookies, storage, network calls, dataLayer,
  CMP, or vendor scripts;
- whether the behavior is safe, obsolete, duplicated, risky, or unclear;
- what runtime QA is still needed when behavior cannot be proven from export
  evidence.

Unacceptable summaries include:

- `custom code inspected`;
- `configuration reviewed`;
- `no issue found`;
- `external URL detected`;
- `no obvious browser side effect`;
- `see config`;
- `static scan completed`;
- `D3 required`;
- `review later`.

## Change Log Criteria

A post-cleanup change log is acceptable only when:

- every applied/generated change has a row;
- each row explains what changed in human terms;
- before/after values are shown when they affect behavior, names, routing,
  dependencies, QA, or rollback;
- each row maps to a cleanup-plan operation ID;
- the user can understand what changed, why, and how to validate it without
  opening GTM View Changes.

## Failure Criteria

Mark the deliverable `Incomplete / blocked` when:

- D1-D3 work is missing while source evidence is available;
- measurement diagnosis is missing for meaningful affected families;
- custom code is not inspected at export/config level;
- cleanup actions require future audit work to decide correctness;
- user-facing outputs are too generic to explain functionality or impact.
