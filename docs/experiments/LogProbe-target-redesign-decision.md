# LogProbe Target Redesign Decision

Claim status: operational_utility_only/no_claim_upgrade

Primary decision: SWITCH_TO_EVIDENCE_PATH_NLL
Secondary decision: ABANDON_LOGPROBE_BRIDGE_FOR_CURRENT_STRATUM
Disabled decisions: SWITCH_TO_FEVER_LABEL_NLL

## Rejected decisions

- KEEP_CURRENT_TARGET_AND_SCALE: current_answer_nll_alignment_weak
- SWITCH_TO_SUFFICIENCY_CLASSIFIER_NLL: support_classifier_target_verbalization_risk_present
- SWITCH_TO_OPTION_NLL: no_existing_option_nll_artifacts_in_scope

## Required unlocks

- independent_review_before_lp6
- operator_approval_before_any_future_live_scoring
- new_target_shadow_stability_check
- fresh_measured_delta_logloss_rows_for_new_target

No bridge repair run was executed.
