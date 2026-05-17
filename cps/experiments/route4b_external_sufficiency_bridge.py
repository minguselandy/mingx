from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.hashing import canonical_json_dumps
from cps.benchmarks.hashing import stable_hash


ROUTE4B_ID = "route4b_bridge_to_external_sufficiency"
ROUTE4B_PHASE_ID = "route4b_bridge_to_external_sufficiency"
ROUTE4B_PROTOCOL_ID = "route4b_hotpotqa_external_sufficiency_bridge_v1"
ACTIVE_STRATUM = "route4b_hotpotqa_external_sufficiency_bridge_v1"
TASK_FAMILY = "hotpotqa_answer_support_external_sufficiency_bridge"
EXTERNAL_UTILITY_SOURCE = "route6a_model_adjudicated_external_sufficiency"
CLAIM_STATUS = "no_claim_upgrade"
METRIC_CLAIM_LEVEL = "failed_closed_no_claim_upgrade"
DEFAULT_OUTPUT_DIR = "artifacts/experiments/route4b_bridge_to_measurement"
DEFAULT_ROUTE4_ROWS_PATH = "artifacts/experiments/route4_bridge/bridge_rows.jsonl"
DEFAULT_CONTEXT_PAIR_SAMPLE_PATH = "artifacts/experiments/route6a_measurement_pilot/context_pair_sample.jsonl"
DEFAULT_MODEL_LABELS_PATH = "artifacts/experiments/route6a_measurement_pilot/model_adjudicated_labels.jsonl"
DEFAULT_PROTOCOL_MD = "docs/experiments/Route4B-bridge-to-external-sufficiency-protocol.md"
DEFAULT_REPORT_MD = "docs/experiments/Route4B-bridge-to-external-sufficiency-report.md"

MIN_ROWS = 500
MIN_UNIQUE_INSTANCES = 150
MIN_EFFECTIVE_SAMPLE_SIZE = 100
MIN_SIGN_AGREEMENT = 0.70
MIN_SPEARMAN = 0.40
MAX_NORMALIZED_RESIDUAL = 0.50

SUFFICIENCY_SCORES = {
    "insufficient": 0.0,
    "partial": 0.5,
    "sufficient": 1.0,
}


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _stable_jsonl(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return ""
    return "\n".join(canonical_json_dumps(dict(row)) for row in rows) + "\n"


def _write_json(path: str | Path, payload: Any) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_stable_json(payload), encoding="utf-8")
    return output_path


def _write_jsonl(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_stable_jsonl(rows), encoding="utf-8")
    return output_path


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{input_path.name}: row {line_number} must be a JSON object")
        rows.append(payload)
    return rows


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.as_posix() if not candidate.is_absolute() else candidate.name


def _route4_row_identity_hash(row: Mapping[str, Any]) -> str:
    identity = {
        "active_stratum": str(row.get("active_stratum") or ""),
        "block_A_packet_ids": [str(item) for item in row.get("block_A_packet_ids") or []],
        "candidate_pool_hash": str(row.get("candidate_pool_hash") or ""),
        "context_L_packet_ids": [str(item) for item in row.get("context_L_packet_ids") or []],
        "instance_id": str(row.get("instance_id") or ""),
        "original_instance_id": str(row.get("original_instance_id") or ""),
        "phase_id": str(row.get("phase_id") or ""),
        "protocol_id": str(row.get("protocol_id") or ""),
        "split_id": str(row.get("split_id") or ""),
    }
    return stable_hash(identity)


def _score(label: Any) -> float | None:
    return SUFFICIENCY_SCORES.get(str(label or "").strip().lower())


def _label_is_usable(label: Mapping[str, Any]) -> bool:
    if str(label.get("delta_label") or "") == "invalid":
        return False
    if bool(label.get("counts_as_human_label")):
        return False
    if bool(label.get("measurement_validation_candidate_allowed")):
        return False
    if bool(label.get("raw_response_stored")):
        return False
    return _score(label.get("baseline_sufficiency")) is not None and _score(label.get("augmented_sufficiency")) is not None


