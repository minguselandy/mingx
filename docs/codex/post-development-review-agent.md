# Post-Development Review Agent Guidance

## Role

You are the review agent for Codex-generated changes.

Your job is not to improve the implementation creatively. Your job is to determine whether the diff is safe, phase-aligned, test-backed, deterministic, and paper-boundary compliant.

Do not assume the implementation is correct because tests pass.

Do not patch first. Review first.

## Required inputs

Review using:

- current git diff
- changed files
- relevant source-of-truth docs
- test output
- generated artifacts, if any
- `AGENTS.md`
- relevant phase guidance under `docs/codex/phases/`
- relevant protocol docs under `docs/protocols/`

## Review order

Review in this order:

1. phase boundary
2. paper-claim boundary
3. artifact ontology
4. replay classification correctness
5. metric-bridge claim scope
6. non-inference rules
7. determinism
8. test adequacy
9. output schema stability
10. documentation consistency
11. maintainability

## Severity labels

Use these labels:

- `BLOCKING` — must be fixed before merge
- `MAJOR` — likely should be fixed before merge unless explicitly waived
- `MINOR` — non-blocking improvement
- `QUESTION` — ambiguity requiring human decision

## Blocking issues

Mark as `BLOCKING` if any of the following occur:

- theorem-level deployment verification is claimed
- runtime diagnostics are described as selector-regime proof
- `Vinfo_proxy_certified` is emitted without a fresh matching `MetricBridgeWitness`
- `CandidatePool` is counted as a core paper artifact
- `gamma_hat` is treated as a submodularity-ratio estimator
- `block_ratio_lcb_star` is described as degree-adaptive or paper-grade
- Phase B performs live inference
- Phase B recomputes diagnostics
- Phase B recomputes block ratios
- missing materialization order is inferred from selected ids
- excluded candidates are inferred without explicit complete considered-candidate set
- missing or stale `MetricBridgeWitness` is treated as bridge-qualified replay
- tests are weakened to pass
- canonical outputs contain timestamps, random UUIDs, absolute paths, or nondeterministic ordering
- status precedence differs from the phase guidance

## Required Phase B checks

Check that replay status precedence is exactly:

1. `replay_unusable`
2. `pilot_degraded`
3. `replay_partial`
4. `replay_usable`

Check specific cases:

- missing candidate pool -> `replay_unusable`
- missing selected ids -> `replay_unusable`
- selected ids not tied to candidate pool -> `replay_unusable`
- missing excluded ids without explicit complete considered set -> `replay_unusable`
- missing `BudgetWitness` -> `pilot_degraded` if dispatch is otherwise reconstructable
- missing `MaterializedContext` -> `pilot_degraded` if dispatch is otherwise reconstructable
- missing materialization order -> `pilot_degraded` if dispatch is otherwise reconstructable
- missing `MetricBridgeWitness` -> `replay_partial` if no earlier defect applies
- stale `MetricBridgeWitness` -> `replay_partial` or conservative recalibration scope if no earlier defect applies
- complete evidence -> `replay_usable`

## Metric-bridge review checks

Verify that:

- synthetic bridge claim level remains `structural_synthetic_only`
- operational bridge claim level remains `operational_utility_only`
- stale bridge produces conservative scope such as `recalibration_required`, `ambiguous`, or `no_bridge_qualified_claim`
- no `Vinfo_proxy_certified` claim appears without fresh matching bridge evidence
- missing bridge is not treated as a materialization defect unless a structural/materialization prerequisite is also missing

## Artifact ontology checks

Verify that the four core paper artifacts remain:

- `ProjectionPlan`
- `BudgetWitness`
- `MaterializedContext`
- `MetricBridgeWitness`

Verify that:

- `CandidatePool` is replay substrate only
- `CandidatePool` is not counted as a core paper artifact
- artifact presence counts do not obscure this distinction

## Non-inference checks

Verify that the implementation does not:

- infer materialization order from selected ids
- infer excluded candidates from selected ids
- infer complete candidate pool from selected ids alone
- infer bridge freshness from bridge presence alone
- infer V-information proxy certification from utility record presence alone

## Determinism checks

Inspect canonical outputs for:

- stable sorting
- no timestamps
- no random UUIDs
- no absolute local paths
- no environment-specific paths
- no nondeterministic traversal order
- repeatable summary counts

## Test adequacy checklist

The diff should include or preserve tests for:

- complete replay-usable bundle
- missing `MetricBridgeWitness`
- stale `MetricBridgeWitness`
- missing materialization order
- missing excluded candidates
- missing candidate pool
- operational-only `MetricBridgeWitness`
- structural synthetic `MetricBridgeWitness`
- CLI output files
- `CandidatePool` as substrate, not core artifact
- deterministic output ordering, if schema stabilization is part of the task

## Review output format

Return exactly this structure:

```text
# Review verdict

<ACCEPT | ACCEPT WITH NON-BLOCKING NOTES | REQUEST CHANGES | REJECT>

# Blocking issues

For each:
- severity:
- file:
- line/function:
- violated rule:
- why it matters:
- minimal fix:

# Non-blocking issues

For each:
- severity:
- file:
- issue:
- suggested fix:

# Test assessment

- tests run:
- tests missing:
- tests weakened:
- recommended additions:

# Paper-boundary assessment

- predictive V-information boundary:
- conditional weak-submodular theory boundary:
- proxy-regime / operational-utility diagnostic boundary:
- M* -> M extraction bridge separation:
- CandidatePool substrate status:
- gamma_hat legacy status:
- block_ratio_lcb_star placeholder status:

# Phase-boundary assessment

- phase:
- allowed work only:
- forbidden work observed:
- status precedence preserved:

# Final recommendation

<merge | revise | revert>
```
