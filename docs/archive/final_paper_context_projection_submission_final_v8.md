# Context Projection Selection in Multi-Agent Systems: Conditional Theory, Bridge Statement, and Measurable Verification

---

## Abstract

We study dispatch-time context projection selection in multi-agent systems. We formalize it as a per-round, per-agent token-budgeted subset selection problem, where each agent's objective is defined by predictive V-information: the reduction in minimum achievable log-loss given selected context under a fixed predictive family. Frontier deployments are increasingly runtime- and session-oriented, but this paper isolates the dispatch-time context-projection layer as the narrowest formally analyzable and operationally diagnosable slice of that broader setting.

Our theoretical results are conditional. Under explicit objective-level conditions, including an approximate-submodularity regime hypothesis and a pairwise-additive complementarity model, we prove structural results for the formal objective: the independence of the submodularity ratio $\gamma$ and the supermodular degree $d$, and a lower bound relating $\gamma$ to $d$ and the maximum pairwise interaction strength. In this regime, greedy-style approximation guarantees have formal meaning.

We do not prove the key regime hypothesis for deployed frontier models. Instead, a second core contribution of the paper is an explicit bridge statement separating the formal objective, the proxy measurement layer, and the runtime heuristic layer. Our deployment-facing contribution is therefore a verification protocol: three measurable diagnostics computed from production traces or offline replay that estimate whether the current deployment is operating in a greedy-valid regime, and an escalation policy that switches to more robust selection procedures when it is not. In deployment, the result is verification, monitoring, and escalation — not theorem inheritance.

Finally, we isolate a separate bridge risk between the formal objective and end-to-end performance. The formal guarantees apply to optimization over the extracted candidate pool $M$, not the underlying information space $M^*$. We therefore treat extraction quality as a testable end-to-end bottleneck, not as an extension of the weak-submodular guarantee, and specify a value-stratified audit protocol to measure whether extraction failures disproportionately remove high-value findings.

## 1. Introduction

Multi-agent LLM systems often fail not because the underlying model lacks capability, but because the wrong information is projected into the wrong agent at the wrong time. Chase (2025) argues that many agent failures are context failures rather than model failures. Anthropic frames this as a context-engineering problem: curating the smallest possible set of high-signal tokens under a finite attention budget. METR (2025a) reports that current frontier agents achieve almost 100% success on tasks taking human experts less than 4 minutes, but less than 10% success on tasks taking more than around 4 hours. AgentTaxo (Wang et al., 2025a) measured 53–86% token duplication across multi-agent systems, and AgentDropout (Wang et al., 2025b) showed that *removing* context can improve performance. Together, these observations suggest that current systems often suffer from context pollution, not just context scarcity.

Existing frontier runtimes already expose multiple surfaces for shaping what a subagent sees — prompt strings, handoff histories, memory retrieval, structured state placeholders, and truncation or summarization hooks — but they typically leave the actual selection rule heuristic and implicit. In practice, token limits are often treated as truncation constraints rather than as optimization constraints, and context construction remains governed by natural-language reasoning, positional filters, or developer callbacks. What remains missing is a unified formal object for per-agent context allocation: an explicit candidate set, an explicit budget, and a value function over subsets. This paper formalizes that sub-layer.

Recent million-token architectures provide an existence proof that context selection is irreducible rather than obsolete: even when extreme context budgets are available, practical systems still rely on compression, sparse access, and locality-preserving retention rather than uniform dense processing. Our work studies the runtime-level analogue of this irreducible selection problem under explicit token budgets and per-round dispatch.

These observations motivate a precise question: given a budget of $B$ tokens and a candidate pool $M$ of $|M| \gg B$ context items produced by a multi-agent system, which subset $S_i^* \subseteq M$ of **content items** should be projected into each worker agent's context window to maximize task performance? This is the **context projection selection problem** studied in this paper. The problem is agent-heterogeneous, token-budgeted, and non-exclusive: the same finding may be valuable to multiple agents and may be projected to multiple downstream contexts.

**Terminology.** We distinguish four related concepts. *Context projection* is the end-to-end process of assembling a token sequence for an agent. *Context selection* is the subset optimization at the core of projection. *Context engineering* (Chase 2025, Anthropic 2025) is the broader design discipline encompassing selection, ordering, formatting, and prompt structure. *Context routing* refers to directing items to specific agents, which in our non-exclusive setting reduces to independent per-agent selection. The selection variable matters: unlike adjacent multi-agent formulations that choose which agents to activate or which communication links to instantiate, we study which **content items** each agent should receive.

**Positioning.** This paper does not propose a whole-session theory of agent behavior. Frontier deployments are increasingly runtime- and session-oriented, but we study a narrower problem: the **dispatch-time context-projection layer** that determines which content items from a candidate pool $M$ should be projected into an agent's window at a given round. This selector is a **myopic control law embedded in a larger runtime**, not a whole-session scheduler. We focus on this layer because it is the narrowest slice of the runtime that is both formally analyzable and operationally diagnosable. We therefore do **not** claim to solve orchestration, scheduling, or system-level coordination in multi-agent runtimes; our claim is that, in the orchestrator-worker regime where such runtimes are actually deployed, per-agent context allocation is a distinct and currently under-formalized sub-layer.

We assume an enclosing orchestrator-worker runtime in which a scheduler decides which worker is activated, when, and with what task description. This paper does not study that scheduler. It studies the distinct downstream subproblem: what token-budgeted context subset the dispatched worker should receive.

**Paper contract.** This paper makes three commitments. **Formal contract:** we define a formal value function for **per-round, per-agent content selection** using predictive V-information, and all approximation statements in the paper apply to this formal object. **Bridge contract:** deployed systems do not optimize this formal object directly; they use proxies and heuristics, so deployment does not automatically inherit theorem-level guarantees. **Failure contract:** when the key regime condition fails, the theory becomes non-applicable, but the verification protocol, escalation policy, and extraction audit remain operationally useful. A second core contribution of the paper is the explicit bridge statement in Section 3.4, which separates the formal object, the proxy measurement layer, and the runtime heuristic layer.

**Multi-agent scope guard.** Multi-agent execution is used here only to induce heterogeneous context requirements across agents. We do not study which agents to activate, when to activate them, or how to coordinate them.

**Scope.** All theory and diagnostics in this paper are defined at the **per-round dispatch snapshot** level. We do not analyze session-level long-horizon effects in which current projection decisions reshape future candidate pools through planning, tool use, or downstream agent interactions. Instead, we treat those cross-round effects as properties of the enclosing runtime, and we expose the state summaries and audit interfaces required to make subsequent dispatch rounds monitorable and auditable. Nor do we claim that orchestrator-worker runtimes are universally superior to strong single-agent alternatives; we study the context-allocation problem in the regime where such runtimes are in fact used.

**Approach.** The theoretical results in this paper are conditional on Condition A (Section 3.1): that V-information-based context value is approximately submodular, or at least weakly submodular with a nontrivial submodularity ratio, for the deployed model family on the target distribution. We do not prove Condition A — it is the central open question (Section 8). Instead, we derive what follows when it holds and specify a diagnostic protocol that estimates from data whether a deployment is operating in a regime where greedy-style reasoning is justified. This makes the paper a **conditional theory + verification protocol** paper rather than a closed end-to-end theory of deployed systems.

**Contributions.** We contribute a regime-aware framework organized around a single core line.

1. **Core contribution — formalization + conditional theory + bridge statement + measurable verification.** We formalize **per-round, per-agent content subset selection under heterogeneous token budgets** as token-budgeted set-function maximization under a predictive V-information objective. The decision variable in our formulation is the subset of content items projected into each agent's context, distinguishing our setting from single-agent partitioning formulations and from multi-agent formulations whose decision variables are agents or communication links. We then derive conditional weak-submodular structural results for that formal object, make explicit the bridge from the formal objective to proxy measurement and runtime heuristics, and pair this bridge with a measurable verification protocol that detects whether a deployment is operating in a greedy-valid regime.

2. **Supporting contribution A — structural theory.** We prove that the submodularity ratio $\gamma$ and supermodular degree $d$ are independent for general monotone set functions, and derive a conditional lower bound relating $\gamma$, $d$, and maximum pairwise interaction strength under pairwise-additive complementarity.

