# Empirical Validation Protocol

**Status:** Future empirical validation protocol. This document does not authorize
live API execution, live cohort execution, external runtime integration, or any
claim that CPS is `measurement_validated`.

**Target manuscript:** `docs/archive/context_projection_revised_v10.md`

**Boundary:** The current P17-P24 evidence package supports conditional theory,
offline runtime-audit evidence, replayable artifacts, and manuscript-facing claim
boundaries. It does not provide scientific validation.

## 1. Validation Ladder

The empirical validation program is staged. Each level can support only the
claim explicitly allowed at that level.

| Level | Purpose | Required evidence | Required artifacts | Allowed claim | Denied claim | Failure conditions |
| --- | --- | --- | --- | --- | --- | --- |
| EV0 replay/determinism validation | Verify deterministic replay of saved artifacts. | Stable hashes, complete replay package, deterministic rerun, no source-artifact mutation. | replay package, projection bundles, evidence ledger, claim gate report, paper evidence summary. | `replayable_artifact_evidence` | `measurement_validated`, scientific validation. | Missing projection bundles, non-deterministic outputs, incomplete required artifacts. |
| EV1 proxy-regime diagnostic validation | Verify controlled proxy/synthetic diagnostics and claim-gate routing. | Proxy-regime matrix, synthetic/proxy diagnostic rows, bridge status, claim gate report. | proxy-regime matrix, diagnostics, metric bridge witnesses, claim gate report. | `vinfo_proxy_supported` or `operational_utility_only` as gated. | Deployed V-information certification, `measurement_validated`. | Contamination fail, stale/missing bridge, missing labels/kappa if validation claims are attempted. |
| EV2 controlled live API pilot | Run a small controlled live API pilot under frozen settings. | 30-50 cases, fixed endpoint, frozen prompts, captured artifacts, run manifest, claim gate report. | all per-case artifacts listed in Section 5, plus run-level manifest. | `pilot_only` or `operational_utility_only` unless EV3/EV4 evidence is present. | `measurement_validated`, scientific validation. | API drift, prompt changes, missing artifacts, unfair baselines, contamination fail. |
| EV3-lite model-adjudicated evaluation | Run the fully automated judge route after EV2 artifacts exist. | DeepSeek V4 Flash prelabels, Codex subagent audit, Codex model adjudication, contamination status, bridge status, claim gate report. | `llm_prelabels.jsonl`, `subagent_audit_report.json`, `model_adjudicated_labels.jsonl`, model-adjudicated summary. | `model_adjudicated_pilot_only`, `automated_judge_evidence`, `annotation_workload_reduction_evidence`, or `operational_utility_only`. | `measurement_validated`, `human_labeled_validation`, human-human kappa, scientific validation. | Model adjudication overtrusted, missing contamination/bridge evidence, attempted human-label or validation claim. |
| EV3 human-labeled measurement validation | Add human labels, adjudication, and agreement evidence. | At least two annotators, adjudication, label records, kappa report, contamination pass. | human labels, adjudication, kappa report, contamination report, claim gate report. | `measurement_validated_candidate` only if EV4 prerequisites are also plausible. | Automatic `measurement_validated`; kappa alone is insufficient. | Missing labels, low kappa, unresolved adjudication, contamination fail. |
| EV4 metric-bridge closure | Close metric bridge freshness and claim-gate eligibility. | Fresh bridge evidence, non-operational metric class when V-information claims are made, claim gate allow. | metric bridge witness, bridge closure report, EV3 evidence, final claim gate report. | `measurement_validated` only if all gates pass. | Deployed V-information certification unless separately proven. | Missing/stale bridge, operational-only metric class, claim gate deny, incomplete EV3 evidence. |

`measurement_validated` requires all of the following: complete artifacts, a
controlled live run, human labels, acceptable kappa, contamination pass, fresh
metric bridge, and a claim gate report that explicitly allows the claim.

EV3-lite is intentionally not a validation substitute. It exists so the project
can proceed with a fully automated model-adjudicated route while preserving that
missing human labels and missing human-human kappa block `measurement_validated`.

