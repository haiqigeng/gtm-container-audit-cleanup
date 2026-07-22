# GTM Web Analyst Audit & Cleanup

[![Latest release](https://img.shields.io/github/v/release/haiqigeng/gtm-container-audit-cleanup?sort=semver)](https://github.com/haiqigeng/gtm-container-audit-cleanup/releases/latest)
[![CI](https://github.com/haiqigeng/gtm-container-audit-cleanup/actions/workflows/ci.yml/badge.svg)](https://github.com/haiqigeng/gtm-container-audit-cleanup/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/haiqigeng/gtm-container-audit-cleanup/blob/main/LICENSE)

A container-only workflow for understanding and cleaning Google Tag Manager as
a web analyst. It finds routine container clutter, checks what every object
actually does, and reviews whether related tags work together as a coherent
measurement system.

It is designed for Codex, Claude Code, Gemini, and other file-capable agents.

## Who It Helps

- Web analysts, analytics consultants, GTM specialists, and agencies.
- Marketing and media teams reviewing conversion-signal quality.
- Developers, dataLayer owners, and consent owners receiving cleanup work.
- Teams that need a reviewable plan before anyone changes a container.

## Questions It Answers

- What is broken, duplicated, unused, obsolete, or unnecessarily complex?
- Does each tag fire for the action its name and event claim to measure?
- Do triggers and recursive variables provide the expected values at that event?
- Do GA4, ecommerce, media, consent, and server-routing settings follow their
  official configuration contracts?
- Do calculated values such as revenue or quantity make business sense?
- Are apparently different funnel steps, vendor events, or consent routes doing
  the same job?
- What should remain, change, consolidate, or be decided by an owner?
- Can the approved target state be applied without breaking references?

## The Three Reviews

Every complete audit first builds one source-fact map: what objects exist, what
they reference, where values originate, how triggers compare, which formulas
are present, and how consent routes are configured. This prevents three agents
from extracting the same container three different ways.

The audit then runs three independent reviews against that same fact map and
the raw export. The map contains evidence, not conclusions, so one review still
cannot substitute its conclusions for another.

The package gate reconstructs this map and the audit context from source. A
copied or stale hash is not enough to pass.

1. **Operational sanitation** checks references, unused and paused-only
   objects, exact duplicates, trigger groups, regex and blocker defects,
   sequencing, schedules, folders, Zones, templates, built-ins, naming,
   consent-control shape, and active-root lifecycle hygiene. Remediation for a
   nested/cyclic trigger group is dependency-ordered, never a blind flatten.
   Payload comparison deliberately excludes route, consent, sequencing,
   schedule, and firing controls so equal payloads on conflicting routes remain
   visible; deleting a consumed object requires complete remap coverage.
2. **Configuration correctness** reviews every tag, trigger, variable,
   Zone, template, client, Google tag configuration, and transformation. It
   follows every referenced variable to every possible terminal source, checks
   every source-owned configuration branch exactly once, keeps cross-object
   leaves as D3/contract context, inspects every exported executable custom-code
   line, and
   tests all matched and unknown-host vendor contracts. UI/export metadata is
   excluded from host inference, and recognized transport endpoints stay in the
   server-routing contract. Cross-object trigger/sequence conditions, empty
   structures, destination peers, and downstream consumer-event fields remain
   citeable D3 evidence, including peer server/type/consent state without
   assuming destination inheritance. Decisive malformed/missing/cyclic source
   states create locked Issue/Unclear obligations across branches, D3,
   contracts, defects, and the overall verdict; duplicate review identities
   fail rather than overwrite. GA4 purchase/refund reviews include
   explicit transaction-ID obligations. Opaque custom templates and incomplete
   parser coverage cannot be certified as Correct. Community-template terms,
   help, tests, licenses, permissions, and comments are not miscounted as
   executable lines; permissions remain contract evidence. Parser fallback describes
   every individual code segment, not merely its hashes, and cannot invert a
   source-proven send, request, DOM/script effect, dataLayer/storage action, or
   return while citing the right tokens. Source-proven health/security signals
   require a finding, concrete proposed action, evidence-bound exception basis,
   or source-specific owner question; relabeling the verdict is not resolution.
   A confirmed technical issue links to exactly one concrete defect.
3. **Business architecture** compares complete execution chains and business
   families. It finds functional overlap, conflicting funnel logic, duplicate
   destinations, Zones governing the same child container, unnecessary
   variants, trigger-group cycles, custom-code business events, route/consent
   variants, browser/server event-destination-consent families, unresolved
   chain edges, and missed consolidation that exact matching cannot reveal.
   Visible unsafe relationships cannot be retained or hidden behind a generic
   container-evidence limit without a candidate-bound operation or precise,
   relationship-specific owner decision. No-op and object/path-mismatched
   operations do not count. Missing runtime deduplication or consent-parity
   proof stays explicitly unproven and cannot be restated as guaranteed,
   identical, synchronized, verified, or equivalent.

The third review also performs an open discovery pass. This catches objects
that look different but serve the same funnel step, use the same terminal data,
send the same business event, or apply conflicting consent logic. Machine-made
candidate lists are the starting point, not the boundary of the audit.
Every added discovery declares a mapped comparison type, is attributed to
suitable locked methods, and inherits any deterministic unsafe-class policy
across candidate subsets/supersets or from its own declared unsafe type.
Retention must cite how every member actually differs; verdicts, dispositions,
owner questions, and zero-discovery attestations are validated as one coherent
decision rather than independent form fields.

Only after all three validators pass are their approved actions reconciled and
simulated against a future copy of the container.

Large reviews can be split into bounded, source-locked shards. The merge tool
refuses missing, duplicate, pending, or source-mismatched work, so scaling the
execution does not reduce audit coverage. Architecture shards include a
separate open-discovery file for added `DISC-*` comparisons and the final
all-object attestation. Configuration shards also keep each code line and D3
logic check in an exact, source-ordered obligation manifest.

## Inputs

The normal input is a complete GTM container export JSON. Source identity,
entity layers, IDs, and shapes are checked before any semantic scaffold is
built; ambiguous or unmodelled identity blocks all three reviews. Equivalent complete,
read-only GTM API or UI configuration evidence is also supported. Website,
business model, ecommerce, market, CMP, media, and server-routing context help
interpret the configuration.
Business inference uses only behavior reachable from active/configured roots.
Orphan logic remains an audit target but cannot redefine the business model,
and a server transport URL is not treated as proof of Google tag gateway.
Exported list-valued domains are normalized, while technical acronyms, generic
consent terms, and advertising labels cannot silently become market, CMP, or
publisher facts. Server-route hosts come only from explicit routing fields.

A web container can be reviewed for the browser-to-server routing visible in
its export. Transport tags do not need separate client-side blockers when the
web configuration demonstrably forwards the required consent state for
server-side enforcement. The audit checks that forwarding contract and keeps
the unseen server behavior outside its verdict. The receiving server container
requires its own complete export for a server-side audit.
Consent-like names/events and arbitrary blockers are only candidates; proof of
forwarding requires both a server route and a behavior-bearing payload chain.

## Outputs

- An audit summary and a separate cleanup-plan XLSX workbook.
- Two visible decision tabs and compact, unprotected proof tabs that analysts
  can unhide when needed.
- Lossless hidden proof: long evidence continues onto another row instead of
  being silently truncated.
- Exact reconciled operations with preconditions, QA, and rollback.
- Deferred operations that exceed the selected cleanup level, plus owner
  decisions and container-evidence limits that still need attention.
- On request and after approval, direct GTM changes or a valid import JSON.
- A separate field-level change log after changes or an import artifact exist.

The cleanup plan says what should change. The change log says what did change.

## What It Does Not Do

This skill does not run GTM Preview, Tag Assistant, browser/network, live CMP,
dataLayer, or vendor-platform QA. It does not make legal decisions, implement a
missing website/dataLayer contract, audit an unseen server container, mutate
without approval, or publish a GTM version.

## Install

Python 3.11+ provides deterministic scaffolds and gates. `openpyxl` creates XLSX
files; optional `esprima` adds JavaScript parser facts. If parser coverage is
unavailable or fails for a code block, the configuration review receives a
mandatory evidence-limit obligation and cannot silently treat empty AST facts
as a clean result.

```powershell
python -m pip install -e ".[analysis,dev]"
```

The full audit requires the deterministic Python pipeline and complete
container evidence. If either is unavailable, report the audit as blocked and
request the missing prerequisite; there is no reduced audit mode.

## Start An Audit

```powershell
python -B scripts/gtm_context_model.py container.json --pretty
python -B scripts/gtm_audit_package_build.py container.json --out-dir audit-package --pretty
```

Present the preflight's provided, high-confidence inferred, and unresolved
context. Resolve material questions in a small JSON file and pass it with
`--context audit-context.json`; non-material questions remain visible without
creating another audit gate.

Complete the three generated review files independently, then validate them:

```powershell
python -B scripts/gtm_operational_review.py validate container.json audit-package/operational_review.json
python -B scripts/gtm_configuration_review.py validate container.json audit-package/configuration_review.json
python -B scripts/gtm_architecture_review.py validate container.json audit-package/architecture_review.json
python -B scripts/gtm_three_run_gate.py container.json audit-package --audit-only --pretty
```

Prefer a fresh reasoning context per run and never provide another run's
verdict artifact as input. For large reviews, run `gtm_review_shards.py check`
after each completed shard, then merge and run the complete validator.

The exact compilation, future-state, workbook, privacy, and change-log commands
are in `references/02-commands/validation-commands.md`.

## Repository Map

- `SKILL.md`: activation and execution instructions for agents.
- `references/01-skill/`: users, questions, inputs, outputs, acceptance, limits.
- `references/02-commands/`: runnable workflow commands.
- `references/03-rules/`: analyst and mutation rules.
- `scripts/`: source scans, three review engines, reconciliation, simulation,
  workbook, privacy, packaging, and validation tools.
- `tests/`: regression fixtures for common and subtle GTM failures.

## Release Checks

```powershell
python -m ruff check --no-cache .
python -B -m unittest discover -s tests -v
python -B scripts/gtm_self_test.py
python -B scripts/gtm_vendor_registry.py
python -B scripts/check_release.py --tag v1.2.0
git diff --check
```

Never commit client exports, generated audits, domains, IDs, credentials,
emails, screenshots, workbooks, or local paths. Release bundles are built with
`scripts/build_skill_package.py`.

Releases use `vMAJOR.MINOR.PATCH` semantic version tags. Pre-release and build
metadata suffixes are accepted when needed, for example `v1.1.0-rc.1` or
`v1.1.0+build.7`; the tag must match the normalized project version for a
versioned release check.

Licensed under the MIT License.
