# POST-LAPI Judge Weak-Evidence Stability Table

Status: POST-3-RUN pilot result under `operational_utility_only/no_claim_upgrade`

These rows are weak model-adjudicated candidate diagnostics only. They do not support human/external gold validation, measurement validation, judge validation, paper-grade evidence, selector superiority, Route 5 unlock, or Route 8 unlock.

| Condition | n judgments | parse success rate | duplicate agreement | order-swap agreement | rubric paraphrase agreement | confidence bucket stability | position bias rate | uncertain rate | parse failed rate | token cost per judgment | latency ms per judgment | claim gate status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| original_order | 30 | 1.0 | n/a | n/a | n/a | 1.0 | n/a | 0.0 | 0.0 | 537.4 | 2306.733 | weak_evidence_candidate_ready |
| order_swapped | 120 | 1.0 | n/a | 0.983333 | n/a | 0.933333 | 0.016667 | 0.0 | 0.0 | 560.958 | 2399.7 | weak_evidence_candidate_ready |
| duplicate_judging | 120 | 1.0 | 0.983333 | n/a | n/a | 0.833333 | n/a | 0.0 | 0.0 | 553.358 | 2491.717 | weak_evidence_candidate_ready |
| rubric_paraphrase | 120 | 1.0 | n/a | n/a | 0.966667 | 0.866667 | n/a | 0.0 | 0.0 | 561.583 | 2376.667 | weak_evidence_candidate_ready |

## Boundary Fields

| Field | Value |
| --- | --- |
| live API call count | `240` |
| model snapshot | `qwen3.6-flash` |
| endpoint | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| raw API responses stored | `false` |
| claim level | `operational_utility_only/no_claim_upgrade` |
| output interpretation | weak/model-adjudicated candidate evidence only |
| Route 5 locked | `true` |
| Route 8 locked | `true` |
| claim upgrade introduced | `false` |
