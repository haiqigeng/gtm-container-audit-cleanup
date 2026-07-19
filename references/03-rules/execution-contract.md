# Authoritative Execution Contract

This is the canonical full-audit contract. A different reference may add a
domain rule but may not weaken this workflow.

## Evidence Boundary

Use a complete GTM JSON export or equivalent complete read-only configuration.
The container proves configured logic, not live website behavior, network
delivery, CMP state, vendor acceptance, or an unseen server container.

Lock one source filename and SHA-256. Build a persistent context artifact and a
canonical deterministic fact artifact. Every generated review must carry the
source, context, and shared-fact hashes. A changed export or material context
change starts a new review package.

The package gate recomputes context content and reconstructs shared facts from
the locked export. Matching hash strings with changed or fabricated content do
not satisfy source integrity.

## Contents

- Required pipeline and the three independent runs
- Reconciliation and future-state validation
- Plan, execution levels, and completion states

## Required Pipeline

```text
raw container evidence
  + provided/inferred audit context
  -> source model and canonical deterministic facts
  -> independent Run 1: operational sanitation
  -> independent Run 2: configuration correctness
  -> independent Run 3: business architecture
  -> three-run completion gate
  -> contradiction-aware operation reconciliation
  -> future-state graph simulation
  -> human cleanup plan
  -> explicit approval and route/aggressiveness selection
  -> optional execution or import JSON
  -> separate post-execution change log
```

The shared fact layer normalizes identity, leaves, references, consumers,
terminal sources, trigger logic, code/formula signals, consent routes, and
behavior signatures. It may not contain correctness, necessity, duplication,
consolidation, or cleanup judgments.

The three runs may execute in parallel after source lock. Each may read the raw
export and shared deterministic facts, but must not read or copy another run's
verdicts. Each completes its own artifact and passes its own validator. Sharing
facts removes extraction drift; keeping judgments separate preserves genuine
independent challenge.

Large runs may be processed in source-locked shards. Every shard remains part of
one run and the merge must recover the exact source-generated obligation set.
Chunking is an execution strategy, not a reduced-depth mode. Architecture uses
a dedicated discovery shard for analyst-added `DISC-*` comparisons and its
all-object attestation; the merged run cannot become complete while either is
pending. Configuration obligation shards contain at most 30 obligations and
must recover every generated branch, reference trace, contract, technical
finding, D3 cross-check, and custom-code line exactly once and in source order.

## Run 1: Operational Sanitation

Source: `operational_scan.json`, `shared_facts.json`, and raw export.

Decision artifact: `operational_review.json`.

Purpose: guarantee basic cleanup coverage even when business analysis is hard.
Every nonzero finding receives `cleanup_operation`, `documented_exception`,
or `owner_decision_needed`. A `documented_exception` is valid only when the
locked intake context identifies that finding, signature, or object and gives a
specific owner reason that the review preserves. `container_evidence_limit` and
`not_applicable` cannot erase a deterministic nonzero finding.
Every zero module retains its source-counted proof row.

Run rules: `operational-sanitation.md`.

## Run 2: Configuration Correctness

Source: raw object branches, `shared_facts.json`, consumer/dependency graph,
technical code facts, vendor registry, and current official documentation.

Decision artifact: `configuration_review.json`.

Purpose: prove literal behavior and correctness for every tag, trigger,
variable, custom template, client, and transformation. Review every logic leaf,
every recursive reference node and hop, every consumer, every applicable
official contract topic, and all custom-code lines. A generic summary or copied
parameter list fails.

Every semantic field cites one or more generated source paths selected for that
claim and names source-derived behavior facts. Citations alone do not validate a
generic statement. Every object also completes the exact generated D3
cross-check set for purpose/output, execution/scope, input/output/consumer, and
consent/sequence, plus code and vendor-contract alignment when applicable. A
failed cross-check links to a concrete defect.

Run rules: `configuration-correctness.md` and `domain-contracts.md`.

## Run 3: Business Architecture

Source: raw export, `shared_facts.json`, source-derived family chains, and
relationship candidates.

Decision artifact: `architecture_review.json`.

Purpose: decide whether individually plausible objects form a necessary,
non-overlapping, maintainable measurement architecture. Review every tag family
or server intake/transformation family, every object in each execution chain,
and every generated cross-object candidate. Then run open discovery across all
source objects and add source-bound comparisons the deterministic queue missed.
The generated method coverage, candidate IDs, all-object review scope, and
source-scope hashes are immutable. Each method review must account for that
exact scope and cite source-derived objects or comparisons in its conclusion.

Run rules: `business-architecture.md`.

## Reconciliation

Do not average or vote across runs.

- A configuration issue may produce a fix even when the object is structurally valid.
- An exact operational duplicate may be deleted only when architecture confirms
  consolidation rather than an intentional variant.
- A correctly configured object may still be unnecessary at family level.
- An architecture operation may redesign several individually correct objects.
- An unresolved owner or container-evidence decision blocks conflicting mutation.

Operations with identical structured mutations may reconcile even when the
three lenses use different human wording or operation keys. Preserve every lens
rationale and source reference. Reusing one operation key for different
structured mutations is an error. Broad issue categories never merge
operations. The completion gate recompiles the three source reviews and
requires the supplied operation packet to match exactly; hand edits require
updating and revalidating the originating review.

Compilation creates a complete decision ledger. Every operational finding,
configuration object, architecture family, and comparison must have one final
disposition; every cleanup disposition must link to one compiled operation.

## Future-State Gate

Apply structured operations to a copy of the export before delivery. Update
complete object creations, missing-field/list additions, variable references,
trigger IDs, trigger-group members, setup/teardown tag names, folders, field
values, names, and deletions. Re-run sanitation.

Block when the simulated state:

- creates a missing reference or duplicate ID;
- creates a new sanitation finding;
- leaves an operational finding selected for cleanup unresolved;
- remaps to an object that is also deleted;
- applies conflicting values to one object field;
- deletes an object while another operation changes it.

The gate also reports projected before/after/delta counts by GTM layer. An
unexpected broad count change is a review blocker even when references remain
technically valid.

## Plan And Execution Levels

Audit depth is always full. Before approval, route and aggressiveness may remain
`Pending user selection` and `Undecided`.

After plan approval, ask for:

1. route: direct GTM/API/MCP or import JSON;
2. aggressiveness: Conservative, Standard, Deep, or Transformational.

Aggressiveness controls execution risk and owner approvals, not what the audit
checks or reports. Each operation declares a minimum safe level. Operations
above the selected level remain visible as deferred and are excluded from the
simulated execution state.

## Completion States

`Complete` requires:

- source-model coverage `pass` or `pass_with_integrity_findings`, with every
  integrity finding retained in the operational review;
- matching source, context, and shared-fact hashes across all three runs;
- all three run statuses `complete`;
- complete architecture open-discovery attestation and decision ledger;
- no review validator error;
- no reconciliation contradiction;
- future-state gate `pass`;
- cleanup workbook and privacy gate `pass`.
- no formula cell or unscanned hidden proof tab in a delivered workbook;
- a separate completed change log, when requested, links only exact
  field-level mutations to approved operation IDs.

Otherwise report `Incomplete / blocked` with the exact missing artifact or
source-bound reason. Do not claim completion because the container is large or
the review is token-intensive. Chunk work while preserving all obligations.
