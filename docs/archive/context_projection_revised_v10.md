# Context Projection Selection in Multi-Agent Systems: Conditional Theory, Metric Bridge, and Proxy-Regime Certification

---

## Abstract

We study dispatch-time context projection selection in multi-agent systems. We formalize it as a per-round, per-agent token-budgeted subset selection problem, where each agent's formal objective is defined by predictive V-information: the reduction in minimum achievable log-loss given selected context under a fixed predictive family. Frontier deployments are increasingly runtime- and session-oriented, but this paper isolates the dispatch-time context-projection layer as the narrowest formally analyzable and operationally diagnosable slice of that broader setting.

Our theoretical results are conditional. Under explicit objective-level conditions, including an approximate-submodularity regime hypothesis and a pairwise-additive complementarity model, we prove structural results for the formal objective: the independence of the submodularity ratio $\gamma$ and the supermodular degree $d$, and a robust lower bound on local block ratios under bounded absolute pairwise interaction. The familiar fractional form $\gamma \ge 1/(1+d\delta_{\max})$ is retained only as an active-context corollary, valid when the relevant singleton marginals are observably bounded away from zero.

We do not prove the key regime hypothesis for deployed frontier models. Instead, a second core contribution of the paper is an explicit bridge statement separating the formal objective, the proxy measurement layer, and the runtime heuristic layer. Our deployment-facing contribution is therefore not broad deployment-time verification, but a proxy-regime labeling and escalation protocol. Full V-information-calibrated diagnostics apply only under log-loss evaluation or a validated utility-to-log-loss bridge; otherwise, the diagnostics are operational-utility-only signals and must not be reported as evidence about the formal V-information regime.

Finally, we isolate a separate bridge risk between the formal objective and end-to-end performance. The formal approximation statements apply to optimization over the extracted candidate pool $M$, not the underlying information space $M^*$. We therefore treat extraction quality as a testable end-to-end bottleneck, not as an extension of the weak-submodular guarantee, and specify a value-stratified audit protocol to measure whether extraction failures disproportionately remove high-value findings.

## 1. Introduction

Multi-agent LLM systems often fail not because the underlying model lacks capability, but because the wrong information is projected into the wrong agent at the wrong time. Chase (2025) argues that many agent failures are context failures rather than model failures. Anthropic frames this as a context-engineering problem: curating the smallest possible set of high-signal tokens under a finite attention budget. METR (2025a) reports that current frontier agents achieve almost 100% success on tasks taking human experts less than 4 minutes, but less than 10% success on tasks taking more than around 4 hours. AgentTaxo (Wang et al., 2025a) measured 53–86% token duplication across multi-agent systems, and AgentDropout (Wang et al., 2025b) showed that *removing* context can improve performance. Together, these observations suggest that current systems often suffer from context pollution, not just context scarcity.

Existing frontier runtimes already expose multiple surfaces for shaping what a subagent sees — prompt strings, handoff histories, memory retrieval, structured state placeholders, and truncation or summarization hooks — but they typically leave the actual selection rule heuristic and implicit. In practice, token limits are often treated as truncation constraints rather than as optimization constraints, and context construction remains governed by natural-language reasoning, positional filters, or developer callbacks. What remains missing is a unified formal object for per-agent context allocation: an explicit candidate set, an explicit budget, and a value function over subsets. This paper formalizes that sub-layer.

Recent million-token architectures provide an existence proof that context selection is irreducible rather than obsolete: even when extreme context budgets are available, practical systems still rely on compression, sparse access, and locality-preserving retention rather than uniform dense processing. Our work studies the runtime-level analogue of this irreducible selection problem under explicit token budgets and per-round dispatch.

These observations motivate a precise question: given a budget of $B$ tokens and a candidate pool $M$ of $|M| \gg B$ context items produced by a multi-agent system, which subset $S_i^* \subseteq M$ of **content items** should be projected into each worker agent's context window to maximize task performance? This is the **context projection selection problem** studied in this paper. The problem is agent-heterogeneous, token-budgeted, and non-exclusive: the same finding may be valuable to multiple agents and may be projected to multiple downstream contexts.

**Terminology.** We distinguish four related concepts. *Context projection* is the end-to-end process of assembling a token sequence for an agent. *Context selection* is the subset optimization at the core of projection. *Context engineering* (Chase 2025, Anthropic 2025) is the broader design discipline encompassing selection, ordering, formatting, and prompt structure. *Context routing* refers to directing items to specific agents, which in our non-exclusive setting reduces to independent per-agent selection. The selection variable matters: unlike adjacent multi-agent formulations that choose which agents to activate or which communication links to instantiate, we study which **content items** each agent should receive.

**Positioning.** This paper does not propose a whole-session theory of agent behavior. Frontier deployments are increasingly runtime- and session-oriented, but we study a narrower problem: the **dispatch-time context-projection layer** that determines which content items from a candidate pool $M$ should be projected into an agent's window at a given round. This selector is a **myopic control law embedded in a larger runtime**, not a whole-session scheduler. We focus on this layer because it is the narrowest slice of the runtime that is both formally analyzable and operationally diagnosable. We therefore do **not** claim to solve orchestration, scheduling, or system-level coordination in multi-agent runtimes; our claim is that, in the orchestrator-worker regime where such runtimes are actually deployed, per-agent context allocation is a distinct and currently under-formalized sub-layer.

We assume an enclosing orchestrator-worker runtime in which a scheduler decides which worker is activated, when, and with what task description. This paper does not study that scheduler. It studies the distinct downstream subproblem: what token-budgeted context subset the dispatched worker should receive.

**Paper contract.** This paper makes four commitments. **Formal contract:** we define a formal value function for **per-round, per-agent content selection** using predictive V-information, and all approximation statements in the paper apply to this formal object. **Bridge contract:** deployed systems do not optimize this formal object directly; they use proxies and heuristics, so deployment does not automatically inherit theorem-level guarantees. **Metric-scope contract:** full V-information-calibrated diagnostics apply only under log-loss evaluation or a validated utility-to-log-loss bridge; otherwise, the same measurements are operational-utility-only escalation signals. **Failure contract:** when the objective-level regime condition or measurement-layer bridge fails, the theory becomes non-applicable at that layer, but proxy labeling, escalation, and extraction audit remain operationally useful when reported at the correct claim level. A second core contribution of the paper is the explicit bridge statement in Section 3.4, which separates the formal object, the proxy measurement layer, the runtime heuristic layer, and the metric-claim level.

**Multi-agent scope guard.** Multi-agent execution is used here only to induce heterogeneous context requirements across agents. We do not study which agents to activate, when to activate them, or how to coordinate them.

**Scope.** All theory and diagnostics in this paper are defined at the **per-round dispatch snapshot** level. We do not analyze session-level long-horizon effects in which current projection decisions reshape future candidate pools through planning, tool use, or downstream agent interactions. Instead, we treat those cross-round effects as properties of the enclosing runtime, and we expose the state summaries and audit interfaces required to make subsequent dispatch rounds monitorable and auditable. Nor do we claim that orchestrator-worker runtimes are universally superior to strong single-agent alternatives; we study the context-allocation problem in the regime where such runtimes are in fact used.

**Approach.** The theoretical results in this paper are conditional on Condition A (Section 3.1): that V-information-based context value is approximately submodular, or at least weakly submodular with a nontrivial block-ratio structure, for the deployed model family on the target distribution. We do not prove Condition A — it is the central open question (Section 8). Instead, we derive what follows when it holds and specify a proxy-regime labeling protocol that estimates, under fixed calibration conditions, whether monitored greedy-style selection is credible, ambiguous, or should be escalated. This makes the paper a **conditional theory + bridge statement + proxy-regime certification** paper rather than a closed end-to-end theory of deployed systems.

**Contributions.** We contribute a regime-aware framework organized around a single core line.

1. **Core contribution — formalization + conditional theory + bridge statement + conservative proxy-regime labeling.** We formalize **per-round, per-agent content subset selection under heterogeneous token budgets** as token-budgeted set-function maximization under a predictive V-information objective. The decision variable in our formulation is the subset of content items projected into each agent's context, distinguishing our setting from single-agent partitioning formulations and from multi-agent formulations whose decision variables are agents or communication links. We then derive conditional weak-submodular structural results for that formal object, make explicit the bridge from the formal objective to proxy measurement and runtime heuristics, and pair this bridge with a measurable protocol that produces conservative proxy-regime labels when the metric bridge is valid and operational-utility escalation signals when it is not.

