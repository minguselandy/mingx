# Phase 2 Experimental Design: Extraction Uniformity Hypothesis Test

**Associated documents:** Phase 0 Specification (`phase0-specification.md`), Phase 1 Probe Protocol (`phase1-protocol.md`), final paper framing (`../archive/final_paper_context_projection_submission_final_v8.md`).

**Document status:** Phase 2 design specification. Specifies both the full-study extraction audit and the Phase 3 pilot as a specific analytical subset of the full-study design.

---

## Scope and Position in the Experimental Program

This document operationalizes the hypothesis test of the extraction uniformity assumption articulated in Section 5 of the paper. Phase 2 is the parent design specification; Phase 3 is the subordinate pilot execution at approximately 20% of the full-study sample size; Phase 4 and beyond (full-study execution) is outside current action scope.

The document is organized to support three distinct consumers. The Phase 3 executor receives an immediately-executable pilot specification including the analytical post-processing of Phase 1 data, the statistical test procedure, and the pilot-to-full-study decision rule. The Phase 4 executor (if the project proceeds to full study) receives the complete full-study design including sample size, retrieval-function audit plan, and decision rules. A future reviewer receives the design rationale including the effect-size derivation, the κ threshold derivation, and the sensitivity-analysis plan.

A structural efficiency is exploited throughout: the Phase 1 probe data already contains bridged δ_loo measurements for all paragraphs in N = 90 questions, which is precisely the input required to compute c_high and c_low under any retrieval function we simulate. Phase 3 pilot execution therefore reduces to analytical post-processing of Phase 1 data rather than a separate data-collection cycle, which compresses timeline and decouples pilot execution from annotator availability.

---

## Section 1: Hypothesis Formalization

### 1.1 The extraction uniformity assumption as a statistical hypothesis

The paper's Section 5 claims that the formal weak-submodular guarantees apply to optimization over the extracted candidate pool M rather than over the underlying information space M*. The extraction uniformity assumption states that extraction completeness is approximately uniform across value strata, which is the condition under which M-level guarantees transfer approximately to M*-level performance. The hypothesis test operationalizes this as a directional null hypothesis on completeness rate divergence.

**H_0 (uniformity):** c_high − c_low ≈ 0, where c_high and c_low are the completeness rates (fraction of stratum members admitted to M from M*) for the high-value and low-value tertiles respectively.

**H_1 (preferential removal of high-value):** c_high − c_low < 0, indicating that extraction preferentially drops high-value findings.

The test is one-sided because the concerning direction is specifically c_high < c_low. The opposite direction (c_high > c_low, extraction preferentially preserves high-value findings) is not concerning for the theorem-to-deployment chain: it means extraction is doing useful filtering work, which is the designer's intent.

### 1.2 Operationalization on MuSiQue

On MuSiQue, the full information space M* is the native paragraph pool associated with each question, typically approximately 20 paragraphs. The extracted candidate pool M is the top-K subset selected by a specified retrieval scoring function. The stratification axis is the bridged δ_loo value from Phase 1, with tertile boundaries computed per hop-depth stratum per the Phase 1 protocol Section D.1.

For each question q, the per-question completeness rates are:

    c_high(q) = |{m ∈ M(q) : m ∈ HighTertile(q)}| / |HighTertile(q)|
    c_low(q)  = |{m ∈ M(q) : m ∈ LowTertile(q)}|  / |LowTertile(q)|

The question-level rates are aggregated across questions via weighted averaging with weights proportional to stratum membership counts, which controls for questions where stratum sizes are unbalanced.

### 1.3 Directionality rationale and scope limitation

The directional test targets the failure mode that matters operationally. A uniformity failure in the opposite direction (c_high > c_low) would still warrant documentation because it shifts the interpretation of the retrieval system, but it does not invalidate the paper's theorem-to-deployment chain. The Phase 2 full-study report will document the observed direction regardless of statistical significance to support retrospective analysis.

The scope limitation inherited from Phase 1 is that the audited extraction process is the retrieval-plus-reranking stage on MuSiQue rather than the openWorker extraction gate. This operational-layer substitution was named as a known limitation in Phase 0 Specification §8 and must be re-stated as a Phase 2 result caveat: a uniformity finding on MuSiQue retrieval does not imply uniformity on openWorker extraction, and a rejection finding on MuSiQue retrieval does not imply rejection on openWorker extraction. Phase 4 re-audit on openWorker traces is required to close this gap.

