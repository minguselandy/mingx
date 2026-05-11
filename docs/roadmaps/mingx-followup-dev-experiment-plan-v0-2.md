# Mingx Follow-up Development and Experiment Planning Document

**Project:** `minguselandy/mingx` — companion measurement and runtime-audit scaffold for the Context Projection Selection paper
**Document version:** v0.2, updated after fixed paper v12
**Planning horizon:** 12 weeks plus release packaging
**Primary goal:** turn the paper and repository into a reproducible, claim-gated evidence-production harness with executed bridge calibration, synthetic structural evidence, model-adjudicated realistic-task evidence, extraction-risk audit, and replayable runtime artifacts.

---

## 1. Executive Summary

The controlling Codex development/reference package for this follow-up program
is now `docs/codex/v12-phase-docs/`. It preserves the P45-P50 plan/review
documents, closes P45 for the current `bio_attribute` stratum as implemented
but non-calibrated, records the P46 synthetic v12 artifact refresh, adds the
P47 offline fixture model-adjudicated realistic-task benchmark, and hardens P48
Phase B replay under v12 claim semantics. P49 adds a deterministic fixture
extraction audit pilot for the M-star to M boundary. P50 adds an optional
fixture ReprojectionWitness scaffold for auditability of re-projection
decisions. The
package is planning and review guidance only; it does not claim
`measurement_validated` evidence and does not supply bridge calibration results
by itself.

The next phase of `mingx` should remain a **paper-facing evidence-production harness**, not a general multi-agent framework. The fixed paper has already shifted from “proxy-regime certification” to **proxy-regime diagnosis**, added the three-object value distinction, introduced a four-gate diagnostic policy, executed a small oracle synthetic benchmark, and clarified the evidence boundary. The development plan must now prioritize the remaining highest-leverage gap:

> **Close the current stratum-level metric bridge attempt honestly, then refresh the synthetic v12 artifacts before broad offline replay.**

P45 has now instantiated the bridge lane and demonstrated the claim gate. For
the current `bio_attribute` stratum, operational or model-adjudicated utility
marginals did not track fixed-model log-loss marginals well enough to support
`calibrated_proxy_supported`. The stratum is therefore downgraded for downstream
use to `operational_utility_only`; the underpowered P45e calibration artifact
itself remains `ambiguous_metric`.

The revised development program should proceed through seven lanes:

1. **Lane 0 — v12 repo and paper alignment.** Make the repository vocabulary, reports, and paper-facing docs match fixed paper v12.
2. **Lane 1 — one-stratum metric bridge calibration.** Estimate `(c_s, zeta_s)` with confidence intervals and claim-level downgrade behavior.
3. **Lane 2 — paper-grade synthetic benchmark hardening.** Extend the oracle smoke test with seed sweeps, noisy proxy layers, cost reporting, and provenance-aware adversarial redundancy.
4. **Lane 3 — model-adjudicated realistic-task benchmark.** Use strong-model generation, labeling, verification, and adjudication under frozen prompts.
5. **Lane 4 — extraction bridge-risk audit.** Measure value-dependent `M* -> M` loss by stratum.
6. **Lane 5 — offline replay and observability.** Reconstruct dispatch traces, recompute diagnostics, and compare observed selections against diagnostic alternatives.
7. **Lane 6 — uncertainty-triggered re-projection.** Add a UT-ACA-inspired content-level re-projection loop and `ReprojectionWitness`.

The current status override is: Lane 1 has been implemented and closed for the
current `bio_attribute` stratum with downgrade behavior. Lane 2/P46 has been
refreshed under v12 labels. Lane 3/P47 now has an offline fixture benchmark
that exercises the model-adjudicated realistic-task schema and claim boundary.
Lane 5/P48 now separates replay usability from metric claim level and hardens
dispatch identity checks.
Lane 4/P49 now has a fixture extraction audit pilot for source-span
traceability, missing critical findings, unsupported findings, duplicate or
over-merged findings, contradictory sources, and deterministic candidate-pool
provenance.
Lane 6/P50 now has an optional fixture ReprojectionWitness scaffold for
recording trigger reasons, context diffs, budget status, dispatch identity, and
candidate-pool provenance without upgrading claims.
Revisit Lane 1 only with a new stratum or materially new utility/logloss
design.

