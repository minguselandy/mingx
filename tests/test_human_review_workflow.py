from __future__ import annotations

import json
from pathlib import Path

import pytest

from cps.experiments.human_label_kappa import LABEL_DIMENSIONS
from cps.experiments.human_review_workflow import (
    build_human_review_packet,
    convert_human_review_submission_to_human_labels,
    validate_human_review_submission,
)


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def _prelabel(
    *,
    case_id: str = "case-001",
    condition: str = "cps_runtime_audit_scaffold",
    confidence: int = 800,
) -> dict:
    return {
        "prelabel_run_id": "prelabel-run",
        "label_source": "llm_assisted_prelabel",
        "judge_model_alias": "deepseek_v4_flash",
        "not_human_label": True,
        "requires_human_confirmation": True,
        "case_id": case_id,
        "condition": condition,
        "model_alias": "deepseek_v4_flash",
        "dimension_labels": {
            dimension: {
                "suggested_label": 1,
                "confidence_milli": confidence,
                "rationale": f"Draft rationale for {dimension}.",
                "evidence_refs": ["model_output.json"],
                "uncertainty_notes": "Human review required.",
                "requires_human_review": True,
            }
            for dimension in LABEL_DIMENSIONS
        },
        "overall_summary": "Draft only.",
        "human_review_priority": "low",
        "claim_boundary": {
            "counts_as_human_label": False,
            "measurement_validated_allowed": False,
        },
    }


def _audit(
    *,
    verdict: str = "ACCEPT_DRAFT",
    severity: str = "low",
    dimension: str = "answer_correctness",
) -> dict:
    return {
        "audit_role": "evidence_alignment_reviewer",
        "audit_source": "codex_subagent_audit",
        "not_human_review": True,
        "case_id": "case-001",
        "condition": "cps_runtime_audit_scaffold",
        "verdict": verdict,
        "issues": [
            {
                "issue_type": "evidence_alignment",
                "severity": severity,
                "dimension": dimension,
                "description": "Audit finding for human review.",
                "recommended_human_action": "adjudicate",
            }
        ]
        if severity
        else [],
        "claim_boundary": {
            "counts_as_human_label": False,
            "measurement_validated_allowed": False,
        },
    }


def _completed_rows(rows: list[dict], *, annotator_id: str = "ann-a") -> list[dict]:
    completed = []
    for row in rows:
        payload = dict(row)
        payload["human_label"] = str(payload["llm_suggested_label"])
        payload["human_rationale"] = "Human checked the artifact evidence."
        payload["human_annotator_id"] = annotator_id
        payload["human_decision"] = "accept"
        completed.append(payload)
    return completed


def test_packet_builder_creates_expected_outputs_with_blank_human_fields(workspace_tmp_dir):
    packet = build_human_review_packet(
        [_prelabel()],
        {"audit_results": [_audit(verdict="REQUEST_HUMAN_PRIORITY", severity="medium")]},
        run_id="human-review-run",
        output_root=workspace_tmp_dir,
    )

    outputs = packet["generated_outputs"]
    expected = {
        "human_review_packet_manifest_json",
        "human_review_sheet_csv",
        "human_review_sheet_jsonl",
        "human_review_instructions_markdown",
        "human_review_packet_summary_json",
        "human_review_packet_summary_markdown",
    }
    assert set(outputs) == expected
    for path in outputs.values():
        assert Path(path).exists()

    first_row = packet["review_rows"][0]
    assert first_row["human_label"] == ""
    assert first_row["human_rationale"] == ""
    assert first_row["human_annotator_id"] == ""
    assert first_row["human_decision"] == ""
    assert _json(outputs["human_review_packet_summary_json"])["measurement_validated_allowed"] is False


def test_review_priority_high_for_reject_blocking_or_low_confidence():
    reject_packet = build_human_review_packet(
        [_prelabel()],
        {"audit_results": [_audit(verdict="REJECT_DRAFT", severity="low")]},
        run_id="review-run",
    )
    blocking_packet = build_human_review_packet(
        [_prelabel()],
        {"audit_results": [_audit(verdict="ACCEPT_DRAFT", severity="blocking")]},
        run_id="review-run",
    )
    low_conf_packet = build_human_review_packet([_prelabel(confidence=499)], run_id="review-run")

    assert {row["review_priority"] for row in reject_packet["review_rows"]} == {"high"}
    assert {row["review_priority"] for row in blocking_packet["review_rows"]} == {"high"}
    assert {row["review_priority"] for row in low_conf_packet["review_rows"]} == {"high"}


def test_review_priority_medium_for_request_or_mid_confidence_and_order_is_deterministic():
    request_packet = build_human_review_packet(
        [_prelabel(case_id="case-002"), _prelabel(case_id="case-001")],
        {"audit_results": [_audit(verdict="REQUEST_HUMAN_PRIORITY", severity="")]},
        run_id="review-run",
    )
    mid_conf_packet = build_human_review_packet([_prelabel(confidence=700)], run_id="review-run")

    assert request_packet["review_rows"][0]["case_id"] == "case-001"
    assert request_packet["review_rows"] == build_human_review_packet(
        [_prelabel(case_id="case-002"), _prelabel(case_id="case-001")],
        {"audit_results": [_audit(verdict="REQUEST_HUMAN_PRIORITY", severity="")]},
        run_id="review-run",
    )["review_rows"]
    assert request_packet["review_rows"][0]["review_priority"] == "medium"
    assert {row["review_priority"] for row in mid_conf_packet["review_rows"]} == {"medium"}


