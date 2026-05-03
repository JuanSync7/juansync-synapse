# @summary
# CLI entry point for the coverage-analyzer tool.
# Default mode: reads .coverage data and reports per-function coverage gaps (CoverageReport).
# --edges mode: performs static AST walk to find cross-package call-graph edges (EdgeCoverageReport).
# Exports: main
# Deps: coverage, ast, argparse, pydantic, schemas
# @end-summary

"""
coverage-analyzer — per-function coverage gaps and cross-package call-graph edge reporter.

Usage
-----
Default mode (coverage gaps):
    python -m src.tools.testing.coverage_analyzer <source_root>

Edge mode (cross-package call graph):
    python -m src.tools.testing.coverage_analyzer <source_root> \\
        --edges \\
        [--test-path PATH] \\
        [--baseline PATH] \\
        [--sha SHA]

Output is always JSON written to stdout.  Exit code is always 0.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


# ---------------------------------------------------------------------------
# Helpers — shared
# ---------------------------------------------------------------------------

def _iter_python_files(root: Path) -> Iterator[Path]:
    """Yield every *.py file under *root*, skipping hidden directories."""
    for path in sorted(root.rglob("*.py")):
        if any(part.startswith(".") for part in path.parts):
            continue
        yield path


def _path_to_module(path: Path, root: Path) -> str:
    """Convert a source file path to a dotted module name relative to *root*."""
    rel = path.relative_to(root)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    elif parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


# ---------------------------------------------------------------------------
# Boundary detection helpers (default mode)
# ---------------------------------------------------------------------------

_BOUNDARY_DECORATOR_NAMES: frozenset[str] = frozenset(
    {
        # Flask / FastAPI / Starlette routes
        "route", "get", "post", "put", "delete", "patch",
        # Temporal / activities
        "defn",
        # Click CLI
        "command", "group",
    }
)

_BOUNDARY_DECORATOR_ATTRS: frozenset[str] = frozenset(
    {
        # e.g. app.route, router.get, activity.defn
        "route", "get", "post", "put", "delete", "patch", "defn", "command", "group",
    }
)

_BOUNDARY_READS: frozenset[str] = frozenset({"request", "os", "sys"})


def _is_boundary(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if *func_node* looks like a public boundary entry-point."""
    for decorator in func_node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id in _BOUNDARY_DECORATOR_NAMES:
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr in _BOUNDARY_DECORATOR_ATTRS:
            return True
        # @app.route(...), @router.get(...) — the decorator is a Call whose func is an Attribute
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr in _BOUNDARY_DECORATOR_ATTRS
        ):
            return True

    # Body reads: request.*, os.environ.*, sys.stdin.*
    for node in ast.walk(func_node):
        if isinstance(node, ast.Name) and node.id in _BOUNDARY_READS:
            return True
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id in _BOUNDARY_READS:
                return True

    return False


# ---------------------------------------------------------------------------
# Default mode — coverage gaps
# ---------------------------------------------------------------------------

