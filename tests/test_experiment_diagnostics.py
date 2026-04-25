from cps.experiments.decision import (
    derive_metric_claim_level,
    derive_selector_action,
    derive_selector_regime_label,
)
from cps.experiments.diagnostics import (
    compute_block_ratio_lcb,
    compute_block_ratio_samples,
    compute_diagnostics,
    compute_pair_block_ratio_lcb,
    sample_triple_excesses,
    compute_trace_decay_proxy,
    estimate_gamma_hat,
)
from cps.experiments.selection import greedy_select, seeded_augmented_greedy
from cps.experiments.synthetic_regimes import SyntheticItem, build_synthetic_instances


def _items(*item_ids: str) -> tuple[SyntheticItem, ...]:
    return tuple(
        SyntheticItem(item_id=item_id, token_cost=1, singleton_value=1.0, text=item_id) for item_id in item_ids
    )


def test_block_ratio_samples_preserve_raw_ratios_and_clamp_for_lcb():
    items = _items("a", "b")

    def value_fn(selected_ids):
        selected = set(selected_ids)
        value = float(len(selected))
        if {"a", "b"}.issubset(selected):
            value += 2.0
        return value

    samples = compute_block_ratio_samples(
        items=items,
        value_fn=value_fn,
        contexts=[[]],
        block_size=2,
    )
    pair_ab = next(row for row in samples if row["block_ids"] == ["a", "b"])

    assert pair_ab["a_sum_marginals"] == 2.0
    assert pair_ab["b_joint_gain"] == 4.0
    assert pair_ab["raw_ratio"] == 0.5
    assert pair_ab["clamped_ratio"] == 0.5
    assert pair_ab["denominator_uninformative"] is False
    assert compute_pair_block_ratio_lcb(items=items, value_fn=value_fn, contexts=[[]]) == 0.5


def test_denominator_uninformative_samples_are_counted_but_excluded_from_lcb():
    items = _items("a", "b")

    def value_fn(_selected_ids):
        return 0.0

    samples = compute_block_ratio_samples(
        items=items,
        value_fn=value_fn,
        contexts=[[]],
        block_size=2,
    )

    assert len(samples) == 1
    assert samples[0]["denominator_uninformative"] is True
    assert samples[0]["raw_ratio"] is None
    assert samples[0]["clamped_ratio"] is None
    assert compute_block_ratio_lcb(samples) is None


def test_trace_decay_proxy_replaces_legacy_gamma_estimator():
    trace = [
        {"singleton_gain": 10.0, "marginal_gain": 10.0, "source": "greedy_completion"},
        {"singleton_gain": 8.0, "marginal_gain": 4.0, "source": "greedy_completion"},
        {"singleton_gain": 5.0, "marginal_gain": 1.0, "source": "greedy_completion"},
    ]

    assert compute_trace_decay_proxy(trace) == estimate_gamma_hat(trace)
    assert "legacy" in estimate_gamma_hat.__doc__.lower()
    assert "not a submodularity-ratio estimator" in estimate_gamma_hat.__doc__.lower()


def _diagnostic_row(**overrides):
    row = {
        "block_ratio_lcb_star": 1.0,
        "block_ratio_lcb_b2": 1.0,
        "block_ratio_lcb_b3": 1.0,
        "block_ratio_sample_count": 4,
        "block_ratio_uninformative_count": 0,
        "synergy_fraction": 0.0,
        "positive_interaction_mass_ucb": 0.0,
        "greedy_augmented_gap": 0.0,
        "triple_excess_flag": "none_detected",
        "higher_order_ambiguity_flag": False,
    }
    row.update(overrides)
    return row


def test_metric_claim_level_comes_from_metric_bridge_witness():
    assert derive_metric_claim_level({"metric_class": "synthetic_oracle", "drift_status": "not_applicable"}) == (
        "structural_synthetic_only"
    )
    assert derive_metric_claim_level({"metric_class": "operational_only", "drift_status": "fresh"}) == (
        "operational_utility_only"
    )
    assert derive_metric_claim_level({"metric_class": "log_loss_aligned", "drift_status": "fresh"}) == (
        "Vinfo_proxy_certified"
    )
    assert derive_metric_claim_level(None) == "ambiguous"
    assert derive_metric_claim_level({"metric_class": "log_loss_aligned", "drift_status": "stale"}) == "ambiguous"
    assert derive_metric_claim_level({"metric_class": "unknown", "drift_status": "fresh"}) == "ambiguous"


def test_selector_regime_label_uses_two_axis_protocol():
    good = _diagnostic_row()
    assert derive_selector_regime_label(good, "structural_synthetic_only", {}) == "greedy_valid"
    assert derive_selector_action("greedy_valid", good, {}) == "monitored_greedy"

    high_synergy = _diagnostic_row(synergy_fraction=0.5, positive_interaction_mass_ucb=0.7)
    assert derive_selector_regime_label(high_synergy, "structural_synthetic_only", {}) == "escalate"
    assert derive_selector_action("escalate", high_synergy, {}) == "seeded_augmented_greedy"

    positive_triple = _diagnostic_row(triple_excess_flag="positive", higher_order_ambiguity_flag=True)
    assert derive_selector_regime_label(positive_triple, "structural_synthetic_only", {}) == "escalate"
    assert derive_selector_action("escalate", positive_triple, {}) == "interaction_aware_local_search"


