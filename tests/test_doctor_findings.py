"""Tests for scripts/lib/doctor_findings.py."""
from __future__ import annotations

import importlib
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"


@pytest.fixture
def df():
    sys.path.insert(0, str(LIB_DIR))
    if "doctor_findings" in sys.modules:
        del sys.modules["doctor_findings"]
    mod = importlib.import_module("doctor_findings")
    yield mod
    sys.path.remove(str(LIB_DIR))


def test_empty_findings_exit_zero(df):
    assert df.aggregate_exit_code([]) == 0


def test_only_info_exits_zero(df):
    findings = [df.Finding(category="submodule_stale", severity="info", artifact="x", message="m")]
    assert df.aggregate_exit_code(findings) == 0


def test_warn_exits_one(df):
    findings = [df.Finding(category="drift", severity="warn", artifact="x", message="m")]
    assert df.aggregate_exit_code(findings) == 1


def test_error_exits_two(df):
    findings = [
        df.Finding(category="drift", severity="warn", artifact="x", message="m"),
        df.Finding(category="missing", severity="error", artifact="y", message="m"),
    ]
    assert df.aggregate_exit_code(findings) == 2


def test_severity_floor_warn_drops_info(df):
    findings = [df.Finding(category="submodule_stale", severity="info", artifact="x", message="m")]
    assert df.aggregate_exit_code(findings, severity_floor="warn") == 0


def test_severity_floor_error_drops_warn(df):
    findings = [df.Finding(category="drift", severity="warn", artifact="x", message="m")]
    assert df.aggregate_exit_code(findings, severity_floor="error") == 0


def test_severity_floor_info_keeps_info_but_still_zero(df):
    # info findings never raise above 0
    findings = [df.Finding(category="submodule_stale", severity="info", artifact="x", message="m")]
    assert df.aggregate_exit_code(findings, severity_floor="info") == 0


def test_to_display_underscore_to_hyphen(df):
    assert df.to_display("pin_rot") == "pin-rot"
    assert df.to_display("submodule_stale") == "submodule-stale"
    assert df.to_display("drift") == "drift"
    assert df.to_display("missing") == "missing"


def test_category_severity_table(df):
    assert df.CATEGORY_SEVERITY["drift"] == "warn"
    assert df.CATEGORY_SEVERITY["missing"] == "error"
    assert df.CATEGORY_SEVERITY["corrupt"] == "error"
    assert df.CATEGORY_SEVERITY["submodule_stale"] == "info"
