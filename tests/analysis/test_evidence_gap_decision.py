from __future__ import annotations

import json
from pathlib import Path

from cps.analysis.evidence_gap_decision import ALLOWED_PORTFOLIO_DECISIONS
from cps.analysis.evidence_gap_decision import run_evidence_gap_diagnosis


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def test_evidence_gap_decision_uses_existing_artifacts_without_claim_upgrade(workspace_tmp_dir):
    root = workspace_tmp_dir
    _write_json(
        root / "artifacts/experiments/route4b_bridge_to_measurement/bridge_fit_summary.json",
        {
            "rows_validated": 300,
            "unique_original_instances": 150,
            "gate_result": "failed_closed_underpowered",
            "bridge_fit": {"normalized_residual": 0.99, "sign_agreement": 0.38, "spearman_rho": 0.23},
            "gate_pass_flags": {
                "row_count_pass": False,
                "normalized_residual_pass": False,
                "sign_agreement_pass": False,
                "spearman_rho_pass": False,
            },
        },
    )
    _write_json(
        root / "artifacts/experiments/route6b_measurement_scaleup/readiness_report.json",
        {
            "accepted_model_adjudicated_count": 4,
            "counts_as_human_labels": False,
            "human_human_kappa_present": False,
            "measurement_validation_candidate_allowed": False,
            "status": "measurement_candidate_ready",
        },
    )
    _write_jsonl(
        root / "artifacts/experiments/route6b_measurement_scaleup/model_adjudicated_labels.jsonl",
        [
            {"delta_label": "improves", "uncertainty": "low", "counts_as_human_label": False},
            {"delta_label": "unchanged", "uncertainty": "low", "counts_as_human_label": False},
            {"delta_label": "improves", "uncertainty": "medium", "counts_as_human_label": False},
            {"delta_label": "unchanged", "uncertainty": "low", "counts_as_human_label": False},
        ],
    )
    _write_json(
        root / "artifacts/experiments/route7_scoped_selector_superiority/readiness_report.json",
        {
            "route7_claim_allowed": False,
            "status": "scoped_multibenchmark_comparison_completed",
            "reason_codes": ["missing_required_deployable_baselines", "route4_5_6_dependencies_unsatisfied"],
        },
    )
    _write_json(
        root / "artifacts/experiments/route7_scoped_selector_superiority/comparison_gate_report.json",
        {
            "route_dependencies_satisfied": False,
            "multi_benchmark_gate_passed": True,
            "project_native_fixture_only": True,
        },
    )
    _write_json(
        root / "artifacts/experiments/route7_scoped_selector_superiority/benchmark_matrix.json",
        {"predeclared_matrix_satisfied": True, "cells": {"HotpotQA": {"evidence_status": "operational_only"}}},
    )

    result = run_evidence_gap_diagnosis(
        repo_root=root,
        output_dir=root / "artifacts/experiments/integrated_validation_workbench/evidence_gap",
    )

    assert result["portfolio_decision"]["decision"] in ALLOWED_PORTFOLIO_DECISIONS
    assert result["portfolio_decision"]["decision"] == "GO_BETA_HYBRID_LABEL_MODEL"
    assert result["portfolio_decision"]["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert result["route6b_label_quality_audit"]["label_variance_status"] == "variance_present"
    assert result["route7_effect_audit"]["claim_boundary_blocked"] is True
    assert (root / "artifacts/experiments/integrated_validation_workbench/evidence_gap/portfolio_decision.json").exists()
