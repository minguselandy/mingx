import json
import builtins
from pathlib import Path

from cps.experiments.artifacts import rebuild_projection_summary_from_events
from cps.experiments.synthetic_benchmark import (
    _artifact_completeness_passed,
    evaluate_pre_registered_validity_gate,
    run_synthetic_benchmark,
)
from cps.experiments.synthetic_regimes import (
    SyntheticRegimeConfig,
    block_ratio,
    build_synthetic_instance_from_config,
    build_synthetic_instances,
    pairwise_interaction,
    singleton_marginal,
    triple_excess,
    value_of_set,
)
from cps.experiments.selection import brute_force_optimal_select, greedy_select
from cps.schema.projection_bundle_v1 import ProjectionBundleV1


def _jsonl_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _stable_summary_payload(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("output_dir", None)
    payload.pop("artifact_paths", None)
    payload.pop("config_path", None)
    return payload


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
        "projection_bundles.jsonl",
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
        "projection_bundles.jsonl",
    ):
        assert len(_jsonl_rows(output_dir / name)) == 3

    events = _jsonl_rows(output_dir / "events.jsonl")
    event_types = [row["event_type"] for row in events]
    assert event_types.count("metric_bridge_witness_materialized") == 3
    assert event_types.count("projection_bundle_materialized") == 3

    event_summary = rebuild_projection_summary_from_events(output_dir, run_id=report["run_id"])
    summary = json.loads(Path(report["summary_path"]).read_text(encoding="utf-8"))
    assert event_summary["dispatch_count"] == summary["dispatch_count"] == 3
    assert event_summary["complete_artifact_sets"] is True
    assert summary["artifact_counts"]["metric_bridge_witnesses"] == 3
    assert summary["artifact_counts"]["projection_bundles"] == 3
    assert summary["metric_claim_level_counts"] == {"ambiguous_metric": 3}
    assert summary["diagnostic_scope_counts"] == {"synthetic_structural_only": 3}
    assert summary["selector_regime_label_counts"] == {
        "greedy_supported": 1,
        "higher_order_risk": 1,
        "pairwise_escalate": 1,
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
            "block_ratio_lcb_star_semantics",
            "trace_decay_proxy",
            "synergy_fraction",
            "positive_interaction_mass_ucb",
            "greedy_augmented_gap",
            "metric_claim_level",
            "diagnostic_scope",
            "selector_regime_label",
            "selector_action",
        ):
            assert key in row
        assert row["within_budget"] is True
        assert row["gamma_hat"] == row["trace_decay_proxy"]
        assert row["gamma_hat_semantics"] == "legacy_trace_decay_alias_not_submodularity_ratio"
        assert row["block_ratio_lcb_star_semantics"] == "placeholder_conservative_min_b2_b3_not_degree_adaptive_star"
        assert row["policy_recommendation"] == row["selector_action"]
        assert row["oracle_status"] in {"available", "skipped_large_n"}
        if row["oracle_status"] == "available":
            assert row["oracle_value"] >= row["greedy_value"]
            assert row["oracle_gap"] >= 0.0
        assert row["metric_claim_level"] == "ambiguous_metric"
        assert row["diagnostic_scope"] == "synthetic_structural_only"
        assert row["metric_claim_level"] not in {
            "Vinfo_proxy_certified",
            "vinfo_proxy_supported",
            "measurement_validated",
        }
        assert row["selector_regime_label"] not in {"greedy_valid", "escalate"}

    witnesses = _jsonl_rows(output_dir / "metric_bridge_witnesses.jsonl")
    for row in witnesses:
        assert row["metric_class"] == "synthetic_oracle"
        assert row["diagnostic_claim_level"] == "ambiguous_metric"
        assert row["diagnostic_scope"] == "synthetic_structural_only"
        assert row["drift_status"] == "fresh"
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
    assert "synthetic_structural_only" in report_text
    assert "vinfo_proxy_supported" not in report_text
    assert "gamma_hat" not in report_text
    assert "Avg gamma_hat" not in report_text
    assert "Block-ratio LCB" in report_text
    assert "placeholder_conservative_min_b2_b3_not_degree_adaptive_star" in report_text
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
        "projection_bundles": 3,
    }
    assert summary["selector_regime_label_counts"] == {
        "greedy_supported": 1,
        "higher_order_risk": 1,
        "pairwise_escalate": 1,
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
            "projection_bundles": dispatch_count,
        },
    }


def test_artifact_completeness_requires_projection_bundle_count_key():
    summary = _gate_summary(1)
    del summary["artifact_counts"]["projection_bundles"]

    assert _artifact_completeness_passed(summary) is False


def test_artifact_completeness_rejects_zero_projection_bundles():
    summary = _gate_summary(1)
    summary["artifact_counts"]["projection_bundles"] = 0

    assert _artifact_completeness_passed(summary) is False


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
        "metric_claim_level": "ambiguous_metric",
        "diagnostic_scope": "synthetic_structural_only",
        "selector_regime_label": "greedy_supported",
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
            selector_regime_label="higher_order_risk",
            selector_action="interaction_aware_local_search",
        ),
    ]

    result = evaluate_pre_registered_validity_gate(rows, _gate_summary(len(rows)), {})

    assert result["ambiguity_count"] == 1
    assert result["pre_registered_gate_passed"] is False
    assert any(failure["gate"] == "ambiguity_accounting" for failure in result["pre_registered_gate_failures"])


