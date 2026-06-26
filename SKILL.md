---
name: gtm-container-audit-cleanup
description: Audit, clean, and standardize Google Tag Manager web or server-side containers from exported container JSON, GTM API/UI evidence, Tag Assistant observations, runtime/network evidence, or implementation screenshots. Use when an agent is asked to review GTM governance, container installation, one tag gateway patterns, consent mode, GA4/ecommerce, marketing pixels, server-side tagging, custom HTML/JavaScript, semantic business logic, variable formula sanity, business objective modeling, naming conventions, duplicate or consolidatable tags/triggers/variables, obsolete elements, runtime QA, change logs, cleaned importable container JSON, or cleanup plans. Compatible with Codex, Claude Code, Gemini, and other agents that can read Markdown. Default to a complete deep audit; mutate only after explicit user approval; never publish or create GTM versions unless explicitly requested.
---

# GTM Container Audit Cleanup

Use this skill to audit and clean a Google Tag Manager container with a
repeatable, evidence-based workflow. Treat this Markdown folder as an
agent-neutral operating guide: no step depends on Codex-only behavior, hidden
memory, or a specific runtime.

## Operating Modes

- **Audit only**: Inspect evidence, understand object semantics, classify
  findings, identify consolidation opportunities, and recommend actions. This is
  the default when writes are not approved.
- **Cleanup plan**: Convert findings into an ordered roadmap with
  dependencies, risks, and expected verification.
- **Approved cleanup**: Modify GTM only after explicit approval, a dedicated
  workspace, a fresh export/snapshot, and the mutation playbook.
- **Importable JSON cleanup**: Generate a valid GTM container import/export JSON
  file for the user to import manually. This means a GTM-compatible `.json`
  container file, not a Markdown report or code block containing JSON. Treat
  manual same-container import as conflict-sensitive unless the user says they
  will overwrite or import into a new container.
- **Runtime QA**: Build or execute Tag Assistant, browser, network, CMP,
  server-side, and vendor-platform validation plans when runtime behavior,
  consent timing, duplicate hits, SPA routes, or vendor acceptance matters.
- **Report generation**: Produce a technical audit table, executive summary,
  stakeholder report, cleanup plan, or change log.

If the user has not clearly approved GTM writes, stay in audit-only or planning
mode.

## Route-Specific Cleanup Strategy

Choose the mutation strategy from the execution route before creating the final
operation set:

- **Direct GTM/MCP/API cleanup**: create a new workspace first, then prioritize
  modifying existing tags, triggers, variables, folders, and templates in place
  when this is safe. Follow `POL-106` and `POL-107` in
  `references/policy-register.md`.
- **Importable JSON cleanup for manual same-container merge**: prepare for GTM
  import conflict handling. Follow `references/import-json-policy.md`,
  especially `POL-202` through `POL-208`.
- **Importable JSON cleanup for overwrite or new-container import**: a full
  cleaned export may update/delete existing objects directly, because
  same-container conflict resolution is not the primary constraint.

If the user asks for JSON but does not specify the import mode, assume manual
same-container merge, state that assumption, and document the conflict strategy.

Use `references/operation-schema.md` before preparing any cleanup plan,
operation table, direct GTM/MCP/API write, or importable JSON. Use
`references/import-json-policy.md` for JSON-specific import behavior.

## Depth And Completeness Defaults

Default to the deepest complete audit and cleanup the evidence supports. Do not
choose a lighter or conservative scope unless the user explicitly asks for a
quick audit, a sample, a narrow layer, or a minimal fix.

Use `cleanup` as the single operational term. Treat related user phrasing as a
cleanup request, not as a separate mode: run the audit first, then apply or
prepare all safe audit-driven improvements across
tags, triggers, variables, folders, templates, consent routing, ecommerce
payloads, custom code, naming, unused objects, exact duplicates, and similar
consolidatable patterns.

