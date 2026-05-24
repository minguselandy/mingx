# Final Reviewer Response Bank

Status: PAPER-REV-7 reviewer defense package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This response bank is for reviewer-facing defense of the live-API operational audit paper. It does not add evidence, run experiments, rerun POST-3 through POST-7, store raw API responses, unlock Route 5, unlock Route 8, or upgrade claims. Every response preserves `operational_utility_only/no_claim_upgrade`.

## 1. Why no fixed-target NLL bridge?

The supported live-API route exposes generated output-token diagnostics, not documented fixed-target continuation scoring. We therefore fail closed rather than relabel sampled chat logprobs as teacher-forced NLL.

This is a backend-capability boundary, not a weakness hidden by wording. A fixed-target NLL bridge would require scoring a predetermined continuation under a fixed materialization policy. The available generated-token logprobs describe the model's own sampled output path, so they remain output-side confidence diagnostics only.

Claim boundary: `operational_utility_only/no_claim_upgrade`. No metric bridge support, fixed-target teacher-forced NLL support, fixed-target continuation scoring support, calibrated proxy support, V-information proxy support, measurement validation, Route 5 unlock, or Route 8 unlock is claimed.

## 2. Why mention V-information at all?

V-information is the formal target that organizes dispatch-time evidence projection: the paper asks what usable information a bounded predictor receives when context is selected under a token budget. That formal lens explains the selection problem and the conditional theory.

The present evidence does not estimate deployed V-information. The paper separates the formal objective from backend-scored measurements, operational utility, heuristic pipelines, and claim levels so that the live-API package cannot be misread as V-information validation.

Claim boundary: `operational_utility_only/no_claim_upgrade`. V-information proxy validation, `vinfo_proxy_supported`, metric bridge support, calibrated proxy support, and measurement validation remain denied.

## 3. Why use LLM judges?

LLM judges are used as weak operational diagnostics because they can expose duplicate disagreement, order sensitivity, rubric sensitivity, sufficiency and abstention behavior, reprojection effects, and extraction-risk patterns at a scale suitable for an audit trail.

They are not treated as human labels, external gold labels, human-human agreement, calibrated judges, or measurement validation. POST-3 stability controls bound the interpretation; they do not turn model-adjudicated outputs into validation evidence.

Claim boundary: `operational_utility_only/no_claim_upgrade`. Judge outputs remain weak/model-adjudicated diagnostics only, with Route 5 and Route 8 locked.

## 4. Why is this not a context-compression paper?

The paper does not claim to be a new compressor, prompt-pruning method, adaptive RAG router, or router benchmark. Compression papers generally optimize for shorter context or direct answer quality; this paper focuses on an audit layer for dispatch-time evidence projection.

The contribution is the claim-gated operational audit surface: ProjectionBundleV1-style artifacts, claim ledgers, selected and excluded evidence, materialization order, sufficiency/abstention diagnostics, reprojection witnesses, extraction-risk accounting, and fail-closed boundaries.

Claim boundary: `operational_utility_only/no_claim_upgrade`. The response does not claim compressor dominance, router dominance, selector superiority, global selector superiority, or paper-grade evidence.

## 5. Why not claim selector superiority?

The operational replay is scoped to named datasets, candidate pools, budgets, baselines, metrics, evaluator/materialization regime, and the frozen replay artifacts. That scope can support an operational replay reading under matched budgets only.

It cannot establish selector superiority in general because no accepted metric bridge, human/external gold validation, or deployed V-information measurement is available. The oracle is explicitly non-deployable and remains an upper bound, not a deployable baseline.

Claim boundary: `operational_utility_only/no_claim_upgrade`. Selector superiority, global selector superiority, metric bridge support, measurement validation, Route 5 unlock, and Route 8 unlock remain denied.

## 6. What does the live-API-only constraint contribute scientifically?

