from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.common import read_jsonl
from cps.benchmarks.common import write_json
from cps.evaluators.logloss import evaluate_logloss_shadow
from cps.evaluators.workbench_types import EvaluationRequest


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
TERMINAL_STATUS = "LOGPROBE_BRIDGE_AUDIT_COMPLETED"
DEFAULT_OUTPUT_DIR = Path("artifacts/experiments/logprobe_bridge_audit")

MIN_BRIDGE_ROWS = 500
MIN_UNIQUE_INSTANCES = 150

REQUIRED_INPUTS: dict[str, Path] = {
    "hotpotqa_answer_nll_generation_report": Path("artifacts/benchmarks/hotpotqa_p55_delta_generation_report.json"),
    "hotpotqa_support_classification_generation_report": Path(
        "artifacts/benchmarks/hotpotqa_support_classification_delta_generation_report.json"
    ),
    "route4a_bridge_fit_summary": Path("artifacts/experiments/route4_bridge/bridge_fit_summary.json"),
    "route4a_bridge_rows": Path("artifacts/experiments/route4_bridge/bridge_rows.jsonl"),
    "route4b_bridge_fit_summary": Path(
        "artifacts/experiments/route4b_bridge_to_measurement/bridge_fit_summary.json"
    ),
    "route4b_bridge_rows": Path("artifacts/experiments/route4b_bridge_to_measurement/bridge_rows.jsonl"),
    "route6b_adjudication_report": Path("artifacts/experiments/route6b_measurement_scaleup/adjudication_report.json"),
    "route6b_readiness_report": Path("artifacts/experiments/route6b_measurement_scaleup/readiness_report.json"),
    "route6b_sample_manifest": Path("artifacts/experiments/route6b_measurement_scaleup/sample_manifest.json"),
    "delta_final_status": Path("artifacts/experiments/delta_strong_model_adjudication/final_status.json"),
    "delta_judge_reliability_audit": Path(
        "artifacts/experiments/delta_strong_model_adjudication/judge_reliability_audit.json"
    ),
    "delta_model_adjudication_scaleup_report": Path(
        "artifacts/experiments/delta_strong_model_adjudication/model_adjudication_scaleup_report.json"
    ),
    "delta_route4e_bridge_fit_summary": Path(
        "artifacts/experiments/delta_strong_model_adjudication/route4e_bridge_fit_summary.json"
    ),
    "delta_route4e_bridge_rows": Path("artifacts/experiments/delta_strong_model_adjudication/route4e_bridge_rows.jsonl"),
    "delta_route4e_metric_bridge_witness": Path(
        "artifacts/experiments/delta_strong_model_adjudication/route4e_metric_bridge_witness.json"
    ),
    "delta_route4e_negative_controls": Path(
        "artifacts/experiments/delta_strong_model_adjudication/route4e_negative_controls.json"
    ),
    "route5_readiness_report": Path("artifacts/experiments/route5_fixed_model_logloss_proxy/readiness_report.json"),
    "workbench_hotpotqa_smoke_bridge_fit_summary": Path(
        "artifacts/experiments/integrated_validation_workbench/hotpotqa_smoke/bridge_fit_summary.json"
    ),
    "workbench_hotpotqa_smoke_claim_gate_result": Path(
        "artifacts/experiments/integrated_validation_workbench/hotpotqa_smoke/claim_gate_result.json"
    ),
    "gamma_workbench_hotpotqa_bridge_fit_summary": Path(
        "artifacts/experiments/gamma_operational_expansion/workbench_hotpotqa/bridge_fit_summary.json"
    ),
    "gamma_workbench_hotpotqa_claim_gate_result": Path(
        "artifacts/experiments/gamma_operational_expansion/workbench_hotpotqa/claim_gate_result.json"
    ),
    "gamma_workbench_project_native_bridge_fit_summary": Path(
        "artifacts/experiments/gamma_operational_expansion/workbench_project_native/bridge_fit_summary.json"
    ),
    "gamma_workbench_project_native_claim_gate_result": Path(
        "artifacts/experiments/gamma_operational_expansion/workbench_project_native/claim_gate_result.json"
    ),
}

