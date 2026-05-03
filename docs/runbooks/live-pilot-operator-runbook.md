# Live Pilot Operator Runbook

**Phase:** P29 Live Pilot Operator Runbook

**Target workflow:** Controlled EV2/EV3 empirical pilot for the CPS
runtime-audit scaffold.

**Model conditions:** DeepSeek V4 Flash and DeepSeek V4 Pro.

**Status:** Operator-facing runbook only. This document does not run live APIs,
authorize live execution by itself, add API clients, or claim
`measurement_validated`.

## 1. Purpose

This runbook governs a controlled EV2/EV3 empirical pilot for Context Projection
Selection (CPS) runtime-audit evidence. It translates the P25-P28 empirical
validation infrastructure into an operator checklist for future live execution,
human labeling, kappa reporting, contamination audit, metric bridge review, and
empirical evidence packaging.

This runbook does not itself run live APIs. Live API execution requires separate
operator approval, an explicit live run manifest, and all live gates defined by
the P26 controlled live pilot runner. Live API success alone is not measurement
validation.

DeepSeek V4 Flash and DeepSeek V4 Pro are model conditions, not validation
authorities. Results on either model are empirical observations under fixed
manifest conditions. Neither model validates CPS by itself.

`measurement_validated` requires all of the following:

- complete artifacts;
- controlled live run;
- human labels;
- acceptable kappa;
- contamination pass;
- fresh metric bridge;
- conservative claim gate approval.

P04 remains deferred/operator-required. P09 remains
`BLOCKED_OPERATOR_REQUIRED`. This runbook does not unblock P04 or P09.

## 2. Empirical Validation Ladder

P29 prepares EV2/EV3 operations but does not execute them.

| Level | Objective | Required artifacts | Allowed claim | Denied claim | Failure condition |
| --- | --- | --- | --- | --- | --- |
| EV0 replay/determinism validation | Confirm deterministic replay of saved evidence. | Replay package, projection bundles, evidence ledger, claim gate report, paper evidence summary. | `replayable_artifact_evidence` | `measurement_validated`, scientific validation. | Missing bundles, non-deterministic outputs, incomplete replay artifacts. |
| EV1 proxy-regime diagnostic validation | Exercise proxy/synthetic diagnostic routing. | Proxy-regime matrix, diagnostics, metric bridge witnesses, claim gate report. | `synthetic_structural_only` or `operational_utility_only` as gated. | Deployed V-information certification, `measurement_validated`. | Contamination fail, stale/missing bridge, attempted validation claim without labels/kappa. |
| EV2 controlled live API pilot | Run fixed live model conditions under a frozen manifest. | Run manifest, per-case artifacts, model outputs, claim gate report, pilot summary. | `controlled_live_pilot_only`, `pilot_only`, or `operational_utility_only` as gated. | `measurement_validated`, scientific validation. | Missing manifest gates, API drift, prompt changes, artifact failure, unfair baselines. |
| EV3 human-labeled measurement validation | Add human labels, adjudication, and kappa evidence. | Human labels, adjudication, completeness report, kappa report, contamination report. | `measurement_validated_candidate` only if EV4 prerequisites are plausible. | Automatic `measurement_validated`; kappa-alone validation. | Missing labels, missing/low kappa, unresolved adjudication, contamination fail. |
| EV4 metric-bridge closure | Close metric bridge freshness and final claim gate eligibility. | Fresh bridge evidence, bridge review, EV3 package, final claim gate report. | `measurement_validated` only if all gates pass. | Deployed V-information certification beyond the validated scope. | Missing/stale bridge, operational-only metric class, claim gate deny, incomplete EV3 evidence. |

## 3. Model Policy: DeepSeek V4 Flash And DeepSeek V4 Pro

### A. DeepSeek V4 Flash

| Field | Policy |
| --- | --- |
| `model_alias` | `deepseek_v4_flash` |
| Role | `primary_pilot_model` |
| Intended use | Main controlled pilot over the full initial case set. |
| Recommended first-run size | 30-50 cases. |
| Recommended expanded size | 100-200 cases after dry-run and pilot stability. |
| Purpose | Cost-efficient primary empirical pilot condition. |

### B. DeepSeek V4 Pro

