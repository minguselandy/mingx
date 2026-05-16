from __future__ import annotations

import json
from pathlib import Path

from cps.experiments.bridge_row_validation import validate_bridge_rows
from cps.experiments.hotpotqa_support_classification_independent_utility_bridge import (
    CLASSIFIER_PROMPT_VERSION,
    DELTA_UTILITY_SOURCE,
    FIXB_TASK_FAMILY,
    LOGLOSS_EVALUATOR_ID,
    LOGPROB_PROMPT_VERSION,
    METRIC_DESIGN,
    UTILITY_DEFINITION,
    UTILITY_EVALUATOR_ID,
    LabelNllScore,
    UtilityPrediction,
    build_fixb_delta_records,
    build_fixb_rows,
    validate_fixb_delta_records,
    write_fixb_outputs,
)


def _pool() -> dict:
    return {
        "candidate_pool": {
            "candidate_pool_hash": "pool-hash-1",
            "packets": [
                {
                    "content": "Alice founded the company in 1999.",
                    "gold_support_label": "gold_supporting",
                    "packet_id": "p-gold",
                    "source_doc_id": "Alice",
                },
                {
                    "content": "The city has several public parks.",
                    "gold_support_label": "same_context_distractor",
                    "packet_id": "p-distractor",
                    "source_doc_id": "City",
                },
                {
                    "content": "Alice later moved to Paris.",
                    "gold_support_label": "same_context_distractor",
                    "packet_id": "p-helper",
                    "source_doc_id": "Alice",
                },
            ],
        },
        "dataset": "HotpotQA",
        "instance_id": "hotpot-1",
        "query": "Who founded the company?",
        "target": {"label": "Alice", "target_type": "answer_string"},
        "task_family": "hotpotqa_answer_support_selection",
    }


def _logloss_scorer(**kwargs) -> LabelNllScore:
    spec = kwargs["spec"]
    label = str(kwargs["label"])
    with_block = bool(kwargs["with_block"])
    if spec.target_packet_id == "p-gold":
        nll = 1.0 if not with_block else 0.4
    else:
        nll = 0.2 if not with_block else 0.8
    return LabelNllScore(
        completion_tokens=1,
        prompt_tokens=10,
        raw_content=label,
        target_label=label,
        token_logprobs=(-nll,),
        total_tokens=11,
    )


def _utility_classifier(**kwargs) -> UtilityPrediction:
    spec = kwargs["spec"]
    with_block = bool(kwargs["with_block"])
    if spec.target_packet_id == "p-gold":
        return UtilityPrediction(predicted_label="SUPPORTING" if with_block else "NON_SUPPORTING")
    return UtilityPrediction(predicted_label="SUPPORTING" if with_block else "NON_SUPPORTING")


def _valid_records_three() -> list[dict]:
    base = {
        "active_stratum": "evidence_packet_selection_microtask_v1",
        "block_size": 1,
        "candidate_pool_hash": "pool-hash-1",
        "candidate_slice_band": "hotpotqa_support_independent_utility_context",
        "classifier_prompt_version": CLASSIFIER_PROMPT_VERSION,
        "contamination_status": "clean",
        "dataset": "HotpotQA",
        "decoding_policy": "deterministic_logprob_scoring_v1",
        "delta_utility_source": DELTA_UTILITY_SOURCE,
        "evaluator_id": LOGLOSS_EVALUATOR_ID,
        "labels_source": "hotpotqa_candidate_pool_gold_support_label",
        "logloss_evaluator_id": LOGLOSS_EVALUATOR_ID,
        "logprob_prompt_version": LOGPROB_PROMPT_VERSION,
        "materialization_policy": "fixed_selector_order_with_source_boundaries",
        "metric_design": METRIC_DESIGN,
        "model_tier": "approved_live_logprob_model_v1",
        "original_instance_id": "hotpot-1",
        "replicate_count": 1,
        "task_family": FIXB_TASK_FAMILY,
        "utility_definition": UTILITY_DEFINITION,
        "utility_evaluator_id": UTILITY_EVALUATOR_ID,
        "utility_prediction_with_block": "SUPPORTING",
        "utility_prediction_without_block": "NON_SUPPORTING",
        "utility_score_with_block": 1,
        "utility_score_without_block": 0,
    }
    return [
        {
            **base,
            "block_A_packet_ids": ["block-1"],
            "context_L_packet_ids": ["context-1"],
            "delta_logloss": 0.12,
            "delta_utility": 1.0,
            "instance_id": "row-1",
            "target_packet_id": "p-gold",
            "target_y": "SUPPORTING",
        },
        {
            **base,
            "block_A_packet_ids": ["block-2"],
            "context_L_packet_ids": ["context-2"],
            "delta_logloss": 0.34,
            "delta_utility": 0.0,
            "instance_id": "row-2",
            "target_packet_id": "p-helper",
            "target_y": "NON_SUPPORTING",
        },
        {
            **base,
            "block_A_packet_ids": ["block-3"],
            "context_L_packet_ids": ["context-3"],
            "delta_logloss": -0.56,
            "delta_utility": -1.0,
            "instance_id": "row-3",
            "target_packet_id": "p-distractor",
            "target_y": "NON_SUPPORTING",
            "utility_prediction_with_block": "SUPPORTING",
            "utility_prediction_without_block": "NON_SUPPORTING",
            "utility_score_with_block": 0,
            "utility_score_without_block": 1,
        },
    ]


def test_fixb_records_use_independent_live_api_contract_metadata():
    records, report = build_fixb_delta_records(
        [_pool()],
        logloss_scorer=_logloss_scorer,
        records_per_instance=2,
        utility_classifier=_utility_classifier,
    )

    assert report["delta_records_validated"] == 2
    assert {row["task_family"] for row in records} == {FIXB_TASK_FAMILY}
    assert {row["metric_design"] for row in records} == {METRIC_DESIGN}
    assert {row["evaluator_id"] for row in records} == {LOGLOSS_EVALUATOR_ID}
    assert {row["logloss_evaluator_id"] for row in records} == {LOGLOSS_EVALUATOR_ID}
    assert {row["utility_evaluator_id"] for row in records} == {UTILITY_EVALUATOR_ID}
    assert {row["utility_definition"] for row in records} == {UTILITY_DEFINITION}
    assert {row["delta_utility_source"] for row in records} == {DELTA_UTILITY_SOURCE}
    assert {row["classifier_prompt_version"] for row in records} == {CLASSIFIER_PROMPT_VERSION}
    assert {row["logprob_prompt_version"] for row in records} == {LOGPROB_PROMPT_VERSION}
    assert {row["delta_utility"] for row in records} == {1.0, -1.0}
    assert any(row["delta_utility"] != row["delta_logloss"] for row in records)
    assert report["non_circularity_checks"]["fraction_delta_utility_equals_delta_logloss"] == 0.0
    assert validate_fixb_delta_records(records).schema_valid is True


def test_fixb_rows_validate_with_full_bridge_key():
    records, _report = build_fixb_delta_records(
        [_pool()],
        logloss_scorer=_logloss_scorer,
        records_per_instance=2,
        utility_classifier=_utility_classifier,
    )

    rows = build_fixb_rows(records)
    validation = validate_bridge_rows(rows)

    assert validation.schema_valid is True
    assert validation.rows_validated == 2
    assert {row["task_family"] for row in rows} == {FIXB_TASK_FAMILY}


def test_fixb_rejects_circular_delta_utility():
    records = [{**record, "delta_utility": record["delta_logloss"]} for record in _valid_records_three()]

    validation = validate_fixb_delta_records(records)

    assert validation.schema_valid is False
    assert "circular_delta_utility_matches_delta_logloss" in validation.errors


def test_fixb_rejects_affine_or_rounded_delta_utility():
    affine = []
    rounded = []
    for index, value in enumerate((0.12, 0.34, -0.56), start=1):
        base = {
            **_valid_records_three()[0],
            "block_A_packet_ids": [f"block-{index}"],
            "context_L_packet_ids": [f"context-{index}"],
            "delta_logloss": value,
            "instance_id": f"row-{index}",
        }
        affine.append({**base, "delta_utility": 2.0 * value + 0.5})
        rounded.append({**base, "delta_utility": round(value, 1)})

    assert "affine_delta_utility_from_delta_logloss" in validate_fixb_delta_records(affine).errors
    assert "rounded_delta_utility_from_delta_logloss" in validate_fixb_delta_records(rounded).errors


def test_fixb_rejects_utility_source_that_uses_logprobs():
    records = _valid_records_three()
    records[0]["delta_utility_source"] = "logprob_derived_classifier_delta"

    validation = validate_fixb_delta_records(records)

    assert validation.schema_valid is False
    assert "row_1:delta_utility_source_uses_logloss_or_logprobs" in validation.errors


def test_fixb_rejects_missing_classifier_predictions():
    records = _valid_records_three()
    del records[0]["utility_prediction_with_block"]

    validation = validate_fixb_delta_records(records)

    assert validation.schema_valid is False
    assert "row_1:missing_utility_prediction_with_block" in validation.errors


def test_fixb_artifacts_are_deterministic(workspace_tmp_dir: Path):
    records, report = build_fixb_delta_records(
        [_pool()],
        logloss_scorer=_logloss_scorer,
        records_per_instance=2,
        utility_classifier=_utility_classifier,
    )
    rows = build_fixb_rows(records)

    first = write_fixb_outputs(
        delta_records=records,
        rows=rows,
        report=report,
        delta_records_path=workspace_tmp_dir / "delta.jsonl",
        operator_rows_path=workspace_tmp_dir / "rows.jsonl",
        report_path=workspace_tmp_dir / "report.json",
    )
    first_bytes = {
        "delta": (workspace_tmp_dir / "delta.jsonl").read_bytes(),
        "rows": (workspace_tmp_dir / "rows.jsonl").read_bytes(),
        "report": (workspace_tmp_dir / "report.json").read_bytes(),
    }
    second = write_fixb_outputs(
        delta_records=records,
        rows=rows,
        report=report,
        delta_records_path=workspace_tmp_dir / "delta.jsonl",
        operator_rows_path=workspace_tmp_dir / "rows.jsonl",
        report_path=workspace_tmp_dir / "report.json",
    )
    second_bytes = {
        "delta": (workspace_tmp_dir / "delta.jsonl").read_bytes(),
        "rows": (workspace_tmp_dir / "rows.jsonl").read_bytes(),
        "report": (workspace_tmp_dir / "report.json").read_bytes(),
    }

    assert first == second
    assert first_bytes == second_bytes
    assert str(workspace_tmp_dir) not in json.dumps(report)
