from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from cps.experiments.artifacts import (
    BudgetWitness,
    CandidatePool,
    MaterializedContext,
    MetricBridgeWitness,
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
from cps.experiments.decision import resolve_selector_thresholds
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
    "metric_bridge_witness_materialized": "metric_bridge_witnesses.jsonl",
    "projection_diagnostics_materialized": "diagnostics.jsonl",
}
REQUIRED_ARTIFACT_COUNT_KEYS = (
    "candidate_pools",
    "projection_plans",
    "budget_witnesses",
    "materialized_contexts",
    "metric_bridge_witnesses",
    "diagnostics",
)


def _load_config(config_path: str | Path) -> dict[str, Any]:
    return json.loads(Path(config_path).read_text(encoding="utf-8"))


def _artifact_paths(output_dir: Path) -> dict[str, Path]:
    return {event_type: output_dir / filename for event_type, filename in ARTIFACT_FILENAMES.items()}


def _reset_derived_jsonl(paths: dict[str, Path]) -> None:
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")


def _reset_event_log(output_dir: Path) -> None:
    events_path = output_dir / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    events_path.write_text("", encoding="utf-8")


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


def _as_float(row: dict[str, Any], field: str, default: float | None = None) -> float | None:
    value = row.get(field)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _dispatch_ids(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row.get("dispatch_id", "unknown")) for row in rows]


def _rows_for_regime(rows: list[dict[str, Any]], regime: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("regime") == regime]


def _artifact_completeness_passed(rebuilt_summary: dict[str, Any]) -> bool:
    dispatch_count = int(rebuilt_summary.get("dispatch_count", 0) or 0)
    artifact_counts = dict(rebuilt_summary.get("artifact_counts") or {})
    counts_match = all(int(artifact_counts.get(key, -1) or -1) == dispatch_count for key in REQUIRED_ARTIFACT_COUNT_KEYS)
    return bool(rebuilt_summary.get("complete_artifact_sets")) and counts_match


def _record_failure(
    failures: list[dict[str, Any]],
    *,
    gate: str,
    reason: str,
    rows: list[dict[str, Any]] | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "gate": gate,
        "reason": reason,
    }
    if rows is not None:
        payload["dispatch_ids"] = _dispatch_ids(rows)
    if details:
        payload["details"] = details
    failures.append(payload)


def _redundancy_signature_passes(row: dict[str, Any], thresholds: dict[str, Any]) -> bool:
    monitored = thresholds["monitored_greedy"]
    block_ratio = _as_float(row, "block_ratio_lcb_star")
    synergy = _as_float(row, "synergy_fraction", 0.0) or 0.0
    gap = _as_float(row, "greedy_augmented_gap", 0.0) or 0.0
    return (
        block_ratio is not None
        and block_ratio >= float(monitored["block_ratio_lcb_star_gte"])
        and synergy <= float(monitored["synergy_fraction_lte"])
        and gap <= float(monitored["greedy_augmented_gap_lte"])
        and row.get("selector_regime_label") == "greedy_valid"
        and row.get("selector_action") == "monitored_greedy"
    )


def _pairwise_signature_passes(
    row: dict[str, Any],
    *,
    redundancy_b2_lcb: float | None,
    thresholds: dict[str, Any],
) -> bool:
    monitored = thresholds["monitored_greedy"]
    interaction_mass = _as_float(row, "positive_interaction_mass_ucb", 0.0) or 0.0
    pair_b2 = _as_float(row, "block_ratio_lcb_b2")
    synergy = _as_float(row, "synergy_fraction", 0.0) or 0.0
    augmented_value = _as_float(row, "augmented_value", 0.0) or 0.0
    greedy_value = _as_float(row, "greedy_value", 0.0) or 0.0
    complementarity_sensitive = (
        row.get("selector_regime_label") == "escalate"
        or synergy > float(monitored["synergy_fraction_lte"])
        or (pair_b2 is not None and redundancy_b2_lcb is not None and pair_b2 < redundancy_b2_lcb)
    )
    seeded_or_escalated = (
        row.get("selector_action") in {"seeded_augmented_greedy", "interaction_aware_local_search"}
        or augmented_value > greedy_value
    )
    return interaction_mass > 0.0 and complementarity_sensitive and seeded_or_escalated


def _higher_order_safety_passes(row: dict[str, Any]) -> bool:
    return row.get("selector_regime_label") != "greedy_valid" and row.get("selector_action") != "monitored_greedy"


def _triple_excess_gate_passes(row: dict[str, Any]) -> bool:
    return (
        row.get("triple_excess_flag") == "positive"
        or bool(row.get("higher_order_ambiguity_flag"))
        or row.get("selector_regime_label") == "ambiguous"
    )