| Field | Policy |
| --- | --- |
| `model_alias` | `deepseek_v4_pro` |
| Role | `strong_model_audit_subset` |
| Intended use | Stronger-model comparison and audit subset. |
| Recommended first-run size | 10-20 matched cases. |
| Recommended expanded size | 50-100 matched cases if budget allows. |
| Purpose | Check whether evidence-chain behavior is stable under a stronger model condition. |

Do not hard-code provider-specific model IDs in source code. Actual API model
names and endpoints must be supplied in the live run manifest by the operator.
Each run must record fixed endpoint, fixed model name, fixed model alias, fixed
temperature, fixed prompt template, fixed case set, and fixed condition
assignment.

Differences between Flash and Pro are empirical observations only. Neither model
can validate the method by itself. Live success on either model does not imply
`measurement_validated`. Both models still require human labels, kappa,
contamination audit, fresh metric bridge, complete artifacts, and claim gate
approval before any `measurement_validated_candidate` claim.

## 4. Recommended Pilot Design

### Initial Pilot

| Model condition | Size | Case policy | Conditions |
| --- | --- | --- | --- |
| DeepSeek V4 Flash | 30-50 cases | Full initial case set. | All required conditions. |
| DeepSeek V4 Pro | 10-20 matched cases | Same cases as a subset from Flash where possible. | Same conditions or selected diagnostic subset. |

### Expanded Pilot

| Model condition | Size | Case policy |
| --- | --- | --- |
| DeepSeek V4 Flash | 100-200 cases | Expanded fixed case set after pilot stability. |
| DeepSeek V4 Pro | 50-100 matched cases if budget allows | Matched audit subset. |

Required conditions:

- `no_cps_baseline`
- `heuristic_selector_baseline`
- `cps_runtime_audit_scaffold`

Optional condition:

- `full_context_upper_baseline`

`full_context_upper_baseline` is optional because it may have high token cost
and may not be fair under strict budget constraints.

Temperature should be 0 or near 0. If the API does not support exactly 0, record
the exact value in the manifest. Prompt templates must be frozen. No prompt
tuning is allowed after pilot cases are frozen. Any prompt change requires a new
`run_id`.

Case ordering and condition assignment must be deterministic. Do not remove
cases post hoc unless the exclusion is recorded with a reason.

## 5. Pilot Stages

| Stage | Objective | Inputs | Outputs | Required artifacts | Stop conditions | Allowed claim level | Forbidden claim level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stage 0: Dry-run rehearsal | Verify local artifact plumbing without live calls. | Dry-run manifest, fixed cases, fixed conditions. | Dry-run pilot outputs and claim gate report. | P26 artifact set, dry-run manifest. | Any artifact failure, non-determinism, missing output root. | `engineering_smoke_only` | `measurement_validated` |
| Stage 1: Controlled live pilot, EV2 | Execute fixed live model conditions after operator approval. | `CPS_ALLOW_LIVE_API=1`, `operator_approval: true`, fixed endpoint/model/prompt/cases/conditions, output root, budget cap. | Live pilot outputs, model outputs, claim gate report. | Full per-case P26 artifacts. | Missing live gate, API drift, budget cap exceeded, artifact capture failure. | `controlled_live_pilot_only`, `pilot_only` | `measurement_validated` |
| Stage 2: Human labeling, EV3 | Collect human labels for validation-scoped outputs. | Model outputs, rubric, annotators, blinding policy. | `human_labels.jsonl`, adjudication records. | Complete labels for all scoped cases/conditions. | Missing labels, annotator leakage, unrecorded disagreement overwrite. | human-labeled pilot evidence | `measurement_validated` |
| Stage 3: Kappa report generation | Compute reliability evidence. | Human labels, required case list, conditions. | `human_label_completeness_report.json`, `kappa_report.json`. | Per-dimension and macro-average kappa. | Fewer than two annotators, missing labels, invalid labels, low kappa. | kappa-supported candidate evidence | kappa-alone validation |
| Stage 4: Contamination audit | Review leakage and fairness risks. | Case lineage, prompt history, candidate pools, labels, baseline access. | `contamination_report.json`. | All required P28 contamination checks. | Any failed check, unknown or incomplete critical audit. | contamination gate status | validation from contamination pass alone |
| Stage 5: Metric bridge freshness review | Decide whether bridge evidence is fresh enough for measurement review. | Metric bridge witnesses, bridge review evidence, model-condition diagnostics. | Metric bridge freshness decision and evidence reference. | Freshness status per scoped model condition if behavior diverges. | Missing/stale bridge, operational-only metric class. | operational or candidate evidence | `measurement_validated` without bridge closure |
| Stage 6: Empirical evidence package build | Package EV2/EV3/EV4 evidence. | Pilot summary, label report, kappa report, contamination report, bridge status. | Empirical evidence package outputs. | P28 package outputs. | Missing labels/kappa/contamination/bridge evidence. | packaged empirical evidence | validation by package completeness |
| Stage 7: Claim gate decision | Apply conservative claim gate to packaged evidence. | Empirical package, claim gate report, operator review. | Final claim decision. | Claim gate report with reason codes. | Gate denies or required evidence missing. | claim level explicitly allowed by gate | upgraded claim by interpretation |
| Stage 8: Manuscript patch decision | Decide what wording can enter the paper. | Final claim decision and evidence package. | Manuscript patch plan or deferral. | Evidence references and claim-boundary notes. | Claim gate not reviewed, missing non-claim text. | cautious scoped wording | empirical validation wording before gate review |

