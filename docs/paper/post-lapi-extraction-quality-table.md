# POST-LAPI Extraction Quality Table

Status: POST-7-RUN result under `operational_utility_only/no_claim_upgrade`

These rows are model-adjudicated candidate operational diagnostics only. They do not support human-validated extraction measurement, measurement validation, metric bridge support, paper evidence, selector superiority, Route 5 unlock, or Route 8 unlock.

| stratum | n examples | completeness by stratum | value-weighted loss proxy | qualifier loss rate | temporal scope error rate | provenance loss rate | selector impact rate | parse failure rate | claim gate status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| simple_factual | 10 | 0.9 | 0.027027 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | model_adjudicated_extraction_risk_ready |
| complex_conditional | 10 | 0.8 | 0.058824 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | model_adjudicated_extraction_risk_ready |
| qualifier_heavy | 10 | 0.8 | 0.094972 | 0.1 | 0.0 | 0.0 | 0.0 | 0.0 | model_adjudicated_extraction_risk_ready |
| temporal_scope | 10 | 0.1 | 0.660584 | 0.0 | 0.8 | 0.0 | 0.0 | 0.0 | model_adjudicated_extraction_risk_ready |
| cross_chunk | 10 | 0.9 | 0.027027 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | model_adjudicated_extraction_risk_ready |
| long_tail_entity | 10 | 0.5 | 0.230769 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | model_adjudicated_extraction_risk_ready |
| high_provenance_value | 10 | 0.9 | 0.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | model_adjudicated_extraction_risk_ready |
| prerequisite | 10 | 0.7 | 0.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | model_adjudicated_extraction_risk_ready |
| contradictory | 10 | 0.7 | 0.099338 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | model_adjudicated_extraction_risk_ready |
| adversarial | 10 | 0.6 | 0.4 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | model_adjudicated_extraction_risk_ready |

## Boundary Fields

| Field | Value |
| --- | --- |
| live API calls run | `100` |
| model snapshot | `qwen3.6-flash` |
| endpoint | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| raw API responses stored | `false` |
| claim level | `operational_utility_only/no_claim_upgrade` |
| diagnostic claim level | `model_adjudicated_extraction_risk_evidence` |
| output interpretation | model-adjudicated candidate operational extraction-risk evidence only |
| value-weighted loss proxy interpretation | candidate operational evidence only |
| Route 5 locked | `true` |
| Route 8 locked | `true` |
| claim upgrade introduced | `false` |