## 2. Two Empirical Routes

The empirical program supports two distinct routes after EV2 controlled live
pilot evidence exists.

| Route | Required evidence | Required artifacts | Allowed maximum claim | Denied claims |
| --- | --- | --- | --- | --- |
| Route A: Human-labeled measurement validation route | Human labels, at least two human annotators, acceptable kappa, contamination pass, fresh metric bridge, claim gate allow. | `human_labels.jsonl`, adjudication records, `human_label_completeness_report.json`, `kappa_report.json`, `contamination_report.json`, bridge evidence, claim gate report. | `measurement_validated_candidate` before final EV4/claim-gate closure. | Automatic `measurement_validated`, kappa-alone validation, deployed V-information certification beyond scope. |
| Route B: Fully automated model-adjudicated route | DeepSeek V4 Flash prelabels, Codex subagent audit, Codex model adjudication, contamination audit, bridge status, claim gate report. | `llm_prelabels.jsonl`, `subagent_audit_report.json`, `model_adjudicated_labels.jsonl`, model-adjudicated summary, contamination report, bridge status. | `model_adjudicated_pilot_only` or `operational_utility_only`. | `measurement_validated`, `human_labeled_validation`, `human_human_kappa_established`, `scientific_validation_completed`, deployed V-information certification. |

Route B does not produce `human_labels.jsonl`, does not compute human-human
kappa, and does not require human annotation. It may be faster and cheaper, but
its claim strength is lower. Model-adjudicated labels are not human labels, Codex
adjudication is not human review, and LLM/Codex agreement is not human-human
kappa.

## 3. Experimental Conditions

Each controlled empirical run must define conditions before execution.

| Condition | Purpose | Required controls | Claim boundary |
| --- | --- | --- | --- |
| No-CPS baseline | Measures task behavior without CPS selection. | Same model, same case set, same endpoint, same prompt family except no CPS materialization. | Baseline comparison only. |
| Heuristic/simple selector baseline | Compares CPS against a simple deterministic selector. | Frozen heuristic, no post-hoc tuning on test cases, same candidate pool. | Operational comparison only. |
| CPS runtime-audit scaffold | Tests the CPS selection and audit path. | Projection artifacts, metric bridge witness, claim gate report, full artifact capture. | Audit/evidence claim only until EV3/EV4 pass. |
| Optional full-context or large-context upper baseline | Estimates whether selection pressure is material. | Same model/endpoint where feasible, explicit token budget and truncation policy. | Upper-baseline diagnostic, not proof of CPS optimality. |

All conditions must use the same case manifest and must prevent unfair access to
labels, answers, hidden evaluator material, or post-hoc prompt tuning.

## 4. Minimum Pilot Design

The controlled live API pilot is an operator-approved future activity.

| Design item | Required policy |
| --- | --- |
| Pilot size | 30-50 cases. |
| Expanded size | 100-200 cases after pilot review. |
| Model/API endpoint | Fixed before execution and recorded in the run manifest. |
| Prompt templates | Frozen before execution; changes require a new manifest version. |
| Temperature | Deterministic setting preferred; if nonzero, record seed/replication policy and treat as pilot evidence only. |
| Run manifest | Required before execution; includes case ids, condition ids, endpoint, model string, prompt version, artifact schema version, operator approval, and planned exclusions. |
| Artifact capture | Required for every live case and every experimental condition. Missing required artifacts downgrade the run. |
| Case exclusion | Allowed only under pre-declared criteria and must be recorded. |
| Post-hoc tuning | Forbidden on test cases. Any prompt tuning after seeing case outcomes contaminates the affected evaluation. |

The pilot is intended to detect feasibility, instrumentation failures, obvious
condition separation, and annotation workload. It is not sufficient by itself for
scientific validation.

## 5. Required Per-Case Artifacts

Each live case must save the following artifacts for every condition where the
artifact applies.