3. **Supporting contribution B — runtime interfaces and extraction QA.** We specify the minimum auditable runtime interfaces required by a verifiable deployment setting, including dispatch artifacts and state summaries, and we isolate extraction quality as a separate bridge-risk bottleneck with a value-stratified audit protocol. These support layers make the verification protocol executable, but they are not parallel theory claims.

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

The submodularity ratio γ (Das & Kempe, JMLR 2018) measures the worst-case ratio of the sum of singleton marginal gains to the joint marginal gain. When γ = 1, the function is submodular and greedy achieves (1 − 1/e) ≈ 63.2% of optimal. When γ < 1, greedy achieves (1 − e^{−γ}) × OPT — a gracefully degrading guarantee.

This subsection is an **assumption layer**, not a proof layer. Its role is to define the regime hypothesis used by the theory, explain why that hypothesis is plausible enough to study, distinguish supporting evidence from proof, and identify the settings where it is most likely to fail.

We organize the regime assumptions into three conditions:

**Condition A (regime hypothesis): approximate diminishing returns for the formal value object.** The central hypothesis of the paper is that the V-information value function for context projection is approximately submodular, or at least weakly submodular with γ bounded away from zero, for the deployed model family on the target task distribution. Operationally, this means the marginal gain of adding a finding usually decreases as the context set becomes more informative.

Condition A is worth studying for three reasons. First, for Shannon mutual information, conditional independence is sufficient for exact submodularity (Krause & Guestrin, 2005), so the hypothesis has a clean information-theoretic ancestor. Second, V-information approaches Shannon-style behavior in the limit where the predictive family becomes sufficiently expressive, while restricted predictive families can suppress high-order synergies the model cannot exploit. Third, in practical context-projection settings many findings are partially redundant or only weakly complementary, which makes a diminishing-returns approximation plausible enough to motivate formal analysis.

The available evidence is **supporting, not proving**. Empirical evidence from multi-hop QA suggests that performance degrades as interactions deepen: Wu et al. (2024) found that GPT-4 performance drops from 62.8 F1 at 2 hops to 53.5 F1 at 4 hops on the IRE benchmark, with the steepest degradation at the 3-hop boundary. On MuSiQue (Trivedi et al., 2022), single-paragraph models achieve about 65 F1 on 2-hop questions but only about 32 F1 on composed multi-hop questions. These results support the idea that pairwise or weakly higher-order interaction models may often be adequate, but they do not prove that V-information itself is approximately submodular.

Mechanistic intuition points in the same direction without closing the proof gap. Wang et al. (2026) show that in a single-layer Transformer, contextual correction decomposes additively across context items, and that multi-item effects are mediated through an attention-weighted aggregate. This suggests two damping forces on complementarity — attention-weight dilution and a low-dimensional aggregation bottleneck — which make pairwise-additive interaction models plausible as an approximation. But this remains a mechanistic analogy, not a derivation of V-information submodularity bounds.

Condition A is most likely to fail in settings with essential higher-order dependence: deep multi-hop reasoning chains, tightly coupled prerequisite bundles, tool outputs that are individually uninformative but jointly decisive, or deployment shifts where the evaluated model tier no longer matches the effective predictive family. These are precisely the cases where the diagnostics in Section 4 should detect low γ̂, elevated synergy, or instability and trigger escalation.

**Condition B: Bounded redundancy within topic clusters.** When findings with overlapping metadata have high pairwise embedding similarity, redundant findings contribute diminishing marginal value. This creates strong local submodularity within topic clusters. The submodularity ratio γ within a cluster is empirically close to 1.

**Condition C: Bounded complementarity degree.** When the number of findings participating in synergistic interactions with any single finding is bounded by a constant d, the interaction graph is combinatorially sparse. This sparsity alone does **not** imply a lower bound of the form γ ≥ 1/(1 + d·δ_max); it only supplies one structural ingredient for such a bound.

**Condition C' (pairwise-additive complementarity).** Theorem 1 additionally assumes that complementary effects aggregate in a pairwise-additive way:
\[
\Delta f(x \mid L \cup S) \le \Delta f(x \mid L)\Bigl(1 + \sum_{y\in S}\delta(x,y\mid L)\Bigr).
\]
This assumption is load-bearing. It rules out uncontrolled higher-order cross terms in the telescoping expansion and is what makes the degree-and-strength lower bound possible. Theorem 1 should therefore be read as a **pairwise-regime sharpening result**, not as a general higher-order interaction theorem.

Bai and Bilmes (2018) Lemma J.1 establish the adjacent bound γ ≥ 1 − κ^g for BP-decomposable functions, where κ^g is the supermodular curvature of the supermodular component, and show via an explicit construction that this bound can be loose: a monotone supermodular function with κ^g = 1 can still have γ arbitrarily close to 1. Their example occupies the analogous corner of the (γ, κ^g) parameter space. We formalize the parallel independence between γ and the combinatorial supermodular degree d (Feige & Izsak, 2013), which is the operative structural parameter for our pairwise-additive regime.

**Proposition 2 (Independence of γ and d).** For general nonnegative monotone set functions, the submodularity ratio γ and the supermodular degree d are independent: neither bounds the other. A function with d = 1 can have γ → 0 (one pair with arbitrarily strong synergy), and a function with d = n−1 can have γ → 1 (every pair interacts but each interaction is vanishingly small). (Constructions in Appendix A.) This is why the Feige & Izsak (ITCS 2013) framework (which bounds approximation via d alone) and the Das & Kempe (JMLR 2018) framework (which bounds via γ alone) cannot be unified without additional structure such as the pairwise-additive assumption of Theorem 1.

**Definition.** The *maximum pairwise interaction strength* δ_max = max_{x,y,L} max(0, [Δf(x | L ∪ {y}) − Δf(x | L)] / Δf(x | L)) measures the largest fractional increase in any item's marginal value due to the presence of any single other item, over all contexts.

**Theorem 1.** In the pairwise-dominated regime defined by Conditions C and C', let f be nonnegative monotone with supermodular degree d and maximum pairwise interaction strength δ_max, and suppose complementary interactions are pairwise-additive (the marginal gain of adding x to L ∪ S is bounded by Δf(x | L) × (1 + Σ_{y ∈ S} δ(x, y | L))). Then γ ≥ 1/(1 + d · δ_max).

*Proof sketch.* Each term in the telescopic expansion of the joint marginal gain is bounded by the standalone marginal times (1 + min(i−1, d) · δ_max). Summing and taking the ratio gives the bound. The simplified bound introduces a factor-of-2 slack at d = 1; the tighter, non-coarsened form in Appendix B matches Construction 1 exactly. For general d, the simplification min(i−1, d) ≤ d introduces additional slack and makes the theorem statement conservative. A full proof appears in Appendix B.

**Corollary 1 (Higher-order correction under non-amplifying third-order synergy).** Suppose, in addition to the pairwise-additive regime of Theorem 1, that third-order synergy contributes additively without amplifying pairwise interactions — that is, the excess triple interaction can be upper bounded by an independent correction term with count t and maximum strength δ₃. Then
\[
\gamma \ge \frac{1}{1 + d\cdot \delta_{\max} + t\cdot \delta_3}.
\]
This is a conditional higher-order correction, not a general third-order bound. It is conservative when third-order synergy is partially redundant with pairwise synergy, and it should not be applied in mediated-amplification regimes where the triple's value requires pairwise links to be present and thereby amplifies rather than adds to pairwise effects.

**Corollary 2 (Combined bound).** For BP-decomposable functions with supermodular curvature κ^g, γ ≥ max(1 − κ^g, 1/(1 + d·δ_max)), where the first bound is Bai and Bilmes (2018) Lemma J.1 and the second is Theorem 1 of the present paper. The first bound dominates when interactions are uniformly weak across the full ground set, where continuous curvature is the natural parameterization; the second dominates when interactions are sparse but potentially strong, where combinatorial degree plus interaction strength is the natural parameterization. This positioning is complementary to prior guarantees that combine γ with curvature-like parameters (for example Bian et al., 2017) and to degree-based guarantees under more general constraint classes (for example Feldman & Izsak, 2014).

Under pessimistic parameters (d = 3, δ_max = 0.3, t = 5, δ₃ = 0.1), Corollary 1 gives γ ≥ 0.42. Under optimistic parameters (d = 3, δ_max = 0.1, t = 2, δ₃ = 0.05), γ ≥ 0.71.

