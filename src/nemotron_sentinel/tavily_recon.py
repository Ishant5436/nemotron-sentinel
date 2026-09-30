"""Tavily Threat & CVE Reconnaissance Client.

Integrates Tavily Agentic Search API to inspect third-party library dependencies,
intercept CVE advisories, and evaluate supply-chain security risks.
Supports deterministic offline mock mode for reproducible CI execution.
"""

from __future__ import annotations

import ast
import os
import re
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field


class PackageRiskReport(BaseModel):
    """Structured security risk report for a package dependency."""
    package_name: str
    risk_level: str
    cve_identifiers: List[str] = Field(default_factory=list)
    summary: str
    references: List[str] = Field(default_factory=list)


class TavilyConfig(BaseModel):
    """Configuration settings for Tavily Agentic Search API."""
    api_key: str = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))
    api_url: str = "https://api.tavily.com/search"
    search_depth: str = "advanced"
    max_results: int = 5
    timeout_seconds: float = 15.0
    mock_mode: bool = Field(default_factory=lambda: not bool(os.getenv("TAVILY_API_KEY")))


def extract_imported_packages(source_code: str) -> List[str]:
    """Extract root imported package identifiers from Python source AST."""
    assert isinstance(source_code, str), "Source code must be provided as a string"
    assert len(source_code) >= 0, "Source code length must be non-negative"

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    packages: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0].strip()
                if root_pkg:
                    packages.add(root_pkg)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0].strip()
                if root_pkg:
                    packages.add(root_pkg)

    result = sorted(list(packages))
    assert isinstance(result, list), "Extracted package result must be a list"
    return result


class TavilyReconClient:
    """Agentic search client querying Tavily for package CVEs and vulnerabilities."""

    def __init__(self, config: Optional[TavilyConfig] = None) -> None:
        """Initialize client with validated configuration."""
        self.config = config or TavilyConfig()
        assert self.config.api_url.startswith("https://"), "Tavily API URL must use HTTPS"
        assert self.config.max_results > 0, "max_results must be strictly positive"

    def build_payload(self, package_name: str) -> Dict[str, Any]:
        """Construct JSON request payload for Tavily search endpoint."""
        assert isinstance(package_name, str) and len(package_name) > 0, "Package name required"
        assert self.config.search_depth in ["basic", "advanced"], "Search depth must be valid"

        query = f"{package_name} security vulnerability CVE exploit advisories 2025 2026"
        return {
            "api_key": self.config.api_key,
            "query": query,
            "search_depth": self.config.search_depth,
            "include_answer": True,
            "max_results": self.config.max_results,
        }

    def scan_package(self, package_name: str) -> PackageRiskReport:
        """Execute CVE threat reconnaissance for the specified package."""
        assert isinstance(package_name, str), "Package name must be a string"
        assert len(package_name.strip()) > 0, "Package name must not be blank"

        clean_pkg = package_name.strip()
        if self.config.mock_mode or not self.config.api_key:
            return self._execute_mock(clean_pkg)

        payload = self.build_payload(clean_pkg)
        return self._execute_http(payload, clean_pkg)

    def _execute_mock(self, package_name: str) -> PackageRiskReport:
        """Generate deterministic mock risk reports for offline testing."""
        assert package_name, "Package name cannot be empty"
        assert isinstance(package_name, str), "Package name must be a string"

        if "vulnerable" in package_name.lower():
            return PackageRiskReport(
                package_name=package_name,
                risk_level="HIGH",
                cve_identifiers=["CVE-2025-48192", "CVE-2026-10493"],
                summary=f"Simulated advisory: High-severity remote execution flaw discovered in {package_name}.",
                references=["https://nvd.nist.gov/vuln/detail/CVE-2025-48192"],
            )

        return PackageRiskReport(
            package_name=package_name,
            risk_level="CLEAN",
            cve_identifiers=[],
            summary=f"No active high-severity CVE advisories found for {package_name}.",
            references=[],
        )

    def _execute_http(self, payload: Dict[str, Any], package_name: str) -> PackageRiskReport:
        """Execute live search query against Tavily API."""
        assert isinstance(payload, dict), "Payload must be a dictionary"
        assert self.config.timeout_seconds > 0.0, "Timeout must be positive"

        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            resp = client.post(self.config.api_url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])
        combined_text = data.get("answer", "") + " " + " ".join(r.get("content", "") for r in results)

        cves = sorted(list(set(re.findall(r"CVE-\d{4}-\d{4,7}", combined_text))))
        risk = "HIGH" if len(cves) > 0 else "CLEAN"
        refs = [r.get("url", "") for r in results if r.get("url")]

        return PackageRiskReport(
            package_name=package_name,
            risk_level=risk,
            cve_identifiers=cves,
            summary=data.get("answer") or f"Identified {len(cves)} CVE advisories for {package_name}",
            references=refs[:3],
        )
