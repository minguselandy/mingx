from __future__ import annotations

from cps.analysis.judge_weak_source_audit import audit_judge_weak_source


def test_judge_weak_source_audit_tracks_consistency_and_keeps_weak_source_ceiling() -> None:
    rows = [
        {"parent_sample_id": "a", "probe_type": "primary", "label": "supporting", "parse_ok": True},
        {"parent_sample_id": "a", "probe_type": "duplicate", "label": "supporting", "parse_ok": True},
        {"parent_sample_id": "a", "probe_type": "order_swap", "label": "not_supporting", "parse_ok": True},
        {"parent_sample_id": "b", "probe_type": "primary", "label": "parse_failed", "parse_ok": False},
    ]

    report = audit_judge_weak_source(rows)

    assert report["claim_ceiling"] == "model_adjudicated_measurement_candidate"
    assert report["duplicate_consistency"]["total"] == 1
    assert report["duplicate_consistency"]["consistent"] == 1
    assert report["order_swap_consistency"]["consistent"] == 0
    assert report["json_validity"]["parse_failure_count"] == 1
    assert report["counts_as_human_or_external_gold"] is False
