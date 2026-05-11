from __future__ import annotations

import hashlib
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
    regime: str | None = None
    synthetic_source: str = "synthetic_regime_benchmark"
    provenance: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        metadata = dict(self.metadata or {})
        metadata.setdefault("synthetic_source", self.synthetic_source)
        if self.regime is not None:
            metadata.setdefault("regime", self.regime)
        provenance = dict(self.provenance or {})
        provenance.setdefault("source", self.synthetic_source)
        return {
            "item_id": self.item_id,
            "candidate_id": self.item_id,
            "token_cost": self.token_cost,
            "singleton_value": self.singleton_value,
            "text": self.text,
            "content": self.text,
            "cluster_id": self.cluster_id,
            "regime": self.regime,
            "synthetic_source": self.synthetic_source,
            "provenance": provenance,
            "metadata": metadata,
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


@dataclass(frozen=True)
class SyntheticRegimeConfig:
    regime_name: str
    n_items: int
    budget_tokens: int
    seed: int
    token_cost_range: tuple[int, int] | None = None
    cluster_count: int | None = None
    pairwise_degree: int | None = None
    triple_count: int | None = None
    noise_level: float = 0.0

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> SyntheticRegimeConfig:
        token_cost_range = payload.get("token_cost_range")
        return cls(
            regime_name=str(payload["regime_name"]),
            n_items=int(payload.get("n_items", 8)),
            budget_tokens=int(payload.get("budget_tokens", 18)),
            seed=int(payload.get("seed", 0)),
            token_cost_range=None if token_cost_range is None else tuple(int(value) for value in token_cost_range),
            cluster_count=None if payload.get("cluster_count") is None else int(payload["cluster_count"]),
            pairwise_degree=None if payload.get("pairwise_degree") is None else int(payload["pairwise_degree"]),
            triple_count=None if payload.get("triple_count") is None else int(payload["triple_count"]),
            noise_level=float(payload.get("noise_level", 0.0)),
        )


def _pair(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def _triple(first: str, second: str, third: str) -> tuple[str, str, str]:
    return tuple(sorted((first, second, third)))


def _scale(value: float, instance_index: int) -> float:
    return round(value * (1.0 + (0.015 * instance_index)), 6)


def _stable_unit_interval(*parts: Any) -> float:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    return int(digest[:12], 16) / float(0xFFFFFFFFFFFF)


def _seed_scale(value: float, *, seed: int, instance_index: int, item_name: str, noise_level: float) -> float:
    if noise_level <= 0:
        return _scale(value, instance_index)
    centered = (_stable_unit_interval(seed, instance_index, item_name) - 0.5) * 2.0
    return round(_scale(value, instance_index) * (1.0 + (centered * noise_level)), 6)


def _token_cost(base_cost: int, *, seed: int, item_name: str, token_cost_range: tuple[int, int] | None) -> int:
    if token_cost_range is None:
        return base_cost
    lower, upper = token_cost_range
    if lower <= 0 or upper < lower:
        raise ValueError("token_cost_range must be positive and ordered")
    span = upper - lower + 1
    return lower + int(_stable_unit_interval(seed, item_name, "cost") * span) % span


def _with_item_count(raw_rows: list[tuple[str, int, float, str | None]], *, n_items: int, prefix: str) -> list[tuple[str, int, float, str | None]]:
    if n_items <= 0:
        raise ValueError("n_items must be positive")
    rows = list(raw_rows[:n_items])
    next_index = 0
    while len(rows) < n_items:
        cluster = f"extra_{next_index % max(1, min(4, n_items))}"
        rows.append((f"x{next_index}", 6, max(0.5, 3.5 - (0.1 * next_index)), cluster if prefix == "redundancy" else None))
        next_index += 1
    return rows


def build_redundancy_dominated_instance(
    *,
    seed: int,
    instance_index: int,
    n_items: int = 8,
    budget_tokens: int = 18,
    token_cost_range: tuple[int, int] | None = None,
    cluster_count: int | None = None,
    noise_level: float = 0.0,
) -> SyntheticInstance:
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
    if cluster_count is not None and cluster_count > 0:
        raw_items = [
            (name, cost, value, f"cluster_{index % cluster_count}") for index, (name, cost, value, _cluster) in enumerate(raw_items)
        ]
    rows = _with_item_count(raw_items, n_items=n_items, prefix="redundancy")
    items = tuple(
        SyntheticItem(
            item_id=f"{prefix}_{name}",
            token_cost=_token_cost(cost, seed=seed, item_name=name, token_cost_range=token_cost_range),
            singleton_value=_seed_scale(value, seed=seed, instance_index=instance_index, item_name=name, noise_level=noise_level),
            text=f"Redundant finding {name} in {cluster}; synthetic seed {seed}.",
            cluster_id=cluster,
            metadata={"regime_role": "near_duplicate", "seed": seed},
            regime="redundancy_dominated",
            provenance={"regime_family": "redundancy-dominated", "seed": seed},
        )
        for name, cost, value, cluster in rows
    )
    return SyntheticInstance(
        instance_id=prefix,
        regime="redundancy_dominated",
        agent_id="synthetic_agent",
        round_id=f"round_{instance_index}",
        budget_tokens=budget_tokens,
        items=items,
        pairwise_bonuses={},
        triple_bonuses={},
        redundancy_residual_ratio=0.08,
        seed=seed,
        expected_policy="monitored_greedy",
        description="Clusters of near-duplicate findings with strong diminishing returns.",
    )


def build_sparse_pairwise_synergy_instance(
    *,
    seed: int,
    instance_index: int,
    n_items: int = 8,
    budget_tokens: int = 18,
    token_cost_range: tuple[int, int] | None = None,
    pairwise_degree: int | None = None,
    noise_level: float = 0.0,
) -> SyntheticInstance:
    prefix = f"pairwise_{instance_index}"
    raw_values = [
        ("p0", 6.0),
        ("p1", 5.8),
        ("p2", 5.6),
        ("p3", 5.4),
        ("p4", 5.2),
        ("p5", 5.0),
        ("d0", 5.9),
        ("d1", 5.7),
    ]
    while len(raw_values) < n_items:
        index = len(raw_values) - 8
        raw_values.append((f"d{index + 2}", max(1.0, 4.4 - (0.1 * index))))
    raw_values = raw_values[:n_items]
    items = tuple(
        SyntheticItem(
            item_id=f"{prefix}_{name}",
            token_cost=_token_cost(6, seed=seed, item_name=name, token_cost_range=token_cost_range),
            singleton_value=_seed_scale(value, seed=seed, instance_index=instance_index, item_name=name, noise_level=noise_level),
            text=f"Pairwise-regime finding {name}; synthetic seed {seed}.",
            metadata={"regime_role": "synergy_candidate" if name.startswith("p") else "decoy", "seed": seed},
            regime="sparse_pairwise_synergy",
            provenance={"regime_family": "pairwise-synergy", "seed": seed},
        )
        for name, value in raw_values
    )
    pairwise_names = [("p0", "p1"), ("p2", "p3"), ("p0", "p2"), ("p4", "p5")]
    if pairwise_degree is not None and pairwise_degree > 0:
        pairwise_names = pairwise_names[: max(1, min(len(pairwise_names), pairwise_degree * 2))]
    available_names = {name for name, _value in raw_values}
    pairwise_bonuses = {
        _pair(f"{prefix}_{left}", f"{prefix}_{right}"): _seed_scale(
            3.6,
            seed=seed,
            instance_index=instance_index,
            item_name=f"{left}:{right}",
            noise_level=noise_level,
        )
        for left, right in pairwise_names
        if left in available_names and right in available_names
    }
    return SyntheticInstance(
        instance_id=prefix,
        regime="sparse_pairwise_synergy",
        agent_id="synthetic_agent",
        round_id=f"round_{instance_index}",
        budget_tokens=budget_tokens,
        items=items,
        pairwise_bonuses=pairwise_bonuses,
        triple_bonuses={},
        redundancy_residual_ratio=None,
        seed=seed,
        expected_policy="seeded_augmented_greedy",
        description="Sparse bounded pairwise complementarities among otherwise useful findings.",
    )


def build_higher_order_synergy_instance(
    *,
    seed: int,
    instance_index: int,
    n_items: int = 10,
    budget_tokens: int = 18,
    token_cost_range: tuple[int, int] | None = None,
    triple_count: int | None = None,
    noise_level: float = 0.0,
) -> SyntheticInstance:
    prefix = f"higher_order_{instance_index}"
    raw_values = [
        ("t0", 2.2),
        ("t1", 2.1),
        ("t2", 2.0),
        ("u0", 2.1),
        ("u1", 2.0),
        ("u2", 1.9),
        ("d0", 6.0),
        ("d1", 5.8),
        ("d2", 5.6),
        ("d3", 5.4),
    ]
    while len(raw_values) < n_items:
        index = len(raw_values) - 10
        raw_values.append((f"d{index + 4}", max(0.6, 1.0 - (0.05 * index))))
    raw_values = raw_values[:n_items]
    items = tuple(
        SyntheticItem(
            item_id=f"{prefix}_{name}",
            token_cost=_token_cost(6, seed=seed, item_name=name, token_cost_range=token_cost_range),
            singleton_value=_seed_scale(value, seed=seed, instance_index=instance_index, item_name=name, noise_level=noise_level),
            text=f"Higher-order-regime finding {name}; synthetic seed {seed}.",
            metadata={"regime_role": "triple_prerequisite" if name[0] in {"t", "u"} else "decoy", "seed": seed},
            regime="higher_order_synergy",
            provenance={"regime_family": "higher-order-synergy", "seed": seed},
        )
        for name, value in raw_values
    )
    available_names = {name for name, _value in raw_values}
    pairwise_bonuses = {}
    for left, right in combinations(("t0", "t1", "t2"), 2):
        if left in available_names and right in available_names:
            pairwise_bonuses[_pair(f"{prefix}_{left}", f"{prefix}_{right}")] = _seed_scale(
                2.0,
                seed=seed,
                instance_index=instance_index,
                item_name=f"{left}:{right}",
                noise_level=noise_level,
            )
    for left, right in combinations(("u0", "u1", "u2"), 2):
        if left in available_names and right in available_names:
            pairwise_bonuses[_pair(f"{prefix}_{left}", f"{prefix}_{right}")] = _seed_scale(
                1.6,
                seed=seed,
                instance_index=instance_index,
                item_name=f"{left}:{right}",
                noise_level=noise_level,
            )
    candidate_triples = [
        ("t0", "t1", "t2", 22.0),
        ("u0", "u1", "u2", 18.0),
    ]
    if triple_count is not None:
        candidate_triples = candidate_triples[: max(0, min(len(candidate_triples), triple_count))]
    triple_bonuses = {
        _triple(f"{prefix}_{left}", f"{prefix}_{middle}", f"{prefix}_{right}"): _seed_scale(
            value,
            seed=seed,
            instance_index=instance_index,
            item_name=f"{left}:{middle}:{right}",
            noise_level=noise_level,
        )
        for left, middle, right, value in candidate_triples
        if left in available_names and middle in available_names and right in available_names
    }
    return SyntheticInstance(
        instance_id=prefix,
        regime="higher_order_synergy",
        agent_id="synthetic_agent",
        round_id=f"round_{instance_index}",
        budget_tokens=budget_tokens,
        items=items,
        pairwise_bonuses=pairwise_bonuses,
        triple_bonuses=triple_bonuses,
        redundancy_residual_ratio=None,
        seed=seed,
        expected_policy="interaction_aware_local_search",
        description="Prerequisite triples whose joint value is not visible from singleton scores.",
    )


def build_adversarial_redundancy_instance(
    *,
    seed: int,
    instance_index: int,
    n_items: int = 10,
    budget_tokens: int = 18,
    token_cost_range: tuple[int, int] | None = None,
    cluster_count: int | None = None,
    noise_level: float = 0.0,
) -> SyntheticInstance:
    prefix = f"adversarial_{instance_index}"
    raw_items = [
        ("a0", 6, 9.7, "claim_a", "primary_claim"),
        ("a1", 6, 9.1, "claim_a", "near_duplicate"),
        ("b0", 6, 8.8, "claim_b", "contradictory_claim"),
        ("b1", 6, 8.2, "claim_b", "near_duplicate"),
        ("c0", 6, 7.7, "claim_c", "ambiguous_corroboration"),
        ("c1", 6, 7.3, "claim_c", "near_duplicate"),
        ("d0", 6, 6.8, "claim_d", "decoy"),
        ("d1", 6, 6.4, "claim_d", "near_duplicate"),
        ("e0", 6, 5.9, "claim_e", "decoy"),
        ("e1", 6, 5.5, "claim_e", "near_duplicate"),
    ]
    if cluster_count is not None and cluster_count > 0:
        raw_items = [
            (name, cost, value, f"claim_{index % cluster_count}", role)
            for index, (name, cost, value, _cluster, role) in enumerate(raw_items)
        ]
    rows = raw_items[:n_items]
    next_index = 0
    while len(rows) < n_items:
        cluster = f"claim_extra_{next_index % max(1, min(4, n_items))}"
        rows.append((f"x{next_index}", 6, max(3.0, 5.0 - (0.1 * next_index)), cluster, "decoy"))
        next_index += 1

    items = tuple(
        SyntheticItem(
            item_id=f"{prefix}_{name}",
            token_cost=_token_cost(cost, seed=seed, item_name=name, token_cost_range=token_cost_range),
            singleton_value=_seed_scale(value, seed=seed, instance_index=instance_index, item_name=name, noise_level=noise_level),
            text=f"Adversarial redundant finding {name} in {cluster}; role={role}; synthetic seed {seed}.",
            cluster_id=cluster,
            metadata={
                "regime_role": role,
                "higher_order_risk": True,
                "seed": seed,
            },
            regime="adversarial_redundancy",
            provenance={"regime_family": "adversarial-redundancy", "seed": seed},
        )
        for name, cost, value, cluster, role in rows
    )
    return SyntheticInstance(
        instance_id=prefix,
        regime="adversarial_redundancy",
        agent_id="synthetic_agent",
        round_id=f"round_{instance_index}",
        budget_tokens=budget_tokens,
        items=items,
        pairwise_bonuses={},
        triple_bonuses={},
        redundancy_residual_ratio=0.05,
        seed=seed,
        expected_policy="no_certified_switch",
        description="Redundant-looking findings with explicit adversarial ambiguity risk; should not certify greedy support.",
    )


REGIME_BUILDERS = {
    "redundancy_dominated": build_redundancy_dominated_instance,
    "sparse_pairwise_synergy": build_sparse_pairwise_synergy_instance,
    "higher_order_synergy": build_higher_order_synergy_instance,
    "adversarial_redundancy": build_adversarial_redundancy_instance,
}


def build_synthetic_instances(
    *,
    regimes: Iterable[str],
    instances_per_regime: int,
    seed: int,
    n_items: int | None = None,
    budget_tokens: int | None = None,
    token_cost_range: tuple[int, int] | None = None,
    cluster_count: int | None = None,
    pairwise_degree: int | None = None,
    triple_count: int | None = None,
    noise_level: float = 0.0,
) -> list[SyntheticInstance]:
    instances: list[SyntheticInstance] = []
    for regime in regimes:
        try:
            builder = REGIME_BUILDERS[str(regime)]
        except KeyError as exc:
            available = ", ".join(sorted(REGIME_BUILDERS))
            raise ValueError(f"unknown synthetic regime {regime!r}; available: {available}") from exc
        for index in range(instances_per_regime):
            kwargs: dict[str, Any] = {
                "seed": seed,
                "instance_index": index,
                "noise_level": noise_level,
            }
            if n_items is not None:
                kwargs["n_items"] = n_items
            if budget_tokens is not None:
                kwargs["budget_tokens"] = budget_tokens
            if token_cost_range is not None:
                kwargs["token_cost_range"] = token_cost_range
            if regime == "redundancy_dominated" and cluster_count is not None:
                kwargs["cluster_count"] = cluster_count
            if regime == "sparse_pairwise_synergy" and pairwise_degree is not None:
                kwargs["pairwise_degree"] = pairwise_degree
            if regime == "higher_order_synergy" and triple_count is not None:
                kwargs["triple_count"] = triple_count
            instances.append(builder(**kwargs))
    return instances


def build_synthetic_instance_from_config(
    config: SyntheticRegimeConfig | dict[str, Any],
    *,
    instance_index: int = 0,
) -> SyntheticInstance:
    resolved = config if isinstance(config, SyntheticRegimeConfig) else SyntheticRegimeConfig.from_mapping(config)
    try:
        builder = REGIME_BUILDERS[resolved.regime_name]
    except KeyError as exc:
        available = ", ".join(sorted(REGIME_BUILDERS))
        raise ValueError(f"unknown synthetic regime {resolved.regime_name!r}; available: {available}") from exc

    kwargs: dict[str, Any] = {
        "seed": resolved.seed,
        "instance_index": instance_index,
        "n_items": resolved.n_items,
        "budget_tokens": resolved.budget_tokens,
        "noise_level": resolved.noise_level,
    }
    if resolved.token_cost_range is not None:
        kwargs["token_cost_range"] = resolved.token_cost_range
    if resolved.regime_name == "redundancy_dominated" and resolved.cluster_count is not None:
        kwargs["cluster_count"] = resolved.cluster_count
    if resolved.regime_name == "sparse_pairwise_synergy" and resolved.pairwise_degree is not None:
        kwargs["pairwise_degree"] = resolved.pairwise_degree
    if resolved.regime_name == "higher_order_synergy" and resolved.triple_count is not None:
        kwargs["triple_count"] = resolved.triple_count
    return builder(**kwargs)


def value_of_set(instance: SyntheticInstance, selected_ids: Iterable[str]) -> float:
    return instance.value(selected_ids)


def singleton_marginal(instance: SyntheticInstance, item_id: str, context_ids: Iterable[str]) -> float:
    context = list(context_ids)
    if item_id in context:
        return 0.0
    return round(instance.value([*context, item_id]) - instance.value(context), 6)


def block_ratio(instance: SyntheticInstance, context_ids: Iterable[str], block_ids: Iterable[str]) -> float | None:
    context = list(context_ids)
    block = list(block_ids)
    base_value = instance.value(context)
    joint_gain = instance.value([*context, *block]) - base_value
    if joint_gain <= 0:
        return None
    marginal_sum = sum(singleton_marginal(instance, item_id, context) for item_id in block)
    return round(max(0.0, min(1.0, marginal_sum / joint_gain)), 6)


def pairwise_interaction(instance: SyntheticInstance, left_id: str, right_id: str) -> float:
    interaction = instance.value([left_id, right_id]) - instance.value([left_id]) - instance.value([right_id])
    return round(max(0.0, interaction), 6)


def triple_excess(instance: SyntheticInstance, first_id: str, second_id: str, third_id: str) -> float:
    singleton_sum = instance.value([first_id]) + instance.value([second_id]) + instance.value([third_id])
    pair_sum = (
        pairwise_interaction(instance, first_id, second_id)
        + pairwise_interaction(instance, first_id, third_id)
        + pairwise_interaction(instance, second_id, third_id)
    )
    excess = instance.value([first_id, second_id, third_id]) - singleton_sum - pair_sum
    return round(max(0.0, excess), 6)
