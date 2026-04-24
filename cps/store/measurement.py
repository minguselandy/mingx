from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ALLOWED_EVENT_TYPES = {
    "run_started",
    "provider_config_loaded",
    "baseline_scored",
    "full_scored",
    "loo_scored",
    "ordering_scored",
    "delta_lcb_materialized",
    "export_materialized",
    "question_materialized",
    "protocol_deviation",
    "annotation_queue_materialized",
    "annotation_label_ingested",
    "expert_arbitration_ingested",
    "kappa_materialized",
    "candidate_pool_materialized",
    "projection_plan_materialized",
    "budget_witness_materialized",
    "materialized_context_materialized",
    "projection_diagnostics_materialized",
    "synthetic_benchmark_summary_materialized",
}
EVENT_FIELDS = (
    "event_type",
    "event_id",
    "recorded_at_utc",
    "run_id",
    "question_id",
    "hop_depth",
    "provider",
    "backend_id",
    "model_id",
    "model_role",
    "ordering_id",
    "ordering",
    "paragraph_id",
    "full_logp",
    "loo_logp",
    "delta_loo",
    "baseline_logp",
    "manifest_hash",
    "sampling_seed",
    "protocol_version",
    "request_fingerprint",
    "response_status",
    "notes",
    "payload",
)


def events_path_for(store_dir: str | Path) -> Path:
    return Path(store_dir) / "events.jsonl"


def snapshot_path_for(store_dir: str | Path, question_id: str, model_role: str | None = None) -> Path:
    questions_dir = Path(store_dir) / "questions"
    if model_role:
        return questions_dir / model_role / f"{question_id}.json"
    return questions_dir / f"{question_id}.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    lower_value = ordered[lower]
    upper_value = ordered[upper]
    return lower_value + (upper_value - lower_value) * (position - lower)


def append_event(store_dir: str | Path, event: dict[str, Any]) -> dict[str, Any]:
    if event.get("event_type") not in ALLOWED_EVENT_TYPES:
        raise ValueError(f"unsupported event_type: {event.get('event_type')}")

    payload = {field: None for field in EVENT_FIELDS}
    payload.update(event)
    payload["event_id"] = payload["event_id"] or str(uuid.uuid4())
    payload["recorded_at_utc"] = payload["recorded_at_utc"] or _utc_now()

    if payload["event_type"] == "baseline_scored" and payload["baseline_logp"] is None:
        raise ValueError("baseline_scored requires baseline_logp")
    if payload["event_type"] == "full_scored":
        required = ("ordering_id", "ordering", "full_logp")
        missing = [field for field in required if payload[field] is None]
        if missing:
            raise ValueError(f"full_scored missing fields: {', '.join(missing)}")
    if payload["event_type"] in {"loo_scored", "ordering_scored"}:
        required = ("ordering_id", "ordering", "paragraph_id", "full_logp", "loo_logp", "delta_loo")
        missing = [field for field in required if payload[field] is None]
        if missing:
            raise ValueError(f"{payload['event_type']} missing fields: {', '.join(missing)}")

    events_path = events_path_for(store_dir)
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload


def iter_events(store_dir: str | Path) -> Iterator[dict[str, Any]]:
    events_path = events_path_for(store_dir)
    if not events_path.exists():
        return

    with events_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                yield json.loads(stripped)


def rebuild_run_progress(store_dir: str | Path, run_id: str | None = None) -> dict[str, Any]:
    """Rebuild completed work from the append-only event log.

    `events.jsonl` is the source of truth. Any checkpoint or snapshot must be
    derived from this reconstruction, not the other way around.
    """
    progress = {
        "source_of_truth": "event_log",
        "run_id": run_id,
        "baseline_scored_questions": set(),
        "full_scored_units": set(),
        "loo_scored_units": set(),
        "materialized_questions": set(),
        "exported_questions": set(),
    }

    for event in iter_events(store_dir):
        if run_id is not None and event.get("run_id") != run_id:
            continue
        event_type = event["event_type"]
        question_id = event.get("question_id")
        ordering_id = event.get("ordering_id")
        paragraph_id = event.get("paragraph_id")

        if event_type == "baseline_scored":
            progress["baseline_scored_questions"].add(question_id)
        elif event_type == "full_scored":
            progress["full_scored_units"].add((question_id, ordering_id))
        elif event_type in {"loo_scored", "ordering_scored"}:
            progress["loo_scored_units"].add((question_id, ordering_id, paragraph_id))
        elif event_type in {"delta_lcb_materialized", "question_materialized"}:
            progress["materialized_questions"].add(question_id)
        elif event_type == "export_materialized":
            progress["exported_questions"].add(question_id)

    return {
        "source_of_truth": progress["source_of_truth"],
        "run_id": progress["run_id"],
        "baseline_scored_questions": sorted(progress["baseline_scored_questions"]),
        "full_scored_units": sorted(progress["full_scored_units"]),
        "loo_scored_units": sorted(progress["loo_scored_units"]),
        "materialized_questions": sorted(progress["materialized_questions"]),
        "exported_questions": sorted(progress["exported_questions"]),
    }


