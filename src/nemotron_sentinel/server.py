"""FastMCP Gateway Server.

Exposes deterministic code safety and verification tools for AI agents
(compatible with modern agent harnesses and IDEs):
1. nemotron_audit_ast: Static AST verification of safety invariants.
2. nemotron_cve_scan: Agentic Tavily intelligence on package dependencies.
3. nemotron_repair_invariants: NVIDIA Nemotron-powered code repair on Nebius Token Factory.
4. nemotron_generate_tdd: Autonomous sandboxed TDD execution and repair.
"""

from __future__ import annotations

from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP

from nemotron_sentinel.ast_invariants import AstInvariantChecker
from nemotron_sentinel.nebius_client import NebiusClient
from nemotron_sentinel.tavily_recon import TavilyReconClient
from nemotron_sentinel.tdd_runner import run_tdd_cycle

# FastMCP Server Instance
mcp = FastMCP("nemotron-sentinel")

_checker = AstInvariantChecker()
_nebius = NebiusClient()
_tavily = TavilyReconClient()


@mcp.tool()
def nemotron_audit_ast(code: str) -> Dict[str, Any]:
    """Audit Python source code against deterministic safety invariants."""
    assert isinstance(code, str), "Code must be provided as a string"
    assert len(code) >= 0, "Code length must be non-negative"

    report = _checker.check_code(code)
    return report.model_dump()


@mcp.tool()
def nemotron_cve_scan(packages: List[str]) -> Dict[str, Any]:
    """Perform agentic threat reconnaissance for a list of library packages."""
    assert isinstance(packages, list), "Packages must be provided as a list"
    assert len(packages) >= 0, "Package list length must be non-negative"

    reports = [_tavily.scan_package(pkg).model_dump() for pkg in packages if pkg.strip()]
    return {"reports": reports, "total_scanned": len(reports)}


@mcp.tool()
def nemotron_repair_invariants(broken_code: str, violations: List[str]) -> Dict[str, Any]:
    """Prompt NVIDIA Nemotron on Nebius Token Factory to repair safety violations."""
    assert isinstance(broken_code, str) and len(broken_code) > 0, "Broken code required"
    assert isinstance(violations, list), "Violations list required"

    repaired = _nebius.generate_code_repair(broken_code, violations)
    return {
        "repaired_code": repaired,
        "violations_addressed": violations,
        "model_used": _nebius.config.model,
    }


@mcp.tool()
def nemotron_generate_tdd(source_code: str, test_code: str) -> Dict[str, Any]:
    """Execute autonomous Red-to-Green sandboxed TDD cycle with Nemotron repair."""
    assert isinstance(source_code, str) and len(source_code) > 0, "Source code required"
    assert isinstance(test_code, str) and len(test_code) > 0, "Test code required"

    cycle_result = run_tdd_cycle(
        target_code=source_code,
        test_code=test_code,
        nebius_client=_nebius,
        max_iterations=3,
    )
    return cycle_result.model_dump()


def run_server() -> None:
    """Entrypoint to launch the FastMCP server over standard I/O."""
    assert mcp is not None, "MCP instance must be initialized"
    assert mcp.name == "nemotron-sentinel", "MCP server name must be verified"
    mcp.run()
