from __future__ import annotations

import json
from pathlib import Path

from cps.benchmarks.hashing import canonical_json_dumps
from cps.experiments.route6b_measurement_scaleup import run_route6b_measurement_scaleup


def _packet(instance_id: str, packet_id: str, label: str, content: str, source_doc_id: str) -> dict:
    return {
        "content": content,
        "dataset": "HotpotQA",
        "gold_support_label": label,
        "packet_id": f"hotpotqa::dev_distractor::{instance_id}::{label}::{packet_id}",
        "provenance": {"dataset": "HotpotQA", "source_doc_id": source_doc_id, "span": "sentence:0-0"},
        "source_doc_id": source_doc_id,
        "token_cost": 8,
    }


def _pool(instance_id: str) -> dict:
    packets = [
        _packet(instance_id, "gold-a", "gold_supporting", "Gold evidence A.", "Doc A"),
        _packet(instance_id, "gold-b", "gold_supporting", "Gold evidence B.", "Doc B"),
        _packet(instance_id, "neg-a", "same_context_distractor", "Distractor sentence.", "Doc C"),
    ]
    return {
        "candidate_pool": {
            "candidate_pool_hash": f"pool-hash-{instance_id}",
            "packets": packets,
        },
        "dataset": "HotpotQA",
        "instance_id": instance_id,
        "query": f"Question for {instance_id}?",
        "schema_version": "benchmark_instance_v1",
        "split": "dev_distractor",
        "target": {"label": "answer", "target_type": "answer_string"},
        "task_family": "hotpotqa_answer_support_selection",
    }


def _route4_row(pool: dict, *, delta_utility: float = 0.5) -> dict:
    return {
        "active_stratum": "route4_hotpotqa_sufficiency_grounded_bridge_v1",
        "augmented_utility": delta_utility,
        "baseline_utility": 0.0,
        "block_A_packet_ids": [pool["candidate_pool"]["packets"][0]["packet_id"]],
        "block_size": 1,
        "budget": 512,
        "candidate_pool_hash": pool["candidate_pool"]["candidate_pool_hash"],
        "candidate_slice_band": "route4_hotpotqa_sufficiency_existing_answer_nll_v1",
        "contamination_status": "clean",
        "context_L_packet_ids": [],
        "dataset": "HotpotQA",
        "decoding_policy": "deterministic_logprob_scoring_v1",
        "delta_logloss": 0.25,
        "delta_logloss_source": "existing_approved_hotpotqa_answer_nll_delta_record",
        "delta_utility": delta_utility,
        "delta_utility_source": "hotpotqa_gold_support_packets_and_source_doc_ids",
        "evaluator_id": "approved-live-logprob",
        "heldout_flag": False,
        "instance_id": f"{pool['instance_id']}::route4::row",
        "materialization_policy": "fixed_selector_order_with_source_boundaries",
        "materialized_context_hash": f"context-hash-{pool['instance_id']}",
        "model_tier": "approved_live_logprob_model_v1",
        "original_instance_id": pool["instance_id"],
        "phase_id": "route4a_hotpotqa_sufficiency_pilot",
        "protocol_id": "route4a_hotpotqa_sufficiency_answer_nll_v1",
        "replicate_count": 1,
        "replicate_count_policy": "single_replicate_existing_approved_delta_record",
        "route_id": "route4_metric_bridge_redesign",
        "split": "dev_distractor",
        "split_id": "route4_original_instance_hash_70_30_v1",
        "target_representation": "hotpotqa_canonical_answer_string",
        "target_y": "answer",
        "task_family": "hotpotqa_answer_support_sufficiency_bridge",
        "utility_definition": "route4_hotpotqa_sufficiency_coverage_v1",
        "utility_target_id": "hotpotqa_answer_support_sufficiency",
        "validation_failure_reason": None,
    }


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text("".join(canonical_json_dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class _AlwaysValidClient:
    def chat_completion(self, **kwargs):
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "answer_supported": "supported",
                                "augmented_sufficiency": "sufficient",
                                "baseline_sufficiency": "insufficient",
                                "delta_label": "improves",
                                "evidence_relevance": "relevant",
                                "invalid_reason": "",
                                "uncertainty": "low",
                            },
                            sort_keys=True,
                        )
                    }
                }
            ]
        }


def test_route6b_reports_measurement_candidate_ready_when_scaleup_minimum_is_met(workspace_tmp_dir):
    pools = [_pool(f"hotpot-{index}") for index in range(3)]
    bridge_rows_path = _write_jsonl(workspace_tmp_dir / "bridge_rows.jsonl", [_route4_row(pool) for pool in pools])
    pools_path = _write_jsonl(workspace_tmp_dir / "candidate_pools.jsonl", pools)

    result = run_route6b_measurement_scaleup(
        output_dir=workspace_tmp_dir / "route6b",
        bridge_rows_path=bridge_rows_path,
        candidate_pools_path=pools_path,
        sample_size=3,
        min_accepted_labels=2,
        run_live_adjudication=True,
        client=_AlwaysValidClient(),
        report_md_path=workspace_tmp_dir / "Route6B.md",
    )

    output_dir = workspace_tmp_dir / "route6b"
    readiness = _read_json(output_dir / "readiness_report.json")
    scaleup = _read_json(output_dir / "scaleup_report.json")
    labels = _read_jsonl(output_dir / "model_adjudicated_labels.jsonl")

    assert result["status"] == "measurement_candidate_ready"
    assert readiness["route_id"] == "route6b_measurement_scaleup"
    assert readiness["accepted_model_adjudicated_count"] == 3
    assert readiness["raw_api_responses_stored"] is False
    assert scaleup["terminal_status"] == "measurement_candidate_ready"
    assert len(labels) == 3


def test_route6b_fails_closed_when_accepted_labels_remain_under_minimum(workspace_tmp_dir):
    pools = [_pool("hotpot-a")]
    bridge_rows_path = _write_jsonl(workspace_tmp_dir / "bridge_rows.jsonl", [_route4_row(pools[0])])
    pools_path = _write_jsonl(workspace_tmp_dir / "candidate_pools.jsonl", pools)

    result = run_route6b_measurement_scaleup(
        output_dir=workspace_tmp_dir / "route6b",
        bridge_rows_path=bridge_rows_path,
        candidate_pools_path=pools_path,
        sample_size=1,
        min_accepted_labels=2,
        run_live_adjudication=True,
        client=_AlwaysValidClient(),
        report_md_path=workspace_tmp_dir / "Route6B.md",
    )

    readiness = _read_json(workspace_tmp_dir / "route6b" / "readiness_report.json")

    assert result["status"] == "failed_closed_measurement_quality"
    assert readiness["status"] == "failed_closed_measurement_quality"
    assert readiness["claim_status"] == "no_claim_upgrade"
    assert "accepted_model_adjudicated_labels_below_minimum" in readiness["reason_codes"]
    assert readiness["measurement_validation_candidate_allowed"] is False
