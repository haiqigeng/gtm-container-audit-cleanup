# Non-Goals

Use this file to avoid expanding the skill beyond its intended responsibility.

The skill is not:

- a simple duplicate, unused-object, or naming cleanup bot;
- a legal/privacy decision maker;
- a replacement for missing website or dataLayer implementation;
- a full server-side GTM audit unless server evidence is available and in
  scope;
- a tool that guesses business intent when evidence is unclear;
- a tool that publishes GTM versions;
- a tool that mutates GTM without explicit approval;
- a tool that floods users with raw config, full code dumps, validator traces,
  or internal reasoning;
- a tool that invents GTM-side custom JavaScript when the correct fix is a
  website/dataLayer contract.
- a tool that replaces literal object behavior with broad categories such as
  "computed value", "payload transformer", or "browser side effect";
- a tool that creates a real post-cleanup change log before cleanup execution.
  Before execution, use `planned change preview` or clearly mark simulated logs.

When a request falls outside these boundaries, record the blocker, owner, or
external work needed.
