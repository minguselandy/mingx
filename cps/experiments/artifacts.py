from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from cps.store.measurement import append_event, iter_events


PROJECTION_EVENT_TYPES = {
    "candidate_pool_materialized",
    "projection_plan_materialized",
    "budget_witness_materialized",
    "materialized_context_materialized",
    "projection_diagnostics_materialized",
}


@dataclass(frozen=True)
class CandidatePool:
    dispatch_id: str
    agent_id: str
    round_id: str
    regime: str
    budget_tokens: int
    items: list[dict[str, Any]]
    candidate_pool_hash: str


@dataclass(frozen=True)
class ProjectionPlan:
    dispatch_id: str
    agent_id: str
    round_id: str
    regime: str
    algorithm: str
    budget_tokens: int
    candidate_pool_hash: str
    selected_ids: list[str]
    excluded_ids: list[str]
    trace: list[dict[str, Any]]
    score_config: dict[str, Any]


@dataclass(frozen=True)
class BudgetWitness:
    dispatch_id: str
    agent_id: str
    round_id: str
    regime: str
    budget_tokens: int
    estimated_tokens: int
    realized_tokens: int
    within_budget: bool
    selected_ids: list[str]
    excluded_ids: list[str]
    tolerance_violations: list[dict[str, Any]]


@dataclass(frozen=True)
class MaterializedContext:
    dispatch_id: str
    agent_id: str
    round_id: str
    regime: str
    selected_ids: list[str]
    section_order: list[str]
    content: str
    token_count: int
    context_hash: str


@dataclass(frozen=True)
class ProjectionDiagnostics:
    dispatch_id: str
    agent_id: str
    round_id: str
    regime: str
    gamma_hat: float
    synergy_fraction: float
    greedy_augmented_gap: float
    policy_recommendation: str
    greedy_value: float
    augmented_value: float
    local_search_value: float
    thresholds: dict[str, Any]
    notes: str


def stable_json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(stable_json_dumps(payload).encode("utf-8")).hexdigest()


def candidate_pool_hash(items: list[dict[str, Any]]) -> str:
    normalized = [
        {
            "item_id": str(item["item_id"]),
            "token_cost": int(item["token_cost"]),
            "singleton_value": float(item.get("singleton_value", 0.0)),
            "text": str(item.get("text", "")),
        }
        for item in sorted(items, key=lambda row: str(row["item_id"]))
    ]
    return stable_hash(normalized)


def context_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def to_payload(record: Any) -> dict[str, Any]:
    if hasattr(record, "__dataclass_fields__"):
        return asdict(record)
    return dict(record)


def write_json(path: str | Path, payload: Any) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def append_jsonl(path: str | Path, payload: Any) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return output_path


def write_text(path: str | Path, content: str) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def append_projection_event(
    *,
    store_dir: str | Path,
    event_type: str,
    run_id: str,
    payload: dict[str, Any],
    notes: str,
) -> dict[str, Any]:
    if event_type not in PROJECTION_EVENT_TYPES and event_type != "synthetic_benchmark_summary_materialized":
        raise ValueError(f"unsupported projection event type: {event_type}")
    return append_event(
        store_dir,
        {
            "event_type": event_type,
            "run_id": run_id,
            "question_id": None,
            "hop_depth": None,
            "provider": "synthetic",
            "backend_id": "synthetic_projection_benchmark",
            "model_id": None,
            "model_role": None,
            "ordering_id": None,
            "ordering": None,
            "paragraph_id": None,
            "full_logp": None,
            "loo_logp": None,
            "delta_loo": None,
            "baseline_logp": None,
            "manifest_hash": None,
            "sampling_seed": payload.get("seed"),
            "protocol_version": payload.get("protocol_version", "synthetic_regime.v1"),
            "request_fingerprint": None,
            "response_status": "materialized",
            "notes": notes,
            "payload": payload,
        },
    )


def rebuild_projection_summary_from_events(
    store_dir: str | Path,
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    diagnostics: list[dict[str, Any]] = []
    candidate_pools = 0
    projection_plans = 0
    budget_witnesses = 0
    materialized_contexts = 0

    for event in iter_events(store_dir):
        if run_id is not None and event.get("run_id") != run_id:
            continue
        event_type = event.get("event_type")
        if event_type == "candidate_pool_materialized":
            candidate_pools += 1
        elif event_type == "projection_plan_materialized":
            projection_plans += 1
        elif event_type == "budget_witness_materialized":
            budget_witnesses += 1
        elif event_type == "materialized_context_materialized":
            materialized_contexts += 1
        elif event_type == "projection_diagnostics_materialized":
            diagnostics.append(dict(event.get("payload") or {}))

    per_regime: dict[str, dict[str, Any]] = {}
    policy_counts: dict[str, int] = {}
    for row in diagnostics:
        regime = str(row.get("regime", "unknown"))
        policy = str(row.get("policy_recommendation", "unknown"))
        bucket = per_regime.setdefault(
            regime,
            {
                "dispatch_count": 0,
                "avg_gamma_hat": 0.0,
                "avg_synergy_fraction": 0.0,
                "avg_greedy_augmented_gap": 0.0,
                "policy_recommendations": {},
            },
        )
        bucket["dispatch_count"] += 1
        bucket["avg_gamma_hat"] += float(row.get("gamma_hat", 0.0))
        bucket["avg_synergy_fraction"] += float(row.get("synergy_fraction", 0.0))
        bucket["avg_greedy_augmented_gap"] += float(row.get("greedy_augmented_gap", 0.0))
        bucket["policy_recommendations"][policy] = bucket["policy_recommendations"].get(policy, 0) + 1
        policy_counts[policy] = policy_counts.get(policy, 0) + 1

    for bucket in per_regime.values():
        count = max(1, int(bucket["dispatch_count"]))
        bucket["avg_gamma_hat"] = round(bucket["avg_gamma_hat"] / count, 6)
        bucket["avg_synergy_fraction"] = round(bucket["avg_synergy_fraction"] / count, 6)
        bucket["avg_greedy_augmented_gap"] = round(bucket["avg_greedy_augmented_gap"] / count, 6)

    complete_artifact_sets = (
        candidate_pools == projection_plans == budget_witnesses == materialized_contexts == len(diagnostics)
    )
    return {
        "source_of_truth": "event_log",
        "run_id": run_id,
        "dispatch_count": len(diagnostics),
        "artifact_counts": {
            "candidate_pools": candidate_pools,
            "projection_plans": projection_plans,
            "budget_witnesses": budget_witnesses,
            "materialized_contexts": materialized_contexts,
            "diagnostics": len(diagnostics),
        },
        "complete_artifact_sets": complete_artifact_sets,
        "policy_counts": dict(sorted(policy_counts.items())),
        "per_regime": {key: per_regime[key] for key in sorted(per_regime)},
    }
