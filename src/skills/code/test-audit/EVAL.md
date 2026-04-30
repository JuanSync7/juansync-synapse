# EVAL — `test-audit`

Evaluation specification for the `test-audit` skill. Three independent surfaces: blind test prompts (T), output quality criteria (O), execution criteria (E).

**Skill description:** Run a read-only diagnostic audit of test coverage health — produce AuditGapReport feeding generate/evaluate/integrate.

---

## Test Prompts (EVAL-Txx)

Generated blind (SKILL.md body not read by prompter). Covers 4 personas: Naive, Experienced, Adversarial, Wrong Tool.

### EVAL-T01 — Naive User: Vague coverage check
**Prompt:** "can you check how good our tests are"
**Expected:** should-trigger
**Why:** Exercises whether the skill resolves a minimal, context-free coverage request, clarifies scope, or proceeds with reasonable defaults.

### EVAL-T02 — Naive User: Single module, no detail
**Prompt:** "audit the tests for the ingest module"
**Expected:** should-trigger
**Why:** Tests scoping to a named subsystem and producing a structured AuditGapReport.

### EVAL-T03 — Naive User: Informal health check, no path context
**Prompt:** "something feels off with coverage lately, can you take a look and tell me what's missing"
**Expected:** should-trigger
**Why:** Verifies open-ended diagnostic interpretation, autonomous test-dir location, actionable findings.

### EVAL-T04 — Experienced: Targeted module + threshold
**Prompt:** "run a test coverage audit on `src/pipeline/` — I want to know which nodes are below 70% branch coverage, what critical paths are untested, and which tests are present but asserting nothing meaningful (stub tests). produce the AuditGapReport."
**Expected:** should-trigger
**Why:** Multi-dimensional criteria handled without oversimplification.

### EVAL-T05 — Experienced: Cross-subsystem integration focus
**Prompt:** "I need a coverage audit across both `src/retrieval/` and `src/ingest/` with emphasis on integration-boundary gaps — places where one subsystem calls into the other but there's no test covering that call path. flag any missing contract tests too."
**Expected:** should-trigger
**Why:** Cross-module integration gap reasoning, unit vs contract distinction.

### EVAL-T06 — Experienced: Unusual domain (ML eval harness)
**Prompt:** "audit test coverage for our LLM evaluation harness in `tests/eval_harness/`. we care about: metric computation functions, prompt rendering edge cases, and the async batch runner. distinguish between coverage holes that are untested-by-design vs actual gaps."
**Expected:** should-trigger
**Why:** Unusual domain handling; intentional vs unintentional gap distinction.

### EVAL-T07 — Adversarial: Scope explosion
**Prompt:** "audit test coverage for the entire codebase — every module, every layer, every integration point. give me a complete gap analysis for everything in `src/` and `tests/` and map every missing test back to a requirement from the spec. do it all in one pass."
**Expected:** should-redirect
**Why:** Recognizes scope explosion, proposes scoped sub-audits.

### EVAL-T08 — Adversarial: Contradictory constraints
**Prompt:** "give me a full coverage audit but don't read any test files — just look at the source code and infer what tests probably exist"
**Expected:** should-redirect
**Why:** Recognizes contradictory constraint, declines or requests clarification.

### EVAL-T09 — Wrong Tool: Test generation request
**Prompt:** "we have gaps in coverage for the auth module — can you write the missing tests?"
**Expected:** should-redirect (to `/test-generate` or `/write-module-tests`)
**Why:** Adjacent task (generation) misidentified as audit.

### EVAL-T10 — Wrong Tool: Report formatting request
**Prompt:** "I've already got the pytest-cov HTML report — can you summarize it and make it presentable for the team?"
**Expected:** should-redirect (to a doc/summary skill)
**Why:** Existing-artifact summarization, not a fresh audit.

---

## Output Criteria (EVAL-Oxx)

Binary pass/fail criteria for the `AuditGapReport` and history artifacts produced by a run.

- [ ] **EVAL-O01:** All 9 tool output fields present in the report
  - **Test:** Inspect `AuditGapReport`. Verify all nine fields exist: `gaps`, `priority_ranking`, `gaming_alerts`, `flakiness_scores`, `dep_vulnerabilities`, `edge_coverage_gaps`, `log_contract_violations`, `audit_timestamp`, `project_sha`. No-data fields appear with declared empty default (`[]`, `{}`, sentinel object).
  - **Fail:** A field is absent, or a no-data field is `null`/`None`.

