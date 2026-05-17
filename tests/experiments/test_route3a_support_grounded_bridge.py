from __future__ import annotations

import json

from cps.benchmarks.hashing import canonical_json_dumps
from cps.experiments.route3a_support_grounded_bridge import GOLD_LABEL
from cps.experiments.route3a_support_grounded_bridge import SUPPORTING
from cps.experiments.route3a_support_grounded_bridge import negative_control_report
from cps.experiments.route3a_support_grounded_bridge import non_circularity_report
from cps.experiments.route3a_support_grounded_bridge import planned_specs
from cps.experiments.route3a_support_grounded_bridge import run_route3a
from cps.experiments.route3a_support_grounded_bridge import utility_payload
from cps.experiments.route3a_support_grounded_bridge import validate_records


def _packet(instance_id: str, packet_id: str, label: str, source_doc_id: str) -> dict:
    return {
        "content": f"{packet_id} content",
        "dataset": "HotpotQA",
        "gold_support_label": label,
        "hash": f"hash-{packet_id}",
        "instance_id": instance_id,
        "packet_id": packet_id,
        "provenance": {
            "dataset": "HotpotQA",
            "source_doc_id": source_doc_id,
            "span": "sentence:0-0",
        },
        "source_doc_id": source_doc_id,
        "span": {"end": 0, "start": 0, "unit": "sentence"},
        "token_cost": 3,
    }


def _pool(instance_id: str = "hotpot-1") -> dict:
    packets = [
        _packet(instance_id, "gold-1", GOLD_LABEL, "Doc A"),
        _packet(instance_id, "gold-2", GOLD_LABEL, "Doc B"),
        _packet(instance_id, "neg-1", "same_context_distractor", "Doc C"),
        _packet(instance_id, "neg-2", "same_context_distractor", "Doc D"),
    ]
    return {
        "candidate_pool": {
            "candidate_pool_hash": f"pool-hash-{instance_id}",
            "packets": packets,
        },
        "dataset": "HotpotQA",
        "instance_id": instance_id,
        "query": "Which facts support the answer?",
        "split": "dev_distractor",
        "target": {"label": "answer", "target_type": "answer_string"},
        "task_family": "hotpotqa_answer_support_selection",
    }


def _score(*, spec, with_block: bool) -> dict:
    without = {"SUPPORTING": 2.0, "NON_SUPPORTING": 1.5}[spec["target_y"]]
    with_value = {"SUPPORTING": 1.0, "NON_SUPPORTING": 1.25}[spec["target_y"]]
    return {
        "completion_tokens": 1,
        "nll": with_value if with_block else without,
        "prompt_tokens": 10,
        "retries": 0,
        "total_tokens": 11,
    }


def test_route3a_planned_specs_generate_four_rows_per_pool():
    specs = planned_specs([_pool()], max_instances=1)

    assert len(specs) == 4
    assert len({spec["instance_id"] for spec in specs}) == 4
    assert {spec["target_y"] for spec in specs} == {"SUPPORTING", "NON_SUPPORTING"}
    assert all(spec["target_packet_id"] != spec["block_A_packet_id"] for spec in specs)


def test_route3a_utility_is_gold_label_support_recall():
    specs = planned_specs([_pool()], max_instances=1)
    by_shape = {(spec["target_y"], spec["block_A_gold_support_label"]): spec for spec in specs}

    assert utility_payload(by_shape[(SUPPORTING, GOLD_LABEL)])["delta_utility"] == 0.5
    assert utility_payload(by_shape[(SUPPORTING, "same_context_distractor")])["delta_utility"] == 0.0
    assert utility_payload(by_shape[("NON_SUPPORTING", GOLD_LABEL)])["delta_utility"] == 0.5
    assert utility_payload(by_shape[("NON_SUPPORTING", "same_context_distractor")])["delta_utility"] == 0.0


def test_route3a_bounded_run_writes_no_operator_inputs(workspace_tmp_dir):
    pools = [_pool(f"hotpot-{index}") for index in range(150)]
    candidate_path = workspace_tmp_dir / "candidate_pools.jsonl"
    candidate_path.write_text("".join(canonical_json_dumps(pool) + "\n" for pool in pools), encoding="utf-8")
    delta_path = workspace_tmp_dir / "delta_records.jsonl"
    report_path = workspace_tmp_dir / "generation_report.json"
    calibration_dir = workspace_tmp_dir / "calibration"

    result = run_route3a(
        calibration_dir=calibration_dir,
        candidate_pools_path=candidate_path,
        delta_records_path=delta_path,
        generation_report_path=report_path,
        max_instances=150,
        max_workers=1,
        report_md=workspace_tmp_dir / "report.md",
        scorer=_score,
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    records = [
        json.loads(line)
        for line in delta_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert result["records_attempted"] == 600
    assert report["records_validated"] == 600
    assert validate_records(records, pools) == []
    assert not (workspace_tmp_dir / "operator_inputs").exists()


def test_route3a_non_circularity_rejects_exact_equality(workspace_tmp_dir):
    pools = [_pool(f"hotpot-{index}") for index in range(150)]
    candidate_path = workspace_tmp_dir / "candidate_pools.jsonl"
    candidate_path.write_text("".join(canonical_json_dumps(pool) + "\n" for pool in pools), encoding="utf-8")
    delta_path = workspace_tmp_dir / "delta_records.jsonl"

    run_route3a(
        calibration_dir=workspace_tmp_dir / "calibration",
        candidate_pools_path=candidate_path,
        delta_records_path=delta_path,
        generation_report_path=workspace_tmp_dir / "generation_report.json",
        max_instances=150,
        max_workers=1,
        report_md=workspace_tmp_dir / "report.md",
        scorer=_score,
    )
    records = [
        json.loads(line)
        for line in delta_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    copied = [{**record, "delta_utility": record["delta_logloss"]} for record in records]

    assert non_circularity_report(copied)["exact_equality_detected"] is True


def test_route3a_negative_controls_are_reported():
    pools = [_pool(f"hotpot-{index}") for index in range(150)]
    specs = planned_specs(pools, max_instances=150)
    records = []
    from cps.experiments.route3a_support_grounded_bridge import record_from_scores

    for spec in specs:
        records.append(record_from_scores(spec, nll_l={"nll": 2.0}, nll_l_plus_a={"nll": 1.0}))

    report = negative_control_report(records)

    assert set(report) == {
        "length_only_baseline",
        "packet_count_only_baseline",
        "random_score_baseline",
        "shuffled_delta_logloss_within_split_budget",
        "wrong_instance_join",
    }
