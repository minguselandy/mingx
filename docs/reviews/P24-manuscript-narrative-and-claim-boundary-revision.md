# P24 Manuscript Narrative And Claim-Boundary Revision

```yaml
phase_id: P24
phase_title: Manuscript Narrative And Claim-Boundary Revision
verdict: ACCEPT_FOR_SUPERVISOR_REVIEW
target_manuscript_path: docs/archive/context_projection_revised_v10.md
source_review_path: docs/reviews/P23-codex-manuscript-narrative-and-evidence-review.md
branch: codex/p24-manuscript-narrative-claim-boundary-revision
document_type: manuscript_revision_only
measurement_validated_claimed: false
p04_status: deferred/operator-required
p09_status: BLOCKED_OPERATOR_REQUIRED
runtime_code_changed: false
claim_level_upgraded: false
original_repo_synced: false
```

## 1. Phase Scope

P24 applies the P23 manuscript narrative and claim-boundary recommendations directly to:

```text
docs/archive/context_projection_revised_v10.md
```

P24 does not add runtime modules, experiment builders, adapters, exporters, tests, live APIs, live cohorts, external runtime integration, or a parallel claim-gate system.

## 2. Changed Files

- `docs/archive/context_projection_revised_v10.md`
- `docs/reviews/P24-manuscript-narrative-and-claim-boundary-revision.md`

## 3. P0 Items Addressed

| P23 P0 item | action in P24 | status |
| --- | --- | --- |
| Abstract / Introduction evidence status not visible early enough. | Added an abstract-level evidence-status sentence and an introduction-level evidence-status paragraph. | addressed |
| Section 4.3.1 audit chain may be confused with benchmark pass evidence. | Clarified that P17 exercises audit plumbing and does not execute the benchmark's pre-registered scientific pass conditions. | addressed |
| Section 6.2 runtime artifact table too implementation-heavy. | Shortened the table to the four core artifacts plus `ProjectionBundleV1`; moved P12-P17 implementation artifacts to prose and companion evidence. | addressed |
| Section 9 / Conclusion lacks compact evidence-gap summary. | Strengthened limitations with no labels, no kappa, no contamination closure, no fresh bridge sufficient for `measurement_validated`, P04, and P09. | addressed |

P0 addressed count: 4.

## 4. P1 Items Addressed

| P23 P1 item | action in P24 | status |
| --- | --- | --- |
| Section 3.4 claim gate table is long. | Compressed redundant rows while preserving contamination, labels/kappa, bridge, synthetic, engineering/replay/paper, live API, and external runtime boundaries. | addressed |
| Section 4.2 `certified proxy-greedy-valid` is reviewer-sensitive. | Replaced with `proxy-greedy-valid diagnostic state under fresh metric-bridge evidence`. | addressed |
| Section 4.3.1 proxy matrix mixes positive and boundary rows. | Kept the three positive synthetic/proxy regimes in the main table and moved boundary cases to claim-gate prose. | addressed |
| Section 5 extraction audit is strong but unexecuted. | Added a sentence stating that the extraction audit is designed, not executed, and remains part of scientific closure. | addressed |
| Section 8 future work is broad. | Added priority ordering for P04-style labels/kappa/contamination/bridge review and P09 operator-approved runtime integration. | addressed |
| Section 7 related work is dense. | Added a concise reviewer-facing takeaway that the gap is the measurement protocol, bridge conditions, and auditable claim boundaries. | addressed |

P1 addressed count: 6.

## 5. P2 Items Applied Or Deferred

| P23 P2 item | P24 handling | status |
| --- | --- | --- |
| Normalize broad encoding artifacts. | Deferred; broad encoding cleanup would be a separate mechanical pass and could create large noisy diffs. | deferred |
| Prefer paper-facing labels over code identifiers in body tables. | Applied in Section 6.2 by moving implementation artifact identifiers out of the main table. | applied |
| Add one memorable conclusion sentence. | Applied indirectly by replacing "certification" conclusion wording with "proxy-regime diagnostic evidence". | applied |
| Add appendix pointer. | Already present; retained the companion evidence patch pointer. | applied |

P2 applied count: 3. P2 deferred count: 1.

## 6. Ambiguous Wording Rewrites