---

## Section 2: Effect-Size Specification

### 2.1 Practically meaningful effect sizes

The effect-size specification is grounded in the operational consequences of non-uniformity for the paper's Section 5.3 claims. Three thresholds are specified.

The minimum detectable effect Δ_min = 0.05 corresponds to a 5 percentage point divergence between c_high and c_low, which is near the boundary of practical meaningfulness and serves as the sample-size design target. The statistical power calculation is performed at this effect size.

The rejection threshold Δ_reject = 0.10 corresponds to a 10 percentage point divergence, which is large enough to be operationally concerning and is the threshold at which the paper's uniformity claim would be unambiguously rejected. An observed Δ ≥ Δ_reject with 95% confidence interval lower bound above 0 constitutes rejection.

The severe-violation threshold Δ_severe = 0.20 corresponds to a 20 percentage point divergence, which would indicate that extraction bias is a primary rather than secondary source of performance loss and would trigger a more substantive revision of the paper's Section 5.3 claims.

These thresholds are Phase 2 design parameters rather than empirically-derived quantities. They are selected based on the judgment that completeness differences below 5% are within typical measurement noise and implementation variance, while differences above 10% cross the boundary of operational meaningfulness for the theorem-to-deployment bridge claim.

### 2.2 Derivation of the binding κ threshold from effect size

The Phase 1 protocol deferred the binding κ threshold to Phase 2 for derivation from effect-size requirements. The derivation proceeds via misclassification-induced attenuation bias in stratified proportion estimation.

Under a balanced-marginal approximation with misclassification rate ε between high-value and low-value strata, the observed effect relates to the true effect as:

    Δ_obs = (1 − 2ε) × Δ_true

The misclassification rate ε is related to Cohen's κ approximately via ε ≈ (1 − κ) / 2 under balanced three-class marginals with the buffer tertile excluded from analysis. This yields the following attenuation-by-κ schedule.

At κ = 0.6, ε ≈ 0.20 and the attenuation factor (1 − 2ε) ≈ 0.60, meaning observed effects are approximately 60% of true effects. A true Δ_min = 0.05 attenuates to Δ_obs ≈ 0.03, which is below typical measurement noise for the sample sizes under consideration.

At κ = 0.7, ε ≈ 0.15 and the attenuation factor ≈ 0.70. A true Δ_min = 0.05 attenuates to Δ_obs ≈ 0.035.

At κ = 0.8, ε ≈ 0.10 and the attenuation factor ≈ 0.80. A true Δ_min = 0.05 attenuates to Δ_obs ≈ 0.040.

The Phase 2 binding κ threshold is specified as **κ ≥ 0.7**, which corresponds to acceptance of up to 30% effect-size attenuation. This choice reflects a moderately conservative position: the more lenient Landis-Koch threshold of 0.6 would accept 40% attenuation, which approaches the boundary at which Δ_min becomes undetectable against sampling noise. The more stringent threshold of 0.8 would be preferable for publication-critical hypothesis tests but is not operationally necessary for the Phase 2 goal of determining whether the extraction uniformity assumption is a material risk factor in the theorem-to-deployment chain.

This derivation supersedes the provisional Landis-Koch reference used in the Phase 1 protocol. Phase 1 outcomes are re-interpreted under the κ ≥ 0.7 criterion: Phase 1 Tier 1 (unconditional pass) now requires κ ≥ 0.7 rather than κ ≥ 0.6, and Tier 2 (conditional pass) covers 0.6 ≤ κ < 0.7.

---

## Section 3: Sample-Size Calculation

### 3.1 Power analysis under two-proportion test

The full-study sample size is derived from a standard one-sided two-proportion test at significance level α = 0.05 and power 1 − β = 0.80. Under a baseline completeness rate p = 0.80 (a plausible value for bi-encoder-plus-cross-encoder retrieval on MuSiQue) and Δ_min = 0.05, the per-arm sample size requirement is:

    n_arm ≈ 2 × p × (1 − p) × (z_α + z_β)² / Δ²
           ≈ 2 × 0.16 × 7.85 / 0.0025
           ≈ 1,005 paragraph observations per stratum

