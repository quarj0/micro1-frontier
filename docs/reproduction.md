# Exact reproduction and audit guide

This guide separates three different operations:

1. **Audit committed measurements** — read the immutable comparison artifacts.
2. **Regenerate comparisons** — rebuild those artifacts from the exact preserved raw report IDs.
3. **Run a new replication** — execute the frozen method again, producing new stochastic runs and new run IDs.

A new model run is not an exact reproduction of an existing trajectory.

## Requirements

- Python 3.12.
- [uv](https://docs.astral.sh/uv/); the benchmark images pin uv 0.11.26.
- Docker for isolated execution.
- A project-scoped `CODEX_API_KEY` for a new Docker-isolated Codex replication.
- Codex CLI 0.150.1, installed by the pinned Codex images.

Install and validate the repository:

```bash
uv sync --frozen
UV_CACHE_DIR=/tmp/ari-uv-cache uv run --frozen pytest -q
git diff --check
```

The test suite checks case/evaluator separation, verifies that every broken hidden evaluator rejects its input, and checks frozen prompt, adapter, configuration, and case-tree hashes.

## 1. Audit committed measurements

The numerical sources of truth are:

```text
benchmark/comparisons/advanced-v1-development.json
benchmark/comparisons/heldout-v1.json
benchmark/comparisons/advanced-v2-heldout-tuning.json
benchmark/comparisons/final-v1.json
```

Print every aggregate without running a model:

```bash
for artifact in \
  benchmark/comparisons/advanced-v1-development.json \
  benchmark/comparisons/heldout-v1.json \
  benchmark/comparisons/advanced-v2-heldout-tuning.json \
  benchmark/comparisons/final-v1.json
do
  jq '{comparison_id, classification, execution_mode, aggregate}' "$artifact"
done
```

Inspect the exact final run selection and source report hashes:

```bash
jq '{selection_policy, rows, aggregate}' benchmark/comparisons/final-v1.json
```

The frozen final-suite preflight is committed at:

```text
benchmark/validations/final-v1-preflight.json
```

## 2. Regenerate comparisons from preserved reports

Raw model reports and trajectories are ignored by Git. These checks therefore require the original retained `benchmark/results/<run-id>/report.json` files. A source-only clone can audit the committed JSON but cannot regenerate it without the corresponding raw-result bundle.

Development baseline vs V1 uses the generator defaults:

```bash
uv run --frozen python scripts/generate_comparison.py --check
```

Check the other three artifacts explicitly:

```bash
uv run --frozen python scripts/generate_comparison.py \
  --spec benchmark/comparisons/heldout-v1.spec.json \
  --output benchmark/comparisons/heldout-v1.json \
  --markdown benchmark/comparisons/heldout-v1.md \
  --check

uv run --frozen python scripts/generate_comparison.py \
  --spec benchmark/comparisons/advanced-v2-heldout-tuning.spec.json \
  --output benchmark/comparisons/advanced-v2-heldout-tuning.json \
  --markdown benchmark/comparisons/advanced-v2-heldout-tuning.md \
  --check

uv run --frozen python scripts/generate_comparison.py \
  --spec benchmark/comparisons/final-v1.spec.json \
  --output benchmark/comparisons/final-v1.json \
  --markdown benchmark/comparisons/final-v1.md \
  --check
```

The generator reads only the run IDs listed in each spec, verifies workflow/case consistency, records source report SHA-256 values, and derives both row and aggregate tables. It does not mutate raw runs.

## 3. Reproduce the harness without a model

Build the deterministic smoke-agent image:

```bash
docker build -f Dockerfile.smoke-agent -t ari-smoke-agent:dev .
uv run --frozen ari run-suite \
  --suite dev \
  --mode docker \
  --docker-image ari-smoke-agent:dev \
  --agent-command smoke \
  --timeout 60
```

The smoke agent proves workspace preparation, patch capture, out-of-sandbox evaluation, metrics, and report generation. It is a harness test double and must not be reported as model performance.

## 4. New Docker-isolated model replication

Docker is the intended official isolation mode. The agent receives only `/workspace`; evaluator files, oracles, other cases, the host repository, and the Docker socket are absent. The container root is read-only, capabilities are dropped, and network defaults to disabled.

Codex requires provider network access, so the following commands opt in explicitly. Export a scoped benchmark key in the invoking shell; do not write it to the repository:

```bash
export CODEX_API_KEY='your-scoped-key'

docker build -f Dockerfile.codex-baseline -t ari-codex-baseline:0.150.1 .
docker build -f Dockerfile.codex-advanced-v2 -t ari-codex-advanced-v2:0.150.1 .
```

Run the frozen baseline once across a selected suite:

```bash
uv run --frozen ari run-suite \
  --suite final \
  --workflow baseline \
  --mode docker \
  --docker-image ari-codex-baseline:0.150.1 \
  --agent-command codex-baseline \
  --allow-network \
  --secret-env CODEX_API_KEY \
  --timeout 900
```

Run the frozen V2 once with the same suite and resource controls:

```bash
uv run --frozen ari run-suite \
  --suite final \
  --workflow advanced-v2 \
  --mode docker \
  --docker-image ari-codex-advanced-v2:0.150.1 \
  --agent-command codex-advanced-v2 \
  --allow-network \
  --secret-env CODEX_API_KEY \
  --timeout 900
```

These commands create a new replication. Do not insert its run IDs into the committed `final-v1.spec.json`; create a new comparison ID and spec so the historical one-shot result stays immutable.

## Historical subprocess method used for reported results

The measured model results used host subscription authentication because `CODEX_API_KEY` was unavailable. Each adapter copied only `auth.json` into a fresh temporary `CODEX_HOME`, used an ephemeral Codex turn, ignored user configuration/rules, and prepared a fresh case workspace.

The exact final baseline command shape was:

```bash
env UV_CACHE_DIR=/tmp/ari-uv-cache uv run --frozen ari run-suite \
  --suite final \
  --workflow baseline \
  --mode subprocess \
  --agent-command '/absolute/repository/.venv/bin/python /absolute/repository/agents/codex-baseline/adapter.py' \
  --timeout 900
```

The exact V2 command shape was:

```bash
env UV_CACHE_DIR=/tmp/ari-uv-cache uv run --frozen ari run-suite \
  --suite final \
  --workflow advanced-v2 \
  --mode subprocess \
  --agent-command '/absolute/repository/.venv/bin/python /absolute/repository/agents/codex_advanced_v2/adapter.py' \
  --timeout 900
```

Subprocess mode is not isolated. It inherits the host environment and may be able to read beyond the temporary workspace. The hidden evaluator was not copied into the workspace until after the adapter exited, but that is weaker than a Docker filesystem boundary. Use subprocess only to replicate the historical method or for development; use Docker for a new official isolated evaluation.

## V1 historical replication

V1 remains frozen for historical comparison:

```bash
docker build -f Dockerfile.codex-advanced -t ari-codex-advanced:0.150.1 .
uv run --frozen ari run-suite \
  --suite heldout \
  --workflow advanced-v1 \
  --mode docker \
  --docker-image ari-codex-advanced:0.150.1 \
  --agent-command codex-advanced \
  --allow-network \
  --secret-env CODEX_API_KEY \
  --timeout 900
```

Do not modify V1 or reinterpret a new run as part of the committed hard-case result.

## Outputs and preservation

Every run produces:

```text
benchmark/results/<run-id>/
├── report.json
├── report.md
├── patch.diff
├── agent.stdout.log
├── agent.stderr.log
├── evaluator.stdout.log
├── evaluator.stderr.log
├── evidence.jsonl        # advanced workflows
└── final-response.md

trajectories/<run-id>.jsonl
```

Preserve successes, failures, timeouts, and launch errors. Never replace or delete an earlier run to improve an aggregate. Create comparisons mechanically from explicit run IDs with `scripts/generate_comparison.py`.

## Cost and usage reporting

The adapters report input, cached-input, output, and reasoning token fields when the Codex CLI emits them. API-key mode can attach a labeled estimate using the versioned pricing snapshot. The committed measured experiments used subscription authentication and contain no API-key billing estimate; therefore exact dollar cost is not reproducible from these artifacts and must not be claimed.