| Artifact | Purpose | Missing-artifact consequence |
| --- | --- | --- |
| `input_case.json` | Case source, prompt inputs, expected metadata, split, and case hash. | Case is not replay-complete. |
| `candidate_pool.jsonl` | Candidate items available to the selector. | Candidate-pool completeness cannot be audited. |
| `projection_plan.json` | Selected/excluded candidates, algorithm, scores, and selection trace. | CPS path cannot support replay evidence. |
| `budget_witness.json` | Token budget, estimated tokens, realized tokens, and budget compliance. | Budget compliance claim denied. |
| `materialized_context.json` | Final context order and content hashes sent to the model. | Context replay incomplete. |
| `metric_bridge_witness.json` | Metric class, bridge freshness, diagnostic scope, and bridge evidence. | Bridge-aware claims become ambiguous or operational-only. |
| `projection_bundle.json` | Canonical bundle tying plan, budget, context, bridge witness, and diagnostics. | ProjectionBundleV1 evidence missing. |
| `model_output.json` | Raw and normalized model output, endpoint metadata, and finish status. | Output cannot be evaluated or replayed. |
| `claim_gate_report.json` | Claim gate output for the case or run. | Claim level cannot be upgraded. |
| `human_labels.jsonl` | Annotator labels by dimension. | `measurement_validated` blocked. |
| `adjudication.json` | Adjudication decisions and rationale for disagreements. | Validation remains unresolved if material disagreements exist. |
| `kappa_report.json` | Agreement computation and threshold result. | `measurement_validated` blocked. |
| `contamination_report.json` | Contamination audit result and evidence. | Missing report blocks validation; failed report forces `pilot_only`. |

Run-level outputs must include a manifest, condition summary, artifact counts,
case-level exclusions, aggregate claim gate report, aggregate label summary,
aggregate kappa report, aggregate contamination report, and final claim-boundary
summary.

Route B adds model-adjudicated artifacts only after the case artifacts exist:
`llm_prelabels.jsonl`, `subagent_audit_report.json`, and
`model_adjudicated_labels.jsonl`. These artifacts must never be renamed or used
as `human_labels.jsonl`.

## 6. Human Labeling And Kappa Requirements

The human labeling protocol is specified in:

```text
docs/protocols/human-label-kappa-protocol.md
```

Minimum requirements:

- at least two independent annotators;
- label dimensions for correctness, completeness, groundedness, context
  sufficiency, missing critical context, irrelevant context, misleading context,
  and conflict/stale context;
- 0/1/2 label scale;
- adjudication for material disagreement;
- kappa report before any validation-level claim.

Missing human labels or missing kappa blocks `measurement_validated`.

Route B does not satisfy this section. Model-adjudicated labels are not human
labels, and Codex adjudication does not establish human-human kappa.

## 7. Contamination Audit Requirements

The contamination audit protocol is specified in:

```text
docs/protocols/contamination-audit-protocol.md
```

The audit must check for leaked labels, cases seen during prompt/development,
candidate pools directly containing answers, unfair baseline access, annotator
leakage, duplicated examples, and post-hoc prompt tuning on test cases.

Hard rule:

```text
contamination failure => pilot_only
```

## 8. Metric Bridge Freshness

Metric bridge status must be recorded in `metric_bridge_witness.json`.

| Bridge status | Definition | Allowed claim effect |
| --- | --- | --- |
| bridge missing | No usable bridge witness or bridge evidence. | `ambiguous` or observability-only. |
| bridge stale | Bridge evidence exists but is outside the accepted freshness window or drift status fails. | `operational_utility_only` or `ambiguous`. |
| bridge current | Bridge evidence is current for operational comparison but not sufficient for validation review. | Operational or pilot claims only. |
| bridge fresh enough for measurement review | Bridge evidence is fresh, non-operational-only when V-information claims are made, and tied to the executed run. | Eligible for `measurement_validated_candidate` or `measurement_validated` only if all other gates pass. |

Stale or missing bridge evidence forces `operational_utility_only` or
`ambiguous`; it cannot support `measurement_validated`.

## 9. Claim Gate Mapping

The claim gate remains the source of truth. This protocol defines the empirical
preconditions that future evidence must provide before the gate can allow stronger
claims.

