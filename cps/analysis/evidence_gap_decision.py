from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.analysis.bridge_power_projection import project_bridge_power
from cps.benchmarks.common import read_jsonl
from cps.benchmarks.common import write_json


ALLOWED_PORTFOLIO_DECISIONS = (
    "GO_ALPHA_MEASUREMENT_FIRST",
    "GO_BETA_HYBRID_LABEL_MODEL",
    "GO_GAMMA_ALTERNATIVE_PROGRESS",
    "GO_DIRECT_BRIDGE_SCALEUP",
    "GO_PAPER_NEGATIVE",
    "INSUFFICIENT_ARTIFACTS",
)

DEFAULT_INPUTS = {
    "route4b_bridge_fit": Path("artifacts/experiments/route4b_bridge_to_measurement/bridge_fit_summary.json"),
    "route6b_labels": Path("artifacts/experiments/route6b_measurement_scaleup/model_adjudicated_labels.jsonl"),
    "route6b_readiness": Path("artifacts/experiments/route6b_measurement_scaleup/readiness_report.json"),
    "route7_benchmark_matrix": Path("artifacts/experiments/route7_scoped_selector_superiority/benchmark_matrix.json"),
    "route7_comparison_gate": Path("artifacts/experiments/route7_scoped_selector_superiority/comparison_gate_report.json"),
    "route7_readiness": Path("artifacts/experiments/route7_scoped_selector_superiority/readiness_report.json"),
}


def _read_json(root: Path, path: Path) -> dict[str, Any]:
    resolved = root / path
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.as_posix()}: expected JSON object")
    return payload


def _distribution(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "missing") for row in rows).items()))