The minimum next paper package is **Lane 1 closure + Lane 2 hardening + a small Lane 3 pilot + Lane 4 pilot**. Lane 5 and Lane 6 are important for artifact strength but should not block the next paper version unless the target venue requires runtime evidence.

---

## 2. Source-of-Truth Updates from Fixed Paper v12

### 2.1 Revised paper identity

The paper should be treated as:

> **Conditional theory + metric bridge + proxy-regime diagnosis + minimal structural evidence.**

It should not be treated as:

> deployed V-information certification, human measurement validation, full multi-agent scheduler theory, or theorem inheritance for a heuristic pipeline.

### 2.2 Current strongest evidence

The strongest paper-facing evidence is now the **oracle synthetic benchmark** with four regimes:

- redundancy-dominated;
- pairwise synergy;
- higher-order prerequisite;
- adversarial redundancy.

The benchmark supports diagnostic signature separation and satisfies the conservative safety target that higher-order prerequisite cases should not receive `greedy_supported`. It remains a **structural smoke test**, not deployment validation.

### 2.3 P45 closure and next gap

P45 is no longer an open-ended retry loop for the current `bio_attribute`
stratum. Section 3.4 defines the bridge relation:

```text
|Delta_U(A | L) - c_s Delta_loss(A | L)| <= zeta_s
```

The repository now has an executable lane and negative canary evidence for one
controlled stratum, but not a passing measured bridge. The next development
cycle should move to P46 synthetic v12 artifact refresh while preserving the
P45 closure and claim downgrade.

### 2.4 Claim posture to enforce in code

Reports must distinguish:

- `synthetic_structural_evidence`
- `vinfo_proxy_supported`
- `calibrated_proxy_supported`
- `model_adjudicated_proxy_evidence`
- `operational_utility_only`
- `replayable_artifact_evidence`
- `model_adjudicated_extraction_audit`
- `ambiguous_metric`
- `ambiguous`

Reports must deny, unless all evidence requirements are present:

- `measurement_validated`
- deployed V-information verification
- theorem inheritance for retrieval/reranking/MMR/packing
- human-validated labels
- scheduler correctness
- end-to-end deployment validation

---

## 3. Product Boundary

### 3.1 What `mingx` should become

`mingx` should produce reproducible evidence bundles that answer four questions for every run:

1. **What layer was evaluated?** Synthetic oracle, fixed-model log-loss, model-adjudicated utility, operational utility, extraction audit, replay, or runtime re-projection.
2. **What claim level is allowed?** The report must emit exactly one allowed claim level and a set of denied claims.
3. **What selector-regime label was produced?** `greedy_supported`, `pairwise_escalate`, `higher_order_risk`, or `ambiguous`.
4. **What evidence is missing?** Human labels, kappa, contamination closure, fresh bridge, effective sample size, materialization order, excluded candidates, or replay fields.

### 3.2 What not to build in the next cycle

Do not build:

- a full multi-agent scheduler;
- a recursive agent runtime;
- a general memory OS;
- a general context-engineering platform;
- a tool-use benchmark suite;
- a theorem verifier for deployed models;
- a claim-upgrade path that bypasses human labels, kappa, contamination closure, and fresh metric bridge evidence.

These are outside the current paper’s contribution and would increase review risk.

---

## 4. Canonical Artifacts and Report Contracts

### 4.1 Minimal artifact family

Every experiment should emit:

```text
events.jsonl
candidate_pools.jsonl
projection_plans.jsonl
budget_witnesses.jsonl
materialized_contexts.jsonl
metric_bridge_witnesses.jsonl
diagnostics.jsonl
summary.json
report.md
claim_gate_report.json
```

### 4.2 Bridge calibration artifacts

Lane 1 must additionally emit:

```text
bridge_calibration_pairs.jsonl
bridge_calibration_fit.json
bridge_calibration_table.csv
bridge_residuals.csv
bridge_claim_gate_report.json
metric_bridge_witnesses.jsonl
```

### 4.3 Model-adjudicated benchmark artifacts

Lane 3 must additionally emit:

```text
prompt_manifest.json
prompt_hashes.json
generated_tasks.jsonl
labeler_outputs.jsonl
verifier_reports.jsonl
adjudicated_labels.jsonl
label_stability_report.json
model_adjudication_claim_gate_report.json
```