Naming standardization is mandatory in every cleanup. It may be
deferred only when the user explicitly excludes it or when unclear business
tokens make safe renaming impossible; in that case, document the blocker and the
exact names that need owner clarification.

Every proposed final name must be unique within its GTM object layer. GTM cannot
reliably support duplicate names for tags, triggers, variables, or folders, and
duplicate proposed names are poor maintenance practice. When two objects share
the same vendor and event role, add a meaningful suffix such as scope, trigger
event, page context, consent category, destination ID suffix, sequence role,
market, product range, variant, or `Legacy`/`Paused`/`Decommission candidate`.
Use an object ID suffix only as a temporary audit placeholder when the real
business distinction is unknown, and mark the blocker.

Treat Google Analytics/event/ecommerce tracking as GA4 or current Google tag
tracking by default. Classify a Google analytics object as Universal Analytics
only when the tag type, property ID, explicit user instruction, or verified
legacy migration evidence proves that it is truly UA. UA is sunset; do not
create or preserve active UA ecommerce mappings unless the user explicitly asks
for a legacy exception and the report marks the risk.

Use conservative judgment only at the individual-change level. If a specific
change lacks enough business, CMP/legal, vendor-platform, or runtime evidence,
defer that change with a concrete blocker and required evidence. Do not use that
blocker to reduce the overall audit or cleanup scope.

Audit depth and mutation aggressiveness are separate. The audit should be deep
by default. Execution should use `Standard` cleanup by default, escalate to
`Deep` or `Transformational` only after explicit approval, and downgrade to
`Conservative` only when the user requests minimal risk or evidence is thin.

## Mandatory Completion Ledger

For every audit, cleanup plan, cleanup run, importable JSON run, final handoff,
or change log, maintain a completion ledger. Read
`references/completion-gates.md` for the required workstreams, phase model,
definition of done, reconciliation counts, and failed-gate handling. Do not rely
on an implied checklist.

Each ledger row must be marked `Done`, `Deferred`, `Not applicable`, or
`User-excluded`. `Deferred` requires affected objects, exact blocker, required
evidence, risk, and next action. Do not mark a workstream complete just because
one example or one vendor family was checked.

Before final delivery, run the final coverage check from
`completion-gates.md`. If a report or workbook includes a reconciliation table,
validate it with `scripts/gtm_audit_gate_check.py`. If any mandatory gate fails,
label the deliverable `Incomplete / blocked` and list failed workstreams,
affected objects, blockers, risk, required evidence, and next action.

## Next-Step Discipline

At the end of every completed audit, cleanup-plan phase, cleanup phase,
JSON generation phase, QA phase, or handoff, state the recommended next step.
Make it specific to the current status, such as owner decision, runtime QA,
cleanup route selection, GTM workspace creation, importable JSON generation,
change-log preparation, or publish readiness review.

When a step is blocked, the next step must name the missing evidence, decision,
or access needed. When a step completes cleanly, the next step must name the
next executable action and whether it requires user approval. Do not end a
deliverable with only findings, files, or a generic "let me know" close.

## Agent Portability Contract

Follow these rules in Codex, Claude Code, Gemini CLI, or any similar agent:

- Read `SKILL.md` first, then load only the referenced files needed for the task.
- Use available local tools, browser tools, GTM API clients, MCP connectors, or
  manual evidence supplied by the user; do not require a specific toolchain.
- Prefer exported GTM container JSON for reproducible first-pass analysis.
- Summarize large inventories into counts, object names, IDs, dependencies, and
  evidence snippets. Avoid pasting whole container exports into chat.
- Mark assumptions, confidence, and missing evidence explicitly.
- Keep all recommendations reversible unless the user asks for final execution.

## Resource Routing

- Read `references/completion-gates.md` for every audit, cleanup plan, cleanup
  execution, importable JSON artifact, final handoff, or change log.
