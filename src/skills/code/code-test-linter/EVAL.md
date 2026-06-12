# EVAL — code-test-linter

Quality criteria + test prompts for the code-test-linter skill. Used by `/synapse-skill-improver` to grade structural and behavioral quality.

> **Skill:** [`SKILL.md`](SKILL.md)
> **Output schema:** `LintReport` (pydantic) — see [`templates/lint-report.md`](templates/lint-report.md)

---

## Test Prompts

### EVAL-T01 — Naive User: Basic scan request

**Prompt:** "run code-test-linter on my repo"

**Why this tests the skill:** Minimal invocation with no arguments — exercises default argument resolution (`--repo-root` falls back to cwd, `--output` falls back to the default path) and whether the skill confirms tool inventory and proceeds without prompting the user for missing context.

---

### EVAL-T02 — Naive User: Clean repo, vague reassurance request

**Prompt:** "can you check if my code is clean? it's a python project at /home/me/myapp"

**Why this tests the skill:** Exercises repo-root path parsing from informal prose, and whether the skill correctly reports a clean run (zero issues) with a human-readable summary rather than silently emitting an empty file.

---

### EVAL-T03 — Naive User: User conflates linting with fixing

**Prompt:** "lint my project and fix whatever you find"

**Why this tests the skill:** Tests wrong-tool detection — the user is asking for auto-fix behavior, which belongs to `/code-test-fixer`. The skill should surface the correct referral rather than attempting any modification.

---

### EVAL-T04 — Experienced User: Missing config files across multiple linters

**Prompt:** "/code-test-linter --repo-root /srv/pipeline -- mypy.ini and .bandit are not committed, but ruff.toml is. I want to see MISSING_CONFIG issues in the report for the absent files, and I still expect ruff to run normally. Don't skip the descriptive-test validator."

**Why this tests the skill:** Directly exercises the MISSING_CONFIG edge case — the skill must emit `LintIssue` entries with `code: "MISSING_CONFIG"` for absent config files, attempt to run the affected linters with defaults, and not abort or silently skip the docstring validator.

---

### EVAL-T05 — Experienced User: Repo with descriptive-test violations

**Prompt:** "/code-test-linter --repo-root /app/ragweave -- several test files have partial docstrings: some have @tests and @scenario but are missing @layer and @asserts. I need each missing tag to emit its own LintIssue, not be collapsed. Make sure the descriptive_test_violations list in the report is populated separately."

**Why this tests the skill:** Tests the per-tag granularity requirement — each missing tag must produce its own `LintIssue` (e.g., `MISSING_LAYER_TAG`, `MISSING_ASSERTS_TAG`), and the `descriptive_test_violations` list must be a distinct named subset in the `LintReport`, not just folded into the main `issues` list.

---

### EVAL-T06 — Experienced User: Pre-existing `.secrets.baseline` with new secrets

**Prompt:** "/code-test-linter --repo-root /srv/ingest — we have a committed .secrets.baseline that covers some old AWS keys from a rotated credential. There's a new hardcoded token in src/loader.py that isn't in the baseline yet. I only want new secrets reported, not baseline-covered ones. Surface the baseline path in the report metadata."

**Why this tests the skill:** Exercises the `detect-secrets` baseline-aware behavior — the skill must honor `.secrets.baseline`, suppress already-baselined findings, report only new secrets, and include the baseline file path in report metadata for downstream consumers.

---

### EVAL-T07 — Experienced User: Linter timeout scenario

**Prompt:** "/code-test-linter --repo-root /monorepo/data-platform — this repo has ~15,000 Python files. mypy has been timing out in CI. I want the report to continue with the remaining linters even if mypy times out, and I want a TIMEOUT LintIssue emitted for it rather than a crash."

**Why this tests the skill:** Exercises the per-linter timeout policy — the skill must emit a `LintIssue` with `code: "TIMEOUT"` for the timed-out linter, continue running ruff, bandit, vulture, detect-secrets, and the docstring validator, and produce a complete report rather than aborting.

---

### EVAL-T08 — Experienced User: Linter config error (exit code 2)

**Prompt:** "/code-test-linter --repo-root /app/service -- ruff.toml has a syntax error I haven't fixed yet (bad rule name under [lint.select]). I want a CONFIG_ERROR issue for ruff in the report, and I still want mypy, bandit, vulture, and the docstring validator to run."

**Why this tests the skill:** Exercises exit-code 2 handling — configuration errors must not abort the entire run. The skill must emit a `LintIssue` with `code: "CONFIG_ERROR"` containing the stderr output for ruff, then continue all remaining linters to completion.

