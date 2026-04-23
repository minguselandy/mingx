from __future__ import annotations

import json
import math
import random
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

from scipy.stats import shapiro

from cps.analysis.exports import write_csv, write_json, write_jsonl


DIAGNOSTIC_SCOPE = "scipy_shapiro_with_pure_python_bridge"
PASS_THRESHOLDS = {
    "normality_pvalue": 0.01,
    "breusch_pagan_pvalue": 0.01,
    "icc_question_residual": 0.3,
    "pearson_r": 0.9,
    "mae_to_sigma_ratio": 0.5,
}
BRIDGE_ESCALATION_SEQUENCE = (
    "linear_ols",
    "isotonic",
    "polynomial_quadratic",
    "frontier_full_n_required",
)


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot compute quantile of empty values")
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    lower_value = ordered[lower]
    upper_value = ordered[upper]
    return lower_value + (upper_value - lower_value) * (position - lower)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _sample_variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = _mean(values)
    return sum((value - mu) ** 2 for value in values) / (len(values) - 1)


def _sample_std(values: list[float]) -> float:
    return math.sqrt(_sample_variance(values))


def _ols_fit(rows: list[dict[str, Any]]) -> tuple[float, float]:
    xs = [float(row["delta_small"]) for row in rows]
    ys = [float(row["delta_frontier"]) for row in rows]
    x_mean = _mean(xs)
    y_mean = _mean(ys)
    denominator = sum((value - x_mean) ** 2 for value in xs)
    if denominator == 0:
        return y_mean, 0.0
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator
    intercept = y_mean - (slope * x_mean)
    return intercept, slope


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2 or len(ys) < 2:
        return 0.0
    x_mean = _mean(xs)
    y_mean = _mean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = math.sqrt(sum((x - x_mean) ** 2 for x in xs) * sum((y - y_mean) ** 2 for y in ys))
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _shapiro_wilk_pvalue(residuals: list[float]) -> float:
    if len(residuals) < 3:
        return 1.0
    sigma = _sample_std(residuals)
    if sigma == 0:
        return 1.0
    return float(shapiro(residuals).pvalue)


def _breusch_pagan_pvalue(xs: list[float], residuals: list[float]) -> float:
    if len(xs) < 2:
        return 1.0
    squared = [value**2 for value in residuals]
    intercept, slope = _ols_fit(
        [{"delta_small": x_value, "delta_frontier": y_value} for x_value, y_value in zip(xs, squared)]
    )
    fitted = [intercept + (slope * value) for value in xs]
    mean_squared = _mean(squared)
    denominator = sum((value - mean_squared) ** 2 for value in squared)
    if denominator == 0:
        return 1.0
    r_squared = 1.0 - (
        sum((observed - estimated) ** 2 for observed, estimated in zip(squared, fitted)) / denominator
    )
    lm = max(0.0, len(xs) * r_squared)
    return math.erfc(math.sqrt(lm / 2.0))


def _icc_by_question(rows: list[dict[str, Any]], residuals: list[float]) -> float:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row, residual in zip(rows, residuals):
        grouped[str(row["question_id"])].append(residual)
    if len(grouped) < 2:
        return 0.0

    all_values = [residual for values in grouped.values() for residual in values]
    grand_mean = _mean(all_values)
    group_sizes = [len(values) for values in grouped.values()]
    ss_between = sum(len(values) * (_mean(values) - grand_mean) ** 2 for values in grouped.values())
    ss_within = sum(sum((value - _mean(values)) ** 2 for value in values) for values in grouped.values())
    df_between = len(grouped) - 1
    df_within = len(all_values) - len(grouped)
    if df_between <= 0 or df_within <= 0:
        return 0.0
    ms_between = ss_between / df_between
    ms_within = ss_within / df_within
    n_total = sum(group_sizes)
    n_bar = (n_total - (sum(size**2 for size in group_sizes) / n_total)) / df_between
    denominator = ms_between + ((n_bar - 1.0) * ms_within)
    if denominator == 0:
        return 0.0
    return (ms_between - ms_within) / denominator


