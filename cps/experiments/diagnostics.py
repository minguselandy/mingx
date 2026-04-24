from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Sequence

from cps.experiments.selection import SelectionResult
from cps.experiments.synthetic_regimes import SyntheticItem


DEFAULT_POLICY_THRESHOLDS = {
    "monitored_greedy": {
        "gamma_hat_gte": 0.75,
        "synergy_fraction_lte": 0.10,
        "greedy_augmented_gap_lte": 0.05,
    },
    "seeded_augmented_greedy": {
        "gamma_hat_gte": 0.45,
        "greedy_augmented_gap_lte": 0.15,
    },
}


@dataclass(frozen=True)
class DiagnosticResult:
    gamma_hat: float
    synergy_fraction: float
    greedy_augmented_gap: float
    policy_recommendation: str
    pairwise_samples: list[dict]
    thresholds: dict
    notes: str


def estimate_gamma_hat(greedy_trace: Sequence[dict], *, quantile: float = 0.1) -> float:
    ratios: list[float] = []
    for row in greedy_trace:
        if row.get("source") == "seed":
            continue
        singleton = float(row.get("singleton_gain") or 0.0)
        marginal = float(row.get("marginal_gain") or 0.0)
        if singleton <= 0 or marginal <= 0:
            continue
        ratio = singleton / max(singleton, marginal)
        ratios.append(max(0.0, min(1.0, ratio)))
    if not ratios:
        return 1.0
    ordered = sorted(ratios)
    if len(ordered) == 1:
        return round(ordered[0], 6)
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(len(ordered) - 1, lower + 1)
    if lower == upper:
        return round(ordered[lower], 6)
    weight = position - lower
    return round(ordered[lower] + ((ordered[upper] - ordered[lower]) * weight), 6)


def sample_pairwise_interactions(
    *,
    items: Sequence[SyntheticItem],
    value_fn,
    top_l: int,
    synergy_epsilon: float = 1e-9,
) -> list[dict]:
    ranked = sorted(
        items,
        key=lambda item: (
            -(value_fn([item.item_id]) / max(1, item.token_cost)),
            item.item_id,
        ),
    )[:top_l]
    samples: list[dict] = []
    for left, right in combinations(ranked, 2):
        left_value = value_fn([left.item_id])
        right_value = value_fn([right.item_id])
        pair_value = value_fn([left.item_id, right.item_id])
        interaction_information = round(left_value + right_value - pair_value, 6)
        if interaction_information < -synergy_epsilon:
            label = "synergy"
        elif interaction_information > synergy_epsilon:
            label = "redundancy"
        else:
            label = "additive"
        samples.append(
            {
                "left_id": left.item_id,
                "right_id": right.item_id,
                "interaction_information": interaction_information,
                "label": label,
            }
        )
    return samples


def synergy_fraction(pairwise_samples: Iterable[dict]) -> float:
    rows = list(pairwise_samples)
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if row["label"] == "synergy") / len(rows), 6)


def greedy_augmented_gap(*, greedy_value: float, augmented_value: float) -> float:
    if augmented_value <= 0:
        return 0.0
    return round(max(0.0, augmented_value - greedy_value) / augmented_value, 6)


def recommend_policy(
    *,
    gamma_hat: float,
    synergy_fraction_value: float,
    greedy_augmented_gap_value: float,
    thresholds: dict | None = None,
) -> str:
    policy_thresholds = thresholds or DEFAULT_POLICY_THRESHOLDS
    monitored = policy_thresholds["monitored_greedy"]
    if (
        gamma_hat >= float(monitored["gamma_hat_gte"])
        and synergy_fraction_value <= float(monitored["synergy_fraction_lte"])
        and greedy_augmented_gap_value <= float(monitored["greedy_augmented_gap_lte"])
    ):
        return "monitored_greedy"

    seeded = policy_thresholds["seeded_augmented_greedy"]
    if (
        gamma_hat >= float(seeded["gamma_hat_gte"])
        and greedy_augmented_gap_value <= float(seeded["greedy_augmented_gap_lte"])
    ):
        return "seeded_augmented_greedy"
    return "interaction_aware_local_search"


def compute_diagnostics(
    *,
    items: Sequence[SyntheticItem],
    value_fn,
    greedy_result: SelectionResult,
    augmented_result: SelectionResult,
    top_l: int,
    thresholds: dict | None = None,
) -> DiagnosticResult:
    pairwise_samples = sample_pairwise_interactions(items=items, value_fn=value_fn, top_l=top_l)
    gamma = estimate_gamma_hat(greedy_result.trace)
    synergy = synergy_fraction(pairwise_samples)
    gap = greedy_augmented_gap(greedy_value=greedy_result.value, augmented_value=augmented_result.value)
    policy = recommend_policy(
        gamma_hat=gamma,
        synergy_fraction_value=synergy,
        greedy_augmented_gap_value=gap,
        thresholds=thresholds,
    )
    return DiagnosticResult(
        gamma_hat=gamma,
        synergy_fraction=synergy,
        greedy_augmented_gap=gap,
        policy_recommendation=policy,
        pairwise_samples=pairwise_samples,
        thresholds=thresholds or DEFAULT_POLICY_THRESHOLDS,
        notes=(
            "Synthetic proxy-layer diagnostic; thresholds are provisional calibration bins "
            "and do not imply theorem inheritance or system-level validation."
        ),
    )
