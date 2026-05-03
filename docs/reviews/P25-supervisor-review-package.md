# P25 Supervisor Review Package

```yaml
phase_id: P25
phase_title: Supervisor Review Package
document_type: review_package_only
current_manuscript_file: docs/archive/context_projection_revised_v10.md
source_verdict: ACCEPT_FOR_SUPERVISOR_REVIEW
source_verdict_phase: P24
branch: codex/p24-manuscript-narrative-claim-boundary-revision
measurement_validated_claimed: false
p04_status: deferred/operator-required
p09_status: BLOCKED_OPERATOR_REQUIRED
runtime_code_changed: false
source_manuscript_changed: false
original_repo_synced: false
```

## 1. Purpose

This package is a supervisor-facing summary of the current CPS manuscript and evidence scaffold. It is intended to help a supervisor decide whether the current draft should proceed to detailed academic feedback, further manuscript compression, or empirical-closure planning.

P25 does not revise the manuscript, add code, run live APIs, run live cohorts, modify `reference/`, sync to the original repo, unblock P04/P09, or claim `measurement_validated`.

## 2. Current Paper Thesis

The current manuscript argues that dispatch-time context projection in multi-agent LLM systems can be isolated as a per-round, per-agent, token-budgeted content-selection problem. It defines a V-information value function for that selection problem, proves conditional structural results under explicit objective-level assumptions, and then separates theorem-level claims from proxy measurement and runtime heuristic layers through a metric bridge and conservative claim gate. The deployment-facing contribution is not scientific validation or deployed V-information certification; it is a measurement and runtime-audit protocol for proxy-regime diagnostics, replayable evidence packaging, and explicit denied-claim boundaries.

Current manuscript file:

```text
docs/archive/context_projection_revised_v10.md
```

Current P24 verdict:

```text
ACCEPT_FOR_SUPERVISOR_REVIEW
```

## 3. Completed Evidence Chain P10-P24

| Phase | Artifact or review contribution | Supervisor-facing meaning | Claim boundary |
| --- | --- | --- | --- |
| P10 | Provider candidate normalization bridge | Provider-like candidate records can be normalized into selector/materializer-compatible records. | Engineering compatibility only. |
| P11 | Provider-to-selector offline smoke path | A deterministic fake/local provider path can produce selector inputs and projection bundles. | Offline engineering smoke only. |
| P12 | Evidence ledger and conservative claim gate report | Evidence availability, missing artifacts, and denied claims are summarized deterministically. | Claim-gate reporting only. |
| P13 | Metric bridge gate hardening | Bridge freshness, labels, kappa, contamination, and evidence mode constrain allowed claims. | Conservative claim-boundary tightening. |
| P14 | Proxy-regime certification matrix | Synthetic/proxy diagnostic regimes are summarized in manuscript-facing JSON/Markdown. | Proxy-regime diagnostic only. |
| P15 | Replay evidence package builder | Existing artifacts, hashes, ledger, claim report, and optional proxy matrix can be packaged for review. | Replay packaging is not scientific validation. |
| P16 | Paper evidence summary builder | Replay evidence can be converted into manuscript-facing summaries and table groups. | Paper summaries do not upgrade claims. |
| P17 | End-to-end evidence demo | P10-P16 are wired into one deterministic offline evidence chain. | Offline runtime-audit demo only. |
| P18 | Manuscript evidence patch | Tables and patch text were generated for `context_projection_revised_v10.md`. | Manuscript integration artifact only. |
| P19 | Engineering debt and paper-relevance audit | Core evidence modules were frozen around paper relevance to avoid generic framework drift. | Audit only. |
| P20 | Manuscript integration decision | Recommended `INTEGRATE_CORE_TABLES_ONLY`. | Decision document only. |
| P21 | Core manuscript table integration | Integrated compact claim-gate, proxy-regime, and runtime-artifact tables into the manuscript. | Manuscript integration only. |
| P22 | Final manuscript claim-boundary review | Confirmed no unsafe overclaims remained after P21. | Review only. |
| P23 | Strict narrative and evidence review | Rated the manuscript `ACCEPT_WITH_MAJOR_REVISIONS` and identified P0/P1/P2 revision items. | Review only. |
| P24 | Narrative and claim-boundary revision | Applied P23 P0/P1 fixes and small safe P2 polish. | Manuscript revision only; current verdict `ACCEPT_FOR_SUPERVISOR_REVIEW`. |

