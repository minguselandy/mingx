from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from cps.experiments.decision import derive_metric_claim_level


DENOMINATOR_THRESHOLD = 1e-9
ARTIFACT_FILE_SPECS = {
    "candidate_pools.jsonl": "candidate_pool",
    "projection_plans.jsonl": "projection_plan",
    "budget_witnesses.jsonl": "budget_witness",
    "materialized_contexts.jsonl": "materialized_context",
    "metric_bridge_witnesses.jsonl": "metric_bridge_witness",
    "diagnostics.jsonl": "diagnostics",
    "utility_records.jsonl": "utility_record",
    "cached_utility_records.jsonl": "utility_record",
    "log_loss_records.jsonl": "utility_record",
}
EVENT_TYPE_TO_ARTIFACT = {
    "candidate_pool_materialized": "candidate_pool",
    "projection_plan_materialized": "projection_plan",
    "budget_witness_materialized": "budget_witness",
    "materialized_context_materialized": "materialized_context",
    "metric_bridge_witness_materialized": "metric_bridge_witness",
    "projection_diagnostics_materialized": "diagnostics",
}
CORE_PAPER_ARTIFACTS = [
    "ProjectionPlan",
    "BudgetWitness",
    "MaterializedContext",
    "MetricBridgeWitness",
]
REPLAY_SUBSTRATE_ARTIFACTS = ["CandidatePool"]
REPLAY_STATUSES = ("replay_usable", "pilot_degraded", "replay_partial", "replay_unusable")


@dataclass
class ReplayArtifactBundle:
    run_id: str | None
    dispatch_id: str | None
    agent_id: str | None
    round_id: str | None
    candidate_pool: dict[str, Any] | None
    projection_plan: dict[str, Any] | None
    budget_witness: dict[str, Any] | None
    materialized_context: dict[str, Any] | None
    metric_bridge_witness: dict[str, Any] | None
    diagnostics: dict[str, Any] | None
    utility_records: list[dict[str, Any]]
    source_files: list[str]
    raw_event_records: list[dict[str, Any]]


@dataclass(frozen=True)
class ReplayManifestRow:
    run_id: str | None
    dispatch_id: str | None
    agent_id: str | None
    round_id: str | None
    replay_status: str
    replay_claim_scope: str
    candidate_pool_present: bool
    projection_plan_present: bool
    budget_witness_present: bool
    materialized_context_present: bool
    metric_bridge_witness_present: bool
    cached_utility_records_present: bool
    selected_ids_present: bool
    excluded_ids_present: bool
    materialization_order_present: bool
    bridge_status: str
    metric_claim_level: str
    selector_regime_label: str
    diagnostic_recompute_status: str
    headline_eligible: bool
    headline_exclusion_reason: str
    selected_token_cost: int | None
    budget_utilization: float | None
    observed_proxy_value: float | None
    block_ratio_lcb_b2: float | None
    contamination_status: str
    missing_required_fields: list[str]
    missing_optional_fields: list[str]
    replay_defects: list[str]
    notes: str


@dataclass(frozen=True)
class MissingFieldRecord:
    run_id: str | None
    dispatch_id: str | None
    agent_id: str | None
    round_id: str | None
    field: str
    artifact: str
    severity: str
    required_for: str
    reason: str


