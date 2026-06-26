# Forward-Test Prompts

Use these prompts to test whether an agent follows the skill on realistic tasks.
Pass raw artifacts and the skill path. Do not pass expected answers or your
diagnosis.

## Test 1: Export-Only Audit With Custom Code

```text
Use the GTM container audit cleanup skill at <skill path>. Audit this exported
GTM container JSON only and produce a workbook or CSV-set audit plus cleanup
plan. Do not mutate GTM. CMP is unknown. Naming standardization is less
important than semantic validation.
```

Expected validation:

- Custom HTML and Custom JavaScript objects are semantically reviewed, not only
  inventoried.
- Workstream reconciliation is present.
- Missing runtime/CMP evidence is deferred with blockers.
- Cleanup plan includes no-change/deferred rows for families without mutations.

## Test 2: Limited Vendor Audit

```text
Use the GTM container audit cleanup skill at <skill path>. Perform a limited
audit only for Piano Analytics and consent routing in this exported GTM
container JSON. Produce a client-readable report. Do not review unrelated vendor
payloads except where they share triggers, variables, or consent dependencies.
```

Expected validation:

- Output says `Limited audit`.
- Excluded workstreams are `User-excluded`, not `Done`.
- Piano Analytics official docs/playbook are used.
- Shared consent dependencies are mapped.

## Test 3: Runtime QA Request

```text
Use the GTM container audit cleanup skill at <skill path>. Build a runtime QA
plan for validating consent, pageview tags, ecommerce events, and server-side
routing after a GTM cleanup. Use Tag Assistant/network/vendor-platform evidence
where available, but do not invent observed results.
```

Expected validation:

- QA matrix includes consent states, pageview/SPA behavior, ecommerce, network,
  and server-side checks.
- Unknown evidence is blocked, not guessed.

## Test 4: Same-Container Import JSON

```text
Use the GTM container audit cleanup skill at <skill path>. From this original
export and this proposed cleaned export, create a same-container GTM View
Changes import artifact and a change log. Preserve review readability.
```

Expected validation:

- Name-preserving route is selected for View Changes.
- Built-in variables, folders, and custom-template dependencies are handled.
- Generated artifact is self-QA'd.
- Broad rename churn is avoided or deferred.

## Test 5: Severity Calibration

```text
Use the GTM container audit cleanup skill at <skill path>. Review these findings
and assign severity, priority, confidence, and recommended next action:
<raw finding list>
```

Expected validation:

- Consent/revenue issues are not undercalled.
- Naming-only/hygiene issues are not overcalled.
- Confidence remains separate from severity.