def audit_route6b_label_quality(
    *,
    readiness_report: Mapping[str, Any],
    label_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    delta_distribution = _distribution(label_rows, "delta_label")
    uncertainty_distribution = _distribution(label_rows, "uncertainty")
    accepted_count = int(readiness_report.get("accepted_model_adjudicated_count") or len(label_rows))
    low_uncertainty_count = uncertainty_distribution.get("low", 0)
    low_uncertainty_share = (low_uncertainty_count / len(label_rows)) if label_rows else 0.0
    variance_present = len([count for count in delta_distribution.values() if count > 0]) >= 2
    model_only = not bool(readiness_report.get("counts_as_human_labels"))
    return {
        "accepted_model_adjudicated_count": accepted_count,
        "claim_status": "operational_utility_only/no_claim_upgrade",
        "counts_as_human_labels": bool(readiness_report.get("counts_as_human_labels")),
        "delta_label_distribution": delta_distribution,
        "human_human_kappa_present": bool(readiness_report.get("human_human_kappa_present")),
        "label_source": "model_adjudicated",
        "label_variance_status": "variance_present" if variance_present else "variance_absent_or_collapsed",
        "low_uncertainty_share": round(low_uncertainty_share, 6),
        "measurement_validation_candidate_allowed": False,
        "model_labels_only_no_measurement_validation": model_only,
        "schema_version": "iw_route6b_label_quality_audit_v1",
        "stability_status": "model_adjudicated_low_uncertainty_only"
        if low_uncertainty_share >= 0.8
        else "model_adjudicated_uncertainty_mixed",
        "uncertainty_distribution": uncertainty_distribution,
    }


def audit_route7_effect(
    *,
    readiness_report: Mapping[str, Any],
    comparison_gate_report: Mapping[str, Any],
    benchmark_matrix: Mapping[str, Any],
) -> dict[str, Any]:
    reason_codes = list(readiness_report.get("reason_codes") or [])
    missing_baselines = list(readiness_report.get("missing_deployable_baselines") or [])
    cells = dict(benchmark_matrix.get("cells") or {})
    unavailable_cells = sorted(
        key
        for key, value in cells.items()
        if str(dict(value).get("evidence_status") or "").startswith(("not_available", "disabled", "blocked"))
    )
    effect_blocked = not bool(comparison_gate_report.get("hotpotqa_operational_cells_positive", True))
    baseline_blocked = bool(missing_baselines) or "missing_required_deployable_baselines" in reason_codes
    task_family_blocked = bool(unavailable_cells) and not bool(benchmark_matrix.get("predeclared_matrix_satisfied"))
    claim_boundary_blocked = (
        not bool(readiness_report.get("route7_claim_allowed"))
        or not bool(comparison_gate_report.get("route_dependencies_satisfied"))
    )
    blocked_by = []
    if effect_blocked:
        blocked_by.append("effect_size")
    if task_family_blocked:
        blocked_by.append("task_family_coverage")
    if baseline_blocked:
        blocked_by.append("baseline_comparability")
    if claim_boundary_blocked:
        blocked_by.append("claim_boundary")
    return {
        "baseline_comparability_blocked": baseline_blocked,
        "blocked_by": blocked_by,
        "claim_boundary_blocked": claim_boundary_blocked,
        "claim_status": "operational_utility_only/no_claim_upgrade",
        "effect_size_blocked": effect_blocked,
        "missing_deployable_baselines": missing_baselines,
        "reason_codes": reason_codes,
        "route7_claim_allowed": False,
        "schema_version": "iw_route7_effect_audit_v1",
        "task_family_coverage_blocked": task_family_blocked,
        "unavailable_or_blocked_cells": unavailable_cells,
    }


def decide_portfolio(
    *,
    bridge_power_projection: Mapping[str, Any],
    route6b_label_quality_audit: Mapping[str, Any],
    route7_effect_audit: Mapping[str, Any],
) -> dict[str, Any]:
    if bridge_power_projection.get("direct_bridge_scaleup_recommended") is True:
        decision = "GO_DIRECT_BRIDGE_SCALEUP"
        rationale = "Route4B appears mainly underpowered without current signal-disqualification gates."
    elif route6b_label_quality_audit.get("label_variance_status") == "variance_present":
        decision = "GO_BETA_HYBRID_LABEL_MODEL"
        rationale = (
            "Route6B model-adjudicated labels have variance, but accepted evidence still requires "
            "independent review or human validation before any claim upgrade."
        )
    elif route7_effect_audit.get("effect_size_blocked"):
        decision = "GO_GAMMA_ALTERNATIVE_PROGRESS"
        rationale = "Route7 appears blocked by effect size before claim-boundary gates can be considered."
    else:
        decision = "GO_ALPHA_MEASUREMENT_FIRST"
        rationale = "Measurement quality is the earliest unresolved blocker."
    return {
        "allowed_decisions": list(ALLOWED_PORTFOLIO_DECISIONS),
        "claim_status": "operational_utility_only/no_claim_upgrade",
        "decision": decision,
        "denied_claims": [
            "calibrated_proxy_supported",
            "vinfo_proxy_supported",
            "measurement validation",
            "metric bridge support",
            "selector superiority",
            "paper evidence",
        ],
        "no_live_api_calls": True,
        "no_new_labels": True,
        "rationale": rationale,
        "route5_locked": True,
        "route8_locked": True,
        "schema_version": "iw_portfolio_decision_v1",
    }


def run_evidence_gap_diagnosis(
    *,
    repo_root: str | Path = ".",
    output_dir: str | Path = "artifacts/experiments/integrated_validation_workbench/evidence_gap",
) -> dict[str, dict[str, Any]]:
    root = Path(repo_root)
    bridge_summary = _read_json(root, DEFAULT_INPUTS["route4b_bridge_fit"])
    route6b_readiness = _read_json(root, DEFAULT_INPUTS["route6b_readiness"])
    route6b_labels = read_jsonl(root / DEFAULT_INPUTS["route6b_labels"])
    route7_readiness = _read_json(root, DEFAULT_INPUTS["route7_readiness"])
    route7_gate = _read_json(root, DEFAULT_INPUTS["route7_comparison_gate"])
    route7_matrix = _read_json(root, DEFAULT_INPUTS["route7_benchmark_matrix"])

    bridge_projection = project_bridge_power(bridge_summary)
    route6b_audit = audit_route6b_label_quality(
        readiness_report=route6b_readiness,
        label_rows=route6b_labels,
    )
    route7_audit = audit_route7_effect(
        readiness_report=route7_readiness,
        comparison_gate_report=route7_gate,
        benchmark_matrix=route7_matrix,
    )
    decision = decide_portfolio(
        bridge_power_projection=bridge_projection,
        route6b_label_quality_audit=route6b_audit,
        route7_effect_audit=route7_audit,
    )

    out = root / output_dir
    write_json(out / "bridge_power_projection.json", bridge_projection)
    write_json(out / "route6b_label_quality_audit.json", route6b_audit)
    write_json(out / "route7_effect_audit.json", route7_audit)
    write_json(out / "portfolio_decision.json", decision)
    return {
        "bridge_power_projection": bridge_projection,
        "portfolio_decision": decision,
        "route6b_label_quality_audit": route6b_audit,
        "route7_effect_audit": route7_audit,
    }