2. **Supporting contribution A — structural theory.** We prove that the submodularity ratio $\gamma$ and supermodular degree $d$ are independent for general monotone set functions. We then derive a robust absolute-increase lower bound for local block ratios under pairwise-additive complementarity, with the fractional $1/(1+d\delta_{\max})$ form recovered only as a round-local active-context corollary.

3. **Supporting contribution B — runtime interfaces, metric witnesses, and extraction QA.** We specify the minimum auditable runtime interfaces required by a verifiable deployment setting, including ProjectionPlan, BudgetWitness, MaterializedContext, and MetricBridgeWitness artifacts. The MetricBridgeWitness records the calibration epoch, active stratum, metric class, bridge residual, drift status, and diagnostic claim level so that V-information proxy labels cannot be silently reported under operational-only metrics. We also isolate extraction quality as a separate bridge-risk bottleneck with a value-stratified audit protocol. These support layers make the proxy-labeling protocol executable, but they are not parallel theory claims.

## 2. Problem Formulation

### 2.1 Setup and notation

Let M = {m₁, ..., m_N} be the candidate pool of findings available for projection. Each finding m has content (natural language text), a token cost tokens(m), and source metadata (worker type, topic tags, evidence type, confidence, provenance references). Every finding in M has passed a dual-gate admission policy enforcing schema validity and budget eligibility — the selection problem operates over a pre-validated candidate pool. M is a snapshot at dispatch time; the pool grows monotonically within a session. The optimization is per-round over the current snapshot; cross-round dynamics where projection choices shape future pools are discussed in Limitation 5.

Let agent_i be a worker with task description q_i, role R_i, predictive family V_i (determined by model tier), and token budget B_i for projected observations. The budget B_i covers the projected observations slot only; system prompt, tool definitions, and task instructions occupy separate allocations held fixed during selection.

The dispatch event $(t, i, q_i, R_i, V_i, B_i)$ is produced by the enclosing runtime scheduler and is treated as input to the context-selection problem.

The **context selection problem for agent_i** is:

    max  f_i(S)
    s.t. Σ_{m ∈ S} tokens(m) ≤ B_i,  S ⊆ M

where f_i(S) measures the total value of set S for agent_i's task.

Throughout the formal development, **findings** are the primary analyzed instance of a broader class of deployable context items. We keep the formal object fixed at the finding level because it is the cleanest unit for stating the theory, defining extraction risk, and instrumenting runtime traces.

### 2.2 The value set function (Proposition 1)

We define the value set function using V-information (Xu et al., ICLR 2020):

    f_i(S) = H_{V_i}(Y_i | q_i) − H_{V_i}(Y_i | q_i, X_S)

where Y_i is agent_i's task output, X_S is the concatenated content of findings in S, and H_{V_i} denotes the minimum expected log-loss achievable by any predictor in family V_i. The difference is the V-information I_{V_i}(X_S → Y_i | q_i): how much the selected context S reduces agent_i's predictive uncertainty about its task output.

**Proposition 1 (Basic properties of V-information context value).** For fixed q_i and predictive family V_i, the value function f_i(S) is normalized, nonnegative, monotone at the formal V-information layer, and agent-heterogeneous, but not necessarily submodular.

*Proof sketch.* Normalization follows because f_i(∅)=0. Nonnegativity follows because conditioning on additional variables cannot increase the minimum achievable log-loss within V_i. Monotonicity holds at the formal V-information layer because the predictive family may ignore additional inputs; equivalently, adding variables cannot reduce the best achievable performance when the predictor can choose not to use them. This does **not** imply that an arbitrary prompt-materialization heuristic improves when more text is inserted. Agent heterogeneity follows because different agents may have different q_i and V_i. Submodularity does not follow from the definition and is the central open question addressed in Section 3.

For frontier models where V-information tracks Shannon-style interaction structure reasonably well, the choice of formulation is primarily one of theoretical precision rather than practical consequence; we adopt V-information because it explicitly accounts for the computational constraints of finite model families.

The **agent-conditional information density** of adding item m to set S is ρ_i(m | S) = Δf_i(m | S) / tokens(m), where Δf_i(m | S) = f_i(S ∪ {m}) − f_i(S) is the marginal value gain. The cost-benefit greedy algorithm selects items in decreasing order of ρ_i(m | S), updating S after each selection.

---

## 3. Theoretical Results

### 3.1 Condition A as a regime hypothesis

The submodularity ratio $\gamma$ (Das & Kempe, JMLR 2018) measures the worst-case ratio of the sum of singleton marginal gains to the joint marginal gain. When $\gamma = 1$, the function is submodular and greedy achieves $(1-1/e) \approx 63.2\%$ of optimal. When $\gamma < 1$, greedy achieves $(1-e^{-\gamma}) \times OPT$ under the usual weak-submodular assumptions.

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

**Theorem 1 (Absolute-increase pairwise-regime bound).** Let $f$ be nonnegative and monotone, and suppose Conditions C and C' hold with supermodular degree $d$ and maximum absolute interaction strength $\eta_{\max}$. For any disjoint context/block pair $(L,S)$ with $S=\{x_1,\ldots,x_s\}$, define
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
yielding the familiar greedy-style factor $(1-e^{-0.77})\approx 54\%$ for the corresponding weak-submodular idealization. **Failure case:** a 3-hop legal reasoning chain (statute $\rightarrow$ precedent $\rightarrow$ application) where each item is individually uninformative until the whole chain is present. In that case $\tau_{r,q}^{LCB}$ is near zero, the fractional corollary is inactive, and the absolute theorem reports a low or zero block ratio rather than masking the prerequisite failure.

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
| Formal | V-information set function $f_i(S)$ | Conditional theory |
| Proxy | CI Value / replay marginal estimates | Diagnostic signal under explicit bridge conditions |
| Pipeline | retrieval / reranking / MMR / packing | Heuristic only |
| Runtime | artifacts, memory, verification, state summaries | Observability and escalation interface |
| Metric bridge | log-loss or calibrated utility-to-log-loss relation | Claim-level gate |

**Formal layer.** The object analyzed in Section 3 is the V-information value function $f_i(S)$. All approximation statements, including Theorem 1 and its corollaries, apply to this formal object. They do not directly apply to an implementation that scores items with heuristics.

The formal-to-theorem transfer via a structural condition is an established template rather than a claim of novelty here. Das and Kempe (2018) use the submodularity ratio $\gamma$, Elenberg, Khanna, Dimakis, and Negahban (2018) use restricted strong convexity parameters to establish weak-submodularity consequences, and Bian, Buhmann, Krause, and Tschiatschek (2017) combine $\gamma$ with generalized curvature. What the bridge statement below adds on top of this established template is an explicit **proxy layer**, an explicit **pipeline layer**, a metric-scope gate, a conditional-equivalence analysis with enumerated failure modes, and the stratified diagnostic decomposition used in Section 4.

**Proxy layer.** The diagnostics in Section 4 require evaluating marginal value gains $\Delta f_i(m\mid S)$, which are defined at the formal layer. In practice, we estimate these via CI Value (Deng et al., 2025), a leave-one-out method that measures the task-utility change when an item is removed from the selected set. CI Value is therefore a **proxy for marginal utility**, not the formal objective itself.

**Metric-bridge regimes.** Full V-information-calibrated diagnostics apply only under log-loss evaluation or a validated utility-to-log-loss bridge; otherwise, the diagnostics are operational-utility-only signals and must not be reported as evidence about the formal V-information regime. We distinguish three metric regimes.

1. **Regime A: log-loss aligned.** The predictive family $V_i$ matches the deployed model tier, the materialization order is fixed, and the evaluation metric is log-loss. In this regime, CI-style finite differences can be interpreted as proxy measurements of the formal V-information value function.

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

3. **Regime C: non-decomposable or uncalibrated production utility.** Pass/fail task success, rubric scores with nonlinear aggregation, evaluator preferences, and human judgments can be measured through finite differences, but they do not automatically approximate log-loss deltas or V-information deltas. In this regime the protocol reports operational-utility-only labels for the utility objective
\[
f_U(S)=\mathbb E[U(\text{output from }S)].
\]
These labels may guide escalation, but they do not certify Condition A, Theorem 1, or V-information weak-submodularity.

**Pipeline layer.** The deployed system uses a heuristic scoring and packing pipeline rather than directly optimizing CI Value or the V-information objective. In other words, the pipeline is not assumed to optimize the proxy; at best, it is expected to correlate with the proxy strongly enough to be useful.

