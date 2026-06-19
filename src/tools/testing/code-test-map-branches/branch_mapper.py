# @summary
# CLI entry point for the branch-mapper tool. Walks a source tree, enumerates
# every executable branch reachable from each public function (including
# branches in same-module private helpers it transitively calls), and emits
# a BranchMap JSON document on stdout.
# Exports: main, build_branch_map, collect_branches_for_function
# Deps: ast, argparse, pydantic, schemas
# @end-summary

"""branch-mapper — enumerate per-function executable branches.

Usage::

    python -m src.tools.testing.branch_mapper <source_root> \\
        [--module DOTTED] [--function NAME] [--include-private]

The tool is informational and always exits 0 unless invoked with bad CLI
arguments. It emits a :class:`schemas.BranchMap` JSON document on stdout.

Branch detection rules
----------------------
``If``       -> emits one ``if`` branch plus one ``elif`` per chained
               ``elif`` and one ``else`` if an else clause exists.
``Try``      -> emits one ``try`` branch plus one ``except`` per handler
               and one ``finally`` if a finalbody exists.
``For``,
``AsyncFor`` -> emits one ``for`` branch.
``While``    -> emits one ``while`` branch.
``IfExp``    -> emits one ``ternary`` branch.
``BoolOp``   -> emits one ``and`` / ``or`` branch per operand after the
               first (each short-circuit decision point is a branch).

Only same-module private helpers (functions whose name starts with ``_``)
are descended into. A visited-set guards against recursive call cycles.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Support both package import and ``python branch_mapper.py``
# (the hyphenated tool directory cannot be imported as a package).
try:  # pragma: no cover - import shim
    from .schemas import Branch, BranchMap, BranchType, FunctionBranchMap
except ImportError:  # pragma: no cover - import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from schemas import (  # type: ignore[no-redef]
        Branch,
        BranchMap,
        BranchType,
        FunctionBranchMap,
    )


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _unparse(node: ast.AST | None) -> str | None:
    """Return source text for ``node`` using ``ast.unparse`` when available."""
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - defensive fallback
        return ast.dump(node)


def _node_end_line(node: ast.AST, default: int) -> int:
    """Return ``end_lineno`` of ``node`` or ``default`` when unavailable."""
    return getattr(node, "end_lineno", None) or default


def _module_name_for_path(path: Path, source_root: Path) -> str:
    """Convert a ``.py`` file path to a dotted module name relative to root."""
    rel = path.resolve().relative_to(source_root.resolve())
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else rel.stem


# ---------------------------------------------------------------------------
# Branch extraction
# ---------------------------------------------------------------------------


FuncDef = ast.FunctionDef | ast.AsyncFunctionDef


def _extract_branches_from_node(
    node: ast.AST, in_function: str, out: list[Branch]
) -> None:
    """Walk ``node`` and append every detected branch to ``out``.

    The traversal is iterative-via-recursion: we inspect ``node`` itself and
    then recurse into its children. We do not stop at nested function or
    class definitions for branch extraction within the *current* function;
    however, the top-level caller passes the function body (not its def), so
    we must skip nested ``FunctionDef``/``AsyncFunctionDef``/``ClassDef``
    bodies which represent separate scopes.
    """

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        # Different scope; do not pull its branches into the parent function.
        return

    if isinstance(node, ast.If):
        # ``if`` itself.
        out.append(
            Branch(
                branch_type="if",
                line=node.lineno,
                end_line=_node_end_line(node, node.lineno),
                condition=_unparse(node.test),
                in_function=in_function,
            )
        )
        # Boolean short-circuits inside the test are themselves branches.
        _extract_branches_from_node(node.test, in_function, out)
        # Walk the ``if`` body.
        for child in node.body:
            _extract_branches_from_node(child, in_function, out)

        # An ``elif`` is an ``If`` nested as the sole orelse element.
        orelse = node.orelse
        while (
            len(orelse) == 1
            and isinstance(orelse[0], ast.If)
        ):
            elif_node = orelse[0]
            out.append(
                Branch(
                    branch_type="elif",
                    line=elif_node.lineno,
                    end_line=_node_end_line(elif_node, elif_node.lineno),
                    condition=_unparse(elif_node.test),
                    in_function=in_function,
                )
            )
            _extract_branches_from_node(elif_node.test, in_function, out)
            for child in elif_node.body:
                _extract_branches_from_node(child, in_function, out)
            orelse = elif_node.orelse

        if orelse:
            first = orelse[0]
            last = orelse[-1]
            out.append(
                Branch(
                    branch_type="else",
                    line=first.lineno,
                    end_line=_node_end_line(last, first.lineno),
                    condition=None,
                    in_function=in_function,
                )
            )
            for child in orelse:
                _extract_branches_from_node(child, in_function, out)
        return

    if isinstance(node, ast.Try):
        try_first = node.body[0] if node.body else node
        try_last = node.body[-1] if node.body else node
        out.append(
            Branch(
                branch_type="try",
                line=try_first.lineno,
                end_line=_node_end_line(try_last, try_first.lineno),
                condition=None,
                in_function=in_function,
            )
        )
        for child in node.body:
            _extract_branches_from_node(child, in_function, out)

        for handler in node.handlers:
            condition = _unparse(handler.type) if handler.type is not None else None
            out.append(
                Branch(
                    branch_type="except",
                    line=handler.lineno,
                    end_line=_node_end_line(handler, handler.lineno),
                    condition=condition,
                    in_function=in_function,
                )
            )
            for child in handler.body:
                _extract_branches_from_node(child, in_function, out)

        if node.orelse:
            # ``try/else`` runs when no exception fired; treat as an else.
            first = node.orelse[0]
            last = node.orelse[-1]
            out.append(
                Branch(
                    branch_type="else",
                    line=first.lineno,
                    end_line=_node_end_line(last, first.lineno),
                    condition=None,
                    in_function=in_function,
                )
            )
            for child in node.orelse:
                _extract_branches_from_node(child, in_function, out)

        if node.finalbody:
            first = node.finalbody[0]
            last = node.finalbody[-1]
            out.append(
                Branch(
                    branch_type="finally",
                    line=first.lineno,
                    end_line=_node_end_line(last, first.lineno),
                    condition=None,
                    in_function=in_function,
                )
            )
            for child in node.finalbody:
                _extract_branches_from_node(child, in_function, out)
        return

    if isinstance(node, (ast.For, ast.AsyncFor)):
        out.append(
            Branch(
                branch_type="for",
                line=node.lineno,
                end_line=_node_end_line(node, node.lineno),
                condition=_unparse(node.iter),
                in_function=in_function,
            )
        )
        for child in ast.iter_child_nodes(node):
            _extract_branches_from_node(child, in_function, out)
        return

    if isinstance(node, ast.While):
        out.append(
            Branch(
                branch_type="while",
                line=node.lineno,
                end_line=_node_end_line(node, node.lineno),
                condition=_unparse(node.test),
                in_function=in_function,
            )
        )
        for child in ast.iter_child_nodes(node):
            _extract_branches_from_node(child, in_function, out)
        return

    if isinstance(node, ast.IfExp):
        out.append(
            Branch(
                branch_type="ternary",
                line=node.lineno,
                end_line=_node_end_line(node, node.lineno),
                condition=_unparse(node.test),
                in_function=in_function,
            )
        )
        for child in ast.iter_child_nodes(node):
            _extract_branches_from_node(child, in_function, out)
        return

    if isinstance(node, ast.BoolOp):
        op_type: BranchType = "and" if isinstance(node.op, ast.And) else "or"
        # Each operand after the first is a short-circuit decision point.
        for operand in node.values[1:]:
            out.append(
                Branch(
                    branch_type=op_type,
                    line=getattr(operand, "lineno", node.lineno),
                    end_line=_node_end_line(operand, node.lineno),
                    condition=_unparse(operand),
                    in_function=in_function,
                )
            )
        for child in ast.iter_child_nodes(node):
            _extract_branches_from_node(child, in_function, out)
        return

    # Default: descend into children.
    for child in ast.iter_child_nodes(node):
        _extract_branches_from_node(child, in_function, out)


def _called_helper_names(func: FuncDef) -> list[str]:
    """Return names of bare-name function calls inside ``func``'s body.

    Only ``Call`` nodes whose ``func`` is an ``ast.Name`` are considered;
    attribute calls (``self.foo()``, ``mod.bar()``) are skipped because
    cross-module / instance-method resolution is out of scope.
    Order is preserved; duplicates removed.
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for sub in ast.walk(func):
        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if sub is func:
                continue
            # Skip nested defs.
            continue
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
            name = sub.func.id
            if name not in seen:
                seen.add(name)
                ordered.append(name)
    return ordered


