# P27 Human Label And Kappa Artifact Review

```yaml
phase_id: P27
phase_title: Human Label and Kappa Artifact Protocol Implementation
document_type: implementation_review
branch: codex/p27-human-label-kappa-artifacts
measurement_validated_claimed: false
p04_status: deferred/operator-required
p09_status: BLOCKED_OPERATOR_REQUIRED
live_api_run: false
labels_fabricated: false
kappa_fabricated: false
empirical_validation_completed: false
source_manuscript_changed: false
original_repo_synced: false
```

## 1. Phase Summary

P27 adds deterministic human-label artifact schemas, empty annotation templates,
label completeness checks, Cohen's kappa calculation, kappa threshold mapping,
and kappa report writers for future EV3 human-labeled measurement validation.

P27 does not run live APIs, fabricate human labels, fabricate kappa, perform
empirical validation, unblock P04/P09, or claim `measurement_validated`.

## 2. Changed Files

- `cps/experiments/human_label_kappa.py`
- `tests/test_human_label_kappa.py`
- `docs/experiments/human-label-kappa-artifacts.md`
- `docs/reviews/P27-review.md`

## 3. Schema Implemented

The label schema includes:

- `answer_correctness`
- `answer_completeness`
- `answer_groundedness`
- `context_sufficiency`
- `missing_critical_context`
- `irrelevant_context`
- `misleading_context`
- `conflict_or_stale_context`

Allowed label values are `0 = fail`, `1 = partial`, and `2 = pass`.

## 4. Completeness Checks Implemented

The completeness report includes:

- required and observed case counts;
- required and observed annotator counts;
- required dimensions;
- missing cases;
- missing annotators;
- missing dimensions;
- duplicate label entries;
- label value errors;
- `labels_complete`;
- stable reason codes.

The checker fails closed on missing labels, invalid values, duplicate entries,
and fewer than two annotators.

## 5. Kappa Calculation Implemented

P27 implements deterministic Cohen's kappa without external dependencies. It:

- aligns items by `case_id` and `condition`;
- computes per-dimension kappa;
- computes macro-average kappa;
- reports item counts per dimension;
- handles more than two annotators with deterministic pairwise average kappa;
- emits stable JSON and Markdown reports.

## 6. Kappa Threshold Mapping

| Threshold | Status | Claim effect |
| --- | --- | --- |
| missing | `kappa_missing` | `measurement_validated_allowed: false` |
| `< 0.40` | `pilot_only` | Low agreement; pilot-only evidence. |
| `0.40 <= kappa < 0.60` | `weak_evidence_not_measurement_validated` | Weak evidence; validation denied. |
| `0.60 <= kappa < 0.75` | `limited_measurement_review_candidate` | Candidate only if other gates later pass. |
| `>= 0.75` | `stronger_measurement_review_candidate` | Stronger candidate only; not validation by itself. |

High kappa alone does not allow `measurement_validated`.

## 7. Denied Claims

- `measurement_validated` is not claimed.
- Scientific validation is not claimed.
- Kappa alone is not scientific validation.
- Human labels alone are not measurement validation.
- High kappa alone does not certify deployed V-information behavior.
- Missing contamination audit blocks validation-level interpretation.
- Missing or stale metric bridge blocks validation-level interpretation.

## 8. Known Limitations

- P27 does not collect labels.
- P27 does not adjudicate real disagreements.
- P27 does not run live APIs.
- P27 does not perform contamination audit.
- P27 does not close metric bridge freshness.
- P27 does not integrate final label/kappa summaries into P26 live packages.
- P04 and P09 remain operator-required.

## 9. Validation Commands And Results

Commands:

```powershell
python -m compileall cps scripts
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
| `pytest tests/test_human_label_kappa.py -q` | 14 passed |
| `pytest tests/test_controlled_live_pilot.py -q` | 14 passed |
| `pytest tests/test_claim_gate_report.py -q` | 11 passed |
| `pytest tests/test_metric_bridge_gate.py -q` | 15 passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |

## 10. Next Recommended Phase

Next recommended phase:

```text
P28 Contamination and Live Evidence Package Integration
```

P28 should integrate contamination artifacts and P26/P27 summaries into a
conservative live evidence package without treating pilot completion or kappa as
measurement validation.

## 11. Claim Boundary

- P27 prepares human-label and kappa artifacts only.
- P27 does not fabricate labels.
- P27 does not fabricate kappa.
- P27 does not perform empirical validation.
- High kappa alone is not measurement validation.
- Contamination audit and fresh metric bridge remain required.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- `measurement_validated` is not claimed.
- No original repo sync was performed.
