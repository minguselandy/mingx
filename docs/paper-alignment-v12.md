# Paper Alignment V12

This document maps the current fixed v12 Context Projection Selection paper
direction to the repository. It is the default paper-alignment entrypoint for
new implementation, review, and evidence-planning work.

Current manuscript anchor:

- `docs/archive/context_projection_fixed_v12.md`

Legacy manuscript and alignment anchors:

- `docs/archive/context_projection_revised_v10.md`
- `docs/paper-alignment-v10.md`

The v10 files are preserved as historical/archive material. They should not be
used as the default source for new paper-facing terminology.

## Current Paper Direction

The v12 paper is framed as:

```text
conditional theory + metric bridge + proxy-regime diagnosis + minimal structural evidence
```

The active framing is proxy-regime diagnosis, not proxy-regime certification.
The repository remains a measurement and runtime-audit scaffold. It does not
claim deployed V-information verification, measurement validation, scientific
validation, theorem inheritance for heuristic pipelines, or scheduler
correctness.

## V12 Claim Vocabulary

Selector-regime labels should migrate toward:

- `greedy_supported`
- `pairwise_escalate`
- `higher_order_risk`
- `ambiguous`

Metric-claim levels should migrate toward:

- `vinfo_proxy_supported`
- `calibrated_proxy_supported`
- `operational_utility_only`
- `ambiguous_metric`

Deprecated or risky active vocabulary includes:

- `Vinfo_proxy_certified`
- `greedy_valid`
- bare `escalate` when it should distinguish `pairwise_escalate` from
  `higher_order_risk`
- proxy-regime `certification` language when the intended claim is diagnosis

Historical artifacts, old reviews, and denied-claim guardrails may still mention
legacy labels. New paper-facing reports should either use the v12 vocabulary or
explicitly mark legacy vocabulary as compatibility or archive state.

## Repo Evidence Lanes

| V12 paper lane | Repository surface | Current status |
|---|---|---|
| dispatch-time context projection artifacts | `cps/experiments/artifacts.py`, `cps/runtime/projection_export.py`, `cps/schema/projection_bundle_v1.py` | Implemented scaffold for `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, `MetricBridgeWitness`, and `ProjectionBundleV1` |
| claim-gated proxy-regime diagnosis | `cps/experiments/metric_bridge_gate.py`, `cps/experiments/claim_gate_report.py`, `cps/experiments/proxy_regime_matrix.py` | Implemented guardrail scaffold; terminology migration remains |
| synthetic structural evidence | `cps/experiments/synthetic_benchmark.py`, `docs/experiments/synthetic-regime-benchmark.md`, synthetic experiment artifacts | Implemented structural smoke evidence; not measurement validation |
| one-stratum metric bridge calibration | `cps/experiments/bridge_calibration.py`, `configs/runs/bridge-calibration-one-stratum.json`, `docs/experiments/bridge-calibration-one-stratum.md`, `docs/experiments/P45-bridge-calibration-closure.md` | P45 lane implemented and operator/API-ready; current `bio_attribute` stratum failed to establish the bridge, so no `calibrated_proxy_supported` claim is allowed |
| Phase B replay | `cps/experiments/phase_b_replay.py`, `cps/experiments/replay_evidence_package.py`, `docs/protocols/phase-b-replay-protocol.md` | Implemented replay scaffold; v12 hardening remains |
| model-adjudicated evidence | `cps/experiments/route_b_evidence_package.py`, `cps/experiments/model_adjudicated_labels.py` | Pilot/model-adjudicated evidence only; not human labels or kappa |
| extraction audit | `docs/protocols/extraction-uniformity-sidecar-plan.md`, `docs/reviews/extraction-uniformity-sidecar-review.md` | Planned sidecar; no measurement validation is claimed |

## Bridge Calibration Closure

P45 implemented the offline/importable lane and the opt-in API-generated data
scaffold. Fixture inputs validate engineering behavior only. Live canaries
verified that the fixed-model measured-logprob path works under explicit target
evidence, but the current `bio_attribute` stratum did not establish a stable
utility-to-logloss bridge.

The target quantities remain:

- `c_s`
- `zeta_s`
- sign agreement
- rank correlation
- held-out residual bound
- claim downgrade behavior

For the current `bio_attribute` stratum, no `calibrated_proxy_supported` claim
is allowed. Downstream utility or model-adjudicated diagnostics should remain
`operational_utility_only`; the P45e canary artifact itself is
`ambiguous_metric` because the exported bridge-fit rows were underpowered and
failed the configured `zeta_s` gate. Synthetic structural evidence remains
structural evidence only.

Do not expand this same stratum to a 20-30 row P45 pilot without a new
scientific rationale, a new active stratum, or a materially new
fixed-logloss/utility design.

## Active Planning Reference

The controlling Codex development/reference package for v12 follow-up work is:

- `docs/codex/v12-phase-docs/README.md`
- `docs/codex/v12-phase-docs/P45-one-stratum-bridge-calibration-plan.md`
- `docs/experiments/P45-bridge-calibration-closure.md`
- `docs/codex/v12-phase-docs/P46-synthetic-v12-artifact-refresh-plan.md`

P45 is closed for the current `bio_attribute` stratum as implemented but
non-calibrated. The next active phase is P46 synthetic v12 artifact refresh.
P50 is optional and must not precede P46-P49 unless explicitly deferred. The
phase-doc package supplies plans and reviews only; it does not claim
`measurement_validated` evidence and does not provide bridge calibration
results by itself.

The active follow-up roadmap is:

- `docs/roadmaps/mingx-followup-dev-experiment-plan-v0-2.md`

That roadmap supersedes v10-era roadmap references for the next development
cycle. It does not authorize live APIs, fabricate bridge values, fabricate
human labels, fabricate kappa, or claim `measurement_validated`.

## Practical Reading Rule

For new work, read this file with `docs/archive/context_projection_fixed_v12.md`
before using older v10 planning documents. If an older file uses
`Vinfo_proxy_certified`, `greedy_valid`, or bare `escalate`, treat that wording
as legacy unless the file explicitly marks it as a denied claim or compatibility
field.
