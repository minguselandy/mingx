# Route 2 + Route 3 Final Status and PR Summary

Status: PR / merge-readiness summary
Claim status: `no_claim_upgrade`

## Route 2 Final Result

Route 2 produced an accepted HotpotQA operational replay/comparison package.
P56-Route2 validated 2,000 / 2,000 operational dispatch traces. P66-Route2 found
that the v12 diagnostic policy improved supporting-fact recall against deployable
baselines under matched budgets. The `gold_support_oracle_upper_bound` selector
remains `non_deployable_upper_bound`.

The Route 2 bridge attempts did not establish metric support. The original P63R
bridge and the non-circular FixB bridge failed closed, while FixA is retained
only as a circular positive-control diagnostic. Route 2 remains
`operational_utility_only`.

## Route 3A Final Result

Route 3A tested a support-grounded bridge protocol as a new Route 3 bridge
attempt, not as a P63R repair. It attempted 600 rows and validated 461 rows,
below the predeclared 500-row minimum. Calibration did not run. No operator rows
were written and no claim upgrade was introduced.

## Route 3B Final Result

Route 3B prospectively revised Route 3A sampling to use all eligible HotpotQA
instances. It attempted 792 rows, validated 613 rows, and covered 197 unique
original HotpotQA instances. Non-circularity checks passed. Calibration ran but
failed the preregistered sign-agreement, Spearman, and normalized-residual gates.
The Route 3B metric claim level is `failed_closed_no_claim_upgrade`.

## Safe Paper Claims

Safe wording:

```text
HotpotQA operational replay/comparison shows that the v12 diagnostic policy
improves supporting-fact recall against deployable baselines under matched
budgets.
```

Required qualifier:

```text
Because Route 2 and Route 3 bridge gates failed closed, this remains
operational-only evidence with no claim upgrade.
```

## Denied Claims

Do not claim:

- `calibrated_proxy_supported`
- `vinfo_proxy_supported`
- measurement validation
- paper evidence
- metric bridge support
- P55 bridge support
- P56 metric support
- global selector superiority
- deployed V-information verification
- support_grounded_bridge_candidate achieved
- Route 2 bridge repaired
- P63R repair succeeded

## Artifact And Storage Notes

Route 2 includes accepted operational traces and comparison artifacts. Route 3A
and Route 3B add small deterministic benchmark and calibration reports. No raw
API response dumps, raw external dataset mirrors, or Route 3 operator-input
files are part of the package.

## Test Summary

Recent Route 3B package checks passed:

- Route 3B focused tests: 9 passed.
- Route 3A regression tests: 5 passed.
- revised framing guardrails: 13 passed.
- full pytest suite: 685 passed, 4 skipped.
- JSON validation and claim-boundary grep passed with denied-claim hits only in
  boundary-preserving contexts.

## Merge Risks

- Reviewers may misread the operational replay result as metric support unless
  the failed bridge-gate qualifier remains adjacent to the Route 2 claim.
- Reviewers may misread Route 3B reaching calibration scale as support. The
  ledger must keep the failed gate result visible.
- Legacy P56 scaffold wording must remain distinct from the accepted
  P56-Route2 operational lane.

## Reviewer-facing Caveats

Route 2 is useful operational evidence, not calibrated metric evidence. Route 3
shows that the current support-grounded bridge designs also fail closed. The
repo is ready for PR / merge review only under the `no_claim_upgrade` boundary.
