from __future__ import annotations

import json
from pathlib import Path

from cps.benchmarks.hashing import canonical_json_dumps
from cps.experiments.route4_metric_bridge import MIN_PILOT_ROWS
from cps.experiments.route4_metric_bridge import MIN_UNIQUE_INSTANCES
from cps.experiments.route4_metric_bridge import REPLICATE_COUNT_POLICY
from cps.experiments.route4_metric_bridge import REQUIRED_IDENTITY_FIELDS
from cps.experiments.route4_metric_bridge import ROUTE4_PHASE_ID
from cps.experiments.route4_metric_bridge import ROUTE4_PROTOCOL_ID
from cps.experiments.route4_metric_bridge import UTILITY_TARGET_ID
from cps.experiments.route4_metric_bridge import build_route4_rows_from_hotpotqa_delta_records
from cps.experiments.route4_metric_bridge import fit_route4_calibration
from cps.experiments.route4_metric_bridge import inspect_dataset_readiness
from cps.experiments.route4_metric_bridge import inspect_evaluator_readiness
from cps.experiments.route4_metric_bridge import run_route4_pipeline
from cps.experiments.route4_metric_bridge import route4_row_identity
from cps.experiments.route4_metric_bridge import split_manifest
from cps.experiments.route4_metric_bridge import validate_route4_rows


def _packet(instance_id: str, packet_id: str, label: str, source_doc_id: str, token_cost: int = 10) -> dict:
    return {
        "content": f"{packet_id} content",
        "dataset": "HotpotQA",
        "gold_support_label": label,
        "packet_id": f"hotpotqa::dev_distractor::{instance_id}::{label}::{packet_id}",
        "provenance": {"dataset": "HotpotQA", "source_doc_id": source_doc_id, "span": "sentence:0-0"},
        "source_doc_id": source_doc_id,
        "token_cost": token_cost,
    }


def _pool(instance_id: str = "hotpot-1") -> dict:
    packets = [
        _packet(instance_id, "gold-a", "gold_supporting", "Doc A", 8),
        _packet(instance_id, "gold-b", "gold_supporting", "Doc B", 9),
        _packet(instance_id, "neg-a", "same_context_distractor", "Doc C", 7),
    ]
    return {
        "candidate_pool": {
            "candidate_pool_hash": f"pool-hash-{instance_id}",
            "packets": packets,
        },
        "dataset": "HotpotQA",
        "instance_id": instance_id,
        "query": "Question?",
        "schema_version": "benchmark_instance_v1",
        "split": "dev_distractor",
        "target": {"label": "answer", "target_type": "answer_string"},
        "task_family": "hotpotqa_answer_support_selection",
    }


