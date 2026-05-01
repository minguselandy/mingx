from __future__ import annotations

from pathlib import Path
from typing import Any

from cps.experiments.artifacts import (
    BudgetWitness,
    CandidatePool,
    MaterializedContext,
    MetricBridgeWitness,
    ProjectionPlan,
    candidate_pool_hash,
    context_hash,
    stable_hash,
    to_payload,
)
from cps.schema import ProjectionBundleV1
from cps.store.measurement import append_event
from cps.store.progress import MeasurementUnitSpec


PROJECTION_EVENT_SEQUENCE = (
    "candidate_pool_materialized",
    "projection_plan_materialized",
    "budget_witness_materialized",
    "materialized_context_materialized",
    "metric_bridge_witness_materialized",
    "projection_bundle_materialized",
)


def build_projection_run_id(
    *,
    experiment_id: str,
    protocol_version: str,
    manifest_hash: str,
    backend_name: str,
    scope_mode: str,
    seed: int,
    small_question_ids: list[str],
    frontier_question_ids: list[str],
    k_lcb: int,
) -> str:
    digest = stable_hash(
        {
            "experiment_id": experiment_id,
            "protocol_version": protocol_version,
            "manifest_hash": manifest_hash,
            "backend_name": backend_name,
            "scope_mode": scope_mode,
            "seed": seed,
            "small_question_ids": list(small_question_ids),
            "frontier_question_ids": list(frontier_question_ids),
            "k_lcb": k_lcb,
        }
    )
    return f"projection-{digest[:16]}"


def _token_count(text: str) -> int:
    return len(str(text).split())


def _candidate_items(question) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for paragraph in question.paragraphs:
        text = str(paragraph.text)
        items.append(
            {
                "item_id": str(paragraph.paragraph_id),
                "paragraph_id": paragraph.paragraph_id,
                "title": str(paragraph.title),
                "text": text,
                "is_supporting": bool(paragraph.is_supporting),
                "token_cost": _token_count(text),
                "singleton_value": 0.0,
            }
        )
    return items


def _materialized_content(items: list[dict[str, Any]], selected_ids: list[str]) -> str:
    lookup = {str(item["item_id"]): item for item in items}
    sections: list[str] = []
    for item_id in selected_ids:
        item = lookup[item_id]
        sections.append(f"[{item_id}] {item['title']}\n{item['text']}")
    return "\n\n".join(sections)


def _event_payload(
    *,
    event_type: str,
    cohort_run_id: str,
    context,
    backend,
    model_role: str,
    question,
    manifest_hash: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "event_type": event_type,
        "run_id": cohort_run_id,
        "question_id": question.question_id,
        "hop_depth": question.hop_depth,
        "provider": context.provider.name,
        "backend_id": backend.backend_id,
        "model_id": backend.model_id,
        "model_role": model_role,
        "ordering_id": None,
        "ordering": None,
        "paragraph_id": None,
        "full_logp": None,
        "loo_logp": None,
        "delta_loo": None,
        "baseline_logp": None,
        "manifest_hash": manifest_hash,
        "sampling_seed": context.experiment["seed"],
        "protocol_version": context.experiment["protocol_version"],
        "request_fingerprint": None,
        "response_status": "materialized",
        "notes": "projection artifact materialized",
        "payload": payload,
    }


