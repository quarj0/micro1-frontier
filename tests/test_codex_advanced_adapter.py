from __future__ import annotations

import json
from pathlib import Path

from agents.codex_advanced.adapter import aggregate_usage


ROOT = Path(__file__).resolve().parents[1]


def test_advanced_and_baseline_hold_model_controls_constant():
    baseline = json.loads(
        (ROOT / "agents" / "codex-baseline" / "config.json").read_text()
    )
    advanced = json.loads(
        (ROOT / "agents" / "codex_advanced" / "config.json").read_text()
    )

    for field in (
        "codex_cli_version",
        "model",
        "reasoning_effort",
        "disabled_features",
    ):
        assert advanced[field] == baseline[field]
    assert advanced["maximum_retries"] == 1


def test_advanced_usage_sums_both_turns(monkeypatch):
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    config = {
        "codex_cli_version": "0.150.1",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "medium",
    }
    pricing = {
        "unit_tokens": 1_000_000,
        "input_per_unit": 4,
        "cached_input_per_unit": 0.4,
        "output_per_unit": 20,
    }
    events = [
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 100,
                "cached_input_tokens": 50,
                "output_tokens": 10,
                "reasoning_output_tokens": 3,
            },
        },
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 200,
                "cached_input_tokens": 100,
                "output_tokens": 20,
                "reasoning_output_tokens": 4,
            },
        },
    ]

    usage = aggregate_usage(events, config, pricing, retry_count=1)

    assert usage["turns"] == 2
    assert usage["input_tokens"] == 300
    assert usage["output_tokens"] == 30
    assert usage["retry_count"] == 1
