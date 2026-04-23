# Phase 1 Live Mini-Batch Report

This document records the completed reduced-scope live run executed with the
current Phase 1 runtime overrides.

## Run Summary

- Run ID: `phase1-cohort-20260423033750`
- Run plan: `configs/runs/live-mini-batch.json`
- Scope mode: `pilot_reduced_scope`
- Backend: `live`
- Runtime model overrides:
  - `small = qwen3.6-flash`
  - `frontier = qwen3.6-plus`
- Final pipeline status: `awaiting_annotation`
- Final measurement status: `pilot_only`

This run should be treated as an engineering/pilot result, not as a
measurement-validated Phase 1 scientific result.

## What Completed Successfully

- The live runner completed all planned scoring units for both roles.
- `small` completed `3 / 3` planned questions.
- `frontier` completed `3 / 3` planned questions.
- The live path produced non-degenerate token logprobs and non-zero
  `baseline_logp` / `full_logp` / `delta_loo` values.
- Bridge analysis completed with:
  - `bridge_status = computed`
  - `bridge_form = linear_ols`
  - `pass_fail = pass`
- The annotation package was generated successfully.
- No `blocked_questions.json` artifact was produced in this mini-batch run,
  so no provider-block replacement was required for the selected three-question
  set.

## Run Size

- Planned question count:
  - `small = 3`
  - `frontier = 3`
- Estimated runner API calls:
  - `small = 93`
  - `frontier = 93`
  - `total = 186`

The selected calibration questions were:

- `2hop__86458_20273`
- `3hop1__222979_40769_64047`
- `4hop1__76111_624859_355213_203322`

## Scientific Gate Outcome

The contamination diagnostic failed.

- `gate_decision = fail`
- `above_threshold_count = 3`
- `question_count = 3`
- `above_threshold_fraction = 1.0`

Questions above threshold:

- `2hop__86458_20273`
- `3hop1__222979_40769_64047`
- `4hop1__76111_624859_355213_203322`

This is a scientific stop condition, not an engineering fault. The run
therefore cannot be interpreted as a validated measurement result.

## Annotation State

- Annotation status: `awaiting_labels`
- Annotation queue size: `10`
- Flagged items: `9`
- Face-validity items: `1`
- Kappa status: `awaiting_annotation`

The annotation package is ready, but no human labels have been ingested yet.

## Key Artifacts

- [run_summary.json](../artifacts/phase1/live_mini_batch/exports/run_summary.json)
- [contamination_diagnostics.json](../artifacts/phase1/live_mini_batch/exports/contamination_diagnostics.json)
- [contamination_escalation_bundle.json](../artifacts/phase1/live_mini_batch/exports/contamination_escalation_bundle.json)
- [bridge_diagnostics.json](../artifacts/phase1/live_mini_batch/exports/bridge_diagnostics.json)
- [annotation_manifest.json](../artifacts/phase1/live_mini_batch/exports/annotations/annotation_manifest.json)
- [annotation_queue.csv](../artifacts/phase1/live_mini_batch/exports/annotations/annotation_queue.csv)
- [annotation_status.json](../artifacts/phase1/live_mini_batch/exports/annotations/annotation_status.json)
- [events.jsonl](../artifacts/phase1/live_mini_batch/measurements/events.jsonl)

## Interpretation

- Engineering status: successful reduced-scope live execution
- Scientific status: contamination gate failed
- Reporting status: do not describe this run as `measurement_validated`
- Operational status: the current model pair (`qwen3.6-flash` /
  `qwen3.6-plus`) is viable for live Phase 1 plumbing and reduced-scope pilot
  execution

## Recommended Next Step

Use the contamination escalation bundle as the decision packet for the next
step. The available paths are:

- restrict to an uncontaminated subset if a meaningful effective sample remains
- perform an independent rerun only if manually justified
- escalate back to Phase 0 revision if contamination invalidates the intended
  interpretation