- Read `references/policy-register.md` when resolving repeated safety,
  completion, naming, mutation, JSON, or reporting rules.
- Read `references/limited-audit-protocol.md` when the user asks for a quick,
  sample, narrow, single-family, or explicitly limited audit.
- Read `references/audit-rubric.md` for the complete audit checklist, severity
  model, cleanup heuristics, and classification rules.
- Read `references/audit-ga4-ecommerce.md` for GA4/current Google tag,
  ecommerce dataLayer, standard ecommerce variable, and missing-event checks.
- Read `references/audit-consent-server.md` for CMP, consent mode,
  browser-to-server transport, and server-side GTM caution checks.
- Read `references/audit-media-vendors.md` for media pixels, affiliate tags,
  publisher/vendor tags, payload shape, and media signal quality.
- Read `references/severity-calibration.md` before assigning client-facing
  severity or priority.
- Read `references/operation-schema.md` when turning audit findings into a
  cleanup plan, selecting aggressiveness, choosing direct GTM/MCP/API versus
  JSON, preparing an operation table, or validating route-specific risks.
- Read `references/import-json-policy.md` before generating, validating, or
  delivering any GTM importable JSON artifact.
- Read `references/container-json-guide.md` when analyzing exported GTM JSON or
  creating scalable inventory, dependency, and semantic-role tables from API/UI
  data.
- Read `references/semantic-model-protocol.md` after dependency mapping for
  conversion, media, ecommerce, lead, server-side, multi-market, or complex
  cleanup tasks.
- Read `references/semantic-logic-checks.md` before finalizing findings or
  cleanup operations for media, ecommerce, lead, conversion, shared-variable,
  custom-code, or value/quantity logic.
- Read `references/optimization-patterns.md` when looking for cleanup ideas
  beyond exact duplicates/unused objects or when proposing consolidation.
- Read `references/source-map.md` when checking modern GTM, GA4, consent mode,
  server-side tagging, UA, Google Optimize assumptions, or official vendor
  event/payload documentation.
- Read `references/vendor-playbooks.md` before judging GA4, Google Ads,
  Floodlight, Meta, TikTok, Pinterest, Microsoft, LinkedIn, Criteo, affiliate,
  Piano Analytics, publisher ads, Marfeel, Outbrain, Logora, CMP, or unknown
  vendor payloads.
- Read `references/runtime-qa-templates.md` when runtime behavior, consent
  timing, duplicate hits, SPA routes, browser-to-server routing, or vendor
  platform acceptance needs validation.
- Read `references/mutation-playbook.md` immediately before any create, update,
  rename, delete, or batch cleanup.
- Read `references/report-templates.md` before delivering audit results,
  cleanup plans, final handoffs, or change logs.
- Use `references/forward-test-prompts.md` when forward-testing a release or
  checking whether the skill generalizes across realistic request types.
- When Python is available and a GTM export is provided, use
  `scripts/gtm_export_inspect.py` to accelerate inventory, duplicate,
  dependency, unused-candidate, and ecommerce-variable discovery. Treat script
  output as audit hints that still require semantic review.
- Use `scripts/gtm_audit_gate_check.py` before claiming a workbook, CSV, JSON,
  or report with workstream reconciliation is complete.
- Use `scripts/gtm_diff_operations.py` when comparing an original export to a
  cleanup draft or post-change export. It emits structured operations and can
  produce change-log-shaped CSV.
- Use `scripts/gtm_validate_artifact.py` before delivering any generated JSON or
  after a direct cleanup readback. Select the route mode explicitly.
- Use `scripts/check_release.py` before packaging or releasing the skill.
- When producing a manual same-container merge JSON from a full cleanup draft,
  use `scripts/gtm_make_merge_patch.py` to emit a minimal patch containing only
  changed objects and to validate that original export plus patch reconstructs
  the cleaned state.
- When producing a same-container JSON intended for GTM View Changes, use
  `scripts/gtm_make_name_preserving_review_patch.py` and state that naming
  standardization is deferred from that artifact.

