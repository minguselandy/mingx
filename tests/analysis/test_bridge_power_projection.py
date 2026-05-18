from __future__ import annotations

from cps.analysis.bridge_power_projection import project_bridge_power


def test_bridge_power_projection_marks_route4b_underpowered_and_weak_signal():
    projection = project_bridge_power(
        bridge_fit_summary={
            "rows_validated": 300,
            "unique_original_instances": 150,
            "gate_result": "failed_closed_underpowered",
            "bridge_fit": {
                "normalized_residual": 0.994,
                "sign_agreement": 0.38,
                "spearman_rho": 0.231,
            },
            "gate_pass_flags": {
                "row_count_pass": False,
                "normalized_residual_pass": False,
                "sign_agreement_pass": False,
                "spearman_rho_pass": False,
            },
        }
    )

    assert projection["bridge_power_status"] == "underpowered_and_signal_weak"
    assert projection["route4b_is_merely_underpowered"] is False
    assert projection["direct_bridge_scaleup_recommended"] is False
    assert projection["claim_status"] == "operational_utility_only/no_claim_upgrade"
