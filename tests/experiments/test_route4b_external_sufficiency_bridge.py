from __future__ import annotations

import json
from pathlib import Path

from cps.benchmarks.hashing import canonical_json_dumps
from cps.experiments.route4b_external_sufficiency_bridge import build_route4b_bridge_rows
from cps.experiments.route4b_external_sufficiency_bridge import fit_route4b_bridge
from cps.experiments.route4b_external_sufficiency_bridge import run_route4b_pipeline


def _route4_row(original_instance_id: str = "hotpot-1") -> dict:
    block_id = f"hotpotqa::dev_distractor::{original_instance_id}::gold_supporting::a"
    return {
        "active_stratum": "route4_hotpotqa_sufficiency_grounded_bridge_v1",
        "block_A_packet_ids": [block_id],
        "block_size": 1,
        "budget": 512,
        "candidate_pool_hash": f"pool-hash-{original_instance_id}",
        "candidate_slice_band": "route4_hotpotqa_sufficiency_existing_answer_nll_v1",
        "contamination_status": "clean",
        "context_L_packet_ids": [],
        "dataset": "HotpotQA",
        "decoding_policy": "deterministic_logprob_scoring_v1",
        "delta_logloss": 0.25,
        "evaluator_id": "approved-live-logprob",
        "heldout_flag": False,
        "instance_id": f"{original_instance_id}::route4::row",
        "materialization_policy": "fixed_selector_order_with_source_boundaries",
        "model_tier": "approved_live_logprob_model_v1",
        "original_instance_id": original_instance_id,
        "phase_id": "route4a_hotpotqa_sufficiency_pilot",
        "protocol_id": "route4a_hotpotqa_sufficiency_answer_nll_v1",
        "replicate_count_policy": "single_replicate_existing_approved_delta_record",
        "route_id": "route4_metric_bridge_redesign",
        "split": "dev_distractor",
        "split_id": "route4_original_instance_hash_70_30_v1",
        "target_y": "answer",
        "task_family": "hotpotqa_answer_support_sufficiency_bridge",
    }


def _sample(sample_id: str, original_instance_id: str = "hotpot-1") -> dict:
    return {
        "sample_id": sample_id,
        "sample_schema_version": "route6a_context_pair_sample_v1",
        "candidate_pool_hash": f"pool-hash-{original_instance_id}",
        "dataset": "HotpotQA",
        "original_instance_id": original_instance_id,
        "question": "Question?",
        "source_route4_row_ref": {
            "candidate_pool_hash": f"pool-hash-{original_instance_id}",
            "heldout_flag": False,
            "original_instance_id": original_instance_id,
            "phase_id": "route4a_hotpotqa_sufficiency_pilot",
            "protocol_id": "route4a_hotpotqa_sufficiency_answer_nll_v1",
        },
        "target_y": "answer",
    }


def _label(sample_id: str, *, delta_label: str = "improves") -> dict:
    return {
        "answer_supported": "supported",
        "augmented_sufficiency": "sufficient",
        "baseline_sufficiency": "insufficient",
        "counts_as_human_label": False,
        "delta_label": delta_label,
        "evidence_relevance": "relevant",
        "invalid_reason_code": "",
        "judge_model_id": "judge-model",
        "judge_provider": "approved-test-provider",
        "label_schema_version": "route6a_model_sufficiency_labels_v1",
        "measurement_validation_candidate_allowed": False,
        "prompt_version": "route6a_external_sufficiency_prompt_v1",
        "raw_response_stored": False,
        "rubric_version": "route6a_external_sufficiency_rubric_v1",
        "sample_id": sample_id,
        "source_sample_ref": sample_id,
        "uncertainty": "low",
    }


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text("".join(canonical_json_dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_route4b_builds_external_sufficiency_rows_without_human_or_raw_claims():
    sample_id = "route6a::sample"
    rows = build_route4b_bridge_rows(
        route4_rows=[_route4_row()],
        context_pair_sample=[_sample(sample_id)],
        model_labels=[_label(sample_id)],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["phase_id"] == "route4b_bridge_to_external_sufficiency"
    assert row["delta_logloss"] == 0.25
    assert row["delta_external_sufficiency_utility"] == 1.0
    assert row["external_utility_source"] == "route6a_model_adjudicated_external_sufficiency"
    assert row["counts_as_human_label"] is False
    assert row["measurement_validation_candidate_allowed"] is False
    assert row["raw_response_stored"] is False
    assert row["metric_claim_level"] == "failed_closed_no_claim_upgrade"
    serialized = json.dumps(row, sort_keys=True)
    assert "raw_response" not in serialized.replace("raw_response_stored", "")


def test_route4b_excludes_invalid_or_human_claiming_labels():
    sample_id = "route6a::sample"
    invalid = _label(sample_id, delta_label="invalid")
    human_claiming = _label(sample_id)
    human_claiming["counts_as_human_label"] = True

    rows = build_route4b_bridge_rows(
        route4_rows=[_route4_row()],
        context_pair_sample=[_sample(sample_id)],
        model_labels=[invalid, human_claiming],
    )

    assert rows == []


def test_route4b_fit_fails_closed_when_model_label_sample_is_underpowered():
    rows = []
    for index in range(4):
        sample_id = f"route6a::sample-{index}"
        built = build_route4b_bridge_rows(
            route4_rows=[_route4_row(f"hotpot-{index}")],
            context_pair_sample=[_sample(sample_id, f"hotpot-{index}")],
            model_labels=[_label(sample_id)],
        )
        rows.extend(built)

    fit = fit_route4b_bridge(rows)

    assert fit["calibration_run"] is False
    assert fit["gate_result"] == "failed_closed_underpowered"
    assert "row_count_below_minimum" in fit["reason_codes"]
    assert fit["metric_bridge_support_candidate"] is False


def test_route4b_pipeline_writes_fail_closed_artifacts(workspace_tmp_dir):
    sample_id = "route6a::sample"
    route4_rows_path = _write_jsonl(workspace_tmp_dir / "route4_rows.jsonl", [_route4_row()])
    sample_path = _write_jsonl(workspace_tmp_dir / "context_pair_sample.jsonl", [_sample(sample_id)])
    labels_path = _write_jsonl(workspace_tmp_dir / "model_adjudicated_labels.jsonl", [_label(sample_id)])

    result = run_route4b_pipeline(
        output_dir=workspace_tmp_dir / "route4b",
        route4_rows_path=route4_rows_path,
        context_pair_sample_path=sample_path,
        model_labels_path=labels_path,
        protocol_md_path=workspace_tmp_dir / "Route4B-protocol.md",
        report_md_path=workspace_tmp_dir / "Route4B-report.md",
    )

    output_dir = workspace_tmp_dir / "route4b"
    assert result["status"] == "failed_closed_underpowered"
    assert result["claim_status"] == "no_claim_upgrade"
    assert result["metric_bridge_support_candidate"] is False
    assert (output_dir / "route4b_readiness_report.json").exists()
    assert (output_dir / "bridge_rows.jsonl").exists()
    assert (output_dir / "bridge_fit_summary.json").exists()
    assert (output_dir / "control_results.json").exists()
    assert (output_dir / "metric_bridge_witness.json").exists()
    assert (output_dir / "claim_gate_result.json").exists()
    assert _read_json(output_dir / "claim_gate_result.json")["calibrated_proxy_supported"] is False
    assert _read_json(output_dir / "metric_bridge_witness.json")["claim_level"] == "ambiguous_metric"
    assert len(_read_jsonl(output_dir / "bridge_rows.jsonl")) == 1
