from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from cps.experiments.artifacts import (
    BudgetWitness,
    CandidatePool,
    MaterializedContext,
    ProjectionDiagnostics,
    ProjectionPlan,
    append_jsonl,
    append_projection_event,
    context_hash,
    rebuild_projection_summary_from_events,
    to_payload,
    write_json,
    write_text,
)
from cps.experiments.diagnostics import DEFAULT_POLICY_THRESHOLDS, compute_diagnostics
from cps.experiments.reporting import format_synthetic_benchmark_report
from cps.experiments.selection import (
    bounded_local_search,
    greedy_select,
    item_costs,
    seeded_augmented_greedy,
    total_cost,
)
from cps.experiments.synthetic_regimes import SyntheticInstance, build_synthetic_instances


ARTIFACT_FILENAMES = {
    "candidate_pool_materialized": "candidate_pools.jsonl",
    "projection_plan_materialized": "projection_plans.jsonl",
    "budget_witness_materialized": "budget_witnesses.jsonl",
    "materialized_context_materialized": "materialized_contexts.jsonl",
    "projection_diagnostics_materialized": "diagnostics.jsonl",
}


def _load_config(config_path: str | Path) -> dict[str, Any]:
    return json.loads(Path(config_path).read_text(encoding="utf-8"))


def _artifact_paths(output_dir: Path) -> dict[str, Path]:
    return {event_type: output_dir / filename for event_type, filename in ARTIFACT_FILENAMES.items()}


def _reset_derived_jsonl(paths: dict[str, Path]) -> None:
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")


def _selected_result_for_policy(policy: str, greedy_result, augmented_result, local_result):
    if policy == "monitored_greedy":
        return greedy_result
    if policy == "seeded_augmented_greedy":
        return augmented_result
    return local_result


def _materialized_content(instance: SyntheticInstance, selected_ids: list[str]) -> str:
    lookup = instance.item_lookup()
    return "\n\n".join(f"[{item_id}]\n{lookup[item_id].text}" for item_id in selected_ids)


def _write_artifact_and_event(
    *,
    output_dir: Path,
    run_id: str,
    event_type: str,
    payload: dict[str, Any],
    notes: str,
    artifact_paths: dict[str, Path],
) -> None:
    append_jsonl(artifact_paths[event_type], payload)
    append_projection_event(
        store_dir=output_dir,
        event_type=event_type,
        run_id=run_id,
        payload=payload,
        notes=notes,
    )


