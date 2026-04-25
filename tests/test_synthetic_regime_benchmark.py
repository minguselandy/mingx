import json
from pathlib import Path

from cps.experiments.artifacts import rebuild_projection_summary_from_events
from cps.experiments.synthetic_benchmark import evaluate_pre_registered_validity_gate, run_synthetic_benchmark


def _jsonl_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_synthetic_benchmark_cli_function_writes_replayable_artifacts(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "synthetic_run"

    report = run_synthetic_benchmark(
        config_path="configs/runs/synthetic-regime-smoke.json",
        output_dir=output_dir,
    )

    assert report["status"] == "green"
    for name in (
        "events.jsonl",
        "candidate_pools.jsonl",
        "projection_plans.jsonl",
        "budget_witnesses.jsonl",
        "materialized_contexts.jsonl",
        "metric_bridge_witnesses.jsonl",
        "diagnostics.jsonl",
        "summary.json",
        "report.md",
    ):
        assert (output_dir / name).exists()

    for name in (
        "candidate_pools.jsonl",
        "projection_plans.jsonl",
        "budget_witnesses.jsonl",
        "materialized_contexts.jsonl",
        "metric_bridge_witnesses.jsonl",
        "diagnostics.jsonl",
    ):
        assert len(_jsonl_rows(output_dir / name)) == 3

    events = _jsonl_rows(output_dir / "events.jsonl")
    event_types = [row["event_type"] for row in events]
    assert event_types.count("metric_bridge_witness_materialized") == 3

    event_summary = rebuild_projection_summary_from_events(output_dir, run_id=report["run_id"])
    summary = json.loads(Path(report["summary_path"]).read_text(encoding="utf-8"))
    assert event_summary["dispatch_count"] == summary["dispatch_count"] == 3
    assert event_summary["complete_artifact_sets"] is True
    assert summary["artifact_counts"]["metric_bridge_witnesses"] == 3
    assert summary["metric_claim_level_counts"] == {"structural_synthetic_only": 3}
    assert summary["selector_regime_label_counts"] == {
        "escalate": 2,
        "greedy_valid": 1,
    }
    assert summary["expected_policy_matches"] == 3
    assert summary["pre_registered_gate_passed"] is True
    assert summary["pre_registered_gate_failures"] == []
    assert summary["ambiguity_count"] == 0
    assert summary["selector_action_counts"] == {
        "interaction_aware_local_search": 1,
        "monitored_greedy": 1,
        "seeded_augmented_greedy": 1,
    }

    diagnostics = _jsonl_rows(output_dir / "diagnostics.jsonl")
    for row in diagnostics:
        for key in (
            "dispatch_id",
            "agent_id",
            "round_id",
            "regime",
            "budget_tokens",
            "candidate_count",
            "candidate_pool_hash",
            "algorithm",
            "selected_ids",
            "excluded_ids",
            "estimated_tokens",
            "realized_tokens",
            "within_budget",
            "block_ratio_lcb_b2",
            "block_ratio_lcb_star",
            "trace_decay_proxy",
            "synergy_fraction",
            "positive_interaction_mass_ucb",
            "greedy_augmented_gap",
            "metric_claim_level",
            "selector_regime_label",
            "selector_action",
        ):
            assert key in row
        assert row["within_budget"] is True
        assert row["gamma_hat"] == row["trace_decay_proxy"]
        assert row["gamma_hat_semantics"] == "legacy_trace_decay_proxy_not_submodularity_ratio"
        assert row["policy_recommendation"] == row["selector_action"]

    witnesses = _jsonl_rows(output_dir / "metric_bridge_witnesses.jsonl")
    for row in witnesses:
        assert row["metric_class"] == "synthetic_oracle"
        assert row["diagnostic_claim_level"] == "structural_synthetic_only"
        assert row["drift_status"] == "not_applicable"
        assert row["utility_metric"] == "synthetic_oracle_value"
        assert row["diagnostic_mode"] == "synthetic_oracle"
        assert row["calibration_epoch"] is None
        assert row["bridge_scale"] is None
        assert row["bridge_residual_zeta"] is None
        assert row["effective_sample_size"] is None

    report_text = Path(report["report_path"]).read_text(encoding="utf-8")
    for section in (
        "## Summary",
        "## Artifact completeness",
        "## Pre-registered validity gate",
        "## Regime diagnostics table",
        "## Ambiguity accounting",
        "## Higher-order safety check",
        "## Interpretation limits",
    ):
        assert section in report_text
    assert "MetricBridgeWitness" in report_text
    assert "not a theorem-inheritance claim" in report_text
    assert "not a system-level performance claim" in report_text
    assert "structural_synthetic_only" in report_text
    assert "gamma_hat" not in report_text
    assert "Avg gamma_hat" not in report_text
    assert "Block-ratio LCB" in report_text
    assert "Triple flag" in report_text


def test_synthetic_benchmark_rerun_resets_event_log_for_output_dir(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "synthetic_rerun"

    first = run_synthetic_benchmark(
        config_path="configs/runs/synthetic-regime-smoke.json",
        output_dir=output_dir,
    )
    second = run_synthetic_benchmark(
        config_path="configs/runs/synthetic-regime-smoke.json",
        output_dir=output_dir,
    )

    assert first["status"] == second["status"] == "green"
    summary = json.loads(Path(second["summary_path"]).read_text(encoding="utf-8"))
    assert summary["dispatch_count"] == 3
    assert summary["artifact_counts"] == {
        "candidate_pools": 3,
        "projection_plans": 3,
        "budget_witnesses": 3,
        "materialized_contexts": 3,
        "metric_bridge_witnesses": 3,
        "diagnostics": 3,
    }
    assert summary["selector_regime_label_counts"] == {
        "escalate": 2,
        "greedy_valid": 1,
    }


def _gate_summary(dispatch_count: int) -> dict:
    return {
        "dispatch_count": dispatch_count,
        "complete_artifact_sets": True,
        "artifact_counts": {
            "candidate_pools": dispatch_count,
            "projection_plans": dispatch_count,
            "budget_witnesses": dispatch_count,
            "materialized_contexts": dispatch_count,
            "metric_bridge_witnesses": dispatch_count,
            "diagnostics": dispatch_count,
        },
    }


def _valid_row(regime: str, **overrides) -> dict:
    defaults = {
        "dispatch_id": f"{regime}-fixture",
        "regime": regime,
        "block_ratio_lcb_b2": 1.0,
        "block_ratio_lcb_star": 1.0,
        "block_ratio_lcb_b3": 1.0,
        "trace_decay_proxy": 1.0,
        "synergy_fraction": 0.0,
        "positive_interaction_mass_ucb": 0.0,
        "triple_excess_flag": "none_detected",
        "higher_order_ambiguity_flag": False,
        "greedy_augmented_gap": 0.0,
        "metric_claim_level": "structural_synthetic_only",
        "selector_regime_label": "greedy_valid",
        "selector_action": "monitored_greedy",
        "augmented_value": 1.0,
        "greedy_value": 1.0,
    }
    defaults.update(overrides)
    return defaults


def test_pre_registered_gate_does_not_count_ambiguous_labels_as_success():
    rows = [
        _valid_row("redundancy_dominated"),
        _valid_row(
            "sparse_pairwise_synergy",
            block_ratio_lcb_b2=0.8,
            block_ratio_lcb_star=0.8,
            synergy_fraction=0.2,
            positive_interaction_mass_ucb=0.5,
            selector_regime_label="ambiguous",
            selector_action="no_certified_switch",
            augmented_value=2.0,
            greedy_value=1.0,
        ),
        _valid_row(
            "higher_order_synergy",
            block_ratio_lcb_b2=0.7,
            block_ratio_lcb_star=0.7,
            triple_excess_flag="positive",
            higher_order_ambiguity_flag=True,
            greedy_augmented_gap=0.5,
            selector_regime_label="escalate",
            selector_action="interaction_aware_local_search",
        ),
    ]

    result = evaluate_pre_registered_validity_gate(rows, _gate_summary(len(rows)), {})

    assert result["ambiguity_count"] == 1
    assert result["pre_registered_gate_passed"] is False
    assert any(failure["gate"] == "ambiguity_accounting" for failure in result["pre_registered_gate_failures"])


def test_pre_registered_gate_rejects_higher_order_false_greedy_certification():
    rows = [
        _valid_row("redundancy_dominated"),
        _valid_row(
            "sparse_pairwise_synergy",
            block_ratio_lcb_b2=0.8,
            block_ratio_lcb_star=0.8,
            synergy_fraction=0.2,
            positive_interaction_mass_ucb=0.5,
            selector_regime_label="escalate",
            selector_action="seeded_augmented_greedy",
            augmented_value=2.0,
            greedy_value=1.0,
        ),
        _valid_row(
            "higher_order_synergy",
            triple_excess_flag="not_evaluable",
            higher_order_ambiguity_flag=False,
            selector_regime_label="greedy_valid",
            selector_action="monitored_greedy",
        ),
    ]

    result = evaluate_pre_registered_validity_gate(rows, _gate_summary(len(rows)), {})

    assert result["pre_registered_gate_passed"] is False
    assert any(failure["gate"] == "higher_order_safety" for failure in result["pre_registered_gate_failures"])
