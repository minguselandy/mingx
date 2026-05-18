from __future__ import annotations

from collections import defaultdict
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.analysis.diagnostic_safety_report import build_diagnostic_safety_report
from cps.analysis.stat_tests import mean
from cps.analysis.stat_tests import paired_mean_delta


def _metric(record: Mapping[str, Any]) -> float:
    evaluation = record.get("evaluation") or {}
    return float(evaluation.get("supporting_fact_recall_at_budget", 0.0))


def _tokens(record: Mapping[str, Any]) -> float:
    evaluation = record.get("evaluation") or {}
    return float(evaluation.get("selected_tokens", 0.0))


def analyze_selector_comparison(
    records: Sequence[Mapping[str, Any]],
    *,
    target_selector: str = "v12_diagnostic_policy",
) -> dict[str, Any]:
    rows = [dict(record) for record in records]
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("selector_name") or ""), int(row.get("budget") or row.get("budget_B_i") or 0))].append(row)

    summary: list[dict[str, Any]] = []
    for (selector, budget), group in sorted(grouped.items(), key=lambda item: (item[0][1], item[0][0])):
        metric_values = [_metric(row) for row in group]
        token_values = [_tokens(row) for row in group]
        mean_tokens = mean(token_values)
        mean_metric = mean(metric_values)
        summary.append(
            {
                "budget": budget,
                "mean_selected_tokens": mean_tokens,
                "mean_supporting_fact_recall": mean_metric,
                "quality_per_1k_tokens": round(mean_metric / (mean_tokens / 1000.0), 6) if mean_tokens else 0.0,
                "selector_name": selector,
                "trace_count": len(group),
            }
        )

    by_pair = {
        (
            str(row.get("candidate_pool_hash") or ""),
            int(row.get("budget") or row.get("budget_B_i") or 0),
            str(row.get("selector_name") or ""),
        ): row
        for row in rows
    }
    pool_budget_keys = sorted(
        {
            (str(row.get("candidate_pool_hash") or ""), int(row.get("budget") or row.get("budget_B_i") or 0))
            for row in rows
            if row.get("selector_name") == target_selector
        }
    )
    baselines = sorted({str(row.get("selector_name") or "") for row in rows if row.get("selector_name") != target_selector})
    tests: dict[str, Any] = {}
    for baseline in baselines:
        for _pool_hash, budget in pool_budget_keys:
            target_values: list[float] = []
            baseline_values: list[float] = []
            for pool_hash, candidate_budget in pool_budget_keys:
                if candidate_budget != budget:
                    continue
                target = by_pair.get((pool_hash, budget, target_selector))
                base = by_pair.get((pool_hash, budget, baseline))
                if target is None or base is None:
                    continue
                target_values.append(_metric(target))
                baseline_values.append(_metric(base))
            key = f"{target_selector}::vs::{baseline}::budget_{budget}"
            tests[key] = {
                **paired_mean_delta(target_values, baseline_values),
                "baseline_selector": baseline,
                "claim_mode": "shadow",
                "primary_metric": "supporting_fact_recall_at_budget",
                "target_selector": target_selector,
            }
    return {
        "comparison_summary": summary,
        "diagnostic_safety_report": build_diagnostic_safety_report(traces_compared=len(rows)),
        "statistical_tests": tests,
        "superiority_claim_gate": {
            "claim_mode": "shadow",
            "global_selector_superiority": False,
            "reason_codes": ["superiority_shadow_mode", "no_independent_review_acceptance", "no_claim_upgrade"],
            "scoped_operational_improvement": True,
            "selector_superiority_claimed": False,
            "shadow_selector_superiority": True,
        },
    }