The live-API-only constraint makes the measurement boundary observable. It shows what deployed API surfaces expose, what they do not expose, which artifacts can be replayed, and where a claim gate must fail closed.

Scientifically, the contribution is the explicit separation between formal V-information, unavailable fixed-target scoring, generated-token diagnostics, weak model-adjudicated evidence, and replayable operational artifacts. That separation prevents backend-constrained diagnostics from being relabeled as stronger measurements.

Claim boundary: `operational_utility_only/no_claim_upgrade`. Live-API diagnostics do not validate V-information, metric bridge support, calibrated proxy support, measurement validation, or selector superiority.

## 7. Why are the POST-LAPI results useful if they are not validation?

The POST-LAPI results are useful because they document the audit behavior of the system under the actual claim ceiling. They show judge stability bounds, sufficiency/abstention outcomes, reprojection witness behavior, scoped replay behavior, extraction-risk diagnostics, table inputs, checksums, and storage-policy hygiene.

Those outputs help reviewers inspect whether the paper fails closed where evidence is weak or missing. Their value is diagnostic, reproducibility-oriented, and claim-boundary-preserving, not validating.

Claim boundary: `operational_utility_only/no_claim_upgrade`. POST-LAPI results do not imply measurement validation, human/external gold validation, metric bridge support, V-information proxy support, paper-grade evidence, selector superiority, Route 5 unlock, or Route 8 unlock.

## 8. Why are no more experiments recommended?

For the current submission, SUB-4 selected `NO_MORE_EXPERIMENTS_RECOMMENDED` because the package is already sufficient for the operational-audit claim, and additional POST-LAPI-style runs would not unlock stronger claims without the missing prerequisites.

The missing prerequisites are not more of the same weak evidence. They are materially different routes: documented fixed-target continuation scoring or teacher-forced NLL support, a fresh accepted metric bridge, human/external gold evidence where needed, and a reviewed claim-upgrade protocol. Running extra weak diagnostics would add volume without changing the claim ceiling.

Claim boundary: `operational_utility_only/no_claim_upgrade`. No new experiments are needed for the present submission, and no current response requests Route 5 unlock, Route 8 unlock, metric bridge support, measurement validation, or selector superiority.

## 9. Why are raw API responses not stored?

Raw API responses are not stored to keep the package storage-minimized and reviewable while avoiding unnecessary retention of provider payloads. The reproducibility layer stores normalized rows, hashes, compact provenance, prompt/template hashes where appropriate, model snapshot / endpoint metadata where applicable, table inputs, checksums, and scan summaries.

That design supports replayable audit and claim-gate review without preserving raw provider responses. It is a storage-policy and reproducibility choice, not a validation claim.

Claim boundary: `operational_utility_only/no_claim_upgrade`. Raw API response storage remains false, and the absence of raw responses is not used to claim measurement validation, metric bridge support, or paper-grade evidence.

## 10. What would be required for future claim upgrade?

A future claim upgrade would require evidence that is currently absent: documented fixed-target continuation scoring or teacher-forced NLL support for the active task family and materialization policy; a fresh matching MetricBridgeWitness with residual, stability, freshness, and stratum gates passed; human/external gold labels or human-sentinel audits where measurement validation is requested; and preregistered scope, datasets, budgets, baselines, metrics, evaluator/materialization regime, and statistical tests.

Any upgrade would also need a new claim-gate review that explicitly changes the allowed claim. Until then, the present package remains operational audit evidence only.

Claim boundary: `operational_utility_only/no_claim_upgrade`. Future requirements are listed as missing prerequisites, not as current evidence of validation, metric bridge support, V-information proxy support, or selector superiority.

## Submission Lock Summary

- Current claim: `operational_utility_only/no_claim_upgrade`.
- Route 5: locked.
- Route 8: locked.
- Raw API responses stored: false.
- Human/external gold validation: false.
- Metric bridge present: false.
- Claim upgrade introduced: false.
