from __future__ import annotations

import json
from pathlib import Path

from cps.analysis.contamination_review import (
    build_contamination_review_packet,
    format_contamination_review_markdown,
)


def test_build_contamination_review_packet_collects_only_above_threshold_questions(workspace_tmp_dir):
    manifest_path = workspace_tmp_dir / "sample_manifest_v1.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "phase0.sample.v1",
                "created_at_utc": "2026-04-23T00:00:00+00:00",
                "source_dataset": {
                    "split": "dev",
                    "content_hash_sha256": "dataset-hash",
                },
                "sampling_config": {"seed": 20260418},
                "diagnostics": {},
                "sample": [
                    {
                        "question_id": "q-high",
                        "hop_depth": "2hop",
                        "hop_subcategory": "2hop",
                        "question_text": "In what year did the founder of the Presbyterian Church die?",
                        "answer_text": "1572",
                        "answer_aliases": [],
                        "answerable": True,
                        "paragraph_count": 2,
                        "paragraphs": [
                            {
                                "paragraph_idx": 0,
                                "title": "Presbyterianism",
                                "paragraph_text": "John Knox was the founder of the Presbyterian Church and died in 1572.",
                                "is_supporting": True,
                            },
                            {
                                "paragraph_idx": 1,
                                "title": "Other",
                                "paragraph_text": "Irrelevant background paragraph.",
                                "is_supporting": False,
                            },
                        ],
                    },
                    {
                        "question_id": "q-low",
                        "hop_depth": "3hop",
                        "hop_subcategory": "3hop",
                        "question_text": "Which county borders the county where Example Person was born?",
                        "answer_text": "Cabarrus County",
                        "answer_aliases": [],
                        "answerable": True,
                        "paragraph_count": 1,
                        "paragraphs": [
                            {
                                "paragraph_idx": 0,
                                "title": "Example",
                                "paragraph_text": "Example paragraph",
                                "is_supporting": True,
                            }
                        ],
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    calibration_manifest_path = workspace_tmp_dir / "calibration_manifest.json"
    calibration_manifest_path.write_text(
        json.dumps(
            {
                "source_manifest_path": str(manifest_path),
                "source_manifest_hash": "hash",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    contamination_report_path = workspace_tmp_dir / "contamination_diagnostics.json"
    contamination_report_path.write_text(
        json.dumps(
            {
                "threshold_logp": -0.6931471805599453,
                "gate_decision": "fail",
                "baseline_rows": [
                    {
                        "question_id": "q-high",
                        "hop_depth": "2hop",
                        "baseline_logp": -0.001,
                        "model_role": "frontier",
                        "model_id": "qwen3.6-plus",
                        "above_threshold": True,
                    },
                    {
                        "question_id": "q-low",
                        "hop_depth": "3hop",
                        "baseline_logp": -1.2,
                        "model_role": "frontier",
                        "model_id": "qwen3.6-plus",
                        "above_threshold": False,
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    run_summary_path = workspace_tmp_dir / "run_summary.json"
    run_summary_path.write_text(
        json.dumps(
            {
                "calibration_manifest_path": str(calibration_manifest_path),
                "contamination": {"path": str(contamination_report_path)},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = build_contamination_review_packet(run_summary_path=run_summary_path, snippet_chars=64)

    assert payload["status"] == "computed"
    assert payload["review_scope"] == "above_threshold_questions_only"
    assert payload["question_count"] == 1
    question = payload["questions"][0]
    assert question["question_id"] == "q-high"
    assert question["baseline_probability"] > 0.5
    assert question["heuristic_signals"]["answer_string_appears_in_question"] is False
    assert len(question["supporting_paragraphs"]) == 1
    assert "gold_answer: 1572" in question["stage2_rewrite_prompt"]
    assert "1572" not in question["stage1_question_only_prompt"]


def test_format_contamination_review_markdown_includes_prompts_and_operator_rules():
    payload = {
        "review_scope": "above_threshold_questions_only",
        "question_count": 1,
        "threshold": {
            "gate_decision": "fail",
            "logp": -0.6931471805599453,
            "probability": 0.5,
        },
        "questions": [
            {
                "question_id": "q-high",
                "hop_depth": "2hop",
                "model_id": "qwen3.6-plus",
                "model_role": "frontier",
                "baseline_logp": -0.001,
                "baseline_probability": 0.999,
                "question_text": "In what year did the founder of the Presbyterian Church die?",
                "answer_text": "1572",
                "heuristic_signals": {
                    "answer_string_appears_in_question": False,
                    "answer_alias_hits_in_question": [],
                    "shared_question_answer_tokens": [],
                },
                "supporting_paragraphs": [
                    {
                        "paragraph_id": 0,
                        "title": "Presbyterianism",
                        "text_excerpt": "John Knox was the founder of the Presbyterian Church and died in 1572.",
                    }
                ],
                "stage1_question_only_prompt": "stage1 prompt",
                "stage2_rewrite_prompt": "stage2 prompt",
            }
        ],
    }

    markdown = format_contamination_review_markdown(
        payload,
        command="python scripts/export_contamination_review_packet.py --run-summary run_summary.json",
        json_report_path="artifacts/phase1/review_packet.json",
    )

    assert "# Phase 1 Contamination Review Packet" in markdown
    assert "AI output is advisory only" in markdown
    assert "## q-high" in markdown
    assert "### Stage 1 Prompt" in markdown
    assert "stage2 prompt" in markdown
