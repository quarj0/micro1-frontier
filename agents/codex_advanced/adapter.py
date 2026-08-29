#!/usr/bin/env python3
"""One-agent evidence workflow with at most one controller-granted retry."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from .evidence import merge_retry, should_retry, validate_evidence
except ImportError:  # Direct script execution inside the benchmark image.
    from evidence import merge_retry, should_retry, validate_evidence

ADAPTER_DIR = Path(__file__).resolve().parent
BASELINE_DIR = ADAPTER_DIR.parent / "codex-baseline"


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


def parse_events(raw: str) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: {exc.msg}")
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            errors.append(f"line {line_number}: event is not an object")
    return events, errors


def aggregate_usage(
    events: list[dict[str, Any]],
    config: dict[str, Any],
    pricing: dict[str, Any],
    retry_count: int,
) -> dict[str, Any]:
    fields = (
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    )
    totals = {field: 0 for field in fields}
    turns = 0
    for event in events:
        usage = event.get("usage")
        if event.get("type") != "turn.completed" or not isinstance(usage, dict):
            continue
        turns += 1
        for field in fields:
            value = usage.get(field)
            if isinstance(value, int):
                totals[field] += value

    api_key_run = bool(os.environ.get("CODEX_API_KEY"))
    result: dict[str, Any] = {
        "provider": "openai-codex-cli",
        "codex_cli_version": config["codex_cli_version"],
        "model": config["model"],
        "reasoning_effort": config["reasoning_effort"],
        **{field: totals[field] if turns else None for field in fields},
        "estimated_cost_usd": None,
        "billing_basis": (
            "api_key_estimate" if api_key_run else "chatgpt_subscription_usage_only"
        ),
        "pricing": pricing,
        "usage_available": bool(turns),
        "turns": turns,
        "retry_count": retry_count,
    }
    if api_key_run and turns:
        uncached = max(totals["input_tokens"] - totals["cached_input_tokens"], 0)
        unit = float(pricing["unit_tokens"])
        estimate = (
            uncached * float(pricing["input_per_unit"])
            + totals["cached_input_tokens"]
            * float(pricing["cached_input_per_unit"])
            + totals["output_tokens"] * float(pricing["output_per_unit"])
        ) / unit
        result["estimated_cost_usd"] = round(estimate, 6)
    return result


def codex_command(
    config: dict[str, Any], workspace: Path, output_path: Path
) -> list[str]:
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
        "--output-schema",
        str(ADAPTER_DIR / "evidence-output.schema.json"),
        "--output-last-message",
        str(output_path),
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
    return command


def run_turn(
    config: dict[str, Any],
    workspace: Path,
    prompt: str,
    output_path: Path,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        codex_command(config, workspace, output_path),
        input=prompt,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=workspace,
        env=environment,
        check=False,
    )


def read_result(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def changed_files(workspace: Path, baseline_revision: str) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", baseline_revision],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return completed.stdout.splitlines()


def main() -> int:
    config = load_json(ADAPTER_DIR / "config.json")
    pricing = load_json(BASELINE_DIR / "pricing.json")
    workspace = require_path("ARI_WORKSPACE").resolve()
    prompt_path = require_path("ARI_PROMPT_PATH").resolve()
    trajectory_path = require_path("ARI_TRAJECTORY_PATH").resolve()
    evidence_path = require_path("ARI_EVIDENCE_PATH").resolve()
    usage_path = require_path("ARI_USAGE_PATH").resolve()
    final_response_path = require_path("ARI_FINAL_RESPONSE_PATH").resolve()

    if os.environ.get("ARI_WORKFLOW") != "advanced-v1":
        print("codex-advanced requires ARI_WORKFLOW=advanced-v1", file=sys.stderr)
        return 78
    if os.environ.get("ARI_EXECUTION_MODE") == "docker":
        if not os.environ.get("CODEX_API_KEY"):
            print(
                "CODEX_API_KEY is required for the isolated Codex advanced workflow",
                file=sys.stderr,
            )
            return 78
        codex_home = Path(os.environ.get("CODEX_HOME", ""))
        if codex_home != Path("/tmp/codex-home"):
            print(
                "Docker advanced workflow requires fresh CODEX_HOME=/tmp/codex-home",
                file=sys.stderr,
            )
            return 78
        codex_home.mkdir(mode=0o700, parents=True, exist_ok=True)
        if any(codex_home.iterdir()):
            print("Docker advanced CODEX_HOME was not fresh", file=sys.stderr)
            return 78

    installed = subprocess.run(
        ["codex", "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    expected = f"codex-cli {config['codex_cli_version']}"
    if installed.returncode != 0 or installed.stdout.strip() != expected:
        print(f"expected {expected}, got {installed.stdout.strip()!r}", file=sys.stderr)
        return 78

    baseline_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout.strip()
    codex_environment = os.environ.copy()
    codex_environment["PYTHONDONTWRITEBYTECODE"] = "1"
    codex_environment["UV_PROJECT_ENVIRONMENT"] = sys.prefix
    temporary_home: tempfile.TemporaryDirectory[str] | None = None
    if os.environ.get("ARI_EXECUTION_MODE") != "docker":
        original_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        temporary_home = tempfile.TemporaryDirectory(prefix="ari-codex-home-")
        isolated_home = Path(temporary_home.name)
        isolated_home.chmod(0o700)
        auth_file = original_home / "auth.json"
        if auth_file.is_file():
            isolated_auth = isolated_home / "auth.json"
            shutil.copyfile(auth_file, isolated_auth)
            isolated_auth.chmod(0o600)
        codex_environment["CODEX_HOME"] = str(isolated_home)

    first_output = workspace / ".ari" / "advanced-turn-1.json"
    first = run_turn(
        config,
        workspace,
        prompt_path.read_text(encoding="utf-8"),
        first_output,
        codex_environment,
    )
    raw_outputs = [first.stdout]
    stderr_outputs = [first.stderr]
    events, parse_errors = parse_events(first.stdout)
    result = read_result(first_output)
    retry_count = 0
    final_exit_code = first.returncode

    if (
        first.returncode == 0
        and should_retry(result, events)
        and int(config["maximum_retries"]) == 1
    ):
        retry_count = 1
        retry_output = workspace / ".ari" / "advanced-turn-2.json"
        retry_prompt = (
            "The workflow controller grants the single allowed retry because recorded "
            "verification failed. You are still the sole coding agent. Do not repeat or "
            "alter the original reproduction and diagnosis. Inspect the current patch, make "
            "at most one targeted correction, then run a focused verification and a distinct "
            "broader regression verification. If either still fails, abstain and stop. Copy "
            "the original reproduction and diagnosis records exactly into the schema output. "
            "Report commands exactly as typed and exact output excerpts.\n\n"
            f"First-turn evidence:\n{json.dumps(result, sort_keys=True)}"
        )
        retried = run_turn(
            config, workspace, retry_prompt, retry_output, codex_environment
        )
        raw_outputs.append(retried.stdout)
        stderr_outputs.append(retried.stderr)
        retry_events, retry_errors = parse_events(retried.stdout)
        events.extend(retry_events)
        parse_errors.extend(retry_errors)
        retry_result = read_result(retry_output)
        if isinstance(result, dict) and isinstance(retry_result, dict):
            result = merge_retry(result, retry_result)
        else:
            result = retry_result
        final_exit_code = retried.returncode

    raw_trajectory = "".join(raw_outputs)
    trajectory_path.write_text(raw_trajectory, encoding="utf-8")
    sys.stdout.write(raw_trajectory)
    sys.stderr.write("".join(stderr_outputs))

    evidence = validate_evidence(
        result,
        events,
        changed_files(workspace, baseline_revision),
        retry_count,
    )
    evidence_path.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in evidence),
        encoding="utf-8",
    )
    final_response_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    usage = aggregate_usage(events, config, pricing, retry_count)
    usage["trajectory_parse_errors"] = parse_errors
    usage["workflow_status"] = result.get("status") if isinstance(result, dict) else None
    usage_path.write_text(
        json.dumps(usage, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if temporary_home is not None:
        temporary_home.cleanup()
    return final_exit_code


if __name__ == "__main__":
    raise SystemExit(main())