---

### EVAL-T09 — Adversarial: Compound request spanning lint + fix + coverage audit

**Prompt:** "run code-test-linter on /srv/myapp, then fix all the ruff errors, then audit test coverage gaps, then write new tests for any gaps it finds"

**Why this tests the skill:** Tests that the skill scopes strictly to its lane — it must produce the `LintReport` and then stop, suggesting `/code-test-fixer` for the fix phase, not chain into fixing, auditing, or generation. The skill must not conflate lint with downstream pipeline stages.

---

### EVAL-T10 — Adversarial: Empty repo with no Python files

**Prompt:** "/code-test-linter --repo-root /tmp/new-project -- I just initialized this repo, there are no Python files yet, no config files, nothing. What does the report look like?"

**Why this tests the skill:** Edge case — an empty manifest means no files to scan, no linters to invoke meaningfully, and no test files for the docstring validator. The skill must still emit a valid `LintReport` (with `files_scanned: 0`, empty `issues` list) and not crash or hang.

---

### EVAL-T11 — Wrong Tool: User wants a coverage gap audit, not a lint pass

**Prompt:** "I want to know which parts of my codebase have no tests. can code-test-linter tell me that?"

**Why this tests the skill:** Near-miss wrong-tool case — coverage gap auditing is the domain of `/code-test-auditor`, not `code-test-linter`. The skill should recognize it is not the right tool for structural test coverage analysis and redirect clearly, even though the request uses testing-adjacent language.

---

### EVAL-T12 — Wrong Tool: User wants lint findings summarized in prose

**Prompt:** "here's the LINT_REPORT.json from a previous run — can you read it and give me a plain-English summary of the biggest problems?"

**Why this tests the skill:** Tests that the skill does not act as a report-reader or prose summarizer. Consuming and interpreting an existing `LintReport` is downstream work (closer to a `code-test-fixer` or reporting skill). The skill's job is to produce a fresh report, not to re-analyze one — it should clarify scope and redirect appropriately.

---

## Output Criteria (EVAL-Oxx)

Binary pass/fail criteria for evaluating the `LintReport` produced by a skill run.

- [ ] **EVAL-O01:** LintReport is valid JSON with all required pydantic fields present
  - **Test:** Parse the output file as JSON. Verify the top-level object contains exactly the four required keys: `issues` (array), `files_scanned` (integer), `duration_ms` (integer), and `descriptive_test_violations` (array). Verify each element of `issues` and `descriptive_test_violations` contains the six `LintIssue` keys: `tool`, `file`, `line`, `code`, `message`, `severity`.
  - **Fail signal:** JSON parse error, missing top-level key, or any `LintIssue` object missing one of the six required fields.

- [ ] **EVAL-O02:** `tool` field in every `LintIssue` uses only allowed Literal values per the template's tool table
  - **Test:** Collect every distinct `tool` value across all entries in `issues` and `descriptive_test_violations`. Verify each value is one of: `"ruff"`, `"mypy"`, `"bandit"`, `"vulture"`, `"detect-secrets"`, `"descriptive-test"`, `"lint-skill"`.
  - **Fail signal:** A `tool` value appears that is not in the allowed set.

- [ ] **EVAL-O03:** `severity` is correctly normalized per per-tool rules
  - **Test:** Cross-reference `tool` + source metadata against the Severity Assignment Recipe in `templates/lint-report.md`. Spot-check: bandit HIGH → `"error"`, MEDIUM → `"warning"`, LOW → `"info"`; mypy error → `"error"`, note → `"info"`; vulture 100% → `"warning"`, 80–99% → `"info"`; `detect-secrets` new secret → `"error"`; `descriptive-test` → `"warning"`; `lint-skill` CONFIG_ERROR → `"error"`, MISSING_CONFIG → `"warning"`.
  - **Fail signal:** Any `LintIssue` whose `severity` contradicts the per-tool normalization table.

- [ ] **EVAL-O04:** No source, test, or lint config files were modified during the run
  - **Test:** Record checksums of all `.py`, `ruff.toml`, `mypy.ini`, `pyproject.toml`, and `.bandit` files before skill execution. Re-record after. Compare — every file must have an identical checksum.
  - **Fail signal:** Any source, test, or config file has a different checksum post-run, or a new non-output file exists.

- [ ] **EVAL-O05:** No `# noqa`, `# type: ignore`, or `# nosec` directives were added to any source file
  - **Test:** `grep -rn '# noqa\|# type: ignore\|# nosec\|# pylint: disable'` on the repo before and after. The set of matching lines must be identical.
  - **Fail signal:** Any suppression directive present after the run that was not present before.

