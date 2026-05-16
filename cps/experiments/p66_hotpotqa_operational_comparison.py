from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence


PHASE = "P66-HotpotQA"
DATASET = "HotpotQA"
TASK_FAMILY = "hotpotqa_answer_support_selection"
OPERATIONAL_METRIC_CLAIM_LEVEL = "operational_utility_only"
BRIDGE_STATUS = "failed_or_absent"
V12_SELECTOR = "v12_cost_aware_diagnostic_policy_operational_only"
BASELINE_SELECTORS = (
    "random_budget",
    "topk_relevance_or_token_budget",
    "mmr_density_greedy",
)
ORACLE_SELECTOR = "gold_support_oracle_upper_bound"
DEFAULT_TRACES_PATH = "artifacts/operator_inputs/p56_realistic_dispatch_traces.jsonl"
DEFAULT_P56_REPORT_PATH = "artifacts/benchmarks/p56_hotpotqa_trace_generation_report.json"
DEFAULT_OUTPUT_DIR = "artifacts/experiments/p56_hotpotqa_operational_comparison"
DEFAULT_DOC_PATH = "docs/experiments/P66-hotpotqa-operational-comparison.md"
DENIED_CLAIMS = (
    "calibrated_proxy_supported",
    "vinfo_proxy_supported",
    "measurement validation",
    "paper evidence",
    "P55 bridge support",
    "metric bridge support",
    "global selector superiority",
)
SUMMARY_COLUMNS = (
    "selector_name",
    "budget",
    "trace_count",
    "mean_supporting_fact_recall",
    "mean_gold_support_packets_selected",
    "mean_selected_tokens",
    "mean_budget_used",
    "within_budget_rate",
    "quality_per_1k_tokens",
    "selector_deployability",
)


def _stable_seed(payload: Any) -> int:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return int(hashlib.sha256(encoded).hexdigest()[:16], 16)


def _round(value: float) -> float:
    return round(float(value), 6)


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return _round(sum(values) / len(values))


