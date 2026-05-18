from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Sequence

from cps.benchmarks.schemas import write_json


DEFAULT_OUTPUT_DIR = Path("artifacts/experiments/route7_scoped_selector_superiority")
DEFAULT_DOCS_PATH = Path("docs/experiments/Route7-scoped-selector-superiority-blocked-report.md")
DEFAULT_HOTPOTQA_STATS_PATH = Path("artifacts/experiments/p56_hotpotqa_operational_comparison/statistical_tests.json")
DEFAULT_HOTPOTQA_SAFETY_PATH = Path("artifacts/experiments/p56_hotpotqa_operational_comparison/diagnostic_safety_summary.json")
DEFAULT_ROUTE4B_CLAIM_GATE_PATH = Path("artifacts/experiments/route4b_bridge_to_measurement/claim_gate_result.json")
DEFAULT_ROUTE4C_READINESS_PATH = Path("artifacts/experiments/route4c_fever/readiness_report.json")
DEFAULT_ROUTE5_READINESS_PATH = Path("artifacts/experiments/route5_fixed_model_logloss_proxy/readiness_report.json")
DEFAULT_ROUTE6A_ADJUDICATION_PATH = Path("artifacts/experiments/route6a_measurement_pilot/adjudication_report.json")
DEFAULT_PROJECT_NATIVE_COMPARISON_PATH = Path(
    "artifacts/experiments/realistic_task_model_adjudicated_v12/realistic_selector_comparison.csv"
)

REQUIRED_DEPLOYABLE_BASELINES = [
    "random_budget",
    "topk_relevance_or_token_budget",
    "BM25_or_dense_retrieval_when_available",
    "mmr_density_greedy",
    "prior_v12_diagnostic_policy_variant",
    "ablated_cost_aware_policy",
]

PROJECT_NATIVE_TASK_FAMILIES = [
    "multi_hop_evidence_assembly",
    "paper_revision_microtask",
    "repo_change_review_microtask",
]


@dataclass(frozen=True)
class Route7Package:
    readiness_report: dict[str, Any]
    benchmark_matrix: dict[str, Any]
    baseline_registry: dict[str, Any]
    comparison_gate_report: dict[str, Any]
    worst_cell_report: dict[str, Any]


