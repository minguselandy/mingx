# Human Review Instructions

Use this document with P33 human review packets.

## Reviewer Role

You are a human annotator reviewing CPS empirical validation cases. LLM
suggestions are optional aids. Codex subagent audit findings are optional aids.
You must independently confirm, modify, reject, or mark each proposed label as
unclear.

Do not treat LLM prelabels as human labels. Do not treat Codex subagent audit as
human review.

## Label Scale

- `0` = fail
- `1` = partial
- `2` = pass

## Required Decisions

For every row, fill:

- `human_label`
- `human_rationale`
- `human_annotator_id`
- `human_decision`

Allowed `human_decision` values:

- `accept`
- `modify`
- `reject`
- `unclear`

If you accept the LLM suggestion, still provide your annotator id and rationale.
Do not leave `human_decision` blank.

## Required Dimensions

- `answer_correctness`
- `answer_completeness`
- `answer_groundedness`
- `context_sufficiency`
- `missing_critical_context`
- `irrelevant_context`
- `misleading_context`
- `conflict_or_stale_context`

## Claim Boundary

Human review sheet completion is required before kappa, but it is not sufficient
for `measurement_validated`. At least two human annotators, human-human kappa,
contamination audit, metric bridge freshness, and claim gate allow remain
required.

Do not report LLM suggestions, Codex audit, or single-annotator review as
scientific validation.
