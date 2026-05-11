# Mingx v12 Follow-up Development and Experiment Documents

This package contains Codex-facing development plans and corresponding review documents for each follow-up phase.

## Phase Order

| Phase | Development Plan | Review Document | Purpose |
|---|---|---|---|
| P45 | `P45-one-stratum-bridge-calibration-plan.md` | `P45-one-stratum-bridge-calibration-review.md` | Implemented the first executable metric-bridge calibration lane; current `bio_attribute` stratum is closed as non-calibrated |
| P46 | `P46-synthetic-v12-artifact-refresh-plan.md` | `P46-synthetic-v12-artifact-refresh-review.md` | Refresh synthetic benchmark outputs using v12 labels and cost accounting |
| P47 | `P47-model-adjudicated-realistic-benchmark-plan.md` | `P47-model-adjudicated-realistic-benchmark-review.md` | Build a model-adjudicated realistic-task benchmark |
| P48 | `P48-phase-b-replay-v12-hardening-plan.md` | `P48-phase-b-replay-v12-hardening-review.md` | Harden Phase B replay under v12 claim semantics |
| P49 | `P49-extraction-audit-pilot-plan.md` | `P49-extraction-audit-pilot-review.md` | Implement a pilot extraction-risk audit |
| P50 | `P50-optional-reprojection-witness-plan.md` | `P50-optional-reprojection-witness-review.md` | Optional runtime re-projection / uncertainty-triggered projection extension |

## Recommended Usage

For each phase:
1. Give Codex the corresponding `*-plan.md`.
2. After Codex completes the implementation, give it the corresponding `*-review.md` for a read-only review.
3. Do not proceed to the next phase until the review verdict is `ACCEPT` or all blocking issues are fixed.
4. Each phase must produce a Chinese final report with changed files, validation commands, remaining claim boundaries, and next steps.

## Current Priority

P45 is closed for the current `bio_attribute` stratum as implemented but
non-calibrated. The closure record is
`docs/experiments/P45-bridge-calibration-closure.md`. The next active phase is
**P46 - synthetic v12 artifact refresh**.

## Repository Placement Note

This folder is the controlling Codex development/reference package for v12
follow-up work. P50 is optional and must not precede P46-P49 unless explicitly
deferred. These phase docs do not claim `measurement_validated` evidence, do
not supply bridge calibration results by themselves, and do not authorize live
API work.
