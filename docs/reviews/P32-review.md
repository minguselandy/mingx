# P32 V4 Flash Prelabels And Codex Subagent Audit Review

```yaml
phase_id: P32
phase_title: V4 Flash Prelabels And Codex Subagent Audit
document_type: implementation_review
branch: codex/p32-v4-flash-prelabels-subagent-audit
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

P32 adds deterministic LLM-assisted prelabel draft generation and Codex
subagent-audit preparation for the CPS empirical validation workflow.

DeepSeek V4 Flash is used only as a prelabel assistant. The outputs are
annotation drafts, not human labels. Codex subagent audit is audit evidence, not
human review.

## 2. Changed Files

- `cps/experiments/llm_assisted_prelabels.py`
- `cps/experiments/prelabel_subagent_audit.py`
- `tests/test_llm_assisted_prelabels.py`
- `tests/test_prelabel_subagent_audit.py`
- `docs/experiments/llm-assisted-prelabels.md`
- `docs/experiments/prelabel-subagent-audit.md`
- `docs/templates/llm-prelabel-manifest-template.json`
- `docs/templates/prelabel-subagent-audit-prompts.md`
- `docs/reviews/P32-review.md`

## 3. Prelabel Outputs Implemented

- `llm_prelabels.jsonl`
- `llm_prelabel_summary.json`
- `llm_prelabel_summary.md`

Every prelabel record preserves:

- `label_source = llm_assisted_prelabel`
- `judge_model_alias = deepseek_v4_flash`
- `not_human_label = true`
- `requires_human_confirmation = true`
- `measurement_validated_allowed = false`

P32 never writes LLM outputs as `human_labels.jsonl`.

## 4. Subagent Audit Outputs Implemented

- `subagent_audit_requests.jsonl`
- `subagent_audit_report.json`
- `subagent_audit_report.md`
- `human_review_queue.csv`
- `human_review_queue.jsonl`

Audit requests are generated for:

- `evidence_alignment_reviewer`
- `rubric_consistency_reviewer`
- `claim_boundary_reviewer`
- `uncertainty_reviewer`
- `cross_condition_consistency_reviewer`

The human review queue leaves `human_label`, `human_annotator_id`, and
`human_decision` blank.

## 5. Live Gates Implemented

Live V4 Flash prelabel generation fails closed unless:

- `CPS_ALLOW_LLM_PRELABEL=1`;
- manifest path exists;
- `mode = live_operator_approved`;
- `operator_approval = true`;
- `judge_model_alias = deepseek_v4_flash`;
- endpoint and model name are fixed and non-placeholder;
- input artifact root exists;
- `max_items` and `budget_cap` are fixed;
- `model_call_fn` is provided.

No provider SDK is imported. Tests use fake deterministic call boundaries only.

## 6. Denied Claims

- `measurement_validated` is not claimed.
- LLM prelabels are not human labels.
- Codex subagent audit is not human review.
- LLM-human agreement does not replace human-human kappa.
- High-quality prelabels alone are not scientific validation.
- Live API success alone is not measurement validation.
- Missing human labels deny `measurement_validated`.
- Missing kappa denies `measurement_validated`.

## 7. Known Limitations

- P32 does not run live APIs.
- P32 does not launch Codex subagents.
- P32 does not collect real human labels.
- P32 does not calculate kappa.
- P32 does not perform contamination audit.
- P32 does not close metric bridge freshness.
- P04 and P09 remain operator-required.

## 8. Validation Commands And Results

Commands:

```powershell
python -m compileall cps scripts
pytest tests/test_llm_assisted_prelabels.py -q
pytest tests/test_prelabel_subagent_audit.py -q
pytest tests/test_human_label_kappa.py -q
pytest tests/test_empirical_evidence_package.py -q
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Results:

| command | result |
| --- | --- |
| `python -m compileall cps scripts` | passed |
| `pytest tests/test_llm_assisted_prelabels.py -q` | 16 passed |
| `pytest tests/test_prelabel_subagent_audit.py -q` | 12 passed |
| `pytest tests/test_human_label_kappa.py -q` | 14 passed |
| `pytest tests/test_empirical_evidence_package.py -q` | 13 passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |

## 9. Next Recommended Phase

Next recommended phase:

```text
P33 Human Review of LLM Prelabels
```

P33 should remain explicit that human review must be performed by real human
annotators and that human-human kappa remains required before validation-level
claims.

## 10. Claim Boundary

- P32 does not generate human labels.
- P32 does not calculate kappa.
- P32 does not perform measurement validation.
- DeepSeek V4 Flash is a prelabel assistant, not a validation authority.
- Codex subagent audit is not human review.
- `measurement_validated` is not claimed.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- No original repo sync was performed.
