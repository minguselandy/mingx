# P41 Route B Model-Adjudicated Evaluation Review


## Verdict

- Verdict: `PENDING_REVIEW`
- Reviewer: Codex no-git automation
- Date: 2026-05-05
- Branch: no-git direct development; current working tree only
- Commit range: none; operator will commit manually after DEV phases

Allowed verdicts:

- `ACCEPT`
- `ACCEPT_WITH_MINOR_REVISIONS`
- `ACCEPT_WITH_MAJOR_REVISIONS`
- `REJECT_UNSAFE_OVERCLAIM`
- `REJECT_INCOMPLETE_ARTIFACTS`
- `PENDING_REVIEW`

## Claim Boundary Review

Confirm:

- [ ] no live API was run unless the milestone explicitly allowed it and approval was recorded
- [ ] no human labels were fabricated
- [ ] no human-human kappa was fabricated
- [ ] no `measurement_validated` claim was made unless all required gates were satisfied
- [ ] synthetic evidence was not described as deployed V-information certification
- [ ] replay evidence was not described as scientific validation
- [ ] Route B/model-adjudicated labels were not described as human labels
- [ ] contamination failures, if present, caused `pilot_only` / scientific-stop interpretation


## Scope

Review whether Route B produces fully automated model-adjudicated pilot evidence while preserving non-human-label semantics.

## Implementation Summary

P41 adds `cps/experiments/route_b_evidence_package.py` and
`tests/test_route_b_evidence_package.py`.

The route package:

- builds a dry-run Route B artifact package without live API calls;
- writes `model_prelabels.*` aliases while preserving existing `llm_prelabels.*`
  outputs;
- consumes subagent audit reports, model-adjudicated labels, adjudication
  summaries, empirical evidence package state, and optional replay package
  manifests;
- enforces `human_labels_present = false`, `kappa_present = false`,
  `human_human_kappa_established = false`, and
  `measurement_validated_allowed = false`;
- downgrades contamination failure to `pilot_only`;
- caps Route B at `model_adjudicated_pilot_only` or
  `operational_utility_only`.

## Artifact Checklist

- [x] `model_prelabels.jsonl`
- [x] `model_prelabel_summary.json`
- [x] `model_prelabel_summary.md`
- [x] `subagent_audit_requests.jsonl`
- [x] `subagent_audit_report.json`
- [x] `subagent_audit_report.md`
- [x] `model_adjudicated_labels.jsonl`
- [x] `model_adjudicated_label_summary.json`
- [x] `model_adjudicated_label_summary.md`
- [x] `route_b_evidence_manifest.json`
- [x] `route_b_claim_gate_report.json`
- [x] `route_b_claim_gate_report.md`

## Non-Human-Label Checklist

- [x] `human_labels_present = false`
- [x] `kappa_present = false`
- [x] `human_human_kappa_established = false`
- [x] `measurement_validated_allowed = false`
- [x] `label_source = model_adjudicated`
- [x] max claim is `model_adjudicated_pilot_only` or `operational_utility_only`

## Agreement Diagnostics

| Field | Present? | Interpreted correctly? | Notes |
|---|---|---|---|
| `model_model_agreement` | Yes | Yes | Reported only when comparable model/prelabel dimensions exist. |
| `model_adjudication_consistency` | Yes | Yes | Model-adjudication diagnostic only; not human agreement. |
| `adjudication_disagreement_rate` | Yes | Yes | Counts uncertain/rejected/blocking model adjudication rows. |
| ambiguity rate | Yes | Yes | Counts uncertain model adjudication rows. |

## Validation

```text
python -m compileall cps scripts
passed

uv run pytest tests/test_route_b_evidence_package.py tests/test_empirical_evidence_package.py tests/test_model_adjudicated_labels.py tests/test_replay_evidence_package.py -q
46 passed

uv run pytest -q
blocked during collection before P41 tests ran:
ImportError: DLL load failed while importing _multiarray_umath: Access denied.
```

The full-suite block is local to the `.venv` NumPy C-extension import path. The
focused P41 and adjacent evidence-package tests passed.

## Required Conclusion

Route B implementation can produce model-adjudicated pilot or operational utility
evidence without violating the paper's claim gate in the focused test surface.
The automation phase is not marked complete because the required full-suite
`uv run pytest -q` command is blocked by the local NumPy import failure.
