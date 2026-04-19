from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cps.analysis.exports import question_export_manifest_path
from cps.store.measurement import iter_events, snapshot_path_for


@dataclass(frozen=True)
class MeasurementUnitSpec:
    question_id: str
    hop_depth: str
    model_role: str
    provider: str
    backend_id: str
    model_id: str
    manifest_hash: str
    ordering_ids: tuple[str, ...]
    paragraph_ids: tuple[int, ...]
    ordering_items: tuple[tuple[str, tuple[int, ...]], ...]


def rebuild_measurement_unit_states(
    *,
    store_dir: str | Path,
    export_dir: str | Path,
    unit_specs: list[MeasurementUnitSpec],
) -> dict[tuple[str, str], dict]:
    export_root = Path(export_dir)
    states: dict[tuple[str, str], dict] = {}

    for spec in unit_specs:
        key = (spec.question_id, spec.model_role)
        states[key] = {
            "question_id": spec.question_id,
            "hop_depth": spec.hop_depth,
            "model_role": spec.model_role,
            "provider": spec.provider,
            "backend_id": spec.backend_id,
            "model_id": spec.model_id,
            "manifest_hash": spec.manifest_hash,
            "ordering_ids": tuple(spec.ordering_ids),
            "paragraph_ids": tuple(spec.paragraph_ids),
            "ordering_map": {ordering_id: ordering for ordering_id, ordering in spec.ordering_items},
            "baseline_present": False,
            "full_scored_orderings": set(),
            "loo_scored_units": set(),
            "ordering_scored_units": set(),
            "delta_materialized_present": False,
            "question_materialized_present": False,
            "export_materialized_present": False,
            "snapshot_path": snapshot_path_for(store_dir, spec.question_id, spec.model_role),
            "export_manifest_path": question_export_manifest_path(
                export_root,
                spec.model_role,
                spec.question_id,
            ),
        }

    for event in iter_events(store_dir):
        key = (event.get("question_id"), event.get("model_role"))
        if key not in states:
            continue
        state = states[key]
        if event.get("provider") != state["provider"]:
            continue
        if event.get("backend_id") != state["backend_id"]:
            continue
        if event.get("model_id") != state["model_id"]:
            continue
        if event.get("manifest_hash") != state["manifest_hash"] and event["event_type"] != "provider_config_loaded":
            continue
        event_type = event["event_type"]
        ordering_id = event.get("ordering_id")
        paragraph_id = event.get("paragraph_id")
        expected_ordering = state["ordering_map"].get(str(ordering_id)) if ordering_id is not None else None
        observed_ordering = tuple(int(item) for item in event.get("ordering") or ())

        if event_type == "baseline_scored":
            state["baseline_present"] = True
        elif event_type == "full_scored" and ordering_id is not None and expected_ordering == observed_ordering:
            state["full_scored_orderings"].add(str(ordering_id))
        elif (
            event_type == "loo_scored"
            and ordering_id is not None
            and paragraph_id is not None
            and expected_ordering == observed_ordering
        ):
            state["loo_scored_units"].add((str(ordering_id), int(paragraph_id)))
        elif (
            event_type == "ordering_scored"
            and ordering_id is not None
            and paragraph_id is not None
            and expected_ordering == observed_ordering
        ):
            state["ordering_scored_units"].add((str(ordering_id), int(paragraph_id)))
        elif event_type == "delta_lcb_materialized":
            state["delta_materialized_present"] = True
        elif event_type == "question_materialized":
            state["question_materialized_present"] = True
        elif event_type == "export_materialized":
            state["export_materialized_present"] = True

    rebuilt: dict[tuple[str, str], dict] = {}
    for key, state in states.items():
        expected_pairs = {
            (ordering_id, paragraph_id)
            for ordering_id in state["ordering_ids"]
            for paragraph_id in state["paragraph_ids"]
        }
        snapshot_exists = state["snapshot_path"].exists()
        export_exists = state["export_manifest_path"].exists()
        inference_complete = (
            state["baseline_present"]
            and set(state["ordering_ids"]).issubset(state["full_scored_orderings"])
            and expected_pairs.issubset(state["loo_scored_units"])
            and expected_pairs.issubset(state["ordering_scored_units"])
        )
        completed = (
            inference_complete
            and state["delta_materialized_present"]
            and state["question_materialized_present"]
            and snapshot_exists
            and state["export_materialized_present"]
            and export_exists
        )
        rebuilt[key] = {
            **state,
            "full_scored_orderings": sorted(state["full_scored_orderings"]),
            "loo_scored_units": sorted(state["loo_scored_units"]),
            "ordering_scored_units": sorted(state["ordering_scored_units"]),
            "snapshot_exists": snapshot_exists,
            "export_exists": export_exists,
            "inference_complete": inference_complete,
            "needs_derivation": inference_complete and not completed,
            "completed": completed,
        }

    return rebuilt
