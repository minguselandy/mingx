from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.experiments.bridge_row_schema import ACTIVE_STRATUM
from cps.experiments.bridge_row_schema import BridgeRowKey
from cps.experiments.bridge_row_schema import HOTPOTQA_DATASET
from cps.experiments.bridge_row_schema import HOTPOTQA_TASK_FAMILY
from cps.experiments.bridge_row_schema import bridge_row_key
from cps.experiments.bridge_row_validation import validate_bridge_rows


DEFAULT_INPUT_ROWS_PATH = "artifacts/operator_inputs/p55_evidence_packet_selection_microtask_v1_rows.jsonl"
DEFAULT_OUTPUT_DIR = "artifacts/experiments/p55_hotpotqa_bridge_calibration"
DEFAULT_REPORT_MD = "docs/experiments/P63R-hotpotqa-real-bridge-calibration-report.md"
DEFAULT_EVALUATOR_ID = (
    "approved_live_api_logprob_endpoint::dashscope::qwen3.6-flash"
    "::deterministic_logprob_scoring_v1"
)
DEFAULT_CALIBRATION_EPOCH = "P63R-HotpotQA-qwen36flash-600x150-v1"
FIT_METHOD = "train_split_ols_through_origin"
METRIC_FAMILY = "hotpotqa_answer_logloss_to_supporting_fact_recall_delta"


class P63RCalibrationError(ValueError):
    """Raised when P63R HotpotQA calibration input or configuration is invalid."""


@dataclass(frozen=True)
class P63RCalibrationConfig:
    min_rows_validated: int = 500
    min_unique_instances: int = 150
    heldout_fraction: float = 0.30
    min_sign_agreement: float = 0.70
    min_spearman_rho: float = 0.40
    min_effective_sample_size: int = 100
    max_normalized_residual: float = 0.50
    calibration_epoch: str = DEFAULT_CALIBRATION_EPOCH
    evaluator_id: str = DEFAULT_EVALUATOR_ID
    active_stratum: str = ACTIVE_STRATUM
    dataset: str = HOTPOTQA_DATASET
    task_family: str = HOTPOTQA_TASK_FAMILY
    metric_family: str = METRIC_FAMILY


@dataclass(frozen=True)
class CalibrationSplit:
    train_rows: tuple[dict[str, Any], ...]
    heldout_rows: tuple[dict[str, Any], ...]
    heldout_fraction: float
    split_policy: str


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_canonical_json(dict(payload)), encoding="utf-8")
    return output_path


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate.name
    return candidate.as_posix()


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    if not input_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//")):
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise P63RCalibrationError(f"{input_path.name}: row {line_number} must be a JSON object")
        rows.append(payload)
    return rows


def _sort_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in sorted(rows, key=bridge_row_key)]


def split_train_heldout(
    rows: Sequence[Mapping[str, Any]],
    *,
    heldout_fraction: float,
) -> CalibrationSplit:
    if not 0.0 < heldout_fraction < 1.0:
        raise P63RCalibrationError("heldout_fraction must be between 0 and 1")
    sorted_rows = _sort_rows(rows)
    if not sorted_rows:
        return CalibrationSplit((), (), 0.0, "stable_bridge_row_key_tail_holdout")
    heldout_count = max(1, int(round(len(sorted_rows) * heldout_fraction)))
    if heldout_count >= len(sorted_rows):
        heldout_count = max(0, len(sorted_rows) - 1)
    train_rows = tuple(sorted_rows[: len(sorted_rows) - heldout_count])
    heldout_rows = tuple(sorted_rows[len(sorted_rows) - heldout_count :])
    actual_fraction = len(heldout_rows) / len(sorted_rows) if sorted_rows else 0.0
    return CalibrationSplit(
        train_rows=train_rows,
        heldout_rows=heldout_rows,
        heldout_fraction=actual_fraction,
        split_policy="stable_bridge_row_key_tail_holdout",
    )


