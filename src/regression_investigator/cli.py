from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

from .harness import (
    BenchmarkConfigurationError,
    discover_cases,
    repository_root,
    run_case,
)
from .metrics import aggregate_reports
from .models import ExecutionMode, Workflow


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ari", description="Django/DRF regression benchmark harness"
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    list_cases = subparsers.add_parser("list-cases", help="List benchmark cases")
    list_cases.add_argument("--suite", choices=["dev", "heldout"], default="dev")

    run = subparsers.add_parser(
        "run", help="Run one case through an agent and evaluator"
    )
    run.add_argument("case")
    run.add_argument("--suite", choices=["dev", "heldout"], default="dev")
    run.add_argument(
        "--agent-command",
        required=True,
        help="Agent command parsed with shell-like quoting",
    )
    run.add_argument(
        "--mode", choices=[mode.value for mode in ExecutionMode], default="docker"
    )
    run.add_argument(
        "--workflow",
        choices=[workflow.value for workflow in Workflow],
        default=Workflow.BASELINE.value,
    )
    run.add_argument("--docker-image", help="Required in Docker mode")
    run.add_argument("--timeout", type=int, default=300)
    run.add_argument(
        "--allow-network",
        action="store_true",
        help="Opt in to agent-container network access",
    )
    run.add_argument(
        "--secret-env",
        action="append",
        default=[],
        metavar="NAME",
        help="Forward one host environment variable by name without recording its value",
    )
    run.add_argument(
        "--keep-workspace",
        action="store_true",
        help="Copy final workspace into ignored results",
    )

    suite = subparsers.add_parser("run-suite", help="Run every case in a suite")
    suite.add_argument("--suite", choices=["dev", "heldout"], default="dev")
    suite.add_argument("--agent-command", required=True)
    suite.add_argument(
        "--mode", choices=[mode.value for mode in ExecutionMode], default="docker"
    )
    suite.add_argument(
        "--workflow",
        choices=[workflow.value for workflow in Workflow],
        default=Workflow.BASELINE.value,
    )
    suite.add_argument("--docker-image")
    suite.add_argument("--timeout", type=int, default=300)
    suite.add_argument("--allow-network", action="store_true")
    suite.add_argument("--secret-env", action="append", default=[], metavar="NAME")
    return parser


def _validate(args: argparse.Namespace) -> None:
    if (
        getattr(args, "mode", None) == ExecutionMode.DOCKER.value
        and not args.docker_image
    ):
        raise BenchmarkConfigurationError("--docker-image is required in Docker mode")
    if getattr(args, "timeout", 1) <= 0:
        raise BenchmarkConfigurationError("--timeout must be positive")
    if getattr(args, "secret_env", []) and getattr(args, "mode", None) != "docker":
        raise BenchmarkConfigurationError("--secret-env is supported only in Docker mode")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = repository_root()
    try:
        _validate(args)
        if args.action == "list-cases":
            for case_id in discover_cases(root, args.suite):
                print(case_id)
            return 0

        command = tuple(shlex.split(args.agent_command))
        if not command:
            raise BenchmarkConfigurationError("agent command cannot be empty")
        mode = ExecutionMode(args.mode)
        workflow = Workflow(args.workflow)

        if args.action == "run":
            report = run_case(
                root=root,
                case_id=args.case,
                suite=args.suite,
                command=command,
                mode=mode,
                workflow=workflow,
                timeout_seconds=args.timeout,
                docker_image=args.docker_image,
                allow_network=args.allow_network,
                secret_environment=tuple(args.secret_env),
                keep_workspace=args.keep_workspace,
            )
            print(json.dumps(report.metrics, sort_keys=True))
            print(f"report: benchmark/results/{report.run_id}/report.md")
            return 0 if report.evaluator.passed else 1

        reports = []
        for case_id in discover_cases(root, args.suite):
            report = run_case(
                root=root,
                case_id=case_id,
                suite=args.suite,
                command=command,
                mode=mode,
                workflow=workflow,
                timeout_seconds=args.timeout,
                docker_image=args.docker_image,
                allow_network=args.allow_network,
                secret_environment=tuple(args.secret_env),
            )
            reports.append(report.to_dict())
            print(f"{case_id}: {'PASS' if report.evaluator.passed else 'FAIL'}")
        print(json.dumps(aggregate_reports(reports), sort_keys=True))
        return (
            0 if all(report["metrics"]["verified_repair"] for report in reports) else 1
        )
    except BenchmarkConfigurationError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
