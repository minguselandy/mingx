from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

from cps.experiments.contamination_audit import (
    REQUIRED_CONTAMINATION_CHECKS,
    build_contamination_audit_template,
    evaluate_contamination_audit,
    format_contamination_audit_markdown,
    write_contamination_audit_outputs,
)


def _checks(status: str = "pass", **overrides: str) -> list[dict]:
    rows: list[dict] = []
    for check_name in REQUIRED_CONTAMINATION_CHECKS:
        rows.append(
            {
                "check_name": check_name,
                "status": overrides.get(check_name, status),
                "evidence_ref": f"evidence/{check_name}.json",
                "notes": "",
            }
        )
    return rows


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_template_contains_all_required_checks_without_fabricating_passes():
    template = build_contamination_audit_template(run_id="contamination-run")

    assert template["contamination_audit_schema_version"] == "ContaminationAuditV1"
    assert [row["check_name"] for row in template["checks"]] == list(REQUIRED_CONTAMINATION_CHECKS)
    assert {row["status"] for row in template["checks"]} == {"unknown"}
    assert template["measurement_validated_allowed"] is False


def test_all_pass_contamination_audit_is_not_validation():
    report = evaluate_contamination_audit(_checks(), run_id="contamination-run")

    assert report["contamination_status"] == "pass"
    assert report["contamination_passed"] is True
    assert report["failed_checks"] == []
    assert report["measurement_validated_allowed"] is False
    assert report["allowed_claim_impact"] == "contamination_gate_passed_only"
    assert "contamination_pass_alone_not_validation" in report["reason_codes"]
    assert "human_labels_required" in report["reason_codes"]
    assert "kappa_required" in report["reason_codes"]
    assert "fresh_metric_bridge_required" in report["reason_codes"]
    assert "claim_gate_allow_required" in report["reason_codes"]


def test_one_failed_check_forces_pilot_only():
    report = evaluate_contamination_audit(_checks(leaked_labels="fail"), run_id="contamination-run")

    assert report["contamination_status"] == "failed"
    assert report["contamination_passed"] is False
    assert report["failed_checks"] == ["leaked_labels"]
    assert report["allowed_claim_impact"] == "pilot_only"
    assert report["measurement_validated_allowed"] is False
    assert "contamination_failed" in report["reason_codes"]
    assert "leaked_labels" in report["reason_codes"]


def test_failed_direct_answer_check_uses_stable_reason_code():
    report = evaluate_contamination_audit(
        _checks(candidate_pool_contains_direct_answer="fail"),
        run_id="contamination-run",
    )

    assert report["contamination_status"] == "failed"
    assert "candidate_pool_contains_direct_answer" in report["failed_checks"]
    assert "direct_answer_in_candidate_pool" in report["reason_codes"]


def test_unknown_checks_deny_measurement_validated():
    report = evaluate_contamination_audit(_checks(answer_key_exposure="unknown"), run_id="contamination-run")

    assert report["contamination_status"] == "unknown"
    assert report["contamination_passed"] is False
    assert report["unknown_checks"] == ["answer_key_exposure"]
    assert report["measurement_validated_allowed"] is False
    assert "contamination_unknown" in report["reason_codes"]


def test_incomplete_audit_denies_measurement_validated():
    report = evaluate_contamination_audit(
        [row for row in _checks() if row["check_name"] != "train_test_overlap"],
        run_id="contamination-run",
    )

    assert report["contamination_status"] == "incomplete"
    assert report["contamination_passed"] is False
    assert "train_test_overlap" in report["unknown_checks"]
    assert report["measurement_validated_allowed"] is False
    assert "contamination_incomplete" in report["reason_codes"]


def test_reason_codes_are_stable_ordered():
    report = evaluate_contamination_audit(
        _checks(
            leaked_labels="fail",
            post_hoc_prompt_tuning_on_test_cases="fail",
            answer_key_exposure="unknown",
        ),
        run_id="contamination-run",
    )

    assert report["reason_codes"] == sorted(
        report["reason_codes"],
        key=report["reason_code_order"].index,
    )


def test_json_and_markdown_outputs_are_deterministic(workspace_tmp_dir):
    report = evaluate_contamination_audit(_checks(), run_id="contamination-run")

    first = write_contamination_audit_outputs(workspace_tmp_dir / "first", report)
    second = write_contamination_audit_outputs(workspace_tmp_dir / "second", report)

    assert _read(first["contamination_report_json"]) == _read(second["contamination_report_json"])
    assert _read(first["contamination_report_markdown"]) == _read(second["contamination_report_markdown"])
    assert _json(first["contamination_report_json"])["measurement_validated_allowed"] is False
    assert "Contamination pass alone is not measurement validation" in format_contamination_audit_markdown(report)


def test_no_external_dependency_network_or_reference_access(monkeypatch, workspace_tmp_dir):
    before = set(sys.modules)
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("contamination audit must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    report = evaluate_contamination_audit(_checks(), run_id="contamination-run")
    outputs = write_contamination_audit_outputs(workspace_tmp_dir / "audit", report)
    imported = set(sys.modules) - before

    assert Path(outputs["contamination_report_json"]).exists()
    assert {"openai", "anthropic", "requests", "httpx", "numpy", "pandas", "sklearn"}.isdisjoint(imported)