def _run_instance(
    *,
    instance: SyntheticInstance,
    output_dir: Path,
    run_id: str,
    protocol_version: str,
    top_l: int,
    thresholds: dict[str, Any],
    artifact_paths: dict[str, Path],
) -> dict[str, Any]:
    item_payloads = instance.item_payloads()
    pool_hash = instance.candidate_pool_hash()
    common = {
        "dispatch_id": instance.instance_id,
        "agent_id": instance.agent_id,
        "round_id": instance.round_id,
        "regime": instance.regime,
        "seed": instance.seed,
        "protocol_version": protocol_version,
    }
    candidate_pool = CandidatePool(
        **{key: common[key] for key in ("dispatch_id", "agent_id", "round_id", "regime")},
        budget_tokens=instance.budget_tokens,
        items=item_payloads,
        candidate_pool_hash=pool_hash,
    )
    candidate_pool_payload = {**to_payload(candidate_pool), **common, "candidate_count": len(item_payloads)}
    _write_artifact_and_event(
        output_dir=output_dir,
        run_id=run_id,
        event_type="candidate_pool_materialized",
        payload=candidate_pool_payload,
        notes="synthetic candidate pool materialized",
        artifact_paths=artifact_paths,
    )

    greedy_result = greedy_select(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
    )
    augmented_result = seeded_augmented_greedy(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
    )
    local_result = bounded_local_search(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
        initial_selected_ids=augmented_result.selected_ids,
    )
    diagnostics = compute_diagnostics(
        items=instance.items,
        value_fn=instance.value,
        greedy_result=greedy_result,
        augmented_result=augmented_result,
        top_l=top_l,
        thresholds=thresholds,
    )
    selected_result = _selected_result_for_policy(
        diagnostics.policy_recommendation,
        greedy_result,
        augmented_result,
        local_result,
    )
    selected_ids = list(selected_result.selected_ids)
    excluded_ids = sorted(item.item_id for item in instance.items if item.item_id not in selected_ids)

    projection_plan = ProjectionPlan(
        **{key: common[key] for key in ("dispatch_id", "agent_id", "round_id", "regime")},
        algorithm=selected_result.algorithm,
        budget_tokens=instance.budget_tokens,
        candidate_pool_hash=pool_hash,
        selected_ids=selected_ids,
        excluded_ids=excluded_ids,
        trace=selected_result.trace,
        score_config={
            "value_source": "synthetic_oracle",
            "top_l_pairwise_diagnostic": top_l,
            "policy_thresholds": thresholds,
        },
    )
    projection_payload = {**to_payload(projection_plan), **common, "candidate_count": len(item_payloads)}
    _write_artifact_and_event(
        output_dir=output_dir,
        run_id=run_id,
        event_type="projection_plan_materialized",
        payload=projection_payload,
        notes="synthetic projection plan materialized",
        artifact_paths=artifact_paths,
    )

    costs = item_costs(instance.items)
    realized_tokens = total_cost(selected_ids, costs)
    budget_witness = BudgetWitness(
        **{key: common[key] for key in ("dispatch_id", "agent_id", "round_id", "regime")},
        budget_tokens=instance.budget_tokens,
        estimated_tokens=realized_tokens,
        realized_tokens=realized_tokens,
        within_budget=realized_tokens <= instance.budget_tokens,
        selected_ids=selected_ids,
        excluded_ids=excluded_ids,
        tolerance_violations=[] if realized_tokens <= instance.budget_tokens else [{"type": "budget_overflow"}],
    )
    witness_payload = {**to_payload(budget_witness), **common, "candidate_pool_hash": pool_hash}
    _write_artifact_and_event(
        output_dir=output_dir,
        run_id=run_id,
        event_type="budget_witness_materialized",
        payload=witness_payload,
        notes="synthetic budget witness materialized",
        artifact_paths=artifact_paths,
    )

    content = _materialized_content(instance, selected_ids)
    materialized_context = MaterializedContext(
        **{key: common[key] for key in ("dispatch_id", "agent_id", "round_id", "regime")},
        selected_ids=selected_ids,
        section_order=selected_ids,
        content=content,
        token_count=realized_tokens,
        context_hash=context_hash(content),
    )
    context_payload = {**to_payload(materialized_context), **common, "candidate_pool_hash": pool_hash}
    _write_artifact_and_event(
        output_dir=output_dir,
        run_id=run_id,
        event_type="materialized_context_materialized",
        payload=context_payload,
        notes="synthetic materialized context recorded",
        artifact_paths=artifact_paths,
    )

    diagnostic_record = ProjectionDiagnostics(
        **{key: common[key] for key in ("dispatch_id", "agent_id", "round_id", "regime")},
        gamma_hat=diagnostics.gamma_hat,
        synergy_fraction=diagnostics.synergy_fraction,
        greedy_augmented_gap=diagnostics.greedy_augmented_gap,
        policy_recommendation=diagnostics.policy_recommendation,
        greedy_value=greedy_result.value,
        augmented_value=augmented_result.value,
        local_search_value=local_result.value,
        thresholds=diagnostics.thresholds,
        notes=diagnostics.notes,
    )
    diagnostic_payload = {
        **to_payload(diagnostic_record),
        **common,
        "candidate_pool_hash": pool_hash,
        "candidate_count": len(item_payloads),
        "budget_tokens": instance.budget_tokens,
        "algorithm": selected_result.algorithm,
        "selected_ids": selected_ids,
        "excluded_ids": excluded_ids,
        "estimated_tokens": realized_tokens,
        "realized_tokens": realized_tokens,
        "within_budget": realized_tokens <= instance.budget_tokens,
        "expected_policy": instance.expected_policy,
        "policy_matches_expected": diagnostics.policy_recommendation == instance.expected_policy,
        "pairwise_sample_count": len(diagnostics.pairwise_samples),
        "pairwise_synergy_count": sum(1 for row in diagnostics.pairwise_samples if row["label"] == "synergy"),
    }
    _write_artifact_and_event(
        output_dir=output_dir,
        run_id=run_id,
        event_type="projection_diagnostics_materialized",
        payload=diagnostic_payload,
        notes="synthetic projection diagnostics materialized",
        artifact_paths=artifact_paths,
    )
    return diagnostic_payload


