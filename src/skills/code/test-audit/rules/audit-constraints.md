# audit-constraints

Read-only invariants. Apply at every node without exception.

---

## File Modification

- MUST NOT edit, create, or delete any file under the project source tree — this includes `*.py`, `pyproject.toml`, `requirements*.txt`, `tests/**`, lint configs, and coverage configs.
- MUST NOT modify any project state file other than the explicit audit history target (`project/coverage/state/AUDIT_HISTORY/<timestamp>.yaml`) and `COVERAGE_STATE.yaml` (initial snapshot on first run only).
- MUST use Read for all file inspection; MUST use Write only for the audit history target.

---

## Scope Discipline

- MUST NOT execute mutation testing inline — mutation testing is `test-generate`'s per-gap responsibility.
- MUST NOT delete, rewrite, quarantine, or auto-fix any flagged test — audit emits reports only.
- MUST treat all 9 tool outputs as required merge inputs to `AuditGapReport`; none may be omitted from [CONSOLIDATE].

---

## Error Handling

- MUST emit a sentinel/empty result and note the absence in `AuditGapReport` if a tool's input file is missing (e.g., `FLAKE_HISTORY.csv` → `flakiness_scores: {}`; `LOG_POLICY.yaml` → skip log-contract node with warning) — MUST NOT abort the pipeline silently.
- MUST honor the `--max-edges` cap during edge analysis; report uncapped edges as `unanalyzed` in `EdgeCoverageGaps` rather than skipping them.

---

## Preconditions

- MUST require a lint-clean precondition before proceeding past [NEW] — lint passes or all `LintReport.issues` are flagged `requires-human-review`; otherwise abort and direct the user to run `/test-fix` first.
- MUST NOT re-run lint inline to satisfy the precondition.
