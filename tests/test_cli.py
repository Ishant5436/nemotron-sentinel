"""Tests for the Institutional CLI Terminal Interface."""

from __future__ import annotations

import tempfile
import pytest
from nemotron_sentinel.cli import main, build_parser


def test_cli_help_parser() -> None:
    """Verifies that the CLI argument parser configures all subcommands correctly."""
    parser = build_parser()
    assert parser.prog == "nemotron-sentinel", "Parser prog must be nemotron-sentinel"
    subparser_actions = [
        action for action in parser._actions if action.dest == "subcommand"
    ]
    assert len(subparser_actions) == 1, "Subcommand selector must be registered"


def test_cli_audit_clean_file() -> None:
    """Verifies that running audit on compliant code returns exit code 0."""
    clean_code = '''
def valid_function(a: int) -> int:
    assert isinstance(a, int), "Must be integer"
    assert a >= 0, "Must be non-negative"
    return a * 2
'''
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(clean_code)
        f_path = f.name

    exit_code = main(["audit", f_path])
    assert exit_code == 0, f"Expected 0 for clean file but got {exit_code}"


def test_cli_audit_violating_file() -> None:
    """Verifies that running audit on invariant-violating code returns exit code 1."""
    bad_code = '''
def monolith_zero_asserts(x: int) -> int:
    return x * 10
'''
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(bad_code)
        f_path = f.name

    exit_code = main(["audit", f_path])
    assert exit_code == 1, f"Expected 1 for violating file but got {exit_code}"


def test_cli_cve_clean_package() -> None:
    """Verifies that running cve on a clean package returns exit code 0."""
    exit_code = main(["cve", "pydantic"])
    assert exit_code == 0, f"Expected 0 for clean package scan but got {exit_code}"


def test_cli_cve_vulnerable_package() -> None:
    """Verifies that running cve on a vulnerable package returns exit code 1."""
    exit_code = main(["cve", "vulnerable-demo-pkg"])
    assert exit_code == 1, f"Expected 1 for vulnerable package scan but got {exit_code}"
