from __future__ import annotations

from collections.abc import Mapping
from typing import Any


DEFAULT_SELECTOR_THRESHOLDS: dict[str, dict[str, float]] = {
    "monitored_greedy": {
        "block_ratio_lcb_star_gte": 0.75,
        "synergy_fraction_lte": 0.10,
        "positive_interaction_mass_ucb_lte": 0.10,
        "greedy_augmented_gap_lte": 0.05,
    },
    "seeded_augmented_greedy": {
        "block_ratio_lcb_star_gte": 0.45,
        "greedy_augmented_gap_lte": 0.15,
    },
    "diagnostic_sufficiency": {
        "block_ratio_sample_count_gte": 1,
        "block_ratio_informative_sample_count_gte": 1,
        "denominator_signal_fraction_gte": 0.50,
    },
}


def _get(record: Any, field: str, default: Any = None) -> Any:
    if record is None:
        return default
    if isinstance(record, Mapping):
        return record.get(field, default)
    return getattr(record, field, default)


def _as_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int | None = None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def resolve_selector_thresholds(thresholds: dict | None) -> dict:
    resolved = {name: dict(values) for name, values in DEFAULT_SELECTOR_THRESHOLDS.items()}
    for name, values in dict(thresholds or {}).items():
        resolved.setdefault(str(name), {}).update(dict(values or {}))

    for values in resolved.values():
        # Legacy compatibility: read old gamma_hat thresholds as block-ratio LCB thresholds only.
        if "block_ratio_lcb_star_gte" not in values and "gamma_hat_gte" in values:
            values["block_ratio_lcb_star_gte"] = values["gamma_hat_gte"]
    return resolved


def derive_metric_claim_level(metric_bridge_witness: Any | None) -> str:
    if not metric_bridge_witness:
        return "ambiguous"

    metric_class = str(_get(metric_bridge_witness, "metric_class", "") or "")
    drift_status = str(_get(metric_bridge_witness, "drift_status", "") or "")

    if drift_status in {"stale", "ambiguous"}:
        return "ambiguous"
    if metric_class == "synthetic_oracle":
        return "structural_synthetic_only"
    if metric_class == "log_loss_aligned" and drift_status == "fresh":
        return "Vinfo_proxy_certified"
    if metric_class == "bridge_calibrated" and drift_status == "fresh":
        return "calibrated_proxy"
    if metric_class == "operational_only":
        return "operational_utility_only"
    return "ambiguous"


def _has_sufficient_denominator_signal(diagnostics: Any, thresholds: dict) -> bool:
    sufficiency = thresholds.get("diagnostic_sufficiency", {})
    sample_count = _as_int(_get(diagnostics, "block_ratio_sample_count"), 0) or 0
    uninformative_count = _as_int(_get(diagnostics, "block_ratio_uninformative_count"), 0) or 0
    informative_count = max(0, sample_count - uninformative_count)

    min_samples = int(sufficiency.get("block_ratio_sample_count_gte", 1))
    min_informative = int(sufficiency.get("block_ratio_informative_sample_count_gte", 1))
    min_signal_fraction = float(sufficiency.get("denominator_signal_fraction_gte", 0.5))

    if sample_count < min_samples or informative_count < min_informative:
        return False
    return (informative_count / sample_count) >= min_signal_fraction


def _has_pairwise_escalation_signal(diagnostics: Any, thresholds: dict) -> bool:
    monitored = thresholds["monitored_greedy"]
    synergy = _as_float(_get(diagnostics, "synergy_fraction"), 0.0) or 0.0
    gap = _as_float(_get(diagnostics, "greedy_augmented_gap"), 0.0) or 0.0
    interaction_mass = _as_float(_get(diagnostics, "positive_interaction_mass_ucb"))

    if synergy > float(monitored["synergy_fraction_lte"]):
        return True
    if gap > float(monitored["greedy_augmented_gap_lte"]):
        return True
    if (
        interaction_mass is not None
        and "positive_interaction_mass_ucb_lte" in monitored
        and interaction_mass > float(monitored["positive_interaction_mass_ucb_lte"])
    ):
        return True
    return False


def derive_selector_regime_label(
    diagnostics: Any,
    metric_claim_level: str,
    thresholds: dict | None,
) -> str:
    resolved = resolve_selector_thresholds(thresholds)
    if metric_claim_level == "ambiguous":
        return "ambiguous"
    if not _has_sufficient_denominator_signal(diagnostics, resolved):
        return "ambiguous"

    triple_excess_flag = str(_get(diagnostics, "triple_excess_flag", "") or "")
    higher_order_ambiguity = _as_bool(_get(diagnostics, "higher_order_ambiguity_flag", False))
    if triple_excess_flag == "positive":
        return "escalate"
    if higher_order_ambiguity:
        return "ambiguous"

    block_ratio = _as_float(_get(diagnostics, "block_ratio_lcb_star"))
    if block_ratio is None:
        return "ambiguous"

    monitored = resolved["monitored_greedy"]
    if block_ratio < float(monitored["block_ratio_lcb_star_gte"]):
        return "escalate"
    if _has_pairwise_escalation_signal(diagnostics, resolved):
        return "escalate"

    return "greedy_valid"


def derive_selector_action(
    selector_regime_label: str,
    diagnostics: Any,
    thresholds: dict | None,
) -> str:
    if selector_regime_label == "greedy_valid":
        return "monitored_greedy"
    if selector_regime_label == "ambiguous":
        return "no_certified_switch"
    if selector_regime_label != "escalate":
        return "no_certified_switch"

    triple_excess_flag = str(_get(diagnostics, "triple_excess_flag", "") or "")
    higher_order_ambiguity = _as_bool(_get(diagnostics, "higher_order_ambiguity_flag", False))
    if triple_excess_flag == "positive" or higher_order_ambiguity:
        return "interaction_aware_local_search"
    return "seeded_augmented_greedy"
