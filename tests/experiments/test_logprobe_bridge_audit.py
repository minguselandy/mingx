from __future__ import annotations

import json
from pathlib import Path

import pytest

from cps.benchmarks.hashing import canonical_json_dumps
from cps.experiments.logprobe_bridge_audit import CLAIM_STATUS
from cps.experiments.logprobe_bridge_audit import LogProbeAuditInputMissingError
from cps.experiments.logprobe_bridge_audit import run_logprobe_bridge_audit


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical_json_dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def _route_row(index: int, *, utility_field: str, utility_value: float, delta_logloss: float) -> dict:
    return {
        "candidate_pool_hash": f"pool-{index}",
        "delta_logloss": delta_logloss,
        utility_field: utility_value,
        "original_instance_id": f"hotpot-{index}",
    }


def _build_required_inputs(root: Path) -> None:
    _write_json(
        root / "artifacts/benchmarks/hotpotqa_p55_delta_generation_report.json",
        {
            "api_failures": [],
            "api_retries": 1,
            "delta_records_validated": 600,
            "evaluator": {"evaluator_id": "approved-live", "model_name": "qwen-test"},
            "score_calls": 750,
        },
    )
    _write_json(
        root / "artifacts/benchmarks/hotpotqa_support_classification_delta_generation_report.json",
        {
            "api_failures": [
                {"error": "expected valid support label but got unsupported_token"},
                {"error": "network timeout"},
            ],
            "api_retries": 2,
            "delta_records_validated": 643,
            "score_calls": 1286,
        },
    )

    _write_json(
        root / "artifacts/experiments/route4_bridge/bridge_fit_summary.json",
        {
            "bridge_fit": {"c_hat_s": -13.28, "normalized_residual": 4.94},
            "claim_status": "no_claim_upgrade",
            "effective_sample_size": 600,
            "gate_pass_flags": {
                "effective_sample_size": True,
                "normalized_residual": False,
                "row_count": True,
                "sign_agreement": False,
                "spearman_rho": False,
                "unique_original_instances": True,
            },
            "gate_result": "failed_closed_gate_failed",
            "reason_codes": ["normalized_residual_failed", "sign_agreement_failed", "spearman_rho_failed"],
            "rows_validated": 600,
            "sign_agreement": 0.16,
            "spearman_rho": -0.19,
            "unique_original_instances": 150,
        },
    )
    _write_jsonl(
        root / "artifacts/experiments/route4_bridge/bridge_rows.jsonl",
        [
            _route_row(1, utility_field="delta_utility", utility_value=1.0, delta_logloss=-0.001),
            _route_row(2, utility_field="delta_utility", utility_value=1.0, delta_logloss=0.0001),
            _route_row(3, utility_field="delta_utility", utility_value=0.0, delta_logloss=0.0),
        ],
    )
    _write_json(
        root / "artifacts/experiments/route4b_bridge_to_measurement/bridge_fit_summary.json",
        {
            "claim_status": "no_claim_upgrade",
            "effective_sample_size": 300,
            "gate_pass_flags": {
                "normalized_residual_pass": False,
                "row_count_pass": False,
                "sign_agreement_pass": False,
                "spearman_rho_pass": False,
            },
            "gate_result": "failed_closed_underpowered",
            "reason_codes": ["row_count_below_minimum", "model_adjudication_not_human_measurement_validation"],
            "rows_validated": 300,
            "sign_agreement": 0.38,
            "spearman_rho": 0.23,
            "unique_original_instances": 150,
        },
    )
    _write_jsonl(
        root / "artifacts/experiments/route4b_bridge_to_measurement/bridge_rows.jsonl",
        [
            _route_row(1, utility_field="delta_external_sufficiency_utility", utility_value=1.0, delta_logloss=-0.001),
            _route_row(2, utility_field="delta_external_sufficiency_utility", utility_value=0.0, delta_logloss=0.0001),
        ],
    )

    _write_json(
        root / "artifacts/experiments/route6b_measurement_scaleup/adjudication_report.json",
        {
            "accepted_model_adjudicated_count": 300,
            "counts_as_human_labels": False,
            "live_api_used": True,
            "measurement_validation_candidate_allowed": False,
            "raw_api_responses_stored": False,
        },
    )
    _write_json(
        root / "artifacts/experiments/route6b_measurement_scaleup/readiness_report.json",
        {
            "accepted_model_adjudicated_count": 300,
            "claim_status": "no_claim_upgrade",
            "human_annotation_status": "blocked_human_annotation_required",
            "measurement_validation_candidate_allowed": False,
            "status": "measurement_candidate_ready",
        },
    )
    _write_json(
        root / "artifacts/experiments/route6b_measurement_scaleup/sample_manifest.json",
        {"judge_hidden_fields": ["delta_logloss", "delta_utility"], "sample_count": 300},
    )

    _write_json(
        root / "artifacts/experiments/delta_strong_model_adjudication/final_status.json",
        {
            "claim_status": CLAIM_STATUS,
            "live_api_used": False,
            "raw_api_responses_stored": False,
            "terminal_status": "FAILED_CLOSED_JUDGE_RELIABILITY",
        },
    )
    _write_json(
        root / "artifacts/experiments/delta_strong_model_adjudication/judge_reliability_audit.json",
        {
            "challenge_checks": {
                "duplicate": False,
                "invalid_rate": False,
                "order_reversal": True,
                "prompt_sensitivity": False,
                "three_view": False,
            },
            "invalid_label_rate": 0.06125,
            "minority_veto_count": 481,
            "order_reversal_stability": {"match_rate": 0.795},
            "status": "FAILED_CLOSED_JUDGE_RELIABILITY",
        },
    )
    _write_json(
        root / "artifacts/experiments/delta_strong_model_adjudication/model_adjudication_scaleup_report.json",
        {
            "adjudicated_item_count": 800,
            "reason_codes": ["three_view_item_count_below_minimum"],
            "status": "failed_closed_underpowered",
            "three_view_item_count": 0,
            "unique_original_instance_count": 150,
        },
    )
    _write_json(
        root / "artifacts/experiments/delta_strong_model_adjudication/route4e_bridge_fit_summary.json",
        {
            "claim_status": CLAIM_STATUS,
            "gate_result": "failed_closed_gate_failed",
            "reason_codes": ["normalized_residual_failed", "sign_agreement_failed", "spearman_rho_failed"],
            "rows_validated": 800,
            "sign_agreement": 0.42,
            "spearman_rho": 0.24,
            "unique_original_instances": 150,
        },
    )
    _write_jsonl(
        root / "artifacts/experiments/delta_strong_model_adjudication/route4e_bridge_rows.jsonl",
        [
            _route_row(1, utility_field="delta_hybrid_utility", utility_value=1.0, delta_logloss=-0.001),
            _route_row(2, utility_field="delta_hybrid_utility", utility_value=0.0, delta_logloss=0.0001),
        ],
    )
    _write_json(
        root / "artifacts/experiments/delta_strong_model_adjudication/route4e_metric_bridge_witness.json",
        {"calibrated_proxy_supported": False, "metric_bridge_support_candidate": False, "vinfo_proxy_supported": False},
    )
    _write_json(
        root / "artifacts/experiments/delta_strong_model_adjudication/route4e_negative_controls.json",
        {"claim_enabling": False, "status": "diagnostic_only_not_claim_enabling"},
    )

    _write_json(
        root / "artifacts/experiments/route5_fixed_model_logloss_proxy/readiness_report.json",
        {
            "fixed_model_logloss_proxy_verification_started": False,
            "metric_bridge_support": False,
            "start_condition_satisfied": False,
            "status": "skipped_no_bridge_candidate",
            "vinfo_proxy_supported": False,
        },
    )
    for workbench_dir in (
        root / "artifacts/experiments/integrated_validation_workbench/hotpotqa_smoke",
        root / "artifacts/experiments/gamma_operational_expansion/workbench_hotpotqa",
        root / "artifacts/experiments/gamma_operational_expansion/workbench_project_native",
    ):
        _write_json(
            workbench_dir / "bridge_fit_summary.json",
            {"bridge_status": "failed_closed_no_rows", "effective_sample_size": 0, "rows_validated": 0},
        )
        _write_json(
            workbench_dir / "claim_gate_result.json",
            {"calibrated_proxy_supported": False, "claim_status": CLAIM_STATUS, "vinfo_proxy_supported": False},
        )