def _bootstrap_coefficients(
    rows: list[dict[str, Any]],
    *,
    seed: int,
    bootstrap_resamples: int,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["question_id"])].append(row)
    question_ids = sorted(grouped)
    if not question_ids:
        return {
            "intercept_ci": [0.0, 0.0],
            "slope_ci": [0.0, 0.0],
            "intercept_variance": 0.0,
            "slope_variance": 0.0,
        }

    rng = random.Random(seed)
    intercepts: list[float] = []
    slopes: list[float] = []
    for _ in range(bootstrap_resamples):
        sampled_rows: list[dict[str, Any]] = []
        sampled_questions = [rng.choice(question_ids) for _ in question_ids]
        for question_id in sampled_questions:
            sampled_rows.extend(grouped[question_id])
        intercept, slope = _ols_fit(sampled_rows)
        intercepts.append(intercept)
        slopes.append(slope)

    return {
        "intercept_ci": [_quantile(intercepts, 0.025), _quantile(intercepts, 0.975)],
        "slope_ci": [_quantile(slopes, 0.025), _quantile(slopes, 0.975)],
        "intercept_variance": _sample_variance(intercepts),
        "slope_variance": _sample_variance(slopes),
    }


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    augmented = [row[:] + [value] for row, value in zip(matrix, vector)]
    for pivot_index in range(size):
        pivot_row = max(range(pivot_index, size), key=lambda idx: abs(augmented[idx][pivot_index]))
        pivot_value = augmented[pivot_row][pivot_index]
        if abs(pivot_value) < 1e-12:
            raise ValueError("singular matrix")
        if pivot_row != pivot_index:
            augmented[pivot_index], augmented[pivot_row] = augmented[pivot_row], augmented[pivot_index]

        normalized = augmented[pivot_index][pivot_index]
        augmented[pivot_index] = [value / normalized for value in augmented[pivot_index]]
        for row_index in range(size):
            if row_index == pivot_index:
                continue
            factor = augmented[row_index][pivot_index]
            augmented[row_index] = [
                current - (factor * pivot)
                for current, pivot in zip(augmented[row_index], augmented[pivot_index])
            ]
    return [augmented[index][-1] for index in range(size)]


def _quadratic_fit(rows: list[dict[str, Any]]) -> tuple[float, float, float]:
    xs = [float(row["delta_small"]) for row in rows]
    ys = [float(row["delta_frontier"]) for row in rows]
    if len({round(value, 12) for value in xs}) < 3:
        intercept, slope = _ols_fit(rows)
        return intercept, slope, 0.0

    sums = {
        "n": float(len(xs)),
        "x": sum(xs),
        "x2": sum(value**2 for value in xs),
        "x3": sum(value**3 for value in xs),
        "x4": sum(value**4 for value in xs),
        "y": sum(ys),
        "xy": sum(x * y for x, y in zip(xs, ys)),
        "x2y": sum((x**2) * y for x, y in zip(xs, ys)),
    }
    matrix = [
        [sums["n"], sums["x"], sums["x2"]],
        [sums["x"], sums["x2"], sums["x3"]],
        [sums["x2"], sums["x3"], sums["x4"]],
    ]
    vector = [sums["y"], sums["xy"], sums["x2y"]]
    try:
        intercept, slope, quadratic = _solve_linear_system(matrix, vector)
    except ValueError:
        intercept, slope = _ols_fit(rows)
        quadratic = 0.0
    return intercept, slope, quadratic


def _group_duplicate_xs(rows: list[dict[str, Any]]) -> tuple[list[float], list[float], list[float]]:
    grouped: dict[float, list[float]] = defaultdict(list)
    for row in rows:
        grouped[float(row["delta_small"])].append(float(row["delta_frontier"]))
    ordered_xs = sorted(grouped)
    ys = [_mean(grouped[x_value]) for x_value in ordered_xs]
    weights = [float(len(grouped[x_value])) for x_value in ordered_xs]
    return ordered_xs, ys, weights


