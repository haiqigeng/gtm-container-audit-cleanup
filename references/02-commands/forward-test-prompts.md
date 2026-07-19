# Forward-Test Protocol

Forward tests evaluate the skill from raw artifacts, not from a description of
the expected defect. Use previously unseen or synthetic exports and review the
three artifacts separately before inspecting the final cleanup plan.

## Test Families

### Operational Regression

Include exports with:

- setup-only tags without firing triggers;
- active and paused duplicate tags;
- variables used only by paused tags;
- missing variable, trigger, folder, tag-sequence, and template references;
- empty, one-member, duplicate-member, nested, and cyclic trigger groups;
- invalid/always-true regex, contradictory conditions, and ineffective blockers;
- duplicate paths/code/templates and built-in wrappers;
- empty, singleton, overloaded, and unfiled folder layouts;
- mixed naming conventions and duplicate proposed names.

Pass condition: Run 1 catches each source defect or records a correct zero row
without relying on Runs 2 or 3.

### Configuration Regression

Include:

- wrong dataLayer paths and event-time availability;
- revenue or quantity formulas that are syntactically valid but logically wrong;
- arrays required by vendor tags but scalars supplied by variables;
- nested variables, cycles, missing values, null fallbacks, and type coercion;
- GA4 standard events with wrong ecommerce dataLayer/item contracts;
- media events with wrong IDs, item shape, currency/value, or deduplication;
- consent outputs with duplicated conditions;
- server-bound transporter tags without client blockers in two variants: one
  with a complete recursively sourced consent parameter/settings contract and
  one with missing or partial forwarding;
- custom code with multiple branches, returns, network/storage/DOM effects,
  unsafe APIs, fixed product slots, and parse failures;
- client/server routing fields that should not be judged like ordinary browser tags.

Pass condition: Run 2 states literal object behavior, covers every logic leaf and
code line, traces all references, checks official contracts, and produces
source-linked defects. Generic prose must fail validation.

### Architecture Regression

Include:

- funnel `question 1`, `Q1`, and `step 1` paths with different conditions;
- duplicate loaders with different names;
- same payload on different routes;
- standard and custom purchase events with revenue duplication risk;
- shared consent helpers used for different Consent Mode outputs;
- product/country variants that are meaningful and variants that are naming drift;
- browser/server duplicate event paths with and without event-ID deduplication;
- individually correct but business-obsolete tags;
- intentionally distinct same-vendor destinations.

Pass condition: Run 3 assesses every member and chain, distinguishes intentional
variants from real overlap, and defines an exact target architecture.

## Reconciliation Adversaries

Test that compilation fails when:

- sanitation says consolidate but architecture says intentional variant;
- two reviews reuse one operation key for different mutations;
- one operation deletes an object another operation changes;
- remaps omit consumers or target a deleted object;
- a high-risk operation lacks challenge evidence;
- one run is pending or uses a different source hash.

Test that future-state validation fails when a planned change creates a missing
reference, duplicate ID, orphan, new folder/trigger issue, or unresolved cleanup finding.

Test that shard merge fails when one item or file is missing, duplicated,
pending, belongs to another run kind, or uses another source hash.

## Human Review

Ask a web analyst who did not inspect the source export to review the workbook.
They should be able to understand each problem, affected objects, impact, exact
action, priority, readiness, and QA. The workbook must not reveal client secrets,
repeat the same conclusion across columns, exceed eight tabs/six columns, or mix
the cleanup plan with a change log.

## No-Cheat Rule

Do not include expected findings in the execution prompt. Keep fixture labels
neutral. Evaluate false positives as well as misses, and compare each run's raw
artifact before viewing reconciliation.
