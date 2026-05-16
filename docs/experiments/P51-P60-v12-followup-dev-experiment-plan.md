# Mingx v12 Follow-up Development and Experiment Plan: P51-P60

Status: proposed planning document
Project: `mingx`
Primary paper anchor: `docs/archive/context_projection_fixed_v12.md`
Primary repo alignment anchor: `docs/paper-alignment-v12.md`
Current framing: Proxy-Regime Diagnosis
Date: 2026-05-11

---

## 0. Executive summary

The next development cycle should not start by adding another broad experiment. The repo has already completed the P45-P50 scaffold package: bridge-calibration lane, synthetic structural diagnostics, fixture realistic-task benchmark, Phase B replay hardening, extraction audit pilot, and optional `ReprojectionWitness` scaffold. The immediate priority is to make the repo and manuscript converge on the same v12 evidence state, repair stale entrypoints, and then introduce only narrow, claim-gated follow-up experiments.

The recommended next cycle is P51-P60:

| Phase | Short name | Primary purpose | Claim ceiling |
|---|---|---|---|
| P51 | State reconciliation | Make top-level docs, checklist, and current manuscript anchor agree with P45-P50 status | documentation hygiene only |
| P52 | Manuscript integration | Repair proof integrity and integrate P45 negative closure into paper text | manuscript alignment only |
| P53 | Diagnostic contract | Pre-register thresholds, LCB method, ESS gates, and failure-to-ambiguous behavior | protocol scaffold only |
| P54 | New bridge stratum design | Design a materially new bridge-calibration stratum; do not retry `bio_attribute` by inertia | design review only |
| P55 | New-stratum bridge pilot | Run/import a bounded bridge pilot only after P54 approval and operator gating | at most `calibrated_proxy_supported` if gates pass |
| P56 | Replay substrate expansion | Move from fixture replay to imported realistic dispatch traces with full identity/hash binding | replay usability only unless bridge valid |
| P57 | Extraction audit v2 | Add value-stratified extraction audit and human-sentinel protocol | extraction-risk evidence only |
| P58 | Provenance-aware redundancy | Separate duplicate, corroborative, adversarial, and prerequisite overlap signals | operational diagnostic only |
| P59 | Reprojection replay integration | Evaluate re-projection as an auditable intervention, not as deployed improvement | operational audit only |
| P60 | Evidence ledger + manuscript package | Produce final v12 evidence ledger and paper-integration diff | no automatic claim upgrade |

This plan keeps the paper's core object narrow: dispatch-time, per-agent, token-budgeted context projection selection over candidate pool `M`. It does not introduce scheduler optimization, memory admission, communication topology, or a generic multi-agent framework.

---

## 1. Non-negotiable boundaries for the next cycle

### 1.1 Active claim vocabulary

All new paper-facing outputs must use the v12 two-axis diagnostic vocabulary.

Allowed `metric_claim_level` values:

- `vinfo_proxy_supported`
- `calibrated_proxy_supported`
- `operational_utility_only`
- `ambiguous_metric`

Allowed `selector_regime_label` values:

- `greedy_supported`
- `pairwise_escalate`
- `higher_order_risk`
- `ambiguous`

Deprecated labels may appear only as legacy compatibility fields or denied-claim examples:

- `Vinfo_proxy_certified`
- `greedy_valid`
- bare `escalate`
- `measurement_validated`
- deployed V-information verification
- theorem-level deployed submodularity verification

### 1.2 Evidence boundaries

The next cycle must preserve these boundaries:

| Evidence type | May support | Must not support |
|---|---|---|
| synthetic structural artifacts | structural signature checks | bridge evidence, V-information support, measurement validation |
| fixture realistic-task artifacts | workflow/schema/model-adjudication scaffold | paper-grade evidence, human-label validation, kappa |
| replay package completeness | replay usability and auditability | metric support by itself |
| extraction audit fixture | extraction-risk substrate | selector validity or metric bridge support |
| `ReprojectionWitness` fixture | operational audit trail | deployed runtime improvement |
| live API smoke success | operational feasibility | scientific validation or human measurement validation |
| model-adjudicated labels | scalable proxy/adjudication lane | human labels or human-human agreement |

