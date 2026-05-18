from __future__ import annotations

import json
from pathlib import Path

from cps.benchmarks.hashing import canonical_json_dumps
from cps.experiments.route6a_measurement_pilot import build_context_pair_sample
from cps.experiments.route6a_measurement_pilot import build_frozen_rubric
from cps.experiments.route6a_measurement_pilot import run_route6a_measurement_pilot


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


def _pool(instance_id: str, answer: str = "answer") -> dict:
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
        "target": {"label": answer, "target_type": "answer_string"},
        "task_family": "hotpotqa_answer_support_selection",
    }


def _route4_row(pool: dict, block_packet_id: str, *, delta_utility: float, heldout: bool = False) -> dict:
    return {
        "active_stratum": "route4_hotpotqa_sufficiency_grounded_bridge_v1",
        "augmented_utility": delta_utility,
        "baseline_utility": 0.0,
        "block_A_packet_ids": [block_packet_id],
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
        "heldout_flag": heldout,
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
        "target_y": pool["target"]["label"],
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


def test_route6a_sample_uses_route4_context_pairs_without_leaking_bridge_measurements():
    pool = _pool("hotpot-1", answer="target answer")
    gold_packet_id = pool["candidate_pool"]["packets"][0]["packet_id"]
    sample = build_context_pair_sample(
        bridge_rows=[_route4_row(pool, gold_packet_id, delta_utility=0.5)],
        candidate_pools=[pool],
        sample_size=1,
    )

    assert len(sample) == 1
    row = sample[0]
    assert row["sample_id"].startswith("route6a::")
    assert row["question"] == "Question for hotpot-1?"
    assert row["target_y"] == "target answer"
    assert row["baseline_context_packets"] == []
    assert row["added_block_packets"][0]["content"] == "Gold evidence A."
    assert row["source_route4_row_ref"]["phase_id"] == "route4a_hotpotqa_sufficiency_pilot"

    serialized = json.dumps(row, sort_keys=True)
    assert "delta_logloss" not in serialized
    assert "delta_utility" not in serialized
    assert "gold_support_label" not in serialized
    assert "baseline_utility" not in serialized
    assert "augmented_utility" not in serialized


def test_route6a_pipeline_writes_blocked_judge_report_and_claim_safe_artifacts(workspace_tmp_dir):
    pools = [_pool("hotpot-a"), _pool("hotpot-b")]
    rows = [
        _route4_row(pools[0], pools[0]["candidate_pool"]["packets"][0]["packet_id"], delta_utility=0.325),
        _route4_row(pools[1], pools[1]["candidate_pool"]["packets"][2]["packet_id"], delta_utility=0.0, heldout=True),
    ]
    bridge_rows_path = _write_jsonl(workspace_tmp_dir / "bridge_rows.jsonl", rows)
    pools_path = _write_jsonl(workspace_tmp_dir / "candidate_pools.jsonl", pools)

    result = run_route6a_measurement_pilot(
        output_dir=workspace_tmp_dir / "route6a",
        bridge_rows_path=bridge_rows_path,
        candidate_pools_path=pools_path,
        sample_size=2,
        run_live_adjudication=False,
        report_md_path=workspace_tmp_dir / "Route6A.md",
    )

    output_dir = workspace_tmp_dir / "route6a"
    assert result["status"] == "blocked_judge_unavailable"
    assert result["claim_status"] == "no_claim_upgrade"
    assert result["measurement_validation_candidate_allowed"] is False
    assert (output_dir / "sample_manifest.json").exists()
    assert (output_dir / "context_pair_sample.jsonl").exists()
    assert (output_dir / "rubric_frozen.json").exists()
    assert (output_dir / "readiness_report.json").exists()
    assert _read_json(output_dir / "readiness_report.json")["human_annotation_status"] == "blocked_human_annotation_required"
    assert _read_json(output_dir / "rubric_frozen.json")["rubric_version"] == "route6a_external_sufficiency_rubric_v1"
    assert len(_read_jsonl(output_dir / "context_pair_sample.jsonl")) == 2


def test_route6a_live_adjudication_stores_normalized_labels_only(workspace_tmp_dir):
    pool = _pool("hotpot-live")
    second_pool = _pool("hotpot-live-2")
    rows = [
        _route4_row(pool, pool["candidate_pool"]["packets"][0]["packet_id"], delta_utility=0.325),
        _route4_row(second_pool, second_pool["candidate_pool"]["packets"][0]["packet_id"], delta_utility=0.325),
    ]
    bridge_rows_path = _write_jsonl(workspace_tmp_dir / "bridge_rows.jsonl", rows)
    pools_path = _write_jsonl(workspace_tmp_dir / "candidate_pools.jsonl", [pool, second_pool])

    class FakeClient:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def chat_completion(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 2:
                return {"choices": [{"message": {"content": "not json"}}]}
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "baseline_sufficiency": "insufficient",
                                    "augmented_sufficiency": "partial",
                                    "delta_label": "improves",
                                    "answer_supported": "partial",
                                    "evidence_relevance": "relevant",
                                    "uncertainty": "low",
                                    "invalid_reason": "",
                                },
                                sort_keys=True,
                            )
                        }
                    }
                ]
            }

    client = FakeClient()
    result = run_route6a_measurement_pilot(
        output_dir=workspace_tmp_dir / "route6a",
        bridge_rows_path=bridge_rows_path,
        candidate_pools_path=pools_path,
        sample_size=2,
        run_live_adjudication=True,
        judge_model_id="judge-model",
        judge_provider="approved-test-provider",
        client=client,
        report_md_path=workspace_tmp_dir / "Route6A.md",
    )

    output_dir = workspace_tmp_dir / "route6a"
    labels = _read_jsonl(output_dir / "model_adjudicated_labels.jsonl")
    report = _read_json(output_dir / "adjudication_report.json")
    assert result["status"] == "model_adjudication_completed"
    assert result["measurement_validation_candidate_allowed"] is False
    assert labels[0]["label_schema_version"] == "route6a_model_sufficiency_labels_v1"
    assert labels[0]["delta_label"] == "improves"
    assert labels[1]["delta_label"] == "invalid"
    assert labels[0]["counts_as_human_label"] is False
    assert labels[0]["raw_response_stored"] is False
    assert report["accepted_model_adjudicated_count"] == 1
    assert report["invalid_or_failed_count"] == 1
    serialized_labels = json.dumps(labels, sort_keys=True)
    assert '"raw_response":' not in serialized_labels
    assert "messages" not in serialized_labels
    assert "Gold evidence A." not in serialized_labels
    assert client.calls[0]["temperature"] == 0.0


def test_route6a_rubric_is_non_circular_and_denies_measurement_validation():
    rubric = build_frozen_rubric()

    assert rubric["rubric_version"] == "route6a_external_sufficiency_rubric_v1"
    assert rubric["model_adjudication_counts_as_human_label"] is False
    assert rubric["measurement_validation_candidate_allowed"] is False
    assert "delta_logloss" in rubric["hidden_from_judge_fields"]
    assert "gold_support_label" in rubric["hidden_from_judge_fields"]