- [ ] **EVAL-O02:** `audit_timestamp` is timezone-aware UTC
  - **Test:** Parse value; confirm `+00:00` or `Z` suffix; confirm not produced by naive `datetime.utcnow()`.
  - **Fail:** Naive datetime, or non-UTC offset.

- [ ] **EVAL-O03:** `project_sha` is full 40-character hex
  - **Test:** `len(value) == 40` and all chars in `[0-9a-fA-F]`.
  - **Fail:** Short SHA, empty, or non-hex chars.

- [ ] **EVAL-O04:** Every `CoverageGap` carries a pyramid layer tag
  - **Test:** Each `gaps[i].layer` ∈ {`unit`, `config`, `contract`, `idempotency`, `mock-integration`, `real-integration`}.
  - **Fail:** Missing or out-of-set layer value.

- [ ] **EVAL-O05:** `priority_ranking` uses 2-factor formula only
  - **Test:** Sample tier assignments; verify critical = `recently_changed AND (public_api OR bug_history > 0)`. No rationale references complexity, fan-in, or weighted coefficients.
  - **Fail:** Critical tier without satisfying both factors, or 4-factor artifacts in rationale.

- [ ] **EVAL-O06:** `gaming_alerts` reference only the 7 named AST patterns
  - **Test:** Every `pattern` value ∈ {`pragma-no-cover-abuse`, `assert-true-padding`, `no-assertions`, `mock-sut`, `copy-paste-test`, `private-attribute-assertion`, `self-referential-helper`}.
  - **Fail:** Novel category name.

- [ ] **EVAL-O07:** Flakiness uses 2% threshold and suppresses low-confidence pairs
  - **Test:** Every `(test_id, sha)` with `total_runs < 3` absent from `flakiness_scores`; included pairs have `fail_rate > 0.02`.
  - **Fail:** Low-confidence pair included, or pair with `fail_rate ≤ 0.02` flagged.

- [ ] **EVAL-O08:** Edge coverage report has both `uncovered` and `unanalyzed` when `--max-edges` fires
  - **Test:** When cap fires, both lists present and non-null; every excluded edge appears in exactly one list.
  - **Fail:** `unanalyzed` absent/empty when cap triggered, or edges silently dropped.

- [ ] **EVAL-O09:** `AUDIT_HISTORY/<timestamp>.yaml` written, never overwrites existing entries
  - **Test:** New file under `project/coverage/state/AUDIT_HISTORY/` with stem matching `audit_timestamp` (`YYYYMMDDTHHMMSSZ`); no pre-existing file modified in place.
  - **Fail:** No new file, mismatched stem, or existing file overwritten.

- [ ] **EVAL-O10:** `COVERAGE_STATE.yaml` written only on first run
  - **Test:** When file exists pre-run, mtime + content unchanged post-run. When absent, file created with `initialized_at`, `project_sha`, `coverage_targets`, `gap_state.open` populated.
  - **Fail:** Overwritten or modified on a non-first run.

- [ ] **EVAL-O11:** No source/test files modified during run (read-only invariant)
  - **Test:** Hash all `*.py`, `pyproject.toml`, `requirements*.txt`, `tests/**` pre-run and post-run. Only permitted changes: new `AUDIT_HISTORY/<timestamp>.yaml`, new `COVERAGE_STATE.yaml` (first run only), updated `EDGE_COVERAGE.yaml`.
  - **Fail:** Any source/test/config hash changed.

- [ ] **EVAL-O12:** Lint-clean precondition checked before any tool executes
  - **Test:** Inject deliberate lint failure; invoke audit. Run aborts at [NEW] with directive to run `/test-fix`; no tool output, no `AUDIT_HISTORY` entry.
  - **Fail:** Skill proceeds past precondition with unflagged lint failure.

- [ ] **EVAL-O13:** Missing optional inputs produce sentinel, not abort
  - **Test:** Remove `FLAKE_HISTORY.csv` and `LOG_POLICY.yaml`. Verify `flakiness_scores: {}`, `log_contract_violations: []`, both absences noted in report. Run completes, history written.
  - **Fail:** Run aborts, field omitted, or set to `null`.

- [ ] **EVAL-O14:** Each `CoverageGap` has all three composite annotations
  - **Test:** Every gap carries `layer` ([SNAPSHOT]), `impact` ∈ {`unaffected`, `valid`, `weak`} ([IMPACT]), and assertion strength score ([ASSERTION-QUALITY]). Missing annotations explicitly noted.
  - **Fail:** Missing annotation silently defaulted to `null`.

---

## Execution Criteria (EVAL-Exx)

Binary criteria graded against the execution trace.

- [ ] **EVAL-E01:** All 11 nodes execute in declared order, no skips
  - **Test:** Trace shows `[NEW] → [SNAPSHOT] → [SCORE] → [IMPACT] → [GAMING] → [FLAKINESS] → [DEP-VULN] → [EDGE-COV] → [LOG-CONTRACT] → [ASSERTION-QUALITY] → [CONSOLIDATE] → [WRITE-HISTORY] → [END]`.
  - **Fail:** Node absent, out of sequence, or halt before [END] without precondition failure.

- [ ] **EVAL-E02:** `Position: [node-id]` recorded each turn
  - **Test:** Every node output opens with matching `Position:` line.
  - **Fail:** Missing or mismatched position header.

- [ ] **EVAL-E03:** `rules/audit-constraints.md` loaded at every node
  - **Test:** Each of the 11 nodes references the constraints file (load or acknowledgment).
  - **Fail:** Constraints loaded only at [NEW] or once for the whole run.

- [ ] **EVAL-E04:** Per-node `Load:` references respected
  - **Test:** [SNAPSHOT]→`coverage-analysis.md`; [SCORE]→`critical-scoring.md`; [GAMING]→`gaming-patterns.md`; [FLAKINESS]→`flakiness-detection.md`; [DEP-VULN]→`dep-vulnerability.md`; [EDGE-COV]→`edge-coverage-analysis.md`; [CONSOLIDATE]→`audit-report.md`+`coverage-pyramid.md`; [WRITE-HISTORY]→`coverage-state-schema.md`.
  - **Fail:** Reference loaded at wrong node or not loaded.

- [ ] **EVAL-E05:** Lint-clean precondition gate at [NEW]
  - **Test:** [NEW] checks lint pass; failed lint aborts before [SNAPSHOT].
  - **Fail:** [SNAPSHOT] begins without lint check, or audit continues past failed lint.

- [ ] **EVAL-E06:** All 9 tools invoked from `ai-synapse/tools/testing/`
  - **Test:** All 9 tool invocations recorded; inventory check at [NEW].
  - **Fail:** Tool absent, wrong path, or inventory check skipped.

- [ ] **EVAL-E07:** Missing `FLAKE_HISTORY.csv` → sentinel + note
  - **Test:** [FLAKINESS] emits `flakiness_scores: {}` + note; continues to [DEP-VULN].
  - **Fail:** Audit aborts, file populated, or absence not noted.

- [ ] **EVAL-E08:** Missing `LOG_POLICY.yaml` → clean skip + warn
  - **Test:** [LOG-CONTRACT] emits warning, skips cleanly; continues to [ASSERTION-QUALITY]; no write to LOG_POLICY.
  - **Fail:** Audit aborts, file written, or warning omitted.

- [ ] **EVAL-E09:** No mutation testing inline
  - **Test:** Trace contains no `mutmut`/`cosmic-ray`/`mutation_tester` invocations.
  - **Fail:** Mutation tool invoked at any node.

- [ ] **EVAL-E10:** No test file delete/quarantine/rewrite
  - **Test:** No write/delete/rename targeting test files. [GAMING] flags only; [ASSERTION-QUALITY] scores only.
  - **Fail:** Test file modified or quarantined.

- [ ] **EVAL-E11:** [CONSOLIDATE] merges all 9 tool outputs
  - **Test:** `AuditGapReport` contains all 9 fields; sentinel outputs included, not dropped.
  - **Fail:** Field missing or sentinel silently dropped.

- [ ] **EVAL-E12:** [END] does not auto-route to `/test-generate`
  - **Test:** Summary + suggestion present; no autonomous dispatch of `/test-generate`.
  - **Fail:** `/test-generate` invoked or test-writing action initiated.