### 1.3 P45 closure lock

The current `bio_attribute` stratum is closed as non-calibrated. Do not expand it into a larger 20-30 row pilot without one of the following:

1. a new active stratum,
2. a materially new fixed-logloss/utility design,
3. a written review explaining why the failed canaries do not apply.

The preserved P45 negative result is useful as fail-closed claim-gate evidence, not as bridge support.

---

## 2. Current state after P45-P50

### 2.1 Implemented scaffold surfaces

The repo currently has scaffold coverage for:

- `ProjectionPlan`
- `BudgetWitness`
- `MaterializedContext`
- `MetricBridgeWitness`
- `ProjectionBundleV1`
- `CounterfactualReplayWitness`
- `ReprojectionWitness`
- synthetic structural benchmark artifacts
- fixture realistic-task benchmark artifacts
- Phase B replay hardening
- fixture extraction audit pilot
- optional re-projection witness pilot

### 2.2 Immediate inconsistencies to resolve

The next cycle starts with document and manuscript reconciliation because several repo entrypoints can still send future agents in the wrong direction.

| Issue | Risk | Phase |
|---|---|---|
| root `README.md` still describes P45 as next priority | new workers may retry closed stratum | P51 |
| `docs/README.md` still describes P45 as next priority and P50 as not preceding P45-P49 | new workers may ignore P45-P50 merged status | P51 |
| `docs/templates/claim-boundary-checklist.md` maps synthetic-only evidence to `vinfo_proxy_supported` | direct claim-boundary violation | P51 |
| GitHub manuscript Appendix B proof is damaged around the pairwise summation | theorem trust risk | P52 |
| GitHub manuscript still frames bridge calibration as future/to-be-measured, not as P45 negative closure | paper/repo evidence-state mismatch | P52 |
| Section 4 policy lacks a compact predeclared threshold/LCB/ESS contract | diagnostics may look underspecified | P53 |

---

## 3. Phase plan overview

### Dependency graph

```text
P51 state reconciliation
  -> P52 manuscript integration
  -> P53 diagnostic threshold contract
  -> P54 new bridge stratum design review
  -> P55 new bridge pilot, only if P54 accepts
  -> P56 replay substrate expansion
  -> P60 evidence ledger / manuscript package

P51 -> P57 extraction audit v2
P51 -> P58 provenance-aware redundancy
P50 existing scaffold -> P59 re-projection replay integration
```

### Stop conditions

Stop and request operator review when a phase requires:

- live API execution,
- credentials,
- human labels,
- human-human kappa evaluation,
- external services,
- license review,
- new scientific claim tier,
- promotion of fixture/synthetic evidence into paper-grade evidence.

---

## 4. P51 — v12 state reconciliation and guardrail cleanup

### Goal

Make the repo's top-level entrypoints reflect the current P45-P50 state and remove direct claim-boundary contradictions.

### Allowed changes

- `README.md`
- `docs/README.md`
- `docs/templates/claim-boundary-checklist.md`
- optional small guardrail tests under `tests/`
- optional review note under `docs/reviews/`

### Required edits

1. Update root `README.md`:
   - replace “P45 is the next priority” with “P45-P50 are completed as evidence/audit scaffold phases.”
   - state that current P45 `bio_attribute` stratum is non-calibrated.
   - state that the next active work is P51 state reconciliation, P52 manuscript integration, and P53 diagnostic contract.

2. Update `docs/README.md`:
   - replace P45-next-priority wording.
   - link the P45-P50 phase summary.
   - mark P45-P50 docs as completed scaffold/reference docs, not current active execution plans.

3. Fix `docs/templates/claim-boundary-checklist.md`:
   - replace `synthetic-only evidence | vinfo_proxy_supported` with `synthetic-only evidence | synthetic_structural_only / ambiguous_metric`.
   - add denied claim: deployed V-information verification.
   - add explicit rule: fixture-only evidence cannot produce `vinfo_proxy_supported` or `calibrated_proxy_supported`.

