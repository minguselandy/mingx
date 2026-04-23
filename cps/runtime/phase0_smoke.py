from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cps.data.manifest import load_manifest, validate_manifest
from cps.store.measurement import (
    append_event,
    events_path_for,
    materialize_question_snapshot,
    snapshot_path_for,
)

PHASE0_SMOKE_MODEL_ID = "qwen3.6-flash"


def _build_synthetic_ordering_events(bundle, question, run_id: str) -> list[dict[str, Any]]:
    paragraph_ids = [paragraph.paragraph_id for paragraph in question.paragraphs[:2]]
    canonical = paragraph_ids + [paragraph.paragraph_id for paragraph in question.paragraphs[2:3]]
    permuted = list(reversed(paragraph_ids)) + [paragraph.paragraph_id for paragraph in question.paragraphs[2:3]]
    shared = {
        "run_id": run_id,
        "question_id": question.question_id,
        "hop_depth": question.hop_depth,
        "model_id": PHASE0_SMOKE_MODEL_ID,
        "baseline_logp": -2.5,
        "manifest_hash": bundle.manifest_hash,
        "sampling_seed": bundle.sampling_config["seed"],
        "protocol_version": bundle.schema_version,
        "notes": "synthetic smoke measurement",
    }

    return [
        {
            "event_type": "ordering_scored",
            "ordering_id": "canonical",
            "ordering": canonical,
            "paragraph_id": paragraph_ids[0],
            "full_logp": -1.2,
            "loo_logp": -1.6,
            "delta_loo": 0.4,
            **shared,
        },
        {
            "event_type": "ordering_scored",
            "ordering_id": "canonical",
            "ordering": canonical,
            "paragraph_id": paragraph_ids[1],
            "full_logp": -1.2,
            "loo_logp": -1.3,
            "delta_loo": 0.1,
            **shared,
        },
        {
            "event_type": "ordering_scored",
            "ordering_id": "permuted",
            "ordering": permuted,
            "paragraph_id": paragraph_ids[0],
            "full_logp": -1.15,
            "loo_logp": -1.5,
            "delta_loo": 0.35,
            **shared,
        },
        {
            "event_type": "ordering_scored",
            "ordering_id": "permuted",
            "ordering": permuted,
            "paragraph_id": paragraph_ids[1],
            "full_logp": -1.15,
            "loo_logp": -1.22,
            "delta_loo": 0.07,
            **shared,
        },
    ]


def run_phase0_smoke(
    manifest_path: str | Path,
    hash_path: str | Path,
    store_dir: str | Path,
    config_path: str | Path = "phase0.yaml",
) -> dict[str, Any]:
    bundle = load_manifest(manifest_path)
    validation = validate_manifest(bundle, hashes_path=hash_path, config_path=config_path)
    if not validation["ok"]:
        return {"status": "red", "validation": validation}

    run_id = f"smoke-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    question = bundle.sample[0]
    events_written = 0

    append_event(
        store_dir,
        {
            "event_type": "run_started",
            "run_id": run_id,
            "question_id": question.question_id,
            "hop_depth": question.hop_depth,
            "model_id": PHASE0_SMOKE_MODEL_ID,
            "ordering_id": None,
            "ordering": None,
            "paragraph_id": None,
            "full_logp": None,
            "loo_logp": None,
            "delta_loo": None,
            "baseline_logp": -2.5,
            "manifest_hash": bundle.manifest_hash,
            "sampling_seed": bundle.sampling_config["seed"],
            "protocol_version": bundle.schema_version,
            "notes": "phase0 smoke run started",
        },
    )
    events_written += 1

    append_event(
        store_dir,
        {
            "event_type": "baseline_scored",
            "run_id": run_id,
            "question_id": question.question_id,
            "hop_depth": question.hop_depth,
            "model_id": PHASE0_SMOKE_MODEL_ID,
            "ordering_id": None,
            "ordering": None,
            "paragraph_id": None,
            "full_logp": None,
            "loo_logp": None,
            "delta_loo": None,
            "baseline_logp": -2.5,
            "manifest_hash": bundle.manifest_hash,
            "sampling_seed": bundle.sampling_config["seed"],
            "protocol_version": bundle.schema_version,
            "notes": "synthetic baseline score",
        },
    )
    events_written += 1

    for event in _build_synthetic_ordering_events(bundle, question, run_id):
        append_event(store_dir, event)
        events_written += 1

    snapshot = materialize_question_snapshot(store_dir, question.question_id)
    events_written += 1
    events_path = events_path_for(store_dir)
    snapshot_path = snapshot_path_for(store_dir, question.question_id)

    return {
        "status": "green",
        "run_id": run_id,
        "question_id": question.question_id,
        "events_written": events_written,
        "events_path": str(events_path),
        "snapshot_path": str(snapshot_path),
        "snapshot": snapshot,
        "validation": validation,
    }
