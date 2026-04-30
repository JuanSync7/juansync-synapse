# fix-constraints.md

Hard invariants for every fix and verify node. Load at every node that touches source files or commits.
No exceptions. No overrides.

---

## 1. Category Sequencing

Execute in this order, always: ruff → mypy → bandit → vulture → detect-secrets.
Never reorder. Never run two categories concurrently.
Rationale: each category may surface issues the previous one masked; ordering is deterministic and auditable.

---

## 2. Mandatory Re-verification

After every fix node, invoke `lint_reporter` scoped to that category before committing or advancing.
A fix node that skips verification has not completed.

---

## 3. Suppression Policy

`# noqa`, `# type: ignore[...]`, and `# nosec` are permitted only when the explicit reason is recorded in the commit-message body.
Bare suppressions (`# noqa`, `# type: ignore`, `# nosec` with no argument or no commit-body entry) are FORBIDDEN.
Rationale: suppressions without rationale become permanent technical debt with no audit trail.

---

## 4. Bandit: Refactor Only

NEVER delete a bandit-flagged security check. Refactor the underlying code to eliminate the risk.
If the remediation requires architectural change (subprocess, pickle, or eval in a core module), append to `requires_human_review` with note "bandit architectural escalation" and advance — do not block the pipeline.
Rationale: removing a check silences the warning without removing the risk.

---

## 5. Vulture: Deletion Criteria

Delete a dead-code symbol only when ALL of the following hold:
- vulture confidence >= 90%
- symbol is NOT in `__all__`
- symbol is NOT decorated (plugin entry point, API endpoint, pytest fixture, etc.)
- symbol has no external importers

Any finding that fails one or more criteria → append to `requires_human_review` with note "vulture public-api" or "vulture low-confidence". Do not lower the threshold.

---

## 6. detect-secrets: Always Escalate

NEVER auto-resolve a detect-secrets finding.
NEVER delete the secret string from source.
NEVER rewrite history to remove the finding.
Every finding → append to `requires_human_review` with: which credential, file and line, recommended rotation steps.
Rationale: secret rotation is an out-of-band human action; automation must not touch live credentials.

---

## 7. Re-verification Residuals

When re-verification finds issues that were not present before the fix node ran, do NOT loop back to re-fix.
Append to `requires_human_review` with note "introduced during fix phase". Advance to the next category.
Rationale: re-fix loops can diverge; residuals introduced by fixes are a human judgment call.

---

## 8. Commit Granularity

One commit per category. Commit only after re-verification passes.
Do not commit if the diff is empty.
Commit message format: `fix(lint): <category>` with suppression reasons in the body when applicable.

---

## 9. Schema Canonical Source

Import `LintIssue` and `LintReport` exclusively from `ai-synapse/tools/testing/schemas.py`.
Do not redeclare these types in fix nodes, verify nodes, or helper modules.
Rationale: a single definition prevents silent schema drift across the pipeline.

---

## 10. PR Soft Gate

The PR opened at [OPEN-PR] is non-blocking. The engine does not wait for review approval.
Apply the `requires-human-review` GitHub label when the list is non-empty. Do not mark the PR as blocking. Do not auto-merge.
Rationale: human-review items are surfaced for visibility, not as a pipeline blocker.
