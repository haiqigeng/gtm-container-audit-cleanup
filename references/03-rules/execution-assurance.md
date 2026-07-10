# Execution Assurance

Use `execution-contract.md` as the completion authority and
`protected-audit-pipeline.md` for artifact ownership.

Assurance is mechanical where possible:

- source identity uses layer plus object ID, never name alone;
- `source_sha256` binds every review to one export;
- configuration hashes invalidate stale rows;
- branch hashes require every exported configuration leaf to be interpreted;
- code-line hashes require every exported nonblank line to be interpreted;
- generated recursive trace requirements prevent stopping at a variable name;
- consumer keys prevent invented usage claims;
- deterministic finding IDs prevent basic hygiene from disappearing;
- operation IDs connect visible plan rows and post-execution field changes.

An agent's statement that it performed D3 is not evidence. Only a review that
passes `gtm_semantic_review.py validate` and the source/workbook gates counts.

The user-facing workbook stays compact because structured hidden cells retain
proof fields that validators can expand. This is presentation compression, not
analytical compression.
