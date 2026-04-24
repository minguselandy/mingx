# Execution-Readiness Checklist: Context Projection Selection Experimental Program

**Associated documents:** Phase 0 Specification (`phase0-specification.md`), Phase 1 Probe Protocol (`phase1-protocol.md`), Phase 2 Experimental Design (`phase2-design.md`), final paper framing (`../archive/final_paper_context_projection_submission_final_v8.md`).

**Document status:** Integration artifact consolidating execution preconditions across the three-document specification suite. Organized as five sequential gates plus one parallel workstream.

---

## Structural Overview

This checklist operationalizes the three-document specification suite into an execution sequence. The five sequential gates establish logical ordering: each gate's entry criteria are the exit criteria of the preceding gate, and each gate's completion is verifiable independently of downstream gates. The openWorker infrastructure audit executes concurrently with Gate 2 (Phase 1 execution), feeds Gate 5 decisions (pilot-to-full-study transition), and is part of the Gate 2 completion package. It does not block live Phase 1 measurement execution, but the Gate 2 package is not complete until the trace-field availability map or an explicit no-code-path blocker record is attached.

The checklist uses four status categories per item. "Specified" indicates the item is defined in the specification suite and requires only verification that the definition has been read and understood by the executor. "Provisioned" indicates the item requires resource allocation (infrastructure, access, personnel) before execution proceeds. "Tested" indicates the item requires a functional verification run before production use. "Executed" indicates the item is a Phase 1 or Phase 3 execution step that produces data or decisions.

---

## Gate 1: Pre-Execution Provisioning

Gate 1 must complete before any Phase 1 work begins. All items are provisioning or testing activities with no data-generating steps.

**Data access and integrity.** The MuSiQue-Ans development split must be downloaded from the canonical dataset distribution source and loaded into a reproducible working store. A content hash over the full dev split must be computed and recorded before any sampling or analysis proceeds. The sampling random seed must be selected and documented in the execution log. These steps reference Phase 1 Protocol Section A.1 and Phase 0 Specification §3.

**Model access and inference provisioning.** API access to DashScope's OpenAI-compatible endpoint must be verified for Qwen3.6-Plus (`qwen3.6-plus`) and Qwen3.6-Flash (`qwen3.6-flash`) via authentication tests and a small-batch inference test. In the current repository implementation, this provisioning path is exposed through the default API profile `dashscope-qwen-phase1`, with provider/model overrides flowing through `api/settings.py` rather than being hardcoded in runtime entrypoints. The forced-decode log-probability extraction pipeline must be tested with `logprobs = true`, `top_logprobs = 0`, `temperature = 0`, `n = 1`, `stream = false`, and `enable_thinking = false`. The inference budget for the protocol-full Phase 1 probe (approximately 9,600 forward passes) must be provisioned with approximately 30% headroom for retry logic and diagnostic re-runs. Rate-limiting and retry logic must be implemented with exponential backoff. These steps reference Phase 1 Protocol Section B.1 and B.2.

**Retrieval simulation infrastructure.** The bi-encoder model (`sentence-transformers/all-mpnet-base-v2` or current-generation equivalent) must be loaded and tested for embedding generation at the paragraph and query levels. The cross-encoder model (`cross-encoder/ms-marco-MiniLM-L-12-v2` or equivalent) must be loaded and tested for (query, paragraph) pair scoring. A BM25 implementation with standard parameters (k1 = 1.2, b = 0.75) must be available. Top-K selection logic for K ∈ {3, 5, 10} must be implemented and tested against a small sample. These steps reference Phase 2 Design Section 4 and Appendix C.

**Annotation infrastructure.** The two primary annotators must be identified and available, with mixed-pool composition matching the Phase 0 Specification §4 hierarchy (graduate student or qualified contractor level, with the pool qualified for the hardest hop-depth stratum). The expert arbitrator must be identified and available (domain-expert researcher in NLP or multi-hop QA). The annotation interface must be deployed with support for three-class labeling (HIGH, LOW, BUFFER) and free-text justification fields. Training materials including five fully-worked examples and a ten-instance calibration set must be prepared. These steps reference Phase 1 Protocol Section E.

