from __future__ import annotations

from typing import Any


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _fmt_counts(counts: dict[str, int] | None) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}: {value}" for key, value in sorted(counts.items()))


def format_synthetic_benchmark_report(
    *,
    summary: dict[str, Any],
    diagnostics_rows: list[dict[str, Any]],
) -> str:
    artifact_counts = dict(summary.get("artifact_counts") or {})
    gate_results = dict(summary.get("pre_registered_gate_results") or {})
    gate_failures = list(summary.get("pre_registered_gate_failures") or [])
    higher_order_rows = [row for row in diagnostics_rows if row.get("regime") == "higher_order_synergy"]
    lines = [
        "# Synthetic Regime Benchmark Report",
        "",
        "## Summary",
        "",
        f"- Run id: `{summary['run_id']}`",
        f"- Status: `{summary['status']}`",
        f"- Dispatches: `{summary['dispatch_count']}`",
        f"- Pre-registered gate passed: `{summary['pre_registered_gate_passed']}`",
        f"- Ambiguity count: `{summary['ambiguity_count']}`",
        f"- Metric claim levels: `{_fmt_counts(summary.get('metric_claim_level_counts'))}`",
        f"- Selector regime labels: `{_fmt_counts(summary.get('selector_regime_label_counts'))}`",
        f"- Selector actions: `{_fmt_counts(summary.get('selector_action_counts'))}`",
        f"- Expected policy matches (legacy compatibility detail): `{summary['expected_policy_matches']}/{summary['dispatch_count']}`",
        "",
        "## Artifact completeness",
        "",
        f"- Complete artifact sets: `{summary['complete_artifact_sets']}`",
        "- Required artifacts include `CandidatePool`, `ProjectionPlan`, `BudgetWitness`, `MaterializedContext`, `MetricBridgeWitness`, and diagnostics.",
        "",
        "| Artifact | Count |",
        "|---|---:|",
    ]
    for artifact_name in (
        "candidate_pools",
        "projection_plans",
        "budget_witnesses",
        "materialized_contexts",
        "metric_bridge_witnesses",
        "diagnostics",
    ):
        display_name = "MetricBridgeWitness" if artifact_name == "metric_bridge_witnesses" else artifact_name
        lines.append(f"| {display_name} | {artifact_counts.get(artifact_name, 0)} |")

    lines.extend(
        [
            "",
            "## Pre-registered validity gate",
            "",
            f"- Gate passed: `{summary['pre_registered_gate_passed']}`",
            f"- Failure count: `{len(gate_failures)}`",
            "- Block-ratio LCB diagnostics are reported through the `block_ratio_lcb_b2`, `block_ratio_lcb_star`, and `block_ratio_lcb_b3` fields.",
            "- `block_ratio_lcb_star` is currently `placeholder_conservative_min_b2_b3_not_degree_adaptive_star`, not a paper-grade degree-adaptive star-block estimator.",
            "",
            "| Gate | Passed |",
            "|---|---|",
        ]
    )
    for gate_name, payload in sorted(gate_results.items()):
        lines.append(f"| {gate_name} | {_fmt(payload.get('passed'))} |")
    if gate_failures:
        lines.extend(["", "| Gate | Reason | Dispatch ids |", "|---|---|---|"])
        for failure in gate_failures:
            lines.append(
                "| "
                f"{failure.get('gate')} | "
                f"{failure.get('reason')} | "
                f"{', '.join(failure.get('dispatch_ids', []))} |"
            )

    lines.extend(
        [
            "",
            "## Regime diagnostics table",
            "",
            "| Dispatch | Regime | block_ratio_lcb_b2 | block_ratio_lcb_star | block_ratio_lcb_star_semantics | block_ratio_lcb_b3 | trace_decay_proxy | synergy_fraction | positive_interaction_mass_ucb | triple_excess_flag | higher_order_ambiguity_flag | greedy_augmented_gap | metric_claim_level | selector_regime_label | selector_action |",
            "|---|---|---:|---:|---|---:|---:|---:|---:|---|---|---:|---|---|---|",
        ]
    )
    for row in diagnostics_rows:
        lines.append(
            "| "
            f"{row['dispatch_id']} | "
            f"{row['regime']} | "
            f"{_fmt(row['block_ratio_lcb_b2'])} | "
            f"{_fmt(row['block_ratio_lcb_star'])} | "
            f"{row['block_ratio_lcb_star_semantics']} | "
            f"{_fmt(row['block_ratio_lcb_b3'])} | "
            f"{_fmt(row['trace_decay_proxy'])} | "
            f"{_fmt(row['synergy_fraction'])} | "
            f"{_fmt(row['positive_interaction_mass_ucb'])} | "
            f"{row['triple_excess_flag']} | "
            f"{row['higher_order_ambiguity_flag']} | "
            f"{row['greedy_augmented_gap']:.6f} | "
            f"{row['metric_claim_level']} | "
            f"{row['selector_regime_label']} | "
            f"{row['selector_action']} |"
        )

    lines.extend(
        [
            "",
            "## Ambiguity accounting",
            "",
            f"- Ambiguous labels: `{summary['ambiguity_count']}`",
            "- Ambiguous labels are reported as safety outcomes and are not counted as benchmark success.",
            f"- Selector regime label counts: `{_fmt_counts(summary.get('selector_regime_label_counts'))}`",
            "",
            "## Higher-order safety check",
            "",
            "| Dispatch | Triple flag | Higher-order ambiguity | Regime label | Action |",
            "|---|---|---|---|---|",
        ]
    )
    for row in higher_order_rows:
        lines.append(
            "| "
            f"{row['dispatch_id']} | "
            f"{row['triple_excess_flag']} | "
            f"{row['higher_order_ambiguity_flag']} | "
            f"{row['selector_regime_label']} | "
            f"{row['selector_action']} |"
        )
    if not higher_order_rows:
        lines.append("| n/a | n/a | n/a | n/a | n/a |")

    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "- All synthetic diagnostic claims in this report are `structural_synthetic_only`.",
            "- Thresholds are provisional calibration bins for synthetic regimes.",
            "- The benchmark validates diagnostic plumbing and controlled regime discrimination only.",
            "- It is not deployment certification and does not certify deployed V-information weak submodularity.",
            "- It does not implement a scheduler, memory architecture, openWorker port, or live benchmark claim.",
            "- It is not a theorem-inheritance claim and not a system-level performance claim.",
            "- Runtime artifacts are sidecar audit records for replay and should not be read as production interfaces.",
            "",
        ]
    )
    return "\n".join(lines)