Two recent works propose partial bridge statements at adjacent abstraction levels. Tok-RAG (Xu et al., 2025) establishes a token-level theory in which distribution similarity between the RAG-fused and retrieved-text distributions serves as a theoretically justified proxy for a benefit-versus-detriment gap, and then operationalizes that theory with a per-token switching rule. AdaGReS (Peng et al., 2025) establishes $\varepsilon$-approximate submodularity for token-budgeted context selection under practical embedding-similarity conditions, together with a closed-form instance-adaptive calibration of the relevance-redundancy trade-off parameter. Both are important adjacent precedents, but their epistemic posture differs from the one taken here. First, the proxy-objective relationship in our setting is explicitly **conditional** on a model-tier match, log-loss utility, or a measured utility-to-log-loss bridge. Second, the deployed pipeline here is explicitly **not assumed to implement** the theoretical decision rule; the pipeline-versus-proxy gap is itself a first-class object of diagnosis. Third, Section 4 stratifies diagnostics across formal, proxy, pipeline-versus-proxy, and metric-claim layers rather than collapsing them into a single operational test.

This distinction matters because the diagnostics do not all measure the same thing:

1. **Formal-layer statements** belong to Section 3 only. They concern $f_i(S)$, $\gamma$, $d$, $\eta_{\max}$, and local block ratios as mathematical objects.
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

## 4. Proxy-Regime Labeling and Escalation Protocol

Before introducing the diagnostic families, it is useful to distinguish our protocol from two adjacent diagnostic literatures. First, recent LLM-memory work has begun to propose pipeline-level diagnostic frameworks. Yuan, Su, and Yao (2026), for example, study retrieval relevance, memory utilization, and failure modes in memory-augmented LLM agents. Their question is primarily one of **output attribution**: where in the retrieval-to-generation pipeline does failure occur? Second, recent information-theoretic work on multi-turn LLM interaction has proposed dialogue-level diagnostics such as Information Gain per Turn and Token Waste Ratio, together with discussion of handoff or escalation under sustained low information gain. That line measures **dialogue-channel information flow** rather than subset-selection structure.

The protocol in this section operates at a different epistemic layer. Its diagnostics are **selector-structure diagnostics**: they estimate whether the operative per-round selection problem appears redundancy-dominated, complementarity-heavy, higher-order, or unstable under calibrated proxy evaluation. In a larger runtime, these diagnostics serve as deployment-facing control signals for subsequent dispatch rounds. The purpose of the protocol is therefore not generic pipeline debugging, and not dialogue-efficiency measurement, but **proxy-regime labeling for context selection**: deciding when monitored greedy-style selection is credible, when the label is ambiguous, and when escalation to stronger search families is warranted.

Full V-information-calibrated diagnostics apply only under log-loss evaluation or a validated utility-to-log-loss bridge; otherwise, the diagnostics are operational-utility-only signals and must not be reported as evidence about the formal V-information regime.

### 4.1 Three empirical diagnostic families

**Diagnostic family 1 — Block-ratio LCB.** The headline weak-submodularity diagnostic is not the old trace ratio. The relevant Das--Kempe-style object is the local block ratio
\[
r_f(L,S)
=
\frac{\sum_{x\in S}\Delta f(x\mid L)}
{\Delta f(S\mid L)},
\qquad S\cap L=\varnothing.
\]
The paper does not claim to estimate the global worst-case $\gamma$ over all $L,S$. Instead, it estimates an **operational lower-quantile block ratio** over the selector's actual decision region:
\[
\gamma^{op}_{b,q}
=
Q_q\left(r_f(L,S):(L,S)\sim \Pi_b\right),
\]
where $b=|S|$, $q$ is a low quantile such as 0.05 or 0.10, and $\Pi_b$ is a specified sampling distribution over top-slice, trace-neighborhood blocks.

The headline block size is $b=2$ because Theorem 1 is a pairwise-additive theorem. Pair blocks are the smallest blocks that detect the pairwise complementarity failure mode. For stress testing, the protocol also reports a degree-adaptive star-block diagnostic and a block-3 or triple-excess diagnostic when Corollary 2 is invoked:
\[
\widehat{\gamma}^{op,LCB}_{2,q},
\qquad
\widehat{\gamma}^{op,LCB}_{star,q},
\qquad
\widehat{\gamma}^{op,LCB}_{3,q}.
\]
The block size adapts to observed complementarity degree, not to observed redundancy. Redundancy tends to make the block ratio larger; complementarity is the failure mode that requires larger stress blocks.

**Sampling distribution.** Uniform sampling over all of $M$ is not appropriate because it estimates a property of items the selector would never consider. The diagnostic samples from the top-$L$ candidate slice $C_L$ where the selector actually operates. Contexts are drawn from a fixed calibration mixture
\[
\Pi_{ctx}
=
\lambda_1\Pi_{prefix}
+
\lambda_2\Pi_{perturb}
+
\lambda_3\Pi_{audit},
\]
where $\Pi_{prefix}$ samples greedy or replay prefixes, $\Pi_{perturb}$ samples small perturbations of those prefixes, and $\Pi_{audit}$ samples random admissible contexts from the top-$L$ slice to prevent total overfitting to the realized trace. Blocks are drawn from the residual slice using
\[
\Pi_b(S\mid L)
=
\rho_1\Pi_{rank}
+
\rho_2\Pi_{edge}
+
\rho_3\Pi_{random}.
\]
The edge-biased component oversamples plausible complements in a cheap pre-screened interaction graph, while the random audit component estimates what the pre-screen misses.

**Noisy ratio estimator.** For sampled block $(L_h,S_h)$ and replicate $r$, define paired evaluation differences
\[
A_{h,r}
=
\sum_{x\in S_h}\left[U_r(L_h\cup\{x\})-U_r(L_h)\right],
\]
\[
B_{h,r}
=
U_r(L_h\cup S_h)-U_r(L_h).
\]
The numerator and denominator share baselines and are therefore correlated. A second-order delta-method bias-corrected point estimate is
\[
\widetilde r_h
=
\frac{\bar A_h}{\bar B_h}
-
\frac{1}{n}
\left(
\frac{\bar A_h s^2_{B,h}}{\bar B_h^3}
-
\frac{s_{AB,h}}{\bar B_h^2}
\right),
\]
where $s^2_{B,h}$ and $s_{AB,h}$ are the sample variance of $B$ and sample covariance of $A,B$. For conservative labels, however, the protocol uses a ratio lower-confidence bound:
\[
\underline r_h
=
\frac{[\bar A_h-\varepsilon_{A,h}]_+}{\bar B_h+\varepsilon_{B,h}},
\]
and reports
\[
\widehat{\gamma}^{op,LCB}_{b,q}
=
Q_{q-\epsilon_H}(\{\underline r_h\}_{h=1}^{H}),
\qquad
\epsilon_H=
\sqrt{\frac{\log(2/\alpha_Q)}{2H}}.
\]
Blocks with denominator signal below a predeclared threshold are marked **uninformative**, not treated as low-ratio failures.

**TraceDecay.** The trace-local statistic
\[
\mathrm{TraceDecay}_t
=
\frac{\Delta f(m_t\mid P_{t-1})}{\Delta f(m_t\mid\varnothing)}
\]
is retained as a marginal-decay signal along the realized path. It can indicate whether later items are losing singleton value as the prefix grows, but it is **not** an estimator of the Das--Kempe submodularity ratio and is not the headline weak-submodularity diagnostic.

**Diagnostic family 2 — Interaction information and higher-order excess.** For sampled pairs $(m_j,m_k)$,
\[
II(m_j,m_k)
=
\Delta f(m_j\mid\varnothing)+\Delta f(m_k\mid\varnothing)-\Delta f(\{m_j,m_k\}\mid\varnothing).
\]
Positive $II$ indicates redundancy; negative $II$ indicates synergy. In deployment or offline replay, pairs are sampled from the top-$L$ candidate slice rather than uniformly over the full pool, since the selector operates in that region. The sample size is chosen to achieve a target confidence-interval width for the estimated synergy fraction or interaction mass.

