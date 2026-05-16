from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


class P55PilotValidationError(ValueError):
    """Raised when P55 pilot inputs cannot be parsed."""


ACTIVE_STRATUM_ID = "evidence_packet_selection_microtask_v1"
OPERATOR_DATA_SOURCE_KIND = "operator_imported_rows"
FIXTURE_DATA_SOURCE_KINDS = {"fixture", "fixture_test_only", "synthetic_fixture"}
COMMENT_LINE_PREFIXES = ("#", "//")
OUTPUT_ARTIFACTS = (
    "manifest.json",
    "claim_gate_report.json",
    "report.md",
)
ROW_OUTPUT_ARTIFACTS = (
    "validated_rows.jsonl",
    "bridge_fit_summary.json",
    "bridge_fit_summary.csv",
)
REQUIRED_ROW_FIELDS = (
    "run_id",
    "dispatch_id",
    "agent_id",
    "round_id",
    "candidate_pool_hash",
    "projection_hash",
    "context_L_hash",
    "block_A_ids",
    "materialization_policy",
    "model_tier",
    "decoding_policy",
    "target_evidence",
    "delta_logloss",
    "delta_utility",
    "utility_metric_version",
    "replicate_count",
    "effective_sample_size",
    "data_source_kind",
    "contamination_status",
    "bridge_contract_id",
    "stratum_id",
    "task_family",
    "candidate_slice_band",
    "block_size",
    "target_type",
    "logloss_measurement_version",
    "operator_approval_ref",
)
DENIED_CLAIMS = (
    "measurement_validation",
    "human_label_validation",
    "human_human_kappa",
    "deployed_v_information_verification",
    "theorem_level_deployed_submodularity_verification",
    "synthetic_evidence_as_bridge_evidence",
    "fixture_evidence_as_paper_grade_evidence",
    "replay_usability_as_metric_support",
    "extraction_audit_as_selector_validity",
    "reprojection_witness_as_deployed_runtime_improvement",
    "current_p45_bio_attribute_as_calibrated_proxy_supported",
    "p55_fixture_rows_as_calibrated_proxy_supported",
    "vinfo_proxy_supported_without_formal_bridge_review",
)
DEFAULT_THRESHOLDS = {
    "min_effective_sample_size": 6,
    "min_total_rows": 6,
    "min_dev_rows": 3,
    "min_heldout_rows": 3,
    "min_abs_delta_logloss_signal": 0.0001,
    "max_heldout_zeta_s": 0.05,
    "min_heldout_sign_agreement": 0.9,
    "min_abs_heldout_rank_correlation": 0.9,
    "max_residual_stability_gap": 0.02,
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise P55PilotValidationError(f"JSON file does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise P55PilotValidationError(f"JSON file must contain an object: {path}")
    return payload


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_stable_json(payload), encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")
    return path


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return path


def _path_reference(path: str | Path | None) -> str | None:
    if path is None:
        return None
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved.name
    return resolved.as_posix()


def _is_payload_line(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith(COMMENT_LINE_PREFIXES)


def detect_input_file_status(path: str | Path | None) -> str:
    if path is None:
        return "absent"
    input_path = Path(path)
    if not input_path.exists():
        return "absent"
    if input_path.suffix.lower() == ".jsonl":
        return "present" if any(_is_payload_line(line) for line in input_path.read_text(encoding="utf-8").splitlines()) else "empty"
    if input_path.stat().st_size == 0:
        return "empty"
    return "present"


def _finite_float(value: Any, field: str, row_label: str, defects: list[str]) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        defects.append(f"{row_label}:{field}_not_numeric")
        return None
    if not math.isfinite(parsed):
        defects.append(f"{row_label}:{field}_not_finite")
        return None
    return parsed


def _positive_int(value: Any, field: str, row_label: str, defects: list[str]) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        defects.append(f"{row_label}:{field}_not_integer")
        return None
    if parsed <= 0:
        defects.append(f"{row_label}:{field}_not_positive")
        return None
    return parsed


def _non_empty_string(value: Any, field: str, row_label: str, defects: list[str]) -> str | None:
    parsed = str(value).strip()
    if not parsed:
        defects.append(f"{row_label}:{field}_empty")
        return None
    return parsed


def _string_list(value: Any, field: str, row_label: str, defects: list[str]) -> list[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    elif isinstance(value, str):
        items = [part.strip() for part in value.split("|") if part.strip()]
    else:
        defects.append(f"{row_label}:{field}_not_list_or_delimited_string")
        return []
    if not items:
        defects.append(f"{row_label}:{field}_empty")
    return items


def _expected_policy(config: Mapping[str, Any], key: str) -> str:
    value = config.get(key)
    if isinstance(value, Mapping):
        return str(value.get("policy_id") or value.get("kind") or value.get("measurement_id") or "")
    return str(value or "")


def _expected_target_type(config: Mapping[str, Any]) -> str:
    value = config.get("target_type")
    if isinstance(value, Mapping):
        return str(value.get("kind") or "")
    return str(value or "")


def _expected_logloss(config: Mapping[str, Any]) -> str:
    value = config.get("logloss_measurement")
    if isinstance(value, Mapping):
        return str(value.get("measurement_id") or "")
    return str(value or "")


def _thresholds(config: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, float | int]:
    configured = dict(DEFAULT_THRESHOLDS)
    contract_ess = contract.get("min_effective_sample_size")
    if isinstance(contract_ess, int):
        configured["min_effective_sample_size"] = contract_ess
    configured.update(dict(config.get("bridge_thresholds") or {}))
    return configured


def load_p55_rows(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    if not input_path.exists():
        raise P55PilotValidationError(f"input row file does not exist: {input_path}")
    rows: list[dict[str, Any]] = []
    if input_path.suffix.lower() == ".jsonl":
        for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not _is_payload_line(line):
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise P55PilotValidationError(f"row {line_number}: JSONL row must be an object")
            rows.append(payload)
    elif input_path.suffix.lower() == ".csv":
        with input_path.open("r", encoding="utf-8", newline="") as handle:
            rows.extend(dict(row) for row in csv.DictReader(handle))
    else:
        raise P55PilotValidationError("P55 row input must be .jsonl or .csv")
    return rows


def _canonical_row(raw: Mapping[str, Any], row_number: int) -> tuple[dict[str, Any] | None, list[str]]:
    defects: list[str] = []
    row_label = f"row_{row_number}"
    missing = [field for field in REQUIRED_ROW_FIELDS if field not in raw]
    if missing:
        defects.extend(f"{row_label}:missing_{field}" for field in missing)
        return None, defects

    canonical = {
        "run_id": _non_empty_string(raw["run_id"], "run_id", row_label, defects),
        "dispatch_id": _non_empty_string(raw["dispatch_id"], "dispatch_id", row_label, defects),
        "agent_id": _non_empty_string(raw["agent_id"], "agent_id", row_label, defects),
        "round_id": _non_empty_string(raw["round_id"], "round_id", row_label, defects),
        "candidate_pool_hash": _non_empty_string(
            raw["candidate_pool_hash"], "candidate_pool_hash", row_label, defects
        ),
        "projection_hash": _non_empty_string(raw["projection_hash"], "projection_hash", row_label, defects),
        "context_L_hash": _non_empty_string(raw["context_L_hash"], "context_L_hash", row_label, defects),
        "block_A_ids": _string_list(raw["block_A_ids"], "block_A_ids", row_label, defects),
        "materialization_policy": _non_empty_string(
            raw["materialization_policy"], "materialization_policy", row_label, defects
        ),
        "model_tier": _non_empty_string(raw["model_tier"], "model_tier", row_label, defects),
        "decoding_policy": _non_empty_string(raw["decoding_policy"], "decoding_policy", row_label, defects),
        "target_evidence": _non_empty_string(raw["target_evidence"], "target_evidence", row_label, defects),
        "delta_logloss": _finite_float(raw["delta_logloss"], "delta_logloss", row_label, defects),
        "delta_utility": _finite_float(raw["delta_utility"], "delta_utility", row_label, defects),
        "utility_metric_version": _non_empty_string(
            raw["utility_metric_version"], "utility_metric_version", row_label, defects
        ),
        "replicate_count": _positive_int(raw["replicate_count"], "replicate_count", row_label, defects),
        "effective_sample_size": _finite_float(
            raw["effective_sample_size"], "effective_sample_size", row_label, defects
        ),
        "data_source_kind": _non_empty_string(
            raw["data_source_kind"], "data_source_kind", row_label, defects
        ),
        "contamination_status": _non_empty_string(
            raw["contamination_status"], "contamination_status", row_label, defects
        ),
        "bridge_contract_id": _non_empty_string(
            raw["bridge_contract_id"], "bridge_contract_id", row_label, defects
        ),
        "stratum_id": _non_empty_string(raw["stratum_id"], "stratum_id", row_label, defects),
        "task_family": _non_empty_string(raw["task_family"], "task_family", row_label, defects),
        "candidate_slice_band": _non_empty_string(
            raw["candidate_slice_band"], "candidate_slice_band", row_label, defects
        ),
        "block_size": _positive_int(raw["block_size"], "block_size", row_label, defects),
        "target_type": _non_empty_string(raw["target_type"], "target_type", row_label, defects),
        "logloss_measurement_version": _non_empty_string(
            raw["logloss_measurement_version"], "logloss_measurement_version", row_label, defects
        ),
        "operator_approval_ref": _non_empty_string(
            raw["operator_approval_ref"], "operator_approval_ref", row_label, defects
        ),
        "split": str(raw.get("split") or "").strip(),
        "drift_status": str(raw.get("drift_status") or "missing").strip(),
        "bridge_witness_status": str(raw.get("bridge_witness_status") or "missing").strip(),
        "residual_stability_group": str(raw.get("residual_stability_group") or "").strip(),
    }
    if defects:
        return None, defects
    return canonical, []


def _stable_row_key(row: Mapping[str, Any]) -> tuple[str, ...]:
    return (
        str(row["run_id"]),
        str(row["dispatch_id"]),
        str(row["agent_id"]),
        str(row["round_id"]),
        str(row["candidate_pool_hash"]),
        "|".join(str(item) for item in row["block_A_ids"]),
        str(row["projection_hash"]),
    )


def _source_kind(rows: Sequence[Mapping[str, Any]]) -> str:
    kinds = sorted({str(row["data_source_kind"]) for row in rows})
    if not kinds:
        return "missing"
    if len(kinds) > 1:
        return "mixed"
    return kinds[0]


def _status_kind(rows: Sequence[Mapping[str, Any]], field: str, default: str) -> str:
    values = sorted({str(row.get(field) or default) for row in rows})
    if not values:
        return default
    if len(values) > 1:
        return "mixed"
    return values[0]


def validate_p55_rows(
    rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    row_defects: list[str] = []
    canonical_rows: list[dict[str, Any]] = []
    for row_number, raw in enumerate(rows, start=1):
        canonical, defects = _canonical_row(raw, row_number)
        row_defects.extend(defects)
        if canonical is not None:
            canonical_rows.append(canonical)
    canonical_rows.sort(key=_stable_row_key)

    expected_contract_ids = {
        str(contract.get("contract_id") or ""),
        str(contract.get("contract_schema_version") or ""),
    }
    expected_stratum = str(config.get("stratum_id") or ACTIVE_STRATUM_ID)
    expected_task_family = str(config.get("task_family") or ACTIVE_STRATUM_ID)
    expected_materialization = _expected_policy(config, "materialization_policy")
    expected_decoding = _expected_policy(config, "decoding_policy")
    expected_candidate_slice = _expected_policy(config, "candidate_slice_band")
    expected_target = _expected_target_type(config)
    expected_logloss = _expected_logloss(config)
    expected_model_tier = str(config.get("model_tier") or "")
    max_block_size = 2
    if isinstance(config.get("block_size"), Mapping):
        max_block_size = int(config["block_size"].get("maximum", 2))

    reason_codes: list[str] = []
    if row_defects:
        reason_codes.append("row_schema_invalid")

    row_count = len(canonical_rows)
    data_source_kind = _source_kind(canonical_rows)
    fixture_only = row_count > 0 and data_source_kind in FIXTURE_DATA_SOURCE_KINDS
    operator_source_match = data_source_kind == OPERATOR_DATA_SOURCE_KIND
    if row_count and not operator_source_match:
        reason_codes.append("data_source_not_operator_imported_rows")
    if fixture_only:
        reason_codes.append("fixture_only_not_bridge_support")

    active_stratum_match = bool(canonical_rows) and all(
        str(row["stratum_id"]) == expected_stratum
        and str(row["task_family"]) == expected_task_family
        and str(row["materialization_policy"]) == expected_materialization
        and str(row["model_tier"]) == expected_model_tier
        and str(row["decoding_policy"]) == expected_decoding
        and str(row["candidate_slice_band"]) == expected_candidate_slice
        and int(row["block_size"]) <= max_block_size
        and str(row["target_type"]) == expected_target
        and str(row["logloss_measurement_version"]) == expected_logloss
        and str(row["bridge_contract_id"]) in expected_contract_ids
        for row in canonical_rows
    )
    if row_count and not active_stratum_match:
        reason_codes.append("active_stratum_mismatch")

    candidate_hashes = sorted({str(row["candidate_pool_hash"]) for row in canonical_rows})
    if any(not str(row["candidate_pool_hash"]).strip() for row in canonical_rows):
        candidate_pool_hash_status = "missing"
        reason_codes.append("candidate_pool_hash_missing")
    elif len(candidate_hashes) > 1:
        candidate_pool_hash_status = "mismatched"
        reason_codes.append("candidate_pool_hash_mismatched")
    elif candidate_hashes:
        candidate_pool_hash_status = "pass"
    else:
        candidate_pool_hash_status = "missing"

    contamination_status = _status_kind(canonical_rows, "contamination_status", "not_applicable")
    if contamination_status == "fail":
        reason_codes.append("contamination_failed")
    elif contamination_status in {"unknown", "missing", "mixed"}:
        reason_codes.append("contamination_not_cleared")

    drift_status = _status_kind(canonical_rows, "drift_status", "missing")
    bridge_witness_status = _status_kind(canonical_rows, "bridge_witness_status", "missing")
    if drift_status != "fresh":
        reason_codes.append(f"drift_status_{drift_status}")
    if bridge_witness_status not in {"fresh", "pass"}:
        reason_codes.append(f"bridge_witness_status_{bridge_witness_status}")

    effective_sample_size = sum(float(row["effective_sample_size"]) for row in canonical_rows)
    min_effective_sample_size = float(_thresholds(config, contract)["min_effective_sample_size"])
    if row_count and effective_sample_size < min_effective_sample_size:
        reason_codes.append("effective_sample_size_underpowered")

    return {
        "active_stratum_match": active_stratum_match,
        "bridge_witness_status": bridge_witness_status,
        "candidate_pool_hash_count": len(candidate_hashes),
        "candidate_pool_hash_status": candidate_pool_hash_status,
        "canonical_rows": canonical_rows,
        "contamination_status": contamination_status,
        "data_source_kind": data_source_kind,
        "drift_status": drift_status,
        "effective_sample_size": effective_sample_size,
        "fixture_only": fixture_only,
        "operator_source_match": operator_source_match,
        "reason_codes": sorted(set(reason_codes)),
        "rows_imported": len(rows),
        "rows_validated": row_count,
        "row_count": row_count,
        "row_defects": row_defects,
        "schema_valid": not row_defects,
    }


def split_dev_heldout(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    sorted_rows = [dict(row) for row in sorted(rows, key=_stable_row_key)]
    split_values = {str(row.get("split") or "").strip() for row in sorted_rows if str(row.get("split") or "").strip()}
    if split_values:
        dev = [row for row in sorted_rows if str(row.get("split")) == "dev"]
        heldout = [row for row in sorted_rows if str(row.get("split")) == "heldout"]
        return dev, heldout, "declared_split"
    if len(sorted_rows) < 2:
        return sorted_rows, [], "deterministic_half_split"
    midpoint = len(sorted_rows) // 2
    return sorted_rows[:midpoint], sorted_rows[midpoint:], "deterministic_half_split"


def fit_bridge_scale(dev_rows: Sequence[Mapping[str, Any]]) -> float | None:
    denominator = sum(float(row["delta_logloss"]) ** 2 for row in dev_rows)
    if denominator == 0.0:
        return None
    numerator = sum(float(row["delta_logloss"]) * float(row["delta_utility"]) for row in dev_rows)
    return numerator / denominator


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2:
        return None
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
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
        for _value, original_index in ordered[index:end]:
            ranks[original_index] = average_rank
        index = end
    return ranks


def _spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2:
        return None
    return _pearson(_average_ranks(xs), _average_ranks(ys))


def evaluate_bridge_fit(
    rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    thresholds = _thresholds(config, contract)
    dev_rows, heldout_rows, split_policy = split_dev_heldout(rows)
    c_s = fit_bridge_scale(dev_rows)
    residual_rows: list[dict[str, Any]] = []
    predicted: list[float] = []
    actual: list[float] = []
    if c_s is not None:
        for row in heldout_rows:
            fitted = c_s * float(row["delta_logloss"])
            residual = float(row["delta_utility"]) - fitted
            residual_rows.append(
                {
                    "absolute_residual": abs(residual),
                    "delta_logloss": float(row["delta_logloss"]),
                    "delta_utility": float(row["delta_utility"]),
                    "fitted_delta_utility": fitted,
                    "residual": residual,
                    "residual_stability_group": str(row.get("residual_stability_group") or ""),
                    "row_key": "|".join(_stable_row_key(row)),
                    "sign_match": _sign(fitted) == _sign(float(row["delta_utility"])),
                }
            )
            predicted.append(fitted)
            actual.append(float(row["delta_utility"]))

    zeta_s = max((row["absolute_residual"] for row in residual_rows), default=None)
    sign_agreement = (
        sum(1 for row in residual_rows if row["sign_match"]) / len(residual_rows)
        if residual_rows
        else None
    )
    rank_correlation = _spearman(predicted, actual)
    groups: dict[str, list[float]] = defaultdict(list)
    for row in residual_rows:
        group = str(row.get("residual_stability_group") or "")
        if group:
            groups[group].append(float(row["absolute_residual"]))
    if len(groups) >= 2:
        group_maxima = {group: max(values) for group, values in sorted(groups.items())}
        residual_stability_gap = max(group_maxima.values()) - min(group_maxima.values())
        residual_stability = {
            "group_max_absolute_residual": group_maxima,
            "passes": residual_stability_gap <= float(thresholds["max_residual_stability_gap"]),
            "status": "available",
            "stability_gap": residual_stability_gap,
        }
    else:
        residual_stability = {
            "group_max_absolute_residual": {},
            "passes": False,
            "status": "unavailable",
            "stability_gap": None,
        }

    return {
        "c_s": c_s,
        "dev_row_count": len(dev_rows),
        "heldout_rank_correlation": rank_correlation,
        "heldout_residual_rows": residual_rows,
        "heldout_row_count": len(heldout_rows),
        "heldout_sign_agreement": sign_agreement,
        "mean_heldout_absolute_residual": _mean([float(row["absolute_residual"]) for row in residual_rows]),
        "residual_stability": residual_stability,
        "split_policy": split_policy,
        "thresholds": thresholds,
        "zeta_s": zeta_s,
    }


def derive_claim_gate(
    validation: Mapping[str, Any],
    fit: Mapping[str, Any],
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    input_rows_present: bool,
    input_file_status: str,
) -> dict[str, Any]:
    thresholds = _thresholds(config, contract)
    reason_codes: list[str] = []
    no_rows = input_file_status in {"absent", "empty"}
    if no_rows:
        reason_codes.extend(["no_operator_imported_rows", "operator_rows_required"])
    reason_codes.extend(str(reason) for reason in validation.get("reason_codes", []))

    if int(validation.get("row_count", 0)) > 0:
        if int(validation.get("row_count", 0)) < int(thresholds["min_total_rows"]):
            reason_codes.append("row_count_underpowered")
        if int(fit.get("dev_row_count", 0)) < int(thresholds["min_dev_rows"]):
            reason_codes.append("dev_split_underpowered")
        if int(fit.get("heldout_row_count", 0)) < int(thresholds["min_heldout_rows"]):
            reason_codes.append("heldout_split_underpowered")
        if fit.get("c_s") is None:
            reason_codes.append("bridge_scale_unavailable")
        if fit.get("zeta_s") is None:
            reason_codes.append("heldout_residual_unavailable")
        elif float(fit["zeta_s"]) > float(thresholds["max_heldout_zeta_s"]):
            reason_codes.append("heldout_residual_too_large")
        if fit.get("heldout_sign_agreement") is None:
            reason_codes.append("heldout_sign_agreement_unavailable")
        elif float(fit["heldout_sign_agreement"]) < float(thresholds["min_heldout_sign_agreement"]):
            reason_codes.append("heldout_sign_agreement_low")
        if fit.get("heldout_rank_correlation") is None:
            reason_codes.append("heldout_rank_correlation_unavailable")
        elif abs(float(fit["heldout_rank_correlation"])) < float(thresholds["min_abs_heldout_rank_correlation"]):
            reason_codes.append("heldout_rank_correlation_low")
        residual_stability = dict(fit.get("residual_stability") or {})
        if not residual_stability.get("passes"):
            reason_codes.append(f"residual_stability_{residual_stability.get('status', 'failed')}")
        low_signal_rows = [
            row
            for row in validation.get("canonical_rows", [])
            if abs(float(row["delta_logloss"])) < float(thresholds["min_abs_delta_logloss_signal"])
        ]
        if low_signal_rows:
            reason_codes.append("signal_denominator_underpowered")

    reason_codes = sorted(set(reason_codes))
    if no_rows:
        metric_claim_level = "ambiguous_metric"
        pilot_status = "blocked_operator_required"
        claim_gate_status = "failed_closed_no_rows"
    elif "contamination_failed" in reason_codes:
        metric_claim_level = "operational_utility_only"
        pilot_status = "pilot_only"
        claim_gate_status = "failed_closed_contamination"
    elif reason_codes:
        metric_claim_level = "ambiguous_metric"
        pilot_status = "pilot_only"
        claim_gate_status = "failed_closed"
    else:
        metric_claim_level = "calibrated_proxy_supported"
        pilot_status = "pilot_only"
        claim_gate_status = "calibrated_proxy_supported_exact_stratum_only"

    calibrated_allowed = metric_claim_level == "calibrated_proxy_supported"
    paper_evidence_eligible = (
        calibrated_allowed
        and validation.get("data_source_kind") == OPERATOR_DATA_SOURCE_KIND
        and validation.get("contamination_status") == "pass"
    )
    return {
        "active_stratum_match": bool(validation.get("active_stratum_match")),
        "allowed_metric_claim_level": metric_claim_level,
        "blocked_operator_required": no_rows,
        "calibrated_proxy_supported_allowed": calibrated_allowed,
        "claim_gate_status": claim_gate_status,
        "contamination_status": validation.get("contamination_status"),
        "data_source_kind": validation.get("data_source_kind"),
        "denied_claims": list(DENIED_CLAIMS),
        "deployed_v_information_verification_claim": False,
        "effective_sample_size": validation.get("effective_sample_size"),
        "human_human_kappa_present": False,
        "human_labels_present": False,
        "input_file_status": input_file_status,
        "input_rows_present": input_rows_present,
        "live_api_used": False,
        "measurement_validation_claim": False,
        "metric_claim_level": metric_claim_level,
        "next_phase_allowed": False,
        "paper_evidence_eligible": paper_evidence_eligible,
        "pilot_status": pilot_status,
        "reason_codes": reason_codes,
        "requires_operator": no_rows,
        "review_ceiling": "none" if no_rows else metric_claim_level,
        "row_count": validation.get("row_count"),
        "rows_imported": validation.get("rows_imported", 0),
        "rows_validated": validation.get("rows_validated", validation.get("row_count", 0)),
        "selector_regime_label_max": "none",
        "vinfo_proxy_supported_allowed": False,
        "fit_metrics_computed": bool(fit.get("c_s") is not None and fit.get("zeta_s") is not None),
    }


def _empty_validation(input_file_status: str) -> dict[str, Any]:
    return {
        "active_stratum_match": False,
        "bridge_witness_status": "missing",
        "candidate_pool_hash_count": 0,
        "candidate_pool_hash_status": "missing",
        "canonical_rows": [],
        "contamination_status": "not_applicable",
        "data_source_kind": "missing",
        "drift_status": "missing",
        "effective_sample_size": 0.0,
        "fixture_only": False,
        "operator_source_match": False,
        "reason_codes": [],
        "rows_imported": 0,
        "rows_validated": 0,
        "row_count": 0,
        "row_defects": [],
        "schema_valid": False,
        "input_file_status": input_file_status,
    }


def _report_markdown(
    claim_gate: Mapping[str, Any],
    validation: Mapping[str, Any],
    fit: Mapping[str, Any],
    config: Mapping[str, Any],
    input_rows_reference: str | None,
) -> str:
    reason_codes = list(claim_gate.get("reason_codes") or [])
    lines = [
        "# P55 New-Stratum Bridge Calibration Pilot Report",
        "",
        "## Summary",
        "",
        f"- Stratum: `{config.get('stratum_id', ACTIVE_STRATUM_ID)}`",
        f"- Input rows reference: `{input_rows_reference or 'not_configured'}`",
        f"- Input file status: `{claim_gate['input_file_status']}`",
        f"- Pilot status: `{claim_gate['pilot_status']}`",
        f"- Claim gate status: `{claim_gate['claim_gate_status']}`",
        f"- Metric claim level: `{claim_gate['metric_claim_level']}`",
        f"- Paper evidence eligible: `{str(claim_gate['paper_evidence_eligible']).lower()}`",
        f"- Measurement validation claim: `{str(claim_gate['measurement_validation_claim']).lower()}`",
        f"- Live API used: `{str(claim_gate['live_api_used']).lower()}`",
        f"- Human labels present: `{str(claim_gate['human_labels_present']).lower()}`",
        f"- Human-human kappa present: `{str(claim_gate['human_human_kappa_present']).lower()}`",
        f"- Blocked operator required: `{str(claim_gate['blocked_operator_required']).lower()}`",
        f"- Next phase allowed: `{str(claim_gate['next_phase_allowed']).lower()}`",
        "",
        "## Row Validation",
        "",
        f"- Rows present: `{str(claim_gate['input_rows_present']).lower()}`",
        f"- Rows imported: `{claim_gate.get('rows_imported', 0)}`",
        f"- Rows validated: `{claim_gate.get('rows_validated', 0)}`",
        f"- Rows accepted for evaluation: `{validation.get('row_count', 0)}`",
        f"- Active stratum match: `{str(validation.get('active_stratum_match')).lower()}`",
        f"- Candidate-pool hash status: `{validation.get('candidate_pool_hash_status')}`",
        f"- Data source kind: `{validation.get('data_source_kind')}`",
        f"- Contamination status: `{validation.get('contamination_status')}`",
        f"- Drift status: `{validation.get('drift_status')}`",
        "",
        "## Fit",
        "",
        f"- Development rows: `{fit.get('dev_row_count', 0)}`",
        f"- Held-out rows: `{fit.get('heldout_row_count', 0)}`",
        f"- `c_s`: `{fit.get('c_s')}`",
        f"- `zeta_s`: `{fit.get('zeta_s')}`",
        f"- Held-out sign agreement: `{fit.get('heldout_sign_agreement')}`",
        f"- Held-out rank correlation: `{fit.get('heldout_rank_correlation')}`",
        f"- Residual stability: `{dict(fit.get('residual_stability') or {}).get('status')}`",
        f"- Fit metrics computed: `{str(claim_gate['fit_metrics_computed']).lower()}`",
        "",
        "## Claim Gate Reasons",
        "",
    ]
    lines.extend(f"- `{reason}`" for reason in reason_codes) if reason_codes else lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- P55 does not claim measurement validation.",
            "- P55 does not claim deployed V-information verification.",
            "- Fixture/test-only rows cannot emit `calibrated_proxy_supported` or `vinfo_proxy_supported`.",
            "- Missing operator-imported rows fail closed without fabricated evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def _summary_csv_rows(fit: Mapping[str, Any], claim_gate: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "active_stratum_match": claim_gate["active_stratum_match"],
            "c_s": fit.get("c_s"),
            "claim_gate_status": claim_gate["claim_gate_status"],
            "heldout_rank_correlation": fit.get("heldout_rank_correlation"),
            "heldout_sign_agreement": fit.get("heldout_sign_agreement"),
            "metric_claim_level": claim_gate["metric_claim_level"],
            "paper_evidence_eligible": claim_gate["paper_evidence_eligible"],
            "pilot_status": claim_gate["pilot_status"],
            "zeta_s": fit.get("zeta_s"),
        }
    ]


def write_canonical_outputs(
    *,
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    validation: Mapping[str, Any],
    fit: Mapping[str, Any],
    claim_gate: Mapping[str, Any],
    output_dir: str | Path,
    input_rows_reference: str | None,
) -> dict[str, str]:
    resolved_output_dir = Path(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, str] = {}
    manifest = {
        "artifact_schema_version": "p55_bridge_calibration_pilot.v1",
        "canonical_outputs": list(OUTPUT_ARTIFACTS)
        + (list(ROW_OUTPUT_ARTIFACTS) if int(validation.get("row_count", 0)) > 0 else []),
        "claim_gate_status": claim_gate["claim_gate_status"],
        "claim_gate_result": claim_gate["claim_gate_status"],
        "config_id": str(config.get("config_id") or "p55_bridge_calibration_pilot"),
        "input_file_status": claim_gate["input_file_status"],
        "input_rows_reference": input_rows_reference,
        "live_api_used": False,
        "metric_claim_level": claim_gate["metric_claim_level"],
        "blocked_operator_required": claim_gate["blocked_operator_required"],
        "operator_approval_scope": "route_a_operator_imported_rows_only",
        "paper_evidence_eligible": claim_gate["paper_evidence_eligible"],
        "phase": "P55",
        "pilot_status": claim_gate["pilot_status"],
        "requires_operator": claim_gate["requires_operator"],
        "next_phase_allowed": claim_gate["next_phase_allowed"],
        "review_ceiling": claim_gate["review_ceiling"],
        "row_count": validation.get("row_count", 0),
        "rows_imported": claim_gate.get("rows_imported", 0),
        "rows_validated": claim_gate.get("rows_validated", 0),
        "stratum_id": str(config.get("stratum_id") or ACTIVE_STRATUM_ID),
    }
    artifacts["manifest"] = str(_write_json(resolved_output_dir / "manifest.json", manifest))
    report_payload = {
        "active_stratum_match": claim_gate["active_stratum_match"],
        "bridge_report": {
            "c_s": fit.get("c_s"),
            "drift_status": validation.get("drift_status"),
            "effective_sample_size": validation.get("effective_sample_size"),
            "fit_metrics_computed": claim_gate["fit_metrics_computed"],
            "heldout_sign_agreement": fit.get("heldout_sign_agreement"),
            "heldout_spearman_or_rank_correlation": fit.get("heldout_rank_correlation"),
            "residual_stability": fit.get("residual_stability"),
            "zeta_s": fit.get("zeta_s"),
        },
        "candidate_pool_hash_status": validation.get("candidate_pool_hash_status"),
        "claim_gate_result": dict(claim_gate),
        "contract_id": str(contract.get("contract_id") or ""),
        "metric_claim_level": claim_gate["metric_claim_level"],
        "paper_evidence_eligible": claim_gate["paper_evidence_eligible"],
        "row_validation": {
            "row_defects": validation.get("row_defects", []),
            "rows_imported": claim_gate.get("rows_imported", 0),
            "rows_validated": claim_gate.get("rows_validated", 0),
            "schema_valid": validation.get("schema_valid"),
        },
        "stratum_id": str(config.get("stratum_id") or ACTIVE_STRATUM_ID),
    }
    artifacts["claim_gate_report"] = str(
        _write_json(resolved_output_dir / "claim_gate_report.json", report_payload)
    )
    (resolved_output_dir / "report.md").write_text(
        _report_markdown(claim_gate, validation, fit, config, input_rows_reference),
        encoding="utf-8",
    )
    artifacts["report"] = str(resolved_output_dir / "report.md")
    if int(validation.get("row_count", 0)) > 0:
        artifacts["validated_rows"] = str(
            _write_jsonl(resolved_output_dir / "validated_rows.jsonl", validation["canonical_rows"])
        )
        fit_payload = {
            "fit_method": "development_split_ols_through_origin",
            "fit_summary": dict(fit),
            "thresholds": _thresholds(config, contract),
        }
        artifacts["bridge_fit_summary"] = str(
            _write_json(resolved_output_dir / "bridge_fit_summary.json", fit_payload)
        )
        artifacts["bridge_fit_summary_csv"] = str(
            _write_csv(
                resolved_output_dir / "bridge_fit_summary.csv",
                _summary_csv_rows(fit, claim_gate),
                [
                    "pilot_status",
                    "claim_gate_status",
                    "metric_claim_level",
                    "paper_evidence_eligible",
                    "active_stratum_match",
                    "c_s",
                    "zeta_s",
                    "heldout_sign_agreement",
                    "heldout_rank_correlation",
                ],
            )
        )
    return artifacts


def run_p55_bridge_calibration_pilot(
    *,
    config_path: str | Path,
    input_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    contract_path: str | Path | None = None,
) -> dict[str, Any]:
    config = _read_json(Path(config_path))
    contract_ref = contract_path or config.get(
        "diagnostic_threshold_contract_template",
        "docs/templates/diagnostic-threshold-contract-template.json",
    )
    contract = _read_json(Path(contract_ref))
    input_ref = input_path or config.get("input_rows_path")
    resolved_input = Path(input_ref) if input_ref is not None else None
    resolved_output = Path(output_dir or config.get("output_dir", "artifacts/experiments/p55_bridge_calibration_pilot"))
    input_file_status = detect_input_file_status(resolved_input)

    if input_file_status == "present" and resolved_input is not None:
        raw_rows = load_p55_rows(resolved_input)
        if raw_rows:
            validation = validate_p55_rows(raw_rows, config, contract)
            validation["input_file_status"] = input_file_status
        else:
            input_file_status = "empty"
            validation = _empty_validation(input_file_status)
    else:
        validation = _empty_validation(input_file_status)
    fit = evaluate_bridge_fit(validation["canonical_rows"], config, contract)
    rows_present = bool(validation.get("rows_validated", 0))
    claim_gate = derive_claim_gate(
        validation,
        fit,
        config,
        contract,
        input_rows_present=rows_present,
        input_file_status=input_file_status,
    )
    artifacts = write_canonical_outputs(
        config=config,
        contract=contract,
        validation=validation,
        fit=fit,
        claim_gate=claim_gate,
        output_dir=resolved_output,
        input_rows_reference=_path_reference(input_ref),
    )
    return {
        "artifacts": artifacts,
        "claim_gate_status": claim_gate["claim_gate_status"],
        "input_file_status": input_file_status,
        "input_rows_present": rows_present,
        "metric_claim_level": claim_gate["metric_claim_level"],
        "paper_evidence_eligible": claim_gate["paper_evidence_eligible"],
        "pilot_status": claim_gate["pilot_status"],
        "reason_codes": claim_gate["reason_codes"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the P55 bridge calibration pilot importer.")
    parser.add_argument("--config", required=True, help="Path to the P55 pilot config JSON.")
    parser.add_argument("--input", help="Optional P55 row input override.")
    parser.add_argument("--output-dir", help="Optional output directory override.")
    parser.add_argument("--contract", help="Optional diagnostic contract template override.")
    args = parser.parse_args()
    result = run_p55_bridge_calibration_pilot(
        config_path=args.config,
        input_path=args.input,
        output_dir=args.output_dir,
        contract_path=args.contract,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
