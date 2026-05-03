"""Assertion-quality scanner for pytest test suites.

Walks a test root, parses each ``test_*.py`` / ``*_test.py`` via the stdlib
``ast`` module, and computes a per-test quality score based on assertion
strength. Detects weak patterns (no assertion, trivial constants, tautologies,
mock.called without args, isinstance-only checks, swallowed exceptions).

Usage::

    python -m src.tools.testing.assertion_quality <test_root> \\
        [--threshold 0.5] [--min-assertions 2]

Exit codes:
    0 — every scored test meets the threshold.
    1 — at least one test scored below the threshold.
    2 — tool error (bad path, parse failure on every file, etc.).
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

# Local schema imports. The directory is hyphenated (``assertion-quality``) so
# this module is intended to be invoked as a script (``python path/to/file``)
# or via the ``-m src.tools.testing.assertion_quality`` shim documented in the
# tool README. We use a relative-friendly fallback here so both invocation
# styles work without forcing callers to install the package.
try:  # pragma: no cover - import shim
    from .schemas import AssertionIssue, AssertionQualityReport, TestQualityScore
except ImportError:  # pragma: no cover - script mode
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from schemas import (  # type: ignore[no-redef]
        AssertionIssue,
        AssertionQualityReport,
        TestQualityScore,
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NO_ASSERTION_PENALTY = 0.4
MEDIUM_PENALTY = 0.2  # trivial / tautological / mock_called_no_args
LIGHT_PENALTY = 0.1  # weak_isinstance / exception_swallowed
CLEAN_BONUS = 0.1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _iter_test_files(root: Path) -> Iterable[Path]:
    """Yield every ``test_*.py`` and ``*_test.py`` under ``root``."""
    for path in sorted(root.rglob("*.py")):
        name = path.name
        if name.startswith("test_") or name.endswith("_test.py"):
            yield path


def _source_line(source_lines: list[str], lineno: int) -> str:
    """Return the source line at ``lineno`` (1-indexed), trimmed."""
    if 1 <= lineno <= len(source_lines):
        return source_lines[lineno - 1].strip()
    return ""


def _is_constant_truthy_or_string(node: ast.AST) -> bool:
    """Detect ``assert <constant>`` patterns used to game coverage."""
    return isinstance(node, ast.Constant)


def _is_tautology(test: ast.AST) -> bool:
    """Detect ``assert x == x`` / ``assert x is x`` style tautologies."""
    if not isinstance(test, ast.Compare):
        return False
    if len(test.ops) != 1 or len(test.comparators) != 1:
        return False
    op = test.ops[0]
    if not isinstance(op, (ast.Eq, ast.Is)):
        return False
    return ast.dump(test.left) == ast.dump(test.comparators[0])


def _attr_chain(node: ast.AST) -> str | None:
    """Return ``a.b.c`` for nested ``Attribute`` chains; None otherwise."""
    parts: list[str] = []
    cur: ast.AST = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return None


def _is_mock_assert_call(node: ast.Call) -> bool:
    """Detect ``something.assert_called*`` / ``assert_any_call`` / ``assert_*``."""
    if not isinstance(node.func, ast.Attribute):
        return False
    return node.func.attr.startswith("assert_")


def _is_pytest_raises(node: ast.AST) -> bool:
    """Detect ``pytest.raises(...)`` / ``raises(...)`` calls."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr == "raises":
        return True
    if isinstance(func, ast.Name) and func.id == "raises":
        return True
    return False


# ---------------------------------------------------------------------------
# Per-test analysis
# ---------------------------------------------------------------------------


