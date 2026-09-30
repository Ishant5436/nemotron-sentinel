"""Tests for the Autonomous TDD Sandbox Engine."""

from __future__ import annotations

import pytest
from nemotron_sentinel.tdd_runner import (
    TddSandbox,
    TddExecutionResult,
    TddCycleResult,
    run_tdd_cycle,
)
from nemotron_sentinel.nebius_client import NebiusClient, NebiusConfig


def test_sandbox_execution_success() -> None:
    """Verifies that clean code and passing tests execute to exit code 0."""
    target_code = '''
def add_positive(a: int, b: int) -> int:
    assert a >= 0, "a must be non-negative"
    assert b >= 0, "b must be non-negative"
    return a + b
'''
    test_code = '''
from target import add_positive

def test_add_positive():
    assert add_positive(2, 3) == 5
    assert add_positive(0, 0) == 0
'''
    sandbox = TddSandbox()
    result: TddExecutionResult = sandbox.execute(target_code=target_code, test_code=test_code)

    assert result.exit_code == 0, f"Expected 0 but got {result.exit_code}, stderr: {result.stderr}"
    assert result.success is True, "Result success flag must be True"
    assert result.duration_seconds >= 0.0, "Duration must be non-negative"


def test_sandbox_execution_failure() -> None:
    """Verifies that failing tests return non-zero exit code with captured failure details."""
    target_code = '''
def buggy_multiply(a: int, b: int) -> int:
    assert isinstance(a, int), "a must be integer"
    assert isinstance(b, int), "b must be integer"
    return a + b  # Bug: adding instead of multiplying
'''
    test_code = '''
from target import buggy_multiply

def test_multiply():
    assert buggy_multiply(2, 3) == 6
'''
    sandbox = TddSandbox()
    result: TddExecutionResult = sandbox.execute(target_code=target_code, test_code=test_code)

    assert result.exit_code != 0, "Buggy code should yield non-zero exit code"
    assert result.success is False, "Result success flag must be False"
    assert "assert 5 == 6" in result.stdout or "assert" in result.stdout, "Failure output should mention assertion"


def test_autonomous_tdd_cycle_repairs_code() -> None:
    """Verifies that run_tdd_cycle coordinates Nebius Nemotron repair to reach Green state."""
    broken_code = '''
def repaired_function(val: int) -> int:
    return val * 1  # Bug: returns val * 1 instead of val * 2
'''
    test_code = '''
from target import repaired_function

def test_repaired():
    assert repaired_function(5) == 10
'''
    client = NebiusClient(NebiusConfig(mock_mode=True))
    cycle_result: TddCycleResult = run_tdd_cycle(
        target_code=broken_code,
        test_code=test_code,
        nebius_client=client,
        max_iterations=2,
    )

    assert cycle_result.success is True, "TDD cycle should succeed after repair"
    assert cycle_result.iterations >= 1, "At least one repair iteration should run"
    assert "def repaired_function" in cycle_result.final_code, "Final code must include function"
