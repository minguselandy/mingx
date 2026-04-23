# Phase 1 Follow-Up Package

This package turns an approved drop list into a ready-to-run follow-up plan.

## Scope
- Source plan: `/home/mingxiaoyu/mingx/configs/runs/live-mini-batch.json`
- Decision sheet: `/home/mingxiaoyu/mingx/artifacts/phase1/live_mini_batch/exports/contamination_operator_decision_sheet.md`
- Dropped question count: `3`
- Current package semantics: generate a fresh reduced-scope follow-up batch without mutating the already completed failed run.

## Generated Files
- `followup_plan.json`: `/home/mingxiaoyu/mingx/artifacts/phase1/live_mini_batch_followup/followup_plan.json`
- `blocked_questions.json`: `/home/mingxiaoyu/mingx/artifacts/phase1/live_mini_batch_followup/blocked_questions.json`
- `calibration_manifest.json`: `/home/mingxiaoyu/mingx/artifacts/phase1/live_mini_batch_followup/calibration_manifest.json`
- `lineage.json`: human-auditable link between the failed run and the prepared follow-up batch.

## Execution
Run the normal cohort entrypoint against the generated plan:

`python -m cps.runtime.cohort --plan /home/mingxiaoyu/mingx/artifacts/phase1/live_mini_batch_followup/followup_plan.json --backend live --env .env`

## Reminder
- This package prepares a future batch.
- It does not clear the contamination gate for the source run.
- It does not rewrite the original question text.
- It keeps the replacement work in the sidecar / follow-up lane.