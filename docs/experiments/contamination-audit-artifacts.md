# Contamination Audit Artifacts

**Phase:** P28 Contamination and Live Evidence Package Integration

**Status:** EV2/EV3/EV4 evidence packaging input. P28 does not run live APIs,
fabricate contamination clearance, fabricate labels, fabricate kappa, or claim
`measurement_validated`.

## 1. Purpose

P28 adds deterministic contamination-audit artifacts for future empirical
validation packages. The audit records whether validation cases, labels,
answers, prompts, candidate pools, baselines, or annotators were exposed in a
way that makes the comparison unfair.

Hard rule:

```text
contamination failure => pilot_only
```

Contamination pass is necessary but not sufficient. Human labels, acceptable
kappa, fresh metric bridge evidence, complete artifacts, and existing claim gate
approval remain required.

## 2. Required Checks

The contamination audit covers these checks in stable order:

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

Each check records:

- `check_name`
- `status: pass | fail | unknown`
- `evidence_ref`
- `notes`

The empty template sets all checks to `unknown`. It is an annotation/audit
template only and does not fabricate a contamination pass.

## 3. Outcome Mapping

| Audit state | Output status | Claim effect |
| --- | --- | --- |
| Any failed check | `failed` | Force `pilot_only`. |
| Required check missing | `incomplete` | Deny `measurement_validated`. |
| Required check unknown | `unknown` | Deny `measurement_validated`. |
| All checks pass | `pass` | Contamination gate passed only; not validation. |

Reason codes are deterministic. Failed checks preserve specific reason codes
where they affect the claim gate, including leaked labels, direct answers in the
candidate pool, unfair baseline access, annotator leakage, duplicates, and
post-hoc prompt tuning.

## 4. Outputs

P28 can write:

- `contamination_report.json`
- `contamination_report.md`

The report includes:

- `contamination_status`
- `contamination_passed`
- `failed_checks`
- `unknown_checks`
- `allowed_claim_impact`
- `measurement_validated_allowed`
- `denied_claims`
- stable `reason_codes`

`measurement_validated_allowed` remains `false` in the contamination artifact
because contamination pass alone is not measurement validation.

## 5. Claim Boundary

- P28 packages contamination audit artifacts only.
- P28 does not run live APIs.
- P28 does not fabricate contamination pass for real data.
- P28 does not fabricate labels or kappa.
- Contamination failure forces `pilot_only`.
- Unknown or incomplete contamination denies `measurement_validated`.
- Live API success alone is not measurement validation.
- High kappa alone is not measurement validation.
- Fresh metric bridge and claim gate approval remain required.
- P04 remains deferred/operator-required.
- P09 remains `BLOCKED_OPERATOR_REQUIRED`.
