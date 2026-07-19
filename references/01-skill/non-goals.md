# Non-Goals

Do not use this skill for:

- Tag Assistant, GTM Preview, browser/network, live dataLayer, CMP-interaction,
  or vendor-platform QA;
- legal approval or privacy-policy interpretation;
- website/dataLayer implementation work;
- auditing an unseen server container merely because a web container sends to it;
- publishing GTM versions;
- mutation without explicit approval and rollback protection;
- deleting an object based only on age, name, inactivity assumptions, or a
  similarity score;
- inventing GTM-side custom JavaScript when the correct solution is a website
  or dataLayer contract;
- replacing literal behavior with categories such as `computed value`,
  `vendor loader`, or `payload transformer`;
- producing a real change log before cleanup execution.

When the request needs live validation, use a separate recette/runtime workflow.
When evidence cannot decide business necessity or legal consent, ask one precise
owner question instead of guessing.
