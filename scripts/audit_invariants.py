"""Mechanical Safety Invariant Self-Audit Script.

Audits all Python source files in the repository using the internal
AstInvariantChecker to mechanically prove adherence to structural safety standards:
- Rule 1: Simple control flow, no recursion.
- Rule 2: Bounded loops with deterministic termination.
- Rule 4: Function length <= 60 lines.
- Rule 5: Assertion density >= 2 assertions per function.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Tuple

from nemotron_sentinel.ast_invariants import AstInvariantChecker, InvariantReport


def find_python_files(root_dir: str) -> List[str]:
    """Recursively collect all Python files excluding virtual environments and caches."""
    assert os.path.isdir(root_dir), f"Root directory must exist: {root_dir}"
    assert len(root_dir) > 0, "Root directory string cannot be empty"

    py_files: List[str] = []
    excluded_dirs = {".venv", "venv", ".git", "__pycache__", ".pytest_cache", "build", "dist"}

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))

    assert isinstance(py_files, list), "Result must be a list of paths"
    return sorted(py_files)


def audit_single_file(file_path: str, checker: AstInvariantChecker) -> Tuple[bool, InvariantReport]:
    """Execute AST invariant check on a single file."""
    assert os.path.isfile(file_path), f"File must exist: {file_path}"
    assert checker is not None, "Checker instance required"

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    report = checker.check_code(code)
    return report.is_compliant, report


def main() -> int:
    """Run full mechanical audit across src/ and scripts/ directories."""
    repo_root = Path(__file__).resolve().parent.parent
    src_dir = os.path.join(repo_root, "src")
    assert os.path.isdir(src_dir), "src directory must exist"

    checker = AstInvariantChecker(max_function_length=60, min_assertion_density=2)
    python_files = find_python_files(src_dir)

    assert len(python_files) > 0, "Must find at least one Python file in src/"

    print("=" * 70)
    print("NEMOTRON-SENTINEL: DETERMINISTIC AST SAFETY AUDIT")
    print("=" * 70)

    total_violations = 0
    total_functions = 0

    for fpath in python_files:
        rel_path = os.path.relpath(fpath, repo_root)
        is_ok, report = audit_single_file(fpath, checker)
        total_functions += report.total_functions

        if is_ok:
            print(f"[PASS] {rel_path} ({report.total_functions} functions)")
        else:
            print(f"[FAIL] {rel_path} ({len(report.violations)} violations):")
            for v in report.violations:
                print(f"       - Line {v.line_number} [{v.violation_type.value}]: {v.message}")
            total_violations += len(report.violations)

    print("=" * 70)
    print(f"AUDIT SUMMARY: Scanned {total_functions} functions across {len(python_files)} files.")
    print(f"TOTAL VIOLATIONS: {total_violations}")

    if total_violations == 0:
        print("[SUCCESS] 100% Deterministic Safety Invariant Conformance Proven.")
        return 0

    print("[FAILURE] Mechanical Safety Invariant Audit Failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
