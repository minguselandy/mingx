from __future__ import annotations

import json
import socket
from pathlib import Path

from cps.experiments.end_to_end_evidence_demo import build_end_to_end_evidence_demo


REQUIRED_OUTPUTS = {
    "projection_bundles_jsonl",
    "evidence_ledger_json",
    "claim_gate_report_json",
    "claim_gate_report_markdown",
    "proxy_regime_matrix_json",
    "proxy_regime_matrix_markdown",
    "replay_package_dir",
    "replay_package_summary_markdown",
    "paper_evidence_summary_json",
    "paper_evidence_summary_markdown",
    "demo_manifest_json",
    "demo_summary_markdown",
}


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_demo_builder_creates_required_output_files(workspace_tmp_dir):
    result = build_end_to_end_evidence_demo(workspace_tmp_dir / "demo")

    assert result["status"] == "green"
    assert REQUIRED_OUTPUTS.issubset(result["generated_outputs"])
    for key in REQUIRED_OUTPUTS:
        path = Path(result["generated_outputs"][key])
        assert path.exists(), key

    replay_dir = Path(result["generated_outputs"]["replay_package_dir"])
    assert replay_dir.is_dir()
    for name in (
        "manifest.json",
        "claim_gate_report.json",
        "claim_gate_report.md",
        "replay_package_summary.md",
    ):
        assert (replay_dir / name).exists()


def test_demo_manifest_and_summary_are_deterministic(workspace_tmp_dir):
    first = build_end_to_end_evidence_demo(workspace_tmp_dir / "demo_a")
    second = build_end_to_end_evidence_demo(workspace_tmp_dir / "demo_b")

    assert _read(first["generated_outputs"]["demo_manifest_json"]) == _read(
        second["generated_outputs"]["demo_manifest_json"]
    )
    assert _read(first["generated_outputs"]["demo_summary_markdown"]) == _read(
        second["generated_outputs"]["demo_summary_markdown"]
    )


def test_demo_json_and_markdown_outputs_are_byte_identical(workspace_tmp_dir):
    first = build_end_to_end_evidence_demo(workspace_tmp_dir / "demo_a")
    second = build_end_to_end_evidence_demo(workspace_tmp_dir / "demo_b")

    json_keys = (
        "evidence_ledger_json",
        "claim_gate_report_json",
        "proxy_regime_matrix_json",
        "paper_evidence_summary_json",
    )
    markdown_keys = (
        "claim_gate_report_markdown",
        "proxy_regime_matrix_markdown",
        "replay_package_summary_markdown",
        "paper_evidence_summary_markdown",
        "demo_summary_markdown",
    )
    for key in json_keys + markdown_keys:
        assert _read(first["generated_outputs"][key]) == _read(second["generated_outputs"][key]), key


def test_demo_manifest_preserves_claim_boundaries(workspace_tmp_dir):
    result = build_end_to_end_evidence_demo(workspace_tmp_dir / "demo")
    manifest = _json(result["generated_outputs"]["demo_manifest_json"])

    assert manifest["demo_schema_version"] == "EndToEndEvidenceDemoV1"
    assert manifest["run_id"] == "p17_offline_evidence_demo"
    assert manifest["evidence_mode"] == "offline_runtime_audit_demo"
    assert manifest["source_phase"] == "P17"
    assert manifest["projection_bundle_count"] == 2
    assert manifest["measurement_validated_allowed"] is False
    assert manifest["p04_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert manifest["p09_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert manifest["live_api_used"] is False
    assert manifest["external_runtime_used"] is False
    assert "measurement_validated" in manifest["denied_claims"]
    assert "engineering_evidence_only" in manifest["reason_codes"]
    assert "measurement_validated is not claimed" in manifest["final_claim_boundary"]


def test_demo_outputs_include_expected_markdown_reports(workspace_tmp_dir):
    result = build_end_to_end_evidence_demo(workspace_tmp_dir / "demo")

    assert "Metric bridge gate status" in _read(result["generated_outputs"]["claim_gate_report_markdown"])
    assert "proxy-regime certification is not deployed V-information certification" in _read(
        result["generated_outputs"]["proxy_regime_matrix_markdown"]
    )
    assert "Replay package completeness is not scientific validation" in _read(
        result["generated_outputs"]["replay_package_summary_markdown"]
    )
    assert "paper-facing summaries do not upgrade claim levels" in _read(
        result["generated_outputs"]["paper_evidence_summary_markdown"]
    )


def test_demo_summary_markdown_includes_required_sections_and_limits(workspace_tmp_dir):
    result = build_end_to_end_evidence_demo(workspace_tmp_dir / "demo")
    summary = _read(result["generated_outputs"]["demo_summary_markdown"])

    for section in (
        "Generated Outputs",
        "Artifact Evidence Summary",
        "Claim Gate Summary",
        "Proxy-Regime Summary",
        "Replay Package Summary",
        "Paper Evidence Summary",
        "Denied Claims",
        "Limitations",
    ):
        assert section in summary
    assert "P17 is offline runtime-audit evidence only" in summary
    assert "P17 is not scientific validation" in summary
    assert "P17 does not claim measurement_validated" in summary
    assert "Synthetic success does not certify deployed V-information submodularity" in summary
    assert "P04 remains deferred/operator-required" in summary
    assert "P09 remains BLOCKED_OPERATOR_REQUIRED" in summary


def test_demo_reason_codes_are_stable_ordered(workspace_tmp_dir):
    result = build_end_to_end_evidence_demo(workspace_tmp_dir / "demo")
    manifest = _json(result["generated_outputs"]["demo_manifest_json"])
    claim_gate = _json(result["generated_outputs"]["claim_gate_report_json"])

    assert manifest["reason_codes"] == sorted(
        manifest["reason_codes"],
        key=claim_gate["reason_code_order"].index,
    )


def test_demo_does_not_use_network_or_reference(monkeypatch, workspace_tmp_dir):
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("end-to-end evidence demo must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    result = build_end_to_end_evidence_demo(workspace_tmp_dir / "demo")

    assert result["manifest"]["live_api_used"] is False
    assert result["manifest"]["external_runtime_used"] is False