| previous wording | revised wording | claim-boundary effect |
| --- | --- | --- |
| `certified proxy-greedy-valid under a fresh metric bridge` | `proxy-greedy-valid diagnostic state under fresh metric-bridge evidence` | Removes certification language from a selector label. |
| `Vinfo_proxy_certified` example context | described as a diagnostic label name, not a deployed V-information certificate | Prevents label-name confusion with deployed certification. |
| `proxy-greedy-valid under the active metric-claim regime` | `proxy-greedy-valid diagnostic state under the active metric-claim regime` | Keeps selector state diagnostic rather than validation-like. |
| `composite proxy-regime certification` heading | `composite proxy-regime evidence gate` | Recasts the section as evidence gating, not certification of deployment. |
| conclusion `conservative proxy-regime certification` | `conservative proxy-regime diagnostic evidence` | Narrows the final paper claim. |

## 7. Table Compression And Placement Changes

- The conservative claim gate table remains in Section 3.4, but redundant rows were merged.
- The proxy-regime matrix in Section 4.3.1 now keeps only the three positive synthetic/proxy regime rows.
- Boundary cases for contamination, labels, kappa, bridge freshness, and artifact incompleteness are now summarized as conservative claim-gate boundaries rather than proxy-regime success rows.
- The runtime artifact table in Section 6.2 now focuses on `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, `MetricBridgeWitness`, and `ProjectionBundleV1`.
- P12-P17 evidence-ledger, claim-gate, metric-bridge-gate, proxy-matrix, replay-package, paper-summary, and demo outputs remain companion evidence rather than main-body claims.

## 8. Post-Edit Risky Claim Findings

Post-edit search terms included:

```text
measurement_validated
measurement validated
scientifically validated
scientific validation
deployed V-information certified
deployed V-information certification
proves submodularity
verified submodularity
verifies submodularity
certifies deployed behavior
certified deployed
guarantees runtime improvement
guaranteed improvement
live validation
production integration
human-validated
Vinfo_proxy_certified
certified greedy-valid
certified proxy-greedy-valid
certified escalate
composite certification
composite proxy-regime certification
```

Findings:

| phrase family | remaining use | classification |
| --- | --- | --- |
| `measurement_validated` | Evidence-status, claim-gate, and limitations denials. | `SAFE_DENIED_CLAIM` |
| scientific validation | Evidence-status and limitations denials. | `SAFE_DENIED_CLAIM` |
| deployed V-information certification | Denied claim in claim-gate/proxy/conclusion contexts. | `SAFE_DENIED_CLAIM` |
| live deployment validation / live API validation | Denied or missing evidence status only. | `SAFE_DENIED_CLAIM` |
| `certified proxy-greedy-valid` | Removed. | resolved |
| `certified greedy-valid` | Removed from claim-bearing prose; remaining `greedy-valid` appears as non-certification diagnostic language. | resolved |
| `certified escalate` | Not present. | resolved |
| `composite certification` | Removed from heading and claim-bearing prose. | resolved |

No `UNSAFE_OVERCLAIM` remains.

## 9. Claim Boundary After Patch

- P24 is manuscript revision only.
- P24 does not upgrade claim levels.
- P24 is not scientific validation.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- `measurement_validated` is not claimed.
- Synthetic success is not deployed V-information certification.
- Engineering success is not scientific validation.
- Replay package completeness is not scientific validation.
- Paper-facing summaries do not upgrade claim levels.
- No original repo sync was performed.

## 10. Remaining Limitations

- No human-label set is supplied.
- No kappa evidence is supplied.
- No contamination closure is supplied.
- No fresh deployed metric bridge sufficient for `measurement_validated` is supplied.
- No live API scientific closure is supplied.
- No P09 external runtime integration is performed.
- Broad encoding cleanup remains deferred to avoid noisy manuscript diffs.

## 11. Validation Commands And Results

Commands run:

```powershell
python -m compileall cps scripts
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
pytest tests/test_manuscript_tables.py -q
pytest tests/test_end_to_end_evidence_demo.py -q
pytest tests/test_paper_evidence_summary.py -q
```

Validation results:

| command | result |
| --- | --- |
| `python -m compileall cps scripts` | passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |
| `pytest tests/test_manuscript_tables.py -q` | 11 passed |
| `pytest tests/test_end_to_end_evidence_demo.py -q` | 8 passed |
| `pytest tests/test_paper_evidence_summary.py -q` | 12 passed |
