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
{"cases": 3, "verified_repair_rate": 1.0, "verified_repairs": 3}
```

The ordering is lexical. Runtime depends on Docker startup, but each development evaluator has a 60-second hard timeout. The smoke image makes no network calls and has no model cost.

## Use another agent

Build or select an image containing the agent command and all dependencies it needs while offline. Then replace the image and command values. Network remains disabled by default; opt in only when the provider requires it and record that resource difference in benchmark results.

Each agent-facing repository includes a pinned uv environment. For a network-disabled official run, bake those locked packages into the agent image or its uv cache before starting the timed container; the harness never enables an implicit image pull or dependency download.

Do not mount credentials, evaluator directories, the host repository, or the Docker socket into the agent container.
