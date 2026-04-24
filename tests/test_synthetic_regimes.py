from cps.experiments.diagnostics import compute_diagnostics
from cps.experiments.selection import greedy_select, seeded_augmented_greedy
from cps.experiments.synthetic_regimes import build_synthetic_instances


def test_synthetic_regime_generation_is_deterministic_and_monotone():
    first = build_synthetic_instances(
        regimes=["redundancy_dominated", "sparse_pairwise_synergy", "higher_order_synergy"],
        instances_per_regime=1,
        seed=20260418,
    )
    second = build_synthetic_instances(
        regimes=["redundancy_dominated", "sparse_pairwise_synergy", "higher_order_synergy"],
        instances_per_regime=1,
        seed=20260418,
    )

    assert [instance.candidate_pool_hash() for instance in first] == [
        instance.candidate_pool_hash() for instance in second
    ]

    for instance in first:
        selected = [item.item_id for item in instance.items[:2]]
        expanded = [item.item_id for item in instance.items[:3]]
        assert instance.value(expanded) >= instance.value(selected)


def test_synthetic_regime_diagnostics_choose_expected_policy():
    instances = build_synthetic_instances(
        regimes=["redundancy_dominated", "sparse_pairwise_synergy", "higher_order_synergy"],
        instances_per_regime=1,
        seed=20260418,
    )

    policies = {}
    for instance in instances:
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
        policies[instance.regime] = diagnostics.policy_recommendation

    assert policies == {
        "redundancy_dominated": "monitored_greedy",
        "sparse_pairwise_synergy": "seeded_augmented_greedy",
        "higher_order_synergy": "interaction_aware_local_search",
    }
