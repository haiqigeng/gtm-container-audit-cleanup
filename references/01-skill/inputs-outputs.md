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
`unresolved_questions`, plus `requested_deliverable`. Run the deterministic
context model before building the package. Its preflight labels each core field
as analyst-provided, high-confidence inferred, or unresolved and identifies
which questions materially affect interpretation. The package merges confirmed
context with inference and records the complete intake state in the context
hash. Supply `cmp`, `markets`, and `server_routing_hosts` as arrays; an explicit
empty array means confirmed none rather than missing context.

Live browser requests, Tag Assistant, CMP interaction, website dataLayer
inspection, and vendor-platform results are not evidence for this skill.

Before interpretation, the evidence gate validates the ContainerVersion root,
the complete current entity-layer registry, layer array shapes, required object
IDs, and per-layer ID uniqueness. Unknown entity-like layers or ambiguous IDs
block the audit; missing references inside an otherwise valid export remain
visible findings and do not reduce the remaining scan scope.

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
evidence limits. It leads with root problem and measurement impact, defines the
exact target state/action, and summarizes retained business-family architecture
as well as cleanup. Hidden proof remains unprotected and privacy-scanned.

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
This applies to every supported layer, including Zones and Google tag
configurations. A before/after source with ambiguous IDs or an unmodelled entity
layer is rejected instead of being partially diffed.
Link an approved operation only when its simulated field mutation exactly
matches the observed layer, object ID, path, before value, and after value.