4. Add guardrail tests if practical:
   - fail if paper-facing docs contain `synthetic-only evidence | vinfo_proxy_supported`.
   - fail if new docs use `measurement_validated` outside denied-claim/legacy contexts.
   - fail if new paper-facing summaries use `Vinfo_proxy_certified` or `greedy_valid` as active labels.

### Suggested checks

```bash
uv run pytest tests/test_revised_framing_guardrails.py
uv run pytest tests/test_projection_artifacts.py tests/test_synthetic_regime_benchmark.py
uv run pytest
```

If full suite is not feasible, record the exact focused checks and why full suite was skipped.

### Exit criteria

- top-level README no longer directs workers to retry closed P45 as the next priority;
- `docs/README.md` treats P45-P50 as completed scaffold phases;
- claim-boundary checklist no longer maps synthetic-only evidence to V-information proxy support;
- guardrail test exists or the review explains why the existing guardrail set already covers it;
- review verdict is `ACCEPT` or `ACCEPT_WITH_NOTES`.

### Claim ceiling

Documentation hygiene only. No evidence claim changes.

---

## 5. P52 — manuscript proof repair and evidence-state integration

### Goal

Bring the manuscript anchor into alignment with the current repo and the corrected uploaded manuscript text.

### Allowed changes

- `docs/archive/context_projection_fixed_v12.md`
- optional manuscript integration note under `docs/paper/`
- optional proof-integrity guardrail test under `tests/`
- review under `docs/reviews/`

### Required edits

1. Repair Appendix B proof integrity:
   - replace the damaged summation around `sum_{j 0` with the correct pairwise telescoping step:

```latex
\Delta f(x_i\mid L\cup\{x_1,\ldots,x_{i-1}\})
\le
\Delta f(x_i\mid L)
+
\sum_{j<i}\eta(x_i,x_j\mid L).
```

   - include the degree cap step:

```latex
\Delta f(x_i\mid L\cup\{x_1,\ldots,x_{i-1}\})
\le
\Delta f(x_i\mid L)+\min(i-1,d)\eta_{\max}.
```

   - include the final summation:

```latex
\Delta f(S\mid L)
\le
A(L,S)+\psi_{s,d}\eta_{\max}.
```

2. Integrate P45 closure into Section 3.4 / 4.7 / 8 / 11:
   - explicitly state that the P45 lane was implemented for the current `bio_attribute` stratum;
   - state that current stratum did not establish a stable utility-to-logloss bridge;
   - preserve the allowed downstream label as `operational_utility_only` or `ambiguous_metric`;
   - state that this is a fail-closed negative result, not bridge support.

3. Update “remaining work” language:
   - do not say one-stratum bridge calibration is entirely unexecuted;
   - say future work is either a materially new stratum or a materially new fixed-logloss/utility design.

4. Tighten `vinfo_proxy_supported` definition:
   - require log-loss alignment plus a fresh fixed-model-to-`V_i` bridge, near-optimality argument, or actual empirical minimization over the declared predictive family;
   - do not allow generic “log-loss aligned” wording to imply formal V-information support by itself.

5. Add proof/string guard if practical:
   - fail if `sum_{j 0` appears in the manuscript;
   - fail if Section 4.7 says all bridge quantities are simply “to be measured” without acknowledging P45 closure.

### Suggested checks

```bash
uv run pytest tests/test_revised_framing_guardrails.py
python -m compileall cps tests
```

If proof-only manuscript edits are made without code edits, focused grep checks may be sufficient, but the review must record that no runtime behavior changed.

### Exit criteria

- Appendix B proof is parseable and complete;
- P45 closure is represented without upgrading claims;
- future-work language is consistent with P45 closure;
- `vinfo_proxy_supported` definition is stricter, not looser;
- no new certification framing is introduced.

### Claim ceiling

Manuscript alignment only. No new empirical evidence.

---

## 6. P53 — diagnostic threshold contract and `MetricBridgeWitness` contract hardening

### Goal

Make the Section 4 diagnostic policy executable as a predeclared audit protocol. This phase should define how thresholds, confidence bounds, effective sample size, and failure-to-ambiguous behavior are recorded.

### Allowed changes

