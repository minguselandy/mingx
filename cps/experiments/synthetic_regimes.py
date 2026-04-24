from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Iterable

from cps.experiments.artifacts import candidate_pool_hash


@dataclass(frozen=True)
class SyntheticItem:
    item_id: str
    token_cost: int
    singleton_value: float
    text: str
    cluster_id: str | None = None
    metadata: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "token_cost": self.token_cost,
            "singleton_value": self.singleton_value,
            "text": self.text,
            "cluster_id": self.cluster_id,
            "metadata": dict(self.metadata or {}),
        }


@dataclass(frozen=True)
class SyntheticInstance:
    instance_id: str
    regime: str
    agent_id: str
    round_id: str
    budget_tokens: int
    items: tuple[SyntheticItem, ...]
    pairwise_bonuses: dict[tuple[str, str], float]
    triple_bonuses: dict[tuple[str, str, str], float]
    redundancy_residual_ratio: float | None
    seed: int
    expected_policy: str
    description: str

    def item_payloads(self) -> list[dict[str, Any]]:
        return [item.to_payload() for item in self.items]

    def candidate_pool_hash(self) -> str:
        return candidate_pool_hash(self.item_payloads())

    def item_lookup(self) -> dict[str, SyntheticItem]:
        return {item.item_id: item for item in self.items}

    def value(self, selected_ids: Iterable[str]) -> float:
        selected = set(selected_ids)
        lookup = self.item_lookup()
        if not selected:
            return 0.0

        value = 0.0
        if self.redundancy_residual_ratio is None:
            value += sum(lookup[item_id].singleton_value for item_id in selected)
        else:
            clustered: dict[str | None, list[float]] = {}
            for item_id in selected:
                item = lookup[item_id]
                clustered.setdefault(item.cluster_id, []).append(item.singleton_value)
            for cluster_id, values in clustered.items():
                if cluster_id is None:
                    value += sum(values)
                    continue
                ordered = sorted(values, reverse=True)
                value += ordered[0] + (self.redundancy_residual_ratio * sum(ordered[1:]))

        for pair, bonus in self.pairwise_bonuses.items():
            if set(pair).issubset(selected):
                value += bonus
        for triple, bonus in self.triple_bonuses.items():
            if set(triple).issubset(selected):
                value += bonus
        return round(value, 6)


