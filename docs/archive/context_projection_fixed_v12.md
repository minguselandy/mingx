# Context Projection Selection in Multi-Agent Systems: Conditional Theory, Metric Bridge, and Proxy-Regime Diagnosis

---

## Abstract

We study dispatch-time context projection in multi-agent LLM systems: given a candidate pool of extracted findings and a per-agent token budget, which content items should be projected into a dispatched worker's context? We formalize this as per-round, per-agent subset selection under a predictive V-information objective: the reduction in minimum achievable log-loss about a task target under a fixed predictive family.

The theoretical contribution is conditional. Under an explicit weak-submodularity regime hypothesis and a pairwise-additive absolute-complementarity assumption, we prove structural results for the formal objective: independence of the submodularity ratio $\gamma$ and the supermodular degree $d$, and a local block-ratio lower bound controlled by singleton mass and bounded pairwise interaction. The familiar fractional form is recovered only inside round-local active contexts where singleton marginals are observably bounded away from zero.

The deployment contribution is not V-information verification. We separate four layers that are often conflated: the formal V-information value, fixed-model or utility proxy measurements, heuristic retrieval/reranking/MMR pipelines, and metric-claim levels. This yields a conservative proxy-regime diagnostic policy that labels a dispatch stratum as `greedy_supported`, `pairwise_escalate`, `higher_order_risk`, or `ambiguous`, while separately reporting whether the metric evidence is V-information-proxy, bridge-calibrated, operational-only, or ambiguous.

As a minimal structural check, we include an oracle synthetic benchmark over redundancy, pairwise-synergy, higher-order-prerequisite, and adversarial-redundancy regimes. The benchmark supports diagnostic signature separation, but it does not establish deployed measurement validation. We also isolate extraction quality as an $M^*\to M$ bridge risk and specify model-adjudicated and human-sentinel audit paths for measuring value-dependent extraction loss.

## 1. Introduction

Multi-agent LLM systems often fail because the wrong information is projected into the wrong worker at the wrong time. A dispatched agent may receive redundant material, miss a prerequisite fact, or be forced to reason over a noisy context whose token budget is treated as a truncation constraint rather than as an optimization constraint. This paper studies that narrow failure surface: **dispatch-time context projection**, the per-round decision that determines which content items from a candidate pool enter a worker's context window.

The problem remains important even as context windows grow. In the ideal information-theoretic limit, a single agent with perfect access to the complete context should not be worse than a message-mediated system that sees only compressed fragments. Practical long-context models, however, suffer from attention dilution, position sensitivity, and context-utilization degradation. Multi-agent systems are therefore useful not because they create information for free, but because they impose structure on what each worker must attend to. The question is how to make that structure explicit, auditable, and measurable.

Let $M$ be a dispatch-time pool of extracted findings and let worker $i$ have task description $q_i$, role $R_i$, model family $\mathcal V_i$, and projected-observation budget $B_i$. The context projection selection problem is
\[
\max_{S_i\subseteq M} f_i(S_i)
\quad\text{s.t.}\quad
\sum_{m\in S_i}\mathrm{tokens}(m)\le B_i.
\]
The decision variable is the **content-item subset** projected into each worker's context. This distinguishes our setting from agent-activation methods, communication-topology pruning, memory-admission policies, and whole-session schedulers. The same finding may be projected to multiple workers, so under non-exclusive per-agent budgets the per-round selection problem decomposes by worker once the scheduler has chosen the dispatch event.

The paper makes five contributions.

1. **Formal object.** We formalize per-round, per-agent, token-budgeted content selection under a predictive V-information value function.
2. **Conditional theory.** We prove that the submodularity ratio $\gamma$ and supermodular degree $d$ are independent for general monotone set functions, and derive an absolute-increase pairwise-regime lower bound for local block ratios.
3. **Bridge statement.** We separate the formal V-information objective from fixed-model log-loss, operational utility, heuristic selector pipelines, and metric-claim levels.
4. **Proxy-regime diagnostics.** We define a conservative staged diagnostic policy that decides when greedy-style projection is supported, when pairwise or higher-order escalation is warranted, and when evidence is insufficient.
5. **Audit interface and extraction-risk model.** We specify runtime artifacts for replayable projection decisions and isolate extraction quality as a separate $M^*\to M$ bottleneck.

The claim boundary is deliberately narrow. The theory applies to the formal V-information objective under stated structural assumptions. The diagnostics estimate proxy or operational quantities under fixed calibration conditions. The runtime artifacts support observability and replay. None of these layers alone establishes deployed V-information verification or human-validated measurement evidence.

## 2. Problem Formulation

### 2.1 Setup and notation

Let $M=\{m_1,\ldots,m_N\}$ be the candidate pool of findings available at a dispatch snapshot. Each finding $m$ has natural-language content, token cost $c(m)=\mathrm{tokens}(m)$, and source metadata such as worker type, topic tags, evidence type, confidence, and provenance references. The selection problem operates over a pre-validated pool: admission, schema validity, and budget eligibility are handled upstream.

Worker $i$ is dispatched with task description $q_i$, role $R_i$, predictive family $\mathcal V_i$, and projected-observation budget $B_i$. The budget $B_i$ covers only the observation slot; system prompt, tool definitions, and task instructions are held fixed during selection. The enclosing runtime supplies the dispatch event
\[
(t,i,q_i,R_i,\mathcal V_i,B_i).
\]

The per-agent context selection problem is
\[
\max_{S\subseteq M} f_i(S)
\quad\text{s.t.}\quad
\sum_{m\in S} c(m)\le B_i.
\]
Findings are the analyzed unit because they are the cleanest unit for stating theory, measuring extraction risk, and instrumenting runtime traces. Other context items can be used if they expose the same cost, provenance, and materialization interfaces.

### 2.2 Formal and measured value functions

The formal value function is defined using predictive V-information (Xu et al., ICLR 2020):
\[
f_i^{\mathcal V}(S)
=
H_{\mathcal V_i}(Y_i\mid q_i)
-
H_{\mathcal V_i}(Y_i\mid q_i,X_S).
\]
Here $Y_i$ is the **task target** for the dispatched worker: a reference answer, latent correct variable, target state, or distribution over acceptable outputs. It is not the stochastic text generated by the worker. $X_S$ is the materialized content of the selected findings, and $H_{\mathcal V_i}$ is the minimum expected log-loss achievable by predictors in the family $\mathcal V_i$.

The measured quantities used by diagnostics need not equal this formal object. We therefore distinguish three value functions:
\[
f_i^{\mathcal V}(S)
\quad\text{formal V-information value},
\]
\[
f_i^{\theta,\ell}(S)
\quad\text{fixed deployed-model log-loss improvement},
\]
\[
f_i^{U}(S)
\quad\text{operational utility or judge-score improvement}.
\]
Section 3 analyzes $f_i^{\mathcal V}$. Section 4 diagnostics estimate $f_i^{\theta,\ell}$ or $f_i^U$ unless an explicit bridge justifies interpreting them as proxy evidence about $f_i^{\mathcal V}$.

**Input-closure assumption.** For monotonicity at the V-information layer, we assume $\mathcal V_i$ is closed under input ignoring: for every predictor using $(q_i,X_S)$ and every $T\supseteq S$, the enlarged-input family using $(q_i,X_T)$ contains a predictor that simulates the original predictor by ignoring $X_{T\setminus S}$.

**Proposition 1 (Basic properties under input closure).** For fixed $q_i$ and an input-closed predictive family $\mathcal V_i$, $f_i^{\mathcal V}$ is normalized, nonnegative, monotone, and agent-heterogeneous, but not necessarily submodular.

*Proof sketch.* Normalization follows from $f_i^{\mathcal V}(\varnothing)=0$. Nonnegativity and monotonicity follow because an input-closed predictive family can ignore additional variables, so the minimum achievable log-loss cannot increase when the available input set grows. Agent heterogeneity follows because workers may differ in $q_i$, $R_i$, and $\mathcal V_i$. Submodularity does not follow from the definition; it is the regime hypothesis studied below. This monotonicity statement is about the formal value object, not about arbitrary prompt materialization: inserting more text into a real prompt can still harm performance through position effects, distraction, or formatting changes.

The agent-conditional density used by greedy-style selectors is
\[
\rho_i(m\mid S)=\frac{\Delta f_i(m\mid S)}{\mathrm{tokens}(m)},
\qquad
\Delta f_i(m\mid S)=f_i(S\cup\{m\})-f_i(S),
\]
where the relevant $f_i$ must always be specified as $f_i^{\mathcal V}$, $f_i^{\theta,\ell}$, or $f_i^U$.

## 3. Theoretical Results

### 3.1 Condition A as a regime hypothesis

The submodularity ratio $\gamma$ (Das & Kempe, JMLR 2018) measures the worst-case ratio of the sum of singleton marginal gains to the joint marginal gain. When $\gamma=1$, the function is submodular. Under the usual cardinality-constrained weak-submodular idealization, greedy has the familiar $(1-e^{-\gamma})$ form. The deployed selector in this paper is token-budgeted and density/MMR-style; it should be treated as a heuristic unless a separate knapsack-specific approximation analysis is supplied.

This subsection is an **assumption layer**, not a proof layer. Its role is to define the regime hypothesis used by the theory, explain why that hypothesis is plausible enough to study, distinguish supporting evidence from proof, and identify the settings where it is most likely to fail.

We organize the regime assumptions into four conditions.

**Condition A (regime hypothesis): approximate diminishing returns for the formal value object.** The central hypothesis of the paper is that the V-information value function for context projection is approximately submodular, or at least weakly submodular with a nontrivial block-ratio structure, for the deployed model family on the target task distribution. Operationally, this means the marginal gain of adding a finding usually decreases as the context set becomes more informative.

Condition A is worth studying for three reasons. First, for Shannon mutual information, conditional independence is sufficient for exact submodularity (Krause & Guestrin, 2005), so the hypothesis has a clean information-theoretic ancestor. Second, V-information approaches Shannon-style behavior in the limit where the predictive family becomes sufficiently expressive, while restricted predictive families can suppress high-order synergies the model cannot exploit. Third, in practical context-projection settings many findings are partially redundant or only weakly complementary, which makes a diminishing-returns approximation plausible enough to motivate formal analysis.

The available evidence is **supporting, not proving**. Empirical evidence from multi-hop QA suggests that performance degrades as interactions deepen: Wu et al. (2024) found that GPT-4 performance drops from 62.8 F1 at 2 hops to 53.5 F1 at 4 hops on the IRE benchmark, with the steepest degradation at the 3-hop boundary. On MuSiQue (Trivedi et al., 2022), single-paragraph models achieve about 65 F1 on 2-hop questions but only about 32 F1 on composed multi-hop questions. These results support the idea that pairwise or weakly higher-order interaction models may often be adequate, but they do not prove that V-information itself is approximately submodular.

Mechanistic intuition points in the same direction without closing the proof gap. Wang et al. (2026) show that in a single-layer Transformer, contextual correction decomposes additively across context items, and that multi-item effects are mediated through an attention-weighted aggregate. This suggests two damping forces on complementarity — attention-weight dilution and a low-dimensional aggregation bottleneck — which make pairwise-additive interaction models plausible as an approximation. But this remains a mechanistic analogy, not a derivation of V-information submodularity bounds.

Condition A is most likely to fail in settings with essential higher-order dependence: deep multi-hop reasoning chains, tightly coupled prerequisite bundles, tool outputs that are individually uninformative but jointly decisive, or deployment shifts where the evaluated model tier no longer matches the effective predictive family. These are precisely the cases where the diagnostics in Section 4 should produce low-confidence proxy labels, elevated synergy, higher-order excess, or ambiguity and trigger escalation or claim downgrade.

