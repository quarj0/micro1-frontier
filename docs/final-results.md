# Final results summary

## Claim supported by the experiment

A general-purpose coding agent repaired all four final unseen Django/DRF regressions. ARI V2 did not increase that already-perfect verified repair rate; it preserved 4/4 success while turning 0/4 evidence-backed baseline repairs into 4/4 evidence-backed repairs grounded in actual execution events.

This is an auditability result, not a claim that V2 repaired more bugs.

## Final unseen suite

The suite was frozen before agent execution and contained:

1. idempotency-key collision across tenants;
2. timezone and daylight-saving day-boundary error;
3. multipart file-upload parser regression;
4. same-tenant, project-scoped approval authorization regression.

The [preflight record](../benchmark/validations/final-v1-preflight.json) records that each visible suite passed on the broken input, each hidden evaluator failed for the intended regression, and each evaluator passed after a minimal repair in a disposable copy. The suite and workflow hashes were committed at `1298a75` before model execution.

## Aggregate

| Workflow | Cases | Verified | Evidence-backed | Runtime | Input | Cached input | Output | Reasoning | Retries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 4 | 4/4 | 0/4 | 398.229s | 660,493 | 548,864 | 10,437 | 1,938 | 0 |
| Advanced V2 | 4 | 4/4 | 4/4 | 1,186.559s | 584,132 | 434,944 | 12,339 | 3,606 | 0 |

Source: [final-v1.json](../benchmark/comparisons/final-v1.json). Values above are rounded only for runtime display; the JSON retains full precision.

## Exact selected runs

| Workflow | Case | Run ID | Verified | Evidence-backed | Runtime |
|---|---|---|---:|---:|---:|
| Baseline | File upload parser | `20260829T143555Z-file-upload-parser-regression-27a4bbcd` | yes | no | 116.364s |
| Baseline | Idempotency collision | `20260829T143752Z-idempotency-key-collision-d93b525f` | yes | no | 70.168s |
| Baseline | Project approval authorization | `20260829T143903Z-project-approval-authorization-867f97f7` | yes | no | 95.347s |
| Baseline | Timezone boundary | `20260829T144039Z-timezone-boundary-error-484c6afd` | yes | no | 116.349s |
| Advanced V2 | File upload parser | `20260829T144434Z-file-upload-parser-regression-43cc4f2c` | yes | yes | 126.278s |
| Advanced V2 | Idempotency collision | `20260829T144641Z-idempotency-key-collision-4ac99df2` | yes | yes | 836.059s |
| Advanced V2 | Project approval authorization | `20260829T151102Z-project-approval-authorization-26f807af` | yes | yes | 103.572s |
| Advanced V2 | Timezone boundary | `20260829T151246Z-timezone-boundary-error-5804a2d4` | yes | yes | 120.651s |

The exact selection policy, source report paths, and SHA-256 report hashes are committed in [final-v1.spec.json](../benchmark/comparisons/final-v1.spec.json) and [final-v1.json](../benchmark/comparisons/final-v1.json). Exactly one completed run per workflow/case was selected; no result-triggered rerun occurred.

## Runtime and usage tradeoff

V2 aggregate runtime was 2.98 times baseline in the final pass. The 836.059s idempotency run accounts for most of that difference. The other three V2 runs were 126.278s, 103.572s, and 120.651s. Because the idempotency run succeeded with zero retries and the experiment forbade reruns, the outlier remains part of the headline total.

V2 used 11.6% fewer input tokens than baseline in aggregate, while output tokens were 18.2% higher and reasoning tokens were higher in absolute terms: 3,606 versus 1,938. These usage values do not establish dollar cost. The runs used host subscription authentication, and the committed reports contain no API-key billing estimate.

## Relationship to earlier stages

| Stage | Comparison | Main measured result |
|---|---|---|
| Development | [advanced-v1-development](../benchmark/comparisons/advanced-v1-development.json) | Baseline 3/3 verified and 0/3 evidence-backed; V1 3/3 and 3/3. |
| V1 hard-case tuning | [heldout-v1](../benchmark/comparisons/heldout-v1.json) | Baseline and V1 both 4/4 verified and 0/4 evidence-backed. |
| V2 tuning | [advanced-v2-heldout-tuning](../benchmark/comparisons/advanced-v2-heldout-tuning.json) | V1 stayed 4/4 verified and 0/4 evidence-backed; V2 reached 4/4 and 4/4. |
| Final unseen | [final-v1](../benchmark/comparisons/final-v1.json) | Baseline and V2 both 4/4 verified; evidence qualification was 0/4 versus 4/4. |

Development and tuning measurements explain workflow evolution. Only the final unseen suite is the one-shot final evaluation.

## Limitations

- Four final cases are enough to demonstrate the evidence mechanism but not enough to estimate broad population-level repair rates.
- All cases are synthetic Django/DRF repositories.
- The final runs were subprocess executions with fresh workspaces and ephemeral Codex homes because `CODEX_API_KEY` was unavailable. Hidden evaluators were separated from the agent workspace, but subprocess mode is not a filesystem security boundary.
- Docker is implemented as the intended official isolation mode, but these measured results are not Docker-isolated API-key results.
- Both workflows repaired every final case, so this experiment cannot support a claim that V2 improves verified repair rate.
