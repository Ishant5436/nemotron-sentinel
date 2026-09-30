# Nemotron-Sentinel: Devpost Hackathon Submission

**Project Name:** Nemotron-Sentinel  
**Elevator Pitch:** Autonomous Deterministic Developer Safety & Verification Agent powered by NVIDIA Nemotron on Nebius Token Factory and Tavily Agentic Intelligence.  
**Track:** Coding and Agentic Engineering Track  
**Mini-Challenge:** Best Use of Tavily ($3,000 Cash)  

---

### 1. Inspiration
As software development pivots rapidly toward autonomous coding agents, an engineering challenge has emerged: code generators frequently produce syntactically valid code that hides structural defects—unbounded `while True` loops, missing precondition checks, monolithic functions, and outdated third-party libraries harboring critical CVEs. Traditional linters only check syntax formatting, while unconstrained generators cannot mechanically prove safety. We set out to build an institutional, deterministic verification layer that combines Gerard J. Holzmann's structural safety standards with NVIDIA Nemotron's reasoning capabilities and Tavily's live vulnerability intelligence.

---

### 2. What It Does
**Nemotron-Sentinel** operates as both a standalone developer CLI (`nemotron-sentinel`) and a high-performance **FastMCP Server** (compatible with modern agent harnesses and IDEs):
1. **Static AST Safety Invariant Engine:** Mechanically audits code ASTs to enforce structural safety standards:
   - Rule 1: Simple control flow, no recursion.
   - Rule 2: Bounded loops with deterministic termination guards.
   - Rule 4: Maximum function length $\le 60$ lines.
   - Rule 5: Minimum assertion density $\ge 2$ assertions per function.
2. **Agentic Threat & CVE Reconnaissance (Tavily):** Intercepts package dependencies from source ASTs and queries Tavily Search for live zero-day advisories, known CVEs, and supply-chain exploits.
3. **NVIDIA Nemotron Reasoning Core (Nebius Token Factory):** Uses `nvidia/llama-3.1-nemotron-70b-instruct` served on Nebius Token Factory with low temperature (0.1) to synthesize targeted test suites and refactor code resolving safety violations.
4. **Autonomous TDD Sandbox Engine:** Executes test suites in isolated subprocess environments with strict execution timeouts, capturing failure telemetry to drive iterative Red-to-Green repair loops.

---

### 3. How We Built It
- **Language & Frameworks:** Built in Python 3.12 using the standard library `ast`, `httpx` for asynchronous HTTP communication, `pydantic` for schema validation, and `mcp` (`FastMCP`) for agent tool exposure.
- **Model Infrastructure:** Integrated with **Nebius Token Factory** endpoints (`https://api.studio.nebius.ai/v1/chat/completions`) driving `nvidia/llama-3.1-nemotron-70b-instruct`.
- **Search Intelligence:** Integrated with **Tavily Agentic Search** (`https://api.tavily.com/search`) for vulnerability reconnaissance.
- **Verification Matrix:** 28 automated unit and integration tests spanning AST validation, mock and live HTTP calls, TDD subprocess execution, and FastMCP schemas.
- **Self-Audit:** The repository audited itself using `scripts/audit_invariants.py`, proving that all 34 functions in the codebase strictly comply with the structural safety standards (0 violations).

---

### 4. Challenges We Ran Into
- **Sandboxed Subprocess Reliability:** Capturing test telemetry from isolated test executions across platforms without subprocess deadlocks required strict monotonic timing and stdout/stderr decoupling.
- **Deterministic Prompt Alignment:** Prompting general models often yields conversational chatter that breaks automated repair. Calibrating prompts for NVIDIA Nemotron ensured strict, clean code returns that drop straight into the sandbox runner.
- **Zero-Dependency AST Traversal:** Building a deterministic AST analyzer without heavy external linters required recursive AST node inspection handling Python 3.12 syntax variants.

---

### 5. Accomplishments We're Proud Of
- **Zero Invariant Violations:** 100% adherence to structural safety standards across all 34 internal functions.
- **Comprehensive Test Suite:** 28 passing tests with 85% test coverage in under 2 seconds.
- **Dual Accessibility:** Directly operable via standard developer terminal commands and as an enterprise FastMCP server.
- **Tavily Integration:** Direct extraction of imports to query CVE databases dynamically without manual configuration.

---

### 6. What We Learned
NVIDIA's Nemotron family excels at structured, low-temperature logical tasks. Where other models often drift into prose or conversational apologies, Nemotron consistently adheres to rigid output contracts (like raw code without markdown wrapping), making it ideal for autonomous agent loops.

---

### 7. What's Next for Nemotron-Sentinel
- Expanding AST inspection to C/C++ via `libclang` to enforce safety invariants in systems programming.
- Pre-commit and GitHub Actions integration to automatically block PRs that fail safety standards or contain unvetted CVEs.
- Autonomous PR auto-remediation bots deploying Nemotron-Sentinel in large open-source repositories.

---

### 8. Feedback for Nebius & NVIDIA
- **Nebius Token Factory:** Extremely fast token latency and predictable standard REST completion endpoint compatibility. The developer console experience and credit activation were frictionless.
- **NVIDIA Nemotron:** Outstanding capability for structured code generation and refactoring tasks. Expanding documentation on Nemotron-specific prompt engineering best practices would further accelerate developer adoption.
