# Route 3 Preflight Protocol

Status: Package A preflight protocol
Route: Route 3 metric-bridge repair planning
Claim status: `operational_utility_only; no_claim_upgrade`

Route 3 is a new metric-bridge protocol informed by Route 2 negative results.
It is not a P63R-compatible repair, does not reinterpret Route 2 as bridge
support, and must not run Route 3A or Route 3C until this Package A receives
major-gate review approval.

## Route 2 Boundary

Route 2 remains operational-only:

- P63R original HotpotQA answer bridge failed closed.
- P63R-FixA is `positive_control_only` and `circular_alignment_control`; it is
  not independent metric bridge evidence.
- P63R-FixB is a valid non-circular negative bridge attempt and failed closed.
- P56/P66 are HotpotQA operational replay/comparison evidence only.

Allowed Route 2 wording:

```text
HotpotQA operational replay/comparison shows that the v12 diagnostic policy
improves supporting-fact recall against deployable baselines under matched
budgets.
```

Required qualifier:

```text
Because P63R bridge gates failed closed, this remains operational_utility_only,
not calibrated metric support.
```

## P68P Status

P68P is closed for Package A. The five paper/control docs have no residual
workspace diff on this branch. Package A does not edit manuscript claim wording.

## Recoverable Lineage

| Attempt | Rows validated | Unique instances | Gate result | Claim level |
|---|---:|---:|---|---|
| P63R original answer bridge | 600 | 150 | `failed_closed_gate_failed` | `operational_utility_only` |
| P63R-FixA circular control | 643 | 643 | `positive_control_only` | `positive_control_only` |
| P63R-FixB independent utility | 826 | 826 | `failed_closed_gate_failed` | `operational_utility_only` |

Recoverable artifacts include sanitized delta records, operator rows,
calibration summaries, metric bridge witnesses, and experiment reports. Raw live
API response dumps are intentionally absent, so exact raw API replay is not
recoverable from repository artifacts.

## Recovered Gate Definitions

Recovered fit equation:

```text
delta_utility ~= c_s * delta_logloss
```

Recovered estimator:

```text
train_split_ols_through_origin
```

Recovered thresholds:

| Gate | Value |
|---|---:|
| `min_rows_validated` | 500 |
| `min_unique_instances` | 150 |
| `heldout_fraction` | 0.30 |
| `min_effective_sample_size` | 100 |
| `min_sign_agreement` | 0.70 |
| `min_spearman_rho` | 0.40 |
| `max_normalized_residual` | 0.50 |

Recovered split definition:

```text
stable_bridge_row_key_tail_holdout
```

Route 3A and Route 3C must replace this with a stable original-HotpotQA-instance
split to prevent rows from the same original instance entering both train and
heldout partitions.

## Candidate-pool Support Achievability

Existing HotpotQA candidate pools support Route 3 planning:

| Quantity | Value |
|---|---:|
| candidate pools | 200 |
| unique instances | 200 |
| total packets | 8,303 |
| gold-supporting packets | 485 |
| gold support reachable under budget 256 | 200 / 200 |
| gold support reachable under budget 512 | 200 / 200 |
| gold support reachable under budget 1024 | 200 / 200 |
| candidate pool size, min / median / mean / max | 11 / 40 / 41.515 / 75 |
| gold token sum, min / median / mean / max | 17 / 53 / 56.745 / 151 |
| Route 3A eligible instances under proposed protocol | 198 |
| Route 3A possible rows under proposed protocol | 792 |
| Route 3A rows from first 150 eligible instances | 600 |

These are achievability and planning statistics only. They are not calibration
evidence.

## Route 3 Framing Decision

Route 3 must be a new bridge protocol, not a P63R-compatible repair.

Reasons:

- P63R original failed the sign-agreement, rank-correlation, and normalized
  residual gates.
- FixB was non-circular but also failed the same substantive bridge gates.
- FixA passed only because it was a circular positive control.
- Reusing the same P63R framing would invite post-hoc threshold or utility
  tuning rather than a pre-registered bridge protocol.

## Route 3A Support-grounded Utility Protocol

Route 3A should pre-register a support-grounded utility target independent from
model logloss.

Primary utility target:

```text
support_coverage_delta =
  support_coverage(L union A) - support_coverage(L)
```

Support coverage should combine HotpotQA gold-support packet recall and
support-source-document recall. It must be computed only from candidate-pool
gold labels, packet IDs, source document IDs, `L`, and `A`.

Secondary support metrics:

- support packet recall delta;
- support document recall delta;
- gold-support packets selected;
- selected support tokens per 1k budget tokens;
- distractor token share.

