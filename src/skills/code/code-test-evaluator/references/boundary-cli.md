# Boundary reference: CLI / subprocess / process boundary

Loaded at [DETECT] when module category is CLI / subprocess / process boundary.

## Detection signals (CLI / subprocess)

- **Runtime tier (boundary-runtime):**
  - `@click.command`, `@click.group`, `click.Context` usage.
  - `argparse.ArgumentParser(...).parse_args(...)` invocations.
  - `typer.Typer()` instances and `.command()` decorators.
  - Direct reads of `sys.argv`, `sys.stdin`, writes to `sys.stdout` / `sys.stderr`.
  - `subprocess.run`, `subprocess.Popen`, `subprocess.check_output`, `subprocess.check_call`.
  - `os.system`, `os.execvp`, `os.execve`, `os.spawnl*`.
- **Logical tier (boundary-logical):**
  - Functions exported via `__all__` from `cli/`, `commands/`, `bin/` packages whose body invokes any runtime-tier signal above.
  - Entry-point functions referenced by `[project.scripts]` / `console_scripts` in `pyproject.toml` / `setup.cfg`.
- **Internal:**
  - Argument validators, `click.types.ParamType` subclasses, help-text builders, command registries / dispatch tables — internal even when imported by command handlers.

## Lifecycle pattern decision rules

- **Project's own CLI in tests -> click `CliRunner` / typer `CliRunner`:** in-process invocation with captured stdout/stderr/exit code; no subprocess overhead; preserves real argument parsing.
- **External binaries -> `subprocess` with captured I/O:** real binary execution, `tmp_path` as cwd, `check=True` to fail loudly, capture both streams. Document binary version requirements in the test strategy preamble.
- **`ephemeral-container` when:** the external binary requires environment setup (system packages, GPU, root, kernel modules) the host CI cannot guarantee. Run inside a pinned image with the binary preinstalled.
- **Never recommend mocking `subprocess.run`** — surface as `over_mocking_warning` for any process-boundary function. Exit-code propagation, signal handling, and stderr capture are exactly what the test must exercise.

## Risk weight (formula)

- `external_dependency_risk = 1` (lowest external category — well-defined contract via exit code, but still a real boundary; do not collapse into `internal`).

## Common over-mock anti-patterns to flag

- Mocking `subprocess.run` to return a fabricated `CompletedProcess` — defeats the boundary contract entirely.
- Patching `sys.argv` directly instead of using `CliRunner` — bypasses click/typer parsing, type coercion, and callback wiring.
- Mocking internal command registries / dispatch maps to inject fake handlers — surface as `over_mocking_warning`; test through the real entry point instead.
- Stubbing `os.system` / `os.execvp` return values — same anti-pattern as `subprocess.run` mocking.

## Out-of-scope

- Signal handling under load, process group / session management, `SIGKILL` vs `SIGTERM` semantics — kernel-level behavior outside this classification.
- Daemon / long-running process patterns, supervision trees — different category (queue/worker).
- Interactive TTY behavior (curses, readline) — separate UI category.
