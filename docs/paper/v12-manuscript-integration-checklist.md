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
- Legacy P56 scaffold state remains `no_imported_traces`; Route 2 P56-Route2
  is a separate operational-only HotpotQA lane.
- P55/P56 blocked states must not be described as successful experiments.
- Route 2 HotpotQA P56/P66 is a separate accepted operational-only lane:
  2,000 HotpotQA traces were validated and P66 accepted the matched-budget
  operational comparison.
- Route 2 bridge attempts did not establish metric support: original P63R and
  FixB failed closed, and FixA is a circular positive-control diagnostic only.
- Route 2 claim level remains `operational_utility_only`; no claim upgrade is
  allowed.
- Route 3A failed closed below the predeclared minimum validated-row threshold;
  calibration did not run.
- Route 3B reached calibration scale and passed non-circularity checks, but
  failed preregistered calibration gates. Its metric claim level is
  `failed_closed_no_claim_upgrade`.
- Route 3 does not repair the Route 2 bridge and does not authorize any claim
  upgrade.
- EPF WS0-WS10 / EPF-FINAL is a live-API-only candidate package factory. It
  organizes operational diagnostics and LLM-generated silver-label candidate
  evidence for independent review, but the current backend does not expose true
  fixed-target teacher-forced continuation scoring.
- EPF WS5 remains blocked from measurement validation without human/external
  gold labels.
- EPF claim status remains `operational_utility_only/no_claim_upgrade`.
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
- Do not describe Route 3A or Route 3B as support_grounded_bridge_candidate
  achieved, bridge repaired, repair succeeded, metric bridge support, P55 bridge
  support, P56 metric support, paper evidence, measurement validation, global
  selector superiority, `calibrated_proxy_supported`, or `vinfo_proxy_supported`.
- Do not describe EPF chat-logprob confidence, constrained label-generation
  proxies, LLM-generated silver labels, LLM judge labels, multi-benchmark
  summaries, or uncertainty-bounded reports as teacher-forced NLL support,
  metric bridge support, measurement validation, human/external gold
  validation, paper evidence, calibrated proxy support, V-information proxy
  support, or global selector superiority.
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
- EPF limited-scope candidate claims require independent review and must remain
  backend-constrained unless a future live API exposes true fixed-target
  continuation scoring and the missing human/external gold-label gate is
  separately satisfied.

## Route 2 Safe Integration Rule

Allowed Route 2 wording:

```text
HotpotQA operational replay shows that the v12 diagnostic policy improves
supporting-fact recall against deployable baselines under matched budgets.
Because Route 2 and Route 3 bridge gates failed closed, this is
operational_utility_only, not calibrated metric support.
```

Route 2 may be placed in Section 4.8 and Appendix C as an operational replay
and negative-bridge case study. The appendix should list P63R original, FixA,
FixB, P56, P66, and P67R with their evidence type, claim level, and denied
claims.

## Route 3 Negative Diagnostic Integration Rule

Allowed Route 3 wording:

```text
Route 3A failed closed below the predeclared minimum validated-row threshold.
Route 3B reached calibration scale, but preregistered calibration gates failed
closed. These support-grounded bridge attempts are negative diagnostics only and
do not repair the Route 2 bridge.
```

Route 3A and Route 3B may be listed in Appendix C or the evidence ledger as
failed-closed bridge-repair diagnostics. They should not be used to upgrade the
Route 2 operational claim.

## EPF Backend-Constrained Candidate Package Rule

Allowed EPF wording:

```text
Under the available live-API backend, EPF does not expose true fixed-target
teacher-forced continuation scoring. EPF outputs are backend-constrained,
reviewable candidate operational evidence packages. Chat-logprob confidence,
constrained label-generation proxies, LLM-generated silver labels, weak-source
judge audits, multi-benchmark operational robustness summaries, and
uncertainty-bounded reports are operational diagnostics or candidate evidence
only.
```

EPF may be referenced as an appendix/repo-only candidate package factory and as
paper-positioning context for live-API backend limitations. It must not be used
as teacher-forced NLL support, metric bridge support, calibrated proxy support,
V-information proxy support, measurement validation, human/external gold
validation, paper evidence, or global selector superiority.

## Safe Integration Rule

When in doubt, cite the artifact as a scaffold, protocol, audit interface,
negative result, or future-gated route. Do not upgrade it to paper evidence,
metric bridge support, selector validity, measurement validation,
`calibrated_proxy_supported`, or `vinfo_proxy_supported` unless a later
independent review explicitly authorizes that claim.
