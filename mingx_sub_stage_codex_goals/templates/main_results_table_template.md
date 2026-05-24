# POST-LAPI Main Results Tables

## Table 1 — Backend capability and claim boundary

| Evidence source | Capability status | Allowed claim | Denied claim |
|---|---|---|---|

## Table 2 — POST-3 judge stability

| Metric | Value |
|---|---:|
| Live API calls | 240 |
| Examples | 30 |
| Normalized rows | 240 |
| Duplicate agreement | 0.9833 |
| Order-swap agreement | 0.9833 |
| Rubric paraphrase agreement | 0.9667 |

Allowed claim: model-adjudicated weak evidence.

## Table 3 — POST-4 sufficiency / abstention

| Metric | Value |
|---|---:|
| Final artifact run calls | 50 |
| Total turn calls | 100 |

Allowed claim: sufficiency / abstention diagnostic.

## Table 4 — POST-5 reprojection witness

| Metric | Value |
|---|---:|
| Live API calls | 26 |
| Repair candidate rate | 0.576923 |
| Label change rate | 0.576923 |
| Unsupported-to-supported rate | 0.576923 |
| Parse failed rate | 0.0 |

Allowed claim: operational reprojection witness.

## Table 5 — POST-6 matched-budget operational replay

| Metric | Value |
|---|---:|
| Live API calls | 0 |
| Normalized replay records | 2,000 |
| HotpotQA candidate pools | 200 |
| Budgets | 512, 1024 |

Allowed claim: scoped operational improvement under matched budgets.

## Table 6 — POST-7 extraction quality audit

| Metric | Value |
|---|---:|
| Live API calls | 100 |
| Normalized records | 100 |
| Records per stratum | 10 |
| Value-weighted loss proxy | 0.197403 |

Allowed claim: model-adjudicated extraction-risk evidence.

## Table 7 — Artifact hygiene

| Metric | Value |
|---|---:|
| JSON files | 27 |
| JSONL files | 5 |
| JSONL rows | 2,416 |
| Focused tests | 59 passed |
| Secret scan | passed |
| Raw-response-storage scan | passed |
| Forbidden-path scan | passed |
| Compileall | passed |

## Table 8 — Denied claims

| Denied claim | Status |
|---|---|
| measurement validation | denied |
| human/external gold validation | denied |
| metric bridge support | denied |
| calibrated_proxy_supported | denied |
| vinfo_proxy_supported | denied |
| paper evidence | denied |
| selector superiority | denied |
| global selector superiority | denied |
| Route 5 unlock | denied |
| Route 8 unlock | denied |