Budgets:

- `512` primary;
- `1024` robustness;
- `256` diagnostic stress only.

Pilot size:

```text
50 original HotpotQA instances / about 200 rows
```

Confirmatory size:

```text
>= 150 original HotpotQA instances
>= 500 validated rows
```

Heldout split:

```text
stable_hash(original_hotpotqa_instance_id), 70/30, no original-instance leakage
```

Negative controls:

- shuffled utility labels;
- distractor-only `A` blocks;
- random `A` blocks;
- circular positive-control check kept separate from metric evidence.

Non-circularity checks:

- utility must not be copied from `delta_logloss`;
- utility must not be ranked from `delta_logloss`;
- utility must not be rounded, clipped, or affine-transformed from
  `delta_logloss`;
- utility must not be derived from NLL or token logprobs.

Success criteria:

- all row, instance, heldout, ESS, sign-agreement, Spearman, and residual gates
  pass;
- all negative controls fail or remain explicitly control-only;
- no claim is used before independent review.

Fail criteria:

- any primary gate fails;
- any non-circularity check fails;
- candidate-pool provenance cannot bind rows to packet IDs and hashes;
- live evaluator availability or storage policy is not approved.

Claim ceiling:

```text
stratum_local_candidate_pending_independent_review
```

before review, and `no_claim_upgrade` unless a future reviewed Route 3 package
passes its gates.

## Route 3C Conditional Calibration Protocol

Route 3C should test whether bridge alignment is conditional on predeclared
HotpotQA strata rather than global across all rows.

Pre-registered strata:

- answer type: yes/no vs string/entity;
- gold-support packet count;
- gold-support token budget bucket;
- candidate-pool size bucket;
- whether `L` already contains gold support;
- whether `A` is gold-supporting or distractor;
- single-hop-like vs multi-hop support pattern when derivable from support
  facts.

Global baselines:

- pooled global Route 3A fit;
- P63R original negative result;
- FixB non-circular negative result;
- shuffled-control baselines.

Conditional calibrator family:

```text
per-stratum through-origin scale: delta_utility ~= c_s * delta_logloss
```

Minimum reportable cell:

```text
>= 100 rows
>= 30 original HotpotQA instances
```

Worst-cell reporting:

- every predeclared cell must be reported;
- failed or underpowered cells remain `operational_utility_only` or
  `ambiguous_metric`;
- partial passing cells cannot support a global claim.

Success criteria:

- each claimed stratum independently passes row, instance, heldout, ESS,
  sign-agreement, Spearman, and residual gates;
- worst-cell failures are reported rather than filtered away;
- independent review accepts the stratum-local interpretation.

Fail criteria:

- underpowered cells are presented as passing;
- strata are modified after row generation;
- failed cells are omitted;
- any global claim is inferred from partial conditional success.

## Stop / Continue / Escalate Gates

Stop if:

- utility is copied from or algebraically derived from `delta_logloss`;
- raw row provenance cannot bind to `candidate_pool_hash` and packet IDs;
- Route 3 text implies denied claims before future gates and review;
- a design overwrites P63R, FixA, FixB, P56, or P66 artifacts;
- large JSONL/operator-input storage is not approved.

Continue if:

- the protocol is pre-registered and independently accepted;
- utility is support-grounded and independent from logloss;
- candidate-pool support achievability remains reproducible;
- future evaluator use is explicitly approved before any NLL generation;
- artifact storage is decided before large rows are generated.

Escalate if:

- live API calls, human annotation, contamination review, or new large artifact
  storage are required;
- any result is proposed as a claim upgrade;
- artifact size would materially expand repository weight;
- oracle behavior is proposed as deployable rather than
  `non_deployable_upper_bound`.

## Artifact Storage Policy

Route 3 should not keep expanding normal Git with large JSONL rows, dispatch
traces, or operator-input files by default.

Recommended policy:

- commit deterministic summaries, manifests, schemas, validation reports, and
  claim-boundary reports;
- store future large JSONL rows/traces/operator inputs in release assets, Git
  LFS, DVC, or external artifact storage;
- commit content hashes, row counts, schema versions, generation configs, and
  validation summaries for large artifacts;
- keep raw benchmark mirrors outside the repository;
- keep raw live API responses out of Git unless sanitized and explicitly
  approved.

## Denied Claims

Route 3 Package A does not support:

- `calibrated_proxy_supported`
- `vinfo_proxy_supported`
- measurement validation
- paper evidence
- metric bridge support
- P55 bridge support
- P56 metric support
- global selector superiority
- deployed V-information verification
