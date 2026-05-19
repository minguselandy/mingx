from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter
from collections import defaultdict
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.common import read_jsonl
from cps.benchmarks.common import write_json
from cps.benchmarks.common import write_jsonl
from cps.benchmarks.schemas import make_candidate_pool
from cps.benchmarks.schemas import make_evidence_packet
from cps.experiments.workbench.run_manager import run_workbench
from cps.experiments.workbench.spec import WorkbenchRunSpec


DEFAULT_OUTPUT_DIR = Path("artifacts/experiments/gamma_operational_expansion")
DEFAULT_DOCS_PATH = Path("docs/experiments/Gamma-operational-expansion-final-report.md")
DEFAULT_HOTPOTQA_CANDIDATE_POOLS_PATH = Path("artifacts/benchmarks/hotpotqa_candidate_pools.jsonl")
DEFAULT_PROJECT_NATIVE_PACKETS_PATH = Path(
    "artifacts/experiments/realistic_task_model_adjudicated_v12/realistic_task_packets.jsonl"
)
DEFAULT_PROJECT_NATIVE_COMPARISON_PATH = Path(
    "artifacts/experiments/realistic_task_model_adjudicated_v12/realistic_selector_comparison.csv"
)

CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
WORKBENCH_CLAIM_STATUS = "operational_utility_only; no_claim_upgrade"
GAMMA_SCHEMA_VERSION = "gamma_operational_expansion_v1"
PROJECT_NATIVE_DATASET = "ProjectNativeRealisticTasks"
PROJECT_NATIVE_SPLIT = "fixture_v12"
DENIED_CLAIMS = (
    "selector superiority",
    "metric bridge support",
    "measurement validation",
    "calibrated_proxy_supported",
    "vinfo_proxy_supported",
    "paper evidence",
)
WORKBENCH_SELECTORS = (
    "random_budget",
    "bm25_topk",
    "mmr_density_greedy",
    "v12_diagnostic_policy",
)
WORKBENCH_EVALUATORS = ("operational", "diagnostic_safety", "claim_ledger")
HOTPOTQA_BUDGETS = (256, 512)
PROJECT_NATIVE_BUDGETS = (32, 34, 38)
LEFTOVER_MARKERS = ("beta", "hybrid_label_model", "route4d", "route6c")
FORBIDDEN_STAGE_PREFIXES = (
    ".codex/goal-state/",
    "artifacts/operator_inputs/",
    "artifacts/raw/",
    "raw_api_dumps/",
    "raw_dataset_mirrors/",
    "docs/archive/context_projection",
    "docs/claim-ledger",
)


