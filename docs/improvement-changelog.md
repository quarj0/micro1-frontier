# Improvement changelog

This changelog describes workflow changes and the measurements that motivated them. It does not treat benchmark-case construction as product improvement, and it does not combine development, tuning, and final results.

## Baseline: credible general-purpose coding agent

Changed:

- Added a provider-neutral command adapter around one Codex CLI agent.
- Fixed Codex CLI 0.150.1, `gpt-5.6-sol`, medium reasoning, and one-agent execution.
- Captured raw JSONL trajectory, exit state, runtime, Git patch, tests, and token usage when available.
- Kept the instruction intentionally simple, with no reproduction gate, evidence ledger, verifier, or retry controller.

Measured:

- Development: 3/3 verified repairs, 0/3 evidence-backed repairs.
- V1 hard cases: 4/4 verified, 0/4 evidence-backed.
- Final unseen: 4/4 verified, 0/4 evidence-backed.

Sources: [development comparison](../benchmark/comparisons/advanced-v1-development.json), [V1 hard-case comparison](../benchmark/comparisons/heldout-v1.json), and [final comparison](../benchmark/comparisons/final-v1.json).

Interpretation: the baseline was already a strong repair agent in this benchmark. The remaining measured problem was auditability, not patch success.

## Advanced V1: evidence-disciplined repair sequence

Changed:

- Required a failing pre-edit reproduction.
- Required a causal hypothesis grounded in pre-edit repository or runtime observations.
- Required targeted repair, focused verification, and distinct broad verification.
- Added explicit abstention and at most one verification-triggered retry.
- Corroborated agent-reported commands and excerpts against raw command events.

Measured:

- Development: 3/3 verified and 3/3 evidence-backed, compared with baseline's 3/3 verified and 0/3 evidence-backed.
- Hard cases: 4/4 verified but 0/4 evidence-backed. V1's evidence representation depended on matching agent-authored prose to raw command output, so successful repairs could still fail qualification.
- Hard-case aggregate runtime was 480.772s for V1 versus 374.252s for baseline; retries were 0 for both.

Sources: [development comparison](../benchmark/comparisons/advanced-v1-development.json) and [V1 hard-case comparison](../benchmark/comparisons/heldout-v1.json).

Interpretation: V1 showed that evidence discipline could work on public development cases, but its free-text evidence link was not reliable on the harder suite.

## Advanced V2: structured execution-event references

Changed:

- Preserved V1's repair instructions, model, reasoning level, tools, and one-retry limit.
- Replaced copied/paraphrased output evidence with recorder-issued event IDs.
- Recorded phase, command argv, timestamp/order, exit code, stdout/stderr hashes and excerpts, edit state, and patch state.
- Required final diagnosis and verification records to cite actual event IDs.
- Cross-checked recorder records against receipts in raw Codex command events.
- Validated pre-edit/post-edit ordering and that verification ran against the reported patch.

Measured during V2 tuning on the same four hard cases:

- V1: 4/4 verified, 0/4 evidence-backed, 480.772s.
- V2: 4/4 verified, 4/4 evidence-backed, 372.759s.
- V2 runtime was 22.5% lower in this tuning comparison.
- Output tokens were 11,851 for V2 versus 19,036 for V1; retries were 0 for both.

Source: [V2 tuning comparison](../benchmark/comparisons/advanced-v2-heldout-tuning.json).

Interpretation: structured references fixed the measured evidence-qualification failure on the tuning suite without changing repair success.

## Final freeze and unseen evaluation

Changed before execution:

- Added four fresh final regressions: idempotency-key collision, timezone boundary error, multipart parser regression, and project-scoped authorization.
- Independently verified visible tests on every broken input, each intended hidden failure, and each minimal-repair hidden pass.
- Froze case trees and workflow hashes at commit `1298a75`.

No workflow or case changed after freeze or after results were observed.

Measured in the single final pass:

- Baseline: 4/4 verified, 0/4 evidence-backed, 398.229s.
- V2: 4/4 verified, 4/4 evidence-backed, 1,186.559s.
- V2 used 584,132 input tokens versus baseline's 660,493, but 12,339 output and 3,606 reasoning tokens versus baseline's 10,437 output and 1,938 reasoning tokens.
- No retry occurred in either workflow.
- One V2 idempotency run took 836.059s and dominates V2's aggregate runtime.

Sources: [final comparison](../benchmark/comparisons/final-v1.json) and [preflight record](../benchmark/validations/final-v1-preflight.json).

Interpretation: the final experiment supports the auditability claim. It does not show a verified-repair-rate improvement, because both workflows repaired all four cases. It also shows a material, variable runtime cost for V2 in the final pass.

## Frozen state

The experiment is complete. Baseline, Advanced V1, Advanced V2, benchmark cases, evaluators, comparison selections, and final suite are historical controls and must not be tuned further. Future work should use new workflow names and new suites rather than rewriting these results.
