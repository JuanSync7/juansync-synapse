# Escalation Rules

Loaded by `synapse-router-suite-validator` Phase 5 when `--escalate` is passed. Without these rules, escalation either (a) fans out unbounded LLM calls and exhausts budget, or (b) wastes calls on artifacts that have known structural failures.

---

## Precondition: structural sweep is clean

`--escalate` runs `/synapse-router-artifact-gatekeeper` on every artifact in parallel. Quality review on a structurally broken artifact is wasted budget — gatekeeper will REJECT it on Phase 1 anyway.

**Rule:** If Phase 3 or Phase 4 produced ANY failure, skip escalation entirely. The Quality section is omitted from the rollup. The Recommendation paragraph notes: "Escalation skipped — fix structural failures and re-run with `--escalate`."

---

## Parallel cap

Dispatch `/synapse-router-artifact-gatekeeper` calls in parallel batches, **capped at 8 concurrent**. The cap exists for two reasons:

1. **LLM rate limits** — bursting 50 concurrent gatekeeper calls trips Anthropic API rate limits and aborts mid-sweep.
2. **Token budget visibility** — bounded concurrency keeps the cost per validator run within an order of magnitude the maintainer can predict.

Use `TaskCreate` to spawn each batch; wait for the batch to complete before starting the next.

---

## Per-artifact dispatch

For each artifact, dispatch:

```
TaskCreate "/synapse-router-artifact-gatekeeper <absolute-path-to-artifact>"
```

For skill artifacts, the artifact path is the skill directory. For agent / protocol artifacts, it is the `.md` file. For tool artifacts, it is the tool directory. For pathway artifacts, it is the `.yaml` file. Gatekeeper handles type detection from the path shape.

Do NOT pass `--score` to escalated calls — the validator is not running quality measurement, just promotion review. Gatekeeper will mark the quality tier `unverified` and cap its verdict at REVISE for skills without scores; that is acceptable here. The validator's role is to surface "would gatekeeper accept this today?", not to generate scores.

---

## Aggregation

Collect each gatekeeper verdict and emit them in the rollup's `### Quality (escalated)` section, one bullet per artifact:

```
- skill/api-linter — APPROVE
- skill/jira-reporter — REVISE (no score; eval missing)
- agent/eval-judge — APPROVE
```

**Rollup-verdict downgrade:** A single escalated REVISE downgrades the suite verdict from APPROVE to REVISE. A single escalated REJECT downgrades to REJECT. The downgrade rule mirrors the "weakest link" semantics of the structural sweep.

---

## Partial failure handling

If a `TaskCreate` invocation fails (network, sandbox, dispatcher error), record the artifact as `ESCALATION_ERROR` in the Quality section:

```
- skill/foo — ESCALATION_ERROR (gatekeeper dispatch failed; rerun manually)
```

A dispatch error does NOT downgrade the suite verdict — it is a tooling issue, not an artifact issue. The Recommendation paragraph notes the artifacts that need a manual gatekeeper rerun.

---

## When NOT to use `--escalate`

The validator's normal mode (no flag) is the right tool for:
- Pre-commit checks on the suite repo
- CI gating on submodule update PRs
- Quick "is this still in shape?" sweeps

`--escalate` is the right tool only when:
- The suite is being **promoted** (first wire-in, or version bump after substantial changes)
- A maintainer wants the **full quality picture** before signing off

Running `--escalate` on every commit burns LLM budget for no gain — structural drift is the common case, and the structural sweep catches it without LLM calls.