**Condition B: bounded redundancy within topic clusters.** When findings with overlapping metadata have high pairwise embedding similarity, redundant findings contribute diminishing marginal value. This creates strong local submodularity within topic clusters. The local block ratio within such clusters is expected to be close to or above 1, and the reported lower-quantile diagnostic should be high after capping to the weak-submodular range.

**Condition C: bounded complementarity degree.** When the number of findings participating in synergistic interactions with any single finding is bounded by a constant $d$, the interaction graph is combinatorially sparse. This sparsity alone does **not** imply a lower bound of the form $\gamma \ge 1/(1+d\delta_{\max})$; it only supplies one structural ingredient for such a bound.

**Condition C' (pairwise-additive absolute complementarity).** Theorem 1 additionally assumes that complementary effects aggregate in a pairwise-additive **absolute-increase** form. For all $x$, all contexts $L$, and all blocks $S$ disjoint from $L\cup\{x\}$,
\[
\Delta f(x\mid L\cup S)
\le
\Delta f(x\mid L)
+
\sum_{y\in S}\eta(x,y\mid L),
\]
where
\[
\eta(x,y\mid L)
=
\left[
\Delta f(x\mid L\cup\{y\})-\Delta f(x\mid L)
\right]_+,
\qquad
\eta_{\max}=\max_{x,y,L}\eta(x,y\mid L).
\]
This assumption is load-bearing. It rules out uncontrolled higher-order cross terms in the telescoping expansion and is what makes the degree-and-strength lower bound possible. Theorem 1 should therefore be read as a **pairwise-regime sharpening result**, not as a general higher-order interaction theorem.

Bai and Bilmes (2018) Lemma J.1 establish the adjacent bound $\gamma \ge 1-\kappa^g$ for BP-decomposable functions, where $\kappa^g$ is the supermodular curvature of the supermodular component, and show via an explicit construction that this bound can be loose: a monotone supermodular function with $\kappa^g = 1$ can still have $\gamma$ arbitrarily close to 1. Their example occupies the analogous corner of the $(\gamma,\kappa^g)$ parameter space. We formalize the parallel independence between $\gamma$ and the combinatorial supermodular degree $d$ (Feige & Izsak, 2013), which is the operative structural parameter for our pairwise-additive regime.

**Proposition 2 (Independence of $\gamma$ and $d$).** For general nonnegative monotone set functions, the submodularity ratio $\gamma$ and supermodular degree $d$ are independent: neither bounds the other. A function with $d = 1$ can have $\gamma \to 0$ (one pair with arbitrarily strong synergy), and a function with $d = n-1$ can have $\gamma \to 1$ (every pair interacts but each interaction is vanishingly small). Constructions are given in Appendix A. This is why the Feige & Izsak (ITCS 2013) framework, which bounds approximation via $d$ alone, and the Das & Kempe (JMLR 2018) framework, which bounds via $\gamma$ alone, cannot be unified without additional structure such as the pairwise-additive assumption of Theorem 1.

**Theorem 1 (Absolute-increase pairwise-regime bound).** Let $f$ be nonnegative and monotone, and suppose Conditions C and C' hold with supermodular degree $d$ and maximum absolute interaction strength $\eta_{\max}$. The ratio statement applies to disjoint context/block pairs $(L,S)$ with $\Delta f(S\mid L)>0$; if $\Delta f(S\mid L)=0$, the block is ratio-uninformative and is excluded from ratio diagnostics. For $S=\{x_1,\ldots,x_s\}$, define
\[
A(L,S)=\sum_{x\in S}\Delta f(x\mid L),
\qquad
\psi_{s,d}=\sum_{i=1}^{s}\min(i-1,d).
\]
Then the local block ratio satisfies
\[
r_f(L,S)
=
\frac{\sum_{x\in S}\Delta f(x\mid L)}
{\Delta f(S\mid L)}
\ge
\frac{A(L,S)}
{A(L,S)+\psi_{s,d}\eta_{\max}}.
\]
Since $\psi_{s,d}\le sd$, a simpler conservative form is
\[
r_f(L,S)
\ge
\frac{A(L,S)}
{A(L,S)+sd\,\eta_{\max}}.
\]

*Interpretation.* This theorem is robust in prerequisite-chain regimes. If all singleton marginals in a block are zero while the joint block has value, then $A(L,S)=0$ and the bound correctly collapses to zero. The theorem therefore does not hide zero-marginal complementarity behind an undefined fractional denominator.

**Corollary 1 (Fractional active-context corollary).** Fix a dispatch round and context $L$. Let
\[
\tau_{r,q}^{LCB}
=
Q_q^{LCB}\left(\{\Delta f(x\mid L):x\in C_L\setminus L\}\right)
\]
be a lower-confidence lower quantile of singleton marginals over the residual top-$L$ candidate slice. Define the active residual set
\[
A_{\tau}(L)=\{x:\Delta f(x\mid L)\ge \tau_{r,q}^{LCB}\}.
\]
For any block $S\subseteq A_{\tau}(L)$, if $\tau_{r,q}^{LCB}>0$, Theorem 1 implies
\[
r_f(L,S)
\ge
\frac{1}
{1+d\cdot \eta_{\max}/\tau_{r,q}^{LCB}}.
\]
Thus the familiar fractional form is recovered with
\[
\delta_{\mathrm{active}}=\eta_{\max}/\tau_{r,q}^{LCB}.
\]
If $\tau_{r,q}^{LCB}$ is near zero, the fractional corollary is marked **inactive** rather than applied with a fragile global positive-marginal assumption.

**Corollary 2 (Higher-order correction under non-amplifying third-order synergy).** Suppose that, in addition to the pairwise-additive regime of Theorem 1, third-order synergy contributes additively without amplifying pairwise interactions. Let $u_{ijk}(L)$ denote the positive excess value of triple $\{i,j,k\}$ beyond singleton and pairwise terms, and suppose at most $t$ such third-order excess terms are relevant to any block and each is bounded by $\eta_3$. Then
\[
r_f(L,S)
\ge
\frac{A(L,S)}
{A(L,S)+\psi_{s,d}\eta_{\max}+t\eta_3}.
\]
This is a conditional higher-order correction, not a general third-order theorem. It should not be applied in mediated-amplification regimes where the triple's value requires pairwise links to be present and thereby amplifies rather than adds to pairwise effects. Section 4 therefore includes a finite-sample triple-excess test before this corollary is used operationally.

**Corollary 3 (Combined active-context bound).** For BP-decomposable functions with supermodular curvature $\kappa^g$, and for blocks inside the round-local active set of Corollary 1,
\[
r_f(L,S)
\ge
\max\left(1-\kappa^g,\; \frac{1}{1+d\delta_{\mathrm{active}}}\right),
\]
where the first bound is Bai and Bilmes (2018) Lemma J.1 and the second is the active-context corollary of Theorem 1. The first bound dominates when interactions are uniformly weak across the full ground set, where continuous curvature is the natural parameterization; the second dominates when interactions are sparse but potentially strong, where combinatorial degree plus interaction strength is the natural parameterization.

| Symbol | Definition |
|--------|-----------|
| $\gamma$ | Global submodularity ratio (Das & Kempe): worst-case ratio of sum-of-marginals to joint marginal |
| $r_f(L,S)$ | Local block ratio $\sum_{x\in S}\Delta f(x\mid L)/\Delta f(S\mid L)$ |
| $\widehat{\gamma}^{op,LCB}_{b,q}$ | Operational lower-quantile LCB for sampled block ratios; the headline diagnostic in Section 4 |
| TraceDecay | Trace-local marginal-decay statistic $\Delta f(m_t\mid P_{t-1})/\Delta f(m_t\mid\varnothing)$; useful but not a submodularity-ratio estimator |
| $d$ | Supermodular degree (Feige & Izsak): max pairwise supermodular interactions per item |
| $\eta_{\max}$ | Maximum absolute pairwise marginal increase |
| $\delta_{\mathrm{active}}$ | Round-local fractional interaction strength $\eta_{\max}/\tau_{r,q}^{LCB}$, valid only in active contexts |
| $t$ | Count or bound on relevant non-amplifying third-order excess terms |
| $\eta_3$ | Maximum absolute third-order excess |

**Worked example.** Consider a data analysis task where a worker receives findings from three upstream workers. Two findings about overlapping market segments interact synergistically with at most $d=2$ complements per item, and the maximum absolute pairwise marginal increase is $\eta_{\max}=0.15$ utility units. If the active-context singleton lower quantile is $\tau_{r,q}^{LCB}=1.0$, the active-context corollary gives
\[
r_f(L,S)\ge \frac{1}{1+2\cdot 0.15}=0.77,
\]
which, under the corresponding cardinality-constrained weak-submodular idealization, would yield the familiar $(1-e^{-0.77})\approx 54\%$ form. This is not a theorem-level guarantee for the deployed token-budgeted density/MMR selector. **Failure case:** a 3-hop legal reasoning chain (statute $\rightarrow$ precedent $\rightarrow$ application) where each item is individually uninformative until the whole chain is present. In that case $\tau_{r,q}^{LCB}$ is near zero, the fractional corollary is inactive, and the absolute theorem reports a low or zero block ratio rather than masking the prerequisite failure.

At deployment time, the key quantity is a calibrated operational block-ratio diagnostic rather than a theorem-level bound on the global worst-case $\gamma$. The a priori bounds from Theorem 1 and its corollaries predict what a healthy pairwise-active regime should look like; discrepancies between those predictions and measured proxy-layer diagnostics are diagnostically informative (Section 4).

**Positioning note.** Under pairwise-additive complementarity, the regime studied here is naturally positioned alongside knapsack problems with pairwise interactions, in a quadratic-knapsack-like sense. This correspondence is structural rather than reformulatory: the budgeted subset-selection interface and the bounded-complementarity parameters align naturally with that family, but the formal objective remains the V-information value function $f_i(S)$, and $\eta_{\max}$ should be read as an interaction-strength analogue rather than as a fixed quadratic coefficient. We use this correspondence only to clarify the interpretation of $d$, $\eta_{\max}$, and the escalation family, not to redefine the formal optimization problem or claim additional approximation guarantees.

### 3.2 Decomposition of the multi-agent problem (Observation 3)

Under non-exclusive allocation and separable per-agent budget constraints, the **per-round** joint problem over $K$ agents with value functions $f_1,\ldots,f_K$ decomposes into independent per-agent selection problems. The architecture (openWorker, described in Section 6) allows the same finding to be projected to multiple agents, so choosing the optimal $S_i^*$ for agent $i$ does not restrict the feasible set for agent $j$.

This is a **design insight**, not a mathematical advance: the architecture was deliberately chosen to allow non-exclusive allocation, so the per-round joint problem decomposes by design into independent per-agent problems and avoids the multi-agent coordination machinery required in the harder exclusive-allocation case (Santiago & Shepherd, APPROX 2018). This decomposition assumes that the scheduler has already committed to the activated agents in round $t$. It is scope-limited: it does not address scheduler-induced inter-round coupling, future candidate-pool shaping, or downstream redundancy externalities across agents.

### 3.3 Extraction as a bridge-risk model

The candidate pool $M$ is produced by an extraction gate that converts free-text worker outputs into structured findings. Any approximation statement from Section 3 is therefore relative to $OPT$ over $M$, not over the true information space $M^*$. We model extraction quality as a **separate bridge risk** between the formal objective and end-to-end performance rather than as an automatic extension of the weak-submodular guarantee.