## Intake

Ask for or infer the minimum context needed:

- GTM account/container name plus `accountId`, `containerId`, and workspace or
  exported version if available.
- Website domains, key page types, ecommerce status, app/SPA/PWA behavior, and
  relevant markets or regions.
- Whether the task covers web GTM, server-side GTM, or both.
- Current evidence source: exported container JSON, GTM API access, UI
  screenshots, Tag Assistant output, page source, crawl output, or stakeholder
  notes.
- Consent/CMP stack and applicable privacy regions, such as EEA, UK, Brazil,
  California, or internal policy zones.
- Known naming convention, ownership model, release process, and previous audit
  or cleanup decisions.

Do not reuse stale IDs, stale exports, or prior assumptions without saying so.

## Evidence Standards

Classify every meaningful check as:

- `Correct`: Evidence supports the current setup.
- `Issue`: Evidence shows broken, risky, duplicate, non-compliant, or obsolete
  behavior.
- `Needs improvement`: Functional but hard to maintain, fragile, inconsistent,
  or inefficient.
- `Not applicable`: The check does not apply to this business, container, or
  scope.
- `More info needed`: The evidence is insufficient or a business/legal decision
  is required.

Attach a confidence level: `High`, `Medium`, or `Low`. Prefer object names plus
IDs, exact trigger/filter conditions, consent settings, custom code snippets, or
observed browser behavior over generic descriptions.

## Workflow

1. **Confirm scope and mode**. Establish whether this is audit-only, planning,
   or approved cleanup.
2. **Load the right references**. Start with `completion-gates.md` and
   `audit-rubric.md`; add JSON, semantic logic, sources, vendor playbooks,
   runtime QA, mutation, or reporting references only when needed.
3. **Build inventory**. Inventory tags, triggers, variables, folders,
   templates, consent settings, workspaces/versions when relevant, and website
   implementation evidence. For large exports, run the bundled inspection
   script when available.
4. **Map dependencies**. Connect tags to firing/blocking triggers, trigger
   groups, setup/teardown tags, variables, custom templates, and custom
   HTML/JavaScript references.
5. **Map official documentation contracts**. Identify every tag/vendor/event
   family and use official documentation as the default source of truth for
   standard event names, website/dataLayer event payload format, required and
   recommended parameters, data types, value formats, base/event sequencing, and
   validation method. First use the bundled source references when the vendor is
   listed. If a vendor, CMP, template, or event family is not pre-included in the
   skill references, search the internet for that vendor's official
   documentation before judging payload correctness. If no official source is
   available after searching, document the search, say so, and lower confidence.
   For Google Analytics/event/ecommerce tracking, default to GA4/current Google
   tag contracts unless the evidence explicitly proves a UA exception.
6. **Profile object semantics**. For each meaningful tag, trigger, and variable,
   infer the intended business role, consumed dataLayer fields, output shape,
   vendor payload fields, consent gate, page/event context, and downstream
   dependency. Do not stop at object counts.
7. **Build the semantic model**. Model business objective, user action,
   event/context, GTM implementation, data source, destination payload, platform
   use, and evidence/blockers for meaningful object families.
8. **Run semantic logic checks**. Build an internal graph from business action
   to trigger, tag, variable/helper, source path/formula, vendor field, consent,
   and server routing. Detect contradictions such as fixed-index total price,
   quantity built from price fields, stale dataLayer reads, scalar values where
   arrays/objects are expected, or shared variables serving incompatible
   consumers. Surface only actionable findings, blockers, operations, or QA.
