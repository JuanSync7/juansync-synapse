# Decision Memo — test-fix

> Artifact type: skill | Memo type: creation | Design doc: `.brainstorms/2026-04-28-test-strategy-improvements/` (design doc pending; HITL gate semantics defined in `notepad.md` § Cross-cutting › HITL Gate Semantics)

---

## What I want

A semi-autonomous skill that consumes a `LintReport` produced by `test-lint` and systematically resolves all auto-resolvable lint issues across five categories (ruff → mypy → bandit → vulture → secrets), re-verifying after each category before moving on. Issues that require human judgment are surfaced explicitly rather than guessed at. At the end, the skill opens a soft-gated PR summarising every change made, queuing a reviewer without blocking the engine.

Scope:
- Iterates per issue category, not per individual file, to keep commits coherent and reviewable.
- Re-runs `lint_reporter` after each category to confirm the category is clean before advancing.
- Identifies issues that fall outside autonomous resolution (dead code in public API, secret rotation) and flags them with `requires-human-review` rather than skipping silently.
- Stops when `LintReport.issues` is empty OR all remaining issues are tagged `requires-human-review`.
- Opens a PR with a per-category fix summary; reviewer triages async (soft gate).

---

## Why Claude needs it

Without this skill, Claude's default behaviour when asked to "fix lint" is to make a single-pass best-effort edit sweep with no systematic category ordering, no re-verification between categories, and no principled stopping condition. Three concrete failure modes result:

1. **Policy violations go undetected.** Claude will append `# type: ignore` to silence mypy rather than adding a proper annotation, because nothing tells it that suppression requires an explicit reason in the commit message. Similarly, it will delete a bandit-flagged check instead of refactoring it.
2. **Fix order creates regressions.** Applying ruff autofixes after mypy type-annotation fixes on the same file can silently undo an annotation. Without a prescribed order and per-category re-verification, overlapping fixes are not caught.
3. **Vulture over-deletion.** Claude deletes dead code at any confidence level. Without a minimum confidence threshold, it removes code that is actually reachable through dynamic imports or plugin hooks.

The skill provides the ordering rules, per-category re-verification checkpoints, and hard constraints that prevent all three failure modes.

---

## Injection shape

