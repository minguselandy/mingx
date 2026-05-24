from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cps.benchmarks.candidate_pool_manifest import build_candidate_pool_manifest
from cps.benchmarks.common import read_jsonl
from cps.benchmarks.common import write_json
from cps.benchmarks.common import write_jsonl
from cps.experiments.artifacts import stable_hash
from cps.experiments.p66_hotpotqa_operational_comparison import BASELINE_SELECTORS
from cps.experiments.p66_hotpotqa_operational_comparison import ORACLE_SELECTOR
from cps.experiments.p66_hotpotqa_operational_comparison import V12_SELECTOR
from cps.experiments.p66_hotpotqa_operational_comparison import compare_hotpotqa_operational_traces


APPROVAL_TOKEN = "APPROVE_POST_6_OPERATIONAL_REPLAY_EXPANSION=true"
CONFIG_PATH = Path("configs/post_lapi/operational_replay_expansion_config.yaml")
SOURCE_CONFIG_PATH = Path("configs/experiments/hotpotqa_operational_replay_v1.yaml")
TRACES_PATH = Path("artifacts/operator_inputs/p56_realistic_dispatch_traces.jsonl")
P56_REPORT_PATH = Path("artifacts/benchmarks/p56_hotpotqa_trace_generation_report.json")
CANDIDATE_POOLS_PATH = Path("artifacts/benchmarks/hotpotqa_candidate_pools.jsonl")
OUTPUT_DIR = Path("artifacts/experiments/post_lapi_operational_replay")
DOC_PATH = Path("docs/experiments/POST-LAPI-operational-replay-expansion.md")
TABLE_PATH = Path("docs/paper/post-lapi-operational-replay-table.md")
RUN_ID = "post_lapi_operational_replay_expansion_offline_v1"

CLAIM_LEVEL = "operational_utility_only/no_claim_upgrade"
DIAGNOSTIC_CLAIM_LEVEL = "scoped_operational_improvement_under_matched_budgets_only"
ALLOWED_CLAIMS = [
    "scoped_operational_improvement_under_matched_budgets",
    "operational_utility_only",
]
DENIED_CLAIMS = [
    "selector_superiority",
    "global_selector_superiority",
    "metric_bridge_support",
    "measurement_validation",
    "V_information_verification",
    "calibrated_proxy_supported",
    "vinfo_proxy_supported",
    "paper_evidence",
    "route_5_unlock",
    "route_8_unlock",
]
FIXED_DOWNSTREAM_CONDITIONS = [
    "candidate_pool_hash",
    "budget",
    "downstream_prompt_hash",
    "model_snapshot",
    "endpoint",
    "thinking_mode",
    "decoding_policy",
    "token_budget_accounting",
]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return payload


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.name if candidate.is_absolute() else candidate.as_posix()


def _selector_deployability(trace: Mapping[str, Any]) -> str:
    if trace.get("selector_name") == ORACLE_SELECTOR:
        return "non_deployable_upper_bound"
    plan = trace.get("projection_plan") or {}
    return str(plan.get("selector_deployability") or "deployable_operational_baseline")


