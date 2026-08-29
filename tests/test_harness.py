from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from regression_investigator.evaluator import evaluate_workspace
from regression_investigator.harness import (
    _prepare_workspace,
    _run_git,
    discover_cases,
    load_case,
    run_case,
)
from regression_investigator.models import ExecutionMode


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FROZEN_PROMPT_HASHES = {
    "baseline.md": "e4cee059ccea31823e639b80823b371af8294c1c89533d1451117251f63b7576",
    "advanced-v1.md": "7fa8137acb6c98e26bbbb6f25512678d5098333378b0e4193bd5f41363583927",
}


def isolated_benchmark_root(tmp_path: Path) -> Path:
    (tmp_path / "benchmark" / "cases").mkdir(parents=True)
    shutil.copytree(PROJECT_ROOT / "benchmark" / "cases" / "dev", tmp_path / "benchmark" / "cases" / "dev")
    shutil.copytree(PROJECT_ROOT / "prompts", tmp_path / "prompts")
    (tmp_path / "benchmark" / "results").mkdir()
    (tmp_path / "trajectories").mkdir()
    return tmp_path


def test_case_inputs_do_not_contain_hidden_evaluator_material():
    for suite in ("dev", "heldout"):
        for case_dir in discover_cases(PROJECT_ROOT, suite).values():
            visible_files = {
                path.name for path in (case_dir / "input").rglob("*") if path.is_file()
            }
            assert "oracle.toml" not in visible_files
            assert "test_regression.py" not in visible_files


def test_hidden_evaluators_reject_every_broken_input(tmp_path: Path):
    for suite in ("dev", "heldout"):
        for case_id, case_dir in discover_cases(PROJECT_ROOT, suite).items():
            workspace = tmp_path / suite / case_id
            shutil.copytree(case_dir / "input" / "repo", workspace)
            evaluator = load_case(case_dir)["evaluator"]

            result = evaluate_workspace(
                case_dir,
                workspace,
                list(evaluator["command"]),
                int(evaluator["timeout_seconds"]),
            )

            assert result.passed is False, (
                f"broken case unexpectedly passed: {suite}/{case_id}"
            )


def test_workflow_prompts_are_frozen_during_heldout_evaluation():
    import hashlib

    for name, expected in FROZEN_PROMPT_HASHES.items():
        actual = hashlib.sha256((PROJECT_ROOT / "prompts" / name).read_bytes()).hexdigest()
        assert actual == expected


def test_heldout_manifest_freezes_complete_workflow_controls():
    import hashlib

    manifest_path = PROJECT_ROOT / "benchmark" / "cases" / "heldout" / "suite.toml"
    with manifest_path.open("rb") as handle:
        manifest = tomllib.load(handle)
    paths = {
        "baseline": {
            "prompt_sha256": PROJECT_ROOT / "prompts" / "baseline.md",
            "adapter_sha256": PROJECT_ROOT / "agents" / "codex-baseline" / "adapter.py",
            "config_sha256": PROJECT_ROOT / "agents" / "codex-baseline" / "config.json",
        },
        "advanced-v1": {
            "prompt_sha256": PROJECT_ROOT / "prompts" / "advanced-v1.md",
            "adapter_sha256": PROJECT_ROOT / "agents" / "codex_advanced" / "adapter.py",
            "config_sha256": PROJECT_ROOT / "agents" / "codex_advanced" / "config.json",
        },
    }
    for workflow, fields in paths.items():
        frozen = manifest["frozen_workflows"][workflow]
        for field, path in fields.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == frozen[field]


def test_three_development_cases_complete_the_subprocess_loop(tmp_path: Path):
    root = isolated_benchmark_root(tmp_path)
    command = (sys.executable, str(PROJECT_ROOT / "tests" / "fixtures" / "smoke_agent.py"))

    reports = [
        run_case(
            root=root,
            case_id=case_id,
            command=command,
            mode=ExecutionMode.SUBPROCESS,
            timeout_seconds=15,
            docker_image=None,
        )
        for case_id in discover_cases(root)
    ]

    assert len(reports) == 3
    assert all(report.evaluator.passed for report in reports)
    assert all(report.metrics["evidence_backed_repair"] is False for report in reports)
    assert all(report.patch for report in reports)
    assert all(report.trajectory_events == 1 for report in reports)
    assert len(list((root / "benchmark" / "results").glob("*/report.json"))) == 3


def test_patch_capture_can_be_based_on_revision_before_agent_commit(tmp_path: Path):
    root = isolated_benchmark_root(tmp_path)
    case_dir = discover_cases(root)["response-contract-drift"]
    workspace, _, baseline_revision = _prepare_workspace(
        case_dir, tmp_path / "prepared", root / "prompts" / "baseline.md"
    )
    subprocess_agent = PROJECT_ROOT / "tests" / "fixtures" / "committing_agent.py"
    env = {
        "ARI_WORKSPACE": str(workspace),
        **os.environ,
    }
    subprocess.run([sys.executable, subprocess_agent], env=env, check=True)

    patch = _run_git(workspace, "diff", "--binary", baseline_revision)

    assert "agent-created.txt" in patch
