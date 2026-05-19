from __future__ import annotations

from cps.analysis.utility_logloss_alignment import build_alignment_decomposition


def test_alignment_decomposition_reports_weak_signal_and_sanitized_leverage_rows():
    rows = [
        {
            "candidate_pool_hash": "pool-a",
            "delta_logloss": -0.001,
            "delta_utility": 1.0,
            "materialization_policy": "fixed",
            "original_instance_id": "item-a",
            "target_representation": "answer_string",
        },
        {
            "candidate_pool_hash": "pool-b",
            "delta_logloss": 0.0002,
            "delta_utility": 0.0,
            "materialization_policy": "fixed",
            "original_instance_id": "item-b",
            "target_representation": "answer_string",
        },
        {
            "candidate_pool_hash": "pool-c",
            "delta_logloss": -0.4,
            "delta_utility": 0.0,
            "materialization_policy": "fixed",
            "original_instance_id": "item-c",
            "target_representation": "answer_string",
        },
    ]

    decomposition = build_alignment_decomposition(
        route_specs=[
            {
                "fit_summary": {
                    "bridge_fit": {"c_hat_s": -1.0, "normalized_residual": 2.0},
                    "gate_result": "failed_closed_gate_failed",
                    "rows_validated": 3,
                    "unique_original_instances": 3,
                },
                "route_id": "Route4A",
                "rows": rows,
                "target_type": "answer_string",
                "utility_field": "delta_utility",
            }
        ]
    )

    route = decomposition["alignment_by_stratum"]["strata"]["Route4A"]
    assert route["weak_signal_classification"] in {"weak_signal", "mixed_signal"}
    assert route["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert decomposition["alignment_by_target_type"]["target_types"]["answer_string"]["row_count"] == 3
    assert decomposition["residual_tail_audit"]["tail_count"] > 0
    assert decomposition["leverage_rows"][0]["route_id"] == "Route4A"
    assert "target_y" not in decomposition["leverage_rows"][0]
