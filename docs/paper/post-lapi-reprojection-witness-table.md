# POST-LAPI Reprojection Witness Table

Status: POST-5-RUN pilot result under `operational_utility_only/no_claim_upgrade`

These rows are model-adjudicated candidate operational diagnostics only. They do not support validated repair, truth correction guarantees, metric bridge support, selector superiority, Route 5 unlock, or Route 8 unlock.

| Case class | n cases | repair rate | label change rate | abstain to support rate | unsupported to supported rate | cost delta | latency delta | position sensitivity rate | claim gate status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| insufficient_and_answered | 15 | 1.0 | 1.0 | 1.0 | 1.0 | 121.6 | 234.933 | 1.0 | reprojection_witness_candidate_ready |
| sufficient_dropped | 11 | 0.0 | 0.0 | 0.0 | 0.0 | 36.545 | 184.273 | 0.090909 | reprojection_witness_candidate_ready |

## Boundary Fields

| Field | Value |
| --- | --- |
| live API call count | `26` |
| model snapshot | `qwen3.6-flash` |
| endpoint | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| raw API responses stored | `false` |
| claim level | `operational_utility_only/no_claim_upgrade` |
| diagnostic claim level | `operational_reprojection_witness` |
| output interpretation | model-adjudicated candidate operational evidence only |
| Route 5 locked | `true` |
| Route 8 locked | `true` |
| claim upgrade introduced | `false` |
