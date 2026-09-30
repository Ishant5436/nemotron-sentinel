"""Institutional CLI Terminal Interface.

Provides deterministic developer safety commands:
- nemotron-sentinel audit <file>: Static AST safety invariant verification.
- nemotron-sentinel cve <package>: Agentic threat reconnaissance via Tavily.
- nemotron-sentinel tdd <source> <test>: Autonomous Red-to-Green repair cycle.
- nemotron-sentinel mcp: Launch FastMCP server over standard I/O.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from nemotron_sentinel.ast_invariants import AstInvariantChecker
from nemotron_sentinel.nebius_client import NebiusClient
from nemotron_sentinel.server import run_server
from nemotron_sentinel.tavily_recon import TavilyReconClient
from nemotron_sentinel.tdd_runner import run_tdd_cycle


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="nemotron-sentinel",
        description="Autonomous Deterministic Developer Safety & Verification Agent",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # audit subcommand
    audit_parser = subparsers.add_parser("audit", help="Verify AST safety invariants")
    audit_parser.add_argument("target", help="Path to Python file to audit")

    # cve subcommand
    cve_parser = subparsers.add_parser("cve", help="Scan package dependency for known CVEs")
    cve_parser.add_argument("package", help="Package identifier to scan")

    # tdd subcommand
    tdd_parser = subparsers.add_parser("tdd", help="Run autonomous Red-to-Green TDD cycle")
    tdd_parser.add_argument("target_file", help="Path to target source file")
    tdd_parser.add_argument("test_file", help="Path to pytest test file")

    # mcp subcommand
    subparsers.add_parser("mcp", help="Launch FastMCP stdio server")

    assert parser.prog == "nemotron-sentinel", "Parser identity must be preserved"
    assert len(parser._actions) > 0, "Parser must register actions"
    return parser


def _handle_audit(target_path: str) -> int:
    """Execute AST safety invariant check on target file."""
    assert isinstance(target_path, str), "Target path must be a string"
    assert len(target_path) > 0, "Target path cannot be empty"

    if not os.path.isfile(target_path):
        print(f"[ERROR] Target file not found: {target_path}", file=sys.stderr)
        return 1

    with open(target_path, "r", encoding="utf-8") as f:
        code = f.read()

    checker = AstInvariantChecker()
    report = checker.check_code(code)

    print(f"[*] Audited {report.total_functions} functions in {target_path}")
    if report.is_compliant:
        print("[PASS] All deterministic safety invariants satisfied (0 violations).")
        return 0

    print(f"[FAIL] Detected {len(report.violations)} safety invariant violations:")
    for v in report.violations:
        print(f"  - Line {v.line_number} [{v.violation_type.value}]: {v.message}")
    return 1


def _handle_cve(package_name: str) -> int:
    """Execute Tavily CVE reconnaissance on specified package."""
    assert isinstance(package_name, str), "Package name must be string"
    assert len(package_name.strip()) > 0, "Package name cannot be blank"

    client = TavilyReconClient()
    report = client.scan_package(package_name.strip())

    print(f"[*] Package: {report.package_name}")
    print(f"[*] Risk Level: {report.risk_level}")
    print(f"[*] Summary: {report.summary}")

    if report.cve_identifiers:
        print(f"[!] CVE Advisories: {', '.join(report.cve_identifiers)}")
        return 1
    return 0


def _handle_tdd(target_path: str, test_path: str) -> int:
    """Execute autonomous Red-to-Green repair cycle on source and test files."""
    assert os.path.isfile(target_path), f"Source file must exist: {target_path}"
    assert os.path.isfile(test_path), f"Test file must exist: {test_path}"

    with open(target_path, "r", encoding="utf-8") as f:
        target_code = f.read()
    with open(test_path, "r", encoding="utf-8") as f:
        test_code = f.read()

    result = run_tdd_cycle(target_code=target_code, test_code=test_code)
    print(f"[*] TDD Cycle Completed: {result.iterations} iterations")
    print(f"[*] Success: {result.success}, Invariant Compliant: {result.invariant_compliant}")

    if result.success and result.iterations > 0:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(result.final_code)
        print(f"[+] Successfully wrote repaired code back to {target_path}")
        return 0
    return 0 if result.success else 1


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint with deterministic dispatch."""
    args_list = argv if argv is not None else sys.argv[1:]
    assert isinstance(args_list, list), "Arguments must be a list"

    parser = build_parser()
    try:
        args = parser.parse_args(args_list)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 0

    assert hasattr(args, "subcommand"), "Parsed arguments must have subcommand"

    if args.subcommand == "audit":
        return _handle_audit(args.target)
    if args.subcommand == "cve":
        return _handle_cve(args.package)
    if args.subcommand == "tdd":
        return _handle_tdd(args.target_file, args.test_file)
    if args.subcommand == "mcp":
        run_server()
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