### 4.4 Extraction audit artifacts

Lane 4 must additionally emit:

```text
ground_truth_findings.jsonl
extraction_outcomes.jsonl
extraction_strata_summary.csv
value_weighted_loss_summary.json
extraction_claim_gate_report.json
```

### 4.5 Replay and re-projection artifacts

Lane 5 and Lane 6 must additionally emit:

```text
counterfactual_replay_witnesses.jsonl
reprojection_witnesses.jsonl
missing_field_report.json
replay_status_report.json
runtime_uncertainty_report.json
```

### 4.6 Required report invariant

Every `report.md` and `summary.json` must include:

```json
{
  "evaluated_layer": "...",
  "metric_claim_level": "...",
  "selector_regime_label": "...",
  "allowed_claims": ["..."],
  "denied_claims": ["measurement_validated", "deployed_vinfo_verification"],
  "missing_evidence": ["..."],
  "headline_eligible": false
}
```

---

## 5. Lane 0 — v12 Repo and Paper Alignment

### 5.1 Purpose

Synchronize repository vocabulary, documentation, report labels, and evidence gates with fixed paper v12.

### 5.2 Development tasks

- [ ] Add or update `docs/paper-alignment-v12.md`.
- [ ] Update README to point to the v12 paper framing.
- [ ] Replace remaining `certified`, `Vinfo_proxy_certified`, `greedy_valid`, and generic `escalate` labels.
- [ ] Add compatibility warnings for old labels if backward compatibility is needed.
- [ ] Update claim-gate tests so deprecated labels cannot appear in new paper-facing reports.
- [ ] Add a compact `CLAIMS.md` with allowed and denied claim levels.
- [ ] Add a paper-facing implementation paragraph source file that can be copied into the manuscript.

### 5.3 Acceptance criteria

- No new report emits `Vinfo_proxy_certified`.
- No new report emits `measurement_validated` without human labels, kappa, contamination pass, and fresh bridge evidence.
- The default report vocabulary matches v12 labels:
  - `greedy_supported`
  - `pairwise_escalate`
  - `higher_order_risk`
  - `ambiguous`
- Full unit test suite passes.

---

## 6. Lane 1 — One-Stratum Metric Bridge Calibration

### 6.1 Purpose

Demonstrate that the bridge contract is executable in at least one controlled
stratum. This lane has been implemented and is closed for the current
`bio_attribute` stratum as non-calibrated. It should not be retried
indefinitely before P46.

### 6.2 Research question

For one fixed stratum, do model-adjudicated or operational utility marginals track fixed-model log-loss marginals well enough to support `calibrated_proxy_supported`?

Current answer for the attempted `bio_attribute` stratum: no. P45c verified
the measured-logprob path, but P45d/P45e did not establish the bridge.

### 6.3 Target stratum

Recommended first stratum:

```text
task_family = synthetic_biography_attribute_qa
model_tier = fixed local/open model with logprob access
materialization_policy = fixed canonical order
block_size = 1 or 2
candidate_slice_band = top_L
metric = model_adjudicated_sufficiency or conceptual accuracy
```

### 6.4 Measurements

For sampled context/block pairs `(L, A)`, measure:

```text
Delta_loss(A | L) = fixed-model log-loss improvement
Delta_U(A | L)    = utility or strong-model sufficiency improvement
```

Fit:

```text
Delta_U(A | L) ~= c_s Delta_loss(A | L)
```

Report:

- `c_hat_s`
- `zeta_hat_s`
- 95% confidence interval or bootstrap interval
- sign agreement
- Spearman correlation
- Pearson correlation
- residual quantiles
- claim-level decision

### 6.5 Paper-facing table

| Stratum | n blocks | c_hat_s | zeta_hat_s | Sign agreement | Spearman rho | Claim level |
|---|---:|---:|---:|---:|---:|---|
| bio_attribute / fixed model / fixed_order_v1 / block_size=1 | live canaries only | P45c positive control passed; P45d/P45e bridge failed | P45e underpowered and failed `zeta_s` | P45e sign agreement on exported rows was not enough to pass | P45e correlation was underpowered | no `calibrated_proxy_supported`; downstream `operational_utility_only`; P45e artifact `ambiguous_metric` |

