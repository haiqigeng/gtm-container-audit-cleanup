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
   sequencing, folders, templates, built-ins, naming, and lifecycle hygiene.
2. **Configuration correctness** reviews every tag, trigger, variable,
   template, client, and transformation. It follows every referenced variable
   to its terminal source, checks every configuration branch, inspects every
   exported custom-code line, and tests applicable vendor contracts.
3. **Business architecture** compares complete execution chains and business
   families. It finds functional overlap, conflicting funnel logic, duplicate
   destinations, unnecessary variants, and missed consolidation that exact
   matching cannot reveal.

The third review also performs an open discovery pass. This catches objects
that look different but serve the same funnel step, use the same terminal data,
send the same business event, or apply conflicting consent logic. Machine-made
candidate lists are the starting point, not the boundary of the audit.

Only after all three validators pass are their approved actions reconciled and
simulated against a future copy of the container.

Large reviews can be split into bounded, source-locked shards. The merge tool
refuses missing, duplicate, pending, or source-mismatched work, so scaling the
execution does not reduce audit coverage. Architecture shards include a
separate open-discovery file for added `DISC-*` comparisons and the final
all-object attestation. Configuration shards also keep each code line and D3
logic check in an exact, source-ordered obligation manifest.

## Inputs

The normal input is a complete GTM container export JSON. Equivalent complete,
read-only GTM API or UI configuration evidence is also supported. Website,
business model, ecommerce, market, CMP, media, and server-routing context help
interpret the configuration.

A web container can be reviewed for the browser-to-server routing visible in
its export. Transport tags do not need separate client-side blockers when the
web configuration demonstrably forwards the required consent state for
server-side enforcement. The audit checks that forwarding contract and keeps
the unseen server behavior outside its verdict. The receiving server container
requires its own complete export for a server-side audit.

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
files; optional `esprima` adds JavaScript parser facts.

```powershell
python -m pip install -e ".[analysis,dev]"
```

The full audit requires the deterministic Python pipeline. Without it, an agent
may provide only a clearly labelled limited advisory after the user accepts the
reduced assurance; it must not claim that the complete audit gates passed.

## Start An Audit

```powershell
python -B scripts/gtm_audit_package_build.py container.json --out-dir audit-package --pretty
```

Optional business context can be supplied in a small JSON file with
`--context audit-context.json`.

Complete the three generated review files independently, then validate them:

```powershell
python -B scripts/gtm_operational_review.py validate container.json audit-package/operational_review.json
python -B scripts/gtm_configuration_review.py validate container.json audit-package/configuration_review.json
python -B scripts/gtm_architecture_review.py validate container.json audit-package/architecture_review.json
python -B scripts/gtm_three_run_gate.py container.json audit-package --audit-only --pretty
```

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
python -B scripts/check_release.py --tag vYYYY.MM.DD.N
git diff --check
```

Never commit client exports, generated audits, domains, IDs, credentials,
emails, screenshots, workbooks, or local paths. Release bundles are built with
`scripts/build_skill_package.py`.

Releases use `vYYYY.MM.DD` and `vYYYY.MM.DD.N` for same-day follow-ups.

Licensed under the MIT License.
