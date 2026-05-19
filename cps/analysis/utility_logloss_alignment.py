from __future__ import annotations

import math
from collections import defaultdict
from typing import Any
from typing import Mapping
from typing import Sequence


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"


def _float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _mean(values: Sequence[float]) -> float | None:
    return round(sum(values) / len(values), 12) if values else None


def _variance(values: Sequence[float]) -> float | None:
    if not values:
        return None
    mean = sum(values) / len(values)
    return round(sum((value - mean) ** 2 for value in values) / len(values), 12)


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _rank(values: Sequence[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][1] == ordered[index][1]:
            end += 1
        rank = (index + end - 1) / 2 + 1
        for original_index, _ in ordered[index:end]:
            ranks[original_index] = rank
        index = end
    return ranks


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return None
    return round(numerator / (denom_x * denom_y), 12)


def _spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    return _pearson(_rank(xs), _rank(ys))


def _kendall(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    concordant = 0
    discordant = 0
    for left in range(len(xs)):
        for right in range(left + 1, len(xs)):
            dx = _sign(xs[left] - xs[right])
            dy = _sign(ys[left] - ys[right])
            if dx == 0 or dy == 0:
                continue
            if dx == dy:
                concordant += 1
            else:
                discordant += 1
    denom = concordant + discordant
    return round((concordant - discordant) / denom, 12) if denom else None


def _bridge_slope(fit_summary: Mapping[str, Any]) -> float:
    bridge_fit = fit_summary.get("bridge_fit") if isinstance(fit_summary.get("bridge_fit"), Mapping) else {}
    return _float(bridge_fit.get("c_hat_s")) or _float(fit_summary.get("c_hat_s")) or 0.0


def _route_pairs(rows: Sequence[Mapping[str, Any]], utility_field: str) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for row in rows:
        delta_logloss = _float(row.get("delta_logloss"))
        delta_utility = _float(row.get(utility_field))
        if delta_logloss is None or delta_utility is None:
            continue
        pairs.append(
            {
                "candidate_pool_hash": str(row.get("candidate_pool_hash") or ""),
                "delta_logloss": delta_logloss,
                "delta_utility": delta_utility,
                "materialization_policy": str(row.get("materialization_policy") or "unknown"),
                "original_instance_id": str(row.get("original_instance_id") or ""),
                "target_representation": str(row.get("target_representation") or "unknown"),
            }
        )
    return pairs


def _summarize_pairs(
    *,
    fit_summary: Mapping[str, Any],
    pairs: Sequence[Mapping[str, Any]],
    route_id: str,
    target_type: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    xs = [float(pair["delta_logloss"]) for pair in pairs]
    ys = [float(pair["delta_utility"]) for pair in pairs]
    slope = _bridge_slope(fit_summary)
    residuals = [y - slope * x for x, y in zip(xs, ys)]
    abs_residuals = [abs(value) for value in residuals]
    mean_abs_y = sum(abs(value) for value in ys) / len(ys) if ys else 0.0
    normalized_mae = (sum(abs_residuals) / len(abs_residuals) / mean_abs_y) if abs_residuals and mean_abs_y else None
    sign_agreement = (
        sum(1 for x, y in zip(xs, ys) if _sign(x) == _sign(y)) / len(xs)
        if xs
        else None
    )
    near_zero_rate = sum(1 for value in xs if abs(value) <= 0.001) / len(xs) if xs else 0.0
    classification = "weak_signal" if near_zero_rate >= 0.5 or (sign_agreement is not None and sign_agreement < 0.4) else "mixed_signal"
    route_summary = {
        "claim_status": CLAIM_STATUS,
        "gate_result": str(fit_summary.get("gate_result") or ""),
        "kendall_tau": _kendall(xs, ys),
        "logloss_variance": _variance(xs),
        "near_zero_delta_logloss_rate": round(near_zero_rate, 12) if xs else None,
        "negative_delta_logloss_count": sum(1 for value in xs if value < 0),
        "normalized_mae": round(normalized_mae, 12) if normalized_mae is not None else None,
        "positive_delta_logloss_count": sum(1 for value in xs if value > 0),
        "row_count": len(pairs),
        "schema_version": "alignment_stratum_summary_v1",
        "sign_agreement": round(sign_agreement, 12) if sign_agreement is not None else None,
        "spearman_rho": _spearman(xs, ys),
        "target_type": target_type,
        "unique_original_instances": len({str(pair["original_instance_id"]) for pair in pairs}),
        "utility_variance": _variance(ys),
        "weak_signal_classification": classification,
    }
    leverage_rows: list[dict[str, Any]] = []
    for index, (pair, residual) in enumerate(zip(pairs, residuals)):
        leverage_rows.append(
            {
                "abs_residual": round(abs(residual), 12),
                "candidate_pool_hash": str(pair["candidate_pool_hash"]),
                "delta_logloss": round(float(pair["delta_logloss"]), 12),
                "delta_utility": round(float(pair["delta_utility"]), 12),
                "original_instance_id": str(pair["original_instance_id"]),
                "residual": round(residual, 12),
                "route_id": route_id,
                "row_index": index,
                "target_representation": str(pair["target_representation"]),
            }
        )
    return route_summary, sorted(leverage_rows, key=lambda row: (-row["abs_residual"], row["route_id"], row["row_index"]))


def build_alignment_decomposition(*, route_specs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    strata: dict[str, dict[str, Any]] = {}
    leverage_rows: list[dict[str, Any]] = []
    target_accumulator: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for spec in route_specs:
        route_id = str(spec["route_id"])
        target_type = str(spec.get("target_type") or "unknown")
        pairs = _route_pairs(spec.get("rows") or [], str(spec["utility_field"]))
        summary, route_leverage = _summarize_pairs(
            fit_summary=spec.get("fit_summary") or {},
            pairs=pairs,
            route_id=route_id,
            target_type=target_type,
        )
        strata[route_id] = summary
        leverage_rows.extend(route_leverage[:10])
        target_accumulator[target_type].extend(pairs)

    target_types: dict[str, dict[str, Any]] = {}
    for target_type, pairs in sorted(target_accumulator.items()):
        target_summary, _ = _summarize_pairs(
            fit_summary={},
            pairs=pairs,
            route_id=f"target_type::{target_type}",
            target_type=target_type,
        )
        target_types[target_type] = target_summary

    sorted_leverage = sorted(leverage_rows, key=lambda row: (-row["abs_residual"], row["route_id"], row["row_index"]))[:25]
    tail_threshold = sorted_leverage[0]["abs_residual"] * 0.5 if sorted_leverage else 0.0
    tail_rows = [row for row in sorted_leverage if row["abs_residual"] >= tail_threshold]
    return {
        "alignment_by_stratum": {
            "claim_status": CLAIM_STATUS,
            "schema_version": "alignment_by_stratum_v1",
            "strata": strata,
        },
        "alignment_by_target_type": {
            "claim_status": CLAIM_STATUS,
            "schema_version": "alignment_by_target_type_v1",
            "target_types": target_types,
        },
        "leverage_rows": sorted_leverage,
        "residual_tail_audit": {
            "claim_status": CLAIM_STATUS,
            "schema_version": "residual_tail_audit_v1",
            "tail_count": len(tail_rows),
            "tail_rows": tail_rows[:10],
            "tail_threshold_abs_residual": round(tail_threshold, 12),
        },
    }
