# @summary
# CLI entrypoint for the mutation-runner tool. Parses a single Python
# source file, generates AST mutants of a target function (or all
# functions), runs the configured test command against each mutant, and
# emits a MutationReport JSON to stdout. Original source is restored in
# try/finally + SIGINT handler so the file is never left mutated.
# Exports: main, generate_mutants, run_mutation
# Deps: ast, argparse, json, signal, subprocess, tempfile, shutil,
#       pydantic, schemas (sibling module)
# @end-summary

"""Mutation-testing harness for a single Python source file.

Usage::

    python -m src.tools.testing.mutation_runner <module_path> \\
        [--function NAME] [--test-cmd "pytest tests/"] \\
        [--max-lines 20] [--timeout 30]

The runner mutates the file in place per mutant, runs the test command,
and restores the original file from a backup. The original is *always*
restored — try/finally plus a SIGINT handler guarantee this even on
interrupt.

Exit codes
----------
* ``0`` — every mutant was killed (kill_rate == 1.0).
* ``1`` — at least one mutant survived.
* ``2`` — tool error (file IO, parse failure, refusal, etc).
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

# Support both ``python -m src.tools.testing.mutation_runner`` (package
# import) and ``python mutation_runner.py`` (script-style execution).
try:  # pragma: no cover - import shim
    from .schemas import Mutant, MutationReport, MutationResult, MutationType
except ImportError:  # pragma: no cover - import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from schemas import Mutant, MutationReport, MutationResult, MutationType  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Mutation generation
# ---------------------------------------------------------------------------


def _arithmetic_swap(op: ast.AST) -> ast.AST | None:
    if isinstance(op, ast.Add):
        return ast.Sub()
    if isinstance(op, ast.Sub):
        return ast.Add()
    if isinstance(op, ast.Mult):
        return ast.Div()
    if isinstance(op, ast.Div):
        return ast.Mult()
    return None


_COMPARISON_PAIRS: dict[type, type] = {
    ast.Lt: ast.Gt,
    ast.Gt: ast.Lt,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.LtE: ast.GtE,
    ast.GtE: ast.LtE,
}


def _comparison_swap(op: ast.AST) -> ast.AST | None:
    target = _COMPARISON_PAIRS.get(type(op))
    return target() if target else None


def _boundary_flip(op: ast.AST) -> ast.AST | None:
    if isinstance(op, ast.Lt):
        return ast.LtE()
    if isinstance(op, ast.Gt):
        return ast.GtE()
    return None


def _boolean_swap(op: ast.AST) -> ast.AST | None:
    if isinstance(op, ast.And):
        return ast.Or()
    if isinstance(op, ast.Or):
        return ast.And()
    return None


def _constant_swap(value: object) -> object | None:
    # Booleans must be checked before ints (``bool`` is a subclass of ``int``).
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        if value == 0:
            return 1
        if value == 1:
            return 0
    return None


def _iter_function_defs(
    tree: ast.AST, function_name: str | None
) -> Iterator[ast.FunctionDef | ast.AsyncFunctionDef]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if function_name is None or node.name == function_name:
                yield node


def _unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - defensive
        return f"<unparse-failed:{type(node).__name__}>"


def generate_mutants(
    source: str,
    module: str,
    function_name: str | None,
    max_lines: int,
) -> list[tuple[Mutant, str]]:
    """Generate mutants for the target function(s) within ``source``.

    Returns a list of ``(Mutant, mutated_source)`` pairs. The line-budget
    is enforced over the count of *distinct* mutated lines (not the count
    of mutants); once the budget is exhausted, no further mutants are
    emitted for new lines.
    """
    tree = ast.parse(source)
    mutated_lines: set[int] = set()
    out: list[tuple[Mutant, str]] = []
    ordinals: dict[tuple[int, MutationType], int] = {}

    def _next_ordinal(line: int, mtype: MutationType) -> int:
        key = (line, mtype)
        ordinals[key] = ordinals.get(key, 0) + 1
        return ordinals[key]

    def _budget_ok(line: int) -> bool:
        if line in mutated_lines:
            return True
        return len(mutated_lines) < max_lines

    def _record(
        func_name: str,
        line: int,
        mtype: MutationType,
        original_code: str,
        mutated_tree: ast.AST,
        mutated_snippet: str,
    ) -> None:
        ast.fix_missing_locations(mutated_tree)
        mutated_source = ast.unparse(mutated_tree)
        ordinal = _next_ordinal(line, mtype)
        mutant = Mutant(
            mutant_id=f"{module}.{func_name}:{line}:{mtype}:{ordinal}",
            module=module,
            function_name=func_name,
            line=line,
            mutation_type=mtype,
            original_code=original_code,
            mutated_code=mutated_snippet,
        )
        out.append((mutant, mutated_source))
        mutated_lines.add(line)

    for func in _iter_function_defs(tree, function_name):
        # Walk only nodes within this function's body.
        for node in ast.walk(func):
            line = getattr(node, "lineno", None)
            if line is None:
                continue

            # arithmetic_op + boundary_flip + comparison_op all act on
            # operator nodes — handle BinOp / Compare / BoolOp cases.
            if isinstance(node, ast.BinOp):
                if not _budget_ok(node.lineno):
                    continue
                swapped = _arithmetic_swap(node.op)
                if swapped is not None:
                    new_tree = ast.parse(source)
                    replacement = _build_binop_replacement(node, swapped)
                    _replace_in_tree(new_tree, node, replacement)
                    _record(
                        func.name,
                        node.lineno,
                        "arithmetic_op",
                        _unparse(node),
                        new_tree,
                        _unparse(replacement),
                    )

            elif isinstance(node, ast.Compare) and node.ops:
                # comparison_op
                for idx, op in enumerate(list(node.ops)):
                    if not _budget_ok(node.lineno):
                        break
                    swapped = _comparison_swap(op)
                    if swapped is not None:
                        new_tree = ast.parse(source)
                        _replace_compare_op(new_tree, node, idx, swapped)
                        mutated_compare = _find_matching(new_tree, node)
                        snippet = (
                            _unparse(mutated_compare)
                            if mutated_compare is not None
                            else _unparse(node)
                        )
                        _record(
                            func.name,
                            node.lineno,
                            "comparison_op",
                            _unparse(node),
                            new_tree,
                            snippet,
                        )
                # boundary_flip is a separate, narrower mutation type.
                for idx, op in enumerate(list(node.ops)):
                    if not _budget_ok(node.lineno):
                        break
                    flipped = _boundary_flip(op)
                    if flipped is not None:
                        new_tree = ast.parse(source)
                        _replace_compare_op(new_tree, node, idx, flipped)
                        mutated_compare = _find_matching(new_tree, node)
                        snippet = (
                            _unparse(mutated_compare)
                            if mutated_compare is not None
                            else _unparse(node)
                        )
                        _record(
                            func.name,
                            node.lineno,
                            "boundary_flip",
                            _unparse(node),
                            new_tree,
                            snippet,
                        )

            elif isinstance(node, ast.BoolOp):
                if not _budget_ok(node.lineno):
                    continue
                swapped = _boolean_swap(node.op)
                if swapped is not None:
                    new_tree = ast.parse(source)
                    _replace_boolop(new_tree, node, swapped)
                    mutated_boolop = _find_matching(new_tree, node)
                    snippet = (
                        _unparse(mutated_boolop)
                        if mutated_boolop is not None
                        else _unparse(node)
                    )
                    _record(
                        func.name,
                        node.lineno,
                        "boolean_op",
                        _unparse(node),
                        new_tree,
                        snippet,
                    )

            elif isinstance(node, ast.Constant):
                if not _budget_ok(node.lineno):
                    continue
                swapped = _constant_swap(node.value)
                if swapped is not None:
                    new_tree = ast.parse(source)
                    _replace_constant(new_tree, node, swapped)
                    _record(
                        func.name,
                        node.lineno,
                        "constant_swap",
                        repr(node.value),
                        new_tree,
                        repr(swapped),
                    )

            elif isinstance(node, ast.Return):
                if node.value is None:
                    continue
                if not _budget_ok(node.lineno):
                    continue
                new_tree = ast.parse(source)
                _replace_return_value(new_tree, node)
                _record(
                    func.name,
                    node.lineno,
                    "return_value",
                    _unparse(node),
                    new_tree,
                    "return None",
                )

            elif isinstance(node, ast.If):
                if not _budget_ok(node.lineno):
                    continue
                new_tree = ast.parse(source)
                _negate_if_test(new_tree, node)
                _record(
                    func.name,
                    node.lineno,
                    "negate_condition",
                    _unparse(node.test),
                    new_tree,
                    f"not ({_unparse(node.test)})",
                )

    return out


# ---------------------------------------------------------------------------
# AST surgery helpers — re-parse-and-replace by source position
# ---------------------------------------------------------------------------


def _node_position(node: ast.AST) -> tuple[int, int] | None:
    line = getattr(node, "lineno", None)
    col = getattr(node, "col_offset", None)
    if line is None or col is None:
        return None
    return (line, col)


def _find_matching(tree: ast.AST, original: ast.AST) -> ast.AST | None:
    pos = _node_position(original)
    target_type = type(original)
    for candidate in ast.walk(tree):
        if not isinstance(candidate, target_type):
            continue
        if _node_position(candidate) == pos:
            return candidate
    return None


def _build_binop_replacement(original: ast.BinOp, new_op: ast.AST) -> ast.BinOp:
    return ast.BinOp(left=original.left, op=new_op, right=original.right)


def _replace_in_tree(
    tree: ast.AST, original: ast.AST, replacement: ast.AST
) -> None:
    pos = _node_position(original)
    target_type = type(original)
    for parent in ast.walk(tree):
        for field, value in list(ast.iter_fields(parent)):
            if isinstance(value, list):
                for i, item in enumerate(value):
                    if (
                        isinstance(item, target_type)
                        and _node_position(item) == pos
                    ):
                        value[i] = replacement
                        return
            elif isinstance(value, target_type) and _node_position(value) == pos:
                setattr(parent, field, replacement)
                return


def _replace_compare_op(
    tree: ast.AST, original: ast.Compare, op_index: int, new_op: ast.AST
) -> None:
    match = _find_matching(tree, original)
    if isinstance(match, ast.Compare) and 0 <= op_index < len(match.ops):
        match.ops[op_index] = new_op


def _replace_boolop(
    tree: ast.AST, original: ast.BoolOp, new_op: ast.AST
) -> None:
    match = _find_matching(tree, original)
    if isinstance(match, ast.BoolOp):
        match.op = new_op


def _replace_constant(
    tree: ast.AST, original: ast.Constant, new_value: object
) -> None:
    match = _find_matching(tree, original)
    if isinstance(match, ast.Constant):
        match.value = new_value


def _replace_return_value(tree: ast.AST, original: ast.Return) -> None:
    match = _find_matching(tree, original)
    if isinstance(match, ast.Return):
        match.value = ast.Constant(value=None)


def _negate_if_test(tree: ast.AST, original: ast.If) -> None:
    match = _find_matching(tree, original)
    if isinstance(match, ast.If):
        match.test = ast.UnaryOp(op=ast.Not(), operand=match.test)


# ---------------------------------------------------------------------------
# Test execution
# ---------------------------------------------------------------------------


_PYTEST_FAIL_RE = re.compile(r"^FAILED\s+(\S+)", re.MULTILINE)


def _parse_first_failing_test(stdout: str) -> str | None:
    match = _PYTEST_FAIL_RE.search(stdout)
    return match.group(1) if match else None


def run_mutation(
    mutant: Mutant,
    mutated_source: str,
    target_path: Path,
    test_cmd: list[str],
    timeout: float,
) -> MutationResult:
    """Apply ``mutated_source`` to ``target_path``, run tests, restore."""
    started = time.monotonic()
    backup = target_path.read_text(encoding="utf-8")

    # Atomic write: tempfile in the same directory + os.replace.
    fd, tmp_path_str = tempfile.mkstemp(
        prefix=".mutation-",
        suffix=".py.tmp",
        dir=str(target_path.parent),
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(mutated_source)
        os.replace(tmp_path, target_path)
        tmp_path = None  # ownership transferred

        try:
            completed = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = time.monotonic() - started
            return MutationResult(
                mutant=mutant,
                killed=True,  # timeout counts as killed by convention
                killing_test=None,
                runtime_seconds=elapsed,
                error_output=f"timeout after {timeout}s: {exc}",
            )
        except (OSError, subprocess.SubprocessError) as exc:
            elapsed = time.monotonic() - started
            return MutationResult(
                mutant=mutant,
                killed=False,
                killing_test=None,
                runtime_seconds=elapsed,
                error_output=f"subprocess error: {exc}",
            )

        elapsed = time.monotonic() - started
        killed = completed.returncode != 0
        killing_test = (
            _parse_first_failing_test(completed.stdout or "") if killed else None
        )
        error_output = None
        if killed and not killing_test and completed.stderr:
            # Surface stderr for diagnostic purposes when no failing-test
            # node id could be parsed.
            error_output = completed.stderr[-2000:]
        return MutationResult(
            mutant=mutant,
            killed=killed,
            killing_test=killing_test,
            runtime_seconds=elapsed,
            error_output=error_output,
        )
    finally:
        # Always restore the original. Use atomic replace.
        try:
            target_path.write_text(backup, encoding="utf-8")
        except Exception as exc:  # pragma: no cover - last-resort
            print(
                f"FATAL: failed to restore {target_path}: {exc}",
                file=sys.stderr,
            )
            raise
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Safety: refuse test files; install signal handler that restores backup
# ---------------------------------------------------------------------------


def _is_test_file(path: Path) -> bool:
    name = path.name
    if name.startswith("test_") or name.endswith("_test.py"):
        return True
    parts = {p.lower() for p in path.parts}
    return "tests" in parts or "test" in parts


class _RestoreOnSignal:
    """Context manager that re-installs SIGINT/SIGTERM handlers to restore
    the target file from an in-memory backup before re-raising.
    """

    def __init__(self, target_path: Path, backup: str) -> None:
        self.target_path = target_path
        self.backup = backup
        self._prev_int = None
        self._prev_term = None

    def _handler(self, signum: int, frame) -> None:  # noqa: ANN001
        try:
            self.target_path.write_text(self.backup, encoding="utf-8")
        finally:
            # Re-raise as KeyboardInterrupt so try/finally up the stack runs.
            raise KeyboardInterrupt(f"interrupted by signal {signum}")

    def __enter__(self) -> "_RestoreOnSignal":
        self._prev_int = signal.signal(signal.SIGINT, self._handler)
        try:
            self._prev_term = signal.signal(signal.SIGTERM, self._handler)
        except (ValueError, OSError):  # pragma: no cover - non-main thread
            self._prev_term = None
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._prev_int is not None:
            signal.signal(signal.SIGINT, self._prev_int)
        if self._prev_term is not None:
            try:
                signal.signal(signal.SIGTERM, self._prev_term)
            except (ValueError, OSError):  # pragma: no cover
                pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mutation-runner",
        description=(
            "Generate AST mutants of a Python function and run the test "
            "suite against each one."
        ),
    )
    parser.add_argument(
        "module_path",
        help="Path to a single .py file containing the target function.",
    )
    parser.add_argument(
        "--function",
        default=None,
        help="Name of the target function. If omitted, all functions are mutated.",
    )
    parser.add_argument(
        "--test-cmd",
        default="pytest",
        help='Test command to run per mutant (default: "pytest").',
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=20,
        help="Maximum number of distinct lines to mutate (default: 20).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Per-mutant subprocess timeout in seconds (default: 30).",
    )
    return parser.parse_args(argv)


def _emit_error(message: str) -> int:
    print(json.dumps({"error": message}, indent=2))
    return 2


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    target_path = Path(args.module_path).resolve()

    if not target_path.exists() or not target_path.is_file():
        return _emit_error(f"module path does not exist: {target_path}")
    if target_path.suffix != ".py":
        return _emit_error(f"module path is not a .py file: {target_path}")
    if _is_test_file(target_path):
        return _emit_error(
            f"refusing to mutate a test file: {target_path}"
        )

    try:
        source = target_path.read_text(encoding="utf-8")
    except OSError as exc:
        return _emit_error(f"failed to read source: {exc}")

    module_name = target_path.stem
    try:
        mutants = generate_mutants(
            source=source,
            module=module_name,
            function_name=args.function,
            max_lines=args.max_lines,
        )
    except SyntaxError as exc:
        return _emit_error(f"failed to parse source: {exc}")

    test_cmd = args.test_cmd.split() if isinstance(args.test_cmd, str) else list(args.test_cmd)

    results: list[MutationResult] = []
    killed = 0
    survived = 0
    timed_out = 0

    backup = source
    with _RestoreOnSignal(target_path, backup):
        try:
            for mutant, mutated_source in mutants:
                result = run_mutation(
                    mutant=mutant,
                    mutated_source=mutated_source,
                    target_path=target_path,
                    test_cmd=test_cmd,
                    timeout=args.timeout,
                )
                results.append(result)
                if result.error_output and "timeout" in (result.error_output or ""):
                    timed_out += 1
                if result.killed:
                    killed += 1
                else:
                    survived += 1
        finally:
            # Belt-and-braces: ensure the original is on disk no matter what.
            try:
                target_path.write_text(backup, encoding="utf-8")
            except Exception as exc:  # pragma: no cover
                print(
                    f"FATAL: failed final restore of {target_path}: {exc}",
                    file=sys.stderr,
                )
                return 2

    total = len(results)
    kill_rate = (killed / total) if total else 1.0

    report = MutationReport(
        source_root=str(target_path.parent),
        target_module=module_name,
        target_function=args.function,
        total_mutants=total,
        killed=killed,
        survived=survived,
        timeout=timed_out,
        kill_rate=kill_rate,
        results=results,
        line_budget=args.max_lines,
        timestamp=datetime.now(timezone.utc),
    )

    print(report.model_dump_json(indent=2))

    if total == 0:
        # No mutants generated — nothing to test, treat as success.
        return 0
    return 0 if kill_rate == 1.0 else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
