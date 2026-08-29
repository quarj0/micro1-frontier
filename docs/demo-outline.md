# Five-minute demo outline

The demo should show the measured distinction between repair and an ARI-validated structured evidence chain. Avoid a live model run: it is stochastic, can exceed the presentation window, and would not be one of the frozen reported runs.

## 0:00-0:40 — Problem and thesis

Open the README headline and say:

> Backend engineers do not only need a plausible patch. They need to know what failed, why the patch addresses it, and which executions verified it. In our final unseen suite, a simple coding agent already repaired all four regressions. ARI V2 preserved that 4/4 success and changed evidence qualification from 0/4 to 4/4.

Clarify that baseline and V2 used the same Codex CLI 0.150.1, GPT-5.6 Sol at medium reasoning, one agent, and the same repository tools.

## 0:40-1:20 — Benchmark trust boundary

Show [benchmark-design.md](benchmark-design.md) and the final suite layout.

Explain:

- the agent receives only a broken synthetic repository and issue report;
- hidden evaluator tests and oracle data remain host-side;
- the evaluator runs after the agent exits;
- verified repair and evidence qualification are separate metrics.

Mention the execution limitation immediately: the measured model runs used fresh-state subprocess mode because no API key was available. Docker isolation exists, but these results are not Docker-isolated claims.

## 1:20-2:05 — Baseline: successful without an ARI-validated chain

Open the preserved baseline authorization run:

```text
submission/evidence/20260829T143903Z-project-approval-authorization-867f97f7/
```

Show `patch.diff`, then `evaluator.stdout.log` and `report.json`.

Point out:

- the repair passed the hidden evaluator;
- the final comparison records it as verified;
- it did not produce a qualified reproduction, diagnosis, and verification chain.

Do not imply the baseline patch was bad or impossible to review by other means. The measured gap is specifically the absence of an ARI-validated structured evidence chain.

## 2:05-3:20 — V2: event-grounded evidence

Open the matching V2 authorization run:

```text
submission/evidence/20260829T151102Z-project-approval-authorization-26f807af/
```

Show, in order:

1. `final-response.md`, highlighting referenced event IDs;
2. `evidence.jsonl`, locating those same IDs;
3. the raw JSONL trajectory receipt for one event;
4. `patch.diff` and evaluator output.

Explain that the adapter validates the event references, pre-edit/post-edit ordering, exit statuses, distinct focused and broad verification, and relationship to the patch. The model does not qualify evidence merely by writing persuasive prose.

The final artifact records this run as verified and evidence-backed at 103.572s; the matching baseline authorization run was 95.347s.

## 3:20-4:10 — Experiment progression

Show the four-stage table in [final-results.md](final-results.md):

- Development: V1 reached 3/3 verified and 3/3 evidence-backed.
- V1 hard cases: V1 remained 4/4 verified but fell to 0/4 evidence-backed.
- V2 tuning: structured references produced 4/4 verified and 4/4 evidence-backed on those hard cases.
- Final unseen: baseline and V2 both repaired 4/4; qualification was 0/4 versus 4/4.

This sequence shows why the project moved from workflow instructions to structured execution references.

Explicitly identify the discarded experiment: V1 tried to qualify evidence by matching agent-authored free text against pre-edit command output. The hard-case runs showed that this matching layer could reject successful, evidence-disciplined repairs. V2 removed that free-text matcher and replaced it with recorder-issued event IDs; V1 itself and its results remain frozen.

## 4:10-4:45 — Tradeoffs and limits

Show the final aggregate table:

- baseline runtime: 398.229s;
- V2 runtime: 1,186.559s;
- V2's idempotency run: 836.059s, successful with zero retries;
- no dollar-cost result, because these were subscription-authenticated runs without API-key billing estimates.

Say explicitly: the final experiment supports ARI structured-evidence qualification, not higher repair rate or a claim that baseline work is impossible to review, and the final sample contains four synthetic Django/DRF regressions.

## 4:45-5:00 — Close

Close with:

> ARI does not ask reviewers to trust the agent's story. It connects the diagnosis and verification record to commands that actually ran, then checks behavioral correctness with an evaluator that is not placed in the agent workspace.

End on links to the [machine-generated final artifact](../benchmark/comparisons/final-v1.json), [exact reproduction guide](reproduction.md), and [trajectory index](trajectory-index.md).