- **Workflow:** Per-category fix loop — five sequential phases (ruff → mypy → bandit → vulture → secrets), each with a fix step and a mandatory re-verification step, followed by a PR-open step.
- **Policy:** Judgment rules that govern when to act vs. escalate:
  - Never `# type: ignore` without an explicit reason in the commit message.
  - Never remove a security check from bandit findings — refactor instead.
  - Never delete code flagged by vulture unless `confidence ≥ 90%`.
  - Secret remediation (rotate, don't just delete) is out-of-scope — surface to human.
  - Dead code in a public API surface is flagged `requires-human-review`, not auto-deleted.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| Source edits (committed per category) | 1–5 commits | Yes | One commit per lint category resolved |
| `requires-human-review` flag list | 1 | No | Issues the skill cannot autonomously resolve |
| Soft-gated PR with fix summary | 1 | No | Queues reviewer; engine continues without blocking |
| Clean codebase (lint-passing) | — | Yes | Prerequisite for `test-audit` to run |

---

## Flow graph

```
LintReport (from lint)
  ↓
[TRIAGE] partition issues by category
  ↓
[FIX-RUFF] apply ruff-safe autofixes
  ↓
[VERIFY-RUFF] re-run lint_reporter (ruff only) → if issues remain → flag requires-human-review
  ↓ commit "fix(lint): ruff"
[FIX-MYPY] add type annotations, resolve type errors
  ↓
[VERIFY-MYPY] re-run lint_reporter (mypy only) → if issues remain → flag requires-human-review
  ↓ commit "fix(lint): mypy"
[FIX-BANDIT] refactor security-flagged code (never delete check)
  ↓
[VERIFY-BANDIT] re-run lint_reporter (bandit only) → if issues remain → flag requires-human-review
  ↓ commit "fix(lint): bandit"
[FIX-VULTURE] delete dead code (confidence ≥ 90% only)
  ↓
[VERIFY-VULTURE] re-run lint_reporter (vulture only) → if issues remain → flag requires-human-review
  ↓ commit "fix(lint): vulture"
[SURFACE-SECRETS] flag all detect-secrets findings as requires-human-review (rotation OOS)
  ↓
[OPEN-PR] compile per-category summary + requires-human-review list → open PR → soft gate
  ↓
work continues (reviewer triages async)
```

---

## Node specifications

**[TRIAGE]** — Load: `rules/fix-constraints.md`. Do: partition `LintReport.issues` into five buckets (ruff, mypy, bandit, vulture, secrets). Identify any issues that are immediately `requires-human-review` (e.g., bandit finding where the check cannot be refactored without architecture change). Do not edit source files. Exit: proceed to FIX-RUFF.

**[FIX-RUFF]** — Load: `rules/fix-constraints.md`. Do: apply ruff-safe, deterministic autofixes (formatting, import ordering, simple style rules). Do not touch mypy/bandit/vulture issues. Do not add `# noqa` suppressions without flagging. Exit: proceed to VERIFY-RUFF.

**[VERIFY-RUFF]** — Load: none (tool call only). Do: re-run `lint_reporter` scoped to ruff. If new issues found: flag as `requires-human-review` with message. Exit: commit ruff changes; proceed to FIX-MYPY.

**[FIX-MYPY]** — Load: `rules/fix-constraints.md`, `references/mypy-fix-patterns.md`. Do: add missing annotations, fix type errors via refactor or correct annotation. Never add `# type: ignore` without appending the reason as a commit-message note. Exit: proceed to VERIFY-MYPY.

**[VERIFY-MYPY]** — Load: none (tool call only). Do: re-run `lint_reporter` scoped to mypy. Flag unresolvable issues as `requires-human-review`. Exit: commit mypy changes; proceed to FIX-BANDIT.

**[FIX-BANDIT]** — Load: `rules/fix-constraints.md`, `references/bandit-remediation.md`. Do: refactor code to eliminate the security finding. Never delete the security check itself. If refactoring is architecturally non-trivial, flag as `requires-human-review`. Exit: proceed to VERIFY-BANDIT.

**[VERIFY-BANDIT]** — Load: none (tool call only). Do: re-run `lint_reporter` scoped to bandit. Flag remaining issues as `requires-human-review`. Exit: commit bandit changes; proceed to FIX-VULTURE.

**[FIX-VULTURE]** — Load: `rules/fix-constraints.md`, `references/vulture-cleanup.md`. Do: delete dead code only if `confidence ≥ 90%`. For code in a public API surface (`__all__`, decorated, or imported externally), flag as `requires-human-review` regardless of confidence. Exit: proceed to VERIFY-VULTURE.

**[VERIFY-VULTURE]** — Load: none (tool call only). Do: re-run `lint_reporter` scoped to vulture. Flag remaining issues as `requires-human-review`. Exit: commit vulture changes; proceed to SURFACE-SECRETS.

**[SURFACE-SECRETS]** — Load: `rules/fix-constraints.md`, `references/secret-remediation.md`. Do: read all detect-secrets findings from `LintReport`. Mark every finding as `requires-human-review` with remediation note (rotate the credential — do not simply delete). Never remove the secret string autonomously. Exit: proceed to OPEN-PR.

**[OPEN-PR]** — Load: `templates/fix-report.md`. Do: compile per-category change summary and `requires-human-review` list. Open PR. Soft gate: PR opens, review is queued in the reviewer backlog, engine moves on without waiting. Exit: skill complete; clean codebase handed off to `test-audit`.

---

## Entry gates

| Transition | Gate |
|---|---|
| Start → TRIAGE | `LintReport` present and parseable; `LintReport.issues` is non-empty OR skill exits immediately with "nothing to fix" |
| VERIFY-RUFF → commit | Re-run completed; remaining ruff issues (if any) recorded as `requires-human-review` |
| VERIFY-MYPY → commit | Re-run completed; remaining mypy issues (if any) recorded as `requires-human-review` |
| VERIFY-BANDIT → commit | Re-run completed; remaining bandit issues (if any) recorded as `requires-human-review` |
| VERIFY-VULTURE → commit | Re-run completed; remaining vulture issues (if any) recorded as `requires-human-review` |
| SURFACE-SECRETS → OPEN-PR | All detect-secrets findings flagged |
| OPEN-PR → done | PR opened (soft gate — non-blocking). For gate semantics (soft vs. hard) see notepad.md § Cross-cutting › HITL Gate Semantics. |

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| Overlapping fixes (ruff autofix + mypy fix touch same line) | Prescribed category order (ruff first, then mypy) ensures ruff's deterministic formatting runs before mypy annotations are added. VERIFY-RUFF catches any collision before mypy phase starts. Creator must specify commit granularity (per-category default recommended). |
| Secret remediation out-of-scope | detect-secrets findings are never auto-resolved. Every finding is flagged `requires-human-review` with a rotation playbook note. Deleting the secret string is explicitly prohibited. |
| Vulture false positives (dynamic imports, plugin hooks) | Confidence threshold of ≥ 90% applied. Public API surface (code in `__all__`, decorated, imported externally) is always `requires-human-review` regardless of confidence — vulture cannot detect runtime callers in those cases. |
| Dead code in public API | Flagged `requires-human-review` even at 100% vulture confidence. API surface removals require human judgment on backward compatibility. |
| All issues are `requires-human-review` | Skill opens PR with only the flagged list (no source edits). Stopping condition is satisfied — PR is the deliverable. |
| `LintReport.issues` is empty on arrival | Skill exits immediately: "nothing to fix — codebase already lint-clean." No PR opened. |
| Re-verification finds new issues (fix introduced regression) | New issues from re-verification are appended to `requires-human-review` with note "introduced during fix phase." Skill does not loop back to re-fix; human resolves. |

---

## Companion files anticipated

**Always loaded (rules):**
- `rules/fix-constraints.md` — loaded at every node. Encodes: never `# type: ignore` without reason, never remove security check, never delete code below vulture confidence threshold, secret rotation is out-of-scope.

**References (loaded per node):**
- `references/mypy-fix-patterns.md` — loaded at FIX-MYPY. Common annotation fixes and refactor patterns.
- `references/bandit-remediation.md` — loaded at FIX-BANDIT. Security fix recipes, refactor examples.
- `references/vulture-cleanup.md` — loaded at FIX-VULTURE. Dead-code removal heuristics and confidence guidance.
- `references/secret-remediation.md` — loaded at SURFACE-SECRETS. Rotation playbook; what to surface to the human.

**Templates:**
- `templates/fix-report.md` — loaded at OPEN-PR. Per-PR change summary template (per-category table + `requires-human-review` section).

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `test-lint` | consumes | `LintReport` pydantic model (defined in `ai-synapse/tools/testing/schemas.py`). Fields: `issues: list[LintIssue]`, `files_scanned: int`, `duration_ms: int`, `descriptive_test_violations: list[LintIssue]`. |
| `test-audit` | produces for | Clean codebase (all linters pass). `audit` precondition is lint-clean; `fix` is the gate. No explicit handoff artifact — codebase state is the contract. |
| `lint_reporter` tool | calls | Re-verification calls scoped to one category at a time (ruff/mypy/bandit/vulture/detect-secrets). Returns `LintReport` subset. |

---

## Open questions

1. **Commit granularity:** Per-category (one commit per linter) is the recommended default. Creator should decide whether to offer a per-file option and document it in the skill.
2. **Overlapping fix ordering rule:** The memo prescribes ruff-first. Creator should validate this ordering against real RagWeave lint output to confirm no mypy annotation is destroyed by a subsequent ruff run.
3. **`# type: ignore` with reason — enforcement mechanism:** The constraint says "never without reason in commit message." Creator must decide whether the skill enforces this by inspecting the commit message before committing, or whether it is a policy statement that the skill self-applies.
4. **Bandit architectural non-triviality threshold:** What qualifies as "too hard to refactor" for a bandit finding? Creator should define a heuristic (e.g., finding involves subprocess/pickle/eval in a core module → escalate) rather than leaving it to per-call LLM judgment.
5. **PR soft gate notification channel:** The cross-cutting section specifies Slack/email for hard gates. Soft gates queue to a review backlog. Creator should confirm the backlog mechanism (GitHub PR label, project tracker ticket, or just the PR queue itself).