Under a stylized uniformity assumption — namely, that extraction failures are approximately uniform across the value distribution and do not disproportionately remove the support of high-value solutions — one expects degradation to scale roughly linearly with extraction completeness $c$. We use this stylized picture only as motivation for Section 5's audit protocol; we do **not** claim a general theorem of the form
\[
E[f(S_{greedy})] \ge (1-e^{-\gamma})\cdot c \cdot OPT(M^*).
\]
If the gate disproportionately misses high-value findings, the degradation can be substantially worse than linear. Section 5 therefore treats extraction quality as a **testable bottleneck**, not as a proven extension of the formal approximation guarantee.

### 3.4 Bridge statement: from formal objective to proxy measurement to runtime heuristic

This subsection is the paper's bridge statement and a second core contribution. It fixes the coordinate system for everything that follows by separating the **formal object**, the **proxy**, the **pipeline**, and the **metric-claim level**, so that theorem-level claims, proxy-level measurements, and runtime behavior are not conflated.

| Layer | Object | Paper claim |
|---|---|---|
| Formal | V-information set function $f_i^{\mathcal V}(S)$ | Conditional theory |
| Fixed-model proxy | $f_i^{\theta,\ell}(S)$, CI/replay log-loss marginal estimates | Diagnostic signal under predictor-optimality and materialization conditions |
| Utility proxy | $f_i^U(S)$, model-judged or task-utility finite differences | Operational signal unless bridge-calibrated |
| Pipeline | retrieval / reranking / MMR / packing | Heuristic only |
| Runtime | artifacts, memory, verification, state summaries | Observability and escalation interface |
| Metric bridge | log-loss or calibrated utility-to-log-loss relation | Claim-level gate |

The claim gate is conservative by construction. Missing evidence lowers the allowed claim rather than being interpreted as a successful diagnostic. The following table fixes the manuscript-level rule used by the runtime-audit scaffold; in particular, missing human labels and missing kappa prevent `measurement_validated`.

| Evidence condition | Allowed claim boundary | Denied claim |
|---|---|---|
| contamination failure | `pilot_only` | `measurement_validated` |
| missing human labels | not `measurement_validated` | `measurement_validated` |
| missing kappa | not `measurement_validated` | `measurement_validated` |
| stale metric bridge | `operational_utility_only` or `ambiguous` | measurement validation |
| missing metric bridge | `operational_utility_only` or `ambiguous` | measurement validation |
| synthetic-only evidence | `synthetic_structural_only` | deployed V-information verification |
| engineering-only evidence | `engineering_smoke_only` | scientific validation |
| replay package completeness | `replayable_artifact_evidence` | scientific validation |
| paper-facing summary | no claim upgrade | measurement validation |
| live API success alone | operational evidence only | measurement validation |
| external runtime success alone | operational evidence only | measurement validation |

**Formal layer.** The object analyzed in Section 3 is the V-information value function $f_i^{\mathcal V}(S)$. All approximation statements, including Theorem 1 and its corollaries, apply to this formal object. They do not directly apply to fixed-model loss, model-judged utility, or an implementation that scores items with heuristics.

The formal-to-theorem transfer via a structural condition is an established template rather than a claim of novelty here. Das and Kempe (2018) use the submodularity ratio $\gamma$, Elenberg, Khanna, Dimakis, and Negahban (2018) use restricted strong convexity parameters to establish weak-submodularity consequences, and Bian, Buhmann, Krause, and Tschiatschek (2017) combine $\gamma$ with generalized curvature. What the bridge statement below adds on top of this established template is an explicit **proxy layer**, an explicit **pipeline layer**, a metric-scope gate, a conditional-equivalence analysis with enumerated failure modes, and the stratified diagnostic decomposition used in Section 4.

**Proxy layer.** The diagnostics in Section 4 require marginal value gains. In practice these are estimated as fixed-model log-loss deltas $\Delta f_i^{\theta,\ell}$ or operational utility deltas $\Delta f_i^U$, for example through CI Value or counterfactual replay. These measurements become evidence about $f_i^{\mathcal V}$ only under a predictor-optimality bridge, log-loss alignment plus a fresh fixed-model-to-$\mathcal V_i$ bridge, a near-optimality argument, actual empirical minimization over the declared predictive family, or a measured utility-to-log-loss bridge.

**Metric-bridge regimes.** Full V-information-calibrated diagnostics apply only under log-loss evaluation or a validated utility-to-log-loss bridge; otherwise, the diagnostics are operational-utility-only signals and must not be reported as evidence about the formal V-information regime. We distinguish three metric regimes.

1. **Regime A: log-loss aligned.** The predictive family $V_i$ matches the deployed model tier, the materialization order is fixed, and the evaluation metric is log-loss. In this regime, CI-style finite differences can be interpreted as proxy measurements of the formal V-information value function only when paired with a fresh fixed-model-to-$V_i$ bridge, a reviewed near-optimality argument, or actual empirical minimization over the declared predictive family. Generic utility-to-log-loss correlation is not formal V-information support by itself.

2. **Regime B: bridge-calibrated decomposable utility.** Production uses a non-log-loss utility $U$, but a stratum-specific bridge calibration verifies that utility marginals track log-loss marginals. For stratum
\[
s=(\text{task family},\text{model tier},\text{materialization policy},b,\text{candidate-slice band},\text{metric}),
\]
the required calibration is
\[
\left|\Delta_U(A\mid L)-c_s\Delta_{\ell}(A\mid L)\right|\le \zeta_s
\]
for evaluated blocks $A$ up to the diagnostic block size. Then a utility-level block ratio can be converted into a conservative log-loss ratio bound:
\[
r_{\ell}(L,S)
\ge
\frac{A_U-b\zeta_s}{B_U+\zeta_s},
\qquad
A_U=\sum_{x\in S}\Delta_U(x\mid L),\quad
B_U=\Delta_U(S\mid L).
\]
This bridge is valid only while the calibration epoch is fresh and the active stratum of the dispatch matches the stratum for which $\zeta_s$ was measured.

**Bridge-calibration status.** The synthetic benchmark in Section 4.6 is an oracle structural check; it does not estimate a real utility-to-log-loss residual. The P45 bridge-calibration lane has now been implemented for the current `bio_attribute` stratum, and that stratum did not establish a stable utility-to-log-loss bridge. For the current `bio_attribute` stratum, no `calibrated_proxy_supported` claim is allowed. Downstream utility diagnostics remain `operational_utility_only`, while the underpowered failed bridge artifact remains `ambiguous_metric`. This is a fail-closed negative result and claim-gate record, not bridge support.

3. **Regime C: non-decomposable or uncalibrated production utility.** Pass/fail task success, rubric scores with nonlinear aggregation, evaluator preferences, and human judgments can be measured through finite differences, but they do not automatically approximate log-loss deltas or V-information deltas. In this regime the protocol reports operational-utility-only labels for the utility objective
\[
f_U(S)=\mathbb E[U(\text{output from }S)].
\]
These labels may guide escalation, but they do not certify Condition A, Theorem 1, or V-information weak-submodularity.

**Pipeline layer.** The deployed system uses a heuristic scoring and packing pipeline rather than directly optimizing CI Value or the V-information objective. In other words, the pipeline is not assumed to optimize the proxy; at best, it is expected to correlate with the proxy strongly enough to be useful.

Two recent works propose partial bridge statements at adjacent abstraction levels. Tok-RAG (Xu et al., 2025) establishes a token-level theory in which distribution similarity between the RAG-fused and retrieved-text distributions serves as a theoretically justified proxy for a benefit-versus-detriment gap, and then operationalizes that theory with a per-token switching rule. AdaGReS (Peng et al., 2025) establishes $\varepsilon$-approximate submodularity for token-budgeted context selection under practical embedding-similarity conditions, together with a closed-form instance-adaptive calibration of the relevance-redundancy trade-off parameter. Both are important adjacent precedents, but their epistemic posture differs from the one taken here. First, the proxy-objective relationship in our setting is explicitly **conditional** on a model-tier match, log-loss utility, or a measured utility-to-log-loss bridge. Second, the deployed pipeline here is explicitly **not assumed to implement** the theoretical decision rule; the pipeline-versus-proxy gap is itself a first-class object of diagnosis. Third, Section 4 stratifies diagnostics across formal, proxy, pipeline-versus-proxy, and metric-claim layers rather than collapsing them into a single operational test.

This distinction matters because the diagnostics do not all measure the same thing:

1. **Formal-layer statements** belong to Section 3 only. They concern $f_i^{\mathcal V}(S)$, $\gamma$, $d$, $\eta_{\max}$, and local block ratios as mathematical objects.
2. **Proxy-layer diagnostics** estimate quantities defined relative to CI-based marginal utilities. The block-ratio LCB and pairwise interaction statistics are in this category only when the metric bridge is valid.
3. **Operational-utility diagnostics** estimate structure in $f_U$ when the metric bridge is absent or stale. They can guide escalation but cannot be used as evidence about the formal V-information regime.
4. **Pipeline-versus-proxy diagnostics** measure whether the deployed heuristic behaves consistently with the proxy layer. The greedy-versus-augmented gap, rank-correlation studies, and replay studies belong here.

Three factors limit proxy fidelity even before the pipeline enters the picture:

1. *Model-tier / log-loss alignment.* The approximation is clean only when the loss function is log-loss and the model tier is fixed. If production uses a different evaluation criterion, the gap between CI Value and V-information must be measured through $\zeta_s$ or the claim must be downgraded.

2. *Sample variance.* Leave-one-out evaluation introduces variance from stochastic decoding. Calibration evaluations should use controlled decoding or average over multiple runs per item and block.

3. *Context position effects.* "Lost in the Middle" positional bias (Liu et al., TACL 2024) means $\Delta f_i(m\mid S)$ depends not just on the set $S$ but on the ordering within the assembled context. CI evaluations must therefore use the same materialization ordering as the production pipeline; if the ordering changes, calibration data may not transfer.

These are limitations of the bridge, not of the formal theory. When the bridge fails, the consequences are asymmetric: overestimating proxy fidelity creates silent false confidence, while underestimating it mainly wastes compute through unnecessary escalation.

**Standing assumption for Section 4.** Unless otherwise stated, the diagnostics in Section 4 should be read as proxy-layer or pipeline-versus-proxy measurements, not as direct evaluations of the formal objective. They are meaningful as V-information proxy labels only to the extent that the CI proxy is well aligned with the deployed model tier, evaluation metric, and materialization order. If that bridge is absent or stale, the same measurements are reported as operational-utility diagnostics only.

Accordingly, deployment receives **proxy-regime labeling + monitoring + escalation**, not automatic theorem inheritance.

---

## 4. Proxy-Regime Diagnosis and Escalation Protocol

This section defines the operational diagnostic policy. Its purpose is not to estimate the global worst-case submodularity ratio and not to verify Condition C' uniformly. It answers a narrower deployment question: **is greedy-style context projection supported in the current calibrated stratum, should the selector escalate, or is the evidence insufficient?**

The protocol returns two labels:
\[
(\texttt{metric\_claim\_level},\texttt{selector\_regime\_label}).
\]
The first label says what the measurements are allowed to mean; the second says what selector action is justified.

### 4.1 Metric-claim levels

| Metric claim level | Meaning |
|---|---|
| `vinfo_proxy_supported` | log-loss alignment plus a fresh fixed-model-to-$V_i$ bridge, a reviewed near-optimality argument, or actual empirical minimization over the declared predictive family |
| `calibrated_proxy_supported` | utility-to-log-loss bridge has a measured residual bound in the active stratum |
| `operational_utility_only` | diagnostics are useful for the deployed utility but not for V-information claims |
| `ambiguous_metric` | bridge missing, stale, underpowered, or stratum-mismatched |

