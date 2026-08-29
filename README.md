# Agentic API Regression Investigator

ARI is a benchmark and workflow for evidence-backed repair of Django REST Framework regressions.

## Problem / User

ARI is for backend engineers who must review AI-generated API regression repairs. A passing patch is necessary, but reviewers also need a compact record of the failure reproduced, the cause inferred, and the exact executions used to verify the change.

The experiment's central result is deliberately narrower than “agents fix bugs better”:

> A general-purpose coding agent repaired all four final unseen regressions, but none of those repairs carried an ARI-validated structured evidence chain. ARI V2 preserved the same 4/4 repair success while producing 4/4 evidence chains grounded in actual execution events.

Both workflows used Codex CLI 0.150.1, `gpt-5.6-sol`, medium reasoning, one agent, and the same repository tools. The measured difference came from workflow and evidence transport, not a model upgrade.

## Hot Take

The patch was not the differentiator: the general-purpose agent already fixed 4/4 final regressions. The useful workflow change was making repair claims checkable without relying on the agent's prose by binding them to recorded command events.

## Final result

| Workflow | Verified repairs | Evidence-backed repairs | Runtime | Input / cached / output / reasoning tokens | Retries |
|---|---:|---:|---:|---:|---:|
| Baseline | 4/4 | 0/4 | 398.229s | 660,493 / 548,864 / 10,437 / 1,938 | 0 |
| Advanced V2 | 4/4 | 4/4 | 1,186.559s | 584,132 / 434,944 / 12,339 / 3,606 | 0 |

Source: the committed, machine-generated [final comparison](benchmark/comparisons/final-v1.json). The final cases were tenant-scoped idempotency keys, timezone/DST day boundaries, multipart upload parsing, and project-scoped expense approval authorization.

V2 did not improve verified repair rate in the final suite; both workflows repaired every case. It changed ARI evidence qualification. The tradeoff was runtime: aggregate V2 runtime was 2.98 times baseline. One V2 idempotency run took 836.059s and dominates that total; it succeeded without a retry. The experiment did not produce API-key billing data, so this repository makes no dollar-cost claim.

## What “evidence-backed” means

The host evaluator determines whether a patch repairs the hidden behavior. Evidence qualification is separate.

V2 requires the agent to reference recorder-issued command event IDs. Each event binds:

- a unique ID and workflow phase;
- exact argv, timestamp, and execution order;
- exit status;
- stdout/stderr hashes and retained excerpts;
- whether it ran before or after the first source edit;
- the patch state present during verification.

The adapter resolves those references against matching receipts in the raw Codex JSONL trajectory. Qualification checks that reproduction and diagnosis evidence are pre-edit, focused and broad verification are distinct passing post-edit executions, and verification ran against the reported patch. The hidden evaluator still runs afterward, outside the agent workspace.

## Experiment stages

The stages below must not be blended; they answer different questions.

### 1. Development results

Three public development regressions proved the end-to-end loop: response contract drift, boolean filtering, and nested-write atomicity.

| Workflow | Verified | Evidence-backed | Runtime | Input / cached / output / reasoning tokens |
|---|---:|---:|---:|---:|
| Baseline | 3/3 | 0/3 | 327.454s | 673,681 / 568,320 / 8,610 / 1,961 |
| Advanced V1 | 3/3 | 3/3 | 259.503s | 363,763 / 282,624 / 10,312 / 1,905 |

Source: [advanced-v1-development.json](benchmark/comparisons/advanced-v1-development.json). These were development cases, not final evaluation.

### 2. V1 hard-case tuning results

The harder four-case suite covered tenant exposure, unstable cursor pagination, query-count growth, and tenant cache contamination. The frozen baseline and V1 both repaired every case, but neither produced a qualifying evidence chain.

| Workflow | Verified | Evidence-backed | Runtime | Input / cached / output / reasoning tokens |
|---|---:|---:|---:|---:|
| Baseline | 4/4 | 0/4 | 374.252s | 610,689 / 485,888 / 10,665 / 2,806 |
| Advanced V1 | 4/4 | 0/4 | 480.772s | 538,502 / 442,880 / 19,036 / 3,733 |

