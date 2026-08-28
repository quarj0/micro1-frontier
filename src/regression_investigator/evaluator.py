from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from .models import EvaluationResult, ProcessState


def evaluate_workspace(
    case_dir: Path, workspace: Path, command: list[str], timeout_seconds: int
) -> EvaluationResult:
    """Run hidden tests on the host after the agent process has exited."""

    hidden_source = case_dir / "evaluator" / "tests"
    hidden_target = workspace / "benchmark_hidden_tests"
    if hidden_target.exists():
        shutil.rmtree(hidden_target)
    shutil.copytree(hidden_source, hidden_target)

    resolved_command = [
        sys.executable if part == "{python}" else part for part in command
    ]
    started = time.monotonic()
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        process = subprocess.Popen(
            resolved_command,
            cwd=workspace,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            state = (
                ProcessState.SUCCEEDED
                if process.returncode == 0
                else ProcessState.FAILED
            )
            error = None
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
            state = ProcessState.TIMED_OUT
            error = f"hard timeout after {timeout_seconds} seconds"
    except (OSError, ValueError) as exc:
        stdout, stderr = "", ""
        process = None
        state = ProcessState.LAUNCH_ERROR
        error = f"{type(exc).__name__}: {exc}"
    finally:
        shutil.rmtree(hidden_target, ignore_errors=True)

    exit_code = process.returncode if process is not None else None
    return EvaluationResult(
        state=state,
        command=resolved_command,
        exit_code=exit_code,
        runtime_seconds=time.monotonic() - started,
        stdout=stdout,
        stderr=stderr,
        error=error,
        passed=state is ProcessState.SUCCEEDED,
    )