def _pava(values: list[float], weights: list[float]) -> list[float]:
    blocks: list[dict[str, Any]] = []
    for index, (value, weight) in enumerate(zip(values, weights)):
        blocks.append(
            {
                "start": index,
                "end": index,
                "weight": float(weight),
                "value": float(value),
            }
        )
        while len(blocks) >= 2 and blocks[-2]["value"] > blocks[-1]["value"]:
            right = blocks.pop()
            left = blocks.pop()
            merged_weight = left["weight"] + right["weight"]
            merged_value = (
                (left["value"] * left["weight"]) + (right["value"] * right["weight"])
            ) / merged_weight
            blocks.append(
                {
                    "start": left["start"],
                    "end": right["end"],
                    "weight": merged_weight,
                    "value": merged_value,
                }
            )

    fitted = [0.0] * len(values)
    for block in blocks:
        for index in range(block["start"], block["end"] + 1):
            fitted[index] = float(block["value"])
    return fitted


def _build_piecewise_predictor(xs: list[float], ys: list[float]) -> Callable[[float], float]:
    if not xs:
        return lambda _value: 0.0
    if len(xs) == 1:
        return lambda _value, constant=ys[0]: float(constant)

    def _predict(x_value: float) -> float:
        if x_value <= xs[0]:
            return float(ys[0])
        if x_value >= xs[-1]:
            return float(ys[-1])
        right_index = bisect_right(xs, x_value)
        left_index = max(0, right_index - 1)
        right_index = min(len(xs) - 1, right_index)
        if xs[right_index] == xs[left_index]:
            return float(ys[right_index])
        ratio = (x_value - xs[left_index]) / (xs[right_index] - xs[left_index])
        return float(ys[left_index] + ((ys[right_index] - ys[left_index]) * ratio))

    return _predict


def _fit_isotonic(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], Callable[[float], float]]:
    xs, ys, weights = _group_duplicate_xs(rows)
    fitted = _pava(ys, weights)
    return {
        "breakpoints_x": xs,
        "breakpoints_y": fitted,
        "monotonic_direction": "increasing",
    }, _build_piecewise_predictor(xs, fitted)


def _load_snapshot_rows(measurement_dir: str | Path, model_role: str) -> list[dict[str, Any]]:
    root = Path(measurement_dir) / "questions" / model_role
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for entry in payload.get("delta_loo_LCB", []):
            rows.append(
                {
                    "question_id": payload["question_id"],
                    "hop_depth": payload["hop_depth"],
                    "paragraph_id": int(entry["paragraph_id"]),
                    "delta_loo": float(entry["delta_loo"]),
                    "model_role": model_role,
                }
            )
    return rows


def _build_hop_summary(
    *,
    rows: list[dict[str, Any]],
    coefficients: dict[str, Any],
    predictor: Callable[[float], float],
    bridge_coefficient_variance: dict[str, float],
) -> dict[str, Any]:
    xs = [float(row["delta_small"]) for row in rows]
    frontier_values = [float(row["delta_frontier"]) for row in rows]
    fitted = [predictor(value) for value in xs]
    residuals = [frontier - estimate for frontier, estimate in zip(frontier_values, fitted)]
    sigma_calibration = _sample_std(frontier_values)
    mae_threshold = PASS_THRESHOLDS["mae_to_sigma_ratio"] * sigma_calibration
    consistency = {
        "pearson_r": _pearson(xs, frontier_values),
        "mae": _mean([abs(value) for value in residuals]),
        "rmse": math.sqrt(_mean([value**2 for value in residuals])) if residuals else 0.0,
        "sigma_calibration": sigma_calibration,
        "mae_threshold": mae_threshold,
    }
    diagnostics = {
        "normality_test": "shapiro_wilk",
        "normality_pvalue": _shapiro_wilk_pvalue(residuals),
        "breusch_pagan_pvalue": _breusch_pagan_pvalue(xs, residuals),
        "icc_question_residual": _icc_by_question(rows, residuals),
    }
    pass_flags = {
        "normality_pass": diagnostics["normality_pvalue"] > PASS_THRESHOLDS["normality_pvalue"],
        "breusch_pagan_pass": (
            diagnostics["breusch_pagan_pvalue"] > PASS_THRESHOLDS["breusch_pagan_pvalue"]
        ),
        "icc_pass": diagnostics["icc_question_residual"] < PASS_THRESHOLDS["icc_question_residual"],
        "pearson_pass": consistency["pearson_r"] >= PASS_THRESHOLDS["pearson_r"],
        "mae_pass": consistency["mae"] <= mae_threshold,
    }
    pass_flags["diagnostic_triplet_pass"] = (
        pass_flags["normality_pass"]
        and pass_flags["breusch_pagan_pass"]
        and pass_flags["icc_pass"]
    )

    return {
        "coefficients": coefficients,
        "calibration": {
            "question_count": len({row["question_id"] for row in rows}),
            "row_count": len(rows),
        },
        "consistency": consistency,
        "diagnostics": diagnostics,
        "bridge_coefficient_variance": bridge_coefficient_variance,
        "pass_flags": pass_flags,
    }