def test_selector_regime_label_downgrades_ambiguous_inputs():
    insufficient_samples = _diagnostic_row(block_ratio_sample_count=0, block_ratio_lcb_star=None)
    assert derive_selector_regime_label(insufficient_samples, "structural_synthetic_only", {}) == "ambiguous"
    assert derive_selector_action("ambiguous", insufficient_samples, {}) == "no_certified_switch"

    low_denominator_signal = _diagnostic_row(block_ratio_sample_count=3, block_ratio_uninformative_count=3)
    assert derive_selector_regime_label(low_denominator_signal, "structural_synthetic_only", {}) == "ambiguous"

    missing_bridge = _diagnostic_row()
    assert derive_selector_regime_label(missing_bridge, "ambiguous", {}) == "ambiguous"

    missing_higher_order_test = _diagnostic_row(
        triple_excess_flag="not_evaluable",
        higher_order_ambiguity_flag=True,
    )
    assert derive_selector_regime_label(missing_higher_order_test, "structural_synthetic_only", {}) == "ambiguous"


def test_compute_diagnostics_headlines_block_ratio_fields():
    instance = build_synthetic_instances(
        regimes=["sparse_pairwise_synergy"],
        instances_per_regime=1,
        seed=20260418,
    )[0]
    greedy = greedy_select(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
    )
    augmented = seeded_augmented_greedy(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
    )

    diagnostics = compute_diagnostics(
        items=instance.items,
        value_fn=instance.value,
        greedy_result=greedy,
        augmented_result=augmented,
        top_l=8,
    )

    assert diagnostics.block_ratio_lcb_b2 is not None
    assert diagnostics.block_ratio_lcb_star is not None
    assert diagnostics.block_ratio_sample_count > 0
    assert diagnostics.trace_decay_proxy == diagnostics.gamma_hat
    assert diagnostics.selector_action == "seeded_augmented_greedy"
    assert diagnostics.policy_recommendation == diagnostics.selector_action
    assert diagnostics.metric_claim_level == "structural_synthetic_only"
    assert diagnostics.selector_regime_label == "escalate"


def test_compute_diagnostics_downgrades_missing_metric_bridge():
    instance = build_synthetic_instances(
        regimes=["redundancy_dominated"],
        instances_per_regime=1,
        seed=20260418,
    )[0]
    greedy = greedy_select(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
    )
    augmented = seeded_augmented_greedy(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
    )

    diagnostics = compute_diagnostics(
        items=instance.items,
        value_fn=instance.value,
        greedy_result=greedy,
        augmented_result=augmented,
        top_l=8,
        metric_bridge_witness=None,
    )

    assert diagnostics.metric_claim_level == "ambiguous"
    assert diagnostics.selector_regime_label == "ambiguous"
    assert diagnostics.selector_action == "no_certified_switch"
    assert diagnostics.policy_recommendation == diagnostics.selector_action


def test_pure_pairwise_instance_has_no_positive_triple_excess():
    instance = build_synthetic_instances(
        regimes=["sparse_pairwise_synergy"],
        instances_per_regime=1,
        seed=20260418,
    )[0]

    triple_samples = sample_triple_excesses(
        items=instance.items,
        value_fn=instance.value,
        contexts=[[]],
        top_l=8,
    )

    assert triple_samples
    assert max(row["omega_ijk"] for row in triple_samples) <= 0.0


def test_higher_order_synthetic_instance_produces_positive_triple_excess():
    instance = build_synthetic_instances(
        regimes=["higher_order_synergy"],
        instances_per_regime=1,
        seed=20260418,
    )[0]
    greedy = greedy_select(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
    )
    augmented = seeded_augmented_greedy(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
    )

    diagnostics = compute_diagnostics(
        items=instance.items,
        value_fn=instance.value,
        greedy_result=greedy,
        augmented_result=augmented,
        top_l=8,
    )

    assert diagnostics.triple_excess_flag == "positive"
    assert diagnostics.triple_excess_lcb_max is not None
    assert diagnostics.triple_excess_lcb_max > 0.0
    assert diagnostics.higher_order_ambiguity_flag is True
    assert diagnostics.selector_regime_label == "escalate"
    assert diagnostics.selector_action == "interaction_aware_local_search"


def test_higher_order_risk_without_triple_evidence_is_not_greedy_valid():
    instance = build_synthetic_instances(
        regimes=["higher_order_synergy"],
        instances_per_regime=1,
        seed=20260418,
    )[0]
    greedy = greedy_select(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
    )
    augmented = seeded_augmented_greedy(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
    )

    diagnostics = compute_diagnostics(
        items=instance.items,
        value_fn=instance.value,
        greedy_result=greedy,
        augmented_result=augmented,
        top_l=2,
    )

    assert diagnostics.triple_excess_flag == "not_evaluable"
    assert diagnostics.higher_order_ambiguity_flag is True
    assert diagnostics.selector_action != "monitored_greedy"
    assert diagnostics.selector_regime_label == "ambiguous"


def test_triple_excess_not_evaluable_without_risk_does_not_crash():
    items = _items("a", "b")

    def value_fn(selected_ids):
        return float(len(set(selected_ids)))

    triple_samples = sample_triple_excesses(
        items=items,
        value_fn=value_fn,
        contexts=[[]],
        top_l=2,
    )

    assert triple_samples == []