The paragraph observation count per question in the high-value and low-value strata is approximately N_paragraphs / 3 × 2 / 3 ≈ 4.4 paragraphs per stratum per question (with the factor 2/3 accounting for the buffer tertile being discarded). Under N_paragraphs = 20 and three strata, approximately 6 paragraphs per stratum per question is the working estimate after recovering buffer-tertile paragraphs misclassified into the extreme strata under the tertile cut points.

The required number of questions is therefore n_questions ≈ 1005 / 6 ≈ 168.

### 3.2 Propagation of Phase 1 uncertainty into inflated sample size

The Phase 1 handoff provides three variance sources that must be propagated into the Phase 2 sample size: bridge coefficient variance, κ-induced attenuation variance, and residual within-stratum δ_loo variance. The propagation is multiplicative under the independence approximation.

Bridge coefficient variance contributes an inflation factor of approximately 1 + σ²(bridge) / σ²(total), which is bounded above by 1.15 under plausible Phase 1 residual diagnostic outcomes. κ-induced attenuation contributes an inflation factor of 1 / (1 − 2ε)², which at κ = 0.7 is approximately 2.04 (compensating for the 30% effect-size attenuation). Within-stratum δ_loo variance affects classification confidence near tertile boundaries and contributes an inflation factor of approximately 1.10 under the ±0.5σ tolerance band.

The composite inflation factor is approximately 1.15 × 2.04 × 1.10 ≈ 2.58. The inflated sample size is therefore **N_full = 168 × 2.58 ≈ 433 questions, rounded up to N_full = 450**.

### 3.3 Computational and annotator budget for the full study

At N_full = 450 and 20 paragraphs per question, the V_small inference cost is 450 × 21 × 5 ≈ 47,250 forward passes. The V_frontier calibration-subsample cost at 15 per stratum × 3 strata = 45 instances is 45 × 21 × 5 ≈ 4,725 forward passes. Total inference approximately 52,000 forward passes, which is approximately 5× the Phase 1 probe cost and remains modest in absolute terms.

Annotator budget at full-study scale depends on whether automated classification retains its Phase 1 κ performance. Under the automation-push design with κ_automated-expert ≥ 0.7, annotator load scales proportionally to tolerance-band membership rate (approximately 20% of paragraphs) and face-validity sampling rate (approximately 10%). The total annotator budget estimate is approximately 70 to 140 hours across primary annotators and approximately 15 to 25 hours of expert arbitration.

---

## Section 4: Retrieval Function Specifications

### 4.1 Primary audit target

The primary audit target is a **bi-encoder plus cross-encoder pipeline** matching the semantic core of the openWorker pipeline specified in the paper's Section 6.3. Specific component choices are: bi-encoder retrieval using a sentence-transformer model (`sentence-transformers/all-mpnet-base-v2` or equivalent current-generation encoder), yielding top-N candidates from the native MuSiQue pool; cross-encoder reranking using a cross-encoder model (`cross-encoder/ms-marco-MiniLM-L-12-v2` or equivalent), producing a final score for each candidate; and final selection of top-K by cross-encoder score.

The Phase 2 primary audit uses K = 5 as the default top-K value, which corresponds to 25% of the native pool and creates meaningful extraction pressure relative to the 20-paragraph pool size. Sensitivity analysis across K ∈ {3, 5, 10} is specified in Section 5.3.

### 4.2 Sensitivity analysis targets

Three additional retrieval configurations are audited as sensitivity analyses. BM25 lexical retrieval serves as a classical baseline and tests whether uniformity findings are specific to semantic retrieval or generalize across retrieval paradigms. Bi-encoder-only retrieval without cross-encoder reranking tests whether reranking is responsible for any observed uniformity or non-uniformity. Hybrid BM25 plus bi-encoder via Reciprocal Rank Fusion tests the specific retrieval architecture cited in the paper's Section 6.3.

### 4.3 Rationale for retrieval function selection

The primary-versus-sensitivity hierarchy is specified as **primary equals anticipated deployment target**. Under this framing, the primary audit target is a deployment-fidelity choice rather than an architectural preference. The semantic-first pipeline (bi-encoder plus cross-encoder) is the primary audit target specifically because it is the retrieval paradigm that openWorker deploys as specified in the paper's Section 6.3, and any other architectural choice would introduce a Phase 2-to-Phase 4 transfer gap that is not justified by scientific considerations.

