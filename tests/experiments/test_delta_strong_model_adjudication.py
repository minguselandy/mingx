from __future__ import annotations

import json
from pathlib import Path

from cps.benchmarks.hashing import canonical_json_dumps
from cps.benchmarks.hashing import stable_hash
from cps.experiments.delta_strong_model_adjudication import run_delta_strong_model_adjudication
from cps.experiments.route6a_measurement_pilot import build_context_pair_sample


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical_json_dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _source_label(parent: str, probe: str, *, delta: str = "improves", uncertainty: str = "low") -> dict:
    sample_id = parent if probe == "primary" else f"{parent}::{probe}"
    row = {
        "answer_supported": "supported",
        "augmented_sufficiency": "sufficient" if delta == "improves" else "insufficient",
        "baseline_sufficiency": "insufficient",
        "consistency_probe_type": probe,
        "counts_as_human_label": False,
        "delta_label": delta,
        "evaluator_id": "test-provider::strong-judge",
        "evidence_relevance": "relevant",
        "human_annotation_status": "blocked_human_annotation_required",
        "judge_model_id": "strong-judge",
        "judge_provider": "test-provider",
        "label_schema_version": "route6c_hybrid_label_source_label_v1",
        "label_source_id": "route6c_existing",
        "label_source_type": "model_adjudicated",
        "measurement_validation_candidate_allowed": False,
        "normalization_version": "route6c_label_normalization_v1",
        "parent_sample_id": parent,
        "prompt_version": "route6c_external_sufficiency_prompt_v1",
        "raw_response_stored": False,
        "rubric_version": "route6a_external_sufficiency_rubric_v1",
        "sample_id": sample_id,
        "source_route4_row_identity_hash": f"route4-{parent}",
        "source_sample_ref": sample_id,
        "uncertainty": uncertainty,
    }
    row["label_record_hash"] = stable_hash(row)
    return row


def _bridge_row(parent: str, *, original: str, delta_logloss: float, index: int) -> dict:
    return {
        "claim_status": "operational_utility_only/no_claim_upgrade",
        "dataset": "HotpotQA",
        "delta_hybrid_utility": 0.0,
        "delta_logloss": delta_logloss,
        "metric_claim_level": "operational_utility_only",
        "original_instance_id": original,
        "parent_sample_id": parent,
        "route4_row_identity_hash": f"route4-{parent}",
        "route4d_bridge_row_hash": f"bridge-{index}",
        "schema_version": "route4d_hybrid_bridge_row_v1",
    }


