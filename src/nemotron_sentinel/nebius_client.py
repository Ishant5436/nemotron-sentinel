"""Nebius Token Factory Adapter.

Drives NVIDIA Nemotron models (nvidia/llama-3.1-nemotron-70b-instruct)
hosted on Nebius Token Factory using standard REST completion schemas.
Supports deterministic offline mock mode for reproducible CI execution.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field


class NebiusConfig(BaseModel):
    """Configuration settings for Nebius Token Factory client."""
    api_key: str = Field(default_factory=lambda: os.getenv("NEBIUS_API_KEY", ""))
    api_url: str = "https://api.studio.nebius.ai/v1/chat/completions"
    model: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout_seconds: float = 30.0
    mock_mode: bool = Field(default_factory=lambda: not bool(os.getenv("NEBIUS_API_KEY")))


class CompletionResponse(BaseModel):
    """Structured response from model inference."""
    content: str
    model_used: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class NebiusClient:
    """Client for querying NVIDIA Nemotron models on Nebius Token Factory."""

    def __init__(self, config: Optional[NebiusConfig] = None) -> None:
        """Initialize Nebius client with validated configuration."""
        self.config = config or NebiusConfig()
        assert self.config.model, "Model identifier cannot be empty"
        assert self.config.temperature >= 0.0, "Temperature cannot be negative"

    def build_payload(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Construct a standard completion request dictionary."""
        assert isinstance(prompt, str) and len(prompt) > 0, "Prompt must be non-empty string"
        assert max_tokens is None or max_tokens > 0, "max_tokens must be positive if provided"

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }

    def generate_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: Optional[int] = None,
    ) -> CompletionResponse:
        """Generate response via live Nebius Token Factory or deterministic mock."""
        assert isinstance(prompt, str), "Prompt must be a string"
        assert self.config.timeout_seconds > 0.0, "Timeout must be positive"

        if self.config.mock_mode or not self.config.api_key:
            return self._execute_mock(prompt, system_prompt)

        payload = self.build_payload(prompt, system_prompt, max_tokens)
        return self._execute_http(payload)

    def generate_code_repair(self, broken_code: str, violations: List[str]) -> str:
        """Prompt NVIDIA Nemotron to rewrite code resolving AST invariant violations."""
        assert isinstance(broken_code, str), "Broken code must be provided as a string"
        assert isinstance(violations, list), "Violations must be a list of strings"

        system_prompt = (
            "You are an expert deterministic systems engineer. "
            "Refactor the provided Python code so that every function is <= 60 lines, "
            "has at least 2 meaningful assertions, and has bounded loops. Output ONLY python code."
        )
        user_prompt = (
            f"Violations detected:\n{chr(10).join(violations)}\n\n"
            f"Original code:\n```python\n{broken_code}\n```"
        )

        resp = self.generate_completion(user_prompt, system_prompt)
        content = resp.content

        # Strip markdown fences if present
        if "```python" in content:
            content = content.split("```python", 1)[1].split("```", 1)[0].strip()
        elif "```" in content:
            content = content.split("```", 1)[1].split("```", 1)[0].strip()

        assert len(content) > 0, "Repaired code must be non-empty"
        return content

    def _execute_mock(self, prompt: str, system_prompt: str) -> CompletionResponse:
        """Produce deterministic mock responses for offline execution and testing."""
        assert prompt is not None, "Prompt cannot be None"
        assert system_prompt is not None, "System prompt cannot be None"

        if "Original code:" in prompt:
            # Deterministic repair mock
            repaired_code = (
                "def repaired_function(val: int) -> int:\n"
                "    assert isinstance(val, int), 'Value must be integer'\n"
                "    assert val >= 0, 'Value must be non-negative'\n"
                "    return val * 2\n"
            )
            return CompletionResponse(
                content=repaired_code,
                model_used=self.config.model,
                prompt_tokens=45,
                completion_tokens=32,
                total_tokens=77,
            )

        mock_content = f"[MOCK NVIDIA NEMOTRON RESPONSE] Processed prompt of length {len(prompt)}."
        return CompletionResponse(
            content=mock_content,
            model_used=self.config.model,
            prompt_tokens=10,
            completion_tokens=15,
            total_tokens=25,
        )

    def _execute_http(self, payload: Dict[str, Any]) -> CompletionResponse:
        """Execute HTTP request to Nebius Token Factory endpoint."""
        assert isinstance(payload, dict), "Payload must be a dictionary"
        assert self.config.api_key, "API key must be present for live HTTP calls"

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            resp = client.post(self.config.api_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        assert "choices" in data and len(data["choices"]) > 0, "Response missing choices"
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return CompletionResponse(
            content=content,
            model_used=data.get("model", self.config.model),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )
