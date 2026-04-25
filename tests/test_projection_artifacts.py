from pathlib import Path

from cps.experiments.artifacts import (
    BudgetWitness,
    CandidatePool,
    MaterializedContext,
    MetricBridgeWitness,
    ProjectionDiagnostics,
    ProjectionPlan,
    append_projection_event,
    rebuild_projection_summary_from_events,
    to_payload,
)


def test_projection_artifacts_round_trip_through_event_log(workspace_tmp_dir):
    store_dir = workspace_tmp_dir / "projection_run"
    common = {
        "dispatch_id": "dispatch-1",
        "agent_id": "agent-a",
        "round_id": "round-1",
        "regime": "redundancy_dominated",
        "seed": 20260418,
        "protocol_version": "synthetic_regime.v1",
    }
    pool = CandidatePool(
        dispatch_id="dispatch-1",
        agent_id="agent-a",
        round_id="round-1",
        regime="redundancy_dominated",
        budget_tokens=10,
        items=[{"item_id": "a", "token_cost": 5, "text": "A", "singleton_value": 1.0}],
        candidate_pool_hash="pool-hash",
    )
    plan = ProjectionPlan(
        dispatch_id="dispatch-1",
        agent_id="agent-a",
        round_id="round-1",
        regime="redundancy_dominated",
        algorithm="greedy",
        budget_tokens=10,
        candidate_pool_hash="pool-hash",
        selected_ids=["a"],
        excluded_ids=[],
        trace=[],
        score_config={},
    )
    witness = BudgetWitness(
        dispatch_id="dispatch-1",
        agent_id="agent-a",
        round_id="round-1",
        regime="redundancy_dominated",
        budget_tokens=10,
        estimated_tokens=5,
        realized_tokens=5,
        within_budget=True,
        selected_ids=["a"],
        excluded_ids=[],
        tolerance_violations=[],
    )
    context = MaterializedContext(
        dispatch_id="dispatch-1",
        agent_id="agent-a",
        round_id="round-1",
        regime="redundancy_dominated",
        selected_ids=["a"],
        section_order=["a"],
        content="[a]\nA",
        token_count=5,
        context_hash="context-hash",
    )
    metric_bridge = MetricBridgeWitness(
        dispatch_id="dispatch-1",
        agent_id="agent-a",
        round_id="round-1",
        regime="redundancy_dominated",
        calibration_epoch=None,
        active_stratum={"regime": "redundancy_dominated"},
        model_tier=None,
        utility_metric="synthetic_oracle_value",
        metric_class="synthetic_oracle",
        materialization_policy={"algorithm": "greedy"},
        decoding_policy={"mode": "not_applicable"},
        bridge_scale=None,
        bridge_residual_zeta=None,
        effective_sample_size=None,
        drift_status="not_applicable",
        diagnostic_mode="synthetic_oracle",
        diagnostic_claim_level="structural_synthetic_only",
    )
    diagnostics = ProjectionDiagnostics(
        dispatch_id="dispatch-1",
        agent_id="agent-a",
        round_id="round-1",
        regime="redundancy_dominated",
        block_ratio_lcb_b2=1.0,
        block_ratio_lcb_star=1.0,
        block_ratio_lcb_star_semantics="placeholder_conservative_min_b2_b3_not_degree_adaptive_star",
        block_ratio_lcb_b3=None,
        block_ratio_uninformative_count=0,
        block_ratio_sample_count=1,
        trace_decay_proxy=1.0,
        gamma_hat=1.0,
        synergy_fraction=0.0,
        positive_interaction_mass_ucb=0.0,
        triple_excess_lcb_max=None,
        triple_excess_flag="not_evaluable",
        higher_order_ambiguity_flag=False,
        greedy_augmented_gap=0.0,
        metric_claim_level="structural_synthetic_only",
        selector_regime_label="greedy_valid",
        selector_action="monitored_greedy",
        policy_recommendation="monitored_greedy",
        greedy_value=1.0,
        augmented_value=1.0,
        local_search_value=1.0,
        pairwise_samples=[],
        block_ratio_samples=[],
        triple_samples=[],
        thresholds={},
        notes="fixture",
    )

    for event_type, record in (
        ("candidate_pool_materialized", pool),
        ("projection_plan_materialized", plan),
        ("budget_witness_materialized", witness),
        ("materialized_context_materialized", context),
        ("metric_bridge_witness_materialized", metric_bridge),
        ("projection_diagnostics_materialized", diagnostics),
    ):
        append_projection_event(
            store_dir=store_dir,
            event_type=event_type,
            run_id="run-1",
            payload={**to_payload(record), **common},
            notes="fixture",
        )

    summary = rebuild_projection_summary_from_events(store_dir, run_id="run-1")

    assert Path(store_dir / "events.jsonl").exists()
    assert summary["source_of_truth"] == "event_log"
    assert summary["dispatch_count"] == 1
    assert summary["complete_artifact_sets"] is True
    assert summary["artifact_counts"]["metric_bridge_witnesses"] == 1
    assert summary["metric_claim_level_counts"] == {"structural_synthetic_only": 1}
    assert summary["selector_regime_label_counts"] == {"greedy_valid": 1}
    assert summary["selector_action_counts"] == {"monitored_greedy": 1}
    assert summary["per_regime"]["redundancy_dominated"]["avg_block_ratio_lcb_star"] == 1.0
    assert "avg_gamma_hat" not in summary["per_regime"]["redundancy_dominated"]


