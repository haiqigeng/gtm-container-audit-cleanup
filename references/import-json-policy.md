# Import JSON Policy

Use this reference whenever the user asks for a GTM-compatible import/export
JSON cleanup artifact, a same-container merge patch, a View Changes review file,
or an overwrite/new-container JSON.

## Contents

- Route Selection
- Same-Container Merge
- View Changes Review
- Final-State Or Replacement JSON
- Schema Dependencies
- Validation Commands
- Failure Handling

## Route Selection

Apply `POL-201` from `policy-register.md`: when cleanup is approved, ask whether
the user wants direct GTM/MCP/API execution or importable JSON. If the user asks
for JSON without specifying import mode, assume manual same-container merge,
state the assumption, and document the conflict strategy.

Use direct GTM/MCP/API when the user needs readable GTM workspace changes,
in-place modification of existing objects, broad naming standardization, or
actual deletions.

Use JSON when the user cannot connect tools/API/MCP or wants manual import. JSON
does not behave like direct API mutation, especially for same-container imports.

## Same-Container Merge

Same-container merge is name-conflict sensitive. GTM can show renamed objects as
added/deleted rather than modified. It can also reject partial patches when a
changed object references an omitted folder, custom template, or built-in layer.

For same-container merge:

- preserve the source export as rollback evidence;
- record whether the artifact is a review patch or final-state patch;
- omit unchanged object arrays when possible;
- include only changed objects plus schema dependencies;
- document objects that cannot be deleted by omitted arrays;
- validate original export plus patch against the intended final state.

## View Changes Review

When the user wants GTM's View Changes screen to inspect per-object
modifications, generate a name-preserving review patch:

- preserve existing tag, trigger, variable, folder, and template names;
- rewrite `{{Variable Name}}`, setup-tag, and teardown-tag references back to
  source names;
- defer naming standardization from this review artifact;
- state that direct GTM/MCP/API or a separate final-state artifact is required
  for final naming.

Use `scripts/gtm_make_name_preserving_review_patch.py` when Python is available.

## Final-State Or Replacement JSON

For manual same-container final-state JSON, replacement/additive objects can be
safer than forcing every object to import as an in-place edit. Use this route
when existing GTM conflicts or empty-value errors make direct-style edits
fragile.

When replacement/additive objects are used:

- provide an old-to-new replacement map;
- prove that consuming tags/triggers/variables point to the intended objects;
- separate decommission candidates from objects that remain blocked;
- do not pretend GTM View Changes will show clean in-place modifications.

For overwrite or new-container imports, a full cleaned export can directly
update, omit, or delete objects because same-container conflict resolution is
not the main constraint.

## Schema Dependencies

Apply `POL-205` through `POL-208` from `policy-register.md`:

- include folders referenced by changed objects' `parentFolderId`;
- include required custom templates for `cvt_*` tag or variable types;
- include the complete intended `customTemplate` layer when GTM needs template
  validation for included objects;
- preserve enabled built-in variables;
- do not include unchanged templates merely as cleanup noise when no included
  object needs them.

## Validation Commands

Use deterministic helpers when Python is available:

```bash
python scripts/gtm_make_merge_patch.py original.json cleaned.json patch.json
python scripts/gtm_make_name_preserving_review_patch.py original.json cleaned.json review.json
python scripts/gtm_validate_artifact.py artifact.json --original original.json --mode same-container-view
python scripts/gtm_validate_artifact.py artifact.json --original original.json --mode same-container-final
python scripts/gtm_validate_artifact.py artifact.json --mode overwrite
python scripts/gtm_diff_operations.py original.json cleaned.json --csv change_log.csv
python scripts/gtm_diff_operations.py original.json patch.json --patch --csv change_log.csv
```

## Failure Handling

Do not deliver JSON as import-ready when validation fails unless the user
explicitly accepts the residual blocker. Report the failed check, affected
object IDs/names, reason, route limitation, and recommended next step.

Common failures:

- unknown cleanup/setup/teardown tag reference;
- unknown folder from `parentFolderId`;
- unknown custom template entity type;
- accidental omission of built-in variables;
- single-member trigger groups left in overwrite/new-container output;
- broad add/delete churn in View Changes review artifacts;
- active GA4/current Google payloads still reading UA Enhanced Ecommerce paths
  without a verified mapper.
