# Common Guardrails for Mingx v12 Development

These phase documents are for the local repository:

`C:\Users\Mingx\Documents\mx-codex\agentic-codex\mingx-dev`

Current paper direction:
- Current manuscript anchor: `docs/archive/context_projection_fixed_v12.md`
- Current alignment anchor: `docs/paper-alignment-v12.md`
- Framing: **Proxy-Regime Diagnosis**, not broad certification
- Selector-regime labels: `greedy_supported`, `pairwise_escalate`, `higher_order_risk`, `ambiguous`
- Metric-claim levels: `vinfo_proxy_supported`, `calibrated_proxy_supported`, `operational_utility_only`, `ambiguous_metric`
- Synthetic-only evidence: `metric_claim_level = ambiguous_metric` and `diagnostic_scope/evidence_scope = synthetic_structural_only`

Hard constraints:
- No live API unless an explicit operator-approved live plan is supplied.
- No fabricated bridge calibration results.
- No fabricated human labels, kappa, or contamination closure.
- No `measurement_validated` claim.
- No deployed V-information verification claim.
- Preserve legacy v10 materials as archive/compatibility references only.
- Prefer deterministic artifacts: stable JSON key ordering, stable row ordering, no timestamps/UUIDs/absolute paths in replay-comparable outputs.
- All reports must distinguish metric claim level, selector-regime label, and evidence/diagnostic scope.


# P45 Development Plan — One-Stratum Metric Bridge Calibration

## Objective

Implement the first executable v12 metric-bridge calibration lane.

The lane estimates whether operational utility marginals can be conservatively related to fixed-model log-loss marginals in one active stratum:

\[
|\Delta_U(A\mid L)-c_s\Delta_\ell(A\mid L)|\le \zeta_s
\]

The goal is **not** to fabricate a successful bridge. The goal is to produce deterministic artifacts that can say one of:

- `calibrated_proxy_supported`
- `operational_utility_only`
- `ambiguous_metric`

## Why This Phase Matters

The paper currently specifies the bridge contract. This phase makes the contract executable in the repository.

A failed or weak bridge is still useful: it should trigger conservative claim downgrade rather than overclaiming.

## Scope

Create or update:

- `cps/experiments/bridge_calibration.py`
- `configs/runs/bridge-calibration-one-stratum.json`
- `tests/test_bridge_calibration_experiment.py`
- `docs/experiments/bridge-calibration-one-stratum.md`
- `docs/paper-alignment-v12.md` if needed

Reuse existing bridge utilities in `cps/analysis/bridge.py` if they are appropriate.

## Required Input Schema

The experiment must accept JSONL or CSV with paired marginal measurements:

```json
{
  "pair_id": "p001",
  "stratum_id": "bio_attribute__fixed_model__fixed_order__block2",
  "task_family": "bio_attribute",
  "model_tier": "offline_fixture_or_operator_provided",
  "materialization_policy": "fixed_order_v1",
  "metric": "model_adjudicated_utility_vs_logloss",
  "block_size": 1,
  "candidate_slice_band": "top_L",
  "context_id": "L001",
  "block_id": "A001",
  "delta_utility": 0.0,
  "delta_logloss": 0.0,
  "replicate_count": 1,
  "source": "fixture | operator_provided | replay",
  "notes": ""
}
```

## Validation Rules

Fail closed if:

- required fields are missing
- records contain non-finite numbers
- `block_size <= 0`
- `replicate_count <= 0`
- sample size is below config threshold
- records mix strata unless explicit multi-stratum mode is configured
- sign agreement, rank correlation, or residual bounds fail configured thresholds

## Fitting Requirements

Compute:

- `c_s`, preferably OLS-through-origin as the primary bridge scale
- optional intercept-aware diagnostic
- absolute residuals
- `zeta_s` as max residual or high quantile, configured explicitly
- mean absolute residual
- residual quantiles
- sign agreement
- Spearman rank correlation if available without heavy dependencies
- Pearson correlation
- sample size and effective sample size

## Claim Gate Behavior

- If thresholds pass: `metric_claim_level = calibrated_proxy_supported`
- If measurements are usable but do not support bridge: `metric_claim_level = operational_utility_only`
- If samples are too small, mixed, invalid, stale, or underpowered: `metric_claim_level = ambiguous_metric`
- Never emit `measurement_validated`
- Never emit deployed V-information verification

