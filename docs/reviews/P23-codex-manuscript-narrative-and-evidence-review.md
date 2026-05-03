# P23 Codex Manuscript Narrative And Evidence Review

```yaml
phase_id: P23
phase_title: Codex Manuscript Narrative And Evidence Review
verdict: ACCEPT_WITH_MAJOR_REVISIONS
document_type: manuscript_review_only
target_manuscript_path: docs/archive/context_projection_revised_v10.md
branch: codex/p23-codex-manuscript-narrative-and-evidence-review
measurement_validated_claimed: false
p04_status: deferred/operator-required
p09_status: BLOCKED_OPERATOR_REQUIRED
runtime_code_changed: false
source_manuscript_changed: false
live_api_required: false
external_runtime_required: false
```

## 1. Executive Verdict

Verdict: `ACCEPT_WITH_MAJOR_REVISIONS`.

The manuscript is coherent enough to remain the active internal draft, and the P21/P22 claim boundaries mostly prevent direct overclaiming. It is not ready for submission. The main weakness is not a single unsafe claim; it is the aggregate paper posture. The manuscript now contains strong theory, a careful metric bridge, and a runtime-audit scaffold, but the evidence sections still read partly like an engineering scaffold report. Before external submission, the paper needs a tighter narrative around what is proven, what is only proposed, what is implemented as offline audit infrastructure, and what remains unexecuted scientific validation.

## 2. One-Paragraph Paper Thesis

The paper claims that dispatch-time context projection in multi-agent LLM systems can be isolated as a per-round, per-agent, token-budgeted subset-selection problem over content items; that a V-information value function provides a useful formal object for conditional weak-submodular theory under explicit regime assumptions; that theorem-level claims do not transfer automatically to deployed pipelines; and that a metric bridge plus proxy-regime labeling protocol can make runtime context projection auditable, replayable, and conservatively claim-gated. The manuscript mostly supports this thesis as a conditional theory and measurement-protocol paper, but it does not yet support any deployed performance, measurement validation, or deployed V-information certification claim.

## 3. Contribution Clarity Review

| contribution item | rating | review |
| --- | --- | --- |
| CPS as a measurement / runtime-audit scaffold | partially clear | Section 6 and the P21 tables make the audit scaffold explicit, but the number of artifacts risks reading as implementation breadth rather than paper contribution. |
| CPS as a context projection selection problem | clear | Sections 1 and 2 define the dispatch-time, per-agent, token-budgeted content-selection problem well. |
| Conditional theory | clear | Section 3 is careful about Condition A, pairwise-additive assumptions, and the theorem boundary. |
| Metric bridge | clear | Section 3.4 is a strong contribution and clearly separates formal, proxy, pipeline, runtime, and metric-claim layers. |
| Proxy-regime certification | partially clear | The concept is bounded, but the word "certification" remains reviewer-sensitive and needs a concise local definition every time it enters headline text. |
| Replayable evidence | partially clear | P15-P17 make replay evidence concrete, but the main manuscript does not yet separate "implemented evidence infrastructure" from "executed empirical evidence" crisply enough. |
| Claim gate | clear | The conservative claim gate table and limitations section make the denied claims visible. |

## 4. Narrative Coherence Review

The intended flow is:

```text
Problem -> CPS formalization -> conditional theory -> metric bridge -> runtime-audit scaffold -> proxy-regime evidence -> replay evidence -> limitations
```

The manuscript broadly follows that order, but three narrative issues remain.

| issue | location | review | recommended revision |
| --- | --- | --- | --- |
| Evidence arrives before the reader has a clean "evidence status" map. | Sections 4.3.1 and 6.2 | The reader sees synthetic benchmark design, proxy-regime rows, offline demo language, and artifact tables before receiving a compact statement of which evidence is executed versus proposed. | Add a small "Evidence status" paragraph or table before the P21 evidence additions. |
| Tables interrupt the argument. | Sections 3.4, 4.3.1, 6.2 | The claim gate table is useful, but three new tables in the body can feel like a compliance appendix inserted into a theory paper. | Keep a shortened claim gate table in main; move or compress proxy matrix and artifact details. |
| Engineering detail competes with contribution framing. | Section 6.2 | `EvidenceLedger`, `ClaimGateReport`, `MetricBridgeGate`, `ReplayEvidencePackage`, `PaperEvidenceSummary`, and `EndToEndEvidenceDemo` are useful internally but look like code artifacts in the main paper. | Retain the four core runtime artifacts in body and move P12-P17 artifact inventory to appendix/companion evidence. |
| Bridge-to-experiment transition is underspecified. | Section 4.3.1 | The manuscript specifies a benchmark and then mentions an implemented offline evidence chain, but the relation between benchmark execution and scaffold execution can be clearer. | State explicitly that P17 exercises the audit chain, not the benchmark's scientific pass conditions. |
| Limitations are strong but late. | Section 9 | The strongest non-claim boundary appears near the end. Reviewers may have already formed an overclaim concern. | Add a concise non-claim sentence earlier, near the contribution list or Section 4.3.1. |

