from __future__ import annotations

import json
from pathlib import Path

from cps.benchmarks.hashing import canonical_json_dumps
from cps.experiments.logprobe_stabilization_readiness import CLAIM_STATUS
from cps.experiments.logprobe_stabilization_readiness import run_logprobe_stabilization_readiness


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical_json_dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def _row(index: int, *, utility_field: str, delta_logloss: float, utility: float) -> dict:
    return {
        "candidate_pool_hash": f"pool-{index}",
        "context_L_packet_ids": ["base"],
        "delta_logloss": delta_logloss,
        utility_field: utility,
        "materialization_policy": "fixed_selector_order_with_source_boundaries",
        "original_instance_id": f"hotpot-{index}",
        "target_representation": "hotpotqa_canonical_answer_string",
        "target_y": "multi token answer",
    }


def _build_inputs(root: Path) -> None:
    _write_json(
        root / "artifacts/benchmarks/hotpotqa_p55_delta_generation_report.json",
        {"api_failures": [], "api_retries": 1, "api_score_calls": 3, "delta_records_validated": 3},
    )
    _write_json(
        root / "artifacts/benchmarks/hotpotqa_support_classification_delta_generation_report.json",
        {
            "api_failures": ["support classifier emitted NON_SUPPORTING expected SUPPORTING"],
            "api_retries": 2,
            "api_score_calls": 3,
            "delta_records_validated": 2,
        },
    )
    _write_json(
        root / "artifacts/experiments/logprobe_bridge_audit/logprobe_stability_report.json",
        {
            "claim_status": CLAIM_STATUS,
            "failure_factor_assessment": {
                "logprobe_instability": {"status": "present"},
                "target_verbalization_tokenization": {"status": "present"},
            },
            "new_live_api_calls": False,
        },
    )
    _write_json(
        root / "artifacts/experiments/logprobe_bridge_audit/utility_logloss_alignment_report.json",
        {
            "claim_status": CLAIM_STATUS,
            "routes": {
                "Route4A": {"weak_utility_logloss_alignment": True},
                "Route4B": {"underpowered_rows": True, "weak_utility_logloss_alignment": True},
            },
        },
    )
    _write_json(
        root / "artifacts/experiments/logprobe_bridge_audit/route4_failure_decomposition.json",
        {
            "claim_status": CLAIM_STATUS,
            "failure_factors": {"bridge_gate_strictness": {"status": "claim_gate_operating_as_designed"}},
            "overall_status": "failed_closed_no_claim_upgrade",
        },
    )
    _write_json(
        root / "artifacts/experiments/route4_bridge/bridge_fit_summary.json",
        {
            "bridge_fit": {"c_hat_s": -1.0, "normalized_residual": 3.0},
            "gate_result": "failed_closed_gate_failed",
            "rows_validated": 3,
            "unique_original_instances": 3,
        },
    )
    _write_jsonl(
        root / "artifacts/experiments/route4_bridge/bridge_rows.jsonl",
        [
            _row(1, utility_field="delta_utility", delta_logloss=-0.001, utility=1.0),
            _row(2, utility_field="delta_utility", delta_logloss=0.0001, utility=0.0),
            _row(3, utility_field="delta_utility", delta_logloss=-0.4, utility=0.0),
        ],
    )
    _write_json(
        root / "artifacts/experiments/route4b_bridge_to_measurement/bridge_fit_summary.json",
        {
            "bridge_fit": {"c_hat_s": -1.0, "normalized_residual": 1.0},
            "gate_result": "failed_closed_underpowered",
            "reason_codes": ["row_count_below_minimum"],
            "rows_validated": 2,
            "unique_original_instances": 2,
        },
    )
    _write_jsonl(
        root / "artifacts/experiments/route4b_bridge_to_measurement/bridge_rows.jsonl",
        [
            _row(1, utility_field="delta_external_sufficiency_utility", delta_logloss=-0.001, utility=1.0),
            _row(2, utility_field="delta_external_sufficiency_utility", delta_logloss=0.0001, utility=0.0),
        ],
    )
    _write_json(
        root / "artifacts/experiments/delta_strong_model_adjudication/route4e_bridge_fit_summary.json",
        {
            "bridge_fit": {"c_hat_s": -1.0, "normalized_residual": 1.0},
            "gate_result": "failed_closed_gate_failed",
            "rows_validated": 2,
            "unique_original_instances": 2,
        },
    )
    _write_jsonl(
        root / "artifacts/experiments/delta_strong_model_adjudication/route4e_bridge_rows.jsonl",
        [
            _row(1, utility_field="delta_hybrid_utility", delta_logloss=-0.001, utility=1.0),
            _row(2, utility_field="delta_hybrid_utility", delta_logloss=0.0001, utility=0.0),
        ],
    )


def test_stabilization_readiness_writes_lp1_to_lp5_without_fever_or_lp6(workspace_tmp_dir):
    _build_inputs(workspace_tmp_dir)

    result = run_logprobe_stabilization_readiness(root=workspace_tmp_dir)

    assert result["terminal_readiness_decision"] == "READY_FOR_TARGET_SWITCH"
    assert result["claim_status"] == CLAIM_STATUS
    assert result["new_live_api_calls"] is False
    assert result["lp6_bridge_repair_run"] is False
    assert result["target_decision"]["primary_decision"] == "SWITCH_TO_EVIDENCE_PATH_NLL"
    assert result["target_decision"]["disabled_decisions"] == ["SWITCH_TO_FEVER_LABEL_NLL"]

    assert (workspace_tmp_dir / "artifacts/experiments/logprobe_stability_shadow/logprobe_stability_matrix.json").exists()
    assert (workspace_tmp_dir / "artifacts/experiments/logprobe_alignment_decomposition/alignment_by_stratum.json").exists()
    assert (workspace_tmp_dir / "artifacts/experiments/logprobe_target_redesign/target_decision.json").exists()
    assert (workspace_tmp_dir / "artifacts/experiments/logprobe_bridge_repair_readiness/readiness_report.json").exists()
    assert (workspace_tmp_dir / "docs/experiments/LogProbe-target-contract.md").exists()
    assert (workspace_tmp_dir / "docs/experiments/LogProbe-target-redesign-decision.md").exists()
    assert (workspace_tmp_dir / "docs/experiments/LogProbe-bridge-repair-readiness.md").exists()

    readiness = json.loads(
        (workspace_tmp_dir / "artifacts/experiments/logprobe_bridge_repair_readiness/readiness_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert readiness["readiness_state"] == "READY_FOR_TARGET_SWITCH"
    assert readiness["checks"]["target_contract_passed"] is True
    assert readiness["checks"]["route5_locked"] is True
    assert readiness["checks"]["route8_locked"] is True
