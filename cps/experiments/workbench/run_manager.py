from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.analysis.bridge_analyzer import analyze_metric_bridge_shadow
from cps.analysis.claim_ledger_exporter import export_claim_ledger
from cps.analysis.comparison_analyzer import analyze_selector_comparison
from cps.benchmarks.candidate_pool_manifest import build_candidate_pool_manifest
from cps.benchmarks.candidate_pool_manifest import validate_candidate_pool_contract
from cps.benchmarks.common import path_ref
from cps.benchmarks.common import pool_packets
from cps.benchmarks.common import read_jsonl
from cps.benchmarks.common import write_json
from cps.benchmarks.common import write_jsonl
from cps.evaluators.registry import default_evaluator_registry
from cps.evaluators.workbench_types import EvaluationRequest
from cps.experiments.workbench.artifact_paths import WorkbenchArtifactPaths
from cps.experiments.workbench.spec import WorkbenchRunSpec
from cps.experiments.workbench.spec import load_workbench_spec
from cps.selectors.registry import default_selector_registry
from cps.selectors.workbench_types import SelectionRequest


def _write_csv(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({key for row in rows for key in row})
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
    return output_path


def _blocked(paths: WorkbenchArtifactPaths, spec: WorkbenchRunSpec, reason_codes: Sequence[str]) -> dict[str, Any]:
    report = {
        "claim_mode": spec.claim_mode,
        "claim_status": spec.claim_status,
        "reason_codes": list(reason_codes),
        "run_id": spec.run_id,
        "schema_version": "workbench_blocked_report_v1",
        "status": "honestly_blocked",
    }
    write_json(paths.blocked_report, report)
    return report


def _materialized_context(selected_packets: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    sections = [
        {
            "content": str(packet.get("content") or ""),
            "packet_id": str(packet.get("packet_id") or ""),
            "source_doc_id": str(packet.get("source_doc_id") or ""),
            "token_cost": int(packet.get("token_cost") or 0),
        }
        for packet in selected_packets
    ]
    return {
        "materialization_order": [section["packet_id"] for section in sections],
        "materialization_policy": "fixed_selector_order_with_source_boundaries",
        "sections": sections,
        "text": "\n\n".join(section["content"] for section in sections),
    }


def _run_records(spec: WorkbenchRunSpec, pools: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    selector_registry = default_selector_registry()
    evaluator_registry = default_evaluator_registry()
    traces: list[dict[str, Any]] = []
    for pool in pools[: spec.limit]:
        candidate_pool = dict(pool.get("candidate_pool") or {})
        packets = pool_packets(pool)
        for budget in spec.budgets:
            for selector_name in spec.selectors:
                selection = selector_registry.select(
                    selector_name,
                    SelectionRequest(
                        budget=int(budget),
                        candidate_pool=candidate_pool,
                        dataset=spec.dataset,
                        instance_id=str(pool.get("instance_id") or ""),
                        query=str(pool.get("query") or ""),
                    ),
                )
                selected_packets = list(selection.selected_packets)
                evaluation_request = EvaluationRequest(
                    all_packets=packets,
                    candidate_pool_hash=selection.candidate_pool_hash,
                    claim_mode=spec.claim_mode,
                    dataset=spec.dataset,
                    instance_id=str(pool.get("instance_id") or ""),
                    query=str(pool.get("query") or ""),
                    selected_packets=selected_packets,
                    target=dict(pool.get("target") or {}),
                )
                evaluations = {
                    name: evaluator_registry.evaluate(name, evaluation_request).to_payload()
                    for name in spec.evaluators
                    if name != "claim_ledger"
                }
                operational = evaluations.get("operational", {"metrics": {}})["metrics"]
                trace = {
                    "budget": int(budget),
                    "budget_witness": {
                        "budget_requested": int(budget),
                        "budget_used": selection.budget_used,
                        "within_budget": selection.budget_used <= int(budget),
                    },
                    "candidate_pool_hash": selection.candidate_pool_hash,
                    "claim_mode": spec.claim_mode,
                    "considered_candidate_packet_ids": list(selection.considered_packet_ids),
                    "dataset": spec.dataset,
                    "evaluation": operational,
                    "evaluations": evaluations,
                    "excluded_packet_ids": list(selection.excluded_packet_ids),
                    "instance_id": str(pool.get("instance_id") or ""),
                    "materialized_context": _materialized_context(selected_packets),
                    "metric_bridge_witness": {
                        "bridge_status": "shadow_or_absent",
                        "calibrated_proxy_supported": False,
                        "metric_claim_level": "operational_utility_only",
                        "shadow_metric_bridge": True,
                        "vinfo_proxy_supported": False,
                    },
                    "metric_claim_level": selection.metric_claim_level,
                    "projection_plan": selection.projection_plan(),
                    "query": str(pool.get("query") or ""),
                    "run_id": spec.run_id,
                    "schema_version": "workbench_trace_v1",
                    "selected_packet_ids": list(selection.selected_packet_ids),
                    "selector_name": selection.selector_name,
                    "selector_regime_label": selection.selector_regime_label,
                    "target": dict(pool.get("target") or {}),
                }
                traces.append(trace)
    return sorted(
        traces,
        key=lambda row: (
            row["dataset"],
            row["instance_id"],
            row["budget"],
            row["selector_name"],
            row["candidate_pool_hash"],
        ),
    )


def run_workbench(spec: WorkbenchRunSpec) -> dict[str, Any]:
    paths = WorkbenchArtifactPaths.from_output_dir(spec.output_dir)
    if not Path(spec.candidate_pools_path).exists():
        return _blocked(paths, spec, ["candidate_pools_path_missing", "no_raw_dataset_download_attempted"])
    pools = read_jsonl(spec.candidate_pools_path)
    contract = validate_candidate_pool_contract(pools)
    if not contract.schema_valid:
        return _blocked(paths, spec, ["candidate_pool_contract_failed", *contract.errors])

    manifest = build_candidate_pool_manifest(pools[: spec.limit], dataset=spec.dataset, budgets=spec.budgets)
    write_json(paths.candidate_pool_manifest, manifest)
    traces = _run_records(spec, pools)
    write_jsonl(paths.traces, traces)

    bridge_result = analyze_metric_bridge_shadow([])
    write_json(paths.bridge_fit_summary, bridge_result["bridge_fit_summary"])
    write_json(paths.control_results, bridge_result["control_results"])
    write_json(paths.metric_bridge_witness, bridge_result["metric_bridge_witness"])
    write_json(paths.claim_gate_result, bridge_result["claim_gate_result"])

    comparison_result = analyze_selector_comparison(traces, target_selector="v12_diagnostic_policy")
    _write_csv(paths.comparison_summary, comparison_result["comparison_summary"])
    write_json(paths.statistical_tests, comparison_result["statistical_tests"])
    write_json(paths.diagnostic_safety_report, comparison_result["diagnostic_safety_report"])
    write_json(paths.superiority_claim_gate, comparison_result["superiority_claim_gate"])

    export_claim_ledger(
        output_dir=paths.output_dir,
        run_id=spec.run_id,
        accepted_claims=["scoped_operational_improvement"],
        bridge_result=bridge_result,
        comparison_result=comparison_result,
    )
    result = {
        "artifact_paths": paths.to_manifest(),
        "candidate_pools_used": min(len(pools), spec.limit),
        "claim_mode": spec.claim_mode,
        "claim_status": spec.claim_status,
        "config": spec.to_payload(),
        "run_id": spec.run_id,
        "schema_version": "workbench_manifest_v1",
        "status": "completed_claim_safe_smoke",
        "traces_generated": len(traces),
    }
    write_json(paths.manifest, result)
    return result


def run_workbench_from_config(config_path: str | Path) -> dict[str, Any]:
    return run_workbench(load_workbench_spec(config_path))


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the Integrated Validation Workbench.")
    parser.add_argument("config_path")
    args = parser.parse_args(argv)
    result = run_workbench_from_config(args.config_path)
    print(json.dumps({k: result[k] for k in ("status", "claim_status", "traces_generated") if k in result}, sort_keys=True))
    return 0 if result.get("status") == "completed_claim_safe_smoke" else 2


if __name__ == "__main__":
    raise SystemExit(main())
