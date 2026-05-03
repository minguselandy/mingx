from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import pytest

from cps.experiments.controlled_live_pilot import (
    LivePilotGateError,
    build_controlled_live_pilot,
    default_run_manifest,
    format_pilot_summary_markdown,
)


def _case(case_id: str = "case-001") -> dict:
    return {
        "case_id": case_id,
        "input": "Summarize the audit status for this case.",
        "candidates": [
            {"item_id": "a", "text": "Relevant bridge evidence.", "token_cost": 4, "score": 0.9},
            {"item_id": "b", "text": "Secondary replay evidence.", "token_cost": 5, "score": 0.5},
        ],
    }


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def _manifest(**overrides) -> dict:
    manifest = default_run_manifest(output_root="unused-output-root")
    manifest.update(
        {
            "run_id": "controlled-live-test",
            "model_endpoint": "https://example.invalid/v1/chat/completions",
            "model_name": "fixed-test-model",
            "prompt_template_id": "prompt-v1",
            "temperature": 0,
            "max_cases": 1,
        }
    )
    manifest.update(overrides)
    return manifest


def test_default_mode_is_dry_run():
    manifest = default_run_manifest(output_root="out")

    assert manifest["mode"] == "dry_run"
    assert manifest["evidence_level"] == "EV2_controlled_live_pilot"
    assert manifest["live_api_used"] is False
    assert manifest["external_runtime_used"] is False
    assert manifest["human_labels_required_for_measurement_validated"] is True
    assert manifest["kappa_required_for_measurement_validated"] is True


def test_dry_run_makes_no_live_calls(workspace_tmp_dir):
    calls: list[dict] = []

    def forbidden_call(payload):
        calls.append(payload)
        raise AssertionError("dry_run must not call model_call_fn")

    result = build_controlled_live_pilot(
        workspace_tmp_dir / "pilot",
        run_manifest=_manifest(),
        cases=[_case()],
        model_call_fn=forbidden_call,
    )

    assert calls == []
    assert result["manifest"]["mode"] == "dry_run"
    assert result["manifest"]["live_api_used"] is False
    assert result["claim_gate_report"]["measurement_validated_allowed"] is False


def test_live_mode_fails_closed_without_cps_allow_live_api(workspace_tmp_dir, monkeypatch):
    monkeypatch.delenv("CPS_ALLOW_LIVE_API", raising=False)
    calls: list[dict] = []

    with pytest.raises(LivePilotGateError, match="CPS_ALLOW_LIVE_API"):
        build_controlled_live_pilot(
            workspace_tmp_dir / "pilot",
            run_manifest=_manifest(mode="live_operator_approved", operator_approval=True),
            run_manifest_path=workspace_tmp_dir / "manifest.json",
            cases=[_case()],
            model_call_fn=lambda payload: calls.append(payload),
        )

    assert calls == []
    assert not (workspace_tmp_dir / "pilot" / "run_manifest.json").exists()


def test_live_mode_fails_closed_without_operator_approval(workspace_tmp_dir, monkeypatch):
    monkeypatch.setenv("CPS_ALLOW_LIVE_API", "1")
    manifest_path = workspace_tmp_dir / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest(mode="live_operator_approved")), encoding="utf-8")

    with pytest.raises(LivePilotGateError, match="operator_approval"):
        build_controlled_live_pilot(
            workspace_tmp_dir / "pilot",
            run_manifest_path=manifest_path,
            cases=[_case()],
            model_call_fn=lambda payload: {"content": "should not run"},
        )

    assert not (workspace_tmp_dir / "pilot" / "run_manifest.json").exists()


def test_live_mode_fails_closed_without_manifest_path(workspace_tmp_dir, monkeypatch):
    monkeypatch.setenv("CPS_ALLOW_LIVE_API", "1")

    with pytest.raises(LivePilotGateError, match="run_manifest_path"):
        build_controlled_live_pilot(
            workspace_tmp_dir / "pilot",
            run_manifest=_manifest(mode="live_operator_approved", operator_approval=True),
            cases=[_case()],
            model_call_fn=lambda payload: {"content": "should not run"},
        )


def test_fake_model_call_fn_writes_deterministic_model_output(workspace_tmp_dir, monkeypatch):
    monkeypatch.setenv("CPS_ALLOW_LIVE_API", "1")
    manifest_path = workspace_tmp_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(_manifest(mode="live_operator_approved", operator_approval=True), sort_keys=True),
        encoding="utf-8",
    )

    def fake_model(payload):
        return {
            "content": f"{payload['case_id']}::{payload['condition_id']}::{payload['model_name']}",
            "finish_reason": "stop",
        }

    first = build_controlled_live_pilot(
        workspace_tmp_dir / "pilot_a",
        run_manifest_path=manifest_path,
        cases=[_case()],
        model_call_fn=fake_model,
    )
    second = build_controlled_live_pilot(
        workspace_tmp_dir / "pilot_b",
        run_manifest_path=manifest_path,
        cases=[_case()],
        model_call_fn=fake_model,
    )

    output_a = _read(first["case_artifacts"][0]["model_output_json"])
    output_b = _read(second["case_artifacts"][0]["model_output_json"])
    assert output_a == output_b
    assert _json(first["case_artifacts"][0]["model_output_json"])["live_api_used"] is True