## 4. Integrated Manuscript Tables

P21 integrated the approved compact subset of the P18/P20 tables into the manuscript. P24 then compressed and clarified them.

| Table | Current location or role | Current treatment | Claim boundary |
| --- | --- | --- | --- |
| Conservative Claim Gate Rules | Section 3.4 | Kept in main body, shortened by merging redundant rows. | Shows contamination, labels/kappa, bridge freshness, synthetic, engineering/replay/paper-summary, live API, and external runtime denial boundaries. |
| Proxy-Regime Diagnostic Matrix | Section 4.3.1 | Keeps only the three positive synthetic/proxy regimes in the main table. Boundary cases moved to claim-gate prose. | Proxy-regime diagnostics are not deployed V-information certification. |
| CPS Runtime-Audit Artifacts | Section 6.2 | Shortened to `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, `MetricBridgeWitness`, and `ProjectionBundleV1`. | Runtime artifacts are audit/replay evidence, not scientific validation. |

Detailed replay package outputs, paper evidence summaries, and long integration notes remain in the companion patch:

```text
docs/paper/context_projection_v10_p18_tables_and_experiment_patch.md
```

## 5. Supported Claims

The current manuscript and evidence scaffold support the following bounded claims:

| Supported claim | Current support | Allowed wording |
| --- | --- | --- |
| CPS is a well-defined per-round context-selection problem. | Manuscript Sections 1-2. | "CPS formalizes dispatch-time per-agent content selection under token budgets." |
| Conditional structural theory is developed for the formal V-information objective. | Manuscript Section 3. | "The paper proves conditional results under explicit objective-level assumptions." |
| A metric bridge is necessary to connect formal V-information claims to proxy/runtime measurements. | Manuscript Section 3.4 and P13. | "Metric bridge freshness and evidence mode constrain reported claim levels." |
| A conservative claim gate exists. | P12/P13 and manuscript Section 3.4. | "The claim gate denies unsupported validation and certification claims." |
| A proxy-regime diagnostic matrix exists. | P14 and manuscript Section 4.3.1. | "Proxy-regime diagnostic behavior is summarized for synthetic/proxy regimes." |
| Offline replay/evidence packaging exists. | P15-P17. | "The scaffold produces deterministic offline runtime-audit evidence packages." |
| Paper-facing summaries exist. | P16/P18/P21/P24. | "The evidence can be summarized for manuscript review without upgrading claims." |

## 6. Denied Claims

The following claims remain explicitly denied:

| Denied claim | Reason |
| --- | --- |
| `measurement_validated` | No human labels, no kappa evidence, no contamination closure, and no fresh deployed metric bridge sufficient for validation are supplied. |
| Scientific validation | Offline engineering, replay, and manuscript-summary evidence do not constitute scientific validation. |
| Deployed V-information certification | Proxy-regime diagnostics do not certify deployed V-information submodularity. |
| Guaranteed deployed performance improvement | No live API or real deployed performance study is complete. |
| Production integration | P09 remains `BLOCKED_OPERATOR_REQUIRED`; no external runtime integration is performed. |
| Live API validation | No live API scientific closure has been run. |
| Human-validated measurement | No human-label protocol execution or agreement evidence is supplied. |

## 7. Remaining Limitations

The remaining limitations are central and should be treated as supervisor-review questions, not as solved implementation tasks:

- No live API scientific closure has been run.
- No live cohort has been run.
- No human-label set is supplied.
- No kappa evidence is supplied.
- No contamination closure is supplied.
- No fresh deployed metric bridge sufficient for `measurement_validated` is supplied.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- Synthetic/proxy success remains proxy/offline evidence only.
- Replay package completeness is not scientific validation.
- Engineering completeness is not scientific validation.
- Paper-facing summaries do not upgrade claim levels.

## 8. P04/P09 Operator-Required Status

| Phase | Current status | Supervisor relevance |
| --- | --- | --- |
| P04 scientific closure | deferred/operator-required | Required before any validation-level scientific claim. It requires human labels, kappa, contamination closure, and metric-bridge review. |
| P09 runtime adapter prototype | `BLOCKED_OPERATOR_REQUIRED` | Required before external runtime integration. Current evidence remains offline and deterministic. |

Neither P04 nor P09 is unblocked by P25.

## 9. Requirements Before `measurement_validated`

Before `measurement_validated` can be considered, the project needs at least:

1. A human-label protocol with supervisor/operator approval.
2. Human labels over the relevant evidence units.
3. Inter-annotator agreement or kappa evidence.
4. Contamination closure.
5. Fresh metric-bridge validation sufficient for the claim scope.
6. Explicit evidence that bridge status is not stale or missing.
7. A claim-gate report that allows, rather than denies, measurement validation.
8. If runtime-facing claims are desired, operator-approved P09 integration and a separate live/replay evaluation protocol.

Live API success alone, external runtime success alone, synthetic benchmark success, replay completeness, or paper-summary completeness is not enough.

## 10. Recommended Questions For Supervisor Review

1. Is the paper thesis best positioned as "conditional theory plus measurement protocol" rather than an empirical systems paper?
2. Should the title keep "Proxy-Regime Certification," or should the body further prefer "proxy-regime diagnostic evidence" to reduce reviewer sensitivity?
3. Are the three integrated main-body tables still too implementation-heavy for the intended venue?
4. Should the full P18 evidence patch become an appendix, a companion artifact, or remain internal review material?
5. Which empirical closure path should be prioritized first: P04 human-label/kappa/contamination work, P09 runtime integration, or synthetic benchmark execution under the pre-registered pass table?
6. Is Section 3.4's bridge statement strong enough to protect the conditional theorem from proxy/runtime overinterpretation?
7. Does the manuscript sufficiently explain why long-context models do not eliminate the selection problem?
8. Should the limitations section include a compact evidence-status table for submission, or is the current paragraph sufficient?
9. Which claims, if any, should be removed entirely before external submission even if they are currently bounded?
10. What venue or reviewer profile should guide the next compression pass: theory, measurement/evaluation, or systems?

## 11. Recommended Path After Supervisor Feedback

Recommended next path:

```text
P26 Supervisor-Guided Manuscript Revision Plan
```

Suggested decision branches:

| Supervisor feedback | Recommended next path |
| --- | --- |
| Manuscript is ready for detailed academic polishing. | P26 should produce a section-by-section polish plan and submission-readiness checklist. |
| Tables remain too implementation-heavy. | P26 should move or compress tables into appendix/companion evidence. |
| Claims still feel too strong. | P26 should perform a stricter claim-language rewrite pass before any sync. |
| Evidence is insufficient for the target venue. | P26 should plan P04 scientific closure before submission. |
| Runtime integration is the priority. | P26 should plan operator-approved P09 work without claiming validation. |

## 12. Validation Commands And Results

Commands required for P25:

```powershell
python -m compileall cps scripts
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Results:

| command | result |
| --- | --- |
| `python -m compileall cps scripts` | passed |
| `python scripts/framework_guard.py status` | passed; P09 remains `BLOCKED_OPERATOR_REQUIRED` |
| `python scripts/framework_guard.py validate --profile target` | passed |

## 13. Claim Boundary

- P25 is review packaging only.
- P25 does not modify `docs/archive/context_projection_revised_v10.md`.
- P25 does not add runtime code, tests, experiment builders, adapters, exporters, or claim-gate systems.
- P25 does not run live APIs or live cohorts.
- P25 does not modify `reference/`.
- P25 does not sync to the original repo.
- P25 does not unblock P04 or P09.
- P25 does not claim `measurement_validated`.
- Engineering success is not scientific validation.
- Synthetic success is not deployed V-information certification.
- Replay package completeness is not scientific validation.
- Paper-facing summaries do not upgrade claim levels.
