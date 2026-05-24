# PAPER-REV-3 Methods Backend Artifact Review

Status: complete
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Scope

PAPER-REV-3 polishes Methods so the backend capability boundary,
ProjectionBundleV1 audit interface, ClaimLedger, weak judge protocol,
sufficiency / abstention protocol, and ReprojectionWitness are described as
method components. This was a paper-only edit. No live API calls, new
experiments, POST-3 through POST-7 reruns, silver-label scaling, route unlocks,
raw API storage, staging, or excluded-leftover changes were made.

## Files Reviewed

| file | status | action |
|---|---|---|
| `docs/archive/context_projection_fixed_v12.md` | present | updated Methods sections 4 and 6 for projector/regime, backend capability table, artifact chain, weak labels, sufficiency / abstention, reprojection, and fail-closed claim ledger |
| `docs/api/live-api-capability-contract.md` | present | added methods-facing capability table and ClaimLedger fail-closed rule |
| `docs/paper/live-api-experiment-boundaries.md` | present | added methods-facing capability boundary table |
| `docs/paper/post-lapi-claim-boundary-summary.md` | present | added ProjectionBundleV1, ClaimLedger, sufficiency / abstention, and ReprojectionWitness method boundary |
| `docs/paper/submission-claim-ledger.md` | present | added methods artifact chain and fail-closed rule |
| `docs/paper/final-submission-artifact-index.md` | absent | recorded as absent; closest manuscript-facing equivalent `docs/paper/submission-artifact-index.md` was updated |
| `docs/paper/submission-artifact-index.md` | closest equivalent | added methods artifact chain table |

## Methods Requirements

The updated Methods state:

- dispatch-time projector and active regime,
- backend capability table in the methods flow,
- generated-token logprobs are output-side confidence diagnostics only,
- fixed-target continuation scoring remains unsupported,
- ProjectionBundleV1 / artifact chain:
  - ProjectionPlan,
  - BudgetWitness,
  - MaterializedContext,
  - MetricBridgeWitness,
  - CounterfactualReplayWitness,
  - ReprojectionWitness,
  - ClaimLedger,
- weak model-adjudicated labels and bias controls,
- sufficiency / abstention regime labels,
- ReprojectionWitness before/after controlled replay fields,
- fail-closed claim ledger rules.

## Nonclaims Preserved

The PAPER-REV-3 edits preserve these denied claims:

- measurement validation,
- human/external gold validation,
- fixed-target teacher-forced NLL support,
- fixed-target continuation scoring support,
- teacher-forced scoring support,
- metric bridge support,
- `calibrated_proxy_supported`,
- `vinfo_proxy_supported`,
- paper-grade evidence / paper evidence,
- deployed V-information verification,
- selector superiority,
- global selector superiority,
- Route 5 unlock,
- Route 8 unlock.

Artifacts remain audit interfaces only. Judge outputs remain weak
model-adjudicated labels, not gold labels. Generated-token logprobs remain
output-side confidence diagnostics, not fixed-target NLL.

## Checks

Recorded after execution:

| command | result |
|---|---|
| `git diff --check` | passed; Git reported LF-to-CRLF working-copy warnings for dirty Markdown files only |
| `uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q` | passed: `20 passed` |
| methods requirement scan | passed: projector/regime, backend table, output-side logprob boundary, unsupported continuation scoring, ProjectionBundleV1 chain, weak labels, sufficiency / abstention labels, ReprojectionWitness fields, and fail-closed ClaimLedger rules present |
| evidence artifact diff scan | passed: no `artifacts/` diffs |
| staged-file scan | passed: no staged files |

## Verdict

PAPER-REV-3 Methods now state the capability boundary and claim ledger
unambiguously under `operational_utility_only/no_claim_upgrade`. No evidence
artifacts were changed and no claim upgrade was introduced.