**Statistical analysis infrastructure.** Bridge regression code (linear OLS with per-stratum specification) must be implemented and tested against synthetic data. Bootstrapped 95% confidence interval computation with B = 1,000 resamples must be implemented for both bridge coefficients and Cohen's κ values. Residual diagnostic code (Shapiro-Wilk, Breusch-Pagan, intra-class correlation) must be implemented. Cohen's κ computation for three-class ordinal agreement must be implemented and validated against a reference implementation. These steps reference Phase 1 Protocol Section C and F and Phase 2 Design Section 5.

**Data storage and reproducibility.** A versioned data store must be provisioned with append-only semantics for per-question measurement records. The execution log schema must be finalized with fields for random seeds, content hashes, model version pins, ordering permutations, and any protocol-deviation events. Resumption logic for interrupted inference runs must be implemented and tested. These steps reference Phase 1 Protocol Section B.5 and G.1.

---

## Gate 2: Phase 1 Execution

Gate 2 is the Phase 1 probe execution itself, spanning approximately three to four calendar weeks per the Phase 1 Protocol Appendix C timeline. Repository-local `live-*` plans with `question_paragraph_limit = 5` and per-hop calibration counts of `1`, `2`, or `3` are reduced-scope pilot artifacts and must not be treated as Phase 2 statistical inputs.

**Data preparation execution.** The hop-stratified sample of N = 90 questions must be drawn under the recorded seed with rejection of questions whose paragraph pool size falls outside [15, 25]. The final accepted sample manifest must be stored with per-question metadata and a sample-level content hash. Per-question paragraph pools must be extracted in canonical order. The 30-instance calibration subsample (10 per hop-depth stratum) must be drawn from within the N = 90 under the same reproducibility seed.

**Automated measurement execution.** V_small (Qwen3.6-Flash) delta_loo measurements must be computed for all paragraphs in all 90 questions under 5 paragraph-order permutations each, yielding approximately 7,200 forward passes in the protocol-full configuration. V_frontier (Qwen3.6-Plus) delta_loo measurements must be computed for the 30-instance calibration subsample, yielding approximately 2,400 forward passes. Per-paragraph delta_loo values must be aggregated as the q = 0.1 LCB quantile per Phase 1 Protocol Section B.3. The contamination diagnostic from Phase 1 Protocol Section B.6 is an unconditional pre-bridge step and must be recorded before bridge fitting proceeds.

**Bridge estimation execution.** Per-stratum linear bridge regression must be fit on the calibration subsample with approximately 150-250 paragraph-level observations per stratum. Residual diagnostics must be computed unconditionally per stratum including Shapiro-Wilk p-value, Breusch-Pagan p-value, intra-class correlation, and bootstrapped 95% confidence intervals on â_stratum and b̂_stratum. The bridged δ_loo values must be computed for the 60 out-of-subsample instances. Internal consistency must be verified with Pearson correlation ≥ 0.9 and MAE ≤ 0.5 × σ_stratum on the calibration subsample where both direct and bridged values are available.

**Tertile stratification and tolerance band execution.** Per-stratum tertile boundaries must be computed from the pooled bridged δ_loo distribution. The ±0.5 × σ_stratum tolerance band must be applied around both tertile boundaries to identify arbitration-flagged instances (approximately 20% of paragraphs). The face-validity subsample (approximately 10% of non-flagged instances) must be drawn randomly with stratification across hop depths and automated tertile assignments.

**Annotation execution.** Primary annotator training must be completed with the five worked examples and ten-instance calibration set. Primary annotation on arbitration-flagged and face-validity-subsampled instances must be executed in parallel by both primary annotators. Expert arbitration on flagged instances (approximately 18 at N = 90) must be completed in a single batched session with written justifications preserved.

**Reliability measurement execution.** The three κ values (κ_primary, κ_primary-expert for each primary annotator, κ_automated-expert) must be computed with bootstrapped 95% confidence intervals. Per-stratum decomposition must be computed by hop depth. Phase 1 Tier classification must be applied using the Phase 2-binding κ ≥ 0.7 threshold specified in Phase 2 Design Section 2.2, superseding the provisional Landis-Koch reference in the Phase 1 Protocol Section F.4.

**openWorker trace-audit completion record.** Gate 2 completion must include the trace-field availability map for at least one concrete candidate openWorker codebase, using `openworker-trace-audit-template.md`, or an explicit record that no concrete openWorker code path was available to audit. This requirement does not block the automated MuSiQue measurement run, bridge fitting, contamination diagnostic, or annotation execution. It prevents the openWorker audit from remaining optional and supplies the Phase B replay and Phase 4 feasibility inputs needed downstream.