def test_pre_registered_gate_rejects_higher_order_false_greedy_support():
    rows = [
        _valid_row("redundancy_dominated"),
        _valid_row(
            "sparse_pairwise_synergy",
            block_ratio_lcb_b2=0.8,
            block_ratio_lcb_star=0.8,
            synergy_fraction=0.2,
            positive_interaction_mass_ucb=0.5,
            selector_regime_label="pairwise_escalate",
            selector_action="seeded_augmented_greedy",
            augmented_value=2.0,
            greedy_value=1.0,
        ),
        _valid_row(
            "higher_order_synergy",
            triple_excess_flag="not_evaluable",
            higher_order_ambiguity_flag=False,
            selector_regime_label="greedy_supported",
            selector_action="monitored_greedy",
        ),
    ]

    result = evaluate_pre_registered_validity_gate(rows, _gate_summary(len(rows)), {})

    assert result["pre_registered_gate_passed"] is False
    assert any(failure["gate"] == "higher_order_safety" for failure in result["pre_registered_gate_failures"])


def test_same_seed_generation_and_outputs_are_deterministic(workspace_tmp_dir):
    config = SyntheticRegimeConfig(
        regime_name="sparse_pairwise_synergy",
        n_items=12,
        budget_tokens=20,
        seed=17,
        pairwise_degree=2,
    )
    first_instance = build_synthetic_instance_from_config(config)
    second_instance = build_synthetic_instance_from_config(config)

    assert first_instance.candidate_pool_hash() == second_instance.candidate_pool_hash()
    assert [item.to_payload() for item in first_instance.items] == [item.to_payload() for item in second_instance.items]

    first_output = workspace_tmp_dir / "first"
    second_output = workspace_tmp_dir / "second"
    first_report = run_synthetic_benchmark(
        config_path="configs/runs/synthetic-regime-smoke.json",
        output_dir=first_output,
        seed=17,
        n_items=12,
        budget_tokens=20,
    )
    second_report = run_synthetic_benchmark(
        config_path="configs/runs/synthetic-regime-smoke.json",
        output_dir=second_output,
        seed=17,
        n_items=12,
        budget_tokens=20,
    )

    assert first_report["status"] == second_report["status"] == "green"
    for filename in (
        "candidate_pools.jsonl",
        "projection_plans.jsonl",
        "budget_witnesses.jsonl",
        "materialized_contexts.jsonl",
        "metric_bridge_witnesses.jsonl",
        "diagnostics.jsonl",
        "projection_bundles.jsonl",
    ):
        assert (first_output / filename).read_text(encoding="utf-8") == (second_output / filename).read_text(
            encoding="utf-8"
        )
    assert _stable_summary_payload(first_output / "summary.json") == _stable_summary_payload(second_output / "summary.json")


def test_different_seeds_produce_controlled_candidate_differences():
    first = build_synthetic_instance_from_config(
        SyntheticRegimeConfig(regime_name="redundancy_dominated", n_items=10, budget_tokens=18, seed=1)
    )
    second = build_synthetic_instance_from_config(
        SyntheticRegimeConfig(regime_name="redundancy_dominated", n_items=10, budget_tokens=18, seed=2)
    )

    assert first.candidate_pool_hash() != second.candidate_pool_hash()
    assert first.regime == second.regime == "redundancy_dominated"
    assert len(first.items) == len(second.items) == 10


def test_item_payload_aliases_preserve_candidate_compatibility():
    instance = build_synthetic_instance_from_config(
        SyntheticRegimeConfig(regime_name="redundancy_dominated", n_items=8, budget_tokens=18, seed=0)
    )
    payload = instance.items[0].to_payload()

    assert payload["candidate_id"] == payload["item_id"]
    assert payload["content"] == payload["text"]
    assert payload["regime"] == "redundancy_dominated"
    assert payload["synthetic_source"] == "synthetic_regime_benchmark"
    assert payload["metadata"]["synthetic_source"] == "synthetic_regime_benchmark"


def test_redundancy_regime_has_high_block_ratio_and_low_synergy():
    instance = build_synthetic_instance_from_config(
        SyntheticRegimeConfig(regime_name="redundancy_dominated", n_items=8, budget_tokens=18, seed=3)
    )
    pair = [instance.items[0].item_id, instance.items[2].item_id]

    assert block_ratio(instance, [], pair) >= 0.9
    assert pairwise_interaction(instance, instance.items[0].item_id, instance.items[2].item_id) == 0.0


def test_pairwise_regime_detects_interaction_mass():
    instance = build_synthetic_instance_from_config(
        SyntheticRegimeConfig(regime_name="sparse_pairwise_synergy", n_items=12, budget_tokens=20, seed=5)
    )

    assert any(
        pairwise_interaction(instance, left, right) > 0.0
        for left, right in instance.pairwise_bonuses
    )


