# Development benchmark design

## Purpose

The development suite validates the benchmark machinery and provides public cases for improving an evidence-disciplined workflow. It is not the final held-out evaluation set.

Each case contains a standalone broken Django/DRF repository with its own pinned `pyproject.toml` and `uv.lock`, a realistic issue report, synthetic data, ordinary visible tests, and a separate evaluator. The agent is expected to establish the failure, locate its cause, make a production-code repair, and leave reviewable evidence.

## Trust boundary

```text
Host repository
├── case/input/ ---------- copied ----------> isolated /workspace
└── case/evaluator/ -- not mounted --> [agent container cannot see it]
                                            |
                                            v exits
                                      host evaluator runs
```

Docker mode provides the official isolation boundary:

- Only the prepared case workspace is mounted.
- The container root filesystem is read-only.
- The workspace mount is writable.
- Network defaults to `none`.
- Images are never pulled implicitly during a timed run; the selected image must already exist locally.
- Linux capabilities are dropped and privilege escalation is disabled.
- The Docker socket, host repository, evaluator, oracle, and other cases are absent.
- A hard timeout kills the named container.

The evaluator runs as a host process only after the agent container has terminated. Hidden tests are then copied temporarily into the workspace, executed with the pinned root environment, and removed.

Subprocess mode provides no security boundary and exists only for rapid harness development.

## Fixed model control

The baseline and all later workflow variants use Codex CLI 0.150.1 with `gpt-5.6-sol` at medium reasoning. Model and reasoning level are controlled variables: workflow changes must not alter them. Official Codex runs also use a fresh, ephemeral `CODEX_HOME`, ignore user configuration and rules, and disable multi-agent, memory, plugin, app, and skill-discovery features.

The hosted model requires an explicit `--allow-network` exception. Credentials are forwarded by environment-variable name at runtime and never written into the repository, workspace, image, trajectory, or report. Case repositories contain only controlled synthetic code and data.

## Case layout

```text
case-id/
├── case.toml
├── input/
│   ├── issue.md
│   └── repo/
└── evaluator/
    ├── oracle.toml
    └── tests/
```

`oracle.toml` records causal targets for later evidence scoring. The current verified-repair metric is behavioral: hidden tests and the visible suite must pass. Automated diagnosis-quality scoring will be added only after its rubric is validated; the scaffold does not claim that a green test suite alone proves evidence quality.

## Current cases

| Case | Failure mechanism | Adjacent behavior protected by hidden tests |
|---|---|---|
| Response contract drift | Serializer output field renamed | Exact shape and non-exposure of internal data |
| Incorrect boolean filtering | Nonempty strings coerced with `bool()` | True, false, case handling, omission, and invalid input |
| Nested-write atomicity | Parent saved before later nested validation fails | Rollback of parent and earlier children; valid commit |

## Current primary metric

The scaffold reports `verified_repair` when the host-side evaluator exits successfully. The suite aggregate reports verified repairs divided by attempted cases.

This is an initial engineering metric. Before final evaluation, the full evidence-backed definition must also enforce structured reproduction evidence, accepted causal localization, no forbidden test weakening, and claim-to-execution traceability.