def _trace_to_record(trace: Mapping[str, Any]) -> dict[str, Any]:
    evaluation = trace.get("evaluation") or {}
    selected_tokens = int(evaluation.get("selected_tokens") or 0)
    recall = float(evaluation.get("supporting_fact_recall_at_budget") or 0.0)
    selector = str(trace.get("selector_name") or "")
    deployability = _selector_deployability(trace)
    return {
        "abstain_rate": 0.0,
        "budget": int(trace.get("budget_B_i") or 0),
        "candidate_pool_hash": str(trace.get("candidate_pool_hash") or ""),
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "dataset": "HotpotQA_continuation",
        "decoding_policy_hash": stable_hash({"mode": "offline_selector_replay", "temperature": None}),
        "deployable_status": deployability,
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "downstream_prompt_hash": "offline_replay_existing_trace_no_prompt_body",
        "endpoint": "offline_existing_replay_artifact",
        "evidence_recall": recall,
        "fixed_downstream_conditions": FIXED_DOWNSTREAM_CONDITIONS,
        "input_tokens": selected_tokens,
        "latency_ms": 0,
        "live_api_call_performed": False,
        "matched_budget": bool((trace.get("budget_witness") or {}).get("within_budget") is True),
        "measurement_validation_claim": False,
        "metric_bridge_support": False,
        "model_snapshot": "offline_existing_replay_artifact_no_model",
        "non_deployable_upper_bound": selector == ORACLE_SELECTOR,
        "output_tokens": 0,
        "paper_evidence_claim": False,
        "parse_success": True,
        "quality_per_1k_tokens": round(recall / (selected_tokens / 1000.0), 6) if selected_tokens > 0 else 0.0,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "schema_version": "post_lapi_operational_replay_record_v1",
        "scoped_operational_comparison_evidence_only": True,
        "selected_gold_support_packets_count": int(evaluation.get("gold_support_packets_selected_count") or 0),
        "selected_packet_hashes": [
            hashlib.sha256(str(packet_id).encode("utf-8")).hexdigest()
            for packet_id in list(trace.get("selected_packet_ids") or [])
        ],
        "selected_tokens": selected_tokens,
        "selector_name": selector,
        "selector_superiority_claimed": False,
        "source_trace_hash": stable_hash(
            {
                "budget": trace.get("budget_B_i"),
                "candidate_pool_hash": trace.get("candidate_pool_hash"),
                "selected_packet_ids": list(trace.get("selected_packet_ids") or []),
                "selector_name": selector,
            }
        ),
        "supporting_fact_recall": recall,
        "thinking_mode": "not_applicable_offline_replay",
        "total_tokens": selected_tokens,
        "vinfo_proxy_supported": False,
        "calibrated_proxy_supported": False,
        "within_budget": bool(evaluation.get("within_budget") is True),
    }


def _summary_rows(comparison_summary: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in comparison_summary:
        selector = str(row["selector_name"])
        rows.append(
            {
                "abstain_rate": 0.0,
                "budget": int(row["budget"]),
                "claim_boundary": CLAIM_LEVEL
                if selector != ORACLE_SELECTOR
                else "non_deployable_upper_bound",
                "claim_gate_distribution": "operational_utility_only/no_claim_upgrade",
                "cost": 0.0,
                "dataset": "HotpotQA_continuation",
                "deployable_status": "non_deployable_upper_bound"
                if selector == ORACLE_SELECTOR
                else str(row["selector_deployability"]),
                "evidence_recall": float(row["mean_supporting_fact_recall"]),
                "latency": 0.0,
                "parse_success_rate": 1.0,
                "quality_per_1k_tokens": float(row["quality_per_1k_tokens"]),
                "selected_tokens": float(row["mean_selected_tokens"]),
                "selector_name": selector,
                "slice": "existing_p56_hotpotqa_operational_traces",
                "supporting_fact_recall": float(row["mean_supporting_fact_recall"]),
                "trace_count": int(row["trace_count"]),
            }
        )
    return rows


def _write_summary_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fieldnames = [
        "dataset",
        "slice",
        "budget",
        "selector_name",
        "deployable_status",
        "supporting_fact_recall",
        "evidence_recall",
        "selected_tokens",
        "quality_per_1k_tokens",
        "latency",
        "cost",
        "parse_success_rate",
        "claim_gate_distribution",
        "abstain_rate",
        "claim_boundary",
        "trace_count",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fieldnames})


