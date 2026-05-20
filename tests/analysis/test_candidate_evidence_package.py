from __future__ import annotations

import json

from cps.analysis.candidate_evidence_package import build_candidate_evidence_package


def test_candidate_evidence_package_writes_limited_scope_claim_request(workspace_tmp_dir) -> None:
    result = build_candidate_evidence_package(
        output_dir=workspace_tmp_dir,
        evidence_reports=[
            {"artifact": "ws2.json", "candidate_claim": "operational_confidence_diagnostic"},
            {"artifact": "ws4.json", "candidate_claim": "model_adjudicated_measurement_candidate"},
        ],
    )

    claim_request = json.loads((workspace_tmp_dir / "claim_request.json").read_text(encoding="utf-8"))
    checklist = (workspace_tmp_dir / "independent_review_checklist.md").read_text(encoding="utf-8")

    assert result["status"] == "reviewable_candidate_package_ready"
    assert claim_request["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert claim_request["development_claim_upgrade_performed"] is False
    assert "vinfo_proxy_supported" in claim_request["denied_claims"]
    assert "Verify no raw API responses are stored." in checklist
