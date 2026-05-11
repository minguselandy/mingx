# One-Stratum Metric Bridge Calibration

This experiment is the P45 offline/importable lane for estimating one
stratum-specific utility-to-log-loss bridge:

```text
|Delta_U(A | L) - c_s * Delta_logloss(A | L)| <= zeta_s
```

It is a claim-gated calibration lane, not a live API runner and not a
measurement-validation procedure.

## Input Schema

The lane accepts `.jsonl` or `.csv` calibration pairs with the following
required fields:

```json
{
  "pair_id": "p001",
  "stratum_id": "bio_attribute__fixed_model__fixed_order__block1",
  "task_family": "bio_attribute",
  "model_tier": "offline_fixture_or_operator_provided",
  "materialization_policy": "fixed_order_v1",
  "metric": "model_adjudicated_utility_vs_logloss",
  "block_size": 1,
  "candidate_slice_band": "top_L",
  "context_id": "L001",
  "block_id": "A001",
  "delta_utility": 0.205,
  "delta_logloss": 0.1,
  "replicate_count": 1,
  "source": "fixture",
  "notes": "deterministic engineering fixture only"
}
```

`source` must be one of `fixture`, `operator_provided`, or `replay`.

## Operator Data Template

Use `docs/templates/bridge-calibration-pairs-template.jsonl` as the operator
handoff template. It contains six placeholder rows because the default run
requires at least six distinct calibration pairs and an effective sample size of
at least six.

The template is not evidence. Copy it to a separate operator-owned data path,
replace every `OPERATOR_FILL_*` value, and keep `source` set to
`operator_provided` only for measurements that were actually computed by the
operator. Do not copy rows from
`artifacts/fixtures/bridge_calibration_pairs_fixture.jsonl` into an operator
data file.

## Computing Real Calibration Pairs

For each pair, keep a fixed context `L` and candidate block `A`.

- Compute `delta_utility` as `utility_with_A - utility_without_A`, using the
  same operational utility scorer, task family, model tier, materialization
  policy, candidate slice band, and replicate rule across the active stratum.
- Compute `delta_logloss` as `logloss_without_A - logloss_with_A`, using the
  fixed model and fixed scoring set. Positive values therefore mean the
  candidate block reduced log loss.
- Use the same sign convention for every row so positive `delta_utility` and
  positive `delta_logloss` both mean improvement.
- Set `replicate_count` to the number of independent repeats or scoring
  replicates summarized by the row. Do not use it to inflate rows copied from
  fixture data.

## One Active Stratum

This lane is one-stratum by default. In one operator input file, keep these
fields fixed across all rows:

- `stratum_id`
- `task_family`
- `model_tier`
- `materialization_policy`
- `metric`
- `block_size`
- `candidate_slice_band`

If any of those fields changes, start a separate input file and separate run.
Do not enable multi-stratum mode for P45 paper handoff unless the protocol is
expanded first.

## Sample Size

The default config requires:

- `minimum_sample_size = 6`
- `minimum_effective_sample_size = 6`

This is a lower bound for running the gate, not a guarantee of paper support.
The run can still downgrade to `operational_utility_only` or
`ambiguous_metric` when residual, sign-agreement, correlation, source, freshness,
or one-stratum checks fail.

## Dry Validation

Run dry validation before writing paper-facing artifacts:

```bash
uv run python -m cps.experiments.bridge_calibration \
  --config configs/runs/bridge-calibration-one-stratum.json \
  --input path/to/operator_bridge_calibration_pairs.jsonl \
  --dry-validate
```

Dry validation checks schema, one-stratum constraints, sample thresholds, source
mixing, residual thresholds, sign agreement, and correlations. It writes no
artifacts and sets `paper_evidence_eligible = false` even if the reported
`would_be_metric_claim_level` would pass in a non-dry run.

P45b also reports low-signal bridge rows. By default,
`minimum_abs_delta_logloss_for_bridge_evidence = 0.001`. Rows with
`abs(delta_logloss)` below that configured threshold are marked
bridge-uninformative and cause the bridge gate to fail closed rather than being
treated as strong bridge evidence. Rows with `delta_logloss < 0` are reported
separately in fit and claim artifacts. The threshold is an added conservative
screen; it is not a relaxation of the existing residual, sign, Pearson, or
Spearman gates.

## Fixture Command

```bash
uv run python -m cps.experiments.bridge_calibration \
  --config configs/runs/bridge-calibration-one-stratum.json \
  --input artifacts/fixtures/bridge_calibration_pairs_fixture.jsonl \
  --output-dir artifacts/experiments/bridge_calibration_one_stratum
```

The committed fixture validates implementation only. It is for engineering
tests, not paper bridge evidence. Operator-provided measurements should use the
same schema but replace `source` and provenance fields accordingly.

## Real Calibration Command

After dry validation passes and the operator has confirmed the data provenance,
run the real calibration against an operator-owned input file:

```bash
uv run python -m cps.experiments.bridge_calibration \
  --config configs/runs/bridge-calibration-one-stratum.json \
  --input path/to/operator_bridge_calibration_pairs.jsonl \
  --output-dir artifacts/experiments/bridge_calibration_one_stratum_operator
```

Do not use the fixture input for paper bridge evidence. Operator-provided data
is required for any paper bridge evidence from this lane.

## Outputs

The lane writes exactly these artifacts to the selected output directory:

- `bridge_calibration_pairs.jsonl`
- `bridge_calibration_fit.json`
- `bridge_calibration_table.csv`
- `bridge_claim_gate_report.json`
- `report.md`

The fit artifact records `bridge_scale_c_s`, `zeta_s`, absolute residual
quantiles, sign agreement, Pearson correlation, Spearman correlation, sample
size, effective sample size, claim level, selector-regime label, evidence scope,
diagnostic scope, and denied claims.

## Claim Behavior

`calibrated_proxy_supported` is emitted only when all configured thresholds
pass for non-synthetic evidence scope. Strict defaults require:

- minimum sample size of 6
- minimum effective sample size of 6
- every row to have `abs(delta_logloss) >= 0.001` for bridge-evidence support
- `zeta_s <= 0.05`
- sign agreement at least 0.90
- Pearson and Spearman correlations at least 0.90

If the data are usable but agreement, correlation, or residual thresholds fail,
the lane emits `operational_utility_only`. If the run is invalid, underpowered,
mixed-stratum without explicit multi-stratum mode, synthetic-only, stale, or
inconclusive, it emits `ambiguous_metric`.

The lane never emits `measurement_validated`, never verifies deployed
V-information, and never creates human labels, kappa, or contamination closure.
Because P45 calibrates the metric bridge rather than the selector regime, its
selector-regime label remains the conservative `ambiguous`.

## Fixture Boundary

Fixture data validates implementation only. It can exercise the calibrated path
as an engineering check, but it is not paper measurement evidence. Fixture
artifacts therefore keep:

```json
{
  "data_source_kind": "fixture",
  "paper_evidence_eligible": false,
  "measurement_validation_claim": false,
  "deployed_v_information_verification_claim": false
}
```

Operator-provided real calibration pairs may become paper evidence only if the
configured bridge gate passes. Even then, this lane still does not claim
`measurement_validated`.

This lane also does not create human labels, human-human kappa, contamination
closure, scientific validation, or deployed V-information verification. Those
must remain outside the P45 bridge-calibration claim boundary.