- `docs/protocols/diagnostic-threshold-contract-v12.md`
- `docs/templates/diagnostic-threshold-contract-template.json`
- optional schema/report fields if already present surfaces can be extended without breaking compatibility
- focused tests for serialization and fail-closed defaults
- review under `docs/reviews/`

### Required protocol fields

The contract must require, at minimum:

| Field | Required purpose |
|---|---|
| `contract_id` | stable identifier for the diagnostic contract |
| `calibration_epoch` | ties thresholds to a bridge epoch |
| `active_stratum` | task family, model tier, materialization policy, block size, candidate slice, metric |
| `metric_claim_level_precondition` | allowed metric level before selector labeling |
| `block_size_max` | maximum evaluated block size |
| `signal_threshold` | denominator/numerator activity threshold |
| `ratio_lcb_method` | bootstrap, empirical quantile, t-bound, or explicitly conservative fallback |
| `ratio_quantile` | lower quantile used for block-ratio reporting |
| `ratio_lcb_threshold` | threshold for healthy pair-block ratio |
| `pairwise_excess_threshold` | threshold for positive `E_2` mass |
| `sag_gap_threshold` | threshold for meaningful `G_SAG` |
| `triple_excess_threshold` | threshold for sentinel `E_3`/`omega` |
| `min_effective_sample_size` | fail closed below this sample size |
| `drift_policy` | fresh/stale/ambiguous bridge handling |
| `underpowered_policy` | must downgrade to `ambiguous` or `ambiguous_metric` |
| `fixture_policy` | fixture-only evidence remains paper-ineligible |
| `synthetic_policy` | synthetic-only evidence remains structural-only |

### Required decision logic

The contract should produce a deterministic decision surface:

```text
if metric bridge missing/stale/underpowered:
    metric_claim_level = operational_utility_only or ambiguous_metric
    no vinfo/calibrated claim

if signal denominator below threshold:
    selector_regime_label = ambiguous

if pair ratio healthy and pair excess low and SAG gap small:
    selector_regime_label = greedy_supported

if pair excess high and SAG gap meaningful:
    selector_regime_label = pairwise_escalate

if triple sentinel fires or hidden-synergy conflict appears:
    selector_regime_label = higher_order_risk

if signals conflict or sample is underpowered:
    selector_regime_label = ambiguous
```

### Implementation guidance

- Use deterministic serialization.
- Avoid universal scientific thresholds unless the paper can justify them.
- Prefer stratum-specific thresholds recorded by contract.
- Threshold values may be `null` only if the contract explicitly says the corresponding gate is inactive and the label must fail closed.
- The contract is not bridge evidence; it is a pre-registration/audit artifact.

### Suggested checks

```bash
uv run pytest tests/test_revised_framing_guardrails.py
uv run pytest tests/test_phase_b_replay.py
uv run pytest tests/test_projection_artifacts.py
```

### Exit criteria

- a reusable threshold contract doc/template exists;
- every diagnostic label can be traced to predeclared thresholds or a fail-closed rule;
- underpowered, stale, fixture-only, and synthetic-only cases cannot emit upgraded claims;
- manuscript Section 4 can reference this contract without implying validation.

### Claim ceiling

Protocol scaffold only.

---

## 7. P54 — materially new bridge-calibration stratum design

### Goal

Design, but do not execute, a new metric-bridge stratum that avoids simply rerunning the closed P45 `bio_attribute` lane.

### Allowed changes

- `docs/experiments/P54-new-bridge-stratum-design-v12.md`
- `configs/runs/bridge-calibration-<new-stratum>-dryrun.json`
- optional schema tests for dry-run config validity
- review under `docs/reviews/`

### Required design criteria

A new bridge stratum must specify:

