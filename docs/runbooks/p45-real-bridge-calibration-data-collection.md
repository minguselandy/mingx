# P45 Real Bridge Calibration Data Collection Runbook

This runbook is for collecting operator-provided paired measurements for the
P45 one-stratum metric bridge calibration lane.

It does not authorize live API calls, fabricated measurements, fixture reuse as
real data, human-label collection, kappa computation, or `measurement_validated`
claims.

## Inputs And Outputs

Use the operator template:

```text
docs/templates/bridge-calibration-pairs-template.jsonl
```

Copy the template to an operator-owned path before filling it, for example:

```text
path/to/operator_bridge_calibration_pairs.jsonl
```

The P45 runner accepts JSONL or CSV and writes these artifacts after dry
validation passes:

- `bridge_calibration_pairs.jsonl`
- `bridge_calibration_fit.json`
- `bridge_calibration_table.csv`
- `bridge_claim_gate_report.json`
- `report.md`

## Recommended First Stratum

Use one active stratum for the first pilot. Keep every stratum field fixed
across all rows in the input file.

| Field | Recommended first-pilot value |
|---|---|
| `task_family` | `bio_attribute` |
| `model_tier` | `operator_provided_fixed_model_v1` |
| `materialization_policy` | `fixed_order_v1` |
| `block_size` | `1` |
| `candidate_slice_band` | `top_L` |
| `metric` | `model_adjudicated_utility_vs_logloss` |

Use a stratum identifier that makes the fixed choices explicit, for example:

```text
bio_attribute__operator_provided_fixed_model_v1__fixed_order_v1__block1__top_L
```

If the operator has a canonical model-tier registry, replace
`operator_provided_fixed_model_v1` with that exact model-tier identifier and
keep it fixed for the whole file.

## Collection Protocol

For each row, choose one held context `L` and one candidate block `A`. The row
must compare the same task under two conditions:

- without the candidate block: `L`
- with the candidate block: `L union A`

Use stable identifiers for `context_id`, `block_id`, and `pair_id`. Record
operator provenance in `notes`, including the scorer, fixed model, scoring set,
replicate policy, and any exclusions.

## Computing `delta_utility`

Compute:

```text
Delta_U(A|L) = U(L union A) - U(L)
```

Write this value to `delta_utility`.

The utility scorer must stay fixed across the active stratum. Positive
`delta_utility` means the candidate block improved operational utility under
the chosen scorer.

## Computing `delta_logloss`

Compute:

```text
Delta_logloss(A|L) = loss(L) - loss(L union A)
```

Write this value to `delta_logloss`.

The log-loss scorer, fixed model, and scoring set must stay fixed across the
active stratum. Positive `delta_logloss` means adding the candidate block
reduced log loss.

## Keeping One Active Stratum Fixed

For one P45 input file, keep these fields identical in every row:

- `stratum_id`
- `task_family`
- `model_tier`
- `materialization_policy`
- `metric`
- `block_size`
- `candidate_slice_band`

Change only row-local identifiers and measurements:

- `pair_id`
- `context_id`
- `block_id`
- `delta_utility`
- `delta_logloss`
- `replicate_count`
- `notes`

If any fixed stratum field changes, start a separate input file and separate
output directory. Do not merge multiple strata into a first P45 paper-facing
pilot.

## Source Separation

Use exactly one source kind in an input file:

- `fixture`: committed deterministic engineering fixture only. It validates
  implementation and is not paper bridge evidence.
- `operator_provided`: real operator-computed paired measurements. This is the
  required source kind for a paper-facing P45 bridge pilot.
- `replay`: imported replay-derived rows. Do not mix with operator-provided
  rows in this lane.

Never copy rows from `artifacts/fixtures/bridge_calibration_pairs_fixture.jsonl`
into an operator file. Never change fixture rows to `operator_provided`.

## Sample Size Guidance

The configured lower bound is intentionally small:

- `6` rows: engineering smoke only. This checks that the runner, schema, and
  gate work, but it is not enough for a convincing paper-facing table.
- `20-30` rows: recommended first real pilot. This is enough to inspect
  stability, sign agreement, correlations, and outliers before expanding.