The sensitivity analysis targets (BM25, bi-encoder-only, hybrid RRF) serve their intended function of characterizing robustness of the uniformity conclusion to retrieval-paradigm variation. They do not establish claims for deployments using those paradigms. If Phase 4 deploys a non-semantic retrieval paradigm, Phase 2 results become non-transferable to that deployment context, and a re-audit under the new paradigm is warranted regardless of the sensitivity-analysis results on the current Phase 2 sample.

This framing makes the scope limitation explicit and defensible. Phase 2 conclusions apply to semantic-retrieval deployment targets; extending them to other retrieval paradigms requires additional empirical work rather than extrapolation from the sensitivity-analysis arm of the current design.

---

## Section 5: Decision Rules and Statistical Inference

### 5.1 Test statistic and confidence interval construction

The primary test statistic is the point estimate Δ̂ = ĉ_low − ĉ_high (reversed sign so that positive values indicate the concerning direction of preferential high-value removal). The confidence interval is constructed via nonparametric bootstrap at B = 1,000 resamples clustered by question to account for within-question paragraph correlation. The one-sided 95% confidence interval lower bound is reported as the primary inference quantity.

Per-stratum decomposition is reported by hop depth, with one-sided 95% confidence intervals per stratum. Per-stratum analysis uses the same bootstrap procedure on the stratum-specific subset of the full sample.

### 5.2 Three-outcome decision rule for the full study

The full-study outcome is categorized into one of three classes based on the relationship between the observed effect and the specified thresholds.

**Reject uniformity** is declared when Δ̂ ≥ Δ_reject = 0.10 and the 95% confidence interval lower bound exceeds 0. This outcome indicates that extraction bias is operationally meaningful, and the paper's Section 5.3 claims must incorporate the measured bias magnitude as a correction factor for the theorem-to-deployment bridge.

**Fail to reject uniformity** is declared when the 95% confidence interval upper bound falls below Δ_min = 0.05. This outcome indicates that the uniformity approximation is practically adequate at the tested effect-size resolution, and the paper's Section 5.3 claims stand without correction.

**Indeterminate** is declared when neither condition holds. This outcome indicates that the study was underpowered for the observed effect size or that the effect falls in the practically-ambiguous region between Δ_min and Δ_reject. Remediation options include full-study sample-size extension or acceptance of the indeterminate status with documented caveats.

### 5.3 Sensitivity analyses

Four sensitivity analyses are specified unconditionally for the full-study report. First, the position-robustness scope limitation inherited from Phase 1 is addressed by re-running the analysis on a subset that adds composition-robustness as a second variance source on approximately 10% of the full sample, which estimates the composition-robustness variance contribution. Second, the linear-bridge assumption is stress-tested by recomputing c_high and c_low under an isotonic-regression bridge, with divergence between linear-bridge and isotonic-bridge results reported as a bridge-sensitivity diagnostic. Third, per-stratum decomposition is reported for hop depth and tertile membership separately. Fourth, robustness to top-K choice is reported via the K ∈ {3, 5, 10} sweep specified in Section 4.1.

---

## Section 6: Phase 3 Pilot as Analytical Subset of Phase 2

### 6.1 Pilot sample and data source

The Phase 3 pilot executes at approximately 20% of the full-study sample size, yielding a pilot sample of approximately 90 questions. This sample size coincides with the Phase 1 probe sample, and the Phase 3 pilot is therefore operationalized as an analytical post-processing of Phase 1 data rather than a separate data-collection cycle. The pilot requires no additional inference runs and no additional annotation.

The pilot inherits the Phase 1 probe's hop-stratified sampling design (30 questions per hop depth) and uses Phase 1's bridged δ_loo values for tertile assignment. The retrieval simulation specified in Section 4.1 is applied to the Phase 1 data to produce the top-K extracted subset M for each question.

### 6.2 Pilot statistical procedure

The pilot computes the primary test statistic Δ̂ = ĉ_low − ĉ_high and its bootstrapped 95% confidence interval under the procedure specified in Section 5.1, using the Phase 1 sample of N = 90 questions. Per-stratum decomposition by hop depth is reported with the understanding that per-stratum confidence intervals at N = 30 per stratum will be substantially wider than full-study confidence intervals at N = 150 per stratum.

### 6.3 Pilot-to-full-study decision rule

The pilot produces a three-outcome classification that determines full-study warrant.

