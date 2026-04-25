from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Iterable, Sequence

from cps.experiments.decision import (
    DEFAULT_SELECTOR_THRESHOLDS,
    derive_metric_claim_level,
    derive_selector_action,
    derive_selector_regime_label,
    resolve_selector_thresholds,
)
from cps.experiments.selection import SelectionResult
from cps.experiments.synthetic_regimes import SyntheticItem


DEFAULT_LCB_QUANTILE = 0.1
DEFAULT_DENOMINATOR_THRESHOLD = 1e-9
DEFAULT_POLICY_THRESHOLDS = {
    name: dict(values)
    for name, values in DEFAULT_SELECTOR_THRESHOLDS.items()
}
STAR_BLOCK_PLACEHOLDER_SEMANTICS = "placeholder_conservative_min_b2_b3_not_degree_adaptive_star"
SYNTHETIC_ORACLE_METRIC_BRIDGE = {
    "metric_class": "synthetic_oracle",
    "drift_status": "fresh",
}


@dataclass(frozen=True)
class DiagnosticResult:
    block_ratio_lcb_b2: float | None
    block_ratio_lcb_star: float | None
    block_ratio_lcb_star_semantics: str
    block_ratio_lcb_b3: float | None
    block_ratio_uninformative_count: int
    block_ratio_sample_count: int
    trace_decay_proxy: float | None
    gamma_hat: float | None
    synergy_fraction: float
    positive_interaction_mass_ucb: float | None
    triple_excess_lcb_max: float | None
    triple_excess_flag: str
    higher_order_ambiguity_flag: bool
    greedy_augmented_gap: float
    metric_claim_level: str
    selector_regime_label: str
    selector_action: str
    policy_recommendation: str
    pairwise_samples: list[dict]
    block_ratio_samples: list[dict]
    triple_samples: list[dict]
    thresholds: dict
    notes: str


def _round(value: float) -> float:
    return round(float(value), 6)


