# POST-LAPI Extraction Quality Table Template

Status: template only; no POST-7 audit results are reported here.
Claim level: `operational_utility_only/no_claim_upgrade`.

Use this table only after an owner-approved extraction quality audit. The table
may summarize operational extraction risk over the M* -> M bottleneck. It must
not be used as human-validated extraction measurement, measurement validation,
theorem transfer to M*, end-to-end validation, metric bridge support, paper
evidence, selector superiority, Route 5 unlock, or Route 8 unlock.

| stratum | configured labels | n items | completeness by stratum | value-weighted loss proxy | qualifier loss rate | temporal scope error rate | provenance loss rate | selector impact rate | claim boundary |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| simple_factual | captured / captured_core_preserved / captured_core_materially_changed / missing / lost_qualifier / temporal_scope_error / provenance_loss / selector_impact | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |
| complex_conditional | captured / captured_core_preserved / captured_core_materially_changed / missing / lost_qualifier / temporal_scope_error / provenance_loss / selector_impact | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |
| qualifier_heavy | captured / captured_core_preserved / captured_core_materially_changed / missing / lost_qualifier / temporal_scope_error / provenance_loss / selector_impact | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |
| temporal_scope | captured / captured_core_preserved / captured_core_materially_changed / missing / lost_qualifier / temporal_scope_error / provenance_loss / selector_impact | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |
| cross_chunk | captured / captured_core_preserved / captured_core_materially_changed / missing / lost_qualifier / temporal_scope_error / provenance_loss / selector_impact | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |
| long_tail_entity | captured / captured_core_preserved / captured_core_materially_changed / missing / lost_qualifier / temporal_scope_error / provenance_loss / selector_impact | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |
| high_provenance_value | captured / captured_core_preserved / captured_core_materially_changed / missing / lost_qualifier / temporal_scope_error / provenance_loss / selector_impact | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |
| prerequisite | captured / captured_core_preserved / captured_core_materially_changed / missing / lost_qualifier / temporal_scope_error / provenance_loss / selector_impact | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |
| contradictory | captured / captured_core_preserved / captured_core_materially_changed / missing / lost_qualifier / temporal_scope_error / provenance_loss / selector_impact | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |
| adversarial | captured / captured_core_preserved / captured_core_materially_changed / missing / lost_qualifier / temporal_scope_error / provenance_loss / selector_impact | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `operational_utility_only` |

Required claim footer for any filled table:

- Live API calls run during this config goal: no
- Model-adjudicated extraction run during this config goal: no
- Raw API responses stored: no
- Human validation claim introduced: no
- Measurement validation claim introduced: no
- Claim upgrade introduced: no
- Route 5 locked: yes
- Route 8 locked: yes