def _resolve(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate.name
    return candidate.as_posix()


def _read_json(root: Path, path: str | Path) -> dict[str, Any]:
    resolved = _resolve(root, path)
    if not resolved.exists() or not resolved.is_file():
        return {}
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _read_csv_rows(root: Path, path: str | Path) -> list[dict[str, str]]:
    resolved = _resolve(root, path)
    if not resolved.exists() or not resolved.is_file():
        return []
    with resolved.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _hotpotqa_cells_positive(stats: dict[str, Any]) -> bool:
    cells = stats.get("v12_vs_baselines")
    if not isinstance(cells, dict) or not cells:
        return False
    for cell in cells.values():
        if not isinstance(cell, dict):
            return False
        if str(cell.get("effect_direction")) != "v12_higher":
            return False
        if float(cell.get("ci95_low", 0.0)) <= 0.0:
            return False
        if float(cell.get("p_value_two_sided", 1.0)) > 0.05:
            return False
    return True


def _worst_hotpotqa_cell(stats: dict[str, Any]) -> dict[str, Any]:
    cells = stats.get("v12_vs_baselines")
    if not isinstance(cells, dict) or not cells:
        return {
            "available": False,
            "claim_use": "none",
            "reason": "missing_hotpotqa_operational_statistical_tests",
        }
    parsed: list[tuple[float, str, dict[str, Any]]] = []
    for key, value in cells.items():
        if isinstance(value, dict):
            parsed.append((float(value.get("mean_paired_delta", 0.0)), str(key), value))
    if not parsed:
        return {
            "available": False,
            "claim_use": "none",
            "reason": "missing_hotpotqa_operational_cells",
        }
    delta, key, cell = min(parsed, key=lambda item: item[0])
    return {
        "available": True,
        "baseline_selector": cell.get("baseline_selector"),
        "budget": cell.get("budget"),
        "cell_id": key,
        "claim_use": "operational_hotpotqa_only",
        "mean_paired_delta": delta,
        "primary_metric": cell.get("primary_metric"),
        "scope": "HotpotQA operational comparison only",
    }


def _baseline_registry(stats: dict[str, Any]) -> dict[str, Any]:
    available = sorted(str(item) for item in stats.get("deployable_baselines", []) if str(item))
    missing = sorted(set(REQUIRED_DEPLOYABLE_BASELINES) - set(available))
    return {
        "artifact_type": "Route7BaselineRegistry",
        "available_deployable_baselines": available,
        "claim_status": "no_claim_upgrade",
        "missing_deployable_baselines": missing,
        "non_deployable_reference": "gold_support_oracle_upper_bound",
        "oracle_used_as_deployable_baseline": False,
        "required_deployable_baselines": list(REQUIRED_DEPLOYABLE_BASELINES),
        "schema_version": "route7_baseline_registry_v1",
    }


def _project_native_summary(rows: Sequence[dict[str, str]]) -> dict[str, Any]:
    by_family: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        family = str(row.get("task_family") or "")
        if family in PROJECT_NATIVE_TASK_FAMILIES:
            by_family.setdefault(family, []).append(row)

    cells: dict[str, dict[str, Any]] = {}
    for family, family_rows in sorted(by_family.items()):
        v12_rows = [row for row in family_rows if row.get("baseline") == "v12_cost_aware_diagnostic_policy"]
        comparable = [
            row
            for row in family_rows
            if row.get("budget_comparable") == "true" and row.get("baseline") != "v12_cost_aware_diagnostic_policy"
        ]
        v12_score = max((float(row.get("sufficiency_score") or 0.0) for row in v12_rows), default=None)
        baseline_scores = {
            str(row.get("baseline") or ""): float(row.get("sufficiency_score") or 0.0)
            for row in comparable
            if str(row.get("baseline") or "")
        }
        data_source_kinds = sorted({str(row.get("data_source_kind") or "unknown") for row in family_rows})
        cells[family] = {
            "baseline_scores": baseline_scores,
            "budget_comparable_baselines": sorted(baseline_scores),
            "data_source_kinds": data_source_kinds,
            "evidence_status": (
                "fixture_operational_only_available"
                if "fixture" in data_source_kinds
                else "operational_only_available"
            ),
            "task_family": family,
            "v12_best_sufficiency_score": v12_score,
            "v12_ties_or_exceeds_budget_baselines": (
                v12_score is not None
                and bool(baseline_scores)
                and all(v12_score >= score for score in baseline_scores.values())
            ),
        }
    return {
        "available_task_families": sorted(cells),
        "cells": cells,
        "fixture_only": any(
            "fixture" in cell["data_source_kinds"]
            for cell in cells.values()
        ),
    }


def _dependencies(root: Path) -> dict[str, Any]:
    route4b = _read_json(root, DEFAULT_ROUTE4B_CLAIM_GATE_PATH)
    route4c = _read_json(root, DEFAULT_ROUTE4C_READINESS_PATH)
    route5 = _read_json(root, DEFAULT_ROUTE5_READINESS_PATH)
    route6a = _read_json(root, DEFAULT_ROUTE6A_ADJUDICATION_PATH)
    return {
        "route4_metric_bridge_candidate": bool(route4b.get("metric_bridge_support_candidate"))
        or bool(route4c.get("candidate_bridge_evidence_accepted")),
        "route5_fixed_model_proxy_candidate": bool(route5.get("vinfo_proxy_supported_candidate")),
        "route6_measurement_validation": bool(route6a.get("measurement_validation_candidate_allowed")),
    }


def assess_route7_gate(
    *,
    root: str | Path = ".",
    hotpotqa_only: bool = False,
    fever_disabled: bool = False,
    hotpotqa_stats_path: str | Path = DEFAULT_HOTPOTQA_STATS_PATH,
    hotpotqa_safety_path: str | Path = DEFAULT_HOTPOTQA_SAFETY_PATH,
    project_native_comparison_path: str | Path = DEFAULT_PROJECT_NATIVE_COMPARISON_PATH,
) -> Route7Package:
    repo_root = Path(root)
    stats = _read_json(repo_root, hotpotqa_stats_path)
    safety = _read_json(repo_root, hotpotqa_safety_path)
    project_native = _project_native_summary(_read_csv_rows(repo_root, project_native_comparison_path))
    hotpotqa_available = bool(stats.get("v12_vs_baselines"))
    hotpotqa_positive = _hotpotqa_cells_positive(stats)
    non_fever_task_families = project_native["available_task_families"] if fever_disabled and not hotpotqa_only else []
    available_benchmark_count = (1 if hotpotqa_available else 0) + len(non_fever_task_families)
    baseline_registry = _baseline_registry(stats)
    dependencies = _dependencies(repo_root)
    dependencies_satisfied = all(dependencies.values())
    missing_baselines = bool(baseline_registry["missing_deployable_baselines"]) and not hotpotqa_only
    multi_benchmark_gate = available_benchmark_count >= 3 if fever_disabled and not hotpotqa_only else available_benchmark_count >= 2
    hotpotqa_first_gate = hotpotqa_only and hotpotqa_available and hotpotqa_positive
    project_native_fixture_only = bool(project_native["fixture_only"] and non_fever_task_families)
    route7_claim_allowed = False if hotpotqa_only or project_native_fixture_only else (
        multi_benchmark_gate and not missing_baselines and dependencies_satisfied and hotpotqa_positive
    )

    reason_codes: list[str] = []
    if hotpotqa_only and hotpotqa_first_gate:
        reason_codes.append("hotpotqa_operational_comparison_available")
    elif available_benchmark_count == 1 and hotpotqa_available:
        reason_codes.append("single_benchmark_only_hotpotqa")
    if not hotpotqa_available:
        reason_codes.append("missing_hotpotqa_operational_comparison")
    if fever_disabled and not hotpotqa_only:
        reason_codes.append("non_fever_project_native_task_families_available" if non_fever_task_families else "missing_non_fever_task_families")
    elif not hotpotqa_only:
        reason_codes.append("missing_fever_benchmark_cell")
    if missing_baselines:
        reason_codes.append("missing_required_deployable_baselines")
    if project_native_fixture_only:
        reason_codes.append("project_native_fixture_operational_only_no_claim_upgrade")
    if not dependencies_satisfied:
        reason_codes.append(
            "route4_5_6_dependencies_unsatisfied_for_claim_upgrade"
            if hotpotqa_only or fever_disabled
            else "route4_5_6_dependencies_unsatisfied"
        )
    if not route7_claim_allowed:
        reason_codes.append(
            "hotpotqa_first_comparison_operational_only_no_claim_upgrade"
            if hotpotqa_only and hotpotqa_first_gate
            else "no_scoped_multi_benchmark_selector_superiority"
        )

    benchmark_cells: dict[str, Any] = {
        "FEVER": {
            "evidence_status": (
                "disabled_by_hotpotqa_only_scope"
                if hotpotqa_only
                else ("disabled_by_user_no_fever" if fever_disabled else "blocked_fever_source_unavailable")
            ),
            "task_family": "claim_verification",
        },
        "HotpotQA": {
            "budgets": sorted(
                {
                    int(cell.get("budget"))
                    for cell in stats.get("v12_vs_baselines", {}).values()
                    if isinstance(cell, dict) and cell.get("budget") is not None
                }
            ),
            "evidence_status": "operational_only_available" if hotpotqa_available else "missing",
            "task_family": "answer_support_selection",
        },
        "NaturalQuestionsOrSimilarQA": {
            "evidence_status": "not_available",
            "task_family": "answer_support_selection",
        },
        "QasperOrLongContextQA": {
            "evidence_status": "not_available",
            "task_family": "document_grounded_qa",
        },
    }
    if fever_disabled and not hotpotqa_only:
        benchmark_cells.update(project_native["cells"])

    benchmark_matrix = {
        "artifact_type": "Route7BenchmarkMatrix",
        "cells": benchmark_cells,
        "claim_status": "no_claim_upgrade",
        "predeclared_matrix_satisfied": multi_benchmark_gate,
        "schema_version": "route7_benchmark_matrix_v1",
        "scope": (
            "hotpotqa_only"
            if hotpotqa_only
            else ("non_fever_scoped_multibenchmark" if fever_disabled else "multi_benchmark")
        ),
    }

    worst_cell_report = _worst_hotpotqa_cell(stats)
    worst_cell_report["artifact_type"] = "Route7WorstCellReport"
    worst_cell_report["schema_version"] = "route7_worst_cell_report_v1"

    comparison_gate_report = {
        "artifact_type": "Route7ComparisonGateReport",
        "claim_status": "no_claim_upgrade",
        "global_selector_superiority_claimed": bool(safety.get("global_selector_superiority_claimed", False)),
        "hotpotqa_operational_cells_positive": hotpotqa_positive,
        "hotpotqa_statistical_tests_path": _path_ref(hotpotqa_stats_path),
        "hotpotqa_first_gate_passed": hotpotqa_first_gate,
        "multi_benchmark_gate_passed": multi_benchmark_gate,
        "oracle_used_as_deployable_baseline": bool(safety.get("oracle_used_as_deployable_baseline", False)),
        "project_native_comparison_path": _path_ref(project_native_comparison_path),
        "project_native_task_families": non_fever_task_families,
        "project_native_fixture_only": project_native_fixture_only,
        "route_dependencies": dependencies,
        "route_dependencies_satisfied": dependencies_satisfied,
        "schema_version": "route7_comparison_gate_report_v1",
        "worst_cell_report_path": "artifacts/experiments/route7_scoped_selector_superiority/worst_cell_report.json",
    }

    readiness_report = {
        "artifact_type": "Route7ScopedSelectorSuperiorityReadinessReport",
        "available_benchmark_count": available_benchmark_count,
        "claim_status": "no_claim_upgrade",
        "global_selector_superiority": False,
        "hotpotqa_first_selector_comparison_available": hotpotqa_first_gate,
        "missing_deployable_baselines": baseline_registry["missing_deployable_baselines"],
        "non_fever_task_families_available": non_fever_task_families,
        "operational_hotpotqa_result_preserved": hotpotqa_available,
        "paper_evidence": False,
        "reason_codes": reason_codes,
        "route7_claim_allowed": route7_claim_allowed,
        "schema_version": "route7_scoped_selector_superiority_readiness_v1",
        "scope": (
            "hotpotqa_only"
            if hotpotqa_only
            else ("non_fever_scoped_multibenchmark" if fever_disabled else "multi_benchmark")
        ),
        "scoped_multi_benchmark_selector_superiority": False,
        "status": (
            "ready_for_scoped_multi_benchmark_review"
            if route7_claim_allowed
            else (
                "scoped_multibenchmark_comparison_completed"
                if fever_disabled and multi_benchmark_gate
                else (
                "hotpotqa_first_operational_comparison_available_no_claim_upgrade"
                if hotpotqa_only and hotpotqa_first_gate
                else "blocked_multi_benchmark_requirements_unmet"
                )
            )
        ),
    }

    return Route7Package(
        readiness_report=readiness_report,
        benchmark_matrix=benchmark_matrix,
        baseline_registry=baseline_registry,
        comparison_gate_report=comparison_gate_report,
        worst_cell_report=worst_cell_report,
    )


def render_route7_report(package: Route7Package) -> str:
    readiness = package.readiness_report
    matrix = package.benchmark_matrix
    baselines = package.baseline_registry
    comparison = package.comparison_gate_report
    reason_codes = "\n".join(f"- `{code}`" for code in readiness["reason_codes"])
    missing = "\n".join(f"- `{name}`" for name in baselines["missing_deployable_baselines"])
    completed = readiness["status"] == "scoped_multibenchmark_comparison_completed"
    title = (
        "# Route7 Non-FEVER Scoped Selector Comparison Report\n\n"
        if completed
        else "# Route7 Scoped Selector-superiority Blocked Report\n\n"
    )
    decision = (
        "Route 7 completed a non-FEVER scoped comparison matrix using HotpotQA "
        "plus available project-native task families. The comparison remains "
        "operational-only because project-native rows are fixture/model-adjudicated "
        "and upstream bridge/proxy dependencies are unsatisfied.\n\n"
        if completed
        else "Route 7 is blocked for scoped multi-benchmark selector superiority. "
        "HotpotQA remains operational-only evidence from the existing P66 "
        "comparison, but the finite multi-benchmark matrix is not satisfied.\n\n"
    )
    return (
        title +
        f"Status: `{readiness['status']}`\n"
        "Claim status: `no_claim_upgrade`\n\n"
        "## Decision\n\n"
        f"{decision}"
        "The global selector superiority remains denied, and no scoped "
        "multi-benchmark selector-superiority claim is introduced.\n\n"
        "## Matrix And Baselines\n\n"
        f"- Available benchmark count: `{readiness['available_benchmark_count']}`.\n"
        f"- HotpotQA evidence status: `{matrix['cells']['HotpotQA']['evidence_status']}`.\n"
        f"- FEVER evidence status: `{matrix['cells']['FEVER']['evidence_status']}`.\n"
        f"- HotpotQA operational cells positive: `{str(comparison['hotpotqa_operational_cells_positive']).lower()}`.\n"
        "- Missing deployable baselines:\n"
        f"{missing}\n\n"
        "## Reason Codes\n\n"
        f"{reason_codes}\n\n"
        "## Claim Boundary\n\n"
        "- `scoped_multi_benchmark_selector_superiority` remains false.\n"
        "- `global_selector_superiority` remains false.\n"
        "- HotpotQA operational comparison evidence is preserved only as operational utility.\n"
    )


def write_route7_artifacts(
    *,
    root: str | Path = ".",
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    docs_path: str | Path = DEFAULT_DOCS_PATH,
    hotpotqa_only: bool = False,
    fever_disabled: bool = False,
) -> dict[str, Path]:
    repo_root = Path(root)
    package = assess_route7_gate(root=repo_root, hotpotqa_only=hotpotqa_only, fever_disabled=fever_disabled)
    out = _resolve(repo_root, output_dir)
    docs = _resolve(repo_root, docs_path)
    paths = {
        "baseline_registry": out / "baseline_registry.json",
        "benchmark_matrix": out / "benchmark_matrix.json",
        "comparison_gate_report": out / "comparison_gate_report.json",
        "readiness_report": out / "readiness_report.json",
        "report_doc": docs,
        "worst_cell_report": out / "worst_cell_report.json",
    }
    write_json(paths["baseline_registry"], package.baseline_registry)
    write_json(paths["benchmark_matrix"], package.benchmark_matrix)
    write_json(paths["comparison_gate_report"], package.comparison_gate_report)
    write_json(paths["readiness_report"], package.readiness_report)
    write_json(paths["worst_cell_report"], package.worst_cell_report)
    docs.parent.mkdir(parents=True, exist_ok=True)
    docs.write_text(render_route7_report(package), encoding="utf-8")
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assess Route 7 scoped selector-superiority gates.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--docs-path", default=str(DEFAULT_DOCS_PATH))
    parser.add_argument("--hotpotqa-only", action="store_true")
    parser.add_argument("--fever-disabled", action="store_true")
    args = parser.parse_args(argv)

    paths = write_route7_artifacts(
        root=args.root,
        output_dir=args.output_dir,
        docs_path=args.docs_path,
        hotpotqa_only=args.hotpotqa_only,
        fever_disabled=args.fever_disabled,
    )
    readiness = json.loads(paths["readiness_report"].read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "claim_status": readiness["claim_status"],
                "route7_claim_allowed": readiness["route7_claim_allowed"],
                "scoped_multi_benchmark_selector_superiority": readiness[
                    "scoped_multi_benchmark_selector_superiority"
                ],
                "status": readiness["status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
