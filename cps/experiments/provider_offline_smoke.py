from __future__ import annotations

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
    candidate_pool_hash,
    context_hash,
    rebuild_projection_summary_from_events,
    to_payload,
    write_json,
)
from cps.providers.graphiti_provider import graphiti_episode_to_candidate, graphiti_fact_to_candidate
from cps.providers.langextract_provider import (
    langextract_extraction_to_candidate,
    langextract_span_to_candidate,
)
from cps.providers.normalizer import normalize_candidate_pool
from cps.schema.projection_bundle_v1 import ProjectionBundleV1


CLAIM_LEVEL = "engineering_smoke_only"
RUN_ID_PREFIX = "provider-offline-smoke"
PROTOCOL_VERSION = "provider_offline_smoke.v1"
ARTIFACT_FILENAMES = {
    "provider_candidates": "provider_candidates.jsonl",
    "normalized_candidates": "normalized_candidates.jsonl",
    "candidate_pool_materialized": "candidate_pools.jsonl",
    "projection_plan_materialized": "projection_plans.jsonl",
    "budget_witness_materialized": "budget_witnesses.jsonl",
    "materialized_context_materialized": "materialized_contexts.jsonl",
    "metric_bridge_witness_materialized": "metric_bridge_witnesses.jsonl",
    "projection_diagnostics_materialized": "diagnostics.jsonl",
    "projection_bundle_materialized": "projection_bundles.jsonl",
}


def _artifact_paths(output_dir: Path) -> dict[str, Path]:
    return {key: output_dir / filename for key, filename in ARTIFACT_FILENAMES.items()}


def _reset_outputs(output_dir: Path, artifact_paths: dict[str, Path]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "events.jsonl").write_text("", encoding="utf-8")
    for path in artifact_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")


def _provider_dispatches() -> list[dict[str, Any]]:
    return [
        {
            "dispatch_id": "provider-smoke-graphiti",
            "agent_id": "provider_smoke_agent",
            "round_id": "round-graphiti",
            "provider_family": "graphiti",
            "records": [
                graphiti_fact_to_candidate(
                    {
                        "id": "graphiti-fact-1",
                        "content": "Alice coordinates retrieval evaluation.",
                        "episode_id": "episode-1",
                        "confidence": 0.91,
                    }
                ),
                graphiti_episode_to_candidate(
                    {
                        "id": "graphiti-episode-1",
                        "content": "Episode notes describe token-bounded context assembly.",
                        "source": "conversation-1",
                        "created_at": "2026-01-01",
                    }
                ),
            ],
        },
        {
            "dispatch_id": "provider-smoke-langextract",
            "agent_id": "provider_smoke_agent",
            "round_id": "round-langextract",
            "provider_family": "langextract",
            "records": [
                langextract_span_to_candidate(
                    {
                        "text": "metric bridge evidence remains operational only",
                        "label": "claim_boundary",
                        "document_id": "doc-1",
                        "start_char": 0,
                        "end_char": 46,
                        "confidence": 0.88,
                    }
                ),
                langextract_extraction_to_candidate(
                    {
                        "extracted_text": "human labels and kappa are required",
                        "type": "requirement",
                        "document_id": "doc-1",
                        "start_char": 48,
                        "end_char": 84,
                    }
                ),
            ],
        },
    ]


def _select_first_fit(items: list[dict[str, Any]], budget_tokens: int) -> tuple[list[str], list[str], int, list[dict[str, Any]]]:
    selected_ids: list[str] = []
    excluded_ids: list[str] = []
    used_tokens = 0
    trace: list[dict[str, Any]] = []
    for item in items:
        item_id = str(item["item_id"])
        token_cost = int(item["token_cost"])
        selected_before = list(selected_ids)
        if used_tokens + token_cost <= budget_tokens:
            selected_ids.append(item_id)
            used_tokens += token_cost
            decision = "selected"
        else:
            excluded_ids.append(item_id)
            decision = "excluded_budget"
        trace.append(
            {
                "step": len(trace) + 1,
                "item_id": item_id,
                "selected_before": selected_before,
                "token_cost": token_cost,
                "used_tokens_after": used_tokens,
                "decision": decision,
                "source": "deterministic_provider_smoke_first_fit",
            }
        )
    return selected_ids, excluded_ids, used_tokens, trace


