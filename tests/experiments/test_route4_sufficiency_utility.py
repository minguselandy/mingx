from __future__ import annotations

import pytest

from cps.experiments.route4_sufficiency_utility import compute_hotpotqa_sufficiency_utility
from cps.experiments.route4_sufficiency_utility import hotpotqa_packet_lookup


def _packet(packet_id: str, label: str, source_doc_id: str, token_cost: int = 10) -> dict:
    return {
        "content": f"{packet_id} content",
        "dataset": "HotpotQA",
        "gold_support_label": label,
        "packet_id": packet_id,
        "provenance": {"dataset": "HotpotQA", "source_doc_id": source_doc_id, "span": "sentence:0-0"},
        "source_doc_id": source_doc_id,
        "token_cost": token_cost,
    }


def _pool() -> dict:
    packets = [
        _packet("gold-a", "gold_supporting", "Doc A", 8),
        _packet("gold-b", "gold_supporting", "Doc B", 9),
        _packet("neg-a", "same_context_distractor", "Doc C", 7),
    ]
    return {
        "candidate_pool": {
            "candidate_pool_hash": "pool-hash",
            "packets": packets,
        },
        "dataset": "HotpotQA",
        "instance_id": "hotpot-1",
        "query": "Question?",
        "split": "dev_distractor",
        "target": {"label": "answer", "target_type": "answer_string"},
        "task_family": "hotpotqa_answer_support_selection",
    }


def test_hotpotqa_sufficiency_utility_rewards_gold_support_and_source_coverage():
    result = compute_hotpotqa_sufficiency_utility(_pool(), context_ids=[], block_ids=["gold-a"])

    assert result.baseline_utility == 0.0
    assert result.augmented_utility > 0.0
    assert result.delta_utility == result.augmented_utility
    assert result.evidence_coverage_delta == 0.5
    assert result.source_coverage_delta == 0.5
    assert result.full_support_hit_delta == 0
    assert result.sufficiency_level_baseline == "none"
    assert result.sufficiency_level_augmented == "partial_support"


def test_hotpotqa_sufficiency_utility_detects_complete_support():
    result = compute_hotpotqa_sufficiency_utility(_pool(), context_ids=["gold-a"], block_ids=["gold-b"])

    assert result.sufficiency_level_baseline == "partial_support"
    assert result.sufficiency_level_augmented == "complete_support"
    assert result.full_support_hit_delta == 1
    assert result.missing_prerequisite_delta == -1


def test_hotpotqa_sufficiency_utility_ignores_distractors_for_primary_coverage():
    result = compute_hotpotqa_sufficiency_utility(_pool(), context_ids=[], block_ids=["neg-a"])

    assert result.augmented_utility == 0.0
    assert result.delta_utility == 0.0
    assert result.sufficiency_level_augmented == "none"
    assert result.utility_source_provenance["uses_logloss_or_model_probability"] is False


def test_hotpotqa_sufficiency_utility_rejects_unknown_packet_ids():
    with pytest.raises(ValueError, match="unknown_packet_id"):
        compute_hotpotqa_sufficiency_utility(_pool(), context_ids=["missing"], block_ids=["gold-a"])


def test_hotpotqa_packet_lookup_requires_candidate_pool_hash_and_packets():
    with pytest.raises(ValueError, match="missing_candidate_pool_hash"):
        hotpotqa_packet_lookup({"candidate_pool": {"packets": []}})
