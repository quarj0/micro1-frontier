# Agentic API Regression Investigator

An evidence-backed benchmark for agents that investigate and repair Django REST Framework API regressions. The intended user is a backend engineer who needs more than a plausible patch: they need a reproduced symptom, a causal explanation, a targeted repair, and verification evidence they can review.

This initial scaffold proves the complete benchmark loop:

```text
broken repository -> issue report -> baseline agent -> patch
                  -> host evaluator -> metrics -> report
```

The development suite currently contains three synthetic cases:

- Response contract drift.
- Incorrect boolean filtering.
- Nested-write atomicity failure.

## Setup

Python 3.12 and [uv](https://docs.astral.sh/uv/) are required. Docker is additionally required for official isolated runs.

```bash
uv sync --frozen
uv run ari list-cases
```

Dependencies are pinned in `pyproject.toml` and resolved in `uv.lock`. The cases use only synthetic data and make no external requests.

## Agent command contract

The harness invokes any command supplied through `--agent-command`; no provider SDK is part of the core workflow. The command starts in the broken repository workspace and receives:

| Variable | Meaning |
|---|---|
| `ARI_WORKSPACE` | Absolute writable workspace path. |
| `ARI_PROMPT_PATH` | Baseline instruction and issue report. |
| `ARI_TRAJECTORY_PATH` | Optional JSONL trajectory output path. |
| `ARI_EXECUTION_MODE` | `docker` for official isolation or `subprocess` for development. |

The harness captures stdout, stderr, exit status, launch errors, hard timeouts, runtime, Git patch, changed paths, and trajectory events. An agent may modify only the workspace presented to it.

## Official Docker mode

Docker is the default and official benchmark mode. The container receives one writable mount at `/workspace`; evaluators, oracles, hidden tests, other cases, the host repository, and the Docker socket are not mounted. Network access is disabled unless `--allow-network` is explicitly supplied.

Build the deterministic smoke-test image and prove the loop:

```bash
docker build -f Dockerfile.smoke-agent -t ari-smoke-agent:dev .
uv run ari run-suite \
  --mode docker \
  --docker-image ari-smoke-agent:dev \
  --agent-command smoke
```

The smoke agent is a harness test double, not a benchmark baseline, and its results must not be reported as agent performance. A real agent image should contain its own command and any runtime dependencies, then be invoked using the same interface:

```bash
uv run ari run response-contract-drift \
  --mode docker \
  --docker-image your-agent-image:fixed-version \
  --agent-command 'your-agent --prompt "$ARI_PROMPT_PATH"'
```

Commands are passed directly, not through a shell. Environment-variable expansion in the example therefore needs to be performed by the agent command itself or by an explicit shell entrypoint inside the image.

## Development-only subprocess mode

Subprocess mode is faster but **not isolated**. The command inherits the host environment and may be able to traverse beyond its workspace. Never use subprocess results as official benchmark evidence.

```bash
uv run ari run-suite \
  --mode subprocess \
  --agent-command "$(pwd)/.venv/bin/python $(pwd)/tests/fixtures/smoke_agent.py"
```

## Outputs

Every run writes ignored artifacts beneath:

```text
benchmark/results/<run-id>/
├── report.json
├── report.md
├── patch.diff
├── agent.stdout.log
├── agent.stderr.log
├── evaluator.stdout.log
└── evaluator.stderr.log

trajectories/<run-id>.jsonl
```

Generated results and trajectories remain outside Git unless representative artifacts are intentionally reviewed and promoted later.

See [benchmark design](docs/benchmark-design.md) and the [reproduction guide](docs/reproduction.md) for the trust boundary and complete workflow.