def materialize_question_snapshot(
    store_dir: str | Path,
    question_id: str,
    model_role: str | None = None,
    lcb_quantile: float = 0.1,
) -> dict[str, Any]:
    question_events = [
        event
        for event in iter_events(store_dir)
        if event["question_id"] == question_id
        and (model_role is None or event.get("model_role") == model_role)
    ]
    baseline_events = [event for event in question_events if event["event_type"] == "baseline_scored"]
    ordering_events = [event for event in question_events if event["event_type"] == "ordering_scored"]
    if not baseline_events:
        raise ValueError(f"no baseline_scored event found for {question_id}")
    if not ordering_events:
        raise ValueError(f"no ordering_scored events found for {question_id}")

    baseline_event = baseline_events[-1]
    ordered_groups: dict[str, dict[str, Any]] = {}
    per_paragraph_deltas: dict[int, list[float]] = {}

    full_events = [event for event in question_events if event["event_type"] == "full_scored"]
    latest_full_by_ordering: dict[str, dict[str, Any]] = {}
    for event in full_events:
        latest_full_by_ordering[str(event["ordering_id"])] = event
    if not latest_full_by_ordering:
        for event in ordering_events:
            latest_full_by_ordering[str(event["ordering_id"])] = event

    latest_ordering_events: dict[tuple[str, int], dict[str, Any]] = {}
    for event in ordering_events:
        ordering_id = str(event["ordering_id"])
        latest_full = latest_full_by_ordering.get(ordering_id)
        if latest_full is None:
            continue
        if tuple(int(item) for item in event.get("ordering") or ()) != tuple(
            int(item) for item in latest_full.get("ordering") or ()
        ):
            continue
        if event.get("run_id") != latest_full.get("run_id"):
            continue
        if event.get("provider") != latest_full.get("provider"):
            continue
        if event.get("backend_id") != latest_full.get("backend_id"):
            continue
        if event.get("model_id") != latest_full.get("model_id"):
            continue
        if event.get("manifest_hash") != latest_full.get("manifest_hash"):
            continue
        latest_ordering_events[(ordering_id, int(event["paragraph_id"]))] = event

    for ordering_id, latest_full in latest_full_by_ordering.items():
        group = ordered_groups.setdefault(
            ordering_id,
            {
                "ordering_id": ordering_id,
                "ordering": list(latest_full["ordering"]),
                "paragraphs": [],
            },
        )
        paragraph_ids = [int(item) for item in latest_full["ordering"]]
        for paragraph_id in paragraph_ids:
            event = latest_ordering_events.get((ordering_id, paragraph_id))
            if event is None:
                continue
            group["paragraphs"].append(
                {
                    "paragraph_id": paragraph_id,
                    "full_logp": float(event["full_logp"]),
                    "loo_logp": float(event["loo_logp"]),
                    "delta_loo": float(event["delta_loo"]),
                }
            )
            per_paragraph_deltas.setdefault(paragraph_id, []).append(float(event["delta_loo"]))

    orderings = list(ordered_groups.values())
    for ordering in orderings:
        ordering["paragraphs"].sort(key=lambda paragraph: paragraph["paragraph_id"])

    snapshot = {
        "question_id": question_id,
        "hop_depth": baseline_event["hop_depth"],
        "V_model": baseline_event["model_id"],
        "model_role": baseline_event.get("model_role"),
        "provider": baseline_event.get("provider"),
        "backend_id": baseline_event.get("backend_id"),
        "baseline_logp": float(baseline_event["baseline_logp"]),
        "orderings": orderings,
        "delta_loo_LCB": [
            {"paragraph_id": paragraph_id, "delta_loo": _quantile(values, lcb_quantile)}
            for paragraph_id, values in sorted(per_paragraph_deltas.items())
        ],
    }

    snapshot_path = snapshot_path_for(store_dir, question_id, model_role=baseline_event.get("model_role"))
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    append_event(
        store_dir,
        {
            "event_type": "question_materialized",
            "run_id": baseline_event["run_id"],
            "question_id": question_id,
            "hop_depth": baseline_event["hop_depth"],
            "provider": baseline_event.get("provider"),
            "backend_id": baseline_event.get("backend_id"),
            "model_id": baseline_event["model_id"],
            "model_role": baseline_event.get("model_role"),
            "ordering_id": None,
            "ordering": None,
            "paragraph_id": None,
            "full_logp": None,
            "loo_logp": None,
            "delta_loo": None,
            "baseline_logp": baseline_event["baseline_logp"],
            "manifest_hash": baseline_event["manifest_hash"],
            "sampling_seed": baseline_event["sampling_seed"],
            "protocol_version": baseline_event["protocol_version"],
            "request_fingerprint": None,
            "response_status": "materialized",
            "notes": str(snapshot_path),
            "payload": {},
        },
    )
    return snapshot
