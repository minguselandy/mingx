# Live Pilot Execution Decision

**Phase:** P31 Operator-Approved Live Pilot Execution Decision

**Target workflow:** Decision gate between P30 dry-run rehearsal and any future
EV2 controlled live pilot.

**Default decision:** `DO_NOT_RUN`

**Status:** Decision/documentation only. This document does not run live APIs,
authorize execution by itself, implement API clients, import SDKs, fabricate
labels, fabricate kappa, fabricate contamination pass, unblock P04/P09, or claim
`measurement_validated`.

## 1. Purpose

P31 is the operator decision gate before any EV2 live pilot for the CPS
measurement and runtime-audit scaffold. It records the information an operator
must provide before moving from P30 dry-run rehearsal to controlled live
execution.

This document does not authorize live execution by itself. Live execution
requires the operator to fill the manifest, explicitly approve the run, set the
required live gate only during execution, and issue a separate instruction for
the execution phase.

No live API is run in P31. DeepSeek V4 Flash and DeepSeek V4 Pro are model
conditions only, not validation authorities. Live output alone cannot become
`measurement_validated`.

## 2. Decision Status

Select exactly one decision status before initiating any future live execution.
Until an operator fills this section, the decision is:

```text
DO_NOT_RUN
```

| Status | Operator selection | Meaning |
| --- | --- | --- |
| `DO_NOT_RUN` | default | No live execution is approved. |
| `APPROVED_FOR_DRY_RUN_ONLY` | unchecked | Only another dry-run rehearsal may be performed. |
| `APPROVED_FOR_FLASH_ONLY_LIVE_PILOT` | unchecked | Approve DeepSeek V4 Flash live pilot only after all gates pass. |
| `APPROVED_FOR_FLASH_AND_PRO_LIVE_PILOT` | unchecked | Approve both model conditions after all gates pass. |
| `DEFER_UNTIL_LABELERS_READY` | unchecked | Do not run until EV3 annotators are available. |
| `DEFER_UNTIL_BUDGET_APPROVED` | unchecked | Do not run until budget cap is approved. |
| `DEFER_UNTIL_METRIC_BRIDGE_READY` | unchecked | Do not run until bridge review ownership is ready. |

The default `DO_NOT_RUN` status is fail-closed. A future phase must not infer
approval from the existence of this document or the manifest template.

## 3. Required Operator Inputs

Before any live run can be considered, the operator must provide:

- operator name or initials;
- approval date placeholder;
- budget cap;
- API provider account readiness;
- API credential location outside the repository;
- DeepSeek V4 Flash endpoint;
- DeepSeek V4 Flash model name;
- DeepSeek V4 Pro endpoint;
- DeepSeek V4 Pro model name;
- planned Flash case count;
- planned Pro case count;
- conditions to run;
- prompt template id;
- temperature;
- output root;
- artifact retention path;
- labeler availability;
- contamination audit reviewer;
- metric bridge reviewer;
- abort threshold.

Do not record real credentials, tokens, secrets, or private endpoint credentials
in the repository. Credential locations may be described only as external,
operator-managed locations.

## 4. Recommended Decision

The conservative recommendation is:

```text
APPROVED_FOR_FLASH_ONLY_LIVE_PILOT only after all go gates pass
```

Initial live pilot:

- model condition: DeepSeek V4 Flash only;
- size: 30-50 cases;
- conditions:
  - `no_cps_baseline`;
  - `heuristic_selector_baseline`;
  - `cps_runtime_audit_scaffold`.

DeepSeek V4 Pro should be held for a later matched audit subset of 10-20 cases
only after the Flash dry/live pipeline succeeds and artifact capture is stable.

Rationale:

- controls cost before spending stronger-model budget;
- validates the artifact pipeline on the primary pilot condition first;
- lowers operational risk;
- avoids interpreting Pro behavior before the Flash pipeline is stable;
- preserves claim boundaries while EV3 labels, kappa, contamination audit, and
  metric bridge review remain pending.

## 5. Required Manifest Template

The required manifest template is:

```text
docs/templates/live-pilot-manifest-template.json
```

The template is deterministic and contains placeholders only. It does not include
real API keys, real credentials, or source-code constants for provider model IDs.

Template defaults:

- `decision_status`: `DO_NOT_RUN`;
- `operator_approval`: `false`;
- `mode`: `dry_run`;
- `live_api_used`: `false`;
- `external_runtime_used`: `false`;
- `measurement_validated` appears only as a forbidden claim.

An operator must fill the placeholders, approve the manifest, and provide a
separate execution instruction before any future P32 live run.

## 6. Go / No-Go Gates

### Go Gates

All go gates must be satisfied before live execution:

- P30 dry-run rehearsal passed;
- clean git state;
- exact commit recorded;
- manifest filled;
- budget approved;
- output root prepared;
- Flash endpoint fixed;
- Flash model name fixed;
- prompt templates frozen;
- cases frozen;
- conditions frozen;
- `operator_approval: true`;
- `CPS_ALLOW_LIVE_API=1` set only during execution;
- labelers available;
- contamination reviewer assigned;
- metric bridge reviewer assigned.

### No-Go Gates

Any no-go gate blocks live execution:

- budget not approved;
- labelers unavailable;
- endpoint or model name uncertain;
- prompt still changing;
- case set still changing;
- output path not prepared;
- contamination reviewer unavailable;
- metric bridge reviewer unavailable;
- claim boundary unclear;
- operator not present.

Missing prerequisites must fail closed.

## 7. Claim Boundary

EV2 live pilot output can at most support controlled live pilot evidence. EV2
without labels and kappa is not `measurement_validated`.

EV3 labels and kappa may support human-labeled pilot evidence, but high kappa
alone is not validation. Contamination pass alone is not validation.

EV4 metric bridge closure and conservative claim gate review are required before
`measurement_validated_candidate`. `measurement_validated` requires explicit
claim gate allow for the scoped run.

DeepSeek V4 Flash or DeepSeek V4 Pro success alone is not validation. Live API
success alone is not measurement validation. Engineering success is not
scientific validation. Synthetic/proxy evidence does not certify deployed
V-information submodularity.

P04 remains deferred/operator-required. P09 remains
`BLOCKED_OPERATOR_REQUIRED`.

## 8. Execution Handoff

If and only if a future operator approves live execution, the next phase should
be:

```text
P32 Operator-Approved Live Pilot Execution
```

P32 must only be initiated by explicit operator instruction that includes:

- approval decision;
- filled manifest path;
- budget cap;
- model endpoints and model names;
- case count;
- output root.

If any of those inputs are missing, P32 must not run live.
