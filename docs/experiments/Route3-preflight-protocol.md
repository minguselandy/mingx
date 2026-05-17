# Route 3 Preflight Protocol

Status: preflight protocol package
Route: Route 3 new bridge protocol
Claim status: `operational_utility_only; no_claim_upgrade`

Route 3 is a new bridge protocol informed by Route 2 negative results. It is
not a P63R repair, does not extend Route 2, and must not start Route 3A until
this preflight package receives independent review approval.

## Route 2 Prior Outcome

Route 2 remains operational-only:

- P63R original HotpotQA answer bridge failed closed.
- P63R-FixA is `positive_control_only` and `circular_alignment_control`; it is
  not independent metric bridge evidence.
- P63R-FixB is a valid non-circular negative bridge attempt and failed closed.
- P56/P66 are HotpotQA operational replay/comparison evidence only.

Allowed Route 2 claim:

```text
HotpotQA operational replay/comparison shows that the v12 diagnostic policy
improves supporting-fact recall against deployable baselines under matched
budgets.
```

Required qualifier:

```text
Because P63R bridge gates failed closed, this remains operational_utility_only,
not calibrated metric support.
```

## Recoverable Artifact Inventory

Recoverable Route 2 bridge artifacts:

| Attempt | Rows validated | Unique instances | Gate result | Claim level |
|---|---:|---:|---|---|
| P63R original answer bridge | 600 | 150 | `failed_closed_gate_failed` | `operational_utility_only` |
| P63R-FixA circular control | 643 | 643 | `positive_control_only` | `positive_control_only` |
| P63R-FixB independent utility | 826 | 826 | `failed_closed_gate_failed` | `operational_utility_only` |

The sanitized delta records, operator rows, calibration summaries, and metric
bridge witnesses are recoverable. Raw live API response dumps are intentionally
absent, so exact raw API replay is not recoverable from repository artifacts.

## Recovered Gate Settings

Recovered P63R/FixB gate settings:

| Gate | Value |
|---|---:|
| `min_rows_validated` | 500 |
| `min_unique_instances` | 150 |
| `heldout_fraction` | 0.30 |
| `min_sign_agreement` | 0.70 |
| `min_spearman_rho` | 0.40 |
| `min_effective_sample_size` | 100 |
| `max_normalized_residual` | 0.50 |

The normalized residual gate was pre-run configured. These recovered gates are
inputs to Route 3 planning only; they do not authorize any claim upgrade.

## Candidate-Pool Support Achievability

Existing HotpotQA candidate pools are sufficient for support-achievability
preflight:

| Quantity | Value |
|---|---:|
| candidate pools | 200 |
| unique instances | 200 |
| total packets | 8,303 |
| gold-supporting packets | 485 |
| gold support reachable under budget 256 | 200 / 200 |
| gold support reachable under budget 512 | 200 / 200 |
| gold support reachable under budget 1024 | 200 / 200 |
| candidate pool size, min / median / mean / max | 11 / 40 / 41.515 / 75 |
| gold token sum, min / median / mean / max | 17 / 53 / 56.745 / 151 |

These quantities can support Route 3 protocol design, but they are not new
calibration evidence.

## Route 3A Support-Grounded Utility Protocol

Route 3A should test a support-grounded utility definition that is independent
from model logloss.

Required design:

- Use existing HotpotQA candidate pools and gold supporting-fact labels.
- Define utility from support coverage, support achievability, or packet-level
  support-label outcomes grounded in candidate-pool gold labels.
- Keep `delta_logloss` on a fixed support-label NLL path if a future approved
  evaluator is used.
- Keep `delta_utility` independent from NLL, token logprobs, `delta_logloss`,
  ranks of `delta_logloss`, and any rounded, clipped, copied, or affine
  transform of `delta_logloss`.
- Pre-register row keys, utility definition, evaluator metadata, sampling, and
  gates before generating any Route 3A rows.

Route 3A must not run until this preflight receives independent review approval.

## Route 3C Conditional Calibration Protocol

Route 3C should test whether bridge alignment is conditional on predeclared
HotpotQA strata rather than global across all rows.

Candidate strata:

- answer type, including yes/no versus entity/string answers;
- number of gold-support packets;
- gold-support token budget bucket;
- candidate-pool size bucket;
- whether context `L` already contains gold support;
- whether block `A` is gold-supporting or distractor;
- single-hop-like versus multi-hop support pattern when derivable from existing
  HotpotQA support facts.

Policy:

- Strata must be declared before row generation.
- Each stratum must independently satisfy row, instance, effective sample size,
  heldout, sign-agreement, rank-correlation, and normalized-residual gates.
- Any passing result is stratum-local and review-pending only.
- Failed strata remain `operational_utility_only` or `ambiguous_metric`.

## Stop / Continue / Escalate Gates

Stop if:

- utility is copied from or algebraically derived from `delta_logloss`;
- raw row provenance cannot bind to `candidate_pool_hash` and packet IDs;
- Route 3 text implies any denied claim before future gates and review;
- a design tries to overwrite P63R, FixA, or FixB artifacts.

Continue if:

- the protocol is pre-registered and independently accepted;
- utility is support-grounded and independent from logloss;
- candidate-pool support achievability remains reproducible;
- future evaluator use is explicitly approved before any NLL generation.

Escalate if:

- live API calls, human annotation, contamination review, or new large artifact
  storage are required;
- any result is proposed as a claim upgrade;
- artifact size would materially expand repository weight.

## Artifact Storage Policy

Route 3 should not keep expanding normal Git with large JSONL rows, dispatch
traces, or operator-input files by default.

Recommended policy:

- Commit deterministic summaries, manifests, schemas, validation reports, and
  claim-boundary reports.
- Store future large JSONL rows/traces/operator inputs in release assets, Git
  LFS, DVC, or external artifact storage.
- Commit content hashes, row counts, schema versions, generation configs, and
  validation summaries for large artifacts.
- Keep raw benchmark mirrors outside the repository.
- Keep raw live API responses out of Git unless sanitized and explicitly
  approved.

## Denied Claims

Route 3 Preflight does not support:

- `calibrated_proxy_supported`
- `vinfo_proxy_supported`
- measurement validation
- paper evidence
- metric bridge support
- P55 bridge support
- P56 metric support
- global selector superiority
- deployed V-information verification
