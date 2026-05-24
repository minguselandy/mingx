# Backend Bridge Audit Witness

Status: LAPI-3 static contract only
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This witness records the current live-API backend scoring boundary. It is a
static documentation/schema witness only. It does not run live API calls, start a
new experiment, store raw API responses, unlock Route 5, unlock Route 8, or
upgrade any paper-facing claim.

The witness is implemented by:

- `cps/api/backend_capability_contract.py`
- `cps/api/backend_capability_witness.py`

## Witness Fields

The static witness records:

- `backend_name`
- `endpoint_family`
- `model_snapshot`
- `documented_generated_token_logprobs`
- `documented_prompt_logprobs`
- `fixed_target_teacher_forced_nll_supported`
- `fixed_target_continuation_scoring_supported`
- `generated_token_logprobs_allowed_use`
- `denied_claims`
- `claim_level`
- `evidence_date_or_doc_snapshot`

The implementation also records guardrail fields:

- `route_5_locked`
- `route_8_locked`
- `raw_response_stored`
- `live_api_call_performed`

## Current Static Witness

| field | value |
|---|---|
| `backend_name` | `dashscope_compatible_live_api` |
| `endpoint_family` | `openai_compatible_chat_completions` |
| `model_snapshot` | `static_doc_snapshot` |
| `documented_generated_token_logprobs` | `true` |
| `documented_prompt_logprobs` | `false` |
| fixed-target teacher-forced NLL supported: false | `false` |
| fixed-target continuation scoring supported: false | `false` |
| `generated_token_logprobs_allowed_use` | `answer_side_confidence_diagnostic_only` |
| `claim_level` | `fail_closed_bridge_audit / operational_utility_only` |
| Route 5 locked: true | `true` |
| Route 8 locked: true | `true` |
| `raw_response_stored` | `false` |
| `live_api_call_performed` | `false` |

## Boundary

Generated-token logprobs are answer-side confidence diagnostics only. They are
not fixed-target teacher-forced NLL and not fixed-target continuation scoring.
They must not be upgraded into metric bridge support, calibrated proxy support,
V-information proxy support, paper-grade evidence, selector superiority, Route 5
unlock evidence, or Route 8 unlock evidence.

The witness denies:

- fixed-target NLL support
- teacher-forced scoring support
- fixed-target continuation scoring support
- prompt logprobs support
- metric bridge support
- calibrated proxy support
- V-information proxy support
- measurement validation
- human/external gold validation
- paper-grade evidence
- selector superiority
- global selector superiority
- deployed V-information verification
- Route 5 unlock
- Route 8 unlock

The correct interpretation is fail-closed bridge audit evidence under
`operational_utility_only/no_claim_upgrade`.
