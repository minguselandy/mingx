from __future__ import annotations

import json

from cps.benchmarks.hashing import canonical_json_dumps
from cps.benchmarks.hotpot_adapter import build_hotpot_candidate_pools
from cps.benchmarks.schemas import compute_candidate_pool_hash
from cps.benchmarks.schemas import validate_benchmark_instance


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def _hotpot_rows():
    return [
        {
            "_id": "hotpot-1",
            "answer": "George Orwell",
            "context": [
                [
                    "Nineteen Eighty-Four",
                    [
                        "Nineteen Eighty-Four is a dystopian novel.",
                        "It was written by English author George Orwell.",
                    ],
                ],
                [
                    "Animal Farm",
                    [
                        "Animal Farm is another book by George Orwell.",
                        "It was first published in England.",
                    ],
                ],
            ],
            "level": "easy",
            "question": "Who wrote Nineteen Eighty-Four?",
            "supporting_facts": [["Nineteen Eighty-Four", 1]],
            "type": "bridge",
        }
    ]


def _instance(workspace_tmp_dir):
    result = build_hotpot_candidate_pools(
        input_json=workspace_tmp_dir / "hotpot.json",
        split="dev",
    )
    assert result.blocked_report is None
    return result.instances[0]


def _write_hotpot(workspace_tmp_dir, rows=None):
    return _write_json(workspace_tmp_dir / "hotpot.json", rows if rows is not None else _hotpot_rows())


def test_hotpot_fixture_converts_to_candidate_pool(workspace_tmp_dir):
    _write_hotpot(workspace_tmp_dir)
    instance = _instance(workspace_tmp_dir)
    payload = instance.to_payload()

    assert payload["dataset"] == "HotpotQA"
    assert payload["task_family"] == "hotpotqa_answer_support_selection"
    assert payload["query"] == "Who wrote Nineteen Eighty-Four?"
    assert payload["target"] == {"label": "George Orwell", "target_type": "answer_string"}
    assert payload["candidate_pool"]["n_candidates"] == 4
    assert validate_benchmark_instance(instance).schema_valid is True


def test_hotpot_supporting_facts_marked_gold_supporting(workspace_tmp_dir):
    _write_hotpot(workspace_tmp_dir)
    packets = _instance(workspace_tmp_dir).candidate_pool.packets

    gold_packets = [packet for packet in packets if packet.gold_support_label == "gold_supporting"]
    assert len(gold_packets) == 1
    assert gold_packets[0].source_doc_id == "Nineteen Eighty-Four"
    assert gold_packets[0].span["start"] == 1


def test_hotpot_non_supporting_context_sentences_marked_distractors(workspace_tmp_dir):
    _write_hotpot(workspace_tmp_dir)
    packets = _instance(workspace_tmp_dir).candidate_pool.packets

    distractors = [packet for packet in packets if packet.gold_support_label == "same_context_distractor"]
    assert len(distractors) == 3


def test_hotpot_exact_answer_packet_is_not_materialized(workspace_tmp_dir):
    rows = _hotpot_rows()
    rows[0]["answer"] = "George Orwell"
    rows[0]["context"][0][1].append("George Orwell")
    path = _write_hotpot(workspace_tmp_dir, rows)

    result = build_hotpot_candidate_pools(input_json=path)

    assert result.blocked_report is None
    assert all(packet.content != "George Orwell" for packet in result.instances[0].candidate_pool.packets)
    assert any("skipped_exact_answer_packet" in warning for warning in result.report["warnings"])


def test_hotpot_candidate_pool_hash_is_deterministic(workspace_tmp_dir):
    _write_hotpot(workspace_tmp_dir)
    first = _instance(workspace_tmp_dir).to_payload()
    second = _instance(workspace_tmp_dir).to_payload()

    assert first["candidate_pool"]["candidate_pool_hash"] == second["candidate_pool"]["candidate_pool_hash"]
    assert first["candidate_pool"]["candidate_pool_hash"] == compute_candidate_pool_hash(second["candidate_pool"])


def test_hotpot_candidate_pool_rejects_missing_supporting_facts(workspace_tmp_dir):
    rows = _hotpot_rows()
    rows[0].pop("supporting_facts")
    path = _write_hotpot(workspace_tmp_dir, rows)

    result = build_hotpot_candidate_pools(input_json=path)

    assert result.instances == ()
    assert result.blocked_report is not None
    assert "no_valid_candidate_pools" in result.blocked_report["reason_codes"]


def test_hotpot_candidate_pool_rejects_missing_answer(workspace_tmp_dir):
    rows = _hotpot_rows()
    rows[0].pop("answer")
    path = _write_hotpot(workspace_tmp_dir, rows)

    result = build_hotpot_candidate_pools(input_json=path)

    assert result.instances == ()
    assert result.blocked_report is not None
    assert "no_valid_candidate_pools" in result.blocked_report["reason_codes"]


def test_hotpot_no_absolute_paths_in_canonical_output(workspace_tmp_dir):
    _write_hotpot(workspace_tmp_dir)
    payload = _instance(workspace_tmp_dir).to_payload()

    assert ":\\" not in canonical_json_dumps(payload)
    assert "/home/" not in canonical_json_dumps(payload)


def test_hotpot_missing_real_data_emits_blocked_report_not_fake_pool(workspace_tmp_dir):
    result = build_hotpot_candidate_pools(input_json=workspace_tmp_dir / "missing-hotpot.json")

    assert result.instances == ()
    assert result.blocked_report is not None
    assert result.blocked_report["dataset"] == "HotpotQA"
    assert result.blocked_report["candidate_pools_generated"] == 0
    assert "missing_hotpotqa_file" in result.blocked_report["reason_codes"]