def _sample_key(sample: Mapping[str, Any]) -> tuple[str, str]:
    return (str(sample.get("original_instance_id") or ""), str(sample.get("candidate_pool_hash") or ""))


def _route4_lookup(route4_rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    by_hash = {_route4_row_identity_hash(row): dict(row) for row in route4_rows}
    by_pool: dict[tuple[str, str], dict[str, Any]] = {}
    for row in route4_rows:
        key = (str(row.get("original_instance_id") or ""), str(row.get("candidate_pool_hash") or ""))
        by_pool.setdefault(key, dict(row))
    return by_hash, by_pool


def build_route4b_bridge_rows(
    *,
    route4_rows: Sequence[Mapping[str, Any]],
    context_pair_sample: Sequence[Mapping[str, Any]],
    model_labels: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    sample_by_id = {str(sample.get("sample_id") or ""): dict(sample) for sample in context_pair_sample}
    route4_by_hash, route4_by_pool = _route4_lookup(route4_rows)
    rows: list[dict[str, Any]] = []
    for label in sorted(model_labels, key=lambda row: str(row.get("sample_id") or "")):
        if not _label_is_usable(label):
            continue
        sample_id = str(label.get("sample_id") or "")
        sample = sample_by_id.get(sample_id)
        if not sample:
            continue
        source_ref = dict(sample.get("source_route4_row_ref") or {})
        route4_hash = str(source_ref.get("route4_row_identity_hash") or "")
        route4_row = route4_by_hash.get(route4_hash) if route4_hash else None
        if route4_row is None:
            route4_row = route4_by_pool.get(_sample_key(sample))
        if route4_row is None:
            continue
        baseline = _score(label.get("baseline_sufficiency"))
        augmented = _score(label.get("augmented_sufficiency"))
        if baseline is None or augmented is None:
            continue
        delta_external = round(augmented - baseline, 12)
        row = {
            "route_id": ROUTE4B_ID,
            "phase_id": ROUTE4B_PHASE_ID,
            "protocol_id": ROUTE4B_PROTOCOL_ID,
            "active_stratum": ACTIVE_STRATUM,
            "task_family": TASK_FAMILY,
            "dataset": "HotpotQA",
            "split": str(route4_row.get("split") or sample.get("split") or ""),
            "sample_id": sample_id,
            "original_instance_id": str(sample.get("original_instance_id") or route4_row.get("original_instance_id") or ""),
            "candidate_pool_hash": str(sample.get("candidate_pool_hash") or route4_row.get("candidate_pool_hash") or ""),
            "source_route4_row_identity_hash": _route4_row_identity_hash(route4_row),
            "source_route6a_label_schema_version": str(label.get("label_schema_version") or ""),
            "source_route6a_rubric_version": str(label.get("rubric_version") or ""),
            "target_y": str(sample.get("target_y") or route4_row.get("target_y") or ""),
            "context_L_packet_ids": [str(item) for item in route4_row.get("context_L_packet_ids") or []],
            "block_A_packet_ids": [str(item) for item in route4_row.get("block_A_packet_ids") or []],
            "block_size": int(route4_row.get("block_size") or 0),
            "budget": int(route4_row.get("budget") or 0),
            "candidate_slice_band": str(route4_row.get("candidate_slice_band") or ""),
            "materialization_policy": str(route4_row.get("materialization_policy") or ""),
            "decoding_policy": str(route4_row.get("decoding_policy") or ""),
            "model_tier": str(route4_row.get("model_tier") or ""),
            "evaluator_id": str(route4_row.get("evaluator_id") or ""),
            "delta_logloss": float(route4_row.get("delta_logloss") or 0.0),
            "delta_logloss_source": str(route4_row.get("delta_logloss_source") or "existing_route4a_answer_nll_delta_record"),
            "baseline_external_sufficiency_utility": baseline,
            "augmented_external_sufficiency_utility": augmented,
            "delta_external_sufficiency_utility": delta_external,
            "external_utility_source": EXTERNAL_UTILITY_SOURCE,
            "external_delta_label": str(label.get("delta_label") or ""),
            "external_answer_supported": str(label.get("answer_supported") or ""),
            "external_evidence_relevance": str(label.get("evidence_relevance") or ""),
            "external_uncertainty": str(label.get("uncertainty") or ""),
            "judge_model_id": str(label.get("judge_model_id") or ""),
            "judge_provider": str(label.get("judge_provider") or ""),
            "counts_as_human_label": False,
            "human_labels_present": False,
            "human_human_kappa_present": False,
            "measurement_validation_candidate_allowed": False,
            "raw_response_stored": False,
            "contamination_status": str(route4_row.get("contamination_status") or "unknown"),
            "metric_claim_level": METRIC_CLAIM_LEVEL,
            "claim_status": CLAIM_STATUS,
        }
        row["route4b_bridge_row_hash"] = stable_hash(row)
        rows.append(row)
    return sorted(rows, key=lambda row: (row["sample_id"], row["route4b_bridge_row_hash"]))


def _mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _rankdata(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0 for _ in values]
    index = 0
    while index < len(indexed):
        end = index
        while end + 1 < len(indexed) and indexed[end + 1][1] == indexed[index][1]:
            end += 1
        rank = (index + end + 2) / 2.0
        for offset in range(index, end + 1):
            ranks[indexed[offset][0]] = rank
        index = end + 1
    return ranks


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    x_mean = _mean(xs)
    y_mean = _mean(ys)
    if x_mean is None or y_mean is None:
        return None
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_den = math.sqrt(sum((x - x_mean) ** 2 for x in xs))
    y_den = math.sqrt(sum((y - y_mean) ** 2 for y in ys))
    if x_den == 0.0 or y_den == 0.0:
        return None
    return numerator / (x_den * y_den)


def _spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2:
        return None
    return _pearson(_rankdata(xs), _rankdata(ys))


def _fit_diagnostics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    xs = [float(row.get("delta_logloss") or 0.0) for row in rows]
    ys = [float(row.get("delta_external_sufficiency_utility") or 0.0) for row in rows]
    denominator = sum(x * x for x in xs)
    c_hat = sum(x * y for x, y in zip(xs, ys)) / denominator if denominator else None
    residuals = [(float(c_hat) * x) - y for x, y in zip(xs, ys)] if c_hat is not None else []
    residual_rms = math.sqrt(sum(residual * residual for residual in residuals) / len(residuals)) if residuals else None
    y_rms = math.sqrt(sum(y * y for y in ys) / len(ys)) if ys else None
    normalized_residual = residual_rms / y_rms if residual_rms is not None and y_rms not in {None, 0.0} else None
    sign_pairs = [(_sign(x), _sign(y)) for x, y in zip(xs, ys) if _sign(x) != 0 and _sign(y) != 0]
    sign_agreement = (
        sum(1 for x_sign, y_sign in sign_pairs if x_sign == y_sign) / len(sign_pairs)
        if sign_pairs
        else None
    )
    return {
        "c_hat_s": c_hat,
        "normalized_residual": normalized_residual,
        "sign_agreement": sign_agreement,
        "spearman_rho": _spearman(xs, ys),
    }


def fit_route4b_bridge(
    rows: Sequence[Mapping[str, Any]],
    *,
    min_rows: int = MIN_ROWS,
    min_unique_instances: int = MIN_UNIQUE_INSTANCES,
) -> dict[str, Any]:
    row_count = len(rows)
    unique_instances = len({str(row.get("original_instance_id") or "") for row in rows})
    effective_sample_size = row_count
    diagnostics = _fit_diagnostics(rows)
    gate_pass_flags = {
        "row_count_pass": row_count >= min_rows,
        "unique_instance_pass": unique_instances >= min_unique_instances,
        "effective_sample_size_pass": effective_sample_size >= MIN_EFFECTIVE_SAMPLE_SIZE,
        "sign_agreement_pass": (diagnostics["sign_agreement"] or 0.0) >= MIN_SIGN_AGREEMENT,
        "spearman_rho_pass": (diagnostics["spearman_rho"] or 0.0) >= MIN_SPEARMAN,
        "normalized_residual_pass": (
            diagnostics["normalized_residual"] is not None
            and diagnostics["normalized_residual"] <= MAX_NORMALIZED_RESIDUAL
        ),
    }
    reason_codes: list[str] = []
    if not gate_pass_flags["row_count_pass"]:
        reason_codes.append("row_count_below_minimum")
    if not gate_pass_flags["unique_instance_pass"]:
        reason_codes.append("unique_instance_below_minimum")
    if not gate_pass_flags["effective_sample_size_pass"]:
        reason_codes.append("effective_sample_size_below_minimum")
    if row_count:
        reason_codes.append("model_adjudication_not_human_measurement_validation")
    if not row_count:
        reason_codes.append("no_usable_route6a_model_labels")

    underpowered = any(
        not gate_pass_flags[name]
        for name in ("row_count_pass", "unique_instance_pass", "effective_sample_size_pass")
    )
    if underpowered:
        gate_result = "failed_closed_underpowered"
        calibration_run = False
    else:
        calibration_run = True
        metric_failures = [
            name
            for name in ("sign_agreement_pass", "spearman_rho_pass", "normalized_residual_pass")
            if not gate_pass_flags[name]
        ]
        if metric_failures:
            gate_result = "failed_closed_gate_failed"
            reason_codes.extend(name.replace("_pass", "_failed") for name in metric_failures)
        else:
            gate_result = "metric_bridge_support_candidate_pending_review"

    return {
        "phase_id": ROUTE4B_PHASE_ID,
        "active_stratum": ACTIVE_STRATUM,
        "claim_status": CLAIM_STATUS,
        "calibration_run": calibration_run,
        "rows_validated": row_count,
        "unique_original_instances": unique_instances,
        "effective_sample_size": effective_sample_size,
        "bridge_fit": diagnostics,
        "gate_pass_flags": gate_pass_flags,
        "gate_result": gate_result,
        "reason_codes": reason_codes,
        "metric_bridge_support_candidate": gate_result == "metric_bridge_support_candidate_pending_review",
        "calibrated_proxy_supported": False,
        "vinfo_proxy_supported": False,
        "measurement_validation": False,
        "paper_evidence": False,
        "metric_claim_level": METRIC_CLAIM_LEVEL,
    }


def _readiness_report(
    *,
    route4_rows: Sequence[Mapping[str, Any]],
    context_pair_sample: Sequence[Mapping[str, Any]],
    model_labels: Sequence[Mapping[str, Any]],
    bridge_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    usable_labels = sum(1 for label in model_labels if _label_is_usable(label))
    status = "ready_model_adjudicated_underpowered_bridge_attempt" if usable_labels else "blocked_route6a_labels_unavailable"
    return {
        "phase_id": ROUTE4B_PHASE_ID,
        "claim_status": CLAIM_STATUS,
        "status": status,
        "route4_rows_count": len(route4_rows),
        "route6a_sample_count": len(context_pair_sample),
        "route6a_label_count": len(model_labels),
        "route6a_usable_model_label_count": usable_labels,
        "bridge_rows_constructed": len(bridge_rows),
        "model_adjudication_counts_as_human_label": False,
        "human_labels_present": False,
        "human_human_kappa_present": False,
        "measurement_validation_candidate_allowed": False,
        "start_condition_satisfied": usable_labels > 0,
        "claim_status_ceiling": "operational_utility_only/no_claim_upgrade",
    }


def _control_results(fit: Mapping[str, Any]) -> dict[str, Any]:
    underpowered = str(fit.get("gate_result") or "") == "failed_closed_underpowered"
    return {
        "phase_id": ROUTE4B_PHASE_ID,
        "claim_status": CLAIM_STATUS,
        "control_status": "not_run_underpowered" if underpowered else "diagnostic_controls_required_before_review",
        "negative_controls": {
            "shuffled_external_utility_within_split": "not_run_underpowered" if underpowered else "not_implemented",
            "shuffled_delta_logloss_within_split": "not_run_underpowered" if underpowered else "not_implemented",
            "length_only_baseline": "not_run_underpowered" if underpowered else "not_implemented",
        },
        "positive_controls": {
            "circular_alignment_control": "not_run_underpowered" if underpowered else "not_metric_evidence",
        },
        "metric_bridge_support_candidate": False if underpowered else bool(fit.get("metric_bridge_support_candidate")),
    }


def _metric_bridge_witness(fit: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "artifact_type": "MetricBridgeWitness",
        "phase_id": ROUTE4B_PHASE_ID,
        "active_stratum": ACTIVE_STRATUM,
        "bridge_status": fit["gate_result"],
        "claim_level": "ambiguous_metric",
        "metric_claim_level": METRIC_CLAIM_LEVEL,
        "calibration_epoch": "route4b_model_adjudicated_external_sufficiency_v1",
        "fresh_for_route4b": False,
        "rows_validated": fit["rows_validated"],
        "unique_original_instances": fit["unique_original_instances"],
        "reason_codes": list(fit["reason_codes"]),
        "calibrated_proxy_supported": False,
        "vinfo_proxy_supported": False,
        "measurement_validation": False,
        "paper_evidence": False,
    }


def _claim_gate_result(fit: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "phase_id": ROUTE4B_PHASE_ID,
        "claim_status": CLAIM_STATUS,
        "gate_result": fit["gate_result"],
        "metric_bridge_support_candidate": bool(fit.get("metric_bridge_support_candidate")),
        "calibrated_proxy_supported": False,
        "vinfo_proxy_supported": False,
        "measurement_validation": False,
        "paper_evidence": False,
        "denied_claims": [
            "calibrated_proxy_supported",
            "vinfo_proxy_supported",
            "measurement validation",
            "human-label validation",
            "human-human kappa",
            "paper evidence",
            "metric bridge support",
            "global selector superiority",
            "deployed V-information verification",
        ],
    }


def _write_protocol(path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(
            [
                "# Route 4B Bridge to External Sufficiency Protocol",
                "",
                "Status: model-adjudicated pilot protocol",
                "Claim status: `no_claim_upgrade`",
                "",
                "Route 4B joins fixed Route 4A answer-NLL deltas to Route 6A external sufficiency labels.",
                "The external utility is derived only from normalized Route 6A label enums, not from logloss, gold support labels, or Route 4 utility scores.",
                "",
                "## Gates",
                "",
                f"- Minimum rows: `{MIN_ROWS}`",
                f"- Minimum unique original instances: `{MIN_UNIQUE_INSTANCES}`",
                f"- Minimum effective sample size: `{MIN_EFFECTIVE_SAMPLE_SIZE}`",
                f"- Sign agreement: `>= {MIN_SIGN_AGREEMENT}`",
                f"- Spearman rho: `>= {MIN_SPEARMAN}`",
                f"- Normalized residual: `<= {MAX_NORMALIZED_RESIDUAL}`",
                "",
                "Model-adjudicated labels do not count as human labels and do not permit measurement validation or human-human kappa claims.",
                "Any underpowered or failed gate result remains `no_claim_upgrade`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return output


def _write_report(path: str | Path, *, readiness: Mapping[str, Any], fit: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(
            [
                "# Route 4B Bridge to External Sufficiency Report",
                "",
                f"Status: {fit['gate_result']}",
                "Claim status: `no_claim_upgrade`",
                "",
                "## Inputs",
                "",
                f"- Route 4A rows: `{readiness['route4_rows_count']}`",
                f"- Route 6A samples: `{readiness['route6a_sample_count']}`",
                f"- Route 6A normalized labels: `{readiness['route6a_label_count']}`",
                f"- Usable model labels: `{readiness['route6a_usable_model_label_count']}`",
                f"- Bridge rows constructed: `{readiness['bridge_rows_constructed']}`",
                "",
                "## Gate Result",
                "",
                f"- Rows validated: `{fit['rows_validated']}`",
                f"- Unique original instances: `{fit['unique_original_instances']}`",
                f"- Gate result: `{fit['gate_result']}`",
                f"- Reason codes: `{', '.join(fit['reason_codes'])}`",
                "",
                "## Claim Boundary",
                "",
                "- `calibrated_proxy_supported`: denied",
                "- `vinfo_proxy_supported`: denied",
                "- measurement validation: denied",
                "- paper evidence: denied",
                "- `operational_utility_only / no_claim_upgrade` remains active.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return output


def run_route4b_pipeline(
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    route4_rows_path: str | Path = DEFAULT_ROUTE4_ROWS_PATH,
    context_pair_sample_path: str | Path = DEFAULT_CONTEXT_PAIR_SAMPLE_PATH,
    model_labels_path: str | Path = DEFAULT_MODEL_LABELS_PATH,
    protocol_md_path: str | Path = DEFAULT_PROTOCOL_MD,
    report_md_path: str | Path = DEFAULT_REPORT_MD,
) -> dict[str, Any]:
    route4_rows = _read_jsonl(route4_rows_path)
    context_pair_sample = _read_jsonl(context_pair_sample_path)
    model_labels = _read_jsonl(model_labels_path)
    bridge_rows = build_route4b_bridge_rows(
        route4_rows=route4_rows,
        context_pair_sample=context_pair_sample,
        model_labels=model_labels,
    )
    fit = fit_route4b_bridge(bridge_rows)
    readiness = _readiness_report(
        route4_rows=route4_rows,
        context_pair_sample=context_pair_sample,
        model_labels=model_labels,
        bridge_rows=bridge_rows,
    )
    controls = _control_results(fit)
    witness = _metric_bridge_witness(fit)
    claim_gate = _claim_gate_result(fit)

    output_path = Path(output_dir)
    _write_json(output_path / "route4b_readiness_report.json", readiness)
    _write_jsonl(output_path / "bridge_rows.jsonl", bridge_rows)
    _write_json(output_path / "bridge_fit_summary.json", fit)
    _write_json(output_path / "control_results.json", controls)
    _write_json(output_path / "metric_bridge_witness.json", witness)
    _write_json(output_path / "claim_gate_result.json", claim_gate)
    _write_protocol(protocol_md_path)
    _write_report(report_md_path, readiness=readiness, fit=fit)

    return {
        "status": fit["gate_result"],
        "claim_status": CLAIM_STATUS,
        "rows_validated": fit["rows_validated"],
        "unique_original_instances": fit["unique_original_instances"],
        "metric_bridge_support_candidate": bool(fit.get("metric_bridge_support_candidate")),
        "calibrated_proxy_supported": False,
        "vinfo_proxy_supported": False,
        "measurement_validation": False,
        "paper_evidence": False,
        "artifacts": {
            "route4b_readiness_report": _path_ref(output_path / "route4b_readiness_report.json"),
            "bridge_rows": _path_ref(output_path / "bridge_rows.jsonl"),
            "bridge_fit_summary": _path_ref(output_path / "bridge_fit_summary.json"),
            "control_results": _path_ref(output_path / "control_results.json"),
            "metric_bridge_witness": _path_ref(output_path / "metric_bridge_witness.json"),
            "claim_gate_result": _path_ref(output_path / "claim_gate_result.json"),
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Route 4B bridge to external sufficiency utility.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--route4-rows", default=DEFAULT_ROUTE4_ROWS_PATH)
    parser.add_argument("--context-pair-sample", default=DEFAULT_CONTEXT_PAIR_SAMPLE_PATH)
    parser.add_argument("--model-labels", default=DEFAULT_MODEL_LABELS_PATH)
    parser.add_argument("--protocol-md", default=DEFAULT_PROTOCOL_MD)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    args = parser.parse_args(argv)
    result = run_route4b_pipeline(
        output_dir=args.output_dir,
        route4_rows_path=args.route4_rows,
        context_pair_sample_path=args.context_pair_sample,
        model_labels_path=args.model_labels,
        protocol_md_path=args.protocol_md,
        report_md_path=args.report_md,
    )
    print(
        canonical_json_dumps(
            {
                "status": result["status"],
                "claim_status": result["claim_status"],
                "rows_validated": result["rows_validated"],
                "metric_bridge_support_candidate": result["metric_bridge_support_candidate"],
                "calibrated_proxy_supported": result["calibrated_proxy_supported"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