### 6.6 Claim rule

If residuals are small and stable:

```text
metric_claim_level = calibrated_proxy_supported
```

If correlation is weak, sign agreement is poor, residuals are large, or samples are underpowered:

```text
metric_claim_level = operational_utility_only or ambiguous_metric
```

A downgrade is still a successful claim-gate demonstration.

### 6.7 Acceptance criteria

- Bridge calibration command is deterministic under fixed inputs.
- All sampled pairs have stable IDs and materialization hashes.
- Report emits a measured `(c_hat_s, zeta_hat_s)` or an explicit underpowered/downgrade reason.
- No fabricated bridge values are allowed.
- The paper can include one paragraph saying the bridge contract was instantiated for one stratum, or that the stratum was downgraded by the claim gate.
- The current `bio_attribute` stratum is not expanded to a 20-30 row pilot
  without a new scientific rationale, a new stratum, or a materially new
  fixed-logloss/utility design.

### 6.8 Suggested module layout

```text
cps/experiments/bridge_calibration.py
cps/analysis/metric_bridge.py
cps/analysis/bridge_report.py
tests/test_bridge_calibration.py
tests/test_bridge_claim_gate.py
configs/runs/bridge-calibration-one-stratum.json
```

### 6.9 Target command

```bash
uv run python -m cps.experiments.bridge_calibration \
  --config configs/runs/bridge-calibration-one-stratum.json \
  --output-dir artifacts/experiments/bridge_calibration_one_stratum
```

---

## 7. Lane 2 — Paper-Grade Synthetic Benchmark Hardening

### 7.1 Purpose

Upgrade the current oracle smoke test into a robust paper-grade experiment.

### 7.2 Development tasks

- [ ] Add seed sweeps across at least 10 seeds.
- [ ] Add noisy proxy layer in addition to oracle layer.
- [ ] Add provenance-aware adversarial redundancy variants.
- [ ] Add cost table: oracle evaluations, proxy evaluations, strong-model calls if any, runtime.
- [ ] Add diagnostic ablations:
  - without pairwise excess;
  - without SAG gap;
  - without higher-order sentinel;
  - without signal adequacy gate.
- [ ] Add pre-registered pass/fail JSON.
- [ ] Regenerate paper tables directly from artifacts.

### 7.3 Required output tables

1. Diagnostic confusion matrix by true regime.
2. Selector value comparison: Greedy/MMR, SAG, local search, OPT.
3. Diagnostic cost table.
4. Ablation table.
5. Noisy proxy degradation table.

### 7.4 Acceptance criteria

- Higher-order prerequisite cases receive zero or near-zero `greedy_supported` under all seeds.
- Pairwise synergy cases frequently trigger `pairwise_escalate`.
- SAG closes a meaningful fraction of the Greedy/OPT gap in pairwise cases.
- Adversarial redundancy is mostly `ambiguous` unless provenance metadata makes it separable.
- Ambiguity is reported separately and never counted as success.

---

## 8. Lane 3 — Model-Adjudicated Realistic-Task Benchmark

### 8.1 Purpose

Create natural-language context-projection instances at scale using strong-model labels, without claiming human measurement validation.

### 8.2 Four-role pipeline

| Role | Function | Output |
|---|---|---|
| Generator | creates task packet, gold sketch, candidate findings | benchmark instance |
| Structural labeler | labels singleton, pair, triple, subset relations | preliminary labels |
| Verifier | finds contradictions and unstable labels | verification report |
| Adjudicator | resolves disagreements under frozen prompts | final labels |

### 8.3 Required labels

Item-level:

```json
{
  "finding_id": "m_017",
  "singleton_value": 0.72,
  "relevance_band": "high",
  "is_prerequisite": true,
  "evidence_type": "statutory_constraint",
  "provenance_strength": "high",
  "redundancy_type": "corroborative",
  "extraction_complexity": "qualifier_heavy",
  "confidence": 0.86
}
```

Pair-level:

```json
{
  "pair": ["m_017", "m_026"],
  "relation": "complementary",
  "pairwise_excess_band": "high",
  "direction": "m_017 enables m_026",
  "confidence": 0.84
}
```

Subset-level:

```json
{
  "subset_id": "S_greedy_003",
  "task_sufficiency": 0.61,
  "missing_critical_findings": ["m_044"],
  "redundant_findings": ["m_009"],
  "sufficiency_state": "unknown_due_to_missing_context",
  "expected_escalation_benefit": "large"
}
```

### 8.4 Stability checks

- [ ] Order reversal agreement.
- [ ] Duplicate judging stability.
- [ ] Paraphrase robustness.
- [ ] Counterfactual deletion.
- [ ] Redundancy swap.
- [ ] Prerequisite ablation.
- [ ] Cross-judge comparison.
- [ ] Unstable-label downgrade rate.

### 8.5 Claim rule

Allowed:

```text
model_adjudicated_proxy_evidence
```

Denied:

```text
measurement_validated
```

### 8.6 Acceptance criteria

- Prompts are frozen before final evaluation.
- Prompt hashes and model versions are recorded.
- Unstable labels are downgraded to `ambiguous`.
- The benchmark reports selector performance and label stability, not only generated examples.

---

## 9. Lane 4 — Extraction Bridge-Risk Audit

### 9.1 Purpose

Measure whether the extraction gate loses high-value or structurally important information before the selector sees it.

### 9.2 Strata

Use more than simple/complex:

- simple factual;
- complex conditional;
- qualifier-heavy;
- temporal-scope;
- cross-chunk;
- long-tail entity;
- high-provenance-value;
- prerequisite;
- contradictory;
- adversarial.

### 9.3 Metrics

For each stratum `s`:

```text
c_s = P(captured correctly | s)
```

Overall effective completeness:

```text
c_effective = sum_s p_s c_s
```

Value-weighted loss:

```text
L_value = sum_j v_j 1[missing_or_distorted_j] / sum_j v_j
```

### 9.4 Acceptance criteria

- Audit reports completeness and distortion by stratum.
- High-value and prerequisite findings are separately analyzed.
- Model-adjudicated evidence is not upgraded to human validation.
- Human sentinel audit is optional but recommended for submission-hardening.

---

## 10. Lane 5 — Offline Replay and Observability

### 10.1 Purpose

Test whether realistic dispatch traces can be reconstructed well enough to recompute diagnostics and compare observed selections against alternatives.

### 10.2 Replay statuses

| Status | Meaning |
|---|---|
| `replay_usable` | all fields and diagnostics recoverable |
| `pilot_degraded` | structural replay works but materialization or task metadata incomplete |
| `replay_partial` | candidate pool and selected set recoverable but diagnostics incomplete |
| `replay_unusable` | cannot reconstruct candidate pool or selected set |

### 10.3 Required replay identity

Every replayable dispatch should include:

```text
run_id
dispatch_id
agent_id
round_id
candidate_pool_hash
projection_plan_hash
materialized_context_hash
metric_bridge_witness_hash
```

### 10.4 Acceptance criteria

- Missing `run_id`, `dispatch_id`, `agent_id`, or `round_id` makes the trace non-usable.
- Missing excluded candidates downgrades replay status.
- Missing materialization order prevents metric-bridge claims.
- Replay reports can recompute selector labels from stored artifacts.

---

## 11. Lane 6 — Uncertainty-Triggered Re-projection

### 11.1 Purpose

Adapt the UT-ACA insight at the content-projection layer: when worker output shows missing-context uncertainty or hallucination risk, restore dispatch state, expand context, change selector if needed, and regenerate.

### 11.2 Runtime uncertainty labels

```text
grounded
unknown_due_to_missing_context
hallucination_risk
wrong_despite_context
ambiguous
```

### 11.3 ReprojectionWitness schema

```json
{
  "run_id": "...",
  "dispatch_id": "...",
  "original_projection_plan_hash": "...",
  "trigger_type": "unknown_due_to_missing_context",
  "uncertainty_score": 0.81,
  "missing_evidence_hypothesis": ["m_017", "m_044"],
  "budget_delta": 512,
  "new_selector": "seeded_augmented_greedy",
  "context_diff_hash": "...",
  "before_output_hash": "...",
  "after_output_hash": "...",
  "quality_delta": 0.0,
  "cost_delta": 0.0
}
```

### 11.4 Experimental comparison

| System | Description |
|---|---|
| Fixed greedy | one-shot greedy/MMR |
| Diagnostic escalation | SAG/local search when pre-dispatch diagnostics say escalate |
| Uncertainty-triggered re-projection | retry only when output shows missing-context or hallucination risk |
| Always-large context | high-cost reference baseline |

