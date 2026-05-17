# Route 3A Pre-registration Plan

Status: pre-registered protocol plan
Route: Route 3A support-grounded metric-bridge repair
Claim status: `no_claim_upgrade`

Route 3A is a new bridge protocol informed by Route 2 negative results. It is
not a P63R-compatible repair and does not reinterpret Route 2 as bridge support.

## Frozen Design

| Field | Value |
|---|---|
| route_id | `route3_metric_bridge_repair` |
| phase_id | `route3a_support_grounded_bridge` |
| active_stratum | `evidence_packet_selection_microtask_v1` |
| task_family | `hotpotqa_support_grounded_utility_bridge` |
| dataset / split | `HotpotQA` / `dev_distractor` |
| candidate-pool source | `artifacts/benchmarks/hotpotqa_candidate_pools.jsonl` |
| candidate-pool version | `hotpotqa_candidate_pool_v1`, Route 2 HotpotQA pools from commit `717796a` |
| materialization_policy | `fixed_selector_order_with_source_boundaries` |
| candidate_slice_band | `route3a_support_grounded_budget_512` |
| budget | `512` primary |
| block_size | `1` |
| split_id | `route3a_original_instance_hash_70_30_v1` |

Budgets `1024` and `256` are reserved for future robustness and diagnostic
runs. Package A executes only budget `512` to keep artifacts bounded.

## Row Identity

Every Route 3A delta record identity includes:

```text
route_id
phase_id
active_stratum
task_family
dataset
instance_id
original_hotpotqa_id
candidate_pool_hash
context_L_packet_ids
block_A_packet_ids
target_y
model_tier
materialization_policy
candidate_slice_band
block_size
budget
decoding_policy
evaluator_id
utility_definition
delta_utility_source
split_id
heldout_flag
```

Non-identity fields include:

```text
delta_logloss
delta_utility
baseline_utility
augmented_utility
replicate_count
contamination_status
materialized_context_hash
non_circularity_flags
```

`instance_id` is deterministically materialized as:

```text
<original_hotpotqa_id>::route3a::<stable_hash(target_packet_id + block_A_packet_id + budget)>
```

## Delta Definitions

`delta_logloss` uses the approved logprob evaluator only:

```text
NLL_L = NLL(target_y | question + target_packet + materialized_context(L))
NLL_L_plus_A = NLL(target_y | question + target_packet + materialized_context(L union A))
delta_logloss = NLL_L - NLL_L_plus_A
```

Evaluator provenance:

```text
provider = dashscope
model_name = qwen3.6-flash
endpoint_type = openai_compatible_chat_completions_logprobs
logprobs = true
top_logprobs = 0
temperature = 0
top_p = 1
enable_thinking = false
evaluator_id = approved_live_api_logprob_endpoint::dashscope::qwen3.6-flash::route3a_support_label_nll_v1
```

If this evaluator is unavailable or cannot return token logprobs for the
expected label, Route 3A fails closed and no logloss is fabricated.

`delta_utility` is independent of logloss and uses only HotpotQA candidate-pool
gold support labels and source documents:

```text
supporting_fact_recall(C) = |C intersect gold_support_packet_ids| / |gold_support_packet_ids|
delta_utility = supporting_fact_recall(L union A) - supporting_fact_recall(L)
```

Secondary support metrics:

```text
full_support_hit_delta
support_coverage_delta
support_doc_recall_delta
gold_support_packets_added
support_token_efficiency
```

The primary `delta_utility` must not use `delta_logloss`, NLL, token logprobs,
model predictions, ranks of logloss, rounded logloss, clipped logloss, or any
affine transform of logloss.

## Sampling and Split

Sampling is deterministic:

1. Sort candidate pools by `instance_id`.
2. Keep pools with at least two gold-supporting packets, at least two non-gold
   packets, valid `candidate_pool_hash`, and packet provenance.
3. Use the first 150 eligible original HotpotQA instances.
4. Emit four planned records per instance:
   - SUPPORTING target with gold-supporting A;
   - SUPPORTING target with distractor A;
   - NON_SUPPORTING target with gold-supporting A;
   - NON_SUPPORTING target with distractor A.
5. Use `L = ()`, `block_size = 1`, and budget `512`.

Heldout split:

```text
split_unit = original_hotpotqa_id
split_method = stable_hash(original_hotpotqa_id)
train_fraction = 0.70
heldout_fraction = 0.30
leakage_rule = no original instance may appear in both train and heldout
```

Minimum gates:

```text
min_rows = 500
min_unique_original_instances = 150
min_ess = 100
min_sign_agreement = 0.70
min_spearman = 0.40
max_normalized_residual = 0.50
heldout_fraction = 0.30
```

## Negative Controls

Route 3A reports these controls on validated delta records:

- shuffled `delta_logloss` within split and budget;
- wrong-instance utility join;
- deterministic random score baseline;
- length-only baseline;
- packet-count-only baseline.

Controls are diagnostic only. They cannot support a claim upgrade.

## Non-circularity Checks

Reject or fail closed if:

- `delta_utility` equals `delta_logloss` across all rows;
- utility is rounded, clipped, ranked, or affine-transformed from logloss;
- utility source mentions NLL, logprobs, model probabilities, or predictions;
- row identity omits provenance fields;
- target packet appears in `L` or `A`;
- packet IDs cannot bind to `candidate_pool_hash`.

Required report fields:

```text
fraction_delta_utility_equals_delta_logloss
pearson_delta_utility_delta_logloss
spearman_delta_utility_delta_logloss
exact_equality_detected
rounded_equality_detected
affine_transform_detected
rank_identity_detected
utility_source_verified
```

## Artifact Paths

Route 3A writes only benchmark/report artifacts:

```text
artifacts/benchmarks/route3a_hotpotqa_support_grounded_delta_records.jsonl
artifacts/benchmarks/route3a_hotpotqa_support_grounded_generation_report.json
artifacts/experiments/route3a_support_grounded_bridge_calibration/bridge_fit_summary.json
artifacts/experiments/route3a_support_grounded_bridge_calibration/non_circularity_report.json
artifacts/experiments/route3a_support_grounded_bridge_calibration/negative_control_report.json
docs/experiments/Route3A-support-grounded-bridge.md
```

Route 3A must not write `artifacts/operator_inputs/`.

## Stop / Continue / Escalate

Stop before scoring if source pools are missing, sampling cannot produce at
least 500 planned rows and 150 original instances, provenance is ambiguous, the
approved evaluator is unavailable, or storage would violate policy.

Stop before calibration if fewer than 500 rows validate, fewer than 150 original
instances validate, heldout split leaks instances, non-circularity checks fail,
or row identities are invalid.

Escalate if any file would exceed 25 MB, raw API responses are requested, or
any result is proposed as a claim upgrade.

## Claim Ceiling

Allowed Route 3A outcomes:

```text
support_grounded_bridge_candidate
failed_closed_no_claim_upgrade
```

The active claim status remains:

```text
no_claim_upgrade
```

Denied active claims:

```text
calibrated_proxy_supported
vinfo_proxy_supported
measurement validation
paper evidence
metric bridge support
P55 bridge support
P56 metric support
global selector superiority
deployed V-information verification
```
