from __future__ import annotations

import json
from pathlib import Path

from cps.experiments.route8_final_integration import assess_route8_final_integration
from cps.experiments.route8_final_integration import write_route8_artifacts


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_blocked_route_inputs(root: Path) -> None:
    _write_json(
        root / "artifacts/experiments/route6a_measurement_pilot/adjudication_report.json",
        {
            "accepted_model_adjudicated_count": 22,
            "claim_status": "no_claim_upgrade",
            "counts_as_human_labels": False,
            "live_api_used": True,
            "measurement_validation_candidate_allowed": False,
        },
    )
    _write_json(
        root / "artifacts/experiments/route4b_bridge_to_measurement/claim_gate_result.json",
        {
            "calibrated_proxy_supported": False,
            "claim_status": "no_claim_upgrade",
            "gate_result": "failed_closed_underpowered",
            "metric_bridge_support_candidate": False,
        },
    )
    _write_json(
        root / "artifacts/experiments/route4c_fever/readiness_report.json",
        {
            "candidate_bridge_evidence_accepted": False,
            "claim_status": "no_claim_upgrade",
            "route4c_second_stratum_supported": False,
            "status": "blocked_fever_source_unavailable",
        },
    )
    _write_json(
        root / "artifacts/experiments/route5_fixed_model_logloss_proxy/readiness_report.json",
        {
            "claim_status": "no_claim_upgrade",
            "start_condition_satisfied": False,
            "status": "blocked_route4_candidate_bridge_required",
            "vinfo_proxy_supported_candidate": False,
        },
    )
    _write_json(
        root / "artifacts/experiments/route7_scoped_selector_superiority/readiness_report.json",
        {
            "claim_status": "no_claim_upgrade",
            "route7_claim_allowed": False,
            "scoped_multi_benchmark_selector_superiority": False,
            "status": "blocked_multi_benchmark_requirements_unmet",
        },
    )


def test_route8_blocks_final_integration_without_accepted_evidence_packages(workspace_tmp_dir: Path) -> None:
    _write_blocked_route_inputs(workspace_tmp_dir)

    package = assess_route8_final_integration(root=workspace_tmp_dir)

    assert package.readiness_report["status"] == "blocked_no_accepted_evidence_packages"
    assert package.readiness_report["final_program_status"] == "honestly_blocked"
    assert package.readiness_report["claim_status"] == "no_claim_upgrade"
    assert package.readiness_report["accepted_evidence_packages"] == []
    assert package.readiness_report["manuscript_update_allowed"] is False
    assert package.readiness_report["claim_ledger_update_allowed"] is False
    assert package.readiness_report["manuscript_update_attempted"] is False
    assert package.readiness_report["claim_ledger_update_attempted"] is False
    assert "claim_upgrade_unsupported" in package.readiness_report["reason_codes"]
    assert "no_route8_claim_ledger_or_manuscript_update" in package.readiness_report["reason_codes"]

    assert package.evidence_status_summary["routes"]["Route6A"]["status"] == "model_adjudication_completed_no_measurement_validation"
    assert package.evidence_status_summary["routes"]["Route4B"]["status"] == "failed_closed_underpowered"
    assert package.evidence_status_summary["routes"]["Route4C"]["status"] == "blocked_fever_source_unavailable"
    assert package.evidence_status_summary["routes"]["Route5"]["status"] == "blocked_route4_candidate_bridge_required"
    assert package.evidence_status_summary["routes"]["Route7"]["status"] == "blocked_multi_benchmark_requirements_unmet"
    assert "calibrated_proxy_supported" in package.blocked_claims_report["blocked_claims"]


def test_route8_writes_final_blocked_artifacts_and_doc(workspace_tmp_dir: Path) -> None:
    _write_blocked_route_inputs(workspace_tmp_dir)
    output_dir = workspace_tmp_dir / "artifacts" / "experiments" / "route8_final_integration"
    docs_path = workspace_tmp_dir / "docs" / "experiments" / "Route8-final-integration-blocked-report.md"

    result = write_route8_artifacts(root=workspace_tmp_dir, output_dir=output_dir, docs_path=docs_path)

    expected = {
        "blocked_claims_report": output_dir / "blocked_claims_report.json",
        "evidence_status_summary": output_dir / "evidence_status_summary.json",
        "integration_gate_report": output_dir / "integration_gate_report.json",
        "readiness_report": output_dir / "readiness_report.json",
        "report_doc": docs_path,
    }
    assert result == expected
    for path in expected.values():
        assert path.exists()

    readiness = json.loads(expected["readiness_report"].read_text(encoding="utf-8"))
    doc = expected["report_doc"].read_text(encoding="utf-8")

    assert readiness["status"] == "blocked_no_accepted_evidence_packages"
    assert "Claim status: `no_claim_upgrade`" in doc
    assert "No manuscript or claim-ledger edits were made." in doc
    assert "Final program status: `honestly_blocked`" in doc


def test_route8_hotpotqa_only_ignores_disabled_route4c_fever(workspace_tmp_dir: Path) -> None:
    _write_blocked_route_inputs(workspace_tmp_dir)
    _write_json(
        workspace_tmp_dir / "artifacts/experiments/route5_hotpotqa_fixed_model_logloss_proxy/readiness_report.json",
        {
            "claim_status": "no_claim_upgrade",
            "scope": "hotpotqa_only",
            "start_condition_satisfied": False,
            "status": "blocked_hotpotqa_route4b_candidate_bridge_required",
            "vinfo_proxy_supported_candidate": False,
        },
    )
    _write_json(
        workspace_tmp_dir / "artifacts/experiments/route7_hotpotqa_first_selector_comparison/readiness_report.json",
        {
            "claim_status": "no_claim_upgrade",
            "hotpotqa_first_selector_comparison_available": True,
            "route7_claim_allowed": False,
            "scope": "hotpotqa_only",
            "status": "hotpotqa_first_operational_comparison_available_no_claim_upgrade",
        },
    )

    package = assess_route8_final_integration(root=workspace_tmp_dir, hotpotqa_only=True)

    assert package.readiness_report["status"] == "blocked_hotpotqa_only_no_accepted_claim_upgrade_evidence"
    assert package.readiness_report["scope"] == "hotpotqa_only"
    assert package.readiness_report["final_program_status"] == "honestly_blocked"
    assert package.readiness_report["accepted_evidence_packages"] == []
    assert "Route4C" not in package.evidence_status_summary["routes"]
    assert package.evidence_status_summary["routes"]["Route5"]["status"] == "blocked_hotpotqa_route4b_candidate_bridge_required"
    assert (
        package.evidence_status_summary["routes"]["Route7"]["status"]
        == "hotpotqa_first_operational_comparison_available_no_claim_upgrade"
    )
    assert "hotpotqa_route4b_failed_closed_underpowered" in package.readiness_report["reason_codes"]
    assert "fever" not in json.dumps(package.readiness_report, sort_keys=True).lower()
