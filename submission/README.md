# Sanitized representative evidence bundle

This directory is the intentionally committed, clone-visible subset referenced by [`docs/trajectory-index.md`](../docs/trajectory-index.md). It contains synthetic benchmark data only. The original generated runs remain ignored under `benchmark/results/` and `trajectories/` and were not changed.

## Evidence runs

| Comparison | Workflow | Run ID | Why included |
|---|---|---|---|
| Final authorization | Baseline | `20260829T143903Z-project-approval-authorization-867f97f7` | Verified control repair without an ARI-validated structured evidence chain |
| Final authorization | Advanced V2 | `20260829T151102Z-project-approval-authorization-26f807af` | Same final regression with recorder-issued evidence references |
| Cross-tenant evolution | Advanced V1 | `20260829T123603Z-cross-tenant-data-exposure-d282d5bf` | Verified repair rejected by V1 free-text evidence matching |
| Cross-tenant evolution | Advanced V2 | `20260829T130732Z-cross-tenant-data-exposure-070153fe` | Same hard regression after structured event references replaced free-text matching |

Each evidence directory contains a complete sanitized copy of the run trajectory plus its report, patch, evaluator logs, and final response. Structured evidence is included where the source run produced it.

## Build-agent excerpts

The files under `build-agent/` are curated excerpts from the Codex build session `01a048e2-af3c-7e41-a3c5-478cb7a67f6f`:

- `design-and-implementation.trajectory-excerpt.jsonl` shows the initial architecture and harness implementation.
- `v1-to-v2-decision.trajectory-excerpt.jsonl` shows the V1 matching failure, the V2 event-reference boundary, and the separate V2 implementation milestone.

They are not complete session exports and are not benchmark-agent inputs or measured results. Each excerpt begins with machine-readable sanitization metadata. Unrelated conversation, approval-system envelopes, and large patch bodies were omitted; implementation events were retained as concise summaries.

## Sanitization and integrity

The promoted evidence copies replace the absolute repository root with `<REPOSITORY>` and the user home with `<HOME>`. Trailing spaces on otherwise blank added lines in copied `patch.diff` files were normalized so the repository passes `git diff --check`; patch hunks and behavior are unchanged. No behavioral result, metric, run ID, command exit state, or evaluator outcome was changed. Because sanitization changes bytes, the promoted `report.json` hashes differ from their raw sources.

Original source-report SHA-256 values, as committed in the machine-generated comparisons:

| Run ID | Source report SHA-256 |
|---|---|
| `20260829T123603Z-cross-tenant-data-exposure-d282d5bf` | `06ab3e344fae24fc4b68bea55afc511ea92464ae2df792922150c9dbf95af6dc` |
| `20260829T130732Z-cross-tenant-data-exposure-070153fe` | `31795bd70d5f472a37088e88f8771fb27646c62157ab1cadb6d77668c476ea3b` |
| `20260829T143903Z-project-approval-authorization-867f97f7` | `463cec32c7dcca66c0367ace27453745f75a7f94e71a08be1a975f91fadafb24` |
| `20260829T151102Z-project-approval-authorization-26f807af` | `604f0ea80c3575006a9de6dab4a2db292e64d2302da2e4051202a1c51a0a3c04` |

Run `sha256sum -c submission/SHA256SUMS` from the repository root to verify every promoted trajectory and run artifact. The final polish pass also scans this directory for common API keys, access tokens, private keys, authorization headers, passwords, and unsanitized home paths before staging it.