def _materialized_content(items: list[dict[str, Any]], selected_ids: list[str]) -> str:
    lookup = {str(item["item_id"]): item for item in items}
    return "\n\n".join(f"[{item_id}]\n{lookup[item_id]['text']}" for item_id in selected_ids)


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


def _run_dispatch(
    *,
    output_dir: Path,
    artifact_paths: dict[str, Path],
    run_id: str,
    dispatch: dict[str, Any],
    budget_tokens: int,
    seed: int,
) -> dict[str, Any]:
    provider_candidates = list(dispatch["records"])
    normalized_candidates = normalize_candidate_pool(provider_candidates)
    for candidate in provider_candidates:
        append_jsonl(
            artifact_paths["provider_candidates"],
            {
                "run_id": run_id,
                "dispatch_id": dispatch["dispatch_id"],
                "agent_id": dispatch["agent_id"],
                "round_id": dispatch["round_id"],
                "provider_family": dispatch["provider_family"],
                "candidate": candidate,
            },
        )
    for candidate in normalized_candidates:
        append_jsonl(
            artifact_paths["normalized_candidates"],
            {
                "run_id": run_id,
                "dispatch_id": dispatch["dispatch_id"],
                "agent_id": dispatch["agent_id"],
                "round_id": dispatch["round_id"],
                "provider_family": dispatch["provider_family"],
                "candidate": candidate,
            },
        )

    selected_ids, excluded_ids, realized_tokens, trace = _select_first_fit(
        normalized_candidates,
        budget_tokens,
    )
    pool_hash = candidate_pool_hash(normalized_candidates)
    common = {
        "dispatch_id": dispatch["dispatch_id"],
        "agent_id": dispatch["agent_id"],
        "round_id": dispatch["round_id"],
        "regime": "provider_offline_smoke",
        "provider_family": dispatch["provider_family"],
        "seed": seed,
        "protocol_version": PROTOCOL_VERSION,
        "claim_level": CLAIM_LEVEL,
    }
    candidate_pool = CandidatePool(
        dispatch_id=dispatch["dispatch_id"],
        agent_id=dispatch["agent_id"],
        round_id=dispatch["round_id"],
        regime="provider_offline_smoke",
        budget_tokens=budget_tokens,
        items=normalized_candidates,
        candidate_pool_hash=pool_hash,
    )
    candidate_pool_payload = {
        **to_payload(candidate_pool),
        **common,
        "candidate_count": len(normalized_candidates),
    }
    _write_artifact_and_event(
        output_dir=output_dir,
        run_id=run_id,
        event_type="candidate_pool_materialized",
        payload=candidate_pool_payload,
        notes="provider offline smoke candidate pool materialized",
        artifact_paths=artifact_paths,
    )

    projection_plan = ProjectionPlan(
        dispatch_id=dispatch["dispatch_id"],
        agent_id=dispatch["agent_id"],
        round_id=dispatch["round_id"],
        regime="provider_offline_smoke",
        algorithm="deterministic_provider_smoke_first_fit",
        budget_tokens=budget_tokens,
        candidate_pool_hash=pool_hash,
        selected_ids=selected_ids,
        excluded_ids=excluded_ids,
        trace=trace,
        score_config={
            "selection_policy": "input_order_first_fit",
            "claim_level": CLAIM_LEVEL,
            "optimization_claim": "none",
        },
    )
    projection_payload = {**to_payload(projection_plan), **common}
    _write_artifact_and_event(
        output_dir=output_dir,
        run_id=run_id,
        event_type="projection_plan_materialized",
        payload=projection_payload,
        notes="provider offline smoke projection plan materialized",
        artifact_paths=artifact_paths,
    )

    budget_witness = BudgetWitness(
        dispatch_id=dispatch["dispatch_id"],
        agent_id=dispatch["agent_id"],
        round_id=dispatch["round_id"],
        regime="provider_offline_smoke",
        budget_tokens=budget_tokens,
        estimated_tokens=realized_tokens,
        realized_tokens=realized_tokens,
        within_budget=realized_tokens <= budget_tokens,
        selected_ids=selected_ids,
        excluded_ids=excluded_ids,
        tolerance_violations=[] if realized_tokens <= budget_tokens else [{"type": "budget_overflow"}],
    )
    witness_payload = {**to_payload(budget_witness), **common, "candidate_pool_hash": pool_hash}
    _write_artifact_and_event(
        output_dir=output_dir,
        run_id=run_id,
        event_type="budget_witness_materialized",
        payload=witness_payload,
        notes="provider offline smoke budget witness materialized",
        artifact_paths=artifact_paths,
    )

    content = _materialized_content(normalized_candidates, selected_ids)
    materialized_context = MaterializedContext(
        dispatch_id=dispatch["dispatch_id"],
        agent_id=dispatch["agent_id"],
        round_id=dispatch["round_id"],
        regime="provider_offline_smoke",
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
        notes="provider offline smoke materialized context recorded",
        artifact_paths=artifact_paths,
    )

    metric_bridge_witness = MetricBridgeWitness(
        dispatch_id=dispatch["dispatch_id"],
        agent_id=dispatch["agent_id"],
        round_id=dispatch["round_id"],
        regime="provider_offline_smoke",
        calibration_epoch=None,
        active_stratum={"regime": "provider_offline_smoke", "provider_family": dispatch["provider_family"]},
        model_tier=None,
        utility_metric="offline_provider_smoke_coverage",
        metric_class="engineering_smoke_only",
        materialization_policy={
            "algorithm": "deterministic_provider_smoke_first_fit",
            "budget_tokens": budget_tokens,
            "selected_count": len(selected_ids),
            "excluded_count": len(excluded_ids),
            "claim_level": CLAIM_LEVEL,
        },
        decoding_policy={"mode": "not_applicable"},
        bridge_scale=None,
        bridge_residual_zeta=None,
        effective_sample_size=None,
        drift_status="not_applicable",
        diagnostic_mode="provider_offline_smoke",
        diagnostic_claim_level=CLAIM_LEVEL,
    )
    metric_bridge_payload = {
        **to_payload(metric_bridge_witness),
        **common,
        "candidate_pool_hash": pool_hash,
        "context_hash": materialized_context.context_hash,
        "notes": "offline engineering smoke evidence only; not measurement validation",
    }
    _write_artifact_and_event(
        output_dir=output_dir,
        run_id=run_id,
        event_type="metric_bridge_witness_materialized",
        payload=metric_bridge_payload,
        notes="provider offline smoke metric bridge witness materialized",
        artifact_paths=artifact_paths,
    )

    diagnostics = ProjectionDiagnostics(
        dispatch_id=dispatch["dispatch_id"],
        agent_id=dispatch["agent_id"],
        round_id=dispatch["round_id"],
        regime="provider_offline_smoke",
        block_ratio_lcb_b2=None,
        block_ratio_lcb_star=None,
        block_ratio_lcb_star_semantics="not_applicable_provider_offline_smoke",
        block_ratio_lcb_b3=None,
        block_ratio_uninformative_count=0,
        block_ratio_sample_count=0,
        trace_decay_proxy=None,
        gamma_hat=None,
        synergy_fraction=0.0,
        positive_interaction_mass_ucb=None,
        triple_excess_lcb_max=None,
        triple_excess_flag="not_applicable",
        higher_order_ambiguity_flag=False,
        greedy_augmented_gap=0.0,
        metric_claim_level=CLAIM_LEVEL,
        selector_regime_label="engineering_smoke",
        selector_action="deterministic_provider_smoke_first_fit",
        policy_recommendation="deterministic_provider_smoke_first_fit",
        greedy_value=float(len(selected_ids)),
        augmented_value=float(len(selected_ids)),
        local_search_value=float(len(selected_ids)),
        pairwise_samples=[],
        block_ratio_samples=[],
        triple_samples=[],
        thresholds={},
        notes="offline provider-to-selector smoke path only",
    )
    diagnostic_payload = {
        **to_payload(diagnostics),
        **common,
        "candidate_pool_hash": pool_hash,
        "candidate_count": len(normalized_candidates),
        "budget_tokens": budget_tokens,
        "selected_ids": selected_ids,
        "excluded_ids": excluded_ids,
        "estimated_tokens": realized_tokens,
        "realized_tokens": realized_tokens,
        "within_budget": realized_tokens <= budget_tokens,
        "normalized_aliases_required": True,
    }
    _write_artifact_and_event(
        output_dir=output_dir,
        run_id=run_id,
        event_type="projection_diagnostics_materialized",
        payload=diagnostic_payload,
        notes="provider offline smoke diagnostics materialized",
        artifact_paths=artifact_paths,
    )

    bundle = ProjectionBundleV1(
        run_id=run_id,
        dispatch_id=dispatch["dispatch_id"],
        agent_id=dispatch["agent_id"],
        round_id=dispatch["round_id"],
        candidate_pool=candidate_pool_payload,
        projection_plan=projection_payload,
        budget_witness=witness_payload,
        materialized_context=context_payload,
        metric_bridge_witness=metric_bridge_payload,
        diagnostics=diagnostic_payload,
        source_mode="provider_offline_smoke",
    )
    bundle_payload = ProjectionBundleV1(
        run_id=run_id,
        dispatch_id=dispatch["dispatch_id"],
        agent_id=dispatch["agent_id"],
        round_id=dispatch["round_id"],
        candidate_pool=candidate_pool_payload,
        projection_plan=projection_payload,
        budget_witness=witness_payload,
        materialized_context=context_payload,
        metric_bridge_witness=metric_bridge_payload,
        diagnostics=diagnostic_payload,
        source_mode="provider_offline_smoke",
        canonical_hash_value=bundle.canonical_hash(),
    ).to_dict()
    _write_artifact_and_event(
        output_dir=output_dir,
        run_id=run_id,
        event_type="projection_bundle_materialized",
        payload=bundle_payload,
        notes="provider offline smoke projection bundle materialized",
        artifact_paths=artifact_paths,
    )
    return diagnostic_payload