# ---------------------------------------------------------------------------
# Module-level analysis
# ---------------------------------------------------------------------------


def _collect_module_functions(tree: ast.Module) -> dict[str, FuncDef]:
    """Map top-level function name -> def node for a parsed module."""
    out: dict[str, FuncDef] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = node
    return out


def _module_all(tree: ast.Module) -> set[str] | None:
    """Return the set of names in ``__all__`` if defined, else ``None``."""
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
        ):
            continue
        value = node.value
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            names: set[str] = set()
            for elt in value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    names.add(elt.value)
            return names
    return None


def _is_public(name: str, all_names: set[str] | None) -> bool:
    """Apply the public-function rule from the schema."""
    if name.startswith("_"):
        return False
    if all_names is None:
        return True
    return name in all_names


def collect_branches_for_function(
    func: FuncDef,
    module_name: str,
    module_funcs: dict[str, FuncDef],
) -> tuple[list[Branch], list[str]]:
    """Collect branches reachable from ``func``, descending into helpers.

    Same-module private helpers (names starting with ``_``) called by name
    inside ``func`` are inlined transitively. A visited set guards cycles.
    """
    branches: list[Branch] = []
    visited_helpers: set[str] = set()
    ordered_helpers: list[str] = []

    qualified = f"{module_name}.{func.name}"
    for stmt in func.body:
        _extract_branches_from_node(stmt, qualified, branches)

    # BFS through helper calls.
    queue: list[tuple[FuncDef, str]] = [(func, qualified)]
    while queue:
        current, current_qualified = queue.pop(0)
        for callee_name in _called_helper_names(current):
            if not callee_name.startswith("_"):
                continue
            if callee_name not in module_funcs:
                # Not defined in this module — skip.
                continue
            if callee_name in visited_helpers:
                continue
            visited_helpers.add(callee_name)
            helper = module_funcs[callee_name]
            helper_qualified = f"{current_qualified}.{callee_name}"
            ordered_helpers.append(helper_qualified)
            for stmt in helper.body:
                _extract_branches_from_node(stmt, helper_qualified, branches)
            queue.append((helper, helper_qualified))

    return branches, ordered_helpers


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def build_branch_map(
    source_root: Path,
    module_filter: str | None = None,
    function_filter: str | None = None,
    include_private: bool = False,
) -> BranchMap:
    """Build a :class:`BranchMap` for ``source_root``."""
    functions: list[FunctionBranchMap] = []

    for path in _iter_python_files(source_root):
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue

        module_name = _module_name_for_path(path, source_root)
        if module_filter is not None and module_name != module_filter:
            continue

        all_names = _module_all(tree)
        module_funcs = _collect_module_functions(tree)

        for name, func in module_funcs.items():
            if function_filter is not None and name != function_filter:
                continue
            is_public = _is_public(name, all_names)
            if not include_private and not is_public:
                continue
            branches, helpers = collect_branches_for_function(
                func, module_name, module_funcs
            )
            functions.append(
                FunctionBranchMap(
                    module=module_name,
                    function_name=name,
                    line_start=func.lineno,
                    line_end=_node_end_line(func, func.lineno),
                    is_public=is_public,
                    branches=branches,
                    transitive_helpers=helpers,
                    total_branch_count=len(branches),
                )
            )

    return BranchMap(
        source_root=str(source_root),
        functions=functions,
        timestamp=datetime.now(timezone.utc),
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="branch-mapper",
        description=(
            "Enumerate per-function executable branches (including transitive "
            "private helpers in the same module) for a Python source tree."
        ),
    )
    parser.add_argument("source_root", help="Path to the source tree to analyze.")
    parser.add_argument(
        "--module",
        dest="module",
        default=None,
        help="Restrict analysis to this dotted module path (relative to source_root).",
    )
    parser.add_argument(
        "--function",
        dest="function",
        default=None,
        help="Restrict analysis to functions with this name.",
    )
    parser.add_argument(
        "--include-private",
        dest="include_private",
        action="store_true",
        help="Include private (underscore-prefixed) functions as top-level entries.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    source_root = Path(args.source_root)
    if not source_root.exists() or not source_root.is_dir():
        # Informational tool: emit empty map rather than failing.
        empty = BranchMap(
            source_root=str(source_root),
            functions=[],
            timestamp=datetime.now(timezone.utc),
        )
        print(json.dumps(empty.model_dump(mode="json"), indent=2))
        return 0

    branch_map = build_branch_map(
        source_root=source_root,
        module_filter=args.module,
        function_filter=args.function,
        include_private=args.include_private,
    )
    print(json.dumps(branch_map.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
