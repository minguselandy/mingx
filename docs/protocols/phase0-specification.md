# Phase 0 Specification: Context Projection Selection — Experimental Cycle Lock-In

**Associated paper:** Context Projection Selection in Multi-Agent Systems: Conditional Weak-Submodular Theory and Regime Diagnostics (`paper-draft-v5_5-taskB-final-gemini-minimal-q7revised-polish2.md`)

**Document status:** Phase 0 exit artifact, pending user confirmation on budget parameters (§4, §5).

---

## Document Purpose

This document records the Phase 0 decisions for the experimental cycle operationalizing the theoretical framework developed in the associated paper. Phase 0 exit requires a one-page specification of (1) target domain, (2) epistemic priority, (3) finding granularity, (4) annotation budget, (5) computational budget, (6) infrastructure status, and (7) operational definitions of the quantities under measurement. The document fixes these parameters and enumerates the portability constraints and known scope limitations under which Phase 1 will operate.

---

## 1. Domain Lock-In

**Pilot domain:** MuSiQue (Trivedi et al., 2022). HotpotQA retained as optional secondary domain if cross-dataset generalization probing becomes warranted during Phase 2 design.

**Deployment target:** openWorker traces (Phase 4 and beyond).

**Sequencing rationale.** MuSiQue furnishes a partially objective annotation oracle (supporting-versus-distractor paragraph labels at native granularity) that openWorker cannot provide, which makes MuSiQue the cheapest domain in which to falsify the extraction uniformity hypothesis. The falsification asymmetry is the structural feature underlying this choice: failure on MuSiQue implies failure on openWorker as a necessary condition with high transfer fidelity, but success on MuSiQue implies success on openWorker only weakly because MuSiQue's clean oracle masks the subjective-importance failure modes that deployment-path extraction exhibits.

---

## 2. Epistemic Priority

The primary purpose of this experimental cycle is to validate **binding assumption #1** from the theory-to-experiment transition analysis: the **extraction uniformity assumption** articulated in Section 5 of the paper. If extraction completeness varies substantially across complexity strata, the formal guarantee over the extracted candidate pool M does not transfer to the underlying information space M*, interrupting the theorem-to-deployment chain at its upstream bottleneck.

Binding assumption #2 (regime-detection validity of γ̂_{q,LCB}) and binding assumption #3 (Shannon-MI versus V-information divergence) are explicitly deferred to subsequent cycles, conditional on the outcome of extraction uniformity validation.

---

## 3. Finding Granularity

**Pilot granularity:** Paragraph-level, inheriting MuSiQue's native unit structure.

**Follow-on granularity:** Proposition-level via atomic-fact extraction, introduced after paragraph-level probe exits and conditional on Phase 1 findings.

**Operationalization at paragraph granularity.** A finding m_i in M corresponds to a paragraph admitted to the retrieval candidate pool for a given MuSiQue question. Per-finding metadata includes: token count tokens(m_i), paragraph source document, and the MuSiQue-native support flag (supporting/distractor).

**Value stratification at paragraph granularity.** The high-value versus low-value axis required by Section 5.3 of the paper is operationalized via leave-one-out counterfactual value:

    δ_loo(m_i) = P_V(y | X_context) − P_V(y | X_context \ {m_i})

where y is the MuSiQue ground-truth answer token sequence, X_context is the concatenated content of the full context, and V is the fixed predictive family (the deployed model tier). The high-value stratum is the top tertile of δ_loo; the low-value stratum is the bottom tertile; the middle tertile is discarded as buffer to sharpen the high/low contrast.

This operationalization is computable automatically with no per-instance human annotation for the value axis itself. Human annotation is required only for face-validity adjudication on a subsample and edge-case arbitration when δ_loo is near the tertile boundaries.

---

## 4. Annotation Budget and Sampling Design

**Probe size derivation.** Hop-stratified sampling combined with the annotator-hours binding constraint forces a specific operating point. The Cohen's κ ≥ 0.6 target requires approximately 30 paired annotations per stratum for stable estimation, which fixes the per-stratum N floor. With three hop-depth strata (2-hop, 3-hop, 4-hop) and 30 per stratum, the total probe size is N = 90, at the upper bound of the initial 50–100 band. A probe below approximately N = 90 yields per-stratum κ estimates too noisy to support the inter-rater reliability gate under hop-stratification; a probe substantially above N = 90 breaches the annotator-hours ceiling unless automation is pushed beyond the design specified here.

**Sampling composition.** 30 questions per hop-depth stratum × 3 strata = 90 total questions, sampled uniformly at random within each stratum from the MuSiQue development set. The 3-hop stratum serves as the primary analysis cell because it sits at the empirically-observed steep-degradation boundary identified in Wu et al. (2024); 2-hop and 4-hop serve as lower-complexity and higher-complexity comparison cells respectively.

**Automation-heavy labor division.** Annotator labor is restricted to two narrow tasks:

- **Edge-case arbitration** on instances whose automated δ_loo classification falls within a defined tolerance band around tertile boundaries, approximately 20% of the sample by construction (18 instances at N = 90).
- **Face-validity verification** on a random subsample across all strata, approximately 10% of the sample (9 instances at N = 90).

**Annotator hierarchy (mixed pool with expert arbitration layer).** The annotator cohort consists of two primary annotators drawn from the mixed pool (graduate student level or qualified contractor level) and one expert arbitrator (domain-expert researcher). The hierarchy generates three distinct inter-rater reliability measurements:

- κ_primary, measured between the two primary annotators on the full arbitration set, testing protocol clarity and baseline consistency.
- κ_primary-expert, measured between each primary annotator and the expert on expert-audited cases, testing systematic deviation and directional bias.
- κ_automated-expert, measured between automated δ_loo tertile classification and expert adjudication on a randomly-sampled expert-audited subset spanning both arbitration-flagged and non-flagged cases, testing the core automation-substitution hypothesis.

The Phase 1 pass criterion is κ_automated-expert ≥ 0.6, which is the operationally consequential measurement for the automation-push design validity. κ_primary and κ_primary-expert ≥ 0.6 are secondary pass criteria testing protocol health.

**Phase 1 annotator-hour budget.** Approximately 7 annotator-hours per primary annotator across two primary annotators, plus approximately 4.5 annotator-hours for expert arbitration on approximately 18 flagged cases at 15 minutes per case. Total approximately 18.5 annotator-hours across three personnel — within the 10–20 hour budget band for primary annotators and adding a modest expert-layer surcharge. The budget assumes approximately 15 minutes per paragraph-context evaluation at typical annotation throughput.

**Phase 3 pilot:** 40–80 annotator-hours at approximately 20% of full-study sample size, calculated in Phase 2 from Phase 1 variance estimates.

**Phase 4 full study:** Deferred. Estimated range 200–500 hours pending Phase 2 sample-size calculation.

---

## 5. Computational Budget

**Two-stage measurement-error-correction design.** The δ_loo operationalization uses V_frontier as the high-precision reference on a calibration subsample and V_small as the low-variance full-coverage measurement on the full N = 90. The subsample consists of 10 randomly-sampled instances per hop-depth stratum (30 total), drawn from within the N = 90 without augmentation. Calibration coefficients (a_stratum, b_stratum) are estimated per stratum via linear regression δ_frontier ≈ a + b · δ_small on the subsample, with residual normality tested as a Phase 1 diagnostic and escalation to nonlinear bridge form (polynomial or isotonic) triggered if residual structure appears.

**Phase 1 probe forward-pass budget.**

- **V_small on the full N = 90.** 90 questions × (~15 paragraphs + 1 baseline) × 5 LCB repeats ≈ 7,200 forward passes.
- **V_frontier on the 30-instance calibration subsample.** 30 questions × 16 evaluations × 5 LCB repeats ≈ 2,400 forward passes, additive to the V_small calls on the same 30 instances.
- **Total:** approximately 9,600 forward passes, of which approximately 25% (2,400) are frontier-tier calls and 75% (7,200) are smaller-tier calls.

**K_LCB = 5** is the minimum for stable LCB estimation under the quantile-q = 0.1 design specified in the paper's Section 4.1 and should not be reduced to accommodate budget constraints. Reduce per-question paragraph count or overall N before reducing K_LCB.

**Phase 3 pilot:** Scaled approximately 5× from Phase 1 estimate, with the same V_frontier-to-V_small ratio, approximately 5 × 10⁴ total forward passes.

**Cost-optimization note.** CI-Value evaluation on MuSiQue reduces to extracting P_V(y | X_S), where y is the ground-truth answer sequence. This admits direct probability scoring via constrained decoding or forced-decode log-probability extraction rather than full free-form generation, reducing per-evaluation cost by approximately an order of magnitude relative to generation-based CI-Value in openWorker. Under this optimization, the Phase 1 inference cost is modest in absolute terms (approximately $10–30 in API costs depending on specific V_frontier and V_small model choices), which means computational budget is not the binding Phase 1 constraint — annotator-hours and expert-arbitration throughput are.

---

## 6. Infrastructure Audit

**Phase 1 parallel track.** Initiate an audit of openWorker trace-field availability for the five fields identified in the theory-to-experiment migration analysis: candidate pool, greedy trace, selected set, materialized context, and extraction alignment. This audit carries zero opportunity cost against Phase 1 execution and preserves optionality for the MuSiQue-to-openWorker migration timeline.

**Phase 1 blocking.** Infrastructure status does not block Phase 1 because MuSiQue supplies all required fields from the benchmark harness. Infrastructure becomes binding in Phase 4 and the audit outcome determines whether the migration is a one-week port or a multi-month engineering project.

---

## 7. Portability Constraints (design invariants for Phase 1)

The following design invariants must be preserved in Phase 1 so that Phase 4 (openWorker migration) and the follow-on proposition-level granularity experiment proceed without protocol restructuring.

