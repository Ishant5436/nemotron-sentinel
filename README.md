# Nemotron-Sentinel

**Autonomous Deterministic Developer Safety & Verification Agent**  
*Built for the Nebius x NVIDIA Global AI Hackathon (Coding and Agentic Engineering Track + Best Use of Tavily)*

---

## 1. Overview

Autonomous coding agents (such as SWE-bench runners and IDE copilots) generate syntactically valid code that frequently harbors structural anomalies: unbounded loops, missing precondition checks, monolithic functions, and unvetted third-party dependencies containing known CVEs.

**Nemotron-Sentinel** provides a deterministic safety and verification layer for agentic software engineering:
1. **NVIDIA Nemotron Reasoning Core:** Driven by `nvidia/llama-3.1-nemotron-70b-instruct` served on **Nebius Token Factory**, executing high-precision AST refactoring, invariant enforcement, and test synthesis.
2. **Tavily Agentic Threat Reconnaissance:** Intercepts package imports and automatically queries Tavily Search for live zero-day advisories and CVE vulnerability disclosures.
3. **Deterministic AST Safety Engine:** Mechanically enforces Gerard J. Holzmann's structural safety standards (function length $\le 60$ lines, assertion density $\ge 2$, bounded loops, recursion prevention).
4. **Autonomous TDD Sandbox Engine:** Generates tests, executes them in isolated subprocesses, and iteratively prompts Nemotron to repair defects until 100% test pass rates are achieved.
5. **FastMCP Server & CLI:** Exposes standard FastMCP tools for integration into agent runtimes and modern IDEs alongside a standalone terminal interface.

---

## 2. Architecture

```
                             +----------------------------------------+
                             |       Client Interface Layer           |
                             |  - CLI: nemotron-sentinel              |
                             |  - FastMCP Server: stdio / stream HTTP |
                             +-------------------+--------------------+
                                                 |
                                                 v
                             +----------------------------------------+
                             |      Nemotron-Sentinel Core Engine     |
                             +-------------------+--------------------+
                                                 |
         +-----------------------+---------------+-----------------------+
         |                       |                                       |
         v                       v                                       v
+-----------------+     +-----------------+                     +-----------------+
|  Nebius Client  |     |  Tavily Client  |                     |  Safety Auditor |
|  - Token Factory|     |  - Agentic CVE  |                     |  - Safety Invar |
|  - Nemotron-70B |     |    Intelligence |                     |  - AST Analyzer |
|  - TDD Repair   |     |  - Supply-Chain |                     |  - Bounds Check |
+-----------------+     +-----------------+                     +-----------------+
         |                       |                                       |
         +-----------------------+---------------+-----------------------+
                                                 |
                                                 v
                               +-----------------------------------+
                               |     Autonomous TDD Runner         |
                               |  - Generate Failing Tests (Red)   |
                               |  - Execute Sandbox Subprocess     |
                               |  - Iterative Fix Loop (Green)     |
                               |  - Mechanical Invariant Proof     |
                               +-----------------------------------+
```

---

## 3. Installation & Quickstart

### Prerequisites
- Python 3.12 or 3.13
- [`uv`](https://github.com/astral-sh/uv) (recommended) or standard `pip`

```bash
# Clone repository
git clone https://github.com/Ishant5436/nemotron-sentinel.git
cd nemotron-sentinel

# Create environment and install dependencies
uv venv --python python3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Environment Configuration (Optional)
Nemotron-Sentinel includes deterministic offline mock adapters for zero-network testing. To enable live inference:

```bash
export NEBIUS_API_KEY="your-nebius-token-factory-key"
export TAVILY_API_KEY="tvly-your-tavily-key"
```

---

## 4. CLI Usage

### 4.1 Static AST Safety Invariant Audit
Scan source code against deterministic structural safety invariants:
```bash
nemotron-sentinel audit src/nemotron_sentinel/ast_invariants.py
```
Output:
```
[*] Audited 7 functions in src/nemotron_sentinel/ast_invariants.py
[PASS] All deterministic safety invariants satisfied (0 violations).
```

### 4.2 Agentic CVE Threat Reconnaissance (Tavily)
Intercept and evaluate security risks for third-party dependencies:
```bash
nemotron-sentinel cve pydantic
```
Output:
```
[*] Package: pydantic
[*] Risk Level: CLEAN
[*] Summary: No active high-severity CVE advisories found for pydantic.
```

### 4.3 Autonomous TDD Repair Cycle
Run an automated Red-to-Green repair loop on a target source file against a test suite:
```bash
nemotron-sentinel tdd buggy_module.py test_buggy_module.py
```

### 4.4 Launch FastMCP Server
Run the FastMCP server over standard I/O for integration with agent runtimes:
```bash
nemotron-sentinel mcp
```

---

## 5. FastMCP Configuration

Add Nemotron-Sentinel to your `mcp_config.json` or host MCP configuration:

```json
{
  "mcpServers": {
    "nemotron-sentinel": {
      "command": "/path/to/nemotron-sentinel/.venv/bin/nemotron-sentinel",
      "args": ["mcp"],
      "env": {
        "NEBIUS_API_KEY": "your-nebius-token-factory-key",
        "TAVILY_API_KEY": "tvly-your-tavily-key"
      }
    }
  }
}
```

### Available FastMCP Tools
- `nemotron_audit_ast`: Audits code against structural safety invariants.
- `nemotron_cve_scan`: Runs Tavily agentic threat intelligence on dependencies.
- `nemotron_repair_invariants`: Invokes NVIDIA Nemotron on Nebius Token Factory to rewrite code resolving safety violations.
- `nemotron_generate_tdd`: Executes sandboxed pytest suites and iterative repair loops.

---

## 6. Verification & Safety Standards

Nemotron-Sentinel enforces and complies with Gerard J. Holzmann's Deterministic Safety Standards across its entire codebase:
- **Function Length:** Every function is $\le 60$ lines.
- **Assertion Density:** Every function maintains $\ge 2$ assertions.
- **Bounded Loops:** Unbounded loops without deterministic breaks are strictly rejected.
- **Recursion Prevention:** Direct and indirect recursion are prohibited.

Run the test suite and self-audit:
```bash
# Run 100% green test suite
pytest -v --cov=nemotron_sentinel

# Run mechanical AST invariant self-audit
python scripts/audit_invariants.py
```

---

## 7. License

MIT License. Copyright (c) 2026 Ishant Panchal.