def _delta(pool: dict, packet_id: str, delta_logloss: float = 0.25, context_ids: list[str] | None = None) -> dict:
    return {
        "active_stratum": "evidence_packet_selection_microtask_v1",
        "block_A_packet_ids": [packet_id],
        "block_size": 1,
        "candidate_pool_hash": pool["candidate_pool"]["candidate_pool_hash"],
        "candidate_slice_band": "hotpotqa_dev_distractor_context",
        "contamination_status": "clean",
        "context_L_packet_ids": context_ids or [],
        "dataset": "HotpotQA",
        "decoding_policy": "deterministic_logprob_scoring_v1",
        "delta_logloss": delta_logloss,
        "delta_utility": 0.0,
        "evaluator_id": "approved_live_api_logprob_endpoint::dashscope::qwen3.6-flash::deterministic_logprob_scoring_v1",
        "instance_id": pool["instance_id"],
        "materialization_policy": "fixed_selector_order_with_source_boundaries",
        "model_tier": "approved_live_logprob_model_v1",
        "replicate_count": 1,
        "target_y": "answer",
        "task_family": "hotpotqa_answer_support_selection",
    }


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text("".join(canonical_json_dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def test_route4_dataset_readiness_uses_hotpotqa_when_fever_is_blocked(workspace_tmp_dir):
    candidate_path = _write_jsonl(workspace_tmp_dir / "hotpotqa_candidate_pools.jsonl", [_pool()])
    delta_path = _write_jsonl(
        workspace_tmp_dir / "hotpotqa_p55_delta_records.jsonl",
        [_delta(_pool(), _pool()["candidate_pool"]["packets"][0]["packet_id"])],
    )

    report = inspect_dataset_readiness(
        fever_candidate_pools_path=workspace_tmp_dir / "missing_fever_candidate_pools.jsonl",
        fever_delta_records_path=workspace_tmp_dir / "missing_fever_delta_records.jsonl",
        hotpotqa_candidate_pools_path=candidate_path,
        hotpotqa_delta_records_path=delta_path,
    )

    assert report["available_strata"] == ["HotpotQA"]
    assert report["blocked_strata"]["FEVER"]["blocker"] == "blocked_dataset_incomplete"
    assert report["strata"]["HotpotQA"]["can_support_pilot_rows"] is True


def test_route4_evaluator_readiness_accepts_existing_approved_delta_report(workspace_tmp_dir):
    generation_report = {
        "delta_records_validated": 600,
        "evaluator": {
            "decoding_policy": "deterministic_logprob_scoring_v1",
            "enable_thinking": False,
            "endpoint_type": "openai_compatible_chat_completions_logprobs",
            "evaluator_id": "approved-live",
            "logprobs_supported": True,
            "model_name": "qwen3.6-flash",
            "provider": "dashscope",
            "temperature": 0,
            "top_logprobs": 0,
            "top_p": 1,
        },
    }
    report_path = workspace_tmp_dir / "generation_report.json"
    report_path.write_text(json.dumps(generation_report), encoding="utf-8")

    readiness = inspect_evaluator_readiness(hotpotqa_generation_report_path=report_path, env_path=None)

    assert readiness["approved_scoring_backend_found"] is True
    assert readiness["token_logprobs_available"] is True
    assert readiness["scoring_source"] == "existing_approved_hotpotqa_delta_records"
    assert "local_live_credential_keys_present" not in readiness
    assert readiness["credential_config_detected"] is False
    assert readiness["credential_base_url_configured"] is False


def test_route4_default_gates_match_frozen_protocol():
    assert MIN_PILOT_ROWS == 500
    assert MIN_UNIQUE_INSTANCES == 150


def test_route4_row_builder_adds_full_identity_and_independent_utility():
    pool = _pool()
    gold_packet_id = pool["candidate_pool"]["packets"][0]["packet_id"]
    rows, report = build_route4_rows_from_hotpotqa_delta_records([pool], [_delta(pool, gold_packet_id)])

    assert report["rows_generated"] == 1
    row = rows[0]
    assert row["phase_id"] == ROUTE4_PHASE_ID
    assert row["protocol_id"] == ROUTE4_PROTOCOL_ID
    assert row["task_family"] == "hotpotqa_answer_support_sufficiency_bridge"
    assert row["target_representation"] == "hotpotqa_canonical_answer_string"
    assert row["original_instance_id"] == pool["instance_id"]
    assert row["delta_utility_source"] == "hotpotqa_gold_support_packets_and_source_doc_ids"
    assert row["split"] == "dev_distractor"
    assert row["utility_target_id"] == UTILITY_TARGET_ID
    assert row["replicate_count_policy"] == REPLICATE_COUNT_POLICY
    assert "split" in REQUIRED_IDENTITY_FIELDS
    assert "utility_target_id" in REQUIRED_IDENTITY_FIELDS
    assert "replicate_count_policy" in REQUIRED_IDENTITY_FIELDS
    assert row["delta_utility"] > 0
    assert row["route_id"] in route4_row_identity(row)


def test_route4_validation_rejects_duplicate_unknown_packet_and_circular_rows():
    pool = _pool()
    gold_packet_id = pool["candidate_pool"]["packets"][0]["packet_id"]
    rows, _ = build_route4_rows_from_hotpotqa_delta_records([pool], [_delta(pool, gold_packet_id)])

    duplicate_result = validate_route4_rows([rows[0], dict(rows[0])], [pool])
    assert duplicate_result["schema_valid"] is False
    assert any("duplicate_row_identity" in error for error in duplicate_result["errors"])

    unknown = dict(rows[0])
    unknown["block_A_packet_ids"] = ["missing"]
    unknown_result = validate_route4_rows([unknown], [pool])
    assert any("packet_id_not_in_candidate_pool" in error for error in unknown_result["errors"])

    circular = dict(rows[0])
    circular["delta_logloss"] = circular["delta_utility"]
    circular_result = validate_route4_rows([circular], [pool])
    assert any("delta_utility_equals_delta_logloss" in error for error in circular_result["errors"])


def test_route4_validation_rejects_missing_frozen_identity_fields():
    pool = _pool()
    gold_packet_id = pool["candidate_pool"]["packets"][0]["packet_id"]
    rows, _ = build_route4_rows_from_hotpotqa_delta_records([pool], [_delta(pool, gold_packet_id)])

    for field in ("split", "utility_target_id", "replicate_count_policy"):
        incomplete = dict(rows[0])
        incomplete.pop(field)
        result = validate_route4_rows([incomplete], [pool])
        assert result["schema_valid"] is False
        assert any(f"missing_{field}" in error for error in result["errors"])


def test_route4_split_manifest_is_original_instance_stable():
    pools = []
    deltas = []
    for index in range(10):
        pool = _pool(f"hotpot-{index}")
        gold_packet_id = pool["candidate_pool"]["packets"][0]["packet_id"]
        pools.append(pool)
        deltas.append(_delta(pool, gold_packet_id))
    rows, _ = build_route4_rows_from_hotpotqa_delta_records(pools, deltas)

    manifest = split_manifest(rows)

    assert manifest["split_unit"] == "original_instance_id"
    assert manifest["heldout_original_instances"] == 3
    assert manifest["train_original_instances"] == 7


def test_route4_calibration_reports_failed_closed_when_gates_fail():
    rows = []
    for index in range(150):
        pool = _pool(f"hotpot-{index}")
        gold_packet_id = pool["candidate_pool"]["packets"][0]["packet_id"]
        built, _ = build_route4_rows_from_hotpotqa_delta_records(
            [pool],
            [_delta(pool, gold_packet_id, delta_logloss=-0.01)],
        )
        rows.extend(built)

    fit = fit_route4_calibration(rows, min_rows=100, min_unique_instances=100)

    assert fit["calibration_run"] is True
    assert fit["gate_result"] == "failed_closed_gate_failed"
    assert fit["claim_status"] == "no_claim_upgrade"


def test_route4_pipeline_writes_reports_without_operator_inputs(workspace_tmp_dir):
    pools = [_pool(f"hotpot-{index}") for index in range(120)]
    deltas = [
        _delta(pool, pool["candidate_pool"]["packets"][0]["packet_id"], delta_logloss=0.5)
        for pool in pools
    ]
    candidate_path = _write_jsonl(workspace_tmp_dir / "hotpotqa_candidate_pools.jsonl", pools)
    delta_path = _write_jsonl(workspace_tmp_dir / "hotpotqa_p55_delta_records.jsonl", deltas)
    generation_report_path = workspace_tmp_dir / "hotpotqa_p55_delta_generation_report.json"
    generation_report_path.write_text(
        json.dumps({"delta_records_validated": len(deltas), "evaluator": {"logprobs_supported": True}}),
        encoding="utf-8",
    )
    output_dir = workspace_tmp_dir / "route4_bridge"

    result = run_route4_pipeline(
        output_dir=output_dir,
        fever_candidate_pools_path=workspace_tmp_dir / "missing_fever_candidate_pools.jsonl",
        fever_delta_records_path=workspace_tmp_dir / "missing_fever_delta_records.jsonl",
        hotpotqa_candidate_pools_path=candidate_path,
        hotpotqa_delta_records_path=delta_path,
        hotpotqa_generation_report_path=generation_report_path,
        min_pilot_rows=100,
        min_unique_instances=100,
        report_md_path=workspace_tmp_dir / "Route4.md",
    )

    assert result["status"] in {"calibration_completed", "failed_closed_gate_failed"}
    assert result["operator_inputs_written"] is False
    assert (output_dir / "bridge_rows.jsonl").exists()
    assert (output_dir / "bridge_generation_report.json").exists()
    assert not (workspace_tmp_dir / "operator_inputs").exists()
