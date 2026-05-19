from __future__ import annotations

from cps.evaluators.logprobe_scorer import score_logprobe_shadow
from cps.evaluators.logprobe_target_contract import build_canonical_target_contract


def _contract() -> dict:
    return build_canonical_target_contract(
        materialization_policy="fixed_selector_order_with_source_boundaries",
        prompt_template="Question: {question}\nAnswer:",
        row_provenance={"route": "Route4A"},
        target_provenance={"dataset": "HotpotQA"},
        target_type="answer_string",
        target_representation="hotpotqa_canonical_answer_string",
        tokenization_policy="teacher_forced_full_target_sequence_v1",
        verbalizer_policy="literal_answer_string_no_label_verbalizer",
    )


def test_shadow_logprobe_scorer_never_calls_live_api_or_emits_scores():
    result = score_logprobe_shadow(
        _contract(),
        {
            "materialization_policy": "fixed_selector_order_with_source_boundaries",
            "target_representation": "hotpotqa_canonical_answer_string",
            "target_y": "gold answer",
        },
    )

    assert result["score_available"] is False
    assert result["live_api_used"] is False
    assert result["new_live_api_calls"] is False
    assert result["fixed_model_logloss_available"] is False
    assert result["claim_status"] == "operational_utility_only/no_claim_upgrade"


def test_shadow_logprobe_scorer_flags_contract_row_mismatch_without_scoring():
    row = {
        "materialization_policy": "different_policy",
        "target_representation": "hotpotqa_canonical_answer_string",
        "target_y": "gold answer",
    }

    result = score_logprobe_shadow(_contract(), row)

    assert result["score_available"] is False
    assert result["contract_validation"]["passed"] is False
    assert "materialization_policy_mismatch" in result["contract_validation"]["errors"]
    assert result["new_live_api_calls"] is False
