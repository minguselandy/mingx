# Phase 1 Probe Protocol: Extraction Uniformity Measurement on MuSiQue

**Associated documents:** Phase 0 Specification (`phase0-specification.md`), paper draft (`paper-draft-v5_5-taskB-final-gemini-minimal-q7revised-polish2.md`).

**Document status:** Phase 1 execution protocol, ready for implementation pending confirmation of the four implementation-level decisions documented in the Phase 0 protocol-authoring parameter resolution.

---

## Scope and Non-Scope

This document specifies the executable procedure for the Phase 1 instrumentation-feasibility probe. The probe tests three of the four links in the measurement validity chain identified at Phase 0 exit: V_small measurement stability (Link 1), V_frontier-to-V_small bridge validity (Link 2), and automated-to-expert classification substitution fidelity (Link 3). Link 4 (MuSiQue-to-openWorker transfer) is structurally untestable in Phase 1 and is addressed through Phase 4 re-audit.

The probe is not a hypothesis test on the extraction uniformity assumption itself, which is the purpose of Phase 3 pilot execution and Phase 4 full-study execution. The probe is a measurement-apparatus validation: it establishes whether the instrumentation produces stable, interpretable, and reliable measurements before annotation or inference budget is committed to the hypothesis test proper.

---

## Section A: Data Preparation

### A.1 MuSiQue dev-set access and loading

The probe draws from the MuSiQue-Ans development split, which is the standard publicly-available MuSiQue release distributed by the dataset authors. The dev set contains approximately 2,417 questions stratified across 2-hop, 3-hop, and 4-hop complexity tiers. Each question is accompanied by a canonical answer string, a set of approximately 20 paragraphs drawn from Wikipedia, and per-paragraph `is_supporting` flags provided by MuSiQue's native annotation.

The dev split is loaded into a reproducible working store with the following schema preserved per question: `question_id`, `question_text`, `answer_text`, `hop_depth`, `paragraphs[]` (each paragraph carrying `paragraph_id`, `title`, `text`, and `is_supporting` flag). A content hash over the full dev split is recorded at load time to detect silent data drift between Phase 1 execution and Phase 2 consumption.

### A.2 Hop-stratified sampling procedure

The probe consists of N = 90 questions drawn from the dev split with a balanced hop-depth composition: 30 questions at 2-hop depth, 30 at 3-hop depth, and 30 at 4-hop depth. Sampling is simple random sampling without replacement within each hop-depth stratum, seeded with a fixed random seed recorded in the protocol execution log to support reproducibility.

The sampling procedure rejects and re-draws any question whose paragraph pool size falls below 15 or exceeds 25, which bounds the per-question inference cost and ensures that paragraph-order permutation has meaningful effect. This rejection criterion is documented in the execution log along with the final accepted sample.

### A.3 Per-question paragraph-pool extraction

For each sampled question, the full paragraph pool is extracted in its native order as presented by MuSiQue. The native order is preserved as `canonical_order` in the per-question record. Additional orderings are generated as described in Section B.4.

---

## Section B: Automated Value Measurement

### B.1 V_frontier and V_small model specifications

The frontier predictive family is instantiated as Claude Opus 4.7 (`claude-opus-4-7`) accessed via the Anthropic API. The smaller predictive family is instantiated as Claude Haiku 4.5 (`claude-haiku-4-5-20251001`). Both models are queried at temperature 0 with forced-decode log-probability extraction to ensure deterministic point estimates per paragraph ordering. API version pins and exact model strings are recorded in the execution log.

The choice of intra-family tiering (Opus 4.7 and Haiku 4.5 both from the Claude 4.x lineage) preserves architectural and training-data coherence between V_frontier and V_small, which is the structural condition under which the linear-per-stratum bridge function is most likely to hold.

### B.2 Forced-decode log-probability extraction protocol

For a given (question, paragraph subset, ordering) triple, the protocol computes `log P_V(y* | q, X_S)` by constructing a prompt of the form:

```
<paragraphs in ordering>

Question: <question_text>
Answer:
```

and forcing the decoder to produce the MuSiQue canonical answer string. The sum of token-level log-probabilities along the forced decode yields `log P_V(y* | q, X_S)`. Tokenization variance between V_frontier and V_small is resolved by computing log-probabilities in the model-native tokenization and comparing across V choices only via the aggregated per-answer scalar, not via token-level alignment.

The baseline `log P_V(y* | q)` (question alone, no paragraphs) is computed once per question per V, and cached for reuse across all subset computations for that question.

### B.3 δ_loo computation algorithm

For each question, for each paragraph m_i in the pool, for each of the K_LCB = 5 orderings specified in Section B.4, the protocol computes:

    δ_loo^{(k)}(m_i) = log P_V(y* | q, X_full^{(k)}) − log P_V(y* | q, X_full^{(k)} \ {m_i})

where X_full^{(k)} denotes the full paragraph pool in the k-th ordering and X_full^{(k)} \ {m_i} denotes the same ordering with m_i omitted (and the remaining paragraphs re-concatenated in their relative order). The result is a K_LCB × N_paragraphs matrix of δ_loo measurements per question.

The aggregated per-paragraph δ_loo is computed as the LCB quantile at q = 0.1:

    δ̂_loo(m_i) = Quantile_{0.1}({δ_loo^{(k)}(m_i) : k = 1, ..., K_LCB})

This matches the estimator form specified in the paper's Section 4.1. The LCB construction controls silent overestimation under paragraph-order variation.

### B.4 K_LCB repetition via paragraph-order permutation

The K_LCB = 5 repetitions correspond to 5 paragraph orderings drawn as follows. The first ordering is always `canonical_order` as provided by MuSiQue. The remaining 4 orderings are drawn as random permutations of the paragraph pool, seeded deterministically from the question_id so that the same 5 orderings are reproducible across execution runs. The full ordering set is recorded per question in the execution log.

This design specifies paragraph-order permutation as the variance source for the LCB construction, which measures positional-attention robustness of the value measurement. The choice is motivated by the well-documented positional effects in transformer attention and by the direct relevance of position sensitivity to the extraction-uniformity hypothesis under test.

**Scope limitation of the variance source.** The protocol deliberately measures positional-attention robustness and does not measure composition-robustness. Composition-robustness (stability of δ_loo under variation in which other paragraphs are present in the context) would require a subset-sampling variance source in which K_LCB orderings correspond to K_LCB different random context compositions of size N_paragraphs − 2. The two properties are orthogonal: a δ_loo measurement that is stable under reordering can be fragile to subset variation, and vice versa. This scope limitation is inherited by Phase 2 and Phase 3 and must be named as a caveat in any Phase 2 sensitivity analysis. The rationale for accepting this limitation in Phase 1 is that paragraph-order permutation is the more conservative measurement for positional-attention artifacts that could corrupt extraction-uniformity inference, and subset-sampling can be added as a second variance source in Phase 2 or Phase 3 if Phase 1 diagnostics suggest the position-only measurement is inadequate.

### B.5 Measurement storage schema

Per-question records are stored with the following schema: `question_id`, `hop_depth`, `V_model`, `baseline_logp`, `orderings[]` (each carrying the ordering permutation and per-paragraph `logp_full`, `logp_loo`, `delta_loo`), and `delta_loo_LCB` (the aggregated LCB quantile per paragraph). Storage is append-only and versioned to support partial-run resumption if inference execution is interrupted.

---

## Section C: Bridge Function Estimation

### C.1 Calibration subsample drawing

The calibration subsample consists of 30 instances drawn from the N = 90 probe: 10 instances per hop-depth stratum, selected by simple random sampling within each stratum under the same reproducibility seed as Section A.2. The calibration subsample is a subset of the full probe and not an augmentation cohort, which means V_small measurements on these 30 instances are already produced by the Section B execution and only V_frontier measurements are additionally required.

### C.2 Linear-per-stratum regression procedure

