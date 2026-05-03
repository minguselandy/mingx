from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from cps.experiments.human_label_kappa import LABEL_DIMENSIONS
from cps.experiments.prelabel_subagent_audit import (
    AUDIT_ROLES,
    build_human_review_queue,
    build_subagent_audit_report,
    build_subagent_audit_requests,
    parse_subagent_audit_output,
    write_prelabel_subagent_audit_outputs,
)


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def _prelabel(case_id: str = "case-001", condition: str = "cps_runtime_audit_scaffold") -> dict:
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
                "confidence_milli": 700,
                "rationale": f"Draft rationale for {dimension}.",
                "evidence_refs": ["model_output.json"],
                "uncertainty_notes": "Needs confirmation.",
                "requires_human_review": True,
            }
            for dimension in LABEL_DIMENSIONS
        },
        "overall_summary": "Draft only.",
        "human_review_priority": "medium",
        "claim_boundary": {
            "counts_as_human_label": False,
            "measurement_validated_allowed": False,
        },
    }


def _valid_audit(role: str = "claim_boundary_reviewer", verdict: str = "ACCEPT_DRAFT") -> dict:
    return {
        "audit_role": role,
        "audit_source": "codex_subagent_audit",
        "not_human_review": True,
        "case_id": "case-001",
        "condition": "cps_runtime_audit_scaffold",
        "verdict": verdict,
        "issues": [],
        "claim_boundary": {
            "counts_as_human_label": False,
            "measurement_validated_allowed": False,
        },
    }


def test_audit_requests_are_generated_for_all_roles_in_stable_order():
    requests = build_subagent_audit_requests(
        [
            _prelabel("case-002", "heuristic_selector_baseline"),
            _prelabel("case-001", "cps_runtime_audit_scaffold"),
        ],
        artifact_refs={"model_output_json": "cases/model_output.json"},
        prelabel_run_id="prelabel-run",
    )

    assert len(requests) == 2 * len(AUDIT_ROLES)
    assert [request["audit_role"] for request in requests[: len(AUDIT_ROLES)]] == list(AUDIT_ROLES)
    assert requests[0]["case_id"] == "case-001"
    assert requests[0]["not_human_review"] is True
    assert requests[0]["measurement_validated_allowed"] is False
    assert "not human labeling" in requests[0]["audit_prompt"]
    assert "JSON only" in requests[0]["audit_prompt"]


def test_audit_parser_accepts_valid_codex_subagent_audit_output():
    parsed = parse_subagent_audit_output(json.dumps(_valid_audit(), sort_keys=True))

    assert parsed["audit_source"] == "codex_subagent_audit"
    assert parsed["not_human_review"] is True
    assert parsed["verdict"] == "ACCEPT_DRAFT"
    assert parsed["measurement_validated_allowed"] is False
    assert parsed["counts_as_human_labels"] is False


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.__setitem__("audit_source", "human_review"),
        lambda payload: payload.__setitem__("not_human_review", False),
        lambda payload: payload.__setitem__("verdict", "FINAL_LABEL"),
        lambda payload: payload["claim_boundary"].__setitem__("counts_as_human_label", True),
        lambda payload: payload["claim_boundary"].__setitem__("measurement_validated_allowed", True),
    ],
)
def test_audit_parser_rejects_human_review_or_validation_claims(mutator):
    payload = _valid_audit()
    mutator(payload)

    with pytest.raises(ValueError):
        parse_subagent_audit_output(payload)


def test_audit_report_counts_verdicts_and_forces_human_priority_for_blocking_issues():
    blocking = _valid_audit(role="evidence_alignment_reviewer", verdict="ACCEPT_DRAFT")
    blocking["issues"] = [
        {
            "issue_type": "missing_evidence",
            "severity": "blocking",
            "dimension": "answer_groundedness",
            "description": "Evidence reference does not support the draft.",
            "recommended_human_action": "adjudicate",
        }
    ]
    reject = _valid_audit(role="rubric_consistency_reviewer", verdict="REJECT_DRAFT")
    request = _valid_audit(role="uncertainty_reviewer", verdict="REQUEST_HUMAN_PRIORITY")
    report = build_subagent_audit_report(
        [_prelabel()],
        build_subagent_audit_requests([_prelabel()], artifact_refs={}, prelabel_run_id="prelabel-run"),
        [blocking, reject, request],
        prelabel_run_id="prelabel-run",
    )

    assert report["total_prelabels"] == 1
    assert report["verdict_counts"]["ACCEPT_DRAFT"] == 1
    assert report["verdict_counts"]["REJECT_DRAFT"] == 1
    assert report["verdict_counts"]["REQUEST_HUMAN_PRIORITY"] == 1
    assert report["blocking_issue_count"] == 1
    assert report["human_priority_count"] == 1
    assert report["rejected_draft_count"] == 1
    assert report["measurement_validated_allowed"] is False
    assert "case-001" in report["cases_requiring_human_priority"]


def test_pending_audit_report_does_not_fabricate_verdicts():
    report = build_subagent_audit_report(
        [_prelabel()],
        build_subagent_audit_requests([_prelabel()], artifact_refs={}, prelabel_run_id="prelabel-run"),
        prelabel_run_id="prelabel-run",
    )

    assert report["audit_results_present"] is False
    assert report["verdict_counts"] == {"ACCEPT_DRAFT": 0, "REQUEST_HUMAN_PRIORITY": 0, "REJECT_DRAFT": 0}
    assert report["human_priority_count"] == 1
    assert report["measurement_validated_allowed"] is False


def test_human_review_queue_leaves_human_fields_blank():
    audit = _valid_audit(verdict="REQUEST_HUMAN_PRIORITY")
    queue = build_human_review_queue([_prelabel()], [audit], run_id="prelabel-run")

    assert len(queue) == len(LABEL_DIMENSIONS)
    first = queue[0]
    assert first["human_label"] == ""
    assert first["human_annotator_id"] == ""
    assert first["human_decision"] == ""
    assert first["needs_adjudication"] == "true"
    assert first["subagent_verdict"] == "REQUEST_HUMAN_PRIORITY"


def test_audit_outputs_are_deterministic_and_never_write_human_labels(workspace_tmp_dir):
    prelabels = [_prelabel()]
    requests = build_subagent_audit_requests(prelabels, artifact_refs={}, prelabel_run_id="prelabel-run")
    report = build_subagent_audit_report(prelabels, requests, prelabel_run_id="prelabel-run")
    queue = build_human_review_queue(prelabels, run_id="prelabel-run")

    first = write_prelabel_subagent_audit_outputs(workspace_tmp_dir / "first", requests, report, queue)
    second = write_prelabel_subagent_audit_outputs(workspace_tmp_dir / "second", requests, report, queue)

    for key in first:
        assert _read(first[key]) == _read(second[key])
    assert _json(first["subagent_audit_report_json"])["measurement_validated_allowed"] is False
    assert "human_label" in _read(first["human_review_queue_csv"])
    assert not (Path(first["human_review_queue_jsonl"]).parent / "human_labels.jsonl").exists()


def test_no_external_sdk_import_is_required():
    forbidden = {"openai", "anthropic", "requests", "httpx", "numpy", "pandas", "sklearn"}

    assert forbidden.isdisjoint(set(sys.modules))