---

## Gate 3: Phase 1 to Phase 3 Handoff

Gate 3 verifies that Phase 1 outputs satisfy Phase 3 input requirements.

**Bridge validation verification.** The bridge diagnostic pass criteria from Phase 1 Protocol Section F.4 must be checked: residual normality at p > 0.01, homoscedasticity at p > 0.01, and ICC < 0.3 in at least two of three strata. If any criterion fails, the escalation path from Phase 1 Protocol Section C.3 must be triggered (isotonic regression, polynomial bridge, or V_frontier on full N). The chosen bridge form must be documented before Phase 3 execution proceeds.

**Tier classification and decision.** The Phase 1 Tier outcome (Tier 1 unconditional pass, Tier 2 conditional pass, Tier 3 design revision) must be determined under the κ ≥ 0.7 threshold. For Tier 3, Gate 3 halts and returns to Phase 0 revision cycle. For Tier 2, the specific conditional limitations must be documented for Phase 3 and Phase 4 inheritance. For Tier 1, Phase 3 proceeds under the unconditional-pass regime.

**Output preservation.** The full Phase 1 data artifact set per Phase 1 Protocol Section G.1 must be preserved with content hashes in the versioned data store. Phase 2 Design Section 7 handoff parameters (within-stratum σ_stratum, bridge coefficient variance, automated-to-expert disagreement rates, per-question inference cost) must be extracted and recorded for Phase 3 consumption.

**Retrieval simulation readiness.** The four retrieval configurations (bi-encoder plus cross-encoder primary, BM25 baseline, bi-encoder-only ablation, hybrid RRF) must be verified against the Phase 1 paragraph pools in a dry-run execution. Top-K values for the sensitivity sweep (K ∈ {3, 5, 10}) must be validated for each question's pool size.

---

## Gate 4: Phase 3 Pilot Execution

Gate 4 is the Phase 3 pilot execution, which is analytical post-processing of Phase 1 data rather than a separate data-collection cycle.

**Retrieval simulation execution.** Each of the four retrieval configurations must be applied to each of the 90 Phase 1 questions at the primary K = 5 and sensitivity-sweep K values. Extracted pool M membership must be recorded per question per configuration per K value.

**Completeness rate computation.** Per-question c_high and c_low must be computed under each retrieval configuration and K value. Stratum membership derives from the Phase 1 tertile classifications (using bridged δ_loo and per-stratum tertile boundaries). Aggregated completeness rates across questions must be computed with weighted averaging proportional to stratum membership counts.

**Statistical inference execution.** The point estimate Δ̂ = ĉ_low − ĉ_high must be computed for the pooled sample and per hop-depth stratum. Bootstrapped 95% confidence intervals must be constructed with B = 1,000 resamples clustered by question. Per-stratum confidence intervals must be reported with explicit sample-size caveats.

**Sensitivity analyses execution.** The top-K sweep across K ∈ {3, 5, 10} must be reported with the observation that per-K results illuminate different operational configurations. The retrieval-paradigm sweep across BM25, bi-encoder-only, and hybrid RRF must be reported with consistency-versus-divergence analysis. The linear-bridge versus isotonic-bridge sensitivity must be reported. The position-robustness scope limitation must be documented as an inherited caveat per Phase 2 Design Section 5.3 (composition-robustness sensitivity is deferred to the full study per Phase 2 Design Section 6.4).

---

## Gate 5: Phase 3 to Phase 4 Decision

Gate 5 applies the pilot-to-full-study decision rule and either warrants full-study execution or concludes the current workstream.

**Decision rule application.** The three-outcome classification from Phase 2 Design Section 6.3 must be applied to the pooled Δ̂ and its 95% confidence interval. The outcome classification (full study warranted, not warranted, or indeterminate) must be recorded with the specific values that triggered the classification.

**Full-study warrant documentation.** If full study is warranted, the handoff parameters per Phase 2 Design Section 7.2 must be extracted: pilot-measured Δ̂ point estimate and variance for power recalculation, pilot-measured within-stratum variance for sample-size refinement, observed bridge sensitivity for bridge-form selection, and top-K sensitivity results for prioritization.