| Symbol | Definition |
|--------|-----------|
| γ | Submodularity ratio (Das & Kempe): worst-case ratio of sum-of-marginals to joint marginal |
| γ̂ | Post-hoc proxy-layer weak-submodularity diagnostic evaluated on the greedy trace |
| d | Supermodular degree (Feige & Izsak): max pairwise supermodular interactions per item |
| δ_max | Maximum pairwise interaction strength: largest fractional marginal gain increase from any single other item |
| δ(x,y\|L) | Pairwise interaction strength of x and y in context L |
| t | Number of third-order interaction chains (length-3 reasoning chains) |
| δ₃ | Maximum third-order interaction strength (excess synergy beyond pairwise) |

**Worked example.** Consider a data analysis task where a worker receives findings from three upstream workers. Two findings about overlapping market segments interact synergistically (d = 2), with maximum interaction strength δ_max = 0.15 (each finding's marginal value increases by up to 15% when the other is present). Theorem 1 gives γ ≥ 1/(1 + 2 × 0.15) = 1/1.3 ≈ 0.77, yielding a greedy guarantee of (1 − e^{−0.77}) ≈ 54% of optimal. **Failure case:** A 3-hop legal reasoning chain (statute → precedent → application) where the precedent is uninformative without the statute and the application is uninformative without both. The triple's value exceeds the sum of all pairwise values — the third-order synergy δ₃ is large. With d = 2, δ_max = 0.2, t = 1, and δ₃ = 0.5, Corollary 1 gives γ ≥ 1/(1 + 0.4 + 0.5) = 1/1.9 ≈ 0.53, a meaningful degradation from the pairwise-only prediction of 0.71.

At deployment time, the key quantity is a post-hoc trace diagnostic rather than a theorem-level bound on the worst-case submodularity ratio. The a priori bounds from Theorem 1 and Corollary 1 predict what a healthy greedy-valid regime should look like; discrepancies between those predictions and the measured proxy-layer diagnostics are diagnostically informative (Section 4).

**Positioning note.** Under pairwise-additive complementarity, the regime studied here is naturally positioned alongside knapsack problems with pairwise interactions, in a quadratic-knapsack-like sense. This correspondence is structural rather than reformulatory: the budgeted subset-selection interface and the bounded-complementarity parameters align naturally with that family, but the formal objective remains the V-information value function $f_i(S)$, and $\delta_{\max}$ should be read as an interaction-strength analogue rather than as a fixed quadratic coefficient. We use this correspondence only to clarify the interpretation of $d$, $\delta_{\max}$, and the escalation family, not to redefine the formal optimization problem or claim additional approximation guarantees.

### 3.2 Decomposition of the multi-agent problem (Observation 3)

Under non-exclusive allocation and separable per-agent budget constraints, the **per-round** joint problem over K agents with value functions f_1, ..., f_K decomposes into independent per-agent selection problems. The architecture (openWorker, described in Section 6) allows the same finding to be projected to multiple agents, so choosing the optimal S_i* for agent i does not restrict the feasible set for agent j.

This is a **design insight**, not a mathematical advance: the architecture was deliberately chosen to allow non-exclusive allocation, so the per-round joint problem decomposes by design into independent per-agent problems and avoids the multi-agent coordination machinery required in the harder exclusive-allocation case (Santiago & Shepherd, APPROX 2018). This decomposition assumes that the scheduler has already committed to the activated agents in round $t$. It is scope-limited: it does not address scheduler-induced inter-round coupling, future candidate-pool shaping, or downstream redundancy externalities across agents.

### 3.3 Extraction as a bridge-risk model

The candidate pool M is produced by an extraction gate that converts free-text worker outputs into structured findings. Any approximation statement from Section 3 is therefore relative to OPT over M, not over the true information space M*. We model extraction quality as a **separate bridge risk** between the formal objective and end-to-end performance rather than as an automatic extension of the weak-submodular guarantee.

Under a stylized uniformity assumption — namely, that extraction failures are approximately uniform across the value distribution and do not disproportionately remove the support of high-value solutions — one expects degradation to scale roughly linearly with extraction completeness c. We use this stylized picture only as motivation for Section 5's audit protocol; we do **not** claim a general theorem of the form
\[
E[f(S_{greedy})] \ge (1-e^{-\gamma})\cdot c \cdot OPT(M^*).
\]
If the gate disproportionately misses high-value findings, the degradation can be substantially worse than linear. Section 5 therefore treats extraction quality as a **testable bottleneck**, not as a proven extension of the formal approximation guarantee.

### 3.4 Bridge statement: from formal objective to proxy measurement to runtime heuristic

This subsection is the paper's bridge statement and a second core contribution. It fixes the coordinate system for everything that follows by separating the **formal object**, the **proxy**, and the **pipeline**, so that theorem-level claims, proxy-level measurements, and runtime behavior are not conflated.

| Layer | Object | Paper claim |
|---|---|---|
| Formal | V-information set function $f_i(S)$ | Conditional theory |
| Proxy | CI Value / replay marginal estimates | Diagnostic signal |
| Pipeline | retrieval / reranking / MMR / packing | Heuristic only |
| Runtime | artifacts, memory, verification, state summaries | Observability and escalation interface |


**Formal layer.** The object analyzed in Section 3 is the V-information value function f_i(S). All approximation statements, including Theorem 1 and its corollaries, apply to this formal object. They do not directly apply to an implementation that scores items with heuristics.

The formal-to-theorem transfer via a structural condition is an established template rather than a claim of novelty here. Das and Kempe (2018) use the submodularity ratio γ, Elenberg, Khanna, Dimakis, and Negahban (2018) use restricted strong convexity parameters to establish weak-submodularity consequences, and Bian, Buhmann, Krause, and Tschiatschek (2017) combine γ with generalized curvature. What the bridge statement below adds on top of this established template is an explicit **proxy layer**, an explicit **pipeline layer**, a conditional-equivalence analysis with enumerated failure modes, and the stratified diagnostic decomposition used in Section 4.

**Proxy layer.** The diagnostics in Section 4 require evaluating marginal value gains Δf_i(m | S), which are defined at the formal layer. In practice, we estimate these via CI Value (Deng et al., 2025), a leave-one-out method that measures the task-utility change when an item is removed from the selected set. CI Value is therefore a **proxy for marginal utility**, not the formal objective itself.

**Equivalence conditions.** CI Value provides a proxy for selected marginal-utility views of Δf_i(m | S) only when two alignment conditions hold: (a) the predictive family V_i matches the specific model tier used by agent_i, and (b) the utility function is log-loss. Under these conditions, CI Value's leave-one-out evaluation can approximate a finite-difference view of utility change on the evaluated set. We do **not** claim exact equivalence between CI leave-one-out marginals and all trace-time marginals used by the diagnostics in Section 4. If the model tier changes between calibration and production, or the evaluation metric shifts away from log-loss, CI estimates should be read strictly as proxy-layer signals rather than direct evaluations of the formal layer.

**Pipeline layer.** The deployed system uses a heuristic scoring and packing pipeline rather than directly optimizing CI Value or the V-information objective. In other words, the pipeline is not assumed to optimize the proxy; at best, it is expected to correlate with the proxy strongly enough to be useful.

Two recent works propose partial bridge statements at adjacent abstraction levels. Tok-RAG (Xu et al., 2025) establishes a token-level theory in which distribution similarity between the RAG-fused and retrieved-text distributions serves as a theoretically justified proxy for a benefit-versus-detriment gap, and then operationalizes that theory with a per-token switching rule. AdaGReS (Peng et al., 2025) establishes ε-approximate submodularity for token-budgeted context selection under practical embedding-similarity conditions, together with a closed-form instance-adaptive calibration of the relevance-redundancy trade-off parameter. Both are important adjacent precedents, but their epistemic posture differs from the one taken here. First, the proxy-objective relationship in our setting is explicitly **conditional** on a model-tier match and log-loss utility, with concrete failure modes enumerated below, rather than treated as an operational equivalence. Second, the deployed pipeline here is explicitly **not assumed to implement** the theoretical decision rule; the pipeline-versus-proxy gap is itself a first-class object of diagnosis. Third, Section 4 stratifies diagnostics across formal, proxy, and pipeline-versus-proxy layers rather than collapsing them into a single operational test. AdaGReS adapts a trade-off parameter within a single objective family; by contrast, our framework treats regime failure as a first-class deployment event and maps it to explicit escalation across search families.

This distinction matters because the diagnostics do not all measure the same thing:

1. **Formal-layer statements** belong to Section 3 only. They concern f_i(S), γ, d, and δ_max as mathematical objects.
2. **Proxy-layer diagnostics** estimate quantities defined relative to CI-based marginal utilities. The post-hoc γ̂ estimate and the pairwise interaction statistics are in this category.
3. **Pipeline-versus-proxy diagnostics** measure whether the deployed heuristic behaves consistently with the proxy layer. The greedy-versus-augmented gap and any rank-correlation or replay studies belong here.

Three factors limit proxy fidelity even before the pipeline enters the picture:

1. *V_i / log-loss alignment.* The approximation is exact only when the loss function is log-loss and the model tier is fixed. If production uses a different evaluation criterion (e.g., task-specific accuracy), the gap between CI Value and V-information is uncharacterized.

2. *Sample variance.* Leave-one-out evaluation introduces variance from stochastic decoding (temperature > 0). Calibration evaluations should use greedy decoding (temperature = 0) or average over multiple runs per item.

3. *Context position effects.* "Lost in the Middle" positional bias (Liu et al., TACL 2024) means Δf_i(m | S) depends not just on the set S but on the ordering within the assembled context. CI evaluations must therefore use the same materialization ordering as the production pipeline; if the ordering changes, calibration data may not transfer.

These are limitations of the bridge, not of the formal theory. When the bridge fails, the consequences are asymmetric: overestimating γ̂ or proxy fidelity creates silent false confidence, while underestimating them mainly wastes compute through unnecessary escalation.

**Standing assumption for Section 4.** Unless otherwise stated, the diagnostics in Section 4 should be read as proxy-layer or pipeline-versus-proxy measurements, not as direct evaluations of the formal objective. They are meaningful only to the extent that the CI proxy is well aligned with the deployed model tier, evaluation metric, and materialization order.

Accordingly, deployment receives **verification + monitoring + escalation**, not automatic theorem inheritance.

---

## 4. Diagnostic Protocol

Before introducing the three diagnostics, it is useful to distinguish our protocol from two adjacent diagnostic literatures. First, recent LLM-memory work has begun to propose pipeline-level diagnostic frameworks. Yuan, Su, and Yao (2026), for example, study retrieval relevance, memory utilization, and failure modes in memory-augmented LLM agents. Their question is primarily one of **output attribution**: where in the retrieval-to-generation pipeline does failure occur? Second, recent information-theoretic work on multi-turn LLM interaction has proposed dialogue-level diagnostics such as Information Gain per Turn and Token Waste Ratio, together with discussion of handoff or escalation under sustained low information gain. That line measures **dialogue-channel information flow** rather than subset-selection structure.

The protocol in this section operates at a different epistemic layer. Our three diagnostics are **selector-structure diagnostics**: they estimate whether the operative per-round selection problem appears redundancy-dominated, complementarity-heavy, or unstable under proxy evaluation. In a larger runtime, these diagnostics serve as deployment-facing control signals for subsequent dispatch rounds. The purpose of the protocol is therefore not generic pipeline debugging, and not dialogue-efficiency measurement, but **regime detection for context selection**: deciding when monitored greedy-style selection is credible, when the regime is ambiguous, and when escalation to stronger search families is warranted.

### 4.1 Three empirical diagnostics

**Diagnostic 1 — Post-hoc weak-submodularity estimate (γ̂).** The worst-case submodularity ratio γ is information-theoretically hard to compute under the oracle model, so the operational quantity is a data-dependent post-hoc estimate evaluated on an observed greedy trace. This diagnostic is not claimed as a new structural parameter: post-hoc and trajectory-sensitive weak-submodularity analyses are established in the approximation literature. Das and Kempe (2018) provide the core data-dependent guarantee perspective, and Santiago and Yoshida (2020) show that a local submodularity ratio can tighten as the greedy trajectory progresses. A methodologically close curvature-side precedent is Welikala, Cassandras, Lin, and Antsaklis (2022), who introduce an extended greedy curvature that can be computed in parallel with greedy execution and sharpened by additional iterations.

Our contribution here is narrower and deployment-facing. We adapt the post-hoc diagnostic idea to the proxy-evaluation setting of LLM context selection, where repeated evaluations are noisy because of decoding variance and proxy mismatch. The raw trace-local diagnostic is
\[
\hat{\gamma}_{raw} = \min_{m \in S} \frac{\Delta f(m \mid S_{before_m})}{\Delta f(m \mid \varnothing)}.
\]
Operationally, we prefer a lower-confidence quantile estimator rather than the raw minimum:

    γ̂_{q,LCB} = Quantile_q({LCB(r_t)})

where r_t = Δf(m_t | P_{t−1}) / Δf(m_t | ∅), repeated evaluations estimate uncertainty, and the lower confidence bound controls silent overestimation. We use \(\hat{\gamma}\) as a **proxy-layer diminishing-returns diagnostic along the observed greedy trace**. It is operationally useful for regime monitoring, but we do **not** claim that this estimator is literally the Das–Kempe post-hoc bound or a provably tight lower bound on the worst-case submodularity ratio. The quantile-LCB form is preferred in deployment because it is more stable under decoding variance.

**Diagnostic 2 — Pairwise interaction information.** For sampled pairs (m_j, m_k): II = Δf(m_j | ∅) + Δf(m_k | ∅) − Δf({m_j, m_k} | ∅). Positive II indicates redundancy; negative indicates synergy. In deployment or offline replay, we sample from a **top-L candidate slice** rather than uniformly over the full pool, since the selector operates in that region. The sample size is chosen to achieve a target confidence-interval width for the estimated synergy fraction, for example using Wilson-style intervals or Hoeffding-style concentration bounds. In adjacent Shannon information-gain settings, interaction- or synergy-sensitive quantities can have formal connections to weak-submodularity parameters (for example Hübotter et al., 2024); in the predictive V-information setting studied here, however, this diagnostic should still be read as a proxy-layer structural signal rather than as a direct estimator of γ.

**Diagnostic 3 — Greedy vs. augmented-greedy gap.** Compare standard greedy with seeded augmented greedy (enumerate feasible singleton or pair seeds, then greedily complete under the remaining budget). This is more expensive than the default diagnostics and is best treated as a calibration-time measurement rather than a per-round production diagnostic.

**Pre-decision + post-verification.** Strategic selection decisions are made pre-dispatch, but the strongest evidence for those decisions is derived from post-dispatch replay and diagnostics. Post-hoc diagnostics calibrate the policy used for subsequent dispatch rounds.

### 4.2 Decision protocol (provisional, pending calibration)

The three diagnostics determine not only whether the current deployment is operating in a greedy-valid regime, but also which escalation layer is appropriate. The thresholds below remain **initial bins**: they are intended to separate clearly favorable, ambiguous, and escalation-worthy regimes, and should be refit by task class and model tier during calibration.

| Regime | γ̂ estimator | Synergy fraction | Recommended policy | Status |
|--------|--------------|------------------|--------------------|--------|
| Greedy-valid | high | low | **Monitored greedy-style selection** | Initial |
| Ambiguous | medium | moderate | **Seeded augmented greedy** (small-seed enumeration + greedy completion) | Initial |
| Escalate | low | high | **Interaction-aware local search** | Initial |

Escalation in our framework is a **diagnostics-triggered switch** from **monitored greedy-style selection** to progressively stronger search families, rather than a deployment inheritance of the approximation guarantees for the formal objective. When diagnostics place the deployment in a clearly favorable regime, we retain **monitored greedy-style selection** as the default policy. When diagnostics indicate an ambiguous regime, we escalate first to **seeded augmented greedy**, implemented as small-seed enumeration followed by greedy completion under the remaining budget. When diagnostics indicate a clearly complementarity-heavy, non-greedy-valid regime — for example, low $\hat{\gamma}$, elevated synergy fraction, or a large greedy-versus-augmented gap in offline replay — we escalate further to **interaction-aware local search**, used here as a conservative escalation family name rather than as an additional theorem-backed layer. In pairwise-dominated escalation regimes, this stronger layer can be interpreted conservatively as an interaction-aware search family, with seeded completion as a lighter escalation step and local-search-style refinement as the stronger fallback.

The purpose of this protocol is not to convert theorem statements into deployment guarantees, but to use measurable diagnostics to decide when **monitored greedy-style selection** is credible and when escalation is required. The greedy-versus-augmented gap should therefore be read primarily as a calibration-time or replay-time signal for whether the medium layer is sufficient, rather than as a required per-round production diagnostic.

The diagnostics produce regime labels and escalation signals; they do not themselves decide which agents to activate or when to block, retry, or terminate. Those decisions belong to the enclosing scheduler.

### 4.3 Calibration architecture

We treat calibration as a **recommended interface** between the theory and a practical system, not as a fixed deployment recipe. One reasonable operationalization is a two-phase workflow.

**Phase 1 (offline replay).** Assemble a calibration set of representative sessions or dispatch rounds, replay selections under controlled evaluation settings, and compute CI-based marginal-utility estimates. The exact number of sessions, model tiers, and budgets is application-dependent; values such as dozens of sessions per task family are illustrative starting points, not requirements. The purpose of this phase is to estimate proxy fidelity, diagnostic stability, and the empirical relationship between regime labels and downstream quality.

**Phase 2 (surrogate modeling, optional).** If CI-style replay is too expensive for frequent use, train a lightweight surrogate to predict CI-based quantities from pipeline signals such as retrieval scores, reranker outputs, token cost, and redundancy features. The surrogate is useful only if it preserves the regime distinctions needed by Section 4; otherwise it should be treated as an exploratory tool rather than a deployment component.

This interface is intentionally open-ended. It can support a pure experimental setup, an offline calibration study, or a production-facing monitoring stack. What matters is not adherence to a single recipe, but that the calibration layer estimates proxy quality, fits provisional thresholds by task and model tier, and provides a principled basis for escalation decisions.

Before any empirical anchor or Sprint A study is run, at minimum five choices should be fixed rather than left implicit: the deployed **model tier**, the **utility metric**, the **materialization ordering policy**, the **decoding / variance-control policy**, and the **candidate-slice policy** used for pairwise interaction and replay studies. These choices determine whether replay numbers can be interpreted as bridge evidence rather than as artifacts of uncontrolled evaluation settings.

The minimal empirical anchor for Section 4 should therefore be defined narrowly: an **offline replay pilot** or **synthetic regime benchmark** under a fixed task family, fixed budget regime, and fixed evaluation policy. The purpose of this anchor is not to establish broad deployment validity, but to show that \(\hat{\gamma}\), synergy-fraction estimates, and augmented-greedy gaps exhibit regime discrimination under controlled conditions, and that pipeline-versus-proxy behavior can at least be classified as proxy-optimizing enough, partially aligned heuristic, or monitored heuristic only.

### 4.3.1 Synthetic regime benchmark (minimal empirical anchor)

As a minimal empirical anchor for the diagnostic protocol, we propose a **synthetic regime benchmark** over budgeted set functions with known interaction structure. The goal of this benchmark is deliberately narrow. It is **not** intended to establish broad deployment validity, and it is **not** a substitute for an eventual offline replay study on real dispatch traces. Its purpose is to test whether the diagnostics introduced in Section 4.1 exhibit the intended **regime discrimination** under controlled conditions.

The benchmark contains three synthetic families, each generated under a fixed budget regime and evaluated under a fixed proxy-noise policy:

1. **Redundancy-dominated instances.** Findings are organized into clusters of near-duplicates or partial paraphrases. Within a cluster, the first selected item contributes most of the value and subsequent items add only small residual gain. These instances operationalize the diminishing-returns intuition behind Condition B.
2. **Pairwise-synergy instances.** The value function contains sparse pairwise interaction bonuses, with each item participating in at most a bounded number of pairwise complementarities. A convenient form is
   \[
   f(S)=\sum_i w_i \mathbf{1}[i\in S] + \sum_{(i,j)\in E}\beta_{ij}\mathbf{1}[i,j\in S],
   \]
   where the interaction graph degree controls the supermodular degree proxy and the coefficients \(\beta_{ij}\) control the interaction-strength regime. These instances instantiate the pairwise-dominated setting studied by Theorem 1.
3. **Higher-order-synergy instances.** In addition to singleton and pairwise terms, the value function contains sparse triple or prerequisite-chain bonuses,
   \[
   f(S)=\sum_i w_i \mathbf{1}[i\in S] + \sum_{(i,j)\in E}\beta_{ij}\mathbf{1}[i,j\in S] + \sum_{(i,j,k)\in T}	\tau_{ijk}\mathbf{1}[i,j,k\in S],
   \]
   with \(	\tau_{ijk}\) large enough that triple interactions cannot be well explained by pairwise structure alone. These instances lie outside the clean applicability domain of Theorem 1 and are intended to stress-test the escalation logic rather than the theorem.

Each synthetic instance also includes a token-cost vector and a dispatch budget \(B\), so that the evaluation remains aligned with the paper's budgeted selection problem rather than with unconstrained set-function maximization. The benchmark is best run in two layers. At the **oracle layer**, the synthetic value function itself is available, allowing direct comparison of greedy, seeded augmented greedy, and optimal or near-optimal solutions. At the **proxy layer**, noisy or partial marginal estimates are derived from the oracle so as to simulate CI-style evaluation noise and thereby test whether \(\hat{\gamma}\), synergy-fraction estimates, and greedy-versus-augmented gaps remain usable under imperfect measurement.

The benchmark is successful if the three diagnostic families separate the synthetic regimes in the expected direction: redundancy-dominated instances should exhibit high \(\hat{\gamma}\), low synergy fraction, and small greedy-versus-augmented gaps; pairwise-synergy instances should shift these quantities into an intermediate regime and favor seeded augmented greedy over vanilla greedy; and higher-order-synergy instances should trigger low-\(\hat{\gamma}\), high-synergy, large-gap signatures that justify escalation while remaining outside the theorem's clean regime. The intended output of this benchmark is therefore not a single leaderboard number, but a **regime-discrimination table** linking structural family, diagnostic signature, and preferred policy layer.

This benchmark is the most compact empirical anchor consistent with the paper's scope. It does not require a full deployed system, and it does not claim system-level validation. But it does operationalize the central question of Section 4: whether the proposed diagnostics can distinguish when monitored greedy-style selection is credible, when the regime is ambiguous, and when escalation is warranted.

The synthetic regime benchmark should therefore be read as the structural-validity floor of a richer empirical stack. A natural next empirical layer is offline replay over real dispatch traces, which would complement synthetic evaluations by testing the selector under realistic workflow distributions.

### 4.4 What remains if Condition A fails?

Condition A is the regime assumption under which greedy-style approximation language is meaningful for the formal objective. If Condition A does not hold, the weak-submodular justification for greedy selection is no longer applicable, and the approximation-style results in Section 3 should not be interpreted as deployment guarantees.

However, the paper's deployment-facing contribution remains intact. The diagnostics in Section 4 still measure whether observed behavior is redundancy-dominated, synergy-dominated, or unstable under proxy evaluation. The verification protocol still supports operational escalation, for example from **monitored greedy-style selection** to seeded augmented greedy or interaction-aware local search. And the extraction audit in Section 5 remains independently necessary, because even a well-behaved selector over M does not certify end-to-end reliability over the underlying information space M*.

In other words, when Condition A fails, the paper does not claim that greedy remains near-optimal. It instead provides a measurable detection-and-escalation framework that identifies regime mismatch, switches algorithms, and audits bridge risks.

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

This section specifies the **minimum runtime observability requirements** needed to support the verification protocol in Section 4. openWorker is the running instantiation, but the point of Section 6 is not merely to describe one system; it is to state what a runtime must expose if dispatch-time context projection is to be verifiable in practice. The selector studied here is a myopic control law embedded in a larger runtime, so the architectural burden is to make each dispatch round auditable rather than to solve whole-session control in one step. The section should therefore be read as a **runtime interface specification for verifiable context projection**, not just as a system description.

In realistic deployments, the surrounding runtime manages higher-level concerns such as session state, task decomposition, tool execution, memory access, evaluation, correction, and long-term evolution. Existing runtimes already expose partial surfaces for context construction, but they do so heuristically and without a unified formal object. The contribution of the present paper is narrower and more formal: it specifies the context-projection layer that sits immediately before worker dispatch, together with the artifacts and state summaries needed to monitor that layer across rounds.

The ProjectionPlan / BudgetWitness / MaterializedContext chain is intended as a minimal auditable interface for runtime context projection. This role is analogous to how long-context inference systems must specify cache layout and reuse policies in order to make execution replayable and efficient, without these mechanisms being part of the underlying objective.

### 6.1.1 Layering assumption

We model the runtime as four cooperating layers:

1. **Scheduler:** decides the dispatch event $(t, i, q_i, R_i, V_i, B_i)$.
2. **Context-projection layer:** selects $S_i \subseteq M$ under budget $B_i$.
3. **Execution layer:** runs the worker, tools, and model inference.
4. **Verification and observability layer:** audits outputs, records artifacts, and updates runtime state summaries.

This paper specifies the second layer and the audit surface required by the fourth. The scheduler and execution layers are assumed to exist but are not optimized here.

### 6.1.2 Scheduler–selector interface

The selector is not an autonomous scheduler; it consumes a dispatch event and reports auditable outputs back to the surrounding runtime.

Boundary-level retention decisions appear here only as interface signals. They do not introduce a global long-horizon objective into the formal selector.

| Direction | Signal | Meaning |
|---|---|---|
| Scheduler → Selector | $(t, i, q_i, R_i, V_i, B_i)$ | dispatch event |
| Scheduler → Selector | admission policy | which candidates may enter $M$ |
| Scheduler → Selector | synchronization mode | blocking, parallel, retry, abort context |
| Scheduler → Selector | persistence policy by state category | which state types survive turn boundaries or tool boundaries |
| Selector → Scheduler | ProjectionPlan | selected / excluded context items |
| Selector → Scheduler | BudgetWitness | realized token use and trims |
| Selector → Scheduler | $\hat{\gamma}$, synergy fraction | regime diagnostics |
| Selector → Scheduler | regime label | greedy-valid / ambiguous / escalate |

### 6.2 The three-artifact projection chain

A runtime that supports verification should reify context projection into three auditable artifacts.

These artifacts should be designed as **machine-readable audit interfaces** first and human-readable records second: their primary purpose is to support replay, proxy evaluation, trace comparison, and structured downstream audit, rather than informal operator inspection alone.

**ProjectionPlan.** This is the selection-side interface. At minimum it should record: the candidate set considered for the round, the selected candidates, the excluded candidates, per-category budgets or quotas if used, and the scoring configuration that produced the ranking (for example embedding model, reranker model, and MMR parameters). The goal is to make the selector's decision surface inspectable rather than implicit.

**BudgetWitness.** This is the budget-side interface. At minimum it should record: estimated versus realized token counts, section-level trims, exclusion logs for dropped content, tolerance violations, and any cost or overflow bookkeeping used to keep the dispatch within budget. When diagnostics are computed on the realized selection, the witness is also the natural place to attach post-hoc regime measurements such as γ̂.

**MaterializedContext.** This is the realization-side interface. It should record the actual token sequence sent to the worker together with a structural manifest of section ordering, section boundaries, and content inventory. This manifest serves two purposes: it fixes the ordering used by proxy evaluations, and it provides the realized payload against which provenance, traceability, and position-sensitive effects can be audited. KV-cache reuse is not part of the formal objective. It matters operationally because the realized token sequence, ordering, and reusable static prefixes determine both the actual budget witness and the materialization policy under which proxy evaluations are replayed.

### 6.3 Three-stage scoring pipeline

The pipeline is a heuristic approximation to the selection framework in Section 2.2, not a faithful optimizer of the V-information objective:

**Stage 1 — Retrieval + RRF signal fusion.** Bi-encoder cosine similarity, recency decay, and metadata signals fused via Reciprocal Rank Fusion. Approximates ρ_i(m | ∅).

**Stage 2 — Cross-encoder reranking.** Joint (task, finding) scoring capturing token-level interactions. Refines ρ_i(m | ∅).

**Stage 3 — MMR diversity selection + greedy knapsack.** Maximal Marginal Relevance penalizes redundancy with already-selected items — its similarity-based penalty on already-selected items is heuristically aligned with the diminishing-returns intuition of Condition B within topic clusters. The efficiency ratio mmr_score / tokens(m) operationalizes a density-based greedy packing heuristic. The pipeline is a heuristic approximation of greedy set-function maximization, not a faithful optimizer of the V-information objective; the diagnostic protocol (Section 4) monitors whether this heuristic remains sufficiently aligned with the proxy-evaluated regime, and triggers escalation when the pipeline-versus-proxy gap exceeds calibrated tolerance.

### 6.4 Observation-mediated communication

Workers communicate exclusively through structured ObservationPacks — the extraction gate's output. ObservationPacks carry findings, decisions, artifacts, confidence assessments, and provenance metadata. In this paper, memory is treated as an upstream persistence and candidate-generation layer, not as the primary object of formal analysis; richer episodic, semantic, and procedural memory architectures remain outside the theorem's scope. Memory governance is included here only because memory can affect the candidate pool $M$. Memory entries are therefore upstream candidate generators and must be treated as claims requiring verification, not as source-of-truth context. A runtime that aims to support verification should still give memory a **minimal governance model** rather than treating it as opaque background state.

At minimum, long-lived memory should be **typed** into categories such as `user`, `feedback`, `project`, and `reference`, because these classes differ in update frequency, contradiction risk, and downstream use. Memory should also be governed by two operational rules. First, **memory is not the source of truth**: a memory hit that says a file, function, flag, or tool capability exists should be treated as a candidate lead, not as a currently verified fact. Second, memory retrieval should be **selective rather than saturating**: reads should return a candidate subset chosen by relevance, freshness, provenance quality, and contradiction risk, rather than injecting the entire store into the working context.

A minimal write contract follows from this. Long-lived memory should record only information that is not trivially recoverable from the current codebase or runtime state, and categories such as `feedback` and `project` should carry a brief **why it matters / how to apply it** note so that later retrieval is actionable rather than merely archival. The runtime should also define whether entries are merged, superseded, or deleted when newer evidence conflicts with older memory.

From a verification standpoint, the runtime should expose not only the projected artifacts in Section 6.2, but also the **trace interfaces** that explain how those artifacts were produced. At minimum, this includes: the provenance chain from upstream evidence to finding, the side effects of subagents or tools that generated candidate findings, memory read/write/update traces that determine what was available at dispatch time, and extraction-gate outputs that map free-form upstream material into the structured candidate pool.

Three design principles follow. **Dual-gate admission** should separate what enters memory from what is eligible for downstream projection. **Provenance-before-scoring** should ensure that findings are verified before they are ranked or packed. **Verification-before-persistence** should ensure that persistence and downstream reuse happen over data that has already passed schema and provenance checks. The point of these principles is not to prescribe one architecture, but to make the runtime observable enough for the Section 4 diagnostics to operate over verified traces rather than opaque state.

---

### 6.5 Runtime state summaries

To support cross-round stability without breaking the per-round formal core, a runtime should maintain lightweight **dispatch-relevant state summaries** rather than a fully optimized session-level control state. These summaries serve as event-triggered control signals for subsequent rounds.

**Task state.** Goals, subtasks, blockers, and current stage of the session-level goal tree.

**Candidate state.** The current dispatch snapshot $M$, together with coarse statistics such as candidate-pool size, top-$L$ score distribution, and observed redundancy/synergy signals.

**Memory state.** Typed memory summaries, freshness indicators, provenance quality, and contradiction-risk markers for memory items that may enter future candidate pools.

**Quality state.** Recent values of $\hat{\gamma}$, synergy fraction, extraction risk, and other proxy-alignment signals used by the monitoring and escalation logic. Quality state is consumed by the scheduler as a read-only control signal: the context-projection layer reports regime health, but it does not decide whether to spawn more agents, change the synchronization policy, or terminate the session.

These summaries do not redefine the theorem-level object. They are a runtime shell around the dispatch-time selector, enabling subsequent rounds to react to prior diagnostics without collapsing the paper into a whole-session scheduling theory. They support dispatch-to-dispatch adaptation, not a formal optimal scheduler over the full runtime.

### 6.6 Dispatch flow

The following flow is not an architectural prescription. It is a traceability requirement: each step identifies a boundary at which information may be filtered, distorted, truncated, or persisted, and therefore must be auditable if the Section 4 diagnostics are to be meaningful.

The dispatch cycle in a verifiable runtime follows an eight-step flow:

1. **Planner / Memory produce raw observations.** Session-level planning, tool use, and memory retrieval expose raw materials relevant to the next worker dispatch.
2. **Extraction gate filters into structured findings.** Free-form upstream outputs are converted into machine-auditable findings and screened by the dual-gate admission policy.
3. **Candidate pool $M$ is assembled.** The dispatch snapshot is formed from the currently admissible findings.
4. **Selector pipeline ranks and packs findings.** Retrieval fusion, reranking, diversity control, and budgeted packing produce a proposed selection.
5. **Artifacts are reified.** The runtime records a ProjectionPlan, BudgetWitness, and MaterializedContext for the dispatch.
6. **Worker executes the task.** The selected context is sent to the worker agent together with its task instructions and tool interface.
7. **Evaluator computes diagnostics.** Post-dispatch replay and proxy measurements estimate regime health, pipeline-versus-proxy mismatch, and bridge risks.
8. **Planner updates state summaries for the next round.** The resulting signals are written back into the runtime state shell, where they influence subsequent dispatch decisions.

## 7. Related Work

The closest prior art differs from our setting along three axes. First, many systems optimize the wrong **granularity**: agents, links, or memory-routing decisions rather than per-agent context units. Second, many works use the wrong **budget object**: cardinality, dropout rates, compression ratios, or whole-system cost caps rather than per-agent token budgets at per-round dispatch time. Third, many works lack the relevant **guarantee structure**: they provide heuristics, learned policies, or empirical improvements without a formal value function over context subsets and without a bridge statement separating theorem, proxy, and runtime layers. We organize the discussion below around these axes.

### 7.1 Single-agent budgeted context selection

Recent work on context selection has begun to treat prompt assembly as an explicit optimization problem, but almost always for a **single predictive target under a single global budget**. Peng et al. (2025) provide a (1 − 1/e − ε') greedy approximation under ε-approximate submodularity for RAG context selection, using a modular-minus-supermodular objective to model redundancy. InSQuaD (Nanda et al., 2025) applies Submodular Mutual Information to exemplar selection for in-context learning, showing that submodular information objectives can improve retrieval quality for a single downstream model. Sub-CP (Zheng et al., 2025) studies budgeted context partitioning for block-wise in-context learning, again with a single target model and a single total context budget. These papers are the closest single-agent antecedents to our setting, but they do not address heterogeneous per-agent routing of content items across multiple downstream agents.

Wang et al. (2026) provide a complementary mechanistic account of when context helps in single-context Transformers. Their framework operates in output-vector space rather than information-theoretic quantities, and their selection strategy scores items independently rather than reasoning over set composition. We use their results as mechanistic support for pairwise interaction structure, not as a formal solution to the multi-agent content-selection problem.

### 7.2 Multi-agent submodular optimization with different selection variables

The closest multi-agent formal work optimizes **different decision variables** from the one studied here. IMAS² (Shi et al., 2026) selects subsets of sensing agents by maximizing mutual information under conditional independence; it is the nearest true submodular multi-agent guarantee we found, but its objects are agents and trajectories in a Dec-POMDP, not LLM context units. Anaconda (Xu & Tzoumas, 2024) selects communication neighborhoods or links under per-agent resource constraints to preserve decentralized coordination quality. More broadly, multi-agent submodular optimization has studied exclusive allocation or coordination constraints over agents, tasks, or channels (for example Santiago & Shepherd, 2018), whereas our non-exclusive architecture allows the same finding to be projected to multiple agents and therefore reduces the per-round problem to independent per-agent content selection. The mismatch is therefore one of both **granularity** and **budget**: prior multi-agent work typically optimizes agents, links, or channels under coordination or cardinality-style constraints, whereas we optimize content units under explicit per-agent token budgets.

This distinction in **selection variable** is central to our positioning. We do not optimize which agents to activate, which neighbors to communicate with, or which shared channel to open. We optimize which **content items** each agent should receive under its own token budget. DyLAN selects agents; AgentDropout, AgentPrune, and GPTSwarm-style graph methods select communication edges; IMAS² selects sensing agents; Anaconda selects communication neighborhoods. None selects content units within a specific agent's token budget at a specific dispatch round. Query-specific, per-agent content allocation under heterogeneous token budgets is therefore adjacent to, but not the same as, prior multi-agent submodular optimization.

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

Across the adjacent literatures surveyed in this section — single-agent budgeted selection, multi-agent optimization over agents or links, learned proxy-level routing or memory systems, and adjacent diagnostic and extraction-evaluation frameworks — the same pattern emerges. Our contribution lies at their intersection: a formal value function for **per-agent content selection** under heterogeneous token budgets, conditional structural theory for that formal object, an explicit bridge statement separating theorem, proxy, and runtime layers, and a measurable regime-diagnostic protocol for deciding when monitored greedy-style selection is credible.

The gap is therefore not the absence of multi-agent scheduling mechanisms, but the absence of a formal context-allocation object inside those mechanisms.

---

## 8. Discussion and Future Work

The present paper stops at a formal, per-round selector. The natural next step is not to replace that selector with an unscoped whole-session theory, but to embed it more tightly in richer runtime settings with better state, quality control, and adaptation. We therefore organize future work around three threads.

**Runtime statefulness.**

A natural next step is scheduler–selector co-design: a scheduler that consumes regime diagnostics from the context-projection layer when deciding whether to activate additional agents, block, retry, escalate model tier, or terminate. We leave this feedback loop to future work.
This regime-aware escalation perspective is consistent with broader industrial patterns where heterogeneous operating regimes are first handled by specialized policies and only later consolidated.

**Open Problem 1: V-information submodularity.** The central open theoretical question is whether V-information with bounded neural network families satisfies approximate submodularity on non-pathological distributions. For Shannon MI, conditional independence implies exact submodularity (Krause & Guestrin, 2005). V-information breaks the chain rule that underpins this proof, and restricting $V$ reshapes the interaction structure in both directions: suppressing synergies $V$ cannot exploit while potentially creating artificial interactions. No impossibility result exists for bounded $V$, and frontier transformers empirically track Shannon MI interaction structure on natural language. Resolving this question would upgrade Condition A from an architectural argument to a theorem. Specifically, a concentration bound on $|I_V(X_S \to Y) - I(X_S; Y)|$ for transformer families of width $w$ and depth $d$ on natural language distributions would close the gap.

**Attention geometry and submodularity.** Wang et al. (2026) provide geometric conditions under which context helps in Transformers, but their context selection strategy scores items independently (top-1 alignment with the error direction), ignoring set composition entirely. Combining geometric item scoring with set-composition-aware selection is a natural direction. The formal bridge between their attention-weighted value geometry (correction norms, alignment angles) and V-information marginal gains would, if established, provide an architecture-grounded proof that context value is approximately submodular for well-conditioned Transformer models.

**Open Problem 2: Interaction-to-γ transfer for diagnostics.** The pairwise interaction coefficients $\delta$ in Theorem 1 invite comparison to co-information and interaction-information quantities, and more broadly to the redundancy/synergy vocabulary of partial information decomposition (Williams & Beer, 2010; Wollstadt, Schmitt & Wibral, 2023). There is now a close formal antecedent for part of this story in the Shannon information-gain setting: Hübotter, Sukhija, Treven, As, and Krause (2024) define a multiplicative information ratio whose regimes distinguish redundancy-dominated from synergy-dominated configurations and relate the corresponding weak-submodularity parameter to greedy approximation quality. But this does not yet provide a direct formal bridge from PID quantities themselves to the submodularity ratio $\gamma$, and it does not directly transfer to our predictive V-information objective. The obstacle is structural: the Hübotter et al. argument is stated in a Shannon-information setting that relies on chain-rule identities, whereas V-information under restricted predictive families need not preserve those identities. The residual open problem for the present paper is therefore narrower but still genuine: to determine whether an analogue of that interaction-to-$\gamma$ connection can be derived for predictive V-information, or for restricted predictive families under which such a bridge holds approximately.

**Calibration and policy search.** The calibration architecture assumes a lightweight model can approximate CI Value from pipeline signals (Section 4.3). The offline-to-online transfer pattern demonstrated by EvolKV (Yu & Chai, 2025) for KV cache budget allocation could be applied to evolving both scoring pipeline parameters and diagnostic escalation thresholds, as an alternative or complement to the surrogate model approach.

**Runtime quality control.**

**Extraction metadata and machine-auditable runtimes.** A practical next step is to enrich the extraction gate and projection artifacts with lightweight runtime metadata derived from upstream free-form reasoning, such as confidence tags, conflict markers, or coarse compression diagnostics. Such signals may support automated monitors, replay triage, or coarse routing policies over auditable runtime states. However, their relationship to the formal quantities in this paper — including $d$, $\delta_{\max}$, $\delta_3$, or the operative regime diagnostics — remains unformalized. In the current paper, these signals should therefore be understood as future proxy-layer instrumentation rather than as extensions of the theory.

**Sprint A execution.** The value-stratified evaluation protocol (Section 5.3) is designed but not yet executed. The three numbers ($p_{simple}$, $c_{high}$, $c_{low}$) will either validate the uniformity assumption or provide the correction factor for the formal guarantee.

**Runtime evolution.**

**Asynchronous Reflection and Supermodular Degree.** Future work could formalize asynchronous "reflection" operations. By strictly replacing a set of highly correlated findings with a single consolidated reflection within the candidate pool $M$, such an operation could theoretically reduce the supermodular degree $d$. This replacement mechanism would stabilize the submodularity ratio $\gamma$ over long contexts without requiring modifications to the core greedy selection pipeline.

**Latent Space Projection.** As architectures evolve towards Multi-Head Latent Attention (MLA), shifting the selection space from discrete text tokens to compressed latent vectors ($c_t$) could reduce the per-token projection cost and redefine the budget constraint from token count to latent vector count, extending the V-information framework into the continuous domain.

## 9. Limitations

Seven limitations bound the claims in this paper.

First, the theory defines the value set function using V-information, but the diagnostic protocol estimates marginal gains via CI Value. The equivalence is conditional on two assumptions: the predictive family V_i matches the deployed model tier, and the loss function is log-loss (Section 3.4). If production evaluation uses a different criterion, the gap between CI Value and V-information is uncharacterized. The diagnostics measure the right quantity only under these conditions.

Second, the evidence for value-dependent extraction bias (Section 5) comes from the summarization and constrained generation literatures, not from direct measurement of extraction gate behavior. We argue transferability on three grounds (compression target, probability distortion, reformulation overgeneralization), but the magnitude of the bias in the specific extraction setting is unknown. The value-stratified evaluation protocol is designed to resolve this; its execution is deferred to future work.

Third, the evaluation protocol is specified but not executed. The formal framework's assumptions are testable but not yet tested. The three-number characterization (p_simple, c_high, c_low) and the diagnostic protocol's initial threshold bins are proposed based on theoretical analysis and prior literature, not on production data.

Fourth, Theorem 1 should be read as a pairwise-regime sharpening result rather than as a general interaction theorem. Its bound γ ≥ 1/(1 + d·δ_max) relies on a pairwise-additive approximation to complementarity, while Corollary 1 treats third-order effects only as a correction term. Accordingly, the relevant optimization neighborhood is pairwise-interaction knapsack rather than general higher-order interaction maximization, and regimes with essential higher-order dependence remain outside the theorem's clean applicability domain.

Fifth, the decomposition (Observation 3) holds per round. Across rounds, greedy-local projection choices shape future candidate pools through the feedback loop, and scheduler decisions in round $t+1$ may depend on diagnostics produced by the selector in round $t$, such as $\hat{\gamma}$, synergy fraction, or extraction-risk signals. This means the current framework stops at dispatch-time control and does not analyze whether session-level state evolution induces long-horizon myopia — a failure mode where locally optimal projections degrade global session performance. The resulting scheduler–selector feedback loop is a property of the enclosing runtime and is not analyzed by the per-round theory.

Sixth, projecting the same high-value finding to multiple agents under non-exclusive allocation can produce redundant downstream outputs. The decomposition result is correct for single-round selection but does not account for cross-agent output coupling across rounds.

Seventh, the extraction gate is a potential attack surface: a malicious or malfunctioning upstream worker could produce outputs designed to survive extraction with artificially high importance scores. The dual-gate admission policy provides structural mitigation, but adversarial robustness of the selection pipeline is not analyzed.

We do not claim to propose an optimal scheduler, solve the critical-path problem, establish multi-agent superiority over single-agent systems, or provide system-level correctness guarantees. The paper formalizes the context-allocation sub-layer that arises when an orchestrator-worker runtime has already chosen to dispatch a worker.

---

## 10. Broader Impact

Improved context assembly reduces computational waste from redundant or irrelevant context in multi-agent LLM systems — the 53–86% token duplication measured by AgentTaxo represents significant wasted inference cost. Formal guarantees make context selection auditable: the BudgetWitness artifact records what was included and excluded with reasons, and the submodularity ratio γ̂ provides a continuous measure of pipeline health. We do not foresee negative societal implications specific to this work, though we note that formal guarantees may create false confidence if the extraction bottleneck in Section 5 is not accounted for — a 50% guarantee over a biased candidate pool may be worse than no guarantee over a complete one. Additionally, guarantees computed from CI Value estimates may overstate reliability when the production evaluation criterion diverges from log-loss — practitioners should verify proxy alignment before relying on γ̂ for operational decisions.

---

## 11. Conclusion

We have formalized context projection selection as monotone set function maximization under knapsack constraints, formalized the independence of the submodularity ratio and supermodular degree in the (γ, d) coordinate system (Proposition 2), and derived a lower bound that combines combinatorial degree with pairwise interaction strength under pairwise-additive complementarity (Theorem 1). The diagnostic protocol provides practitioners with measurable regime diagnostics rather than untestable deployment assumptions, and the extraction bottleneck identifies a previously under-specified limit on end-to-end system performance. The immediate next step is empirical validation: measuring γ̂ on production data, executing the value-stratified extraction audit, and comparing the scoring pipeline against baselines. The central open theoretical question — whether V-information with bounded neural network families is approximately submodular on natural language distributions — remains the key target for upgrading Condition A from an architectural argument to a formal guarantee.

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

**Theorem 1.** Let f be a nonnegative monotone set function on ground set V with supermodular degree d and maximum pairwise interaction strength δ_max. Suppose complementary interactions are context-dependent pairwise-additive: for all x ∈ V, all L ⊆ V \ {x}, and all S ⊆ V \ (L ∪ {x}),

    Δf(x | L ∪ S) ≤ Δf(x | L) × (1 + Σ_{y ∈ S} δ(x, y | L))

where δ(x, y | L) = max(0, [Δf(x | L ∪ {y}) − Δf(x | L)] / Δf(x | L)). Then γ ≥ 1/(1 + d · δ_max).

**Proof.** Let S = {x₁, ..., x_s} and L be an arbitrary set with S ∩ L = ∅. By the pairwise-additive assumption applied at context L ∪ {x₁, ..., x_{i-1}}:

    Δf(xᵢ | L ∪ {x₁, ..., x_{i-1}}) ≤ Δf(xᵢ | L) × (1 + Σ_{j < i} δ(xᵢ, xⱼ | L))

For each xᵢ, at most d items have δ(xᵢ, xⱼ | L) > 0 (by definition of supermodular degree). Among the items {x₁, ..., x_{i-1}}, at most min(i−1, d) have nonzero interaction with xᵢ. Each such δ is bounded by δ_max. Therefore:

    Δf(xᵢ | L ∪ {x₁, ..., x_{i-1}}) ≤ Δf(xᵢ | L) × (1 + min(i−1, d) · δ_max)

The denominator of the submodularity ratio is:

    Δf(S | L) = Σᵢ Δf(xᵢ | L ∪ {x₁, ..., x_{i-1}})
              ≤ Σᵢ Δf(xᵢ | L) × (1 + min(i−1, d) · δ_max)

Since min(i−1, d) ≤ d for all i:

    Δf(S | L) ≤ (1 + d · δ_max) × Σᵢ Δf(xᵢ | L)

The numerator of γ is Σᵢ Δf(xᵢ | L). Therefore:

    γ = min_{L,S} [Σᵢ Δf(xᵢ | L)] / [Δf(S | L)] ≥ 1 / (1 + d · δ_max)

**Tightness at d = 1.** Construction 1 (Appendix A) gives γ = 2/M with d = 1 and δ_max = M − 2. The simplified bound stated in the theorem yields

    γ ≥ 1 / (1 + 1·(M−2)) = 1 / (M−1),

which is of the same order but does **not** exactly match Construction 1; it introduces a factor-of-2 slack in this case. The exact match is obtained from the tighter, non-coarsened form:

    γ ≥ s / [Σᵢ (1 + min(i−1, d)·δ_max)].

At d = 1 and s = 2, this becomes

    γ ≥ 2 / (2 + δ_max) = 2 / M,

which matches Construction 1 exactly. For general d > 1, the coarsening step min(i−1, d) ≤ d yields the simpler theorem statement at the cost of additional slack. ∎
