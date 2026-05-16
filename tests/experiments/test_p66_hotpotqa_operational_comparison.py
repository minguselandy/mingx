from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from cps.experiments.p66_hotpotqa_operational_comparison import (
    BASELINE_SELECTORS,
    ORACLE_SELECTOR,
    V12_SELECTOR,
    compare_hotpotqa_operational_traces,
    run_hotpotqa_p66_operational_comparison,
)


def _trace(selector: str, pool_hash: str, budget: int, recall: float, tokens: int, gold_count: int) -> dict:
    return {
        "budget_B_i": budget,
        "budget_witness": {"budget_requested": budget, "budget_used": tokens, "within_budget": True},
        "candidate_pool_hash": pool_hash,
        "dataset": "HotpotQA",
        "evaluation": {
            "answer_available_if_present": recall > 0,
            "budget_used": tokens,
            "gold_support_packets_selected": ["g1"] * gold_count,
            "gold_support_packets_selected_count": gold_count,
            "selected_tokens": tokens,
            "supporting_fact_recall_at_budget": recall,
            "within_budget": True,
        },
        "metric_bridge_witness": {
            "bridge_status": "failed_or_absent",
            "calibrated_proxy_supported": False,
            "metric_claim_level": "operational_utility_only",
            "source": "P63R HotpotQA failed_closed_gate_failed / FixB operational_utility_only",
            "vinfo_proxy_supported": False,
        },
        "metric_claim_level": "operational_utility_only",
        "projection_plan": {
            "non_deployable_upper_bound": selector == ORACLE_SELECTOR,
            "selector_deployability": "non_deployable_upper_bound"
            if selector == ORACLE_SELECTOR
            else "deployable_operational_baseline",
            "selector_name": selector,
        },
        "selector_name": selector,
        "task_family": "hotpotqa_answer_support_selection",
    }


def _trace_rows() -> list[dict]:
    rows: list[dict] = []
    for pool_hash, random_recall, topk_recall, mmr_recall, v12_recall in (
        ("pool-1", 0.0, 0.5, 0.5, 1.0),
        ("pool-2", 0.5, 0.5, 1.0, 1.0),
        ("pool-3", 0.0, 1.0, 0.5, 0.5),
    ):
        rows.extend(
            [
                _trace("random_budget", pool_hash, 512, random_recall, 100, int(random_recall > 0)),
                _trace("topk_relevance_or_token_budget", pool_hash, 512, topk_recall, 100, int(topk_recall > 0)),
                _trace("mmr_density_greedy", pool_hash, 512, mmr_recall, 100, int(mmr_recall > 0)),
                _trace(V12_SELECTOR, pool_hash, 512, v12_recall, 100, int(v12_recall > 0)),
                _trace(ORACLE_SELECTOR, pool_hash, 512, 1.0, 100, 1),
            ]
        )
    return rows


def test_operational_summary_groups_by_selector_and_budget():
    result = compare_hotpotqa_operational_traces(_trace_rows())
    summaries = {
        (row["selector_name"], row["budget"]): row
        for row in result["comparison_summary"]
    }

    v12_summary = summaries[(V12_SELECTOR, 512)]
    assert v12_summary["trace_count"] == 3
    assert v12_summary["mean_supporting_fact_recall"] == pytest.approx(0.833333)
    assert v12_summary["mean_selected_tokens"] == pytest.approx(100.0)
    assert v12_summary["within_budget_rate"] == pytest.approx(1.0)
    assert v12_summary["quality_per_1k_tokens"] == pytest.approx(8.333333)


def test_v12_is_compared_against_deployable_baselines_only():
    result = compare_hotpotqa_operational_traces(_trace_rows())
    tests = result["statistical_tests"]["v12_vs_baselines"]

    assert set(tests) == {
        "random_budget::budget_512",
        "topk_relevance_or_token_budget::budget_512",
        "mmr_density_greedy::budget_512",
    }
    assert ORACLE_SELECTOR not in json.dumps(tests, sort_keys=True)
    assert tests["random_budget::budget_512"]["mean_paired_delta"] == pytest.approx(0.666667)


def test_oracle_is_reported_as_non_deployable_upper_bound():
    result = compare_hotpotqa_operational_traces(_trace_rows())
    safety = result["diagnostic_safety_summary"]

    assert safety["oracle_status"] == "non_deployable_upper_bound"
    assert safety["oracle_used_as_deployable_baseline"] is False
    assert safety["metric_claim_level"] == "operational_utility_only"


def test_claim_upgrade_trace_is_rejected():
    rows = _trace_rows()
    rows[0]["metric_claim_level"] = "calibrated_proxy_supported"

    with pytest.raises(ValueError, match="metric_claim_level_not_operational_utility_only"):
        compare_hotpotqa_operational_traces(rows)


def test_run_writes_p66_artifacts_deterministically(workspace_tmp_dir: Path):
    traces_path = workspace_tmp_dir / "traces.jsonl"
    report_path = workspace_tmp_dir / "p56_report.json"
    output_dir = workspace_tmp_dir / "comparison"
    doc_path = workspace_tmp_dir / "P66-hotpotqa-operational-comparison.md"
    traces_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in _trace_rows()),
        encoding="utf-8",
    )
    report_path.write_text(json.dumps({"traces_validated": len(_trace_rows())}, sort_keys=True), encoding="utf-8")

    first = run_hotpotqa_p66_operational_comparison(
        doc_path=doc_path,
        output_dir=output_dir,
        p56_report_path=report_path,
        traces_path=traces_path,
    )
    first_csv = (output_dir / "comparison_summary.csv").read_bytes()
    first_tests = (output_dir / "statistical_tests.json").read_bytes()
    second = run_hotpotqa_p66_operational_comparison(
        doc_path=doc_path,
        output_dir=output_dir,
        p56_report_path=report_path,
        traces_path=traces_path,
    )

    assert first["traces_loaded"] == len(_trace_rows())
    assert second == first
    assert (output_dir / "comparison_summary.csv").read_bytes() == first_csv
    assert (output_dir / "statistical_tests.json").read_bytes() == first_tests
    with (output_dir / "comparison_summary.csv").open(newline="", encoding="utf-8") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert {row["selector_name"] for row in csv_rows} == {V12_SELECTOR, ORACLE_SELECTOR, *BASELINE_SELECTORS}
    assert "No calibrated_proxy_supported claim" in doc_path.read_text(encoding="utf-8")
