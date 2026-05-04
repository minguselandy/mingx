# P42 Follow-Up Live Batch Decision Review


## Verdict

- Verdict: `PENDING_REVIEW`
- Reviewer:
- Date:
- Branch:
- Commit range:

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

Review whether a fresh replacement-based reduced-scope live follow-up batch is ready, executed, or rejected.

## Decision

- Decision: `DO_NOT_RUN` / `DRY_RUN_ONLY` / `RUN_APPROVED` / `RUN_COMPLETED` / `RUN_REJECTED`
- Operator approval evidence:
- Approved output root:
- Approved API profile:
- Approved case ids:

## Pre-Live Checklist

- [ ] P37 state lock complete
- [ ] failed prior batch preserved
- [ ] replacement manifest present
- [ ] replacement ids match plan
- [ ] API profile verified
- [ ] non-live tests passed
- [ ] output root is fresh
- [ ] budget/scope approved

## Replacement Cases

| Case id | Included? | Lineage evidence | Notes |
|---|---|---|---|
| `2hop__132929_684936` | TBD | TBD | TBD |
| `3hop1__409517_547811_80702` | TBD | TBD | TBD |
| `4hop3__373866_5189_38229_86687` | TBD | TBD | TBD |

## Post-Run Checklist, If Executed

- [ ] run summary exists
- [ ] `events.jsonl` exists
- [ ] resolved runtime recorded
- [ ] contamination report exists
- [ ] claim gate report exists
- [ ] run status is not inflated
- [ ] no `measurement_validated` claim from live success alone

## Required Conclusion

State whether the batch remains `pilot_only`, is blocked by contamination, or can be used only as operational evidence.
