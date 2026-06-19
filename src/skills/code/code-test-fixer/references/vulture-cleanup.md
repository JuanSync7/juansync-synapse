# Vulture Cleanup Reference

Dead-code removal heuristics and public-API protection rules for [FIX-VULTURE].

---

## 1. Confidence Threshold

Delete only when vulture reports confidence **≥ 90%**.

Below 90%: append to `requires_human_review` with reason `"vulture low-confidence"`. Do not attempt deletion regardless of how obvious the symbol looks.

---

## 2. Public-API Protection

Auto-flag as `requires-human-review` regardless of confidence when any of the following apply:

- Symbol appears in `__all__` of any module.
- Symbol carries a decorator (vulture cannot trace runtime registration; the decorator may wire it into a framework or DI container).
- Symbol is imported by another module in the project — grep before deciding:
  ```
  grep -r "symbol_name" . --include="*.py" | grep -v "def symbol_name"
  ```
- Symbol name matches a plugin entry-point pattern: `load_plugin`, `register_*`, `*_handler`.
- Symbol is referenced in `setup.py` or `pyproject.toml` under `[project.entry-points]` or `entry_points=`.
- Symbol is referenced in YAML or JSON config files (string-based dispatch resolves names at runtime).
- Symbol matches a framework hook signature: pytest fixtures, Flask route functions, Click commands, FastAPI path-operation handlers, SQLAlchemy event listeners.

Reason to record: `"vulture public-api"`.

---

## 3. Common False Positives Vulture Cannot Detect

These patterns make a symbol look unused to vulture even though it is exercised at runtime:

- **Dynamic imports**: `importlib.import_module("mypackage.module")` — the symbol is never statically referenced.
- **`getattr` / `setattr` access**: `getattr(obj, method_name)()` — no static call site exists.
- **Magic methods invoked by frameworks**: `__call__`, `__enter__`, `__exit__`, `__get__` — called by the runtime, not by user code.
- **String-keyed dispatch tables**:
  ```python
  HANDLERS = {"submit": handle_submit, "cancel": handle_cancel}
  ```
  The function is stored by value but vulture sees no call.
- **Reflection-only test coverage**: a test that exercises a symbol exclusively via `getattr` or `importlib` will not register as a reference in vulture's static scan.

When any of these patterns are plausible, grep is not sufficient — escalate to `requires-human-review`.

---

## 4. Safe-to-Delete Categories

All conditions must hold: **confidence ≥ 90%** AND **not on the public-API exclusion list above**.

| Category | Notes |
|---|---|
| Local variable assigned but never read | Lowest risk. Confirm the variable is local (not an attribute assignment). |
| Unused import | ruff F401 should catch this first. If vulture reports it and ruff did not, ruff may have been suppressed — delete and note in commit. |
| Unreachable code after `return` / `raise` | Verify the `return`/`raise` is unconditional before deleting the trailing block. |
| Private function (`_`-prefixed) with no internal callers | Grep the whole file and project for references. Leading `_` is not a guarantee of no callers. |
| Unused method on a class with no subclasses | Confirm no subclasses exist anywhere in the project before deleting. |

---

## 5. Test Code

Vulture frequently flags pytest fixtures and test helper functions. Apply extra caution:

- If the symbol is in a `tests/` directory, default to `requires-human-review` unless it is provably unused.
- Pytest collects fixtures by name matching, not by explicit call sites — a fixture used in a test function signature will not appear as a static reference.
- Test helpers prefixed with `_` may still be called indirectly by parametrized or generated tests.
- Cross-check pytest collection rules: test files use `test_*` prefix; fixtures use `@pytest.fixture`. A flagged symbol that has `@pytest.fixture` falls under the decorator rule in section 2 and must be flagged as `requires-human-review`.

---

## 6. Workflow Per Finding

1. Read the file and line vulture reported.
2. Grep across the project for symbol references, excluding the definition site:
   ```
   grep -rn "symbol_name" . --include="*.py" | grep -v ":<line_of_definition>:"
   ```
   Also grep YAML, JSON, TOML, and config files for string occurrences.
3. If references exist → vulture false positive → `requires-human-review` with reason `"vulture false-positive"`.
4. If no references exist AND the symbol is not on any exclusion in section 2 AND confidence ≥ 90% → safe to delete.
5. Otherwise → `requires-human-review` with a specific reason drawn from sections 1–3.

Commit deletions as `fix(lint): vulture` with a brief per-symbol note in the commit body.
