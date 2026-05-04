# P39 Artifact Schema Freeze Review


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

Review whether replay-critical artifact schemas are stable, versioned, hashable, and conservative under missing fields.

## Schema Checklist

- [ ] `CandidatePool` schema exists and is versioned
- [ ] `ProjectionPlan` schema exists and is versioned
- [ ] `BudgetWitness` schema exists and is versioned
- [ ] `MaterializedContext` schema exists and is versioned
- [ ] `MetricBridgeWitness` schema exists and is versioned
- [ ] `ProjectionBundleV1` hash behavior is stable, if used

## Hash Checklist

- [ ] canonical JSON serialization
- [ ] sorted keys
- [ ] no local absolute paths in stable identity
- [ ] no secrets
- [ ] timestamps excluded from stable identity unless intended
- [ ] schema version included

## Missing-Field Downgrade Review

| Missing field | Expected downgrade | Tested? | Notes |
|---|---|---|---|
| candidate pool | `replay_unusable` | TBD | TBD |
| selected ids | `replay_unusable` | TBD | TBD |
| excluded ids | `replay_partial` or worse | TBD | TBD |
| materialization order | replay defect | TBD | TBD |
| metric bridge witness | `ambiguous` | TBD | TBD |
| utility records | `replay_partial` | TBD | TBD |

## Required Conclusion

State whether artifacts are ready for P40 Phase B replay.
