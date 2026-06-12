# @summary
# Walks a source tree, parses every .py file with stdlib `ast`, and classifies
# each function as a runtime-exposed boundary or internal helper. Detection
# priority is strict: decorator > body-scan > export. First match wins.
# Exports: classify_source_root, main
# Deps: ast, pydantic, .schemas
# @end-summary

"""Boundary classifier CLI.

Usage::

    python -m src.tools.testing.boundary_classifier <source_root> [--include-internals]

Emits a JSON `BoundaryClassification` to stdout. Exit code 0 always (the tool is
informational; downstream consumers decide how to act on counts/empties).

Detection rules (first match wins):

1. **Decorator-based** -- inspected by the right-hand attribute of the decorator
   so that `@app.route`, `@bp.route`, `@router.get`, etc. all match uniformly.
   The matched decorator's full source (`ast.unparse`) is recorded.
2. **Body-scan** -- only consulted when no decorator matched. Detects reads of
   `os.environ` / `os.getenv` (env_reader) and `sys.stdin` / `sys.argv`
   (stdin_reader).
3. **Export-based** -- function name is in the module's static `__all__` and is
   not `_private`.

If none of the above fire the function is classified as `InternalFunction`.
"""

from __future__ import annotations

import argparse
import ast
import sys
from datetime import datetime, timezone
from pathlib import Path

# Support both package import and ``python boundary_classifier.py``
# (the hyphenated tool directory cannot be imported as a package).
try:  # pragma: no cover - import shim
    from .schemas import (
        BoundaryClassification,
        BoundaryFunction,
        BoundaryType,
        InternalFunction,
    )
except ImportError:  # pragma: no cover - import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from schemas import (  # type: ignore[no-redef]
        BoundaryClassification,
        BoundaryFunction,
        BoundaryType,
        InternalFunction,
    )

# ---------------------------------------------------------------------------
# Decorator -> boundary_type lookup tables.
# Match on the *attribute* name (right-hand side of the dotted decorator) so
# this stays project-agnostic regardless of which object name is used.
# ---------------------------------------------------------------------------

_HTTP_ROUTE_ATTRS: frozenset[str] = frozenset(
    {"route", "get", "post", "put", "patch", "delete", "head", "options"}
)
_TEMPORAL_ACTIVITY_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {("activity", "defn")}
)
_TEMPORAL_WORKFLOW_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {("workflow", "defn")}
)
_CLI_COMMAND_ATTRS: frozenset[str] = frozenset({"command", "group"})
# For Celery: either `@celery.task` / `@app.task` (attribute form) or the
# bare-name `@shared_task` decorator.
_CELERY_TASK_ATTRS: frozenset[str] = frozenset({"task"})
_CELERY_TASK_BARE_NAMES: frozenset[str] = frozenset({"shared_task"})


# ---------------------------------------------------------------------------
# Module discovery
# ---------------------------------------------------------------------------


def _iter_py_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def _module_name(root: Path, path: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else path.stem


# ---------------------------------------------------------------------------
# `__all__` extraction
# ---------------------------------------------------------------------------


def _extract_all(tree: ast.Module) -> tuple[set[str], bool]:
    """Return (names_in_all, has_all).

    Tolerates dynamic construction by skipping non-literal forms. Only
    list/tuple/set of string constants is recognised.
    """

    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
            value = node.value
        else:
            continue
        for tgt in targets:
            if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
                    names: set[str] = set()
                    for elt in value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            names.add(elt.value)
                    return names, True
                # Dynamic construction -> tolerate by treating as absent.
                return set(), True
    return set(), False


# ---------------------------------------------------------------------------
# Decorator inspection helpers
# ---------------------------------------------------------------------------


def _decorator_callable(dec: ast.expr) -> ast.expr:
    """Strip a Call wrapper to inspect the underlying callable expression."""

    return dec.func if isinstance(dec, ast.Call) else dec


def _attr_pair(expr: ast.expr) -> tuple[str | None, str | None]:
    """Return (left_name, right_attr) for `Name.attr` decorators, else (None, None)."""

    if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
        return expr.value.id, expr.attr
    return None, None


def _classify_decorator(dec: ast.expr) -> tuple[BoundaryType, str] | None:
    """Return (boundary_type, reason) if the decorator marks a boundary."""

    callable_expr = _decorator_callable(dec)
    left, right = _attr_pair(callable_expr)

    # Bare-name decorators, e.g. `@shared_task`.
    if isinstance(callable_expr, ast.Name):
        if callable_expr.id in _CELERY_TASK_BARE_NAMES:
            return "celery_task", f"bare decorator @{callable_expr.id}"
        return None

    if left is None or right is None:
        return None

    if (left, right) in _TEMPORAL_ACTIVITY_PAIRS:
        return "temporal_activity", f"decorator matches @{left}.{right}"
    if (left, right) in _TEMPORAL_WORKFLOW_PAIRS:
        return "temporal_workflow", f"decorator matches @{left}.{right}"
    if right in _HTTP_ROUTE_ATTRS:
        return "http_route", f"decorator attribute '.{right}' matches HTTP verb/route"
    if right in _CLI_COMMAND_ATTRS:
        return "cli_command", f"decorator attribute '.{right}' matches Click command/group"
    if right in _CELERY_TASK_ATTRS:
        return "celery_task", f"decorator attribute '.{right}' matches Celery task"

    return None


# ---------------------------------------------------------------------------
# Body-scan helpers
# ---------------------------------------------------------------------------


class _BodyScanner(ast.NodeVisitor):
    """Detect env/stdin reads in a function body."""

    def __init__(self) -> None:
        self.reads_env = False
        self.reads_stdin = False

    def visit_Subscript(self, node: ast.Subscript) -> None:  # noqa: N802
        # `os.environ[...]`
        if (
            isinstance(node.value, ast.Attribute)
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id == "os"
            and node.value.attr == "environ"
        ):
            self.reads_env = True
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:  # noqa: N802
        # `sys.argv` (any access counts), `sys.stdin` (without method call)
        if isinstance(node.value, ast.Name) and node.value.id == "sys":
            if node.attr == "argv":
                self.reads_stdin = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        func = node.func
        # `os.environ.get(...)` -> Attribute(Attribute(Name('os'),'environ'),'get')
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Attribute)
            and isinstance(func.value.value, ast.Name)
            and func.value.value.id == "os"
            and func.value.attr == "environ"
            and func.attr == "get"
        ):
            self.reads_env = True
        # `os.getenv(...)`
        elif (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "os"
            and func.attr == "getenv"
        ):
            self.reads_env = True
        # `sys.stdin.read(...)` / `sys.stdin.readline(...)`
        elif (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Attribute)
            and isinstance(func.value.value, ast.Name)
            and func.value.value.id == "sys"
            and func.value.attr == "stdin"
            and func.attr in {"read", "readline", "readlines"}
        ):
            self.reads_stdin = True
        self.generic_visit(node)