- [ ] **EVAL-O06:** All linter findings are present in `issues` — no silent deduplication or filtering
  - **Test:** Run each linter independently on the same repo root. Compare each tool's raw count against the count of `LintIssue` entries in `issues` where `tool` equals that linter's name. Counts must match exactly.
  - **Fail signal:** Any tool's issue count in the report is lower than the tool's independently-measured raw count.

- [ ] **EVAL-O07:** One `LintIssue` is emitted per missing descriptive-test tag — no collapsing
  - **Test:** Identify a test function with two missing required tags (e.g., `@asserts` and `@layer`). Verify the report contains exactly two separate `LintIssue` entries for that function, each with a distinct `code` (`"MISSING_ASSERTS_TAG"` and `"MISSING_LAYER_TAG"`).
  - **Fail signal:** A single `LintIssue` covers multiple missing tags, or a merged code appears.

- [ ] **EVAL-O08:** `descriptive_test_violations` is a strict subset of `issues`
  - **Test:** For every `LintIssue` in `descriptive_test_violations`, verify an identical object appears in `issues`. Verify no entry in `descriptive_test_violations` is absent from `issues`, and all entries have `tool: "descriptive-test"`.
  - **Fail signal:** Any entry in `descriptive_test_violations` has no matching entry in `issues`, or contains entries with a different `tool` value.

- [ ] **EVAL-O09:** Linter exit-code 2 produces `CONFIG_ERROR` rather than skill abort
  - **Test:** Simulate a run where one linter exits code 2. Verify (a) a `LintIssue` with `code: "CONFIG_ERROR"`, `severity: "error"`, `tool: "lint-skill"` is in `issues`; (b) `message` contains stderr output; (c) findings from remaining linters still appear in `issues`.
  - **Fail signal:** No `CONFIG_ERROR` issue, findings from subsequent linters absent, or skill exit code non-zero.

- [ ] **EVAL-O10:** Skill exits non-zero only on linter execution failure, not on findings
  - **Test:** Run against a repo with findings (linter exit 1). Skill exit code must be 0. Run with a missing linter binary; skill exit must be non-zero.
  - **Fail signal:** Skill exits non-zero when findings exist but linters ran successfully, or zero when a binary was missing.

- [ ] **EVAL-O11:** `.secrets.baseline` is respected — only new secrets reported, baseline path surfaced
  - **Test:** With a committed `.secrets.baseline`, verify (a) no `detect-secrets` issue references a baselined secret; (b) every `detect-secrets` issue's `message` contains the absolute path to `.secrets.baseline`.
  - **Fail signal:** A baselined secret appears, or the baseline path is missing from `message`.

- [ ] **EVAL-O12:** Schema imported from `src/tools/testing/code-test-report-lint/schemas.py` (and `src/tools/testing/code-test-scan-secrets/schemas.py` for secret findings), not redeclared
  - **Test:** Search all files generated/modified for class definitions named `LintIssue` or `LintReport`. None should exist outside the canonical schema files. Schemas must be loaded from `src/tools/testing/code-test-report-lint/schemas.py` (and `src/tools/testing/code-test-scan-secrets/schemas.py` where applicable) via file-path import — hyphenated tool dirs are not dotted-importable.
  - **Fail signal:** A local class definition exists, or imports resolve elsewhere.

- [ ] **EVAL-O13:** A test function with no docstring emits exactly one `MISSING_DOCSTRING` issue
  - **Test:** For a test function with no docstring at all, verify exactly one `LintIssue` with `code: "MISSING_DOCSTRING"` — and no per-tag issues for the same function.
  - **Fail signal:** Multiple issues are emitted for a no-docstring function, or per-tag codes appear instead.

- [ ] **EVAL-O14:** `files_scanned` equals unique Python files in manifest, not files-with-findings
  - **Test:** Count `.py` files in the repo (excluding ignored). Compare against `files_scanned`. Values must match.
  - **Fail signal:** `files_scanned` equals files-with-findings count, or is 0 when the repo has Python files.

- [ ] **EVAL-O15:** Linter timeout emits `TIMEOUT` issue and does not abort remaining linters
  - **Test:** Trigger a linter timeout. Verify (a) `LintIssue` with `code: "TIMEOUT"`, `tool: "lint-skill"`, `severity: "error"`; (b) findings from later linters still present.
  - **Fail signal:** No `TIMEOUT` issue, subsequent linter findings absent, or skill exits non-zero.