Stage 0 must use dry-run only and must not call live APIs. Stage 8 occurs only
after claim gate review.

## 6. Operator Prerequisites Before Live Execution

Before live execution, confirm:

- clean git state;
- exact commit hash recorded;
- current branch recorded;
- run manifest created;
- model endpoint fixed;
- model name fixed;
- model alias fixed;
- prompt template frozen;
- temperature fixed;
- max cases fixed;
- cases frozen;
- conditions frozen;
- output root empty or archived;
- `CPS_ALLOW_LIVE_API=1` set only during execution;
- `operator_approval: true` in manifest;
- budget cap acknowledged;
- API credentials configured outside repo;
- no credentials committed;
- no unit test calls live APIs;
- rollback/abort plan ready;
- artifact storage path confirmed;
- labeler availability confirmed for EV3;
- contamination audit reviewer identified;
- metric bridge reviewer identified.

If any prerequisite is missing, do not run live. Missing prerequisites must fail
closed.

## 7. Required Run Manifest

Required manifest fields:

- `run_id`
- `evidence_level`
- `mode`
- `model_conditions`
- `model_alias`
- `model_role`
- `model_endpoint`
- `model_name`
- `temperature`
- `prompt_template_id`
- `case_count`
- `case_subset_policy`
- `max_cases`
- `conditions`
- `output_root`
- `operator_approval`
- `budget_cap`
- `live_api_used`
- `external_runtime_used`
- `human_labels_required_for_measurement_validated`
- `kappa_required_for_measurement_validated`
- `contamination_audit_required`
- `metric_bridge_freshness_required`
- `claim_gate_required`
- `dry_run_rehearsal_required`
- `abort_policy`
- `artifact_retention_policy`

Example manifest skeleton:

```yaml
run_id: "<operator_filled_run_id>"
evidence_level: "EV2_controlled_live_pilot"
mode: "live_operator_approved"
model_conditions:
  - model_alias: "deepseek_v4_flash"
    model_role: "primary_pilot_model"
    model_endpoint: "<operator_filled_deepseek_v4_flash_endpoint>"
    model_name: "<operator_filled_deepseek_v4_flash_model_name>"
    temperature: 0
    prompt_template_id: "<frozen_prompt_template_id>"
    case_count: 50
    case_subset_policy: "full_initial_case_set"
  - model_alias: "deepseek_v4_pro"
    model_role: "strong_model_audit_subset"
    model_endpoint: "<operator_filled_deepseek_v4_pro_endpoint>"
    model_name: "<operator_filled_deepseek_v4_pro_model_name>"
    temperature: 0
    prompt_template_id: "<frozen_prompt_template_id>"
    case_count: 20
    case_subset_policy: "matched_subset_from_flash_cases"
max_cases: 50
conditions:
  - "no_cps_baseline"
  - "heuristic_selector_baseline"
  - "cps_runtime_audit_scaffold"
output_root: "<operator_filled_output_root>"
operator_approval: true
budget_cap: "<operator_filled_budget_cap>"
live_api_used: true
external_runtime_used: false
human_labels_required_for_measurement_validated: true
kappa_required_for_measurement_validated: true
contamination_audit_required: true
metric_bridge_freshness_required: true
claim_gate_required: true
dry_run_rehearsal_required: true
abort_policy: "fail_closed_on_missing_gate_or_artifact_failure"
artifact_retention_policy: "retain_all_run_artifacts_with_manifest_hash"
```

