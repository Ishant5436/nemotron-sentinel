"""Unit tests asserting deterministic execution of worker."""

from target import repaired_function


def test_repaired_function_deterministic() -> None:
    """Verifies that repaired function executes deterministically."""
    res = repaired_function(10)
    assert res == 20, f"Expected 20 but got {res}"
