from __future__ import annotations

from typing import Any


def format_synthetic_benchmark_report(
    *,
    summary: dict[str, Any],
    diagnostics_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# Synthetic Regime Benchmark Report",
        "",
        "This is a synthetic proxy-layer diagnostic benchmark. It is not a scheduler result, not a memory-system result, not a theorem-inheritance claim, and not a system-level performance claim.",
        "",
        "## Summary",
        "",
        f"- Run id: `{summary['run_id']}`",
        f"- Status: `{summary['status']}`",
        f"- Dispatches: `{summary['dispatch_count']}`",
        f"- Complete artifact sets: `{summary['complete_artifact_sets']}`",
        f"- Expected policy matches: `{summary['expected_policy_matches']}/{summary['dispatch_count']}`",
        "",
        "## Regime Diagnostics",
        "",
        "| Regime | Dispatches | Avg gamma_hat | Avg synergy fraction | Avg greedy-augmented gap | Policy counts |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for regime, payload in summary["per_regime"].items():
        policy_counts = ", ".join(
            f"{policy}: {count}" for policy, count in sorted(payload["policy_recommendations"].items())
        )
        lines.append(
            "| "
            f"{regime} | "
            f"{payload['dispatch_count']} | "
            f"{payload['avg_gamma_hat']:.6f} | "
            f"{payload['avg_synergy_fraction']:.6f} | "
            f"{payload['avg_greedy_augmented_gap']:.6f} | "
            f"{policy_counts} |"
        )

    lines.extend(
        [
            "",
            "## Dispatch Rows",
            "",
            "| Dispatch | Regime | gamma_hat | Synergy fraction | Gap | Recommendation | Expected |",
            "|---|---|---:|---:|---:|---|---|",
        ]
    )
    for row in diagnostics_rows:
        lines.append(
            "| "
            f"{row['dispatch_id']} | "
            f"{row['regime']} | "
            f"{row['gamma_hat']:.6f} | "
            f"{row['synergy_fraction']:.6f} | "
            f"{row['greedy_augmented_gap']:.6f} | "
            f"{row['policy_recommendation']} | "
            f"{row['expected_policy']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation Limits",
            "",
            "- Thresholds are provisional calibration bins for synthetic regimes.",
            "- The benchmark validates diagnostic plumbing and controlled regime discrimination only.",
            "- It does not implement a scheduler, memory architecture, openWorker port, or live benchmark claim.",
            "- Runtime artifacts are sidecar audit records for replay and should not be read as production interfaces.",
            "",
        ]
    )
    return "\n".join(lines)