def test_projection_summary_requires_metric_bridge_witness(workspace_tmp_dir):
    store_dir = workspace_tmp_dir / "projection_run_missing_metric_bridge"
    common = {
        "dispatch_id": "dispatch-1",
        "agent_id": "agent-a",
        "round_id": "round-1",
        "regime": "redundancy_dominated",
        "seed": 20260418,
        "protocol_version": "synthetic_regime.v1",
    }
    records = (
        (
            "candidate_pool_materialized",
            CandidatePool(
                dispatch_id="dispatch-1",
                agent_id="agent-a",
                round_id="round-1",
                regime="redundancy_dominated",
                budget_tokens=10,
                items=[{"item_id": "a", "token_cost": 5, "text": "A", "singleton_value": 1.0}],
                candidate_pool_hash="pool-hash",
            ),
        ),
        (
            "projection_plan_materialized",
            ProjectionPlan(
                dispatch_id="dispatch-1",
                agent_id="agent-a",
                round_id="round-1",
                regime="redundancy_dominated",
                algorithm="greedy",
                budget_tokens=10,
                candidate_pool_hash="pool-hash",
                selected_ids=["a"],
                excluded_ids=[],
                trace=[],
                score_config={},
            ),
        ),
        (
            "budget_witness_materialized",
            BudgetWitness(
                dispatch_id="dispatch-1",
                agent_id="agent-a",
                round_id="round-1",
                regime="redundancy_dominated",
                budget_tokens=10,
                estimated_tokens=5,
                realized_tokens=5,
                within_budget=True,
                selected_ids=["a"],
                excluded_ids=[],
                tolerance_violations=[],
            ),
        ),
        (
            "materialized_context_materialized",
            MaterializedContext(
                dispatch_id="dispatch-1",
                agent_id="agent-a",
                round_id="round-1",
                regime="redundancy_dominated",
                selected_ids=["a"],
                section_order=["a"],
                content="[a]\nA",
                token_count=5,
                context_hash="context-hash",
            ),
        ),
        (
            "projection_diagnostics_materialized",
            ProjectionDiagnostics(
                dispatch_id="dispatch-1",
                agent_id="agent-a",
                round_id="round-1",
                regime="redundancy_dominated",
                block_ratio_lcb_b2=1.0,
                block_ratio_lcb_star=1.0,
                block_ratio_lcb_star_semantics="placeholder_conservative_min_b2_b3_not_degree_adaptive_star",
                block_ratio_lcb_b3=None,
                block_ratio_uninformative_count=0,
                block_ratio_sample_count=1,
                trace_decay_proxy=1.0,
                gamma_hat=1.0,
                synergy_fraction=0.0,
                positive_interaction_mass_ucb=0.0,
                triple_excess_lcb_max=None,
                triple_excess_flag="not_evaluable",
                higher_order_ambiguity_flag=False,
                greedy_augmented_gap=0.0,
                metric_claim_level="structural_synthetic_only",
                selector_regime_label="greedy_valid",
                selector_action="monitored_greedy",
                policy_recommendation="monitored_greedy",
                greedy_value=1.0,
                augmented_value=1.0,
                local_search_value=1.0,
                pairwise_samples=[],
                block_ratio_samples=[],
                triple_samples=[],
                thresholds={},
                notes="fixture",
            ),
        ),
    )

    for event_type, record in records:
        append_projection_event(
            store_dir=store_dir,
            event_type=event_type,
            run_id="run-1",
            payload={**to_payload(record), **common},
            notes="fixture",
        )

    summary = rebuild_projection_summary_from_events(store_dir, run_id="run-1")

    assert summary["artifact_counts"]["metric_bridge_witnesses"] == 0
    assert summary["complete_artifact_sets"] is False
