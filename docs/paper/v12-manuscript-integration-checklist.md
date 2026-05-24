# V12 Manuscript Integration Checklist

Status: PAPER-RS live-API operational restructuring checklist
Claim ceiling: `operational_utility_only/no_claim_upgrade`

Use this checklist when revising the v12 manuscript from the P51-P60 evidence
state, accepted Route 2 operational package, fail-closed Route 3/4 bridge
attempts, Route 6B model-adjudicated measurement candidate, Delta/Gamma
operational packages, LogProbe/EPN/TFS blocked diagnostic chain, and EPF-FINAL
candidate package. This checklist creates no empirical evidence.

## Required Framing

- Preserve Proxy-Regime Diagnosis framing.
- Keep the formal object as predictive V-information over dispatch-time,
  per-agent, token-budgeted context projection.
- State that formal theorems apply only to formal `f_i^V` under the stated
  assumptions.
- Keep fixed-model logloss, operational utility, proxy metrics, heuristic
  selector behavior, and metric-claim levels separate.
- For the live-API-only paper section, use the exact title "Operational
  evaluation and weak-evidence diagnostics". Do not title this section
  validation.
- The exact section name is `Operational evaluation and weak-evidence
  diagnostics`.

## LAPI-8 Live-API-Only Paper Integration

The LAPI-8 paper-facing integration consists of:

- `docs/paper/live-api-operational-evaluation-section.md`
- `docs/paper/reviewer-defense-live-api-only.md`
- `docs/paper/related-work-live-api-operational-audit.md`

These documents integrate the completed live-API-only LAPI package into
paper-facing prose and reviewer defense only. They do not modify experiment
code, run live API calls, add empirical evidence, or change any route state.

The completed package is tracked as:

- LAPI-1: live API capability contract; generated output-token logprobs are
  answer-side confidence diagnostics only.
- LAPI-2: ProjectionBundleV1 artifact envelope and claim ledger; raw response
  storage remains false.
- LAPI-3: backend bridge audit witness; fixed-target teacher-forced NLL and
  fixed-target continuation scoring remain unsupported.
- LAPI-4: LLM judge weak-evidence harness; stable model-adjudicated labels are
  weak candidate evidence only.
- LAPI-5: sufficiency, abstention, and reprojection protocol; all outputs are
  candidate operational diagnostics.
- LAPI-6: operational replay expansion plan; it prepares matched-budget configs
  but does not run replay or live API calls.
- LAPI-7: extraction quality audit framework; model-adjudicated extraction-risk
  records remain diagnostics only, with human sentinel audit future optional.

Required LAPI-8 stance:

- live-API-only
- audit-first
- claim-gated
- formal V-information anchor only
- current experiments do not estimate a fixed-target bridge
- hard replay evidence is separated from weak model-adjudicated evidence
- live-API outputs remain operational diagnostics or candidate evidence only
- Route 5 locked: true
- Route 8 locked: true

## SUB-1 POST-LAPI Manuscript Integration

SUB-1 integrates the frozen POST-LAPI package into manuscript-facing docs as
weak candidate evidence only. The source of truth is the SUB-0 freeze package:

- `artifacts/audits/post_lapi_evidence_freeze/manifest.json`
- `artifacts/audits/post_lapi_evidence_freeze/table_inputs.json`
- `artifacts/audits/post_lapi_evidence_freeze/checksums.sha256`
- `docs/paper/post-lapi-evidence-freeze-ledger.md`
- `docs/paper/post-lapi-main-results-tables.md`
- `docs/paper/post-lapi-claim-boundary-summary.md`

SUB-1 manuscript integration creates no new experiment and runs no live API
call. It must leave the conclusion as
`operational_utility_only/no_claim_upgrade`.

Required POST-LAPI result summaries:

| result | manuscript placement | live API calls | required boundary |
|---|---|---:|---|
| POST-3 judge stability | `Operational evaluation and weak-evidence diagnostics` / judge stability diagnostics | 240 | model-adjudicated weak evidence only; no measurement validation or paper-grade evidence |
| POST-4 sufficiency / abstention | `Operational evaluation and weak-evidence diagnostics` / sufficiency and abstention diagnostics | 50 final artifact calls / 100 total turn calls | operational diagnostic candidate only; no human-calibrated abstention or paper-grade evidence |
| POST-5 reprojection witness | `Operational evaluation and weak-evidence diagnostics` / reprojection witness diagnostics | 26 | operational omitted-evidence evidence only; no selector superiority or metric bridge support |
| POST-6 operational replay expansion | `Operational evaluation and weak-evidence diagnostics` / matched-budget operational replay | 0 | scoped to named datasets, budgets, baselines, metrics, and materialization regime; no global selector superiority |
| POST-7 extraction quality audit | `Operational evaluation and weak-evidence diagnostics` / extraction quality audit diagnostics | 100 | model-adjudicated extraction-risk evidence only; no human/external gold validation |
| Artifact hygiene / raw-response policy | `Operational evaluation and weak-evidence diagnostics` / reproducibility and artifact hygiene appendix | 0 during SUB-0/SUB-1 synthesis | no raw API responses stored; no new live API evidence |

For every POST-LAPI result, manuscript-facing rows must state allowed claim,
denied claim, evidence tier, live API call count, human label status, metric
bridge status, Route 5 and Route 8 status, and `raw_response_stored` status.
All human label statuses are absent, all metric bridge statuses are absent,
Route 5 and Route 8 remain locked, and `raw_response_stored` remains false.

