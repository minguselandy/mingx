# Human Review Sheet Workflow

**Phase:** P33 Human Review Sheet Workflow for LLM Prelabels

P33 converts P32 LLM-assisted prelabels and Codex subagent audit outputs into a
human-review packet. The packet is a worklist for real annotators. It is not
human labeling completion and does not claim `measurement_validated`.

## Inputs

The packet builder consumes:

- `llm_assisted_prelabel` records from `llm_prelabels.jsonl`;
- optional Codex subagent audit outputs;
- a stable `run_id`.

LLM suggestions are optional aids. Codex subagent audit is also an optional aid.
Neither source counts as human review.

## Outputs

The packet builder emits:

- `human_review_packet_manifest.json`
- `human_review_sheet.csv`
- `human_review_sheet.jsonl`
- `human_review_instructions.md`
- `human_review_packet_summary.json`
- `human_review_packet_summary.md`

Generated sheets leave these fields blank:

- `human_label`
- `human_rationale`
- `human_annotator_id`
- `human_decision`

P33 must not pre-fill those fields.

## Review Priority

Review priority is deterministic:

- `high` if a subagent verdict is `REJECT_DRAFT`;
- `high` if any blocking or high issue exists;
- `high` if `confidence_milli < 500`;
- `medium` if a verdict is `REQUEST_HUMAN_PRIORITY`;
- `medium` if `confidence_milli < 750`;
- `low` otherwise.

No randomness, timestamps, UUIDs, network calls, or external SDKs are used.

## Human Submission Validation

Completed sheets fail closed if:

- `human_annotator_id` is missing;
- `human_label` is missing;
- `human_label` is not `0`, `1`, or `2`;
- `human_decision` is not `accept`, `modify`, `reject`, or `unclear`;
- required dimensions are missing;
- duplicate annotator/case/condition/dimension entries are present;
- LLM prelabel rows are mistaken for human labels;
- Codex audit is used as an annotator.

Human labels are only created after human submission validation passes.

## Conversion Boundary

Validated rows may be converted into `human_labels.jsonl`-compatible candidate
records with:

```text
label_source = human_annotator
```

The conversion does not write `human_labels.jsonl` automatically. The default
safe target is `human_labels_candidate.jsonl` when an explicit output path is
provided.

Conversion never includes `label_source = llm_assisted_prelabel` and never uses
Codex audit as an annotator.

## Claim Boundary

P33 does not fabricate human labels, compute kappa, or perform empirical
validation. Kappa requires at least two real human annotators in a later phase.

`measurement_validated` remains denied until human labels, human-human kappa,
contamination audit, metric bridge freshness, and claim gate allow all pass.

P04 remains deferred/operator-required. P09 remains
`BLOCKED_OPERATOR_REQUIRED`.
