# Inputs And Outputs

## Required Evidence

- a complete GTM container JSON export or equivalent complete read-only GTM
  API/UI configuration evidence;
- container type: web or server;
- website/domain and business model when relevant to interpretation;
- known CMP, browser-to-server routing, ecommerce, lead, media, publisher, or
  market context.

The agent should infer safe facts from the export and supplied website context.
Ask only for material unknowns, especially unexplained product/market prefixes,
business-specific event families, legal consent decisions, or missing server
container scope.

Persist context in a small JSON object when supplied explicitly. Typical keys
are `website_url`, `business_model`, `container_type`, `cmp`, `markets`,
`product_scopes`, `server_routing_hosts`, `known_owner_exceptions`, and
`unresolved_questions`. The package merges this with deterministic inference
and records a context hash.

Live browser requests, Tag Assistant, CMP interaction, website dataLayer
inspection, and vendor-platform results are not evidence for this skill.

## Deliverables

Depending on the request:

- audit summary;
- cleanup plan as a dedicated XLSX workbook;
- planned change preview;
- validated importable GTM JSON;
- approved direct GTM workspace changes;
- post-execution change log as a separate XLSX workbook.

The audit evidence package contains `context.json`, `source_model.json`,
`shared_facts.json`, three independent review artifacts, technical code facts,
reconciled operations with a decision ledger, projected object counts, and the
future-state gate. These are working/proof artifacts; the visible workbook
remains concise.

The visible plan includes proposed operations, operations deferred by the
selected aggressiveness, unresolved owner questions, and documented container-
evidence limits. Hidden proof remains unprotected and privacy-scanned.

## Lifecycle

1. **Audit and cleanup plan:** proposed decisions only.
2. **Approval and route selection:** direct GTM/API/MCP or import JSON, plus
   mutation aggressiveness.
3. **Execution:** only after explicit approval.
4. **Change log:** what actually changed, produced only after execution or
   generated cleanup artifact creation.

Never integrate the change log into the cleanup plan. A requested hypothetical
record must be labelled `planned change preview` or `simulated change log`, not
presented as executed GTM work.

## Change-Log Detail

The post-execution change log must be understandable without GTM View Changes.
Use one row per changed object field, dependency, route, source, folder, code
block, rename, deletion, or creation. Include linked operation ID, before,
after, reason, impact, QA status, rollback, and blocker where applicable.
Link an approved operation only when its simulated field mutation exactly
matches the observed layer, object ID, path, before value, and after value.
