# IW-P Evidence-gap And Portfolio Decision

Status: `completed_claim_safe_analysis`
Claim status: `operational_utility_only/no_claim_upgrade`

## Inputs

- Route 4B bridge fit: `artifacts/experiments/route4b_bridge_to_measurement/bridge_fit_summary.json`
- Route 6B model-adjudicated labels: `artifacts/experiments/route6b_measurement_scaleup/model_adjudicated_labels.jsonl`
- Route 6B readiness: `artifacts/experiments/route6b_measurement_scaleup/readiness_report.json`
- Route 7 readiness and comparison gate: `artifacts/experiments/route7_scoped_selector_superiority/`

No live API calls were made. No new labels were created.

## Route 4B Bridge Power

Route 4B is not merely underpowered. It is underpowered and signal-weak:

- Rows validated: `300`
- Minimum rows used by IW-P projection: `500`
- Row shortfall: `200`
- Normalized residual: `0.9943939943352396`
- Sign agreement: `0.38`
- Spearman rho: `0.2315837581304158`
- Status: `underpowered_and_signal_weak`

Direct bridge scale-up is not recommended from this state.

## Route 6B Label Quality

Route 6B has model-adjudicated label variance and low reported uncertainty:

- Accepted model-adjudicated labels: `300`
- Delta-label distribution: `improves=61`, `unchanged=239`
- Uncertainty distribution: `low=300`
- Label variance status: `variance_present`
- Stability status: `model_adjudicated_low_uncertainty_only`

These labels do not count as human labels. Human-label validation, kappa, and measurement validation remain denied.

## Route 7 Effect Audit

Route 7 is not blocked by observed HotpotQA operational effect size in this audit. It remains blocked by:

- baseline comparability
- claim boundary

Missing deployable baselines:

- `BM25_or_dense_retrieval_when_available`
- `ablated_cost_aware_policy`
- `prior_v12_diagnostic_policy_variant`

Route 7 claim upgrade remains disallowed because route dependencies are not satisfied and no independent review has accepted an evidence package.

## Portfolio Decision

Decision: `GO_BETA_HYBRID_LABEL_MODEL`

Rationale: Route 6B model-adjudicated labels have variance, but accepted evidence still requires independent review or human validation before any claim upgrade. Route 4B should not proceed as direct bridge scale-up because the current result is both underpowered and signal-weak.

## Claim Boundary

Allowed claim: `operational_utility_only/no_claim_upgrade`

Denied claims:

- `calibrated_proxy_supported`
- `vinfo_proxy_supported`
- measurement validation
- metric bridge support
- selector superiority
- paper evidence

Route 5 remains locked without `accepted_bridge_candidate` plus `independent_review`. Route 8 remains locked without nonempty accepted evidence packages plus `independent_review`.