def test_manifest_and_summary_are_deterministic(workspace_tmp_dir):
    first = build_controlled_live_pilot(workspace_tmp_dir / "pilot_a", run_manifest=_manifest(), cases=[_case()])
    second = build_controlled_live_pilot(workspace_tmp_dir / "pilot_b", run_manifest=_manifest(), cases=[_case()])

    assert _read(first["generated_outputs"]["run_manifest_json"]) == _read(
        second["generated_outputs"]["run_manifest_json"]
    )
    assert _read(first["generated_outputs"]["pilot_summary_markdown"]) == _read(
        second["generated_outputs"]["pilot_summary_markdown"]
    )
    assert format_pilot_summary_markdown(first) == format_pilot_summary_markdown(second)


def test_missing_labels_and_kappa_deny_measurement_validation(workspace_tmp_dir):
    result = build_controlled_live_pilot(workspace_tmp_dir / "pilot", run_manifest=_manifest(), cases=[_case()])
    report = result["claim_gate_report"]

    assert report["measurement_validated_allowed"] is False
    assert "measurement_validated" in report["denied_claims"]
    assert "missing_human_labels" in report["reason_codes"]
    assert "missing_kappa" in report["reason_codes"]
    assert result["manifest"]["human_labels_present"] is False
    assert result["manifest"]["kappa_present"] is False


def test_live_api_used_alone_does_not_allow_measurement_validation(workspace_tmp_dir, monkeypatch):
    monkeypatch.setenv("CPS_ALLOW_LIVE_API", "1")
    manifest_path = workspace_tmp_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(_manifest(mode="live_operator_approved", operator_approval=True), sort_keys=True),
        encoding="utf-8",
    )

    result = build_controlled_live_pilot(
        workspace_tmp_dir / "pilot",
        run_manifest_path=manifest_path,
        cases=[_case()],
        model_call_fn=lambda payload: {"content": "deterministic live stub", "finish_reason": "stop"},
    )

    assert result["manifest"]["live_api_used"] is True
    assert result["claim_gate_report"]["measurement_validated_allowed"] is False
    assert "live_api_not_validation" in result["claim_gate_report"]["reason_codes"]
    assert "missing_human_labels" in result["claim_gate_report"]["reason_codes"]
    assert "missing_kappa" in result["claim_gate_report"]["reason_codes"]


def test_case_artifacts_are_created(workspace_tmp_dir):
    result = build_controlled_live_pilot(workspace_tmp_dir / "pilot", run_manifest=_manifest(), cases=[_case()])

    expected_names = {
        "input_case_json",
        "candidate_pool_jsonl",
        "projection_plan_json",
        "budget_witness_json",
        "materialized_context_json",
        "metric_bridge_witness_json",
        "projection_bundle_json",
        "model_output_json",
        "claim_gate_report_json",
    }
    assert result["case_artifacts"]
    for artifact in result["case_artifacts"]:
        assert expected_names.issubset(artifact)
        for key in expected_names:
            assert Path(artifact[key]).exists(), key


def test_no_external_sdk_import_is_required(workspace_tmp_dir):
    before = set(sys.modules)
    build_controlled_live_pilot(workspace_tmp_dir / "pilot", run_manifest=_manifest(), cases=[_case()])
    imported = set(sys.modules) - before

    forbidden = {"openai", "anthropic", "dashscope", "requests", "httpx"}
    assert forbidden.isdisjoint(imported)


def test_reason_codes_are_stable_ordered(workspace_tmp_dir):
    result = build_controlled_live_pilot(workspace_tmp_dir / "pilot", run_manifest=_manifest(), cases=[_case()])
    report = result["claim_gate_report"]

    assert report["reason_codes"] == sorted(report["reason_codes"], key=report["reason_code_order"].index)


def test_p04_p09_remain_visible_as_operator_required(workspace_tmp_dir):
    result = build_controlled_live_pilot(workspace_tmp_dir / "pilot", run_manifest=_manifest(), cases=[_case()])
    summary = _read(result["generated_outputs"]["pilot_summary_markdown"])

    assert result["manifest"]["p04_status"] == "deferred/operator-required"
    assert result["manifest"]["p09_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert "P04 remains deferred/operator-required" in summary
    assert "P09 remains BLOCKED_OPERATOR_REQUIRED" in summary


def test_runner_does_not_use_network_or_reference(monkeypatch, workspace_tmp_dir):
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("controlled live pilot dry_run must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    result = build_controlled_live_pilot(workspace_tmp_dir / "pilot", run_manifest=_manifest(), cases=[_case()])

    assert result["manifest"]["live_api_used"] is False
    assert result["manifest"]["external_runtime_used"] is False
