from __future__ import annotations

import json
from pathlib import Path

from cps.experiments.route7_scoped_selector_superiority import assess_route7_gate
from cps.experiments.route7_scoped_selector_superiority import write_route7_artifacts


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_hotpotqa_stats(root: Path) -> None:
    _write_json(
        root / "artifacts/experiments/p56_hotpotqa_operational_comparison/statistical_tests.json",
        {
            "comparison_target": "v12_cost_aware_diagnostic_policy_operational_only",
            "deployable_baselines": ["random_budget", "topk_relevance_or_token_budget", "mmr_density_greedy"],
            "phase": "P66-HotpotQA",
            "v12_vs_baselines": {
                "random_budget::budget_512": {
                    "baseline_selector": "random_budget",
                    "budget": 512,
                    "ci95_low": 0.1,
                    "effect_direction": "v12_higher",
                    "mean_paired_delta": 0.2,
                    "p_value_two_sided": 0.01,
                    "primary_metric": "supporting_fact_recall_at_budget",
                }
            },
        },
    )


def _write_project_native_comparison(root: Path) -> None:
    path = root / "artifacts/experiments/realistic_task_model_adjudicated_v12/realistic_selector_comparison.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "task_id,task_family,baseline,sufficiency_score,budget_comparable,data_source_kind,metric_claim_level",
                "mh,multi_hop_evidence_assembly,top_k_retrieval,0.5,true,fixture,operational_utility_only",
                "mh,multi_hop_evidence_assembly,mmr_density_greedy,1.0,true,fixture,operational_utility_only",
                "mh,multi_hop_evidence_assembly,v12_cost_aware_diagnostic_policy,1.0,true,fixture,operational_utility_only",
                "paper,paper_revision_microtask,top_k_retrieval,1.0,true,fixture,operational_utility_only",
                "paper,paper_revision_microtask,mmr_density_greedy,1.0,true,fixture,operational_utility_only",
                "paper,paper_revision_microtask,v12_cost_aware_diagnostic_policy,1.0,true,fixture,operational_utility_only",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_json(
        root / "artifacts/experiments/p56_hotpotqa_operational_comparison/diagnostic_safety_summary.json",
        {
            "claim_status": "operational_utility_only; no_claim_upgrade",
            "global_selector_superiority_claimed": False,
            "oracle_used_as_deployable_baseline": False,
            "selector_superiority_claimed": False,
        },
    )


def test_route7_blocks_multi_benchmark_claim_when_only_hotpotqa_operational_input_exists(workspace_tmp_dir: Path) -> None:
    _write_hotpotqa_stats(workspace_tmp_dir)

    package = assess_route7_gate(root=workspace_tmp_dir)

    assert package.readiness_report["status"] == "blocked_multi_benchmark_requirements_unmet"
    assert package.readiness_report["claim_status"] == "no_claim_upgrade"
    assert package.readiness_report["scoped_multi_benchmark_selector_superiority"] is False
    assert package.readiness_report["global_selector_superiority"] is False
    assert package.readiness_report["available_benchmark_count"] == 1
    assert package.readiness_report["route7_claim_allowed"] is False
    assert "single_benchmark_only_hotpotqa" in package.readiness_report["reason_codes"]
    assert "missing_required_deployable_baselines" in package.readiness_report["reason_codes"]
    assert "route4_5_6_dependencies_unsatisfied" in package.readiness_report["reason_codes"]

    matrix = package.benchmark_matrix
    assert matrix["cells"]["HotpotQA"]["evidence_status"] == "operational_only_available"
    assert matrix["cells"]["FEVER"]["evidence_status"] == "blocked_fever_source_unavailable"
    assert package.baseline_registry["missing_deployable_baselines"] == [
        "BM25_or_dense_retrieval_when_available",
        "ablated_cost_aware_policy",
        "prior_v12_diagnostic_policy_variant",
    ]
    assert package.comparison_gate_report["hotpotqa_operational_cells_positive"] is True
    assert package.comparison_gate_report["multi_benchmark_gate_passed"] is False
    assert package.worst_cell_report["claim_use"] == "operational_hotpotqa_only"


def test_route7_writes_blocked_artifacts_and_doc(workspace_tmp_dir: Path) -> None:
    _write_hotpotqa_stats(workspace_tmp_dir)
    output_dir = workspace_tmp_dir / "artifacts" / "experiments" / "route7_scoped_selector_superiority"
    docs_path = workspace_tmp_dir / "docs" / "experiments" / "Route7-scoped-selector-superiority-blocked-report.md"

    result = write_route7_artifacts(root=workspace_tmp_dir, output_dir=output_dir, docs_path=docs_path)

    expected = {
        "baseline_registry": output_dir / "baseline_registry.json",
        "benchmark_matrix": output_dir / "benchmark_matrix.json",
        "comparison_gate_report": output_dir / "comparison_gate_report.json",
        "readiness_report": output_dir / "readiness_report.json",
        "report_doc": docs_path,
        "worst_cell_report": output_dir / "worst_cell_report.json",
    }
    assert result == expected
    for path in expected.values():
        assert path.exists()

    readiness = json.loads(expected["readiness_report"].read_text(encoding="utf-8"))
    doc = expected["report_doc"].read_text(encoding="utf-8")

    assert readiness["status"] == "blocked_multi_benchmark_requirements_unmet"
    assert readiness["operational_hotpotqa_result_preserved"] is True
    assert "Claim status: `no_claim_upgrade`" in doc
    assert "HotpotQA remains operational-only evidence" in doc
    assert "global selector superiority remains denied" in doc


def test_route7_hotpotqa_only_preserves_available_hotpotqa_operational_comparison(workspace_tmp_dir: Path) -> None:
    _write_hotpotqa_stats(workspace_tmp_dir)

    package = assess_route7_gate(root=workspace_tmp_dir, hotpotqa_only=True)

    assert package.readiness_report["status"] == "hotpotqa_first_operational_comparison_available_no_claim_upgrade"
    assert package.readiness_report["claim_status"] == "no_claim_upgrade"
    assert package.readiness_report["scope"] == "hotpotqa_only"
    assert package.readiness_report["hotpotqa_first_selector_comparison_available"] is True
    assert package.readiness_report["scoped_multi_benchmark_selector_superiority"] is False
    assert package.readiness_report["global_selector_superiority"] is False
    assert package.readiness_report["route7_claim_allowed"] is False
    assert "hotpotqa_operational_comparison_available" in package.readiness_report["reason_codes"]
    assert "missing_fever_benchmark_cell" not in package.readiness_report["reason_codes"]
    assert "missing_required_deployable_baselines" not in package.readiness_report["reason_codes"]
    assert package.benchmark_matrix["cells"]["FEVER"]["evidence_status"] == "disabled_by_hotpotqa_only_scope"
    assert package.comparison_gate_report["hotpotqa_operational_cells_positive"] is True
    assert package.comparison_gate_report["hotpotqa_first_gate_passed"] is True


def test_route7_fever_disabled_uses_project_native_tasks_as_terminal_non_claim_comparison(
    workspace_tmp_dir: Path,
) -> None:
    _write_hotpotqa_stats(workspace_tmp_dir)
    _write_project_native_comparison(workspace_tmp_dir)

    package = assess_route7_gate(root=workspace_tmp_dir, fever_disabled=True)

    assert package.readiness_report["status"] == "scoped_multibenchmark_comparison_completed"
    assert package.readiness_report["scope"] == "non_fever_scoped_multibenchmark"
    assert package.readiness_report["available_benchmark_count"] == 3
    assert package.readiness_report["route7_claim_allowed"] is False
    assert package.readiness_report["scoped_multi_benchmark_selector_superiority"] is False
    assert package.readiness_report["global_selector_superiority"] is False
    assert package.readiness_report["non_fever_task_families_available"] == [
        "multi_hop_evidence_assembly",
        "paper_revision_microtask",
    ]
    assert "non_fever_project_native_task_families_available" in package.readiness_report["reason_codes"]
    assert "project_native_fixture_operational_only_no_claim_upgrade" in package.readiness_report["reason_codes"]
    assert "missing_fever_benchmark_cell" not in package.readiness_report["reason_codes"]
    assert package.benchmark_matrix["cells"]["FEVER"]["evidence_status"] == "disabled_by_user_no_fever"
    assert package.benchmark_matrix["cells"]["paper_revision_microtask"]["evidence_status"] == "fixture_operational_only_available"
    assert package.comparison_gate_report["multi_benchmark_gate_passed"] is True
