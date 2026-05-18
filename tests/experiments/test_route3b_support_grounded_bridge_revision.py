from __future__ import annotations

import json

from cps.benchmarks.hashing import canonical_json_dumps
from cps.experiments.route3b_support_grounded_bridge_revision import GOLD_LABEL
from cps.experiments.route3b_support_grounded_bridge_revision import REVISION_PROTOCOL_ID
from cps.experiments.route3b_support_grounded_bridge_revision import SUPPORTING
from cps.experiments.route3b_support_grounded_bridge_revision import negative_control_report
from cps.experiments.route3b_support_grounded_bridge_revision import non_circularity_report
from cps.experiments.route3b_support_grounded_bridge_revision import planned_specs
from cps.experiments.route3b_support_grounded_bridge_revision import read_jsonl
from cps.experiments.route3b_support_grounded_bridge_revision import record_from_scores
from cps.experiments.route3b_support_grounded_bridge_revision import row_identity
from cps.experiments.route3b_support_grounded_bridge_revision import run_route3b
from cps.experiments.route3b_support_grounded_bridge_revision import utility_payload
from cps.experiments.route3b_support_grounded_bridge_revision import validate_records


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


def test_diagnosis_classifies_route3a_attrition_as_label_mismatch():
    report = json.loads(
        open(
            "artifacts/benchmarks/route3b_attrition_diagnosis_report.json",
            encoding="utf-8",
        ).read()
    )

    assert report["route3a_result"]["records_attempted"] == 600
    assert report["route3a_result"]["records_validated"] == 461
    assert report["validation_failure_categories"]["live_logprob_label_mismatch_value_error"] == 139
    assert report["validation_failure_categories"]["schema_validation_errors"] == 0
    assert report["revision_decision"]["utility_semantics_changed"] is False


def test_route3b_planning_uses_all_eligible_real_instances():
    pools = read_jsonl("artifacts/benchmarks/hotpotqa_candidate_pools.jsonl")
    specs = planned_specs(pools)

    assert len(specs) == 792
    assert len({spec["original_hotpotqa_id"] for spec in specs}) == 198


def test_route3b_row_identity_includes_revision_protocol_id():
    spec = planned_specs([_pool()], max_instances=1)[0]
    record = record_from_scores(spec, nll_l={"nll": 2.0}, nll_l_plus_a={"nll": 1.0})

    assert record["revision_protocol_id"] == REVISION_PROTOCOL_ID
    assert REVISION_PROTOCOL_ID in row_identity(record)


def test_route3b_utility_remains_support_grounded():
    specs = planned_specs([_pool()], max_instances=1)
    by_shape = {(spec["target_y"], spec["block_A_gold_support_label"]): spec for spec in specs}

    assert utility_payload(by_shape[(SUPPORTING, GOLD_LABEL)])["delta_utility"] == 0.5
    assert utility_payload(by_shape[(SUPPORTING, "same_context_distractor")])["delta_utility"] == 0.0


def test_route3b_duplicate_row_identity_rejected():
    spec = planned_specs([_pool()], max_instances=1)[0]
    record = record_from_scores(spec, nll_l={"nll": 2.0}, nll_l_plus_a={"nll": 1.0})

    errors = validate_records([record, dict(record)], [_pool()])

    assert any("duplicate_row_identity" in error for error in errors)


def test_route3b_non_circularity_checks_detect_bad_transforms():
    specs = planned_specs([_pool(f"hotpot-{index}") for index in range(3)], max_instances=3)
    records = [
        {
            **record_from_scores(spec, nll_l={"nll": 1.0 + index}, nll_l_plus_a={"nll": 0.5}),
            "delta_logloss": float(index + 1),
        }
        for index, spec in enumerate(specs[:8])
    ]

    exact = [{**record, "delta_utility": record["delta_logloss"]} for record in records]
    affine = [{**record, "delta_utility": 2 * record["delta_logloss"] + 1} for record in records]
    ranked = [
        {**record, "delta_utility": float(index)}
        for index, record in enumerate(sorted(records, key=lambda item: item["delta_logloss"]))
    ]

    assert non_circularity_report(exact)["exact_equality_detected"] is True
    assert non_circularity_report(affine)["affine_transform_detected"] is True
    assert non_circularity_report(ranked)["rank_identity_detected"] is True


def test_route3b_generation_report_records_no_operator_rows(workspace_tmp_dir):
    pools = [_pool(f"hotpot-{index}") for index in range(150)]
    candidate_path = workspace_tmp_dir / "candidate_pools.jsonl"
    candidate_path.write_text("".join(canonical_json_dumps(pool) + "\n" for pool in pools), encoding="utf-8")
    delta_path = workspace_tmp_dir / "delta_records.jsonl"
    report_path = workspace_tmp_dir / "generation_report.json"

    run_route3b(
        calibration_dir=workspace_tmp_dir / "calibration",
        candidate_pools_path=candidate_path,
        delta_records_path=delta_path,
        generation_report_path=report_path,
        max_instances=150,
        max_workers=1,
        report_md=workspace_tmp_dir / "report.md",
        scorer=_score,
    )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["records_attempted"] == 600
    assert report["records_validated"] == 600
    assert report["operator_rows_generated"] == 0
    assert report["operator_rows_validated"] == 0
    assert report["operator_rows_written"] is False


def test_route3b_failed_below_min_branch_is_deterministic(workspace_tmp_dir):
    pools = [_pool(f"hotpot-{index}") for index in range(100)]
    candidate_path = workspace_tmp_dir / "candidate_pools.jsonl"
    candidate_path.write_text("".join(canonical_json_dumps(pool) + "\n" for pool in pools), encoding="utf-8")
    report_path = workspace_tmp_dir / "generation_report.json"

    result = run_route3b(
        calibration_dir=workspace_tmp_dir / "calibration",
        candidate_pools_path=candidate_path,
        delta_records_path=workspace_tmp_dir / "delta_records.jsonl",
        generation_report_path=report_path,
        max_instances=100,
        max_workers=1,
        report_md=workspace_tmp_dir / "report.md",
        scorer=_score,
    )

    assert result["status"] == "failed_closed_pre_score_gate"
    assert json.loads(report_path.read_text(encoding="utf-8"))["operator_rows_written"] is False


def test_route3b_negative_controls_are_reported():
    specs = planned_specs([_pool(f"hotpot-{index}") for index in range(150)], max_instances=150)
    records = [record_from_scores(spec, nll_l={"nll": 2.0}, nll_l_plus_a={"nll": 1.0}) for spec in specs]

    report = negative_control_report(records)

    assert set(report) == {
        "length_only_baseline",
        "packet_count_only_baseline",
        "random_score_baseline",
        "shuffled_delta_logloss_within_split_budget",
        "wrong_instance_join",
    }
