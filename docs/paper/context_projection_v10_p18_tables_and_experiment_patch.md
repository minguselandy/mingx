# Context Projection v10 P18 Tables and Experiment Patch

## Target Manuscript

- Target manuscript path: `docs/archive/context_projection_revised_v10.md`
- This patch does not modify the source manuscript unless separately approved.
- P18 is manuscript integration only.
- P18 does not upgrade claim levels.
- P17 is not scientific validation.
- `measurement_validated` is not claimed.

## Recommended Insertion Points

| section | action |
| --- | --- |
| 3.4 Bridge statement | Add the metric bridge / claim gate patch after the bridge table. |
| 4.3.1 Synthetic regime benchmark | Add the experiment/evidence and proxy-regime certification patch after the validity gate table. |
| 6 Runtime Interface Requirements | Add the runtime-audit artifact table near the four-artifact projection chain. |
| 9 Limitations | Add the limitations and non-claims patch as an evidence-boundary paragraph. |
| 10-11 Broader Impact and Conclusion | Mention that P17 is offline runtime-audit evidence only, not scientific validation. |

## Table 1: CPS Runtime-Audit Artifacts

| artifact | manuscript role | suggested section | claim boundary |
| --- | --- | --- | --- |
| `ProjectionPlan` | Selection decision record for candidates considered, selected, and excluded. | Section 6.2 runtime artifact chain | Audit interface only; not scientific validation. |
| `BudgetWitness` | Token-budget witness for estimated and realized context costs. | Section 6.2 runtime artifact chain | Audit interface only; not scientific validation. |
| `MaterializedContext` | Realized context payload and materialization manifest. | Section 6.2 runtime artifact chain | Audit interface only; not scientific validation. |
| `MetricBridgeWitness` | Measurement-claim witness for metric class, drift, and diagnostic scope. | Sections 3.4, 4.2, and 6.2 | Audit interface only; not scientific validation. |
| `ProjectionBundleV1` | Canonical bundle tying plan, budget, materialized context, bridge witness, and diagnostics. | Runtime-audit evidence bundle | Audit interface only; not scientific validation. |
| `EvidenceLedger` | Deterministic summary of available runtime-audit evidence and missing required artifacts. | P12 audit layer | Audit interface only; not scientific validation. |
| `ClaimGateReport` | Conservative claim report that denies measurement claims when labels, kappa, bridge, or artifacts are missing. | P12/P13 claim gate | Audit interface only; not scientific validation. |
| `MetricBridgeGate` | Bridge-specific conservative gate for freshness, metric class, labels, kappa, and contamination status. | P13 metric bridge hardening | Audit interface only; not scientific validation. |
| `ProxyRegimeMatrix` | Manuscript-facing proxy/synthetic regime diagnostic matrix. | P14 proxy-regime certification | Audit interface only; not scientific validation. |
| `ReplayEvidencePackage` | Stable package of replayable artifacts, ledger, claim report, hashes, and optional matrix. | P15 replay package | Audit interface only; not scientific validation. |
| `PaperEvidenceSummary` | Manuscript-facing summary over the replay package and conservative claim gate. | P16 paper summary | Audit interface only; not scientific validation. |
| `EndToEndEvidenceDemo` | Offline P10-P16 demo wiring provider normalization through paper evidence summary. | P17 offline runtime-audit demo | Audit interface only; not scientific validation. |

## Table 2: Conservative Claim Gate Rules

| condition | allowed claim boundary | denied claim | manuscript note |
| --- | --- | --- | --- |
| contamination failure | `pilot_only` | `measurement_validated` | Contamination failure restricts claims to pilot-only evidence. |
| missing human labels | not `measurement_validated` | `measurement_validated` | Human labels remain required for measurement validation. |
| missing kappa | not `measurement_validated` | `measurement_validated` | Inter-annotator agreement remains required for measurement validation. |
| stale metric bridge | `operational_utility_only` or `ambiguous` | measurement validation | A stale bridge cannot support validation-level claims. |
| missing metric bridge | `operational_utility_only` or `ambiguous` | measurement validation | A missing bridge cannot support validation-level claims. |
| synthetic-only evidence | `synthetic_structural_only` | deployed V-information certification | Synthetic structure is not deployed V-information certification. |
| engineering-only evidence | `engineering_smoke_only` | scientific validation | Engineering smoke success is not scientific validation. |
| replay package completeness | `replayable_artifact_evidence` | scientific validation | Packaging completeness is audit evidence only. |
| paper-facing summary | no claim upgrade | measurement validation | Paper summaries surface existing gates but do not raise claims. |
| live API success alone | operational evidence only | measurement validation | Live execution alone does not provide labels, kappa, or bridge validation. |
| external runtime success alone | operational evidence only | measurement validation | Runtime integration alone does not validate measurement. |

## Table 3: Proxy-Regime Certification Matrix

| regime | manuscript role | certification scope | claim boundary |
| --- | --- | --- | --- |
| `redundancy_dominated` | synthetic/proxy diagnostic row | `proxy_regime_diagnostic_only` | Proxy-regime certification is not deployed V-information certification. |
| `sparse_pairwise_synergy` | synthetic/proxy diagnostic row | `synthetic_structural_only` | Proxy-regime certification is not deployed V-information certification. |
| `higher_order_synergy` | higher-order/prerequisite boundary row | `synthetic_structural_only` | Proxy-regime certification is not deployed V-information certification. |
| `contamination_failed` | negative claim-gate boundary row | `pilot_only` | Proxy-regime certification is not deployed V-information certification. |
| `missing_human_labels` | negative claim-gate boundary row | `ambiguous` | Proxy-regime certification is not deployed V-information certification. |
| `missing_kappa` | negative claim-gate boundary row | `ambiguous` | Proxy-regime certification is not deployed V-information certification. |
| `stale_metric_bridge` | metric bridge boundary row | `operational_utility_only` or `ambiguous` | Proxy-regime certification is not deployed V-information certification. |
| `missing_metric_bridge` | metric bridge boundary row | `operational_utility_only` or `ambiguous` | Proxy-regime certification is not deployed V-information certification. |
| `artifact_incomplete` | artifact completeness boundary row | `ambiguous` | Proxy-regime certification is not deployed V-information certification. |

## Table 4: Replay Evidence Package Summary

| output | manuscript role | claim boundary |
| --- | --- | --- |
| `manifest.json` | package manifest and claim scope | Replay evidence package completeness is not scientific validation. |
| `artifact_counts.json` | required artifact count summary | Replay evidence package completeness is not scientific validation. |
| `projection_bundle_hashes.json` | stable `ProjectionBundleV1` hash coverage | Replay evidence package completeness is not scientific validation. |
| `evidence_ledger.json` | P12 evidence ledger | Replay evidence package completeness is not scientific validation. |
| `claim_gate_report.json` | P12/P13 conservative claim gate report | Replay evidence package completeness is not scientific validation. |
| `claim_gate_report.md` | human-readable conservative claim report | Replay evidence package completeness is not scientific validation. |
| `proxy_regime_matrix.json` | P14 proxy-regime matrix JSON | Replay evidence package completeness is not scientific validation. |
| `proxy_regime_matrix.md` | P14 proxy-regime matrix Markdown | Replay evidence package completeness is not scientific validation. |
| `replay_package_summary.md` | P15 replay package summary | Replay evidence package completeness is not scientific validation. |
| `paper_evidence_summary.json` | P16 paper evidence summary JSON | Paper-facing summaries do not upgrade claim levels. |
| `paper_evidence_summary.md` | P16 paper evidence summary Markdown | Paper-facing summaries do not upgrade claim levels. |
| `demo_manifest.json` | P17 end-to-end demo manifest | P17 is offline runtime-audit evidence only. |
| `demo_summary.md` | P17 end-to-end demo summary | P17 is offline runtime-audit evidence only. |

## Table 5: Limitations and Non-Claims

| limitation | manuscript note |
| --- | --- |
| P04 remains deferred/operator-required | Keep scientific closure outside this manuscript patch until operator review is complete. |
| P09 remains `BLOCKED_OPERATOR_REQUIRED` | Keep external runtime integration outside this manuscript patch until operator approval. |
| `measurement_validated` is not claimed | Missing labels, kappa, contamination closure, and bridge evidence block validation. |
| synthetic success is not deployed V-information certification | Synthetic/proxy evidence is diagnostic, not deployed certification. |
| engineering success is not scientific validation | Offline compatibility and smoke evidence are engineering artifacts. |
| replay package completeness is not scientific validation | Complete replay files make evidence reviewable but do not validate measurement. |
| paper-facing summaries do not upgrade claim levels | Summaries surface existing gates only. |
| live API/external runtime success alone is not measurement validation | Live execution or runtime integration alone does not provide labels, kappa, or metric bridge validation. |
| missing labels/kappa block measurement validation | Human labels and agreement remain required. |

## Experiment / Evidence Section Patch

Insert after Section 4.3.1:

> The current implementation adds a deterministic offline runtime-audit evidence chain for the manuscript-facing scaffold. The chain normalizes provider-style candidates, runs a fake/local provider-to-selector smoke path, materializes `ProjectionBundleV1` artifacts, rebuilds an evidence ledger, applies the conservative claim gate and metric bridge gate, emits a proxy-regime matrix, packages replay evidence, and produces paper-facing summaries. This evidence is useful because it makes the proposed audit surface executable and replayable. It is not scientific validation, does not claim `measurement_validated`, and does not certify deployed V-information submodularity.

## Metric Bridge / Claim Gate Patch

Insert near Section 3.4 or Section 4.2:

> The runtime-audit scaffold treats claim scope as a first-class output. `MetricBridgeWitness`, `EvidenceLedger`, `MetricBridgeGate`, and `ClaimGateReport` jointly prevent engineering evidence from being reported as V-information validation. The current offline evidence permits only conservative engineering or synthetic/proxy-scoped claims. `measurement_validated` remains denied because P04 scientific closure, human labels, kappa, contamination closure, and fresh deployed metric bridge evidence are not supplied by this patch.

## Proxy-Regime Certification Patch

Insert after the synthetic benchmark validity gate:

> The proxy-regime matrix should be read as a manuscript-facing diagnostic map over synthetic/proxy regimes. It records expected diagnostic behavior, observed diagnostic summaries when available, failure modes, allowed claim boundaries, and denied claims for redundancy-dominated, pairwise-synergy, higher-order-synergy, contamination-failed, missing-label, missing-kappa, stale-bridge, missing-bridge, and artifact-incomplete regimes. The matrix does not certify deployed V-information submodularity.

## Limitations and Non-Claims Patch

Insert in Section 9:

> The replay and paper-evidence layers make the evidence chain inspectable, deterministic, and easier to cite, but they do not raise the scientific claim level. P17 remains an offline runtime-audit evidence demo. P04 remains deferred/operator-required, P09 remains `BLOCKED_OPERATOR_REQUIRED`, `measurement_validated` is not claimed, and replay package completeness does not imply scientific validation. Synthetic success, engineering success, live API success, or external runtime success alone must not be reported as deployed V-information certification or measurement validation.

## Claims That Must Remain Denied

- `measurement_validated`
- `scientific_validation`
- `deployed_v_information_certification`
- `deployed_v_information_submodularity_certified`
- `runtime_integration_complete`

## Claims Requiring P04/P09/Operator Work

- P04 operator scientific closure
- P09 operator runtime integration
- Human label completion
- Kappa computation and review
- Contamination pass/fail closure
- Fresh deployed metric bridge evidence

## Final Claim Boundary

- Paper-facing summaries do not upgrade claim levels.
- `measurement_validated_allowed: false`
- P04 status: `BLOCKED_OPERATOR_REQUIRED`
- P09 status: `BLOCKED_OPERATOR_REQUIRED`
- P17 is not scientific validation.
- Replay package completeness is not scientific validation.
- Synthetic success is not deployed V-information certification.
- Engineering success is not scientific validation.