## 5. Claim-Boundary Review

| phrase | nearby context | classification | risk | recommended replacement |
| --- | --- | --- | --- | --- |
| `measurement_validated` | Section 3.4 claim gate and Section 9 limitations. | `SAFE_DENIED_CLAIM` | Low. It appears as a denied claim. | Keep. |
| measurement validation | Section 3.4 claim gate rows for stale/missing bridge and live/runtime success. | `SAFE_DENIED_CLAIM` | Low. It is denied, not claimed. | Keep. |
| scientific validation | Sections 3.4, 4.3.1, 6.2, 9. | `SAFE_DENIED_CLAIM` | Low. It is consistently negated. | Keep. |
| deployed V-information certification | Sections 3.4, 4.3.1, 6.2, 11. | `SAFE_DENIED_CLAIM` | Low to medium. The denial is clear, but the phrase appears often. | Keep denials; reduce repeated table rows if the body feels defensive. |
| certified proxy-greedy-valid under a fresh metric bridge | Section 4.2 two-axis decision table. | `AMBIGUOUS_NEEDS_REWRITE` | Medium. The guardrail is present, but "certified" in a table label may still read as stronger than intended. | "proxy-greedy-valid under fresh metric-bridge evidence" |
| `Vinfo_proxy_certified` | Section 4.2 examples. | `SAFE_CONDITIONAL_CLAIM` | Medium. It is explicitly conditional, but the identifier looks claim-bearing. | Add "label name" or "diagnostic label" if retained. |
| composite proxy-regime certification | Section 4.4 heading and union-bound paragraph. | `SAFE_CONDITIONAL_CLAIM` | Medium. The heading is now scoped, but the word "certification" remains sensitive. | "composite proxy-regime evidence gate" if the submission venue is skeptical. |
| deployed V-information submodularity | Section 4.3.1 denial and Section 11 conclusion. | `SAFE_DENIED_CLAIM` | Low. It is explicitly not certified. | Keep. |
| live API or external runtime success alone is not measurement validation | Section 9 limitations. | `SAFE_DENIED_CLAIM` | Low. It is correctly denied. | Keep. |

No `UNSAFE_OVERCLAIM` was found. One class of phrasing, especially "certified proxy-greedy-valid," remains `AMBIGUOUS_NEEDS_REWRITE` because it is locally guarded but still reviewer-sensitive.

## 6. Evidence Adequacy Review

| Claim | Current support | Evidence type | Missing evidence | Allowed wording | Forbidden wording |
| --- | --- | --- | --- | --- | --- |
| Runtime-audit scaffold exists | P10-P17 modules, P17 docs, P21 manuscript table. | Offline engineering scaffold and documentation. | External runtime deployment and operator approval. | "offline runtime-audit scaffold implemented" | "production runtime integration complete" |
| Deterministic replay package exists | P15 module/docs/tests. | Deterministic packaging evidence. | Real dispatch traces and scientific validation data. | "replay package builder exists" | "replay package validates measurement" |
| Proxy-regime diagnostic matrix exists | P14 module/docs/tests and P21 table. | Synthetic/proxy diagnostic matrix. | Executed benchmark results and external validity evidence. | "proxy-regime diagnostic matrix" | "deployed V-information certification" |
| Conservative claim gate exists | P12/P13 docs/tests and manuscript table. | Audit/claim-boundary evidence. | Human labels, kappa, contamination closure, fresh bridge validation. | "conservative claim gate denies unsupported claims" | "claim gate proves measurement validity" |
| Metric bridge gate exists | P13 docs/tests and Section 3.4. | Bridge-audit evidence. | Fresh deployed metric bridge evidence. | "metric bridge gate constrains claim level" | "metric bridge is validated in deployment" |
| Paper evidence summary exists | P16 docs/tests. | Manuscript-facing summary tooling. | Scientific validation evidence. | "paper summaries surface evidence and denied claims" | "paper summaries upgrade claims" |
| CPS improves real deployed multi-agent performance | Literature motivation and protocol design only. | Indirect motivation. | Live or offline real-trace comparative study. | "CPS targets a plausible performance bottleneck" | "CPS improves deployed performance" |
| CPS is `measurement_validated` | No support. Explicitly denied. | None. | Human labels, kappa, contamination pass, fresh bridge, protocol execution. | "`measurement_validated` is not claimed" | "CPS is measurement_validated" |
| Deployed V-information submodularity is certified | No support. Explicitly denied. | Conditional theory only. | Proof for deployed model family or strong empirical bridge evidence. | "conditional proxy-regime evidence" | "deployed V-information submodularity is certified" |
| Live API validation is complete | No support. Explicitly outside scope. | None. | Live API study and operator-approved protocol. | "live API validation remains future work" | "live validation is complete" |
| Human-labeled validation is complete | No support. Explicitly missing. | Protocol only. | Human labels and kappa. | "human-labeled validation remains required" | "human-validated" |

