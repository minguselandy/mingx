from __future__ import annotations

from typing import Any
from typing import Mapping
from typing import Sequence

from cps.analysis.bridge_controls import shadow_bridge_controls


def _mean(values: Sequence[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _spearman_placeholder(rows: Sequence[Mapping[str, Any]]) -> float | None:
    if len(rows) < 2:
        return None
    left = [float(row.get("delta_logloss", 0.0)) for row in rows]
    right = [float(row.get("delta_utility", 0.0)) for row in rows]
    left_order = {value: index for index, value in enumerate(sorted(set(left)))}
    right_order = {value: index for index, value in enumerate(sorted(set(right)))}
    ranked = [(left_order[left_value], right_order[right_value]) for left_value, right_value in zip(left, right)]
    if not ranked:
        return None
    left_ranks = [float(left_rank) for left_rank, _right_rank in ranked]
    right_ranks = [float(right_rank) for _left_rank, right_rank in ranked]
    left_mean = sum(left_ranks) / len(left_ranks)
    right_mean = sum(right_ranks) / len(right_ranks)
    numerator = sum(
        (left_rank - left_mean) * (right_rank - right_mean)
        for left_rank, right_rank in zip(left_ranks, right_ranks)
    )
    left_denominator = sum((left_rank - left_mean) ** 2 for left_rank in left_ranks)
    right_denominator = sum((right_rank - right_mean) ** 2 for right_rank in right_ranks)
    if left_denominator == 0 or right_denominator == 0:
        return None
    return round(numerator / ((left_denominator * right_denominator) ** 0.5), 6)


def analyze_metric_bridge_shadow(
    rows: Sequence[Mapping[str, Any]],
    *,
    min_rows: int = 500,
    min_unique_instances: int = 150,
) -> dict[str, Any]:
    parsed = [dict(row) for row in rows]
    valid = [
        row
        for row in parsed
        if row.get("delta_logloss") is not None and row.get("delta_utility") is not None
    ]
    unique_instances = len({str(row.get("instance_id") or "") for row in valid if row.get("instance_id")})
    rows_validated = len(valid)
    if rows_validated == 0:
        bridge_status = "failed_closed_no_rows"
    elif rows_validated < min_rows or unique_instances < min_unique_instances:
        bridge_status = "failed_closed_underpowered"
    else:
        bridge_status = "failed_closed_gate_failed"

    sign_pairs = [
        (_sign(float(row.get("delta_logloss", 0.0))), _sign(float(row.get("delta_utility", 0.0))))
        for row in valid
    ]
    sign_agreement = (
        round(sum(1 for left, right in sign_pairs if left == right) / len(sign_pairs), 6)
        if sign_pairs
        else None
    )
    residuals = [
        abs(float(row.get("delta_logloss", 0.0)) - float(row.get("delta_utility", 0.0)))
        for row in valid
    ]
    bridge_fit_summary = {
        "ESS": rows_validated,
        "bridge_status": bridge_status,
        "claim_mode": "shadow",
        "normalized_MAE": _mean(residuals),
        "residual_distribution": {
            "max_abs_residual": max(residuals) if residuals else None,
            "mean_abs_residual": _mean(residuals),
        },
        "rows_imported": len(parsed),
        "rows_validated": rows_validated,
        "sign_agreement": sign_agreement,
        "spearman_rho": _spearman_placeholder(valid),
        "unique_instances": unique_instances,
    }
    witness = {
        "bridge_status": bridge_status,
        "calibrated_proxy_supported": False,
        "claim_mode": "shadow",
        "metric_claim_level": "operational_utility_only",
        "shadow_metric_bridge": True,
        "vinfo_proxy_supported": False,
    }
    gate = {
        **shadow_bridge_controls(),
        "claim_mode": "shadow",
        "reason_codes": [bridge_status, "bridge_shadow_mode", "no_claim_upgrade"],
        "shadow_labels": ["shadow_metric_bridge", "shadow_vinfo_proxy"],
    }
    return {
        "bridge_fit_summary": bridge_fit_summary,
        "claim_gate_result": gate,
        "control_results": shadow_bridge_controls(),
        "metric_bridge_witness": witness,
    }
