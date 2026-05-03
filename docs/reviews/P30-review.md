# P30 Operator-Approved Dry-Run Rehearsal Review

```yaml
phase_id: P30
phase_title: Operator-Approved Dry-Run Rehearsal
document_type: implementation_review
branch: codex/p30-operator-approved-dry-run-rehearsal
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

P30 adds a deterministic dry-run rehearsal harness for the EV2/EV3 empirical
validation workflow. It wires P26 controlled live pilot dry-run outputs, P27
empty human-label templates and missing-kappa reports, P28 unknown contamination
reports, and P28 empirical evidence package outputs into one offline rehearsal
package.

P30 does not run live APIs, call external model providers, import external SDKs,
fabricate labels, fabricate kappa, fabricate contamination pass, unblock P04/P09,
or claim `measurement_validated`.

## 2. Changed Files

- `cps/experiments/operator_dry_run_rehearsal.py`
- `tests/test_operator_dry_run_rehearsal.py`
- `docs/experiments/operator-dry-run-rehearsal.md`
- `docs/reviews/P30-review.md`

## 3. Dry-Run Outputs

The rehearsal emits:

- `dry_run_manifest.json`
- `pilot_summary.json`
- `case_artifacts/`
- `human_labels_template.csv`
- `human_labels_template.jsonl`
- `human_label_completeness_report.json`
- `kappa_report.json`
- `contamination_report.json`
- `empirical_evidence_manifest.json`
- `empirical_claim_gate_report.json`
- `empirical_evidence_summary.md`
- `rehearsal_summary.json`
- `rehearsal_summary.md`

The P28 writer also emits `live_pilot_summary.json`, and the P27/P28 writers
emit Markdown support reports.

## 4. DeepSeek V4 Flash / Pro Dry-Run Conditions

| Model alias | Role | Case count | Claim boundary |
| --- | --- | --- | --- |
| `deepseek_v4_flash` | `primary_pilot_model` | 2 | Dry-run model condition only. |
| `deepseek_v4_pro` | `strong_model_audit_subset` | 1 | Dry-run model condition only. |

No real provider model IDs are required. The harness uses placeholders only.

## 5. Denied Claims

- `measurement_validated` is not claimed.
- Live empirical validation is not completed.
- Dry-run rehearsal is not live empirical validation.
- Engineering success is not scientific validation.
- Missing labels deny `measurement_validated`.
- Missing kappa denies `measurement_validated`.
- Unknown contamination denies `measurement_validated`.
- Missing metric bridge freshness denies validation-level interpretation.
- DeepSeek V4 Flash / Pro dry-run outputs do not validate the method.

## 6. Known Limitations

- P30 does not add a CLI.
- P30 does not run live APIs.
- P30 does not collect labels.
- P30 does not compute kappa from real labels.
- P30 does not perform real contamination audit.
- P30 does not close metric bridge freshness.
- P30 does not update the manuscript.
- P04 and P09 remain operator-required.

## 7. Validation Commands And Results

Commands:

```powershell
python -m compileall cps scripts
pytest tests/test_operator_dry_run_rehearsal.py -q
pytest tests/test_controlled_live_pilot.py -q
pytest tests/test_human_label_kappa.py -q
pytest tests/test_contamination_audit.py -q
pytest tests/test_empirical_evidence_package.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Results:

| command | result |
| --- | --- |
| `python -m compileall cps scripts` | passed |
| `pytest tests/test_operator_dry_run_rehearsal.py -q` | 10 passed |
| `pytest tests/test_controlled_live_pilot.py -q` | 14 passed |
| `pytest tests/test_human_label_kappa.py -q` | 14 passed |
| `pytest tests/test_contamination_audit.py -q` | 9 passed |
| `pytest tests/test_empirical_evidence_package.py -q` | 13 passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |

## 8. Next Recommended Phase

Next recommended phase:

```text
P31 Operator-Approved Live Pilot Execution Decision
```

P31 should decide whether operators approve a live pilot. P30 dry-run completion
does not authorize live execution by itself.

## 9. Claim Boundary

- P30 is dry-run rehearsal only.
- No live API was called.
- No external model provider was called.
- No human labels were fabricated.
- No kappa was fabricated.
- No contamination pass was fabricated.
- DeepSeek V4 Flash / Pro are dry-run model conditions only.
- `measurement_validated` is not claimed.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- No original repo sync was performed.
