# Contamination Operator Decision Sheet

- Run: `phase1-cohort-20260423033750`
- Scope: `pilot_reduced_scope`
- Gate status: `fail`
- Default repository action: `stop_and_escalate`
- Upstream packet: `contamination_review_packet.md`
- Upstream memo: `contamination_triage_memo.md`
- Replacement manifest: `../replacement_manifest.json`
- Replacement note: `replacement_plan.md`

## Use Of This Sheet

This sheet is for human approval and lineage tracking after contamination fail.

It does not:

- clear the gate automatically
- authorize an automatic rerun
- upgrade this run to `measurement_validated`

## Run-Level Decision

- Current recommendation: `stop_and_escalate`
- Current scientific interpretation status: `not allowed`
- Rerun before human signoff: `no`
- Suggested next batch action: `replace all 3 items`

## Question Decisions

| question_id | recommended action | operator decision | status | rationale | rerun precondition |
| --- | --- | --- | --- | --- | --- |
| `2hop__86458_20273` | `drop_and_replace` | `[pending]` | `pending_signoff` | Strongly recoverable from public prior knowledge; not worth rewrite budget. | Replace question and record lineage. |
| `3hop1__222979_40769_64047` | `drop_and_replace` | `[pending]` | `pending_signoff` | A controlled rewrite attempt was reprobed live and still failed the contamination threshold. | Replace question and record failed rewrite lineage. |
| `4hop1__76111_624859_355213_203322` | `drop_and_replace` | `[pending]` | `pending_signoff` | Likely entity-collision / data-quality issue; not a clean rewrite target. | Replace question and flag upstream review. |

## Human Approval Block

- Scientific owner: `[pending]`
- Runtime owner: `[pending]`
- Decision timestamp: `[pending]`
- Approved follow-up action: `[pending]`

## Allowed Follow-Up Actions

Choose exactly one run-level path after signoff:

1. `replace_only`
   Replace the dropped questions and record any failed rewrite attempts as lineage-only artifacts.
2. `replace_plus_one_rewrite_probe`
   Deprecated for the current batch because the approved rewrite candidate already failed live reprobe.
3. `return_to_phase0_revision`
   Use if the team decides the contamination pattern is structural rather than item-local.

## Required Lineage Notes

If a rewrite attempt was evaluated, record:

- original `question_id`
- original question text
- approved rewritten text
- approving human
- date
- reason for rewrite
- fresh reprobe result
- whether the rewritten item remains in scope for a future run
- if rejected, the measured reprobe result

If `drop_and_replace` is approved, record:

- dropped `question_id`
- reason dropped
- replacement `question_id`
- hop depth preserved: `yes/no`

## Current Recommended Fill

- `2hop__86458_20273 -> drop_and_replace`
- `3hop1__222979_40769_64047 -> drop_and_replace`
- `4hop1__76111_624859_355213_203322 -> drop_and_replace`
- Run-level path: `replace_only`

## Reminder

This sheet is intentionally conservative.

The goal is to move from contamination fail to a human-audited next action, not
to turn a reduced-scope blocked run into an implied scientific pass.
