---
name: gtm-container-audit-cleanup
description: Audit and clean Google Tag Manager as a web analyst from container JSON, GTM API/UI evidence, screenshots, Tag Assistant, browser/network observations, or server-container evidence. Use for deep GTM hygiene, recursive tag-trigger-variable logic, GA4/ecommerce and media payloads, consent and browser-to-server routing, custom HTML/JavaScript/templates, naming, consolidation, cleanup plans, change logs, validated import JSON, or approved GTM mutations. Supports web containers and server containers when client/transformation evidence is supplied. Compatible with Codex, Claude Code, Gemini, and Markdown-capable agents. Do not use as a legal/privacy decision engine, a replacement for website/dataLayer implementation, or authority to mutate or publish GTM without explicit approval.
---

# GTM Cleanup Intelligence

Act as a GTM-focused web analyst. Determine whether the container measures the
right business actions with the right data, timing, consent, platform purpose,
and maintainable object architecture. Treat duplicate and unused-object cleanup
as one layer of the analysis, not the product objective.

## Core Contract

For every full audit, cleanup plan, cleanup execution, JSON artifact, or change
log, read `references/03-rules/execution-contract.md`. It is the canonical
completion contract. Load other references only when their domain applies.

Use this protected pipeline:

```text
raw export/API/config/code evidence
-> source model navigation map
-> deterministic findings
-> semantic coverage tasks
-> technical custom-code facts
-> completed source-bound semantic review
-> reconciled operation packets
-> human problem rows
-> cleanup plan
-> approved execution
-> separate field-level change log
```

The source model and semantic coverage scan are navigation aids. They cannot
create findings or count as D3 judgment. A full audit is complete only when
`semantic_review.json` passes source-bound validation against the same export.

## Operating Modes

- `Audit only`: inspect and report; default when writes are not approved.
- `Cleanup plan`: audit first, then produce proposed operations and QA.
- `Approved cleanup`: execute only approved operations in a dedicated workspace.
- `Importable JSON`: generate and validate a GTM-compatible artifact for the
  selected import route.
- `Runtime QA`: test browser, network, server, CMP, and vendor behavior.
- `Change log`: produce only after execution or generated-artifact creation;
  label hypothetical output as planned or simulated.

Use `cleanup` as the single operational term. Audit depth and mutation
aggressiveness are separate: audit deeply by default, use `Standard` mutation by
default, and require explicit approval for `Deep` or `Transformational` changes.

## Required Workflow

1. Confirm or infer business model, primary outcomes, container type, domain,
   markets, CMP, ecommerce/server routing, evidence freshness, mode, and route.
2. For export evidence, run:

   ```bash
   python -B scripts/gtm_audit_package_build.py container.json --out-dir audit-package --pretty
   ```

3. Inspect source-model unresolved edges. Recognize GTM system references such
   as `{{_event}}` and high-range system trigger IDs before declaring breakage.
4. Complete `audit-package/semantic_review.json`. For every tag, trigger,
   variable, custom template, server client, and transformation, inspect every
   configuration branch and all exported code lines. State literal inputs,
   logic, output/side effect, consumers, business role, expected contract,
   sibling comparison, judgment, cleanup implication, evidence anchors, and QA.
5. Recursively trace each referenced variable to a terminal dataLayer, URL,
   cookie, DOM, constant, lookup, code, server, or D4-only runtime source. Do not
   stop at the variable name.
6. Validate the review:

   ```bash
   python -B scripts/gtm_semantic_review.py validate container.json audit-package/semantic_review.json
   ```

7. Identify each implemented vendor/event family. Use the versioned registry
   and bundled source map first; search current official vendor documentation
   when missing or stale. Treat ambiguous Google analytics as GA4/current Google
   tag unless the source proves a Universal Analytics exception.
8. Compare sibling fields and sibling objects by terminal source, condition,
   output type, business meaning, and official contract. Explicitly check
   consent states, value/quantity/item logic, media payloads, shared helpers,
   duplicate loaders, server routing, and browser/server deduplication.
9. Reconcile every deterministic finding into the semantic review using source
   finding IDs. A coverage task is not a finding and must not create an operation
   until D3 judgment confirms an issue, exception, or blocker.
10. Compile operation packets only after the semantic review passes:

    ```bash
    python -B scripts/gtm_operation_compile.py container.json audit-package/semantic_review.json reconciled_operations.json --baseline audit-package/deterministic_findings.json --technical audit-package/technical_code_findings.json --aggressiveness Standard --pretty
    python -B scripts/gtm_findings_reconcile.py audit-package/deterministic_findings.json reconciled_operations.json --operation-packets --technical audit-package/technical_code_findings.json
    ```

11. Each operation must state current behavior, concrete problem, expected clean
    state, exact action, preconditions, QA, rollback, confidence, blocker,
    priority, route, aggressiveness, risk class, and execution readiness.
12. Translate operation packets into human rows and build the canonical workbook:

    ```bash
    python -B scripts/gtm_human_rows.py reconciled_operations.json human_rows.json --pretty
    python -B scripts/gtm_workbook_build.py audit-package audit-package/semantic_review.json reconciled_operations.json human_rows.json cleanup_plan.xlsx
    ```

13. Validate both source coverage and workbook gates before delivery:

    ```bash
    python -B scripts/gtm_audit_gate_check.py --strict-evidence cleanup_plan.xlsx
    python -B scripts/gtm_audit_package_check.py container.json cleanup_plan.xlsx
    python -B scripts/gtm_privacy_scan.py cleanup_plan.xlsx
    ```

