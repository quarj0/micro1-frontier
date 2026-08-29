from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class ExecutionMode(StrEnum):
    """How an agent command is isolated."""

    DOCKER = "docker"
    SUBPROCESS = "subprocess"


class Workflow(StrEnum):
    """Agent workflow variant under evaluation."""

    BASELINE = "baseline"
    ADVANCED_V1 = "advanced-v1"


class ProcessState(StrEnum):
    """Normalized terminal states for agent and evaluator processes."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    LAUNCH_ERROR = "launch_error"


@dataclass(frozen=True)
class AgentInvocation:
    """Provider-neutral command contract.

    The command runs with ``workspace`` as its current directory. It receives
    ARI_WORKSPACE and ARI_PROMPT_PATH. It may edit anything inside the
    workspace and may write JSON Lines events to ARI_TRAJECTORY_PATH.
    """

    command: tuple[str, ...]
    workspace: Path
    prompt_path: Path
    trajectory_path: Path
    timeout_seconds: int
    mode: ExecutionMode
    workflow: Workflow = Workflow.BASELINE
    docker_image: str | None = None
    allow_network: bool = False
    secret_environment: tuple[str, ...] = ()
    environment: dict[str, str] = field(default_factory=dict)


@dataclass
class ProcessResult:
    state: ProcessState
    command: list[str]
    exit_code: int | None
    runtime_seconds: float
    stdout: str
    stderr: str
    error: str | None = None


@dataclass
class EvaluationResult(ProcessResult):
    passed: bool = False


@dataclass
class RunReport:
    schema_version: str
    run_id: str
    case_id: str
    suite: str
    mode: str
    workflow: str
    started_at: str
    agent: ProcessResult
    evaluator: EvaluationResult
    patch: str
    patch_files: list[str]
    trajectory_events: int
    trajectory_error: str | None
    evidence: list[dict[str, Any]]
    evidence_error: str | None
    usage: dict[str, Any] | None
    usage_error: str | None
    final_response: str | None
    metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