def _fit_linear_per_hop(
    calibration_rows: list[dict[str, Any]],
    *,
    seed: int,
    bootstrap_resamples: int,
) -> tuple[dict[str, Any], dict[str, Callable[[float], float]]]:
    per_hop: dict[str, Any] = {}
    predictors: dict[str, Callable[[float], float]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in calibration_rows:
        grouped[str(row["hop_depth"])].append(row)

    for hop_depth, rows in grouped.items():
        intercept, slope = _ols_fit(rows)
        bootstrap = _bootstrap_coefficients(
            rows,
            seed=seed + sum(ord(char) for char in hop_depth),
            bootstrap_resamples=bootstrap_resamples,
        )
        predictors[hop_depth] = lambda value, base=intercept, gain=slope: base + (gain * value)
        per_hop[hop_depth] = _build_hop_summary(
            rows=rows,
            coefficients={
                "intercept": intercept,
                "slope": slope,
                "intercept_ci": bootstrap["intercept_ci"],
                "slope_ci": bootstrap["slope_ci"],
            },
            predictor=predictors[hop_depth],
            bridge_coefficient_variance={
                "intercept": bootstrap["intercept_variance"],
                "slope": bootstrap["slope_variance"],
                "quadratic": 0.0,
            },
        )
    return per_hop, predictors


def _fit_isotonic_per_hop(
    calibration_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Callable[[float], float]]]:
    per_hop: dict[str, Any] = {}
    predictors: dict[str, Callable[[float], float]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in calibration_rows:
        grouped[str(row["hop_depth"])].append(row)

    for hop_depth, rows in grouped.items():
        coefficients, predictor = _fit_isotonic(rows)
        predictors[hop_depth] = predictor
        per_hop[hop_depth] = _build_hop_summary(
            rows=rows,
            coefficients=coefficients,
            predictor=predictor,
            bridge_coefficient_variance={
                "intercept": 0.0,
                "slope": 0.0,
                "quadratic": 0.0,
            },
        )
    return per_hop, predictors


def _fit_quadratic_per_hop(
    calibration_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Callable[[float], float]]]:
    per_hop: dict[str, Any] = {}
    predictors: dict[str, Callable[[float], float]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in calibration_rows:
        grouped[str(row["hop_depth"])].append(row)

    for hop_depth, rows in grouped.items():
        intercept, slope, quadratic = _quadratic_fit(rows)
        predictors[hop_depth] = (
            lambda value, a0=intercept, a1=slope, a2=quadratic: a0 + (a1 * value) + (a2 * value * value)
        )
        per_hop[hop_depth] = _build_hop_summary(
            rows=rows,
            coefficients={
                "intercept": intercept,
                "slope": slope,
                "quadratic": quadratic,
            },
            predictor=predictors[hop_depth],
            bridge_coefficient_variance={
                "intercept": 0.0,
                "slope": 0.0,
                "quadratic": 0.0,
            },
        )
    return per_hop, predictors


def _apply_bridge(
    *,
    small_rows: list[dict[str, Any]],
    frontier_rows: list[dict[str, Any]],
    calibration_question_ids: set[str],
    predictors: dict[str, Callable[[float], float]],
    bridge_form: str,
) -> list[dict[str, Any]]:
    frontier_lookup = {
        (row["question_id"], row["paragraph_id"]): float(row["delta_loo"]) for row in frontier_rows
    }
    bridged_rows: list[dict[str, Any]] = []
    for row in small_rows:
        predictor = predictors[str(row["hop_depth"])]
        bridged = predictor(float(row["delta_loo"]))
        key = (row["question_id"], row["paragraph_id"])
        direct_frontier = frontier_lookup.get(key)
        frontier_equivalent = direct_frontier if direct_frontier is not None else bridged
        bridged_rows.append(
            {
                "question_id": row["question_id"],
                "hop_depth": row["hop_depth"],
                "paragraph_id": row["paragraph_id"],
                "delta_small": float(row["delta_loo"]),
                "delta_frontier_direct": direct_frontier,
                "delta_loo_bridged": bridged,
                "delta_loo_frontier_equivalent": frontier_equivalent,
                "bridge_source": "direct_frontier" if row["question_id"] in calibration_question_ids else "bridged_small",
                "calibration_member": row["question_id"] in calibration_question_ids,
                "bridge_form": bridge_form,
            }
        )
    return bridged_rows


def _compute_tolerance_band(bridged_rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in bridged_rows:
        grouped[str(row["hop_depth"])].append(row)

    per_hop: dict[str, Any] = {}
    for hop_depth, rows in grouped.items():
        values = [float(row["delta_loo_frontier_equivalent"]) for row in rows]
        lower_cut = _quantile(values, 1 / 3)
        upper_cut = _quantile(values, 2 / 3)
        sigma = _sample_std(values)
        lower_band = [lower_cut - (0.5 * sigma), lower_cut + (0.5 * sigma)]
        upper_band = [upper_cut - (0.5 * sigma), upper_cut + (0.5 * sigma)]
        flagged_instances: list[dict[str, Any]] = []
        label_counts = {"HIGH": 0, "LOW": 0, "BUFFER": 0}

        for row in rows:
            value = float(row["delta_loo_frontier_equivalent"])
            if value < lower_cut:
                label = "LOW"
            elif value > upper_cut:
                label = "HIGH"
            else:
                label = "BUFFER"
            label_counts[label] += 1

            flagged = (lower_band[0] <= value <= lower_band[1]) or (upper_band[0] <= value <= upper_band[1])
            if flagged:
                flagged_instances.append(
                    {
                        "question_id": row["question_id"],
                        "paragraph_id": row["paragraph_id"],
                        "delta_loo_frontier_equivalent": value,
                        "automated_label": label,
                    }
                )
            row["automated_label"] = label
            row["tolerance_flagged"] = flagged

        per_hop[hop_depth] = {
            "lower_cut": lower_cut,
            "upper_cut": upper_cut,
            "sigma": sigma,
            "lower_band": lower_band,
            "upper_band": upper_band,
            "counts": {
                "total": len(rows),
                "flagged": len(flagged_instances),
                "high": label_counts["HIGH"],
                "low": label_counts["LOW"],
                "buffer": label_counts["BUFFER"],
            },
            "flagged_instances": flagged_instances,
        }
    return {
        "status": "computed",
        "band_width_sigma_multiplier": 0.5,
        "per_hop": per_hop,
    }


def _pooled_overlap_summary(
    calibration_rows: list[dict[str, Any]],
    predictors: dict[str, Callable[[float], float]],
) -> dict[str, Any]:
    xs = [float(row["delta_small"]) for row in calibration_rows]
    ys = [float(row["delta_frontier"]) for row in calibration_rows]
    fitted = [predictors[str(row["hop_depth"])](float(row["delta_small"])) for row in calibration_rows]
    residuals = [frontier - estimate for frontier, estimate in zip(ys, fitted)]
    sigma_calibration = _sample_std(ys)
    mae_threshold = PASS_THRESHOLDS["mae_to_sigma_ratio"] * sigma_calibration
    pearson_r = _pearson(fitted, ys)
    mae = _mean([abs(value) for value in residuals])
    return {
        "pearson_r": pearson_r,
        "mae": mae,
        "sigma_calibration": sigma_calibration,
        "mae_threshold": mae_threshold,
        "pearson_pass": pearson_r >= PASS_THRESHOLDS["pearson_r"],
        "mae_pass": mae <= mae_threshold,
    }


def _evaluate_candidate(
    *,
    bridge_form: str,
    per_hop: dict[str, Any],
    calibration_rows: list[dict[str, Any]],
    predictors: dict[str, Callable[[float], float]],
) -> dict[str, Any]:
    diagnostic_pass_count = sum(
        1 for payload in per_hop.values() if payload["pass_flags"]["diagnostic_triplet_pass"]
    )
    required_diagnostic_passes = min(2, len(per_hop))
    pooled_consistency = _pooled_overlap_summary(calibration_rows, predictors)

    failure_reasons: list[str] = []
    if diagnostic_pass_count < required_diagnostic_passes:
        failure_reasons.append(
            f"diagnostic_triplet_pass count {diagnostic_pass_count} < required {required_diagnostic_passes}"
        )
    if not pooled_consistency["pearson_pass"]:
        failure_reasons.append(
            f"pooled Pearson r {pooled_consistency['pearson_r']:.4f} < {PASS_THRESHOLDS['pearson_r']}"
        )
    if not pooled_consistency["mae_pass"]:
        failure_reasons.append(
            "pooled MAE "
            f"{pooled_consistency['mae']:.4f} > threshold {pooled_consistency['mae_threshold']:.4f}"
        )

    overall_pass = not failure_reasons
    return {
        "bridge_form": bridge_form,
        "pass_fail": "pass" if overall_pass else "fail",
        "diagnostic_pass_count": diagnostic_pass_count,
        "required_diagnostic_passes": required_diagnostic_passes,
        "pooled_consistency": pooled_consistency,
        "failure_reasons": failure_reasons,
        "recommended_next_action": (
            "proceed_with_bridge_outputs"
            if overall_pass
            else "escalate_to_next_bridge_form"
        ),
    }


def _build_candidate(
    *,
    bridge_form: str,
    calibration_rows: list[dict[str, Any]],
    small_rows: list[dict[str, Any]],
    frontier_rows: list[dict[str, Any]],
    calibration_question_ids: set[str],
    seed: int,
    bootstrap_resamples: int,
) -> dict[str, Any]:
    if bridge_form == "linear_ols":
        per_hop, predictors = _fit_linear_per_hop(
            calibration_rows,
            seed=seed,
            bootstrap_resamples=bootstrap_resamples,
        )
    elif bridge_form == "isotonic":
        per_hop, predictors = _fit_isotonic_per_hop(calibration_rows)
    elif bridge_form == "polynomial_quadratic":
        per_hop, predictors = _fit_quadratic_per_hop(calibration_rows)
    else:
        raise ValueError(f"Unsupported bridge form: {bridge_form}")

    bridged_rows = _apply_bridge(
        small_rows=small_rows,
        frontier_rows=frontier_rows,
        calibration_question_ids=calibration_question_ids,
        predictors=predictors,
        bridge_form=bridge_form,
    )
    tolerance_payload = _compute_tolerance_band(bridged_rows)
    evaluation = _evaluate_candidate(
        bridge_form=bridge_form,
        per_hop=per_hop,
        calibration_rows=calibration_rows,
        predictors=predictors,
    )
    return {
        "bridge_form": bridge_form,
        "per_hop": per_hop,
        "bridged_rows": bridged_rows,
        "tolerance_payload": tolerance_payload,
        "evaluation": evaluation,
    }


def _pending_bridge_exports(
    *,
    export_root: Path,
    reason: str,
) -> dict[str, Any]:
    diagnostics_path = write_json(
        export_root / "bridge_diagnostics.json",
        {
            "status": "pending_measurement_consumption",
            "reason": reason,
            "diagnostic_scope": DIAGNOSTIC_SCOPE,
            "bridge_escalation_sequence": list(BRIDGE_ESCALATION_SEQUENCE),
        },
    )
    tolerance_path = write_json(
        export_root / "tolerance_band.json",
        {
            "status": "pending_measurement_consumption",
            "reason": reason,
        },
    )
    variance_path = write_json(
        export_root / "variance_bias_budget.json",
        {
            "status": "pending_measurement_consumption",
            "reason": reason,
        },
    )
    return {
        "status": "pending_measurement_consumption",
        "bridge_diagnostics": str(diagnostics_path),
        "tolerance_band": str(tolerance_path),
        "variance_bias_budget": str(variance_path),
        "bridged_delta_loo_jsonl": "",
        "bridged_delta_loo_csv": "",
    }


def run_bridge_analysis(
    *,
    measurement_dir: str | Path,
    export_dir: str | Path,
    calibration_manifest_path: str | Path,
    seed: int,
    bootstrap_resamples: int = 1000,
) -> dict[str, Any]:
    export_root = Path(export_dir)
    calibration_payload = json.loads(Path(calibration_manifest_path).read_text(encoding="utf-8"))
    calibration_question_ids = {
        str(entry["question_id"]) for entry in calibration_payload.get("selected_questions", [])
    }

    small_rows = _load_snapshot_rows(measurement_dir, "small")
    frontier_rows = _load_snapshot_rows(measurement_dir, "frontier")
    if not small_rows or not frontier_rows or not calibration_question_ids:
        return _pending_bridge_exports(
            export_root=export_root,
            reason="small/frontier snapshots or calibration manifest are incomplete",
        )

    small_lookup = {
        (row["question_id"], row["paragraph_id"]): row for row in small_rows if row["question_id"] in calibration_question_ids
    }
    frontier_lookup = {
        (row["question_id"], row["paragraph_id"]): row for row in frontier_rows if row["question_id"] in calibration_question_ids
    }
    shared_keys = sorted(set(small_lookup) & set(frontier_lookup))
    calibration_rows = [
        {
            "question_id": key[0],
            "paragraph_id": key[1],
            "hop_depth": small_lookup[key]["hop_depth"],
            "delta_small": float(small_lookup[key]["delta_loo"]),
            "delta_frontier": float(frontier_lookup[key]["delta_loo"]),
        }
        for key in shared_keys
    ]
    if not calibration_rows:
        return _pending_bridge_exports(
            export_root=export_root,
            reason="no overlapping calibration rows between small and frontier snapshots",
        )

    attempts: list[dict[str, Any]] = []
    selected_candidate: dict[str, Any] | None = None
    for bridge_form in BRIDGE_ESCALATION_SEQUENCE[:-1]:
        candidate = _build_candidate(
            bridge_form=bridge_form,
            calibration_rows=calibration_rows,
            small_rows=small_rows,
            frontier_rows=frontier_rows,
            calibration_question_ids=calibration_question_ids,
            seed=seed,
            bootstrap_resamples=bootstrap_resamples,
        )
        attempts.append(candidate)
        if candidate["evaluation"]["pass_fail"] == "pass":
            selected_candidate = candidate
            break

    final_status = "computed"
    selected_bridge_form = selected_candidate["bridge_form"] if selected_candidate else "frontier_full_n_required"
    diagnostics_pass_fail = "pass"
    escalation_reason = ""
    recommended_next_action = "proceed_with_bridge_outputs"
    export_candidate = selected_candidate or attempts[-1]
    if selected_candidate is None:
        final_status = "frontier_full_n_required"
        diagnostics_pass_fail = "fail"
        escalation_reason = (
            "All configured bridge forms failed pass criteria; "
            f"last attempted form was {export_candidate['bridge_form']}"
        )
        recommended_next_action = "execute_v_frontier_on_full_n"
        export_candidate["tolerance_payload"]["status"] = "provisional_bridge_only"
        export_candidate["tolerance_payload"]["recommended_next_action"] = recommended_next_action
    elif selected_candidate["bridge_form"] == "linear_ols":
        escalation_reason = "linear_ols satisfied the bridge pass criteria"
    else:
        escalation_reason = (
            f"linear_ols failed pass criteria, escalated to {selected_candidate['bridge_form']}"
        )

    diagnostics_payload = {
        "status": final_status,
        "bridge_form": selected_bridge_form,
        "diagnostic_scope": DIAGNOSTIC_SCOPE,
        "calibration_manifest_path": str(Path(calibration_manifest_path).resolve()),
        "bootstrap_resamples": bootstrap_resamples,
        "pass_fail": diagnostics_pass_fail,
        "escalation_reason": escalation_reason,
        "recommended_next_action": recommended_next_action,
        "bridge_escalation_sequence": list(BRIDGE_ESCALATION_SEQUENCE),
        "pass_criteria": {
            "normality_pvalue_gt": PASS_THRESHOLDS["normality_pvalue"],
            "breusch_pagan_pvalue_gt": PASS_THRESHOLDS["breusch_pagan_pvalue"],
            "icc_question_residual_lt": PASS_THRESHOLDS["icc_question_residual"],
            "diagnostic_triplet_passes_required": min(2, len(export_candidate["per_hop"])),
            "pooled_pearson_r_gte": PASS_THRESHOLDS["pearson_r"],
            "pooled_mae_lte_ratio_sigma": PASS_THRESHOLDS["mae_to_sigma_ratio"],
        },
        "selected_candidate_form": export_candidate["bridge_form"],
        "candidate_evaluations": [
            {
                "bridge_form": candidate["bridge_form"],
                **candidate["evaluation"],
            }
            for candidate in attempts
        ],
        "per_hop": export_candidate["per_hop"],
        "pooled_overlap": export_candidate["evaluation"]["pooled_consistency"],
    }
    variance_payload = {
        "status": final_status,
        "bridge_status": final_status,
        "bridge_form": selected_bridge_form,
        "pass_fail": diagnostics_pass_fail,
        "escalation_reason": escalation_reason,
        "recommended_next_action": recommended_next_action,
        "calibration_manifest_path": str(Path(calibration_manifest_path).resolve()),
        "per_hop": {
            hop_depth: {
                "sigma_stratum": export_candidate["tolerance_payload"]["per_hop"][hop_depth]["sigma"],
                "bridge_coefficient_variance": diagnostics["bridge_coefficient_variance"],
                "calibration_consistency": diagnostics["consistency"],
                "annotation_reliability": {
                    "status": "pending_annotation",
                    "reason": "annotation disagreement rates populate after annotation and kappa ingestion",
                },
            }
            for hop_depth, diagnostics in export_candidate["per_hop"].items()
        },
    }

    bridged_jsonl_path = write_jsonl(export_root / "bridged_delta_loo.jsonl", export_candidate["bridged_rows"])
    bridged_csv_path = write_csv(
        export_root / "bridged_delta_loo.csv",
        export_candidate["bridged_rows"],
        [
            "question_id",
            "hop_depth",
            "paragraph_id",
            "delta_small",
            "delta_frontier_direct",
            "delta_loo_bridged",
            "delta_loo_frontier_equivalent",
            "bridge_source",
            "calibration_member",
            "bridge_form",
            "automated_label",
            "tolerance_flagged",
        ],
    )
    diagnostics_path = write_json(export_root / "bridge_diagnostics.json", diagnostics_payload)
    tolerance_path = write_json(export_root / "tolerance_band.json", export_candidate["tolerance_payload"])
    variance_path = write_json(export_root / "variance_bias_budget.json", variance_payload)

    return {
        "status": final_status,
        "bridge_diagnostics": str(diagnostics_path),
        "bridged_delta_loo_jsonl": str(bridged_jsonl_path),
        "bridged_delta_loo_csv": str(bridged_csv_path),
        "tolerance_band": str(tolerance_path),
        "variance_bias_budget": str(variance_path),
    }
