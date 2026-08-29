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
| `ARI_USAGE_PATH` | Optional normalized usage JSON output path. |
| `ARI_FINAL_RESPONSE_PATH` | Optional final natural-language response path. |
| `ARI_EVIDENCE_PATH` | Optional validated workflow-evidence JSONL path. |
| `ARI_WORKFLOW` | Selected workflow: `baseline` or `advanced-v1`. |

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

## Real Codex baseline

The first credible baseline is one Codex CLI agent with one simple instruction. It fixes these controls for the baseline and later workflow variants:

- Codex CLI `0.150.1`.
- `gpt-5.6-sol`.
- Medium reasoning.
- No subagents, memories, skill discovery, plugins, apps, retry orchestration, evidence gate, or independent verifier.

The adapter invokes a fresh `codex exec --json --ephemeral` turn, captures the raw JSONL stream and final response, and normalizes the `turn.completed` token usage. API-key runs also receive a clearly labeled cost estimate from the versioned pricing snapshot in `agents/codex-baseline/pricing.json`.

Build the pinned baseline image:

```bash
docker build -f Dockerfile.codex-baseline -t ari-codex-baseline:0.150.1 .
```

Set a project-scoped `CODEX_API_KEY` in the invoking shell without writing it into this repository, then run:

```bash
uv run ari run-suite \
  --mode docker \
  --docker-image ari-codex-baseline:0.150.1 \
  --agent-command codex-baseline \
  --allow-network \
  --secret-env CODEX_API_KEY \
  --timeout 900
```

`--secret-env` adds only the variable name to Docker argv. Docker inherits its value from the harness process; the value is not included in the report, trajectory, image, or workspace. The synthetic repository can still execute code inside the container, so use a scoped benchmark key with an appropriate spend limit.

Every Docker baseline run starts with an empty temporary `CODEX_HOME`, ignores user configuration and execution rules, disables stateful or multi-agent features, and persists no Codex session. The only host mount remains the prepared case workspace.

For a non-isolated development check, the same adapter can reuse authentication shared by the host Codex CLI and VS Code extension:

```bash
uv run ari run response-contract-drift \
  --mode subprocess \
  --agent-command "$(pwd)/.venv/bin/python $(pwd)/agents/codex-baseline/adapter.py" \
  --timeout 900
```

Do not report subprocess results as official benchmark evidence.

## Advanced evidence workflow

`advanced-v1` keeps the baseline's Codex CLI, GPT-5.6 Sol Medium model, disabled features, repository tools, cases, evaluator, and resource limits. It changes only the workflow:

- Reproduce the reported behavior with a failing command before source edits.
- Ground the diagnosis in pre-edit repository or runtime command output.
- Make a targeted production repair.
- Run distinct focused and broader regression verification commands.
- Abstain when the evidence is insufficient.
- Permit at most one new agent turn, and only after a corroborated verification failure.

Agent-authored evidence does not qualify merely because it uses the expected labels. The adapter checks reported commands, exit codes, and exact output lines against raw Codex command events and enforces pre-edit/post-edit ordering. Raw model JSONL remains separate from normalized evidence JSONL.

Build and run the official isolated variant with the same scoped key mechanism:

```bash
docker build -f Dockerfile.codex-advanced -t ari-codex-advanced:0.150.1 .
uv run ari run-suite \
  --workflow advanced-v1 \
  --mode docker \
  --docker-image ari-codex-advanced:0.150.1 \
  --agent-command codex-advanced \
  --allow-network \
  --secret-env CODEX_API_KEY \
  --timeout 900
```

The equivalent development-only command is:

```bash
uv run ari run-suite \
  --workflow advanced-v1 \
  --mode subprocess \
  --agent-command "$(pwd)/.venv/bin/python $(pwd)/agents/codex_advanced/adapter.py" \
  --timeout 900
```

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
├── evaluator.stderr.log
├── evidence.jsonl           # advanced workflow only
└── final-response.md        # when supplied by the adapter

trajectories/<run-id>.jsonl
```

Generated results and trajectories remain outside Git unless representative artifacts are intentionally reviewed and promoted later.

See [benchmark design](docs/benchmark-design.md) and the [reproduction guide](docs/reproduction.md) for the trust boundary and complete workflow.