---

## Execution Criteria (EVAL-Exx)

Graded against the agent's execution trace, not the final output.

- [ ] **EVAL-E01:** `rules/lint-constraints.md` loaded at every node, not only at entry
  - **Test:** Observe a `Load: rules/lint-constraints.md` action immediately before each of [SCAN], [RUN-EACH-LINTER], [AGGREGATE], [EMIT-REPORT].
  - **Fail signal:** Loaded once at [NEW]/[SCAN] but no reload before later nodes.

- [ ] **EVAL-E02:** All five reference files loaded at [RUN-EACH-LINTER]
  - **Test:** At [RUN-EACH-LINTER], the trace shows Read calls for `references/ruff-config.md`, `references/mypy-strict.md`, `references/bandit-rules.md`, `references/vulture-thresholds.md`, `references/descriptive-test-rules.md`.
  - **Fail signal:** Fewer than five reference files loaded, or any reference loaded at a different node.

- [ ] **EVAL-E03:** Tool inventory verified at [NEW] before any linter is invoked
  - **Test:** [NEW] shows existence checks for `src/tools/testing/code-test-report-lint` and `src/tools/testing/code-test-scan-secrets` (invoked as `python src/tools/testing/code-test-report-lint/lint_reporter.py` / `python src/tools/testing/code-test-scan-secrets/secret_scanner.py`) preceding any linter invocation.
  - **Fail signal:** Skill proceeds with no tool-inventory check, or check occurs after first linter call.

- [ ] **EVAL-E04:** `schemas.py` verified at [NEW]; schema imported from canonical path at [AGGREGATE]
  - **Test:** [NEW] verifies `src/tools/testing/code-test-report-lint/schemas.py` exports `LintIssue`/`LintReport`. [AGGREGATE] loads them from that file (and `src/tools/testing/code-test-scan-secrets/schemas.py` for secret findings) via file-path import. No local class definitions.
  - **Fail signal:** Local class defined, or no canonical-path import.

- [ ] **EVAL-E05:** All four nodes visited in declared order
  - **Test:** `Position:` markers appear in sequence [SCAN] → [RUN-EACH-LINTER] → [AGGREGATE] → [EMIT-REPORT] → [END].
  - **Fail signal:** Node missing, out of sequence, or [EMIT-REPORT] before [AGGREGATE].

- [ ] **EVAL-E06:** Linters invoked sequentially, not in parallel
  - **Test:** The trace shows linter invocations one at a time in declared order. No parallel dispatch block.
  - **Fail signal:** Two or more linters in the same parallel tool-call block.

- [ ] **EVAL-E07:** CONFIG_ERROR and TIMEOUT handled per policy
  - **Test:** After a code-2 exit or timeout: (a) issue is recorded with correct code/severity; (b) subsequent linter still invoked.
  - **Fail signal:** Subsequent linter not invoked, issue absent, or exception propagates.

- [ ] **EVAL-E08:** No Edit or Write tool calls targeting source/test/config files
  - **Test:** Every Edit/Write call resolves to the `--output` LintReport path or parent directory creation. No `.py`, `.toml`, `.ini`, `.cfg`, `.yaml` project file is touched.
  - **Fail signal:** Any non-output project file modified.

- [ ] **EVAL-E09:** `Position:` marker recorded at each node transition
  - **Test:** At minimum four `Position:` lines naming `[SCAN]`, `[RUN-EACH-LINTER]`, `[AGGREGATE]`, `[EMIT-REPORT]`, each preceding the node's work.
  - **Fail signal:** Fewer than four markers, or non-canonical labels.

- [ ] **EVAL-E10:** `LintReport` written to declared output path with parent dir creation
  - **Test:** Trace shows JSON serialization to default path (or `--output`). Write preceded by `mkdir -p` or equivalent.
  - **Fail signal:** Different path used, no parent-dir step, or no Write call.

- [ ] **EVAL-E11:** Descriptive-test violations emitted as individual `LintIssue` entries per missing tag
  - **Test:** Function missing two tags emits two distinct issues with distinct codes. No-docstring function emits exactly one `MISSING_DOCSTRING`.
  - **Fail signal:** Tags merged, or no-docstring function emits per-tag codes.

- [ ] **EVAL-E12:** `detect-secrets` baseline respected; baseline path in issue messages
  - **Test:** With `.secrets.baseline`, scanner invoked with baseline-aware flags; emitted issues include the resolved absolute path in `message`. No baselined secret reported.
  - **Fail signal:** No baseline check, baselined secret reported, or baseline path missing from messages.
