from __future__ import annotations

import json
from pathlib import Path

from cps.experiments.route5_fixed_model_logloss_proxy import assess_route5_start_gate
from cps.experiments.route5_fixed_model_logloss_proxy import write_route5_artifacts


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_route5_blocks_when_route4_candidate_bridge_evidence_is_absent(workspace_tmp_dir: Path) -> None:
    _write_json(
        workspace_tmp_dir / "artifacts/experiments/route4b_bridge_to_measurement/claim_gate_result.json",
        {
            "claim_status": "no_claim_upgrade",
            "gate_result": "failed_closed_underpowered",
            "metric_bridge_support_candidate": False,
        },
    )
    _write_json(
        workspace_tmp_dir / "artifacts/experiments/route4b_bridge_to_measurement/metric_bridge_witness.json",
        {
            "bridge_status": "failed_closed_underpowered",
            "metric_claim_level": "failed_closed_no_claim_upgrade",
            "reason_codes": ["row_count_below_minimum"],
        },
    )
    _write_json(
        workspace_tmp_dir / "artifacts/experiments/route4c_fever/readiness_report.json",
        {
            "candidate_bridge_evidence_accepted": False,
            "claim_status": "no_claim_upgrade",
            "reason_codes": ["full_fever_evidence_source_unavailable"],
            "status": "blocked_fever_source_unavailable",
        },
    )

    package = assess_route5_start_gate(root=workspace_tmp_dir)

    assert package.readiness_report["status"] == "blocked_route4_candidate_bridge_required"
    assert package.readiness_report["claim_status"] == "no_claim_upgrade"
    assert package.readiness_report["start_condition_satisfied"] is False
    assert package.readiness_report["live_api_used"] is False
    assert package.readiness_report["fixed_model_logloss_proxy_verification_started"] is False
    assert package.readiness_report["vinfo_proxy_supported_candidate"] is False
    assert package.readiness_report["vinfo_proxy_supported"] is False
    assert "no_accepted_route4_candidate_bridge_evidence" in package.readiness_report["reason_codes"]
    assert "route4b_failed_closed_underpowered" in package.readiness_report["reason_codes"]
    assert "route4c_blocked_fever_source_unavailable" in package.readiness_report["reason_codes"]

    gate = package.dependency_gate_report
    assert gate["route4b"]["accepted_candidate_bridge_evidence"] is False
    assert gate["route4c"]["accepted_candidate_bridge_evidence"] is False
    assert gate["route5_live_api_allowed"] is False
    assert gate["blocked_before_live_api"] is True


def test_route5_writes_blocked_reports_and_doc(workspace_tmp_dir: Path) -> None:
    output_dir = workspace_tmp_dir / "artifacts" / "experiments" / "route5_fixed_model_logloss_proxy"
    docs_path = workspace_tmp_dir / "docs" / "experiments" / "Route5-fixed-model-logloss-proxy-blocked-report.md"

    result = write_route5_artifacts(root=workspace_tmp_dir, output_dir=output_dir, docs_path=docs_path)

    expected = {
        "readiness_report": output_dir / "readiness_report.json",
        "dependency_gate_report": output_dir / "dependency_gate_report.json",
        "report_doc": docs_path,
    }
    assert result == expected
    for path in expected.values():
        assert path.exists()

    readiness = json.loads(expected["readiness_report"].read_text(encoding="utf-8"))
    gate = json.loads(expected["dependency_gate_report"].read_text(encoding="utf-8"))
    doc = expected["report_doc"].read_text(encoding="utf-8")

    assert readiness["status"] == "blocked_route4_candidate_bridge_required"
    assert readiness["live_api_used"] is False
    assert gate["blocked_before_live_api"] is True
    assert "Claim status: `no_claim_upgrade`" in doc
    assert "Live API use was not invoked" in doc
    assert "`vinfo_proxy_supported_candidate` remains false" in doc


def test_route5_hotpotqa_only_ignores_disabled_fever_route4c(workspace_tmp_dir: Path) -> None:
    _write_json(
        workspace_tmp_dir / "artifacts/experiments/route4b_bridge_to_measurement/claim_gate_result.json",
        {
            "claim_status": "no_claim_upgrade",
            "gate_result": "failed_closed_underpowered",
            "metric_bridge_support_candidate": False,
        },
    )
    _write_json(
        workspace_tmp_dir / "artifacts/experiments/route4b_bridge_to_measurement/metric_bridge_witness.json",
        {
            "bridge_status": "failed_closed_underpowered",
            "metric_claim_level": "failed_closed_no_claim_upgrade",
            "reason_codes": ["row_count_below_minimum"],
        },
    )

    package = assess_route5_start_gate(root=workspace_tmp_dir, hotpotqa_only=True)

    assert package.readiness_report["status"] == "blocked_hotpotqa_route4b_candidate_bridge_required"
    assert package.readiness_report["scope"] == "hotpotqa_only"
    assert package.readiness_report["start_condition_satisfied"] is False
    assert package.readiness_report["live_api_used"] is False
    assert package.dependency_gate_report["route4c_disabled"] is True
    assert "route4c" not in package.dependency_gate_report
    assert "route4b_failed_closed_underpowered" in package.readiness_report["reason_codes"]
    assert "route4c_blocked_fever_source_unavailable" not in package.readiness_report["reason_codes"]
