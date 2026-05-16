# mingx Route 2 Real-Data Development / Experiment Plan

**Document status:** proposed development-control plan
**Intended repo location:** `docs/roadmaps/mingx-route2-real-data-dev-experiment-plan.md`
**Route:** real-data bridge calibration + realistic dispatch replay + comparative selector evaluation
**Framing:** v12 `Proxy-Regime Diagnosis`
**Current state anchor:** P45-P60 scaffold/evidence-state package complete; P55/P56 remain input-blocked.

---

## 0. Non-negotiable claim boundary

This plan intentionally moves beyond scaffold work into real-data experiments, but it does **not** relax the v12 evidence boundaries.

Allowed active `metric_claim_level` values remain:

```text
vinfo_proxy_supported
calibrated_proxy_supported
operational_utility_only
ambiguous_metric
```

Allowed active `selector_regime_label` values remain:

```text
greedy_supported
pairwise_escalate
higher_order_risk
ambiguous
```

The following claims remain forbidden unless a separately documented evidence package supports them:

```text
measurement_validated
human-label validation
human-human kappa
deployed V-information verification
theorem-level deployed submodularity verification
global calibrated proxy support
global V-information proxy support
fixture/synthetic/no-row/no-trace/scaffold paper evidence
deployed runtime improvement from ReprojectionWitness
```

Real-data success can support **stratum-local** claims only. For example, if P55 succeeds on `evidence_packet_selection_microtask_v1 / fever_claim_verification / fixed_model_tier / fixed_materialization_policy`, then `calibrated_proxy_supported` is allowed only for that active stratum and calibration epoch. It is not global deployed V-information verification.

---

## 1. Current project state that this route must repair

The current repo state is healthy as an audit scaffold, but real empirical lanes remain blocked.

```text
Remote HEAD: cc3ea30
Latest commit: P57-P60 add v12 final audit scaffolds and evidence ledger
P45-P60: complete and pushed
P55: failed_closed_no_rows / blocked_operator_required
P56: no_imported_traces
```

P55 currently lacks:

```text
artifacts/operator_inputs/p55_evidence_packet_selection_microtask_v1_rows.jsonl
rows_imported = 0
rows_validated = 0
bridge_fit_summary.json = absent
calibrated_proxy_supported = denied
vinfo_proxy_supported = denied
```

P56 currently lacks:

```text
artifacts/operator_inputs/p56_realistic_dispatch_traces.jsonl
traces_imported = 0
traces_validated = 0
paper_evidence = false
metric_support = false
```

P57-P60 are useful scaffolds and ledgers, but they do not repair P55/P56 blocked states. Route 2 exists to produce real operator rows and real replay traces.

---

## 2. Route 2 target outcome

The target outcome is a real-data evidence package with three components.

### 2.1 Metric bridge package

At least one controlled public-benchmark stratum produces valid P55 bridge rows, and the bridge calibration run reports:

```text
n_rows_imported
n_rows_validated
held-out residual zeta_hat_s
scale c_hat_s
sign agreement
Spearman rho
effective sample size
calibration epoch
active stratum
allowed metric_claim_level
```

Success criterion:

```text
calibrated_proxy_supported is allowed only if residual and stability gates pass.
```

Failure criterion:

```text
If residual/stability gates fail, report operational_utility_only or ambiguous_metric.
Do not rescue a failed bridge by terminology.
```

### 2.2 Realistic dispatch replay package

At least one public multi-hop/evidence-selection dataset produces valid P56 dispatch traces with complete:

```text
run_id
dispatch_id
agent_id
round_id
q_i
R_i
B_i
considered candidate pool
selected and excluded candidate IDs
candidate-pool hash
ProjectionPlan
BudgetWitness
MaterializedContext
MetricBridgeWitness
selector diagnostics
evaluator result
```

Success criterion:

```text
valid replayable artifact evidence + operational or calibrated metric interpretation depending on MetricBridgeWitness status.
```

Failure criterion:

```text
Replay completeness alone cannot imply metric support or selector validity.
```

### 2.3 Comparative selector evidence package

The v12 diagnostic policy is compared against strong baselines on the same candidate pools, budgets, materialization policies, evaluator models, and random seeds.

Superiority may be claimed only as:

```text
operational superiority on measured task/evidence/token/safety metrics
```

or, if P55 bridge passes and the active stratum matches:

```text
calibrated-proxy-supported superiority for that active stratum
```

No global V-information or measurement-validation claim is allowed.

---

## 3. Benchmark plan

Route 2 uses public benchmark data as the real-data substrate. The benchmark adapters must support local mirrors and must not require live proprietary APIs.

### 3.1 Primary bridge dataset: FEVER

Use FEVER as the primary P55 bridge dataset because the task target is a discrete verification label and sentence-level evidence is available for supported/refuted claims.

Recommended active stratum:

```text
active_stratum = evidence_packet_selection_microtask_v1
task_family = fever_claim_verification
metric = verdict_logloss + verdict_accuracy + evidence_recall
block_size <= 2
candidate_slice_band = top_20 or top_40
materialization_policy = fixed_selector_order_with_source_boundaries
model_tier = fixed_local_or_operator_approved_evaluator
```

FEVER bridge row definition:

```text
q_i = claim
Y_i = {SUPPORTED, REFUTED, NOTENOUGHINFO}
M = gold evidence sentences + hard distractors + lexical/dense retrieved distractors
L = current context packet set
A = singleton or pair block
Delta_logloss(A | L) = NLL(Y | q, L) - NLL(Y | q, L union A)
Delta_utility(A | L) = U(q, L union A, Y) - U(q, L, Y)
```

### 3.2 Primary replay datasets: HotpotQA, MuSiQue, 2WikiMultiHopQA

Use these datasets as the primary P56 replay/comparison suite because they provide multi-hop or reasoning-path evidence and naturally stress prerequisite / higher-order risk.

Recommended use:

```text
HotpotQA: supporting-fact recall + answer EM/F1 + distractor robustness
MuSiQue: hop/path coverage + answer F1/EM + prerequisite-chain stress
2WikiMultiHopQA: reasoning-path evidence recall + answer F1/EM
```

### 3.3 Optional long-document stress dataset: QASPER

Use QASPER only after the primary FEVER/HotpotQA/MuSiQue/2Wiki package is stable. QASPER is useful for long-document scientific evidence projection, but abstractive answer log-loss is harder to bridge cleanly.

Recommended status:

```text
optional_generalization_stress
not primary bridge stratum
```

---

## 4. Candidate pool construction

Each benchmark instance must be converted into mingx's dispatch-time candidate pool representation.

### 4.1 Evidence packet schema

Each packet should include at minimum:

```json
{
  "packet_id": "stable string",
  "dataset": "FEVER | HotpotQA | MuSiQue | 2WikiMultiHopQA | QASPER",
  "instance_id": "stable string",
  "source_doc_id": "stable string or null",
  "span": {"start": 0, "end": 0, "unit": "sentence|paragraph"},
  "content": "evidence text",
  "token_cost": 0,
  "gold_support_label": "support|distractor|unknown",
  "hop_index": null,
  "path_id": null,
  "retrieval_features": {},
  "provenance": {},
  "hash": "stable hash"
}
```

### 4.2 Candidate pool composition

For each instance, construct candidate pool `M` using:

```text
positive packets:
  gold evidence / supporting facts / reasoning path paragraphs

hard negative packets:
  same entity distractors
  same document non-supporting sentences
  lexical high-overlap distractors
  dense-retrieval near misses
  contradictory or near-duplicate evidence where available

random negative packets:
  unrelated but plausible distractors for sanity floor
```

Each pool must expose:

```text
candidate_pool_hash
n_candidates
n_gold_packets
n_hard_negative_packets
n_random_negative_packets
total_tokens
gold_reachable_under_budget boolean for each budget
```

### 4.3 Candidate-pool validity checks

Fail closed if:

```text
candidate_pool_hash unstable
packet_id collision
token_cost missing
provenance missing for gold-support packet
gold support missing where dataset provides it
candidate pool contains leaked answer text in prohibited fields
budget makes gold evidence unreachable in all configured settings
```

---

## 5. Development phases

### P61R 鈥?Public benchmark adapters

**Goal:** load public datasets or local mirrors and emit normalized benchmark instances.

Suggested files:

```text
cps/benchmarks/__init__.py
cps/benchmarks/schemas.py
cps/benchmarks/fever_adapter.py
cps/benchmarks/hotpot_adapter.py
cps/benchmarks/musique_adapter.py
cps/benchmarks/twowiki_adapter.py
cps/benchmarks/qasper_adapter.py          # optional
cps/benchmarks/build_candidate_pools.py
```