Pairwise interaction diagnostics should be run through a cost-sensitive cascade when $L$ is large. A cheap pre-screen scores pairs by embedding overlap, metadata collision, provenance overlap, shared entities, temporal proximity, and dependency-graph links. Expensive utility-difference evaluation is run on retained pairs plus a random audit stratum. The audit estimates missed interaction mass, not merely missed edge count. A cascade is admissible for a target $\gamma_{\min}$ only if
\[
\max_x\left(G_x^{eval}+\xi_x^{miss,UCB}\right)
\le
\frac{1}{\gamma_{\min}}-1,
\]
where $G_x^{eval}$ is evaluated positive interaction mass incident to $x$ and $\xi_x^{miss,UCB}$ is an upper bound on omitted positive mass. One conservative audit allocation can be stated explicitly. Let $O_x$ be the omitted candidate-neighbor set incident to anchor $x$ after the cheap pre-screen, and let $A_x\subseteq O_x$ be a uniform audit sample of size $m_x$. If positive interaction strengths satisfy $\delta_+(x,y\mid L)\in[0,R_x]$, then
\[
\widehat G_x^{miss}
=
\frac{|O_x|}{m_x}\sum_{y\in A_x}\delta_+(x,y\mid L)
\]
is an unbiased estimator of omitted positive interaction mass, and the Hoeffding-style allocation
\[
m_x
\ge
\frac{|O_x|^2 R_x^2}{2\epsilon_x^2}
\log\frac{2L}{\alpha}
\]
suffices to bound every anchor's missed-mass estimate within $\epsilon_x$ with failure probability at most $\alpha$ over a top-$L$ slice. Empirical-Bernstein bounds or Neyman allocation can reduce this cost when variance estimates are favorable, but the key operational point is that per-anchor missed-mass certification is not a constant-fraction audit. If the required audit budget is too large, the system must shrink the top-$L$ slice, widen the pre-screen, or downgrade the label to ambiguous.

When Corollary 2 is invoked, the protocol tests whether third-order excess is additive or mediated-amplifying. For triple $\{i,j,k\}$ in context $L$, define the pairwise-additive prediction
\[
P_{ijk}
=
a_i+a_j+a_k+\beta_{ij}+\beta_{ik}+\beta_{jk},
\]
where $a_i=\Delta f(i\mid L)$ and $\beta_{ij}=\Delta f(\{i,j\}\mid L)-a_i-a_j$. The triple excess is
\[
\omega_{ijk}
=
\Delta f(\{i,j,k\}\mid L)-P_{ijk}.
\]
A one-sided test rejects the non-amplifying assumption if $\mathrm{LCB}(\omega_{ijk})>\tau_3$. Ambiguous triples are treated as ambiguous rather than validating the corollary.

**Diagnostic family 3 — Augmented-greedy gap and escalation certificates.** Compare monitored greedy-style selection with seeded augmented greedy and, when necessary, interaction-aware local search. Seeded augmented greedy enumerates feasible seeds $T$ of size at most $k$, greedily completes each seed under the remaining budget, and returns the best completed set.

Let $\alpha_0=1-\exp(-\gamma_0)$, where $\gamma_0$ is the applicable certified or assumed block-ratio lower bound. If an offline calibration solver supplies an incumbent $\widehat O$ and an upper bound $U^+$ on $OPT$, then the observable certificate is
\[
\frac{f(\mathrm{SAG}_k)}{OPT}
\ge
\max_{\substack{T\subseteq \widehat O\\ |T|\le k}}
\frac{
\alpha_0 L^-(\widehat O)+(1-\alpha_0)L^-(T)
}{
\widetilde U^+ + \epsilon_s
}.
\]
Here $L^-$ denotes lower-confidence value estimates and $\widetilde U^+$ is the upper bound returned by the calibration-time solver or surrogate. If $\widetilde U^+$ is produced by a fitted pairwise or knapsack-style surrogate rather than by an exact solver on the true evaluated objective, the slack term must be decomposed as
\[
\epsilon_s
=
\epsilon^{bridge}_s+\epsilon^{surrogate}_s+\epsilon^{eval}_s.
\]
The bridge component $\epsilon^{bridge}_s$ is inherited from the stratified utility-to-log-loss residual $\zeta_s$ recorded in the MetricBridgeWitness. The surrogate component $\epsilon^{surrogate}_s$ is a high-confidence upper residual of the fitted surrogate over feasible calibration sets in stratum $s$. The evaluation component $\epsilon^{eval}_s$ is the finite-sample and decoding-variance slack used to turn repeated proxy evaluations into lower or upper confidence bounds. If $\widetilde U^+$ is produced by exact optimization over the true evaluated objective, then $\epsilon^{surrogate}_s=0$; if the metric bridge is absent, then the certificate is for the operational utility or surrogate objective only. If no credible upper bound is available, seeded augmented greedy is reported as an escalation heuristic, not as a certified guarantee.

Interaction-aware local search is specified as a monotone improvement layer over greedy or seeded greedy. Its neighborhood consists of cost-feasible 2-addition or swap moves on the detected interaction graph, accepted only when a lower confidence bound on improvement is positive. It provides a termination certificate and a no-improving-detected-pair-move certificate, not a universal multiplicative improvement over greedy.

### 4.2 Two-axis decision protocol

The diagnostic protocol outputs a pair:
\[
(\texttt{metric\_claim\_level},\texttt{selector\_regime\_label}).
\]
The first axis says what the diagnostics are allowed to claim about the measurement layer; the second says what the selector should do.

| Metric bridge status | Selector signal | Reported label |
|---|---|---|
| log-loss aligned | high block-ratio LCB, low synergy, small augmented-greedy gap | certified proxy-greedy-valid |
| bridge-calibrated | same, after $\zeta_s$ degradation | calibrated proxy-greedy-valid |
| bridge stale | any signal | ambiguous; recalibrate |
| operational-only | high utility block-ratio, low utility synergy | utility-greedy-valid only |
| operational-only | low utility block-ratio or high utility synergy | utility-escalate |
| any metric | insufficient samples, failed cascade audit, low denominator signal, or conflicting diagnostics | ambiguous |

Examples:
\[
(\texttt{Vinfo\_proxy\_certified},\texttt{greedy\_valid})
\]
and
\[
(\texttt{operational\_utility\_only},\texttt{escalate})
\]
are not interchangeable. The former is a calibrated proxy statement about the formal objective. The latter is an operational utility signal about the deployed metric.

The selector-regime label has three possible values:

1. **certified greedy-valid**: the bridge is valid, block-ratio LCB is above threshold, synergy and higher-order excess are below threshold, and the augmented-greedy gap is small;
2. **certified escalate**: low block-ratio evidence, elevated synergy, higher-order excess, or a large augmented-greedy gap is detected with sufficient confidence;
3. **ambiguous**: bridge stale, insufficient samples, cascade audit failure, low denominator signal, or conflicting diagnostics.

Escalation is a diagnostics-triggered switch from monitored greedy-style selection to progressively stronger search families. It is not deployment inheritance of the approximation guarantees for the formal objective. The greedy-versus-augmented gap is primarily a calibration-time or replay-time signal, not a required per-round production diagnostic.

### 4.3 Calibration architecture

We treat calibration as a required interface between the theory and a practical system, but not as a single fixed recipe. A reasonable operationalization is a two-phase workflow.

**Phase 1 (offline replay).** Assemble a calibration set of representative sessions or dispatch rounds, replay selections under controlled evaluation settings, and compute CI-based or log-loss marginal estimates. The exact number of sessions, model tiers, and budgets is application-dependent. The purpose of this phase is to estimate proxy fidelity, diagnostic stability, and the empirical relationship between regime labels and downstream quality.

**Phase 2 (surrogate modeling, optional).** If CI-style replay is too expensive for frequent use, train a lightweight surrogate to predict CI-based quantities from pipeline signals such as retrieval scores, reranker outputs, token cost, and redundancy features. The surrogate is useful only if it preserves the regime distinctions needed by Section 4; otherwise it should be treated as exploratory rather than as a deployment component.

Before any empirical anchor is run, at minimum six choices should be fixed rather than left implicit: the deployed **model tier**, the **utility metric**, the **metric-claim regime**, the **materialization ordering policy**, the **decoding / variance-control policy**, and the **candidate-slice policy** used for pairwise interaction and replay studies. These choices determine whether replay numbers can be interpreted as bridge evidence rather than as artifacts of uncontrolled evaluation settings.

### 4.3.1 Synthetic regime benchmark with pre-registered validity gate

As a minimal empirical anchor for the diagnostic protocol, we specify a **synthetic regime benchmark** over budgeted set functions with known interaction structure. The goal of this benchmark is deliberately narrow. It is **not** intended to establish broad deployment validity, and it is **not** a substitute for an eventual offline replay study on real dispatch traces. Its purpose is to test whether the diagnostic stack exhibits the intended **signature-level regime discrimination** under controlled conditions.

The benchmark validity table is fixed before benchmark execution. Results are interpreted according to the pre-registered table rather than post-hoc reassignment of negative outcomes to calibration evidence.

The benchmark contains three synthetic families, each generated under a fixed budget regime and evaluated under a fixed proxy-noise policy:

1. **Redundancy-dominated instances.** Findings are organized into clusters of near-duplicates or partial paraphrases. Within a cluster, the first selected item contributes most of the value and subsequent items add only small residual gain. These instances operationalize the diminishing-returns intuition behind Condition B.
2. **Pairwise-synergy instances.** The value function contains sparse pairwise interaction bonuses, with each item participating in at most a bounded number of pairwise complementarities:
   \[
   f(S)=\sum_i w_i \mathbf{1}[i\in S] + \sum_{(i,j)\in E}\beta_{ij}\mathbf{1}[i,j\in S].
   \]
   These instances instantiate the pairwise-dominated setting studied by Theorem 1.
3. **Higher-order-synergy instances.** In addition to singleton and pairwise terms, the value function contains sparse triple or prerequisite-chain bonuses,
   \[
   f(S)=\sum_i w_i \mathbf{1}[i\in S] + \sum_{(i,j)\in E}\beta_{ij}\mathbf{1}[i,j\in S] + \sum_{(i,j,k)\in T}\tau_{ijk}\mathbf{1}[i,j,k\in S],
   \]
   with $\tau_{ijk}$ large enough that triple interactions cannot be well explained by pairwise structure alone. These instances lie outside the clean applicability domain of Theorem 1 and are intended to stress-test the escalation logic rather than the theorem.

Each synthetic instance includes a token-cost vector and dispatch budget $B$. The benchmark is run in two layers. At the **oracle layer**, the synthetic value function itself is available, allowing direct comparison of greedy, seeded augmented greedy, local search, and optimal or near-optimal solutions. At the **proxy layer**, noisy or partial marginal estimates are derived from the oracle to simulate CI-style evaluation noise and test whether block-ratio LCBs, interaction estimates, and augmented-greedy gaps remain usable under imperfect measurement.

The benchmark should not require a single monotone ordering such as
\[
\widehat\gamma_R > \widehat\gamma_P > \widehat\gamma_H.
\]
In pure higher-order prerequisite settings, pairwise diagnostics can look deceptively healthy because no pair alone carries the decisive interaction. The correct target is signature-level discrimination by the full stack:

| Synthetic family | Expected signature |
|---|---|
| Redundancy-dominated | high block-ratio LCB, low synergy, small augmented-greedy gap |
| Pairwise-synergy | detected pairwise interaction mass, lower pair-block ratio, seeded greedy improves |
| Higher-order-synergy | pairwise diagnostics may be insufficient; block-3 or triple-excess test fires; greedy-valid label is withheld |

The pre-registered interpretation table is:

| Benchmark outcome | Interpretation | Required paper response |
|---|---|---|
| Oracle regimes separate; proxy regimes separate | Minimal empirical anchor succeeds | Maintain conservative proxy-regime certification claim |
| Oracle regimes separate; proxy regimes fail | Measurement-layer calibration failure | Downgrade to oracle-only structural evidence or increase calibration budget |
| Oracle regimes fail | Diagnostic stack lacks structural validity | Revise diagnostics before deployment-facing claim |
| Diagnostics flag complementarity; escalation improves | Escalation claim supported | Keep escalation protocol |
| Diagnostics flag complementarity; escalation does not improve | Monitoring supported, escalation unsupported | Reframe escalation as warning-only or revise algorithm family |
| Higher-order instances labeled greedy-valid | Unsafe false-positive failure | No deployment-facing verification claim |
| Most instances labeled ambiguous | Conservative but low-discrimination | Report feasibility limitation; do not count ambiguity as successful regime discrimination |

Minimal pass conditions are: oracle-layer signature separation for most instances in each family; no high-confidence greedy-valid label on higher-order-synergy instances; seeded augmented greedy closes a meaningful fraction of the greedy-optimal gap on pairwise-synergy instances; proxy-layer label instability remains below a declared tolerance or the paper reports the required sample-size increase; and ambiguous labels are reported separately rather than counted as successful regime discrimination.

This benchmark is the structural-validity floor of a richer empirical stack. A natural next layer is offline replay over real dispatch traces, which would test the selector under realistic workflow distributions.

### 4.4 Adaptive calibration, metric scope, and composite certification

This subsection separates two distinct failure modes.

**Objective-level regime failure** occurs when Condition A fails for the formal V-information objective. In that case, weak-submodular approximation language no longer applies to the formal object, and selector escalation is the appropriate response.

**Measurement-layer bridge failure** occurs when CI-style or utility-based finite differences are not reliable measurements of the formal V-information objective. In that case, the selector may still be operationally useful, but the metric-claim level must be downgraded to calibrated proxy, operational utility only, or ambiguous.

Calibration is organized by epoch. Within epoch $e$, diagnostic labels are computed against a fixed reference distribution
\[
D_{ref}^{(e)}(Z),
\qquad
Z=(L,S,\text{task},\text{materialization policy},\text{metric stratum}).
\]
The reference distribution is fixed within the epoch but refreshed when a drift sentinel fires. Refresh triggers include bridge-residual drift,
\[
\mathrm{UCB}(Q_p(e_h))>\zeta_s+\Delta_{tol},
\]
candidate-slice shift, such as an MMD, KS, PSI, or calibrated-classifier two-sample test crossing threshold $\tau_{shift}$, or a calendar/volume staleness limit.

If an escalated selector $\pi$ changes the induced trace distribution, on-policy claims require either recalibration or importance weighting under an overlap condition $D_\pi\ll \mu$. With clipped weights $\tilde w_h$,
\[
n_{eff}
=
\frac{\left(\sum_h \tilde w_h\right)^2}{\sum_h \tilde w_h^2}.
\]
If overlap or effective sample size is inadequate, the label is ambiguous until recalibration.

Composite certification uses a transparent union bound in the main text. Let events $E_\gamma,E_{cas},E_3,E_\zeta,E_{seed},E_{drift}$ denote validity of the block-ratio LCB, cascade missed-mass bound, third-order test, metric bridge, seeded-greedy certificate, and drift sentinel. If each has failure probability $\alpha_j$, then
\[
\Pr\left[\bigcap_j E_j\right]\ge 1-\sum_j\alpha_j.
\]
Sequential gatekeeping can reduce average evaluation cost, but only if the testing policy and alpha-spending rule are predeclared; it is therefore best treated as an implementation appendix rather than the primary certificate.

For non-decomposable metrics such as pass/fail task success, rubric scores, or human-preference judgments, marginal utility estimates are episode-level finite differences rather than decomposable log-loss reductions. The diagnostics may still guide escalation for the deployed utility, but they do not estimate V-information submodularity unless a separate bridge calibration is supplied. For Bernoulli pass/fail utility, detecting an effect of size $\delta$ requires $O(1/\delta^2)$ paired evaluations per marginal or block, before accounting for block sampling, strata, cascade audits, or decoding variance.

---

## 5. Extraction Quality as a Testable End-to-End Bottleneck

### 5.1 The uniformity assumption

This section does **not** extend the weak-submodular guarantee in Section 3. Instead, it isolates a separate bridge risk between the formal objective and end-to-end performance: the formal optimization problem is defined over the extracted candidate pool $M$, whereas real system performance depends on the quality of the extraction process that constructs $M$ from richer upstream outputs. This is a quality bottleneck over the $M^* \rightarrow M$ bridge, not an additional theorem layer.

The stylized linear-degradation picture in Section 3.3 assumes extraction completeness c is uniform across the value distribution. If this holds, the degradation is linear in extraction incompleteness. If it fails — if the extraction gate preferentially drops high-value findings — the degradation can be superlinear. We therefore treat extraction quality as a **testable bottleneck**, not as a proven ceiling.

### 5.2 Evidence against uniformity

Multiple independent lines of evidence suggest the uniformity assumption does not hold. We distinguish three epistemic levels: established evidence from peer-reviewed studies in adjacent domains, a transfer hypothesis arguing that these findings apply to extraction gates, and unmeasured claims that require the evaluation protocol in Section 5.3 to resolve.

**Problem A: hard output constraints can harm reasoning or generation quality.** CRANE (Banerjee et al., ICML 2025) proves that LLMs constrained to restrictive grammars can only solve problems within TC⁰. A parallel line of evidence shows a "projection tax" during forced formatting: Draft-Conditioned Constrained Decoding (DCCD) similarly argues that strict grammatical constraints can materially degrade mathematical reasoning accuracy, reporting substantially lower GSM8K performance under standard constrained decoding in the reported 1B setting (Reddy et al., 2026). These results do not directly measure extraction completeness, but they do establish that hard output constraints can change what the model is able to express.

**Problem B: even with two-step mitigation, format conversion may still lose high-value information.** The openWorker architecture follows the standard mitigation of separating unconstrained reasoning from constrained extraction, so the strongest CRANE-style reasoning limitation does not apply directly to the full worker pipeline. But this does not eliminate the second risk: a free-form answer can still lose nuance when it is converted into a compact structured finding. This is where the extraction bottleneck lives.

