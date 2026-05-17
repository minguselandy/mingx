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
