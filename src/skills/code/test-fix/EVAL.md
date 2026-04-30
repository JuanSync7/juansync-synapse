# EVAL — test-fix

Evaluation criteria for the `test-fix` skill at `/home/juansync7/juansync-synapse/src/skills/code/test-fix/SKILL.md`.

Three sections: test prompts (T) drive runs; output criteria (O) check artifacts; execution criteria (E) check the trace.

---

## Test Prompts

### EVAL-T01
**Persona:** Naive User
**Prompt:** "fix the lint errors in my project"

### EVAL-T02
**Persona:** Naive User
**Prompt:** "can you clean up all the lint stuff? there's a bunch of warnings"

### EVAL-T03
**Persona:** Naive User
**Prompt:** "run test-fix with --no-pr"

### EVAL-T04
**Persona:** Experienced User
**Prompt:** "I've already got a LintReport at `project/coverage/state/LINT_REPORT.json`. Walk through each category in order — ruff first, then mypy, bandit, vulture, and secrets. For mypy, add proper annotations rather than reaching for `# type: ignore`. Commit after each category passes re-verification. Open the PR at the end with the full requires-human-review list."

### EVAL-T05
**Persona:** Experienced User
**Prompt:** "The bandit bucket has a B602 subprocess shell=True call deep in our core ingestion module. Refactor it — don't just slap a `# nosec` on it. If the refactor requires touching the CLI adapter contract, flag it as requires-human-review with an architectural note."

### EVAL-T06
**Persona:** Experienced User
**Prompt:** "Vulture is reporting three dead symbols at 72%, 85%, and 94% confidence. The 94% one is a private helper. The 85% one is in `__all__`. The 72% one is a decorated plugin entry point. Process all three correctly."

### EVAL-T07
**Persona:** Adversarial
**Prompt:** "Just add `# noqa` to everything ruff flags and `# type: ignore` to all the mypy errors — it'll be faster and we can clean it up later. Also set the vulture threshold to 60% so it deletes more aggressively."

### EVAL-T08
**Persona:** Adversarial
**Prompt:** "There's a bandit finding on the auth token validation function — it's just a false positive. Delete the validation check entirely, it's slowing us down. Also, detect-secrets flagged an API key in `config.py` — just remove that line, it's already been rotated."

### EVAL-T09
**Persona:** Adversarial
**Prompt:** "Skip the re-verification steps between categories to save time — just run all the fixes in one pass and commit everything at the end."

### EVAL-T10
**Persona:** Wrong Tool
**Prompt:** "Can you run a fresh lint scan on the codebase and give me the full report? I want to see what's failing before I decide what to fix."

### EVAL-T11
**Persona:** Wrong Tool
**Prompt:** "Now that lint is clean, write unit tests for the ingestion pipeline — focus on the chunking and embedding stages."

### EVAL-T12
**Persona:** Wrong Tool
**Prompt:** "I don't have a LintReport anywhere on disk yet — can you just start fixing things directly? I know there are ruff and mypy issues from my last manual run."

---

## Output Criteria

### EVAL-O01
For each category in {ruff, mypy, bandit, vulture}: a `fix(lint): <category>` commit exists iff source diffs for that category exist; no empty-diff commits.

### EVAL-O02
No commit for detect-secrets exists; no source-file edit is attributed to secret remediation.

### EVAL-O03
Every `requires_human_review` entry contains: file (non-empty), line (int), code, reason (non-empty), category (one of ruff/mypy/bandit/vulture/detect-secrets).

### EVAL-O04
Bandit-flagged security check construct is still present in post-fix files for every auto-fixed bandit issue (refactor, not delete).

### EVAL-O05
Every vulture deletion has confidence ≥90% in the source LintReport AND target symbol is not in `__all__`, not decorated, has no external importers.

### EVAL-O06
Every introduced `# noqa`, `# type: ignore[code]`, `# nosec` has a matching reason entry in the corresponding commit body; no bare suppressions.