**Full study warranted** is declared when the pilot point estimate Δ̂ exceeds 0.075 (the midpoint of Δ_min and Δ_reject) or when the 95% confidence interval upper bound exceeds Δ_reject. Either condition indicates that the full-study sample size is likely to detect a meaningful effect, justifying full-study execution.

**Full study not warranted** is declared when the pilot point estimate Δ̂ falls below Δ_min with upper confidence bound also below Δ_reject. This outcome indicates that the full study at N = 450 would almost certainly fail to reject uniformity, so the additional sample size represents limited incremental value. The pilot-level conclusion of approximate uniformity is reported with appropriate sample-size caveats.

**Indeterminate** is declared when the pilot point estimate falls in the ambiguous range (Δ_min ≤ Δ̂ < 0.075). This outcome motivates either full-study execution or pilot extension (adding approximately 30% more questions) depending on budget and timeline constraints.

**Cost-asymmetry acknowledgment.** The 0.075 midpoint threshold treats the two pilot-decision error costs as symmetric despite a genuine asymmetry between them. The cost of a false positive (proceeding to full study when the true effect is below Δ_min) is bounded at approximately 5× pilot resource expenditure, which is recoverable. The cost of a false negative (failing to proceed when a meaningful effect exists) propagates into the paper's Section 5.3 claims as an uncorrected uniformity assumption, with downstream consequences that are not recoverable through resource expenditure alone. Under strict cost-asymmetry accounting, this argues for a lower warrant threshold biased toward full-study execution.

The midpoint is nevertheless preserved as the default for two structural reasons. First, cost-asymmetry arguments exhibit a slippery-slope property under which any threshold can be pushed toward Δ_min, which collapses the three-outcome decision structure into a binary "always proceed if effect is above zero" rule. The midpoint serves as a Schelling-point default that preserves decision-rule integrity against this degenerate limit. Second, the indeterminate classification is designed precisely for cases where default reasoning fails to resolve the decision, and it explicitly permits case-by-case judgment override when contextual evidence warrants proceeding to full study despite a pilot effect below the midpoint. The three-outcome structure therefore accommodates the cost asymmetry through the indeterminate-case adjudication pathway rather than by encoding the asymmetry into the default threshold itself.

### 6.4 Pilot-level sensitivity analyses

The pilot executes a reduced subset of the full-study sensitivity analyses. The top-K sensitivity sweep is executed in full because it requires no additional data. The retrieval-paradigm sensitivity across BM25, bi-encoder-only, and hybrid-RRF is also executed in full because retrieval simulation on existing data is cheap. The position-robustness-to-composition-robustness comparison is deferred to the full study because it requires additional inference passes that were not performed in Phase 1.

---

## Section 7: Outputs and Handoff

### 7.1 Phase 3 pilot artifacts

The Phase 3 pilot produces the following artifacts: retrieval-simulation output manifests for each audited retrieval configuration and each top-K value, per-question completeness rate records with stratum-level decomposition, bootstrapped confidence intervals on Δ̂ for the pooled sample and per-stratum decompositions, the three-outcome classification result, and the pilot-to-full-study decision-rule application record.

### 7.2 Parameters handed to Phase 4 if full study proceeds

If the Phase 3 pilot outcome warrants full-study execution, the following parameters are passed to Phase 4: the point estimate and variance of the pilot-measured Δ̂ for full-study power recalculation, the pilot-measured within-stratum variance for sample-size refinement, any observed divergence between linear-bridge and isotonic-bridge results for bridge-form selection in the full study, and the top-K value or values prioritized for full-study execution based on pilot sensitivity analysis.

### 7.3 Known limitations and caveats

The limitations carried forward from Phase 0 and Phase 1 remain binding. The operational-layer substitution (retrieval-plus-reranking on MuSiQue audited in lieu of openWorker extraction gate) is inherited. The position-robustness-only variance source of Phase 1 data propagates into the pilot; the full study adds composition-robustness as a secondary variance source but the pilot does not. The linear-bridge working hypothesis is carried forward and is addressed via isotonic-bridge sensitivity analysis rather than via bridge-form verification. The effect-size thresholds (Δ_min = 0.05, Δ_reject = 0.10, Δ_severe = 0.20) are Phase 2 design parameters reflecting judgment rather than empirical calibration, and are revisable if Phase 3 or Phase 4 findings motivate revision.

---