For each hop-depth stratum, a linear bridge is fit via ordinary least squares regression:

    δ_frontier(m) = a_stratum + b_stratum × δ_small(m) + ε

where the regression pools paragraphs across the 10 calibration-subsample questions within that stratum, yielding approximately 150 to 250 paragraph-level observations per stratum. Parameter estimates (â_stratum, b̂_stratum) and their standard errors are recorded with the calibration artifact.

The bridge function is then applied to the 60 out-of-subsample instances to produce `delta_loo_bridged(m) = â_stratum + b̂_stratum × δ_small(m)` for each paragraph in each stratum, yielding a V_frontier-equivalent δ_loo estimate on the full N = 90 cohort without requiring V_frontier inference on the full N.

### C.3 Residual diagnostics and escalation criteria

**Unconditional reporting requirement.** Residual diagnostics are computed and reported per stratum regardless of pass or fail status. The reporting requirement is unconditional because Phase 2 sample-size calculation consumes bridge variance as an input parameter, and Phase 2 cannot distinguish between a bridge that passed comfortably and a bridge that passed marginally if only pass/fail status is reported. The per-stratum diagnostic report includes: Shapiro-Wilk p-value for residual normality, Breusch-Pagan p-value for homoscedasticity, intra-class correlation coefficient clustered by question_id, bootstrapped 95% confidence intervals on â_stratum and b̂_stratum under B = 1000 nonparametric bootstrap resamples, the root-mean-square residual, and a kernel-smoothed scatter plot of residuals versus δ_small.

**Escalation thresholds.** The residual distribution per stratum is examined for three properties. Normality is tested via Shapiro-Wilk with p-value threshold 0.01 below which normality is rejected. Homoscedasticity is examined via Breusch-Pagan test at p < 0.01. Independence is examined by clustering residuals by question_id and measuring intra-class correlation, with ICC > 0.3 indicating significant within-question correlation requiring mixed-effects bridge specification rather than pooled OLS.

**Escalation paths.** If any diagnostic fails, the protocol escalates to a nonlinear bridge specification. The first escalation tier is a monotonic isotonic regression, which relaxes linearity while preserving the rank-order relationship between δ_small and δ_frontier. The second escalation tier is a per-hop-depth polynomial bridge (quadratic) if isotonic regression shows systematic residual structure. The third escalation tier is collapse to V_frontier on the full N = 90 at approximately 4× inference cost increase, which represents the fallback position if the bridge design fundamentally fails to recover V_frontier-equivalent measurements.

**Rationale for the linear-first starting point.** The linear-per-stratum bridge is a functional-form assumption rather than a theoretically-derived specification. The scientific basis for the assumption is pragmatic: linear bridges are typically adequate as first approximations in regression calibration, and the nonparametric alternative (kernel regression or Gaussian process regression over δ_small) would require a calibration subsample approximately 2× to 3× larger for comparable precision, which defeats the cost-optimization rationale for the tiered V design. The protocol therefore starts with linear bridging, reports residual diagnostics unconditionally, and escalates only on failure. Phase 2 consumers of the bridge output must treat the linearity assumption as a working hypothesis rather than a verified property, and any Phase 2 result that is sensitive to bridge functional form should trigger a retrospective escalation to isotonic bridging in sensitivity analysis.

### C.4 Bridge-validated δ_loo aggregation

After bridge fitting and diagnostic validation, each paragraph m in each question in the N = 90 probe carries a `delta_loo_bridged` value that estimates the V_frontier-equivalent δ_loo. For calibration-subsample instances where V_frontier is directly measured, the bridged and directly-measured values are compared as an internal consistency check with Pearson correlation threshold ≥ 0.9 and mean-absolute-error threshold ≤ 0.5 × within-stratum δ_loo standard deviation.

---

## Section D: Tertile Stratification and Tolerance Band

### D.1 Per-stratum tertile boundary computation