def _scan_body(func: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[BoundaryType, str] | None:
    scanner = _BodyScanner()
    for stmt in func.body:
        scanner.visit(stmt)
    if scanner.reads_env:
        return "env_reader", "body reads os.environ / os.getenv"
    if scanner.reads_stdin:
        return "stdin_reader", "body reads sys.stdin / sys.argv"
    return None


# ---------------------------------------------------------------------------
# Per-module classification
# ---------------------------------------------------------------------------


def _qualified(module: str, func_name: str) -> str:
    return f"{module}.{func_name}" if module else func_name


def _classify_function(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    module: str,
    all_names: set[str],
    has_all: bool,
) -> BoundaryFunction | InternalFunction:
    qname = _qualified(module, func.name)

    # 1. Decorator-based detection (highest priority).
    for dec in func.decorator_list:
        match = _classify_decorator(dec)
        if match is not None:
            btype, reason = match
            return BoundaryFunction(
                module=module,
                function_name=func.name,
                qualified_name=qname,
                line=func.lineno,
                boundary_type=btype,
                detection_reason=reason,
                decorator_source=ast.unparse(dec),
            )

    # 2. Body-scan detection.
    body_match = _scan_body(func)
    if body_match is not None:
        btype, reason = body_match
        return BoundaryFunction(
            module=module,
            function_name=func.name,
            qualified_name=qname,
            line=func.lineno,
            boundary_type=btype,
            detection_reason=reason,
            decorator_source=None,
        )

    # 3. Export-based detection.
    is_private = func.name.startswith("_")
    in_all = func.name in all_names
    if has_all and in_all and not is_private:
        return BoundaryFunction(
            module=module,
            function_name=func.name,
            qualified_name=qname,
            line=func.lineno,
            boundary_type="exported_public",
            detection_reason="listed in module __all__ and not a private name",
            decorator_source=None,
        )

    return InternalFunction(
        module=module,
        function_name=func.name,
        qualified_name=qname,
        line=func.lineno,
        is_private=is_private,
        in_all=in_all,
    )


def _iter_functions(
    tree: ast.Module,
) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Walk every function/method (including nested) in the module."""

    out: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(node)
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_source_root(
    source_root: str | Path, *, include_internals: bool = False
) -> BoundaryClassification:
    """Classify every function under `source_root`."""

    root = Path(source_root).resolve()
    boundaries: list[BoundaryFunction] = []
    internals: list[InternalFunction] = []
    total = 0
    internal_count = 0

    for path in _iter_py_files(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            # Skip files we can't parse; tool is informational.
            continue

        module = _module_name(root, path)
        all_names, has_all = _extract_all(tree)

        for func in _iter_functions(tree):
            total += 1
            result = _classify_function(
                func,
                module=module,
                all_names=all_names,
                has_all=has_all,
            )
            if isinstance(result, BoundaryFunction):
                boundaries.append(result)
            else:
                internal_count += 1
                if include_internals:
                    internals.append(result)

    return BoundaryClassification(
        source_root=str(root),
        boundaries=boundaries,
        internals=internals,
        total_functions=total,
        boundary_count=len(boundaries),
        internal_count=internal_count,
        timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="boundary-classifier",
        description=(
            "Classify every function in a source tree as boundary "
            "(runtime-exposed) or internal."
        ),
    )
    parser.add_argument("source_root", help="Path to the source tree to classify.")
    parser.add_argument(
        "--include-internals",
        action="store_true",
        help="Include the full list of internal functions in the output JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = classify_source_root(
        args.source_root, include_internals=args.include_internals
    )
    sys.stdout.write(report.model_dump_json(indent=2))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
