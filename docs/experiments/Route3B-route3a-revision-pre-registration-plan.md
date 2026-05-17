# Route 3B / Route 3A-Revision Pre-registration Plan

Status: pre-registered revision plan
Route: Route 3B support-grounded bridge revision
Claim status: `no_claim_upgrade`

Route 3B is a prospective revision of the Route 3A support-grounded bridge
protocol. It does not modify, overwrite, or reinterpret the pushed Route 3A
fail-closed run. Route 3 remains a new bridge protocol informed by Route 2
negative results, not a P63R-compatible repair.

## Diagnosis Lock

The Route 3A attrition diagnosis is frozen before Route 3B execution:

```text
Route 3A attempted rows = 600
Route 3A validated rows = 461
Route 3A attrition = 139
Primary attrition cause = live logprob evaluator emitted the opposite label
Candidate-pool/schema/utility validation failures = 0 diagnosed
```

The safe revision is to keep utility semantics and evaluator provenance fixed
while expanding the prospective sampling frame from the first 150 eligible
instances to all 198 eligible instances.

## Frozen Design

| Field | Value |
|---|---|
| route_id | `route3_metric_bridge_repair` |
| phase_id | `route3b_support_grounded_bridge_revision` |
| revision_protocol_id | `route3b_all_eligible_support_grounded_v1` |
| active_stratum | `evidence_packet_selection_microtask_v1` |
| task_family | `hotpotqa_support_grounded_utility_bridge` |
| dataset / split | `HotpotQA` / `dev_distractor` |
| candidate-pool source | `artifacts/benchmarks/hotpotqa_candidate_pools.jsonl` |
| candidate-pool version | `hotpotqa_candidate_pool_v1`, Route 2 HotpotQA pools from commit `717796a` |
| materialization_policy | `fixed_selector_order_with_source_boundaries` |
| candidate_slice_band | `route3b_support_grounded_budget_512` |
| budget | `512` primary |
| block_size | `1` |
| split_id | `route3b_original_instance_hash_70_30_v1` |

Budgets `1024` and `256` remain out of scope for this execution package.

## Eligibility And Sampling

Eligibility is deterministic and unchanged from Route 3A except that every
eligible instance is used:

```text
eligible instance =
  >=2 gold-supporting packets
  >=2 non-gold packets
  candidate_pool_hash present
  packet_id/source_doc_id/provenance present
```

Sampling protocol:

1. Sort candidate pools by `instance_id`.
2. Keep every eligible HotpotQA instance.
3. Attempt four rows per eligible instance:
   - SUPPORTING target with gold-supporting A;
   - SUPPORTING target with distractor A;
   - NON_SUPPORTING target with gold-supporting A;
   - NON_SUPPORTING target with distractor A.
4. Use `L = ()`, `block_size = 1`, and budget `512`.

Predeclared attempt target:

```text
eligible_original_instances = 198
target_attempted_rows = 792
min_validated_rows = 500
min_unique_original_instances = 150
```

Rows rejected because the live logprob evaluator emits the opposite label remain
fail-closed attrition. They are not repaired, forced, inferred, or filled.

## Row Identity

Every Route 3B delta record identity includes:

```text
route_id
phase_id
revision_protocol_id
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
validation_failure_reason
non_circularity_flags
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
evaluator_id = approved_live_api_logprob_endpoint::dashscope::qwen3.6-flash::route3b_support_label_nll_v1
```

If this evaluator is unavailable or cannot return token logprobs for the
expected label, Route 3B fails closed and no logloss is fabricated.

`delta_utility` is independent of logloss and uses only HotpotQA candidate-pool
gold support labels and source documents:

```text
supporting_fact_recall(C) = |C intersect gold_support_packet_ids| / |gold_support_packet_ids|
delta_utility = supporting_fact_recall(L union A) - supporting_fact_recall(L)
```

The primary `delta_utility` must not use `delta_logloss`, NLL, token logprobs,
model predictions, ranks of logloss, rounded logloss, clipped logloss, or any
affine transform of logloss.

## Heldout Split And Calibration Gates

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
min_validated_rows = 500
min_unique_original_instances = 150
heldout_fraction = 0.30
min_ess = 100
min_sign_agreement = 0.70
min_spearman = 0.40
max_normalized_residual = 0.50
```

Calibration runs only after the pre-calibration gates pass. Passing gates can
produce only `support_grounded_bridge_candidate_pending_independent_validation`.

## Validation Failure Handling

Rows are rejected, not repaired, if:

- candidate-pool hash is missing or unknown;
- L/A packet IDs or target packet ID cannot bind to the pool;
- target packet appears in L or A;
- block A is empty;
- `delta_logloss` or `delta_utility` is non-numeric;
- evaluator emits the opposite label;
- token logprobs are unavailable;
- duplicate full row identity appears;
- contamination status is `failed`;
- utility source is not the frozen support-label/source-doc utility.

Duplicate rows are fail-closed validation errors.

## Negative Controls

Route 3B reports these controls on validated rows:

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
- row identity omits provenance fields.

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

Route 3B writes only benchmark/report artifacts:

```text
artifacts/benchmarks/route3b_attrition_diagnosis_report.json
artifacts/benchmarks/route3b_hotpotqa_support_grounded_delta_records.jsonl
artifacts/benchmarks/route3b_hotpotqa_support_grounded_generation_report.json
artifacts/experiments/route3b_support_grounded_bridge_calibration/bridge_fit_summary.json
artifacts/experiments/route3b_support_grounded_bridge_calibration/non_circularity_report.json
artifacts/experiments/route3b_support_grounded_bridge_calibration/negative_control_report.json
docs/experiments/Route3B-support-grounded-bridge-revision.md
```

Route 3B must not write `artifacts/operator_inputs/`.

## Storage Policy

Route 3B may commit small deterministic JSON/JSONL reports. It must not commit
raw API response dumps, raw external dataset mirrors, or operator-input files.
Any artifact larger than 25 MB requires review before staging.

## Stop / Continue / Escalate

Stop before execution if source pools are missing, the diagnosis report is
absent or unsafe, planned rows are fewer than 500, planned unique original
instances are fewer than 150, provenance is ambiguous, the evaluator is
unavailable, or storage would violate policy.

Stop before calibration if fewer than 500 rows validate, fewer than 150 original
instances validate, heldout split leaks instances, non-circularity checks fail,
or row identities are invalid.

Escalate if any result is proposed as a claim upgrade.

## Claim Ceiling

Allowed Route 3B outcomes:

```text
failed_closed_no_claim_upgrade
support_grounded_bridge_candidate_pending_independent_validation
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
