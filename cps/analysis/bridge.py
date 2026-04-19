from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from cps.analysis.exports import write_csv, write_json, write_jsonl


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


def _jarque_bera_pvalue(residuals: list[float]) -> float:
    n = len(residuals)
    if n < 3:
        return 1.0
    sigma = _sample_std(residuals)
    if sigma == 0:
        return 1.0
    centered = [(value - _mean(residuals)) / sigma for value in residuals]
    skew = sum(value**3 for value in centered) / n
    kurtosis = sum(value**4 for value in centered) / n
    jb = (n / 6.0) * (skew**2 + ((kurtosis - 3.0) ** 2) / 4.0)
    return math.exp(-jb / 2.0)


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


def _fit_per_hop(calibration_rows: list[dict[str, Any]], *, seed: int, bootstrap_resamples: int) -> dict[str, Any]:
    per_hop: dict[str, Any] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in calibration_rows:
        grouped[str(row["hop_depth"])].append(row)

    for hop_depth, rows in grouped.items():
        intercept, slope = _ols_fit(rows)
        fitted = [intercept + (slope * row["delta_small"]) for row in rows]
        frontier_values = [float(row["delta_frontier"]) for row in rows]
        residuals = [frontier - estimate for frontier, estimate in zip(frontier_values, fitted)]
        sigma_calibration = _sample_std(frontier_values)
        bootstrap = _bootstrap_coefficients(
            rows,
            seed=seed + sum(ord(char) for char in hop_depth),
            bootstrap_resamples=bootstrap_resamples,
        )
        per_hop[hop_depth] = {
            "coefficients": {
                "intercept": intercept,
                "slope": slope,
                "intercept_ci": bootstrap["intercept_ci"],
                "slope_ci": bootstrap["slope_ci"],
            },
            "calibration": {
                "question_count": len({row["question_id"] for row in rows}),
                "row_count": len(rows),
            },
            "consistency": {
                "pearson_r": _pearson(
                    [float(row["delta_small"]) for row in rows],
                    frontier_values,
                ),
                "mae": _mean([abs(value) for value in residuals]),
                "rmse": math.sqrt(_mean([value**2 for value in residuals])) if residuals else 0.0,
                "sigma_calibration": sigma_calibration,
                "mae_threshold": 0.5 * sigma_calibration,
            },
            "diagnostics": {
                "normality_test": "jarque_bera_proxy_without_scipy",
                "normality_pvalue": _jarque_bera_pvalue(residuals),
                "breusch_pagan_pvalue": _breusch_pagan_pvalue(
                    [float(row["delta_small"]) for row in rows],
                    residuals,
                ),
                "icc_question_residual": _icc_by_question(rows, residuals),
            },
            "bridge_coefficient_variance": {
                "intercept": bootstrap["intercept_variance"],
                "slope": bootstrap["slope_variance"],
            },
        }
    return per_hop


def _apply_bridge(
    *,
    small_rows: list[dict[str, Any]],
    frontier_rows: list[dict[str, Any]],
    calibration_question_ids: set[str],
    coefficients: dict[str, Any],
) -> list[dict[str, Any]]:
    frontier_lookup = {
        (row["question_id"], row["paragraph_id"]): float(row["delta_loo"]) for row in frontier_rows
    }
    bridged_rows: list[dict[str, Any]] = []
    for row in small_rows:
        hop_coefficients = coefficients[str(row["hop_depth"])]["coefficients"]
        bridged = hop_coefficients["intercept"] + (hop_coefficients["slope"] * float(row["delta_loo"]))
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
        diagnostics_path = write_json(
            export_root / "bridge_diagnostics.json",
            {
                "status": "pending_measurement_consumption",
                "reason": "small/frontier snapshots or calibration manifest are incomplete",
            },
        )
        tolerance_path = write_json(
            export_root / "tolerance_band.json",
            {
                "status": "pending_measurement_consumption",
                "reason": "bridge output is incomplete",
            },
        )
        variance_path = write_json(
            export_root / "variance_bias_budget.json",
            {
                "status": "pending_measurement_consumption",
                "reason": "bridge output is incomplete",
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
        diagnostics_path = write_json(
            export_root / "bridge_diagnostics.json",
            {
                "status": "pending_measurement_consumption",
                "reason": "no overlapping calibration rows between small and frontier snapshots",
            },
        )
        tolerance_path = write_json(
            export_root / "tolerance_band.json",
            {
                "status": "pending_measurement_consumption",
                "reason": "no overlapping calibration rows between small and frontier snapshots",
            },
        )
        variance_path = write_json(
            export_root / "variance_bias_budget.json",
            {
                "status": "pending_measurement_consumption",
                "reason": "no overlapping calibration rows between small and frontier snapshots",
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

    coefficients = _fit_per_hop(
        calibration_rows,
        seed=seed,
        bootstrap_resamples=bootstrap_resamples,
    )
    bridged_rows = _apply_bridge(
        small_rows=small_rows,
        frontier_rows=frontier_rows,
        calibration_question_ids=calibration_question_ids,
        coefficients=coefficients,
    )
    tolerance_payload = _compute_tolerance_band(bridged_rows)

    diagnostics_payload = {
        "status": "computed",
        "bridge_form": "linear_ols",
        "diagnostic_scope": "pure_python_without_scipy",
        "calibration_manifest_path": str(Path(calibration_manifest_path).resolve()),
        "bootstrap_resamples": bootstrap_resamples,
        "per_hop": coefficients,
    }
    variance_payload = {
        "status": "computed",
        "calibration_manifest_path": str(Path(calibration_manifest_path).resolve()),
        "per_hop": {
            hop_depth: {
                "sigma_stratum": tolerance_payload["per_hop"][hop_depth]["sigma"],
                "bridge_coefficient_variance": diagnostics["bridge_coefficient_variance"],
                "calibration_consistency": diagnostics["consistency"],
                "note": "annotation disagreement rates remain pending until kappa/annotation wiring",
            }
            for hop_depth, diagnostics in coefficients.items()
        },
    }

    bridged_jsonl_path = write_jsonl(export_root / "bridged_delta_loo.jsonl", bridged_rows)
    bridged_csv_path = write_csv(
        export_root / "bridged_delta_loo.csv",
        bridged_rows,
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
            "automated_label",
            "tolerance_flagged",
        ],
    )
    diagnostics_path = write_json(export_root / "bridge_diagnostics.json", diagnostics_payload)
    tolerance_path = write_json(export_root / "tolerance_band.json", tolerance_payload)
    variance_path = write_json(export_root / "variance_bias_budget.json", variance_payload)

    return {
        "status": "computed",
        "bridge_diagnostics": str(diagnostics_path),
        "bridged_delta_loo_jsonl": str(bridged_jsonl_path),
        "bridged_delta_loo_csv": str(bridged_csv_path),
        "tolerance_band": str(tolerance_path),
        "variance_bias_budget": str(variance_path),
    }
