# P28 Contamination And Empirical Evidence Package Review

```yaml
phase_id: P28
phase_title: Contamination and Live Evidence Package Integration
document_type: implementation_review
branch: codex/p28-contamination-live-evidence-package
measurement_validated_claimed: false
p04_status: deferred/operator-required
p09_status: BLOCKED_OPERATOR_REQUIRED
live_api_run: false
labels_fabricated: false
kappa_fabricated: false
contamination_pass_fabricated: false
empirical_validation_completed: false
source_manuscript_changed: false
original_repo_synced: false
```

## 1. Phase Summary

P28 adds deterministic contamination-audit artifacts and an empirical evidence
package builder. The package integrates P26 controlled live pilot outputs, P27
human-label completeness and kappa reports, contamination audit status, metric
bridge freshness, and existing conservative claim-gate semantics.

P28 does not run live APIs, fabricate labels, fabricate kappa, fabricate
contamination pass, unblock P04/P09, or claim `measurement_validated`.

## 2. Changed Files

- `cps/experiments/contamination_audit.py`
- `cps/experiments/empirical_evidence_package.py`
- `tests/test_contamination_audit.py`
- `tests/test_empirical_evidence_package.py`
- `docs/experiments/contamination-audit-artifacts.md`
- `docs/experiments/empirical-evidence-package.md`
- `docs/reviews/P28-review.md`

## 3. Contamination Checks Implemented

The contamination audit implements these deterministic checks:

- `leaked_labels`
- `seen_during_prompt_or_dev`
- `candidate_pool_contains_direct_answer`
- `unfair_baseline_access`
- `annotator_leakage`
- `duplicated_examples`
- `post_hoc_prompt_tuning_on_test_cases`
- `train_test_overlap`
- `answer_key_exposure`
- `condition_assignment_leakage`

Any failed check forces `pilot_only`. Unknown or incomplete contamination audits
deny `measurement_validated`.

## 4. Empirical Package Outputs

The empirical package writer emits:

- `empirical_evidence_manifest.json`
- `live_pilot_summary.json`
- `human_label_completeness_report.json`
- `kappa_report.json`
- `contamination_report.json`
- `empirical_claim_gate_report.json`
- `empirical_evidence_summary.md`

The builder accepts P26-style output directories or in-memory mappings. Missing
EV3/EV4 artifacts fail closed.

## 5. Claim Mapping

| Evidence state | Claim effect |
| --- | --- |
| No controlled live run | `not_empirical_validation` |
| Live run without labels | `controlled_live_pilot_only` |
| Missing labels | Not `measurement_validated` |
| Missing kappa | Not `measurement_validated` |
| Low kappa | `pilot_only` or weak evidence |
| Contamination failed | `pilot_only` |
| Contamination unknown/incomplete | Not `measurement_validated` |
| Stale or missing metric bridge | `operational_utility_only` or `ambiguous` |
| Favorable evidence without claim gate allow | `measurement_validated_candidate` only |

P28 preserves the hard claim boundary that live API success, high kappa,
contamination pass, artifact completeness, and fresh bridge evidence are not
individually sufficient for measurement validation.

## 6. Denied Claims

- `measurement_validated` is not claimed by default.
- Scientific validation is not claimed.
- Live API success alone is not measurement validation.
- High kappa alone is not measurement validation.
- Contamination pass alone is not measurement validation.
- Replay or engineering package completeness is not scientific validation.
- Synthetic/proxy evidence does not certify deployed V-information
  submodularity.

## 7. Known Limitations

- P28 does not execute a controlled live run.
- P28 does not collect labels.
- P28 does not adjudicate labels.
- P28 does not compute kappa from new empirical labels.
- P28 does not perform a real contamination audit.
- P28 does not close metric bridge freshness.
- P28 does not unblock P04 or P09.

## 8. Validation Commands And Results

Commands:

```powershell
python -m compileall cps scripts
pytest tests/test_contamination_audit.py -q
pytest tests/test_empirical_evidence_package.py -q
pytest tests/test_human_label_kappa.py -q
pytest tests/test_controlled_live_pilot.py -q
pytest tests/test_claim_gate_report.py -q
pytest tests/test_metric_bridge_gate.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Results:

| command | result |
| --- | --- |
| `python -m compileall cps scripts` | passed |
| `pytest tests/test_contamination_audit.py -q` | 9 passed |
| `pytest tests/test_empirical_evidence_package.py -q` | 13 passed |
| `pytest tests/test_human_label_kappa.py -q` | 14 passed |
| `pytest tests/test_controlled_live_pilot.py -q` | 14 passed |
| `pytest tests/test_claim_gate_report.py -q` | 11 passed |
| `pytest tests/test_metric_bridge_gate.py -q` | 15 passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |

## 9. Next Recommended Phase

Next recommended phase:

```text
P29 Controlled Empirical Results Manuscript Patch
```

Alternative if operators are preparing execution rather than writing:

```text
P29 Live Pilot Operator Runbook
```

## 10. Claim Boundary

- P28 packages empirical evidence artifacts only.
- P28 did not call live APIs.
- P28 did not fabricate labels or kappa.
- P28 did not fabricate contamination pass for real data.
- P28 does not complete empirical validation.
- Contamination pass alone is not validation.
- High kappa alone is not validation.
- Fresh metric bridge and claim gate approval remain required.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- `measurement_validated` is not claimed by default.
- No original repo sync was performed.
