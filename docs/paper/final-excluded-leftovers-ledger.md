# Final Excluded Leftovers Ledger

Status: PAPER-REV-6 category-only ledger
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This ledger records excluded leftovers by category only. It intentionally omits individual leftover file names and paths. The categories below are not submission evidence, are not staged by this goal, and are not used to upgrade claims.

## Category-Only Ledger

| category | treatment | submission boundary |
|---|---|---|
| Beta leftovers | excluded | not submission evidence |
| Route4D leftovers | excluded | not submission evidence |
| Route6C leftovers | excluded | not submission evidence |
| WS0 / WS1 leftovers | excluded | not submission evidence |
| Teacher-forced backend leftovers | excluded | not submission evidence |
| EPF WS6 nested ledger leftovers | excluded | not submission evidence |
| Old goal packs | excluded | not submission evidence |
| Unrelated historical leftovers | excluded | not submission evidence |
| Codex local goal / automation state | excluded | local control state only |
| Operator-input material | excluded | operator-controlled material only |
| Raw API dump locations | excluded | not used; raw responses remain unstored in the submission package |
| Raw dataset mirrors | excluded | not submission evidence |

## Rules

- Do not stage excluded leftovers.
- Do not delete excluded leftovers during paper-revision goals.
- Do not cite excluded leftovers as evidence.
- Do not use excluded leftovers to claim fixed-target teacher-forced NLL, fixed-target continuation scoring, metric bridge support, calibrated proxy support, V-information proxy support, measurement validation, human/external gold validation, paper-grade evidence, selector superiority, Route 5 unlock, or Route 8 unlock.

## Boundary Summary

- Claim level: `operational_utility_only/no_claim_upgrade`.
- Route 5: locked.
- Route 8: locked.
- Raw API responses stored: false.
- Evidence artifacts changed by this ledger: false.
