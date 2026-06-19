# @summary
# CLI for the hypothesis-strategy-generator tool. Walks .py files under a
# source root, extracts function signatures via ast, and emits Hypothesis
# @given decorator strings for each parameter based on its type hint.
# Exports: main, build_strategy_report, map_annotation_to_strategy
# Deps: pydantic, src.tools.testing.hypothesis-strategy-generator.schemas
# @end-summary

"""CLI entry point for the ``hypothesis-strategy-generator`` tool.

Usage::

    python -m src.tools.testing.hypothesis_strategy_generator <source_root> \\
        [--module DOTTED] [--function NAME] [--public-only]

The tool is informational: parse failures and unsupported types never abort
the run. Unsupported parameters are emitted as ``st.nothing()`` with a TODO
comment so callers can patch them by hand.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

# Support being run both as ``python -m src.tools.testing.hypothesis_strategy_generator``
# and directly from the package directory; the kebab-case parent makes a normal
# relative import impossible, so we re-resolve via the file's sibling.
try:  # pragma: no cover - import shim
    from .schemas import (  # type: ignore[import-not-found]
        FunctionStrategy,
        ParameterStrategy,
        StrategyReport,
    )
except ImportError:  # pragma: no cover - import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from schemas import (  # type: ignore[no-redef]
        FunctionStrategy,
        ParameterStrategy,
        StrategyReport,
    )


# ---------------------------------------------------------------------------
# Type-hint -> strategy mapping
# ---------------------------------------------------------------------------


_PRIMITIVE_STRATEGIES: dict[str, str] = {
    "int": "st.integers()",
    "str": "st.text()",
    "bool": "st.booleans()",
    "float": "st.floats(allow_nan=False, allow_infinity=False)",
    "bytes": "st.binary()",
    "None": "st.none()",
    "NoneType": "st.none()",
}

# Names from the standard library that, when used as the *strategy* for a
# parameter, also require a runtime import in the generated test file.
_STDLIB_TYPE_IMPORTS: dict[str, str] = {
    "datetime": "from datetime import datetime",
    "date": "from datetime import date",
    "time": "from datetime import time",
    "timedelta": "from datetime import timedelta",
    "Decimal": "from decimal import Decimal",
    "UUID": "from uuid import UUID",
}

_STDLIB_TYPE_STRATEGIES: dict[str, str] = {
    "datetime": "st.datetimes()",
    "date": "st.dates()",
    "time": "st.times()",
    "timedelta": "st.timedeltas()",
    "Decimal": "st.decimals(allow_nan=False, allow_infinity=False)",
    "UUID": "st.uuids()",
}


@dataclass
class _MappingResult:
    """Internal mapping return value tracking both code and side-effect imports."""

    code: str
    is_supported: bool
    fallback_reason: str | None = None
    extra_imports: set[str] = field(default_factory=set)


def _annotation_name(node: ast.AST) -> str | None:
    """Return the leaf name of a simple ``ast.Name``/``ast.Attribute`` node."""

    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_none_constant(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def map_annotation_to_strategy(node: ast.AST) -> _MappingResult:
    """Map a single annotation AST node to a Hypothesis strategy expression.

    Unknown annotations return a non-supported result with a fallback to
    ``st.nothing()`` so the caller can patch the generated decorator by hand.
    """

    # ``None`` literal annotation
    if _is_none_constant(node):
        return _MappingResult(code="st.none()", is_supported=True)

    # Bare names: int, str, datetime, MyEnum, MyModel, ...
    if isinstance(node, ast.Name) or isinstance(node, ast.Attribute):
        name = _annotation_name(node)
        if name is None:
            return _MappingResult(
                code="st.nothing()  # TODO: unsupported",
                is_supported=False,
                fallback_reason="Could not resolve annotation name.",
            )
        if name in _PRIMITIVE_STRATEGIES:
            return _MappingResult(code=_PRIMITIVE_STRATEGIES[name], is_supported=True)
        if name in _STDLIB_TYPE_STRATEGIES:
            extras: set[str] = set()
            if name in _STDLIB_TYPE_IMPORTS:
                extras.add(_STDLIB_TYPE_IMPORTS[name])
            return _MappingResult(
                code=_STDLIB_TYPE_STRATEGIES[name],
                is_supported=True,
                extra_imports=extras,
            )
        # Unknown bare name (could be Enum, BaseModel, dataclass, ...). The
        # AST layer cannot tell — flag as unsupported and let the caller wire
        # up ``st.sampled_from`` / ``st.builds`` by hand.
        return _MappingResult(
            code="st.nothing()  # TODO: unsupported",
            is_supported=False,
            fallback_reason=(
                f"Bare type {name!r} could not be resolved at AST time. "
                "If it is an Enum subclass use st.sampled_from(list(...)); "
                "if a pydantic BaseModel subclass use st.builds(...)."
            ),
        )

    # PEP 604 unions: A | B | None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _map_union([node.left, node.right])

    # Subscripted generics: list[int], Optional[str], Literal["a", "b"], ...
    if isinstance(node, ast.Subscript):
        return _map_subscript(node)

    return _MappingResult(
        code="st.nothing()  # TODO: unsupported",
        is_supported=False,
        fallback_reason=f"Unrecognised annotation node type {type(node).__name__}.",
    )


def _map_subscript(node: ast.Subscript) -> _MappingResult:
    container = _annotation_name(node.value)
    slice_node = node.slice
    # Python 3.9+ exposes the slice node directly (not wrapped in ast.Index).
    elements = (
        list(slice_node.elts)
        if isinstance(slice_node, ast.Tuple)
        else [slice_node]
    )

    if container in {"Optional"}:
        if not elements:
            return _MappingResult(
                code="st.nothing()  # TODO: unsupported",
                is_supported=False,
                fallback_reason="Optional[...] with no inner type.",
            )
        return _map_union([elements[0], ast.Constant(value=None)])

    if container in {"Union"}:
        return _map_union(elements)

    if container in {"Literal"}:
        # Each element should be a constant; render its source via ast.unparse.
        rendered = ", ".join(ast.unparse(elem) for elem in elements)
        return _MappingResult(
            code=f"st.sampled_from([{rendered}])",
            is_supported=True,
        )

    if container in {"list", "List"}:
        inner = map_annotation_to_strategy(elements[0]) if elements else _MappingResult(
            code="st.nothing()", is_supported=False, fallback_reason="list with no inner type."
        )
        return _MappingResult(
            code=f"st.lists({inner.code})",
            is_supported=inner.is_supported,
            fallback_reason=inner.fallback_reason,
            extra_imports=inner.extra_imports,
        )

    if container in {"set", "Set", "frozenset", "FrozenSet"}:
        inner = map_annotation_to_strategy(elements[0]) if elements else _MappingResult(
            code="st.nothing()", is_supported=False, fallback_reason="set with no inner type."
        )
        wrapper = "st.frozensets" if container in {"frozenset", "FrozenSet"} else "st.sets"
        return _MappingResult(
            code=f"{wrapper}({inner.code})",
            is_supported=inner.is_supported,
            fallback_reason=inner.fallback_reason,
            extra_imports=inner.extra_imports,
        )

    if container in {"tuple", "Tuple"}:
        if (
            len(elements) == 2
            and isinstance(elements[1], ast.Constant)
            and elements[1].value is Ellipsis
        ):
            inner = map_annotation_to_strategy(elements[0])
            return _MappingResult(
                code=f"st.lists({inner.code}).map(tuple)",
                is_supported=inner.is_supported,
                fallback_reason=inner.fallback_reason,
                extra_imports=inner.extra_imports,
            )
        inner_results = [map_annotation_to_strategy(elem) for elem in elements]
        codes = ", ".join(r.code for r in inner_results)
        extras: set[str] = set()
        for r in inner_results:
            extras.update(r.extra_imports)
        all_ok = all(r.is_supported for r in inner_results)
        first_reason = next(
            (r.fallback_reason for r in inner_results if r.fallback_reason), None
        )
        return _MappingResult(
            code=f"st.tuples({codes})",
            is_supported=all_ok,
            fallback_reason=first_reason,
            extra_imports=extras,
        )

    if container in {"dict", "Dict"}:
        if len(elements) < 2:
            return _MappingResult(
                code="st.nothing()  # TODO: unsupported",
                is_supported=False,
                fallback_reason="dict[...] requires both key and value types.",
            )
        key = map_annotation_to_strategy(elements[0])
        value = map_annotation_to_strategy(elements[1])
        extras = key.extra_imports | value.extra_imports
        return _MappingResult(
            code=f"st.dictionaries({key.code}, {value.code})",
            is_supported=key.is_supported and value.is_supported,
            fallback_reason=key.fallback_reason or value.fallback_reason,
            extra_imports=extras,
        )

    return _MappingResult(
        code="st.nothing()  # TODO: unsupported",
        is_supported=False,
        fallback_reason=(
            f"Unsupported generic container {container!r}. "
            "Only list/tuple/set/frozenset/dict/Optional/Union/Literal are mapped."
        ),
    )


def _map_union(branches: list[ast.AST]) -> _MappingResult:
    inner_results = [map_annotation_to_strategy(branch) for branch in branches]
    codes = ", ".join(r.code for r in inner_results)
    extras: set[str] = set()
    for r in inner_results:
        extras.update(r.extra_imports)
    all_ok = all(r.is_supported for r in inner_results)
    first_reason = next(
        (r.fallback_reason for r in inner_results if r.fallback_reason), None
    )
    return _MappingResult(
        code=f"st.one_of({codes})",
        is_supported=all_ok,
        fallback_reason=first_reason,
        extra_imports=extras,
    )


# ---------------------------------------------------------------------------
# AST walking
# ---------------------------------------------------------------------------


_BASE_HYPOTHESIS_IMPORT = "from hypothesis import given, strategies as st"


def _module_dotted_path(file_path: Path, source_root: Path) -> str:
    """Compute a dotted module path relative to ``source_root``."""

    try:
        rel = file_path.resolve().relative_to(source_root.resolve())
    except ValueError:
        # File is outside source_root — fall back to the bare stem.
        return file_path.stem
    parts = list(rel.with_suffix("").parts)
    # Drop trailing __init__ marker so packages report as their package path.
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else file_path.stem


def _iter_python_files(source_root: Path) -> Iterable[Path]:
    yield from sorted(source_root.rglob("*.py"))


def _collect_annotated_parameters(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[str, ast.AST]]:
    """Return ``(name, annotation)`` pairs for every annotated parameter.

    Skips ``self``/``cls`` and any unannotated parameter.
    """

    args = func.args
    collected: list[tuple[str, ast.AST]] = []
    positional = list(args.posonlyargs) + list(args.args)
    for index, arg in enumerate(positional):
        if index == 0 and arg.arg in {"self", "cls"}:
            continue
        if arg.annotation is None:
            continue
        collected.append((arg.arg, arg.annotation))
    for arg in args.kwonlyargs:
        if arg.annotation is None:
            continue
        collected.append((arg.arg, arg.annotation))
    return collected


def _build_function_strategy(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    module: str,
) -> FunctionStrategy | None:
    """Return a :class:`FunctionStrategy` for ``func`` or ``None`` if no annotated params."""

    annotated = _collect_annotated_parameters(func)
    if not annotated:
        return None

    parameters: list[ParameterStrategy] = []
    extra_imports: set[str] = set()
    all_supported = True
    for name, annotation in annotated:
        result = map_annotation_to_strategy(annotation)
        extra_imports.update(result.extra_imports)
        if not result.is_supported:
            all_supported = False
        parameters.append(
            ParameterStrategy(
                parameter_name=name,
                type_hint_source=ast.unparse(annotation),
                strategy_code=result.code,
                is_supported=result.is_supported,
                fallback_reason=result.fallback_reason,
            )
        )

    decorator_lines = ["@given("]
    for param in parameters:
        decorator_lines.append(f"    {param.parameter_name}={param.strategy_code},")
    decorator_lines.append(")")
    given_decorator = "\n".join(decorator_lines)

    required_imports = [_BASE_HYPOTHESIS_IMPORT] + sorted(extra_imports)

    return FunctionStrategy(
        module=module,
        function_name=func.name,
        line_start=func.lineno,
        parameters=parameters,
        given_decorator=given_decorator,
        required_imports=required_imports,
        all_supported=all_supported,
    )


def _walk_functions(
    tree: ast.AST,
) -> Iterable[ast.FunctionDef | ast.AsyncFunctionDef]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def build_strategy_report(
    source_root: Path,
    *,
    module_filter: str | None = None,
    function_filter: str | None = None,
    public_only: bool = False,
) -> StrategyReport:
    """Walk ``source_root`` and assemble a :class:`StrategyReport`."""

    functions: list[FunctionStrategy] = []
    for file_path in _iter_python_files(source_root):
        module = _module_dotted_path(file_path, source_root)
        if module_filter is not None and module != module_filter:
            continue
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except (OSError, SyntaxError, UnicodeDecodeError):
            # Per spec: never raise on parse failure — skip and continue.
            continue
        for func in _walk_functions(tree):
            if public_only and func.name.startswith("_"):
                continue
            if function_filter is not None and func.name != function_filter:
                continue
            entry = _build_function_strategy(func, module=module)
            if entry is not None:
                functions.append(entry)

    fully = sum(1 for f in functions if f.all_supported)
    partial = sum(1 for f in functions if not f.all_supported)
    return StrategyReport(
        source_root=str(source_root),
        functions=functions,
        total_functions=len(functions),
        fully_supported=fully,
        partially_supported=partial,
        timestamp=datetime.now(timezone.utc),
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hypothesis-strategy-generator",
        description=(
            "Emit Hypothesis @given strategies from function type hints, for "
            "property-based test generation."
        ),
    )
    parser.add_argument(
        "source_root",
        type=Path,
        help="Source root to scan for .py files.",
    )
    parser.add_argument(
        "--module",
        dest="module",
        default=None,
        help="Restrict to functions defined in this dotted module path (relative to source_root).",
    )
    parser.add_argument(
        "--function",
        dest="function",
        default=None,
        help="Restrict to functions with this exact name.",
    )
    parser.add_argument(
        "--public-only",
        dest="public_only",
        action="store_true",
        help="Skip functions whose name starts with an underscore.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Always returns ``0`` (the report is informational)."""

    args = _parse_args(argv)
    if not args.source_root.exists():
        # Spec: never raise. Emit an empty report for the missing root and exit 0.
        report = StrategyReport(
            source_root=str(args.source_root),
            functions=[],
            total_functions=0,
            fully_supported=0,
            partially_supported=0,
            timestamp=datetime.now(timezone.utc),
        )
    else:
        report = build_strategy_report(
            args.source_root,
            module_filter=args.module,
            function_filter=args.function,
            public_only=args.public_only,
        )
    json.dump(report.model_dump(mode="json"), sys.stdout, indent=2, sort_keys=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