Within each hop-depth stratum, the bridged δ_loo values are pooled across all paragraphs in all questions in that stratum, and the 33rd and 67th percentile cut points are computed. Paragraphs with δ_loo above the 67th percentile are assigned to the high-value tertile, paragraphs below the 33rd percentile to the low-value tertile, and paragraphs in the middle third to the buffer tertile. The buffer tertile is discarded from the extraction-uniformity analysis to sharpen the high-versus-low contrast, but is preserved in the data store for sensitivity analyses in Phase 2.

Tertile boundaries are computed per stratum rather than pooled across strata because the δ_loo distribution shifts with hop depth: deeper hops produce larger absolute δ_loo values because individual supporting paragraphs carry more information relative to the baseline when the question requires chained reasoning. Per-stratum stratification controls for this shift.

### D.2 Tolerance band derivation

The within-stratum δ_loo standard deviation σ_stratum is computed as the sample standard deviation of bridged δ_loo values in that stratum. The tolerance band around each tertile boundary extends ±0.5 × σ_stratum. Paragraphs whose bridged δ_loo falls within either tolerance band are flagged for expert arbitration, and approximately 20% of the total paragraph set falls into the tolerance band in expectation under approximately normal δ_loo distributions.

### D.3 Edge-case identification algorithm

The tolerance-band flagging produces a list of approximately 18 arbitration-candidate instances at the question level (with an instance being a (question, paragraph) pair whose paragraph falls in the tolerance band). The flagging list is frozen at a single pass over the data after bridge fitting is complete and is not updated iteratively during annotation. Each flagged instance is assigned to the expert arbitration queue. Non-flagged instances receive automated tertile assignment as their final classification, subject to face-validity verification on a random subsample.

---

## Section E: Human Annotation

### E.1 Annotator selection and training

The annotator cohort consists of two primary annotators drawn from the mixed pool (NLP-trained graduate students, qualified research contractors, or equivalent) and one expert arbitrator (domain-expert researcher in NLP or multi-hop QA). Primary annotators complete a training session of approximately 2 hours consisting of: a walkthrough of 5 fully-worked examples demonstrating the expected reasoning about paragraph value, a calibration set of 10 instances with gold-standard expert classifications provided after initial annotation, and a discussion round resolving any systematic disagreement patterns.

The expert arbitrator completes the same training materials but does not complete the calibration set as a student, instead serving as the gold-standard source for primary annotator calibration.

### E.2 Primary annotation task specification

Primary annotators receive the full list of (question, paragraph) instances grouped by question and presented with the full paragraph context. For each paragraph, the annotator is asked:

> Does this paragraph contain information that is directly necessary for answering the question correctly? Rate this paragraph as HIGH (directly necessary), LOW (not necessary), or BUFFER (ambiguous or indirectly necessary).

The annotator does not see the automated δ_loo classification, the bridged value, or the MuSiQue `is_supporting` flag during this task. The annotator does see the MuSiQue canonical answer, because the task is to identify paragraphs necessary for reaching that specific answer rather than to solve the question independently.

### E.3 Expert arbitration task specification

The expert arbitrator receives only the tolerance-band-flagged instances (approximately 18). For each flagged instance, the expert sees the question, the full paragraph pool with the target paragraph highlighted, and the two primary annotator classifications. The expert is asked to provide a final classification (HIGH, LOW, or BUFFER) that serves as the gold-standard label for that instance, with a brief free-text justification preserved in the annotation log for later review.

### E.4 Face-validity subsample task specification

A random subsample of 9 non-flagged instances (approximately 10% of the non-flagged pool, stratified across hop depths and across automated-classification tertiles) is assigned to the expert for face-validity verification. The expert performs the same classification task as in E.3 on these instances. The face-validity subsample supports computation of κ_automated-expert on cases where automated classification is expected to agree with expert judgment, which is the complementary measurement to the arbitration-case κ_automated-expert.

---

## Section F: Inter-Rater Reliability Measurement

### F.1 κ_primary computation