def _mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _through_origin_scale(rows: Sequence[Mapping[str, Any]]) -> float | None:
    denominator = sum(float(row["delta_logloss"]) ** 2 for row in rows)
    if denominator == 0.0:
        return None
    numerator = sum(float(row["delta_logloss"]) * float(row["delta_utility"]) for row in rows)
    return numerator / denominator


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


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


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2:
        return None
    x_mean = _mean(xs)
    y_mean = _mean(ys)
    if x_mean is None or y_mean is None:
        return None
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = math.sqrt(
        sum((x - x_mean) ** 2 for x in xs) * sum((y - y_mean) ** 2 for y in ys)
    )
    if denominator == 0.0:
        return None
    return numerator / denominator


def _spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2:
        return None
    return _pearson(_average_ranks(xs), _average_ranks(ys))


def _unique_instances(rows: Sequence[Mapping[str, Any]]) -> int:
    return len({str(row.get("instance_id", "")) for row in rows if str(row.get("instance_id", "")).strip()})


def _effective_sample_size(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(int(row.get("replicate_count", 0)) for row in rows)


def _row_key_strings(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    def key_to_string(key: BridgeRowKey) -> str:
        return json.dumps(asdict(key), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    return [key_to_string(bridge_row_key(row)) for row in rows]


def _empty_fit(
    *,
    rows_imported: int,
    config: P63RCalibrationConfig,
    reason_codes: Sequence[str],
    gate_result: str,
) -> dict[str, Any]:
    metric_claim_level = "ambiguous_metric"
    return {
        "active_stratum": config.active_stratum,
        "bridge_fit": {
            "c_hat_s": None,
            "fit_method": FIT_METHOD,
            "mean_absolute_residual": None,
            "normalized_residual": None,
            "spearman_rho": None,
            "zeta_hat_s": None,
        },
        "calibrated_proxy_supported_candidate": False,
        "calibration_epoch": config.calibration_epoch,
        "claim_status": "ambiguous_metric; no_claim_upgrade",
        "dataset": config.dataset,
        "effective_sample_size": 0,
        "evaluator_id": config.evaluator_id,
        "gate_pass_flags": {
            "effective_sample_size_pass": False,
            "fit_denominator_pass": False,
            "heldout_fraction_pass": False,
            "normalized_residual_pass": False,
            "row_count_pass": False,
            "sign_agreement_pass": False,
            "spearman_rho_pass": False,
            "unique_instance_pass": False,
        },
        "gate_result": gate_result,
        "heldout_fraction": 0.0,
        "heldout_rows": 0,
        "metric_claim_level": metric_claim_level,
        "metric_family": config.metric_family,
        "reason_codes": sorted(set(reason_codes)),
        "rows_imported": rows_imported,
        "rows_validated": 0,
        "sign_agreement": None,
        "split_policy": "stable_bridge_row_key_tail_holdout",
        "task_family": config.task_family,
        "thresholds": asdict(config),
        "train_rows": 0,
        "unique_instances": 0,
    }


def fit_calibration(
    rows: Sequence[Mapping[str, Any]],
    *,
    config: P63RCalibrationConfig | None = None,
) -> dict[str, Any]:
    config = config or P63RCalibrationConfig()
    validation = validate_bridge_rows(rows)
    if not rows:
        return _empty_fit(
            rows_imported=0,
            config=config,
            reason_codes=["no_operator_rows"],
            gate_result="failed_closed_no_rows",
        )
    if not validation.schema_valid:
        return _empty_fit(
            rows_imported=len(rows),
            config=config,
            reason_codes=["row_schema_invalid", *validation.errors],
            gate_result="failed_closed_gate_failed",
        )

    sorted_rows = _sort_rows(rows)
    unique_instances = _unique_instances(sorted_rows)
    effective_sample_size = _effective_sample_size(sorted_rows)
    split = split_train_heldout(sorted_rows, heldout_fraction=config.heldout_fraction)
    c_hat_s = _through_origin_scale(split.train_rows)
    predictions: list[float] = []
    actuals: list[float] = []
    residuals: list[float] = []
    residual_rows: list[dict[str, Any]] = []
    for row in split.heldout_rows:
        actual = float(row["delta_utility"])
        predicted = None if c_hat_s is None else c_hat_s * float(row["delta_logloss"])
        if predicted is None:
            continue
        residual = actual - predicted
        predictions.append(predicted)
        actuals.append(actual)
        residuals.append(abs(residual))
        residual_rows.append(
            {
                "absolute_residual": abs(residual),
                "block_A_packet_ids": list(row["block_A_packet_ids"]),
                "delta_logloss": float(row["delta_logloss"]),
                "delta_utility": actual,
                "fitted_delta_utility": predicted,
                "instance_id": str(row["instance_id"]),
                "residual": residual,
                "row_key": json.loads(_row_key_strings([row])[0]),
            }
        )

    zeta_hat_s = max(residuals) if residuals else None
    mean_abs_residual = _mean(residuals)
    mean_abs_utility = _mean([abs(float(row["delta_utility"])) for row in split.heldout_rows])
    normalized_residual = None
    if zeta_hat_s is not None and mean_abs_utility is not None:
        normalized_residual = zeta_hat_s / max(mean_abs_utility, 1e-12)
    sign_agreement = None
    if split.heldout_rows:
        sign_agreement = sum(
            _sign(float(row["delta_logloss"])) == _sign(float(row["delta_utility"]))
            for row in split.heldout_rows
        ) / len(split.heldout_rows)
    spearman_rho = _spearman(predictions, actuals)

    pass_flags = {
        "row_count_pass": validation.rows_validated >= config.min_rows_validated,
        "unique_instance_pass": unique_instances >= config.min_unique_instances,
        "heldout_fraction_pass": split.heldout_fraction >= config.heldout_fraction,
        "effective_sample_size_pass": effective_sample_size >= config.min_effective_sample_size,
        "fit_denominator_pass": c_hat_s is not None,
        "normalized_residual_pass": (
            normalized_residual is not None and normalized_residual <= config.max_normalized_residual
        ),
        "sign_agreement_pass": sign_agreement is not None and sign_agreement >= config.min_sign_agreement,
        "spearman_rho_pass": spearman_rho is not None and spearman_rho >= config.min_spearman_rho,
    }
    reason_codes = sorted(flag.replace("_pass", "_failed") for flag, passed in pass_flags.items() if not passed)
    underpowered_flags = {
        "row_count_pass",
        "unique_instance_pass",
        "heldout_fraction_pass",
        "effective_sample_size_pass",
    }
    if any(not pass_flags[flag] for flag in underpowered_flags):
        gate_result = "failed_closed_underpowered"
        metric_claim_level = "ambiguous_metric"
        claim_status = "ambiguous_metric; no_claim_upgrade"
        candidate = False
    elif all(pass_flags.values()):
        gate_result = "calibrated_proxy_supported_candidate"
        metric_claim_level = "calibrated_proxy_supported_candidate"
        claim_status = "calibrated_proxy_supported_candidate_pending_review"
        candidate = True
    else:
        gate_result = "failed_closed_gate_failed"
        metric_claim_level = "operational_utility_only"
        claim_status = "operational_utility_only; no_claim_upgrade"
        candidate = False

    return {
        "active_stratum": config.active_stratum,
        "bridge_fit": {
            "c_hat_s": c_hat_s,
            "fit_method": FIT_METHOD,
            "heldout_residual_rows": residual_rows,
            "mean_absolute_residual": mean_abs_residual,
            "normalized_residual": normalized_residual,
            "spearman_rho": spearman_rho,
            "zeta_hat_s": zeta_hat_s,
        },
        "calibrated_proxy_supported_candidate": candidate,
        "calibration_epoch": config.calibration_epoch,
        "claim_status": claim_status,
        "dataset": config.dataset,
        "effective_sample_size": effective_sample_size,
        "evaluator_id": config.evaluator_id,
        "gate_pass_flags": pass_flags,
        "gate_result": gate_result,
        "heldout_fraction": split.heldout_fraction,
        "heldout_rows": len(split.heldout_rows),
        "metric_claim_level": metric_claim_level,
        "metric_family": config.metric_family,
        "reason_codes": reason_codes,
        "rows_imported": len(rows),
        "rows_validated": validation.rows_validated,
        "sign_agreement": sign_agreement,
        "split_policy": split.split_policy,
        "task_family": config.task_family,
        "thresholds": {
            **asdict(config),
            "max_normalized_residual_pre_run_configured": True,
        },
        "train_rows": len(split.train_rows),
        "unique_instances": unique_instances,
    }


def _import_report(
    *,
    input_rows_jsonl: str | Path,
    rows_imported: int,
    fit: Mapping[str, Any],
    validation_errors: Sequence[str],
) -> dict[str, Any]:
    return {
        "active_stratum": fit["active_stratum"],
        "calibration_epoch": fit["calibration_epoch"],
        "dataset": fit["dataset"],
        "input_rows_path": _path_ref(input_rows_jsonl),
        "n_rows_imported": rows_imported,
        "n_rows_validated": fit["rows_validated"],
        "n_unique_instances": fit["unique_instances"],
        "phase": "P63R",
        "rows_imported": rows_imported,
        "rows_validated": fit["rows_validated"],
        "schema_valid": not validation_errors,
        "task_family": fit["task_family"],
        "validation_errors": list(validation_errors),
    }


def _bridge_fit_summary(fit: Mapping[str, Any]) -> dict[str, Any]:
    bridge_fit = dict(fit["bridge_fit"])
    return {
        "active_stratum": fit["active_stratum"],
        "calibration_epoch": fit["calibration_epoch"],
        "dataset": fit["dataset"],
        "effective_sample_size": fit["effective_sample_size"],
        "evaluator_id": fit["evaluator_id"],
        "gate_pass_flags": dict(fit["gate_pass_flags"]),
        "gate_result": fit["gate_result"],
        "heldout_fraction": fit["heldout_fraction"],
        "heldout_rows": fit["heldout_rows"],
        "metric_claim_level": fit["metric_claim_level"],
        "reason_codes": list(fit["reason_codes"]),
        "sign_agreement": fit["sign_agreement"],
        "spearman_rho": bridge_fit["spearman_rho"],
        "task_family": fit["task_family"],
        "thresholds": dict(fit["thresholds"]),
        "train_rows": fit["train_rows"],
        "unique_instances": fit["unique_instances"],
        **bridge_fit,
    }


def _metric_bridge_witness(fit: Mapping[str, Any], output_dir: str | Path) -> dict[str, Any]:
    bridge_fit = dict(fit["bridge_fit"])
    return {
        "active_stratum": fit["active_stratum"],
        "calibrated_proxy_supported": False,
        "calibrated_proxy_supported_candidate": bool(fit["calibrated_proxy_supported_candidate"]),
        "calibration_epoch": fit["calibration_epoch"],
        "claim_status": fit["claim_status"],
        "dataset": fit["dataset"],
        "deployed_v_information_verification": False,
        "effective_sample_size": fit["effective_sample_size"],
        "evaluator_id": fit["evaluator_id"],
        "gate_result": fit["gate_result"],
        "measurement_validation": False,
        "metric_claim_level": fit["metric_claim_level"],
        "metric_family": fit["metric_family"],
        "n_rows_validated": fit["rows_validated"],
        "n_unique_instances": fit["unique_instances"],
        "normalized_residual": bridge_fit["normalized_residual"],
        "output_dir": _path_ref(output_dir),
        "paper_evidence": False,
        "p56_status": "no_imported_traces",
        "phase": "P63R",
        "reason_codes": list(fit["reason_codes"]),
        "sign_agreement": fit["sign_agreement"],
        "spearman_rho": bridge_fit["spearman_rho"],
        "task_family": fit["task_family"],
        "vinfo_proxy_supported": False,
        "witness_schema_version": "metric_bridge_witness.p63r_hotpotqa.v1",
        "zeta_hat_s": bridge_fit["zeta_hat_s"],
    }


def _markdown_report(fit: Mapping[str, Any]) -> str:
    bridge_fit = dict(fit["bridge_fit"])
    reason_codes = list(fit["reason_codes"])
    lines = [
        "# P63R HotpotQA Real Bridge Calibration Report",
        "",
        "## Summary",
        "",
        f"- Dataset: `{fit['dataset']}`",
        f"- Task family: `{fit['task_family']}`",
        f"- Active stratum: `{fit['active_stratum']}`",
        f"- Calibration epoch: `{fit['calibration_epoch']}`",
        f"- Gate result: `{fit['gate_result']}`",
        f"- Metric claim level: `{fit['metric_claim_level']}`",
        f"- Claim status: `{fit['claim_status']}`",
        f"- Rows validated: `{fit['rows_validated']}`",
        f"- Unique instances: `{fit['unique_instances']}`",
        f"- P56 status: `no_imported_traces`",
        "",
        "## Fit Metrics",
        "",
        f"- Train rows: `{fit['train_rows']}`",
        f"- Heldout rows: `{fit['heldout_rows']}`",
        f"- Heldout fraction: `{fit['heldout_fraction']}`",
        f"- `c_hat_s`: `{bridge_fit['c_hat_s']}`",
        f"- `zeta_hat_s`: `{bridge_fit['zeta_hat_s']}`",
        f"- Normalized residual: `{bridge_fit['normalized_residual']}`",
        f"- Sign agreement: `{fit['sign_agreement']}`",
        f"- Spearman rho: `{bridge_fit['spearman_rho']}`",
        f"- Effective sample size: `{fit['effective_sample_size']}`",
        "",
        "## Gate Reasons",
        "",
    ]
    lines.extend(f"- `{reason}`" for reason in reason_codes) if reason_codes else lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- This is a HotpotQA stratum-local P63R calibration run.",
            "- Passing gates would only produce `calibrated_proxy_supported_candidate` pending independent review.",
            "- No final `calibrated_proxy_supported` claim is introduced here.",
            "- No `vinfo_proxy_supported` claim is introduced here.",
            "- No measurement validation, human-label validation, human-human kappa, deployed V-information verification, or paper evidence claim is introduced here.",
            "- P56 remains `no_imported_traces`.",
            "",
        ]
    )
    return "\n".join(lines)


def run_p63r_hotpotqa_bridge_calibration(
    *,
    input_rows_jsonl: str | Path = DEFAULT_INPUT_ROWS_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    report_md: str | Path | None = None,
    config: P63RCalibrationConfig | None = None,
) -> dict[str, Any]:
    config = config or P63RCalibrationConfig()
    rows = _read_jsonl(input_rows_jsonl)
    validation = validate_bridge_rows(rows)
    validation_errors = list(validation.errors)
    fit = fit_calibration(rows, config=config)
    resolved_output_dir = Path(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    import_report = _import_report(
        input_rows_jsonl=input_rows_jsonl,
        rows_imported=len(rows),
        fit=fit,
        validation_errors=validation_errors,
    )
    fit_summary = _bridge_fit_summary(fit)
    witness = _metric_bridge_witness(fit, resolved_output_dir)
    _write_json(resolved_output_dir / "import_report.json", import_report)
    _write_json(resolved_output_dir / "bridge_fit_summary.json", fit_summary)
    _write_json(resolved_output_dir / "metric_bridge_witness.json", witness)
    report_text = _markdown_report(fit)
    if report_md is not None:
        report_path = Path(report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_text, encoding="utf-8")

    return {
        "artifacts": {
            "bridge_fit_summary": _path_ref(resolved_output_dir / "bridge_fit_summary.json"),
            "import_report": _path_ref(resolved_output_dir / "import_report.json"),
            "metric_bridge_witness": _path_ref(resolved_output_dir / "metric_bridge_witness.json"),
            **({"report_md": _path_ref(report_md)} if report_md is not None else {}),
        },
        "calibration_epoch": fit["calibration_epoch"],
        "claim_status": fit["claim_status"],
        "gate_result": fit["gate_result"],
        "heldout_fraction": fit["heldout_fraction"],
        "metric_claim_level": fit["metric_claim_level"],
        "normalized_residual": fit["bridge_fit"]["normalized_residual"],
        "rows_imported": fit["rows_imported"],
        "rows_validated": fit["rows_validated"],
        "sign_agreement": fit["sign_agreement"],
        "spearman_rho": fit["bridge_fit"]["spearman_rho"],
        "unique_instances": fit["unique_instances"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run P63R HotpotQA P55 bridge calibration.")
    parser.add_argument("--input-rows-jsonl", default=DEFAULT_INPUT_ROWS_PATH)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    args = parser.parse_args(argv)
    result = run_p63r_hotpotqa_bridge_calibration(
        input_rows_jsonl=args.input_rows_jsonl,
        output_dir=args.output_dir,
        report_md=args.report_md,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