def emit_projection_artifact_events(
    *,
    store_dir: str | Path,
    context,
    backend,
    model_role: str,
    spec: MeasurementUnitSpec,
    question,
    snapshot: dict[str, Any],
    manifest_hash: str,
    cohort_run_id: str,
    projection_run_id: str,
    scope_mode: str,
    k_lcb: int,
    source_mode: str,
) -> tuple[ProjectionBundleV1, str]:
    identity = {
        "run_id": projection_run_id,
        "dispatch_id": f"{question.question_id}:{model_role}",
        "agent_id": model_role,
        "round_id": f"{context.scoring.canonical_ordering_id}:k_lcb_{k_lcb}",
        "regime": scope_mode,
    }
    artifact_identity = {
        "dispatch_id": identity["dispatch_id"],
        "agent_id": identity["agent_id"],
        "round_id": identity["round_id"],
        "regime": identity["regime"],
    }
    items = _candidate_items(question)
    selected_ids = [str(item["item_id"]) for item in items]
    excluded_ids: list[str] = []
    pool_hash = candidate_pool_hash(items)
    realized_tokens = sum(int(item["token_cost"]) for item in items)
    content = _materialized_content(items, selected_ids)

    candidate_pool = CandidatePool(
        **artifact_identity,
        budget_tokens=realized_tokens,
        items=items,
        candidate_pool_hash=pool_hash,
    )
    candidate_pool_payload = {
        **to_payload(candidate_pool),
        "run_id": projection_run_id,
        "candidate_count": len(items),
    }
    projection_plan = ProjectionPlan(
        **artifact_identity,
        algorithm="cohort_current_context_order",
        budget_tokens=realized_tokens,
        candidate_pool_hash=pool_hash,
        selected_ids=selected_ids,
        excluded_ids=excluded_ids,
        trace=[
            {
                "action": "select_all_current_context",
                "question_id": question.question_id,
                "model_role": model_role,
                "paragraph_ids": [paragraph.paragraph_id for paragraph in question.paragraphs],
            }
        ],
        score_config={
            "utility_metric": context.scoring.utility_metric,
            "canonical_ordering_id": context.scoring.canonical_ordering_id,
            "ordering_ids": list(spec.ordering_ids),
            "k_lcb": k_lcb,
            "source": "cohort_runtime_projection_export",
        },
    )
    projection_plan_payload = {**to_payload(projection_plan), "run_id": projection_run_id}
    budget_witness = BudgetWitness(
        **artifact_identity,
        budget_tokens=realized_tokens,
        estimated_tokens=realized_tokens,
        realized_tokens=realized_tokens,
        within_budget=True,
        selected_ids=selected_ids,
        excluded_ids=excluded_ids,
        tolerance_violations=[],
    )
    budget_witness_payload = {
        **to_payload(budget_witness),
        "run_id": projection_run_id,
        "candidate_pool_hash": pool_hash,
    }
    materialized_context = MaterializedContext(
        **artifact_identity,
        selected_ids=selected_ids,
        section_order=selected_ids,
        content=content,
        token_count=realized_tokens,
        context_hash=context_hash(content),
    )
    materialized_context_payload = {
        **to_payload(materialized_context),
        "run_id": projection_run_id,
        "candidate_pool_hash": pool_hash,
    }
    metric_bridge_witness = MetricBridgeWitness(
        **artifact_identity,
        calibration_epoch=None,
        active_stratum={
            "scope_mode": scope_mode,
            "question_id": question.question_id,
            "hop_depth": question.hop_depth,
            "model_role": model_role,
        },
        model_tier=model_role,
        utility_metric=context.scoring.utility_metric,
        metric_class="operational_only",
        materialization_policy={
            "source": "cohort_runtime_projection_export",
            "claim": "non_certifying_observability_artifact",
        },
        decoding_policy={
            "backend_id": backend.backend_id,
            "model_id": backend.model_id,
            "source_mode": source_mode,
        },
        bridge_scale=None,
        bridge_residual_zeta=None,
        effective_sample_size=None,
        drift_status="not_applicable",
        diagnostic_mode="cohort_runtime_export",
        diagnostic_claim_level="operational_utility_only",
    )
    metric_bridge_payload = {
        **to_payload(metric_bridge_witness),
        "run_id": projection_run_id,
        "candidate_pool_hash": pool_hash,
        "context_hash": materialized_context.context_hash,
    }

    bundle = ProjectionBundleV1(
        run_id=projection_run_id,
        dispatch_id=identity["dispatch_id"],
        agent_id=identity["agent_id"],
        round_id=identity["round_id"],
        candidate_pool=candidate_pool_payload,
        projection_plan=projection_plan_payload,
        budget_witness=budget_witness_payload,
        materialized_context=materialized_context_payload,
        metric_bridge_witness=metric_bridge_payload,
        source_mode=source_mode,
    )
    canonical_hash = bundle.canonical_hash()
    bundle_payload = {**bundle.to_dict(), "canonical_hash": canonical_hash}

    for event_type, payload in (
        ("candidate_pool_materialized", candidate_pool_payload),
        ("projection_plan_materialized", projection_plan_payload),
        ("budget_witness_materialized", budget_witness_payload),
        ("materialized_context_materialized", materialized_context_payload),
        ("metric_bridge_witness_materialized", metric_bridge_payload),
        ("projection_bundle_materialized", bundle_payload),
    ):
        append_event(
            store_dir,
            _event_payload(
                event_type=event_type,
                cohort_run_id=cohort_run_id,
                context=context,
                backend=backend,
                model_role=model_role,
                question=question,
                manifest_hash=manifest_hash,
                payload=payload,
            ),
        )
    return bundle, canonical_hash
