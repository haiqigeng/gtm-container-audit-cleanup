# Protected Audit Pipeline

`execution-contract.md` is canonical. This file explains artifact ownership and
why no stage may be skipped.

## Artifacts

| Artifact | Purpose | May create an operation? |
| --- | --- | --- |
| `source_model.json` | Exact object, field, reference, consumer, code, folder, and template navigation. | No |
| `deterministic_findings.json` | Reproducible hygiene findings and zero-finding module rows. | Only after semantic resolution |
| `semantic_coverage_tasks.json` | Object and topic questions that D3 must answer. | No |
| `technical_code_findings.json` | Parsed code facts, side effects, technical risks, and handoff seeds. | Only after semantic resolution |
| `semantic_review.json` | Source-bound D1-D3 business and configuration judgment for every object. | Yes, after validation |
| `reconciled_operations.json` | Confirmed, execution-ready or explicitly blocked cleanup decisions. | It is the operation source |
| `human_rows.json` | Compact stakeholder wording derived from operations. | No |

## Stage Gates

1. **Source model**: all exported objects are indexed by layer and ID; nested
   leaves, references, consumers, system references, server clients, and
   transformations are preserved.
2. **Independent scans**: deterministic, semantic-task, and technical-code
   stages run from raw source. One scan must not suppress another.
3. **D1-D3 review**: every object, configuration branch, code line, consumer,
   recursive reference, and required sibling comparison is reviewed.
4. **Source validation**: object key, config hash, JSON path, branch hashes,
   code-line hashes, variable chains, and consumers match the original export.
5. **Reconciliation**: every deterministic finding ID is resolved and relevant
   technical evidence is linked. Conflicts block compilation.
6. **Operation compilation**: only confirmed issues, exceptions, or blockers
   become operation packets. Coverage tasks never become operations.
7. **Human translation**: visible rows are derived from operation packets and
   cannot introduce new findings.
8. **Workbook gates**: source coverage, evidence quality, operation links,
   architecture, and privacy all pass.
9. **Mutation**: explicit approval and route selection are required.
10. **Change log**: field-level changes are linked back to approved operations.

## Incremental Reuse

Large containers may reuse completed semantic rows only through
`gtm_semantic_review.py scaffold --reuse-review` or `merge`. Reuse requires the
same object key, config hash, source path, references, consumers, branch
anchors, code-line hashes, and recursive trace requirements. Changed objects
return to pending review.

Never reuse prose by name alone. Never reuse a completed workbook as if it were
source evidence.

## Failure Behavior

Stop and label the work `Incomplete / blocked` when:

- source objects or branches are missing;
- generic text replaces object-specific D3 behavior;
- a code line or variable chain is not reviewed;
- deterministic findings are unresolved;
- an operation conflicts with technical evidence;
- a direct or JSON mutation cannot preserve dependencies;
- workbook or privacy validation fails.

D4 runtime, server-container, vendor-platform, legal-owner, or business-owner
evidence may remain open after D1-D3. Missing export-level review may not.
