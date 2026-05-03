# Model-Adjudicated Labels

**Phase:** P34 Codex Model-Adjudicated Labels

P34 allows Codex to adjudicate DeepSeek V4 Flash prelabels and Codex subagent
audit outputs into model-adjudicated annotation records. This replaces the
planned human-confirmation step with model adjudication only for pilot evidence.

The outputs are not human labels.

## Why This Mode Exists

Model adjudication can consolidate:

- V4 Flash suggested labels;
- confidence values;
- evidence references;
- uncertainty notes;
- Codex subagent verdicts;
- Codex subagent issues.

This gives the project a deterministic model-adjudicated evidence layer for
pilot analysis and annotation-workload reduction studies.

## Outputs

P34 emits:

- `model_adjudicated_labels.jsonl`
- `codex_adjudication_report.json`
- `codex_adjudication_report.md`
- `model_adjudicated_label_summary.json`
- `model_adjudicated_label_summary.md`

Forbidden output names are never used:

- `human_labels.jsonl`
- `human_validated_labels.jsonl`
- `measurement_labels.jsonl`
- `final_human_labels.jsonl`

## Adjudication Policy

The adjudicator is deterministic:

- `REJECT_DRAFT` creates `rejected_draft_model_adjudicated`;
- `REQUEST_HUMAN_PRIORITY` creates `high_uncertainty`;
- `confidence_milli < 500` creates `high_uncertainty`;
- blocking issues create `model_adjudicated_with_blocking_warning`;
- high-confidence drafts with no issues become `model_adjudicated_label`.

Evidence references and uncertainty notes are preserved in each record.

## Claim Boundary

Codex adjudication is not human review. Codex-adjudicated labels are not human
labels. Codex agreement is not human-human kappa.

Model-adjudicated evidence cannot claim:

- `human_labeled_validation`;
- `measurement_validated`;
- `scientific_validation_completed`.

Allowed cautious wording:

- `model_adjudicated_pilot_only`;
- `operational_utility_only`;
- `annotation_workload_reduction_evidence`.

Human labels, human-human kappa, contamination audit, fresh metric bridge, and
claim gate approval remain required for any future validation-level claim.

P04 remains deferred/operator-required. P09 remains
`BLOCKED_OPERATOR_REQUIRED`.
