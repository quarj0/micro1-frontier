from __future__ import annotations

import os
import signal
import subprocess
import time
import uuid
import re
from collections.abc import Callable
from pathlib import Path

from .models import AgentInvocation, ExecutionMode, ProcessResult, ProcessState


def _finish_process(
    process: subprocess.Popen[str],
    command: list[str],
    started: float,
    timeout_seconds: int,
    on_timeout: Callable[[], None] | None = None,
) -> ProcessResult:
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        if on_timeout is not None:
            on_timeout()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        return ProcessResult(
            state=ProcessState.TIMED_OUT,
            command=command,
            exit_code=process.returncode,
            runtime_seconds=time.monotonic() - started,
            stdout=stdout,
            stderr=stderr,
            error=f"hard timeout after {timeout_seconds} seconds",
        )

    state = ProcessState.SUCCEEDED if process.returncode == 0 else ProcessState.FAILED
    return ProcessResult(
        state=state,
        command=command,
        exit_code=process.returncode,
        runtime_seconds=time.monotonic() - started,
        stdout=stdout,
        stderr=stderr,
    )


def _launch(
    command: list[str], **kwargs: object
) -> tuple[subprocess.Popen[str] | None, str | None]:
    try:
        return (
            subprocess.Popen(
                command,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **kwargs,
            ),
            None,
        )
    except (OSError, ValueError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def run_agent(invocation: AgentInvocation) -> ProcessResult:
    if invocation.mode is ExecutionMode.DOCKER:
        return _run_docker(invocation)
    return _run_subprocess(invocation)


def _contract_environment(
    invocation: AgentInvocation, workspace: str
) -> dict[str, str]:
    return {
        "ARI_WORKSPACE": workspace,
        "ARI_PROMPT_PATH": (
            f"{workspace}/.ari/prompt.md"
            if workspace == "/workspace"
            else str(invocation.prompt_path)
        ),
        "ARI_TRAJECTORY_PATH": (
            f"{workspace}/.ari/trajectory.jsonl"
            if workspace == "/workspace"
            else str(invocation.trajectory_path)
        ),
        "ARI_EXECUTION_MODE": invocation.mode.value,
        "ARI_USAGE_PATH": (
            f"{workspace}/.ari/usage.json"
            if workspace == "/workspace"
            else str(invocation.workspace / ".ari" / "usage.json")
        ),
        "ARI_FINAL_RESPONSE_PATH": (
            f"{workspace}/.ari/final-response.md"
            if workspace == "/workspace"
            else str(invocation.workspace / ".ari" / "final-response.md")
        ),
        **invocation.environment,
    }


def _run_subprocess(invocation: AgentInvocation) -> ProcessResult:
    command = list(invocation.command)
    environment = os.environ.copy()
    environment.update(_contract_environment(invocation, str(invocation.workspace)))
    started = time.monotonic()
    process, error = _launch(
        command,
        cwd=invocation.workspace,
        env=environment,
        start_new_session=True,
    )
    if process is None:
        return ProcessResult(
            state=ProcessState.LAUNCH_ERROR,
            command=command,
            exit_code=None,
            runtime_seconds=time.monotonic() - started,
            stdout="",
            stderr="",
            error=error,
        )
    return _finish_process(process, command, started, invocation.timeout_seconds)


def _run_docker(invocation: AgentInvocation) -> ProcessResult:
    if not invocation.docker_image:
        raise ValueError("docker_image is required for Docker execution")

    container_name = f"ari-agent-{uuid.uuid4().hex[:12]}"
    command = [
        "docker",
        "run",
        "--rm",
        "--pull",
        "never",
        "--name",
        container_name,
        "--network",
        "bridge" if invocation.allow_network else "none",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=256m",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "256",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--mount",
        f"type=bind,src={invocation.workspace.resolve()},dst=/workspace",
        "--workdir",
        "/workspace",
        "--env",
        "HOME=/tmp",
    ]
    for key, value in _contract_environment(invocation, "/workspace").items():
        command.extend(["--env", f"{key}={value}"])
    for key in invocation.secret_environment:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ValueError(f"invalid secret environment variable name: {key!r}")
        if key not in os.environ:
            return ProcessResult(
                state=ProcessState.LAUNCH_ERROR,
                command=command,
                exit_code=None,
                runtime_seconds=0.0,
                stdout="",
                stderr="",
                error=f"required secret environment variable is unset: {key}",
            )
        # Docker inherits the value from this process. The value never appears
        # in argv, reports, or the workspace.
        command.extend(["--env", key])
    command.extend([invocation.docker_image, *invocation.command])

    started = time.monotonic()
    process, error = _launch(command, start_new_session=True)
    if process is None:
        return ProcessResult(
            state=ProcessState.LAUNCH_ERROR,
            command=command,
            exit_code=None,
            runtime_seconds=time.monotonic() - started,
            stdout="",
            stderr="",
            error=error,
        )

    def kill_container() -> None:
        try:
            subprocess.run(
                ["docker", "kill", container_name],
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
                check=False,
            )
        except subprocess.TimeoutExpired:
            pass
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            subprocess.run(
                ["docker", "rm", "--force", container_name],
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
                check=False,
            )
        except subprocess.TimeoutExpired:
            pass

    return _finish_process(
        process,
        command,
        started,
        invocation.timeout_seconds,
        on_timeout=kill_container,
    )
