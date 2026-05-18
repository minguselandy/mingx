from __future__ import annotations

import json

from cps.benchmarks.candidate_pool_manifest import build_candidate_pool_manifest
from cps.benchmarks.candidate_pool_manifest import validate_candidate_pool_contract


def _pool(hash_value: str = "pool-hash-1") -> dict:
    return {
        "candidate_pool": {
            "candidate_pool_hash": hash_value,
            "gold_reachable_under_budget": {"512": True},
            "n_candidates": 2,
            "n_gold_packets": 1,
            "n_hard_negative_packets": 1,
            "packets": [
                {
                    "content": "Gold evidence text.",
                    "gold_support_label": "gold_supporting",
                    "packet_id": "p-gold",
                    "provenance": {"dataset": "HotpotQA", "source_doc_id": "Gold"},
                    "source_doc_id": "Gold",
                    "token_cost": 4,
                },
                {
                    "content": "Hard distractor text.",
                    "gold_support_label": "same_context_distractor",
                    "packet_id": "p-neg",
                    "provenance": {"dataset": "HotpotQA", "source_doc_id": "Neg"},
                    "source_doc_id": "Neg",
                    "token_cost": 4,
                },
            ],
            "total_tokens": 8,
        },
        "dataset": "HotpotQA",
        "instance_id": "hp-1",
        "query": "question",
        "target": {"label": "answer", "target_type": "answer_string"},
        "task_family": "hotpotqa_answer_support_selection",
    }


def test_candidate_pool_manifest_tracks_provenance_and_reachability():
    manifest = build_candidate_pool_manifest([_pool()], dataset="HotpotQA", budgets=(512,))

    assert manifest["schema_version"] == "workbench_candidate_pool_manifest_v1"
    assert manifest["dataset"] == "HotpotQA"
    assert manifest["pool_count"] == 1
    assert manifest["gold_reachable_by_budget"] == {"512": 1}
    assert manifest["provenance_complete"] is True
    assert manifest["hard_negative_packets"] == 1
    assert manifest["candidate_pool_hashes"] == ["pool-hash-1"]


def test_candidate_pool_contract_blocks_missing_gold_provenance():
    broken = _pool()
    broken["candidate_pool"]["packets"][0].pop("provenance")

    result = validate_candidate_pool_contract([broken])

    assert result.schema_valid is False
    assert "row_1:packet_1:missing_gold_support_provenance" in result.errors


def test_candidate_pool_manifest_is_deterministic():
    first = build_candidate_pool_manifest([_pool("pool-b"), _pool("pool-a")], dataset="HotpotQA", budgets=(512,))
    second = build_candidate_pool_manifest([_pool("pool-a"), _pool("pool-b")], dataset="HotpotQA", budgets=(512,))

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["candidate_pool_hashes"] == ["pool-a", "pool-b"]
