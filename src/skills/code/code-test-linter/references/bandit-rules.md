# Bandit Security Rules Reference

Loaded at [RUN-EACH-LINTER]. Covers bandit's scope, severity mapping, invocation, config, and suppression handling for the code-test-linter skill.

---

## Bandit's Scope

Bandit performs AST-level static analysis to catch security anti-patterns in Python source. It does not execute code — it pattern-matches the parse tree. Main test groups:

| Group | Range | Focus area |
|-------|-------|------------|
| B1xx | B101–B113 | Assert statements, exec, hardcoded bind-all, request-related issues |
| B2xx | B201–B202 | Flask debug mode, Jinja2 autoescape |
| B3xx | B301–B325 | Deserialization (pickle, marshal, yaml), weak hash (md5, sha1), weak cipher (DES, RC4) |
| B4xx | B401–B415 | Insecure imports (telnetlib, ftplib), weak random, deprecated SSL |
| B5xx | B501–B510 | SSL/TLS context misuse, certificate verification disabled, weak protocol versions |
| B6xx | B601–B612 | Shell injection (subprocess shell=True, os.system, paramiko) |
| B7xx | B701–B703 | Jinja2 template injection, Mako |

Key rules to know by name: B105/B106/B107 (hardcoded password string/argument/default), B201 (Flask debug=True), B301 (pickle.loads), B302 (marshal.loads), B303 (md5/sha1 for security use), B311 (random for security use), B324 (hashlib weak algorithm), B501 (SSL cert verify disabled), B506 (yaml.load without Loader), B602/B603/B607 (subprocess shell=True or partial path).

---

## Severity and Confidence

Bandit assigns two independent dimensions to each finding:

- **Severity**: LOW, MEDIUM, HIGH — how dangerous the pattern is if exploited.
- **Confidence**: LOW, MEDIUM, HIGH — how certain bandit is that this is actually the bad pattern.

**Mapping to `LintIssue.severity`:**

| Bandit severity | LintIssue.severity |
|-----------------|--------------------|
| HIGH            | `"error"`          |
| MEDIUM          | `"warning"`        |
| LOW             | `"info"`           |

Confidence is metadata, not a filter. Preserve it in `LintIssue.message` so code-test-fixer and human reviewers can weigh LOW-confidence findings appropriately. Example message format: `[B301] Use of pickle.loads (confidence: HIGH)`.

Do NOT use confidence to drop or downgrade findings. Surface all findings; humans decide.

---

## Invocation Flags

Standard invocation used by `lint_reporter`:

```
bandit -r <repo-root> -f json -ll
```

- `-r`: recursive scan
- `-f json`: machine-readable output for aggregation
- `-ll`: report issues at LOW severity and above (includes everything)

**Test directory exclusion:** The `--exclude tests/` flag is common because test files legitimately use `assert` (B101) and hardcoded fixture values. The skill does NOT add this flag automatically — it respects whatever the project's bandit config declares. If the project omits an exclusion, test-file findings are surfaced as normal.

---

## Config File Precedence

Bandit respects project-level configuration in two locations:

1. `.bandit` file at the repo root (INI-style `[bandit]` section)
2. `[tool.bandit]` table in `pyproject.toml`

When both exist, bandit uses `.bandit`. The skill relies entirely on whichever config the project declares — it does not inject or override settings. During [SCAN], the presence or absence of a bandit config is recorded; a missing config emits `LintIssue` with `code: "MISSING_CONFIG"`.

Common config keys: `skips` (list of test IDs to suppress globally), `exclude_dirs`, `tests` (allowlist of test IDs to run).

---

## `# nosec` Suppression Directive

`# nosec` appended to a line tells bandit to skip that line. Bandit handles suppression automatically — suppressed findings never appear in JSON output.

**Skill rules:**

- MUST NOT add new `# nosec` comments. This violates the read-only constraint.
- MUST NOT silently accept existing suppressions as invisible. For every Python file where a `# nosec` comment is detected, emit one `LintIssue`:
  - `severity`: `"info"`
  - `code`: `"NOSEC_PRESENT"`
  - `message`: include the file path and line number(s) of each `# nosec` occurrence
- This surfaces suppressions for code-test-fixer to review whether each is justified. Bandit still skips the suppressed line — the `NOSEC_PRESENT` issue is an audit flag only, not a re-surfaced security finding.

---

## Common False-Positive Patterns

Bandit surfaces all findings. The skill does not filter. These patterns are known to produce frequent false positives — document them so code-test-fixer and reviewers have context:

| Rule | Pattern | Why it's often benign |
|------|---------|----------------------|
| B101 | `assert` in test files | Normal pytest/unittest assertion; not an assert removal risk in production |
| B311 | `random.randint`, `random.choice` | Non-cryptographic randomness (shuffling, sampling, simulation) is fine; only a risk when used for secrets/tokens |
| B603 | `subprocess.run(["git", "status"])` | Hardcoded string list with no shell=True; no injection surface |
| B324 | `hashlib.md5(data)` | Acceptable for checksums/fingerprints; only a problem when used for password hashing or security tokens |
| B506 | `yaml.safe_load(...)` | B506 targets `yaml.load` without Loader; `safe_load` is the correct fix and should not appear as a finding |

Surface all findings as-is. If a finding is a false positive for the project, code-test-fixer or a human reviewer should add the rule to `skips` in the bandit config — not add `# nosec` inline, and not filter at aggregation time.
