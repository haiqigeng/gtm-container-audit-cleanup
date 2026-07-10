# Completion Gates

The canonical criteria are in `execution-contract.md`. Run these gates in
order; a later pass cannot excuse an earlier failure.

## Audit Package

- manifest source hash matches the export;
- source-model coverage is `pass`;
- deterministic modules include finding IDs or zero-finding rows;
- semantic tasks are labelled tasks, not findings;
- all custom code has technical extraction rows;
- clients and transformations are included for a server export.

## Semantic Review

`gtm_semantic_review.py validate` must confirm:

- one row per source object key;
- unchanged config hash and source path;
- D1, D2, and D3 completed;
- object-specific role, contract, inputs, behavior, output, consumers,
  judgment, and cleanup implication;
- every source branch and code line interpreted;
- every variable trace and consumer source-bound;
- required sibling comparisons completed;
- official documentation basis present;
- action fields complete for non-keep decisions.

## Operations

- every deterministic finding ID is resolved;
- technical and semantic conflicts are resolved;
- each packet has exact action, preconditions, QA, rollback, route, cleanup
  level, readiness, and risk class;
- no coverage task is promoted directly to an operation.

## Workbook

- canonical tabs and visibility are used;
- all visible detail rows link to operation packets;
- source coverage and strict-evidence gates pass;
- tabs stay within the compact column architecture;
- all-sheet privacy scanning passes.

## Mutation And Change Log

- explicit approval and route are recorded;
- direct cleanup uses a dedicated workspace;
- JSON artifacts pass route-specific validation;
- executed changes match approved operations;
- every field or dependency change is represented in the separate change log;
- publication/version creation occurs only when explicitly requested.

Any failed gate makes the result `Incomplete / blocked`, with the exact failed
gate and next action stated.