OPTIONAL_INPUTS: dict[str, Path] = {
    "route8_readiness_report": Path("artifacts/experiments/route8_final_integration/readiness_report.json"),
    "route8_integration_gate_report": Path("artifacts/experiments/route8_final_integration/integration_gate_report.json"),
    "route8_evidence_status_summary": Path(
        "artifacts/experiments/route8_final_integration/evidence_status_summary.json"
    ),
}

DENIED_CLAIMS = (
    "measurement_validation",
    "metric_bridge_support",
    "calibrated_proxy_supported",
    "vinfo_proxy_supported",
    "paper_evidence",
    "selector_superiority",
    "deployed_v_information_verification",
)


class LogProbeAuditInputMissingError(RuntimeError):
    """Raised before writing outputs when an audit-required artifact is absent."""


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _resolve(root: str | Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else Path(root) / candidate


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.name if candidate.is_absolute() else candidate.as_posix()


def _load_inputs(root: str | Path) -> dict[str, Any]:
    missing = [name for name, path in REQUIRED_INPUTS.items() if not _resolve(root, path).exists()]
    if missing:
        raise LogProbeAuditInputMissingError("missing required LogProbe audit inputs: " + ", ".join(sorted(missing)))

    loaded: dict[str, Any] = {}
    for name, path in REQUIRED_INPUTS.items():
        resolved = _resolve(root, path)
        loaded[name] = read_jsonl(resolved) if resolved.suffix == ".jsonl" else _read_json(resolved)
    for name, path in OPTIONAL_INPUTS.items():
        resolved = _resolve(root, path)
        loaded[name] = _read_json(resolved) if resolved.exists() else {}
    return loaded


def _float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _mean(values: Sequence[float]) -> float | None:
    return round(sum(values) / len(values), 12) if values else None


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


def _nested(payload: Mapping[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _count_failures(report: Mapping[str, Any]) -> dict[str, int]:
    failures = report.get("api_failures") or []
    if not isinstance(failures, list):
        failures = []
    target_terms = ("expected", "label", "unsupported", "token", "verbal", "classification")
    network_terms = ("timeout", "network", "connection", "remote", "rate limit", "read timed out")
    target_count = 0
    network_count = 0
    for failure in failures:
        text = json.dumps(failure, sort_keys=True).casefold()
        if any(term in text for term in target_terms):
            target_count += 1
        if any(term in text for term in network_terms):
            network_count += 1
    return {
        "api_failure_count": len(failures),
        "network_failure_count": network_count,
        "target_verbalization_failure_count": target_count,
    }


def _generation_summary(name: str, report: Mapping[str, Any]) -> dict[str, Any]:
    failure_counts = _count_failures(report)
    evaluator = report.get("evaluator") if isinstance(report.get("evaluator"), Mapping) else {}
    score_calls = int(report.get("api_score_calls") or report.get("score_calls") or 0)
    return {
        "api_retries": int(report.get("api_retries") or 0),
        "delta_records_validated": int(report.get("delta_records_validated") or report.get("records_validated") or 0),
        "evaluator_id": str(evaluator.get("evaluator_id") or ""),
        "model_name": str(evaluator.get("model_name") or ""),
        "name": name,
        "score_calls": score_calls,
        **failure_counts,
    }


def _route_alignment_summary(
    *,
    route_id: str,
    fit: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    utility_field: str,
) -> dict[str, Any]:
    pairs: list[tuple[float, float]] = []
    for row in rows:
        delta_logloss = _float(row.get("delta_logloss"))
        delta_utility = _float(row.get(utility_field))
        if delta_logloss is None or delta_utility is None:
            continue
        pairs.append((delta_logloss, delta_utility))
    delta_logloss_values = [pair[0] for pair in pairs]
    delta_utility_values = [pair[1] for pair in pairs]
    sign_matches = sum(1 for logloss, utility in pairs if _sign(logloss) == _sign(utility))
    row_count = int(fit.get("rows_validated") or len(rows))
    unique_instances = int(fit.get("unique_original_instances") or len({str(row.get("original_instance_id") or "") for row in rows}))
    reason_codes = [str(item) for item in fit.get("reason_codes") or []]
    gate_pass_flags = dict(fit.get("gate_pass_flags") or {})
    normalized_residual = _float(fit.get("normalized_residual"))
    if normalized_residual is None:
        normalized_residual = _float(_nested(fit, "bridge_fit", "normalized_residual"))
    fitted_sign_agreement = _float(fit.get("sign_agreement"))
    if fitted_sign_agreement is None:
        fitted_sign_agreement = _float(_nested(fit, "bridge_fit", "sign_agreement"))
    fitted_spearman = _float(fit.get("spearman_rho"))
    if fitted_spearman is None:
        fitted_spearman = _float(_nested(fit, "bridge_fit", "spearman_rho"))
    gate_result = str(fit.get("gate_result") or "")
    sign_agreement_failed = gate_pass_flags.get("sign_agreement") is False or gate_pass_flags.get("sign_agreement_pass") is False
    spearman_failed = gate_pass_flags.get("spearman_rho") is False or gate_pass_flags.get("spearman_rho_pass") is False
    residual_failed = (
        gate_pass_flags.get("normalized_residual") is False
        or gate_pass_flags.get("normalized_residual_pass") is False
    )
    weak_alignment = bool(
        gate_result.endswith("gate_failed")
        or "sign_agreement_failed" in reason_codes
        or "spearman_rho_failed" in reason_codes
        or "normalized_residual_failed" in reason_codes
        or sign_agreement_failed
        or spearman_failed
        or residual_failed
    )
    underpowered = row_count < MIN_BRIDGE_ROWS or unique_instances < MIN_UNIQUE_INSTANCES or "row_count_below_minimum" in reason_codes
    return {
        "claim_status": str(fit.get("claim_status") or CLAIM_STATUS),
        "computed_alignment": {
            "low_signal_abs_delta_logloss_count": sum(1 for value in delta_logloss_values if abs(value) <= 0.001),
            "low_signal_abs_delta_logloss_rate": round(
                sum(1 for value in delta_logloss_values if abs(value) <= 0.001) / len(delta_logloss_values), 12
            )
            if delta_logloss_values
            else None,
            "mean_delta_logloss": _mean(delta_logloss_values),
            "mean_delta_utility": _mean(delta_utility_values),
            "negative_delta_logloss_count": sum(1 for value in delta_logloss_values if value < 0),
            "pearson_r": _pearson(delta_logloss_values, delta_utility_values),
            "row_pairs_scanned": len(pairs),
            "sign_agreement": round(sign_matches / len(pairs), 12) if pairs else None,
            "spearman_rho": _spearman(delta_logloss_values, delta_utility_values),
            "zero_delta_logloss_count": sum(1 for value in delta_logloss_values if value == 0),
        },
        "effective_sample_size": int(fit.get("effective_sample_size") or 0),
        "fit_summary_alignment": {
            "normalized_residual": normalized_residual,
            "sign_agreement": fitted_sign_agreement,
            "spearman_rho": fitted_spearman,
        },
        "gate_pass_flags": gate_pass_flags,
        "gate_result": gate_result,
        "reason_codes": reason_codes,
        "route_id": route_id,
        "row_count": row_count,
        "underpowered_rows": underpowered,
        "unique_original_instances": unique_instances,
        "utility_field": utility_field,
        "weak_utility_logloss_alignment": weak_alignment,
    }


def _workbench_summary(name: str, fit: Mapping[str, Any], gate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "calibrated_proxy_supported": bool(gate.get("calibrated_proxy_supported")),
        "claim_status": str(gate.get("claim_status") or CLAIM_STATUS),
        "effective_sample_size": int(fit.get("effective_sample_size") or 0),
        "name": name,
        "rows_validated": int(fit.get("rows_validated") or fit.get("rows_imported") or 0),
        "status": str(fit.get("bridge_status") or fit.get("gate_result") or "unknown"),
        "vinfo_proxy_supported": bool(gate.get("vinfo_proxy_supported")),
    }


def _logloss_evaluator_path_audit() -> dict[str, Any]:
    request = EvaluationRequest(
        all_packets=[],
        candidate_pool_hash="logprobe_bridge_audit_shadow_probe",
        dataset="audit",
        instance_id="logprobe_bridge_audit_shadow_probe",
        query="offline audit probe",
        selected_packets=[],
        target={"target_type": "audit_probe"},
    )
    result = evaluate_logloss_shadow(request).to_payload()
    return {
        "claim_flags": result["claim_flags"],
        "metrics": result["metrics"],
        "source_path": "cps/evaluators/logloss.py",
        "status": result["metrics"].get("logloss_status"),
    }


def build_logprobe_stability_report(inputs: Mapping[str, Any]) -> dict[str, Any]:
    answer_generation = _generation_summary("HotpotQA answer NLL delta records", inputs["hotpotqa_answer_nll_generation_report"])
    support_generation = _generation_summary(
        "HotpotQA support-classification delta records",
        inputs["hotpotqa_support_classification_generation_report"],
    )
    route5 = dict(inputs["route5_readiness_report"])
    target_issue_present = support_generation["target_verbalization_failure_count"] > 0
    instability_present = (
        answer_generation["api_retries"] > 0
        or support_generation["api_retries"] > 0
        or support_generation["api_failure_count"] > 0
    )
    return {
        "audit_live_api_used": False,
        "claim_status": CLAIM_STATUS,
        "failure_factor_assessment": {
            "fixed_model_logloss_proxy": {
                "status": str(route5.get("status") or "skipped_no_bridge_candidate"),
                "summary": "Route 5 remained stopped before fixed-model logloss proxy verification.",
            },
            "logprobe_instability": {
                "status": "present" if instability_present else "not_observed_in_existing_reports",
                "summary": "Existing reports show retry or failure signals; this audit did not rerun scoring.",
            },
            "target_verbalization_tokenization": {
                "status": "present" if target_issue_present else "not_observed_in_existing_reports",
                "summary": "Support-classification scoring produced label or token mismatch failures."
                if target_issue_present
                else "No support-classification target mismatch failures were found in the existing report.",
            },
        },
        "generation_reports": {
            "answer_nll": answer_generation,
            "support_classification": support_generation,
        },
        "logloss_evaluator_path_audit": _logloss_evaluator_path_audit(),
        "new_live_api_calls": False,
        "route5_logloss_proxy_gate": {
            "fixed_model_logloss_proxy_verification_started": bool(
                route5.get("fixed_model_logloss_proxy_verification_started")
            ),
            "metric_bridge_support": bool(route5.get("metric_bridge_support")),
            "start_condition_satisfied": bool(route5.get("start_condition_satisfied")),
            "status": str(route5.get("status") or ""),
            "vinfo_proxy_supported": bool(route5.get("vinfo_proxy_supported")),
        },
        "route5_unlocked": False,
        "route8_unlocked": False,
        "schema_version": "logprobe_stability_report_v1",
        "source_artifacts": {name: _path_ref(path) for name, path in REQUIRED_INPUTS.items() if "generation_report" in name},
        "workbench_bridge_analyzer_outputs": [
            _workbench_summary(
                "integrated_validation_workbench_hotpotqa_smoke",
                inputs["workbench_hotpotqa_smoke_bridge_fit_summary"],
                inputs["workbench_hotpotqa_smoke_claim_gate_result"],
            ),
            _workbench_summary(
                "gamma_workbench_hotpotqa",
                inputs["gamma_workbench_hotpotqa_bridge_fit_summary"],
                inputs["gamma_workbench_hotpotqa_claim_gate_result"],
            ),
            _workbench_summary(
                "gamma_workbench_project_native",
                inputs["gamma_workbench_project_native_bridge_fit_summary"],
                inputs["gamma_workbench_project_native_claim_gate_result"],
            ),
        ],
    }


def build_utility_logloss_alignment_report(inputs: Mapping[str, Any]) -> dict[str, Any]:
    routes = {
        "Route4A": _route_alignment_summary(
            route_id="Route4A",
            fit=inputs["route4a_bridge_fit_summary"],
            rows=inputs["route4a_bridge_rows"],
            utility_field="delta_utility",
        ),
        "Route4B": _route_alignment_summary(
            route_id="Route4B",
            fit=inputs["route4b_bridge_fit_summary"],
            rows=inputs["route4b_bridge_rows"],
            utility_field="delta_external_sufficiency_utility",
        ),
        "DeltaRoute4E": _route_alignment_summary(
            route_id="DeltaRoute4E",
            fit=inputs["delta_route4e_bridge_fit_summary"],
            rows=inputs["delta_route4e_bridge_rows"],
            utility_field="delta_hybrid_utility",
        ),
    }
    route6b_readiness = dict(inputs["route6b_readiness_report"])
    route6b_adjudication = dict(inputs["route6b_adjudication_report"])
    delta_reliability = dict(inputs["delta_judge_reliability_audit"])
    delta_final = dict(inputs["delta_final_status"])
    return {
        "audit_live_api_used": False,
        "claim_gate_summary": {
            "calibrated_proxy_supported": False,
            "measurement_validation": False,
            "metric_bridge_support": False,
            "paper_evidence": False,
            "vinfo_proxy_supported": False,
        },
        "claim_status": CLAIM_STATUS,
        "judge_label_summary": {
            "delta": {
                "claim_status": str(delta_final.get("claim_status") or CLAIM_STATUS),
                "invalid_label_rate": _float(delta_reliability.get("invalid_label_rate")),
                "minority_veto_count": int(delta_reliability.get("minority_veto_count") or 0),
                "order_reversal_match_rate": _float(_nested(delta_reliability, "order_reversal_stability", "match_rate")),
                "raw_api_responses_stored": bool(delta_final.get("raw_api_responses_stored")),
                "status": str(delta_reliability.get("status") or delta_final.get("terminal_status") or ""),
            },
            "route6b": {
                "accepted_model_adjudicated_count": int(route6b_readiness.get("accepted_model_adjudicated_count") or 0),
                "counts_as_human_labels": bool(route6b_adjudication.get("counts_as_human_labels")),
                "human_annotation_status": str(route6b_readiness.get("human_annotation_status") or ""),
                "measurement_validation_candidate_allowed": bool(
                    route6b_readiness.get("measurement_validation_candidate_allowed")
                ),
                "raw_api_responses_stored": bool(route6b_adjudication.get("raw_api_responses_stored")),
                "status": str(route6b_readiness.get("status") or ""),
            },
        },
        "new_live_api_calls": False,
        "routes": routes,
        "schema_version": "utility_logloss_alignment_report_v1",
    }


def build_route4_failure_decomposition(
    inputs: Mapping[str, Any],
    stability: Mapping[str, Any],
    alignment: Mapping[str, Any],
) -> dict[str, Any]:
    routes = alignment["routes"]
    route4b_underpowered = bool(routes["Route4B"]["underpowered_rows"])
    delta_scaleup = dict(inputs["delta_model_adjudication_scaleup_report"])
    route8 = dict(inputs.get("route8_readiness_report") or {})
    judge_status = str(_nested(alignment, "judge_label_summary", "delta", "status") or "")
    weak_routes = [
        name for name, route in routes.items() if isinstance(route, Mapping) and route.get("weak_utility_logloss_alignment")
    ]
    return {
        "audit_live_api_used": False,
        "claim_status": CLAIM_STATUS,
        "denied_claims": list(DENIED_CLAIMS),
        "failure_factors": {
            "bridge_gate_strictness": {
                "evidence": "Route4A and DeltaRoute4E had enough rows for the pilot threshold but failed sign, rank, or residual gates.",
                "recommendation": "do_not_relax_claim_gate",
                "status": "claim_gate_operating_as_designed",
            },
            "judge_label_noise": {
                "evidence": {
                    "delta_judge_status": judge_status,
                    "route6b_counts_as_human_labels": _nested(
                        alignment, "judge_label_summary", "route6b", "counts_as_human_labels"
                    ),
                },
                "status": "present" if "FAILED_CLOSED" in judge_status else "model_adjudicated_not_measurement_validation",
            },
            "logprobe_instability": dict(stability["failure_factor_assessment"]["logprobe_instability"]),
            "target_verbalization_tokenization": dict(
                stability["failure_factor_assessment"]["target_verbalization_tokenization"]
            ),
            "underpowered_rows": {
                "evidence": {
                    "delta_three_view_item_count": int(delta_scaleup.get("three_view_item_count") or 0),
                    "delta_unique_original_instance_count": int(delta_scaleup.get("unique_original_instance_count") or 0),
                    "route4b_rows_validated": int(routes["Route4B"]["row_count"]),
                },
                "status": "present" if route4b_underpowered or int(delta_scaleup.get("three_view_item_count") or 0) == 0 else "not_primary",
            },
            "weak_utility_logloss_alignment": {
                "affected_routes": weak_routes,
                "status": "present" if weak_routes else "not_observed",
            },
        },
        "locked_routes": {
            "Route5": "locked_no_accepted_metric_bridge",
            "Route8": "locked_no_accepted_evidence_package",
        },
        "new_live_api_calls": False,
        "overall_status": "failed_closed_no_claim_upgrade",
        "route8_reference_status": str(route8.get("status") or "not_required_for_audit"),
        "schema_version": "route4_failure_decomposition_v1",
    }


def build_next_logprobe_repair_plan(decomposition: Mapping[str, Any]) -> str:
    factors = decomposition["failure_factors"]
    affected_routes = ", ".join(factors["weak_utility_logloss_alignment"]["affected_routes"]) or "none"
    return "\n".join(
        [
            "# Next LogProbe Repair Plan",
            "",
            f"Claim status: {CLAIM_STATUS}",
            "",
            "## Current finding",
            "",
            "The existing bridge evidence remains failed closed. The audit found target-verbalization/tokenization risk, "
            "weak utility-logloss alignment, model-judge reliability limits, and underpowered model-adjudicated bridge "
            "slices. A stricter claim gate is not the defect; it is preventing unsupported upgrades.",
            "",
            "## Locked routes",
            "",
            "- Do not unlock Route 5 or Route 8.",
            "- Do not start fixed-model logloss proxy verification until an accepted metric bridge candidate exists.",
            "- Do not update manuscript claims or claim ledgers from this audit.",
            "",
            "## Repair sequence",
            "",
            "1. Freeze a target-verbalization contract before any new scoring: exact target string, tokenization policy, "
            "allowed labels, and invalid-output handling.",
            "2. Separate logprobe stability from bridge utility design. If live scoring is later approved, repeat a small "
            "fixed row set under the same target contract and report variance before fitting a bridge.",
            "3. Repair utility-logloss alignment before scale-up. The currently weak routes are: " + affected_routes + ".",
            "4. Keep model-adjudicated labels as operational evidence only. Human labels and kappa remain absent.",
            "5. Rerun bridge gates only after stability, target-contract, and non-circular utility checks pass.",
            "",
            "## Denied claims",
            "",
            "\n".join(f"- {claim}" for claim in DENIED_CLAIMS),
            "",
        ]
    )


def run_logprobe_bridge_audit(
    *,
    root: str | Path = ".",
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    inputs = _load_inputs(root)
    output_path = Path(output_dir)
    stability = build_logprobe_stability_report(inputs)
    alignment = build_utility_logloss_alignment_report(inputs)
    decomposition = build_route4_failure_decomposition(inputs, stability, alignment)
    plan = build_next_logprobe_repair_plan(decomposition)

    artifacts = {
        "logprobe_stability_report": write_json(output_path / "logprobe_stability_report.json", stability),
        "utility_logloss_alignment_report": write_json(output_path / "utility_logloss_alignment_report.json", alignment),
        "route4_failure_decomposition": write_json(output_path / "route4_failure_decomposition.json", decomposition),
    }
    plan_path = output_path / "next_logprobe_repair_plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(plan, encoding="utf-8")
    artifacts["next_logprobe_repair_plan"] = plan_path

    return {
        "artifacts": {name: _path_ref(path) for name, path in artifacts.items()},
        "claim_status": CLAIM_STATUS,
        "new_live_api_calls": False,
        "route5_unlocked": False,
        "route8_unlocked": False,
        "terminal_status": TERMINAL_STATUS,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the offline LogProbe bridge audit package.")
    parser.add_argument("--root", default=".", help="Repository root containing existing route artifacts.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for audit reports.")
    args = parser.parse_args(argv)
    result = run_logprobe_bridge_audit(root=args.root, output_dir=args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
