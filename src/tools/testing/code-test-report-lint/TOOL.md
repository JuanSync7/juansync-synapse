---
name: code-test-report-lint
description: Aggregates ruff, mypy, bandit, and vulture into a single structured LintReport
domain: code
subdomain: test
action: report
target: lint
kind: internal
tags: [testing, lint, ruff, mypy, bandit, vulture, quality]
---

# Lint Reporter

Runs four Python linters (`ruff`, `mypy`, `bandit`, `vulture`) as subprocesses against a source root and merges their output into a single typed `LintReport`. Pure reporter — never modifies source. Linter unavailability (binary missing from `PATH`) is tolerated and surfaced as `available: false` in the per-tool summary; it never raises.

## When to use

- `/code-test-linter` — entry-stage of the test coverage engine pipeline; produces the `LintReport` consumed by downstream stages.
- `/code-test-fixer` — re-runs the reporter after auto-fix passes to verify resolution and surface residuals.
- Standalone forensic check — point at any source root to get one structured roll-up of code-quality signals.

## Input / output contract

### CLI

```bash
python src/tools/testing/code-test-report-lint/lint_reporter.py <source_root> \
    [--tools ruff,mypy,bandit,vulture] [--exclude PATTERN]
```

| Arg | Required | Description |
|-----|----------|-------------|
| `<source_root>` | yes | Path to the source root to lint. |
| `--tools` | no | Comma-separated subset of tools to run. Default: all four. |
| `--exclude` | no | Glob/path pattern to exclude. May be passed multiple times. |

### stdout

A JSON document conforming to the `LintReport` schema (see `schemas.py`):

```json
{
  "source_root": "src/",
  "issues": [
    {
      "file_path": "src/foo.py",
      "line": 12,
      "column": 5,
      "rule_id": "E501",
      "message": "line too long (120 > 100)",
      "severity": "error",
      "tool": "ruff"
    }
  ],
  "summaries": [
    {
      "tool": "ruff",
      "issue_count": 1,
      "error_count": 1,
      "warning_count": 0,
      "available": true,
      "error_message": null
    }
  ],
  "total_issues": 1,
  "total_errors": 1,
  "report_timestamp": "2026-05-01T12:00:00Z"
}
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | No error-severity issues found. |
| `1` | One or more error-severity issues detected (warnings/info alone do not trigger `1`). |
| `2` | Tool error — bad arguments, unreadable `source_root`, schema validation failure. |

## Schema reference

See `schemas.py` — pydantic v2 models:

- `LintIssue` — single normalized finding.
- `LintToolSummary` — per-tool aggregate including `available` flag.
- `LintReport` — top-level CLI payload.

## Severity mapping

Each tool's native severity is normalized into `error | warning | info`:

| Tool | Native input | Normalized severity |
|------|--------------|---------------------|
| ruff | (all diagnostics in JSON mode) | `error` |
| mypy | `error` | `error` |
| mypy | `warning` | `warning` |
| mypy | `note` | `info` |
| bandit | `HIGH` | `error` |
| bandit | `MEDIUM` | `warning` |
| bandit | `LOW` | `info` |
| vulture | (dead-code findings, `--min-confidence 60`) | `warning` |

Severity drives the `total_errors` count and the exit code: only `error`-level issues cause exit `1`.

## How it works

1. Validate `source_root` exists; otherwise exit `2`.
2. For each requested tool:
   - Probe `PATH` with `shutil.which`. If absent, record `available: false` and continue.
   - Invoke the tool via `subprocess.run` in its native machine-readable mode:
     - `ruff check --output-format=json <source_root>` (+ `--exclude` per pattern)
     - `mypy --no-error-summary --no-color-output --show-error-codes --no-pretty <source_root>` (text parsed via regex; mypy's JSON output is not stable across versions)
     - `bandit -r <source_root> -f json` (+ `-x` comma-joined excludes)
     - `vulture <source_root> --min-confidence 60` (+ `--exclude` comma-joined)
   - Parse output into `LintIssue` records using each tool's native field names.
3. Tally totals, stamp `report_timestamp` (UTC), serialize the `LintReport` to stdout.
4. Exit `0` if `total_errors == 0`, else `1`.

## Constraints

- **Linter unavailability is tolerated.** Missing binaries are reported as `available: false`; the tool never raises on a missing linter.
- **Pure reporter.** The tool never modifies source files, never auto-fixes, never invokes formatters.
- **No hardcoded paths.** `source_root` is always supplied by the caller; the tool itself is project-agnostic.
- **No LLM.** Pure deterministic subprocess orchestration.
- **Python 3.11+, pydantic v2.** No third-party deps beyond pydantic and the linter binaries themselves.

## Out of scope

- Fixing or rewriting source code — that is the job of `/code-test-fixer` and the underlying tools' own `--fix` modes, not this reporter.
- Quality judgment about *which* findings matter — that is downstream policy.
- Non-Python linters (eslint, shellcheck, etc.) — out of scope for this tool's first cut.

## Failure handling

Per-tool failures (parse errors, crashed subprocess) are captured in the corresponding `LintToolSummary.error_message` and *do not* abort the run — other tools still execute and the report is still emitted. Only top-level failures (bad args, unreadable `source_root`, schema-validation failure on the assembled report) cause exit `2`.
