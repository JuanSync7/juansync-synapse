# @summary
# CLI entry point for log-contract-validator: walks a source tree, AST-extracts
# logging calls, detects archetype-contract violations, and emits a
# LogContractReport JSON with a log-path coverage metric.
# Exports: main, validate_source_tree, analyze_file
# Deps: ast, argparse, json, pathlib, datetime, pydantic, (optional) yaml
# @end-summary
"""log-contract-validator: validate logging archetype contracts.

Walks every ``.py`` file under a source root, extracts logging calls via the
standard library ``ast`` module, and detects violations against an optional
``LOG_POLICY.yaml`` archetype contract. Computes a ``log_path_coverage``
metric defined as ``branches_with_log / total_branches`` over the union of
``If``, ``ExceptHandler``, ``For``, and ``While`` branch nodes in source.

The tool is heuristic by design — for example, "log in hot loop" may produce
false positives on intentionally throttled call sites. Callers should treat
the report as advisory and pair it with code review.

CLI usage::

    python -m src.tools.testing.log_contract_validator <source_root> \\
        [--policy LOG_POLICY.yaml] [--ignore-patterns tests/,migrations/]

Exit codes:

* ``0`` — no violations
* ``1`` — at least one violation
* ``2`` — tool error (invalid arguments, unreadable source, etc.)
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

try:  # PyYAML is optional; policy enforcement degrades to no-op without it.
    import yaml  # type: ignore[import-untyped]

    _HAS_YAML = True
except ImportError:  # pragma: no cover - exercised at import time
    yaml = None  # type: ignore[assignment]
    _HAS_YAML = False

from .schemas import LogCall, LogContractReport, LogContractViolation


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LOG_LEVELS: frozenset[str] = frozenset(
    {"debug", "info", "warning", "error", "critical", "exception"}
)
_LOGGER_NAMES: frozenset[str] = frozenset({"logger", "log", "logging"})
_BARE_MODULE_NAME = "logging"

# Levels considered "below warning" — used for archetype-level checks.
_WEAK_LEVELS: frozenset[str] = frozenset({"debug", "info"})


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _attach_parents(tree: ast.AST) -> None:
    """Annotate every AST node with a ``parent`` attribute (in place)."""
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node  # type: ignore[attr-defined]


def _iter_ancestors(node: ast.AST) -> Iterable[ast.AST]:
    """Yield ancestors of ``node`` from nearest to root."""
    cur = getattr(node, "parent", None)
    while cur is not None:
        yield cur
        cur = getattr(cur, "parent", None)


def _enclosing_function(node: ast.AST) -> str | None:
    """Return the name of the enclosing function/method, if any."""
    for anc in _iter_ancestors(node):
        if isinstance(anc, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return anc.name
    return None


def _is_log_call(node: ast.Call) -> tuple[bool, str | None, str | None]:
    """Inspect a Call node; return ``(is_log, level, receiver)``.

    ``receiver`` is the textual head used (``logger``, ``log``, or
    ``logging``) when the call shape is ``<receiver>.<level>(...)``.
    """
    func = node.func
    if not isinstance(func, ast.Attribute):
        return False, None, None
    level = func.attr
    if level not in _LOG_LEVELS:
        return False, None, None
    value = func.value
    if isinstance(value, ast.Name) and value.id in _LOGGER_NAMES:
        return True, level, value.id
    return False, None, None


def _extract_message_template(call: ast.Call) -> str:
    """Best-effort extraction of the message template from a log call."""
    if not call.args:
        return ""
    first = call.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    if isinstance(first, ast.JoinedStr):
        # Reconstruct a representative template for f-strings.
        parts: list[str] = []
        for v in first.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                parts.append(v.value)
            else:
                parts.append("{...}")
        return "".join(parts)
    return ast.unparse(first) if hasattr(ast, "unparse") else "<expr>"


def _extract_extra_fields(call: ast.Call) -> tuple[bool, list[str]]:
    """Inspect kwargs for structured fields.

    Returns ``(has_extra_fields, field_names)``. The ``extra={...}`` kwarg is
    the canonical structured-field channel; other non-reserved kwargs are
    also reported as field names.
    """
    reserved = {"exc_info", "stack_info", "stacklevel"}
    field_names: list[str] = []
    has_extra = False
    for kw in call.keywords:
        if kw.arg is None:
            continue  # **kwargs splat — opaque
        if kw.arg == "extra":
            has_extra = True
            if isinstance(kw.value, ast.Dict):
                for key in kw.value.keys:
                    if isinstance(key, ast.Constant) and isinstance(
                        key.value, str
                    ):
                        field_names.append(key.value)
        elif kw.arg not in reserved:
            field_names.append(kw.arg)
            has_extra = True
    return has_extra, field_names


def _contains_log_call(node: ast.AST) -> bool:
    """Return True if ``node`` (transitively) contains any log call."""
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            ok, _, _ = _is_log_call(child)
            if ok:
                return True
    return False


def _module_name_from_path(path: Path, source_root: Path) -> str:
    """Compute a dotted module name relative to ``source_root``."""
    try:
        rel = path.relative_to(source_root).with_suffix("")
    except ValueError:
        rel = path.with_suffix("")
    parts = [p for p in rel.parts if p != "__init__"]
    return ".".join(parts) if parts else path.stem


# ---------------------------------------------------------------------------
# Violation detectors
# ---------------------------------------------------------------------------


def _detect_except_violations(
    handler: ast.ExceptHandler,
    module: str,
) -> list[LogContractViolation]:
    """Flag except blocks that lack a log, and weak-level logs in except."""
    violations: list[LogContractViolation] = []
    body = handler.body
    has_log = False
    has_raise_or_pass = False
    weak_log_lines: list[tuple[int, str]] = []

    for stmt in body:
        if isinstance(stmt, (ast.Raise, ast.Pass)):
            has_raise_or_pass = True
        for child in ast.walk(stmt):
            if isinstance(child, ast.Call):
                ok, level, _ = _is_log_call(child)
                if ok:
                    has_log = True
                    if level in _WEAK_LEVELS:
                        weak_log_lines.append((child.lineno, level or ""))

    if not has_log and not has_raise_or_pass:
        violations.append(
            LogContractViolation(
                module=module,
                line=handler.lineno,
                violation_type="missing_log_in_except",
                message=(
                    "except block has no log call, no raise, and no pass"
                ),
                expected="logger.error/exception(...) or raise",
                actual="silent except",
            )
        )

    for line, level in weak_log_lines:
        violations.append(
            LogContractViolation(
                module=module,
                line=line,
                violation_type="wrong_level_for_archetype",
                message=(
                    "log call inside except block uses weak level "
                    f"'{level}'; expected warning/error/exception/critical"
                ),
                expected="warning|error|exception|critical",
                actual=level,
            )
        )
    return violations


def _detect_post_raise_weak_log(
    func_body: list[ast.stmt],
    module: str,
) -> list[LogContractViolation]:
    """Flag weak-level log calls that follow a Raise statement."""
    violations: list[LogContractViolation] = []
    after_raise = False
    for stmt in func_body:
        if isinstance(stmt, ast.Raise):
            after_raise = True
            continue
        if after_raise:
            for child in ast.walk(stmt):
                if isinstance(child, ast.Call):
                    ok, level, _ = _is_log_call(child)
                    if ok and level in _WEAK_LEVELS:
                        violations.append(
                            LogContractViolation(
                                module=module,
                                line=child.lineno,
                                violation_type="wrong_level_for_archetype",
                                message=(
                                    "log call follows a raise but uses "
                                    f"weak level '{level}'"
                                ),
                                expected="error|critical|exception",
                                actual=level,
                            )
                        )
    return violations


def _detect_call_violations(
    call: ast.Call,
    level: str,
    receiver: str,
    module: str,
    policy: dict | None,
    extra_field_names: list[str],
) -> list[LogContractViolation]:
    """Per-call rules: f-string templates, bare logger, hot loops, policy."""
    violations: list[LogContractViolation] = []

    # f-string template
    if call.args and isinstance(call.args[0], ast.JoinedStr):
        violations.append(
            LogContractViolation(
                module=module,
                line=call.lineno,
                violation_type="f_string_template",
                message=(
                    "log call uses an f-string; use a % or {} template "
                    "with structured fields instead"
                ),
                expected="logger.info('msg %s', value) or extra={...}",
                actual="f-string",
            )
        )

    # Bare logger usage (logging.info(...)).
    if receiver == _BARE_MODULE_NAME:
        violations.append(
            LogContractViolation(
                module=module,
                line=call.lineno,
                violation_type="bare_logger_no_module",
                message=(
                    "uses bare logging.<level>(...) instead of a "
                    "module-bound logger"
                ),
                expected="logger = logging.getLogger(__name__); logger.x(...)",
                actual=f"logging.{level}(...)",
            )
        )

    # Hot-loop heuristic: inside For/While, no enclosing If between loop and call.
    in_loop = False
    guarded = False
    for anc in _iter_ancestors(call):
        if isinstance(anc, ast.If):
            guarded = True
        if isinstance(anc, (ast.For, ast.AsyncFor, ast.While)):
            in_loop = True
            break
        if isinstance(anc, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            break
    if in_loop and not guarded:
        violations.append(
            LogContractViolation(
                module=module,
                line=call.lineno,
                violation_type="log_in_hot_loop",
                message=(
                    "log call inside a loop without an enclosing guard; "
                    "consider throttling or moving outside the loop"
                ),
                expected="if <should_log>: logger.<level>(...)",
                actual="unguarded log in loop",
            )
        )

    # Policy-driven required-field enforcement.
    if policy:
        required_map = policy.get("required_fields_per_level") or {}
        required = required_map.get(level) or []
        missing = [f for f in required if f not in extra_field_names]
        for field in missing:
            violations.append(
                LogContractViolation(
                    module=module,
                    line=call.lineno,
                    violation_type="missing_required_field",
                    message=(
                        f"log call at level '{level}' is missing required "
                        f"structured field '{field}'"
                    ),
                    expected=f"extra={{'{field}': ...}}",
                    actual=str(extra_field_names) if extra_field_names else "(no extra)",
                )
            )

    return violations


# ---------------------------------------------------------------------------
# File / tree analysis
# ---------------------------------------------------------------------------


def analyze_file(
    path: Path,
    source_root: Path,
    policy: dict | None,
) -> tuple[list[LogCall], list[LogContractViolation], int, int]:
    """Analyze a single .py file.

    Returns ``(log_calls, violations, total_branches, branches_with_log)``.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:  # pragma: no cover
        # Surface a tool-error-style violation but keep the run going.
        return (
            [],
            [
                LogContractViolation(
                    module=str(path),
                    line=0,
                    violation_type="missing_log_in_except",
                    message=f"could not read file: {exc}",
                )
            ],
            0,
            0,
        )

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        # Skip unparseable files silently — not this tool's job.
        return [], [], 0, 0

    _attach_parents(tree)
    module = _module_name_from_path(path, source_root)

    log_calls: list[LogCall] = []
    violations: list[LogContractViolation] = []

    # Walk Calls for log-call discovery and per-call violations.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            ok, level, receiver = _is_log_call(node)
            if not ok or level is None or receiver is None:
                continue
            template = _extract_message_template(node)
            has_extra, field_names = _extract_extra_fields(node)
            log_calls.append(
                LogCall(
                    module=module,
                    function_name=_enclosing_function(node),
                    line=node.lineno,
                    level=level,  # type: ignore[arg-type]
                    message_template=template,
                    has_extra_fields=has_extra,
                    extra_field_names=field_names,
                )
            )
            violations.extend(
                _detect_call_violations(
                    node, level, receiver, module, policy, field_names
                )
            )

    # Except-handler-level violations.
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            violations.extend(_detect_except_violations(node, module))

    # Post-raise weak-level checks (per function body).
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            violations.extend(_detect_post_raise_weak_log(node.body, module))

    # Branch counting.
    branch_nodes = [
        n
        for n in ast.walk(tree)
        if isinstance(n, (ast.If, ast.ExceptHandler, ast.For, ast.While))
    ]
    total_branches = len(branch_nodes)
    branches_with_log = sum(1 for n in branch_nodes if _contains_log_call(n))

    return log_calls, violations, total_branches, branches_with_log


