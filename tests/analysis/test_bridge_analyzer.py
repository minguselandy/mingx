from __future__ import annotations

from cps.analysis.bridge_analyzer import analyze_metric_bridge_shadow


def test_bridge_analyzer_fails_closed_without_validated_rows():
    result = analyze_metric_bridge_shadow([], min_rows=500, min_unique_instances=150)

    assert result["claim_gate_result"]["accepted_metric_claim"] == "operational_utility_only"
    assert result["claim_gate_result"]["calibrated_proxy_supported"] is False
    assert result["metric_bridge_witness"]["bridge_status"] == "failed_closed_no_rows"
    assert result["bridge_fit_summary"]["rows_validated"] == 0
    assert "shadow_metric_bridge" in result["claim_gate_result"]["shadow_labels"]


def test_bridge_analyzer_keeps_underpowered_rows_in_shadow_mode():
    rows = [
        {"instance_id": f"hp-{index}", "delta_logloss": 0.1, "delta_utility": 0.2}
        for index in range(3)
    ]

    result = analyze_metric_bridge_shadow(rows, min_rows=500, min_unique_instances=150)

    assert result["metric_bridge_witness"]["bridge_status"] == "failed_closed_underpowered"
    assert result["bridge_fit_summary"]["rows_validated"] == 3
    assert result["bridge_fit_summary"]["unique_instances"] == 3
    assert result["claim_gate_result"]["claim_mode"] == "shadow"
    assert result["claim_gate_result"]["vinfo_proxy_supported"] is False
