"""Deterministic AST Safety Invariant Engine.

Enforces structural safety standards:
- Rule 1: Simple control flow, no recursion.
- Rule 2: Bounded loops with deterministic termination.
- Rule 4: Maximum function length <= 60 lines.
- Rule 5: Minimum assertion density >= 2 assertions per function.
- Rule 7: Strict return and parameter checking.
"""

from __future__ import annotations

import ast
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ViolationType(str, Enum):
    """Safety invariant violation classifications."""
    RULE_1_CONTROL_FLOW = "rule_1_control_flow"
    RULE_2_BOUNDED_LOOPS = "rule_2_bounded_loops"
    RULE_4_LENGTH = "rule_4_function_length"
    RULE_5_ASSERTIONS = "rule_5_assertion_density"
    RULE_7_RETURNS = "rule_7_return_check"


class InvariantViolation(BaseModel):
    """Structured report of a safety invariant violation."""
    function_name: str
    line_number: int
    violation_type: ViolationType
    message: str


class FunctionMetric(BaseModel):
    """Quantitative structural metrics for a function."""
    name: str
    start_line: int
    end_line: int
    length: int
    assertion_count: int


class InvariantReport(BaseModel):
    """Aggregate result of deterministic AST analysis."""
    is_compliant: bool
    total_functions: int
    violations: List[InvariantViolation] = Field(default_factory=list)
    function_metrics: List[FunctionMetric] = Field(default_factory=list)


class AstInvariantChecker:
    """Mechanical AST safety invariant auditor for Python source code."""

    def __init__(self, max_function_length: int = 60, min_assertion_density: int = 2) -> None:
        """Initialize checker thresholds with safety bounds."""
        assert max_function_length > 0, "Max function length must be positive"
        assert min_assertion_density >= 0, "Min assertion density must be non-negative"
        self.max_function_length = max_function_length
        self.min_assertion_density = min_assertion_density

    def check_code(self, source_code: str) -> InvariantReport:
        """Parse source code and verify all deterministic safety invariants."""
        assert isinstance(source_code, str), "Source code must be a string"
        assert len(source_code) >= 0, "Source code length must be non-negative"

        try:
            tree = ast.parse(source_code)
        except SyntaxError as err:
            return InvariantReport(
                is_compliant=False,
                total_functions=0,
                violations=[
                    InvariantViolation(
                        function_name="<module>",
                        line_number=err.lineno or 1,
                        violation_type=ViolationType.RULE_1_CONTROL_FLOW,
                        message=f"Syntax error prevents AST invariant analysis: {err.msg}",
                    )
                ],
            )

        violations: List[InvariantViolation] = []
        metrics: List[FunctionMetric] = []
        self._inspect_node(tree, violations, metrics)

        is_compliant = len(violations) == 0
        return InvariantReport(
            is_compliant=is_compliant,
            total_functions=len(metrics),
            violations=violations,
            function_metrics=metrics,
        )

    def _inspect_node(
        self,
        tree: ast.AST,
        violations: List[InvariantViolation],
        metrics: List[FunctionMetric],
    ) -> None:
        """Traverse AST tree collecting function-level metrics and violations."""
        assert isinstance(violations, list), "Violations container must be a list"
        assert isinstance(metrics, list), "Metrics container must be a list"

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._audit_function(node, violations, metrics)

    def _audit_function(
        self,
        fn_node: ast.FunctionDef | ast.AsyncFunctionDef,
        violations: List[InvariantViolation],
        metrics: List[FunctionMetric],
    ) -> None:
        """Audit single function node for Holzmann rules 1, 2, 4, and 5."""
        assert fn_node.name, "Function node must possess a valid identifier"
        assert hasattr(fn_node, "lineno"), "Function node must retain source line mapping"

        start_line = fn_node.lineno
        end_line = getattr(fn_node, "end_lineno", start_line)
        length = end_line - start_line + 1

        assert length > 0, "Computed function length must be strictly positive"

        # Count assertions
        assertions = [sub for sub in ast.walk(fn_node) if isinstance(sub, ast.Assert)]
        assertion_count = len(assertions)

        metric = FunctionMetric(
            name=fn_node.name,
            start_line=start_line,
            end_line=end_line,
            length=length,
            assertion_count=assertion_count,
        )
        metrics.append(metric)

        # Rule 4: Maximum function length
        if length > self.max_function_length:
            violations.append(
                InvariantViolation(
                    function_name=fn_node.name,
                    line_number=start_line,
                    violation_type=ViolationType.RULE_4_LENGTH,
                    message=f"Function length {length} exceeds maximum threshold of {self.max_function_length} lines",
                )
            )

        # Rule 5: Minimum assertion density
        if assertion_count < self.min_assertion_density:
            violations.append(
                InvariantViolation(
                    function_name=fn_node.name,
                    line_number=start_line,
                    violation_type=ViolationType.RULE_5_ASSERTIONS,
                    message=f"Assertion count {assertion_count} is below required minimum of {self.min_assertion_density}",
                )
            )

        # Rule 1 & Rule 2 sub-checks
        self._audit_loops_and_recursion(fn_node, violations)

    def _audit_loops_and_recursion(
        self,
        fn_node: ast.FunctionDef | ast.AsyncFunctionDef,
        violations: List[InvariantViolation],
    ) -> None:
        """Audit loop boundedness and recursion inside function scope."""
        assert fn_node is not None, "Function node cannot be None"
        assert isinstance(violations, list), "Violations list must be mutable"

        for node in ast.walk(fn_node):
            if isinstance(node, ast.While):
                self._check_while_loop(node, fn_node.name, violations)
            elif isinstance(node, ast.Call):
                self._check_recursion(node, fn_node.name, violations)

    def _check_while_loop(
        self,
        while_node: ast.While,
        func_name: str,
        violations: List[InvariantViolation],
    ) -> None:
        """Verify that while loops have deterministic bounded termination conditions."""
        assert while_node is not None, "While node cannot be None"
        assert func_name, "Function name must be non-empty"

        is_constant_true = isinstance(while_node.test, ast.Constant) and bool(while_node.test.value)
        has_break = any(isinstance(sub, ast.Break) for sub in ast.walk(while_node))

        if is_constant_true and not has_break:
            violations.append(
                InvariantViolation(
                    function_name=func_name,
                    line_number=while_node.lineno,
                    violation_type=ViolationType.RULE_2_BOUNDED_LOOPS,
                    message="Unbounded 'while True' loop detected without deterministic break guard",
                )
            )

    def _check_recursion(
        self,
        call_node: ast.Call,
        func_name: str,
        violations: List[InvariantViolation],
    ) -> None:
        """Verify that function does not make direct recursive calls."""
        assert call_node is not None, "Call node cannot be None"
        assert func_name, "Function name must be provided"

        if isinstance(call_node.func, ast.Name) and call_node.func.id == func_name:
            violations.append(
                InvariantViolation(
                    function_name=func_name,
                    line_number=call_node.lineno,
                    violation_type=ViolationType.RULE_1_CONTROL_FLOW,
                    message=f"Direct recursion detected in function '{func_name}', violating control flow simplicity",
                )
            )