def _collect_coverage_gaps(source_root: Path) -> dict:
    """Return a CoverageReport-shaped dict using the coverage Python API."""
    try:
        import coverage as coverage_lib  # noqa: PLC0415
    except ImportError:
        _fatal("The 'coverage' package is required for default mode. Install it with: pip install coverage")

    cov = coverage_lib.Coverage()
    try:
        cov.load()
    except coverage_lib.exceptions.NoDataError:
        _fatal(
            "No .coverage data file found. Run 'pytest --cov=<source_root>' first, "
            "then re-run coverage-analyzer."
        )

    from schemas import CoverageGap, CoverageReport  # noqa: PLC0415  (relative import at runtime)

    gaps: list[CoverageGap] = []
    total_functions = 0

    for py_file in _iter_python_files(source_root):
        module_name = _path_to_module(py_file, source_root)

        try:
            source_text = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source_text, filename=str(py_file))
        except (SyntaxError, OSError):
            continue

        # Get line-level coverage for this file
        try:
            analysis = cov.analysis2(str(py_file))
            # analysis2 returns (filename, stmts, excluded, missing, missing_formatted)
            _, _, _, missing_lines_all, _ = analysis
            missing_set: set[int] = set(missing_lines_all)
            executed_set: set[int] = set()

            # Build executed lines from stmts - missing
            _, stmts, _, _, _ = analysis
            executed_set = set(stmts) - missing_set
        except Exception:  # noqa: BLE001
            # File not tracked by coverage — treat as 0 % covered
            missing_set = set()
            executed_set = set()

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            total_functions += 1
            func_start = node.lineno
            func_end = node.end_lineno or node.lineno

            # Lines belonging to this function
            func_lines = set(range(func_start, func_end + 1))
            func_missing = sorted(missing_set & func_lines)

            if not func_missing:
                continue

            func_stmts = func_lines & (executed_set | missing_set)
            if func_stmts:
                pct = 100.0 * len(func_stmts - missing_set) / len(func_stmts)
            else:
                pct = 100.0

            gaps.append(
                CoverageGap(
                    module=module_name,
                    function_name=node.name,
                    line_start=func_start,
                    line_end=func_end,
                    coverage_pct=round(pct, 2),
                    missing_lines=func_missing,
                    is_boundary=_is_boundary(node),
                )
            )

    report = CoverageReport(
        source_root=str(source_root.resolve()),
        gaps=sorted(gaps, key=lambda g: (g.module, g.line_start)),
        total_functions=total_functions,
        functions_with_gaps=len(gaps),
        report_timestamp=datetime.now(tz=timezone.utc),
    )
    return report.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Edge mode — cross-package call-graph
# ---------------------------------------------------------------------------

class _EdgeCollector(ast.NodeVisitor):
    """AST visitor that collects cross-package call-graph edges for one module."""

    def __init__(self, caller_module: str, import_map: dict[str, str]) -> None:
        self.caller_module = caller_module
        # import_map: local_name -> dotted_module
        self.import_map = import_map
        self.edges: list[dict] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        callee_module = self._resolve_callee(node.func)
        if callee_module and self._is_cross_package(self.caller_module, callee_module):
            self.edges.append(
                {
                    "caller_module": self.caller_module,
                    "callee_module": callee_module,
                    "call_site_line": node.lineno,
                }
            )
        self.generic_visit(node)

    # ------------------------------------------------------------------
    def _resolve_callee(self, node: ast.expr) -> str | None:
        """Best-effort resolution of a call target to a dotted module name."""
        if isinstance(node, ast.Name):
            return self.import_map.get(node.id)
        if isinstance(node, ast.Attribute):
            root = self._resolve_callee(node.value)
            return root  # attribute call — attribute on the imported module
        return None

    @staticmethod
    def _is_cross_package(caller: str, callee: str) -> bool:
        return caller.split(".")[0] != callee.split(".")[0]


def _build_import_map(tree: ast.Module) -> dict[str, str]:
    """
    Build a mapping from local names to dotted module paths for all imports
    at the top level of *tree*.

    ``import foo.bar`` → {"foo": "foo", "bar": "foo.bar"} (both roots mapped)
    ``from foo.bar import baz`` → {"baz": "foo.bar"}
    ``import foo.bar as fb`` → {"fb": "foo.bar"}
    """
    mapping: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                local = alias.asname if alias.asname else mod.split(".")[0]
                mapping[local] = mod
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for alias in node.names:
                    local = alias.asname if alias.asname else alias.name
                    mapping[local] = node.module
    return mapping


