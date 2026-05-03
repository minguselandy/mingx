# P36 Model-Adjudicated Evidence Package Integration Review

```yaml
phase_id: P36
phase_title: Model-Adjudicated Evidence Package Integration
document_type: implementation_review
branch: codex/p36-model-adjudicated-evidence-package
route_b_integrated: true
live_api_run: false
human_labels_fabricated: false
kappa_fabricated: false
model_adjudicated_labels_converted_to_human_labels: false
codex_adjudication_treated_as_human_review: false
measurement_validated_claimed: false
p04_status: deferred/operator-required
p09_status: BLOCKED_OPERATOR_REQUIRED
original_repo_synced: false
```

## 1. Phase Summary

P36 integrates Route B model-adjudicated evaluation artifacts into the empirical
evidence package. The package can now consume V4 Flash prelabels, Codex subagent
audit output, Codex adjudication reports, and model-adjudicated labels while
preserving the claim boundary that Route B cannot produce
`measurement_validated`.

## 2. Changed Files

- `cps/experiments/empirical_evidence_package.py`
- `tests/test_empirical_evidence_package.py`
- `docs/experiments/empirical-evidence-package.md`
- `docs/reviews/P36-review.md`

## 3. Route B Package Integration Summary

The empirical package now records these Route B fields:

- `route_type: model_adjudicated`
- `evaluation_route: Route_B_model_adjudicated`
- `llm_prelabels_present`
- `llm_prelabel_count`
- `subagent_audit_present`
- `codex_adjudication_report_present`
- `model_adjudicated_labels_present`
- `model_adjudicated_label_count`
- `model_adjudicated_label_summary_present`
- `human_labels_present: false`
- `kappa_present: false`
- `human_human_kappa_established: false`
- `measurement_validated_allowed: false`

The package supports mapping input and output-directory input for:

- `llm_prelabels.jsonl`
- `subagent_audit_report.json`
- `model_adjudicated_labels.jsonl`
- `codex_adjudication_report.json`
- `model_adjudicated_label_summary.json`

## 4. Claim Boundary

Route B does not require human labels because it is explicitly not a
human-labeled measurement validation route. Route B also cannot claim
`measurement_validated` because it does not produce human labels or human-human
kappa.

Maximum Route B claim:

```text
model_adjudicated_pilot_only
```

or, when metric bridge evidence is stale or operational-only:

```text
operational_utility_only
```

Contamination failure forces:

```text
pilot_only
```

Missing bridge evidence produces:

```text
ambiguous
```

## 5. Denied Claims

Route B denies:

- `measurement_validated`;
- `human_labeled_validation`;
- `human_human_kappa_established`;
- `scientific_validation`;
- `scientific_validation_completed`;
- deployed V-information certification.

Model-adjudicated labels are not human labels. Codex adjudication is not human
review. LLM/Codex agreement is not human-human kappa.

## 6. Reason Codes Added

- `route_b_model_adjudicated`
- `model_adjudicated_labels_not_human_labels`
- `codex_adjudication_not_human_review`
- `human_labels_not_required_for_route_b`
- `human_labels_missing_for_measurement_validation`
- `human_kappa_missing_for_measurement_validation`
- `measurement_validated_denied_for_route_b`
- `model_adjudicated_pilot_only`
- `route_b_max_claim_boundary`
- `contamination_required_for_stronger_claim`
- `fresh_metric_bridge_required_for_stronger_claim`

Reason-code ordering is deterministic.

## 7. Validation Commands And Results

Commands:

```powershell
python -m compileall cps scripts
pytest tests/test_empirical_evidence_package.py -q
pytest tests/test_model_adjudicated_labels.py -q
pytest tests/test_llm_assisted_prelabels.py -q
pytest tests/test_prelabel_subagent_audit.py -q
pytest tests/test_human_label_kappa.py -q
pytest tests/test_contamination_audit.py -q
pytest tests/test_metric_bridge_gate.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Results:

| command | result |
| --- | --- |
| `python -m compileall cps scripts` | passed |
| `pytest tests/test_empirical_evidence_package.py -q` | 20 passed |
| `pytest tests/test_model_adjudicated_labels.py -q` | 10 passed |
| `pytest tests/test_llm_assisted_prelabels.py -q` | 16 passed |
| `pytest tests/test_prelabel_subagent_audit.py -q` | 12 passed |
| `pytest tests/test_human_label_kappa.py -q` | 14 passed |
| `pytest tests/test_contamination_audit.py -q` | 9 passed |
| `pytest tests/test_metric_bridge_gate.py -q` | 15 passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |

## 8. Known Limitations

- P36 does not run live APIs.
- P36 does not generate V4 Flash prelabels.
- P36 does not launch Codex subagents.
- P36 does not fabricate human labels or kappa.
- P36 does not close contamination or metric bridge gates.
- P36 does not sync to the original repo.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.

## 9. Next Recommended Phase

Recommended next phase:

```text
P37 Sync Empirical Readiness Package to Original Repo
```

This is preferred unless the operator provides live V4 Flash credentials and an
approved output root for:

```text
P37 Operator-Approved V4 Flash Prelabel Generation
```

## 10. Claim Boundary Restatement

- Route B does not require human labels.
- Route B cannot claim `measurement_validated`.
- Model-adjudicated labels are not human labels.
- Codex adjudication is not human review.
- No live API was run.
- No human labels were fabricated.
- No kappa was fabricated.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- No original repo sync was performed.
