from __future__ import annotations

import argparse
import csv
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


class BridgeCalibrationValidationError(ValueError):
    """Raised when bridge calibration input cannot be trusted."""


REQUIRED_FIELDS = (
    "pair_id",
    "stratum_id",
    "task_family",
    "model_tier",
    "materialization_policy",
    "metric",
    "block_size",
    "candidate_slice_band",
    "context_id",
    "block_id",
    "delta_utility",
    "delta_logloss",
    "replicate_count",
    "source",
    "notes",
)
NON_EMPTY_STRING_FIELDS = (
    "pair_id",
    "stratum_id",
    "task_family",
    "model_tier",
    "materialization_policy",
    "metric",
    "candidate_slice_band",
    "context_id",
    "block_id",
    "source",
)
ALLOWED_SOURCES = ("fixture", "operator_provided", "replay")
OPTIONAL_PROVENANCE_FIELDS = (
    "data_origin",
    "delta_utility_source",
    "delta_logloss_source",
    "review_status",
    "bridge_signal_status",
    "bridge_fit_eligible",
    "evidence_strength_band",
    "utility_rationale",
)
OPTIONAL_NUMERIC_AUDIT_FIELDS = (
    "utility_without",
    "utility_with",
    "candidate_set_size_before",
    "candidate_set_size_after",
)
DENIED_CLAIMS = (
    "measurement_validated",
    "scientific_validation",
    "deployed_v_information_verification",
    "deployed_v_information_certification",
)
OUTPUT_ARTIFACTS = (
    "bridge_calibration_pairs.jsonl",
    "bridge_calibration_fit.json",
    "bridge_calibration_table.csv",
    "bridge_claim_gate_report.json",
    "report.md",
)
DEFAULT_CONFIG = {
    "experiment_id": "bridge_calibration_one_stratum_v1",
    "protocol_version": "bridge_calibration.v1",
    "input_file": "artifacts/fixtures/bridge_calibration_pairs_fixture.jsonl",
    "output_dir": "artifacts/experiments/bridge_calibration_one_stratum",
    "allow_multi_stratum": False,
    "fit_method": "ols_through_origin",
    "zeta_mode": "max",
    "zeta_quantile": 0.95,
    "minimum_sample_size": 6,
    "minimum_effective_sample_size": 6,
    "minimum_abs_delta_logloss_for_bridge_evidence": 0.001,
    "max_allowed_zeta": 0.05,
    "min_sign_agreement": 0.9,
    "min_pearson_correlation": 0.9,
    "min_spearman_correlation": 0.9,
    "evidence_scope": "one_stratum_bridge_calibration",
    "diagnostic_scope": "one_stratum_bridge_calibration",
    "selector_regime_label": "ambiguous",
    "bridge_freshness": "fresh",
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise BridgeCalibrationValidationError(f"config file does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BridgeCalibrationValidationError("config must be a JSON object")
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return path


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _finite_float(value: Any, field: str, row_label: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise BridgeCalibrationValidationError(f"{row_label}: {field} must be a finite number") from exc
    if not math.isfinite(parsed):
        raise BridgeCalibrationValidationError(f"{row_label}: {field} must be finite")
    return parsed


def _positive_int(value: Any, field: str, row_label: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise BridgeCalibrationValidationError(f"{row_label}: {field} must be a positive integer") from exc
    if parsed <= 0:
        raise BridgeCalibrationValidationError(f"{row_label}: {field} must be positive")
    return parsed


def _canonical_pair(raw: Mapping[str, Any], row_number: int) -> dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if field not in raw]
    row_label = f"row {row_number}"
    if missing:
        raise BridgeCalibrationValidationError(f"{row_label}: missing required fields: {', '.join(missing)}")

    for field in NON_EMPTY_STRING_FIELDS:
        if str(raw.get(field, "")).strip() == "":
            raise BridgeCalibrationValidationError(f"{row_label}: {field} must be non-empty")

    source = str(raw["source"]).strip()
    if source not in ALLOWED_SOURCES:
        raise BridgeCalibrationValidationError(
            f"{row_label}: source must be one of {', '.join(ALLOWED_SOURCES)}"
        )

    canonical = {
        "pair_id": str(raw["pair_id"]).strip(),
        "stratum_id": str(raw["stratum_id"]).strip(),
        "task_family": str(raw["task_family"]).strip(),
        "model_tier": str(raw["model_tier"]).strip(),
        "materialization_policy": str(raw["materialization_policy"]).strip(),
        "metric": str(raw["metric"]).strip(),
        "block_size": _positive_int(raw["block_size"], "block_size", row_label),
        "candidate_slice_band": str(raw["candidate_slice_band"]).strip(),
        "context_id": str(raw["context_id"]).strip(),
        "block_id": str(raw["block_id"]).strip(),
        "delta_utility": _finite_float(raw["delta_utility"], "delta_utility", row_label),
        "delta_logloss": _finite_float(raw["delta_logloss"], "delta_logloss", row_label),
        "replicate_count": _positive_int(raw["replicate_count"], "replicate_count", row_label),
        "source": source,
        "notes": str(raw.get("notes", "")),
    }
    for field in OPTIONAL_PROVENANCE_FIELDS:
        if field in raw and str(raw.get(field, "")).strip():
            canonical[field] = str(raw[field]).strip()
    for field in OPTIONAL_NUMERIC_AUDIT_FIELDS:
        if field in raw and str(raw.get(field, "")).strip():
            canonical[field] = _finite_float(raw[field], field, row_label)
    return canonical


def _load_pairs(input_path: Path) -> list[dict[str, Any]]:
    if not input_path.exists():
        raise BridgeCalibrationValidationError(f"input file does not exist: {input_path}")

    suffix = input_path.suffix.lower()
    rows: list[dict[str, Any]] = []
    if suffix == ".jsonl":
        for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            raw = json.loads(line)
            if not isinstance(raw, dict):
                raise BridgeCalibrationValidationError(f"row {line_number}: JSONL row must be an object")
            rows.append(_canonical_pair(raw, line_number))
    elif suffix == ".csv":
        with input_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for line_number, raw in enumerate(reader, start=2):
                rows.append(_canonical_pair(raw, line_number))
    else:
        raise BridgeCalibrationValidationError("input must be .jsonl or .csv")

    if not rows:
        raise BridgeCalibrationValidationError("input contains no calibration pairs")
    return sorted(rows, key=lambda row: (row["stratum_id"], row["pair_id"]))


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _quantile(values: Sequence[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * (position - lower))


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2:
        return None
    x_mean = _mean(xs)
    y_mean = _mean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = math.sqrt(
        sum((x - x_mean) ** 2 for x in xs) * sum((y - y_mean) ** 2 for y in ys)
    )
    if denominator == 0.0:
        return None
    return numerator / denominator


def _average_ranks(values: Sequence[float]) -> list[float]:
    ordered = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][0] == ordered[index][0]:
            end += 1
        average_rank = (index + 1 + end) / 2.0
        for _, original_index in ordered[index:end]:
            ranks[original_index] = average_rank
        index = end
    return ranks


def _spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2:
        return None
    return _pearson(_average_ranks(xs), _average_ranks(ys))


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _sign_agreement(rows: Sequence[Mapping[str, Any]]) -> float:
    if not rows:
        return 0.0
    matches = 0
    for row in rows:
        matches += int(_sign(float(row["delta_utility"])) == _sign(float(row["delta_logloss"])))
    return matches / len(rows)


def _through_origin_scale(rows: Sequence[Mapping[str, Any]]) -> float | None:
    numerator = sum(float(row["delta_logloss"]) * float(row["delta_utility"]) for row in rows)
    denominator = sum(float(row["delta_logloss"]) ** 2 for row in rows)
    if denominator == 0.0:
        return None
    return numerator / denominator


def _intercept_diagnostic(rows: Sequence[Mapping[str, Any]]) -> dict[str, float | None]:
    xs = [float(row["delta_logloss"]) for row in rows]
    ys = [float(row["delta_utility"]) for row in rows]
    if len(xs) < 2:
        return {"intercept": None, "slope": None, "mean_absolute_residual": None}
    x_mean = _mean(xs)
    y_mean = _mean(ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0.0:
        intercept = y_mean
        slope = 0.0
    else:
        slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator
        intercept = y_mean - (slope * x_mean)
    residuals = [abs(y - (intercept + (slope * x))) for x, y in zip(xs, ys)]
    return {
        "intercept": intercept,
        "slope": slope,
        "mean_absolute_residual": _mean(residuals),
    }


def _is_synthetic_scope(config: Mapping[str, Any]) -> bool:
    scopes = (
        str(config.get("evidence_scope") or ""),
        str(config.get("diagnostic_scope") or ""),
    )
    return any("synthetic" in scope for scope in scopes)


def _data_source_kind(rows: Sequence[Mapping[str, Any]]) -> str:
    sources = sorted({str(row["source"]) for row in rows})
    if len(sources) != 1:
        return "mixed"
    if sources[0] == "operator_provided":
        origins = sorted({str(row.get("data_origin") or "") for row in rows if row.get("data_origin")})
        if origins == ["api_generated"]:
            return "operator_provided_api_generated"
    return sources[0]


def _zeta(residuals: Sequence[float], config: Mapping[str, Any]) -> float:
    mode = str(config.get("zeta_mode", "max"))
    if mode == "max":
        return max(residuals) if residuals else 0.0
    if mode == "quantile":
        return _quantile(residuals, float(config.get("zeta_quantile", 0.95)))
    raise BridgeCalibrationValidationError("zeta_mode must be 'max' or 'quantile'")


def _threshold_config(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "minimum_sample_size": int(config.get("minimum_sample_size", DEFAULT_CONFIG["minimum_sample_size"])),
        "minimum_effective_sample_size": int(
            config.get("minimum_effective_sample_size", DEFAULT_CONFIG["minimum_effective_sample_size"])
        ),
        "minimum_abs_delta_logloss_for_bridge_evidence": float(
            config.get(
                "minimum_abs_delta_logloss_for_bridge_evidence",
                DEFAULT_CONFIG["minimum_abs_delta_logloss_for_bridge_evidence"],
            )
        ),
        "max_allowed_zeta": float(config.get("max_allowed_zeta", DEFAULT_CONFIG["max_allowed_zeta"])),
        "min_sign_agreement": float(config.get("min_sign_agreement", DEFAULT_CONFIG["min_sign_agreement"])),
        "min_pearson_correlation": float(
            config.get("min_pearson_correlation", DEFAULT_CONFIG["min_pearson_correlation"])
        ),
        "min_spearman_correlation": float(
            config.get("min_spearman_correlation", DEFAULT_CONFIG["min_spearman_correlation"])
        ),
        "zeta_mode": str(config.get("zeta_mode", DEFAULT_CONFIG["zeta_mode"])),
        "zeta_quantile": float(config.get("zeta_quantile", DEFAULT_CONFIG["zeta_quantile"])),
    }


def _bridge_signal_diagnostics(
    rows: Sequence[Mapping[str, Any]],
    *,
    minimum_abs_delta_logloss_for_bridge_evidence: float,
) -> dict[str, Any]:
    low_signal_pair_ids: list[str] = []
    negative_pair_ids: list[str] = []
    for row in rows:
        delta_logloss = float(row["delta_logloss"])
        pair_id = str(row["pair_id"])
        if abs(delta_logloss) < minimum_abs_delta_logloss_for_bridge_evidence:
            low_signal_pair_ids.append(pair_id)
        if delta_logloss < 0.0:
            negative_pair_ids.append(pair_id)
    return {
        "bridge_informative_delta_pair_count": len(rows) - len(low_signal_pair_ids),
        "low_signal_delta_logloss_count": len(low_signal_pair_ids),
        "low_signal_delta_logloss_pair_ids": low_signal_pair_ids,
        "negative_delta_logloss_count": len(negative_pair_ids),
        "negative_delta_logloss_pair_ids": negative_pair_ids,
    }


def _claim_from_gate(
    *,
    config: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    bridge_scale: float | None,
    zeta_s: float,
    sign_agreement: float,
    pearson: float | None,
    spearman: float | None,
    thresholds: Mapping[str, Any],
    signal_diagnostics: Mapping[str, Any],
) -> tuple[str, str, list[str], dict[str, bool]]:
    sample_size = len(rows)
    effective_sample_size = sum(int(row["replicate_count"]) for row in rows)
    stratum_ids = {str(row["stratum_id"]) for row in rows}
    allow_multi_stratum = _as_bool(config.get("allow_multi_stratum", False))
    source_kind = _data_source_kind(rows)
    reason_codes: list[str] = []
    pass_flags = {
        "one_stratum_pass": allow_multi_stratum or len(stratum_ids) == 1,
        "source_kind_pass": source_kind != "mixed",
        "sample_size_pass": sample_size >= int(thresholds["minimum_sample_size"]),
        "effective_sample_size_pass": effective_sample_size >= int(thresholds["minimum_effective_sample_size"]),
        "bridge_informative_delta_pass": int(signal_diagnostics["low_signal_delta_logloss_count"]) == 0,
        "fit_denominator_pass": bridge_scale is not None,
        "zeta_pass": zeta_s <= float(thresholds["max_allowed_zeta"]),
        "sign_agreement_pass": sign_agreement >= float(thresholds["min_sign_agreement"]),
        "pearson_pass": pearson is not None and pearson >= float(thresholds["min_pearson_correlation"]),
        "spearman_pass": spearman is not None and spearman >= float(thresholds["min_spearman_correlation"]),
        "synthetic_scope_pass": not _is_synthetic_scope(config),
        "bridge_freshness_pass": str(config.get("bridge_freshness", "fresh")) == "fresh",
    }

    for flag, passed in pass_flags.items():
        if not passed:
            reason_codes.append(flag.replace("_pass", "_failed"))

    ambiguous_failures = {
        "one_stratum_pass",
        "sample_size_pass",
        "effective_sample_size_pass",
        "fit_denominator_pass",
        "source_kind_pass",
        "synthetic_scope_pass",
        "bridge_freshness_pass",
    }
    if any(not pass_flags[name] for name in ambiguous_failures):
        claim = "ambiguous_metric"
        status = "failed_closed"
    elif all(pass_flags.values()):
        claim = "calibrated_proxy_supported"
        status = "calibrated_proxy_supported"
    else:
        claim = "operational_utility_only"
        status = "bridge_unsupported"

    if _is_synthetic_scope(config):
        reason_codes.append("synthetic_only_not_deployed_certification")
    if int(signal_diagnostics["low_signal_delta_logloss_count"]):
        reason_codes.append("low_delta_logloss_uninformative")
    return claim, status, sorted(set(reason_codes)), pass_flags


def _table_rows(
    rows: Sequence[Mapping[str, Any]],
    bridge_scale: float | None,
    *,
    minimum_abs_delta_logloss_for_bridge_evidence: float,
) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    for row in rows:
        fitted = None if bridge_scale is None else bridge_scale * float(row["delta_logloss"])
        residual = None if fitted is None else float(row["delta_utility"]) - fitted
        delta_logloss = float(row["delta_logloss"])
        table.append(
            {
                **dict(row),
                "bridge_signal_status": (
                    "bridge_uninformative"
                    if abs(delta_logloss) < minimum_abs_delta_logloss_for_bridge_evidence
                    else str(row.get("bridge_signal_status") or "bridge_informative")
                ),
                "fitted_delta_utility": "" if fitted is None else fitted,
                "residual": "" if residual is None else residual,
                "absolute_residual": "" if residual is None else abs(residual),
                "negative_delta_logloss": delta_logloss < 0.0,
                "sign_match": _sign(float(row["delta_utility"])) == _sign(float(row["delta_logloss"])),
            }
        )
    return table


def _format_report(fit: Mapping[str, Any], claim_report: Mapping[str, Any]) -> str:
    reason_codes = list(claim_report.get("reason_codes") or [])
    lines = [
        "# One-Stratum Metric Bridge Calibration Report",
        "",
        "## Summary",
        "",
        f"- Metric claim level: `{fit['metric_claim_level']}`",
        f"- Claim gate status: `{claim_report['claim_gate_status']}`",
        f"- Data source kind: `{fit['data_source_kind']}`",
        f"- Selector regime label: `{fit['selector_regime_label']}`",
        f"- Evidence scope: `{fit['evidence_scope']}`",
        f"- Diagnostic scope: `{fit['diagnostic_scope']}`",
        f"- Paper evidence eligible: {str(fit['paper_evidence_eligible']).lower()}",
        f"- Measurement validation claim: {str(fit['measurement_validation_claim']).lower()}",
        f"- Deployed V-information verification claim: {str(fit['deployed_v_information_verification_claim']).lower()}",
        "",
        "## Fit",
        "",
        f"- Fit method: `{fit['fit_method']}`",
        f"- `c_s`: `{fit['bridge_scale_c_s']}`",
        f"- `zeta_s`: `{fit['zeta_s']}`",
        f"- Mean absolute residual: `{fit['mean_absolute_residual']}`",
        f"- Sign agreement: `{fit['sign_agreement']}`",
        f"- Pearson correlation: `{fit['pearson_correlation']}`",
        f"- Spearman correlation: `{fit['spearman_correlation']}`",
        f"- Sample size: `{fit['sample_size']}`",
        f"- Effective sample size: `{fit['effective_sample_size']}`",
        f"- Bridge-informative delta pairs: `{fit['bridge_informative_delta_pair_count']}`",
        f"- Low-signal `delta_logloss` rows: `{fit['low_signal_delta_logloss_count']}`",
        f"- Negative `delta_logloss` rows: `{fit['negative_delta_logloss_count']}`",
        "",
        "## Claim Gate",
        "",
    ]
    if reason_codes:
        lines.extend(f"- `{reason}`" for reason in reason_codes)
    else:
        lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Fixture data is engineering validation only and is not paper measurement evidence.",
            "- Operator-provided calibration pairs are eligible for paper evidence only after the configured bridge gate passes.",
            "- This lane does not create human labels, kappa, contamination closure, or measurement validation.",
            "- This lane does not verify deployed V-information.",
            "",
        ]
    )
    return "\n".join(lines)


def _result_payload(
    *,
    config: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    thresholds = _threshold_config(config)
    signal_diagnostics = _bridge_signal_diagnostics(
        rows,
        minimum_abs_delta_logloss_for_bridge_evidence=float(
            thresholds["minimum_abs_delta_logloss_for_bridge_evidence"]
        ),
    )
    bridge_scale = _through_origin_scale(rows)
    residuals = [
        abs(float(row["delta_utility"]) - ((bridge_scale or 0.0) * float(row["delta_logloss"])))
        for row in rows
    ]
    zeta_s = _zeta(residuals, config)
    xs = [float(row["delta_logloss"]) for row in rows]
    ys = [float(row["delta_utility"]) for row in rows]
    pearson = _pearson(xs, ys)
    spearman = _spearman(xs, ys)
    sign_agreement = _sign_agreement(rows)
    claim, gate_status, reason_codes, pass_flags = _claim_from_gate(
        config=config,
        rows=rows,
        bridge_scale=bridge_scale,
        zeta_s=zeta_s,
        sign_agreement=sign_agreement,
        pearson=pearson,
        spearman=spearman,
        thresholds=thresholds,
        signal_diagnostics=signal_diagnostics,
    )
    source_kind = _data_source_kind(rows)
    evidence_scope = str(config.get("evidence_scope") or DEFAULT_CONFIG["evidence_scope"])
    diagnostic_scope = str(config.get("diagnostic_scope") or evidence_scope)
    selector_regime_label = "ambiguous"
    paper_evidence_eligible = source_kind == "operator_provided" and claim == "calibrated_proxy_supported"
    stratum_ids = sorted({str(row["stratum_id"]) for row in rows})
    fit = {
        "active_stratum_id": stratum_ids[0] if len(stratum_ids) == 1 else None,
        "active_stratum_ids": stratum_ids,
        "bridge_freshness": str(config.get("bridge_freshness", "fresh")),
        "bridge_scale_c_s": bridge_scale,
        **signal_diagnostics,
        "data_source_kind": source_kind,
        "denied_claims": list(DENIED_CLAIMS),
        "deployed_v_information_verification_claim": False,
        "diagnostic_scope": diagnostic_scope,
        "effective_sample_size": sum(int(row["replicate_count"]) for row in rows),
        "evidence_scope": evidence_scope,
        "experiment_id": str(config.get("experiment_id", DEFAULT_CONFIG["experiment_id"])),
        "fit_method": str(config.get("fit_method", DEFAULT_CONFIG["fit_method"])),
        "intercept_diagnostic": _intercept_diagnostic(rows),
        "mean_absolute_residual": _mean(residuals),
        "measurement_validation_claim": False,
        "measurement_validated_allowed": False,
        "metric_claim_level": claim,
        "paper_evidence_eligible": paper_evidence_eligible,
        "pass_flags": pass_flags,
        "pearson_correlation": pearson,
        "protocol_version": str(config.get("protocol_version", DEFAULT_CONFIG["protocol_version"])),
        "reason_codes": reason_codes,
        "residual_quantiles": {
            "p50": _quantile(residuals, 0.5),
            "p90": _quantile(residuals, 0.9),
            "p95": _quantile(residuals, 0.95),
            "p100": _quantile(residuals, 1.0),
        },
        "sample_size": len(rows),
        "selector_regime_label": selector_regime_label,
        "sign_agreement": sign_agreement,
        "spearman_correlation": spearman,
        "thresholds": thresholds,
        "zeta_s": zeta_s,
    }
    table = _table_rows(
        rows,
        bridge_scale,
        minimum_abs_delta_logloss_for_bridge_evidence=float(
            thresholds["minimum_abs_delta_logloss_for_bridge_evidence"]
        ),
    )
    claim_report = {
        "allowed_claim_level": claim,
        "bridge_scale_c_s": bridge_scale,
        "claim_gate_status": gate_status,
        "data_source_kind": source_kind,
        "denied_claims": list(DENIED_CLAIMS),
        "deployed_v_information_verification_claim": False,
        "diagnostic_scope": diagnostic_scope,
        "effective_sample_size": fit["effective_sample_size"],
        "evidence_scope": evidence_scope,
        "measurement_validation_claim": False,
        "measurement_validated_allowed": False,
        "metric_claim_level": claim,
        **signal_diagnostics,
        "paper_evidence_eligible": paper_evidence_eligible,
        "pass_flags": pass_flags,
        "reason_codes": reason_codes,
        "sample_size": len(rows),
        "selector_regime_label": selector_regime_label,
        "zeta_s": zeta_s,
    }
    return fit, table, claim_report


def run_bridge_calibration(
    *,
    config_path: str | Path,
    input_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    config = {**DEFAULT_CONFIG, **_read_json(Path(config_path))}
    if str(config.get("fit_method")) != "ols_through_origin":
        raise BridgeCalibrationValidationError("fit_method must be ols_through_origin")

    resolved_input = Path(input_path or config["input_file"])
    resolved_output_dir = Path(output_dir or config["output_dir"])
    rows = _load_pairs(resolved_input)
    fit, table, claim_report = _result_payload(config=config, rows=rows)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    pairs_path = _write_jsonl(resolved_output_dir / "bridge_calibration_pairs.jsonl", rows)
    fit_path = _write_json(resolved_output_dir / "bridge_calibration_fit.json", fit)
    table_path = _write_csv(
        resolved_output_dir / "bridge_calibration_table.csv",
        table,
        [
            *REQUIRED_FIELDS,
            *OPTIONAL_PROVENANCE_FIELDS,
            *OPTIONAL_NUMERIC_AUDIT_FIELDS,
            "fitted_delta_utility",
            "residual",
            "absolute_residual",
            "negative_delta_logloss",
            "sign_match",
        ],
    )
    claim_path = _write_json(resolved_output_dir / "bridge_claim_gate_report.json", claim_report)
    report_path = resolved_output_dir / "report.md"
    report_path.write_text(_format_report(fit, claim_report), encoding="utf-8")

    return {
        "status": claim_report["claim_gate_status"],
        "metric_claim_level": fit["metric_claim_level"],
        "paper_evidence_eligible": fit["paper_evidence_eligible"],
        "artifacts": {
            "bridge_calibration_pairs": str(pairs_path),
            "bridge_calibration_fit": str(fit_path),
            "bridge_calibration_table": str(table_path),
            "bridge_claim_gate_report": str(claim_path),
            "report": str(report_path),
        },
    }


def dry_validate_bridge_calibration(
    *,
    config_path: str | Path,
    input_path: str | Path | None = None,
) -> dict[str, Any]:
    """Validate operator calibration input without writing artifacts or claiming evidence."""

    config = {**DEFAULT_CONFIG, **_read_json(Path(config_path))}
    if str(config.get("fit_method")) != "ols_through_origin":
        raise BridgeCalibrationValidationError("fit_method must be ols_through_origin")

    resolved_input = Path(input_path or config["input_file"])
    rows = _load_pairs(resolved_input)
    fit, _table, claim_report = _result_payload(config=config, rows=rows)
    pass_flags = dict(claim_report["pass_flags"])
    return {
        "active_stratum_ids": fit["active_stratum_ids"],
        "artifacts_written": [],
        "data_source_kind": fit["data_source_kind"],
        "denied_claims": list(DENIED_CLAIMS),
        "deployed_v_information_verification_claim": False,
        "effective_sample_size": fit["effective_sample_size"],
        "bridge_informative_delta_pair_count": fit["bridge_informative_delta_pair_count"],
        "low_signal_delta_logloss_count": fit["low_signal_delta_logloss_count"],
        "low_signal_delta_logloss_pair_ids": fit["low_signal_delta_logloss_pair_ids"],
        "measurement_validation_claim": False,
        "mode": "dry_validation",
        "negative_delta_logloss_count": fit["negative_delta_logloss_count"],
        "negative_delta_logloss_pair_ids": fit["negative_delta_logloss_pair_ids"],
        "paper_evidence_claimed": False,
        "paper_evidence_eligible": False,
        "pass_flags": pass_flags,
        "reason_codes": fit["reason_codes"],
        "sample_size": fit["sample_size"],
        "schema_validation_status": "passed",
        "threshold_validation_status": "passed" if all(pass_flags.values()) else "failed",
        "thresholds": fit["thresholds"],
        "would_be_claim_gate_status": claim_report["claim_gate_status"],
        "would_be_metric_claim_level": fit["metric_claim_level"],
        "would_be_paper_evidence_eligible": fit["paper_evidence_eligible"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the P45 one-stratum bridge calibration lane.")
    parser.add_argument("--config", required=True, help="Path to bridge calibration config JSON.")
    parser.add_argument("--input", help="Optional JSONL/CSV calibration pair input override.")
    parser.add_argument("--output-dir", help="Optional output directory override.")
    parser.add_argument(
        "--dry-validate",
        action="store_true",
        help="Validate schema and thresholds without writing artifacts or claiming paper evidence.",
    )
    args = parser.parse_args()
    if args.dry_validate:
        result = dry_validate_bridge_calibration(
            config_path=args.config,
            input_path=args.input,
        )
    else:
        result = run_bridge_calibration(
            config_path=args.config,
            input_path=args.input,
            output_dir=args.output_dir,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
