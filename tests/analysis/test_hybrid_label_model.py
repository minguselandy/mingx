from __future__ import annotations

from cps.analysis.hybrid_label_model import build_hybrid_validation_candidate


def test_hybrid_validation_blocks_measurement_candidate_without_human_gold() -> None:
    report = build_hybrid_validation_candidate(
        human_gold_manifest={"human_external_gold_available": False},
        judge_audit={"status": "weak_source_audit_completed"},
        label_rows=[{"label": "supporting"}],
    )

    assert report["measurement_validation_candidate"] is False
    assert report["status"] == "blocked_no_human_external_gold"
    assert report["claim_status"] == "operational_utility_only/no_claim_upgrade"
