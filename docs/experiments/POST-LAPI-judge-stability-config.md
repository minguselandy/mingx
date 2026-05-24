# POST-LAPI Judge Weak-Evidence Stability Configuration

Goal ID: POST-3-CONFIG / Judge weak-evidence stability configuration
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This document records the configuration-only package for the judge
weak-evidence stability pilot. It prepares the schema, prompt bindings,
manifest dry-run, metrics, and table template. It does not run live API calls,
perform model judging, scale silver labels, store raw API responses, unlock
Route 5, unlock Route 8, or upgrade claims.

Live API pilot execution is reserved for the later POST-3 run-pilot goal only
after this config goal passes.

## Configured Inputs

- Config: `configs/post_lapi/judge_stability_pilot_config.yaml`
- Schema: `schemas/post_lapi_judge_stability.schema.json`
- Base prompt: `prompts/judge/weak_evidence_v1.md`
- Order-swapped prompt: `prompts/judge/weak_evidence_v1_order_swapped.md`
- Paper table template: `docs/paper/post-lapi-judge-stability-table-template.md`
- Dry-run manifest builder: `cps.judge.judge_manifest.build_judge_run_manifest`

## Configured Conditions

| Condition | Purpose | Prompt binding |
| --- | --- | --- |
| `original_order` | Baseline blinded pairwise judgment order. | `prompts/judge/weak_evidence_v1.md` |
| `order_swapped` | Position-bias and order-swap stability check. | `prompts/judge/weak_evidence_v1_order_swapped.md` |
| `duplicate_judging` | Duplicate consistency check with at least two judgments. | `prompts/judge/weak_evidence_v1.md` |
| `rubric_paraphrase` | Rubric paraphrase stability check with at least two variants. | `prompts/judge/weak_evidence_v1.md` |

## Labels

Allowed normalized labels:
- `support`
- `insufficient`
- `contradict`
- `uncertain`
- `parse_failed`

Unknown or unparseable labels must normalize to `parse_failed`; they do not
create human/external gold labels, judge validation, or measurement validation.

## Metrics

Configured metrics:
- `parse_success_rate`
- `duplicate_agreement`
- `order_swap_agreement`
- `rubric_paraphrase_agreement`
- `confidence_bucket_stability`
- `position_bias_rate`
- `uncertain_rate`
- `parse_failed_rate`
- `cost_per_judgment`
- `latency_per_judgment`

Configured fail-closed thresholds:
- `max_parse_failure_rate = 0.15`
- `min_order_swap_agreement = 0.80`
- `min_duplicate_agreement = 0.80`
- `min_rubric_paraphrase_agreement = 0.75`

If any threshold fails, the later pilot result must downgrade to ambiguous or
suppress the weak-evidence claim.

## Claim Boundary

Allowed:
- `model_adjudicated_weak_evidence`
- `operational_diagnostic_evidence`

Denied:
- human gold
- human/external gold validation
- measurement validation
- judge validation
- paper-grade evidence
- selector superiority

Boundary flags:
- Live API calls run during this config goal: no
- Model judging run during this config goal: no
- Silver-label scaling run during this config goal: no
- Raw API responses stored: no
- Route 5 locked: yes
- Route 8 locked: yes
- Claim upgrade introduced: no

## Dry-Run Validation

The focused test `tests/test_post_lapi_judge_stability_config.py` validates the
config and schema, confirms the prompt assets exist, builds a deterministic
dry-run manifest over fixture items, and checks that the manifest records
`live_api_call_performed=false` and `raw_response_stored=false`.

Run:

```powershell
uv run pytest tests/test_post_lapi_judge_stability_config.py -q
```

This validation builds planned request metadata only. It does not call a model,
send data to a provider, or store raw provider bodies.
