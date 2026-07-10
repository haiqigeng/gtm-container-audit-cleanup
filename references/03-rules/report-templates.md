# Report Templates

Use `workbook-architecture.md` for the canonical files and tabs. Use this file
for wording.

## Contents

- Audit summary and cleanup rows
- Hidden semantic and custom-code proof
- Change-log rows and delivery boundary

## Audit Summary

Keep the summary short:

```text
Scope and evidence
Overall status
Highest-impact confirmed problems
Safe-now operations
Runtime or owner blockers
Recommended route and cleanup level
Validation status
Next action
```

Do not use the summary to claim object-level coverage. The hidden proof tabs and
source gates establish coverage.

## Cleanup Plan Row

```text
ID
Level: Single | Summary | Detail
Area / problem type
Affected object(s)
Problem / evidence
Action / priority / QA
```

Write the problem as observable configuration behavior plus its consequence.
Write the action as a concrete target state. Include the operation ID, priority,
blocker, and QA compactly in the final column.

Good:

```text
Consent & compliance / Conflicting state mapping
CV - analytics_storage; CV - ad_storage
Both variables evaluate the same Didomi purpose condition, so analytics and ads
consent cannot diverge when the user chooses different purposes.
Map each storage signal to its documented purpose; P1; test four consent
combinations in Preview and verify the outbound consent parameters.
```

Bad:

```text
Semantic issue | Review consent variables | Check in GTM
```

## Hidden Semantic Proof

The semantic matrix uses six structured groups:

1. Object identity.
2. Purpose and contract.
3. Configuration logic, including branch and code-line reviews.
4. Output and consumers.
5. Judgment.
6. Proof and recursive traces.

Do not replace literal functionality with a category. Preserve statements such
as `returns Date.now()` or `reads ecommerce.items and maps every item_id into a
string array consumed by Meta Purchase content_ids`.

## Custom Code Proof

State:

- the specific purpose;
- what each line or block reads and does;
- return, push, load, mutation, network, storage, cookie, DOM, or API effects;
- referenced GTM variables and consumers;
- code health and semantic judgment;
- exact action, blocker, and QA when change is needed.

AST and regex facts support this review but never replace it.

## Change Log Row

```text
Change ID
Area / object
Change made
Before
After
Reason / QA / status
```

Use completed language for real execution. Include the approved operation ID.
The row must identify the exact changed field or dependency and be understandable
without GTM View Changes. Planned or simulated logs must say so.

## Delivery Boundary

Deliver the cleanup plan after audit and before execution. Deliver a separate
change log after direct cleanup or artifact generation. Keep raw exports, full
code, secrets, local paths, and scratch reasoning out of both files.

End every audit, plan, execution, and change-log delivery with one concrete next
action.
