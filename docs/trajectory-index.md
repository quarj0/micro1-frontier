# Representative trajectory submission index

Raw trajectories and run directories remain ignored by Git. This index identifies the small, sanitized representative set intentionally promoted under [`submission/`](../submission/README.md) so a judge can inspect it from a clean clone. The preserved raw source runs were not edited.

## Recommended core pair

Submit these two trajectories together. They cover the same difficult final authorization regression, both produced evaluator-verified repairs, and their runtimes were close enough that the comparison centers on evidence behavior rather than the final idempotency runtime outlier.

| Role | Workflow | Run ID | Verified | Evidence-backed | Runtime |
|---|---|---|---:|---:|---:|
| General-purpose control | Baseline | `20260829T143903Z-project-approval-authorization-867f97f7` | yes | no | 95.347s |
| Structured-evidence result | Advanced V2 | `20260829T151102Z-project-approval-authorization-26f807af` | yes | yes | 103.572s |

Sources: the exact rows in [final-v1.json](../benchmark/comparisons/final-v1.json).

Committed bundle paths:

```text
submission/evidence/20260829T143903Z-project-approval-authorization-867f97f7/
submission/evidence/20260829T151102Z-project-approval-authorization-26f807af/
```

Each directory includes the trajectory, report, patch, evaluator stdout/stderr, and final response. The V2 directory also includes its structured `evidence.jsonl`.

- Baseline authorization: [trajectory](../submission/evidence/20260829T143903Z-project-approval-authorization-867f97f7/trajectory.jsonl) and [report](../submission/evidence/20260829T143903Z-project-approval-authorization-867f97f7/report.json)
- V2 authorization: [trajectory](../submission/evidence/20260829T151102Z-project-approval-authorization-26f807af/trajectory.jsonl), [report](../submission/evidence/20260829T151102Z-project-approval-authorization-26f807af/report.json), and [structured evidence](../submission/evidence/20260829T151102Z-project-approval-authorization-26f807af/evidence.jsonl)

What reviewers should compare:

1. Both patches pass the same host-side hidden evaluator.
2. The baseline trajectory contains useful engineering work but no ARI-validated structured reproduction/diagnosis/verification chain.
3. The V2 final response cites recorder-issued event IDs.
4. V2 `evidence.jsonl` binds those IDs to command phase, ordering, exit state, output hashes/excerpts, edit state, and patch-aware verification.

## Recommended workflow-evolution pair

If the submission can include two more trajectories, use the same cross-tenant hard case from V1 and V2 tuning:

| Role | Workflow | Run ID | Verified | Evidence-backed | Runtime |
|---|---|---|---:|---:|---:|
| Free-text evidence limitation | Advanced V1 | `20260829T123603Z-cross-tenant-data-exposure-d282d5bf` | yes | no | 116.370s |
| Structured event references | Advanced V2 | `20260829T130732Z-cross-tenant-data-exposure-070153fe` | yes | yes | 86.521s |

Sources: [heldout-v1.json](../benchmark/comparisons/heldout-v1.json) and [advanced-v2-heldout-tuning.json](../benchmark/comparisons/advanced-v2-heldout-tuning.json).

Committed bundle paths:

```text
submission/evidence/20260829T123603Z-cross-tenant-data-exposure-d282d5bf/
submission/evidence/20260829T130732Z-cross-tenant-data-exposure-070153fe/
```

This pair explains why V2 exists: both runs repaired the hard case, while only the structured-reference run qualified as evidence-backed.

- V1 cross-tenant: [trajectory](../submission/evidence/20260829T123603Z-cross-tenant-data-exposure-d282d5bf/trajectory.jsonl) and [report](../submission/evidence/20260829T123603Z-cross-tenant-data-exposure-d282d5bf/report.json)
- V2 cross-tenant: [trajectory](../submission/evidence/20260829T130732Z-cross-tenant-data-exposure-070153fe/trajectory.jsonl), [report](../submission/evidence/20260829T130732Z-cross-tenant-data-exposure-070153fe/report.json), and [structured evidence](../submission/evidence/20260829T130732Z-cross-tenant-data-exposure-070153fe/evidence.jsonl)

## Representative build-agent trajectories

Two curated excerpts show how the benchmark itself was designed and why the evidence representation changed:

- [`design-and-implementation.trajectory-excerpt.jsonl`](../submission/build-agent/design-and-implementation.trajectory-excerpt.jsonl) covers the provider-neutral harness, Docker trust boundary, first end-to-end cases, and early evidence metric design.
- [`v1-to-v2-decision.trajectory-excerpt.jsonl`](../submission/build-agent/v1-to-v2-decision.trajectory-excerpt.jsonl) covers the observed V1 free-text matching failure and the decision to replace it with recorder-issued event references in V2.

These are explicitly marked excerpts, not complete Codex sessions. Their first record documents the source session, selection basis, path sanitization, and omitted material. They are project-construction context rather than benchmark-agent evidence and are not inputs to any measured result.

## Runtime-tradeoff appendix

The runtime-outlier trajectory is intentionally not part of the small promoted bundle. The [committed final artifact](../benchmark/comparisons/final-v1.json) identifies it as run `20260829T144641Z-idempotency-key-collision-4ac99df2` and records it at 836.059s, verified and evidence-backed, with zero retries. It should be presented as an observed one-shot runtime outlier, not discarded or explained with an unmeasured cause.

## Packaging checklist

- Use the committed files under `submission/`; preserve filenames and run IDs exactly.
- Treat evidence-run JSONL as sanitized complete copies. The separately labeled build-agent files are curated excerpts.
- Keep `report.json`, `patch.diff`, evaluator output, final response, and V2 evidence beside each trajectory.
- Verify promoted-file hashes with [`submission/SHA256SUMS`](../submission/SHA256SUMS). Original source-report hashes are recorded in the bundle README and match the relevant committed comparison JSON.
- State that raw artifacts use synthetic repositories and were produced in subprocess mode.
- Do not label these trajectories Docker-isolated; they are fresh-state, evaluator-separated subprocess runs.
- Review the upload bundle for credentials even though the adapters were designed not to write authentication material into trajectories or reports.
