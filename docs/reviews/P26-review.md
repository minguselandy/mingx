# P26 Controlled Live API Pilot Runner Review

```yaml
phase_id: P26
phase_title: Controlled Live API Pilot Runner Design
document_type: implementation_review
branch: codex/p26-controlled-live-api-pilot-runner
measurement_validated_claimed: false
p04_status: deferred/operator-required
p09_status: BLOCKED_OPERATOR_REQUIRED
live_api_run: false
live_cohort_run: false
external_sdk_imported: false
runtime_code_changed: true
source_manuscript_changed: false
original_repo_synced: false
```

## 1. Phase Summary

P26 adds a guarded controlled live pilot runner scaffold for future EV2 empirical
validation. The runner defaults to `dry_run`, writes deterministic local
artifacts, and can enter `live_operator_approved` mode only when all explicit
operator gates are present.

P26 does not run live APIs, implement vendor clients, import external SDKs,
fabricate human labels, fabricate kappa, unblock P04/P09, or claim
`measurement_validated`.

## 2. Changed Files

- `cps/experiments/controlled_live_pilot.py`
- `tests/test_controlled_live_pilot.py`
- `docs/experiments/controlled-live-pilot-runner.md`
- `docs/reviews/P26-review.md`

## 3. Live Gates Implemented

Live mode fails closed before any model call unless all gates are present:

| Gate | Behavior |
| --- | --- |
| `CPS_ALLOW_LIVE_API=1` | Missing env var raises `LivePilotGateError`. |
| Explicit run manifest path | Missing path raises `LivePilotGateError`. |
| Fixed endpoint/model/prompt/temperature/output root | Missing required fields raise `LivePilotGateError`. |
| `operator_approval: true` | Missing approval raises `LivePilotGateError`. |
| Injected `model_call_fn` | Missing callable raises `LivePilotGateError`. |

No vendor-specific client is implemented. Tests use deterministic fake callables.

## 4. Dry-Run Behavior

- Default mode is `dry_run`.
- `model_call_fn` is not called in dry-run.
- `live_api_used` is `false`.
- `external_runtime_used` is `false`.
- The runner writes deterministic local artifacts and summaries.
- The claim gate denies `measurement_validated` because human labels and kappa
  are absent.

## 5. Denied Claims

- `measurement_validated` is not claimed.
- Controlled live pilot alone is not measurement validation.
- Live API success alone does not imply measurement validation.
- Missing human labels deny `measurement_validated`.
- Missing kappa denies `measurement_validated`.
- Stale or missing metric bridge remains `operational_utility_only` or
  `ambiguous`.
- Engineering success is not scientific validation.
- Synthetic/proxy evidence does not certify deployed V-information
  submodularity.

## 6. Known Limitations

- P26 does not provide a real provider or model API client.
- P26 does not perform human labeling.
- P26 does not compute kappa.
- P26 does not execute contamination closure.
- P26 does not close metric bridge freshness.
- P26 does not perform P09 external runtime integration.
- P26 does not advance P04 scientific closure.

## 7. Validation Commands And Results

Commands:

```powershell
python -m compileall cps scripts
pytest tests/test_controlled_live_pilot.py -q
pytest tests/test_claim_gate_report.py -q
pytest tests/test_metric_bridge_gate.py -q
pytest tests/test_replay_evidence_package.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Results:

| command | result |
| --- | --- |
| `python -m compileall cps scripts` | passed |
| `pytest tests/test_controlled_live_pilot.py -q` | 14 passed |
| `pytest tests/test_claim_gate_report.py -q` | 11 passed |
| `pytest tests/test_metric_bridge_gate.py -q` | 15 passed |
| `pytest tests/test_replay_evidence_package.py -q` | 11 passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |

## 8. Next Recommended Phase

Next recommended phase:

```text
P27 Human Label and Kappa Artifact Protocol Implementation
```

P27 should implement human-label and kappa artifact handling without treating P26
pilot completion as validation.

## 9. Claim Boundary

- P26 defaults to dry-run.
- P26 did not call live APIs.
- P26 is controlled-live-pilot scaffolding only.
- Human labels and kappa remain required.
- Contamination pass and fresh metric bridge remain required.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- `measurement_validated` is not claimed.
- No original repo sync was performed.