## 7. Table Integration Review

| table | recommendation | rationale | row-level notes |
| --- | --- | --- | --- |
| Conservative Claim Gate Rules | should stay in main body, shortened | It directly protects the bridge statement. | Merge live API and external runtime rows; merge missing labels and missing kappa only if the text still names both. |
| Proxy-Regime Certification Matrix | should move partly to appendix or be shortened | It duplicates the synthetic benchmark table and mixes positive regimes with boundary rows. | Keep only the three synthetic regimes in main; move contamination/labels/kappa/bridge/artifact boundary rows to claim-gate table or appendix. |
| CPS Runtime-Audit Artifacts | should be shortened | The first four artifacts are manuscript-relevant; P12-P17 implementation objects are more appendix-like. | Keep `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, `MetricBridgeWitness`, and possibly `ProjectionBundleV1` in main; move evidence ledger/report/package/demo rows to appendix/companion patch. |

## 8. Engineering Bloat Review

The manuscript currently reads as a hybrid of a clean measurement protocol paper and an engineering scaffold report. It does not read like a generic agent framework, because the scope guards are repeated and the formal object remains dispatch-time context projection. However, Sections 4.3.1 and 6.2 now expose enough implementation artifact names that reviewers may ask whether the paper's contribution is theory, measurement protocol, or code scaffolding.

Appendix-only or companion-only material should include detailed replay-package outputs, P15/P16/P17 writer outputs, milestone review history, and implementation-specific class names that do not need to define the scientific argument. The main paper should emphasize the measurement protocol: formal object, bridge conditions, diagnostic regimes, runtime observability requirements, claim gate, and limitations.

## 9. Reviewer Attack Simulation

| reviewer concern | why plausible | current manuscript response | sufficient? | recommended revision |
| --- | --- | --- | --- | --- |
| Synthetic evidence has weak external validity. | Synthetic regimes do not reflect real dispatch traces. | The manuscript says the benchmark is a structural floor and not deployment validity. | Partially. | Add a short "external validity gap" sentence near the proxy matrix. |
| No human labels are present. | Measurement validation usually needs human ground truth. | Claim gate denies `measurement_validated`; Section 9 states labels are missing. | Yes for claim boundary, no for submission strength. | Make human-label work a P0/P1 empirical next step. |
| No kappa is reported. | Agreement is needed for human-labeled validation. | Claim gate denies validation without kappa. | Yes for boundary. | Add kappa to the evidence-status table. |
| No live API validation is complete. | Deployment-facing framing invites runtime evidence expectations. | Section 9 denies live API success alone and P09 remains blocked. | Partially. | Clarify that P17 is a dry offline chain, not live validation. |
| Metric bridge validity is the real bottleneck. | The bridge is necessary for V-information proxy claims. | Section 3.4 is strong and Section 9 names bridge limits. | Mostly. | Put bridge status in a concise evidence-status box. |
| This is just engineering scaffolding. | Many artifact/module names appear in body tables. | The paper says artifacts are audit interfaces, not validation. | Partially. | Move implementation artifact inventory to appendix and foreground the measurement protocol. |
| Long-context models make CPS obsolete. | Million-token contexts weaken the budget motivation. | Introduction argues selection remains irreducible under compression/sparse access. | Mostly. | Add one line tying long-context cost/attention locality to the formal budget object. |
| Proxy-regime certification is overclaimed. | "Certification" reads strong. | The paper repeatedly says not deployed V-information certification. | Partially. | Consider renaming some body labels to "proxy-regime diagnostic evidence." |
| The theorem may be too conditional to matter. | Condition A is not proven for deployed models. | The paper admits this and positions itself as conditional theory. | Mostly. | Strengthen the "why conditional theory is still useful" transition before Section 4. |
| Extraction quality could dominate selection quality. | The candidate pool may omit high-value findings. | Section 5 treats extraction as a separate bottleneck. | Mostly. | Add a compact status note that Sprint A extraction audit is not executed. |

## 10. Required Revision List

### P0 Blocking Before Submission

| target section | problem | proposed fix | risk if not fixed |
| --- | --- | --- | --- |
| Abstract / Introduction | The paper's empirical status is not visible early enough. | Add a concise evidence-status sentence: conditional theory and offline audit scaffold are present; scientific validation is not. | Reviewers may expect deployed validation and judge the evidence as inadequate. |
| Section 4.3.1 | The offline evidence-chain paragraph sits next to the synthetic benchmark and may be confused with executed benchmark evidence. | State that P17 exercises audit plumbing, not the benchmark pass conditions. | Reviewers may read dry-run evidence as empirical benchmark support. |
| Section 6.2 | Runtime artifact table is too implementation-heavy for the main body. | Keep the four core artifacts plus `ProjectionBundleV1`; move P12-P17 artifact inventory to appendix. | The paper reads like a code artifact catalog. |
| Section 9 / Conclusion | Missing labels, kappa, contamination, and fresh bridge evidence are acknowledged but not summarized as a single evidence gap. | Add a compact claim-to-evidence status table or paragraph. | Reviewer may miss why `measurement_validated` is denied. |

### P1 Important Before Supervisor Review

| target section | problem | proposed fix | risk if not fixed |
| --- | --- | --- | --- |
| Section 3.4 | Claim gate table is useful but long. | Merge redundant rows and keep the core failure modes. | Main bridge statement feels administrative. |
| Section 4.2 | "certified proxy-greedy-valid" remains reviewer-sensitive. | Rename to "proxy-greedy-valid under fresh metric-bridge evidence." | A reviewer may interpret "certified" as overclaim. |
| Section 4.3.1 | Proxy matrix combines regime rows with boundary rows. | Keep positive synthetic regimes in body; move boundary rows to appendix or claim gate. | Narrative interruption and duplicated denial rows. |
| Section 5 | Extraction audit protocol is strong but unexecuted. | Add explicit "designed, not executed" status sentence. | Reviewer may ask where the extraction numbers are. |
| Section 8 | Future work list is broad. | Prioritize P04 labels/kappa/contamination/bridge and P09 runtime integration. | The next-step path appears diffuse. |
| Section 7 | Related work is broad and strong but dense. | Add a short summary paragraph at start or end saying exactly which gap remains. | Contribution signal may be diluted. |

### P2 Polish / Optional

| target section | problem | proposed fix | risk if not fixed |
| --- | --- | --- | --- |
| Whole manuscript | Some copied text shows encoding artifacts such as `鈥?`. | Normalize encoding before external distribution. | Surface polish issue. |
| Tables | Several tables use implementation identifiers. | Prefer paper-facing labels in body and code identifiers in appendix. | Reviewers may perceive implementation bloat. |
| Conclusion | The conclusion is accurate but dense. | Add one sentence restating "conditional theory plus bridge protocol." | Contribution may be less memorable. |
| Appendix | P18 companion material is not integrated as an appendix. | Add an appendix pointer if P24 moves material out of the body. | Evidence chain may be harder to locate. |

Counts: P0 = 4, P1 = 6, P2 = 4.

## 11. Minimal Patch Plan For P24

Do not apply this in P23.

1. Edit Abstract / Introduction to add one early evidence-status sentence.
2. In Section 3.4, shorten the claim gate table by merging redundant operational rows while preserving labels/kappa/bridge/contamination boundaries.
3. In Section 4.2, replace the label `certified proxy-greedy-valid under a fresh metric bridge` with less claim-heavy wording.
4. In Section 4.3.1, clarify that the P17 offline evidence chain is audit plumbing only, and move boundary rows from the proxy matrix into appendix or claim-gate references.
5. In Section 6.2, shorten the artifact table to the four core artifacts plus `ProjectionBundleV1`; move P12-P17 implementation artifacts to appendix/companion evidence.
6. In Section 9, add a compact evidence-gap summary covering human labels, kappa, contamination closure, fresh bridge evidence, P04, and P09.
7. Add or update an appendix pointer to `docs/paper/context_projection_v10_p18_tables_and_experiment_patch.md` for full evidence tables.

## 12. Final Recommendation

Primary next phase: **P24 Apply Manuscript Narrative and Claim-Boundary Revision**.

This is the right next step because the manuscript does not need new runtime engineering before the next paper revision. It needs a careful paper edit that compresses engineering detail, foregrounds the measurement protocol, clarifies evidence status earlier, and preserves the conservative claim gate. A live API scientific closure protocol would be premature until the manuscript is cleaner about what the current offline evidence does and does not support.

## 13. P23 Claim Boundary

- P23 is review-only.
- P23 does not modify `docs/archive/context_projection_revised_v10.md`.
- P23 does not upgrade claim levels.
- P23 is not scientific validation.
- Engineering success is not scientific validation.
- Synthetic success is not deployed V-information certification.
- Replay package completeness is not scientific validation.
- Paper-facing summaries do not upgrade claim levels.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- `measurement_validated` is not claimed.

## 14. Validation Commands And Results

Commands run for P23 acceptance:

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