Do not put API keys, tokens, or credentials in the manifest.

## 8. Required Artifacts Per Case

For each case and condition, save:

- `input_case.json`
- `candidate_pool.jsonl`
- `projection_plan.json`
- `budget_witness.json`
- `materialized_context.json`
- `metric_bridge_witness.json`
- `projection_bundle.json`
- `model_output.json`
- `claim_gate_report.json`

These must later be joined with:

- `human_labels.jsonl`
- `human_label_completeness_report.json`
- `kappa_report.json`
- `contamination_report.json`
- `empirical_evidence_manifest.json`
- `empirical_claim_gate_report.json`
- `empirical_evidence_summary.md`

Artifacts must include `model_alias`, `condition`, `case_id`, and `run_id`.
Flash and Pro artifacts must not be mixed without explicit `model_condition`
identifiers.

## 9. Human Labeling Protocol

Human labeling follows P27:

- at least two annotators are required;
- use condition blinding where practical;
- use model alias blinding where practical when comparing Flash and Pro;
- annotator IDs must be stable pseudonyms;
- adjudication must be recorded separately;
- disagreements must not be silently overwritten;
- labels must not be fabricated.

Required label dimensions:

- `answer_correctness`
- `answer_completeness`
- `answer_groundedness`
- `context_sufficiency`
- `missing_critical_context`
- `irrelevant_context`
- `misleading_context`
- `conflict_or_stale_context`

Label scale:

- `0 = fail`
- `1 = partial`
- `2 = pass`

## 10. Kappa Decision Rules

| Kappa result | Claim effect |
| --- | --- |
| missing kappa | Not `measurement_validated` |
| `kappa < 0.40` | `pilot_only` |
| `0.40 <= kappa < 0.60` | `weak_evidence_not_measurement_validated` |
| `0.60 <= kappa < 0.75` | `limited_measurement_review_candidate` |
| `kappa >= 0.75` | `stronger_measurement_review_candidate` |

High kappa alone is not measurement validation. Contamination pass, fresh metric
bridge, complete artifacts, and claim gate approval are still required. Kappa
must be reported per dimension and as a macro-average.

## 11. Contamination Audit

Required checks:

- `leaked_labels`
- `seen_during_prompt_or_dev`
- `candidate_pool_contains_direct_answer`
- `unfair_baseline_access`
- `annotator_leakage`
- `duplicated_examples`
- `post_hoc_prompt_tuning_on_test_cases`
- `train_test_overlap`
- `answer_key_exposure`
- `condition_assignment_leakage`

Rules:

- any failed contamination check => `pilot_only`;
- unknown or incomplete contamination audit => not `measurement_validated`;
- contamination pass alone is not validation;
- contamination audit must be recorded as `contamination_report.json`.

## 12. Metric Bridge Freshness

Required review states:

- `bridge_missing`
- `bridge_stale`
- `bridge_current`
- `bridge_fresh_enough_for_measurement_review`

Rules:

- missing or stale bridge => `operational_utility_only` or `ambiguous`;
- bridge freshness alone is not measurement validation;
- metric bridge reviewer must record decision and evidence reference;
- Flash and Pro may need separate bridge review if behavior diverges.

## 13. Claim Gate Decision Table