Cohen's κ is computed between the two primary annotators on the union of (tolerance-band-flagged, face-validity-subsampled) instances, yielding approximately 27 paired annotations. The statistic is computed with the standard equal-weighting scheme over the three-class (HIGH, LOW, BUFFER) labeling. Per-stratum κ_primary is also computed by hop depth as a secondary measurement, with the understanding that per-stratum sample size (approximately 9) admits only coarse discrimination.

### F.2 κ_primary-expert computation

κ_primary-expert is computed between each primary annotator and the expert on the 18 tolerance-band-flagged instances (where the expert provided a gold-standard label). Two values are produced, one per primary annotator, and they are reported separately rather than averaged because systematic bias of one annotator relative to the expert is informative about annotator-pool heterogeneity.

### F.3 κ_automated-expert computation

κ_automated-expert is the core measurement for the automation-push design validity. It is computed on the full expert-labeled set (tolerance-band-flagged plus face-validity-subsampled, approximately 27 instances) by comparing the automated tertile classification against the expert label. The automated classification is mapped to the three-class labeling via: HIGH tertile → HIGH, LOW tertile → LOW, BUFFER tertile → BUFFER.

### F.4 Graded outcome reporting and deferred binding threshold

**High-resolution κ reporting.** Phase 1 reports κ values at high resolution rather than as binary pass/fail outcomes. For each of the three κ measurements (κ_primary, κ_primary-expert with both primary annotators, κ_automated-expert), the protocol reports the point estimate, a bootstrapped 95% confidence interval under B = 1000 nonparametric bootstrap resamples, and a per-stratum decomposition by hop depth where per-stratum sample size permits meaningful decomposition.

**Why the binding threshold is deferred to Phase 2.** The Landis-Koch (1977) convention of κ ≥ 0.6 for "substantial agreement" is a heuristic interpretive scheme developed for medical diagnostic agreement on binary classifications. Its applicability to three-class ordinal classification with non-uniform marginal distributions under an extraction-uniformity measurement chain is not self-evidently appropriate. A more defensible binding threshold would be derived from the operational consequences of automated misclassification: if automated misclassification introduces measurement error of magnitude ε into the c_high and c_low parameters that Phase 3 and Phase 4 estimate, then the κ threshold should be set such that the resulting ε is smaller than the effect size the paper intends to detect. This derivation requires Phase 2 effect-size specification and is therefore deferred.

**Provisional three-tier outcome structure.** The protocol adopts the Landis-Koch κ ≥ 0.6 threshold as a provisional interpretive benchmark while the binding threshold is pending Phase 2 derivation. Three tiers of Phase 1 outcome are defined.

Tier 1 (unconditional pass) is achieved when all three κ values exceed 0.6 with 95% confidence interval lower bounds above 0.5. Phase 2 proceeds under the full automation-push design with no documented limitations on Phase 1 measurement quality.

Tier 2 (conditional pass) is achieved when κ_automated-expert exceeds 0.6 but confidence intervals are wide (lower bound below 0.5), or when one of the secondary κ values (κ_primary or κ_primary-expert) falls below 0.6. Phase 2 proceeds with documented limitations recorded in the Phase 2 design document, and Phase 2 sample-size calculation incorporates the measured κ uncertainty as an additional variance component.

Tier 3 (design revision) is triggered when κ_automated-expert falls below 0.6 with high confidence (95% confidence interval upper bound below 0.7). Phase 1 halts and returns to Phase 0 for tolerance-band width revision, annotator-hierarchy restructuring, or tertile-operationalization redesign. The specific revision path is chosen based on diagnostic decomposition: systematic misclassification in specific strata indicates tolerance-band revision, systematic disagreement between primary annotators and expert indicates annotator-hierarchy revision, and systematic misclassification near tertile boundaries indicates tertile-operationalization redesign.

**Bridge diagnostic pass criteria.** Bridge diagnostics are reported unconditionally per Section C.3, and the pass criteria are: residual normality at p > 0.01, homoscedasticity at p > 0.01, and ICC < 0.3 in at least two of three hop-depth strata (complete uniformity across all three strata is not required; a single-stratum failure is an escalation trigger rather than a hard fail). Phase 2 consumes the bridge variance report regardless of pass status.

