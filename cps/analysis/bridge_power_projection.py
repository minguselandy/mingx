from __future__ import annotations

from typing import Any
from typing import Mapping


def _float_value(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(payload.get(key, default))
    except (TypeError, ValueError):
        return default


def project_bridge_power(
    bridge_fit_summary: Mapping[str, Any],
    *,
    min_rows: int = 500,
    min_sign_agreement: float = 0.70,
    min_spearman_rho: float = 0.40,
    max_normalized_residual: float = 0.35,
) -> dict[str, Any]:
    bridge_fit = dict(bridge_fit_summary.get("bridge_fit") or {})
    gate_flags = dict(bridge_fit_summary.get("gate_pass_flags") or {})
    rows_validated = int(bridge_fit_summary.get("rows_validated") or 0)
    unique_instances = int(bridge_fit_summary.get("unique_original_instances") or 0)
    normalized_residual = _float_value(bridge_fit, "normalized_residual", 1.0)
    sign_agreement = _float_value(bridge_fit, "sign_agreement")
    spearman_rho = _float_value(bridge_fit, "spearman_rho")

    underpowered = rows_validated < min_rows or gate_flags.get("row_count_pass") is False
    signal_failures = []
    if normalized_residual > max_normalized_residual or gate_flags.get("normalized_residual_pass") is False:
        signal_failures.append("normalized_residual_gate_failed")
    if sign_agreement < min_sign_agreement or gate_flags.get("sign_agreement_pass") is False:
        signal_failures.append("sign_agreement_gate_failed")
    if spearman_rho < min_spearman_rho or gate_flags.get("spearman_rho_pass") is False:
        signal_failures.append("spearman_gate_failed")
    signal_weak = bool(signal_failures)

    if underpowered and signal_weak:
        status = "underpowered_and_signal_weak"
    elif underpowered:
        status = "underpowered_but_signal_not_disqualified"
    elif signal_weak:
        status = "powered_but_signal_weak"
    else:
        status = "candidate_bridge_signal"

    return {
        "bridge_power_status": status,
        "claim_status": "operational_utility_only/no_claim_upgrade",
        "direct_bridge_scaleup_recommended": underpowered and not signal_weak,
        "gate_result": str(bridge_fit_summary.get("gate_result") or "unknown"),
        "metric_claim_level": "operational_utility_only",
        "observed": {
            "normalized_residual": normalized_residual,
            "rows_validated": rows_validated,
            "sign_agreement": sign_agreement,
            "spearman_rho": spearman_rho,
            "unique_original_instances": unique_instances,
        },
        "power_gap": {
            "min_rows": min_rows,
            "row_shortfall": max(0, min_rows - rows_validated),
        },
        "route4b_is_merely_underpowered": underpowered and not signal_weak,
        "schema_version": "iw_bridge_power_projection_v1",
        "signal_failures": signal_failures,
        "signal_weak": signal_weak,
        "underpowered": underpowered,
    }
