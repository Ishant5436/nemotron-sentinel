"""Autonomous TDD Sandbox Engine.

Executes test suites in isolated subprocess sandboxes, captures failure telemetry,
and coordinates iterative repair cycles with NVIDIA Nemotron on Nebius Token Factory.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from typing import Optional
from pydantic import BaseModel, Field

from nemotron_sentinel.ast_invariants import AstInvariantChecker
from nemotron_sentinel.nebius_client import NebiusClient, NebiusConfig


class TddExecutionResult(BaseModel):
    """Telemetry captured from sandboxed test execution."""
    success: bool
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0


class TddCycleResult(BaseModel):
    """Aggregate result of an autonomous Red-to-Green repair cycle."""
    success: bool
    iterations: int
    final_code: str
    initial_execution: TddExecutionResult
    final_execution: TddExecutionResult
    invariant_compliant: bool
    error_message: Optional[str] = None


class TddSandbox:
    """Isolated subprocess runner for unit test execution."""

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        """Initialize sandbox with bounded execution timeout."""
        assert timeout_seconds > 0.0, "Timeout must be strictly positive"
        assert timeout_seconds <= 60.0, "Timeout cannot exceed safety threshold of 60s"
        self.timeout_seconds = timeout_seconds

    def execute(self, target_code: str, test_code: str) -> TddExecutionResult:
        """Write source and test code into temp environment and execute pytest."""
        assert isinstance(target_code, str), "Target code must be string"
        assert isinstance(test_code, str), "Test code must be string"

        with tempfile.TemporaryDirectory(prefix="nemotron_tdd_") as tmpdir:
            target_path = os.path.join(tmpdir, "target.py")
            test_path = os.path.join(tmpdir, "test_target.py")

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(target_code)
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(test_code)

            return self._run_pytest_subprocess(tmpdir, test_path)

    def _run_pytest_subprocess(self, cwd: str, test_file: str) -> TddExecutionResult:
        """Invoke pytest executable in a sandboxed subprocess with strict timeout."""
        assert os.path.isdir(cwd), "Sandbox working directory must exist"
        assert os.path.isfile(test_file), "Target test file must exist on disk"

        cmd = [sys.executable, "-m", "pytest", os.path.basename(test_file)]
        start_time = time.monotonic()

        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            duration = time.monotonic() - start_time
            return TddExecutionResult(
                success=(proc.returncode == 0),
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_seconds=duration,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - start_time
            stdout_str = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            return TddExecutionResult(
                success=False,
                exit_code=124,
                stdout=stdout_str,
                stderr=f"Execution timed out after {self.timeout_seconds} seconds",
                duration_seconds=duration,
            )


def run_tdd_cycle(
    target_code: str,
    test_code: str,
    nebius_client: Optional[NebiusClient] = None,
    max_iterations: int = 3,
) -> TddCycleResult:
    """Orchestrate Red-to-Green autonomous repair cycle with safety invariant checks."""
    assert max_iterations > 0, "max_iterations must be strictly positive"
    assert len(target_code.strip()) > 0, "Target code cannot be empty"

    client = nebius_client or NebiusClient(NebiusConfig())
    sandbox = TddSandbox()
    checker = AstInvariantChecker()

    initial_run = sandbox.execute(target_code, test_code)
    if initial_run.success:
        report = checker.check_code(target_code)
        return TddCycleResult(
            success=True,
            iterations=0,
            final_code=target_code,
            initial_execution=initial_run,
            final_execution=initial_run,
            invariant_compliant=report.is_compliant,
        )

    return _repair_loop(target_code, test_code, initial_run, client, sandbox, checker, max_iterations)


def _repair_loop(
    target_code: str,
    test_code: str,
    initial_run: TddExecutionResult,
    client: NebiusClient,
    sandbox: TddSandbox,
    checker: AstInvariantChecker,
    max_iterations: int,
) -> TddCycleResult:
    """Execute iterative Nemotron repair passes until green tests or iteration limit."""
    assert max_iterations >= 1, "Must allow at least one repair iteration"
    assert client is not None, "Client instance required for repair pass"

    current_code = target_code
    latest_run = initial_run

    for i in range(1, max_iterations + 1):
        err_context = latest_run.stdout if latest_run.stdout else latest_run.stderr
        current_code = client.generate_code_repair(
            broken_code=current_code,
            violations=[f"Test suite failure:\n{err_context}"],
        )

        latest_run = sandbox.execute(current_code, test_code)
        if latest_run.success:
            report = checker.check_code(current_code)
            return TddCycleResult(
                success=True,
                iterations=i,
                final_code=current_code,
                initial_execution=initial_run,
                final_execution=latest_run,
                invariant_compliant=report.is_compliant,
            )

    report = checker.check_code(current_code)
    return TddCycleResult(
        success=False,
        iterations=max_iterations,
        final_code=current_code,
        initial_execution=initial_run,
        final_execution=latest_run,
        invariant_compliant=report.is_compliant,
        error_message=f"Failed to achieve green tests within {max_iterations} iterations",
    )