def _should_ignore(path: Path, source_root: Path, patterns: list[str]) -> bool:
    """Return True if ``path`` matches any ignore substring or glob pattern."""
    if not patterns:
        return False
    try:
        rel = path.relative_to(source_root).as_posix()
    except ValueError:
        rel = path.as_posix()
    for pat in patterns:
        pat = pat.strip()
        if not pat:
            continue
        if pat in rel:
            return True
        if path.match(pat):
            return True
    return False


def _load_policy(policy_path: Path | None) -> dict | None:
    """Load the policy YAML, or return None if unavailable."""
    if policy_path is None:
        return None
    if not _HAS_YAML:
        return None
    if not policy_path.exists():
        return None
    try:
        with policy_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)  # type: ignore[union-attr]
        return data if isinstance(data, dict) else None
    except Exception:  # pragma: no cover - policy parse errors are advisory
        return None


def validate_source_tree(
    source_root: Path,
    policy_path: Path | None = None,
    ignore_patterns: list[str] | None = None,
) -> LogContractReport:
    """Validate every ``.py`` file under ``source_root`` and aggregate."""
    ignore_patterns = ignore_patterns or []
    policy = _load_policy(policy_path)

    all_calls: list[LogCall] = []
    all_violations: list[LogContractViolation] = []
    total_branches = 0
    branches_with_log = 0

    for path in sorted(source_root.rglob("*.py")):
        if _should_ignore(path, source_root, ignore_patterns):
            continue
        calls, viols, total, with_log = analyze_file(
            path, source_root, policy
        )
        all_calls.extend(calls)
        all_violations.extend(viols)
        total_branches += total
        branches_with_log += with_log

    coverage = (
        branches_with_log / total_branches if total_branches > 0 else 0.0
    )

    return LogContractReport(
        source_root=str(source_root),
        policy_path=str(policy_path) if policy_path else None,
        log_calls=all_calls,
        violations=all_violations,
        total_branches=total_branches,
        branches_with_log=branches_with_log,
        log_path_coverage=coverage,
        timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="log-contract-validator",
        description=(
            "Validate logging calls against a log archetype contract and "
            "compute log-path coverage."
        ),
    )
    parser.add_argument(
        "source_root",
        help="Root directory to scan for .py files",
    )
    parser.add_argument(
        "--policy",
        default=None,
        help="Path to LOG_POLICY.yaml (optional)",
    )
    parser.add_argument(
        "--ignore-patterns",
        default="",
        help=(
            "Comma-separated path substrings/globs to skip "
            "(e.g. 'tests/,migrations/')"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the process exit code."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    source_root = Path(args.source_root).resolve()
    if not source_root.exists() or not source_root.is_dir():
        print(
            f"error: source_root not a directory: {source_root}",
            file=sys.stderr,
        )
        return 2

    policy_path = Path(args.policy).resolve() if args.policy else None
    ignore = [p for p in args.ignore_patterns.split(",") if p.strip()]

    try:
        report = validate_source_tree(source_root, policy_path, ignore)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"error: validation failed: {exc}", file=sys.stderr)
        return 2

    print(report.model_dump_json(indent=2))
    return 1 if report.violations else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
