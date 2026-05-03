# LLM-Assisted Prelabels

**Phase:** P32 V4 Flash LLM-Assisted Prelabels with Codex Subagent Audit

P32 adds a guarded workflow for producing annotation drafts from DeepSeek V4
Flash. These drafts are written as `llm_prelabels.jsonl`; they are never written
as `human_labels.jsonl`.

## What Prelabels Are

LLM-assisted prelabels are model-assisted annotation drafts. They may reduce
human annotation workload by proposing rubric-aligned labels, rationale, evidence
references, and uncertainty notes.

Every prelabel record states:

- `label_source = llm_assisted_prelabel`
- `judge_model_alias = deepseek_v4_flash`
- `not_human_label = true`
- `requires_human_confirmation = true`
- `subagent_audit_is_not_human_label = true`
- `measurement_validated_allowed = false`

## What Prelabels Are Not

LLM prelabels are not:

- human labels;
- final labels;
- validated labels;
- measurement labels;
- human-validated labels;
- substitutes for human-human kappa.

DeepSeek V4 Flash is a prelabel assistant, not a validation authority. High
quality prelabels alone are not scientific validation.

## Live Gate

Default mode is `dry_run`. Live DeepSeek V4 Flash prelabel generation is allowed
only when:

- `CPS_ALLOW_LLM_PRELABEL=1`;
- a manifest path exists;
- `mode = live_operator_approved`;
- `operator_approval = true`;
- `judge_model_alias = deepseek_v4_flash`;
- endpoint and model name are fixed and non-placeholder;
- input artifact root exists;
- output root is operator-approved;
- `max_items` and `budget_cap` are fixed;
- credentials are provided outside the repository.

If any gate is missing, the workflow fails closed before any model call.

## Outputs

The prelabel builder emits:

- `llm_prelabels.jsonl`
- `llm_prelabel_summary.json`
- `llm_prelabel_summary.md`

The summary denies `measurement_validated` and lists the next required evidence:
human annotation, human-human kappa, contamination audit, metric bridge freshness
review, and claim gate decision.

## Claim Boundary

Missing human labels still deny `measurement_validated`. Missing kappa still
denies `measurement_validated`. LLM-human agreement does not replace human-human
kappa. Live API success alone is not measurement validation. P04 remains
deferred/operator-required. P09 remains `BLOCKED_OPERATOR_REQUIRED`.
