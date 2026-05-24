# POST-LAPI Sufficiency / Abstention Table

Status: POST-4-RUN pilot result under `operational_utility_only/no_claim_upgrade`

These rows are model-adjudicated candidate operational diagnostics only. They do not support truth validation, human-calibrated abstention, measurement validation, paper-grade evidence, Route 5 unlock, or Route 8 unlock.

| Regime | n cases | support rate | insufficient rate | contradict rate | uncertain rate | parse failed rate | abstain rate | abstain when insufficient rate | unsafe answer rate | missing evidence type distribution | cost per case | latency per case | claim gate status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| sufficient_kept | 10 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | `{'unknown': 10}` | 514.6 | 2097.2 | sufficiency_abstention_candidate_ready |
| sufficient_dropped | 11 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | `{'unknown': 11}` | 525.273 | 2284.364 | sufficiency_abstention_candidate_ready |
| insufficient_and_answered | 15 | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 1.0 | 1.0 | 1.0 | `{'bridge_fact': 6, 'entity': 11, 'temporal': 5}` | 543.067 | 2407.533 | sufficiency_abstention_candidate_ready |
| insufficient_and_abstained | 14 | 0.0 | 0.928571 | 0.0 | 0.071429 | 0.0 | 1.0 | 1.0 | 0.0 | `{'bridge_fact': 5, 'entity': 11, 'temporal': 1}` | 536.643 | 2347.643 | sufficiency_abstention_candidate_ready |

## Boundary Fields

| Field | Value |
| --- | --- |
| live API call count | `50` |
| model snapshot | `qwen3.6-flash` |
| endpoint | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| raw API responses stored | `false` |
| claim level | `operational_utility_only/no_claim_upgrade` |
| output interpretation | model-adjudicated candidate operational evidence only |
| Route 5 locked | `true` |
| Route 8 locked | `true` |
| claim upgrade introduced | `false` |
