from __future__ import annotations

import json
import socket
from pathlib import Path

from cps.experiments.replay_evidence_package import (
    build_replay_evidence_package_from_summary,
    write_replay_evidence_package,
)
from cps.experiments.route_b_evidence_package import (
    build_route_b_dry_run_package,
    build_route_b_evidence_package_from_artifact_dir,
    format_route_b_claim_gate_markdown,
    write_route_b_evidence_package,
)


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def _case_artifact(case_id: str = "case-001") -> dict:
    return {
        "case_id": case_id,
        "condition": "cps_runtime_audit_scaffold",
        "model_alias": "deepseek_v4_flash",
        "artifact_refs": {
            "model_output_json": f"artifacts/{case_id}/model_output.json",
            "projection_bundle_json": f"artifacts/{case_id}/projection_bundle.json",
        },
        "model_output": {"answer": "CPS uses auditable projection artifacts."},
    }


def _write_route_b_source(source_dir: Path) -> None:
    source_dir.mkdir(parents=True, exist_ok=True)
    source_dir.joinpath("llm_prelabels.jsonl").write_text(
        json.dumps({"case_id": "case-001", "condition": "cps_runtime_audit_scaffold"}, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    source_dir.joinpath("subagent_audit_report.json").write_text(
        json.dumps(
            {
                "prelabel_run_id": "p41-source",
                "total_prelabels": 1,
                "measurement_validated_allowed": False,
                "codex_subagent_audit_is_not_human_review": True,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    source_dir.joinpath("model_adjudicated_labels.jsonl").write_text(
        json.dumps(
            {
                "case_id": "case-001",
                "condition": "cps_runtime_audit_scaffold",
                "label_dimension": "answer_correctness",
                "label": 1,
                "counts_as_human_label": False,
                "counts_for_human_kappa": False,
                "measurement_validated_allowed": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    source_dir.joinpath("codex_adjudication_report.json").write_text(
        json.dumps(
            {
                "total_labels": 1,
                "accepted_model_adjudicated_count": 1,
                "uncertain_count": 0,
                "rejected_or_blocking_warning_count": 0,
                "measurement_validated_allowed": False,
                "allowed_claim_level": "model_adjudicated_pilot_only",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    source_dir.joinpath("model_adjudicated_label_summary.json").write_text(
        json.dumps(
            {
                "total_labels": 1,
                "total_cases": 1,
                "model_adjudicated_labels_present": True,
                "human_labels_present": False,
                "kappa_present": False,
                "measurement_validated_allowed": False,
                "allowed_claim_level": "model_adjudicated_pilot_only",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_route_b_dry_run_emits_required_artifacts_without_human_gates(workspace_tmp_dir):
    result = build_route_b_dry_run_package(
        workspace_tmp_dir / "route-b",
        case_artifacts=[_case_artifact()],
        run_id="p41-dry-run",
    )

    outputs = result["generated_outputs"]
    expected_outputs = {
        "model_prelabels_jsonl",
        "model_prelabel_summary_json",
        "model_prelabel_summary_markdown",
        "subagent_audit_requests_jsonl",
        "subagent_audit_report_json",
        "subagent_audit_report_markdown",
        "model_adjudicated_labels_jsonl",
        "model_adjudicated_label_summary_json",
        "model_adjudicated_label_summary_markdown",
        "route_b_evidence_manifest_json",
        "route_b_claim_gate_report_json",
        "route_b_claim_gate_report_markdown",
    }
    assert expected_outputs.issubset(outputs)
    for key in expected_outputs:
        assert Path(outputs[key]).exists()

    manifest = _json(outputs["route_b_evidence_manifest_json"])
    assert manifest["route_type"] == "model_adjudicated"
    assert manifest["evaluation_route"] == "Route_B_model_adjudicated"
    assert manifest["label_source"] == "model_adjudicated"
    assert manifest["human_labels_present"] is False
    assert manifest["kappa_present"] is False
    assert manifest["human_human_kappa_established"] is False
    assert manifest["measurement_validated_allowed"] is False
    assert manifest["max_claim"] == "model_adjudicated_pilot_only"
    assert manifest["allowed_route_b_claim_level"] == "operational_utility_only"
    assert manifest["live_api_used"] is False


def test_route_b_package_consumes_artifacts_and_replay_manifest(workspace_tmp_dir):
    source_dir = workspace_tmp_dir / "route-b-source"
    _write_route_b_source(source_dir)
    replay_dir = workspace_tmp_dir / "replay-package"
    replay_package = build_replay_evidence_package_from_summary(
        {
            "run_id": "p41-replay",
            "claim_level": "operational_utility_only",
            "dispatch_count": 1,
            "artifact_counts": {
                "candidate_pools": 1,
                "projection_plans": 1,
                "budget_witnesses": 1,
                "materialized_contexts": 1,
                "metric_bridge_witnesses": 1,
                "diagnostics": 1,
                "projection_bundles": 1,
            },
            "complete_artifact_sets": True,
        },
        evidence_overrides={
            "bridge_freshness": "fresh",
            "human_labels_present": False,
            "kappa_present": False,
        },
    )
    write_replay_evidence_package(replay_dir, replay_package)

    package = build_route_b_evidence_package_from_artifact_dir(
        source_dir,
        replay_package_dir=replay_dir,
        evidence_overrides={
            "run_id": "p41-source",
            "metric_bridge_freshness": "fresh",
            "artifact_completeness_status": "complete",
            "contamination_status": "pass",
        },
    )

    manifest = package["manifest"]
    assert manifest["route_b_core_artifacts_present"] is True
    assert manifest["replay_package_present"] is True
    assert manifest["replay_package_claim_scope"] == "operational_utility_only"
    assert manifest["allowed_route_b_claim_level"] == "model_adjudicated_pilot_only"
    assert manifest["measurement_validated_allowed"] is False
    assert manifest["model_adjudication_consistency"] == 1.0
    assert manifest["adjudication_disagreement_rate"] == 0.0


def test_contamination_failure_forces_pilot_only_without_validation_claim(workspace_tmp_dir):
    source_dir = workspace_tmp_dir / "route-b-source"
    _write_route_b_source(source_dir)

    package = build_route_b_evidence_package_from_artifact_dir(
        source_dir,
        evidence_overrides={
            "run_id": "p41-contamination-failure",
            "metric_bridge_freshness": "fresh",
            "artifact_completeness_status": "complete",
            "contamination_status": "failed",
        },
    )

    manifest = package["manifest"]
    assert manifest["allowed_route_b_claim_level"] == "pilot_only"
    assert manifest["measurement_validated_allowed"] is False
    assert "contamination_failed" in manifest["reason_codes"]
    assert "measurement_validated" in manifest["denied_claims"]


def test_route_b_outputs_are_deterministic(workspace_tmp_dir):
    source_dir = workspace_tmp_dir / "route-b-source"
    _write_route_b_source(source_dir)
    package = build_route_b_evidence_package_from_artifact_dir(source_dir)

    first = write_route_b_evidence_package(workspace_tmp_dir / "first", package)
    second = write_route_b_evidence_package(workspace_tmp_dir / "second", package)

    for key in first:
        assert _read(first[key]) == _read(second[key])
    markdown = format_route_b_claim_gate_markdown(package["claim_gate_report"])
    assert "Model-adjudicated labels are not human labels" in markdown
    assert "measurement_validated is denied" in markdown


def test_route_b_package_does_not_use_network_or_provider_sdks(monkeypatch, workspace_tmp_dir):
    before_modules = set(__import__("sys").modules)
    source_dir = workspace_tmp_dir / "route-b-source"
    _write_route_b_source(source_dir)
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("route B evidence package must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    package = build_route_b_evidence_package_from_artifact_dir(source_dir)
    outputs = write_route_b_evidence_package(workspace_tmp_dir / "route-b-out", package)
    imported = set(__import__("sys").modules) - before_modules

    assert Path(outputs["route_b_evidence_manifest_json"]).exists()
    assert {"openai", "anthropic", "requests", "httpx"}.isdisjoint(imported)