def run_synthetic_benchmark(
    *,
    config_path: str | Path,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    config = _load_config(config_path)
    resolved_output_dir = Path(output_dir or config["output_dir"]).resolve()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    artifact_paths = _artifact_paths(resolved_output_dir)
    _reset_derived_jsonl(artifact_paths)

    seed = int(config.get("seed", 20260418))
    protocol_version = str(config.get("protocol_version", "synthetic_regime.v1"))
    run_id = str(config.get("run_id") or f"synthetic-regime-smoke-{seed}")
    thresholds = dict(config.get("policy_thresholds") or DEFAULT_POLICY_THRESHOLDS)
    instances = build_synthetic_instances(
        regimes=config["regimes"],
        instances_per_regime=int(config.get("instances_per_regime", 1)),
        seed=seed,
    )
    diagnostics_rows = [
        _run_instance(
            instance=instance,
            output_dir=resolved_output_dir,
            run_id=run_id,
            protocol_version=protocol_version,
            top_l=int(config.get("top_l", 8)),
            thresholds=thresholds,
            artifact_paths=artifact_paths,
        )
        for instance in instances
    ]
    rebuilt = rebuild_projection_summary_from_events(resolved_output_dir, run_id=run_id)
    expected_matches = sum(1 for row in diagnostics_rows if row["policy_matches_expected"])
    status = "green" if rebuilt["complete_artifact_sets"] and expected_matches == len(diagnostics_rows) else "red"
    summary = {
        **rebuilt,
        "status": status,
        "run_id": run_id,
        "config_path": str(Path(config_path).resolve()),
        "output_dir": str(resolved_output_dir),
        "expected_policy_matches": expected_matches,
        "artifact_paths": {
            "events": str(resolved_output_dir / "events.jsonl"),
            **{event_type: str(path) for event_type, path in artifact_paths.items()},
        },
        "interpretation_limits": [
            "synthetic proxy-layer diagnostic only",
            "no scheduler implementation",
            "no memory architecture implementation",
            "no theorem-inheritance claim",
            "no system-level performance claim",
        ],
    }
    summary_path = write_json(resolved_output_dir / "summary.json", summary)
    report_path = write_text(
        resolved_output_dir / "report.md",
        format_synthetic_benchmark_report(summary=summary, diagnostics_rows=diagnostics_rows),
    )
    append_projection_event(
        store_dir=resolved_output_dir,
        event_type="synthetic_benchmark_summary_materialized",
        run_id=run_id,
        payload={
            "run_id": run_id,
            "seed": seed,
            "protocol_version": protocol_version,
            "status": status,
            "dispatch_count": len(diagnostics_rows),
            "summary_path": str(summary_path),
            "report_path": str(report_path),
        },
        notes="synthetic benchmark summary materialized",
    )
    return {
        "status": status,
        "run_id": run_id,
        "summary_path": str(summary_path),
        "report_path": str(report_path),
        "events_path": str(resolved_output_dir / "events.jsonl"),
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the synthetic context-projection regime benchmark.")
    parser.add_argument("--config", default="configs/runs/synthetic-regime-smoke.json")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    report = run_synthetic_benchmark(config_path=args.config, output_dir=args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "green" else 1


if __name__ == "__main__":
    raise SystemExit(main())
