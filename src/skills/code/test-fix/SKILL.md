---
name: test-fix
description: "consume a LintReport from test-lint and resolve auto-fixable issues per category (ruff→mypy→bandit→vulture→secrets) with re-verification, surfacing requires-human-review items and opening a soft-gated PR"
domain: code.test
intent: refactor
tags: [lint, fix, ruff, mypy, bandit, vulture, secrets, autofix]
user-invocable: true
argument-hint: "[--lint-report PATH] [--no-pr]"
---

Second stage of the 6-skill test coverage engine. Consumes `LintReport` produced by `test-lint`; iterates through five lint categories (ruff → mypy → bandit → vulture → secrets) with mandatory re-verification between categories. Issues that require human judgment are surfaced as `requires-human-review` rather than guessed at. Closes with a soft-gated PR summarising every change.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## MUST (every turn)
- Load `rules/fix-constraints.md` — invariants apply at every fix and verify node
- Record position: `Position: [node-id] — <context>`
- Run categories in declared order (ruff → mypy → bandit → vulture → secrets); commit per category before advancing
- Re-verify after each fix node before committing or advancing

## MUST NOT (global)
- Add `# type: ignore`, `# noqa`, or `# nosec` without recording an explicit reason in the commit message
- Remove a bandit-flagged security check — refactor only, or escalate as `requires-human-review`
- Delete code flagged by vulture below the 90% confidence threshold or that lives on a public API surface (`__all__`, decorated, imported externally)
- Auto-resolve detect-secrets findings — every finding is `requires-human-review` with a rotation note; never delete the secret string
- Loop back to re-fix when re-verification finds new issues — append them to `requires-human-review` with "introduced during fix phase" and continue

## Wrong-Tool Detection
- **User wants a fresh lint scan** → `/test-lint` (produces the LintReport this skill consumes)
- **User wants test coverage gaps audited** → `/test-audit` (downstream, requires lint-clean state)
- **User wants tests written** → `/test-generate`
- **User has no LintReport on disk** → `/test-lint` first, then return here

## Entry

### [NEW] Fresh session
Do:
  1. Parse arguments: `--lint-report` (default `project/coverage/state/LINT_REPORT.json`), `--no-pr` (skip [OPEN-PR], stop after VERIFY-VULTURE).
  2. Load `LintReport` from disk; verify it parses against `ai-synapse/tools/testing/schemas.py` `LintReport` model.
  3. If `LintReport.issues` is empty AND `descriptive_test_violations` is empty → print "nothing to fix — codebase already lint-clean" and exit (no PR).
  4. Confirm `lint_reporter` tool is available in `ai-synapse/tools/testing/` — abort if missing.
Don't: Proceed if the report cannot be parsed; proceed if `lint_reporter` is missing.
Exit: → [TRIAGE]

## Flow

### [TRIAGE] Partition issues by category
Load: rules/fix-constraints.md
Do: Partition `LintReport.issues` into five buckets keyed by `tool` (ruff, mypy, bandit, vulture, detect-secrets). Pre-flag obvious `requires-human-review` items: bandit findings on subprocess/pickle/eval in core modules, vulture findings on `__all__`/decorated/externally-imported symbols, all detect-secrets findings. Initialize `requires_human_review: list[LintIssue]` for accumulation.
Don't: Edit any source file; collapse buckets; drop issues silently.
Exit: → [FIX-RUFF]

### [FIX-RUFF] Apply ruff-safe autofixes
Load: rules/fix-constraints.md
Do: Apply ruff-safe deterministic autofixes (formatting, import ordering, simple style). Touch only ruff-bucket issues; leave mypy/bandit/vulture issues untouched. If a fix requires `# noqa`, append the rule code and reason to the bucket's commit-message draft.
Don't: Cross category boundaries; suppress with bare `# noqa`.
Exit: → [VERIFY-RUFF]