def _quantile(values: Sequence[float], quantile: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return _round(ordered[0])
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(len(ordered) - 1, lower + 1)
    if lower == upper:
        return _round(ordered[lower])
    weight = position - lower
    return _round(ordered[lower] + ((ordered[upper] - ordered[lower]) * weight))


def _normalized_ids(ids: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item_id in ids:
        key = str(item_id)
        if key not in seen:
            normalized.append(key)
            seen.add(key)
    return normalized


def _with_block(context_ids: Sequence[str], block_ids: Sequence[str]) -> list[str]:
    return _normalized_ids([*context_ids, *block_ids])


def _ranked_item_ids(
    *,
    items: Sequence[SyntheticItem],
    value_fn,
    top_l: int | None = None,
) -> list[str]:
    ranked = sorted(
        items,
        key=lambda item: (
            -(value_fn([item.item_id]) / max(1, item.token_cost)),
            item.item_id,
        ),
    )
    if top_l is not None:
        ranked = ranked[:top_l]
    return [item.item_id for item in ranked]


def _greedy_contexts(greedy_trace: Sequence[dict], *, max_contexts: int = 8) -> list[list[str]]:
    contexts: list[list[str]] = [[]]
    selected: list[str] = []
    for row in greedy_trace:
        before = _normalized_ids(row.get("selected_before") or selected)
        contexts.append(before)
        item_id = row.get("item_id")
        if item_id is not None:
            selected = _with_block(before, [str(item_id)])
            contexts.append(selected)

    deduped: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for context in contexts:
        key = tuple(context)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(context)
        if len(deduped) >= max_contexts:
            break
    return deduped


def compute_block_ratio_samples(
    *,
    items: Sequence[SyntheticItem],
    value_fn,
    contexts: Sequence[Sequence[str]] | None = None,
    block_size: int,
    top_l: int | None = None,
    denominator_threshold: float = DEFAULT_DENOMINATOR_THRESHOLD,
) -> list[dict]:
    ranked_ids = _ranked_item_ids(items=items, value_fn=value_fn, top_l=top_l)
    context_rows = list(contexts) if contexts is not None else [[]]
    samples: list[dict] = []

    for context_index, raw_context in enumerate(context_rows):
        context_ids = _normalized_ids(raw_context)
        context_set = set(context_ids)
        available_ids = [item_id for item_id in ranked_ids if item_id not in context_set]
        if len(available_ids) < block_size:
            continue

        base_value = float(value_fn(context_ids))
        for block_ids_tuple in combinations(available_ids, block_size):
            block_ids = list(block_ids_tuple)
            a_sum_marginals = sum(float(value_fn(_with_block(context_ids, [item_id]))) - base_value for item_id in block_ids)
            b_joint_gain = float(value_fn(_with_block(context_ids, block_ids))) - base_value
            denominator_uninformative = b_joint_gain <= denominator_threshold
            raw_ratio = None
            clamped_ratio = None
            if not denominator_uninformative:
                raw_ratio = a_sum_marginals / b_joint_gain
                clamped_ratio = max(0.0, min(1.0, raw_ratio))

            samples.append(
                {
                    "context_index": context_index,
                    "context_ids": context_ids,
                    "block_ids": block_ids,
                    "block_size": block_size,
                    "a_sum_marginals": _round(a_sum_marginals),
                    "b_joint_gain": _round(b_joint_gain),
                    "raw_ratio": None if raw_ratio is None else _round(raw_ratio),
                    "clamped_ratio": None if clamped_ratio is None else _round(clamped_ratio),
                    "denominator_uninformative": denominator_uninformative,
                    "denominator_threshold": denominator_threshold,
                }
            )
    return samples


def compute_block_ratio_lcb(
    samples: Sequence[dict],
    *,
    quantile: float = DEFAULT_LCB_QUANTILE,
) -> float | None:
    informative = [
        float(row["clamped_ratio"])
        for row in samples
        if not bool(row.get("denominator_uninformative")) and row.get("clamped_ratio") is not None
    ]
    if not informative:
        return None
    return _quantile(informative, quantile)


def compute_pair_block_ratio_lcb(
    *,
    items: Sequence[SyntheticItem],
    value_fn,
    contexts: Sequence[Sequence[str]] | None = None,
    top_l: int | None = None,
    denominator_threshold: float = DEFAULT_DENOMINATOR_THRESHOLD,
    quantile: float = DEFAULT_LCB_QUANTILE,
) -> float | None:
    samples = compute_block_ratio_samples(
        items=items,
        value_fn=value_fn,
        contexts=contexts,
        block_size=2,
        top_l=top_l,
        denominator_threshold=denominator_threshold,
    )
    return compute_block_ratio_lcb(samples, quantile=quantile)


def compute_block3_ratio_lcb(
    *,
    items: Sequence[SyntheticItem],
    value_fn,
    contexts: Sequence[Sequence[str]] | None = None,
    top_l: int | None = None,
    denominator_threshold: float = DEFAULT_DENOMINATOR_THRESHOLD,
    quantile: float = DEFAULT_LCB_QUANTILE,
) -> float | None:
    samples = compute_block_ratio_samples(
        items=items,
        value_fn=value_fn,
        contexts=contexts,
        block_size=3,
        top_l=top_l,
        denominator_threshold=denominator_threshold,
    )
    return compute_block_ratio_lcb(samples, quantile=quantile)


def compute_trace_decay_proxy(greedy_trace: Sequence[dict], *, quantile: float = DEFAULT_LCB_QUANTILE) -> float | None:
    ratios: list[float] = []
    for row in greedy_trace:
        if row.get("source") == "seed":
            continue
        singleton = float(row.get("singleton_gain") or 0.0)
        marginal = float(row.get("marginal_gain") or 0.0)
        if singleton <= 0:
            continue
        ratios.append(marginal / singleton)
    if not ratios:
        return 1.0
    return _quantile(ratios, quantile)


def estimate_gamma_hat(greedy_trace: Sequence[dict], *, quantile: float = DEFAULT_LCB_QUANTILE) -> float | None:
    """Legacy compatibility wrapper; not a submodularity-ratio estimator."""

    return compute_trace_decay_proxy(greedy_trace, quantile=quantile)


def sample_pairwise_interactions(
    *,
    items: Sequence[SyntheticItem],
    value_fn,
    top_l: int,
    synergy_epsilon: float = 1e-9,
) -> list[dict]:
    ranked_ids = _ranked_item_ids(items=items, value_fn=value_fn, top_l=top_l)
    samples: list[dict] = []
    for left_id, right_id in combinations(ranked_ids, 2):
        left_value = value_fn([left_id])
        right_value = value_fn([right_id])
        pair_value = value_fn([left_id, right_id])
        interaction_information = round(left_value + right_value - pair_value, 6)
        if interaction_information < -synergy_epsilon:
            label = "synergy"
        elif interaction_information > synergy_epsilon:
            label = "redundancy"
        else:
            label = "additive"
        samples.append(
            {
                "left_id": left_id,
                "right_id": right_id,
                "interaction_information": interaction_information,
                "positive_interaction_mass": _round(max(0.0, -interaction_information)),
                "label": label,
            }
        )
    return samples


def synergy_fraction(pairwise_samples: Iterable[dict]) -> float:
    rows = list(pairwise_samples)
    if not rows:
        return 0.0
    return _round(sum(1 for row in rows if row["label"] == "synergy") / len(rows))


def positive_interaction_mass_ucb(pairwise_samples: Iterable[dict]) -> float | None:
    rows = list(pairwise_samples)
    if not rows:
        return None
    return _round(sum(float(row.get("positive_interaction_mass", 0.0)) for row in rows) / len(rows))


def sample_triple_excesses(
    *,
    items: Sequence[SyntheticItem],
    value_fn,
    contexts: Sequence[Sequence[str]] | None = None,
    top_l: int,
) -> list[dict]:
    ranked_ids = _ranked_item_ids(items=items, value_fn=value_fn, top_l=top_l)
    context_rows = list(contexts) if contexts is not None else [[]]
    samples: list[dict] = []
    for context_index, raw_context in enumerate(context_rows):
        context_ids = _normalized_ids(raw_context)
        context_set = set(context_ids)
        available_ids = [item_id for item_id in ranked_ids if item_id not in context_set]
        if len(available_ids) < 3:
            continue

        base_value = float(value_fn(context_ids))
        for triple_ids_tuple in combinations(available_ids, 3):
            i_id, j_id, k_id = list(triple_ids_tuple)
            a_i = float(value_fn(_with_block(context_ids, [i_id]))) - base_value
            a_j = float(value_fn(_with_block(context_ids, [j_id]))) - base_value
            a_k = float(value_fn(_with_block(context_ids, [k_id]))) - base_value
            beta_ij = float(value_fn(_with_block(context_ids, [i_id, j_id]))) - base_value - a_i - a_j
            beta_ik = float(value_fn(_with_block(context_ids, [i_id, k_id]))) - base_value - a_i - a_k
            beta_jk = float(value_fn(_with_block(context_ids, [j_id, k_id]))) - base_value - a_j - a_k
            p_ijk = a_i + a_j + a_k + beta_ij + beta_ik + beta_jk
            triple_value = float(value_fn(_with_block(context_ids, [i_id, j_id, k_id])))
            omega_ijk = triple_value - base_value - p_ijk
            samples.append(
                {
                    "context_index": context_index,
                    "context_ids": context_ids,
                    "triple_ids": [i_id, j_id, k_id],
                    "a_i": _round(a_i),
                    "a_j": _round(a_j),
                    "a_k": _round(a_k),
                    "beta_ij": _round(beta_ij),
                    "beta_ik": _round(beta_ik),
                    "beta_jk": _round(beta_jk),
                    "p_ijk": _round(p_ijk),
                    "triple_value": _round(triple_value),
                    "omega_ijk": _round(omega_ijk),
                    "triple_excess": _round(omega_ijk),
                }
            )
    return samples


def _has_higher_order_risk(items: Sequence[SyntheticItem]) -> bool:
    for item in items:
        metadata = dict(item.metadata or {})
        if metadata.get("regime_role") == "triple_prerequisite":
            return True
        if bool(metadata.get("higher_order_risk")):
            return True
    return False


def _triple_excess_status(
    *,
    triple_samples: Sequence[dict],
    higher_order_risk_hint: bool,
) -> tuple[float | None, str, bool]:
    if not triple_samples:
        return None, "not_evaluable", higher_order_risk_hint

    max_omega = _round(max(float(row.get("omega_ijk", row.get("triple_excess", 0.0))) for row in triple_samples))
    if max_omega > DEFAULT_DENOMINATOR_THRESHOLD:
        return max_omega, "positive", True
    if higher_order_risk_hint:
        return max_omega, "ambiguous", True
    return max_omega, "none_detected", False


def greedy_augmented_gap(*, greedy_value: float, augmented_value: float) -> float:
    if augmented_value <= 0:
        return 0.0
    return _round(max(0.0, augmented_value - greedy_value) / augmented_value)


def _resolved_thresholds(thresholds: dict | None) -> dict:
    return resolve_selector_thresholds(thresholds)


def _min_present(values: Iterable[float | None]) -> float | None:
    present = [float(value) for value in values if value is not None]
    if not present:
        return None
    return _round(min(present))


def recommend_policy(
    *,
    block_ratio_lcb_star: float | None,
    synergy_fraction_value: float,
    greedy_augmented_gap_value: float,
    higher_order_ambiguity_flag: bool,
    thresholds: dict | None = None,
) -> str:
    policy_thresholds = _resolved_thresholds(thresholds)
    diagnostics = {
        "block_ratio_lcb_star": block_ratio_lcb_star,
        "block_ratio_sample_count": 1,
        "block_ratio_uninformative_count": 0,
        "synergy_fraction": synergy_fraction_value,
        "positive_interaction_mass_ucb": None,
        "greedy_augmented_gap": greedy_augmented_gap_value,
        "triple_excess_flag": "not_evaluable" if higher_order_ambiguity_flag else "none_detected",
        "higher_order_ambiguity_flag": higher_order_ambiguity_flag,
    }
    label = derive_selector_regime_label(diagnostics, "structural_synthetic_only", policy_thresholds)
    return derive_selector_action(label, diagnostics, policy_thresholds)


def _selector_regime_label(
    *,
    block_ratio_lcb_star: float | None,
    synergy_fraction_value: float,
    higher_order_ambiguity_flag: bool,
    thresholds: dict,
) -> str:
    diagnostics = {
        "block_ratio_lcb_star": block_ratio_lcb_star,
        "block_ratio_sample_count": 1,
        "block_ratio_uninformative_count": 0,
        "synergy_fraction": synergy_fraction_value,
        "positive_interaction_mass_ucb": None,
        "greedy_augmented_gap": 0.0,
        "triple_excess_flag": "not_evaluable" if higher_order_ambiguity_flag else "none_detected",
        "higher_order_ambiguity_flag": higher_order_ambiguity_flag,
    }
    return derive_selector_regime_label(diagnostics, "structural_synthetic_only", thresholds)


def compute_diagnostics(
    *,
    items: Sequence[SyntheticItem],
    value_fn,
    greedy_result: SelectionResult,
    augmented_result: SelectionResult,
    top_l: int,
    thresholds: dict | None = None,
    metric_bridge_witness: Any | None = SYNTHETIC_ORACLE_METRIC_BRIDGE,
) -> DiagnosticResult:
    resolved_thresholds = _resolved_thresholds(thresholds)
    contexts = _greedy_contexts(greedy_result.trace)
    pairwise_samples = sample_pairwise_interactions(items=items, value_fn=value_fn, top_l=top_l)
    block2_samples = compute_block_ratio_samples(
        items=items,
        value_fn=value_fn,
        contexts=contexts,
        block_size=2,
        top_l=top_l,
    )
    block3_samples = compute_block_ratio_samples(
        items=items,
        value_fn=value_fn,
        contexts=contexts,
        block_size=3,
        top_l=top_l,
    )
    block_ratio_samples = [*block2_samples, *block3_samples]
    block_ratio_lcb_b2 = compute_block_ratio_lcb(block2_samples)
    block_ratio_lcb_b3 = compute_block_ratio_lcb(block3_samples)
    block_ratio_lcb_star = _min_present([block_ratio_lcb_b2, block_ratio_lcb_b3])
    trace_decay = compute_trace_decay_proxy(greedy_result.trace)
    synergy = synergy_fraction(pairwise_samples)
    interaction_mass = positive_interaction_mass_ucb(pairwise_samples)
    triple_samples = sample_triple_excesses(items=items, value_fn=value_fn, contexts=contexts, top_l=top_l)
    triple_excess_lcb_max, triple_excess_flag, higher_order_ambiguity = _triple_excess_status(
        triple_samples=triple_samples,
        higher_order_risk_hint=_has_higher_order_risk(items),
    )
    gap = greedy_augmented_gap(greedy_value=greedy_result.value, augmented_value=augmented_result.value)
    metric_claim_level = derive_metric_claim_level(metric_bridge_witness)
    decision_context = {
        "block_ratio_lcb_b2": block_ratio_lcb_b2,
        "block_ratio_lcb_star": block_ratio_lcb_star,
        "block_ratio_lcb_b3": block_ratio_lcb_b3,
        "block_ratio_uninformative_count": sum(1 for row in block_ratio_samples if row["denominator_uninformative"]),
        "block_ratio_sample_count": len(block_ratio_samples),
        "synergy_fraction": synergy,
        "positive_interaction_mass_ucb": interaction_mass,
        "triple_excess_lcb_max": triple_excess_lcb_max,
        "triple_excess_flag": triple_excess_flag,
        "higher_order_ambiguity_flag": higher_order_ambiguity,
        "greedy_augmented_gap": gap,
    }
    selector_regime_label = derive_selector_regime_label(decision_context, metric_claim_level, resolved_thresholds)
    selector_action = derive_selector_action(selector_regime_label, decision_context, resolved_thresholds)
    return DiagnosticResult(
        block_ratio_lcb_b2=block_ratio_lcb_b2,
        block_ratio_lcb_star=block_ratio_lcb_star,
        block_ratio_lcb_star_semantics=STAR_BLOCK_PLACEHOLDER_SEMANTICS,
        block_ratio_lcb_b3=block_ratio_lcb_b3,
        block_ratio_uninformative_count=sum(1 for row in block_ratio_samples if row["denominator_uninformative"]),
        block_ratio_sample_count=len(block_ratio_samples),
        trace_decay_proxy=trace_decay,
        gamma_hat=trace_decay,
        synergy_fraction=synergy,
        positive_interaction_mass_ucb=interaction_mass,
        triple_excess_lcb_max=triple_excess_lcb_max,
        triple_excess_flag=triple_excess_flag,
        higher_order_ambiguity_flag=higher_order_ambiguity,
        greedy_augmented_gap=gap,
        metric_claim_level=metric_claim_level,
        selector_regime_label=selector_regime_label,
        selector_action=selector_action,
        policy_recommendation=selector_action,
        pairwise_samples=pairwise_samples,
        block_ratio_samples=block_ratio_samples,
        triple_samples=triple_samples,
        thresholds=resolved_thresholds,
        notes=(
            "Synthetic proxy-layer diagnostic; block-ratio LCB is the headline "
            "weak-submodularity diagnostic. block_ratio_lcb_star is a "
            "placeholder conservative min over b=2/b=3 diagnostics, not a "
            "degree-adaptive star-block estimator. gamma_hat is retained only "
            "as a legacy trace_decay_proxy compatibility alias and is not a "
            "Das-Kempe submodularity-ratio estimator."
        ),
    )