### 11.5 Acceptance criteria

- Re-projection improves missing-context or hallucination-risk cases.
- Retry cost and latency are reported.
- `ReprojectionWitness` is treated as operational evidence unless metric bridge and evaluation labels support stronger claims.

---

## 12. Twelve-Week Execution Plan

| Week | Focus | Deliverables |
|---:|---|---|
| 1 | v12 repo alignment | `paper-alignment-v12.md`, claim vocabulary tests, updated README/CLAIMS |
| 2 | bridge calibration design | config, schemas, sampling plan, fixed stratum, log-loss evaluator |
| 3 | bridge calibration execution | P45 implemented and closed for current stratum; claim downgrade documented |
| 4 | synthetic benchmark hardening I | P46 synthetic v12 artifact refresh: seed sweeps, noisy proxy layer, cost table |
| 5 | synthetic benchmark hardening II | ablations, adversarial/provenance variants, paper tables |
| 6 | model-adjudicated prompt development | P47 fixture schema and four-role fields implemented without live API |
| 7 | frozen model-adjudicated run | P47 offline fixture labels, stability report, and realistic-task benchmark implemented |
| 8 | extraction audit pilot | strata, model-adjudicated audit, value-weighted loss |
| 9 | offline replay implementation | P48 replay schemas, replay statuses, missing-field and identity checks hardened |
| 10 | replay experiment | P48 deterministic v12 replay report, claim fields, and alternative selector comparison scaffold |
| 11 | re-projection prototype | uncertainty labels, `ReprojectionWitness`, small retry experiment |
| 12 | paper/release packaging | regenerated tables, artifact manifest, final claim report, reference audit |

---

## 13. Go / No-Go Gates

### 13.1 Bridge calibration gate

Go if:

- bridge values are measured or downgraded honestly;
- the report can justify `calibrated_proxy_supported`, `operational_utility_only`, or `ambiguous_metric`;
- materialization policy and model tier are fixed.

No-go if:

- bridge values are manually filled;
- utility and log-loss are compared under mismatched strata;
- the report upgrades claims without residual estimates.

### 13.2 Synthetic benchmark gate

Go if:

- higher-order cases are not falsely labeled `greedy_supported`;
- pairwise cases trigger escalation often enough;
- ambiguity is separately reported.

No-go if:

- higher-order false `greedy_supported` rate is high;
- ablations show labels depend on a fragile single statistic;
- noisy proxy settings silently preserve overconfident labels.

### 13.3 Model-adjudicated benchmark gate

Go if:

- prompts are frozen;
- order reversal and duplicate judging are stable enough;
- unstable labels are downgraded.

No-go if:

- labels flip frequently under order reversal;
- generator and adjudicator use the same prompt without verification;
- model-adjudicated evidence is described as ground truth.

### 13.4 Replay gate

Go if:

- dispatch identity is complete;
- selected and excluded candidates are available;
- materialization order is available;
- diagnostics can be recomputed.

No-go if:

- traces cannot bind `run_id`, `dispatch_id`, `agent_id`, and `round_id`;
- materialized context hashes are missing;
- replay silently ignores missing fields.

---

## 14. Paper Integration Plan

### 14.1 Changes to make after Lane 1

Add to Section 3.4:

- one-stratum bridge-calibration paragraph;
- bridge table with `(c_hat_s, zeta_hat_s)`;
- claim outcome: `calibrated_proxy_supported`, `operational_utility_only`, or `ambiguous_metric`.

### 14.2 Changes to make after Lane 2

Update Section 4.6:

- seed-sweep table;
- noisy proxy results;
- ablation table;
- diagnostic cost table;
- stronger adversarial-redundancy explanation.

### 14.3 Changes to make after Lane 3

Add a realistic-task benchmark section:

- model-adjudicated label stability;
- selector comparison;
- missing-critical-finding rate;
- subset sufficiency table;
- explicit denial of `measurement_validated`.

### 14.4 Changes to make after Lane 4

Update Section 5:

- extraction completeness by stratum;
- value-weighted extraction loss;
- examples of high-value lost findings;
- model-adjudicated versus human-sentinel boundary.

