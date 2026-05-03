# P33 Human Review Sheet Workflow Review

```yaml
phase_id: P33
phase_title: Human Review Sheet Workflow for LLM Prelabels
document_type: implementation_review
branch: codex/p33-human-review-sheet-workflow
measurement_validated_claimed: false
p04_status: deferred/operator-required
p09_status: BLOCKED_OPERATOR_REQUIRED
live_api_run: false
external_sdk_imported: false
human_labels_fabricated: false
kappa_fabricated: false
codex_subagent_audit_treated_as_human_review: false
source_manuscript_changed: false
original_repo_synced: false
```

## 1. Phase Summary

P33 adds a deterministic human-review packet workflow for P32 LLM-assisted
prelabels. It creates review sheets, instructions, packet summaries, validation
reports, and a guarded conversion path for validated human-reviewed rows.

P33 does not fabricate human labels, auto-accept LLM prelabels, treat Codex audit
as human review, compute kappa, run live APIs, or claim `measurement_validated`.

## 2. Changed Files

- `cps/experiments/human_review_workflow.py`
- `tests/test_human_review_workflow.py`
- `docs/experiments/human-review-sheet-workflow.md`
- `docs/templates/human-review-instructions.md`
- `docs/reviews/P33-review.md`

## 3. Human Review Packet Outputs

- `human_review_packet_manifest.json`
- `human_review_sheet.csv`
- `human_review_sheet.jsonl`
- `human_review_instructions.md`
- `human_review_packet_summary.json`
- `human_review_packet_summary.md`

Generated sheets leave `human_label`, `human_rationale`,
`human_annotator_id`, and `human_decision` blank.

## 4. Validation Rules

The validator fails closed for:

- missing `human_annotator_id`;
- missing `human_label`;
- invalid `human_label`;
- invalid `human_decision`;
- missing required dimensions;
- duplicate annotator/case/condition/dimension entries;
- LLM prelabel rows mistaken for human labels;
- Codex audit identifiers used as annotators.

## 5. Conversion Rules

Conversion is allowed only after human submission validation passes. Converted
records use:

```text
label_source = human_annotator
```

The conversion does not write `human_labels.jsonl` automatically. P33 uses
candidate output only when explicitly requested and rejects automatic
`human_labels.jsonl` writes.

## 6. Denied Claims

- `measurement_validated` is not claimed.
- LLM prelabels are not human labels.
- Codex subagent audit is not human review.
- Human review packet generation is not human labeling completion.
- Kappa is not computed.
- High-quality prelabels alone are not validation.
- Single-annotator review is not kappa evidence.

## 7. Known Limitations

- P33 does not collect real annotations.
- P33 does not require two annotators by itself.
- P33 does not compute kappa.
- P33 does not run contamination audit.
- P33 does not close metric bridge freshness.
- P04 and P09 remain operator-required.

## 8. Validation Commands And Results

Commands:

```powershell
python -m compileall cps scripts
pytest tests/test_human_review_workflow.py -q
pytest tests/test_llm_assisted_prelabels.py -q
pytest tests/test_prelabel_subagent_audit.py -q
pytest tests/test_human_label_kappa.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Results:

| command | result |
| --- | --- |
| `python -m compileall cps scripts` | passed |
| `pytest tests/test_human_review_workflow.py -q` | 15 passed |
| `pytest tests/test_llm_assisted_prelabels.py -q` | 16 passed |
| `pytest tests/test_prelabel_subagent_audit.py -q` | 12 passed |
| `pytest tests/test_human_label_kappa.py -q` | 14 passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |

## 9. Next Recommended Phase

Next recommended phase:

```text
P34 Human Annotation Collection
```

Alternative path, if explicitly approved by the operator:

```text
P34 Flash-Only Live Pilot Execution
```

Either path must preserve that P33 did not fabricate labels or kappa and did not
claim `measurement_validated`.

## 10. Claim Boundary

- P33 is a human review sheet workflow only.
- P33 does not fabricate human labels.
- P33 does not fabricate kappa.
- Prelabels remain non-human labels.
- Codex audit remains non-human review.
- `measurement_validated` is not claimed.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- No original repo sync was performed.
