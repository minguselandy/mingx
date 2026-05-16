# P67R Route 2 Operational Evidence Package

## Purpose

This package summarizes the accepted Route 2 HotpotQA evidence state without updating manuscript claims. It records that P55/P63R bridge attempts failed closed or were positive-control only, while P56/P66 provide operational replay and comparison evidence under `operational_utility_only`.

## Bridge Evidence State

- P63R original HotpotQA bridge: `failed_closed_gate_failed` with metric claim `operational_utility_only`. Gates failed on `normalized_residual_failed, sign_agreement_failed, spearman_rho_failed`.
- P63R-FixA: `positive_control_only`. FixA is a circular positive control and not metric bridge evidence.
- P63R-FixB: `failed_closed_gate_failed` with metric claim `operational_utility_only`. FixB is a valid non-circular negative bridge attempt.

Therefore no calibrated metric support exists in Route 2 at this package point.

## Operational Evidence State

- P56 generated and validated `2000` HotpotQA operational dispatch traces.
- P66 compared `2000` traces across budgets `[512, 1024]`.
- P66 supports an operational-only HotpotQA comparison result.
- v12 improves supporting-fact recall against deployable baselines under matched budgets.
- P66 deployable-baseline paired comparisons with positive 95% CI: `6 / 6`.
- Oracle remains `non_deployable_upper_bound_only` and is not a deployable baseline.

## Claim Ledger

The machine-readable claim ledger is at `artifacts/experiments/route2_operational_evidence_package/claim_ledger.json`.

Rows included:

1. P63R original bridge
2. P63R-FixA positive control
3. P63R-FixB non-circular negative bridge
4. P56 operational traces
5. P66 operational comparison

## Claim Boundary

Allowed wording:

- P66 supports an operational-only HotpotQA comparison result.
- v12 improves supporting-fact recall against deployable baselines under matched budgets.
- The result is `operational_utility_only` because P55/P63R bridge gates failed.
- FixA is a circular positive control and not metric bridge evidence.
- FixB is a valid non-circular negative bridge attempt.

Denied claims:

- No `calibrated_proxy_supported` claim is introduced.
- No `vinfo_proxy_supported` claim is introduced.
- No measurement validation claim is introduced.
- No paper evidence claim is introduced.
- No P55 bridge support claim is introduced.
- No metric bridge support claim is introduced.
- No global selector superiority claim is introduced.
- No P56 metric support claim is introduced.
- No deployed V-information verification claim is introduced.

## Package Artifacts

- `artifacts/experiments/route2_operational_evidence_package/claim_ledger.json`
- `artifacts/experiments/route2_operational_evidence_package/evidence_summary.json`
- `docs/experiments/P67R-route2-operational-evidence-package.md`