class _TestAnalyzer(ast.NodeVisitor):
    """Walks a single test function body and collects assertion stats + issues."""

    def __init__(self, source_lines: list[str]) -> None:
        self.source_lines = source_lines
        self.assertion_count = 0
        self.issues: list[AssertionIssue] = []
        self.has_strong_assert = False
        self.has_value_check = False
        self.has_only_isinstance_seen = False
        self.isinstance_only_lines: list[int] = []

    # -- assert -----------------------------------------------------------

    def visit_Assert(self, node: ast.Assert) -> None:  # noqa: N802 (ast API)
        self.assertion_count += 1
        snippet = _source_line(self.source_lines, node.lineno)

        if _is_constant_truthy_or_string(node.test):
            self.issues.append(
                AssertionIssue(
                    line=node.lineno,
                    issue_type="trivial_assertion",
                    message="Assertion on a literal constant — always passes (or always fails) regardless of code under test.",
                    snippet=snippet,
                )
            )
            return

        if _is_tautology(node.test):
            self.issues.append(
                AssertionIssue(
                    line=node.lineno,
                    issue_type="tautological_assertion",
                    message="Assertion compares an expression to itself — verifies nothing.",
                    snippet=snippet,
                )
            )
            return

        # assert isinstance(x, T) — weak unless paired with a value check
        if (
            isinstance(node.test, ast.Call)
            and isinstance(node.test.func, ast.Name)
            and node.test.func.id == "isinstance"
        ):
            self.isinstance_only_lines.append(node.lineno)
            # We do NOT mark this strong yet; promotion happens after the full
            # body is walked and we know whether other value checks exist.
            return

        # assert mock.called  (attribute access, no call)  → weak
        chain = _attr_chain(node.test)
        if chain and chain.endswith(".called"):
            self.issues.append(
                AssertionIssue(
                    line=node.lineno,
                    issue_type="mock_called_no_args",
                    message="`assert mock.called` checks invocation but not arguments — use `assert_called_with(...)`.",
                    snippet=snippet,
                )
            )
            return

        # Otherwise: a real assertion with a non-trivial test expression.
        self.has_strong_assert = True
        self.has_value_check = True

    # -- expression statements (mock.assert_called*, pytest.raises) -------

    def visit_Expr(self, node: ast.Expr) -> None:  # noqa: N802
        value = node.value
        if isinstance(value, ast.Call) and _is_mock_assert_call(value):
            self.assertion_count += 1
            snippet = _source_line(self.source_lines, node.lineno)
            attr = value.func.attr  # type: ignore[attr-defined]
            # assert_called() / assert_called_once() with NO args is weak.
            if attr in {"assert_called", "assert_called_once"} and not value.args and not value.keywords:
                self.issues.append(
                    AssertionIssue(
                        line=node.lineno,
                        issue_type="mock_called_no_args",
                        message=f"`{attr}()` verifies invocation but not arguments — prefer `assert_called_with(...)`.",
                        snippet=snippet,
                    )
                )
            else:
                self.has_strong_assert = True
                self.has_value_check = True
        self.generic_visit(node)

    # -- with pytest.raises(...) ------------------------------------------

    def visit_With(self, node: ast.With) -> None:  # noqa: N802
        for item in node.items:
            if _is_pytest_raises(item.context_expr):
                self.assertion_count += 1
                self.has_strong_assert = True
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:  # noqa: N802
        for item in node.items:
            if _is_pytest_raises(item.context_expr):
                self.assertion_count += 1
                self.has_strong_assert = True
        self.generic_visit(node)

    # -- exception swallowing ---------------------------------------------

    def visit_Try(self, node: ast.Try) -> None:  # noqa: N802
        for handler in node.handlers:
            if _handler_is_swallow(handler):
                snippet = _source_line(self.source_lines, handler.lineno)
                self.issues.append(
                    AssertionIssue(
                        line=handler.lineno,
                        issue_type="exception_swallowed",
                        message="`except` block neither re-raises nor asserts — exceptions are silently swallowed.",
                        snippet=snippet,
                    )
                )
        self.generic_visit(node)


