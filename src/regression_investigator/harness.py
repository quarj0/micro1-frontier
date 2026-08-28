from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import tomllib
import uuid
from datetime import UTC, datetime
from pathlib import Path

from .evaluator import evaluate_workspace
from .metrics import calculate_metrics
from .models import AgentInvocation, ExecutionMode, RunReport
from .reporting import write_report
from .runner import run_agent
from .workflows.baseline import render_baseline_prompt


class BenchmarkConfigurationError(ValueError):
    pass


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def discover_cases(root: Path, suite: str = "dev") -> dict[str, Path]:
    cases_root = root / "benchmark" / "cases" / suite
    if not cases_root.exists():
        return {}
    return {
        path.name: path
        for path in sorted(cases_root.iterdir())
        if path.is_dir() and (path / "case.toml").is_file()
    }


def load_case(case_dir: Path) -> dict[str, object]:
    with (case_dir / "case.toml").open("rb") as handle:
        data = tomllib.load(handle)
    if data.get("id") != case_dir.name:
        raise BenchmarkConfigurationError(
            f"case id must match directory name: {case_dir}"
        )
    return data


def _run_git(workspace: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(arguments)} failed: {result.stderr.strip()}")
    return result.stdout


def _prepare_workspace(
    case_dir: Path, destination: Path, prompt_template: Path
) -> tuple[Path, Path, str]:
    workspace = destination / "workspace"
    shutil.copytree(case_dir / "input" / "repo", workspace)
    issue_text = (case_dir / "input" / "issue.md").read_text(encoding="utf-8")
    shutil.copy2(case_dir / "input" / "issue.md", workspace / "ISSUE.md")
    ari_dir = workspace / ".ari"
    ari_dir.mkdir()
    prompt_path = ari_dir / "prompt.md"
    prompt_path.write_text(
        render_baseline_prompt(prompt_template, issue_text), encoding="utf-8"
    )

    _run_git(workspace, "init", "--quiet")
    _run_git(workspace, "config", "user.name", "ARI Harness")
    _run_git(workspace, "config", "user.email", "ari-harness@example.invalid")
    _run_git(workspace, "add", "--all")
    _run_git(workspace, "commit", "--quiet", "-m", "broken benchmark input")
    baseline_revision = _run_git(workspace, "rev-parse", "HEAD").strip()
    return workspace, prompt_path, baseline_revision


def _load_trajectory(path: Path) -> tuple[list[dict[str, object]], str | None]:
    if not path.exists():
        return [], None
    events: list[dict[str, object]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            return events, f"invalid JSONL at line {line_number}: {exc.msg}"
        if not isinstance(event, dict):
            return events, f"trajectory line {line_number} is not a JSON object"
        events.append(event)
    return events, None


def _load_json_object(path: Path) -> tuple[dict[str, object] | None, str | None]:
    if not path.exists():
        return None, None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc.msg}"
    if not isinstance(value, dict):
        return None, "value is not a JSON object"
    return value, None


def run_case(
    *,
    root: Path,
    case_id: str,
    command: tuple[str, ...],
    mode: ExecutionMode,
    timeout_seconds: int,
    docker_image: str | None,
    allow_network: bool = False,
    secret_environment: tuple[str, ...] = (),
    keep_workspace: bool = False,
) -> RunReport:
    cases = discover_cases(root)
    if case_id not in cases:
        raise BenchmarkConfigurationError(f"unknown development case: {case_id}")
    case_dir = cases[case_id]
    case = load_case(case_dir)
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{case_id}-{uuid.uuid4().hex[:8]}"
    run_root = root / "benchmark" / "results" / run_id
    run_root.mkdir(parents=True, exist_ok=False)

    temp_context = tempfile.TemporaryDirectory(prefix=f"ari-{case_id}-")
    temp_path = Path(temp_context.name)
    try:
        workspace, prompt_path, baseline_revision = _prepare_workspace(
            case_dir,
            temp_path,
            root / "prompts" / "baseline.md",
        )
        trajectory_path = workspace / ".ari" / "trajectory.jsonl"
        agent = run_agent(
            AgentInvocation(
                command=command,
                workspace=workspace,
                prompt_path=prompt_path,
                trajectory_path=trajectory_path,
                timeout_seconds=timeout_seconds,
                mode=mode,
                docker_image=docker_image,
                allow_network=allow_network,
                secret_environment=secret_environment,
            )
        )

        patch = _run_git(workspace, "diff", "--binary", baseline_revision)
        changed = _run_git(
            workspace, "diff", "--name-only", baseline_revision
        ).splitlines()
        trajectory, trajectory_error = _load_trajectory(trajectory_path)
        usage, usage_error = _load_json_object(workspace / ".ari" / "usage.json")
        final_response_path = workspace / ".ari" / "final-response.md"
        final_response = (
            final_response_path.read_text(encoding="utf-8")
            if final_response_path.exists()
            else None
        )
        if trajectory_path.exists():
            shutil.copy2(trajectory_path, root / "trajectories" / f"{run_id}.jsonl")

        evaluator_config = case["evaluator"]
        if not isinstance(evaluator_config, dict):
            raise BenchmarkConfigurationError(f"missing evaluator table for {case_id}")
        evaluator = evaluate_workspace(
            case_dir,
            workspace,
            list(evaluator_config["command"]),
            int(evaluator_config.get("timeout_seconds", 60)),
        )
        metrics = calculate_metrics(agent, evaluator, changed, trajectory, usage)
        report = RunReport(
            schema_version="1.0",
            run_id=run_id,
            case_id=case_id,
            mode=mode.value,
            started_at=datetime.now(UTC).isoformat(),
            agent=agent,
            evaluator=evaluator,
            patch=patch,
            patch_files=changed,
            trajectory_events=len(trajectory),
            trajectory_error=trajectory_error,
            usage=usage,
            usage_error=usage_error,
            final_response=final_response,
            metrics=metrics,
        )
        write_report(report, run_root)
        if keep_workspace:
            shutil.copytree(workspace, run_root / "workspace")
        return report
    finally:
        temp_context.cleanup()