A fixed-model finite difference estimates $f_i^{\theta,\ell}$, not $f_i^{\mathcal V}$, unless the deployed predictor is known to be near-optimal within $\mathcal V_i$, a fresh fixed-model-to-$V_i$ bridge has been reviewed, or the empirical risk minimum over $\mathcal V_i$ is actually estimated. Generic utility-to-log-loss correlation is not formal V-information support by itself. For utility metrics, a stratum-specific calibration is required:
\[
\left|\Delta_U(A\mid L)-c_s\Delta_\ell(A\mid L)\right|\le \zeta_s.
\]
If this bridge is stale or absent, the same numerical diagnostics may still guide operations, but they must be reported as `operational_utility_only` or `ambiguous_metric`.

### 4.2 Selector-regime labels

| Selector label | Meaning | Action |
|---|---|---|
| `greedy_supported` | bridge fresh, signal adequate, pair-block ratio healthy, positive pairwise excess low, seeded-augmented-greedy gap small | use monitored greedy/MMR |
| `pairwise_escalate` | pairwise complementarity or meaningful seeded-augmented-greedy improvement detected | use seeded augmented greedy or pair-aware local search |
| `higher_order_risk` | pair diagnostics insufficient, triple/prerequisite sentinel fires, or greedy-vs-SAG disagreement suggests hidden synergy | use stronger search, re-projection, decomposition, or adjudication |
| `ambiguous` | low denominator, insufficient samples, failed audit, conflicting signals, or stale bridge | recalibrate, run replay, or report operational-only evidence |

The protocol is optimized for asymmetric risk. A false `greedy_supported` label is worse than an unnecessary `ambiguous` or escalation label. Ambiguity is therefore a safety state, not a failed experiment.

### 4.3 Four-gate diagnostic policy

**Gate 0 — metric bridge.** The runtime checks model tier, metric class, materialization policy, calibration epoch, active stratum, bridge residual, effective sample size, and drift status. Failure at this gate prevents V-information proxy claims.

**Gate 1 — signal adequacy.** For each sampled block $(L,S)$, define
\[
A(L,S)=\sum_{x\in S}\Delta f(x\mid L),\qquad
B(L,S)=\Delta f(S\mid L).
\]
A block is active if $B(L,S)$ is confidently above a predeclared signal threshold, ordinary if numerator and denominator are both usable, inactive-singleton if $A$ is near zero but $B$ is positive, and uninformative if $B$ is too small or too noisy. Ratios are computed only for informative blocks.

**Gate 2 — pairwise structure.** The headline ratio diagnostic is the lower-confidence lower quantile of pair-block ratios over the selector's top-slice decision region:
\[
\widehat\gamma^{op,LCB}_{2,q}.
\]
The companion interaction diagnostic is the pairwise set-function excess
\[
E_2(x,y\mid L)
=
\Delta f(\{x,y\}\mid L)-\Delta f(x\mid L)-\Delta f(y\mid L).
\]
Positive $E_2$ indicates synergy; negative $E_2$ indicates redundancy. This is a set-function excess statistic, not classical co-information or interaction information.

**Gate 3 — algorithmic gap.** The most decision-relevant diagnostic is the calibration-time gap between monitored greedy/MMR and seeded augmented greedy:
\[
G_{SAG}=f(\mathrm{SAG}_k)-f(\mathrm{Greedy}).
\]
Healthy pair diagnostics plus a small $G_{SAG}$ support `greedy_supported`. Elevated pairwise excess plus a meaningful $G_{SAG}$ supports `pairwise_escalate`. Healthy pair diagnostics plus a large $G_{SAG}$ triggers `higher_order_risk` or `ambiguous`, because it suggests hidden higher-order structure or pipeline mismatch.

TraceDecay is retained only as a runtime health monitor for prefix saturation: it tracks position-conditional singleton decay along the realized prefix and is not a submodularity-ratio estimator.

### 4.4 Higher-order and runtime escalation

Triple diagnostics are not part of the default path. They are invoked as sentinels when pair diagnostics and algorithmic-gap evidence disagree, when singleton marginals are near zero but joint block values are positive, or when the task family is known to involve prerequisite chains. For triples $\{i,j,k\}$, define the pairwise-additive prediction
\[
P_{ijk}=a_i+a_j+a_k+\beta_{ij}+\beta_{ik}+\beta_{jk}
\]
and triple excess
\[
\omega_{ijk}=\Delta f(\{i,j,k\}\mid L)-P_{ijk}.
\]
A positive lower-confidence bound on $\omega_{ijk}$ triggers `higher_order_risk`; an underpowered test triggers `ambiguous`, not validation.

The runtime may also use post-dispatch uncertainty as an escalation trigger. Inspired by uncertainty-triggered adaptive context allocation, the worker output can be labeled as `grounded`, `unknown_due_to_missing_context`, `hallucination_risk`, `wrong_despite_context`, or `ambiguous`. Missing-context or hallucination-risk labels trigger re-projection: restore the dispatch state, expand the budget or switch selector, regenerate, and record a `ReprojectionWitness`.

### 4.5 Model-adjudicated benchmark construction

Manual annotation is not required for scalable dataset construction. The experimental lane used here is model-adjudicated: a strong evaluator model generates and labels benchmark instances under frozen prompts. These labels support structural and operational proxy evidence; they do not by themselves establish human-validated measurement claims.

The benchmark pipeline separates four roles:

| Role | Function | Output |
|---|---|---|
| Generator | creates task packet, gold sketch, candidate findings | benchmark instance |
| Structural labeler | labels singleton, pair, triple, and subset relations | preliminary labels |
| Verifier | finds contradictions, unstable labels, and prompt failures | verification report |
| Adjudicator | resolves disagreements under frozen prompts | final labels |

Prompt development is performed on a development split and frozen before final evaluation. The benchmark records model version, prompt hash, decoding policy, date, and all generated labels. Quality controls include order reversal, duplicate judging, paraphrase robustness, counterfactual deletion, redundancy swap, prerequisite ablation, cross-judge comparison, and unstable-label downgrade to `ambiguous`.

### 4.6 Minimal oracle synthetic benchmark

As a structural smoke test, we executed a small oracle benchmark with four synthetic families: redundancy-dominated, pairwise synergy, higher-order prerequisite, and adversarial redundancy. Each family contains 40 instances with $n=14$ items and budget $B=14$ under heterogeneous token costs. The oracle value function is known, so greedy, seeded augmented greedy with seeds of size at most two, pair-aware local search, and optimal brute-force selection can be compared directly. The random seed is `20260319`; the result files are included as companion CSV artifacts.

This benchmark is intentionally limited. It tests whether the diagnostic policy has the intended signature behavior on controlled set functions. The marginal query used in the benchmark is the oracle analogue of a CI-style leave-one-out finite difference: exact singleton, pair, and block deltas replace empirical log-loss or utility deltas. Thus the benchmark tests selector-structure behavior under known value functions, not the fidelity of CI Value, model-adjudicated utility, or deployed V-information. It does not validate deployed V-information, does not validate model-adjudicated labels, and does not replace bridge calibration or offline replay on real dispatch traces.

| True regime | `ambiguous` | `greedy_supported` | `higher_order_risk` | `pairwise_escalate` |
|---|---:|---:|---:|---:|
| adversarial redundancy | 37 | 0 | 0 | 3 |
| higher-order prerequisite | 9 | 0 | 31 | 0 |
| pairwise synergy | 10 | 7 | 0 | 23 |
| redundancy-dominated | 3 | 37 | 0 | 0 |

| Regime | $\widehat\gamma^{op}_{2,.10}$ | mean positive $E_2$ | max $E_2$ | max $E_3$ | Greedy/OPT | SAG/OPT | SAG gap / OPT |
|---|---:|---:|---:|---:|---:|---:|---:|
| adversarial redundancy | 0.594 | 0.320 | 3.278 | 0.000 | 0.987 | 0.998 | 0.012 |
| higher-order prerequisite | 1.000 | 0.000 | 0.000 | 8.292 | 0.376 | 0.686 | 0.310 |
| pairwise synergy | 0.981 | 0.197 | 3.528 | 0.000 | 0.895 | 0.997 | 0.102 |
| redundancy-dominated | 1.000 | 0.000 | 0.000 | 0.000 | 0.993 | 1.000 | 0.007 |

The smoke test satisfies the conservative safety target: no higher-order prerequisite instance receives `greedy_supported`. Pairwise-synergy instances frequently trigger `pairwise_escalate`, and seeded augmented greedy nearly closes the optimality gap in that family. The adversarial-redundancy family is mostly labeled `ambiguous`, which is the intended conservative response because duplicate redundancy, corroborative redundancy, and adversarial repetition share surface similarity features that pairwise value diagnostics alone cannot reliably distinguish. In such cases, the protocol deliberately prefers abstention over a false `greedy_supported` label; provenance and contradiction metadata, as specified in Section 6, are the runtime signals needed to break this tie. The high ambiguity rate is still a limitation: the diagnostic policy is safe but not yet highly discriminative in adversarial settings.

### 4.7 One-stratum bridge calibration and replay requirements

The first one-stratum bridge-calibration lane has been executed for the current `bio_attribute` stratum. Its purpose was to test whether the metric contract in Section 3.4 is executable for a controlled stratum, not to validate all deployments. The lane fixed task family, model tier, materialization order, decoding policy, block size, and candidate-slice band, then compared fixed-model log-loss marginals $\Delta_\ell(A\mid L)$ with operational or model-adjudicated utility marginals $\Delta_U(A\mid L)$.

| Stratum | P45 status | Bridge outcome | Allowed downstream label | Claim boundary |
|---|---|---|---|---|
| current `bio_attribute` stratum | implemented and closed | no stable utility-to-log-loss bridge; underpowered failed fit for the final bridge artifact | `operational_utility_only` or `ambiguous_metric` | no `calibrated_proxy_supported`, no `vinfo_proxy_supported`, no measurement validation |

This negative result is fail-closed claim-gate evidence, not bridge support. It shows that the measurement path and gate can withhold V-information-facing labels when the utility bridge fails. Future bridge work should use a materially new active stratum or a materially new fixed-logloss/utility design; it should not expand the same `bio_attribute` pilot by inertia.

Offline replay over realistic dispatch traces should come after this calibration step. Before replay, six choices must be fixed: model tier, utility metric, metric-claim regime, materialization ordering policy, decoding and variance-control policy, and candidate-slice policy. Replay records should include a `CounterfactualReplayWitness` with snapshot ID, frozen context state, item added or removed, continuation policy, evaluator model, replicate count, effective sample size, and metric-bridge status.

## 5. Extraction Quality as a Testable End-to-End Bottleneck

The theory and diagnostics optimize over the extracted candidate pool $M$. End-to-end performance depends on a richer upstream information space $M^*$ and on the extraction gate that maps free-form worker outputs, tool traces, and memory records into structured findings. Approximation or diagnostic statements over $M$ do not automatically transfer to $M^*$.

### 5.1 Extraction as bridge risk

A uniform extraction-completeness assumption would suggest approximately linear degradation: if the gate captures a fraction $c$ of useful findings uniformly across value levels, then the selector loses roughly proportional opportunity. The paper does not assume this. If extraction preferentially drops high-value, prerequisite, qualifier-heavy, or long-tail findings, degradation can be much worse than linear. Extraction is therefore treated as a measured bridge risk, not as another theorem layer.

