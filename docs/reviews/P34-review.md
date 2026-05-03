# P34 Codex Model-Adjudicated Labels Review

```yaml
phase_id: P34
phase_title: Codex Model-Adjudicated Labels
document_type: implementation_review
branch: codex/p34-model-adjudicated-labels
measurement_validated_claimed: false
p04_status: deferred/operator-required
p09_status: BLOCKED_OPERATOR_REQUIRED
live_api_run: false
external_sdk_imported: false
human_labels_fabricated: false
kappa_fabricated: false
codex_adjudication_treated_as_human_review: false
source_manuscript_changed: false
original_repo_synced: false
```

## 1. Phase Summary

P34 adds deterministic Codex model adjudication over V4 Flash prelabels and
subagent audit outputs. The output is model-adjudicated annotation evidence only.

P34 does not fabricate human labels, fabricate annotator IDs, compute kappa, run
live APIs, or claim `measurement_validated`.

## 2. Changed Files

- `cps/experiments/model_adjudicated_labels.py`
- `tests/test_model_adjudicated_labels.py`
- `docs/experiments/model-adjudicated-labels.md`
- `docs/reviews/P34-review.md`

## 3. Adjudication Outputs

- `model_adjudicated_labels.jsonl`
- `codex_adjudication_report.json`
- `codex_adjudication_report.md`
- `model_adjudicated_label_summary.json`
- `model_adjudicated_label_summary.md`

Forbidden human-label output names are not used.

## 4. Claim Boundary

- Codex adjudication is not human review.
- Model-adjudicated labels are not human labels.
- Model-adjudicated labels cannot be used for human-human kappa.
- Model-adjudicated evidence cannot satisfy `human_labels_present` for
  `measurement_validated`.
- Model-adjudicated evidence can support only pilot/model-adjudicated/operational
  evidence.

Allowed claim level:

```text
model_adjudicated_pilot_only
```

## 5. Denied Claims

- `human_labeled_validation`
- `measurement_validated`
- `scientific_validation_completed`
- deployed V-information certification

## 6. Known Limitations

- P34 does not collect real human labels.
- P34 does not create human annotator IDs.
- P34 does not compute kappa.
- P34 does not perform contamination audit.
- P34 does not close metric bridge freshness.
- P04 and P09 remain operator-required.

## 7. Validation Commands And Results

Commands:

```powershell
python -m compileall cps scripts
pytest tests/test_model_adjudicated_labels.py -q
pytest tests/test_llm_assisted_prelabels.py -q
pytest tests/test_prelabel_subagent_audit.py -q
pytest tests/test_human_review_workflow.py -q
pytest tests/test_human_label_kappa.py -q
pytest tests/test_empirical_evidence_package.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Results:

| command | result |
| --- | --- |
| `python -m compileall cps scripts` | passed |
| `pytest tests/test_model_adjudicated_labels.py -q` | 10 passed |
| `pytest tests/test_llm_assisted_prelabels.py -q` | 16 passed |
| `pytest tests/test_prelabel_subagent_audit.py -q` | 12 passed |
| `pytest tests/test_human_review_workflow.py -q` | 15 passed |
| `pytest tests/test_human_label_kappa.py -q` | 14 passed |
| `pytest tests/test_empirical_evidence_package.py -q` | 13 passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |

## 8. Next Recommended Phase

Next recommended phase:

```text
P35 Model-Adjudicated Pilot Evidence Package
```

Alternative path if validation-level evidence is still desired:

```text
P35 Human Labeling
```

Human labeling remains required for any future `measurement_validated` claim.

## 9. Claim Boundary Restatement

- P34 does not fabricate human labels.
- P34 does not fabricate kappa.
- P34 does not run live APIs.
- Codex adjudication is not human review.
- Model-adjudicated labels are not human labels.
- `measurement_validated` is not claimed.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- No original repo sync was performed.