def test_delta_fails_closed_when_judge_reliability_views_are_missing(workspace_tmp_dir: Path) -> None:
    labels_path = _write_jsonl(
        workspace_tmp_dir / "route6c_labels.jsonl",
        [_source_label("sample-a", "primary"), _source_label("sample-b", "primary")],
    )
    bridge_rows_path = _write_jsonl(
        workspace_tmp_dir / "route4d_rows.jsonl",
        [
            _bridge_row("sample-a", original="orig-a", delta_logloss=0.1, index=0),
            _bridge_row("sample-b", original="orig-b", delta_logloss=0.2, index=1),
        ],
    )

    result = run_delta_strong_model_adjudication(
        output_dir=workspace_tmp_dir / "delta",
        docs_path=workspace_tmp_dir / "docs" / "Delta-final.md",
        existing_labels_path=labels_path,
        route4d_bridge_rows_path=bridge_rows_path,
        run_live_adjudication=False,
        minimum_adjudicated_items=2,
        preferred_adjudicated_items=2,
        minimum_unique_parent_items=2,
        minimum_unique_original_instances=2,
        minimum_three_view_items=2,
        route4e_min_rows=2,
        route4e_min_unique_instances=2,
    )

    labels = _read_jsonl(workspace_tmp_dir / "delta" / "model_adjudicated_labels.jsonl")
    reliability = _read_json(workspace_tmp_dir / "delta" / "judge_reliability_audit.json")
    final_status = _read_json(workspace_tmp_dir / "delta" / "final_status.json")
    serialized = json.dumps(labels, sort_keys=True)

    assert result["terminal_status"] == "FAILED_CLOSED_JUDGE_RELIABILITY"
    assert reliability["status"] == "FAILED_CLOSED_JUDGE_RELIABILITY"
    assert final_status["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert final_status["human_annotation_required"] is False
    assert all(label["human_annotation_status"] == "not_requested_model_only_by_user_instruction" for label in labels)
    assert all(label["measurement_validation_claim"] is False for label in labels)
    assert '"raw_response":' not in serialized
    assert '"choices":' not in serialized
    assert "blocked_human_annotation_required" not in serialized


def test_delta_runs_route4e_and_keeps_bridge_failure_operational_only(workspace_tmp_dir: Path) -> None:
    labels = []
    bridge_rows = []
    for index in range(6):
        parent = f"sample-{index}"
        labels.extend(
            [
                _source_label(parent, "primary"),
                _source_label(parent, "order_reversal"),
                _source_label(parent, "duplicate"),
                _source_label(parent, "alternate_prompt"),
            ]
        )
        bridge_rows.append(
            _bridge_row(
                parent,
                original=f"orig-{index}",
                delta_logloss=0.1 * (index + 1),
                index=index,
            )
        )
    labels_path = _write_jsonl(workspace_tmp_dir / "route6c_labels.jsonl", labels)
    bridge_rows_path = _write_jsonl(workspace_tmp_dir / "route4d_rows.jsonl", bridge_rows)

    result = run_delta_strong_model_adjudication(
        output_dir=workspace_tmp_dir / "delta",
        docs_path=workspace_tmp_dir / "docs" / "Delta-final.md",
        existing_labels_path=labels_path,
        route4d_bridge_rows_path=bridge_rows_path,
        run_live_adjudication=False,
        minimum_adjudicated_items=24,
        preferred_adjudicated_items=24,
        minimum_unique_parent_items=6,
        minimum_unique_original_instances=6,
        minimum_three_view_items=6,
        route4e_min_rows=6,
        route4e_min_unique_instances=6,
    )

    bridge = _read_json(workspace_tmp_dir / "delta" / "route4e_bridge_fit_summary.json")
    selector = _read_json(workspace_tmp_dir / "delta" / "route7_model_adjudicated_selector_comparison.json")
    doc = (workspace_tmp_dir / "docs" / "Delta-final.md").read_text(encoding="utf-8")

    assert result["terminal_status"] == "FAILED_CLOSED_BRIDGE_GATES"
    assert bridge["status"] == "FAILED_CLOSED_BRIDGE_GATES"
    assert bridge["calibrated_proxy_supported"] is False
    assert bridge["vinfo_proxy_supported"] is False
    assert bridge["metric_bridge_support"] is False
    assert selector["selector_superiority_claimed"] is False
    assert "human measurement validation" in doc
    assert "calibrated_proxy_supported" in doc


def test_delta_can_generate_missing_model_views_with_normalized_fake_client(workspace_tmp_dir: Path) -> None:
    class FakeClient:
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

    pool = {
        "candidate_pool": {
            "candidate_pool_hash": "pool-a",
            "packets": [
                {
                    "content": "Gold evidence.",
                    "gold_support_label": "gold_supporting",
                    "packet_id": "p1",
                    "source_doc_id": "Doc",
                    "token_cost": 8,
                }
            ],
        },
        "instance_id": "orig-a",
        "query": "Question?",
        "split": "dev_distractor",
        "target": {"label": "Answer", "target_type": "answer_string"},
    }
    route4 = {
        "active_stratum": "route4_hotpotqa_sufficiency_grounded_bridge_v1",
        "block_A_packet_ids": ["p1"],
        "budget": 512,
        "candidate_pool_hash": "pool-a",
        "contamination_status": "clean",
        "context_L_packet_ids": [],
        "dataset": "HotpotQA",
        "delta_logloss": 0.1,
        "delta_utility": 1.0,
        "heldout_flag": False,
        "instance_id": "orig-a::route4",
        "materialization_policy": "fixed_selector_order_with_source_boundaries",
        "original_instance_id": "orig-a",
        "phase_id": "route4a_hotpotqa_sufficiency_pilot",
        "protocol_id": "route4a_hotpotqa_sufficiency_answer_nll_v1",
        "split": "dev_distractor",
        "split_id": "route4_original_instance_hash_70_30_v1",
        "target_y": "Answer",
        "validation_failure_reason": None,
    }
    parent = build_context_pair_sample(bridge_rows=[route4], candidate_pools=[pool], sample_size=1)[0]["sample_id"]
    pool_path = _write_jsonl(
        workspace_tmp_dir / "pools.jsonl",
        [pool],
    )
    route4_path = _write_jsonl(
        workspace_tmp_dir / "route4_rows.jsonl",
        [route4],
    )
    labels_path = _write_jsonl(
        workspace_tmp_dir / "route6c_labels.jsonl",
        [_source_label(parent, "primary")],
    )
    bridge_rows_path = _write_jsonl(
        workspace_tmp_dir / "route4d_rows.jsonl",
        [_bridge_row(parent, original="orig-a", delta_logloss=0.1, index=0)],
    )

    run_delta_strong_model_adjudication(
        output_dir=workspace_tmp_dir / "delta",
        docs_path=workspace_tmp_dir / "docs" / "Delta-final.md",
        existing_labels_path=labels_path,
        route4d_bridge_rows_path=bridge_rows_path,
        route4_rows_path=route4_path,
        candidate_pools_path=pool_path,
        run_live_adjudication=True,
        client=FakeClient(),
        judge_model_id="strong-judge",
        judge_provider="test-provider",
        minimum_adjudicated_items=3,
        preferred_adjudicated_items=3,
        minimum_unique_parent_items=1,
        minimum_unique_original_instances=1,
        minimum_three_view_items=1,
        route4e_min_rows=1,
        route4e_min_unique_instances=1,
    )

    labels = _read_jsonl(workspace_tmp_dir / "delta" / "model_adjudicated_labels.jsonl")
    probes = {label["consistency_probe_type"] for label in labels}

    assert probes == {"alternate_prompt", "duplicate", "order_reversal", "primary"}
    assert all(label["raw_response_stored"] is False for label in labels)
    assert all("confidence" in label for label in labels)