9. **Validate GA4 dataLayer format before variables**. For every GA4 standard or
   ecommerce event, compare the current website/dataLayer event payload to the
   official GA4 event schema before judging or creating GTM variables. For GA4
   ecommerce, verify that event-level fields such as `transaction_id`, `value`,
   `currency`, `tax`, `shipping`, `coupon`, and `items` exist in the expected
   current event context and that `items` is an array of GA4 item objects using
   fields such as `item_id`, `item_name`, `item_brand`, `item_category`, `price`,
   and `quantity`. Treat old Universal Analytics Enhanced Ecommerce paths such
   as `ecommerce.purchase.actionField.*`, `ecommerce.purchase.products.*`,
   `ecommerce.add.products.*`, or `ecommerce.detail.products.*` as migration
   evidence, not as correct GA4 paths, unless there is explicit mapping evidence
   and Preview/debug proves the outgoing GA4 payload is correct.
10. **Validate standard ecommerce logic**. Always inspect common ecommerce
   variables such as revenue, total price, total quantity, tax, shipping,
   transaction ID, product IDs, names, categories, item arrays, checkout
   products, and purchase products. Confirm paths, formulas, output types,
   multi-item handling, null/`NaN` behavior, and every consuming tag field.
11. **Audit missing standard events and dataLayer readiness**. For GA4 and each
   vendor with official event documentation, identify missing useful standard
   events and whether the website/dataLayer already provides the required
   event, item, value, currency, ID, and consent data. Treat missing dataLayer
   readiness as a blocker before creating tags.
12. **Infer naming scope carefully**. Use object names to detect country, market,
   language, product range, campaign, or audience scope, but do not assume
   unclear tokens are understood. Ask the user about ambiguous labels such as
   product-range or internal campaign prefixes before judging correctness.
13. **Define the naming convention**. Unless the user provides a house style,
   use `Vendor - Event/role - Scope/detail` for tags, `Utility/type - Event or
   condition - Scope/detail` for triggers, and `VariableTypeAcronym - Variable
   name/source path` for variables. Decide final names before creating helpers,
   reusable triggers, or replacement tags. Validate proposed names for
   uniqueness within each layer before publishing the audit plan, operation
   table, rename map, or cleanup artifact.
14. **Detect gateway and consolidation patterns**. Identify whether the container
   uses a one tag gateway, server-side gateway, lookup-table gateway, shared
   vendor loader, or repeated one-tag-per-market/event pattern. Cluster exact
   duplicates, single-member trigger groups, and similar objects that could be
   consolidated safely.
15. **Select optimization patterns**. Use `optimization-patterns.md` to evaluate
   hygiene, structural, semantic, and strategic optimization ideas without
   flattening business meaning or over-consolidating.
16. **Classify client-to-server transport tags before judging Google IDs or
   consent triggers**. If a Google tag or Google event tag has a
   `server_container_url`, transport URL, first-party tagging endpoint, gateway
   naming, S2S naming, placeholder-looking tag ID such as `G-XXXXXX`, or
   event/settings parameters that forward consent, click IDs, event IDs, user
   data, or media identifiers, treat it as a possible browser-to-server
   transport tag. Do not mark the measurement ID or missing client-side blocking
   trigger as broken solely from the web container export. Classify it as
   `server-container validation needed` until the server container mapping,
   transformations, consent enforcement, and server-to-vendor destination are
   checked.
17. **Audit by risk area**. Review governance, implementation, security,
   organization, setup hygiene, privacy/consent, GA4, server-side GTM, vendor
   pixels, and Google Ads.
18. **Prioritize**. Rank findings by business impact, data quality impact,
   privacy risk, operational risk, performance impact, and cleanup complexity.
19. **Stage cleanup decisions**. Separate objects that are currently unused from
   objects that become obsolete only after an approved consolidation. Do not
   present the first orphan list as the final cleanup list.
20. **Compile operations**. Convert findings into structured operations with
   route, aggressiveness, dependencies, QA method, rollback, and blockers. Use
   `operation-schema.md`; do not jump from findings directly to writes.