---

## Section G: Phase 1 Outputs and Phase 2 Handoff

### G.1 Data artifacts preserved

Phase 1 produces the following artifacts, each stored in a versioned data store with content hashes for reproducibility: the hop-stratified N = 90 sample manifest (A.2), the full per-question measurement store including all orderings and log-probabilities (B.5), the calibration subsample V_frontier measurements and fitted bridge coefficients per stratum (C.2), the residual-diagnostic statistics and any escalation-triggered bridge refits (C.3), the bridged δ_loo values for all out-of-subsample paragraphs (C.4), the tertile boundaries and tolerance-band membership labels (D.1 and D.3), the primary annotator labels and expert arbitration labels (E.2 and E.3), and the three computed κ values with per-stratum decomposition where applicable (F.1–F.3).

### G.2 Statistical parameters passed to Phase 2

Phase 2 sample-size calculation for the full-study extraction audit consumes the following Phase 1 outputs: within-stratum δ_loo standard deviation σ_stratum per hop depth, bridge coefficient variance Var(â_stratum, b̂_stratum) per hop depth, automated-to-expert classification disagreement rate per tertile and per hop depth, and per-question inference cost for V_frontier and V_small under observed paragraph-pool sizes.

### G.3 Known limitations and caveats for Phase 2 design

The limitations and caveats surfaced during Phase 1 execution are recorded for Phase 2 consumption. These include any residual-diagnostic failures that triggered bridge escalation, any annotator-level systematic bias patterns detected in κ_primary-expert, any hop-depth strata where per-stratum κ falls below 0.6 even when pooled κ meets the threshold, and any measurement artifacts detected during face-validity verification that suggest the automated classification is systematically biased in ways not captured by the tertile-boundary tolerance band.

---

## Appendix A: Implementation-Level Decisions (locked)

The four protocol-authoring parameters carried over from Phase 0 §9 are locked as follows:

**V_frontier specific model:** Claude Opus 4.7 (`claude-opus-4-7`), which is the current Anthropic frontier and matches anticipated openWorker deployment. This decision is revisable if openWorker deployment uses a non-Anthropic frontier provider, and that revision would propagate through the bridge portability analysis.

**V_small specific model:** Claude Haiku 4.5 (`claude-haiku-4-5-20251001`), which preserves intra-family architectural coherence with V_frontier and enables the bridge function to operate within a coherent training and architecture lineage.

**MuSiQue split:** Development set. Test-set integrity is preserved for future headline evaluation, and dev-set training-data contamination is mitigated structurally by the fact that the extraction uniformity hypothesis tests bias patterns across strata rather than absolute accuracy.

**Execution timeline:** Parallel with openWorker infrastructure audit. Phase 1 proceeds on the MuSiQue-sufficient infrastructure independently of openWorker trace-field export progress.

---

## Appendix B: Failure-Mode Remediation Paths

Three primary Phase 1 failure modes are anticipated, each with a documented remediation path.

**V_small bridge failure (Link 2):** Triggered by residual normality p < 0.01 and heteroscedasticity p < 0.01 jointly across two or more strata, or by Pearson correlation below 0.9 between bridged and directly-measured δ_loo on the calibration subsample. Remediation escalates through isotonic regression, then per-hop-depth polynomial bridge, then V_frontier-only execution on the full N = 90 at approximately 4× inference cost increase.

**Automation-substitution failure (Link 3):** Triggered by κ_automated-expert < 0.6. Remediation options are: widen the tolerance band (increases arbitration rate, increases expert-layer load), invert the annotator hierarchy (expert primary with primary annotators as verification, which changes the annotator-hour budget profile), or revise the tertile-stratification operationalization itself.

**Inter-primary disagreement (κ_primary < 0.6):** Triggered by κ_primary < 0.6 on the arbitration set. Remediation is protocol refinement via an expert-led calibration session with the primary annotators, followed by re-annotation of the disagreement subset. If protocol refinement does not restore κ ≥ 0.6, the annotator-pool expertise profile is revised (likely toward domain-expert contractors) and the budget is recomputed accordingly.

