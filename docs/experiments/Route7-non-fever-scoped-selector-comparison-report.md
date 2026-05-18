# Route7 Non-FEVER Scoped Selector Comparison Report

Status: `scoped_multibenchmark_comparison_completed`
Claim status: `no_claim_upgrade`

## Decision

Route 7 completed a non-FEVER scoped comparison matrix using HotpotQA plus available project-native task families. The comparison remains operational-only because project-native rows are fixture/model-adjudicated and upstream bridge/proxy dependencies are unsatisfied.

The global selector superiority remains denied, and no scoped multi-benchmark selector-superiority claim is introduced.

## Matrix And Baselines

- Available benchmark count: `4`.
- HotpotQA evidence status: `operational_only_available`.
- FEVER evidence status: `disabled_by_user_no_fever`.
- HotpotQA operational cells positive: `true`.
- Missing deployable baselines:
- `BM25_or_dense_retrieval_when_available`
- `ablated_cost_aware_policy`
- `prior_v12_diagnostic_policy_variant`

## Reason Codes

- `non_fever_project_native_task_families_available`
- `missing_required_deployable_baselines`
- `project_native_fixture_operational_only_no_claim_upgrade`
- `route4_5_6_dependencies_unsatisfied_for_claim_upgrade`
- `no_scoped_multi_benchmark_selector_superiority`

## Claim Boundary

- `scoped_multi_benchmark_selector_superiority` remains false.
- `global_selector_superiority` remains false.
- HotpotQA operational comparison evidence is preserved only as operational utility.