**Not-warranted documentation.** If full study is not warranted, the pilot-level conclusion of approximate uniformity must be documented with the sample-size caveats specified in Phase 2 Design Section 6.3. The paper's Section 5.3 claims are affirmed at the pilot-level confidence, and the Phase 4 full-study work is deprioritized pending future re-evaluation.

**Indeterminate documentation.** If the pilot outcome is indeterminate, the context-sensitive adjudication pathway specified in Phase 2 Design Section 6.3 must be invoked. The contextual evidence that informs the judgment (timeline pressure, external constraints, scientific priority) must be documented explicitly so that the override decision is auditable.

---

## Parallel Workstream: openWorker Infrastructure Audit

The parallel workstream executes concurrently with Gate 2 and may continue through later gates. Its first output, the trace-field availability map or no-code-path blocker record, is a Gate 2 completion-package item. Later refinements can still feed Gate 5, but the initial availability conclusion is no longer optional.

**Trace-field availability mapping.** The five trace fields from the migration analysis (candidate pool, greedy trace, selected set, materialized context, extraction alignment) must be audited in the current openWorker codebase. For each field, the audit records availability status (already exported, partially exported, not exported), engineering effort estimate for full export, and any coupling to other infrastructure changes. This audit is specified as the early deliverable per Phase 0 Specification §6 and Phase 1 Protocol Appendix C.

**Engineering effort aggregation.** The per-field effort estimates must be aggregated into a total engineering-scope assessment with classification as "one-week port," "one-month effort," or "multi-month engineering project" per the Phase 0 Specification §6 taxonomy.

**Phase 4 feasibility documentation.** The infrastructure audit output must be documented as a Phase 4 feasibility input regardless of the Gate 5 decision outcome. If Gate 5 warrants full-study on MuSiQue, the infrastructure audit informs the downstream Phase 4 openWorker migration. If Gate 5 does not warrant full-study, the infrastructure audit still informs the Phase 4 direct-audit path that bypasses MuSiQue.

If no concrete openWorker code path is accessible, the audit output must state that blocker explicitly and must not infer any availability status from templates or adjacent systems.

---

## Risk Register and Mitigation Paths

The three-document suite identifies specific failure modes at each gate with pre-specified mitigation paths. This register consolidates them for rapid reference during execution.

**Gate 1 risks.** Model API access failures or rate-limit constraints motivate a fallback to smaller inference batches with longer wall-clock time. Annotator unavailability motivates pool re-recruitment with revised timeline.

**Gate 2 risks.** Bridge regression failures (residual diagnostic failures per Phase 1 Protocol Section C.3) trigger the three-tier escalation path to isotonic, polynomial, and V_frontier-only bridge forms. Inter-primary κ failures trigger the protocol refinement cycle per Phase 1 Protocol Appendix B.

**Gate 3 risks.** Tier 3 automation-substitution failure (κ_automated-expert < 0.7 with high confidence) halts the workstream and returns to Phase 0 for tolerance-band, annotator-hierarchy, or tertile-operationalization redesign per Phase 1 Protocol Appendix B.

**Gate 4 risks.** Retrieval simulation instability across seeds or implementation variants must be detected by reproducibility checks before downstream analysis. Divergence across sensitivity-analysis configurations (primary versus alternatives) requires scoping the Phase 2 conclusion to the deployment-target configuration per Phase 2 Design Section 4.3.

**Gate 5 risks.** Indeterminate outcomes require explicit context-sensitive adjudication per Phase 2 Design Section 6.3; silent default to "proceed" or "halt" is inadequate. The cost-asymmetry acknowledgment must be honored by documenting the specific reasoning that informs the indeterminate-case override.

---

## Checklist Summary

The three-document suite plus this checklist specifies the execution pathway from the current Phase 0 exit state to a Gate 5 decision on full-study warrant. The sequential gates each have verifiable completion criteria, and the parallel workstream proceeds independently on its own timeline. The specification suite is self-contained: no further design work is required to execute Phase 1, Phase 3, or Gate 5 decision-rule application. Additional design work becomes necessary only if Gate 5 warrants Phase 4 execution, which requires a Phase 4 full-study protocol document as its prerequisite.

The next executable action is Gate 1 pre-execution provisioning, which does not require further specification and can commence immediately upon user authorization.
