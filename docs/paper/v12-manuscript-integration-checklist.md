# V12 Manuscript Integration Checklist

Status: P60 packaging checklist plus Route 2 operational-only integration
Claim ceiling: manuscript integration guidance only

Use this checklist when revising the v12 manuscript from the P51-P60 evidence
state and the accepted Route 2 operational package. This checklist is not a
manuscript patch and creates no empirical evidence.

## Required Framing

- Preserve Proxy-Regime Diagnosis framing.
- Keep the formal object as predictive V-information over dispatch-time,
  per-agent, token-budgeted context projection.
- State that formal theorems apply only to formal `f_i^V` under the stated
  assumptions.
- Keep fixed-model logloss, operational utility, proxy metrics, heuristic
  selector behavior, and metric-claim levels separate.

## Required Evidence-State Boundaries

- P45 negative closure must not be hidden.
- P45 current `bio_attribute` stratum remains non-calibrated.
- P55 remains `failed_closed_no_rows / blocked_operator_required`.
- P56 remains `no_imported_traces`.
- P55/P56 blocked states must not be described as successful experiments.
- Route 2 HotpotQA P56/P66 is a separate accepted operational-only lane:
  2,000 HotpotQA traces were validated and P66 accepted the matched-budget
  operational comparison.
- Route 2 bridge attempts did not establish metric support: original P63R and
  FixB failed closed, and FixA is a circular positive-control diagnostic only.
- Route 2 claim level remains `operational_utility_only`; no claim upgrade is
  allowed.
- P57 remains extraction-risk scaffold only.
- P58 remains operational diagnostic scaffold only.
- P59 remains operational audit scaffold only.

## Denied Manuscript Moves

- Do not describe synthetic or fixture results as validation.
- Do not describe model-adjudicated labels as human labels.
- Do not describe missing human labels or missing human-human kappa as filled
  by model adjudication.
- Do not describe replay usability as metric support.
- Do not describe extraction audit as selector validity.
- Do not describe `ReprojectionWitness` rows as deployed runtime improvement.
- Do not use `Vinfo_proxy_certified`, `greedy_valid`, or
  `measurement_validated` as active current claims.
- Do not claim deployed V-information verification.
- Do not claim theorem-level deployed submodularity verification.
- Do not describe Route 2 as metric bridge support, P55 bridge support, P56
  metric support, paper evidence, measurement validation, global selector
  superiority, `calibrated_proxy_supported`, or `vinfo_proxy_supported`.
- Do not present `gold_support_oracle_upper_bound` as deployable; it must remain
  marked `non_deployable_upper_bound`.

## Future / Operator-Gated Work

- P55 bridge progression requires contract-compliant operator-imported rows and
  P55 claim-gate review.
- P56 replay progression requires imported realistic dispatch traces and replay
  claim-gate review.
- Human-sentinel extraction audit requires operator approval, actual human
  annotators, and valid agreement calculation if human-human kappa is claimed.
- Measurement-validation candidates require separate human-label, kappa,
  contamination, and metric-bridge review.
- Route 2 manuscript integration may proceed only as operational replay and
  negative-bridge reporting. Any metric-claim upgrade requires a separately
  reviewed bridge result that the current Route 2 package does not provide.

## Route 2 Safe Integration Rule

Allowed Route 2 wording:

```text
HotpotQA operational replay shows that the v12 diagnostic policy improves
supporting-fact recall against deployable baselines under matched budgets.
Because P63R bridge gates failed closed, this is operational_utility_only, not
calibrated metric support.
```

Route 2 may be placed in Section 4.8 and Appendix C as an operational replay
and negative-bridge case study. The appendix should list P63R original, FixA,
FixB, P56, P66, and P67R with their evidence type, claim level, and denied
claims.

## Safe Integration Rule

When in doubt, cite the artifact as a scaffold, protocol, audit interface,
negative result, or future-gated route. Do not upgrade it to paper evidence,
metric bridge support, selector validity, measurement validation,
`calibrated_proxy_supported`, or `vinfo_proxy_supported` unless a later
independent review explicitly authorizes that claim.
