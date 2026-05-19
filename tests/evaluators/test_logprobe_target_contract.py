from __future__ import annotations

import pytest

from cps.evaluators.logprobe_target_contract import build_canonical_target_contract
from cps.evaluators.logprobe_target_contract import validate_target_contract


def test_canonical_target_contract_contains_required_hashes_and_provenance():
    contract = build_canonical_target_contract(
        materialization_policy="fixed_selector_order_with_source_boundaries",
        prompt_template="Question: {question}\nAnswer:",
        row_provenance={"route": "Route4A", "source": "existing_bridge_rows"},
        target_provenance={"dataset": "HotpotQA", "split": "dev_distractor"},
        target_type="answer_string",
        target_representation="hotpotqa_canonical_answer_string",
        tokenization_policy="teacher_forced_full_target_sequence_v1",
        verbalizer_policy="literal_answer_string_no_label_verbalizer",
    )

    assert contract["teacher_forced_scoring_required"] is True
    assert contract["target_type"] == "answer_string"
    assert contract["fixed_target_representation"] == "hotpotqa_canonical_answer_string"
    assert contract["target_format_hash"]
    assert contract["prompt_template_hash"]
    assert contract["materialization_policy_hash"]
    assert contract["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert validate_target_contract(contract)["passed"] is True


def test_target_contract_rejects_missing_teacher_forced_policy():
    contract = build_canonical_target_contract(
        materialization_policy="fixed_selector_order_with_source_boundaries",
        prompt_template="Question: {question}\nAnswer:",
        row_provenance={"route": "Route4A"},
        target_provenance={"dataset": "HotpotQA"},
        target_type="answer_string",
        target_representation="hotpotqa_canonical_answer_string",
        teacher_forced_scoring_required=False,
        tokenization_policy="teacher_forced_full_target_sequence_v1",
        verbalizer_policy="literal_answer_string_no_label_verbalizer",
    )

    validation = validate_target_contract(contract)

    assert validation["passed"] is False
    assert "teacher_forced_scoring_required_false" in validation["errors"]


def test_target_contract_rejects_active_fever_target():
    with pytest.raises(ValueError, match="FEVER"):
        build_canonical_target_contract(
            materialization_policy="fixed_selector_order_with_source_boundaries",
            prompt_template="Claim: {claim}\nLabel:",
            row_provenance={"route": "Route4C"},
            target_provenance={"dataset": "FEVER"},
            target_type="fever_label",
            target_representation="fever_label_string",
            tokenization_policy="teacher_forced_full_target_sequence_v1",
            verbalizer_policy="fever_label_verbalizer",
        )
