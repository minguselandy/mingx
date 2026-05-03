from __future__ import annotations

import json
import sys
from pathlib import Path

from cps.experiments.human_label_kappa import LABEL_DIMENSIONS
from cps.experiments.model_adjudicated_labels import (
    build_model_adjudicated_labels,
    build_model_adjudicated_labels_from_paths,
)


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def _prelabel(confidence: int = 850) -> dict:
    return {
        "prelabel_run_id": "prelabel-run",
        "label_source": "llm_assisted_prelabel",
        "judge_model_alias": "deepseek_v4_flash",
        "not_human_label": True,
        "requires_human_confirmation": True,
        "case_id": "case-001",
        "condition": "cps_runtime_audit_scaffold",
        "model_alias": "deepseek_v4_flash",
        "dimension_labels": {
            dimension: {
                "suggested_label": 1,
                "confidence_milli": confidence,
                "rationale": f"Draft rationale for {dimension}.",
                "evidence_refs": ["model_output.json"],
                "uncertainty_notes": "Draft only.",
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


def _queue_row(
    *,
    dimension: str = "answer_correctness",
    verdict: str = "ACCEPT_DRAFT",
    severity: str = "low",
    confidence: int = 850,
) -> dict:
    issues = [
        {
            "audit_role": "evidence_alignment_reviewer",
            "verdict": verdict,
            "issue_type": "evidence_alignment",
            "severity": severity,
            "dimension": dimension,
            "description": "Audit finding.",
            "recommended_human_action": "adjudicate",
        }
    ] if severity else []
    return {
        "run_id": "review-run",
        "case_id": "case-001",
        "condition": "cps_runtime_audit_scaffold",
        "model_alias": "deepseek_v4_flash",
        "label_dimension": dimension,
        "llm_suggested_label": "1",
        "llm_confidence_milli": str(confidence),
        "llm_rationale": f"Draft rationale for {dimension}.",
        "llm_evidence_refs": "model_output.json",
        "subagent_verdict": verdict,
        "subagent_issues": json.dumps(issues, sort_keys=True),
        "review_priority": "low",
        "human_label": "",
        "human_rationale": "",
        "human_annotator_id": "",
        "human_decision": "",
        "needs_adjudication": "false",
    }


def _queue(verdict: str = "ACCEPT_DRAFT", severity: str = "low", confidence: int = 850) -> list[dict]:
    return [_queue_row(dimension=dimension, verdict=verdict, severity=severity, confidence=confidence) for dimension in LABEL_DIMENSIONS]


def test_model_adjudicated_labels_are_generated_from_prelabels(workspace_tmp_dir):
    result = build_model_adjudicated_labels(
        [_prelabel()],
        human_review_queue=_queue(),
        run_id="model-adjudication-run",
        output_root=workspace_tmp_dir,
    )

    assert len(result["model_adjudicated_labels"]) == len(LABEL_DIMENSIONS)
    record = result["model_adjudicated_labels"][0]
    assert record["adjudicator_source"] == "codex_model_adjudicator"
    assert record["not_human_label"] is True
    assert record["counts_as_human_label"] is False
    assert record["counts_for_human_kappa"] is False
    assert record["measurement_validated_allowed"] is False
    assert record["allowed_claim_level"] == "model_adjudicated_pilot_only"
    assert "human_annotator_id" not in record
    assert "human_label" not in record
    assert "human_decision" not in record


def test_output_file_is_model_adjudicated_not_human_labels(workspace_tmp_dir):
    result = build_model_adjudicated_labels(
        [_prelabel()],
        human_review_queue=_queue(),
        run_id="model-adjudication-run",
        output_root=workspace_tmp_dir,
    )

    outputs = result["generated_outputs"]
    assert "model_adjudicated_labels_jsonl" in outputs
    assert Path(outputs["model_adjudicated_labels_jsonl"]).name == "model_adjudicated_labels.jsonl"
    assert not (workspace_tmp_dir / "human_labels.jsonl").exists()
    assert not (workspace_tmp_dir / "human_validated_labels.jsonl").exists()
    assert not (workspace_tmp_dir / "measurement_labels.jsonl").exists()
    assert not (workspace_tmp_dir / "final_human_labels.jsonl").exists()


def test_reject_draft_creates_rejected_model_adjudication_status():
    result = build_model_adjudicated_labels(
        [_prelabel()],
        human_review_queue=_queue(verdict="REJECT_DRAFT", severity="low"),
        run_id="model-adjudication-run",
    )

    statuses = {record["review_status"] for record in result["model_adjudicated_labels"]}
    assert statuses == {"rejected_draft_model_adjudicated"}
    assert result["report"]["rejected_or_blocking_warning_count"] == len(LABEL_DIMENSIONS)


def test_request_human_priority_creates_high_uncertainty_status():
    result = build_model_adjudicated_labels(
        [_prelabel()],
        human_review_queue=_queue(verdict="REQUEST_HUMAN_PRIORITY", severity=""),
        run_id="model-adjudication-run",
    )

    statuses = {record["review_status"] for record in result["model_adjudicated_labels"]}
    assert statuses == {"high_uncertainty"}
    assert result["report"]["uncertain_count"] == len(LABEL_DIMENSIONS)


def test_low_confidence_creates_uncertainty():
    result = build_model_adjudicated_labels(
        [_prelabel(confidence=499)],
        human_review_queue=_queue(verdict="ACCEPT_DRAFT", severity="", confidence=499),
        run_id="model-adjudication-run",
    )

    statuses = {record["review_status"] for record in result["model_adjudicated_labels"]}
    assert statuses == {"high_uncertainty"}


def test_blocking_issue_creates_blocking_warning():
    result = build_model_adjudicated_labels(
        [_prelabel()],
        human_review_queue=_queue(verdict="ACCEPT_DRAFT", severity="blocking"),
        run_id="model-adjudication-run",
    )

    statuses = {record["label_status"] for record in result["model_adjudicated_labels"]}
    assert statuses == {"model_adjudicated_with_blocking_warning"}
    assert result["report"]["rejected_or_blocking_warning_count"] == len(LABEL_DIMENSIONS)


def test_report_and_summary_deny_measurement_validated():
    result = build_model_adjudicated_labels(
        [_prelabel()],
        human_review_queue=_queue(),
        run_id="model-adjudication-run",
    )

    assert result["report"]["measurement_validated_allowed"] is False
    assert result["summary"]["measurement_validated_allowed"] is False
    assert "measurement_validated" in result["report"]["denied_claims"]
    assert "human_labels_missing" in result["report"]["reason_codes"]
    assert "human_kappa_missing" in result["report"]["reason_codes"]
    assert result["empirical_summary"]["human_labels_present"] is False
    assert result["empirical_summary"]["kappa_present"] is False
    assert result["empirical_summary"]["allowed_claim_level"] == "model_adjudicated_pilot_only"


def test_json_and_markdown_outputs_are_deterministic(workspace_tmp_dir):
    first = build_model_adjudicated_labels(
        [_prelabel()],
        human_review_queue=_queue(),
        run_id="model-adjudication-run",
        output_root=workspace_tmp_dir / "first",
    )
    second = build_model_adjudicated_labels(
        [_prelabel()],
        human_review_queue=_queue(),
        run_id="model-adjudication-run",
        output_root=workspace_tmp_dir / "second",
    )

    for key in first["generated_outputs"]:
        assert _read(first["generated_outputs"][key]) == _read(second["generated_outputs"][key])


def test_build_from_paths_consumes_p32_and_p33_outputs(workspace_tmp_dir):
    prelabels_path = workspace_tmp_dir / "llm_prelabels.jsonl"
    queue_path = workspace_tmp_dir / "human_review_queue.jsonl"
    audit_report_path = workspace_tmp_dir / "subagent_audit_report.json"
    prelabels_path.write_text(json.dumps(_prelabel(), sort_keys=True) + "\n", encoding="utf-8")
    queue_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in _queue()) + "\n", encoding="utf-8")
    audit_report_path.write_text(
        json.dumps({"prelabel_run_id": "prelabel-run", "measurement_validated_allowed": False}, sort_keys=True),
        encoding="utf-8",
    )

    result = build_model_adjudicated_labels_from_paths(
        prelabels_path=prelabels_path,
        subagent_audit_report_path=audit_report_path,
        human_review_queue_path=queue_path,
        run_id="model-adjudication-run",
        output_root=workspace_tmp_dir / "out",
    )

    assert result["report"]["total_labels"] == len(LABEL_DIMENSIONS)
    assert Path(result["generated_outputs"]["model_adjudicated_labels_jsonl"]).exists()


def test_no_external_sdk_import_or_live_api_is_required():
    forbidden = {"openai", "anthropic", "requests", "httpx", "numpy", "pandas", "sklearn"}

    assert forbidden.isdisjoint(set(sys.modules))
