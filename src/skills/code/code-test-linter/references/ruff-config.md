# Ruff Configuration Reference

Loaded at [RUN-EACH-LINTER]. Guides invocation and output normalization for ruff — the style, import-order, and simple-bug-pattern linter in this pipeline.

---

## Ruleset Selection

Enable at minimum these rule families. Each maps to a focused concern:

| Family | Prefix | What it catches |
|--------|--------|-----------------|
| pycodestyle errors | `E` | Indentation, whitespace, blank-line violations — PEP 8 structural errors |
| pyflakes | `F` | Undefined names, unused imports, redefined variables — runtime-breaking bugs |
| pycodestyle warnings | `W` | Line-length, whitespace warnings — style signals, not crashes |
| isort | `I` | Import ordering and grouping |
| flake8-bugbear | `B` | Common bug patterns: mutable default args, loop variable capture, bare `except` |
| pyupgrade | `UP` | Syntax that can be modernized for the target Python version |
| flake8-simplify | `SIM` | Redundant conditions, unnecessary `else`, collapsible branches |
| ruff-native | `RUF` | Ruff's own rules: ambiguous string joins, implicit optional, etc. |

These eight families cover the majority of actionable findings without noise. Additional families (`ANN`, `D`, `N`) should only be enabled if the project's config explicitly declares them — do not add rules beyond this baseline unless already present in the project's ruff config.

---

## Severity Normalization

Ruff emits a flat list of codes. Map each to `LintIssue.severity` using this decision tree:

```
F401, F811, F821, F841 (and all F8xx)  →  error
  (unused imports that shadow, undefined names, unreachable code)

E, W, I, B, RUF  →  warning
  (style violations, import order, bugbear patterns — annoying but not crash-inducing)

UP, SIM  →  info
  (modernization and simplification suggestions — safe to defer)
```

Rationale: F-family rules are pyflakes — they detect patterns that either break at runtime (`F821` undefined name) or produce silent correctness bugs (`F811` redefinition). Everything else is a quality signal, not a failure signal.

When in doubt about an unknown rule prefix, default to `warning`.

---

## Config File Precedence

Ruff resolves config in this order (first match wins):

1. `ruff.toml` in the project root — dedicated file, takes full precedence
2. `pyproject.toml` `[tool.ruff]` section — used when no `ruff.toml` exists
3. Ruff defaults — applied if neither config file is present

When both `ruff.toml` and `pyproject.toml [tool.ruff]` exist, ruff silently prefers `ruff.toml`. Always invoke ruff from the repo root so config resolution is deterministic. Do not pass `--config` unless the project explicitly uses a non-root config path.

---

## Recommended Invocation

```bash
ruff check --output-format=json --no-fix --quiet <repo_root>
```

Flag rationale:

- `--output-format=json` — structured output for reliable parsing; never parse prose output
- `--no-fix` — this skill is read-only; ruff must not modify files under any circumstances
- `--quiet` — suppresses progress bars and summary lines; only JSON goes to stdout
- `<repo_root>` — pass the resolved repo root, not `.`, to avoid CWD-dependent results

For large repos (>500 Python files), add `--jobs 4` to parallelize file processing. Do not exceed the machine's CPU count. Omit `--jobs` for small repos — the overhead is not worth it.

Exit codes: `0` = clean, `1` = findings present (normal), `2` = config or parse error. Treat exit code `2` as a `CONFIG_ERROR` `LintIssue` at severity `error`; capture stderr verbatim as the issue message.

---

## What Ruff Does NOT Cover

Ruff handles style, import order, and simple bug patterns. It does not replace:

- **Type errors** → mypy (`references/mypy-strict.md`)
- **Security vulnerabilities** → bandit (`references/bandit-rules.md`)
- **Dead code** → vulture (`references/vulture-thresholds.md`)
- **Hardcoded secrets** → detect-secrets / `secret_scanner` tool

Do not attempt to infer type safety or security posture from ruff output. Route those findings to the appropriate linter results at [AGGREGATE].

---

## Fixture and Test File Exclusions

Projects commonly declare `per-file-ignores` in their ruff config to relax rules for test files. Typical patterns:

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["E501", "F401"]
# E501: long lines are common in test fixtures and assertion chains
# F401: imports used only for fixture wiring appear "unused" to ruff
```

Policy: **respect what the project already declares — do not add or modify ignore patterns.** If a finding appears in output, it means the project's config did not suppress it and it is fair game for the LintReport. Only surface findings ruff actually emits; do not second-guess the config by filtering issues that "probably should be ignored."

If the project has no ruff config and you observe high E501 noise in test files, record it as a `LintIssue` with a note that `per-file-ignores` configuration is missing — let `code-test-fixer` decide whether to add it.
