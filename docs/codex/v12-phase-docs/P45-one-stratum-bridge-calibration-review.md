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


# P45 Review Document — One-Stratum Metric Bridge Calibration

## Review Goal

Review the P45 implementation for correctness, claim safety, determinism, and paper alignment.

This is a read-only review unless blocking fixes are explicitly requested in a later development round.

## Required Review Checks

### 1. Artifact Completeness

Verify that the lane emits:

- `bridge_calibration_pairs.jsonl`
- `bridge_calibration_fit.json`
- `bridge_calibration_table.csv`
- `bridge_claim_gate_report.json`
- `report.md`

Each artifact must be deterministic and path-stable.

### 2. Schema Correctness

Check that calibration pairs validate:

- one active `stratum_id`
- finite `delta_utility`
- finite `delta_logloss`
- positive `block_size`
- positive `replicate_count`
- required stratum fields
- explicit source kind: `fixture`, `operator_provided`, or `replay`

### 3. Bridge Fit Correctness

Check:

- `c_s` computation is transparent
- residual definition is correct:
  \[
  |\Delta_U-c_s\Delta_\ell|
  \]
- `zeta_s` is conservative and config-controlled
- correlations and sign agreement are computed over valid samples only
- too-small samples fail closed

### 4. Claim Gate Correctness

Verify:

- `calibrated_proxy_supported` appears only when thresholds pass
- weak or invalid bridge emits `operational_utility_only` or `ambiguous_metric`
- no fixture output is treated as scientific measurement evidence
- no output claims `measurement_validated`
- no output claims deployed V-information verification

### 5. Synthetic-Only Boundary

Confirm synthetic-only evidence remains:

```text
metric_claim_level = ambiguous_metric
diagnostic_scope/evidence_scope = synthetic_structural_only
```

unless there is explicit log-loss alignment or bridge support.

### 6. Determinism

Run repeated fixture execution if feasible and compare outputs.

No timestamps, UUIDs, absolute paths, or nondeterministic ordering should affect reproducibility.

### 7. Test Review

Run or inspect results for:

```bash
python -m compileall cps scripts
uv run pytest tests/test_bridge_calibration_experiment.py -q
uv run pytest tests/test_metric_bridge_gate.py tests/test_claim_gate_report.py -q
uv run pytest tests/test_revised_framing_guardrails.py -q
uv run pytest -q
git diff --check
```

## Review Verdict Format

Return in Chinese:

```text
# P45 Review Verdict

ACCEPT | ACCEPT_WITH_NOTES | REQUEST_CHANGES

## Blocking Issues
- severity:
- file:
- issue:
- why it matters:
- minimal fix:

## Non-blocking Notes

## Claim Boundary Assessment

## Tests Reviewed

## Final Recommendation
```