### 5.2 Stratified audit protocol

The audit estimates completeness by stratum rather than collapsing extraction quality into one score. Let $s$ range over extraction-risk strata such as simple factual, complex conditional, qualifier-heavy, temporal-scope, cross-chunk, long-tail entity, high-provenance-value, prerequisite, contradictory, and adversarial findings. For each stratum,
\[
c_s=\Pr(\text{captured correctly}\mid s),
\qquad
c_{effective}=\sum_s p_s c_s.
\]
The value-weighted loss is
\[
L_{value}=\frac{\sum_j v_j\mathbf 1[\text{missing or materially distorted}]}{\sum_j v_j}.
\]

Each ground-truth finding is labeled as captured, captured with core preserved, captured with core materially changed, or missing. The audit also records lost qualifiers, temporal-scope errors, provenance loss, and selector impact.

### 5.3 Model-adjudicated and human-sentinel lanes

For scalable dataset construction, the default audit lane may use strong-model adjudication under frozen prompts. This supports `model_adjudicated_extraction_audit` evidence. It does not imply `measurement_validated`. A small human sentinel audit can estimate agreement and reveal systematic judge-model failures. Human labels plus inter-annotator agreement are required before upgrading the evidence tier to human-validated measurement.

The extraction section therefore reports three boundaries:

| Evidence | Allowed claim | Denied claim |
|---|---|---|
| model-adjudicated audit only | scalable extraction-risk evidence | human-validated measurement |
| model audit plus human sentinel | calibrated model-adjudicated evidence | full deployment validation |
| human labels plus agreement and fresh bridge | measurement-validation candidate | theorem transfer to $M^*$ |

This audit is separate from the set-selection theorem. If high-value extraction loss is large, the correct response is to improve the extraction gate or widen the candidate-generation layer, not to reinterpret the weak-submodular guarantee.

## 6. Runtime Interface Requirements for Verifiable Context Projection

### 6.1 Architecture overview

This section specifies the **minimum runtime observability requirements** needed to support the proxy-regime labeling protocol in Section 4. openWorker is the running instantiation, but the point of Section 6 is not merely to describe one system; it is to state what a runtime must expose if dispatch-time context projection is to be verifiable in practice. The selector studied here is a myopic control law embedded in a larger runtime, so the architectural burden is to make each dispatch round auditable rather than to solve whole-session control in one step.

In realistic deployments, the surrounding runtime manages higher-level concerns such as session state, task decomposition, tool execution, memory access, evaluation, correction, and long-term evolution. Existing runtimes already expose partial surfaces for context construction, but they do so heuristically and without a unified formal object. The contribution of the present paper is narrower and more formal: it specifies the context-projection layer that sits immediately before worker dispatch, together with the artifacts and state summaries needed to monitor that layer across rounds.

The ProjectionPlan / BudgetWitness / MaterializedContext / MetricBridgeWitness chain is the minimal auditable interface for one-shot projection. Two optional witnesses extend it for experiments and adaptive runtime control: CounterfactualReplayWitness records replay evaluations, and ReprojectionWitness records uncertainty-triggered context expansion or selector escalation.

### 6.1.1 Layering assumption

We model the runtime as four cooperating layers:

1. **Scheduler:** decides the dispatch event $(t,i,q_i,R_i,V_i,B_i)$.
2. **Context-projection layer:** selects $S_i \subseteq M$ under budget $B_i$.
3. **Execution layer:** runs the worker, tools, and model inference.
4. **Verification and observability layer:** audits outputs, records artifacts, records metric-bridge state, and updates runtime state summaries.

This paper specifies the second layer and the audit surface required by the fourth. The scheduler and execution layers are assumed to exist but are not optimized here.

### 6.1.2 Scheduler–selector interface

The selector is not an autonomous scheduler; it consumes a dispatch event and reports auditable outputs back to the surrounding runtime.

| Direction | Signal | Meaning |
|---|---|---|
| Scheduler → Selector | $(t,i,q_i,R_i,V_i,B_i)$ | dispatch event |
| Scheduler → Selector | admission policy | which candidates may enter $M$ |
| Scheduler → Selector | synchronization mode | blocking, parallel, retry, abort context |
| Scheduler → Selector | persistence policy by state category | which state types survive turn boundaries or tool boundaries |
| Selector → Scheduler | ProjectionPlan | selected / excluded context items |
| Selector → Scheduler | BudgetWitness | realized token use and trims |
| Selector → Scheduler | MaterializedContext | realized token sequence and manifest |
| Selector → Scheduler | MetricBridgeWitness | calibration epoch, active stratum, bridge residual, drift status, claim level |
| Selector → Scheduler | CounterfactualReplayWitness | frozen replay state, intervention, evaluator, replicates, effective sample size |
| Selector → Scheduler | ReprojectionWitness | uncertainty trigger, budget delta, context diff, selector change, before/after output |
| Selector → Scheduler | $\widehat{\gamma}^{op,LCB}_{b,q}$, TraceDecay, pairwise excess, SAG gap | selector diagnostics |
| Selector → Scheduler | $(\texttt{metric\_claim\_level},\texttt{selector\_regime\_label})$ | two-axis decision label |

### 6.2 Projection, replay, and re-projection artifacts

A runtime that supports verification should reify context projection into machine-readable audit artifacts. Their primary purpose is replay, proxy evaluation, trace comparison, and structured downstream audit.

**ProjectionPlan.** This is the selection-side interface. At minimum it should record: the candidate set considered for the round, the selected candidates, the excluded candidates, per-category budgets or quotas if used, and the scoring configuration that produced the ranking (for example embedding model, reranker model, and MMR parameters). The goal is to make the selector's decision surface inspectable rather than implicit.

**BudgetWitness.** This is the budget-side interface. At minimum it should record: estimated versus realized token counts, section-level trims, exclusion logs for dropped content, tolerance violations, and any cost or overflow bookkeeping used to keep the dispatch within budget. When diagnostics are computed on the realized selection, the witness records which selected set and token budget the diagnostics apply to.

**MaterializedContext.** This is the realization-side interface. It should record the actual token sequence sent to the worker together with a structural manifest of section ordering, section boundaries, and content inventory. This manifest fixes the ordering used by proxy evaluations and provides the realized payload against which provenance, traceability, and position-sensitive effects can be audited. KV-cache reuse is not part of the formal objective. It matters operationally because the realized token sequence, ordering, and reusable static prefixes determine both the actual budget witness and the materialization policy under which proxy evaluations are replayed.

**MetricBridgeWitness.** This is the measurement-side interface. It prevents the runtime from silently reporting V-information proxy labels under an uncalibrated or stale production metric. At minimum it should record:

| Field | Required content |
|---|---|
| calibration epoch | epoch identifier $e$ |
| active stratum | $s=(\text{task family},\text{model tier},\text{metric},\text{block size},\text{candidate-slice band},\text{materialization policy})$ for the current dispatch |
| model tier | deployed/evaluated model |
| utility metric | log-loss, decomposable score, pass/fail, rubric, human preference, etc. |
| metric class | log-loss aligned / bridge-calibrated / operational-only |
| materialization policy | ordering and formatting used during replay |
| decoding policy | temperature, seeds, replicate count |
| bridge scale | $c_s$ |
| bridge residual | $\zeta_s$ |
| effective sample size | after weighting or filtering |
| drift status | fresh / stale / ambiguous |
| diagnostic mode | absolute / fractional-active / fractional-inactive |
| diagnostic claim level | V-information proxy / calibrated proxy / operational utility only |

A calibration epoch can contain multiple strata with different $\zeta_s$ values. The active-stratum field is therefore mandatory: without it, the witness records that some bridge calibration exists, but not that the current dispatch inherits the correct one.

The offline audit scaffold extends this artifact chain into a compact evidence surface. These artifacts make replay and manuscript review possible, but they remain audit interfaces rather than scientific validation.

| Artifact | Role | Audit / replay relevance | Claim boundary |
|---|---|---|---|
| `ProjectionPlan` | selection decision record | exposes selected, excluded, and considered candidates | audit interface only |
| `BudgetWitness` | token-budget witness | fixes estimated and realized context costs | audit interface only |
| `MaterializedContext` | realized context payload | fixes ordering and context inventory for replay | audit interface only |
| `MetricBridgeWitness` | measurement-claim witness | records metric class, freshness, and diagnostic scope | claim-level gate, not validation by itself |
| `CounterfactualReplayWitness` | replay witness | records frozen state, intervention, evaluator, and replicates | proxy evidence only |
| `ReprojectionWitness` | adaptive runtime witness | records uncertainty trigger, context expansion, selector change, and before/after output | operational evidence only unless separately calibrated |
| `ProjectionBundleV1` | canonical bundle | ties plan, budget, context, bridge witness, replay witness, and diagnostics with stable hashes | replay evidence only |

**Companion implementation.** The `mingx` companion implementation instantiates this interface as an evidence-production scaffold. It emits append-only event traces, candidate pools, ProjectionPlans, BudgetWitnesses, MaterializedContexts, MetricBridgeWitnesses, diagnostics, summaries, and paper-facing reports, and it includes claim-gate logic that prevents engineering runs, synthetic-only runs, or stale-bridge runs from being reported as measurement validation. The implementation is used as executable support for replay and artifact inspection, not as a source of scientific validation by itself. In particular, implementation completeness may support `replayable_artifact_evidence` or `engineering_smoke_only`, but it does not upgrade a result to `measurement_validated` without the required metric bridge, contamination closure, and human-label evidence.

### 6.3 Three-stage scoring pipeline

The pipeline is a heuristic approximation to the selection framework in Section 2.2, not a faithful optimizer of the V-information objective.

**Stage 1 — Retrieval + RRF signal fusion.** Bi-encoder cosine similarity, recency decay, and metadata signals fused via Reciprocal Rank Fusion. Approximates a singleton relevance score.

**Stage 2 — Cross-encoder reranking.** Joint (task, finding) scoring capturing token-level interactions. Refines singleton relevance but still does not evaluate set composition.

**Stage 3 — MMR diversity selection + greedy knapsack.** Maximal Marginal Relevance penalizes redundancy with already-selected items. Its similarity-based penalty on already-selected items is heuristically aligned with the diminishing-returns intuition of Condition B within topic clusters. The efficiency ratio `mmr_score / tokens(m)` operationalizes a density-based greedy packing heuristic. The pipeline is a heuristic approximation of greedy set-function maximization, not a faithful optimizer of the V-information objective; the protocol in Section 4 monitors whether this heuristic remains sufficiently aligned with the calibrated proxy regime and triggers escalation when the pipeline-versus-proxy gap exceeds calibrated tolerance.

### 6.4 Observation-mediated communication and memory governance

Workers communicate exclusively through structured ObservationPacks — the extraction gate's output. ObservationPacks carry findings, decisions, artifacts, confidence assessments, and provenance metadata. In this paper, memory is treated as an upstream persistence and candidate-generation layer, not as the primary object of formal analysis; richer episodic, semantic, and procedural memory architectures remain outside the theorem's scope. Memory governance is included here only because memory can affect the candidate pool $M$.

At minimum, long-lived memory should be **typed** into categories such as `user`, `feedback`, `project`, and `reference`, because these classes differ in update frequency, contradiction risk, and downstream use. Memory should also be governed by two operational rules. First, **memory is not the source of truth**: a memory hit that says a file, function, flag, or tool capability exists should be treated as a candidate lead, not as a currently verified fact. Second, memory retrieval should be **selective rather than saturating**: reads should return a candidate subset chosen by relevance, freshness, provenance quality, and contradiction risk, rather than injecting the entire store into the working context.

