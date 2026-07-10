# GTM Cleanup Intelligence

[![Latest release](https://img.shields.io/github/v/release/haiqigeng/gtm-container-audit-cleanup?sort=semver)](https://github.com/haiqigeng/gtm-container-audit-cleanup/releases/latest)
[![CI](https://github.com/haiqigeng/gtm-container-audit-cleanup/actions/workflows/ci.yml/badge.svg)](https://github.com/haiqigeng/gtm-container-audit-cleanup/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/haiqigeng/gtm-container-audit-cleanup/blob/main/LICENSE)

An open, reusable workflow that helps web analysts and marketing teams decide
whether a Google Tag Manager container measures the right business actions with
the right data, timing, consent, and platform setup.

It goes beyond deleting unused objects. The review follows tags through their
triggers and variables, checks the real configuration or code, compares related
objects, and turns confirmed problems into a practical cleanup plan.

## Who It Serves

- Web analysts, analytics consultants, GTM specialists, and agencies.
- Marketing and media teams reviewing conversion-signal quality.
- Developers, dataLayer owners, and consent owners receiving implementation work.
- Codex, Claude Code, Gemini, and other agents that can follow Markdown skills.

## Questions It Answers

- Does each tag represent the business action named by the event?
- Do its trigger, consent conditions, variables, and payload agree with that action?
- Are GA4 ecommerce and media values sourced and formatted correctly?
- Do computed values such as order value or quantity make business sense?
- Are duplicate loaders, triggers, variables, and code safe to consolidate?
- Is browser-to-server routing coherent without claiming to audit an unseen
  server container?
- Are objects named, grouped, and shared in a readable, scalable way?
- What is safe to change now, and what needs runtime or owner evidence?

## How It Works

The workflow runs three independent reviews:

1. **Container hygiene** finds broken references, duplicates, unused objects,
   single-member trigger groups, legacy setup, and naming/folder drift.
2. **Business logic** reads every object's exported configuration, follows
   referenced variables to their terminal source, compares sibling fields, and
   checks event and payload logic against official vendor documentation.
3. **Custom code** inspects every exported nonblank code line, code behavior,
   side effects, dependencies, safety, and maintainability.

The three reviews are reconciled before an operation is proposed. A scan task,
hash, name, or generic summary cannot become a cleanup finding on its own.

## Inputs

The best starting point is a GTM container export JSON. The skill can also use:

- GTM API/MCP or UI evidence;
- Tag Assistant, dataLayer, browser, network, CMP, and server observations;
- website, business-model, ecommerce, market, and naming context;
- explicit web-container or server-container scope.

A web container that forwards events to a server endpoint can be audited for
its routing. Auditing the receiving server container requires its own export or
equivalent client, transformation, tag, trigger, and variable evidence.

## Outputs

- A concise audit summary and a separate cleanup-plan workbook.
- Two visible workbook tabs for decisions and consolidated hidden proof tabs.
- Reconciled operations with exact action, preconditions, QA, and rollback.
- A validated GTM import JSON or approved direct workspace changes when asked.
- A separate field-level change log after execution or artifact generation.

Cleanup plans explain what should change. Change logs explain what did change.
They are never merged by default.

## Boundaries

The skill does not publish GTM, mutate without approval, make legal decisions,
replace missing website/dataLayer work, or declare an unseen server container
audited. It never deletes an object merely because it is old and never invents
GTM JavaScript to conceal a missing data contract.

## Install And Run

Python 3.11+ is recommended for deterministic checks. `openpyxl` creates XLSX
deliverables; `esprima` adds JavaScript AST facts.

```powershell
python -m pip install -e ".[analysis,dev]"
python -B scripts/gtm_audit_package_build.py container.json --out-dir audit-package --pretty
```

Complete the generated `semantic_review.json`, then validate it:

```powershell
python -B scripts/gtm_semantic_review.py validate container.json audit-package/semantic_review.json
```

The full command sequence is in
`references/02-commands/validation-commands.md`. Agent behavior starts in
`SKILL.md`; the canonical completion rules are in
`references/03-rules/execution-contract.md`.

## Repository Map

- `SKILL.md`: when and how an agent should execute the workflow.
- `references/01-skill/`: users, purpose, inputs, outputs, acceptance, non-goals.
- `references/02-commands/`: runnable checks and QA commands.
- `references/03-rules/`: audit and mutation rules.
- `scripts/`: deterministic source, review, reconciliation, workbook, privacy,
  change-log, packaging, and validation tools.
- `tests/`: regression coverage for the protected workflow.

## Contributing And Releases

Before a release:

```powershell
python -m ruff check --no-cache .
python -m unittest discover -s tests -v
python -B scripts/gtm_self_test.py
python -B scripts/gtm_vendor_registry.py
python -B scripts/check_release.py --tag vYYYY.MM.DD.N
git diff --check
```

Do not commit client exports, workbooks, screenshots, domains, container IDs,
emails, credentials, generated audit packages, or local paths. Clean release
bundles are built with `scripts/build_skill_package.py`.

Releases use Calendar Versioning: `vYYYY.MM.DD` and `vYYYY.MM.DD.N` for a
same-day follow-up. Release notes should explain what changed, why it matters to
analysts, how it was verified, and any remaining limits.

Licensed under the MIT License.
