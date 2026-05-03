# @summary
# CLI tool: computes per-function coverage gaps (default) or cross-package call graph edges (--edges).
# Exports: main
# Deps: coverage, ast, argparse, pydantic, schemas
# @end-summary

"""coverage-analyzer — two-mode test coverage tool.

Default mode: reads a .coverage data file and reports per-function gaps.
--edges mode:  walks the source AST to find cross-package call graph edges,
               optionally diffing against a baseline EdgeCoverageReport.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# Boundary detection helpers
# ---------------------------------------------------------------------------

_BOUNDARY_DECORATORS = {
    "route", "get", "post", "put", "patch", "delete",  # Flask/FastAPI/APIRouter
    "activity", "defn",                                  # Temporal
    "command", "group",                                  # Click
    "task",                                              # Celery
}

_BOUNDARY_READS = {"request", "os", "sys"}


def _is_boundary(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for dec in func_node.decorator_list:
        name = ""
        if isinstance(dec, ast.Name):
            name = dec.id
        elif isinstance(dec, ast.Attribute):
            name = dec.attr
        elif isinstance(dec, ast.Call):
            inner = dec.func
            if isinstance(inner, ast.Name):
                name = inner.id
            elif isinstance(inner, ast.Attribute):
                name = inner.attr
        if name.lower() in _BOUNDARY_DECORATORS:
            return True

    # Check if function body reads request / os.environ / sys.stdin
    for node in ast.walk(func_node):
        if isinstance(node, ast.Name) and node.id in _BOUNDARY_READS:
            return True
        if isinstance(node, ast.Attribute) and node.attr in {"environ", "stdin"}:
            return True
    return False


# ---------------------------------------------------------------------------
# Default mode: per-function coverage gaps
# ---------------------------------------------------------------------------

def _run_default(source_root: Path) -> None:
    try:
        import coverage as coverage_lib  # type: ignore[import]
    except ImportError:
        sys.stderr.write("coverage package not installed; run: pip install coverage\n")
        sys.exit(2)

    from schemas import CoverageGap, CoverageReport  # type: ignore[import]

    cov = coverage_lib.Coverage()
    try:
        cov.load()
    except coverage_lib.exceptions.NoDataError:
        sys.stderr.write("No .coverage data file found. Run pytest --cov first.\n")
        sys.exit(2)

    gaps: list[CoverageGap] = []
    total_functions = 0

    for py_file in sorted(source_root.rglob("*.py")):
        rel = py_file.relative_to(source_root)
        module = str(rel.with_suffix("")).replace("/", ".").replace("\\", ".")

        try:
            source_text = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source_text, filename=str(py_file))
        except (SyntaxError, OSError):
            continue

        try:
            _, executable, _, missing, _ = cov.analysis2(str(py_file))
        except Exception:
            continue

        missing_set = set(missing)

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            total_functions += 1
            func_lines = range(node.lineno, (node.end_lineno or node.lineno) + 1)
            func_missing = [ln for ln in func_lines if ln in missing_set]
            covered = len([ln for ln in func_lines if ln in set(executable)])
            total_exec = len([ln for ln in func_lines if ln in set(executable)]) + len(func_missing)
            pct = (covered / total_exec * 100.0) if total_exec > 0 else 100.0

            if func_missing:
                gaps.append(CoverageGap(
                    module=module,
                    function_name=node.name,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    coverage_pct=round(pct, 2),
                    missing_lines=func_missing,
                    is_boundary=_is_boundary(node),
                ))

    report = CoverageReport(
        source_root=str(source_root),
        gaps=gaps,
        total_functions=total_functions,
        functions_with_gaps=len(gaps),
        report_timestamp=_utcnow(),
    )
    print(report.model_dump_json(indent=2))


# ---------------------------------------------------------------------------
# --edges mode: static AST cross-package edge walk
# ---------------------------------------------------------------------------

def _module_from_path(path: Path, source_root: Path) -> str:
    rel = path.relative_to(source_root)
    return str(rel.with_suffix("")).replace("/", ".").replace("\\", ".")


def _build_import_map(tree: ast.Module, caller_module: str) -> dict[str, str]:
    """Return {local_name: dotted_module} for all imports in a module."""
    mapping: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".")[0]
                mapping[local] = alias.name
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level and node.level > 0:
                # Relative import — resolve against caller package
                parts = caller_module.split(".")
                base_parts = parts[: len(parts) - node.level]
                base = ".".join(base_parts) + ("." + base if base else "")
            for alias in node.names:
                local = alias.asname or alias.name
                mapping[local] = base + "." + alias.name if base else alias.name
    return mapping


class _EdgeCollector(ast.NodeVisitor):
    def __init__(self, caller_module: str, import_map: dict[str, str]) -> None:
        self.caller_module = caller_module
        self.import_map = import_map
        self.edges: list[tuple[str, str, int | None]] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        callee_module: str | None = None
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                local_name = node.func.value.id
                callee_module = self.import_map.get(local_name)
        elif isinstance(node.func, ast.Name):
            callee_module = self.import_map.get(node.func.id)

        if callee_module:
            caller_pkg = self.caller_module.split(".")[0]
            callee_pkg = callee_module.split(".")[0]
            if caller_pkg != callee_pkg:
                self.edges.append((self.caller_module, callee_module, node.lineno))

        self.generic_visit(node)


def _run_edges(
    source_root: Path,
    test_suite_path: str,
    baseline_path: Path | None,
    sha: str | None,
) -> None:
    from schemas import Edge, EdgeCoverageReport  # type: ignore[import]

    all_edges: list[Edge] = []

    for py_file in sorted(source_root.rglob("*.py")):
        try:
            source_text = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source_text, filename=str(py_file))
        except (SyntaxError, OSError):
            continue

        caller_module = _module_from_path(py_file, source_root)
        import_map = _build_import_map(tree, caller_module)
        collector = _EdgeCollector(caller_module, import_map)
        collector.visit(tree)

        for caller, callee, line in collector.edges:
            all_edges.append(Edge(caller_module=caller, callee_module=callee, call_site_line=line))

    # Deduplicate by (caller, callee)
    seen: set[tuple[str, str]] = set()
    deduped: list[Edge] = []
    for e in all_edges:
        key = (e.caller_module, e.callee_module)
        if key not in seen:
            seen.add(key)
            deduped.append(e)

    # Compute new_edges against baseline
    new_edges: list[Edge] = []
    if baseline_path:
        try:
            baseline_data = json.loads(baseline_path.read_text(encoding="utf-8"))
            baseline_pairs = {
                (e["caller_module"], e["callee_module"])
                for e in baseline_data.get("edges", [])
            }
            new_edges = [e for e in deduped if (e.caller_module, e.callee_module) not in baseline_pairs]
        except Exception as exc:
            sys.stderr.write(f"Warning: could not load baseline ({exc}); new_edges will be empty\n")

    report = EdgeCoverageReport(
        commit_sha=sha,
        test_suite_path=test_suite_path,
        edges=deduped,
        new_edges=new_edges,
        snapshot_timestamp=_utcnow(),
    )
    print(report.model_dump_json(indent=2))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze test coverage gaps or cross-package call graph edges.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("source_root", help="Path to the Python source root to analyze")
    parser.add_argument(
        "--edges",
        action="store_true",
        help="Run in edge-coverage mode (static AST walk for cross-package calls)",
    )
    parser.add_argument(
        "--test-path",
        default="tests/",
        help="Test suite path (recorded in EdgeCoverageReport metadata; default: tests/)",
    )
    parser.add_argument(
        "--baseline",
        metavar="PATH",
        help="Path to a prior EdgeCoverageReport JSON for new-edge diffing (--edges mode only)",
    )
    parser.add_argument(
        "--sha",
        help="Git commit SHA to embed in EdgeCoverageReport (--edges mode only)",
    )

    args = parser.parse_args()
    source_root = Path(args.source_root).resolve()

    if not source_root.is_dir():
        sys.stderr.write(f"source_root not found or not a directory: {source_root}\n")
        sys.exit(2)

    # Add tool directory to path so 'from schemas import ...' resolves
    sys.path.insert(0, str(Path(__file__).parent))

    if args.edges:
        baseline = Path(args.baseline).resolve() if args.baseline else None
        _run_edges(source_root, args.test_path, baseline, args.sha)
    else:
        _run_default(source_root)


if __name__ == "__main__":
    main()
