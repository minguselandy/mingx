# Prelabel Subagent Audit

**Phase:** P32 V4 Flash LLM-Assisted Prelabels with Codex Subagent Audit

P32 prepares Codex reviewer/subagent audit requests for LLM-assisted prelabel
drafts. The audit layer checks schema validity, evidence alignment, rubric
consistency, uncertainty, cross-condition consistency, and claim-boundary safety.

Codex subagent audit is not human review. It cannot create human labels, final
labels, kappa evidence, or `measurement_validated` evidence.

## Audit Roles

- `evidence_alignment_reviewer`
- `rubric_consistency_reviewer`
- `claim_boundary_reviewer`
- `uncertainty_reviewer`
- `cross_condition_consistency_reviewer`

Each request states:

- `not_human_review = true`
- `measurement_validated_allowed = false`

Audit prompts are stored in:

```text
docs/templates/prelabel-subagent-audit-prompts.md
```

## Outputs

The audit layer emits:

- `subagent_audit_requests.jsonl`
- `subagent_audit_report.json`
- `subagent_audit_report.md`
- `human_review_queue.csv`
- `human_review_queue.jsonl`

If no audit results are supplied, the report remains pending and all drafts enter
the human review queue. This does not fabricate subagent verdicts.

## Human Review Queue

The queue is a worklist for real annotators. It includes LLM suggestions,
rationale, evidence refs, and audit status, but leaves these fields blank:

- `human_label`
- `human_annotator_id`
- `human_decision`

Human annotators must accept, modify, reject, or adjudicate suggestions in a
separate process. Disagreements must not be silently overwritten.

## Claim Boundary

Prelabels and subagent audits can reduce annotation workload, but they do not
weaken the claim gate. Human labels, human-human kappa, contamination audit,
fresh metric bridge evidence, and claim gate allow remain required before any
validation-level claim can be considered.

P04 remains deferred/operator-required. P09 remains
`BLOCKED_OPERATOR_REQUIRED`. `measurement_validated` is not claimed.