---

## Appendix C: Timeline Estimate

Under nominal execution conditions and assuming the Appendix A decisions hold, Phase 1 executes in approximately 3 to 4 calendar weeks, structured as follows. Week 1 consists of engineering setup including data loading, inference-pipeline construction, and annotation-interface deployment. Days 6 to 8 consist of the automated inference run (V_small on full N, V_frontier on calibration subsample), which requires approximately 9,600 forward passes and is expected to complete in 1 to 2 days of wall-clock time under typical API rate limits. Days 9 to 11 consist of annotator training and calibration. Week 2 consists of primary annotation execution, with the two primary annotators operating in parallel. Day 15 consists of expert arbitration on the flagged instances, which is a single batched session. Days 16 to 20 consist of statistical analysis including bridge fitting, residual diagnostics, κ computation, and Phase 2 parameter export.

The parallel openWorker infrastructure audit proceeds independently on its own timeline, with an early deliverable of a "trace-field availability map" expected within the first two weeks and feeding the Phase 4 feasibility analysis.

---

## Appendix D: Design-Decision Scrutiny Record

The protocol documents three design decisions whose defensibility rests on explicit reasoning rather than on inherited defaults. This appendix records the scrutiny applied to each and the resolution adopted.

### D.1 Variance source for K_LCB repetitions

The alternative variance sources considered were paragraph-order permutation (position-robustness), subset sampling (composition-robustness), and prompt-template variation (wording-robustness). Paragraph-order permutation was selected with the explicit acknowledgment that it measures a strict subset of the robustness properties relevant to the extraction-uniformity hypothesis. A measurement that is stable under paragraph reordering can still be fragile under context composition variation, and Phase 2 consumers of Phase 1 outputs must treat the measurement as position-robust only. The rationale for accepting this scope limitation in Phase 1 is that position-robustness is the more conservative measurement for the specific artifact class (positional-attention bias) most likely to corrupt extraction-uniformity inference, and that subset-sampling can be added as a second variance source in Phase 2 or Phase 3 if Phase 1 diagnostics suggest the position-only measurement is inadequate.

### D.2 Linear-per-stratum bridge function

The alternative bridge specifications considered were nonparametric bridging via kernel regression or Gaussian process regression, and rank-preserving bridging via isotonic regression from the outset. Linear-per-stratum was selected as the starting point with an unconditional diagnostic-reporting requirement and escalation paths to isotonic, polynomial, and V_frontier-full-N fallbacks. The rationale is pragmatic rather than theoretical: linear bridges are typically adequate as first approximations in regression calibration, and the nonparametric alternatives require calibration subsamples 2× to 3× larger for comparable precision. The unconditional diagnostic-reporting requirement is the protocol's specific structural response to the absence of theoretical justification for linearity: Phase 2 consumers receive the full bridge variance report regardless of pass status and can perform retrospective sensitivity analysis with escalated bridge forms if their Phase 2 results are sensitive to bridge specification.

### D.3 Cohen's κ threshold for pass/fail gating

The Landis-Koch (1977) κ ≥ 0.6 threshold for "substantial agreement" is a heuristic convention developed for binary medical diagnostic agreement. Its applicability to three-class ordinal classification under non-uniform marginal distributions in an extraction-uniformity measurement chain is not self-evident. The protocol therefore replaces the Landis-Koch threshold as a binding pass/fail criterion with a three-tier graded outcome structure (Tier 1: unconditional pass, Tier 2: conditional pass with documented limitations, Tier 3: design revision), and the binding threshold itself is deferred to Phase 2, where it can be derived from effect-size requirements on c_high and c_low via propagation of measurement error through the extraction-uniformity estimator. Phase 1 reports κ values at high resolution with bootstrapped confidence intervals so that Phase 2 has the information necessary to perform this derivation.
