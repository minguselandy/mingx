# P45 API-Generated Calibration Data Live Smoke Readiness

## Status

Live generation was skipped. The live API authorization and operator config are
not complete, so no API call was made and no calibration rows were generated.

## Required Live Gates

| Gate | Observed state | Status |
|---|---|---|
| credential CSV | `mingx-dev/默认业务空间-apiKey-4648916.csv` exists; key value not printed | partial |
| `CPS_ALLOW_LIVE_API=1` | unset | fail |
| `P45_ALLOW_API_DATA_GENERATION=1` | unset | fail |
| `mode = live_operator_approved` | `dry_run` | fail |
| `operator_approval = true` | `false` | fail |
| `provider_profile` | empty | fail |
| `fixed_model_id` | empty | fail |
| `strong_review_model_id` | empty | fail |

## Scope Boundary

- No live API was called.
- No task packets were sent to a provider.
- No `delta_logloss` was fabricated.
- No accepted P45 calibration rows were exported.
- No P45 dry validation was run because there are no accepted rows.
- No P45 calibration artifacts were generated.
- No `measurement_validated`, human-label, kappa, or deployed V-information
  verification claim is made.

## Missing Operator Inputs

To run a live smoke later, provide an operator config with:

- `mode = live_operator_approved`
- `operator_approval = true`
- non-empty `provider_profile`
- non-empty `fixed_model_id`
- non-empty `strong_review_model_id`
- a credential mapping from the CSV into the provider environment expected by
  the selected `provider_profile`

Then set both environment flags before launching the run:

```text
CPS_ALLOW_LIVE_API=1
P45_ALLOW_API_DATA_GENERATION=1
```

The fixed model must return measured token logprobs. If logprobs are unavailable,
rows must be marked unusable and excluded from accepted bridge calibration input.