Required artifacts:

```text
artifacts/benchmarks/fever_candidate_pools_sample.jsonl
artifacts/benchmarks/hotpot_candidate_pools_sample.jsonl
artifacts/benchmarks/musique_candidate_pools_sample.jsonl
artifacts/benchmarks/twowiki_candidate_pools_sample.jsonl
docs/experiments/P61R-public-benchmark-adapters.md
```

Acceptance criteria:

```text
>= 100 dry-run instances per primary dataset if local data are available
schema validation passes
candidate_pool_hash stable across reruns
gold evidence reachable flag computed
no live proprietary API call required
missing data produces blocked-data report, not fake rows
```

---

### P62R 鈥?P55 bridge row generator

**Goal:** generate contract-compliant real P55 rows for `evidence_packet_selection_microtask_v1`.

Suggested files:

```text
cps/experiments/p55_bridge_rows_from_benchmarks.py
cps/experiments/bridge_row_schema.py
cps/experiments/bridge_row_validation.py
```

Required input/output:

```text
input: artifacts/benchmarks/fever_candidate_pools.jsonl
output: artifacts/operator_inputs/p55_evidence_packet_selection_microtask_v1_rows.jsonl
```

Row schema:

```json
{
  "active_stratum": "evidence_packet_selection_microtask_v1",
  "task_family": "fever_claim_verification",
  "dataset": "FEVER",
  "instance_id": "...",
  "model_tier": "...",
  "materialization_policy": "...",
  "candidate_slice_band": "top_20",
  "block_size": 1,
  "context_L_packet_ids": ["..."],
  "block_A_packet_ids": ["..."],
  "target_y": "SUPPORTED|REFUTED|NOTENOUGHINFO",
  "delta_logloss": 0.0,
  "delta_utility": 0.0,
  "replicate_count": 1,
  "decoding_policy": "deterministic_or_documented",
  "evaluator_id": "...",
  "candidate_pool_hash": "...",
  "materialized_context_hash": "...",
  "contamination_status": "clean|ambiguous|failed"
}
```

Acceptance criteria:

```text
>= 500 validated rows for FEVER primary stratum
>= 150 unique instances when feasible
block_size in {1,2}
delta_logloss present for every validated row
delta_utility present for every validated row
candidate_pool_hash present and stable
materialized_context_hash present and stable
contamination_status not failed
```

If evaluator outputs are unavailable:

```text
emit blocked_operator_required report
rows_imported = 0
no bridge claim
```

---

### P63R 鈥?P55 real bridge calibration run

**Goal:** run the existing P55 importer/report scaffold on real rows and produce a bridge witness.

Suggested files:

```text
cps/experiments/run_p55_bridge_calibration.py
cps/experiments/bridge_fit.py
```

Required artifacts:

```text
artifacts/experiments/p55_real_bridge_calibration/import_report.json
artifacts/experiments/p55_real_bridge_calibration/bridge_fit_summary.json
artifacts/experiments/p55_real_bridge_calibration/metric_bridge_witness.json
docs/experiments/P63R-p55-real-bridge-calibration-report.md
docs/reviews/P63R-p55-real-bridge-calibration-review.md
```

Predeclared initial gates:

```text
min_rows_validated = 500
min_unique_instances = 150
heldout_fraction = 0.30
min_sign_agreement = 0.70
min_spearman_rho = 0.40
min_effective_sample_size = 100
max_normalized_residual = predeclared in config before run
```

Allowed outcomes:

```text
calibrated_proxy_supported_candidate:
  residual/stability gates pass; active stratum exactly matches witness

operational_utility_only:
  utility measurements are usable but bridge residual/stability fails

ambiguous_metric:
  underpowered, stale, stratum-mismatched, contaminated, or unstable

failed_closed_no_rows:
  no valid rows imported
```

Forbidden outcomes:

```text
measurement_validated
vinfo_proxy_supported from utility rows alone
global calibrated proxy support
human-label validation
```

---

### P64R 鈥?Baseline selector suite

**Goal:** implement strong baseline selectors under the same candidate pools, budgets, evaluator, materialization, and random seeds.

Baseline families:

```text
random_budget
bm25_topk_budget
dense_topk_budget
rrf_fusion_topk_budget
cross_encoder_topk_budget
full_context_truncate
mmr_density_greedy
static_lambda_mmr
adagres_style_adaptive_redundancy_greedy
ci_value_positive
always_sag_k2
pair_local_search
rcr_router_adapted
gold_evidence_oracle_upper_bound
v12_cost_aware_diagnostic_policy
```

Suggested files:

```text
cps/selectors/baselines/random_budget.py
cps/selectors/baselines/bm25_topk.py
cps/selectors/baselines/dense_topk.py
cps/selectors/baselines/rrf_topk.py
cps/selectors/baselines/cross_encoder_topk.py
cps/selectors/baselines/full_context_truncate.py
cps/selectors/baselines/mmr_density.py
cps/selectors/baselines/adagres_style.py
cps/selectors/baselines/ci_value_positive.py
cps/selectors/baselines/always_sag.py
cps/selectors/baselines/pair_local_search.py
cps/selectors/baselines/rcr_router_adapted.py
cps/selectors/baselines/gold_oracle.py
cps/selectors/v12_diagnostic_policy.py
```

Acceptance criteria:

```text
all selectors consume the same CandidatePool schema
all selectors obey token budget B_i
all selectors emit ProjectionPlan-compatible records
all selectors produce selected and excluded candidate IDs
oracle baseline clearly marked non-deployable upper bound
v12 policy emits both metric_claim_level and selector_regime_label
```

---

### P65R 鈥?Realistic dispatch trace generation

**Goal:** generate P56 traces by running selectors on real benchmark candidate pools.

Required output:

```text
artifacts/operator_inputs/p56_realistic_dispatch_traces.jsonl
```

Trace schema:

```json
{
  "run_id": "...",
  "dispatch_id": "...",
  "agent_id": "answer_worker",
  "round_id": 1,
  "task_q_i": "...",
  "role_R_i": "evidence_grounded_answerer",
  "budget_B_i": 1024,
  "dataset": "HotpotQA|MuSiQue|2WikiMultiHopQA|FEVER",
  "candidate_pool_hash": "...",
  "considered_candidate_packet_ids": ["..."],
  "selected_packet_ids": ["..."],
  "excluded_packet_ids": ["..."],
  "projection_plan": {},
  "budget_witness": {},
  "materialized_context": {},
  "metric_bridge_witness": {},
  "selector_regime_label": "greedy_supported|pairwise_escalate|higher_order_risk|ambiguous",
  "metric_claim_level": "vinfo_proxy_supported|calibrated_proxy_supported|operational_utility_only|ambiguous_metric",
  "answer_output": "...",
  "gold_target": "...",
  "evaluation": {}
}
```

Acceptance criteria:

```text
>= 300 traces per primary replay dataset if data/evaluator available
complete dispatch identity
complete considered/excluded candidates
stable candidate_pool_hash
ProjectionPlan present
BudgetWitness present
MaterializedContext present
MetricBridgeWitness present
no trace treated as metric support without valid witness
```

---

### P66R 鈥?Comparative realistic replay experiment

**Goal:** run the P56 importer/report scaffold on real traces and produce selector comparison results.

Primary test matrix:

```text
Datasets: HotpotQA, MuSiQue, 2WikiMultiHopQA, FEVER
Budgets: 512, 1024, 2048 tokens for multi-hop QA; 256, 512, 1024 for FEVER
Selectors: baseline suite + v12_cost_aware_diagnostic_policy + oracle upper bound
```

Required artifacts:

```text
artifacts/experiments/p56_realistic_replay/import_report.json
artifacts/experiments/p56_realistic_replay/comparison_summary.csv
artifacts/experiments/p56_realistic_replay/statistical_tests.json
artifacts/experiments/p56_realistic_replay/diagnostic_safety_summary.json
docs/experiments/P66R-realistic-replay-comparison.md
docs/reviews/P66R-realistic-replay-comparison-review.md
```

Task metrics:

```text
FEVER:
  verdict accuracy
  macro-F1
  evidence recall@budget
  label+evidence correctness

HotpotQA:
  answer EM/F1
  supporting-fact F1
  evidence recall@budget

MuSiQue:
  answer EM/F1
  hop evidence recall
  prerequisite chain coverage

2WikiMultiHopQA:
  answer EM/F1
  reasoning-path recall
  path completeness
```

Efficiency metrics:

```text
mean selected tokens
quality per 1k selected tokens
evidence recall per 1k selected tokens
token reduction at matched quality
quality improvement at matched budget
```

Diagnostic safety metrics:

```text
false_greedy_supported_rate
pairwise_escalation_precision
pairwise_escalation_recall
higher_order_risk_detection_rate
ambiguous_rate
SAG_gap_reduction
policy regret vs oracle_opt_small_pool where available
```

Superiority rule:

```text
A superiority claim is allowed only when paired bootstrap/permutation tests show a statistically meaningful gain over the named baseline under matched dataset, budget, candidate pool, evaluator, materialization policy, and metric-claim regime.
```

---

### P67R 鈥?Ablation and failure analysis

**Goal:** identify which gates and features matter, and prevent overclaiming if results are mixed.

Ablations:

```text
v12_full_policy
without_metric_bridge_gate
without_pairwise_excess_gate
without_SAG_gap_gate
without_higher_order_sentinel
without_provenance_redundancy_features
always_greedy
always_SAG
```

Failure taxonomy:

```text
retrieval_miss
extraction_miss
candidate_pool_gold_unreachable
selector_miss
materialization_order_miss
answerer_utilization_miss
bridge_mismatch
higher_order_prerequisite_miss
provenance_conflict_miss
metric_underpowered
```

Required output:

```text
artifacts/experiments/p66_p67_error_analysis/error_taxonomy_summary.json
docs/experiments/P67R-ablation-and-error-analysis.md
```

---

### P68R 鈥?Manuscript integration package

**Goal:** update the paper from scaffold/future-work status into real-data experiment status, while preserving claim boundaries.

New or revised manuscript sections:

```text
4.7 Real-data bridge calibration
4.8 Realistic dispatch replay
4.9 Baseline comparison and ablation
4.10 Evidence-state and claim ledger
Limitations: failed/blocked/underpowered outcomes if any
```

Required tables:

```text
Bridge calibration table
Main replay comparison table
Diagnostic safety table
Ablation table
Evidence/claim ledger table
```

Mandatory caveats:

```text
Bridge support, if achieved, is stratum-local.
Replay evidence is not metric support by itself.
Operational utility gains are not V-information proxy evidence without a valid bridge.
Oracle upper bound is not deployable.
Synthetic/fixture/scaffold results remain non-validating.
```

---

### P69R 鈥?Independent review and claim audit

**Goal:** run a package-level independent review before commit/paper update.

Review questions:

```text
Does P55 actually import valid rows?
Does P63 compute bridge fit metrics on held-out rows?
Does any text claim calibrated support when gates fail?
Does P56 actually import realistic traces?
Are selectors compared on identical candidate pools, budgets, materialization, evaluator, and seeds?
Are statistical tests paired and baseline-specific?
Are superiority claims metric-specific and dataset-specific?
Are vinfo_proxy_supported and calibrated_proxy_supported denied unless their gates pass?
```

Hard rejection conditions:

```text
no rows but positive bridge claim
no traces but replay evidence claim
fixture/synthetic evidence used as paper-grade validation
operator inputs committed without explicit approval
RCR/AdaGReS/CI baselines compared under mismatched budgets/evaluators
human validation/kappa language without human labels and agreement
```

---

### P70R 鈥?Release / submission package

**Goal:** produce a clean route-2 commit package and paper-facing artifact package.

Expected package:

```text
docs/experiments/P63R-p55-real-bridge-calibration-report.md
docs/experiments/P66R-realistic-replay-comparison.md
docs/experiments/P67R-ablation-and-error-analysis.md
docs/reviews/P69R-route2-independent-review.md
docs/paper-alignment-v13-or-v12-route2.md
artifacts/experiments/p55_real_bridge_calibration/...
artifacts/experiments/p56_realistic_replay/...
```

Commit hygiene:

```text
No .codex/automation-state commit.
No accidental operator_inputs commit unless explicitly approved.
No duplicate planning docs.
No stale P55/P56 blocked wording after real rerun unless still true.
All generated evidence reports include claim boundary table.
```

---

## 6. Baseline implementation details

### 6.1 Common selector interface

All selectors must implement a shared interface:

```python
class Selector:
    name: str
    def select(self, task, role, candidate_pool, budget, config) -> ProjectionPlan:
        ...
```

The returned `ProjectionPlan` must include:

```text
selector_name
selector_config
selected_packet_ids
excluded_packet_ids
considered_packet_ids
scores_by_packet_id
budget_requested
budget_realized
candidate_pool_hash
```

### 6.2 Fairness rules

All baseline comparisons must obey:

```text
same candidate pool
same budget
same materialization policy
same answerer/evaluator model tier
same decoding policy
same random seed set
same trace validation rules
same metric-claim gate
```

### 6.3 RCR-Router adapted baseline

Do not compare against RCR-Router's paper-reported numbers unless the experimental setup is exactly reproduced. Instead, implement an adapted baseline on the same candidate pools:

```text
role-aware scoring = relevance(task, packet) + role_match(role, packet) + stage_prior
semantic filter = remove low-relevance or role-mismatched packets
budget allocator = fixed per-worker B_i in this paper's setting
selection = top scored packets until budget
```

Report it as `rcr_router_adapted`, not as a full reproduction.

### 6.4 CI Value adapted baseline

CI-style leave-one-out value is expensive. Use it on a restricted top-slice:

```text
retrieve top L candidates
compute utility/log-loss degradation when removing each candidate from full top-slice context
retain candidates with positive CI value
pack by value density under budget
```

Report evaluator cost and top-slice size.

---

## 7. Statistical plan

For each dataset / budget / selector comparison:

```text
paired bootstrap 95% CI for answer/evidence metrics
paired permutation test or Wilcoxon signed-rank for per-instance utility delta
Holm correction for multiple baseline comparisons
effect size: mean delta and standardized paired delta
```

Report at least three types of evidence:

```text
quality win:
  v12 policy improves answer/evidence metric at matched budget

token win:
  v12 policy matches baseline quality with fewer tokens

safety win:
  v12 policy lowers false_greedy_supported_rate or improves escalation precision/recall
```

If only one type is achieved, the manuscript claim must specify which type. Do not convert a safety-only win into answer-quality superiority.

---

## 8. Outcome-to-paper-claim mapping

| Outcome | Allowed paper claim | Denied paper claim |
|---|---|---|
| P55 rows absent | blocked/fail-closed scaffold only | bridge evidence |
| P55 rows valid but residual fails | operational or ambiguous metric evidence | `calibrated_proxy_supported` |
| P55 residual/stability gates pass | stratum-local `calibrated_proxy_supported` | global metric validation |
| P56 traces absent | no-trace blocked scaffold only | replay evidence |
| P56 traces valid but bridge absent | replayable/operational evidence | V-information proxy evidence |
| P56 v12 beats baselines operationally | operational superiority on named metrics | measurement validation |
| P56 v12 beats baselines with active bridge | calibrated-proxy-supported superiority for matching stratum | deployed V-information verification |
| Human sentinel absent | no human validation claim | human labels/kappa |

---

## 9. Recommended first execution sequence

Do not start with all datasets and all baselines. Execute in this order:

```text
1. P61R FEVER adapter dry-run
2. P62R FEVER bridge row generator with a small validated sample
3. P63R bridge calibration on FEVER primary stratum
4. P64R baseline selector interface + minimal baselines
5. P65R HotpotQA/MuSiQue/2Wiki trace generation dry-run
6. P66R comparison on one dataset and two budgets
7. Expand baselines/datasets only after validation gates pass
8. P67R ablation/error analysis
9. P68R manuscript integration
10. P69R independent review
```

The shortest path to stronger paper evidence is not more scaffolding; it is a valid FEVER bridge row package plus one real replay comparison that obeys the same trace and claim gates.

---

## 10. External benchmark / baseline anchors

Use current primary sources when implementing or writing the paper:

```text
FEVER official dataset: https://fever.ai/dataset/fever.html
HotpotQA official site: https://hotpotqa.github.io/
MuSiQue ACL Anthology: https://aclanthology.org/2022.tacl-1.31/
2WikiMultiHopQA ACL Anthology: https://aclanthology.org/2020.coling-main.580/
QASPER ACL Anthology: https://aclanthology.org/2021.naacl-main.365/
RCR-Router arXiv: https://arxiv.org/abs/2508.04903
CI Value OpenReview: https://openreview.net/forum?id=ugaepulZyA
AdaGReS arXiv: https://arxiv.org/abs/2512.25052
RRF ACM: https://dl.acm.org/doi/10.1145/1571941.1572114
MMR PDF: https://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf
```
