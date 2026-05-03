# Human Label And Kappa Protocol

**Status:** Future human-label protocol. This document does not execute labeling,
select annotators, compute kappa, or claim `measurement_validated`.

## 1. Purpose

Human labels and agreement evidence are required before any empirical run can be
considered for measurement-validation review. Missing human labels or missing
kappa blocks `measurement_validated` regardless of replay completeness, live API
success, or engineering success.

## 2. Labeling Unit

Each label record is attached to one `(case_id, condition_id)` output. The label
packet shown to annotators should include:

- input case text and permitted evidence;
- model output;
- materialized context or a reviewable summary of it;
- condition identifier without revealing the experimental hypothesis;
- rubric definitions;
- fields for dimension scores and free-text rationale.

Annotators must not see hidden expected outcomes, prior annotator labels, kappa
results, claim gate outputs, or condition-performance summaries during primary
labeling.

## 3. Label Dimensions

All dimensions use the same 0/1/2 scale.

| Dimension | Question answered by the label |
| --- | --- |
| `answer_correctness` | Is the final answer correct for the case? |
| `answer_completeness` | Does the answer cover all required parts? |
| `answer_groundedness` | Is the answer supported by the supplied context and evidence? |
| `context_sufficiency` | Was enough relevant context present to answer correctly? |
| `missing_critical_context` | Did the context omit information needed for a correct answer? |
| `irrelevant_context_rate` | Was the context polluted by irrelevant material? |
| `misleading_context` | Did the context include material that could mislead the model? |
| `conflict_or_stale_context` | Did the context include conflicts, obsolete information, or stale evidence? |

## 4. Label Scale

| Score | Meaning | General rule |
| --- | --- | --- |
| 0 | fail | The dimension fails materially. |
| 1 | partial | The dimension is mixed, incomplete, or requires caveat. |
| 2 | pass | The dimension satisfies the rubric for the scoped case. |

For negative dimensions such as `missing_critical_context`, `misleading_context`,
and `conflict_or_stale_context`, the project must define polarity before
execution. The recommended default is:

- `0`: severe problem present;
- `1`: minor or ambiguous problem present;
- `2`: no material problem detected.

The run manifest must record this polarity so kappa computation is interpretable.

## 5. Annotator Requirements

Minimum requirements:

- at least two independent annotators for every validation-scoped case;
- annotator training on the rubric before labeling;
- blind primary labeling where feasible;
- no annotator access to hidden labels, condition summaries, or expected
  condition ranking;
- adjudication for material disagreement;
- preserved annotator rationales for audit.

If fewer than two annotators label the validation-scoped cases,
`measurement_validated` is blocked.

## 6. Adjudication

Adjudication is required when:

- annotators differ by two points on any dimension;
- one annotator flags missing critical context and another does not;
- one annotator flags misleading or stale context and another does not;
- aggregate correctness/completeness differs enough to affect condition ranking;
- kappa falls below the minimum review threshold and disagreement analysis is
  needed.

Adjudication output is saved as `adjudication.json` and must include:

- case id;
- condition id;
- disputed dimensions;
- primary labels;
- adjudicated label;
- adjudicator rationale;
- whether the case remains eligible for validation aggregation.

## 7. Kappa Computation

The kappa report must specify:

- annotator pair or pool;
- label dimension;
- number of labeled items;
- label distribution;
- unweighted or weighted kappa choice;
- confidence interval method;
- exclusions;
- final threshold bucket.

Recommended default:

- compute Cohen's kappa for two annotators per dimension;
- use weighted kappa for ordinal 0/1/2 labels when implementation support is
  available;
- report unweighted kappa as a sensitivity check if weighted kappa is used;
- compute bootstrap confidence intervals when sample size allows;
- report dimension-level kappa and an aggregate conservative interpretation.

The aggregate interpretation should use the weakest validation-critical dimension
unless the protocol pre-registers a different aggregation rule.

## 8. Conservative Kappa Thresholds

| Kappa range | Interpretation | Allowed claim effect |
| --- | --- | --- |
| `kappa < 0.40` | Poor or unstable agreement. | `pilot_only`; revise rubric or annotator training. |
| `0.40 <= kappa < 0.60` | Weak evidence. | Not `measurement_validated`; may support pilot diagnostics only. |
| `0.60 <= kappa < 0.75` | Limited measurement review candidate. | May support `measurement_validated_candidate` only if other gates pass. |
| `kappa >= 0.75` | Stronger measurement review candidate. | May support validation review, but never grants validation alone. |

Kappa alone does not claim `measurement_validated`. It must be combined with
complete artifacts, controlled live run evidence, contamination pass, fresh metric
bridge, and claim gate allow.

## 9. Low-Kappa Response

If kappa is low:

1. Do not claim `measurement_validated`.
2. Preserve the failed kappa report.
3. Analyze disagreement by dimension, condition, case type, and annotator.
4. Revise the rubric only on a new training or calibration set.
5. Do not tune the rubric on held-out test outcomes and then reuse the same
   cases for validation.
6. Repeat labeling only under a new manifest version with lineage preserved.

Low kappa is a measurement failure, not an engineering failure.

## 10. Required Outputs

The labeling workstream must produce:

- `human_labels.jsonl`;
- `adjudication.json`;
- `kappa_report.json`;
- label rubric version;
- annotator training record;
- exclusion record;
- claim-boundary summary.

Missing `human_labels.jsonl`, missing `adjudication.json` when adjudication is
required, or missing `kappa_report.json` blocks validation-level claims.