Two adjacent evidence streams support that second risk. First, Peters and Chin-Yee (2025) found that LLM summaries are nearly 5× more likely to contain overgeneralizations than human summaries (OR = 4.85, n = 4,900). The information most at risk — scope qualifiers, statistical nuance, and temporal restrictors — often carries a disproportionate share of value. Second, FABLES (Kim et al., COLM 2024) found that unfaithful claims concentrate in content requiring multi-hop reasoning, such as events (31.5%) and character states (38.6%). Together, these studies suggest that complex, conditional, or qualification-heavy content is more vulnerable to distortion during reformulation. We use them as evidence against the uniformity assumption, not as prior extraction-audit methodologies.

**Transfer hypothesis.** These findings transfer to extraction gates because (1) the 30% conciseness target requires selective extraction rather than transcription, (2) constrained decoding can distort the probability distribution over outputs, and (3) overgeneralization can arise during any LLM reformulation, including schema filling and summarizing into structured findings.

**Unmeasured claim.** The magnitude of the bias in our specific extraction setting remains unknown. The value-stratified evaluation protocol in Section 5.3 is designed to resolve exactly this question by distinguishing simple from complex findings and captured from distorted from missing outcomes.

A practical runtime may therefore implement the extraction gate as a dual-output interface: in addition to the structured finding itself, it may emit lightweight auxiliary metadata such as compression confidence, conflict indicators, or coarse reasoning-depth tags derived from the upstream free-form trace. In this paper, such metadata are treated strictly as **proxy-layer runtime signals**, not as formal variables in the theory. Their purpose is to support instrumentation, monitoring, or later audit of the extraction process, not to extend the weak-submodular guarantee from the extracted candidate pool \(M\) back to the underlying information space \(M^*\).

### 5.3 A value-stratified evaluation protocol

Prior IE and summarization evaluation has developed substantial **value-weighting** machinery, but weighting and stratification answer different questions. ACE-style application-value scoring and the Pyramid method in summarization collapse non-uniform content importance into a single aggregate score. More recent structured-output evaluations continue this broader lineage by improving schema accuracy, content fidelity, or application-centric correction-oriented evaluation. What we propose is methodologically distinct: **per-stratum reporting** of extraction completeness for free-form-to-structured extraction as a preprocessing step prior to selection. The diagnostic output is $p_{\mathrm{simple}}$, $c_{\mathrm{high}}$, and $c_{\mathrm{low}}$ as three separate numbers under a mixture-model aggregate, rather than a single weighted score.

Existing benchmarks, to our knowledge, do not report separate completeness rates for simple versus complex findings in order to test whether the extraction-completeness assumption is approximately uniform. BFCL (Patil et al., 2025) evaluates function-call correctness and ToolBench (Qin et al., 2023) evaluates API-chain execution; these are orthogonal structured-action benchmarks rather than extraction-completeness audits. SLOT (Shen et al., 2025) evaluates schema accuracy and content fidelity for structured outputs, KIEval (Khang et al., 2025) introduces an application-centric correction-oriented metric for document KIE. These are useful adjacent precedents, but we are not aware of prior work that reports per-stratum extraction completeness for free-form-to-structured extraction in order to test the uniformity assumption behind a downstream formal guarantee.

The protocol produces three numbers:

    c_effective = p_simple × c_high + (1 − p_simple) × c_low

where p_simple is the fraction of simple findings, c_high is completeness for simple findings, and c_low is completeness for complex findings. Human annotators classify each ground-truth finding by complexity (extraction difficulty) and each extraction outcome as captured, captured-with-overgeneralization (sub-classified as "core preserved" or "core materially changed"), or missing.

This replaces the uniform \(c\) with a testable mixture model. The purpose of the protocol is not merely to obtain a more nuanced score, but to test whether extraction failures are approximately uniform across strata or concentrated in the complex/high-value stratum. Human annotation remains the ground-truth protocol for this audit. In a practical system, one may additionally maintain automated probes based on extraction-time metadata such as confidence or compression diagnostics, but such signals should be treated as supplementary monitors rather than substitutes for the value-stratified audit itself. We leave full execution to future work; the contribution here is designing the right diagnostic measurement where none existed.

---

## 6. Runtime Interface Requirements for Verifiable Context Projection

### 6.1 Architecture overview

This section specifies the **minimum runtime observability requirements** needed to support the proxy-regime labeling protocol in Section 4. openWorker is the running instantiation, but the point of Section 6 is not merely to describe one system; it is to state what a runtime must expose if dispatch-time context projection is to be verifiable in practice. The selector studied here is a myopic control law embedded in a larger runtime, so the architectural burden is to make each dispatch round auditable rather than to solve whole-session control in one step.

In realistic deployments, the surrounding runtime manages higher-level concerns such as session state, task decomposition, tool execution, memory access, evaluation, correction, and long-term evolution. Existing runtimes already expose partial surfaces for context construction, but they do so heuristically and without a unified formal object. The contribution of the present paper is narrower and more formal: it specifies the context-projection layer that sits immediately before worker dispatch, together with the artifacts and state summaries needed to monitor that layer across rounds.

The ProjectionPlan / BudgetWitness / MaterializedContext / MetricBridgeWitness chain is intended as a minimal auditable interface for runtime context projection. The first three artifacts make selector and materialization decisions replayable. The fourth artifact makes measurement-layer claims auditable.

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
| Selector → Scheduler | $\widehat{\gamma}^{op,LCB}_{b,q}$, TraceDecay, interaction mass, augmented-greedy gap | selector diagnostics |
| Selector → Scheduler | $(\texttt{metric\_claim\_level},\texttt{selector\_regime\_label})$ | two-axis decision label |

### 6.2 The four-artifact projection chain

A runtime that supports verification should reify context projection into four auditable artifacts. These artifacts should be designed as **machine-readable audit interfaces** first and human-readable records second: their primary purpose is to support replay, proxy evaluation, trace comparison, and structured downstream audit.

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

A calibration epoch can contain multiple strata with different $\zeta_s$ values. The active-stratum field is therefore mandatory: without it, the witness certifies that some bridge calibration exists, but not that the current dispatch inherits the correct one.

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
5. **Artifacts are reified.** The runtime records a ProjectionPlan, BudgetWitness, MaterializedContext, and MetricBridgeWitness for the dispatch.
6. **Worker executes the task.** The selected context is sent to the worker agent together with its task instructions and tool interface.
7. **Evaluator computes diagnostics.** Post-dispatch replay and proxy measurements estimate block-ratio health, interaction mass, pipeline-versus-proxy mismatch, metric-bridge status, and extraction risk.
8. **Planner updates state summaries for the next round.** The resulting signals are written back into the runtime state shell, where they influence subsequent dispatch decisions.

## 7. Related Work

The closest prior art differs from our setting along three axes. First, many systems optimize the wrong **granularity**: agents, links, or memory-routing decisions rather than per-agent context units. Second, many works use the wrong **budget object**: cardinality, dropout rates, compression ratios, or whole-system cost caps rather than per-agent token budgets at per-round dispatch time. Third, many works lack the relevant **guarantee structure**: they provide heuristics, learned policies, or empirical improvements without a formal value function over context subsets and without a bridge statement separating theorem, proxy, and runtime layers. We organize the discussion below around these axes.

### 7.1 Single-agent budgeted context selection

