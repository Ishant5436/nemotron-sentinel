"""Tests for the Tavily Threat & CVE Reconnaissance Client."""

from __future__ import annotations

import pytest
from nemotron_sentinel.tavily_recon import (
    TavilyReconClient,
    TavilyConfig,
    PackageRiskReport,
    extract_imported_packages,
)


def test_extract_imported_packages() -> None:
    """Verifies AST-based extraction of root package names from Python source code."""
    source_code = '''
import os
import sys
import httpx
from pydantic import BaseModel
from fastmcp.server import FastMCP
'''
    packages = extract_imported_packages(source_code)
    assert isinstance(packages, list), "Result must be a list"
    assert "httpx" in packages, "Should extract httpx"
    assert "pydantic" in packages, "Should extract pydantic"
    assert "fastmcp" in packages, "Should extract root package fastmcp"
    assert "os" in packages and "sys" in packages, "Should extract standard library imports"


def test_mock_cve_scan_clean_package() -> None:
    """Verifies that clean/safe packages return a CLEAN risk level in mock mode."""
    client = TavilyReconClient(TavilyConfig(mock_mode=True))
    report: PackageRiskReport = client.scan_package("pydantic")

    assert report.package_name == "pydantic", "Report package must match query"
    assert report.risk_level in ["CLEAN", "LOW"], "Standard library/safe package should have low/clean risk"
    assert isinstance(report.cve_identifiers, list), "CVE identifiers must be a list"


def test_mock_cve_scan_vulnerable_package() -> None:
    """Verifies that vulnerable packages return HIGH/MEDIUM risk with CVE identifiers."""
    client = TavilyReconClient(TavilyConfig(mock_mode=True))
    report: PackageRiskReport = client.scan_package("vulnerable-demo-pkg")

    assert report.package_name == "vulnerable-demo-pkg", "Package name must match"
    assert report.risk_level in ["HIGH", "CRITICAL"], "Vulnerable package must be flagged"
    assert len(report.cve_identifiers) > 0, "Must detect simulated CVE identifiers"
    assert any("CVE-" in cve for cve in report.cve_identifiers), "CVE format must be valid"


def test_tavily_payload_formatting() -> None:
    """Verifies that Tavily search request payload is formatted per Tavily API specs."""
    client = TavilyReconClient(TavilyConfig(api_key="mock_tavily_key", mock_mode=False))
    payload = client.build_payload(package_name="cryptography")

    assert payload["api_key"] == "mock_tavily_key", "Payload must contain API key"
    assert "cryptography" in payload["query"], "Query must reference target package"
    assert payload["search_depth"] in ["basic", "advanced"], "Search depth must be valid"
