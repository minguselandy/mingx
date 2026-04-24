from pathlib import Path

from cps.experiments.artifacts import (
    BudgetWitness,
    CandidatePool,
    MaterializedContext,
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
    diagnostics = ProjectionDiagnostics(
        dispatch_id="dispatch-1",
        agent_id="agent-a",
        round_id="round-1",
        regime="redundancy_dominated",
        gamma_hat=1.0,
        synergy_fraction=0.0,
        greedy_augmented_gap=0.0,
        policy_recommendation="monitored_greedy",
        greedy_value=1.0,
        augmented_value=1.0,
        local_search_value=1.0,
        thresholds={},
        notes="fixture",
    )

    for event_type, record in (
        ("candidate_pool_materialized", pool),
        ("projection_plan_materialized", plan),
        ("budget_witness_materialized", witness),
        ("materialized_context_materialized", context),
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
    assert summary["policy_counts"] == {"monitored_greedy": 1}
    assert summary["per_regime"]["redundancy_dominated"]["avg_gamma_hat"] == 1.0
