# Route 7 Scoped Selector-superiority Protocol

Status: protocol freeze only
Claim status: `no_claim_upgrade`

Route 7 freezes a finite multi-benchmark comparison protocol. It explicitly
rejects literal global selector superiority. Any future selector claim must be
scoped to the declared benchmark/task/budget distribution and must respect the
Route 4-6 evidence ceiling.

## Benchmark And Task Matrix

The matrix must be finite and predeclared before execution. Initial candidates:

| Benchmark | Task family | Claim role |
|---|---|---|
| HotpotQA | answer support selection | first operational and support bridge stratum |
| FEVER | claim verification | first verification bridge stratum if real evidence sources exist |
| Natural Questions or similar QA set | answer support selection | optional future robustness stratum |
| Qasper or long-context QA | document-grounded QA | optional future long-context stress stratum |

Optional benchmarks cannot be added after seeing results.

## Baseline Registry

Deployable baselines:

- random budget selector;
- top-k relevance or token-budget selector;
- BM25 or dense retrieval baseline when available;
- MMR density greedy;
- prior v12 diagnostic policy variant;
- ablated cost-aware policy.

Non-deployable reference:

- gold-support oracle upper bound, always marked
  `non_deployable_upper_bound`.

Oracle results cannot be used as a deployable baseline.

## Budget Matrix

Budgets must be predeclared per task family. Initial budget candidates:

- 256 diagnostic stress;
- 512 primary HotpotQA support budget;
- 1024 robustness budget;
- task-specific larger budgets only if justified before execution.

## Metrics

Primary metrics:

- supporting-fact or evidence recall at budget;
- sufficiency-grounded utility where Route 4 validates it;
- answer EM/F1 or label accuracy when independently evaluated;
- bridge-linked utility only where an accepted bridge candidate exists.

Token-efficiency metrics:

- utility per 1k tokens;
- support packets per 1k tokens;
- selected-token budget use;
- within-budget rate.

Diagnostic-safety metrics:

- distractor token share;
- omitted gold-support rate;
- contradiction or wrong-source rate where labels exist;
- selector instability across equivalent ordering.

## Statistical Tests

Route 7 must use matched item/budget comparisons:

- paired bootstrap 95 percent confidence intervals;
- paired permutation or Wilcoxon signed-rank tests;
- mean paired deltas and standardized effect sizes;
- multiplicity correction across predeclared families;
- worst-cell reporting for task and budget slices.

## Scoped Superiority Gates

A future scoped multi-benchmark selector-superiority candidate requires:

- predeclared benchmark/task/budget matrix;
- all deployable baselines present or fail-closed exclusions justified before
  execution;
- statistically positive paired deltas for the primary metric in the declared
  scope;
- token-efficiency and diagnostic-safety gates not failing;
- no hidden failed benchmark or budget cell;
- Route 4-6 dependencies satisfied for any paper-grade interpretation;
- independent review acceptance.

If a cell fails, the result is either scoped to the passing cells with the failed
cell reported, or the claim remains operational-only. Partial success cannot be
reported as global selector superiority.

## Allowed Wording

Allowed only after future gates and review:

```text
The selector improves the declared primary metric over the declared deployable
baselines on the declared benchmark/task/budget distribution.
```

Denied active wording:

- global selector superiority;
- benchmark-agnostic selector superiority;
- superiority over non-deployable oracle;
- superiority inferred from operational replay without bridge or validation
  dependencies;
- paper-grade selector superiority without Route 4-6 support where required.

## Stop Conditions

Stop Route 7 if:

- benchmark cells are added or removed after seeing results;
- baselines are missing without predeclared fail-closed handling;
- oracle is treated as deployable;
- paired tests fail but wording implies superiority;
- route dependencies are missing for the intended paper claim;
- claim wording exceeds the finite declared scope.