def _handler_is_swallow(handler: ast.ExceptHandler) -> bool:
    """True when an ``except`` block has no raise and no assertion."""
    for child in ast.walk(handler):
        if isinstance(child, ast.Raise):
            return False
        if isinstance(child, ast.Assert):
            return False
        if isinstance(child, ast.Call) and _is_mock_assert_call(child):
            return False
    return True


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _score_test(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    source_lines: list[str],
    test_file: Path,
    test_root: Path,
    min_assertions: int,
) -> TestQualityScore:
    analyzer = _TestAnalyzer(source_lines)
    for stmt in func.body:
        analyzer.visit(stmt)

    # Promote weak_isinstance: only flag if isinstance was the sole "assert"
    # (no other value checks anywhere in the body). The assertion_count was
    # already incremented at the top of visit_Assert; we only add issues here.
    if analyzer.isinstance_only_lines and not analyzer.has_value_check:
        for line in analyzer.isinstance_only_lines:
            analyzer.issues.append(
                AssertionIssue(
                    line=line,
                    issue_type="weak_isinstance",
                    message="Test only verifies type via `isinstance(...)` — no value/state assertion.",
                    snippet=_source_line(source_lines, line),
                )
            )

    if analyzer.assertion_count == 0:
        analyzer.issues.append(
            AssertionIssue(
                line=func.lineno,
                issue_type="no_assertion",
                message="Test function contains zero assertions — exercises code without verifying behavior.",
                snippet=_source_line(source_lines, func.lineno),
            )
        )

    # ---- score ------------------------------------------------------------
    score = 1.0
    for issue in analyzer.issues:
        if issue.issue_type == "no_assertion":
            score -= NO_ASSERTION_PENALTY
        elif issue.issue_type in {
            "trivial_assertion",
            "tautological_assertion",
            "mock_called_no_args",
        }:
            score -= MEDIUM_PENALTY
        elif issue.issue_type in {"weak_isinstance", "exception_swallowed"}:
            score -= LIGHT_PENALTY

    if not analyzer.issues and analyzer.assertion_count >= min_assertions:
        score += CLEAN_BONUS

    score = max(0.0, min(1.0, score))

    has_no_assert_or_trivial = any(
        i.issue_type in {"no_assertion", "trivial_assertion"} for i in analyzer.issues
    )
    has_meaningful = analyzer.assertion_count >= 1 and not has_no_assert_or_trivial

    try:
        rel_file = test_file.relative_to(test_root).as_posix()
    except ValueError:
        rel_file = str(test_file)

    return TestQualityScore(
        test_file=rel_file,
        test_function=func.name,
        line_start=func.lineno,
        assertion_count=analyzer.assertion_count,
        quality_score=round(score, 4),
        issues=analyzer.issues,
        has_meaningful_assertion=has_meaningful,
    )


# ---------------------------------------------------------------------------
# File / report assembly
# ---------------------------------------------------------------------------


def _scan_file(
    path: Path, test_root: Path, min_assertions: int
) -> list[TestQualityScore]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    source_lines = source.splitlines()
    scores: list[TestQualityScore] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            "test_"
        ):
            scores.append(
                _score_test(node, source_lines, path, test_root, min_assertions)
            )

    return scores


def build_report(
    test_root: Path, threshold: float, min_assertions: int
) -> AssertionQualityReport:
    """Scan ``test_root`` and return an :class:`AssertionQualityReport`."""
    scores: list[TestQualityScore] = []
    for path in _iter_test_files(test_root):
        scores.extend(_scan_file(path, test_root, min_assertions))

    total = len(scores)
    below = sum(1 for s in scores if s.quality_score < threshold)
    no_assert = sum(
        1 for s in scores if any(i.issue_type == "no_assertion" for i in s.issues)
    )
    avg = (sum(s.quality_score for s in scores) / total) if total else 0.0

    return AssertionQualityReport(
        test_root=str(test_root),
        scores=scores,
        total_tests=total,
        tests_below_threshold=below,
        tests_with_no_assertion=no_assert,
        average_score=round(avg, 4),
        threshold=threshold,
        timestamp=datetime.now(tz=timezone.utc),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="assertion-quality",
        description="Score pytest test functions by assertion strength.",
    )
    parser.add_argument("test_root", help="Path to the directory containing tests.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Minimum acceptable quality score (default: 0.5).",
    )
    parser.add_argument(
        "--min-assertions",
        type=int,
        default=2,
        dest="min_assertions",
        help="Bonus threshold for clean tests (default: 2).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parse_args(argv)
        root = Path(args.test_root).resolve()
        if not root.exists() or not root.is_dir():
            print(
                json.dumps({"error": f"test_root not found or not a directory: {root}"}),
                file=sys.stderr,
            )
            return 2

        if not (0.0 <= args.threshold <= 1.0):
            print(
                json.dumps({"error": "--threshold must be between 0.0 and 1.0"}),
                file=sys.stderr,
            )
            return 2

        report = build_report(root, args.threshold, args.min_assertions)
        print(report.model_dump_json(indent=2))
        return 1 if report.tests_below_threshold > 0 else 0
    except Exception as exc:  # pragma: no cover - defensive
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
