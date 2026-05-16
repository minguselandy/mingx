# P66 HotpotQA Operational Comparison

## Purpose

P66 compares accepted P56 HotpotQA dispatch traces under `operational_utility_only`.
The bridge witness remains `failed_or_absent`, so this comparison is operational only.

## Inputs

- Traces: `artifacts/operator_inputs/p56_realistic_dispatch_traces.jsonl`
- P56 report: `artifacts/benchmarks/p56_hotpotqa_trace_generation_report.json`

## Outputs

- Comparison summary: `artifacts/experiments/p56_hotpotqa_operational_comparison/comparison_summary.csv`
- Statistical tests: `artifacts/experiments/p56_hotpotqa_operational_comparison/statistical_tests.json`
- Diagnostic safety summary: `artifacts/experiments/p56_hotpotqa_operational_comparison/diagnostic_safety_summary.json`

## Results

- Traces compared: `2000`
- V12 deployable-baseline wins with positive 95% CI: `6`
- V12 losses with negative 95% CI: `0`
- V12 ties or inconclusive comparisons: `0`
- Oracle is retained only as `non_deployable_upper_bound`.

## Claim Boundary

- Allowed claim: operational comparison result under `operational_utility_only`.
- No calibrated_proxy_supported claim is introduced.
- No vinfo_proxy_supported claim is introduced.
- No measurement validation, paper evidence, P55 bridge support, metric bridge support, or global selector superiority claim is introduced.
