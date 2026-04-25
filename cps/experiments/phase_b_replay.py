from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from cps.experiments.decision import derive_metric_claim_level


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
    missing_field_counts: dict[str, int]
    replay_usable_dispatches: int
    replay_nonusable_dispatches: int
    replay_usable_dispatch_ids: list[str]
    replay_nonusable_dispatch_ids: list[str]
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


def classify_replay_bundle(bundle: ReplayArtifactBundle) -> tuple[ReplayManifestRow, list[MissingFieldRecord]]:
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
            severity="warning",
            required_for="stable_grouping",
            reason="run_id is missing; bundle was grouped by remaining dispatch identity fields",
        )
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
    metric_claim_level = derive_metric_claim_level(bundle.metric_bridge_witness)
    bridge_status, replay_claim_scope = _bridge_scope(bundle.metric_bridge_witness, metric_claim_level)

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
    elif not metric_bridge_witness_present or metric_claim_level == "ambiguous" or not cached_utility_records_present:
        replay_status = "replay_partial"
    elif (
        not projection_plan_present
        or not budget_witness_present
        or not materialized_context_present
        or not excluded_ids_present
        or not materialization_order_present
    ):
        replay_status = "pilot_degraded"
    else:
        replay_status = "replay_usable"

    notes = (
        "CandidatePool is replay substrate, not one of the four core paper artifacts. "
        "Diagnostic recomputation is intentionally deferred."
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
    return ReplaySummary(
        total_dispatches=len(rows),
        replay_status_counts={status: status_counts[status] for status in REPLAY_STATUSES if status_counts[status]},
        artifact_presence_counts=artifact_presence_counts,
        metric_claim_level_counts=dict(sorted(metric_counts.items())),
        missing_field_counts=dict(sorted(missing_counts.items())),
        replay_usable_dispatches=len(usable),
        replay_nonusable_dispatches=len(nonusable),
        replay_usable_dispatch_ids=[_dispatch_label(row) for row in usable],
        replay_nonusable_dispatch_ids=[_dispatch_label(row) for row in nonusable],
        core_paper_artifacts=list(CORE_PAPER_ARTIFACTS),
        replay_substrate_artifacts=list(REPLAY_SUBSTRATE_ARTIFACTS),
    )


def run_phase_b_replay(*, input_dir: str | Path, output_dir: str | Path) -> dict[str, Any]:
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    bundles = load_replay_artifact_bundles(input_path)
    manifest_rows: list[ReplayManifestRow] = []
    missing_records: list[MissingFieldRecord] = []
    for bundle in bundles:
        manifest, missing = classify_replay_bundle(bundle)
        manifest_rows.append(manifest)
        missing_records.extend(missing)

    summary = build_replay_summary(manifest_rows, missing_records)
    manifest_payloads = [asdict(row) for row in manifest_rows]
    missing_payloads = [asdict(record) for record in missing_records]
    summary_payload = asdict(summary)

    _write_jsonl(output_path / "replay_manifest.jsonl", manifest_payloads)
    _write_json(
        output_path / "missing_fields.json",
        {
            "missing_fields": missing_payloads,
            "missing_field_counts": summary_payload["missing_field_counts"],
        },
    )
    _write_json(output_path / "replay_summary.json", summary_payload)
    return {
        "status": "classified",
        "input_dir": str(input_path),
        "output_dir": str(output_path),
        "manifest_path": str(output_path / "replay_manifest.jsonl"),
        "missing_fields_path": str(output_path / "missing_fields.json"),
        "summary_path": str(output_path / "replay_summary.json"),
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
