# P41 Route B Model-Adjudicated Evaluation Plan

**Milestone:** P41  
**Route:** fully automated model-adjudicated evaluation  
**Status:** implementation plan  
**Live API:** not required for initial dry-run; live calls require explicit approval  
**Maximum claim:** `model_adjudicated_pilot_only` or `operational_utility_only`


## Source Basis

This document is aligned to:

- `docs/archive/context_projection_revised_v10.md`
- `docs/paper-alignment-v10.md`
- `docs/experiment-design-overview.md`
- `docs/protocols/phase-b-replay-protocol.md`
- `docs/phase-tree-crosswalk.md`
- `docs/current-work-summary.md`
- `configs/runs/README.md`

Local execution status must always be verified from `git status`, run plans, `run_summary.json`, `events.jsonl`, and concrete artifacts. Paper text and roadmap documents are not run-completion evidence.


## 1. Purpose

P41 implements Route B: a fully automated model-adjudicated evaluation route that can produce operational pilot evidence without human labels.

Route B is useful because it reduces annotation workload and provides a scalable audit lane. It cannot claim `measurement_validated` because it does not provide human labels or human-human kappa.


## Claim Boundary Lock

This milestone is part of the Context Projection Selection measurement and runtime-audit scaffold. It must not be reported as deployed V-information certification, theorem inheritance for a heuristic pipeline, scheduler correctness, full system validation, or `measurement_validated` evidence.

Conservative claim rules:

- contamination failure => `pilot_only` and scientific-stop for measurement interpretation
- missing human labels => not `measurement_validated`
- missing human-human kappa => not `measurement_validated`
- stale or missing metric bridge => `operational_utility_only` or `ambiguous`
- synthetic-only evidence => `structural_synthetic_only`, not deployed V-information certification
- replay package completeness => replay/observability evidence only, not scientific validation
- model-adjudicated labels => not human labels
- Codex/model audit => not human review
- live API success alone => operational evidence only, not measurement validation


## 2. Route B Pipeline

```text
input cases and artifacts
  -> prelabel model generates dimension-level labels and rationales
  -> audit model or Codex subagent reviews label quality and failure cases
  -> adjudication model resolves conflicts or marks ambiguity
  -> model-adjudicated labels are written
  -> evidence package records non-human-label semantics
  -> claim gate enforces Route B maximum claim
```

## 3. Required Label Dimensions

Use the current human-label dimensions for structural compatibility, while preserving label source:

```text
answer_correctness
answer_completeness
answer_groundedness
context_sufficiency
missing_critical_context
irrelevant_context
misleading_context
conflict_or_stale_context
```

Each label record must include:

```text
case_id
run_id
dispatch_id
condition
label_dimension
model_label
model_rationale
label_source = model_adjudicated
prelabel_model_id
audit_model_id
adjudication_model_id
adjudication_status
confidence
ambiguity_reason
```

## 4. Non-Human-Label Fields

Every Route B evidence package must write:

```json
{
  "human_labels_present": false,
  "kappa_present": false,
  "human_human_kappa_established": false,
  "measurement_validated_allowed": false,
  "label_source": "model_adjudicated",
  "max_claim": "model_adjudicated_pilot_only"
}
```

## 5. Model Agreement Diagnostics

Route B may report model-model consistency, but it must not call it human-human kappa.

Allowed fields:

```text
model_model_agreement
model_adjudication_consistency
adjudication_disagreement_rate
high_disagreement_queue_size
ambiguity_rate
```

Denied fields unless human annotators are actually present:

```text
human_label
human_human_kappa
measurement_validated
```

## 6. Provider-Neutral Design

Do not hardcode provider names into `cps/runtime`. Model resolution should use API profile and role-model mapping. Route B should support dry-run/mock mode first.

Recommended roles:

```text
prelabel_model
audit_model
adjudication_model
coding_or_report_model, optional
```

## 7. Recommended Implementation Targets

```text
cps/experiments/model_prelabels.py
cps/experiments/subagent_audit.py
cps/experiments/model_adjudicated_labels.py
cps/experiments/route_b_evidence_package.py
cps/experiments/route_b_claim_gate.py
tests/test_route_b_claim_gate.py
tests/test_model_adjudicated_not_human_labels.py
tests/test_route_b_manifest_validation.py
tests/test_route_b_dry_run.py
```

## 8. Required Outputs

```text
model_prelabels.jsonl
model_prelabel_summary.json
model_prelabel_summary.md
subagent_audit_requests.jsonl
subagent_audit_report.json
subagent_audit_report.md
model_adjudicated_labels.jsonl
model_adjudicated_label_summary.json
model_adjudicated_label_summary.md
route_b_evidence_manifest.json
route_b_claim_gate_report.json
route_b_claim_gate_report.md
```

## 9. Validation

```bash
uv run python -m compileall cps scripts
uv run pytest tests/test_route_b_claim_gate.py -q
uv run pytest tests/test_model_adjudicated_not_human_labels.py -q
uv run pytest tests/test_route_b_manifest_validation.py -q
uv run pytest tests/test_route_b_dry_run.py -q
```

## 10. Acceptance Criteria

P41 is accepted when:

- dry-run Route B emits all required artifacts;
- claim gate blocks `measurement_validated`;
- model-adjudicated labels are never serialized as human labels;
- no human-human kappa is fabricated;
- ambiguity and disagreement are explicitly counted;
- output can be consumed by Phase B replay or a later empirical evidence package.
