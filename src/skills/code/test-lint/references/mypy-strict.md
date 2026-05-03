# mypy Strict-Mode Reference

Loaded at [RUN-EACH-LINTER]. Covers invocation, output parsing, severity mapping, and
config precedence for mypy strict-mode runs inside the test-lint skill.

---

## 1. What `--strict` Enables

`--strict` is a meta-flag that activates the following individual flags. Understand each
so you can reason about findings rather than treating them as a black box.

| Flag | Effect |
|------|--------|
| `--disallow-untyped-defs` | Every function must have annotated parameters and return type. |
| `--disallow-incomplete-defs` | Partial annotations (some args typed, some not) are rejected. |
| `--disallow-any-generics` | Generic types like `list`, `dict` must carry type parameters (`list[str]`). |
| `--disallow-any-unimported` | Types from unimported modules cannot resolve to `Any`. |
| `--disallow-subclassing-any` | Prevents subclassing a class typed as `Any`. |
| `--no-implicit-optional` | `def f(x: str = None)` is an error; must write `Optional[str]`. |
| `--warn-return-any` | Flags functions that return `Any` when the declared return is narrower. |
| `--warn-redundant-casts` | Flags `cast()` calls that are no-ops given the inferred type. |
| `--warn-unused-ignores` | Flags `# type: ignore` comments that no longer suppress anything. |
| `--warn-unused-configs` | Flags mypy config sections that match no actual module. |
| `--extra-checks` | Enables additional strict checks (e.g., `--strict-equality`). |

Do not pass individual strict flags on the command line — use `--strict` and let the
project's `mypy.ini` / `pyproject.toml` add or remove flags as needed.

---

## 2. Daemon Mode (dmypy)

For repos with 1,000+ Python files, use `dmypy` (the mypy daemon). The daemon keeps a
warm type cache across runs, cutting incremental check time from minutes to seconds.

**Preferred invocation:**

```
dmypy run -- --strict --show-error-codes --no-color-output --no-error-summary <target>
```

`dmypy run` starts the daemon if not already running and reuses the cache on subsequent
calls. The daemon is transparent to output format — parse it the same way as plain mypy.

**Fallback:** If `dmypy` is unavailable (binary missing, daemon refuses to start, or the
project explicitly opts out via `MYPY_FORCE_PLAIN=1`), fall back to plain `mypy`. Emit a
`LintIssue` with `code: "MYPY_DAEMON_UNAVAILABLE"` and `severity: "info"` so the report
signals the slower path without failing the run.

---

## 3. Invocation Flags

### Standard (human-readable) invocation

```
mypy --strict --show-error-codes --no-color-output --no-error-summary <target>
```

- `--show-error-codes` — required; populates `LintIssue.code` (e.g., `[arg-type]`).
- `--no-color-output` — avoids ANSI escape sequences in captured stdout.
- `--no-error-summary` — suppresses the trailing `Found N errors in M files` line, which
  would otherwise require special-casing during line-by-line parsing.

### Machine-readable (JSON) invocation

Newer mypy (≥ 0.981) supports `--output=json`:

```
mypy --strict --show-error-codes --no-color-output --output=json <target>
```

Each stdout line is a JSON object. Prefer this when available — it eliminates fragile
regex parsing. Detect support with `mypy --version` and compare the version string.

Fall back to parsing the standard format when `--output=json` is unsupported.

### Standard format parse pattern

```
<file>:<line>:<col>: <severity>: <message>  [<code>]
```

Example: `src/foo.py:42:8: error: Argument 1 has incompatible type "str"  [arg-type]`

Note lines (`note:`) appear directly after the error they annotate — associate them with
the preceding error rather than emitting a standalone `LintIssue`.

---

## 4. Severity Normalization

| mypy token | `LintIssue.severity` | Notes |
|------------|----------------------|-------|
| `error` | `"error"` | The vast majority of mypy output. |
| `note` | `"info"` | Attach to the preceding `error` issue as supplementary context; do not emit a separate `LintIssue`. |
| `warning` | `"warning"` | Rare; mypy uses this for deprecation and some config warnings. |

When `--no-error-summary` is set, the final summary line is suppressed. If it appears
anyway (older mypy), skip lines matching `^Found \d+ error`.

---

## 5. Config Inheritance

mypy resolves configuration in this precedence order (highest to lowest):

1. `mypy.ini` — standalone file at repo root.
2. `pyproject.toml` under `[tool.mypy]` — used when no `mypy.ini` is present.
3. `setup.cfg` under `[mypy]` — legacy fallback.

The first file found wins; mypy does not merge across files. Document which config file
was resolved in the report metadata so findings are reproducible across environments.
When no config file is found, emit a `LintIssue` with `code: "MISSING_CONFIG"` —
consistent with the [SCAN] node's convention.

---

## 6. Third-Party Libraries Without Stubs

When a third-party library has no bundled type stubs and no `py.typed` marker, mypy
emits `import-untyped` errors:

```
src/foo.py:3:1: error: Library stubs not installed for "requests"  [import-untyped]
```

MUST surface these — do not suppress or filter. They represent genuine typing gaps.

When you encounter `import-untyped` findings, record them faithfully in the `LintReport`.
The correct remediation is for the project to either:

- Install stubs (e.g., `types-requests`) and declare them in `pyproject.toml`, or
- Add a `[[tool.mypy.overrides]]` section to silence the specific import.

The skill MUST NOT modify any config file to suppress these errors. Surface the finding;
let the project owner decide the remediation strategy.

---

## 7. Per-File Ignores

Projects may declare per-module overrides in their mypy config:

```ini
[mypy-foo.bar.*]
ignore_missing_imports = True
```

or in `pyproject.toml`:

```toml
[[tool.mypy.overrides]]
module = "foo.bar.*"
ignore_missing_imports = true
```

Respect these overrides — mypy will already apply them at runtime. Do not re-emit
suppressed findings, and do not invent new overrides inside the skill. If a project's
overrides are overly broad (e.g., `ignore_errors = True` on entire packages), surface
the suppression scope in report metadata as a `LintIssue` with `code: "BROAD_MYPY_OVERRIDE"`
and `severity: "warning"` so downstream reviewers are aware of the blind spot.