Required POST-LAPI prose:

- generated-token chat logprobs are operational confidence diagnostics only;
- model-adjudicated labels are weak evidence only;
- operational replay is scoped to named datasets, budgets, baselines, metrics,
  and materialization regime;
- extraction audit is model-adjudicated extraction-risk evidence only;
- reprojection witness is operational omitted-evidence evidence only.

Denied POST-LAPI upgrades:

- fixed-target NLL support;
- teacher-forced scoring support;
- metric bridge support;
- `calibrated_proxy_supported`;
- `vinfo_proxy_supported`;
- measurement validation;
- human/external gold validation;
- paper-grade evidence;
- selector superiority;
- global selector superiority;
- Route 5 unlock;
- Route 8 unlock.

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
- Route 4A/4B/4C are fail-closed or blocked bridge-redesign diagnostics only;
  they do not produce an accepted bridge candidate or unlock Route 5.
- Route 6B is a model-adjudicated measurement candidate. It uses accepted
  model-adjudicated labels, not human labels, external gold labels, or kappa.
- Delta failed closed on judge reliability and bridge gates. Its model-only
  labels remain operational audit evidence only.
- Gamma completed operational expansion smokes under matched budgets and shadow
  claim mode. It does not establish selector superiority or metric support.
- LogProbe / EPN / TFS documents form a blocked diagnostic chain: generated-token
  chat logprobs are rejected for fixed-target evidence-path NLL, the
  teacher-forced backend is unavailable, EPN remains blocked, and Route 5/Route
  8 remain locked.
- EPF WS0-WS10 / EPF-FINAL is a live-API-only candidate package factory. It
  was accepted with notes as candidate operational evidence and organizes
  operational diagnostics plus 8 LLM-generated silver-label rows over 2 parent
  samples, but the current backend does not expose true fixed-target
  teacher-forced continuation scoring.
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
- Do not describe Route 4A/4B/4C as accepted bridge candidates, bridge repair
  success, final bridge support, calibrated proxy support, V-information proxy
  support, measurement validation, paper evidence, or Route 5 unlock.
- Do not describe Route 6B model-adjudicated labels as human labels, external
  gold labels, kappa evidence, measurement validation, paper evidence, or
  human/external gold validation.
- Do not describe Delta as judge-reliability validation, human measurement
  validation, metric bridge support, calibrated proxy support, V-information
  support, selector superiority, or global selector superiority.
- Do not describe Gamma as selector superiority, global selector superiority,
  metric bridge support, calibrated proxy support, V-information support,
  measurement validation, or paper evidence.
- Do not describe LogProbe / EPN / TFS readiness or blocked reports as
  fixed-target teacher-forced NLL support, fixed-target continuation scoring
  support, bridge calibration, metric bridge support, Route 5 unlock, or Route 8
  unlock.
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
  separately satisfied. The current accepted-with-notes EPF-FINAL state does not
  satisfy those stronger gates.

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

## Route 4 Fail-Closed Bridge Integration Rule

Allowed Route 4 wording:

```text
Route 4 bridge-redesign attempts are retained as fail-closed or blocked
diagnostics. Route 4A and Route 4B did not pass their gates, and Route 4C was
blocked by missing FEVER source/evidence provenance. These records do not
produce an accepted bridge candidate and do not unlock Route 5.
```

Route 4 may be listed as bridge-redesign due diligence and negative diagnostic
evidence only. It must not be used as metric bridge support, calibrated proxy
support, V-information support, measurement validation, paper evidence, or Route
5 unlock evidence.

## Route 6B / Delta / Gamma Integration Rule

Allowed wording:

```text
Route 6B is a model-adjudicated measurement candidate, not measurement
validation. Delta failed closed on judge reliability and bridge gates. Gamma
adds operational expansion smokes under matched budgets and shadow claim mode.
Together these packages remain operational or candidate evidence under
operational_utility_only/no_claim_upgrade.
```

Route 6B, Delta, and Gamma may support the paper's audit narrative: model-only
labels can scale candidate review, judge reliability can fail closed, and
operational workbenches can be run without claim upgrade. They must not be used
as human validation, kappa evidence, metric bridge support, selector
superiority, global selector superiority, paper evidence, or deployed
V-information verification.

## LogProbe / EPN / TFS Blocked Diagnostic Rule

Allowed wording:

```text
The LogProbe / EPN / TFS chain records a backend limitation: generated-token
chat logprobs are not fixed-target teacher-forced continuation scoring, the
teacher-forced backend is unavailable, and evidence-path NLL remains blocked.
```

This chain may be used to explain why live-API logprob outputs are operational
confidence diagnostics only. It must not be used as teacher-forced NLL support,
fixed-target continuation scoring support, bridge calibration, Route 5 unlock,
or Route 8 unlock.

## EPF Backend-Constrained Candidate Package Rule

Allowed EPF wording:

```text
Under the available live-API backend, EPF does not expose true fixed-target
teacher-forced continuation scoring. EPF outputs are backend-constrained,
reviewable candidate operational evidence packages. EPF-FINAL was accepted with
notes as candidate operational evidence and contains 8 LLM-generated silver-label
rows over 2 parent samples. Chat-logprob confidence, constrained
label-generation proxies, LLM-generated silver labels, weak-source judge audits,
multi-benchmark operational robustness summaries, and uncertainty-bounded
reports are operational diagnostics or candidate evidence only.
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
