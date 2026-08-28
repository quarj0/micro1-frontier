import sys
from pathlib import Path

from regression_investigator.models import AgentInvocation, ExecutionMode, ProcessState
from regression_investigator.runner import run_agent


def test_subprocess_runner_captures_success(tmp_path: Path):
    ari = tmp_path / ".ari"
    ari.mkdir()
    prompt = ari / "prompt.md"
    prompt.write_text("test", encoding="utf-8")

    result = run_agent(
        AgentInvocation(
            command=(sys.executable, "-c", "print('agent output')"),
            workspace=tmp_path,
            prompt_path=prompt,
            trajectory_path=ari / "trajectory.jsonl",
            timeout_seconds=5,
            mode=ExecutionMode.SUBPROCESS,
        )
    )

    assert result.state is ProcessState.SUCCEEDED
    assert result.exit_code == 0
    assert result.stdout.strip() == "agent output"


def test_subprocess_runner_enforces_hard_timeout(tmp_path: Path):
    ari = tmp_path / ".ari"
    ari.mkdir()
    prompt = ari / "prompt.md"
    prompt.write_text("test", encoding="utf-8")

    result = run_agent(
        AgentInvocation(
            command=(sys.executable, "-c", "import time; time.sleep(5)"),
            workspace=tmp_path,
            prompt_path=prompt,
            trajectory_path=ari / "trajectory.jsonl",
            timeout_seconds=1,
            mode=ExecutionMode.SUBPROCESS,
        )
    )

    assert result.state is ProcessState.TIMED_OUT
    assert result.error == "hard timeout after 1 seconds"