| Component | Required detail |
|---|---|
| `task_family` | concrete task class, not generic “LLM task” |
| `target_type` | categorical, constrained text, exact field, or other logloss-compatible target |
| `model_tier` | fixed evaluated model tier |
| `materialization_policy` | fixed ordering/formatting policy |
| `decoding_policy` | deterministic or replicate-controlled |
| `candidate_slice_band` | top-L or other fixed slice policy |
| `block_size` | preferably `b<=2` for first new stratum |
| `utility_metric` | decomposable utility or explicit reason why bridge is plausible |
| `logloss_measurement` | exact target evidence and scorer path |
| `data_source_kind` | fixture, operator-imported, or live API generated |
| `contamination_policy` | known/unknown/pass/fail |
| `claim_gate` | fail-closed mapping for all failure states |

### Candidate stratum options

The design review should choose exactly one option for P55. Good candidates are those with constrained targets and explicit target evidence.

#### Option A — `repo_change_review_microtask_v1`

- Task: choose whether a repo change violates a stated claim boundary or artifact invariant.
- Target: constrained label such as `no_violation`, `claim_boundary_violation`, `artifact_identity_violation`, `budget_comparability_violation`.
- Utility: decomposable correctness or rubric score over the constrained label.
- Rationale: naturally aligned with existing P47/P48/P49 fixture families but can be instantiated with imported non-fixture examples.
- Risk: may overfit to repo-specific rules; not a broad deployed stratum.

#### Option B — `paper_revision_claim_gate_microtask_v1`

- Task: decide whether a manuscript paragraph makes an allowed or denied claim.
- Target: constrained claim-boundary label.
- Utility: decomposable label correctness plus severity weighting.
- Rationale: directly tests the paper-facing claim-gate layer.
- Risk: may test claim-boundary classification rather than context projection value unless candidate findings are designed carefully.

#### Option C — `evidence_packet_selection_microtask_v1`

- Task: select a small set of findings needed to answer a constrained factual/evidence question.
- Target: exact answer field or forced-choice answer.
- Utility: exact answer correctness or decomposable field match.
- Rationale: cleanest logloss target; easiest bridge measurement.
- Risk: may drift toward single-agent RAG unless framed as dispatch-time worker projection.

### Required negative controls

Every proposed stratum must include:

- redundancy-heavy cases;
- pairwise-complementarity cases;
- underpowered/noisy cases expected to produce `ambiguous_metric`;
- stale/mismatched bridge witness cases expected to fail closed;
- candidate-pool hash mismatch cases expected to be paper-ineligible.

### Exit criteria

- one new stratum is selected and justified;
- the design explicitly explains why P45 `bio_attribute` failure does not automatically apply;
- dry-run config validates without live APIs;
- review approves or blocks P55.

### Claim ceiling

Design review only.

---

## 8. P55 — new-stratum bridge calibration pilot

### Goal

Execute or import a bounded pilot for the P54-approved stratum. The purpose is to test whether the metric bridge can pass in a controlled, materially new setting. Failure is acceptable and must remain fail-closed.

### Operator gates

P55 is blocked unless the operator approves the data source:

| Data source | Operator approval required? | Claim ceiling |
|---|---:|---|
| deterministic fixture rows | no | engineering/fixture only |
| operator-imported model rows | yes | possible bridge pilot if protocol complete |
| live API-generated rows | yes | possible bridge pilot if protocol complete |
| human-labeled rows | yes | still not measurement validation unless kappa/contamination gates also pass |

### Minimum measured fields

Each row must include:

- `run_id`
- `dispatch_id`
- `agent_id`
- `round_id`
- `candidate_pool_hash`
- `projection_hash` or selected block identity
- `context_L_hash`
- `block_A_ids`
- `materialization_policy`
- `model_tier`
- `decoding_policy`
- `target_evidence`
- `delta_logloss`
- `delta_utility`
- `utility_metric_version`
- `replicate_count`
- `effective_sample_size`
- `data_source_kind`
- `contamination_status`
- `bridge_contract_id`

### Fit/report requirements

The bridge report must include:

| Quantity | Required handling |
|---|---|
| `c_s` | estimated on development split only |
| `zeta_s` | held-out residual bound |
| sign agreement | held-out and confidence-aware |
| Spearman/rank correlation | held-out, with underpowered caveat |
| residual stability | across candidate-slice bands or seeds if available |
| ESS | fail closed if below contract threshold |
| drift status | fresh/stale/ambiguous |
| active stratum match | exact match required for claim inheritance |