| Claim level | Minimum evidence | Allowed use | Denied use |
| --- | --- | --- | --- |
| `engineering_smoke_only` | Local/offline smoke evidence. | Implementation feasibility. | Scientific validation. |
| `replayable_artifact_evidence` | Complete deterministic replay artifacts. | Replay and audit evidence. | `measurement_validated`. |
| `vinfo_proxy_supported` | Synthetic/proxy structural diagnostics. | Proxy-regime diagnostic reporting. | Deployed V-information certification. |
| `operational_utility_only` | Operational metric evidence without full bridge closure. | Utility-scoped operational comparison. | V-information validation. |
| `pilot_only` | Controlled pilot with incomplete validation evidence or contamination failure. | Feasibility and pilot reporting. | Measurement validation. |
| `model_adjudicated_pilot_only` | Route B model-adjudicated labels from V4 Flash prelabels plus Codex audit/adjudication, without human labels or kappa. | Automated pilot evidence and model-adjudicated comparison. | `measurement_validated`, `human_labeled_validation`, human-human kappa, scientific validation. |
| `automated_judge_evidence` | LLM/Codex judge outputs with explicit non-human-label boundaries. | Automated judging analysis and error triage. | Human review, human labels, kappa evidence. |
| `annotation_workload_reduction_evidence` | Prelabels, audit requests, review queues, or model adjudication used to reduce annotation effort. | Workflow efficiency evidence. | Measurement validation or scientific validation. |
| `measurement_validated_candidate` | EV3 evidence appears sufficient for review, but final bridge/claim gate closure is not complete. | Supervisor/operator validation review candidate. | Final validation claim. |
| `measurement_validated` | Complete artifacts, controlled live run, human labels, acceptable kappa, contamination pass, fresh metric bridge, and claim gate allow. | Measurement validation claim for the scoped run only. | Deployed V-information certification beyond the validated scope. |

No single artifact grants validation. Live API success alone, external runtime
success alone, kappa alone, replay completeness, paper-summary completeness, or
synthetic success alone is insufficient.

Route B specifically denies `measurement_validated`, `human_labeled_validation`,
`human_human_kappa_established`, `scientific_validation_completed`, and
deployed V-information certification.

## 10. Manuscript Impact

Before empirical validation, the manuscript may say:

- CPS has conditional theory for the formal V-information objective.
- The runtime-audit scaffold is implemented offline.
- Replay packages and paper evidence summaries exist.
- Proxy-regime diagnostics are available for synthetic/proxy evidence.
- `measurement_validated` is not claimed.

After EV2 controlled live pilot, the manuscript may say:

- A controlled live API pilot was executed under frozen settings.
- Pilot evidence supports feasibility or operational utility within the scoped
  conditions.
- Validation remains blocked if human labels, kappa, contamination pass, and
  fresh bridge closure are absent.

After EV3-lite model-adjudicated evaluation, the manuscript may say:

- A fully automated model-adjudicated evaluation route was executed.
- V4 Flash prelabels, Codex subagent audit, and Codex model adjudication support
  model-adjudicated pilot or operational evidence.
- No human labels or human-human kappa were produced.
- `measurement_validated`, human-labeled validation, and scientific validation
  remain denied.

After EV3/EV4 human-labeled validation and metric-bridge closure, the manuscript
may say only what the final claim gate allows. If the gate permits
`measurement_validated`, the claim must be scoped to the run, case set, endpoint,
prompt version, metric bridge, and annotation protocol.

Current P17-P24 evidence is not measurement validation because it is offline,
synthetic/proxy/replay/manuscript-facing evidence without live controlled run
closure, human labels, acceptable kappa, contamination closure, and fresh metric
bridge sufficient for measurement review.

## 11. Non-Goals

This protocol does not:

- run live APIs;
- implement a live runner;
- add model API clients;
- import external SDKs;
- perform external runtime integration;
- unblock P04 or P09;
- claim `measurement_validated`;
- treat model-adjudicated labels as human labels;
- treat Codex adjudication as human review;
- treat LLM/Codex agreement as human-human kappa;
- certify deployed V-information submodularity;
- convert engineering success into scientific validation.
