from __future__ import annotations

import importlib.util
from pathlib import Path


ADAPTER_PATH = (
    Path(__file__).resolve().parents[1] / "agents" / "codex-baseline" / "adapter.py"
)
SPEC = importlib.util.spec_from_file_location("codex_baseline_adapter", ADAPTER_PATH)
assert SPEC is not None and SPEC.loader is not None
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


def test_normalized_usage_captures_tokens_and_api_key_cost(monkeypatch):
    monkeypatch.setenv("CODEX_API_KEY", "test-only")
    config = {
        "codex_cli_version": "0.150.1",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "medium",
    }
    pricing = {
        "unit_tokens": 1_000_000,
        "input_per_unit": 4.0,
        "cached_input_per_unit": 0.4,
        "output_per_unit": 20.0,
    }
    events = [
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 1_000,
                "cached_input_tokens": 400,
                "output_tokens": 100,
                "reasoning_output_tokens": 25,
            },
        }
    ]

    usage = ADAPTER.normalized_usage(events, config, pricing)

    assert usage["model"] == "gpt-5.6-sol"
    assert usage["reasoning_effort"] == "medium"
    assert usage["estimated_cost_usd"] == 0.00456


def test_chatgpt_authenticated_usage_has_no_dollar_cost(monkeypatch):
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    usage = ADAPTER.normalized_usage(
        [{"type": "turn.completed", "usage": {"input_tokens": 10}}],
        {
            "codex_cli_version": "0.150.1",
            "model": "gpt-5.6-sol",
            "reasoning_effort": "medium",
        },
        {},
    )

    assert usage["billing_basis"] == "chatgpt_subscription_usage_only"
    assert usage["estimated_cost_usd"] is None

