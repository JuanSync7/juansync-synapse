# Example Rollups

Three worked rollups — one per verdict. These are the format the skill MUST emit. Copy the shape exactly; do not invent variations.

---

## Example 1 — APPROVE (clean suite, no escalation)

**Invocation:** `/synapse-router-suite-validator external/jira-tools`

**Expected output:**

```
SUITE: APPROVE (path: external/jira-tools)

## Suite Conformance Report

Total artifacts: 5
Pass (structural): 5
Fail (structural): 0
Unreadable: 0
Cross-suite issues: 0

### Per-artifact results
- [PASS] skill/jira-reporter
- [PASS] skill/jira-planner
- [PASS] agent/jira-ticket-summarizer
- [PASS] protocol/jira-handoff
- [PASS] pathway/jira-end-to-end

### Recommendation
No blockers. The suite is structurally conformant and contains no name collisions or taxonomy drift against the ai-synapse main tree. Wire the submodule pointer and merge. For full quality certification before promotion, rerun with `--escalate`.
```

Note: Cross-suite issues section and Quality section are both omitted — silent success.

---

## Example 2 — REVISE (fixable structural + cross-suite issues)

**Invocation:** `/synapse-router-suite-validator external/devops-suite`

**Expected output:**

```
SUITE: REVISE (path: external/devops-suite)

## Suite Conformance Report

Total artifacts: 7
Pass (structural): 4
Fail (structural): 2
Unreadable: 1
Cross-suite issues: 3

### Per-artifact results
- [PASS] skill/deploy-checker
- [PASS] skill/log-tailer
- [PASS] agent/deploy-eval-judge
- [PASS] tool/repo-stats
- [FAIL] skill/code-formatter — missing EVAL.md alongside SKILL.md
- [FAIL] agent/incident-mediator — taxonomy: role=`mediator` not in AGENT_TAXONOMY.md
- [UNREADABLE] protocol/legacy.md — frontmatter parse error (unterminated YAML)

### Cross-suite issues
- Name collision: skill `code-formatter` already exists in registry/SKILL_REGISTRY.md (synapse/skills/code/code-formatter). Rename to avoid shadowing.
- Taxonomy drift: 2 skills declare `domain: automation`, which is not in SKILL_TAXONOMY.md. Either rename to an existing domain or propose a taxonomy addition.
- Domain README missing row: agents/devops/README.md does not list `deploy-eval-judge`.

### Recommendation
Three classes of work block promotion: (1) fix structural failures on `code-formatter` (add EVAL.md) and `incident-mediator` (use a valid `role`), (2) repair the unparseable `legacy.md` frontmatter, (3) resolve the cross-suite issues — rename `code-formatter`, decide on the `automation` domain, and patch the missing README row. After fixes, rerun the validator. No `--escalate` was passed; once structurally clean, rerun with `--escalate` for full quality certification.
```

---

## Example 3 — REJECT (fundamental: empty suite)

**Invocation:** `/synapse-router-suite-validator external/half-baked-suite`

**Expected output:**

```
SUITE: REJECT (path: external/half-baked-suite)

## Suite Conformance Report

No recognizable artifacts found. A suite must contain at least one of: skills/, agents/, protocols/, tools/, pathways/.

### Recommendation
Either this directory was added to `external/` prematurely (no artifacts authored yet) or its layout does not match ai-synapse conventions. Author at least one artifact under one of the recognized top-level directories, or remove the submodule pointer. There is nothing for the validator to sweep.
```

Note: When the suite is rejected at discovery, all intermediate sections collapse — only the Recommendation matters.

---

## Example 4 — APPROVE with --escalate (full pipeline)

**Invocation:** `/synapse-router-suite-validator external/jira-tools --escalate`

**Expected output:**

```
SUITE: REVISE (path: external/jira-tools)

## Suite Conformance Report

Total artifacts: 5
Pass (structural): 5
Fail (structural): 0
Unreadable: 0
Cross-suite issues: 0

### Per-artifact results
- [PASS] skill/jira-reporter
- [PASS] skill/jira-planner
- [PASS] agent/jira-ticket-summarizer
- [PASS] protocol/jira-handoff
- [PASS] pathway/jira-end-to-end

### Quality (escalated)
- skill/jira-reporter — APPROVE
- skill/jira-planner — REVISE (no --score; quality tier unverified)
- agent/jira-ticket-summarizer — APPROVE
- protocol/jira-handoff — APPROVE
- pathway/jira-end-to-end — APPROVE

### Recommendation
Structurally clean and free of cross-suite issues, but escalated quality review surfaces one gap: `jira-planner` has no measured eval score, so `/synapse-router-artifact-gatekeeper` capped its verdict at REVISE. Run `/synapse-skill-skill-improver external/jira-tools/skills/jira/jira-planner` to obtain a score, then rerun the validator with `--escalate` to confirm full APPROVE.
```

Note: A single escalated REVISE downgrades the suite verdict from APPROVE to REVISE — weakest-link semantics.