def _read_json(path: str | Path) -> dict[str, Any]:
    input_path = Path(path)
    if not input_path.exists() or not input_path.is_file():
        return {}
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _write_csv(path: str | Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return output_path


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.name if candidate.is_absolute() else candidate.as_posix()


def _workbench_path(path: str | Path) -> str:
    return Path(path).as_posix()


def _round(value: float) -> float:
    return round(float(value), 6)


def _mean(values: Sequence[float]) -> float:
    return _round(sum(values) / len(values)) if values else 0.0


def _git_lines(root: Path, args: Sequence[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _leftover_category(path: str) -> str:
    lowered = path.casefold()
    if "route4d" in lowered:
        return "Route4D"
    if "route6c" in lowered:
        return "Route6C"
    if "beta" in lowered or "hybrid_label_model" in lowered:
        return "Beta"
    return "other"


def _forbidden_stage_reason(path: str) -> str | None:
    normalized = path.replace("\\", "/")
    for prefix in FORBIDDEN_STAGE_PREFIXES:
        if normalized.startswith(prefix):
            return f"forbidden_prefix:{prefix.rstrip('/')}"
    if "raw_api" in normalized.casefold() or "raw_response" in normalized.casefold():
        return "raw_api_or_response_marker"
    return None


def audit_untracked_leftovers(
    *,
    root: str | Path = ".",
    output_dir: str | Path | None = DEFAULT_OUTPUT_DIR,
    untracked_paths: Sequence[str] | None = None,
) -> dict[str, Any]:
    repo_root = Path(root)
    untracked = list(untracked_paths) if untracked_paths is not None else _git_lines(repo_root, ["ls-files", "--others", "--exclude-standard"])
    staged = set(_git_lines(repo_root, ["diff", "--cached", "--name-only"]))
    audited: list[dict[str, Any]] = []
    for path in sorted(untracked):
        normalized = path.replace("\\", "/")
        if not any(marker in normalized.casefold() for marker in LEFTOVER_MARKERS):
            continue
        resolved = repo_root / normalized
        size = resolved.stat().st_size if resolved.exists() and resolved.is_file() else 0
        audited.append(
            {
                "category": _leftover_category(normalized),
                "forbidden_stage_reason": _forbidden_stage_reason(normalized),
                "gamma_staging_action": "left_unstaged",
                "path": normalized,
                "size_bytes": size,
                "staged": normalized in staged,
                "status": "untracked",
            }
        )
    staged_violations = [item["path"] for item in audited if item["staged"]]
    category_counts = Counter(item["category"] for item in audited)
    report = {
        "audited_leftover_count": len(audited),
        "category_counts": dict(sorted(category_counts.items())),
        "claim_status": CLAIM_STATUS,
        "leftovers": audited,
        "schema_version": "gamma_leftover_audit_report_v1",
        "staged_leftover_count": len(staged_violations),
        "staged_leftover_paths": staged_violations,
        "status": "pass_leftovers_unstaged" if not staged_violations else "stage_violation_detected",
        "total_untracked_leftover_count": len(audited),
    }
    if output_dir is not None:
        write_json(Path(output_dir) / "leftover_audit_report.json", report)
    return report


def build_task_family_readiness(
    *,
    root: str | Path = ".",
    hotpotqa_candidate_pools_path: str | Path = DEFAULT_HOTPOTQA_CANDIDATE_POOLS_PATH,
    project_native_packets_path: str | Path = DEFAULT_PROJECT_NATIVE_PACKETS_PATH,
    project_native_comparison_path: str | Path = DEFAULT_PROJECT_NATIVE_COMPARISON_PATH,
) -> dict[str, Any]:
    repo_root = Path(root)
    hotpotqa_path = repo_root / hotpotqa_candidate_pools_path
    project_packets_path = repo_root / project_native_packets_path
    project_comparison_path = repo_root / project_native_comparison_path
    benchmark_names = {
        path.name.casefold()
        for path in (repo_root / "artifacts" / "benchmarks").glob("*")
        if path.is_file()
    }
    project_native_available = project_packets_path.exists() and project_comparison_path.exists()
    safe_families = []
    if hotpotqa_path.exists():
        safe_families.append("HotpotQA")
    if project_native_available:
        safe_families.extend(
            [
                "multi_hop_evidence_assembly",
                "paper_revision_microtask",
                "repo_change_review_microtask",
            ]
        )
    report = {
        "checked_task_families": {
            "2WikiMultiHopQA": {
                "candidate_pool_available": any("2wiki" in name or "twowiki" in name for name in benchmark_names),
                "status": "not_available_without_raw_external_mirror",
            },
            "FEVER": {
                "candidate_pool_available": False,
                "status": "disabled_by_gamma_goal",
            },
            "HotpotQA": {
                "candidate_pool_available": hotpotqa_path.exists(),
                "candidate_pools_path": _path_ref(hotpotqa_candidate_pools_path),
                "status": "available_operational_only" if hotpotqa_path.exists() else "missing",
            },
            "MuSiQue": {
                "candidate_pool_available": any("musique" in name for name in benchmark_names),
                "status": "not_available_without_raw_external_mirror",
            },
            "project_native": {
                "comparison_path": _path_ref(project_native_comparison_path),
                "packets_path": _path_ref(project_native_packets_path),
                "status": "available_fixture_operational_only" if project_native_available else "missing",
            },
        },
        "claim_status": CLAIM_STATUS,
        "fever_disabled": True,
        "raw_external_mirrors_created": False,
        "safe_task_families": safe_families,
        "schema_version": "gamma_task_family_readiness_v1",
        "status": "ready_for_non_fever_operational_comparison" if safe_families else "blocked_no_safe_task_families",
    }
    return report


def project_native_packets_to_candidate_pools(
    rows: Sequence[Mapping[str, Any]],
    *,
    budgets: Sequence[int] = PROJECT_NATIVE_BUDGETS,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: str(item.get("task_id") or "")):
        task_id = str(row.get("task_id") or "")
        task_family = str(row.get("task_family") or "project_native_task")
        expected = {str(item) for item in row.get("expected_critical_findings") or []}
        packets = []
        for index, finding in enumerate(row.get("candidate_findings") or []):
            finding_id = str(finding.get("finding_id") or "")
            label = "gold_supporting" if finding_id in expected else "same_context_distractor"
            packets.append(
                make_evidence_packet(
                    dataset=PROJECT_NATIVE_DATASET,
                    split=PROJECT_NATIVE_SPLIT,
                    instance_id=task_id,
                    content=str(finding.get("text") or ""),
                    gold_support_label=label,
                    source_doc_id=str(finding.get("evidence_type") or task_family),
                    span={"end": index + 1, "start": index, "unit": "finding"},
                    source_packet_key=finding_id,
                    token_cost=int(finding.get("token_cost") or 0),
                    retrieval_features={
                        "heuristic_score": float(finding.get("heuristic_score") or 0.0),
                        "provenance_strength": str(finding.get("provenance_strength") or ""),
                    },
                    provenance_extra={
                        "data_source_kind": "fixture",
                        "label_source": "existing_project_native_fixture",
                        "live_api_used": False,
                        "paper_evidence_eligible": False,
                        "task_family": task_family,
                    },
                )
            )
        candidate_pool = make_candidate_pool(
            dataset=PROJECT_NATIVE_DATASET,
            split=PROJECT_NATIVE_SPLIT,
            instance_id=task_id,
            packets=packets,
            budgets=budgets,
        )
        records.append(
            {
                "adapter_metadata": {
                    "adapter_name": "gamma_project_native_fixture_adapter",
                    "claim_boundary": "fixture_operational_only_no_claim_upgrade",
                    "data_source_kind": "fixture",
                    "raw_external_mirror_created": False,
                },
                "candidate_pool": candidate_pool.to_payload(),
                "dataset": PROJECT_NATIVE_DATASET,
                "instance_id": task_id,
                "query": str(row.get("task_prompt") or ""),
                "schema_version": "benchmark_instance_v1",
                "split": PROJECT_NATIVE_SPLIT,
                "target": {
                    "expected_critical_findings": sorted(expected),
                    "label": " ".join(sorted(expected)),
                    "target_type": "answer_string",
                },
                "task_family": task_family,
            }
        )
    return records


def write_project_native_candidate_pools(
    *,
    packets_path: str | Path,
    output_path: str | Path,
    budgets: Sequence[int] = PROJECT_NATIVE_BUDGETS,
) -> dict[str, Any]:
    rows = read_jsonl(packets_path)
    records = project_native_packets_to_candidate_pools(rows, budgets=budgets)
    write_jsonl(output_path, records)
    return {
        "budgets": [int(budget) for budget in budgets],
        "candidate_pool_count": len(records),
        "candidate_pools_path": _path_ref(output_path),
        "claim_status": CLAIM_STATUS,
        "data_source_kind": "fixture",
        "paper_evidence_eligible": False,
        "raw_external_mirror_created": False,
        "schema_version": "gamma_project_native_candidate_pool_report_v1",
        "source_packets_path": _path_ref(packets_path),
        "task_families": sorted({str(record.get("task_family") or "") for record in records}),
    }


def _load_workbench_traces(output_dir: Path) -> list[dict[str, Any]]:
    traces_path = output_dir / "workbench_traces.jsonl"
    return read_jsonl(traces_path) if traces_path.exists() else []


def _postprocess_gamma_workbench_claim_boundaries(output_dir: str | Path) -> None:
    out = Path(output_dir)
    claim_ledger_path = out / "claim_ledger.json"
    if claim_ledger_path.exists():
        ledger = _read_json(claim_ledger_path)
        prior_claims = [str(item) for item in ledger.get("accepted_claims") or []]
        ledger["accepted_claims"] = []
        ledger["claim_status"] = CLAIM_STATUS
        ledger["claim_upgrade_attempted"] = False
        ledger["gamma_operational_observations_shadow_only"] = prior_claims
        ledger["measurement_validation_claim"] = False
        ledger["selector_superiority_claimed"] = False
        write_json(claim_ledger_path, ledger)

    gate_path = out / "superiority_claim_gate.json"
    if gate_path.exists():
        gate = _read_json(gate_path)
        if "scoped_operational_improvement" in gate:
            gate["scoped_operational_improvement_shadow_only"] = bool(gate["scoped_operational_improvement"])
        gate["claim_status"] = CLAIM_STATUS
        gate["global_selector_superiority"] = False
        gate["selector_superiority_claimed"] = False
        write_json(gate_path, gate)


def _trace_metric(trace: Mapping[str, Any], field: str) -> float:
    evaluation = trace.get("evaluation") or {}
    return float(evaluation.get(field, 0.0) or 0.0)


def build_diagnostic_effect_audit(traces: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, int, str], list[Mapping[str, Any]]] = defaultdict(list)
    for trace in traces:
        groups[
            (
                str(trace.get("dataset") or ""),
                int(trace.get("budget") or 0),
                str(trace.get("selector_name") or ""),
            )
        ].append(trace)

    rows: list[dict[str, Any]] = []
    for (dataset, budget, selector), group in sorted(groups.items()):
        recalls = [_trace_metric(trace, "supporting_fact_recall_at_budget") for trace in group]
        tokens = [_trace_metric(trace, "selected_tokens") for trace in group]
        gold_counts = [_trace_metric(trace, "gold_support_packets_selected_count") for trace in group]
        within = [
            1.0
            if bool((trace.get("budget_witness") or {}).get("within_budget"))
            else 0.0
            for trace in group
        ]
        greedy_supported = [trace for trace in group if trace.get("selector_regime_label") == "greedy_supported"]
        false_greedy = [
            trace
            for trace in greedy_supported
            if _trace_metric(trace, "supporting_fact_recall_at_budget") < 1.0
        ]
        mean_tokens = _mean(tokens)
        mean_recall = _mean(recalls)
        rows.append(
            {
                "ambiguity_rate": _round(
                    sum(1 for trace in group if trace.get("selector_regime_label") == "ambiguous") / len(group)
                ),
                "budget": budget,
                "budget_compliance_rate": _mean(within),
                "dataset": dataset,
                "false_greedy_supported_risk_rate": _round(len(false_greedy) / len(greedy_supported))
                if greedy_supported
                else 0.0,
                "mean_gold_support_packets_selected": _mean(gold_counts),
                "mean_selected_tokens": mean_tokens,
                "mean_supporting_fact_recall_at_budget": mean_recall,
                "quality_per_1k_tokens": _round(mean_recall / (mean_tokens / 1000.0)) if mean_tokens else 0.0,
                "selector_name": selector,
                "trace_count": len(group),
            }
        )
    all_within = [
        1.0 if bool((trace.get("budget_witness") or {}).get("within_budget")) else 0.0
        for trace in traces
    ]
    all_greedy = [trace for trace in traces if trace.get("selector_regime_label") == "greedy_supported"]
    all_false_greedy = [
        trace for trace in all_greedy if _trace_metric(trace, "supporting_fact_recall_at_budget") < 1.0
    ]
    return {
        "claim_status": CLAIM_STATUS,
        "denied_claims": list(DENIED_CLAIMS),
        "effect_rows": rows,
        "global_selector_superiority_claimed": False,
        "metric_bridge_support": False,
        "overall": {
            "ambiguity_rate": _round(
                sum(1 for trace in traces if trace.get("selector_regime_label") == "ambiguous") / len(traces)
            )
            if traces
            else 0.0,
            "budget_compliance_rate": _mean(all_within),
            "false_greedy_supported_risk_rate": _round(len(all_false_greedy) / len(all_greedy))
            if all_greedy
            else 0.0,
            "trace_count": len(traces),
        },
        "schema_version": "gamma_diagnostic_effect_audit_v1",
        "selector_superiority_claimed": False,
        "status": "completed_operational_effect_audit" if traces else "blocked_no_traces",
    }


def _write_effect_audit_csv(path: str | Path, effect_audit: Mapping[str, Any]) -> Path:
    return _write_csv(
        path,
        [dict(row) for row in effect_audit.get("effect_rows") or []],
        (
            "dataset",
            "budget",
            "selector_name",
            "trace_count",
            "mean_selected_tokens",
            "mean_supporting_fact_recall_at_budget",
            "mean_gold_support_packets_selected",
            "quality_per_1k_tokens",
            "false_greedy_supported_risk_rate",
            "ambiguity_rate",
            "budget_compliance_rate",
        ),
    )


def _workbench_spec(
    *,
    budgets: Sequence[int],
    candidate_pools_path: str | Path,
    dataset: str,
    limit: int,
    output_dir: str | Path,
    run_id: str,
) -> WorkbenchRunSpec:
    return WorkbenchRunSpec(
        budgets=tuple(int(budget) for budget in budgets),
        candidate_pools_path=_workbench_path(candidate_pools_path),
        claim_status=CLAIM_STATUS,
        dataset=dataset,
        evaluators=WORKBENCH_EVALUATORS,
        limit=int(limit),
        output_dir=_workbench_path(output_dir),
        run_id=run_id,
        selectors=WORKBENCH_SELECTORS,
    )


def _render_final_report(
    *,
    effect_audit: Mapping[str, Any],
    final_status: Mapping[str, Any],
    leftover_audit: Mapping[str, Any],
    readiness: Mapping[str, Any],
    run_results: Sequence[Mapping[str, Any]],
) -> str:
    run_lines = "\n".join(
        "- `{run_id}`: `{status}`, traces `{traces}`.".format(
            run_id=result.get("run_id"),
            status=result.get("status"),
            traces=result.get("traces_generated", 0),
        )
        for result in run_results
    )
    family_lines = "\n".join(f"- `{family}`" for family in readiness.get("safe_task_families", []))
    denied_lines = "\n".join(f"- `{claim}`" for claim in DENIED_CLAIMS)
    overall = effect_audit.get("overall") or {}
    return (
        "# Gamma Operational Expansion Final Report\n\n"
        f"Terminal status: `{final_status['terminal_status']}`\n"
        f"Claim status: `{CLAIM_STATUS}`\n\n"
        "## Gamma-0 Branch Hygiene And Leftover Audit\n\n"
        f"- Leftover audit status: `{leftover_audit['status']}`.\n"
        f"- Audited untracked Beta/Route4D/Route6C files: `{leftover_audit['audited_leftover_count']}`.\n"
        f"- Staged leftovers: `{leftover_audit['staged_leftover_count']}`.\n\n"
        "## Gamma-1 Non-FEVER Readiness\n\n"
        "- FEVER status: `disabled_by_gamma_goal`.\n"
        "- Safe task families:\n"
        f"{family_lines}\n\n"
        "MuSiQue and 2WikiMultiHopQA were not used because no local candidate-pool mirrors were available "
        "without adding raw external mirrors or oversized artifacts.\n\n"
        "## Gamma-2 Lightweight Surfaces\n\n"
        "- HotpotQA used the existing candidate-pool artifact.\n"
        "- Project-native candidate pools were derived from existing fixture realistic-task packets.\n"
        "- No benchmark labels, raw dataset mirrors, or raw API responses were created.\n\n"
        "## Gamma-3 Workbench Runs\n\n"
        f"{run_lines}\n\n"
        "All workbench runs used shadow claim mode and deployable selectors under matched budgets and identical "
        "candidate pools. No oracle upper bound was used as a deployable baseline.\n\n"
        "## Gamma-4 Diagnostic Effect Audit\n\n"
        f"- Traces audited: `{overall.get('trace_count', 0)}`.\n"
        f"- Budget compliance rate: `{overall.get('budget_compliance_rate', 0.0)}`.\n"
        f"- Ambiguity rate: `{overall.get('ambiguity_rate', 0.0)}`.\n"
        f"- False greedy-supported risk rate: `{overall.get('false_greedy_supported_risk_rate', 0.0)}`.\n"
        "- Per-selector rows include selected tokens, quality per 1k tokens, recall/evidence metrics, "
        "ambiguity rate, and budget compliance.\n\n"
        "## Gamma-5 Claim Boundary\n\n"
        "- No Route 4F or Route 4G bridge retry was performed.\n"
        "- No manuscript claim file was edited.\n"
        "- No claim-ledger upgrade was performed.\n"
        "- Denied claims remain:\n"
        f"{denied_lines}\n"
    )


def run_gamma_operational_expansion(
    *,
    root: str | Path = ".",
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    docs_path: str | Path = DEFAULT_DOCS_PATH,
    hotpotqa_candidate_pools_path: str | Path = DEFAULT_HOTPOTQA_CANDIDATE_POOLS_PATH,
    project_native_packets_path: str | Path = DEFAULT_PROJECT_NATIVE_PACKETS_PATH,
    project_native_comparison_path: str | Path = DEFAULT_PROJECT_NATIVE_COMPARISON_PATH,
    hotpotqa_limit: int = 5,
    untracked_paths: Sequence[str] | None = None,
) -> dict[str, Any]:
    repo_root = Path(root)
    output = Path(output_dir)
    docs = Path(docs_path)
    output.mkdir(parents=True, exist_ok=True)

    leftover_audit = audit_untracked_leftovers(root=repo_root, output_dir=output, untracked_paths=untracked_paths)
    readiness = build_task_family_readiness(
        root=repo_root,
        hotpotqa_candidate_pools_path=hotpotqa_candidate_pools_path,
        project_native_packets_path=project_native_packets_path,
        project_native_comparison_path=project_native_comparison_path,
    )
    write_json(output / "task_family_readiness.json", readiness)

    project_native_report: dict[str, Any] = {
        "candidate_pool_count": 0,
        "schema_version": "gamma_project_native_candidate_pool_report_v1",
        "status": "not_available",
    }
    project_native_candidate_pools_path = output / "project_native_candidate_pools.jsonl"
    if readiness["checked_task_families"]["project_native"]["status"] == "available_fixture_operational_only":
        project_native_report = write_project_native_candidate_pools(
            packets_path=project_native_packets_path,
            output_path=project_native_candidate_pools_path,
            budgets=PROJECT_NATIVE_BUDGETS,
        )
    write_json(output / "project_native_candidate_pool_report.json", project_native_report)

    run_results: list[dict[str, Any]] = []
    trace_dirs: list[Path] = []
    specs: list[WorkbenchRunSpec] = []
    if readiness["checked_task_families"]["HotpotQA"]["status"] == "available_operational_only":
        specs.append(
            _workbench_spec(
                budgets=HOTPOTQA_BUDGETS,
                candidate_pools_path=hotpotqa_candidate_pools_path,
                dataset="HotpotQA",
                limit=hotpotqa_limit,
                output_dir=output / "workbench_hotpotqa",
                run_id="gamma_hotpotqa_non_fever_operational",
            )
        )
    if int(project_native_report.get("candidate_pool_count") or 0) > 0:
        specs.append(
            _workbench_spec(
                budgets=PROJECT_NATIVE_BUDGETS,
                candidate_pools_path=project_native_candidate_pools_path,
                dataset=PROJECT_NATIVE_DATASET,
                limit=int(project_native_report["candidate_pool_count"]),
                output_dir=output / "workbench_project_native",
                run_id="gamma_project_native_fixture_operational",
            )
        )

    for spec in specs:
        write_json(output / f"{spec.run_id}_workbench_config.json", spec.to_payload())
        result = run_workbench(spec)
        _postprocess_gamma_workbench_claim_boundaries(spec.output_dir)
        run_results.append(dict(result))
        trace_dirs.append(Path(spec.output_dir))

    traces: list[dict[str, Any]] = []
    for trace_dir in trace_dirs:
        traces.extend(_load_workbench_traces(trace_dir))
    effect_audit = build_diagnostic_effect_audit(traces)
    write_json(output / "diagnostic_effect_audit.json", effect_audit)
    _write_effect_audit_csv(output / "gamma_operational_comparison_summary.csv", effect_audit)

    hotpotqa_completed = any(result.get("run_id") == "gamma_hotpotqa_non_fever_operational" for result in run_results)
    project_native_completed = any(result.get("run_id") == "gamma_project_native_fixture_operational" for result in run_results)
    if hotpotqa_completed and project_native_completed:
        terminal_status = "GAMMA_OPERATIONAL_COMPARISON_COMPLETED"
    elif hotpotqa_completed:
        terminal_status = "GAMMA_SCOPED_HOTPOTQA_ONLY_COMPLETED"
    else:
        terminal_status = "GAMMA_BLOCKED_INSUFFICIENT_NON_FEVER_TASKS"

    final_status = {
        "bridge_retry_performed": False,
        "calibrated_proxy_supported": False,
        "claim_ledger_upgrade_attempted": False,
        "claim_status": CLAIM_STATUS,
        "denied_claims": list(DENIED_CLAIMS),
        "fever_disabled": True,
        "global_selector_superiority_claimed": False,
        "live_api_used": False,
        "manuscript_claim_files_edited": False,
        "measurement_validation": False,
        "metric_bridge_support": False,
        "oracle_used_as_deployable_baseline": False,
        "project_native_fixture_only": project_native_completed,
        "raw_api_responses_stored": False,
        "raw_dataset_mirrors_created": False,
        "run_ids": [str(result.get("run_id") or "") for result in run_results],
        "schema_version": "gamma_final_status_v1",
        "selector_superiority_claimed": False,
        "terminal_status": terminal_status,
        "traces_compared": len(traces),
        "vinfo_proxy_supported": False,
    }
    write_json(output / "final_status.json", final_status)
    docs.parent.mkdir(parents=True, exist_ok=True)
    docs.write_text(
        _render_final_report(
            effect_audit=effect_audit,
            final_status=final_status,
            leftover_audit=leftover_audit,
            readiness=readiness,
            run_results=run_results,
        ),
        encoding="utf-8",
    )
    return final_status


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Gamma operational expansion.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--docs-path", default=str(DEFAULT_DOCS_PATH))
    parser.add_argument("--hotpotqa-limit", type=int, default=5)
    args = parser.parse_args(argv)
    result = run_gamma_operational_expansion(
        root=args.root,
        output_dir=args.output_dir,
        docs_path=args.docs_path,
        hotpotqa_limit=args.hotpotqa_limit,
    )
    print(
        json.dumps(
            {
                "claim_status": result["claim_status"],
                "terminal_status": result["terminal_status"],
                "traces_compared": result["traces_compared"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["terminal_status"] != "HONESTLY_BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