def _cost_latency_ledger(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ledger_rows = []
    for row in rows:
        total_tokens = int(round(float(row["selected_tokens"]) * int(row["trace_count"])))
        ledger_rows.append(
            {
                "budget": int(row["budget"]),
                "cost_basis": "offline_selected_token_proxy_not_provider_billing",
                "estimated_cost": 0.0,
                "input_tokens": total_tokens,
                "latency_ms": 0,
                "output_tokens": 0,
                "selector_name": str(row["selector_name"]),
                "total_tokens": total_tokens,
            }
        )
    return {
        "ledger": ledger_rows,
        "schema_version": "post_lapi_operational_replay_cost_latency_ledger_v1",
    }


def _aggregate(
    *,
    comparison: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    summary_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    budgets = sorted({int(record["budget"]) for record in records})
    selectors = sorted({str(record["selector_name"]) for record in records})
    return {
        "allowed_claims_after_gate": ALLOWED_CLAIMS,
        "budgets": budgets,
        "calibrated_proxy_supported": False,
        "candidate_pool_count": len({record["candidate_pool_hash"] for record in records}),
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "comparison_summary_rows": len(summary_rows),
        "dataset": "HotpotQA_continuation",
        "denied_claims": DENIED_CLAIMS,
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "final_gate_status": "post6_operational_replay_completed",
        "global_selector_superiority_claimed": False,
        "live_api_call_count": 0,
        "matched_budget_conditions_documented": True,
        "measurement_validation_claim": False,
        "metric_bridge_support": False,
        "oracle_status": "non_deployable_upper_bound",
        "oracle_used_as_deployable_baseline": False,
        "paper_evidence_claim": False,
        "paired_comparison_count": len((comparison.get("statistical_tests") or {}).get("v12_vs_baselines") or {}),
        "raw_response_stored": False,
        "record_count": len(records),
        "route_5_locked": True,
        "route_8_locked": True,
        "schema_version": "post_lapi_operational_replay_aggregate_v1",
        "scoped_operational_comparison_evidence_only": True,
        "selector_counts": dict(sorted(Counter(record["selector_name"] for record in records).items())),
        "selector_superiority_claimed": False,
        "selectors": selectors,
        "trace_count": len(records),
        "vinfo_proxy_supported": False,
    }


def _write_docs(
    *,
    aggregate: Mapping[str, Any],
    doc_path: Path,
    output_dir: Path,
    summary_rows: Sequence[Mapping[str, Any]],
    table_path: Path,
) -> None:
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(
        "\n".join(
            [
                "# POST-LAPI Operational Replay Expansion",
                "",
                "Goal ID: POST-6-RUN / Matched-budget operational replay expansion",
                f"Claim ceiling: `{CLAIM_LEVEL}`",
                "",
                "## Scope",
                "",
                "This owner-approved POST-6 run packages existing offline HotpotQA matched-budget operational replay traces into POST-LAPI scoped operational comparison artifacts. It does not run live API calls and does not store raw API responses.",
                "",
                "## Run Metadata",
                "",
                f"- Live API calls run: `{aggregate['live_api_call_count']}`",
                f"- Replay records: `{aggregate['record_count']}`",
                f"- Candidate pools: `{aggregate['candidate_pool_count']}`",
                f"- Budgets: `{aggregate['budgets']}`",
                f"- Raw API responses stored: `{str(aggregate['raw_response_stored']).lower()}`",
                f"- Route 5 locked: `{str(aggregate['route_5_locked']).lower()}`",
                f"- Route 8 locked: `{str(aggregate['route_8_locked']).lower()}`",
                f"- Claim upgrade introduced: `{str(aggregate['claim_upgrade_introduced']).lower()}`",
                f"- Gate status: `{aggregate['final_gate_status']}`",
                "",
                "## Matched-Budget Conditions",
                "",
                "Rows are comparable only within the same candidate-pool hash and fixed budget. The package records fixed downstream placeholders for offline replay: prompt hash, model snapshot, endpoint, thinking mode, decoding policy, and token-budget accounting are held constant as offline replay conditions.",
                "",
                "## Oracle Treatment",
                "",
                "`gold_support_oracle_upper_bound` is retained only as `non_deployable_upper_bound` and is not used as a deployable baseline.",
                "",
                "## Claim Boundary",
                "",
                "Allowed interpretation is scoped operational improvement evidence under matched budgets and `operational_utility_only`. Denied interpretations include selector superiority, global selector superiority, metric bridge support, measurement validation, calibrated proxy support, vinfo proxy support, paper evidence, Route 5 unlock, and Route 8 unlock.",
                "",
                "## Artifact Index",
                "",
                f"- `{(output_dir / 'replay_records.jsonl').as_posix()}`",
                f"- `{(output_dir / 'comparison_summary.csv').as_posix()}`",
                f"- `{(output_dir / 'paired_comparisons.json').as_posix()}`",
                f"- `{(output_dir / 'candidate_pool_manifest.json').as_posix()}`",
                f"- `{(output_dir / 'run_manifest.json').as_posix()}`",
                f"- `{(output_dir / 'claim_ledger.json').as_posix()}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# POST-LAPI Operational Replay Table",
        "",
        f"Status: POST-6-RUN result under `{CLAIM_LEVEL}`",
        "",
        "These rows are scoped operational comparison evidence only. They do not claim selector superiority, global selector superiority, metric bridge support, measurement validation, V-information verification, paper evidence, Route 5 unlock, or Route 8 unlock.",
        "",
        "| dataset | slice | budget | baseline | deployable status | supporting fact recall | evidence recall | selected tokens | quality per 1k tokens | latency | cost | parse success rate | claim gate distribution | abstain rate | claim boundary |",
        "|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    for row in summary_rows:
        lines.append(
            "| {dataset} | {slice} | {budget} | {selector_name} | {deployable_status} | {supporting_fact_recall} | {evidence_recall} | {selected_tokens} | {quality_per_1k_tokens} | {latency} | {cost} | {parse_success_rate} | {claim_gate_distribution} | {abstain_rate} | `{claim_boundary}` |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Boundary Fields",
            "",
            "| Field | Value |",
            "| --- | --- |",
            "| live API calls run | `0` |",
            "| raw API responses stored | `false` |",
            f"| claim level | `{CLAIM_LEVEL}` |",
            f"| diagnostic claim level | `{DIAGNOSTIC_CLAIM_LEVEL}` |",
            "| oracle treatment | `non_deployable_upper_bound` |",
            "| Route 5 locked | `true` |",
            "| Route 8 locked | `true` |",
            "| claim upgrade introduced | `false` |",
        ]
    )
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_blocker(output_dir: Path, *, reason: str) -> dict[str, Any]:
    report = {
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "live_api_call_count": 0,
        "raw_response_stored": False,
        "reason": reason,
        "route_5_locked": True,
        "route_8_locked": True,
        "schema_version": "post_lapi_operational_replay_blocker_v1",
        "terminal_status": "BLOCKED",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "blocker_report.json", report)
    return report


def run_post6_operational_replay(
    *,
    approval: str,
    doc_path: str | Path = DOC_PATH,
    output_dir: str | Path = OUTPUT_DIR,
    repo_root: str | Path = ROOT,
    table_path: str | Path = TABLE_PATH,
) -> dict[str, Any]:
    repo = Path(repo_root)
    output = Path(output_dir)
    if approval != APPROVAL_TOKEN:
        return _write_blocker(output, reason="missing_required_owner_approval_token")

    config = _load_json(repo / CONFIG_PATH)
    if config.get("claim_level") != CLAIM_LEVEL:
        raise RuntimeError("claim_level_config_mismatch")
    if config.get("route_5_locked") is not True or config.get("route_8_locked") is not True:
        raise RuntimeError("route_lock_config_not_true")
    if config.get("raw_response_storage_allowed") is not False:
        raise RuntimeError("config_allows_raw_response_storage")
    if config.get("teacher_forced_nll_allowed") is not False:
        raise RuntimeError("teacher_forced_nll_not_allowed")

    traces = read_jsonl(repo / TRACES_PATH)
    comparison = compare_hotpotqa_operational_traces(traces)
    records = [_trace_to_record(trace) for trace in traces]
    if any(record["matched_budget"] is not True for record in records):
        return _write_blocker(output, reason="budget_mismatch_detected")

    candidate_pools = read_jsonl(repo / CANDIDATE_POOLS_PATH)
    pool_manifest = build_candidate_pool_manifest(
        candidate_pools,
        dataset="HotpotQA_continuation",
        budgets=sorted({record["budget"] for record in records}),
    )
    summary_rows = _summary_rows(comparison["comparison_summary"])
    aggregate = _aggregate(comparison=comparison, records=records, summary_rows=summary_rows)
    cost_latency = _cost_latency_ledger(summary_rows)
    claim_ledger = {
        "allowed_claims": ALLOWED_CLAIMS,
        "calibrated_proxy_supported": False,
        "claim_level": CLAIM_LEVEL,
        "claim_status": CLAIM_LEVEL,
        "claim_upgrade": False,
        "claim_upgrade_introduced": False,
        "current_claim_level": CLAIM_LEVEL,
        "denied_claims": DENIED_CLAIMS,
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "global_selector_superiority_claimed": False,
        "measurement_validation_claim": False,
        "metric_bridge_support": False,
        "paper_evidence_claim": False,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "scoped_operational_comparison_evidence_only": True,
        "selector_superiority_claimed": False,
        "vinfo_proxy_supported": False,
    }
    paired = {
        **comparison["statistical_tests"],
        "claim_boundary": CLAIM_LEVEL,
        "interpretation": "scoped_operational_comparison_only_no_selector_superiority_claim",
        "oracle_status": "non_deployable_upper_bound",
    }
    manifest = {
        "approval_gate_token_verified": True,
        "budgets": aggregate["budgets"],
        "candidate_pool_manifest_hash": stable_hash(pool_manifest),
        "claim_ledger_hash": stable_hash(claim_ledger),
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "config_hash": _sha256_file(repo / CONFIG_PATH),
        "cost_latency_ledger_hash": stable_hash(cost_latency),
        "dataset": "HotpotQA_continuation",
        "deployable_baselines": list(BASELINE_SELECTORS) + [V12_SELECTOR],
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "endpoint": "offline_existing_replay_artifact",
        "fixed_downstream_conditions": FIXED_DOWNSTREAM_CONDITIONS,
        "live_api_call_count": 0,
        "live_api_call_performed": False,
        "matched_budget_controls": dict(config["matched_budget_controls"]),
        "model_snapshot": "offline_existing_replay_artifact_no_model",
        "oracle_upper_bound": {
            "deployable": False,
            "selector_name": ORACLE_SELECTOR,
            "status": "non_deployable_upper_bound",
        },
        "output_dir": _path_ref(output),
        "p56_report_hash": _sha256_file(repo / P56_REPORT_PATH),
        "raw_response_stored": False,
        "replay_records_hash": stable_hash(records),
        "route_5_locked": True,
        "route_8_locked": True,
        "run_id": RUN_ID,
        "schema_version": "post_lapi_operational_replay_run_manifest_v1",
        "source_config_hash": _sha256_file(repo / SOURCE_CONFIG_PATH),
        "source_traces_hash": _sha256_file(repo / TRACES_PATH),
        "terminal_status": aggregate["final_gate_status"],
        "thinking_mode": "not_applicable_offline_replay",
        "token_budget_accounting": "offline_selected_token_proxy_not_provider_usage",
        "trace_count": len(records),
    }
    manifest["manifest_hash"] = stable_hash(manifest)
    claim_gate_report = {
        "allowed_claims": ALLOWED_CLAIMS,
        "calibrated_proxy_supported": False,
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "denied_claims": DENIED_CLAIMS,
        "final_gate_status": aggregate["final_gate_status"],
        "global_selector_superiority_claimed": False,
        "live_api_call_count": 0,
        "measurement_validation_claim": False,
        "metric_bridge_support": False,
        "oracle_status": "non_deployable_upper_bound",
        "paper_evidence_claim": False,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "selector_superiority_claimed": False,
        "vinfo_proxy_supported": False,
    }

    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "replay_records.jsonl", records)
    _write_summary_csv(output / "comparison_summary.csv", summary_rows)
    write_json(output / "paired_comparisons.json", paired)
    write_json(output / "candidate_pool_manifest.json", pool_manifest)
    write_json(output / "cost_latency_ledger.json", cost_latency)
    write_json(output / "aggregate_report.json", aggregate)
    write_json(output / "run_manifest.json", manifest)
    write_json(output / "claim_ledger.json", claim_ledger)
    write_json(output / "claim_gate_report.json", claim_gate_report)
    _write_docs(
        aggregate=aggregate,
        doc_path=Path(doc_path),
        output_dir=output,
        summary_rows=summary_rows,
        table_path=Path(table_path),
    )

    return {
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "final_gate_status": aggregate["final_gate_status"],
        "live_api_call_count": 0,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "terminal_status": "DONE",
        "trace_count": len(records),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run POST-6 matched-budget operational replay expansion.")
    parser.add_argument("--approval", required=True)
    parser.add_argument("--doc-path", default=str(DOC_PATH))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--table-path", default=str(TABLE_PATH))
    args = parser.parse_args(argv)
    result = run_post6_operational_replay(
        approval=str(args.approval),
        doc_path=args.doc_path,
        output_dir=args.output_dir,
        repo_root=args.repo_root,
        table_path=args.table_path,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("terminal_status") == "DONE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
