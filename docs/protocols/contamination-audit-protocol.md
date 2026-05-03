# Contamination Audit Protocol

**Status:** Future contamination audit protocol. This document does not execute a
contamination audit, run live APIs, or clear any empirical claim gate.

## 1. Purpose

Contamination auditing prevents a controlled empirical run from being interpreted
as validation when cases, labels, answers, prompts, annotators, or baselines have
been exposed in ways that make the comparison unfair.

Hard rule:

```text
contamination failure => pilot_only
```

Engineering completion, replay completeness, kappa, or live API success cannot
override a contamination failure.

## 2. Audit Scope

The contamination audit covers:

- case selection;
- prompt development;
- candidate pool construction;
- baseline and CPS condition access;
- annotator exposure;
- duplicate or near-duplicate examples;
- post-hoc tuning;
- run manifest lineage.

The audit must be completed before any validation-level claim is considered.

## 3. Required Checks

| Check | Failure example | Required action |
| --- | --- | --- |
| Leaked labels | Gold labels, expected answers, or adjudication labels are visible to model prompts or condition builders. | Mark affected cases contaminated; validation claim denied. |
| Cases seen during prompt/dev | Test cases are used to tune prompts, selectors, thresholds, or rubrics. | Exclude cases or mark run as pilot only. |
| Candidate pool directly containing answers | Candidate text includes answer strings in a way unavailable to fair baselines or not intended by the task. | Audit whether this is valid evidence or leakage; fail if unfair. |
| Unfair baseline access | CPS and baseline conditions see different hidden evidence or labels. | Invalidate comparison or rerun with equalized access. |
| Annotator leakage | Annotators see condition identities, expected outcomes, prior labels, or hidden answers outside the rubric. | Remove affected labels or rerun annotation. |
| Duplicated examples | Test cases duplicate training, calibration, prompt-development, or annotator-training examples. | Exclude duplicates or downgrade to pilot. |
| Post-hoc prompt tuning on test cases | Prompt or selector changes are made after observing test outcomes and then evaluated on the same cases. | Contamination failure for validation purposes. |

## 4. Case Exposure Review

Before execution, the operator must classify each case:

| Status | Meaning | Validation effect |
| --- | --- | --- |
| `clean` | No known leakage or prompt/dev exposure. | Eligible. |
| `suspect` | Possible exposure or duplicate risk. | Requires review before inclusion. |
| `contaminated` | Known leakage, duplicate, or unfair exposure. | Exclude or force pilot-only interpretation. |
| `unknown` | Insufficient provenance. | Treat conservatively; not validation-ready. |

The case manifest must preserve the status and rationale.

## 5. Candidate Pool Review

The candidate pool audit must check whether:

- the answer string appears directly in candidate text;
- answer-containing evidence is legitimate task context or leakage;
- CPS and baselines receive comparable evidence access;
- candidate generation used labels, adjudication, or hidden answers;
- candidate generation was tuned after observing test outcomes.

If the candidate pool directly contains answers in a way that makes the task
trivial or gives one condition unfair access, the affected comparison cannot
support validation.

## 6. Prompt And Selector Lineage

The run manifest must preserve:

- prompt template id and content hash;
- selector configuration id and content hash;
- metric bridge configuration;
- label rubric version;
- case manifest hash;
- pre-execution approval record;
- any protocol deviations.

Prompt, selector, or rubric changes after seeing test outcomes require a new run
manifest and a new evaluation split. Silent post-hoc tuning is contamination.

## 7. Annotator Leakage Review

Annotator instructions must prevent exposure to:

- condition identity where blinding is feasible;
- hidden expected condition ranking;
- prior annotator labels;
- claim gate outputs;
- aggregate model performance summaries;
- gold labels not required by the rubric.

If annotator leakage affects validation-critical labels, the labels must be
excluded or recollected under a clean protocol.

## 8. Contamination Report

The contamination report is saved as `contamination_report.json` and must include:

- run id;
- case ids reviewed;
- checks performed;
- clean/suspect/contaminated/unknown counts;
- case-level contamination decisions;
- prompt and selector lineage review;
- annotator leakage review;
- baseline fairness review;
- final contamination status: `passed`, `failed`, or `inconclusive`;
- claim gate effect.

Recommended mapping:

| Final status | Claim gate effect |
| --- | --- |
| `passed` | Contamination gate can pass to the next evidence gate. |
| `inconclusive` | `measurement_validated` remains denied; repeat or narrow scope. |
| `failed` | Force `pilot_only`. |

## 9. Relationship To Claim Gate

The contamination report must be attached to the evidence ledger or equivalent
claim-gate input. The claim gate must preserve the reason code when contamination
fails or is missing.

Contamination pass is necessary but not sufficient. Validation still requires
complete artifacts, controlled live run evidence, human labels, acceptable kappa,
fresh metric bridge, and claim gate allow.
