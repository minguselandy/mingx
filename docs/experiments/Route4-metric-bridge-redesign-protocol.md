# Route 4 Metric-bridge Redesign Protocol

Status: protocol freeze only
Claim status: `no_claim_upgrade`

Route 4 defines a new bridge protocol. It is not a rescue of the failed Route 2
or Route 3 bridge attempts, and it does not use threshold tuning to reinterpret
negative results.

## Bridge Target

The Route 4 bridge target is sufficiency-grounded evidence utility. The utility
must be measured independently from model logloss, token logprobs, or
`delta_logloss`. It asks whether an evidence set is sufficient for the declared
task target, not whether the scoring model became more confident.

Primary utility:

```text
delta_utility =
  sufficiency_utility(L union A, target_y)
  - sufficiency_utility(L, target_y)
```

The sufficiency utility must come from predeclared gold evidence labels,
external adjudication, or approved human/hybrid labels. It must not be copied,
ranked, rounded, clipped, affine-transformed, or otherwise derived from
`delta_logloss`.

Bridge quantity:

```text
delta_logloss =
  NLL(target_y | question_or_claim + materialized_context(L))
  - NLL(target_y | question_or_claim + materialized_context(L union A))
```

Route 4 evaluates whether the independent utility is predictable from the fixed
logloss improvement under a predeclared bridge fit.

## Secondary Utilities

Secondary utilities may be reported only as supporting diagnostics:

- answer support coverage;
- source-document coverage;
- answerability delta from an approved independent evaluator;
- human or strong-model sufficiency labels when the route plan approves them;
- token-normalized support efficiency.

Secondary utilities cannot replace the primary utility after row generation.

## First Strata

### FEVER Claim-verification Stratum

Dataset: FEVER, only if a complete evidence source, candidate pools, and
contract-valid evaluator records are available.

Task family:

```text
fever_claim_verification_sufficiency_bridge
```

Target: canonical FEVER label. Evidence packets are sentence-level evidence
units. Primary utility is whether the current evidence is sufficient to justify
the canonical label under the predeclared rubric.

### HotpotQA Answer-support Stratum

Dataset: HotpotQA dev distractor or a separately approved split.

Task family:

```text
hotpotqa_answer_support_sufficiency_bridge
```

Target: canonical gold answer plus support requirement. Evidence packets are
sentence-level packets from candidate pools. Primary utility is whether the
context suffices to support the answer under the predeclared support rubric.

## Row-key Contract

Each row identity must include:

- `route_id`
- `phase_id`
- `active_stratum`
- `task_family`
- `dataset`
- `split`
- `instance_id`
- `original_instance_id`
- `candidate_pool_hash`
- `context_L_packet_ids`
- `block_A_packet_ids`
- `target_y`
- `utility_target_id`
- `model_tier`
- `evaluator_id`
- `materialization_policy`
- `candidate_slice_band`
- `block_size`
- `budget`
- `decoding_policy`
- `split_id`
- `replicate_count_policy`

Measurement fields must remain outside row identity:

- `delta_logloss`
- `delta_utility`
- `baseline_utility`
- `augmented_utility`
- `contamination_status`
- `materialized_context_hash`
- non-circularity flags

## Splits

Route 4 must use stable original-instance splits:

- train/dev/heldout by original dataset instance;
- no original-instance leakage across splits;
- heldout fraction fixed before row generation;
- all strata and controls must preserve split identity.

Rows from the same original instance cannot be split across train and heldout
partitions.

## Controls

Negative controls:

- shuffled utility labels within split;
- shuffled `delta_logloss` within split;
- wrong-instance context joins;
- random `A` blocks;
- length-only and packet-count-only baselines;
- distractor-only blocks where available.

Positive controls:

- a circular alignment control may be kept only as a machinery sanity check;
- positive controls must be stored separately and marked not metric bridge
  evidence.

## Calibration Gates

Initial Route 4 gates:

| Gate | Threshold |
|---|---:|
| validated rows per stratum | >= 500 |
| original instances per stratum | >= 150 |
| heldout fraction | 0.30 |
| effective sample size | >= 100 |
| heldout sign agreement | >= 0.70 |
| heldout Spearman rho | >= 0.40 |
| normalized residual | <= 0.50 |

Additional gates:

- non-circularity checks pass;
- contamination status is clean or explicitly bounded;
- negative controls do not pass the bridge gates;
- positive controls remain positive-control only;
- independent review accepts the interpretation.

## Allowed Claim Levels

Before review, the maximum claim level is:

```text
metric_bridge_support_candidate
```

Only after Route 4 gates and independent review may the package be considered
for:

```text
calibrated_proxy_supported_candidate
```

Neither candidate state is a final `calibrated_proxy_supported` claim.

## Stop Conditions

Stop Route 4 if:

- the primary utility depends on NLL, logprobs, model confidence, or
  `delta_logloss`;
- FEVER or HotpotQA real evidence sources are missing;
- row keys cannot bind packets to candidate-pool hashes;
- any control shows circularity or label leakage;
- evaluator provenance is incomplete;
- validation falls below predeclared row or instance thresholds;
- claim wording implies final bridge support before review.
