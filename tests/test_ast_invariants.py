"""Tests for the Deterministic AST Safety Invariant Engine."""

from __future__ import annotations

import pytest
from nemotron_sentinel.ast_invariants import AstInvariantChecker, InvariantReport, ViolationType


def test_clean_function_passes() -> None:
    """Verifies that a function complying with safety invariants passes cleanly."""
    clean_code = '''
def calculate_ratio(a: float, b: float) -> float:
    assert b != 0.0, "Denominator cannot be zero"
    assert a >= 0.0, "Numerator must be non-negative"
    res = a / b
    return res
'''
    checker = AstInvariantChecker()
    report: InvariantReport = checker.check_code(clean_code)
    assert report.is_compliant is True
    assert len(report.violations) == 0


def test_function_length_exceeded_flagged() -> None:
    """Verifies that a function exceeding 60 lines is flagged with RULE_4_LENGTH."""
    lines = ["def long_monolith(base_val: int) -> int:"]
    lines.append("    assert base_val > 0, 'Base value must be positive'")
    lines.append("    assert base_val < 100000, 'Base value must be bounded'")
    for i in range(65):
        lines.append(f"    x_{i} = base_val + {i}")
    lines.append("    return x_0")
    code = "\n".join(lines)

    checker = AstInvariantChecker()
    report = checker.check_code(code)
    assert report.is_compliant is False
    assert any(v.violation_type == ViolationType.RULE_4_LENGTH for v in report.violations)


def test_insufficient_assertions_flagged() -> None:
    """Verifies that a function with fewer than 2 assertions is flagged with RULE_5_ASSERTIONS."""
    code = '''
def under_asserted(val: int) -> int:
    assert val > 0, "Val must be positive"
    return val * 2
'''
    checker = AstInvariantChecker()
    report = checker.check_code(code)
    assert report.is_compliant is False
    assert any(v.violation_type == ViolationType.RULE_5_ASSERTIONS for v in report.violations)


def test_unbounded_while_loop_flagged() -> None:
    """Verifies that an infinite while loop without an explicit break is flagged with RULE_2_BOUNDED_LOOPS."""
    code = '''
def endless_worker(state_val: int) -> None:
    assert state_val >= 0, "State must be non-negative"
    assert state_val < 1000, "State must be bounded"
    while True:
        pass
'''
    checker = AstInvariantChecker()
    report = checker.check_code(code)
    assert report.is_compliant is False
    assert any(v.violation_type == ViolationType.RULE_2_BOUNDED_LOOPS for v in report.violations)


def test_bounded_while_loop_with_break_passes() -> None:
    """Verifies that a while loop with an explicit deterministic break passes."""
    code = '''
def bounded_worker(limit: int) -> int:
    assert limit > 0, "Limit must be positive"
    assert limit < 1000, "Limit must be bounded"
    count = 0
    while True:
        count += 1
        if count >= limit:
            break
    return count
'''
    checker = AstInvariantChecker()
    report = checker.check_code(code)
    loop_violations = [v for v in report.violations if v.violation_type == ViolationType.RULE_2_BOUNDED_LOOPS]
    assert len(loop_violations) == 0


def test_direct_recursion_flagged() -> None:
    """Verifies that direct recursive calls are flagged with RULE_1_CONTROL_FLOW."""
    code = '''
def factorial(n: int) -> int:
    assert n >= 0, "Value must be non-negative"
    assert n < 100, "Value must be under 100"
    if n <= 1:
        return 1
    return n * factorial(n - 1)
'''
    checker = AstInvariantChecker()
    report = checker.check_code(code)
    assert report.is_compliant is False
    assert any(v.violation_type == ViolationType.RULE_1_CONTROL_FLOW for v in report.violations)
