# Representative trajectory submission index

Raw trajectories and run directories are intentionally ignored by Git. This index identifies the smallest useful submission set from the preserved local runs. It does not promote or rewrite them.

## Recommended core pair

Submit these two trajectories together. They cover the same difficult final authorization regression, both produced evaluator-verified repairs, and their runtimes were close enough that the comparison centers on evidence behavior rather than the final idempotency runtime outlier.

| Role | Workflow | Run ID | Verified | Evidence-backed | Runtime |
|---|---|---|---:|---:|---:|
| General-purpose control | Baseline | `20260829T143903Z-project-approval-authorization-867f97f7` | yes | no | 95.347s |
| Structured-evidence result | Advanced V2 | `20260829T151102Z-project-approval-authorization-26f807af` | yes | yes | 103.572s |

Sources: the exact rows in [final-v1.json](../benchmark/comparisons/final-v1.json).

Local trajectory paths:

```text
trajectories/20260829T143903Z-project-approval-authorization-867f97f7.jsonl
trajectories/20260829T151102Z-project-approval-authorization-26f807af.jsonl
```

For each run, submit the trajectory together with the corresponding preserved directory under `benchmark/results/<run-id>/`. At minimum include `report.json`, `patch.diff`, evaluator stdout/stderr, and `final-response.md`. For V2 also include `evidence.jsonl`.

What reviewers should compare:

1. Both patches pass the same host-side hidden evaluator.
2. The baseline trajectory contains useful engineering work but no separately qualified reproduction/diagnosis/verification chain.
3. The V2 final response cites recorder-issued event IDs.
4. V2 `evidence.jsonl` binds those IDs to command phase, ordering, exit state, output hashes/excerpts, edit state, and patch-aware verification.

## Recommended workflow-evolution pair

If the submission can include two more trajectories, use the same cross-tenant hard case from V1 and V2 tuning:

| Role | Workflow | Run ID | Verified | Evidence-backed | Runtime |
|---|---|---|---:|---:|---:|
| Free-text evidence limitation | Advanced V1 | `20260829T123603Z-cross-tenant-data-exposure-d282d5bf` | yes | no | 116.370s |
| Structured event references | Advanced V2 | `20260829T130732Z-cross-tenant-data-exposure-070153fe` | yes | yes | 86.521s |

Sources: [heldout-v1.json](../benchmark/comparisons/heldout-v1.json) and [advanced-v2-heldout-tuning.json](../benchmark/comparisons/advanced-v2-heldout-tuning.json).

Local paths:

```text
trajectories/20260829T123603Z-cross-tenant-data-exposure-d282d5bf.jsonl
trajectories/20260829T130732Z-cross-tenant-data-exposure-070153fe.jsonl
```

This pair explains why V2 exists: both runs repaired the hard case, while only the structured-reference run qualified as evidence-backed.

## Runtime-tradeoff appendix

If reviewers need to audit the final runtime caveat, also submit:

```text
trajectories/20260829T144641Z-idempotency-key-collision-4ac99df2.jsonl
benchmark/results/20260829T144641Z-idempotency-key-collision-4ac99df2/
```

The committed final artifact records this V2 run at 836.059s, verified and evidence-backed, with zero retries. It should be presented as an observed one-shot runtime outlier, not discarded or explained with an unmeasured cause.

## Packaging checklist

- Preserve filenames and run IDs exactly.
- Do not edit or truncate JSONL. If the submission system imposes a size limit, archive the complete files rather than copying selected lines.
- Keep `report.json`, `patch.diff`, evaluator output, final response, and V2 evidence beside each trajectory.
- Verify that the run ID and source report SHA-256 match the row committed in the relevant comparison JSON.
- State that raw artifacts use synthetic repositories and were produced in subprocess mode.
- Do not label these trajectories Docker-isolated; they are fresh-state, evaluator-separated subprocess runs.
- Review the upload bundle for credentials even though the adapters were designed not to write authentication material into trajectories or reports.