From a verification standpoint, the runtime should expose not only the projected artifacts in Section 6.2, but also the **trace interfaces** that explain how those artifacts were produced. At minimum, this includes: the provenance chain from upstream evidence to finding, the side effects of subagents or tools that generated candidate findings, memory read/write/update traces that determine what was available at dispatch time, and extraction-gate outputs that map free-form upstream material into the structured candidate pool.

Three design principles follow. **Dual-gate admission** should separate what enters memory from what is eligible for downstream projection. **Provenance-before-scoring** should ensure that findings are verified before they are ranked or packed. **Verification-before-persistence** should ensure that persistence and downstream reuse happen over data that has already passed schema and provenance checks.

### 6.5 Runtime state summaries

To support cross-round stability without breaking the per-round formal core, a runtime should maintain lightweight **dispatch-relevant state summaries** rather than a fully optimized session-level control state. These summaries serve as event-triggered control signals for subsequent rounds.

**Task state.** Goals, subtasks, blockers, and current stage of the session-level goal tree.

**Candidate state.** The current dispatch snapshot $M$, together with coarse statistics such as candidate-pool size, top-$L$ score distribution, and observed redundancy/synergy signals.

**Memory state.** Typed memory summaries, freshness indicators, provenance quality, and contradiction-risk markers for memory items that may enter future candidate pools.

**Quality state.** Recent values of $\widehat{\gamma}^{op,LCB}_{b,q}$, TraceDecay, synergy fraction, augmented-greedy gap, metric-claim level, extraction risk, and proxy-alignment signals used by the monitoring and escalation logic. Quality state is consumed by the scheduler as a read-only control signal: the context-projection layer reports regime health, but it does not decide whether to spawn more agents, change the synchronization policy, or terminate the session.

These summaries do not redefine the theorem-level object. They are a runtime shell around the dispatch-time selector, enabling subsequent rounds to react to prior diagnostics without collapsing the paper into a whole-session scheduling theory.

### 6.6 Dispatch flow

The following flow is not an architectural prescription. It is a traceability requirement: each step identifies a boundary at which information may be filtered, distorted, truncated, persisted, or re-labeled, and therefore must be auditable if the Section 4 diagnostics are to be meaningful.

The dispatch cycle in a verifiable runtime follows an eight-step flow:

1. **Planner / Memory produce raw observations.** Session-level planning, tool use, and memory retrieval expose raw materials relevant to the next worker dispatch.
2. **Extraction gate filters into structured findings.** Free-form upstream outputs are converted into machine-auditable findings and screened by the dual-gate admission policy.
3. **Candidate pool $M$ is assembled.** The dispatch snapshot is formed from the currently admissible findings.
4. **Selector pipeline ranks and packs findings.** Retrieval fusion, reranking, diversity control, and budgeted packing produce a proposed selection.
5. **Artifacts are reified.** The runtime records a ProjectionPlan, BudgetWitness, MaterializedContext, and MetricBridgeWitness for the dispatch, and records CounterfactualReplayWitness or ReprojectionWitness artifacts when replay or adaptive re-projection occurs.
6. **Worker executes the task.** The selected context is sent to the worker agent together with its task instructions and tool interface.
7. **Evaluator computes diagnostics.** Post-dispatch replay and proxy measurements estimate block-ratio health, interaction mass, pipeline-versus-proxy mismatch, metric-bridge status, and extraction risk.
8. **Planner updates state summaries for the next round.** The resulting signals are written back into the runtime state shell, where they influence subsequent dispatch decisions.

## 7. Related Work

The closest prior art differs from our setting along three axes. First, many systems optimize the wrong **granularity**: agents, links, or memory-routing decisions rather than per-agent context units. Second, many works use the wrong **budget object**: cardinality, dropout rates, compression ratios, or whole-system cost caps rather than per-agent token budgets at per-round dispatch time. Third, many works lack the relevant **guarantee structure**: they provide heuristics, learned policies, or empirical improvements without a formal value function over context subsets and without a bridge statement separating theorem, proxy, and runtime layers. We organize the discussion below around these axes.

### 7.1 Single-agent budgeted context selection