Recent work on context selection has begun to treat prompt assembly as an explicit optimization problem, but almost always for a **single predictive target under a single global budget**. Peng et al. (2025) provide a (1 − 1/e − ε') greedy approximation under ε-approximate submodularity for RAG context selection, using a modular-minus-supermodular objective to model redundancy. InSQuaD (Nanda et al., 2025) applies Submodular Mutual Information to exemplar selection for in-context learning, showing that submodular information objectives can improve retrieval quality for a single downstream model. Sub-CP (Zheng et al., 2025) studies budgeted context partitioning for block-wise in-context learning, again with a single target model and a single total context budget. These papers are the closest single-agent antecedents to our setting, but they do not address heterogeneous per-agent routing of content items across multiple downstream agents.

Wang et al. (2026) provide a complementary mechanistic account of when context helps in single-context Transformers. Their framework operates in output-vector space rather than information-theoretic quantities, and their selection strategy scores items independently rather than reasoning over set composition. We use their results as mechanistic support for pairwise interaction structure, not as a formal solution to the multi-agent content-selection problem.

### 7.2 Multi-agent submodular optimization with different selection variables

The closest multi-agent formal work optimizes **different decision variables** from the one studied here. IMAS² (Shi et al., 2026) selects subsets of sensing agents by maximizing mutual information under conditional independence; it is the nearest true submodular multi-agent guarantee we found, but its objects are agents and trajectories in a Dec-POMDP, not LLM context units. Anaconda (Xu & Tzoumas, 2024) selects communication neighborhoods or links under per-agent resource constraints to preserve decentralized coordination quality. More broadly, multi-agent submodular optimization has studied exclusive allocation or coordination constraints over agents, tasks, or channels (for example Santiago & Shepherd, 2018), whereas our non-exclusive architecture allows the same finding to be projected to multiple agents and therefore reduces the per-round problem to independent per-agent content selection. The mismatch is therefore one of both **granularity** and **budget**: prior multi-agent work typically optimizes agents, links, or channels under coordination or cardinality-style constraints, whereas we optimize content units under explicit per-agent token budgets.

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

A different adjacency comes from learned routing and memory-admission systems. BudgetMem (Zhang et al., 2026), LatentMem (Fu & Zhang, 2026), and Learning to Share (Fioresi et al., 2026) optimize memory routing or sharing policies by learned or reinforcement-style procedures and evaluate them empirically through performance-cost trade-offs. These systems are relevant because they explicitly inhabit the deployed pipeline layer. But they generally do not define a formal objective with provable structural properties, do not specify a theoretically justified proxy layer with stated equivalence conditions, and do not separate policy-learning success from theorem transfer. Other nearby systems miss at a different level of granularity: graph-pruning or agent-importance approaches reduce token cost by acting on communication edges or agents rather than on the context units sent to a specific worker.

The closest published analogue to our target object is DACS (2026), whose registry/focus pattern introduces a candidate-like set of agent contexts, a budget-like cap on registry summaries, and a trigger for temporarily restoring one agent's full context. DACS is therefore important evidence that the missing layer is real. But it still operates at agent-block granularity, lacks a learned or formal value function over context units, and offers no approximation or verification guarantee for per-agent token-budgeted projection.

A further adjacency comes from recent LLM diagnostic frameworks. Yuan, Su, and Yao (2026) propose a three-probe framework for memory-augmented LLM agents that diagnoses retrieval relevance, utilization, and failure modes. Gupta et al. (2025) propose Information Gain per Turn and Token Waste Ratio as information-theoretic diagnostics for multi-turn LLM conversations, including discussion of handoff or escalation under sustained low information gain. These are important contemporaneous precedents, but they operate at different epistemic layers: Yuan et al. diagnose **pipeline bottlenecks**, and Gupta et al. diagnose **dialogue-channel information flow**. By contrast, our protocol diagnoses **selector structure** and then asks how that structural diagnosis should and should not transfer through the proxy and pipeline layers. More broadly, these runtime-oriented works motivate viewing modern agent systems as layered runtimes with distinct planning, memory, evaluation, and execution roles, within which dispatch-time context projection can be isolated as a separable control problem.

Finally, PID- and interaction-information-based feature-selection work provides methodological context for our pairwise interaction diagnostic. Wollstadt, Schmitt, and Wibral (2023) use a PID-informed information-theoretic framework to distinguish redundancy and synergy in feature selection. This is a useful antecedent for the instrument level of Diagnostic 2, but not a deployment-facing bridge statement or escalation framework for token-budgeted context selection. In adjacent Shannon information-gain settings, the connection can be taken one step further: Hübotter, Sukhija, Treven, As, and Krause (2024) relate redundancy-versus-synergy structure to a weak-submodularity parameter for active-learning objectives and thereby provide the closest formal antecedent to the present discussion. We nevertheless treat that result as adjacent rather than directly transferable, because our formal object is predictive V-information and our deployed diagnostics are defined at the proxy and pipeline layers rather than as direct evaluations of the Shannon-information objective.

Taken together, the prior literature covers proxy-valued context scoring, formal objective plus calibration, routing and memory systems, learned policies, and adjacent diagnostic frameworks. We are not aware of prior work in LLM context selection or routing that simultaneously **(i)** makes an explicit three-layer separation between formal objective, proxy measurement, and heuristic pipeline, **(ii)** states the conditions under which the theorem-level story does or does not transfer across those layers, and **(iii)** treats the pipeline-versus-proxy gap as a first-class object of verification and escalation.

### 7.4 Structured extraction and faithfulness

The most relevant adjacent literature falls into three groups. First, orthogonal structured-action benchmarks such as BFCL (Patil et al., 2025) and ToolBench (Qin et al., 2023) evaluate function-call correctness and API-chain execution rather than free-form-to-structured extraction completeness. Second, structured-output benchmarks such as SLOT (Shen et al., 2025) and KIEval (Khang et al., 2025) improve schema-accuracy evaluation, content-fidelity evaluation, and application-centric correction-oriented evaluation, but they do not report separate completeness rates for simple versus complex findings as a diagnostic test of uniformity. Third, adjacent faithfulness work — including Peters and Chin-Yee (2025) on overgeneralization, CRANE (Banerjee et al., ICML 2025) on constrained-generation limits, FABLES (Kim et al., COLM 2024) on long-form faithfulness failures, and FActScore (Min et al., EMNLP 2023) on atomic-fact factuality — supports the broader concern that qualification-heavy, reasoning-intensive, or indirectly supported content is especially vulnerable during reformulation.

Taken together, these literatures establish value-weighted evaluation, fine-grained factuality analysis, and structured-output benchmarking as important adjacent traditions. To our knowledge, however, prior work does not audit **free-form-to-structured extraction** by reporting separate per-stratum completeness rates in order to test whether high-value or complex findings are disproportionately lost during reformulation — the gap our evaluation protocol addresses.

Across the adjacent literatures surveyed in this section — single-agent budgeted selection, multi-agent optimization over agents or links, learned proxy-level routing or memory systems, and adjacent diagnostic and extraction-evaluation frameworks — the same pattern emerges. Our contribution lies at their intersection: a formal value function for **per-agent content selection** under heterogeneous token budgets, conditional structural theory for that formal object, an explicit bridge statement separating theorem, proxy, and runtime layers, and a measurable proxy-regime labeling protocol for deciding when monitored greedy-style selection is credible.

The gap is therefore not the absence of multi-agent scheduling mechanisms, but the absence of a formal context-allocation object inside those mechanisms.

---

## 8. Discussion and Future Work

The present paper stops at a formal, per-round selector and a calibrated proxy-regime labeling interface. The natural next step is not to replace that selector with an unscoped whole-session theory, but to embed it more tightly in richer runtime settings with better state, quality control, and adaptation.

**Runtime statefulness.** A natural next step is scheduler–selector co-design: a scheduler that consumes two-axis labels from the context-projection layer when deciding whether to activate additional agents, block, retry, escalate model tier, or terminate. We leave this feedback loop to future work.

**Open Problem 1: V-information submodularity.** The central open theoretical question is whether V-information with bounded neural network families satisfies approximate submodularity on non-pathological distributions. For Shannon MI, conditional independence implies exact submodularity (Krause & Guestrin, 2005). V-information breaks the chain rule that underpins this proof, and restricting $V$ reshapes the interaction structure in both directions: suppressing synergies $V$ cannot exploit while potentially creating artificial interactions. Resolving this question would upgrade Condition A from an architectural argument to a theorem.

**Open Problem 2: Interaction-to-ratio transfer for diagnostics.** The pairwise interaction coefficients in Theorem 1 invite comparison to co-information and interaction-information quantities, and more broadly to the redundancy/synergy vocabulary of partial information decomposition (Williams & Beer, 2010; Wollstadt, Schmitt & Wibral, 2023). The residual open problem is to determine whether an analogue of the interaction-to-$\gamma$ connection can be derived for predictive V-information, or for restricted predictive families under which such a bridge holds approximately.

**Calibration and policy search.** The calibration architecture assumes that a lightweight model may approximate CI Value or log-loss marginal estimates from pipeline signals. The offline-to-online transfer pattern demonstrated by EvolKV (Yu & Chai, 2025) for KV cache budget allocation could be applied to evolving scoring pipeline parameters, diagnostic thresholds, and escalation policies. Such adaptation must respect the fixed-within-epoch reference distribution and drift-sentinel rules of Section 4.4.

**Synthetic benchmark execution and replay.** The benchmark in Section 4.3.1 is the minimal empirical anchor. Executing it under the pre-registered validity table would establish whether the diagnostic stack has structural validity on controlled regimes. A subsequent offline replay pilot over real dispatch traces would test whether the bridge, proxy, and runtime artifacts behave under realistic workflow distributions.

**Extraction metadata and machine-auditable runtimes.** A practical next step is to enrich the extraction gate and projection artifacts with lightweight runtime metadata derived from upstream free-form reasoning, such as confidence tags, conflict markers, or coarse compression diagnostics. Such signals may support automated monitors, replay triage, or coarse routing policies over auditable runtime states. In the current paper, these signals are future proxy-layer instrumentation rather than extensions of the theory.

**Sprint A execution.** The value-stratified evaluation protocol (Section 5.3) is designed but not yet executed. The three numbers ($p_{simple}$, $c_{high}$, $c_{low}$) will either validate the uniformity assumption or provide the correction factor for the extraction bridge risk.

**Runtime evolution.** Future work could formalize asynchronous "reflection" operations. By strictly replacing a set of highly correlated findings with a single consolidated reflection within the candidate pool $M$, such an operation could theoretically reduce the supermodular degree $d$. As architectures evolve towards Multi-Head Latent Attention, shifting the selection space from discrete text tokens to compressed latent vectors could also redefine the budget constraint from token count to latent vector count.

## 9. Limitations

Nine limitations bound the claims in this paper.

First, the theory defines the value set function using V-information, but the diagnostic protocol estimates marginal gains through CI Value, replay, or production-utility finite differences. Full V-information-calibrated diagnostics apply only under log-loss evaluation or a validated utility-to-log-loss bridge; otherwise, the diagnostics are operational-utility-only signals and must not be reported as evidence about the formal V-information regime.

Second, the metric bridge can be expensive. Stratified calibration of $\zeta_s$ may require hundreds to thousands of evaluated blocks per stratum, with repeated decoding or evaluation replicates when output variance is high. For pass/fail or rubric-style metrics, effect sizes are often small enough that operational-utility-only labeling may be the only feasible deployment mode.

Third, the evidence for value-dependent extraction bias (Section 5) comes from the summarization and constrained generation literatures, not from direct measurement of extraction gate behavior. The value-stratified evaluation protocol is designed to resolve this; its execution is deferred to future work.

Fourth, the synthetic benchmark is specified as the structural-validity floor, but execution and reporting remain required empirical work. If oracle-layer synthetic regimes fail to separate, the diagnostic protocol should be treated as an unvalidated design proposal rather than as a verified proxy-regime labeler.

Fifth, Theorem 1 should be read as a pairwise-regime sharpening result rather than as a general interaction theorem. Its primary absolute-increase form is robust to zero singleton marginals, but the fractional $1/(1+d\delta)$ form applies only inside round-local active contexts. Regimes with essential mediated higher-order dependence remain outside the theorem's clean applicability domain.

Sixth, the decomposition (Observation 3) holds per round. Across rounds, projection choices shape future candidate pools through feedback loops, and scheduler decisions in round $t+1$ may depend on diagnostics produced by the selector in round $t$. The current framework stops at dispatch-time control and does not analyze session-level long-horizon optimality.

Seventh, projecting the same high-value finding to multiple agents under non-exclusive allocation can produce redundant downstream outputs. The decomposition result is correct for single-round selection but does not account for cross-agent output coupling across rounds.

Eighth, the extraction gate is a potential attack surface: a malicious or malfunctioning upstream worker could produce outputs designed to survive extraction with artificially high importance scores. The dual-gate admission policy provides structural mitigation, but adversarial robustness of the selection pipeline is not analyzed.

Ninth, the runtime-interface requirements presume observability that some hosted frontier runtimes may not expose, including excluded candidates, materialization order, bridge calibration state, and replay-compatible evaluation traces. In such systems the protocol can still guide design, but it cannot certify proxy-regime labels without the required artifacts.

We do not claim to propose an optimal scheduler, solve the critical-path problem, establish multi-agent superiority over single-agent systems, or provide system-level correctness guarantees. The paper formalizes the context-allocation sub-layer that arises when an orchestrator-worker runtime has already chosen to dispatch a worker.

---

## 10. Broader Impact

Improved context assembly can reduce computational waste from redundant or irrelevant context in multi-agent LLM systems — the 53–86% token duplication measured by AgentTaxo represents significant wasted inference cost. The revised protocol is intentionally conservative: it distinguishes V-information proxy labels from operational-utility-only labels, records metric-bridge status, and requires ambiguity when bridge, cascade, or sample evidence is insufficient.

The main risk is false confidence. Formal guarantees over the V-information objective do not automatically transfer to heuristic pipelines, production metrics, or biased candidate pools. The MetricBridgeWitness, block-ratio LCB, extraction audit, and pre-registered synthetic benchmark validity gate are designed to make such gaps visible rather than to eliminate them. Practitioners should verify proxy alignment before relying on any diagnostic for operational decisions.

---

## 11. Conclusion

We have formalized context projection selection as monotone set-function maximization under token-budget constraints, formalized the independence of the submodularity ratio and supermodular degree in the $(\gamma,d)$ coordinate system, and derived a pairwise-regime lower bound that is robust to zero singleton marginals through an absolute-increase parameterization. The fractional $1/(1+d\delta)$ form survives only as a round-local active-context corollary.

The deployment contribution is correspondingly modest and explicit. The protocol does not verify true deployment-time V-information weak submodularity in general. It provides conservative proxy-regime certification when the metric bridge is valid, and operational-utility escalation signals when it is not. The immediate next empirical steps are to execute the pre-registered synthetic regime benchmark, run an offline replay pilot on real dispatch traces, and perform the value-stratified extraction audit. The central open theoretical question — whether V-information with bounded neural network families is approximately submodular on natural language distributions — remains the key target for upgrading Condition A from an architectural argument to a formal guarantee.

---

## References

Anthropic (2025). Effective Context Engineering for AI Agents. Anthropic Engineering blog.

Bai & Bilmes (2018). Greed is Still Good: Maximizing Monotone Submodular+Supermodular Functions. ICML.

Banerjee et al. (2025). CRANE: Reasoning with Constrained LLM Generation. ICML.

Bian, Buhmann, Krause & Tschiatschek (2017). Guarantees for Greedy Maximization of Non-submodular Functions with Applications. ICML.

Chase (2025). The Rise of Context Engineering. LangChain Blog.

Das & Kempe (2018). Submodular meets Spectral: Greedy Algorithms for Subset Selection, Sparse Approximation and Dictionary Selection. JMLR 19(1).

Deng, Shen, Pei, Chen & Huang (2025). Influence Guided Context Selection for Effective Retrieval-Augmented Generation. NeurIPS 2025 poster / OpenReview.

Elenberg, Khanna, Dimakis & Negahban (2018). Restricted Strong Convexity Implies Weak Submodularity. Annals of Statistics 46(6B), 3539–3568.

Reddy, Walker, Ide & Bedi (2026). Draft-Conditioned Constrained Decoding for Structured Generation in LLMs. arXiv.

Feige & Izsak (2013). Welfare Maximization and the Supermodular Degree. ITCS.

Feldman & Izsak (2014). Constrained Monotone Function Maximization and the Supermodular Degree. APPROX.

Fioresi et al. (2026). Learning to Share: Multi-Agent Shared Memory via Reinforcement Learning. arXiv.

Fu & Zhang (2026). LatentMem: Latent Memory for Task-Aware Context Propagation. arXiv.

Min et al. (2023). FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation. EMNLP.

Nenkova & Passonneau (2004). Evaluating Content Selection in Summarization: The Pyramid Method. HLT-NAACL 2004.

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

Liu et al. (2025). RCR-Router: Efficient Role-Aware Context Routing for Multi-Agent LLM Systems with Structured Memory. arXiv.

METR (2025a). Measuring AI Ability to Complete Long Tasks. METR research report.

Nanda et al. (2025). InSQuaD: Submodular Mutual Information for In-Context Learning Exemplar Selection. EMNLP 2025 Findings.

Peters & Chin-Yee (2025). Generalization Bias in Large Language Model Summarization of Scientific Research. Royal Society Open Science 12(4):241776.

Santiago & Yoshida (2020). Weakly Submodular Function Maximization Using Local Submodularity Ratio. ISAAC 2020.

Rezazadeh et al. (2025). Collaborative Memory for Multi-Agent Systems. arXiv.

Santiago & Shepherd (2018). Multi-Agent Submodular Optimization. APPROX.

Shi et al. (2026). IMAS²: Joint Agent Selection and Information-Theoretic Coordinated Perception in Dec-POMDPs. AAMAS.

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

Zhang et al. (2026). BudgetMem: Budget-Aware Memory Routing for Multi-Agent Systems. arXiv.

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