- `50+` rows: preferred for a paper-facing table. This gives a stronger basis
  for summarizing `c_s`, `zeta_s`, correlations, and downgrade behavior.

These counts do not guarantee a positive claim. The bridge gate can still
downgrade if residuals, sign agreement, Pearson, Spearman, source consistency,
freshness, or one-stratum checks fail.

## Dry Validation

Run dry validation before writing artifacts:

```bash
uv run python -m cps.experiments.bridge_calibration --config configs/runs/bridge-calibration-one-stratum.json --input path/to/operator_bridge_calibration_pairs.jsonl --dry-validate
```

Dry validation checks schema, one-stratum consistency, source mixing, sample
thresholds, residual thresholds, sign agreement, Pearson correlation, and
Spearman correlation. It writes no artifacts and does not claim paper evidence.

Review these fields in dry-validation output:

- `mode`
- `schema_validation_status`
- `threshold_validation_status`
- `data_source_kind`
- `active_stratum_ids`
- `sample_size`
- `effective_sample_size`
- `pass_flags`
- `reason_codes`
- `would_be_metric_claim_level`
- `would_be_paper_evidence_eligible`
- `paper_evidence_eligible`
- `paper_evidence_claimed`

For dry validation, `paper_evidence_eligible` and `paper_evidence_claimed` must
remain `false`.

## Artifact Generation

After dry validation passes and the operator confirms provenance, generate
artifacts:

```bash
uv run python -m cps.experiments.bridge_calibration --config configs/runs/bridge-calibration-one-stratum.json --input path/to/operator_bridge_calibration_pairs.jsonl --output-dir artifacts/experiments/bridge_calibration_one_stratum_operator
```

Use a separate output directory for each operator run. Do not overwrite fixture
outputs when preparing paper-facing artifacts.

## Claim Boundary

This lane estimates whether the active stratum supports a utility-to-log-loss
bridge:

```text
|Delta_U(A|L) - c_s * Delta_logloss(A|L)| <= zeta_s
```

Bridge success can support only:

```text
calibrated_proxy_supported
```

and only for the active stratum represented by the operator-provided input.

Bridge failure or weak support must downgrade to:

```text
operational_utility_only
```

or:

```text
ambiguous_metric
```

This lane does not create human labels, does not create kappa, does not close
contamination, does not claim scientific validation, does not verify deployed
V-information, and does not create `measurement_validated`.

## Paper Integration

For paper-facing summaries, use generated artifacts rather than the operator
input file alone.

From `bridge_calibration_fit.json`, summarize:

- `bridge_scale_c_s` as `c_s`
- `zeta_s`
- `sign_agreement`
- `spearman_correlation`
- `pearson_correlation`
- `sample_size` as `n`
- `effective_sample_size`
- `metric_claim_level`
- `active_stratum_id`
- `data_source_kind`
- `paper_evidence_eligible`
- `reason_codes`

From `bridge_claim_gate_report.json`, summarize:

- `claim_gate_status`
- `allowed_claim_level`
- `pass_flags`
- `denied_claims`

If `metric_claim_level` is not `calibrated_proxy_supported`, report the
downgrade directly. A failed bridge is still useful evidence for conservative
claim handling, but it is not a successful bridge-calibration result.

## API-Generated Live Smoke Preflight

API-generated rows are still operator-provided rows only when the operator
explicitly approves the live run and keeps credential handling local. Start from
the non-secret template:

```text
configs/local/bridge-data-generation-live-template.example.json
```

Copy it to an untracked local config, replace provider and model identifiers,
and keep API key values outside the repository. Credential CSV files and `.env`
files must remain untracked and ignored.

Set live gates in the operator shell, not in tracked files:

```powershell
$env:CPS_ALLOW_LIVE_API = "1"
$env:P45_ALLOW_API_DATA_GENERATION = "1"
```

For local operator work, the same values and provider credential env vars may be
kept in ignored `.env.local`. When generated from a local credential CSV, keep
`.env.local` untracked and never print its values.

Before a live smoke, verify:

- Credential file exists.
- Credential file is untracked.
- Credential file is ignored.
- Environment gates are set.
- Local config uses `mode = live_operator_approved`.
- Local config uses `operator_approval = true`.
- Fixed model supports actual logprobs.
- Strong reviewer/adjudicator is configured.
- Output directory is unique for the smoke.

Do not run live generation if any preflight item fails.

Run preflight without calling the provider:

```bash
uv run python -m cps.experiments.bridge_data_generation --config configs/local/bridge-data-generation-live.local.json --preflight-only
```

## P45b Bridge Canary Task Design

The first API-generated live smoke was a valid engineering smoke but not a
successful bridge. It produced measured fixed-model logprobs, then failed
`pearson`, `spearman`, `sign_agreement`, and `zeta` thresholds because utility
scores saturated and `delta_logloss` values were tiny. One row also had
positive utility but negative `delta_logloss`. The claim level for that smoke
therefore remains `operational_utility_only`.

For the next 8-row canary, use the P45b task-packet mode or equivalent
operator-authored packets:

```json
{
  "task_packet_mode": "bridge_canary_v2",
  "sample_limit": 8
}
```

Each packet should keep:

- `task_family = bio_attribute`
- `materialization_policy = fixed_order_v1`
- `block_size = 1`
- `candidate_slice_band = top_L`

Design principles:

- Baseline context `L` must be insufficient to infer the target answer.
- Added block `A` must be the decisive or controlled evidence.
- Target answers should use low-prior operator-coded bio-attribute strings.
- The question and baseline must not leak the exact target string.
- Avoid common city, person, date, or generic attribute answers.
- Use varied evidence-strength bands: `irrelevant`, `weak_hint`,
  `partial_constraint`, `strong_clue`, and `explicit_answer`.

This variation is intended to avoid utility saturation. It does not relax any
bridge threshold and does not fabricate utility or log-loss measurements.

## Utility Reviewer Rubric

The strong reviewer should return `utility_without`, `utility_with`,
`delta_utility`, `utility_rationale`, and `evidence_strength_band`. The scoring
rubric is:

- `0.00`: no support
- `0.25`: weak clue only
- `0.50`: partial constraint
- `0.75`: strong but ambiguous
- `1.00`: exact target entailed

The reviewer must ignore world knowledge and use only the supplied context.
It must not estimate `delta_logloss`, `loss_without`, or `loss_with`.

## Low-Signal Handling

The next canary uses a configured low-signal screen:

```json
{
  "minimum_abs_delta_logloss_for_bridge_evidence": 0.001
}
```

Rows with `abs(delta_logloss)` below the threshold are reported as
bridge-uninformative rather than used as strong bridge evidence. Rows with
`delta_logloss < 0` are reported separately. These rows are not silently
dropped; their counts and reason codes must remain in review, dry-validation,
or fit artifacts.

When preflight passes and the operator explicitly authorizes live generation,
run the provider-profile path with an explicit task-packet JSONL:

```bash
uv run python -m cps.experiments.bridge_data_generation --config configs/local/bridge-data-generation-live.local.json --task-packets path/to/operator_task_packets.jsonl --use-live-provider-profile
```

The provider-profile path constructs the fixed-model log-loss scorer, strong
utility reviewer, and adjudicator from the approved local config. The fixed
model must return actual non-degenerate token logprobs for the target answer.
Rows without measured logprobs remain review artifacts only and are not exported
as accepted calibration rows. The strong reviewer output is rejected if it tries
to supply `delta_logloss`.

## Operator Checklist

- Copy the template to an operator-owned path.
- Replace every `OPERATOR_FILL_*` value.
- Keep one active stratum fixed.
- Use `source = operator_provided` only for real operator-computed rows.
- Do not mix `fixture`, `operator_provided`, and `replay`.
- Collect at least `20-30` rows for the first real pilot when feasible.
- Prefer `50+` rows before using the table as paper-facing evidence.
- Run dry validation.
- Generate artifacts only after dry validation passes and provenance is
  confirmed.
- Report claim downgrades without upgrading them to measurement validation.