@dataclass(frozen=True)
class ReplaySummary:
    total_dispatches: int
    replay_status_counts: dict[str, int]
    artifact_presence_counts: dict[str, int]
    metric_claim_level_counts: dict[str, int]
    headline_metric_claim_level_counts: dict[str, int]
    headline_selector_regime_counts: dict[str, int]
    headline_exclusion_counts: dict[str, int]
    missing_field_counts: dict[str, int]
    replay_usable_dispatches: int
    replay_nonusable_dispatches: int
    headline_eligible_dispatches: int
    headline_excluded_dispatches: int
    replay_usable_dispatch_ids: list[str]
    replay_nonusable_dispatch_ids: list[str]
    headline_eligible_dispatch_ids: list[str]
    headline_excluded_dispatch_ids: list[str]
    core_paper_artifacts: list[str]
    replay_substrate_artifacts: list[str]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL in {path} line {line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"invalid JSONL in {path} line {line_number}: expected object")
        rows.append(row)
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"invalid JSON in {path}: expected object")
    return payload


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _clean_id(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _record_identity(record: dict[str, Any]) -> dict[str, str | None]:
    return {
        "run_id": _clean_id(record.get("run_id")),
        "dispatch_id": _clean_id(record.get("dispatch_id")),
        "agent_id": _clean_id(record.get("agent_id")),
        "round_id": _clean_id(record.get("round_id")),
    }


def _dispatch_group_key(identity: dict[str, str | None], source_file: str, index: int) -> tuple[Any, ...]:
    dispatch_id = identity.get("dispatch_id")
    agent_id = identity.get("agent_id")
    round_id = identity.get("round_id")
    if dispatch_id or agent_id or round_id:
        return ("dispatch", dispatch_id, agent_id, round_id)
    return ("unbound", identity.get("run_id"), source_file, index)


def _merge_identity(current: dict[str, str | None], record: dict[str, Any]) -> None:
    identity = _record_identity(record)
    for field, value in identity.items():
        if current.get(field) is None and value is not None:
            current[field] = value


def _empty_bundle(identity: dict[str, str | None]) -> dict[str, Any]:
    return {
        "identity": dict(identity),
        "candidate_pool": None,
        "projection_plan": None,
        "budget_witness": None,
        "materialized_context": None,
        "metric_bridge_witness": None,
        "diagnostics": None,
        "utility_records": [],
        "source_files": set(),
        "raw_event_records": [],
    }


def _put_artifact(bundle: dict[str, Any], artifact_kind: str, row: dict[str, Any], source_file: str) -> None:
    _merge_identity(bundle["identity"], row)
    bundle["source_files"].add(source_file)
    if artifact_kind == "utility_record":
        bundle["utility_records"].append(row)
    elif artifact_kind == "diagnostics":
        bundle["diagnostics"] = row
    else:
        bundle[artifact_kind] = row


def _bundle_from_state(state: dict[str, Any]) -> ReplayArtifactBundle:
    identity = state["identity"]
    return ReplayArtifactBundle(
        run_id=identity.get("run_id"),
        dispatch_id=identity.get("dispatch_id"),
        agent_id=identity.get("agent_id"),
        round_id=identity.get("round_id"),
        candidate_pool=state["candidate_pool"],
        projection_plan=state["projection_plan"],
        budget_witness=state["budget_witness"],
        materialized_context=state["materialized_context"],
        metric_bridge_witness=state["metric_bridge_witness"],
        diagnostics=state["diagnostics"],
        utility_records=list(state["utility_records"]),
        source_files=sorted(state["source_files"]),
        raw_event_records=list(state["raw_event_records"]),
    )


def load_replay_artifact_bundles(input_dir: str | Path) -> list[ReplayArtifactBundle]:
    root = Path(input_dir)
    grouped: dict[tuple[Any, ...], dict[str, Any]] = {}

    for filename, artifact_kind in ARTIFACT_FILE_SPECS.items():
        path = root / filename
        for index, row in enumerate(_read_jsonl(path)):
            identity = _record_identity(row)
            key = _dispatch_group_key(identity, filename, index)
            bundle = grouped.setdefault(key, _empty_bundle(identity))
            _put_artifact(bundle, artifact_kind, row, filename)

    events_path = root / "events.jsonl"
    for index, event in enumerate(_read_jsonl(events_path)):
        event_type = str(event.get("event_type", "") or "")
        artifact_kind = EVENT_TYPE_TO_ARTIFACT.get(event_type)
        payload = dict(event.get("payload") or {})
        if not artifact_kind or not payload:
            continue
        payload.setdefault("run_id", event.get("run_id"))
        identity = _record_identity(payload)
        key = _dispatch_group_key(identity, "events.jsonl", index)
        bundle = grouped.setdefault(key, _empty_bundle(identity))
        _put_artifact(bundle, artifact_kind, payload, "events.jsonl")
        _merge_identity(bundle["identity"], event)
        bundle["source_files"].add("events.jsonl")
        bundle["raw_event_records"].append(event)

    return [_bundle_from_state(grouped[key]) for key in sorted(grouped, key=str)]


def _ids_from_record(record: dict[str, Any] | None, field: str) -> list[str]:
    if not record:
        return []
    value = record.get(field)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def _candidate_ids(candidate_pool: dict[str, Any] | None) -> list[str]:
    if not candidate_pool:
        return []
    items = candidate_pool.get("items")
    if not isinstance(items, list):
        return []
    ids: list[str] = []
    for item in items:
        if isinstance(item, dict) and item.get("item_id") is not None:
            ids.append(str(item["item_id"]))
    return ids


def _selected_ids(bundle: ReplayArtifactBundle) -> list[str]:
    for record in (bundle.projection_plan, bundle.budget_witness, bundle.materialized_context, bundle.diagnostics):
        ids = _ids_from_record(record, "selected_ids")
        if ids:
            return ids
    return []


def _excluded_ids_present(bundle: ReplayArtifactBundle, selected_ids: list[str]) -> bool:
    for record in (bundle.projection_plan, bundle.budget_witness, bundle.diagnostics):
        excluded = _ids_from_record(record, "excluded_ids")
        if excluded:
            return True
    candidate_ids = set(_candidate_ids(bundle.candidate_pool))
    if candidate_ids and set(selected_ids) == candidate_ids:
        return True
    plan = bundle.projection_plan or {}
    for field in ("considered_candidate_ids", "candidate_ids_considered", "candidate_ids"):
        considered = _ids_from_record(plan, field)
        if considered:
            return True
    return False


def _materialization_order_present(bundle: ReplayArtifactBundle) -> bool:
    context = bundle.materialized_context or {}
    for field in ("section_order", "materialization_order", "section_manifest"):
        value = context.get(field)
        if isinstance(value, list) and value:
            return True
    return False


def _realized_budget_present(bundle: ReplayArtifactBundle) -> bool:
    witness = bundle.budget_witness or {}
    for field in ("realized_tokens", "estimated_tokens", "token_count"):
        value = witness.get(field)
        if isinstance(value, (int, float)):
            return True
    return False


def _selected_token_cost(bundle: ReplayArtifactBundle, selected_ids: list[str]) -> int | None:
    if not selected_ids or not bundle.candidate_pool:
        return None
    by_id = {
        str(item.get("item_id")): item
        for item in bundle.candidate_pool.get("items", [])
        if isinstance(item, dict) and item.get("item_id") is not None
    }
    total = 0
    for item_id in selected_ids:
        item = by_id.get(str(item_id))
        if item is None or not isinstance(item.get("token_cost"), (int, float)):
            return None
        total += int(item["token_cost"])
    return total


def _budget_utilization(bundle: ReplayArtifactBundle, selected_token_cost: int | None) -> float | None:
    if selected_token_cost is None:
        return None
    budget = None
    for record in (bundle.budget_witness, bundle.projection_plan, bundle.candidate_pool):
        if not record:
            continue
        value = record.get("budget_tokens")
        if isinstance(value, (int, float)) and value > 0:
            budget = float(value)
            break
    if budget is None:
        return None
    return round(float(selected_token_cost) / budget, 6)


def _utility_payload(bundle: ReplayArtifactBundle) -> dict[str, Any] | None:
    for row in bundle.utility_records:
        if isinstance(row.get("singleton_values"), dict) and isinstance(row.get("block_values"), dict):
            return row
    return None


def _pair_key(first: str, second: str) -> str:
    return ",".join(sorted([str(first), str(second)]))


def _diagnostic_recompute(
    bundle: ReplayArtifactBundle,
    *,
    selected_ids: list[str],
    selected_token_cost: int | None,
    budget_utilization: float | None,
) -> dict[str, Any]:
    utility = _utility_payload(bundle)
    if utility is None:
        return {
            "diagnostic_recompute_status": "insufficient_utility_records",
            "observed_proxy_value": None,
            "block_ratio_lcb_b2": None,
            "selected_token_cost": selected_token_cost,
            "budget_utilization": budget_utilization,
        }

    singleton_values = utility.get("singleton_values") or {}
    block_values = utility.get("block_values") or {}
    if not selected_ids or any(item_id not in singleton_values for item_id in selected_ids):
        return {
            "diagnostic_recompute_status": "insufficient_utility_records",
            "observed_proxy_value": None,
            "block_ratio_lcb_b2": None,
            "selected_token_cost": selected_token_cost,
            "budget_utilization": budget_utilization,
        }

    selected_key = ",".join(sorted(selected_ids))
    if selected_key in block_values:
        observed_proxy_value = float(block_values[selected_key])
    else:
        observed_proxy_value = sum(float(singleton_values[item_id]) for item_id in selected_ids)

    candidate_ids = _candidate_ids(bundle.candidate_pool)
    if len(candidate_ids) < 2:
        return {
            "diagnostic_recompute_status": "insufficient_utility_records",
            "observed_proxy_value": round(observed_proxy_value, 6),
            "block_ratio_lcb_b2": None,
            "selected_token_cost": selected_token_cost,
            "budget_utilization": budget_utilization,
        }

    ratios: list[float] = []
    saw_uninformative_denominator = False
    for index, first in enumerate(candidate_ids):
        for second in candidate_ids[index + 1 :]:
            key = _pair_key(first, second)
            if first not in singleton_values or second not in singleton_values or key not in block_values:
                continue
            denominator = float(block_values[key])
            if denominator <= DENOMINATOR_THRESHOLD:
                saw_uninformative_denominator = True
                continue
            numerator = float(singleton_values[first]) + float(singleton_values[second])
            ratios.append(round(max(0.0, min(1.0, numerator / denominator)), 6))

    if not ratios:
        status = "uninformative_denominator" if saw_uninformative_denominator else "insufficient_utility_records"
        return {
            "diagnostic_recompute_status": status,
            "observed_proxy_value": round(observed_proxy_value, 6),
            "block_ratio_lcb_b2": None,
            "selected_token_cost": selected_token_cost,
            "budget_utilization": budget_utilization,
        }

    return {
        "diagnostic_recompute_status": "recomputed",
        "observed_proxy_value": round(observed_proxy_value, 6),
        "block_ratio_lcb_b2": min(ratios),
        "selected_token_cost": selected_token_cost,
        "budget_utilization": budget_utilization,
    }


def _contamination_status(input_dir: Path) -> str:
    payload = _read_json(input_dir / "contamination_report.json")
    if not payload:
        return "not_applicable"
    status = str(payload.get("contamination_status") or payload.get("status") or "unknown").strip().lower()
    if status == "fail":
        return "failed"
    if status not in {"pass", "failed", "incomplete", "unknown"}:
        return "unknown"
    return status


def _add_missing(
    missing: list[MissingFieldRecord],
    bundle: ReplayArtifactBundle,
    *,
    field: str,
    artifact: str,
    severity: str,
    required_for: str,
    reason: str,
) -> None:
    missing.append(
        MissingFieldRecord(
            run_id=bundle.run_id,
            dispatch_id=bundle.dispatch_id,
            agent_id=bundle.agent_id,
            round_id=bundle.round_id,
            field=field,
            artifact=artifact,
            severity=severity,
            required_for=required_for,
            reason=reason,
        )
    )


def _bridge_scope(metric_bridge_witness: dict[str, Any] | None, metric_claim_level: str) -> tuple[str, str]:
    if not metric_bridge_witness:
        return "missing", "observability_only"
    drift_status = str(metric_bridge_witness.get("drift_status") or "unknown")
    if drift_status == "stale":
        return drift_status, "recalibration_required"
    if drift_status == "ambiguous":
        return drift_status, "ambiguous"
    return drift_status, metric_claim_level


def classify_replay_bundle(
    bundle: ReplayArtifactBundle,
    *,
    contamination_status: str = "not_applicable",
) -> tuple[ReplayManifestRow, list[MissingFieldRecord]]:
    missing: list[MissingFieldRecord] = []
    replay_defects: list[str] = []
    missing_optional_fields: list[str] = []
    selected_ids = _selected_ids(bundle)

    if not bundle.run_id:
        _add_missing(
            missing,
            bundle,
            field="run_id",
            artifact="identity",
            severity="error",
            required_for="dispatch_binding",
            reason="run_id is required to reconstruct a dispatch binding",
        )
        replay_defects.append("missing_dispatch_binding")
    for field in ("dispatch_id", "agent_id", "round_id"):
        if not getattr(bundle, field):
            _add_missing(
                missing,
                bundle,
                field=field,
                artifact="identity",
                severity="error",
                required_for="dispatch_binding",
                reason=f"{field} is required to reconstruct a dispatch binding",
            )
            replay_defects.append("missing_dispatch_binding")

    candidate_pool_present = bundle.candidate_pool is not None
    projection_plan_present = bundle.projection_plan is not None
    budget_witness_present = bundle.budget_witness is not None
    materialized_context_present = bundle.materialized_context is not None
    metric_bridge_witness_present = bundle.metric_bridge_witness is not None
    cached_utility_records_present = bool(bundle.utility_records)
    selected_ids_present = bool(selected_ids)
    excluded_ids_present = _excluded_ids_present(bundle, selected_ids)
    materialization_order_present = _materialization_order_present(bundle)
    realized_budget_present = _realized_budget_present(bundle)
    metric_claim_level = derive_metric_claim_level(bundle.metric_bridge_witness)
    bridge_status, replay_claim_scope = _bridge_scope(bundle.metric_bridge_witness, metric_claim_level)
    if contamination_status == "failed":
        metric_claim_level = "pilot_only"
        replay_claim_scope = "pilot_only"
    selector_regime_label = str((bundle.diagnostics or {}).get("selector_regime_label") or "unknown")
    selected_token_cost = _selected_token_cost(bundle, selected_ids)
    budget_utilization = _budget_utilization(bundle, selected_token_cost)
    diagnostic = _diagnostic_recompute(
        bundle,
        selected_ids=selected_ids,
        selected_token_cost=selected_token_cost,
        budget_utilization=budget_utilization,
    )

    if not candidate_pool_present:
        _add_missing(
            missing,
            bundle,
            field="CandidatePool",
            artifact="candidate_pools.jsonl",
            severity="error",
            required_for="replay_usable",
            reason="candidate pool is replay substrate required to reconstruct M",
        )
    if not projection_plan_present:
        _add_missing(
            missing,
            bundle,
            field="ProjectionPlan",
            artifact="projection_plans.jsonl",
            severity="error",
            required_for="replay_usable",
            reason="projection plan is required to reconstruct observed selector output",
        )
    if not selected_ids_present:
        _add_missing(
            missing,
            bundle,
            field="selected_ids",
            artifact="ProjectionPlan",
            severity="error",
            required_for="dispatch_binding",
            reason="selected candidate ids are required to reconstruct S_i",
        )
    if not excluded_ids_present:
        _add_missing(
            missing,
            bundle,
            field="excluded_ids",
            artifact="ProjectionPlan",
            severity="error",
            required_for="replay_usable",
            reason="excluded candidates are required to audit candidate-pool completeness",
        )
        replay_defects.append("missing_excluded_candidates")
    if not budget_witness_present:
        _add_missing(
            missing,
            bundle,
            field="BudgetWitness",
            artifact="budget_witnesses.jsonl",
            severity="error",
            required_for="replay_usable",
            reason="budget witness is required to reconstruct B_i",
        )
    elif not realized_budget_present:
        _add_missing(
            missing,
            bundle,
            field="realized_budget",
            artifact="BudgetWitness",
            severity="error",
            required_for="replay_usable",
            reason="realized or estimated token usage is required to reconstruct B_i",
        )
        replay_defects.append("missing_realized_budget")
    if not materialized_context_present:
        _add_missing(
            missing,
            bundle,
            field="MaterializedContext",
            artifact="materialized_contexts.jsonl",
            severity="error",
            required_for="replay_usable",
            reason="materialized context is required to audit context assembly",
        )
    if not materialization_order_present:
        _add_missing(
            missing,
            bundle,
            field="materialization_order",
            artifact="MaterializedContext",
            severity="error",
            required_for="replay_usable",
            reason="materialization order must be recorded and cannot be inferred from selected ids",
        )
        replay_defects.append("missing_materialization_order")
    if not metric_bridge_witness_present:
        _add_missing(
            missing,
            bundle,
            field="MetricBridgeWitness",
            artifact="metric_bridge_witnesses.jsonl",
            severity="error",
            required_for="bridge_qualified_claim",
            reason="full claim-level replay requires a metric bridge witness",
        )
    if metric_bridge_witness_present and metric_claim_level == "ambiguous":
        _add_missing(
            missing,
            bundle,
            field="MetricBridgeWitness",
            artifact="metric_bridge_witnesses.jsonl",
            severity="error",
            required_for="bridge_qualified_claim",
            reason="metric bridge witness is stale, ambiguous, or unknown and cannot qualify proxy-regime claims",
        )
        replay_defects.append("metric_bridge_not_fresh")
    if not cached_utility_records_present:
        _add_missing(
            missing,
            bundle,
            field="cached_utility_records",
            artifact="utility_records.jsonl",
            severity="error",
            required_for="future_diagnostic_recomputation",
            reason="cached utility or log-loss records are required for future diagnostic recomputation",
        )
    if bundle.diagnostics is None:
        missing_optional_fields.append("diagnostics")

    missing_required_fields = [row.field for row in missing if row.severity == "error"]
    if not candidate_pool_present or not selected_ids_present or "missing_dispatch_binding" in replay_defects:
        replay_status = "replay_unusable"
    elif not metric_bridge_witness_present or metric_claim_level == "ambiguous":
        replay_status = "replay_partial"
    elif (
        not projection_plan_present
        or not budget_witness_present
        or not materialized_context_present
        or not excluded_ids_present
        or not materialization_order_present
        or not realized_budget_present
    ):
        replay_status = "pilot_degraded"
    else:
        replay_status = "replay_usable"

    if contamination_status == "failed":
        headline_exclusion_reason = "contamination_failed"
    elif contamination_status in {"incomplete", "unknown"}:
        headline_exclusion_reason = f"contamination_{contamination_status}"
    elif replay_status != "replay_usable":
        headline_exclusion_reason = f"replay_status_{replay_status}"
    elif diagnostic["diagnostic_recompute_status"] != "recomputed":
        headline_exclusion_reason = str(diagnostic["diagnostic_recompute_status"])
    elif bridge_status in {"missing", "stale", "ambiguous", "unknown"}:
        headline_exclusion_reason = f"metric_bridge_{bridge_status}"
    elif metric_claim_level in {"ambiguous", "operational_utility_only", "pilot_only"}:
        headline_exclusion_reason = f"metric_claim_level_{metric_claim_level}"
    else:
        headline_exclusion_reason = ""
    headline_eligible = headline_exclusion_reason == ""

    notes = (
        "CandidatePool is replay substrate, not one of the four core paper artifacts. "
        "Replay status and claim level are reported separately; headline diagnostics exclude ineligible rows."
    )
    return (
        ReplayManifestRow(
            run_id=bundle.run_id,
            dispatch_id=bundle.dispatch_id,
            agent_id=bundle.agent_id,
            round_id=bundle.round_id,
            replay_status=replay_status,
            replay_claim_scope=replay_claim_scope,
            candidate_pool_present=candidate_pool_present,
            projection_plan_present=projection_plan_present,
            budget_witness_present=budget_witness_present,
            materialized_context_present=materialized_context_present,
            metric_bridge_witness_present=metric_bridge_witness_present,
            cached_utility_records_present=cached_utility_records_present,
            selected_ids_present=selected_ids_present,
            excluded_ids_present=excluded_ids_present,
            materialization_order_present=materialization_order_present,
            bridge_status=bridge_status,
            metric_claim_level=metric_claim_level,
            selector_regime_label=selector_regime_label,
            diagnostic_recompute_status=str(diagnostic["diagnostic_recompute_status"]),
            headline_eligible=headline_eligible,
            headline_exclusion_reason=headline_exclusion_reason,
            selected_token_cost=diagnostic["selected_token_cost"],
            budget_utilization=diagnostic["budget_utilization"],
            observed_proxy_value=diagnostic["observed_proxy_value"],
            block_ratio_lcb_b2=diagnostic["block_ratio_lcb_b2"],
            contamination_status=contamination_status,
            missing_required_fields=missing_required_fields,
            missing_optional_fields=missing_optional_fields,
            replay_defects=sorted(set(replay_defects)),
            notes=notes,
        ),
        missing,
    )


def _dispatch_label(row: ReplayManifestRow) -> str:
    return "/".join(
        str(value)
        for value in (row.run_id, row.dispatch_id, row.agent_id, row.round_id)
        if value is not None
    )


def build_replay_summary(rows: list[ReplayManifestRow], missing: list[MissingFieldRecord]) -> ReplaySummary:
    status_counts = Counter(row.replay_status for row in rows)
    metric_counts = Counter(row.metric_claim_level for row in rows)
    headline_rows = [row for row in rows if row.headline_eligible]
    headline_metric_counts = Counter(row.metric_claim_level for row in headline_rows)
    headline_selector_counts = Counter(row.selector_regime_label for row in headline_rows)
    headline_exclusion_counts = Counter(row.headline_exclusion_reason for row in rows if not row.headline_eligible)
    missing_counts = Counter(record.field for record in missing)
    artifact_presence_counts = {
        "candidate_pools": sum(1 for row in rows if row.candidate_pool_present),
        "projection_plans": sum(1 for row in rows if row.projection_plan_present),
        "budget_witnesses": sum(1 for row in rows if row.budget_witness_present),
        "materialized_contexts": sum(1 for row in rows if row.materialized_context_present),
        "metric_bridge_witnesses": sum(1 for row in rows if row.metric_bridge_witness_present),
        "cached_utility_records": sum(1 for row in rows if row.cached_utility_records_present),
    }
    usable = [row for row in rows if row.replay_status == "replay_usable"]
    nonusable = [row for row in rows if row.replay_status != "replay_usable"]
    headline_excluded = [row for row in rows if not row.headline_eligible]
    return ReplaySummary(
        total_dispatches=len(rows),
        replay_status_counts={status: status_counts[status] for status in REPLAY_STATUSES if status_counts[status]},
        artifact_presence_counts=artifact_presence_counts,
        metric_claim_level_counts=dict(sorted(metric_counts.items())),
        headline_metric_claim_level_counts=dict(sorted(headline_metric_counts.items())),
        headline_selector_regime_counts=dict(sorted(headline_selector_counts.items())),
        headline_exclusion_counts=dict(sorted(headline_exclusion_counts.items())),
        missing_field_counts=dict(sorted(missing_counts.items())),
        replay_usable_dispatches=len(usable),
        replay_nonusable_dispatches=len(nonusable),
        headline_eligible_dispatches=len(headline_rows),
        headline_excluded_dispatches=len(headline_excluded),
        replay_usable_dispatch_ids=[_dispatch_label(row) for row in usable],
        replay_nonusable_dispatch_ids=[_dispatch_label(row) for row in nonusable],
        headline_eligible_dispatch_ids=[_dispatch_label(row) for row in headline_rows],
        headline_excluded_dispatch_ids=[_dispatch_label(row) for row in headline_excluded],
        core_paper_artifacts=list(CORE_PAPER_ARTIFACTS),
        replay_substrate_artifacts=list(REPLAY_SUBSTRATE_ARTIFACTS),
    )


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _per_dispatch_diagnostic_payload(row: ReplayManifestRow) -> dict[str, Any]:
    return {
        "run_id": row.run_id,
        "dispatch_id": row.dispatch_id,
        "agent_id": row.agent_id,
        "round_id": row.round_id,
        "replay_status": row.replay_status,
        "metric_claim_level": row.metric_claim_level,
        "selector_regime_label": row.selector_regime_label,
        "diagnostic_recompute_status": row.diagnostic_recompute_status,
        "headline_eligible": row.headline_eligible,
        "headline_exclusion_reason": row.headline_exclusion_reason,
        "selected_token_cost": row.selected_token_cost,
        "budget_utilization": row.budget_utilization,
        "observed_proxy_value": row.observed_proxy_value,
        "block_ratio_lcb_b2": row.block_ratio_lcb_b2,
    }


def _pipeline_proxy_alignment(rows: list[ReplayManifestRow]) -> dict[str, Any]:
    headline = [row for row in rows if row.headline_eligible]
    excluded = [row for row in rows if not row.headline_eligible]
    return {
        "total_dispatches": len(rows),
        "headline_denominator": len(headline),
        "excluded_dispatches": len(excluded),
        "excluded_counts": dict(sorted(Counter(row.headline_exclusion_reason for row in excluded).items())),
        "headline_selected_token_cost_mean": _mean(
            [float(row.selected_token_cost) for row in headline if row.selected_token_cost is not None]
        ),
        "headline_budget_utilization_mean": _mean(
            [float(row.budget_utilization) for row in headline if row.budget_utilization is not None]
        ),
        "headline_observed_proxy_value_mean": _mean(
            [float(row.observed_proxy_value) for row in headline if row.observed_proxy_value is not None]
        ),
        "headline_block_ratio_lcb_b2_min": (
            min(float(row.block_ratio_lcb_b2) for row in headline if row.block_ratio_lcb_b2 is not None)
            if any(row.block_ratio_lcb_b2 is not None for row in headline)
            else None
        ),
        "note": "Excluded dispatches are not mixed into headline diagnostics.",
    }


def _metric_claim_level_summary(rows: list[ReplayManifestRow]) -> dict[str, Any]:
    headline = [row for row in rows if row.headline_eligible]
    excluded = [row for row in rows if not row.headline_eligible]
    return {
        "total_dispatches": len(rows),
        "headline_denominator": len(headline),
        "all_counts": dict(sorted(Counter(row.metric_claim_level for row in rows).items())),
        "headline_counts": dict(sorted(Counter(row.metric_claim_level for row in headline).items())),
        "excluded_counts": dict(sorted(Counter(row.headline_exclusion_reason for row in excluded).items())),
    }


def _selector_regime_summary(rows: list[ReplayManifestRow]) -> dict[str, Any]:
    headline = [row for row in rows if row.headline_eligible]
    excluded = [row for row in rows if not row.headline_eligible]
    return {
        "total_dispatches": len(rows),
        "headline_denominator": len(headline),
        "all_counts": dict(sorted(Counter(row.selector_regime_label for row in rows).items())),
        "headline_counts": dict(sorted(Counter(row.selector_regime_label for row in headline).items())),
        "excluded_counts": dict(sorted(Counter(row.headline_exclusion_reason for row in excluded).items())),
    }


def _format_report(summary: dict[str, Any], alignment: dict[str, Any]) -> str:
    lines = [
        "# Phase B Offline Replay Report",
        "",
        "P40 is offline replay / observability evidence only. It does not run live APIs and does not claim measurement validation.",
        "",
        "## Claim Boundary",
        "",
        "- Replay package completeness is not scientific validation.",
        "- Missing human labels or missing kappa prevents `measurement_validated`.",
        "- Contamination failure downgrades claim level to `pilot_only`.",
        "- Stale or missing metric bridge downgrades claim level to `operational_utility_only` or `ambiguous`.",
        "",
        "## Replay Summary",
        "",
        f"- Total dispatches: {summary['total_dispatches']}",
        f"- Headline eligible dispatches: {summary['headline_eligible_dispatches']} / {summary['total_dispatches']}",
        f"- Replay status counts: `{json.dumps(summary['replay_status_counts'], sort_keys=True)}`",
        f"- Metric claim level counts: `{json.dumps(summary['metric_claim_level_counts'], sort_keys=True)}`",
        f"- Headline exclusion counts: `{json.dumps(summary['headline_exclusion_counts'], sort_keys=True)}`",
        "",
        "## Headline Diagnostics",
        "",
        "Excluded dispatches are not mixed into headline diagnostics.",
        f"- Headline denominator: {alignment['headline_denominator']}",
        f"- Mean selected token cost: {alignment['headline_selected_token_cost_mean']}",
        f"- Mean budget utilization: {alignment['headline_budget_utilization_mean']}",
        f"- Mean observed proxy value: {alignment['headline_observed_proxy_value_mean']}",
        f"- Minimum block-ratio LCB b2: {alignment['headline_block_ratio_lcb_b2_min']}",
        "",
    ]
    return "\n".join(lines)


def run_phase_b_replay(*, input_dir: str | Path, output_dir: str | Path) -> dict[str, Any]:
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    bundles = load_replay_artifact_bundles(input_path)
    contamination_status = _contamination_status(input_path)
    manifest_rows: list[ReplayManifestRow] = []
    missing_records: list[MissingFieldRecord] = []
    for bundle in bundles:
        manifest, missing = classify_replay_bundle(bundle, contamination_status=contamination_status)
        manifest_rows.append(manifest)
        missing_records.extend(missing)

    summary = build_replay_summary(manifest_rows, missing_records)
    manifest_payloads = [asdict(row) for row in manifest_rows]
    missing_payloads = [asdict(record) for record in missing_records]
    summary_payload = asdict(summary)
    diagnostics_payloads = [_per_dispatch_diagnostic_payload(row) for row in manifest_rows]
    alignment_payload = _pipeline_proxy_alignment(manifest_rows)
    metric_summary_payload = _metric_claim_level_summary(manifest_rows)
    selector_summary_payload = _selector_regime_summary(manifest_rows)
    replay_status_counts_payload = {
        "replay_status_counts": summary_payload["replay_status_counts"],
        "headline_exclusion_counts": summary_payload["headline_exclusion_counts"],
        "headline_denominator": summary_payload["headline_eligible_dispatches"],
        "total_dispatches": summary_payload["total_dispatches"],
    }
    missing_field_payload = {
        "missing_fields": missing_payloads,
        "missing_field_counts": summary_payload["missing_field_counts"],
    }

    _write_json(output_path / "replay_manifest.json", {"rows": manifest_payloads})
    _write_jsonl(output_path / "replay_manifest.jsonl", manifest_payloads)
    _write_jsonl(output_path / "per_dispatch_diagnostics.jsonl", diagnostics_payloads)
    _write_json(output_path / "missing_field_report.json", missing_field_payload)
    _write_json(output_path / "missing_fields.json", missing_field_payload)
    _write_json(output_path / "pipeline_proxy_alignment.json", alignment_payload)
    _write_json(output_path / "metric_claim_level_summary.json", metric_summary_payload)
    _write_json(output_path / "selector_regime_summary.json", selector_summary_payload)
    _write_json(output_path / "replay_status_counts.json", replay_status_counts_payload)
    _write_json(output_path / "replay_summary.json", summary_payload)
    (output_path / "report.md").write_text(_format_report(summary_payload, alignment_payload), encoding="utf-8")
    return {
        "status": "classified",
        "input_dir": str(input_path),
        "output_dir": str(output_path),
        "manifest_json_path": str(output_path / "replay_manifest.json"),
        "manifest_path": str(output_path / "replay_manifest.jsonl"),
        "per_dispatch_diagnostics_path": str(output_path / "per_dispatch_diagnostics.jsonl"),
        "missing_field_report_path": str(output_path / "missing_field_report.json"),
        "missing_fields_path": str(output_path / "missing_fields.json"),
        "pipeline_proxy_alignment_path": str(output_path / "pipeline_proxy_alignment.json"),
        "metric_claim_level_summary_path": str(output_path / "metric_claim_level_summary.json"),
        "selector_regime_summary_path": str(output_path / "selector_regime_summary.json"),
        "replay_status_counts_path": str(output_path / "replay_status_counts.json"),
        "summary_path": str(output_path / "replay_summary.json"),
        "report_path": str(output_path / "report.md"),
        "summary": summary_payload,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify Phase B offline replay artifact readiness.")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    result = run_phase_b_replay(input_dir=args.input_dir, output_dir=args.output_dir)
    compact = {
        "status": result["status"],
        "total_dispatches": result["summary"]["total_dispatches"],
        "replay_status_counts": result["summary"]["replay_status_counts"],
        "summary_path": result["summary_path"],
    }
    print(json.dumps(compact, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