| Evidence state | Allowed claim | Denied claim |
| --- | --- | --- |
| Dry-run only | `engineering_smoke_only` | `measurement_validated`, scientific validation |
| Live run without labels | `controlled_live_pilot_only` | `measurement_validated` |
| Live run with missing kappa | Not `measurement_validated` | Validation-level claim |
| Live run with low kappa | `pilot_only` or weak evidence | `measurement_validated` |
| Contamination failure | `pilot_only` | Any validation-level claim |
| Stale metric bridge | `operational_utility_only` or `ambiguous` | `measurement_validated` |
| Flash-only favorable live outputs | Model-conditioned operational observation | `measurement_validated` |
| Pro-only favorable live outputs | Model-conditioned operational observation | `measurement_validated` |
| Flash+Pro favorable live outputs without labels/kappa | Operational observation only | `measurement_validated` |
| Complete favorable evidence | `measurement_validated_candidate` | Final validation without claim gate allow |
| Claim gate explicitly allows all requirements | Gate-scoped `measurement_validated` only | Claims beyond scoped run |

## 14. Abort / Fail-Closed Conditions

Abort or fail closed if:

- manifest missing;
- operator approval missing;
- `CPS_ALLOW_LIVE_API` not set in live mode;
- model endpoint/model/prompt not fixed;
- model alias missing;
- output root already contains incompatible artifacts;
- schema validation fails;
- artifact completeness fails;
- contamination check fails;
- labels missing;
- kappa missing;
- metric bridge stale or missing;
- unexpected external dependency import is needed;
- live API errors prevent reproducible artifact capture;
- budget cap exceeded;
- Flash/Pro outputs are mixed without model condition identifiers;
- prompt or case set changes mid-run.

## 15. Budget And Cost Control

DeepSeek V4 Flash should be used as the primary pilot model for cost efficiency.
DeepSeek V4 Pro should be used as a stronger-model audit subset.

Rules:

- budget cap must be declared before the run;
- stop if projected cost exceeds the cap;
- record token counts if available;
- record case count and condition count;
- do not silently expand sample size;
- do not retry failed cases indefinitely;
- retries must be bounded and recorded;
- use placeholders for budget values until operators provide exact caps;
- do not include exact prices unless supplied by the operator in a future
  manifest or budget record.

## 16. Manuscript Impact

After EV2 only, the manuscript may report:

- controlled live pilot evidence;
- operational observations;
- model-conditioned observations for DeepSeek V4 Flash and Pro;
- no `measurement_validated` claim.

After EV3 with labels and kappa, the manuscript may report:

- human-labeled pilot evidence;
- kappa-supported annotation reliability;
- still not `measurement_validated` unless contamination and metric bridge pass.

After EV4 with fresh metric bridge and claim gate review, the manuscript may
report:

- possible `measurement_validated_candidate`;
- final wording only as allowed by the claim gate.

Forbidden manuscript wording:

- "DeepSeek V4 validates the method"
- "Pro proves CPS works"
- "Flash/Pro results certify V-information"
- "live API success proves measurement validation"
- "high kappa alone validates CPS"

Allowed cautious wording:

- "controlled live pilot on DeepSeek V4 Flash / Pro"
- "model-conditioned operational evidence"
- "human-labeled pilot evidence when labels exist"
- "`measurement_validated_candidate` only if all gates pass"

## 17. Minimal Command Sketch

No matching executable `python -m` CLI entrypoints currently exist for the P26
controlled live pilot runner, P27 label/kappa artifact builder, P28
contamination audit, or P28 empirical evidence package builder. P29 therefore
does not prescribe executable commands.

Current operational interface:

| Step | Current interface |
| --- | --- |
| Dry-run rehearsal | Function/API currently available; CLI not required in P29. |
| Operator-approved live run | Function/API currently available with injected model call boundary; CLI not required in P29. |
| Human label template generation | Function/API currently available; CLI not required in P29. |
| Kappa report | Function/API currently available; CLI not required in P29. |
| Contamination audit report | Function/API currently available; CLI not required in P29. |
| Empirical evidence package | Function/API currently available; CLI not required in P29. |

Do not run these steps from this runbook. A future P30 dry-run rehearsal can
decide whether a CLI wrapper is needed, but P29 does not add one.

## 18. Final Claim Boundary

- P29 is runbook only.
- P29 does not run live APIs.
- P29 does not add API clients or external SDKs.
- P29 does not fabricate human labels, kappa, contamination pass, or bridge
  freshness.
- DeepSeek V4 Flash and DeepSeek V4 Pro are model conditions, not validation
  authorities.
- Live success on either model is not measurement validation.
- High kappa alone is not measurement validation.
- Contamination pass alone is not measurement validation.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
- `measurement_validated` is not claimed.