def evaluate_pre_registered_validity_gate(
    diagnostics_rows: list[dict[str, Any]],
    rebuilt_summary: dict[str, Any],
    thresholds: dict[str, Any] | None,
) -> dict[str, Any]:
    resolved_thresholds = resolve_selector_thresholds(thresholds)
    rows = list(diagnostics_rows)
    failures: list[dict[str, Any]] = []
    gate_results: dict[str, Any] = {}

    artifact_passed = _artifact_completeness_passed(rebuilt_summary)
    gate_results["artifact_completeness"] = {
        "passed": artifact_passed,
        "artifact_counts": dict(rebuilt_summary.get("artifact_counts") or {}),
    }
    if not artifact_passed:
        _record_failure(
            failures,
            gate="artifact_completeness",
            reason="every dispatch must materialize candidate pool, projection plan, budget witness, materialized context, metric bridge witness, and diagnostics",
        )

    ambiguity_rows = [row for row in rows if row.get("selector_regime_label") == "ambiguous"]
    ambiguity_count = len(ambiguity_rows)
    gate_results["ambiguity_accounting"] = {
        "passed": ambiguity_count == 0,
        "ambiguity_count": ambiguity_count,
        "dispatch_ids": _dispatch_ids(ambiguity_rows),
    }
    if ambiguity_count:
        _record_failure(
            failures,
            gate="ambiguity_accounting",
            reason="ambiguous labels are reported separately and do not count as benchmark success",
            rows=ambiguity_rows,
        )

    redundancy_rows = _rows_for_regime(rows, "redundancy_dominated")
    redundancy_passed_rows = [row for row in redundancy_rows if _redundancy_signature_passes(row, resolved_thresholds)]
    gate_results["redundancy_signature"] = {
        "passed": bool(redundancy_rows) and len(redundancy_passed_rows) == len(redundancy_rows),
        "dispatch_ids": _dispatch_ids(redundancy_rows),
    }
    if not redundancy_rows:
        _record_failure(failures, gate="redundancy_signature", reason="missing redundancy_dominated rows")
    elif len(redundancy_passed_rows) != len(redundancy_rows):
        failed_rows = [row for row in redundancy_rows if row not in redundancy_passed_rows]
        _record_failure(
            failures,
            gate="redundancy_signature",
            reason="redundancy rows must show high block-ratio LCB, low synergy, small gap, greedy_valid label, and monitored_greedy action",
            rows=failed_rows,
        )

    redundancy_b2_values = [
        value
        for value in (_as_float(row, "block_ratio_lcb_b2") for row in redundancy_rows)
        if value is not None
    ]
    redundancy_b2_lcb = min(redundancy_b2_values) if redundancy_b2_values else None
    pairwise_rows = _rows_for_regime(rows, "sparse_pairwise_synergy")
    pairwise_passed_rows = [
        row
        for row in pairwise_rows
        if _pairwise_signature_passes(row, redundancy_b2_lcb=redundancy_b2_lcb, thresholds=resolved_thresholds)
    ]
    gate_results["pairwise_synergy_signature"] = {
        "passed": bool(pairwise_rows) and len(pairwise_passed_rows) == len(pairwise_rows),
        "dispatch_ids": _dispatch_ids(pairwise_rows),
        "redundancy_b2_lcb": redundancy_b2_lcb,
    }
    if not pairwise_rows:
        _record_failure(failures, gate="pairwise_synergy_signature", reason="missing sparse_pairwise_synergy rows")
    elif len(pairwise_passed_rows) != len(pairwise_rows):
        failed_rows = [row for row in pairwise_rows if row not in pairwise_passed_rows]
        _record_failure(
            failures,
            gate="pairwise_synergy_signature",
            reason="pairwise rows must show interaction mass, complementarity sensitivity, and seeded/escalated action or augmented improvement",
            rows=failed_rows,
        )

    higher_order_rows = _rows_for_regime(rows, "higher_order_synergy")
    higher_order_passed_rows = [row for row in higher_order_rows if _higher_order_safety_passes(row)]
    gate_results["higher_order_safety"] = {
        "passed": bool(higher_order_rows) and len(higher_order_passed_rows) == len(higher_order_rows),
        "dispatch_ids": _dispatch_ids(higher_order_rows),
    }
    if not higher_order_rows:
        _record_failure(failures, gate="higher_order_safety", reason="missing higher_order_synergy rows")
    elif len(higher_order_passed_rows) != len(higher_order_rows):
        failed_rows = [row for row in higher_order_rows if row not in higher_order_passed_rows]
        _record_failure(
            failures,
            gate="higher_order_safety",
            reason="higher-order rows must not be labeled high-confidence greedy_valid",
            rows=failed_rows,
        )

    triple_passed_rows = [row for row in higher_order_rows if _triple_excess_gate_passes(row)]
    gate_results["triple_excess_detection"] = {
        "passed": bool(higher_order_rows) and len(triple_passed_rows) == len(higher_order_rows),
        "dispatch_ids": _dispatch_ids(higher_order_rows),
    }
    if higher_order_rows and len(triple_passed_rows) != len(higher_order_rows):
        failed_rows = [row for row in higher_order_rows if row not in triple_passed_rows]
        _record_failure(
            failures,
            gate="triple_excess_detection",
            reason="higher-order rows require positive triple-excess evidence or ambiguity instead of false certification",
            rows=failed_rows,
        )

    return {
        "pre_registered_gate_passed": not failures,
        "pre_registered_gate_failures": failures,
        "pre_registered_gate_results": gate_results,
        "ambiguity_count": ambiguity_count,
    }


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
        diagnostics.selector_action,
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

    metric_bridge_witness = MetricBridgeWitness(
        **{key: common[key] for key in ("dispatch_id", "agent_id", "round_id", "regime")},
        calibration_epoch=None,
        active_stratum={"regime": instance.regime},
        model_tier=None,
        utility_metric="synthetic_oracle_value",
        metric_class="synthetic_oracle",
        materialization_policy={
            "algorithm": selected_result.algorithm,
            "selector_action": diagnostics.selector_action,
            "policy_recommendation": diagnostics.policy_recommendation,
            "budget_tokens": instance.budget_tokens,
            "selected_count": len(selected_ids),
            "excluded_count": len(excluded_ids),
        },
        decoding_policy={
            "mode": "synthetic_oracle",
            "value_source": "synthetic_oracle",
            "temperature": None,
        },
        bridge_scale=None,
        bridge_residual_zeta=None,
        effective_sample_size=None,
        drift_status="fresh",
        diagnostic_mode="synthetic_oracle",
        diagnostic_claim_level="structural_synthetic_only",
    )
    metric_bridge_payload = {
        **to_payload(metric_bridge_witness),
        **common,
        "candidate_pool_hash": pool_hash,
        "context_hash": materialized_context.context_hash,
    }
    _write_artifact_and_event(
        output_dir=output_dir,
        run_id=run_id,
        event_type="metric_bridge_witness_materialized",
        payload=metric_bridge_payload,
        notes="synthetic metric bridge witness materialized",
        artifact_paths=artifact_paths,
    )

    diagnostic_record = ProjectionDiagnostics(
        **{key: common[key] for key in ("dispatch_id", "agent_id", "round_id", "regime")},
        block_ratio_lcb_b2=diagnostics.block_ratio_lcb_b2,
        block_ratio_lcb_star=diagnostics.block_ratio_lcb_star,
        block_ratio_lcb_star_semantics=diagnostics.block_ratio_lcb_star_semantics,
        block_ratio_lcb_b3=diagnostics.block_ratio_lcb_b3,
        block_ratio_uninformative_count=diagnostics.block_ratio_uninformative_count,
        block_ratio_sample_count=diagnostics.block_ratio_sample_count,
        trace_decay_proxy=diagnostics.trace_decay_proxy,
        gamma_hat=diagnostics.gamma_hat,
        synergy_fraction=diagnostics.synergy_fraction,
        positive_interaction_mass_ucb=diagnostics.positive_interaction_mass_ucb,
        triple_excess_lcb_max=diagnostics.triple_excess_lcb_max,
        triple_excess_flag=diagnostics.triple_excess_flag,
        higher_order_ambiguity_flag=diagnostics.higher_order_ambiguity_flag,
        greedy_augmented_gap=diagnostics.greedy_augmented_gap,
        metric_claim_level=diagnostics.metric_claim_level,
        selector_regime_label=diagnostics.selector_regime_label,
        selector_action=diagnostics.selector_action,
        policy_recommendation=diagnostics.policy_recommendation,
        greedy_value=greedy_result.value,
        augmented_value=augmented_result.value,
        local_search_value=local_result.value,
        pairwise_samples=diagnostics.pairwise_samples,
        block_ratio_samples=diagnostics.block_ratio_samples,
        triple_samples=diagnostics.triple_samples,
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
        "policy_matches_expected": diagnostics.selector_action == instance.expected_policy,
        "gamma_hat_semantics": "legacy_trace_decay_alias_not_submodularity_ratio",
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
    _reset_event_log(resolved_output_dir)
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
    gate_evaluation = evaluate_pre_registered_validity_gate(diagnostics_rows, rebuilt, thresholds)
    status = "green" if gate_evaluation["pre_registered_gate_passed"] else "red"
    summary = {
        **rebuilt,
        **gate_evaluation,
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
