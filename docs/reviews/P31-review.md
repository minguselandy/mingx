# P31 Operator-Approved Live Pilot Execution Decision Review

```yaml
phase_id: P31
phase_title: Operator-Approved Live Pilot Execution Decision
document_type: decision_review
branch: codex/p31-live-pilot-execution-decision
measurement_validated_claimed: false
p04_status: deferred/operator-required
p09_status: BLOCKED_OPERATOR_REQUIRED
live_api_run: false
external_sdk_imported: false
labels_fabricated: false
kappa_fabricated: false
contamination_pass_fabricated: false
empirical_validation_completed: false
source_manuscript_changed: false
original_repo_synced: false
```

## 1. Phase Summary

P31 adds the operator decision gate between P30 dry-run rehearsal and any future
P32 operator-approved live pilot execution. It is decision/documentation only.

P31 does not run live APIs, implement API clients, import external SDKs,
fabricate labels, fabricate kappa, fabricate contamination pass, unblock P04/P09,
or claim `measurement_validated`.

## 2. Changed Files

- `docs/runbooks/live-pilot-execution-decision.md`
- `docs/templates/live-pilot-manifest-template.json`
- `docs/reviews/P31-review.md`

## 3. Decision Statuses Documented

The decision document defines these statuses:

- `DO_NOT_RUN`
- `APPROVED_FOR_DRY_RUN_ONLY`
- `APPROVED_FOR_FLASH_ONLY_LIVE_PILOT`
- `APPROVED_FOR_FLASH_AND_PRO_LIVE_PILOT`
- `DEFER_UNTIL_LABELERS_READY`
- `DEFER_UNTIL_BUDGET_APPROVED`
- `DEFER_UNTIL_METRIC_BRIDGE_READY`

The default status is `DO_NOT_RUN`.

## 4. Manifest Template Created

Template path:

```text
docs/templates/live-pilot-manifest-template.json
```

The template uses placeholders only. It defaults to:

- `decision_status: DO_NOT_RUN`;
- `operator_approval: false`;
- `mode: dry_run`;
- `live_api_used: false`;
- `external_runtime_used: false`.

`measurement_validated` appears only as a forbidden claim.

## 5. Recommended Initial Live Plan

The recommended initial live plan is conservative:

- prefer DeepSeek V4 Flash only;
- run 30-50 cases;
- use `no_cps_baseline`, `heuristic_selector_baseline`, and
  `cps_runtime_audit_scaffold`;
- hold DeepSeek V4 Pro for a 10-20 matched audit subset only after the Flash
  pipeline succeeds.

This controls cost, validates artifact capture on the primary pilot condition
first, and avoids spending Pro budget before the pipeline is stable.

## 6. Denied Claims

- `measurement_validated` is not claimed.
- P31 is not empirical validation completed.
- P31 does not authorize live execution by itself.
- Live API success alone is not measurement validation.
- DeepSeek V4 Flash / Pro are model conditions, not validation authorities.
- High kappa alone is not validation.
- Contamination pass alone is not validation.
- Engineering success is not scientific validation.
- Synthetic/proxy evidence does not certify deployed V-information
  submodularity.

## 7. Known Limitations

- P31 does not execute P32.
- P31 does not fill the operator manifest.
- P31 does not approve budget.
- P31 does not configure credentials.
- P31 does not collect labels.
- P31 does not compute kappa.
- P31 does not run contamination audit.
- P31 does not close metric bridge freshness.
- P04 and P09 remain operator-required.

## 8. Validation Commands And Results

Commands:

```powershell
python -m compileall cps scripts
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
pytest tests/test_operator_dry_run_rehearsal.py -q
pytest tests/test_controlled_live_pilot.py -q
pytest tests/test_empirical_evidence_package.py -q
```

Results:

| command | result |
| --- | --- |
| `python -m compileall cps scripts` | passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |
| `pytest tests/test_operator_dry_run_rehearsal.py -q` | 10 passed |
| `pytest tests/test_controlled_live_pilot.py -q` | 14 passed |
| `pytest tests/test_empirical_evidence_package.py -q` | 13 passed |

## 9. Next Recommended Phase

Next recommended phase:

```text
P32 Operator-Approved Live Pilot Execution only after explicit operator approval
```

P32 must only begin from explicit operator instruction that includes approval
decision, filled manifest path, budget cap, model endpoints/model names, case
count, and output root.

## 10. Claim Boundary

- P31 is decision/documentation only.
- No live API was run.
- No external SDK was imported.
- DeepSeek V4 Flash / Pro are model conditions, not validation authorities.
- `measurement_validated` is not claimed.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- No original repo sync was performed.
