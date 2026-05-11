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

METRIC_CLAIM_LEVEL_ALIASES = {
    "Vinfo_proxy_certified": "vinfo_proxy_supported",
    "structural_synthetic_only": "ambiguous_metric",
    "calibrated_proxy": "calibrated_proxy_supported",
    "ambiguous": "ambiguous_metric",
}

SELECTOR_REGIME_LABEL_ALIASES = {
    "greedy_valid": "greedy_supported",
}
SYNTHETIC_DIAGNOSTIC_SCOPES = {
    "synthetic_structural_only",
    "oracle_structural_only",
    "synthetic_oracle_structural_only",
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


def normalize_metric_claim_level(value: Any) -> str:
    label = str(value or "ambiguous_metric")
    return METRIC_CLAIM_LEVEL_ALIASES.get(label, label)


def normalize_diagnostic_scope(value: Any) -> str:
    label = str(value or "ambiguous_metric")
    aliases = {
        "synthetic": "synthetic_structural_only",
        "synthetic_structural": "synthetic_structural_only",
        "structural_synthetic_only": "synthetic_structural_only",
    }
    return aliases.get(label, label)


def is_synthetic_diagnostic_scope(value: Any) -> bool:
    return normalize_diagnostic_scope(value) in SYNTHETIC_DIAGNOSTIC_SCOPES


def normalize_selector_regime_label(
    value: Any,
    diagnostics: Any | None = None,
    thresholds: dict | None = None,
) -> str:
    label = str(value or "ambiguous")
    if label in SELECTOR_REGIME_LABEL_ALIASES:
        return SELECTOR_REGIME_LABEL_ALIASES[label]
    if label == "escalate":
        resolved = resolve_selector_thresholds(thresholds)
        triple_excess_flag = str(_get(diagnostics, "triple_excess_flag", "") or "")
        higher_order_ambiguity = _as_bool(_get(diagnostics, "higher_order_ambiguity_flag", False))
        if triple_excess_flag == "positive":
            return "higher_order_risk"
        if higher_order_ambiguity:
            return "ambiguous"
        return "pairwise_escalate" if _has_pairwise_escalation_signal(diagnostics, resolved) else "pairwise_escalate"
    return label


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
        return "ambiguous_metric"

    metric_class = str(_get(metric_bridge_witness, "metric_class", "") or "")
    drift_status = str(_get(metric_bridge_witness, "drift_status", "") or "")

    if drift_status in {"stale", "ambiguous"}:
        return "ambiguous_metric"
    if metric_class == "synthetic_oracle":
        return normalize_metric_claim_level(_get(metric_bridge_witness, "diagnostic_claim_level", "ambiguous_metric"))
    if metric_class == "log_loss_aligned" and drift_status == "fresh":
        return "vinfo_proxy_supported"
    if metric_class == "bridge_calibrated" and drift_status == "fresh":
        return "calibrated_proxy_supported"
    if metric_class == "operational_only":
        return "operational_utility_only"
    return normalize_metric_claim_level(_get(metric_bridge_witness, "diagnostic_claim_level", "ambiguous_metric"))


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
    normalized_metric_claim_level = normalize_metric_claim_level(metric_claim_level)
    diagnostic_scope = _get(diagnostics, "diagnostic_scope", _get(diagnostics, "evidence_scope", ""))
    if normalized_metric_claim_level == "ambiguous_metric" and not is_synthetic_diagnostic_scope(diagnostic_scope):
        return "ambiguous"
    if not _has_sufficient_denominator_signal(diagnostics, resolved):
        return "ambiguous"

    triple_excess_flag = str(_get(diagnostics, "triple_excess_flag", "") or "")
    higher_order_ambiguity = _as_bool(_get(diagnostics, "higher_order_ambiguity_flag", False))
    if triple_excess_flag == "positive":
        return "higher_order_risk"
    if higher_order_ambiguity:
        return "ambiguous"

    block_ratio = _as_float(_get(diagnostics, "block_ratio_lcb_star"))
    if block_ratio is None:
        return "ambiguous"

    monitored = resolved["monitored_greedy"]
    if block_ratio < float(monitored["block_ratio_lcb_star_gte"]):
        return "pairwise_escalate"
    if _has_pairwise_escalation_signal(diagnostics, resolved):
        return "pairwise_escalate"

    return "greedy_supported"


def derive_selector_action(
    selector_regime_label: str,
    diagnostics: Any,
    thresholds: dict | None,
) -> str:
    normalized_label = normalize_selector_regime_label(selector_regime_label, diagnostics, thresholds)
    if normalized_label == "greedy_supported":
        return "monitored_greedy"
    if normalized_label == "ambiguous":
        return "no_certified_switch"
    if normalized_label == "pairwise_escalate":
        return "seeded_augmented_greedy"
    if normalized_label != "higher_order_risk":
        return "no_certified_switch"

    return "interaction_aware_local_search"