### Decision table

| Outcome | Required output |
|---|---|
| residual/stability gates pass | `calibrated_proxy_supported` may be allowed for this stratum only |
| logloss-aligned ERM/near-optimality bridge established | `vinfo_proxy_supported` may be considered only if explicitly reviewed |
| residual large or unstable | `operational_utility_only` or `ambiguous_metric` |
| ESS underpowered | `ambiguous_metric` |
| fixture-only data | no paper evidence eligibility |
| contamination failure | `pilot_only`; no measurement validation |
| stratum mismatch | no claim inheritance |

### Suggested checks

```bash
uv run pytest tests/test_bridge_calibration.py
uv run pytest tests/test_revised_framing_guardrails.py
uv run pytest tests/test_phase_b_replay.py
```

### Exit criteria

- bridge report is deterministic and auditable;
- negative and positive outcomes are both represented correctly;
- no claim is emitted without active-stratum match;
- failed pilot is preserved as negative evidence rather than retried silently.

### Claim ceiling

At most `calibrated_proxy_supported` for the exact active stratum, and only if all predeclared gates pass. No `measurement_validated` claim.

---

## 9. P56 — replay substrate expansion for realistic dispatch traces

### Goal

Upgrade replay from fixture-only/hardened schema checks to imported realistic dispatch traces while preserving identity/hash binding and metric-claim separation.

### Allowed changes

- `docs/protocols/P56-realistic-dispatch-replay-protocol-v12.md`
- import validators for dispatch traces
- replay classification/report extensions
- focused tests for identity/hash fail-closed behavior
- review under `docs/reviews/`

### Required trace fields

A replayable dispatch trace must include:

- full dispatch identity: `run_id`, `dispatch_id`, `agent_id`, `round_id`;
- complete considered candidate set, not just selected items;
- stable candidate-pool hash;
- `ProjectionPlan` with selected and excluded candidates;
- `BudgetWitness` with estimated and realized token costs;
- `MaterializedContext` with ordering and section boundaries;
- `MetricBridgeWitness` with active stratum and freshness;
- replay intervention definition;
- evaluator/metric policy;
- replicate and ESS policy.

### Classification rules

| Replay condition | Required classification |
|---|---|
| complete identity + candidate pool + materialization + bridge witness | replay-comparable |
| missing identity | not replay-comparable |
| candidate-pool hash mismatch | fail closed |
| selected-only candidate list | not selector-comparable |
| stale/missing bridge | replay usable, metric claim downgraded |
| fixture-only trace | engineering/fixture evidence only |

### Experiment outputs

- `realistic_dispatch_replay_records.jsonl`
- `realistic_dispatch_replay_summary.csv`
- `realistic_dispatch_replay_claim_gate_report.json`
- `realistic_dispatch_replay_report.md`
- manifest with schema version and contract ID

### Exit criteria

- imported traces classify deterministically;
- replay usability is separate from metric support;
- bridge status cannot be inferred from replay completeness;
- candidate-pool hash mismatch fails closed.

### Claim ceiling

Replay usability and auditability only unless a valid matching bridge exists.

---

## 10. P57 — value-stratified extraction audit v2 and human-sentinel protocol

### Goal

Move beyond fixture extraction audit toward a value-stratified extraction measurement plan that estimates whether high-value, prerequisite, qualifier-heavy, or contradiction-sensitive findings are disproportionately lost in `M* -> M`.

### Allowed changes

- `docs/experiments/P57-extraction-audit-v2-plan.md`
- extraction audit schema extensions
- human-sentinel protocol template
- optional fixture tests for new labels
- review under `docs/reviews/`

### Required strata

At minimum:

- simple factual;
- complex conditional;
- qualifier-heavy;
- temporal-scope;
- cross-chunk;
- long-tail entity;
- high-provenance-value;
- prerequisite;
- contradictory;
- adversarial/repetition-sensitive.

### Required labels

For each source-side ground-truth finding:

- `captured_exact`
- `captured_core_preserved`
- `captured_core_changed`
- `missing`
- `unsupported_added`
- `duplicate_or_overmerged`
- `contradiction_lost`
- `qualifier_lost`
- `temporal_scope_error`
- `provenance_lost`
- `selector_impact_estimate`

