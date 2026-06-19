# Vulture Thresholds — Dead Code Detection Reference

Loaded at `[RUN-EACH-LINTER]` during the linter sweep phase.

---

## What Vulture Catches

Vulture performs AST-based static analysis to find symbols defined but never referenced
anywhere in the scanned codebase. It catches:

- **Functions and methods** — defined but never called
- **Classes** — declared but never instantiated or subclassed
- **Variables** — assigned but never read
- **Imports** — imported names that go unused
- **Attributes** — set on `self` but never accessed
- **Unreachable code** — branches after unconditional `return`/`raise`/`continue`

Because vulture uses AST traversal rather than runtime tracing, it cannot see dynamic
dispatch (`getattr(obj, name)()`) or runtime attribute access. This is the source of most
false positives.

---

## Confidence Threshold

Vulture assigns each finding a **confidence score (0–100%)** representing how certain it
is the symbol is truly unused. Lower scores indicate more speculative findings.

| Confidence | Meaning |
|---|---|
| 100% | Symbol has no references anywhere in the scanned tree |
| 60–99% | Symbol may have dynamic or indirect references |
| Below 60% | Highly speculative; nearly always a false positive |

**Default:** vulture reports at 60% confidence.

**Recommended threshold for this skill: 80% minimum.**

Invoke with:

```
vulture <path> --min-confidence 80 --sort-by-size
```

`--sort-by-size` ranks larger dead symbols first, prioritizing high-impact cleanup.
The 80% floor eliminates the bulk of false positives from framework hooks and dynamic
dispatch while keeping genuinely orphaned code visible.

---

## Severity Normalization

The `lint_reporter` tool maps vulture confidence bands to `LintIssue.severity`:

| Vulture confidence | `LintIssue.severity` | Rationale |
|---|---|---|
| 100% | `"warning"` | Very likely dead, but dead code never breaks runtime |
| 80–99% | `"info"` | Probable but dynamic dispatch cannot be ruled out |
| Below 80% | Not reported | Filtered before aggregation |

Dead code is never escalated to `"error"` — it does not prevent execution. The warning/info
distinction signals confidence, not severity in the runtime sense. `code-test-fixer` uses these
levels to prioritize its action queue.

---

## Whitelist Convention

Vulture supports a **whitelist file** — a Python file containing fake references to symbols
that are intentionally unused (framework callbacks, public API surface, `__all__` entries).

Example `whitelist.py`:

```python
# vulture whitelist — intentionally unused symbols
MyView.get          # Django CBV handler
app.on_startup      # FastAPI lifecycle hook
MyModel.save        # Overridden in subclass
```

The skill respects an existing whitelist if found at any of these locations:

- `<repo-root>/whitelist.py`
- `<repo-root>/vulture_whitelist.py`
- `<repo-root>/tests/whitelist.py`

Pass it to vulture automatically when found:

```
vulture <path> whitelist.py --min-confidence 80 --sort-by-size
```

The whitelist is the **project's escape hatch** for any symbol vulture flags incorrectly.
Do not delete or bypass it — `code-test-fixer` can add entries when actionable suppression is
needed.

---

## Common False-Positive Patterns

The following patterns produce false positives at any confidence level. Recognize them
before treating a finding as actionable:

- **Django/FastAPI route handlers** — `get()`, `post()`, `delete()` on class-based views; FastAPI path functions registered via decorator. Vulture does not trace decorator magic.
- **pytest fixtures** — functions decorated with `@pytest.fixture` are called by the test framework via name injection, not direct call.
- **ABC abstract method implementations** — a method in a subclass that satisfies an abstract base class contract has no explicit caller in user code.
- **`__init__` defined in subclasses** — calls from `super().__init__()` in sibling subclasses are invisible to AST-only analysis.
- **`__all__` entries** — names exported via `__all__` may have no internal callers but are part of the public API.

**Important:** `# pragma: no cover` and `# noqa` comments do **not** silence vulture.
Only entries in the whitelist file suppress a finding. Remind `code-test-fixer` of this if it
attempts noqa-based suppression.

---

## Output Parsing

Vulture does not produce native JSON. Its textual output format is:

```
path/to/file.py:42: unused function 'my_func' (60% confidence)
```

The `lint_reporter` tool parses this format into normalized `LintIssue` objects before
aggregation. No manual parsing is needed inside the skill flow.

---

## What Dead Code Means in Practice

Findings from vulture are typically one of:

- **Orphaned helpers** — utility functions left behind after a refactor removed their callers
- **Unused imports** — names imported during prototyping or copy-paste that were never used
- **Leftover debug functions** — `dump_state()`, `debug_print()` added during development

`code-test-fixer` will action these findings by either deleting the dead symbol or adding it to
the whitelist if the removal is unsafe. The code-test-linter skill's responsibility is only to
surface findings accurately — never to delete or suppress them.
