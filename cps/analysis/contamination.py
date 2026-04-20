from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from cps.analysis.exports import write_json
from cps.store.measurement import iter_events


CONTAMINATION_THRESHOLD_LOGP = math.log(0.5)
PROVIDER_FAMILY = "qwen3"


def _select_latest_baselines(store_dir: str | Path) -> list[dict[str, Any]]:
    latest_by_question_and_role: dict[tuple[str, str], dict[str, Any]] = {}
    for event in iter_events(store_dir):
        if event.get("event_type") != "baseline_scored":
            continue
        question_id = event.get("question_id")
        model_role = event.get("model_role") or "unknown"
        if question_id is None:
            continue
        latest_by_question_and_role[(str(question_id), str(model_role))] = event

    selected_by_question: dict[str, dict[str, Any]] = {}
    for (question_id, _model_role), event in latest_by_question_and_role.items():
        existing = selected_by_question.get(question_id)
        if existing is None:
            selected_by_question[question_id] = event
            continue
        existing_role = str(existing.get("model_role") or "")
        current_role = str(event.get("model_role") or "")
        if existing_role != "frontier" and current_role == "frontier":
            selected_by_question[question_id] = event
    return list(selected_by_question.values())


def run_contamination_analysis(
    *,
    measurement_dir: str | Path,
    export_dir: str | Path,
) -> dict[str, Any]:
    baseline_events = _select_latest_baselines(measurement_dir)
    export_path = Path(export_dir) / "contamination_diagnostics.json"
    if not baseline_events:
        payload = {
            "status": "pending_measurement_consumption",
            "provider_family": PROVIDER_FAMILY,
            "threshold_logp": CONTAMINATION_THRESHOLD_LOGP,
            "threshold_probability": 0.5,
            "question_count": 0,
            "above_threshold_count": 0,
            "above_threshold_fraction": 0.0,
            "per_hop": {},
            "question_ids_above_threshold": [],
            "gate_decision": "warning",
            "reason": "no baseline_scored events available",
        }
        return {
            "status": payload["status"],
            "path": str(write_json(export_path, payload)),
            "payload": payload,
        }

    per_hop_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    above_threshold_question_ids: list[str] = []
    question_rows: list[dict[str, Any]] = []
    for event in baseline_events:
        question_id = str(event["question_id"])
        hop_depth = str(event["hop_depth"])
        baseline_logp = float(event["baseline_logp"])
        above_threshold = baseline_logp > CONTAMINATION_THRESHOLD_LOGP
        if above_threshold:
            above_threshold_question_ids.append(question_id)
        row = {
            "question_id": question_id,
            "hop_depth": hop_depth,
            "baseline_logp": baseline_logp,
            "model_role": event.get("model_role"),
            "model_id": event.get("model_id"),
            "above_threshold": above_threshold,
        }
        question_rows.append(row)
        per_hop_rows[hop_depth].append(row)

    question_count = len(question_rows)
    above_threshold_count = len(above_threshold_question_ids)
    above_threshold_fraction = above_threshold_count / question_count if question_count else 0.0
    gate_decision = "fail" if above_threshold_fraction > 0.2 else "pass"

    payload = {
        "status": "computed",
        "provider_family": PROVIDER_FAMILY,
        "threshold_logp": CONTAMINATION_THRESHOLD_LOGP,
        "threshold_probability": 0.5,
        "question_count": question_count,
        "above_threshold_count": above_threshold_count,
        "above_threshold_fraction": above_threshold_fraction,
        "per_hop": {
            hop_depth: {
                "question_count": len(rows),
                "above_threshold_count": sum(1 for row in rows if row["above_threshold"]),
                "above_threshold_fraction": (
                    sum(1 for row in rows if row["above_threshold"]) / len(rows) if rows else 0.0
                ),
                "question_ids_above_threshold": sorted(
                    row["question_id"] for row in rows if row["above_threshold"]
                ),
            }
            for hop_depth, rows in sorted(per_hop_rows.items())
        },
        "question_ids_above_threshold": sorted(above_threshold_question_ids),
        "baseline_rows": sorted(question_rows, key=lambda row: (row["hop_depth"], row["question_id"])),
        "gate_decision": gate_decision,
    }
    return {
        "status": payload["status"],
        "path": str(write_json(export_path, payload)),
        "payload": payload,
    }
