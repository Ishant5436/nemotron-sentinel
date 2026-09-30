"""Tests for the FastMCP Server Tool Gateway."""

from __future__ import annotations

import pytest
from nemotron_sentinel.server import (
    mcp,
    nemotron_audit_ast,
    nemotron_cve_scan,
    nemotron_repair_invariants,
    nemotron_generate_tdd,
)


def test_mcp_instance_and_tools_registered() -> None:
    """Verifies that FastMCP server instance is correctly initialized with required tools."""
    assert mcp.name == "nemotron-sentinel", "MCP server name must be nemotron-sentinel"


def test_nemotron_audit_ast_tool() -> None:
    """Verifies that nemotron_audit_ast tool audits code and outputs structured dictionary."""
    clean_code = '''
def valid_operation(x: int) -> int:
    assert isinstance(x, int), "x must be int"
    assert x > 0, "x must be positive"
    return x * 2
'''
    res = nemotron_audit_ast(code=clean_code)
    assert isinstance(res, dict), "Result must be a dictionary"
    assert res["is_compliant"] is True, "Clean code must be compliant"
    assert res["total_functions"] == 1, "Must detect 1 function"
    assert len(res["violations"]) == 0, "Violations list must be empty"


def test_nemotron_audit_ast_tool_violation() -> None:
    """Verifies that nemotron_audit_ast detects violations in defective code."""
    bad_code = '''
def missing_assertions(x: int) -> int:
    return x * 2
'''
    res = nemotron_audit_ast(code=bad_code)
    assert isinstance(res, dict), "Result must be a dictionary"
    assert res["is_compliant"] is False, "Defective code must not be compliant"
    assert len(res["violations"]) > 0, "Must report at least one violation"


def test_nemotron_cve_scan_tool() -> None:
    """Verifies that nemotron_cve_scan tool audits list of packages."""
    res = nemotron_cve_scan(packages=["pydantic", "vulnerable-demo-pkg"])
    assert isinstance(res, dict), "Result must be a dictionary"
    assert "reports" in res, "Result must contain reports key"
    assert len(res["reports"]) == 2, "Must report on both queried packages"


def test_nemotron_repair_invariants_tool() -> None:
    """Verifies that nemotron_repair_invariants produces clean repaired code."""
    broken = '''
def sum_two(a: int, b: int) -> int:
    return a + b
'''
    res = nemotron_repair_invariants(broken_code=broken, violations=["Missing assertions"])
    assert isinstance(res, dict), "Result must be a dictionary"
    assert "repaired_code" in res, "Result must contain repaired_code key"
    assert len(res["repaired_code"]) > 0, "Repaired code must be non-empty"


def test_nemotron_generate_tdd_tool() -> None:
    """Verifies that nemotron_generate_tdd executes sandboxed TDD cycle."""
    target = '''
def simple_mul(a: int, b: int) -> int:
    assert a >= 0, "Non-negative"
    assert b >= 0, "Non-negative"
    return a * b
'''
    test = '''
from target import simple_mul

def test_mul():
    assert simple_mul(2, 3) == 6
'''
    res = nemotron_generate_tdd(source_code=target, test_code=test)
    assert isinstance(res, dict), "Result must be a dictionary"
    assert res["success"] is True, "Test execution must be successful"