def test_higher_order_regime_detects_triple_excess_and_is_not_greedy_supported(workspace_tmp_dir):
    instance = build_synthetic_instance_from_config(
        SyntheticRegimeConfig(regime_name="higher_order_synergy", n_items=12, budget_tokens=20, seed=7)
    )
    triple = next(iter(instance.triple_bonuses))
    greedy = greedy_select(items=instance.items, budget_tokens=instance.budget_tokens, value_fn=instance.value)

    assert triple_excess(instance, *triple) > 0.0
    assert greedy.algorithm == "greedy"
    report = run_synthetic_benchmark(
        config_path="configs/runs/synthetic-regime-smoke.json",
        output_dir=workspace_tmp_dir / "higher_order_label_check",
        seed=7,
        n_items=12,
        budget_tokens=20,
    )
    diagnostics = _jsonl_rows(Path(report["summary"]["output_dir"]) / "diagnostics.jsonl")
    higher = next(row for row in diagnostics if row["regime"] == "higher_order_synergy")
    assert higher["selector_regime_label"] == "higher_order_risk"


def test_greedy_selection_and_bruteforce_oracle_respect_budget():
    instance = build_synthetic_instance_from_config(
        SyntheticRegimeConfig(regime_name="sparse_pairwise_synergy", n_items=10, budget_tokens=18, seed=11)
    )
    greedy = greedy_select(items=instance.items, budget_tokens=instance.budget_tokens, value_fn=instance.value)
    oracle = brute_force_optimal_select(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
    )

    assert greedy.token_cost <= instance.budget_tokens
    assert oracle.oracle_status == "available"
    assert oracle.token_cost <= instance.budget_tokens
    assert oracle.value >= greedy.value


def test_bruteforce_oracle_skips_large_instances():
    instance = build_synthetic_instance_from_config(
        SyntheticRegimeConfig(regime_name="redundancy_dominated", n_items=21, budget_tokens=30, seed=13)
    )

    result = brute_force_optimal_select(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
        max_items=20,
    )

    assert result.oracle_status == "skipped_large_n"
    assert result.selected_ids == []


def test_projection_bundle_rows_reconstruct_and_hash_stably(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "bundle_rows"
    report = run_synthetic_benchmark(
        config_path="configs/runs/synthetic-regime-smoke.json",
        output_dir=output_dir,
    )

    rows = _jsonl_rows(output_dir / "projection_bundles.jsonl")
    assert len(rows) == report["summary"]["dispatch_count"]
    for row in rows:
        bundle = ProjectionBundleV1.from_dict(row)
        assert row["canonical_hash"] == bundle.canonical_hash()
        assert ProjectionBundleV1.from_dict(bundle.to_dict()).canonical_hash() == bundle.canonical_hash()


def test_forbidden_metric_claim_levels_never_appear(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "claim_levels"
    run_synthetic_benchmark(
        config_path="configs/runs/synthetic-regime-smoke.json",
        output_dir=output_dir,
    )
    forbidden = {
        "Vinfo_proxy_certified",
        "greedy_valid",
        '"escalate"',
        "structural_synthetic_only",
        "measurement_validated",
    }
    combined = "\n".join(path.read_text(encoding="utf-8") for path in output_dir.glob("*.json*"))

    assert not any(claim in combined for claim in forbidden)
    summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    diagnostics = _jsonl_rows(output_dir / "diagnostics.jsonl")
    witnesses = _jsonl_rows(output_dir / "metric_bridge_witnesses.jsonl")

    assert summary["metric_claim_level_counts"] == {"ambiguous_metric": 3}
    assert summary["diagnostic_scope_counts"] == {"synthetic_structural_only": 3}
    assert {row["metric_claim_level"] for row in diagnostics} == {"ambiguous_metric"}
    assert {row["diagnostic_scope"] for row in diagnostics} == {"synthetic_structural_only"}
    assert {row["diagnostic_claim_level"] for row in witnesses} == {"ambiguous_metric"}
    assert {row["diagnostic_scope"] for row in witnesses} == {"synthetic_structural_only"}


def test_benchmark_does_not_read_reference_or_import_live_api(monkeypatch, workspace_tmp_dir):
    real_open = Path.open
    real_import = builtins.__import__

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.split(".", 1)[0] == "api":
            raise AssertionError("synthetic benchmark must not import live API module")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    run_synthetic_benchmark(
        config_path="configs/runs/synthetic-regime-smoke.json",
        output_dir=workspace_tmp_dir / "offline_only",
    )


def test_value_helpers_are_pure_and_context_sensitive():
    instance = build_synthetic_instance_from_config(
        SyntheticRegimeConfig(regime_name="sparse_pairwise_synergy", n_items=8, budget_tokens=18, seed=19)
    )
    item_id = instance.items[0].item_id

    assert value_of_set(instance, [item_id]) == instance.value([item_id])
    assert singleton_marginal(instance, item_id, []) == value_of_set(instance, [item_id])