def test_logprobe_audit_reports_preserve_claim_boundary_and_failure_factors(workspace_tmp_dir):
    _build_required_inputs(workspace_tmp_dir)

    result = run_logprobe_bridge_audit(root=workspace_tmp_dir, output_dir=workspace_tmp_dir / "audit")

    assert result["terminal_status"] == "LOGPROBE_BRIDGE_AUDIT_COMPLETED"
    assert result["claim_status"] == CLAIM_STATUS
    assert result["route5_unlocked"] is False
    assert result["route8_unlocked"] is False
    assert set(result["artifacts"]) == {
        "logprobe_stability_report",
        "next_logprobe_repair_plan",
        "route4_failure_decomposition",
        "utility_logloss_alignment_report",
    }

    stability = json.loads((workspace_tmp_dir / "audit/logprobe_stability_report.json").read_text(encoding="utf-8"))
    assert stability["new_live_api_calls"] is False
    assert stability["generation_reports"]["answer_nll"]["score_calls"] == 750
    assert stability["logloss_evaluator_path_audit"]["metrics"]["fixed_model_logloss_available"] is False
    assert stability["logloss_evaluator_path_audit"]["claim_flags"]["vinfo_proxy_supported"] is False
    assert stability["failure_factor_assessment"]["target_verbalization_tokenization"]["status"] == "present"
    assert stability["route5_logloss_proxy_gate"]["fixed_model_logloss_proxy_verification_started"] is False

    alignment = json.loads((workspace_tmp_dir / "audit/utility_logloss_alignment_report.json").read_text(encoding="utf-8"))
    assert alignment["claim_status"] == CLAIM_STATUS
    assert alignment["claim_gate_summary"]["calibrated_proxy_supported"] is False
    assert alignment["routes"]["Route4A"]["weak_utility_logloss_alignment"] is True
    assert alignment["routes"]["Route4B"]["underpowered_rows"] is True
    assert alignment["routes"]["Route4B"]["weak_utility_logloss_alignment"] is True

    decomposition = json.loads((workspace_tmp_dir / "audit/route4_failure_decomposition.json").read_text(encoding="utf-8"))
    assert decomposition["overall_status"] == "failed_closed_no_claim_upgrade"
    assert decomposition["failure_factors"]["judge_label_noise"]["status"] == "present"
    assert decomposition["failure_factors"]["bridge_gate_strictness"]["recommendation"] == "do_not_relax_claim_gate"
    assert decomposition["locked_routes"]["Route5"] == "locked_no_accepted_metric_bridge"
    assert decomposition["locked_routes"]["Route8"] == "locked_no_accepted_evidence_package"

    plan = (workspace_tmp_dir / "audit/next_logprobe_repair_plan.md").read_text(encoding="utf-8")
    assert "operational_utility_only/no_claim_upgrade" in plan
    assert "Do not unlock Route 5 or Route 8" in plan


def test_logprobe_audit_missing_required_input_fails_closed_without_outputs(workspace_tmp_dir):
    _build_required_inputs(workspace_tmp_dir)
    missing = workspace_tmp_dir / "artifacts/experiments/route4_bridge/bridge_fit_summary.json"
    missing.unlink()

    with pytest.raises(LogProbeAuditInputMissingError) as error:
        run_logprobe_bridge_audit(root=workspace_tmp_dir, output_dir=workspace_tmp_dir / "audit")

    assert "route4a_bridge_fit_summary" in str(error.value)
    assert not (workspace_tmp_dir / "audit").exists()
