# Benchmark design and trust boundary

## Purpose

ARI evaluates two separate outcomes for Django REST Framework regression repair:

1. **Verified repair:** does a host-side hidden evaluator accept the patched repository?
2. **Evidence-backed repair:** does a verified patch also carry a validated reproduction, diagnosis, and verification chain grounded in commands that actually ran?

This separation matters because the final baseline repaired every regression while qualifying no evidence chain. ARI V2 preserved the same repair result and qualified every chain. See [final-results.md](final-results.md) for the measurements.

## Case structure

Each case is a standalone broken Django/DRF repository with pinned dependencies, a synthetic issue report and data, visible tests, and a separate hidden evaluator.

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

The agent-facing input never includes `evaluator/`, hidden tests, the oracle, other cases, or case-construction notes.

## Trust boundary

```text
Host repository
├── case/input/ ---------- copied ----------> agent /workspace
└── case/evaluator/ -- withheld -----------> host evaluator after agent exit
```

Docker mode is the intended official boundary:

- only the prepared case workspace is mounted;
- the container root filesystem is read-only;
- the workspace is writable;
- network defaults to `none`;
- images are not pulled during a timed run;
- Linux capabilities are dropped and privilege escalation is disabled;
- the Docker socket, host repository, evaluator, oracle, and other cases are absent;
- a hard timeout terminates the named container.

The host copies hidden tests into the workspace only after the agent process exits, runs the evaluator, and removes those tests.

Subprocess mode uses a fresh temporary workspace and, for the Codex adapters, a fresh ephemeral `CODEX_HOME`. It does not provide filesystem or environment isolation. All committed measured model comparisons used subprocess mode because no API key was available, so they must not be represented as Docker-isolated results.

## Controlled model and tools

Baseline, V1, and V2 use:

- Codex CLI 0.150.1;
- `gpt-5.6-sol`;
- medium reasoning;
- one agent;
- the same repository inspection, editing, and test tools;
- disabled multi-agent, memory, plugin, app, and skill-discovery features.

The baseline receives a simple repair instruction and one fresh Codex turn.

V1 changes the workflow by requiring pre-edit reproduction and diagnosis evidence, targeted repair, focused and broad verification, abstention, and at most one verification-triggered retry. V1 links evidence by comparing agent-authored command/output records with raw command events.

V2 preserves V1's repair sequence and controls but replaces free-text evidence linkage with structured recorder event IDs.

## V2 command evidence

Every evidence-bearing V2 command runs through `ari-evidence`, which records:

- event ID and phase: reproduction, investigation, focused verification, or broad verification;
- argv and display command;
- start/finish timestamps and monotonic order;
- exit status;
- SHA-256 hashes and bounded excerpts for stdout and stderr;
- before-edit, after-edit, or edit-spanning state;
- changed files present before and after execution.

The recorder emits a receipt into the raw command output. The adapter accepts a cited event only when the recorder record, digest, receipt, raw Codex command event, and exit status agree.

For a successful evidence chain, qualification requires:

- a cited failing reproduction event before the first source edit;
- a non-empty diagnosis citing corroborated pre-edit reproduction/investigation events;
- reported repair files that match the Git patch, including a production file;
- a cited passing focused verification after editing;
- a distinct, later, passing broad verification after editing;
- verification events whose recorded patch state contains the reported repair files.

The hidden evaluator then independently determines behavioral correctness.

## Benchmark stages and cases

### Development suite

- Response contract drift.
- Incorrect boolean filtering.
- Nested-write atomicity failure.

These public cases established and debugged the complete benchmark loop and V1 workflow.

### V1 hard-case and V2 tuning suite

- Cross-tenant data exposure.
- Unstable cursor pagination.
- Query-count regression.
- Cross-tenant cache contamination.

The workflow hashes were frozen for the V1 comparison. The same cases then served as V2 development/tuning cases; they are not the final unseen evaluation.

### Final unseen suite

- Idempotency-key collision.
- Timezone boundary error.
- File-upload parser regression.
- Project-scoped approval authorization.

Before execution, every broken repository was independently checked for visible-test behavior and intended hidden-evaluator failure; every evaluator was also validated against a minimal repair in a disposable copy. Case-tree and workflow hashes were frozen at commit `1298a75`. Baseline and V2 then ran exactly once per case.

## Metrics and reports

`verified_repair` is true when the host evaluator exits successfully.

`evidence_backed_repair` is true only when the evaluator passes and validated evidence contains reproduction, diagnosis, and verification event types.

Every run report also records process state, exit code, runtime, patch, changed files, trajectory parsing, evidence parsing, and normalized token usage when available. Comparison artifacts are generated from explicit run-ID specs and include source report SHA-256 values.

No automated metric claims that a passing patch is minimal, production-ready, or generally correct beyond the protected behavior. No committed measurement supplies API-key dollar cost.

## Experiment immutability

The experiment is complete. Existing workflows, cases, evaluators, suite manifests, run selections, and comparison artifacts are historical controls. Further research should introduce new version names and new suites instead of tuning these frozen stages.
