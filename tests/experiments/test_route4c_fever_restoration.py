from __future__ import annotations

import json
from pathlib import Path

from cps.experiments.route4c_fever_restoration import assess_route4c
from cps.experiments.route4c_fever_restoration import write_route4c_artifacts


def _serialized(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def test_route4c_missing_fever_sources_fails_closed_without_claim_upgrade(workspace_tmp_dir: Path) -> None:
    package = assess_route4c(root=workspace_tmp_dir)

    assert package.readiness_report["status"] == "blocked_fever_source_unavailable"
    assert package.readiness_report["claim_status"] == "no_claim_upgrade"
    assert package.readiness_report["route4c_second_stratum_supported"] is False
    assert package.readiness_report["candidate_bridge_evidence_accepted"] is False
    assert package.readiness_report["route5_start_condition_satisfied"] is False
    assert package.readiness_report["measurement_validation"] is False
    assert package.readiness_report["metric_bridge_support"] is False
    assert package.readiness_report["calibrated_proxy_supported"] is False
    assert "full_fever_evidence_source_unavailable" in package.readiness_report["reason_codes"]
    assert "missing_fever_candidate_pools" in package.readiness_report["reason_codes"]
    assert "missing_fever_delta_records" in package.readiness_report["reason_codes"]

    assert package.source_manifest["official_fever_evidence_source_restored"] is False
    assert package.source_manifest["raw_dataset_mirror_committed"] is False
    assert package.source_manifest["evidence_sentence_provenance_verified"] is False
    assert package.candidate_pool_manifest["candidate_pools_generated"] == 0
    assert package.candidate_pool_manifest["candidate_pool_rows_available"] == 0
    assert package.candidate_pool_manifest["delta_record_rows_available"] == 0
    assert package.candidate_pool_manifest["logloss_scoring_ready"] is False
    assert package.blocked_report["status"] == "blocked_data_unavailable"
    assert "claims_jsonl:local_fever_claims_not_supplied" in package.blocked_report["blocked_items"]

    serialized = _serialized(
        {
            "blocked_report": package.blocked_report,
            "candidate_pool_manifest": package.candidate_pool_manifest,
            "readiness_report": package.readiness_report,
            "source_manifest": package.source_manifest,
        }
    )
    assert ":\\" not in serialized
    assert "/home/" not in serialized


def test_route4c_writes_required_blocked_artifacts(workspace_tmp_dir: Path) -> None:
    output_dir = workspace_tmp_dir / "artifacts" / "experiments" / "route4c_fever"
    docs_path = workspace_tmp_dir / "docs" / "experiments" / "Route4C-FEVER-restoration-and-second-stratum.md"

    result = write_route4c_artifacts(root=workspace_tmp_dir, output_dir=output_dir, docs_path=docs_path)

    expected_files = {
        "readiness_report": output_dir / "readiness_report.json",
        "source_manifest": output_dir / "source_manifest.json",
        "candidate_pool_manifest": output_dir / "candidate_pool_manifest.json",
        "blocked_report": output_dir / "blocked_report.json",
        "report_doc": docs_path,
    }
    assert result == expected_files
    for path in expected_files.values():
        assert path.exists()

    readiness = json.loads(expected_files["readiness_report"].read_text(encoding="utf-8"))
    candidate_pool_manifest = json.loads(expected_files["candidate_pool_manifest"].read_text(encoding="utf-8"))
    doc = expected_files["report_doc"].read_text(encoding="utf-8")

    assert readiness["status"] == "blocked_fever_source_unavailable"
    assert readiness["paper_evidence"] is False
    assert candidate_pool_manifest["candidate_pool_builder_available"] is True
    assert candidate_pool_manifest["blocked_report_path"] == "artifacts/experiments/route4c_fever/blocked_report.json"
    assert "Claim status: `no_claim_upgrade`" in doc
    assert "FEVER candidate pools were not generated" in doc
    assert "No fabricated FEVER evidence was introduced." in doc