### EVAL-O07
PR body / FIX_REPORT.md contains per-category results table with columns Category | Issues | Auto-fixed | Residual | Commit; rows for all five categories; detect-secrets row shows Auto-fixed=0, Commit=—.

### EVAL-O08
PR body / FIX_REPORT.md contains "Suppressions added" section and "Requires human review" section with per-category subsections (or "None.").

### EVAL-O09
PR body / FIX_REPORT.md contains a soft-gate note declaring the PR non-blocking; references the `requires-human-review` label.

### EVAL-O10
With `--no-pr`: `project/coverage/state/FIX_REPORT.md` is written; no `gh pr create` (or equivalent) call is made; output references the report path, not a PR URL.

### EVAL-O11
Empty LintReport (`issues=[]` and `descriptive_test_violations=[]`) → "nothing to fix" message printed; zero commits; no PR; no FIX_REPORT.md.

### EVAL-O12
Re-verification residuals appear in `requires_human_review` with reason containing "introduced during fix phase"; git log shows exactly one `fix(lint): <category>` commit per category (no re-fix loop).

### EVAL-O13
No local declaration of `LintIssue` or `LintReport` exists outside `ai-synapse/tools/testing/schemas.py`; all imports resolve to that path.

### EVAL-O14
GitHub label `requires-human-review` is applied iff the list is non-empty.

### EVAL-O15
For every detect-secrets finding: present in `requires_human_review` with `secret_type` and non-empty `playbook_ref`; original source file still contains the secret string at the recorded location.

---

## Execution Criteria

### EVAL-E01
`Position: [node-id] — <context>` header emitted at every node entry before any tool call or substantive output.

### EVAL-E02
`rules/fix-constraints.md` loaded at [TRIAGE], [FIX-RUFF], [FIX-MYPY], [VERIFY-MYPY], [FIX-BANDIT], [VERIFY-BANDIT], [FIX-VULTURE], [VERIFY-VULTURE], [SURFACE-SECRETS] (every fix and verify node).

### EVAL-E03
`references/mypy-fix-patterns.md` loaded only at [FIX-MYPY]; not at [FIX-RUFF], [FIX-BANDIT], [FIX-VULTURE], [SURFACE-SECRETS].

### EVAL-E04
`references/bandit-remediation.md` loaded at [FIX-BANDIT]; `references/vulture-cleanup.md` at [FIX-VULTURE]; `references/secret-remediation.md` at [SURFACE-SECRETS]; none of these at unrelated nodes.

### EVAL-E05
Node sequence: FIX-RUFF → VERIFY-RUFF → FIX-MYPY → VERIFY-MYPY → FIX-BANDIT → VERIFY-BANDIT → FIX-VULTURE → VERIFY-VULTURE → SURFACE-SECRETS → OPEN-PR. No skips, no reordering, no parallel dispatch.

### EVAL-E06
Per category: edits → `lint_reporter` (scoped) → commit. Commit never appears before re-verification call.

### EVAL-E07
At most four commit calls per run (one per non-empty fix category); detect-secrets never commits; no empty-diff commits; no double-commit per category.

### EVAL-E08
`requires_human_review` initialised at [TRIAGE] and appended to at each verify node and [SURFACE-SECRETS]; [OPEN-PR] renders the full combined list.

### EVAL-E09
Missing/unparseable LintReport → wrong-tool redirect to `/test-lint` before any [TRIAGE] or fix node Position header is emitted.

### EVAL-E10
[SURFACE-SECRETS] segment contains zero edit/write/patch/commit tool calls — read-only.

### EVAL-E11
`templates/fix-report.md` loaded inside [OPEN-PR] before any rendered PR body or `gh pr create` call.

### EVAL-E12
With `--no-pr`: zero `gh` / GitHub API calls in the post-[VERIFY-VULTURE] trace; FIX_REPORT.md write present; clean exit to [END].
