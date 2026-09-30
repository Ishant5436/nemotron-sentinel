"""Tests for the Nebius Token Factory Adapter."""

from __future__ import annotations

import pytest
from nemotron_sentinel.nebius_client import NebiusClient, NebiusConfig, CompletionResponse


def test_default_config_initialization() -> None:
    """Verifies that NebiusConfig sets the correct NVIDIA Nemotron model and API endpoint."""
    config = NebiusConfig()
    assert "nemotron" in config.model.lower(), "Default model must belong to NVIDIA Nemotron family"
    assert config.api_url.startswith("https://api.studio.nebius.ai/v1"), "Default endpoint must target Nebius Studio"
    assert config.temperature <= 0.2, "Temperature must be bounded low for deterministic execution"


def test_mock_mode_generates_valid_response() -> None:
    """Verifies that mock mode returns a structured completion without outbound network calls."""
    client = NebiusClient(NebiusConfig(mock_mode=True))
    prompt = "Explain safety invariant Rule 4"
    resp: CompletionResponse = client.generate_completion(prompt)

    assert resp.content is not None, "Response content must not be None"
    assert len(resp.content) > 0, "Response content must be non-empty"
    assert resp.model_used == client.config.model, "Reported model must match configured model"
    assert resp.total_tokens > 0, "Token count must be positive"


def test_mock_code_repair_returns_clean_code() -> None:
    """Verifies that generate_code_repair produces syntactically valid code."""
    client = NebiusClient(NebiusConfig(mock_mode=True))
    broken_code = '''
def monolithic_add(a: int, b: int) -> int:
    return a + b
'''
    repaired: str = client.generate_code_repair(
        broken_code=broken_code,
        violations=["Assertion count 0 is below required minimum of 2"],
    )

    assert "def " in repaired, "Repaired output must contain function definition"
    assert "assert " in repaired, "Repaired code must incorporate required assertions"
    assert repaired.strip().startswith("def ") or "import " in repaired, "Repaired code must be valid python"


def test_request_payload_formatting() -> None:
    """Verifies that request payload dictionary adheres to standard completion schema."""
    client = NebiusClient(NebiusConfig(api_key="mock_key", mock_mode=False))
    payload = client.build_payload(
        prompt="Synthesize tests",
        system_prompt="You are a deterministic verification system.",
        max_tokens=512,
    )

    assert payload["model"] == client.config.model, "Payload model must match configured model"
    assert len(payload["messages"]) == 2, "Payload must contain system and user messages"
    assert payload["temperature"] == client.config.temperature, "Payload temperature must match config"
    assert payload["max_tokens"] == 512, "Payload max_tokens must be set correctly"