def _pair(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def _triple(first: str, second: str, third: str) -> tuple[str, str, str]:
    return tuple(sorted((first, second, third)))


def _scale(value: float, instance_index: int) -> float:
    return round(value * (1.0 + (0.015 * instance_index)), 6)


def build_redundancy_dominated_instance(*, seed: int, instance_index: int) -> SyntheticInstance:
    prefix = f"redundancy_{instance_index}"
    raw_items = [
        ("a0", 6, 10.0, "cluster_a"),
        ("a1", 6, 9.4, "cluster_a"),
        ("b0", 6, 9.0, "cluster_b"),
        ("b1", 6, 8.5, "cluster_b"),
        ("c0", 6, 8.1, "cluster_c"),
        ("c1", 6, 7.7, "cluster_c"),
        ("d0", 6, 5.0, "cluster_d"),
        ("d1", 6, 4.8, "cluster_d"),
    ]
    items = tuple(
        SyntheticItem(
            item_id=f"{prefix}_{name}",
            token_cost=cost,
            singleton_value=_scale(value, instance_index),
            text=f"Redundant finding {name} in {cluster}.",
            cluster_id=cluster,
            metadata={"regime_role": "near_duplicate"},
        )
        for name, cost, value, cluster in raw_items
    )
    return SyntheticInstance(
        instance_id=prefix,
        regime="redundancy_dominated",
        agent_id="synthetic_agent",
        round_id=f"round_{instance_index}",
        budget_tokens=18,
        items=items,
        pairwise_bonuses={},
        triple_bonuses={},
        redundancy_residual_ratio=0.08,
        seed=seed,
        expected_policy="monitored_greedy",
        description="Clusters of near-duplicate findings with strong diminishing returns.",
    )


def build_sparse_pairwise_synergy_instance(*, seed: int, instance_index: int) -> SyntheticInstance:
    prefix = f"pairwise_{instance_index}"
    raw_values = {
        "p0": 6.0,
        "p1": 5.8,
        "p2": 5.6,
        "p3": 5.4,
        "p4": 5.2,
        "p5": 5.0,
        "d0": 5.9,
        "d1": 5.7,
    }
    items = tuple(
        SyntheticItem(
            item_id=f"{prefix}_{name}",
            token_cost=6,
            singleton_value=_scale(value, instance_index),
            text=f"Pairwise-regime finding {name}.",
            metadata={"regime_role": "synergy_candidate" if name.startswith("p") else "decoy"},
        )
        for name, value in raw_values.items()
    )
    pairwise_names = [("p0", "p1"), ("p2", "p3"), ("p0", "p2"), ("p4", "p5")]
    pairwise_bonuses = {
        _pair(f"{prefix}_{left}", f"{prefix}_{right}"): _scale(3.6, instance_index)
        for left, right in pairwise_names
    }
    return SyntheticInstance(
        instance_id=prefix,
        regime="sparse_pairwise_synergy",
        agent_id="synthetic_agent",
        round_id=f"round_{instance_index}",
        budget_tokens=18,
        items=items,
        pairwise_bonuses=pairwise_bonuses,
        triple_bonuses={},
        redundancy_residual_ratio=None,
        seed=seed,
        expected_policy="seeded_augmented_greedy",
        description="Sparse bounded pairwise complementarities among otherwise useful findings.",
    )


def build_higher_order_synergy_instance(*, seed: int, instance_index: int) -> SyntheticInstance:
    prefix = f"higher_order_{instance_index}"
    raw_values = {
        "t0": 2.2,
        "t1": 2.1,
        "t2": 2.0,
        "u0": 2.1,
        "u1": 2.0,
        "u2": 1.9,
        "d0": 6.0,
        "d1": 5.8,
        "d2": 5.6,
        "d3": 5.4,
    }
    items = tuple(
        SyntheticItem(
            item_id=f"{prefix}_{name}",
            token_cost=6,
            singleton_value=_scale(value, instance_index),
            text=f"Higher-order-regime finding {name}.",
            metadata={"regime_role": "triple_prerequisite" if name[0] in {"t", "u"} else "decoy"},
        )
        for name, value in raw_values.items()
    )
    pairwise_bonuses = {}
    for left, right in combinations(("t0", "t1", "t2"), 2):
        pairwise_bonuses[_pair(f"{prefix}_{left}", f"{prefix}_{right}")] = _scale(2.0, instance_index)
    for left, right in combinations(("u0", "u1", "u2"), 2):
        pairwise_bonuses[_pair(f"{prefix}_{left}", f"{prefix}_{right}")] = _scale(1.6, instance_index)
    triple_bonuses = {
        _triple(f"{prefix}_t0", f"{prefix}_t1", f"{prefix}_t2"): _scale(22.0, instance_index),
        _triple(f"{prefix}_u0", f"{prefix}_u1", f"{prefix}_u2"): _scale(18.0, instance_index),
    }
    return SyntheticInstance(
        instance_id=prefix,
        regime="higher_order_synergy",
        agent_id="synthetic_agent",
        round_id=f"round_{instance_index}",
        budget_tokens=18,
        items=items,
        pairwise_bonuses=pairwise_bonuses,
        triple_bonuses=triple_bonuses,
        redundancy_residual_ratio=None,
        seed=seed,
        expected_policy="interaction_aware_local_search",
        description="Prerequisite triples whose joint value is not visible from singleton scores.",
    )


REGIME_BUILDERS = {
    "redundancy_dominated": build_redundancy_dominated_instance,
    "sparse_pairwise_synergy": build_sparse_pairwise_synergy_instance,
    "higher_order_synergy": build_higher_order_synergy_instance,
}


def build_synthetic_instances(
    *,
    regimes: Iterable[str],
    instances_per_regime: int,
    seed: int,
) -> list[SyntheticInstance]:
    instances: list[SyntheticInstance] = []
    for regime in regimes:
        try:
            builder = REGIME_BUILDERS[str(regime)]
        except KeyError as exc:
            available = ", ".join(sorted(REGIME_BUILDERS))
            raise ValueError(f"unknown synthetic regime {regime!r}; available: {available}") from exc
        for index in range(instances_per_regime):
            instances.append(builder(seed=seed, instance_index=index))
    return instances