@pytest.mark.parametrize(
    "mutator,reason",
    [
        (lambda row: row.__setitem__("human_label", ""), "missing_human_label"),
        (lambda row: row.__setitem__("human_annotator_id", ""), "missing_human_annotator_id"),
        (lambda row: row.__setitem__("human_label", "3"), "invalid_human_label"),
        (lambda row: row.__setitem__("human_decision", "auto_accept"), "invalid_human_decision"),
    ],
)
def test_validator_rejects_missing_or_invalid_human_submission_fields(mutator, reason):
    packet = build_human_review_packet([_prelabel()], run_id="human-review-run")
    rows = _completed_rows(packet["review_rows"])
    mutator(rows[0])

    report = validate_human_review_submission(rows)

    assert report["human_submission_valid"] is False
    assert reason in report["reason_codes"]
    assert report["human_labels_present"] is False


def test_validator_rejects_duplicate_rows():
    packet = build_human_review_packet([_prelabel()], run_id="human-review-run")
    rows = _completed_rows(packet["review_rows"])
    rows.append(dict(rows[0]))

    report = validate_human_review_submission(rows)

    assert report["human_submission_valid"] is False
    assert report["duplicate_rows"]
    assert "duplicate_human_label_entry" in report["reason_codes"]


def test_validator_rejects_missing_required_dimensions():
    packet = build_human_review_packet([_prelabel()], run_id="human-review-run")
    rows = [row for row in _completed_rows(packet["review_rows"]) if row["label_dimension"] != "answer_correctness"]

    report = validate_human_review_submission(rows)

    assert report["human_submission_valid"] is False
    assert "missing_required_dimension" in report["reason_codes"]


def test_validator_rejects_generated_prelabel_rows_mistaken_for_human_labels():
    packet = build_human_review_packet([_prelabel()], run_id="human-review-run")
    rows = _completed_rows(packet["review_rows"], annotator_id="codex_subagent_audit")
    rows[0]["label_source"] = "llm_assisted_prelabel"

    report = validate_human_review_submission(rows)

    assert report["human_submission_valid"] is False
    assert "prelabel_rows_not_human_labels" in report["reason_codes"]
    assert "codex_audit_not_human_annotator" in report["reason_codes"]


def test_validator_accepts_completed_valid_human_sheet():
    packet = build_human_review_packet([_prelabel()], run_id="human-review-run")
    rows = _completed_rows(packet["review_rows"])

    report = validate_human_review_submission(rows)

    assert report["human_submission_valid"] is True
    assert report["human_labels_present"] is True
    assert report["annotator_ids"] == ["ann-a"]
    assert report["case_count"] == 1
    assert report["dimension_count"] == len(LABEL_DIMENSIONS)


def test_conversion_produces_human_annotator_records_only():
    packet = build_human_review_packet([_prelabel()], run_id="human-review-run")
    rows = _completed_rows(packet["review_rows"])
    report = validate_human_review_submission(rows)

    conversion = convert_human_review_submission_to_human_labels(rows, validation_report=report)

    assert len(conversion["human_label_records"]) == len(LABEL_DIMENSIONS)
    assert {row["label_source"] for row in conversion["human_label_records"]} == {"human_annotator"}
    assert {row["annotator_id"] for row in conversion["human_label_records"]} == {"ann-a"}
    assert "llm_assisted_prelabel" not in json.dumps(conversion["human_label_records"], sort_keys=True)
    assert "codex_subagent_audit" not in json.dumps(conversion["human_label_records"], sort_keys=True)
    assert conversion["measurement_validated_allowed"] is False


def test_conversion_fails_when_submission_is_invalid():
    packet = build_human_review_packet([_prelabel()], run_id="human-review-run")
    rows = packet["review_rows"]
    report = validate_human_review_submission(rows)

    with pytest.raises(ValueError):
        convert_human_review_submission_to_human_labels(rows, validation_report=report)


def test_packet_outputs_are_byte_deterministic(workspace_tmp_dir):
    first = build_human_review_packet([_prelabel()], run_id="human-review-run", output_root=workspace_tmp_dir / "first")
    second = build_human_review_packet([_prelabel()], run_id="human-review-run", output_root=workspace_tmp_dir / "second")

    for key in first["generated_outputs"]:
        assert _read(first["generated_outputs"][key]) == _read(second["generated_outputs"][key])


def test_packet_summary_denies_measurement_validated():
    packet = build_human_review_packet([_prelabel()], run_id="human-review-run")
    summary = packet["summary"]

    assert summary["packet_is_human_labeling_completion"] is False
    assert summary["prelabels_are_human_labels"] is False
    assert summary["subagent_audit_is_human_review"] is False
    assert summary["measurement_validated_allowed"] is False
    assert "measurement_validated_denied" in summary["reason_codes"]