## Appendix A: Effect-Size Derivation Reasoning

The effect-size thresholds were selected by reference to the specific mechanism by which extraction bias threatens the paper's claims. The paper's Section 5.3 claims concern the *relative approximation ratio* of the greedy algorithm on the extracted pool M, not absolute performance metrics. Uniform scaling between M and M* (proportional item removal across all value strata) does not affect the relative approximation ratio because both the M-optimum and the M*-optimum scale by the same factor. The operationally-meaningful failure mode is therefore **non-uniform bias**: extraction that preferentially removes high-value items produces an M-optimum that is structurally different from the M*-optimum rather than a proportional shadow of it, which breaks the theorem-to-deployment bridge in a way that uniform removal does not.

Under this mechanism, the relevant effect size is the stratum-wise completeness divergence c_low − c_high, which directly measures the fraction of high-value items disproportionately absent from M relative to low-value items. A 5 percentage point divergence roughly corresponds to a 5% probability that a given M*-optimal item is absent from M while its low-value competitor is retained, which translates to approximation-quality degradation of comparable magnitude for the specific greedy-selection claims in the paper.

Three considerations constrain the threshold selection under this mechanism. First, thresholds below 5% are operationally indistinguishable from implementation variance in retrieval pipelines: typical run-to-run variation across random seeds and tokenization artifacts is in the 2-4% range for completeness metrics. Second, thresholds above 20% indicate that extraction is a dominant rather than secondary performance factor, which would require revising the paper's Section 5.3 claims structurally rather than quantitatively. Third, the threshold triple must produce a non-degenerate three-outcome decision rule, which requires meaningful separation between Δ_min, Δ_reject, and Δ_severe.

The 0.05/0.10/0.20 triple satisfies these three constraints while remaining conservative at both endpoints. Alternative triples such as 0.03/0.07/0.15 or 0.08/0.15/0.25 would satisfy the constraints with different sample-size and operational-interpretation consequences; the specific choice retains an element of judgment that is flagged as a Phase 2 design parameter rather than an empirically-derived quantity. The full-study report will evaluate whether the threshold selection requires revision based on observed effect distributions.

---

## Appendix B: κ Threshold Derivation Worked Example

The derivation in Section 2.2 assumes balanced three-class marginals with the buffer tertile excluded. Under unbalanced marginals the relationship between κ and the misclassification rate ε becomes more complex, and the attenuation factor formula must be re-derived. The Phase 2 full-study report will re-compute the attenuation using the empirically-observed marginal distribution rather than the balanced-marginal approximation.

For a worked example at κ = 0.7 under balanced marginals: ε ≈ (1 − 0.7) / 2 = 0.15. Given true rates c_high^true = 0.70 and c_low^true = 0.90 (true Δ = 0.20), the observed rates are c_high^obs = 0.85 × 0.70 + 0.15 × 0.90 = 0.73 and c_low^obs = 0.85 × 0.90 + 0.15 × 0.70 = 0.87, yielding observed Δ = 0.14. The attenuation factor is 0.14 / 0.20 = 0.70, matching the formula-derived value (1 − 2 × 0.15) = 0.70.

The composite bias and power implications are that the Phase 2 full study at N_full = 450 has power 0.80 to detect true Δ = 0.05 after accounting for κ = 0.7 attenuation, where the raw statistical test is designed for observed Δ = 0.035.

---

## Appendix C: Retrieval Configuration Specifications

The bi-encoder retrieval is performed with mean-pooled embeddings of paragraph text concatenated with the paragraph title, normalized to unit length. Query representation is the mean-pooled embedding of the question text. Similarity is cosine similarity. Top-N is set to 10 for input to the cross-encoder stage.

The cross-encoder reranking takes (question, paragraph-with-title) pairs as input and produces a relevance score. The top-K paragraphs by cross-encoder score form the extracted candidate pool M. Tie-breaking at rank K uses bi-encoder similarity as a secondary key.

The BM25 baseline uses standard parameters (k1 = 1.2, b = 0.75) with paragraph-level tokenization including the title. The hybrid RRF configuration combines BM25 and bi-encoder rankings via Reciprocal Rank Fusion with the standard c = 60 parameter.

All retrieval configurations are applied identically across all 90 pilot questions and (if full study proceeds) all 450 full-study questions, with seeds and parameters fixed and recorded in the execution log for reproducibility.