14. Label failed D1-D3 or coverage gates `Incomplete / blocked`. Only D4 runtime,
    server, vendor-platform, legal-owner, or business-owner proof may remain
    deferred after export-level analysis is complete.
15. When cleanup is approved, ask whether to execute directly through available
    GTM tools/API/MCP or create import JSON. For direct execution, create a new
    workspace and warn before proceeding when workspace quota blocks creation.
16. Apply naming after behavior, consolidation, and dependency decisions. Follow
    user convention first; otherwise normalize the dominant local convention
    while preserving meaningful acronyms and unique names within each layer.
17. After execution or artifact creation, generate a field-level diff and a
    separate change-log workbook linked to approved operation IDs.
18. End every stage with one concrete next action.

## Analyst Rules

- Establish measurement intent before proposing cleanup for meaningful objects.
- Judge configuration, not names alone. Names are scope clues, not proof.
- Validate current-event availability and output type for every consumed value.
- Always check standard ecommerce variables, including order value, total price,
  total quantity, transaction ID, currency, item arrays, product identifiers,
  categories, prices, and all consuming fields.
- Do not invent GTM-side JavaScript when the official website/dataLayer contract
  should provide the missing field.
- Treat fixed product indexes and old UA ecommerce paths as migration risks unless
  a verified current-payload mapper exists.
- For custom code, combine optional AST facts with complete exported line review;
  regex or AST output alone is not semantic proof.
- Classify browser-to-server transport before changing Google IDs or consent
  triggers. Full server audits must include clients and transformations.
- Identify exact duplicates, similar logic, shared-source misuse, single-member
  trigger groups, and objects made obsolete by consolidation.
- Naming standardization is mandatory in cleanup unless excluded or blocked by
  unknown business tokens.

## Mutation Safety

- Never publish, submit, or create a GTM version unless explicitly requested.
- Never mutate a live/default workspace without explicit acceptance and rollback.
- Never delete based on age; require dependency and semantic proof.
- Never change consent, payload shape, dataLayer meaning, or custom-code variable
  references without business/privacy impact and QA.
- Never replace a custom-code variable reference with an unrelated hardcoded value.
- Prefer direct GTM/API/MCP for readable in-place changes and real deletions.
- Treat same-container JSON as name-conflict sensitive. Preserve built-ins,
  folders, templates, setup/teardown references, and route limitations.
- Self-audit generated JSON and do not call it import-ready when validation fails.

## Output Contract

Cleanup plans and change logs are for web analysts and marketing stakeholders.
Keep visible output concrete, concise, and actionable. Do not expose raw code,
parameter dumps, hashes, dependency graphs, or validator traces in visible tabs.

Use the canonical cleanup workbook:

- visible: `01 Summary`, `02 Cleanup Plan`;
- hidden proof: `03 Workstream Reconciliation`, `04 Reconciled Operations`,
  `05 Semantic Object Matrix`, `06 Deterministic Baseline`,
  `07 Custom Code Review`, `08 Source Model & QA`.

Use six visible cleanup columns: ID, level, area/problem type, affected objects,
problem/evidence, and action/priority/QA. Use separate change-log workbooks with
one row per changed object field or dependency.

## Resource Routing

| Need | Read/use |
| --- | --- |
| Canonical full-audit and completion contract | `references/03-rules/execution-contract.md` |
| Product users, inputs, outputs, acceptance, non-goals | `references/01-skill/` |
| General audit scope, severity, and stable policies | `references/03-rules/audit-domain-checks.md`, `references/03-rules/audit-rubric.md`, `references/03-rules/severity-calibration.md`, `references/03-rules/policy-register.md` |
| Pipeline assurance and completion troubleshooting | `references/03-rules/protected-audit-pipeline.md`, `references/03-rules/execution-assurance.md`, `references/03-rules/completion-gates.md` |
| Limited/sample audit | `references/03-rules/limited-audit-protocol.md` |
| JSON structure and source navigation | `references/03-rules/container-json-guide.md` |
| Semantic business logic | `references/03-rules/semantic-model-protocol.md`, `references/03-rules/semantic-logic-checks.md`, `references/03-rules/semantic-object-matrix.md`, `references/03-rules/summary-quality.md` |
| GA4 and ecommerce | `references/03-rules/audit-ga4-ecommerce.md` |
| Consent and browser/server routing | `references/03-rules/audit-consent-server.md` |
| Media/vendor payloads | `references/03-rules/audit-media-vendors.md`, `references/03-rules/vendor-playbooks.md` |
| Official documentation | `references/03-rules/vendor-registry.toml`, `references/03-rules/source-map.md` |
| Naming and consolidation | `references/03-rules/naming-standardization.md`, `references/03-rules/optimization-patterns.md` |
| Operations, aggressiveness, mutation, JSON | `references/03-rules/operation-schema.md`, `references/03-rules/mutation-playbook.md`, `references/03-rules/import-json-policy.md` |
| Human output and change logs | `references/03-rules/human-problem-taxonomy.md`, `references/03-rules/workbook-architecture.md`, `references/03-rules/report-templates.md`, `references/03-rules/change-log-template.md` |
| Validation and runtime QA commands | `references/02-commands/` |

## Portability

Use the Markdown workflow manually on any capable agent. Python 3.11+ provides
the deterministic path; `openpyxl` creates workbooks and optional `esprima`
enriches JavaScript facts. If Python or an optional dependency is unavailable,
reproduce the same artifacts and gates manually and state which deterministic
checks could not run. Never lower the analytical scope silently.
