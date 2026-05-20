from __future__ import annotations

from cps.analysis.uncertainty_bounded_reporting import build_uncertainty_report


def test_uncertainty_report_emits_candidate_not_claim_upgrade() -> None:
    report = build_uncertainty_report(
        evidence_items=[
            {"candidate_claim": "operational_confidence_diagnostic", "confidence": 0.8},
            {"candidate_claim": "model_adjudicated_measurement_candidate", "confidence": 0.6},
        ]
    )

    assert report["allowed_claim"] == "uncertainty_bounded_operational_reporting_candidate"
    assert report["claim_upgrade_allowed"] is False
    assert report["lower_confidence_bound"] <= report["mean_confidence"]