### Metrics

Use separate notation to avoid collision with bridge `c_s`:

- `extraction_completeness_by_stratum`
- `effective_extraction_completeness`
- `value_weighted_extraction_loss`
- `critical_finding_miss_rate`
- `unsupported_finding_rate`
- `provenance_loss_rate`

### Human sentinel design

Human sentinel work is operator-gated. If executed, record:

- annotator count;
- label protocol version;
- adjudication procedure;
- agreement statistic if valid;
- disagreement analysis;
- whether labels can be used only as sentinel evidence or as measurement-validation candidates.

Missing human labels or missing kappa must not be filled by model adjudication.

### Exit criteria

- audit schema separates extraction-risk evidence from selector validity;
- value-weighted loss can be computed deterministically for fixture/imported records;
- human-sentinel protocol is ready but not assumed executed;
- no extraction result upgrades metric-bridge claims.

### Claim ceiling

Extraction-risk evidence only. No selector validity or V-information support.

---

## 11. P58 — provenance-aware redundancy diagnostics

### Goal

Reduce the ambiguity seen in adversarial redundancy by distinguishing duplicate waste, independent corroboration, adversarial repetition, contradiction, and prerequisite overlap.

### Allowed changes

- `docs/experiments/P58-provenance-aware-redundancy-plan.md`
- provenance/redundancy feature extraction helpers
- synthetic/fixture diagnostic extensions
- focused tests for deterministic classification
- review under `docs/reviews/`

### Diagnostic categories

| Category | Selector implication |
|---|---|
| duplicate redundancy | safe to penalize strongly |
| independent corroboration | preserve if source independence is high and claim is important |
| adversarial repetition | trigger contradiction/provenance audit, not simple diversity penalty |
| prerequisite overlap | preserve until prerequisite chain is resolved |
| paraphrase near-duplicate | lower priority unless provenance differs |
| source-conflict pair | escalate or adjudicate |

### Required features

- source independence score;
- provenance handle overlap;
- contradiction flag;
- qualifier mismatch flag;
- temporal-scope mismatch flag;
- prerequisite relation flag;
- semantic similarity score;
- finding hash and source-span hash.

### Outputs

- updated synthetic/fixture diagnostic report;
- redundancy category confusion table if fixture labels exist;
- claim-gate report showing no upgrade to bridge or measurement status.

### Exit criteria

- adversarial redundancy cases can be subdivided without lowering ambiguity guardrails;
- duplicate redundancy and corroborative redundancy are no longer treated identically;
- selector changes remain heuristic/operational unless separately calibrated.

### Claim ceiling

Operational diagnostic improvement only.

---

## 12. P59 — `ReprojectionWitness` replay integration

### Goal

Connect the optional `ReprojectionWitness` scaffold to replay records so that re-projection interventions are auditable and comparable. This phase evaluates the witness as an artifact, not deployed runtime improvement.

### Allowed changes

- `docs/experiments/P59-reprojection-replay-integration-plan.md`
- replay/reprojection linking schema
- fixture/import validators
- focused tests for trigger/action/context-diff correctness
- review under `docs/reviews/`

### Required witness fields

- initial dispatch identity;
- trigger type: `unknown_due_to_missing_context`, `hallucination_risk`, `wrong_despite_context`, `ambiguous`, or other reviewed enum;
- original budget and revised budget;
- selector before/after;
- candidate-pool hash before/after;
- materialized-context hash before/after;
- selected/excluded context diff;
- output before/after;
- evaluator/uncertainty label;
- over-budget flag;
- metric bridge status;
- claim-gate result.

### Decision rules

| Condition | Required decision |
|---|---|
| identity mismatch | not comparable |
| candidate-pool mismatch without documented expansion | fail closed |
| revised context over budget | operational violation |
| metric bridge missing | no metric claim upgrade |
| before/after improvement in fixture | operational audit only |

### Exit criteria

- re-projection events bind to replay records;
- context diffs are deterministic and inspectable;
- improvements are not described as deployed runtime improvement;
- witness supports auditability, not scientific validation.