21. **Build the full cleanup set**. For cleanup or importable JSON,
   include every evidence-safe correction, consolidation, deletion candidate,
   naming/folder improvement, trigger cleanup, variable cleanup, tag
   payload fix, and custom code hardening. Do not stop at the first high-risk
   family.
22. **Flatten single-member trigger groups before final naming**. For each
   trigger group with exactly one child trigger, update consuming tags to use the
   child trigger directly, then delete the group in direct GTM/API or
   overwrite/new-container JSON. In same-container merge JSON, document that the
   merge patch can remap consumers but cannot reliably delete omitted existing
   objects; provide a direct/overwrite deletion path.
23. **Apply naming last when behavior changes exist**. After payload fixes,
   consolidation, deletion, and folder moves are decided, rename remaining
   objects according to the final convention and produce a before/after naming
   map. Re-scan all `{{Variable Name}}` references, especially inside custom HTML
   and custom JavaScript, plus setup/teardown `tagName` references after tag
   renames.
24. **Recommend next actions**. Separate no-write recommendations,
   user/business decisions, consolidation candidates, and approved mutation
   candidates.
25. **Confirm execution route**. When the user approves cleanup, ask whether
   they want direct GTM execution through available
   tools/MCP/API or a GTM-compatible import JSON file they can import manually.
26. **Select route-specific cleanup strategy**. For direct GTM/MCP/API cleanup,
   preserve and modify existing objects in place when safe. For manual
   same-container import JSON, use a conflict-aware replacement/additive strategy
   when it reduces GTM import conflicts, emit only changed objects in the import
   file, and document old-to-new decommission mapping. For overwrite/new-container
   JSON, direct object updates/deletions may be appropriate.
27. **Stop before writes**. If mutation is requested, read
   `mutation-playbook.md`, prepare a plan, and ask for explicit approval unless
   approval has already been given for the exact operations.
28. **Self-QA generated outputs**. Before delivering an importable JSON, inspect
   the generated file as if it were a fresh export: run inventory, dependency,
   duplicate, unused, naming, GA4 dataLayer, and residual-issue checks. This is
   a self-audit gate, not an external workspace/export check.
29. **Reconcile completion gates**. Before final delivery, check the completion
   ledger against `completion-gates.md`; if a reconciliation workbook/table is
   produced, run `scripts/gtm_audit_gate_check.py`. If a required gate fails,
   label the deliverable `Incomplete / blocked` and list failed rows, blockers,
   risk, required evidence, and next action.
30. **State the next step**. After each completed audit or workflow phase,
   state the concrete next step, including whether the user must approve a
   route, decide an owner/business question, provide evidence, or allow
   execution.
31. **Report clearly**. Use `report-templates.md` and provide a reproducible
   audit trail.

## Non-Negotiable Safety Rules

- Do not publish, submit, or create a GTM version unless the user explicitly
  requests that exact action.
- Do not delete tags, triggers, variables, or templates based on age alone.
- Do not mark unused objects as safe to delete until a dependency sweep covers
  tags, triggers, variables, trigger groups, setup/teardown tags, templates, and
  custom HTML/JavaScript bodies.
- Do not finalize deletion candidates until consolidation/refactor proposals
  have been evaluated; consolidation can make currently used objects obsolete.
- Do not turn an approved cleanup into a minimal correction pass
  unless the user explicitly asked for minimal or conservative changes.
- Do not generate a cleaned importable JSON that only fixes one object
  family when evidence-safe cleanup exists in triggers, variables, tags,
  folders, naming, duplicates, or consolidation candidates.
- Do not treat Google analytics/event/ecommerce tracking as Universal Analytics
  by default. UA objects are deprecated exceptions; ambiguous Google events are
  GA4/current Google tag candidates until proven otherwise.
- Do not leave active UA Enhanced Ecommerce paths such as
  `ecommerce.purchase.actionField.*`, `ecommerce.purchase.products.*`,
  `ecommerce.add.products.*`, or `ecommerce.detail.products.*` as GA4 mappings
  unless a verified mapper and outgoing GA4 payload evidence exist.