def _collect_edges(source_root: Path, test_suite_path: str, baseline_path: Path | None, sha: str | None) -> dict:
    """Return an EdgeCoverageReport-shaped dict using stdlib AST only."""
    from schemas import Edge, EdgeCoverageReport  # noqa: PLC0415

    all_edges: list[Edge] = []
    seen: set[tuple[str, str]] = set()

    for py_file in _iter_python_files(source_root):
        caller_module = _path_to_module(py_file, source_root)
        try:
            source_text = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source_text, filename=str(py_file))
        except (SyntaxError, OSError):
            continue

        import_map = _build_import_map(tree)
        collector = _EdgeCollector(caller_module, import_map)
        collector.visit(tree)

        for raw in collector.edges:
            key = (raw["caller_module"], raw["callee_module"])
            if key not in seen:
                seen.add(key)
            all_edges.append(Edge(**raw))

    # Deduplicate by (caller, callee) keeping first occurrence
    deduped: list[Edge] = []
    dedup_seen: set[tuple[str, str]] = set()
    for edge in all_edges:
        k = (edge.caller_module, edge.callee_module)
        if k not in dedup_seen:
            dedup_seen.add(k)
            deduped.append(edge)

    # Compute new_edges vs baseline
    new_edges: list[Edge] = []
    if baseline_path is not None:
        try:
            baseline_data = json.loads(baseline_path.read_text(encoding="utf-8"))
            baseline_pairs: set[tuple[str, str]] = {
                (e["caller_module"], e["callee_module"])
                for e in baseline_data.get("edges", [])
            }
            new_edges = [e for e in deduped if (e.caller_module, e.callee_module) not in baseline_pairs]
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            _warn(f"Could not load baseline snapshot from '{baseline_path}': {exc}. Treating all edges as new.")
            new_edges = list(deduped)
    # If no baseline, new_edges stays empty per spec

    report = EdgeCoverageReport(
        commit_sha=sha,
        test_suite_path=test_suite_path,
        edges=deduped,
        new_edges=new_edges,
        snapshot_timestamp=datetime.now(tz=timezone.utc),
    )
    return report.model_dump(mode="json")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _fatal(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def _warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coverage-analyzer",
        description=(
            "Compute per-function coverage gaps (default) or cross-package call-graph "
            "edges (--edges) from a test suite. Output is JSON written to stdout."
        ),
    )
    parser.add_argument(
        "source_root",
        help="Path to the source root directory to analyse.",
    )
    parser.add_argument(
        "--edges",
        action="store_true",
        default=False,
        help=(
            "Enable edge mode: perform static AST walk to build a cross-package "
            "call-graph rather than computing coverage gaps."
        ),
    )
    parser.add_argument(
        "--test-path",
        dest="test_path",
        default=None,
        help="[--edges] Path to the test suite directory or file (recorded in the report).",
    )
    parser.add_argument(
        "--baseline",
        dest="baseline",
        default=None,
        metavar="PATH",
        help=(
            "[--edges] Path to a prior EdgeCoverageReport JSON snapshot. "
            "When provided, new_edges is computed as the diff against this baseline."
        ),
    )
    parser.add_argument(
        "--sha",
        dest="sha",
        default=None,
        metavar="SHA",
        help="[--edges] Git commit SHA to embed in the EdgeCoverageReport.",
    )
    return parser


def main() -> None:
    """Entry point for the coverage-analyzer tool."""
    parser = _build_parser()
    args = parser.parse_args()

    source_root = Path(args.source_root)
    if not source_root.is_dir():
        _fatal(f"source_root '{source_root}' is not a directory or does not exist.")

    # Ensure schemas module is importable from this tool's directory
    import importlib.util  # noqa: PLC0415
    import sys as _sys  # noqa: PLC0415

    tool_dir = Path(__file__).parent
    if str(tool_dir) not in _sys.path:
        _sys.path.insert(0, str(tool_dir))

    if args.edges:
        baseline_path = Path(args.baseline) if args.baseline else None
        if baseline_path is not None and not baseline_path.is_file():
            _fatal(f"--baseline '{baseline_path}' is not a file or does not exist.")
        test_suite_path = args.test_path or str(source_root)
        result = _collect_edges(source_root, test_suite_path, baseline_path, args.sha)
    else:
        result = _collect_coverage_gaps(source_root)

    print(json.dumps(result, indent=2, default=str))
    sys.exit(0)


if __name__ == "__main__":
    main()