Source: [heldout-v1.json](benchmark/comparisons/heldout-v1.json). Classification: development-only subprocess evaluation.

### 3. V2 tuning results

V2 changed evidence transport and qualification, not the repair sequence, model, reasoning level, tools, or retry limit. On the same four hard cases, V2 preserved 4/4 repair success and raised evidence qualification from 0/4 to 4/4.

| Workflow | Verified | Evidence-backed | Runtime | Input / cached / output / reasoning tokens |
|---|---:|---:|---:|---:|
| Advanced V1 | 4/4 | 0/4 | 480.772s | 538,502 / 442,880 / 19,036 / 3,733 |
| Advanced V2 | 4/4 | 4/4 | 372.759s | 539,143 / 426,752 / 11,851 / 3,128 |

Source: [advanced-v2-heldout-tuning.json](benchmark/comparisons/advanced-v2-heldout-tuning.json). V2 runtime was 22.5% lower than V1 in this tuning comparison. This was still development/tuning, not the final unseen suite.

### 4. Final unseen evaluation

The final suite was independently validated and frozen at commit `1298a75` before either workflow ran. Every broken input passed its intended visible tests, failed its intended hidden evaluator, and passed that evaluator after a minimal repair in a disposable copy. Baseline and V2 then ran exactly once per case with fresh state.

The final result is the headline result above: 4/4 verified for both workflows; 0/4 evidence-backed for baseline and 4/4 for V2. Exact run IDs, report hashes, per-case usage, and aggregate metrics are in [final-v1.json](benchmark/comparisons/final-v1.json). The independent preflight is in [final-v1-preflight.json](benchmark/validations/final-v1-preflight.json).

## Trust boundary and execution limitation

Docker mode is the benchmark's intended official isolation boundary. It mounts only the case workspace, defaults the network to disabled, uses a read-only container root, and runs the hidden evaluator on the host only after the agent exits.

The reported model experiments were run in subprocess mode because no `CODEX_API_KEY` was available. Each invocation still received a fresh temporary repository and ephemeral Codex home, and the evaluator was added only after the agent finished. However, subprocess mode is not a security boundary: the command inherits the host environment and may be able to read beyond its workspace. Therefore these results are accurately classified as development/tuning or evaluator-separated final one-shot results, not official Docker-isolated API-key results.

## Quick start

Requirements: Python 3.12 and [uv](https://docs.astral.sh/uv/). Docker is additionally required for isolated runs.

```bash
uv sync --frozen
uv run pytest
uv run ari list-cases --suite dev
uv run ari list-cases --suite heldout
uv run ari list-cases --suite final
```

The core harness is provider-neutral: `--agent-command` invokes any adapter implementing the environment contract. Dependencies are pinned, cases use synthetic data, and generated workspaces make no external requests.

For exact artifact checks and new isolated replications, use the [reproduction guide](docs/reproduction.md). Do not describe a new stochastic run as reproduction of an existing run ID.

## Repository guide

- [Final results summary](docs/final-results.md)
- [Improvement changelog](docs/improvement-changelog.md)
- [Exact reproduction guide](docs/reproduction.md)
- [Trajectory submission index](docs/trajectory-index.md)
- [Sanitized representative evidence bundle](submission/README.md)
- [Five-minute demo outline](docs/demo-outline.md)
- [Benchmark and trust-boundary design](docs/benchmark-design.md)
- [Hackathon brief, preserved unchanged](docs/micro1%20-%20First%20Hackathon97ce7c5.pdf)

Every run writes ignored raw reports, patches, logs, evidence, and trajectories beneath `benchmark/results/<run-id>/` and `trajectories/`. A small sanitized representative subset is intentionally committed under `submission/`; the raw source artifacts remain ignored and unchanged. Committed comparison artifacts are generated mechanically from explicit run-ID specifications and include SHA-256 hashes of their source reports.