- Do not modify production/default workspaces when a dedicated workspace can be
  used.
- Do not perform direct GTM cleanup in an existing/default workspace. Create a
  new workspace first, unless the user explicitly accepts a different path after
  being warned.
- Do not proceed with direct cleanup when GTM workspace creation is blocked by a
  quota or active-workspace limit. Alert the user and offer the importable JSON
  route or a workspace cleanup decision.
- Do not apply the same mutation assumptions to both cleanup routes. Direct
  GTM/MCP/API cleanup should preserve and update existing objects where safe;
  manual same-container import JSON may use replacement/additive objects to
  reduce conflict resolution and empty-value import errors.
- Do not change consent behavior, dataLayer semantics, or vendor payload shape
  without identifying the privacy/business impact.
- Do not accept a variable formula, helper output, or media payload as correct
  merely because it resolves. Its name, event context, source path, formula,
  output type, and every consuming vendor field must make logical sense.
- Do not invent custom JavaScript variables or synthetic calculations to bypass
  missing standard website/dataLayer fields when official documentation expects
  those fields to be sent by the site. Flag the missing dataLayer/event contract
  as the issue and mark tag creation as blocked until the dataLayer is ready.
- Do not "fix" GA4 ecommerce by mapping Universal Analytics Enhanced Ecommerce
  paths into GA4 unless the migration/mapping is explicit, documented, and
  verified at the outgoing GA4 payload boundary. Prefer a website/dataLayer fix
  when the official GA4 event payload is missing.
- Do not rewrite custom HTML by replacing variable references with hardcoded
  values unless the user explicitly approved that semantic change.
- Do not create helper variables, triggers, or tags without defining their final
  naming pattern and all consumers first; avoid proposing elements that will
  immediately need to be renamed or re-referenced.
- Do not let names contradict behavior. A tag, trigger, or variable whose name
  says `purchase`, `form_submit`, a country, a product range, or a consent
  vendor must have configuration that enforces that meaning, or it must be
  renamed/deferred with a blocker.
- Do not skip naming standardization in an approved cleanup unless
  the user excludes it or the required scope/product/campaign meaning is
  unknown. If skipped, list the exact blocker and target naming convention.
- Do not preserve a trigger group with exactly one child trigger as a cleaned
  object. Remap consumers to the child trigger and delete the group when the
  selected route supports deletion; otherwise list it as a route-limited delete
  candidate with the required direct/overwrite cleanup path.
- Do not deliver an importable cleanup JSON until generated-file self-QA passes
  or every failed check is listed as a residual blocker.
- In importable JSON patches, avoid custom template churn, include referenced
  folders, preserve enabled built-in variables, and satisfy GTM validation for
  any included `cvt_*` tag or variable types. Never include unchanged templates
  in a same-container patch unless required for validation; if a
  `customTemplate` layer is required, follow `mutation-playbook.md` and warn
  about possible template delete/add noise.
- Do not treat legal/privacy advice as final. Flag legal-dependent decisions for
  the user's privacy/legal owner.

## Output Expectations

Use `references/report-templates.md` for the required report, workbook, roadmap,
operation, runtime QA, change-log, and handoff schemas. At minimum, every
deliverable must expose evidence freshness, inventory/dependency coverage,
semantic validation status, official documentation coverage, findings or
no-change evidence, cleanup route/aggressiveness, blockers, QA requirements,
rollback/publish status when cleanup is involved, and deferred decisions.
The cleanup plan is the decision source and the change log is the execution
record; keep IDs, before/after values, reason, impact, QA, and status aligned.

Every audit, phase handoff, cleanup result, generated JSON delivery, or QA
summary must include `Recommended next step`. This next step must be concrete
and approval-aware.

End audit and cleanup handoffs with the change-log question from
`references/report-templates.md`.
