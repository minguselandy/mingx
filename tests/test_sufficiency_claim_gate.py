from __future__ import annotations

from cps.evaluation.sufficiency_regime import (
    SufficiencyRegimeRecord,
    evaluate_sufficiency_claim_gate,
)
from cps.replay.reprojection_witness import ReprojectionWitness


def _record(record_id, **overrides):
    payload = {
        "record_id": record_id,
        "item_id": record_id,
        "judge_label": "support",
        "projected_evidence_sufficient": True,
        "answer_emitted": True,
        "abstained": False,
        "missing_evidence_types": [],
        "input_token_count": 50,
        "output_token_count": 8,
        "raw_response_stored": False,
        "live_api_call_performed": False,
    }
    payload.update(overrides)
    return SufficiencyRegimeRecord.from_dict(payload)


def _witness(witness_id, **overrides):
    payload = {
        "witness_id": witness_id,
        "item_id": witness_id,
        "trigger_label": "insufficient_and_answered",
        "intervention_type": "restore_excluded_evidence_span",
        "downstream_prompt_template_hash": "downstream-hash",
        "model_snapshot": "static-model-snapshot",
        "endpoint": "static-endpoint",
        "thinking_mode": "disabled",
        "decoding_policy": {"temperature": 0, "top_p": 1},
        "token_budget_accounting_method": "offline_token_estimate_v1",
        "original_budget_tokens": 80,
        "reprojected_budget_tokens": 92,
        "selector_before": "greedy",
        "selector_after": "pair_aware_local_search",
        "context_hash_before": "before",
        "context_hash_after": "after",
        "context_diff_hash": "diff",
        "before_output_hash": "before-output",
        "after_output_hash": "after-output",
        "repair_status": "reprojection_candidate",
        "raw_response_stored": False,
        "live_api_call_performed": False,
    }
    payload.update(overrides)
    return ReprojectionWitness.from_dict(payload)


def test_sufficiency_claim_gate_reports_operational_diagnostics_only() -> None:
    gate = evaluate_sufficiency_claim_gate(
        records=[
            _record("kept"),
            _record(
                "unsafe",
                projected_evidence_sufficient=False,
                judge_label="insufficient",
            ),
            _record(
                "abstain",
                projected_evidence_sufficient=False,
                answer_emitted=False,
                abstained=True,
                judge_label="uncertain",
            ),
        ],
        witnesses=[_witness("unsafe")],
    )

    assert gate["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert gate["allowed_claims"] == ["sufficiency_abstention_diagnostic_only"]
    assert gate["final_gate_status"] == "offline_framework_ready_live_api_not_run"
    assert gate["candidate_operational_evidence_only"] is True
    assert gate["measurement_validation_claim"] is False
    assert gate["truth_validation_claim"] is False
    assert gate["calibrated_abstention_claim"] is False
    assert gate["raw_response_stored"] is False
    assert gate["live_api_call_performed"] is False
    assert gate["route_5_locked"] is True
    assert gate["route_8_locked"] is True
    assert gate["metrics"]["unsupported_answer_rate"] == 1 / 3
    assert gate["metrics"]["abstain_rate"] == 1 / 3
    assert gate["metrics"]["reprojection_repair_rate"] == 1.0
    assert "measurement_validation" in gate["denied_claims"]
    assert "truth_validation" in gate["denied_claims"]
    assert "calibrated_abstention" in gate["denied_claims"]


def test_sufficiency_claim_gate_suppresses_claim_when_parse_failures_exceed_threshold() -> None:
    gate = evaluate_sufficiency_claim_gate(
        records=[
            _record("ok"),
            _record("bad", judge_label="parse_failed", parse_status="parse_failed"),
        ],
        witnesses=[],
    )

    assert gate["final_gate_status"] == "downgraded_to_ambiguous"
    assert gate["allowed_claims"] == []
    assert "parse_failure_rate_above_threshold" in gate["reason_codes"]
    assert gate["metrics"]["parse_failure_rate"] == 0.5


def test_sufficiency_claim_gate_suppresses_claim_when_witness_is_not_comparable() -> None:
    gate = evaluate_sufficiency_claim_gate(
        records=[_record("unsafe", projected_evidence_sufficient=False, judge_label="insufficient")],
        witnesses=[
            _witness(
                "unsafe",
                repair_status="not_comparable_control_mismatch",
                trigger_label="insufficient_and_answered",
            )
        ],
    )

    assert gate["final_gate_status"] == "downgraded_to_ambiguous"
    assert gate["allowed_claims"] == []
    assert "non_comparable_reprojection_witness" in gate["reason_codes"]