def _sample_stddev(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def _percentile(sorted_values: Sequence[float], quantile: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = quantile * (len(sorted_values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(sorted_values[lower])
    weight = position - lower
    return float(sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight)


def _bootstrap_ci(deltas: Sequence[float], *, seed_payload: Any, samples: int = 2000) -> dict[str, Any]:
    if not deltas:
        return {"bootstrap_samples": 0, "ci95_high": 0.0, "ci95_low": 0.0, "method": "paired_bootstrap"}
    rng = random.Random(_stable_seed(["bootstrap", seed_payload]))
    n = len(deltas)
    means = []
    for _ in range(samples):
        means.append(sum(deltas[rng.randrange(n)] for _index in range(n)) / n)
    means.sort()
    return {
        "bootstrap_samples": samples,
        "ci95_high": _round(_percentile(means, 0.975)),
        "ci95_low": _round(_percentile(means, 0.025)),
        "method": "paired_bootstrap",
    }


def _permutation_p_value(deltas: Sequence[float], *, seed_payload: Any, samples: int = 4096) -> dict[str, Any]:
    if not deltas:
        return {"method": "paired_sign_flip_permutation", "p_value_two_sided": 1.0, "permutations": 0}
    observed = abs(sum(deltas) / len(deltas))
    if len(deltas) <= 16:
        total = 1 << len(deltas)
        extreme = 0
        for mask in range(total):
            permuted = [
                value if (mask >> index) & 1 else -value
                for index, value in enumerate(deltas)
            ]
            if abs(sum(permuted) / len(permuted)) >= observed - 1e-12:
                extreme += 1
        return {
            "method": "paired_sign_flip_permutation_exact",
            "p_value_two_sided": _round(extreme / total),
            "permutations": total,
        }
    rng = random.Random(_stable_seed(["permutation", seed_payload]))
    extreme = 0
    for _ in range(samples):
        permuted = [value if rng.randrange(2) else -value for value in deltas]
        if abs(sum(permuted) / len(permuted)) >= observed - 1e-12:
            extreme += 1
    return {
        "method": "paired_sign_flip_permutation_monte_carlo",
        "p_value_two_sided": _round((extreme + 1) / (samples + 1)),
        "permutations": samples,
    }


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{input_path.name}: line {line_number} must be a JSON object")
        rows.append(payload)
    return rows


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.name if candidate.is_absolute() else candidate.as_posix()


def _selector_deployability(trace: Mapping[str, Any]) -> str:
    plan = trace.get("projection_plan") or {}
    return str(plan.get("selector_deployability") or "")


def _validate_operational_trace(trace: Mapping[str, Any], index: int) -> list[str]:
    errors: list[str] = []
    if trace.get("dataset") != DATASET:
        errors.append(f"row_{index}:dataset_not_hotpotqa")
    if trace.get("task_family") != TASK_FAMILY:
        errors.append(f"row_{index}:wrong_task_family")
    if trace.get("metric_claim_level") != OPERATIONAL_METRIC_CLAIM_LEVEL:
        errors.append(f"row_{index}:metric_claim_level_not_operational_utility_only")
    bridge = trace.get("metric_bridge_witness") or {}
    if bridge.get("bridge_status") != BRIDGE_STATUS:
        errors.append(f"row_{index}:metric_bridge_witness_not_failed_or_absent")
    if bridge.get("calibrated_proxy_supported") is not False:
        errors.append(f"row_{index}:calibrated_proxy_supported_not_false")
    if bridge.get("vinfo_proxy_supported") is not False:
        errors.append(f"row_{index}:vinfo_proxy_supported_not_false")
    selector = trace.get("selector_name")
    if selector not in (*BASELINE_SELECTORS, V12_SELECTOR, ORACLE_SELECTOR):
        errors.append(f"row_{index}:unknown_selector")
    if selector == ORACLE_SELECTOR:
        plan = trace.get("projection_plan") or {}
        if plan.get("selector_deployability") != "non_deployable_upper_bound" or plan.get("non_deployable_upper_bound") is not True:
            errors.append(f"row_{index}:oracle_not_non_deployable_upper_bound")
    evaluation = trace.get("evaluation") or {}
    for field in ("supporting_fact_recall_at_budget", "gold_support_packets_selected_count", "selected_tokens", "budget_used", "within_budget"):
        if field not in evaluation:
            errors.append(f"row_{index}:missing_evaluation_{field}")
    if not trace.get("candidate_pool_hash"):
        errors.append(f"row_{index}:missing_candidate_pool_hash")
    if "budget_B_i" not in trace:
        errors.append(f"row_{index}:missing_budget_B_i")
    return errors


def _validate_traces(traces: Sequence[Mapping[str, Any]]) -> None:
    errors: list[str] = []
    for index, trace in enumerate(traces, start=1):
        errors.extend(_validate_operational_trace(trace, index))
    if errors:
        raise ValueError(";".join(sorted(set(errors))))


def _trace_metric(trace: Mapping[str, Any]) -> dict[str, float]:
    evaluation = trace["evaluation"]
    return {
        "budget_used": float(evaluation["budget_used"]),
        "gold_support_packets_selected": float(evaluation["gold_support_packets_selected_count"]),
        "selected_tokens": float(evaluation["selected_tokens"]),
        "supporting_fact_recall": float(evaluation["supporting_fact_recall_at_budget"]),
        "within_budget": 1.0 if evaluation["within_budget"] is True else 0.0,
    }


def _comparison_summary(traces: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[Mapping[str, Any]]] = {}
    for trace in traces:
        grouped.setdefault((str(trace["selector_name"]), int(trace["budget_B_i"])), []).append(trace)
    rows: list[dict[str, Any]] = []
    for (selector_name, budget), group in sorted(grouped.items(), key=lambda item: (item[0][1], item[0][0])):
        metrics = [_trace_metric(trace) for trace in group]
        mean_recall = _mean([metric["supporting_fact_recall"] for metric in metrics])
        mean_tokens = _mean([metric["selected_tokens"] for metric in metrics])
        quality = _round(mean_recall / (mean_tokens / 1000.0)) if mean_tokens > 0 else 0.0
        rows.append(
            {
                "budget": int(budget),
                "mean_budget_used": _mean([metric["budget_used"] for metric in metrics]),
                "mean_gold_support_packets_selected": _mean([metric["gold_support_packets_selected"] for metric in metrics]),
                "mean_selected_tokens": mean_tokens,
                "mean_supporting_fact_recall": mean_recall,
                "quality_per_1k_tokens": quality,
                "selector_deployability": _selector_deployability(group[0]),
                "selector_name": selector_name,
                "trace_count": len(group),
                "within_budget_rate": _mean([metric["within_budget"] for metric in metrics]),
            }
        )
    return rows


def _paired_index(traces: Sequence[Mapping[str, Any]]) -> dict[tuple[str, int, str], Mapping[str, Any]]:
    indexed: dict[tuple[str, int, str], Mapping[str, Any]] = {}
    for trace in traces:
        key = (str(trace["candidate_pool_hash"]), int(trace["budget_B_i"]), str(trace["selector_name"]))
        if key in indexed:
            raise ValueError(f"duplicate_matched_trace_key:{key[0]}:{key[1]}:{key[2]}")
        indexed[key] = trace
    return indexed


def _paired_tests(traces: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    indexed = _paired_index(traces)
    budgets = sorted({int(trace["budget_B_i"]) for trace in traces})
    results: dict[str, Any] = {}
    for budget in budgets:
        pool_hashes = sorted({
            str(trace["candidate_pool_hash"])
            for trace in traces
            if int(trace["budget_B_i"]) == budget and trace.get("selector_name") == V12_SELECTOR
        })
        for baseline in BASELINE_SELECTORS:
            pairs: list[tuple[float, float]] = []
            for pool_hash in pool_hashes:
                v12_trace = indexed.get((pool_hash, budget, V12_SELECTOR))
                baseline_trace = indexed.get((pool_hash, budget, baseline))
                if v12_trace is None or baseline_trace is None:
                    continue
                pairs.append(
                    (
                        float(v12_trace["evaluation"]["supporting_fact_recall_at_budget"]),
                        float(baseline_trace["evaluation"]["supporting_fact_recall_at_budget"]),
                    )
                )
            deltas = [v12_value - baseline_value for v12_value, baseline_value in pairs]
            mean_delta = _mean(deltas)
            stddev = _sample_stddev(deltas)
            key = f"{baseline}::budget_{budget}"
            ci = _bootstrap_ci(deltas, seed_payload=key)
            permutation = _permutation_p_value(deltas, seed_payload=key)
            results[key] = {
                "baseline_selector": baseline,
                "bootstrap_method": ci["method"],
                "bootstrap_samples": ci["bootstrap_samples"],
                "budget": budget,
                "ci95_high": ci["ci95_high"],
                "ci95_low": ci["ci95_low"],
                "cohens_dz": _round((sum(deltas) / len(deltas)) / stddev) if deltas and stddev > 0 else 0.0,
                "effect_direction": "v12_higher" if mean_delta > 0 else "v12_lower" if mean_delta < 0 else "tie",
                "matched_pairs": len(pairs),
                "mean_baseline": _mean([baseline_value for _v12_value, baseline_value in pairs]),
                "mean_paired_delta": mean_delta,
                "mean_v12": _mean([v12_value for v12_value, _baseline_value in pairs]),
                "paired_delta_stddev": _round(stddev),
                "p_value_two_sided": permutation["p_value_two_sided"],
                "permutation_method": permutation["method"],
                "permutations": permutation["permutations"],
                "primary_metric": "supporting_fact_recall_at_budget",
                "test_interpretation": "operational_comparison_only",
                "v12_selector": V12_SELECTOR,
            }
    return results


def _diagnostic_safety_summary(traces: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "bridge_witness_status": BRIDGE_STATUS,
        "calibrated_proxy_supported": False,
        "claim_status": "operational_utility_only; no_claim_upgrade",
        "denied_claims": list(DENIED_CLAIMS),
        "global_selector_superiority_claimed": False,
        "measurement_validation": False,
        "metric_bridge_support": False,
        "metric_claim_level": OPERATIONAL_METRIC_CLAIM_LEVEL,
        "oracle_status": "non_deployable_upper_bound",
        "oracle_trace_count": sum(1 for trace in traces if trace.get("selector_name") == ORACLE_SELECTOR),
        "oracle_used_as_deployable_baseline": False,
        "paper_evidence": False,
        "p55_bridge_support": False,
        "selector_superiority_claimed": False,
        "traces_compared": len(traces),
        "vinfo_proxy_supported": False,
    }


def compare_hotpotqa_operational_traces(traces: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    _validate_traces(traces)
    summary = _comparison_summary(traces)
    tests = _paired_tests(traces)
    return {
        "comparison_summary": summary,
        "diagnostic_safety_summary": _diagnostic_safety_summary(traces),
        "statistical_tests": {
            "comparison_target": V12_SELECTOR,
            "deployable_baselines": list(BASELINE_SELECTORS),
            "oracle_selector": ORACLE_SELECTOR,
            "oracle_treatment": "non_deployable_upper_bound_only",
            "v12_vs_baselines": tests,
        },
        "traces_loaded": len(traces),
    }


def _write_comparison_summary_csv(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SUMMARY_COLUMNS), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in SUMMARY_COLUMNS})
    return output_path


def _write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def _wins_losses_ties(tests: Mapping[str, Mapping[str, Any]]) -> dict[str, int]:
    result = {"losses": 0, "ties": 0, "wins": 0}
    for test in tests.values():
        mean_delta = float(test.get("mean_paired_delta", 0.0))
        ci_low = float(test.get("ci95_low", 0.0))
        ci_high = float(test.get("ci95_high", 0.0))
        if mean_delta > 0 and ci_low > 0:
            result["wins"] += 1
        elif mean_delta < 0 and ci_high < 0:
            result["losses"] += 1
        else:
            result["ties"] += 1
    return result


def _write_doc(path: str | Path, result: Mapping[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tests = result["statistical_tests"]["v12_vs_baselines"]
    win_loss = _wins_losses_ties(tests)
    lines = [
        "# P66 HotpotQA Operational Comparison",
        "",
        "## Purpose",
        "",
        "P66 compares accepted P56 HotpotQA dispatch traces under `operational_utility_only`.",
        "The bridge witness remains `failed_or_absent`, so this comparison is operational only.",
        "",
        "## Inputs",
        "",
        f"- Traces: `{DEFAULT_TRACES_PATH}`",
        f"- P56 report: `{DEFAULT_P56_REPORT_PATH}`",
        "",
        "## Outputs",
        "",
        f"- Comparison summary: `{DEFAULT_OUTPUT_DIR}/comparison_summary.csv`",
        f"- Statistical tests: `{DEFAULT_OUTPUT_DIR}/statistical_tests.json`",
        f"- Diagnostic safety summary: `{DEFAULT_OUTPUT_DIR}/diagnostic_safety_summary.json`",
        "",
        "## Results",
        "",
        f"- Traces compared: `{result['traces_loaded']}`",
        f"- V12 deployable-baseline wins with positive 95% CI: `{win_loss['wins']}`",
        f"- V12 losses with negative 95% CI: `{win_loss['losses']}`",
        f"- V12 ties or inconclusive comparisons: `{win_loss['ties']}`",
        "- Oracle is retained only as `non_deployable_upper_bound`.",
        "",
        "## Claim Boundary",
        "",
        "- Allowed claim: operational comparison result under `operational_utility_only`.",
        "- No calibrated_proxy_supported claim is introduced.",
        "- No vinfo_proxy_supported claim is introduced.",
        "- No measurement validation, paper evidence, P55 bridge support, metric bridge support, or global selector superiority claim is introduced.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def run_hotpotqa_p66_operational_comparison(
    *,
    doc_path: str | Path = DEFAULT_DOC_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    p56_report_path: str | Path = DEFAULT_P56_REPORT_PATH,
    traces_path: str | Path = DEFAULT_TRACES_PATH,
) -> dict[str, Any]:
    traces = _read_jsonl(traces_path)
    result = compare_hotpotqa_operational_traces(traces)
    output_path = Path(output_dir)
    statistical_tests = {
        **result["statistical_tests"],
        "input_p56_report_path": _path_ref(p56_report_path),
        "input_traces_path": _path_ref(traces_path),
        "phase": PHASE,
    }
    safety = {
        **result["diagnostic_safety_summary"],
        "comparison_summary_path": _path_ref(output_path / "comparison_summary.csv"),
        "doc_path": _path_ref(doc_path),
        "phase": PHASE,
        "statistical_tests_path": _path_ref(output_path / "statistical_tests.json"),
    }
    _write_comparison_summary_csv(output_path / "comparison_summary.csv", result["comparison_summary"])
    _write_json(output_path / "statistical_tests.json", statistical_tests)
    _write_json(output_path / "diagnostic_safety_summary.json", safety)
    _write_doc(doc_path, result)
    return {
        "budgets": sorted({row["budget"] for row in result["comparison_summary"]}),
        "comparison_summary_rows": len(result["comparison_summary"]),
        "doc_path": _path_ref(doc_path),
        "metric_claim_level": OPERATIONAL_METRIC_CLAIM_LEVEL,
        "output_dir": _path_ref(output_path),
        "phase": PHASE,
        "statistical_test_count": len(result["statistical_tests"]["v12_vs_baselines"]),
        "traces_loaded": result["traces_loaded"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run P66 HotpotQA operational comparison.")
    parser.add_argument("--traces-path", default=DEFAULT_TRACES_PATH)
    parser.add_argument("--p56-report-path", default=DEFAULT_P56_REPORT_PATH)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-path", default=DEFAULT_DOC_PATH)
    args = parser.parse_args(argv)
    result = run_hotpotqa_p66_operational_comparison(
        doc_path=args.doc_path,
        output_dir=args.output_dir,
        p56_report_path=args.p56_report_path,
        traces_path=args.traces_path,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
