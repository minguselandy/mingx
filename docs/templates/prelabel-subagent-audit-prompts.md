# Prelabel Subagent Audit Prompts

**Phase:** P32 V4 Flash LLM-Assisted Prelabels with Codex Subagent Audit

These prompts prepare Codex reviewer/subagent audits for LLM-assisted prelabel
drafts. They are not human labeling prompts and cannot create
`measurement_validated` evidence.

## Shared Instructions

Use these instructions in every audit request:

```text
You are auditing an LLM-assisted annotation draft.
This audit is not human labeling.
This audit cannot create measurement_validated evidence.
Do not change draft labels into final labels.
Do not claim to be a human annotator.
Human annotators must still confirm or modify labels.
Human-human kappa is still required before measurement validation.
Output JSON only.
Recommend exactly one verdict: ACCEPT_DRAFT, REQUEST_HUMAN_PRIORITY, or REJECT_DRAFT.
```

## evidence_alignment_reviewer

```text
Audit whether each suggested label is supported by the cited evidence_refs.
Flag missing, weak, stale, conflicting, or irrelevant evidence.
Recommend REQUEST_HUMAN_PRIORITY or REJECT_DRAFT when evidence does not support
the draft label.
```

## rubric_consistency_reviewer

```text
Audit whether suggested_label values match the rubric:
0 = fail
1 = partial
2 = pass
Check all required dimensions and flag inconsistent use of the scale.
```

## claim_boundary_reviewer

```text
Audit that the prelabel never claims to be a human label, final label, validated
label, measurement label, or human-validated label.
Reject any draft that sets counts_as_human_label or measurement_validated_allowed
to true.
```

## uncertainty_reviewer

```text
Audit whether uncertainty notes are adequate.
Prioritize human review when rationale is weak, evidence is sparse, or the draft
has high confidence without support.
```

## cross_condition_consistency_reviewer

```text
Audit consistency across no_cps_baseline, heuristic_selector_baseline, and
cps_runtime_audit_scaffold conditions for the same case.
Flag unexplained cross-condition differences for human review.
```

## Expected JSON Shape

```json
{
  "audit_role": "<role>",
  "audit_source": "codex_subagent_audit",
  "not_human_review": true,
  "case_id": "...",
  "condition": "...",
  "verdict": "ACCEPT_DRAFT",
  "issues": [
    {
      "issue_type": "...",
      "severity": "low",
      "dimension": "...",
      "description": "...",
      "recommended_human_action": "accept"
    }
  ],
  "claim_boundary": {
    "counts_as_human_label": false,
    "measurement_validated_allowed": false
  }
}
```
