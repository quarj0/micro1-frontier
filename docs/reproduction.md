# Reproduction guide

## Requirements

- Linux or another platform capable of running the selected agent image.
- Python 3.12.
- uv 0.11 or newer.
- Docker for official isolated runs.

No credentials or private data are required for the included development suite.

## Install

```bash
uv sync --frozen
uv run pytest
```

## Confirm that broken inputs fail

The hidden evaluators are deliberately not exposed through an agent-facing command. The project test suite checks case separation, then the full-loop smoke run demonstrates that the evaluator accepts repaired workspaces.

## Isolated smoke run

```bash
docker build -f Dockerfile.smoke-agent -t ari-smoke-agent:dev .
uv run ari run-suite \
  --mode docker \
  --docker-image ari-smoke-agent:dev \
  --agent-command smoke \
  --timeout 60
```

Expected result:

```text
incorrect-boolean-filtering: PASS
nested-write-atomicity: PASS
response-contract-drift: PASS
{"cases": 3, "evidence_backed_repair_rate": 0.0, "evidence_backed_repairs": 0, "verified_repair_rate": 1.0, "verified_repairs": 3}
```

The ordering is lexical. Runtime depends on Docker startup, but each development evaluator has a 60-second hard timeout. The smoke image makes no network calls and has no model cost.

## Use another agent

Build or select an image containing the agent command and all dependencies it needs while offline. Then replace the image and command values. Network remains disabled by default; opt in only when the provider requires it and record that resource difference in benchmark results.

Each agent-facing repository includes a pinned uv environment. For a network-disabled official run, bake those locked packages into the agent image or its uv cache before starting the timed container; the harness never enables an implicit image pull or dependency download.

Do not mount credentials, evaluator directories, the host repository, or the Docker socket into the agent container.

## Real baseline

Build and run the fixed Codex baseline with a project-scoped `CODEX_API_KEY` available only in the invoking shell:

```bash
docker build -f Dockerfile.codex-baseline -t ari-codex-baseline:0.150.1 .
uv run ari run-suite \
  --mode docker \
  --docker-image ari-codex-baseline:0.150.1 \
  --agent-command codex-baseline \
  --allow-network \
  --secret-env CODEX_API_KEY \
  --timeout 900
```

The adapter is intentionally minimal. It reads the existing baseline prompt, runs one fresh non-interactive Codex turn, tees the raw JSONL trajectory, captures the final response, and extracts usage. It does not add workflow logic.

## Advanced workflow

Use the separate image, command, and workflow selector against the same case suite:

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

For fair comparisons, change only `--workflow`, `--docker-image`, and `--agent-command`. Keep the case suite, timeout, CLI version, model, reasoning effort, and network policy fixed. The advanced adapter writes raw Codex events to the trajectory and separately writes only corroborated semantic events to `evidence.jsonl`. A retry is a second ephemeral turn with the same controls and is allowed at most once after recorded verification failure.