### 14.5 Changes to make after Lane 5 and Lane 6

Update runtime section or appendix:

- replay status table;
- `CounterfactualReplayWitness` examples;
- `ReprojectionWitness` examples;
- cost/latency/quality tradeoff table.

---

## 15. Reference and Citation Audit Plan

The paper should not depend on unverified 2025/2026 references. Add a citation-audit table with:

| Citation | Status | Action |
|---|---|---|
| IMAS² | verify exact arXiv / venue; treat as agent/sensor selection, not content projection | keep only if exact source verified |
| Wang et al. “When Does Context Help?” | verify exact result and wording | use only as mechanistic analogy |
| AdaGReS | verify approximate-submodularity and calibration claims | keep as adjacent RAG context-selection precedent |
| RCR-Router | verify title and role-aware routing claims | keep as systems neighbor |
| DACS | verify title and agent-block granularity | keep only as runtime/context-restoration adjacency |
| DCCD | verify structured-generation result | use only for extraction/structured-output adjacency |
| BudgetMem / LatentMem | verify title, arXiv ID, and claims | avoid overstating venue status |
| Yuan/Su/Yao diagnostics | verify existence and claims | remove if unverified |

Every unverified source should be removed, weakened to “contemporaneous preprint,” or replaced with a verified prior.

---

## 16. Risk Register

| Risk | Consequence | Mitigation |
|---|---|---|
| bridge calibration fails | no calibrated proxy claim | report `operational_utility_only`; claim gate works |
| model labels unstable | realistic-task benchmark weak | downgrade unstable examples to `ambiguous`; add human sentinel |
| synthetic noisy proxy fails | structural result not robust to measurement noise | report oracle-only structural evidence; improve calibration budget |
| extraction loses high-value findings | selector can look healthy while system fails | improve extraction gate; widen candidate generation |
| replay traces incomplete | diagnostics cannot be recomputed | fail closed to `replay_unusable` or `pilot_degraded` |
| re-projection too expensive | runtime loop not default-feasible | frame as high-risk fallback |
| references unverifiable | reviewer trust loss | audit before submission |
| scope creep into full runtime | project becomes unfocused | enforce paper-facing artifact boundary |

---

## 17. Minimum Submission-Grade Package

For the next serious paper submission, aim for:

1. **One-stratum metric bridge calibration** with measured or honestly downgraded `(c_hat_s, zeta_hat_s)`. For the current `bio_attribute` stratum, this is the P45 closure and downgrade record.
2. **Hardened synthetic benchmark** with seed sweeps, noisy proxy, ablations, and cost reporting. This is the next active phase.
3. **Small model-adjudicated realistic-task benchmark** with frozen prompts and stability checks.
4. **Small extraction-risk audit** with value-weighted loss by stratum.
5. **Companion implementation statement** linking paper claims to executable artifacts.
6. **Reference audit table** for the recent-work cluster.

This package moves the project from:

> conditional theory + synthetic smoke test

to:

> conditional theory + demonstrated bridge contract or claim-gate downgrade + structural benchmark + model-adjudicated proxy evidence + extraction-risk pilot.

---

## 18. Immediate Next Sprint Checklist

- [ ] Create branch for v12 alignment.
- [ ] Add `docs/paper-alignment-v12.md`.
- [x] Add bridge-calibration config and schema.
- [x] Implement `bridge_calibration.py` with deterministic test fixture.
- [x] Add claim-gate tests for bridge downgrade.
- [x] Run bounded P45 canaries and preserve negative bridge reports.
- [x] Add P45 closure/status document.
- [x] Start P46 synthetic v12 artifact refresh.
- [x] Update synthetic benchmark artifacts with v12 labels and cost accounting.
- [x] Add paper-ready paragraph summarizing the P45 downgrade and P46 synthetic refresh result.
- [x] Add offline fixture P47 realistic-task benchmark artifacts and claim-gate report.

---

## 19. Final Principle

The repo should fail closed. A run that detects stale bridge evidence, missing contamination closure, unstable model labels, or incomplete replay identity is not a failed project; it is a successful demonstration of the paper’s claim-gate philosophy.

The strongest version of `mingx` is not the one that reports the most positive labels. It is the one that makes every evidence boundary reproducible, auditable, and impossible to silently overclaim.