### [VERIFY-RUFF] Re-run ruff scope
Do: Invoke `lint_reporter` scoped to ruff. Append any remaining ruff issues to `requires_human_review` with note "ruff verify residual". Commit edits as `fix(lint): ruff` (include the suppression-reason notes from [FIX-RUFF] in the commit body, if any).
Don't: Loop back to [FIX-RUFF]; commit if no edits were made.
Exit: → [FIX-MYPY]

### [FIX-MYPY] Resolve mypy errors
Load: rules/fix-constraints.md, references/mypy-fix-patterns.md
Do: Add missing annotations or refactor to satisfy strict-mode mypy. If `# type: ignore` is unavoidable, append the precise error code (`# type: ignore[arg-type]`) and record the reason in the commit-message draft.
Don't: Use bare `# type: ignore`; suppress without commit-message reason; touch ruff-only style issues.
Exit: → [VERIFY-MYPY]

### [VERIFY-MYPY] Re-run mypy scope
Do: Invoke `lint_reporter` scoped to mypy. Append unresolved issues to `requires_human_review` with note "mypy verify residual". Commit as `fix(lint): mypy` with suppression reasons in body.
Don't: Re-fix; commit empty changes.
Exit: → [FIX-BANDIT]

### [FIX-BANDIT] Refactor security findings
Load: rules/fix-constraints.md, references/bandit-remediation.md
Do: Refactor flagged code to remove the underlying risk (replace `subprocess` with safer API, swap pickle for json, parameterise SQL). If the finding requires architectural change beyond the fix scope, append to `requires_human_review` with note "bandit architectural escalation".
Don't: Delete the security check itself; add `# nosec` without explicit reason in commit body.
Exit: → [VERIFY-BANDIT]

### [VERIFY-BANDIT] Re-run bandit scope
Do: Invoke `lint_reporter` scoped to bandit. Append residuals to `requires_human_review`. Commit as `fix(lint): bandit`.
Don't: Re-fix; bypass the verification call.
Exit: → [FIX-VULTURE]

### [FIX-VULTURE] Delete dead code (≥90% confidence only)
Load: rules/fix-constraints.md, references/vulture-cleanup.md
Do: Delete unused symbols only when vulture confidence is ≥90% AND the symbol is not in `__all__`, not decorated, and has no external importers. Public-API or low-confidence findings → append to `requires_human_review` with note "vulture public-api" or "vulture low-confidence".
Don't: Delete plugin entry points, decorated callables, or `__all__` members; lower the threshold.
Exit: → [VERIFY-VULTURE]

### [VERIFY-VULTURE] Re-run vulture scope
Do: Invoke `lint_reporter` scoped to vulture. Append residuals to `requires_human_review`. Commit as `fix(lint): vulture`.
Don't: Re-fix; relax threshold.
Exit: → [SURFACE-SECRETS]

### [SURFACE-SECRETS] Flag detect-secrets findings
Load: rules/fix-constraints.md, references/secret-remediation.md
Do: For every detect-secrets issue in the bucket, append to `requires_human_review` with the rotation playbook reference (which credential, where it was found, recommended rotation steps).
Don't: Delete the secret string; rewrite history; commit any change.
Exit: → [OPEN-PR]

### [OPEN-PR] Open soft-gated PR
Load: templates/fix-report.md
Do:
  1. Compile per-category change summary (commits made, files touched, residuals).
  2. Render `requires_human_review` list with category, file, line, code, reason.
  3. If `--no-pr`, write the rendered report to `project/coverage/state/FIX_REPORT.md` and exit.
  4. Otherwise open a PR using the template; apply GitHub label `requires-human-review` if the list is non-empty (soft gate — non-blocking).
Don't: Wait for review; merge the PR; mark blocking.
Exit: → [END]

### [END]
Do: Print PR URL (or report path with `--no-pr`), per-category commit list, and `requires_human_review` count. Suggest `/test-audit` once the PR is reviewed and merged.
Don't: Auto-route or invoke `/test-audit` directly — handoff is the user's call.
