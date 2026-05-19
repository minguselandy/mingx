from __future__ import annotations

from cps.analysis.logprobe_stability import build_logprobe_stability_reports
from cps.evaluators.logprobe_target_contract import build_canonical_target_contract


def test_stability_reports_detect_tokenization_and_shadow_only_risk():
    contract = build_canonical_target_contract(
        materialization_policy="fixed_selector_order_with_source_boundaries",
        prompt_template="Question: {question}\nAnswer:",
        row_provenance={"route": "Route4A"},
        target_provenance={"dataset": "HotpotQA"},
        target_type="answer_string",
        target_representation="hotpotqa_canonical_answer_string",
        tokenization_policy="teacher_forced_full_target_sequence_v1",
        verbalizer_policy="literal_answer_string_no_label_verbalizer",
    )
    route_rows = [
        {
            "context_L_packet_ids": ["a", "b"],
            "delta_logloss": -0.0001,
            "materialization_policy": "fixed_selector_order_with_source_boundaries",
            "target_y": "multi token answer",
        },
        {
            "context_L_packet_ids": [],
            "delta_logloss": 0.4,
            "materialization_policy": "fixed_selector_order_with_source_boundaries",
            "target_y": "short",
        },
    ]

    reports = build_logprobe_stability_reports(
        answer_generation_report={"api_retries": 1, "api_failures": [], "delta_records_validated": 2},
        contract=contract,
        route4_rows=route_rows,
        support_generation_report={
            "api_retries": 2,
            "api_failures": ["support classifier emitted NON_SUPPORTING expected SUPPORTING"],
            "delta_records_validated": 1,
        },
    )

    assert reports["logprobe_stability_matrix"]["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert reports["logprobe_stability_matrix"]["new_live_api_calls"] is False
    assert reports["logprobe_stability_matrix"]["fever_disabled"] is True
    assert reports["logprobe_stability_matrix"]["logprobe_stability_passed"] is False
    assert reports["tokenization_risk_report"]["multi_token_target_risk"]["status"] == "present"
    assert reports["materialization_sensitivity_report"]["materialization_policy_count"] == 1
