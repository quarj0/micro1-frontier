#!/usr/bin/env python3
"""Thin Codex CLI adapter for the intentionally simple baseline workflow."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ADAPTER_DIR = Path(__file__).resolve().parent


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value


def require_path(variable: str) -> Path:
    value = os.environ.get(variable)
    if not value:
        raise RuntimeError(f"required environment variable is unset: {variable}")
    return Path(value)


def normalized_usage(
    events: list[dict[str, Any]], config: dict[str, Any], pricing: dict[str, Any]
) -> dict[str, Any]:
    usage: dict[str, Any] | None = None
    for event in events:
        if event.get("type") == "turn.completed" and isinstance(
            event.get("usage"), dict
        ):
            usage = event["usage"]

    result: dict[str, Any] = {
        "provider": "openai-codex-cli",
        "codex_cli_version": config["codex_cli_version"],
        "model": config["model"],
        "reasoning_effort": config["reasoning_effort"],
        "input_tokens": None,
        "cached_input_tokens": None,
        "output_tokens": None,
        "reasoning_output_tokens": None,
        "estimated_cost_usd": None,
        "billing_basis": (
            "api_key_estimate"
            if os.environ.get("CODEX_API_KEY")
            else "chatgpt_subscription_usage_only"
        ),
        "pricing": pricing,
    }
    if usage is None:
        result["usage_available"] = False
        return result

    for field in (
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    ):
        value = usage.get(field)
        result[field] = value if isinstance(value, int) else None
    result["usage_available"] = True

    if os.environ.get("CODEX_API_KEY"):
        input_tokens = int(result["input_tokens"] or 0)
        cached_tokens = int(result["cached_input_tokens"] or 0)
        output_tokens = int(result["output_tokens"] or 0)
        uncached_tokens = max(input_tokens - cached_tokens, 0)
        unit = float(pricing["unit_tokens"])
        estimate = (
            uncached_tokens * float(pricing["input_per_unit"])
            + cached_tokens * float(pricing["cached_input_per_unit"])
            + output_tokens * float(pricing["output_per_unit"])
        ) / unit
        result["estimated_cost_usd"] = round(estimate, 6)
    return result


def main() -> int:
    config = load_json(ADAPTER_DIR / "config.json")
    pricing = load_json(ADAPTER_DIR / "pricing.json")
    workspace = require_path("ARI_WORKSPACE").resolve()
    prompt_path = require_path("ARI_PROMPT_PATH").resolve()
    trajectory_path = require_path("ARI_TRAJECTORY_PATH").resolve()
    usage_path = require_path("ARI_USAGE_PATH").resolve()
    final_response_path = require_path("ARI_FINAL_RESPONSE_PATH").resolve()

    if os.environ.get("ARI_EXECUTION_MODE") == "docker":
        if not os.environ.get("CODEX_API_KEY"):
            print(
                "CODEX_API_KEY is required for the isolated Codex baseline",
                file=sys.stderr,
            )
            return 78
        codex_home = Path(os.environ.get("CODEX_HOME", ""))
        if codex_home != Path("/tmp/codex-home"):
            print(
                "Docker baseline requires fresh CODEX_HOME=/tmp/codex-home",
                file=sys.stderr,
            )
            return 78
        codex_home.mkdir(mode=0o700, parents=True, exist_ok=True)
        if any(codex_home.iterdir()):
            print("Docker baseline CODEX_HOME was not fresh", file=sys.stderr)
            return 78

    installed_version = subprocess.run(
        ["codex", "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    expected_version = f"codex-cli {config['codex_cli_version']}"
    if (
        installed_version.returncode != 0
        or installed_version.stdout.strip() != expected_version
    ):
        print(
            f"expected {expected_version}, got {installed_version.stdout.strip()!r}",
            file=sys.stderr,
        )
        return 78

    command = [
        "codex",
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--model",
        str(config["model"]),
        "--config",
        f'model_reasoning_effort="{config["reasoning_effort"]}"',
        "--color",
        "never",
        "--output-last-message",
        str(final_response_path),
        "--cd",
        str(workspace),
    ]
    for feature in config["disabled_features"]:
        command.extend(["--disable", str(feature)])
    if os.environ.get("ARI_EXECUTION_MODE") == "docker":
        command.append("--dangerously-bypass-approvals-and-sandbox")
    else:
        command.append("--approve-for-me")
    command.append("-")

    completed = subprocess.run(
        command,
        input=prompt_path.read_text(encoding="utf-8"),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=workspace,
        check=False,
    )
    trajectory_path.write_text(completed.stdout, encoding="utf-8")
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)

    events: list[dict[str, Any]] = []
    parse_errors: list[str] = []
    for line_number, line in enumerate(completed.stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            parse_errors.append(f"line {line_number}: {exc.msg}")
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            parse_errors.append(f"line {line_number}: event is not an object")

    usage = normalized_usage(events, config, pricing)
    usage["trajectory_parse_errors"] = parse_errors
    usage_path.write_text(
        json.dumps(usage, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