def run_provider_offline_smoke(
    output_dir: str | Path,
    *,
    seed: int = 0,
    budget_tokens: int = 12,
) -> dict[str, Any]:
    resolved_output_dir = Path(output_dir).resolve()
    artifact_paths = _artifact_paths(resolved_output_dir)
    _reset_outputs(resolved_output_dir, artifact_paths)
    run_id = f"{RUN_ID_PREFIX}-{int(seed)}"
    diagnostics_rows = [
        _run_dispatch(
            output_dir=resolved_output_dir,
            artifact_paths=artifact_paths,
            run_id=run_id,
            dispatch=dispatch,
            budget_tokens=int(budget_tokens),
            seed=int(seed),
        )
        for dispatch in _provider_dispatches()
    ]
    rebuilt = rebuild_projection_summary_from_events(resolved_output_dir, run_id=run_id)
    artifact_complete = bool(rebuilt.get("complete_artifact_sets"))
    status = "green" if artifact_complete else "red"
    summary = {
        **rebuilt,
        "status": status,
        "run_id": run_id,
        "seed": int(seed),
        "budget_tokens": int(budget_tokens),
        "output_dir": str(resolved_output_dir),
        "claim_level": CLAIM_LEVEL,
        "provider_families": ["graphiti", "langextract"],
        "selection_policy": "deterministic_provider_smoke_first_fit",
        "artifact_complete": artifact_complete,
        "dispatch_ids": [row["dispatch_id"] for row in diagnostics_rows],
        "artifact_paths": {
            "events": str(resolved_output_dir / "events.jsonl"),
            **{key: str(path) for key, path in artifact_paths.items()},
        },
        "interpretation_limits": [
            "engineering smoke only",
            "no live cohort",
            "no external runtime integration",
            "no measurement validation",
            "no deployed V-information certification",
        ],
    }
    summary_path = write_json(resolved_output_dir / "summary.json", summary)
    return {
        "status": status,
        "run_id": run_id,
        "summary_path": str(summary_path),
        "events_path": str(resolved_output_dir / "events.jsonl"),
        "summary": summary,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the provider-to-selector offline smoke path.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--budget-tokens", type=int, default=12)
    args = parser.parse_args()

    report = run_provider_offline_smoke(
        args.output_dir,
        seed=args.seed,
        budget_tokens=args.budget_tokens,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "green" else 1


if __name__ == "__main__":
    raise SystemExit(main())
