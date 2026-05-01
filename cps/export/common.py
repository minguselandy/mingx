from __future__ import annotations

from typing import Any

from cps.schema import ProjectionBundleV1


PREVIEW_LIMIT = 80


def _omit_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _bounded_preview(value: Any, *, limit: int = PREVIEW_LIMIT) -> str:
    text = str(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def _selected_ids(bundle_payload: dict[str, Any]) -> list[Any]:
    for section_name in ("projection_plan", "budget_witness", "materialized_context"):
        section = bundle_payload.get(section_name) or {}
        selected = section.get("selected_ids")
        if selected is not None:
            return list(selected)
    return []


def _candidate_count(candidate_pool: dict[str, Any]) -> int | None:
    if "candidate_count" in candidate_pool:
        return candidate_pool["candidate_count"]
    items = candidate_pool.get("items")
    if items is not None:
        return len(items)
    candidates = candidate_pool.get("candidates")
    if candidates is not None:
        return len(candidates)
    return None


def _observability_attributes(bundle: ProjectionBundleV1, bundle_payload: dict[str, Any]) -> dict[str, Any]:
    candidate_pool = bundle_payload["candidate_pool"]
    projection_plan = bundle_payload["projection_plan"]
    budget_witness = bundle_payload["budget_witness"]
    materialized_context = bundle_payload["materialized_context"]
    metric_bridge_witness = bundle_payload["metric_bridge_witness"]
    diagnostics = bundle_payload.get("diagnostics") or {}

    selected_ids = _selected_ids(bundle_payload)
    budget_tokens = (
        budget_witness.get("budget_tokens")
        or projection_plan.get("budget_tokens")
        or candidate_pool.get("budget_tokens")
    )

    attributes = {
        "cps.bundle_version": bundle.bundle_version,
        "cps.run_id": bundle.run_id,
        "cps.dispatch_id": bundle.dispatch_id,
        "cps.agent_id": bundle.agent_id,
        "cps.round_id": bundle.round_id,
        "cps.source_mode": bundle.source_mode,
        "cps.canonical_hash": bundle.canonical_hash(),
        "cps.candidate_count": _candidate_count(candidate_pool),
        "cps.selected_count": len(selected_ids),
        "cps.selected_ids": selected_ids,
        "cps.budget_tokens": budget_tokens,
        "cps.estimated_tokens": budget_witness.get("estimated_tokens"),
        "cps.realized_tokens": budget_witness.get("realized_tokens"),
        "cps.within_budget": budget_witness.get("within_budget"),
        "cps.context_hash": materialized_context.get("context_hash"),
        "cps.metric_class": metric_bridge_witness.get("metric_class"),
        "cps.diagnostic_claim_level": metric_bridge_witness.get("diagnostic_claim_level"),
        "cps.metric_claim_level": diagnostics.get("metric_claim_level"),
        "cps.selector_regime_label": diagnostics.get("selector_regime_label"),
        "cps.selector_action": diagnostics.get("selector_action"),
        "cps.contamination_gate_decision": diagnostics.get("contamination_gate_decision"),
        "cps.annotation_mode": diagnostics.get("annotation_mode"),
        "cps.kappa_summary_path": diagnostics.get("kappa_summary_path"),
        "cps.bridge_status": diagnostics.get("bridge_status"),
    }
    return _omit_none(attributes)


def projection_bundle_observability_fields(
    bundle: ProjectionBundleV1,
    *,
    include_payload_preview: bool = False,
) -> dict[str, Any]:
    bundle.validate_required_identity()
    bundle_payload = bundle.to_dict()
    attributes = _observability_attributes(bundle, bundle_payload)

    fields: dict[str, Any] = {
        "bundle_version": bundle.bundle_version,
        "run_id": bundle.run_id,
        "dispatch_id": bundle.dispatch_id,
        "agent_id": bundle.agent_id,
        "round_id": bundle.round_id,
        "source_mode": bundle.source_mode,
        "canonical_hash": bundle.canonical_hash(),
        "attributes": attributes,
    }
    fields = _omit_none(fields)

    if include_payload_preview:
        materialized_context = bundle_payload["materialized_context"]
        candidate_pool = bundle_payload["candidate_pool"]
        projection_plan = bundle_payload["projection_plan"]
        fields["payload_preview"] = _omit_none(
            {
                "materialized_context_preview": _bounded_preview(
                    materialized_context.get("content", "")
                ),
                "candidate_ids_preview": [
                    item.get("candidate_id") or item.get("item_id")
                    for item in candidate_pool.get("items", [])[:5]
                ],
                "selected_ids_preview": list(projection_plan.get("selected_ids", []))[:10],
            }
        )

    return fields