**Granularity-agnostic evaluation harness.** The CI-Value evaluation implementation must operate on a selected set regardless of whether its units are paragraphs or propositions. No granularity-specific assumptions may be baked into the scoring pipeline or diagnostic computation.

**Relative rather than absolute value thresholds.** Stratum assignment (c_high, c_low) is defined by tertile of the counterfactual-delta distribution rather than by absolute δ thresholds, so stratification transfers across granularities and domains without re-calibration.

**Unit-type metadata on all records.** The annotation schema carries a `unit_type` field with values paragraph, proposition, or finding so that aggregated results from mixed-granularity studies can be disambiguated post-hoc.

**Retrieval-stage trace export.** Phase 1 logs which paragraphs were admitted to M by the retrieval-plus-reranking stage versus which were filtered out, so that retrieval-stage extraction uniformity can be measured independently of selection-stage greedy choices downstream.

---

## 8. Known Scope Limitations (explicit, tracked)

**Operational-layer substitution.** On MuSiQue, the upstream filter being audited is the retrieval-plus-reranking stage rather than the openWorker extraction gate. These two layers can exhibit different bias profiles: retrieval-stage bias tends to manifest as terminology mismatch and semantic subtlety, whereas extraction-gate bias tends to manifest as compression-target constraints and probability-distortion artifacts. Phase 2 results therefore constitute evidence for retrieval-layer uniformity, not directly for extraction-gate uniformity. Phase 4 re-audit is required to close this gap.

**Optimistic-bias risk for openWorker transfer.** Positive Phase 1 results are weakly transferable to openWorker because the MuSiQue oracle is clean. The Phase 2 design document must specify the conditions under which MuSiQue results are considered generalizable to openWorker versus pilot-confirming-only.

**Counterfactual-value operationalization drift.** The leave-one-out operationalization of value is sensitive to the choice of predictive family V. If openWorker deployment uses a different model tier than the MuSiQue evaluation, the value axis shifts and stratification is not directly portable; Phase 4 must re-stratify under the openWorker-native V.

**MuSiQue-in-Qwen3 contamination risk.** MuSiQue is public and may have been present in Qwen3 pretraining. Under the locked DashScope/Qwen3 substitution this becomes a tracked scope limitation rather than a background assumption. Phase 1 therefore treats the baseline `log P(y* | q)` contamination diagnostic as a mandatory gate before any bridge result can be interpreted as measurement-valid.

**Diagnostic coverage is partial in Phase 1.** Extraction uniformity is the primary focus; γ̂_{q,LCB} and pairwise interaction information are measured only on the subsample required to establish trace infrastructure and estimator stability. Full regime-detection validation is Phase 5 and beyond.

---

## 9. Phase 0 Exit and Remaining Phase 1 Protocol-Authoring Parameters

**Phase 0 exit.** This document constitutes Phase 0 exit. All specification dimensions are locked:

- **Domain:** MuSiQue pilot → openWorker follow-on.
- **Epistemic priority:** binding assumption #1 (extraction uniformity).
- **Finding granularity:** paragraph pilot → proposition follow-on.
- **Sampling design:** hop-stratified, 30 per stratum, N = 90 total.
- **Annotator hierarchy:** mixed pool with expert arbitration layer, three-level κ measurement.
- **V selection:** two-stage measurement-error-correction design, V_frontier on 30-instance calibration subsample + V_small on full N = 90, linear-per-stratum bridge with residual-diagnostic escalation.
- **Edge-case tolerance:** ±0.5σ default band, approximately 20% arbitration rate.
- **Annotator budget:** approximately 18.5 hours across three personnel (14 hours primary + 4.5 hours expert).
- **Computational budget:** approximately 9,600 forward passes, approximately 25% frontier-tier and 75% smaller-tier.
- **Infrastructure status:** openWorker trace-field audit parallel-tracked, non-blocking.

**Provider and V-selection lock.** The execution environment fixes the provider/model family for Phase 1. V_frontier is Qwen3-32B (`qwen3-32b`) and V_small is Qwen3-14B (`qwen3-14b`), both accessed through DashScope's OpenAI-compatible endpoint with `enable_thinking = false` and token-level log-probability extraction enabled. In the repository implementation, this lock is surfaced as the default API profile `dashscope-qwen-phase1` under `api/settings.py`; the implementation abstraction does not relax the protocol lock. This is an infrastructural lock, not a remaining protocol-authoring choice.

**MuSiQue split.** Development set, preserved as the scientific working split with an explicit contamination caveat under Qwen3.

**Phase 1 execution timeline.** Parallel with the openWorker infrastructure audit.

**Sequencing.** The next artifact is the Phase 1 probe protocol document, which operationalizes the locked Phase 0 design into an executable measurement procedure. This document should be developed in alternation with the Phase 2 experimental design document so that probe findings can feed sample-size parameters back into Phase 2 rather than proceeding in strict sequential construction.