Recent work on context selection has begun to treat prompt assembly as an explicit optimization problem, but almost always for a **single predictive target under a single global budget**. Peng et al. (2025) provide a (1 − 1/e − ε') greedy approximation under ε-approximate submodularity for RAG context selection, using a modular-minus-supermodular objective to model redundancy. InSQuaD (Nanda et al., 2025) applies Submodular Mutual Information to exemplar selection for in-context learning, showing that submodular information objectives can improve retrieval quality for a single downstream model. Sub-CP (Zheng et al., 2025) studies budgeted context partitioning for block-wise in-context learning, again with a single target model and a single total context budget. These papers are the closest single-agent antecedents to our setting, but they do not address heterogeneous per-agent routing of content items across multiple downstream agents.

Wang et al. (2026) provide a complementary mechanistic account of when context helps in single-context Transformers. Their framework operates in output-vector space rather than information-theoretic quantities, and their selection strategy scores items independently rather than reasoning over set composition. We use their results as mechanistic support for pairwise interaction structure, not as a formal solution to the multi-agent content-selection problem.

### 7.2 Multi-agent submodular optimization with different selection variables

The closest multi-agent formal work optimizes **different decision variables** from the one studied here. IMAS² (Shi et al., 2025) selects subsets of sensing agents by maximizing mutual information under conditional independence; it is the nearest true submodular multi-agent guarantee we found, but its objects are agents and trajectories in a Dec-POMDP, not LLM context units. Anaconda (Xu & Tzoumas, 2024) selects communication neighborhoods or links under per-agent resource constraints to preserve decentralized coordination quality. More broadly, multi-agent submodular optimization has studied exclusive allocation or coordination constraints over agents, tasks, or channels (for example Santiago & Shepherd, 2018), whereas our non-exclusive architecture allows the same finding to be projected to multiple agents and therefore reduces the per-round problem to independent per-agent content selection. The mismatch is therefore one of both **granularity** and **budget**: prior multi-agent work typically optimizes agents, links, or channels under coordination or cardinality-style constraints, whereas we optimize content units under explicit per-agent token budgets.

This distinction in **selection variable** is central to our positioning. We do not optimize which agents to activate, which neighbors to communicate with, or which shared channel to open. We optimize which **content items** each agent should receive under its own token budget. DyLAN selects agents; AgentDropout, AgentPrune, and GPTSwarm-style graph methods select communication edges; IMAS² selects sensing agents; Anaconda selects communication neighborhoods. None selects content units within a specific agent's token budget at a specific dispatch round. Query-specific, per-agent content allocation under heterogeneous token budgets is therefore adjacent to, but not the same as, prior multi-agent submodular optimization.

A minimal instance shows why the distinction is representational rather than cosmetic. The true per-agent formulation uses variables $z_{i,m}\in\{0,1\}$ and constraints $\sum_m c_m z_{i,m}\le B_i$. A unique-item single-budget reduction uses variables $x_m\in\{0,1\}$ and the map $x_m=\bigvee_i z_{i,m}$, which forgets projection multiplicity.

**One shared item.** Let two agents $A_1,A_2$ each have budget 1, and let a single item $s$ have cost $c(s)=1$ and value 1 for each agent.

| Agent | Budget | Value of $s$ |
|---|---:|---:|
| $A_1$ | 1 | 1 |
| $A_2$ | 1 | 1 |

The per-agent projection solution sends $s$ to both agents and achieves value 2. A unique-item single-budget reduction has only one variable $x_s$. If it counts $s$ once, it achieves value 1 and loses a factor of $1/2$ despite the matched total token budget. If it counts $s$ twice while paying cost once, it undercounts projection cost.

**Two shared items.** Now let two items $s,t$ each have cost 1 and value 1 for both agents, with the same two unit budgets.

| Agent | Budget | Value of $s$ | Value of $t$ |
|---|---:|---:|---:|
| $A_1$ | 1 | 1 | 1 |
| $A_2$ | 1 | 1 | 1 |

A unique-item global-budget formulation with total budget 2 can select $\{s,t\}$ and claim value 4 if it counts value for both agents. But no feasible per-agent projection realizes value 4, because each agent can receive only one item; the true per-agent optimum is 2. To repair the reduction, one must introduce agent-indexed variables or copies, which is exactly the selection variable used in this paper.

More distantly, the economic literature on combinatorial auctions had already studied valuation classes with decreasing marginal utilities and limited complementarity well before the current weak-submodularity vocabulary; see, for example, Lehmann, Lehmann, and Nisan (2006) for a greedy approximation perspective under decreasing-marginal-utility valuations. We use this lineage only as historical positioning for bounded-complementarity structure, not as a diagnostic precedent.

### 7.3 Proxy-valued, calibrated, and learned routing or memory systems

A second adjacent line of work studies practical context routing, memory selection, or proxy-valued context evaluation without turning these ingredients into an explicit bridge statement between theorem, proxy, and deployment. Contextual Influence (CI) Value (Deng et al., 2025) is the closest antecedent on the proxy side: it reframes context assessment as inference-time data valuation and uses leave-one-out utility change as a practical marginal-value signal. But CI Value does not itself specify a formal value object with provable set-function properties, does not state equivalence conditions under which the proxy matches that formal object, and does not characterize how a deployed scoring pipeline may diverge from the proxy.

RCR-Router (Liu et al., 2025) is the closest antecedent on the routing side. It proposes a practical role-aware context-routing framework under token budgets, together with a lightweight scoring policy and output-aware evaluation. This makes it a strong systems-side neighbor, but not a bridge statement in our sense: it does not explicitly separate formal objective, proxy measurement layer, and heuristic runtime layer, nor does it specify conditions under which any theorem-level reasoning would or would not transfer to deployed routing behavior.

Recent RAG selection work is closer in decision variable but still differs in bridge rigor. AdaGReS (Peng et al., 2025) introduces an instance-adaptive calibration of the relevance-redundancy trade-off parameter so that the resulting objective remains near a favorable approximate-submodularity regime. This is an important adjacent precedent for **formal objective + structural condition + calibration** in token-budgeted context selection. But AdaGReS does not separately name a proxy layer, does not analyze a heuristic pipeline that may only correlate with the proxy, and does not turn bridge failure into a first-class deployment claim. The same distinction applies to context-partitioning systems such as Sub-CP (Zheng et al., 2025): they rely on submodular or approximately submodular design choices, but do not monitor the selector's regime online or in replay.

A different adjacency comes from learned routing and memory-admission systems. BudgetMem (Zhang et al., 2026), LatentMem (Fu et al., 2026), and Learning to Share (Fioresi et al., 2026) optimize memory routing or sharing policies by learned or reinforcement-style procedures and evaluate them empirically through performance-cost trade-offs. These systems are relevant because they explicitly inhabit the deployed pipeline layer. But they generally do not define a formal objective with provable structural properties, do not specify a theoretically justified proxy layer with stated equivalence conditions, and do not separate policy-learning success from theorem transfer. Other nearby systems miss at a different level of granularity: graph-pruning or agent-importance approaches reduce token cost by acting on communication edges or agents rather than on the context units sent to a specific worker.

The closest published analogue to our target object is DACS (Patel, 2026), whose registry/focus pattern introduces a candidate-like set of agent contexts, a budget-like cap on registry summaries, and a trigger for temporarily restoring one agent's full context. DACS is therefore important evidence that the missing layer is real. But it still operates at agent-block granularity, lacks a learned or formal value function over context units, and offers no approximation or verification guarantee for per-agent token-budgeted projection.

A further adjacency comes from recent LLM diagnostic frameworks. Yuan, Su, and Yao (2026) propose a three-probe framework for memory-augmented LLM agents that diagnoses retrieval relevance, utilization, and failure modes. Gupta et al. (2025) propose Information Gain per Turn and Token Waste Ratio as information-theoretic diagnostics for multi-turn LLM conversations, including discussion of handoff or escalation under sustained low information gain. These are important contemporaneous precedents, but they operate at different epistemic layers: Yuan et al. diagnose **pipeline bottlenecks**, and Gupta et al. diagnose **dialogue-channel information flow**. By contrast, our protocol diagnoses **selector structure** and then asks how that structural diagnosis should and should not transfer through the proxy and pipeline layers. More broadly, these runtime-oriented works motivate viewing modern agent systems as layered runtimes with distinct planning, memory, evaluation, and execution roles, within which dispatch-time context projection can be isolated as a separable control problem.

Finally, PID- and interaction-information-based feature-selection work provides methodological context for our pairwise interaction diagnostic. Wollstadt, Schmitt, and Wibral (2023) use a PID-informed information-theoretic framework to distinguish redundancy and synergy in feature selection. This is a useful antecedent for the instrument level of Diagnostic 2, but not a deployment-facing bridge statement or escalation framework for token-budgeted context selection. In adjacent Shannon information-gain settings, the connection can be taken one step further: Hübotter, Sukhija, Treven, As, and Krause (2024) relate redundancy-versus-synergy structure to a weak-submodularity parameter for active-learning objectives and thereby provide the closest formal antecedent to the present discussion. We nevertheless treat that result as adjacent rather than directly transferable, because our formal object is predictive V-information and our deployed diagnostics are defined at the proxy and pipeline layers rather than as direct evaluations of the Shannon-information objective.

Taken together, the prior literature covers proxy-valued context scoring, formal objective plus calibration, routing and memory systems, learned policies, and adjacent diagnostic frameworks. We are not aware of prior work in LLM context selection or routing that simultaneously **(i)** makes an explicit three-layer separation between formal objective, proxy measurement, and heuristic pipeline, **(ii)** states the conditions under which the theorem-level story does or does not transfer across those layers, and **(iii)** treats the pipeline-versus-proxy gap as a first-class object of verification and escalation.

### 7.4 Structured extraction and faithfulness

The most relevant adjacent literature falls into three groups. First, orthogonal structured-action benchmarks such as BFCL (Patil et al., 2025) and ToolBench (Qin et al., 2023) evaluate function-call correctness and API-chain execution rather than free-form-to-structured extraction completeness. Second, structured-output benchmarks such as SLOT (Shen et al., 2025) and KIEval (Khang et al., 2025) improve schema-accuracy evaluation, content-fidelity evaluation, and application-centric correction-oriented evaluation, but they do not report separate completeness rates for simple versus complex findings as a diagnostic test of uniformity. Third, adjacent faithfulness work — including Peters and Chin-Yee (2025) on overgeneralization, CRANE (Banerjee et al., ICML 2025) on constrained-generation limits, FABLES (Kim et al., COLM 2024) on long-form faithfulness failures, and FActScore (Min et al., EMNLP 2023) on atomic-fact factuality — supports the broader concern that qualification-heavy, reasoning-intensive, or indirectly supported content is especially vulnerable during reformulation.

Taken together, these literatures establish value-weighted evaluation, fine-grained factuality analysis, and structured-output benchmarking as important adjacent traditions. To our knowledge, however, prior work does not audit **free-form-to-structured extraction** by reporting separate per-stratum completeness rates in order to test whether high-value or complex findings are disproportionately lost during reformulation — the gap our evaluation protocol addresses.

Across the adjacent literatures surveyed in this section — single-agent budgeted selection, multi-agent optimization over agents or links, learned proxy-level routing or memory systems, and adjacent diagnostic and extraction-evaluation frameworks — the same pattern emerges. Our contribution lies at their intersection: a formal value function for **per-agent content selection** under heterogeneous token budgets, conditional structural theory for that formal object, an explicit bridge statement separating theorem, proxy, and runtime layers, and a measurable proxy-regime labeling protocol for deciding when monitored greedy-style selection is credible.

The gap is therefore not the absence of multi-agent scheduling mechanisms, but the absence of a formal context-allocation object inside those mechanisms. The reviewer-facing contribution is this narrower measurement protocol: a formal per-agent content-selection object, explicit bridge conditions, and auditable claim boundaries for proxy-regime diagnostics.

---

## 8. Discussion and Future Work

The paper's main open problem is still objective-level: characterize when predictive V-information over natural-language context items is approximately submodular or weakly submodular for restricted model families. The current theorem supplies a pairwise-regime bound, not a proof of Condition A.

The current `bio_attribute` bridge lane has been executed and closed as non-calibrated. The synthetic benchmark in Section 4.6 is a structural smoke test, and the P45 negative closure shows that the current utility-to-log-loss bridge did not pass for the tested stratum. Future bridge work therefore requires either a materially new stratum or a materially new fixed-logloss/utility design, rather than scaling the same `bio_attribute` pilot by inertia.

The second empirical step is offline replay on real dispatch traces. Realistic replay must test whether the same labels predict selector behavior under actual task distributions, materialization policies, and judge metrics, while preserving the metric-claim boundary recorded by the MetricBridgeWitness.

A third direction is adaptive runtime control. Post-dispatch uncertainty labels can trigger re-projection, larger budgets, stronger selectors, model-tier escalation, or hierarchical adjudication. This connects the dispatch-time selector studied here to token-level adaptive context-allocation systems without changing the formal decision variable.

A fourth direction is provenance-aware redundancy. Duplicate redundancy, corroborative redundancy, adversarial redundancy, and prerequisite overlap should not be treated identically. Future selectors should penalize duplicate waste while preserving independent corroboration and high-provenance corrective evidence.

Finally, extraction quality needs direct measurement. Model-adjudicated audits can scale benchmark construction, but human sentinel audits are needed to estimate model-label bias and support stronger measurement claims.

## 9. Limitations

First, the theory concerns $f_i^{\mathcal V}$, while most diagnostics estimate $f_i^{\theta,\ell}$ or $f_i^U$. Without a fresh predictor-optimality or utility-to-log-loss bridge, V-information proxy claims must be downgraded.

Second, Theorem 1 is a pairwise-regime result. Condition C' is a global structural assumption; the diagnostics test observable consequences of that assumption but cannot verify it uniformly.

Third, the formal problem is token-budgeted. Cardinality-style weak-submodular approximation language is used only as intuition unless a separate knapsack-specific analysis is supplied for the deployed selector.

Fourth, the synthetic benchmark is small and oracle-level. It supports structural smoke-test evidence, not deployment validation, human measurement validation, or proof of Condition A.

Fifth, model-adjudicated labels are scalable but not ground truth. Prompt versioning, order reversal, duplicate judging, and human sentinel checks are required before stronger measurement claims are appropriate.

Sixth, extraction quality is a separate $M^*\to M$ bottleneck. If the extraction gate drops high-value or prerequisite findings, optimization over $M$ can look healthy while end-to-end performance fails.

Seventh, the per-round decomposition assumes non-exclusive allocation and fixed scheduler decisions. It does not analyze long-horizon scheduler feedback, future candidate-pool shaping, or cross-agent output redundancy.

Eighth, the runtime artifacts presume observability that some hosted systems may not expose. Without excluded candidates, materialization order, calibration state, and replay-compatible traces, the protocol can guide design but cannot support strong diagnostic claims.

Ninth, companion implementation runs are not automatically evidence upgrades. A reduced-scope run that completes engineering execution but lacks contamination closure, fresh bridge evidence, or human-label agreement must remain `pilot_only` or `engineering_smoke_only`. This is intended claim-gate behavior rather than a failure of the framework: runtime success alone is insufficient for measurement validation.

Tenth, the paper does not claim multi-agent superiority over single-agent systems. It studies the context-allocation sub-layer that arises when an orchestrator-worker runtime is already being used.

## 10. Broader Impact

Improved context assembly can reduce computational waste from redundant or irrelevant context in multi-agent LLM systems — the 53–86% token duplication measured by AgentTaxo represents significant wasted inference cost. The revised protocol is intentionally conservative: it distinguishes V-information proxy labels from operational-utility-only labels, records metric-bridge status, and requires ambiguity when bridge, cascade, or sample evidence is insufficient.

The main risk is false confidence. Formal guarantees over the V-information objective do not automatically transfer to heuristic pipelines, production metrics, or biased candidate pools. The MetricBridgeWitness, block-ratio LCB, extraction audit, and pre-registered synthetic benchmark validity gate are designed to make such gaps visible rather than to eliminate them. Practitioners should verify proxy alignment before relying on any diagnostic for operational decisions.

---

## 11. Conclusion

We formalized dispatch-time context projection as per-agent, token-budgeted content selection under a predictive V-information objective. The theoretical contribution is conditional: $\gamma$ and $d$ are independent for general monotone set functions, and under pairwise-additive absolute complementarity a local block-ratio lower bound follows from singleton mass, degree, and interaction strength. The fractional $1/(1+d\delta)$ form is valid only in active contexts.

The deployment contribution is a claim-gated diagnostic framework, not deployed V-information verification. The paper separates formal V-information value, fixed-model log-loss, operational utility, heuristic selector pipelines, metric-claim levels, runtime artifacts, and extraction risk. The resulting protocol conservatively labels selector regimes as `greedy_supported`, `pairwise_escalate`, `higher_order_risk`, or `ambiguous`.

A small oracle synthetic benchmark provides initial structural evidence that the diagnostic policy separates redundancy, pairwise synergy, and higher-order prerequisite regimes without issuing false `greedy_supported` labels on higher-order cases. The P45 bridge lane has also produced a fail-closed negative result for the current non-calibrated `bio_attribute` stratum. The remaining bridge work is empirical but no longer entirely unexecuted: it requires a materially new stratum or materially new fixed-logloss/utility design, alongside model-adjudicated realistic-task benchmarks, offline replay on real dispatch traces, human sentinel audits, and value-stratified extraction measurement.

## References

Anthropic (2025). Effective Context Engineering for AI Agents. Anthropic Engineering blog.

Bai & Bilmes (2018). Greed is Still Good: Maximizing Monotone Submodular+Supermodular Functions. ICML.

Banerjee et al. (2025). CRANE: Reasoning with Constrained LLM Generation. ICML.

Bian, Buhmann, Krause & Tschiatschek (2017). Guarantees for Greedy Maximization of Non-submodular Functions with Applications. ICML.

Chase (2025). The Rise of Context Engineering. LangChain Blog.

Das & Kempe (2018). Submodular meets Spectral: Greedy Algorithms for Subset Selection, Sparse Approximation and Dictionary Selection. JMLR 19(1).

Deng, Shen, Pei, Chen & Huang (2025). Influence Guided Context Selection for Effective Retrieval-Augmented Generation. NeurIPS 2025 poster / OpenReview.

Elenberg, Khanna, Dimakis & Negahban (2018). Restricted Strong Convexity Implies Weak Submodularity. Annals of Statistics 46(6B), 3539–3568.

Reddy, Walker, Ide & Bedi (2026). Draft-Conditioned Constrained Decoding for Structured Generation in LLMs. arXiv:2603.03305.

Feige & Izsak (2013). Welfare Maximization and the Supermodular Degree. ITCS.

Feldman & Izsak (2014). Constrained Monotone Function Maximization and the Supermodular Degree. APPROX.

Fioresi et al. (2026). Learning to Share: Multi-Agent Shared Memory via Reinforcement Learning. arXiv.

Fu, Zhang, Xue, Li, He, Huang, Qu, Cheng & Yang (2026). LatentMem: Customizing Latent Memory for Multi-Agent Systems. arXiv:2602.03036.

Min et al. (2023). FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation. EMNLP.

Nenkova & Passonneau (2004). Evaluating Content Selection in Summarization: The Pyramid Method. HLT-NAACL 2004.

Patel (2026). Dynamic Attentional Context Scoping: Agent-Triggered Focus Sessions for Isolated Per-Agent Steering in Multi-Agent LLM Orchestration. arXiv:2604.07911.

Patil et al. (2025). The Berkeley Function-Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models. PMLR 267.

Qin et al. (2023). ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs. arXiv.

Khang, Jung, Park & Hong (2025). KIEval: Evaluation Metric for Document Key Information Extraction. arXiv.

Gupta, Gorle, Yadav & Weissman (2025). Quantifying Information Gain and Redundancy in Multi-Turn LLM Conversations. MTI-LLM @ NeurIPS 2025 Workshop (OpenReview).

Doddington, Mitchell, Przybocki, Ramshaw, Strassel & Weischedel (2004). The Automatic Content Extraction (ACE) Program - Tasks, Data, and Evaluation. LREC 2004.

Harshaw, Feldman, Ward & Karbasi (2019). Submodular Maximization beyond Non-negativity: Guarantees, Fast Algorithms, and Applications. ICML.

Hübotter, Sukhija, Treven, As & Krause (2024). Transductive Active Learning: Theory and Applications. NeurIPS 2024.

Peng, Wang, Long & Sheng (2025). AdaGReS: Adaptive Greedy Context Selection via Redundancy-Aware Scoring for Token-Budgeted RAG. arXiv.

Kim et al. (2024). FABLES: Evaluating Faithfulness and Content Selection in Book-Length Summarization. COLM.

Lehmann, Lehmann & Nisan (2006). Combinatorial Auctions with Decreasing Marginal Utilities. Games and Economic Behavior 55(2), 270–296.

Krause & Guestrin (2005). Near-optimal Nonmyopic Value of Information in Graphical Models. ICML.

Liu et al. (2024). Lost in the Middle: How Language Models Use Long Contexts. TACL.

Liu et al. (2025). RCR-Router: Efficient Role-Aware Context Routing for Multi-Agent LLM Systems with Structured Memory. arXiv:2508.04903.

METR (2025a). Measuring AI Ability to Complete Long Tasks. METR research report.

Nanda et al. (2025). InSQuaD: Submodular Mutual Information for In-Context Learning Exemplar Selection. EMNLP 2025 Findings.

Peters & Chin-Yee (2025). Generalization Bias in Large Language Model Summarization of Scientific Research. Royal Society Open Science 12(4):241776.

Santiago & Yoshida (2020). Weakly Submodular Function Maximization Using Local Submodularity Ratio. ISAAC 2020.

Rezazadeh et al. (2025). Collaborative Memory for Multi-Agent Systems. arXiv.

Santiago & Shepherd (2018). Multi-Agent Submodular Optimization. APPROX.

Shi, Suttle, Dorothy & Fu (2025). IMAS²: Joint Agent Selection and Information-Theoretic Coordinated Perception in Dec-POMDPs. arXiv:2510.20009.

Shen, Wang, Mishra et al. (2025). SLOT: Structuring the Output of Large Language Models. EMNLP 2025 Industry Track.

Welikala, Cassandras, Lin & Antsaklis (2022). A New Performance Bound for Submodular Maximization Problems and its Application to Multi-Agent Optimal Coverage Problems. Automatica 144, 110493.

Wollstadt, Schmitt & Wibral (2023). A Rigorous Information-Theoretic Definition of Redundancy and Relevancy in Feature Selection Based on (Partial) Information Decomposition. JMLR 24(131).

Xu & Tzoumas (2024). Performance-Aware Self-Configurable Multi-Agent Networks: A Distributed Submodular Approach for Simultaneous Coordination and Network Design. CDC.

Xu, Pang, Shen & Cheng (2025). A Theory for Token-Level Harmonization in Retrieval-Augmented Generation. ICLR 2025.

Trivedi et al. (2022). MuSiQue: Multihop Questions via Single-hop Question Composition. TACL.

Wang et al. (2025a). AgentTaxo: Taxonomizing Redundancy in Multi-Agent Systems. ICLR 2025 Workshop on Foundation Models in the Wild.

Wang et al. (2025b). AgentDropout: Dynamic Agent Elimination for Token-Efficient Multi-Agent Communication. ACL.

Wang, D. et al. (2026). When Does Context Help? Error Dynamics of Contextual Information in Large Language Models. arXiv:2602.08294.

Williams & Beer (2010). Nonnegative Decomposition of Multivariate Information. arXiv:1004.2515.

Wu et al. (2024). Evaluating LLMs' Inherent Multi-hop Reasoning Ability. arXiv:2402.11924.

Xu, Zhao, Song, Stewart & Ermon (2020). A Theory of Usable Information under Computational Constraints. ICLR.

Yuan, Su & Yao (2026). Diagnosing Retrieval vs. Utilization Bottlenecks in LLM Agent Memory. arXiv:2603.02473.

Yuen et al. (2025). Intrinsic Memory Agents: Heterogeneous Context for Multi-Agent Systems. arXiv.

Yu & Chai (2025). EvolKV: Evolutionary KV Cache Budget Allocation for Efficient LLM Inference. EMNLP Findings. arXiv:2509.08315.

Zheng, Zhang, Kumari, Zhou & Wang (2025). Submodular Context Partitioning and Compression for In-Context Learning. arXiv.

Zhang et al. (2025). G-Memory: Hierarchical Memory Architecture for Multi-Agent Systems. NeurIPS Spotlight.

Zhang et al. (2026). Learning Query-Aware Budget-Tier Routing for Runtime Agent Memory. arXiv:2602.06025.

---

## Appendix A: Proof of Proposition 2 (Independence of γ and d)

Two constructions fill opposite cells of the (γ, d) matrix.

*Construction 1 (d = 1, γ → 0).* Let V = {a, b, c₁, ..., cₙ} and define f(S) = |S ∩ {c₁,...,cₙ}| + 𝟙[a ∈ S] + 𝟙[b ∈ S] + (M − 2)·𝟙[{a,b} ⊆ S] for M >> 1. Only a and b have a supermodular interaction, so d = 1. But taking S = {a, b} and L = ∅: γ ≤ [Δf(a | ∅) + Δf(b | ∅)] / Δf({a,b} | ∅) = 2/M → 0 as M → ∞.

*Construction 2 (d = n − 1, γ → 1).* Let V = {1, ..., n} and define f(S) = Σᵢ∈S wᵢ + ε · C(|S|, 2) for wᵢ ≥ 1 and ε > 0 small. Every pair interacts supermodularly, so d = n − 1. For any S of size s: γ ≥ Σᵢ wᵢ / (Σᵢ wᵢ + ε · C(s, 2)) → 1 as ε → 0. This construction is the combinatorial-degree analogue of the tightness example in Bai and Bilmes (2018) Section J.1, which exhibits κ^g = 1 with γ ≈ 1; our version rewrites the same corner in the (γ, d) coordinate system.

---

## Appendix B: Full Proof of Theorem 1

**Theorem 1 (Absolute-increase pairwise-regime bound).** Let $f$ be a nonnegative monotone set function on ground set $V$. Suppose that for all $x\in V$, all $L\subseteq V\setminus\{x\}$, and all $S\subseteq V\setminus(L\cup\{x\})$,
\[
\Delta f(x\mid L\cup S)
\le
\Delta f(x\mid L)
+
\sum_{y\in S}\eta(x,y\mid L),
\]
where
\[
\eta(x,y\mid L)
=
\left[
\Delta f(x\mid L\cup\{y\})-\Delta f(x\mid L)
\right]_+
\]
and at most $d$ items $y$ have $\eta(x,y\mid L)>0$ for any fixed $x,L$. Let $\eta_{\max}=\max_{x,y,L}\eta(x,y\mid L)$. For any disjoint $L,S$ with $S=\{x_1,\ldots,x_s\}$, define
\[
A(L,S)=\sum_{x\in S}\Delta f(x\mid L),
\qquad
\psi_{s,d}=\sum_{i=1}^s \min(i-1,d).
\]
Then
\[
\frac{\sum_{x\in S}\Delta f(x\mid L)}{\Delta f(S\mid L)}
\ge
\frac{A(L,S)}{A(L,S)+\psi_{s,d}\eta_{\max}}.
\]

**Proof.** Write the joint marginal by telescoping in an arbitrary order $x_1,\ldots,x_s$:
\[
\Delta f(S\mid L)
=
\sum_{i=1}^{s}\Delta f(x_i\mid L\cup\{x_1,\ldots,x_{i-1}\}).
\]
By the pairwise-additive absolute-increase assumption,
\[
\Delta f(x_i\mid L\cup\{x_1,\ldots,x_{i-1}\})
\le
\Delta f(x_i\mid L)
+
\sum_{j<i}\eta(x_i,x_j\mid L).
\]
For each $x_i$, at most $d$ previous items can have positive interaction with it, and there are only $i-1$ previous items. Thus at most $\min(i-1,d)$ terms are nonzero, and each is bounded by $\eta_{\max}$. Therefore
\[
\Delta f(x_i\mid L\cup\{x_1,\ldots,x_{i-1}\})
\le
\Delta f(x_i\mid L)+\min(i-1,d)\eta_{\max}.
\]
Summing over $i$ gives
\[
\Delta f(S\mid L)
\le
\sum_{i=1}^{s}\Delta f(x_i\mid L)
+
\eta_{\max}\sum_{i=1}^{s}\min(i-1,d)
=
A(L,S)+\psi_{s,d}\eta_{\max}.
\]
Dividing $A(L,S)$ by both sides yields the claimed local block-ratio bound. If $A(L,S)=0$ and $\Delta f(S\mid L)>0$, the bound gives zero, which correctly reflects a prerequisite-chain failure rather than producing an undefined fractional interaction parameter. ∎

**Corollary 1 (Fractional active-context corollary).** If every $x\in S$ satisfies $\Delta f(x\mid L)\ge \tau>0$, then $A(L,S)\ge s\tau$. Since $\psi_{s,d}\le sd$,
\[
r_f(L,S)
\ge
\frac{s\tau}{s\tau+sd\eta_{\max}}
=
\frac{1}{1+d\,\eta_{\max}/\tau}.
\]
Setting $\delta_{\mathrm{active}}=\eta_{\max}/\tau$ recovers the familiar fractional form. In the paper, $\tau$ is not a global constant; it is the round-local lower-confidence singleton-marginal quantile $\tau_{r,q}^{LCB}$. When that quantile is near zero, the fractional corollary is inactive.

**Relation to Construction 1.** Construction 1 in Appendix A has singleton marginals 1 for $a$ and $b$ and joint value $M$, so $\eta_{\max}=M-2$, $d=1$, $s=2$, and $\psi_{2,1}=1$. The absolute theorem gives
\[
r_f(\varnothing,\{a,b\})
\ge
\frac{2}{2+(M-2)}
=
\frac{2}{M},
\]
which matches the construction exactly. The coarser fractional active-context form with $\tau=1$ gives $1/(1+M-2)=1/(M-1)$, which is same-order but looser. This is why the paper makes the absolute-increase theorem primary and treats the fractional expression as a convenient active-context corollary rather than as the robust theorem statement.
