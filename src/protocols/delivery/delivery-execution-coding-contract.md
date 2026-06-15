---
name: delivery-execution-coding-contract
description: "Subagent code-quality discipline injected per dispatch — YAGNI, neighbors-first, no-dead-code, fail-loudly, green-tree-exit (lint+typecheck), security-tripwires. Complements tdd-contract; not for slice anatomy (slice-contract) or test-first/Ralph (tdd-contract)."
domain: delivery
subdomain: execution
subject: coding
kind: contract
version: 1
status: stable
tags: [code-quality, yagni, lint-typecheck, security-tripwires, subagent-discipline]
---

# Coding Contract

Without this contract, subagent workers ship speculative abstractions, neighbor-blind drops, dead code, swallowed exceptions, fabricated lint/typecheck claims, and hardcoded secrets. `tdd-contract` enforces test-first and Ralph; `slice-contract` enforces slice shape and edges; `closeout-schema` enforces report wire format. None of them catch what the worker wrote *inside* the source diff. This contract closes that gap with six rules — four bright-line auto-reject, two advisory-with-signature — every one anchored to a compliance signature the main agent can verify against the closeout. Two rules (5, 6) are explicitly non-overrideable so the escape hatch never collapses into a backdoor.

## Contract

1. **YAGNI / no speculative abstraction.** BEFORE adding any file to `files_created`, verify the file is NOT named `*_factory*`, `*_wrapper*`, or `*_base*` with a single caller in `files_modified`. If the file matches this signature, STOP and route to replan with reason `speculative_abstraction`. A refactor or extension idea surfaced mid-slice MUST NOT be implemented — surface it in `next_moves` with `rationale: yagni_deferred`.

2. **Read neighbors first.** BEFORE editing any file in `files_modified`, MUST identify and read at least one sibling file in the same module that defines the matching idiom (style, naming, error-handling). AFTER completing the slice, MUST populate `neighbors_consulted: [<file paths>]` in the closeout with the files read. If the field is absent or empty, STOP and route to replan with reason `neighbors_unconsulted`.

3. **No dead code.** BEFORE writing the closeout, MUST scan the `files_modified` diff for commented-out code. A commented-out code block is two or more consecutive lines matching `^\s*[#//]\s*[a-zA-Z_]+\s*[=(.]`, excluding lines containing `TODO`, `FIXME`, `noqa`, or `type:ignore`. If any block matches, MUST populate `dead_code_violations: [<file:line ranges>]` in the closeout. Any non-empty value rejects the closeout; route to replan.

4. **Fail loudly.** DO NOT introduce bare except / catch-and-ignore in `files_modified`. The diff MUST NOT contain `except:\s*pass`, `except\s+Exception:\s*pass`, `rescue\s*=>\s*nil`, or `catch\s*\(\s*_+\s*\)\s*{\s*}`. AFTER each file edit, MUST re-scan the patched lines for these patterns. On match, STOP and route to replan with reason `silent_failure`.

5. **Green-tree exit (lint + typecheck) — non-overrideable.** BEFORE emitting the closeout, MUST invoke the project's lint tool and typecheck tool. THEN populate `lint_command_invoked`, `lint_exit_code`, `lint_result`, `lint_output_digest`, `typecheck_command_invoked`, `typecheck_exit_code`, and `typecheck_result` in the closeout. Each `*_result` field MUST take one of `pass | fail | not_applicable`. The `not_applicable` value MUST come from the orchestrator's `[PRE-FLIGHT]` determination — the worker MUST NOT assign it. If any `*_result: pass` is reported without a corresponding `*_command_invoked` value, the closeout is a fabricated pass — STOP and flag for human review with reason `lint_typecheck_fabrication`.

6. **Security-tripwires — non-overrideable.** BEFORE writing the closeout, MUST scan the `files_modified` diff for: (a) string literals matching common token / secret shapes (high-entropy 20+ char strings, `AKIA[0-9A-Z]{16}`, `sk-[A-Za-z0-9]{20,}`, `ghp_[A-Za-z0-9]{20,}`); (b) string-concatenated SQL via `+` or interpolation that references an external input; (c) boundary inputs (HTTP body, file read, env var) used downstream WITHOUT an explicit validator call. On any match, STOP and route to replan with reason `security_tripwire`.

7. **Discipline deltas.** A worker MAY only deviate from rules 1, 2, 3, or 4 by populating `applied_deltas: [{rule_id: <int>, exception_scope: <file glob>, justification: <text>}]` in the closeout. `rule_id ∈ {5, 6}` MUST reject the dispatch immediately. An unknown `rule_id` MUST reject the dispatch. Every entry in `applied_deltas` MUST echo verbatim into the closeout — no summarization.

## Failure Assertion

If the orchestrator's pre-flight verification of dispatch-contract loading or this protocol's presence in `worker_protocols` fails — or if the worker receives a dispatch prompt that does not contain this contract's rule set — STOP and output:

`PROTOCOL FAILURE: delivery-execution-coding-contract — [precondition: dispatch-contract not loaded | protocol absent from worker_protocols | injection collision: multiple coding-discipline variants present]`

If the closeout lacks any required field from rules 2, 3, 5, or 7 above, STOP and output:

`PROTOCOL FAILURE: delivery-execution-coding-contract — closeout missing required field: [field-name]`

## Configuration

| Mode | Behavior | Default |
|------|----------|---------|
| `applied_deltas` | Per-dispatch override list scoped to a file glob; deltas against rules 1–4 only; deltas against 5 or 6 reject dispatch | empty (no deltas) |