## Required Output Artifacts

Output to an experiment directory:

```text
bridge_calibration_pairs.jsonl
bridge_calibration_fit.json
bridge_calibration_table.csv
bridge_claim_gate_report.json
report.md
```

## Fixture Boundary

Add a deterministic fixture for tests only.

The fixture must be explicitly labeled as engineering validation, not paper measurement evidence.
Fixture data validates implementation only; operator-provided data is required
for any paper bridge evidence.

Report fields should include:

```json
{
  "data_source_kind": "fixture",
  "paper_evidence_eligible": false,
  "measurement_validation_claim": false
}
```

For operator-provided real measurements, use:

```json
{
  "data_source_kind": "operator_provided",
  "paper_evidence_eligible": true_or_false_based_on_claim_gate,
  "measurement_validation_claim": false
}
```

## Operator Data Handoff

Add and maintain an operator-facing template:

```text
docs/templates/bridge-calibration-pairs-template.jsonl
```

The template must remain obviously non-real: it should use placeholder values
such as `OPERATOR_FILL_*`, not fixture rows and not fabricated measurements.
The default handoff includes six placeholder records because the default gate
requires `minimum_sample_size = 6` and `minimum_effective_sample_size = 6`.

Real operator data should be prepared in a separate operator-owned JSONL or CSV
file. For a one-stratum P45 run, all rows must keep the same active
`stratum_id`, `task_family`, `model_tier`, `materialization_policy`, `metric`,
`block_size`, and `candidate_slice_band`. If any of those fields changes, create
a separate run rather than mixing strata.

Compute real marginals with a fixed sign convention:

- `delta_utility = utility_with_A - utility_without_A`
- `delta_logloss = logloss_without_A - logloss_with_A`

Positive values should mean improvement for both fields. Use the same scorer,
fixed model, fixed scoring set, and replicate policy across the active stratum.
Set `source = operator_provided` only for operator-computed data. Do not mix
`fixture` and `operator_provided` rows in one run.

## Dry Validation Mode

Provide a dry validation command that checks schema and configured thresholds
without writing paper-facing artifacts and without claiming paper evidence:

```bash
uv run python -m cps.experiments.bridge_calibration \
  --config configs/runs/bridge-calibration-one-stratum.json \
  --input path/to/operator_bridge_calibration_pairs.jsonl \
  --dry-validate
```

Dry validation may report `would_be_metric_claim_level`, but it must keep
`paper_evidence_eligible = false`, `paper_evidence_claimed = false`,
`measurement_validation_claim = false`, and deployed V-information verification
disabled.

## Recommended Command Shape

```bash
uv run python -m cps.experiments.bridge_calibration \
  --config configs/runs/bridge-calibration-one-stratum.json \
  --input artifacts/fixtures/bridge_calibration_pairs_fixture.jsonl \
  --output-dir artifacts/experiments/bridge_calibration_one_stratum
```

## Required Tests

Add focused tests for:

1. Valid deterministic fixture produces all artifacts.
2. Passing fixture can produce `calibrated_proxy_supported` only when thresholds pass.
3. Too-small sample fails closed.
4. Sign-disagreement sample fails closed.
5. Non-finite values are rejected.
6. Synthetic-only scope is not upgraded to `vinfo_proxy_supported`.
7. No artifact claims `measurement_validated`.
8. Repeated runs are deterministic.

## Validation Commands

Run:

```bash
python -m compileall cps scripts
uv run pytest tests/test_bridge_calibration_experiment.py -q
uv run pytest tests/test_metric_bridge_gate.py tests/test_claim_gate_report.py -q
uv run pytest tests/test_revised_framing_guardrails.py -q
uv run pytest -q
git diff --check
```

## Final Codex Report

Use Chinese:

```text
# P45 One-Stratum Metric Bridge Calibration Report

## 1. Summary
## 2. Changed Files
## 3. New Artifacts and Schema
## 4. Claim Gate Behavior
## 5. Fixture vs Real Measurement Boundary
## 6. Validation
## 7. Remaining Work
```