### Claim ceiling

Operational audit only.

---

## 13. P60 — final v12 evidence ledger and manuscript package

### Goal

Create a paper-facing evidence ledger that summarizes what each artifact supports, what it does not support, and how the manuscript should reference it.

### Allowed changes

- `docs/paper/v12-evidence-ledger.md`
- `docs/reviews/P51-P60-v12-phase-summary.md`
- manuscript integration checklist
- optional paper-facing tables

### Required ledger columns

| Column | Required content |
|---|---|
| phase | P45-P60 |
| artifact family | files or directories |
| data source kind | synthetic, fixture, imported, live, human |
| metric bridge status | missing/stale/fresh/underpowered/non-calibrated |
| metric claim level | one of v12 allowed values |
| selector label scope | supported/escalate/risk/ambiguous scope |
| paper evidence eligible | true/false |
| denied claims | explicit denied claims |
| manuscript location | section/appendix where result may be cited |
| caveat sentence | exact wording to prevent claim overreach |

### Required paper-integration outputs

- a table of evidence that may appear in the main paper;
- a table of scaffold artifacts that belong in appendix/repo only;
- a list of negative results that must be preserved;
- a list of future-work items that remain unexecuted;
- a list of labels/phrases forbidden in final manuscript.

### Exit criteria

- every paper-facing result has a claim boundary;
- negative P45 closure is represented;
- synthetic and fixture results are not paper-grade validation;
- manuscript can be revised without evidence-state ambiguity.

### Claim ceiling

Evidence ledger and manuscript packaging only.

---

## 14. Cross-phase validation commands

Use focused checks for local edits, then full checks when feasible.

```bash
uv run pytest tests/test_revised_framing_guardrails.py
uv run pytest tests/test_projection_artifacts.py
uv run pytest tests/test_synthetic_regime_benchmark.py
uv run pytest tests/test_phase_b_replay.py
uv run pytest tests/test_bridge_calibration.py
uv run pytest
python -m compileall cps tests scripts
python scripts/framework_guard.py status
python scripts/framework_guard.py validate --profile target
```

Record exact command output in the phase review. If a test is skipped because it is not present or the phase is doc-only, record that explicitly.

---

## 15. Required review handoff for every phase

Every implementation or documentation phase must end with a review file containing:

1. changed files;
2. implementation summary;
3. phase boundary statement;
4. evidence claim ceiling;
5. tests run;
6. exact results;
7. skipped checks and reasons;
8. assumptions;
9. limitations;
10. paper-boundary guardrails touched;
11. generated artifact schema changes;
12. whether operator approval is required before the next phase;
13. final verdict.

Allowed verdicts:

- `ACCEPT`
- `ACCEPT_WITH_NOTES`
- `REQUEST_CHANGES`
- `BLOCKED_OPERATOR_REQUIRED`
- `REJECT`

---

## 16. Codex handoff template

Use this template when spawning a local development window for a phase.

```text
You are working in the mingx repo.
Current phase: P<NN> <phase name>.

Read first:
- AGENTS.md
- docs/paper-alignment-v12.md
- docs/archive/context_projection_fixed_v12.md
- this P51-P60 follow-up plan
- the relevant phase plan/review docs

Scope:
<allowed files>

Forbidden:
- do not claim measurement validation
- do not claim deployed V-information verification
- do not upgrade fixture/synthetic evidence
- do not run live APIs unless explicitly operator-approved
- do not edit unrelated phase files

Task:
<phase-specific task>

Checks:
<focused commands>

Required final report:
- changed files
- summary
- boundary statement
- tests and exact results
- limitations
- next-phase recommendation
```

---

## 17. Recommended execution order

Start with P51 and P52. Do not start P55 before P53 and P54 have accepted reviews.

Immediate next actions:

1. P51: fix top-level state drift and claim checklist.
2. P52: sync corrected proof and P45 closure into manuscript.
3. P53: create diagnostic threshold contract.
4. P54: design the next bridge stratum.
5. P55+: execute only after reviewed protocol and operator gates.
