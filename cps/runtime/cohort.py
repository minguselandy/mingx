from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from cps.analysis.bridge import run_bridge_analysis
from cps.analysis.contamination import run_contamination_analysis
from cps.analysis.exports import (
    ensure_directories,
    export_delta_lcb,
    write_json,
)
from cps.analysis.reliability import compute_reliability_from_events
from cps.data.manifest import ManifestQuestion, load_manifest, validate_manifest
from cps.providers.dashscope import DashScopeChatBackend
from cps.runtime.annotation import (
    annotation_status_from_files,
    ingest_annotation_labels,
    materialize_annotation_artifacts,
)
from cps.runtime.calibration import build_calibration_manifest
from cps.runtime.config import load_phase1_context
from cps.runtime.retrieval import build_retrieval_dry_run
from cps.scoring.backends import MockScoringBackend
from cps.scoring.delta_loo import (
    append_delta_materialized_event,
    compute_question_delta_loo,
    limit_question_for_smoke,
)
from cps.scoring.orderings import build_orderings
from cps.store.measurement import append_event, events_path_for, materialize_question_snapshot
from cps.store.progress import MeasurementUnitSpec, rebuild_measurement_unit_states


def _resolve_plan_path(path: str | Path) -> Path:
    return Path(path).resolve()


def _resolve_from_plan(plan: dict, key: str, plan_path: Path, root_dir: Path) -> Path:
    candidate = Path(plan[key])
    if candidate.is_absolute():
        return candidate.resolve()

    local_candidate = (plan_path.parent / candidate).resolve()
    if local_candidate.exists():
        return local_candidate
    return (root_dir / candidate).resolve()


def _build_question_lookup(bundle) -> dict[str, ManifestQuestion]:
    return {question.question_id: question for question in bundle.sample}


def _resolve_question_ids(raw_value, calibration_question_ids: list[str], bundle) -> list[str]:
    if raw_value == "all":
        return [question.question_id for question in bundle.sample]
    if raw_value == "calibration_manifest":
        return list(calibration_question_ids)
    if isinstance(raw_value, list):
        return [str(item) for item in raw_value]
    raise ValueError(f"Unsupported question selection: {raw_value!r}")


def _build_backend(context, backend_name: str, model_role: str):
    if backend_name == "mock":
        return MockScoringBackend(model_id=context.models[model_role].model)
    if backend_name == "live":
        return DashScopeChatBackend(context=context, model_role=model_role)
    raise ValueError(f"Unsupported backend: {backend_name}")


def _calibration_per_hop_count(plan: dict) -> int:
    calibration_block = dict(plan.get("calibration") or {})
    return int(calibration_block.get("per_hop_count", 10))


def _resolve_scope_mode(plan: dict) -> str:
    explicit = str(plan.get("scope_mode") or "").strip()
    if explicit:
        return explicit
    if (
        plan.get("question_paragraph_limit") is not None
        or _calibration_per_hop_count(plan) != 10
        or plan.get("small_full_n", {}).get("questions") != "all"
        or plan.get("frontier_calibration", {}).get("questions") != "calibration_manifest"
    ):
        return "pilot_reduced_scope"
    return "protocol_full"


def _pipeline_status(
    *,
    blocked: bool,
    bridge_status: str,
    annotation_status: str,
    model_roles: dict[str, dict[str, int]],
) -> str:
    if blocked:
        return "blocked"
    if any(role["incomplete"] for role in model_roles.values()) or bridge_status != "computed":
        return "incomplete"
    if annotation_status == "awaiting_labels":
        return "awaiting_annotation"
    return "pipeline_validated"


def _measurement_status(
    *,
    scope_mode: str,
    contamination_gate_decision: str,
    annotation_mode: str,
    kappa_status: str,
) -> str:
    if scope_mode == "pilot_reduced_scope":
        return "pilot_only"
    if contamination_gate_decision != "pass":
        return "awaiting_contamination_check"
    if annotation_mode != "human_labels" or kappa_status != "computed":
        return "awaiting_real_annotation"
    return "measurement_validated"


def _blocked_questions_path(calibration_manifest_path: Path) -> Path:
    return calibration_manifest_path.parent / "blocked_questions.json"


def _read_blocked_question_ids(blocked_questions_path: Path) -> list[str]:
    if not blocked_questions_path.exists():
        return []
    payload = json.loads(blocked_questions_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        values = payload.get("blocked_question_ids") or ()
    elif isinstance(payload, list):
        values = payload
    else:
        values = ()
    return sorted({str(question_id) for question_id in values})


def _write_blocked_question_ids(blocked_questions_path: Path, blocked_question_ids: list[str]) -> Path:
    return write_json(
        blocked_questions_path,
        {
            "blocked_question_ids": sorted({str(question_id) for question_id in blocked_question_ids}),
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "reason_code": "data_inspection_failed",
            "replacement_policy": "same_hop_next_rank_on_resume_v1",
        },
    )


def _is_data_inspection_failed(exc: Exception) -> bool:
    return "data_inspection_failed" in str(exc)


def _append_provider_loaded_event(*, store_dir: Path, context, backend, model_role: str, run_id: str) -> None:
    append_event(
        store_dir,
        {
            "event_type": "provider_config_loaded",
            "run_id": run_id,
            "question_id": None,
            "hop_depth": None,
            "provider": context.provider.name,
            "backend_id": backend.backend_id,
            "model_id": backend.model_id,
            "model_role": model_role,
            "ordering_id": None,
            "ordering": None,
            "paragraph_id": None,
            "baseline_logp": None,
            "full_logp": None,
            "loo_logp": None,
            "delta_loo": None,
            "manifest_hash": None,
            "sampling_seed": context.experiment["seed"],
            "protocol_version": context.experiment["protocol_version"],
            "request_fingerprint": None,
            "response_status": "loaded",
            "notes": "provider config loaded",
            "payload": {
                "base_url": context.provider.base_url,
                "backend_name": backend.backend_id,
            },
        },
    )


def _append_export_event(
    *,
    store_dir: Path,
    context,
    backend,
    model_role: str,
    run_id: str,
    question: ManifestQuestion,
    manifest_hash: str,
    export_paths: dict[str, str],
) -> None:
    append_event(
        store_dir,
        {
            "event_type": "export_materialized",
            "run_id": run_id,
            "question_id": question.question_id,
            "hop_depth": question.hop_depth,
            "provider": context.provider.name,
            "backend_id": backend.backend_id,
            "model_id": backend.model_id,
            "model_role": model_role,
            "ordering_id": None,
            "ordering": None,
            "paragraph_id": None,
            "baseline_logp": None,
            "full_logp": None,
            "loo_logp": None,
            "delta_loo": None,
            "manifest_hash": manifest_hash,
            "sampling_seed": context.experiment["seed"],
            "protocol_version": context.experiment["protocol_version"],
            "request_fingerprint": None,
            "response_status": "exported",
            "notes": "phase1 cohort exports ready",
            "payload": export_paths,
        },
    )


def _append_protocol_deviation_event(
    *,
    store_dir: Path,
    context,
    backend,
    model_role: str,
    run_id: str,
    original_question: ManifestQuestion,
    limited_question: ManifestQuestion,
) -> None:
    append_event(
        store_dir,
        {
            "event_type": "protocol_deviation",
            "run_id": run_id,
            "question_id": limited_question.question_id,
            "hop_depth": limited_question.hop_depth,
            "provider": context.provider.name,
            "backend_id": backend.backend_id,
            "model_id": backend.model_id,
            "model_role": model_role,
            "ordering_id": None,
            "ordering": None,
            "paragraph_id": None,
            "baseline_logp": None,
            "full_logp": None,
            "loo_logp": None,
            "delta_loo": None,
            "manifest_hash": None,
            "sampling_seed": context.experiment["seed"],
            "protocol_version": context.experiment["protocol_version"],
            "request_fingerprint": None,
            "response_status": "deviation",
            "notes": "cohort run uses a truncated paragraph subset for cost-controlled replay",
            "payload": {
                "original_paragraph_count": original_question.paragraph_count,
                "cohort_paragraph_count": limited_question.paragraph_count,
            },
        },
    )


def _append_blocked_question_event(
    *,
    store_dir: Path,
    context,
    backend,
    model_role: str,
    run_id: str,
    question: ManifestQuestion,
    manifest_hash: str,
    blocked_questions_path: Path,
    error_message: str,
) -> None:
    append_event(
        store_dir,
        {
            "event_type": "protocol_deviation",
            "run_id": run_id,
            "question_id": question.question_id,
            "hop_depth": question.hop_depth,
            "provider": context.provider.name,
            "backend_id": backend.backend_id,
            "model_id": backend.model_id,
            "model_role": model_role,
            "ordering_id": None,
            "ordering": None,
            "paragraph_id": None,
            "baseline_logp": None,
            "full_logp": None,
            "loo_logp": None,
            "delta_loo": None,
            "manifest_hash": manifest_hash,
            "sampling_seed": context.experiment["seed"],
            "protocol_version": context.experiment["protocol_version"],
            "request_fingerprint": None,
            "response_status": "blocked",
            "notes": "question blocked by provider content inspection; rerun will replace from same-hop ranking",
            "payload": {
                "error_code": "data_inspection_failed",
                "error_message": error_message,
                "blocked_questions_path": str(blocked_questions_path),
                "replacement_policy": "same_hop_next_rank_on_resume_v1",
            },
        },
    )


def _append_annotation_queue_event(
    *,
    store_dir: Path,
    context,
    run_id: str,
    annotation_report: dict[str, object],
) -> None:
    append_event(
        store_dir,
        {
            "event_type": "annotation_queue_materialized",
            "run_id": run_id,
            "question_id": None,
            "hop_depth": None,
            "provider": context.provider.name,
            "backend_id": None,
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
            "sampling_seed": context.experiment["seed"],
            "protocol_version": context.experiment["protocol_version"],
            "request_fingerprint": None,
            "response_status": "materialized",
            "notes": str(annotation_report["annotation_manifest_path"]),
            "payload": {
                "annotation_manifest_hash": annotation_report["annotation_manifest_hash"],
                "annotation_manifest_path": annotation_report["annotation_manifest_path"],
                "annotation_queue_path": annotation_report["annotation_queue_path"],
                "annotation_items_path": annotation_report["annotation_items_path"],
                "annotation_readme_path": annotation_report["annotation_readme_path"],
                "queue_count": annotation_report["queue_count"],
                "flagged_count": annotation_report["flagged_count"],
                "face_validity_count": annotation_report["face_validity_count"],
            },
        },
    )


def _write_annotation_status(
    *,
    export_dir: Path,
    annotation_report: dict[str, object],
    annotation_file_status: dict[str, object],
) -> Path:
    return write_json(
        export_dir / "annotations" / "annotation_status.json",
        {
            "status": annotation_file_status["status"],
            "annotation_mode": annotation_file_status["annotation_mode"],
            "annotation_manifest_hash": annotation_report["annotation_manifest_hash"],
            "annotation_manifest_path": annotation_report["annotation_manifest_path"],
            "annotation_queue_path": annotation_report["annotation_queue_path"],
            "annotation_items_path": annotation_report["annotation_items_path"],
            "annotation_readme_path": annotation_report["annotation_readme_path"],
            "queue_count": annotation_report["queue_count"],
            "flagged_count": annotation_report["flagged_count"],
            "face_validity_count": annotation_report["face_validity_count"],
            "completion": annotation_file_status["completion"],
        },
    )


def _finalize_variance_bias_budget(
    *,
    variance_bias_budget_path: str | Path,
    kappa_summary_path: str | Path,
) -> Path:
    variance_path = Path(variance_bias_budget_path)
    variance_payload = json.loads(variance_path.read_text(encoding="utf-8"))
    kappa_payload = json.loads(Path(kappa_summary_path).read_text(encoding="utf-8"))

    variance_payload["annotation_summary"] = {
        "kappa_summary_path": str(Path(kappa_summary_path).resolve()),
        "annotation_mode": kappa_payload.get("annotation_mode"),
        "tier_classification": kappa_payload["tier_classification"],
        "threshold": kappa_payload["threshold"],
    }
    for hop_depth, hop_payload in variance_payload.get("per_hop", {}).items():
        hop_payload["annotation_reliability"] = {
            "kappa_primary": kappa_payload["per_hop"].get(hop_depth, {}).get("kappa_primary"),
            "kappa_primary_expert": kappa_payload["per_hop"].get(hop_depth, {}).get("kappa_primary_expert"),
            "kappa_automated_expert": kappa_payload["per_hop"].get(hop_depth, {}).get("kappa_automated_expert"),
        }
    return write_json(variance_path, variance_payload)


def _build_unit_specs(*, questions: list[ManifestQuestion], model_role: str, context, backend, manifest_hash: str, k_lcb: int) -> tuple[list[MeasurementUnitSpec], dict[tuple[str, str], list]]:
    specs: list[MeasurementUnitSpec] = []
    orderings_by_unit: dict[tuple[str, str], list] = {}
    for question in questions:
        orderings = build_orderings(
            question.question_id,
            [paragraph.paragraph_id for paragraph in question.paragraphs],
            k_lcb=k_lcb,
            canonical_ordering_id=context.scoring.canonical_ordering_id,
            seed=int(context.experiment["seed"]),
        )
        key = (question.question_id, model_role)
        orderings_by_unit[key] = orderings
        specs.append(
            MeasurementUnitSpec(
                question_id=question.question_id,
                hop_depth=question.hop_depth,
                model_role=model_role,
                provider=context.provider.name,
                backend_id=backend.backend_id,
                model_id=backend.model_id,
                manifest_hash=manifest_hash,
                ordering_ids=tuple(ordering.ordering_id for ordering in orderings),
                paragraph_ids=tuple(paragraph.paragraph_id for paragraph in question.paragraphs),
                ordering_items=tuple(
                    (ordering.ordering_id, tuple(ordering.paragraph_ids)) for ordering in orderings
                ),
            )
        )
    return specs, orderings_by_unit


def run_phase1_cohort(
    *,
    backend_name: str,
    cohort_plan_path: str | Path = "configs/runs/cohort.json",
    env_path: str | Path | None = None,
) -> dict:
    plan_path = _resolve_plan_path(cohort_plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    scope_mode = _resolve_scope_mode(plan)
    context = load_phase1_context(
        phase1_config_path=plan.get("phase1_config_path", "phase1.yaml"),
        run_plan_path=plan_path,
        env_path=env_path,
    )
    manifest_path = _resolve_from_plan(plan, "manifest_path", plan_path, context.root_dir)
    hash_path = _resolve_from_plan(plan, "hash_path", plan_path, context.root_dir)
    calibration_manifest_path = _resolve_from_plan(
        plan,
        "calibration_manifest_path",
        plan_path,
        context.root_dir,
    )

    bundle = load_manifest(manifest_path)
    validation = validate_manifest(bundle, hashes_path=hash_path, config_path="phase0.yaml")
    if not validation["ok"]:
        return {"status": "red", "validation": validation}
    if context.scoring.variance_source != "paragraph_order_permutation_only":
        raise ValueError("Phase 1 cohort runner only supports paragraph-order permutation variance")
    if int(plan["scoring"]["k_lcb"]) != context.scoring.permutation_count:
        raise ValueError("cohort plan k_lcb must match phase1 permutation_count")
    if float(plan["scoring"].get("lcb_quantile", 0.1)) != 0.1:
        raise ValueError("Phase 1 cohort runner currently locks lcb_quantile to 0.1")

    ensure_directories(
        context.storage.measurement_dir,
        context.storage.export_dir,
        context.storage.checkpoint_dir,
        context.storage.cache_dir,
    )
    blocked_questions_path = _blocked_questions_path(calibration_manifest_path)
    blocked_question_ids = _read_blocked_question_ids(blocked_questions_path)

    calibration_manifest = build_calibration_manifest(
        bundle,
        calibration_manifest_path,
        seed=int(context.experiment["seed"]),
        per_hop_count=_calibration_per_hop_count(plan),
        exclude_question_ids=tuple(blocked_question_ids),
    )
    calibration_question_ids = [
        entry["question_id"] for entry in calibration_manifest["selected_questions"]
    ]
    question_lookup = _build_question_lookup(bundle)

    small_question_ids = _resolve_question_ids(
        plan["small_full_n"]["questions"],
        calibration_question_ids,
        bundle,
    )
    frontier_question_ids = _resolve_question_ids(
        plan["frontier_calibration"]["questions"],
        calibration_question_ids,
        bundle,
    )
    paragraph_limit = plan.get("question_paragraph_limit")
    small_questions = [
        limit_question_for_smoke(question_lookup[question_id], paragraph_limit)
        for question_id in small_question_ids
    ]
    frontier_questions = [
        limit_question_for_smoke(question_lookup[question_id], paragraph_limit)
        for question_id in frontier_question_ids
    ]
    original_questions_by_key = {
        (question_id, "small"): question_lookup[question_id] for question_id in small_question_ids
    }
    original_questions_by_key.update(
        {(question_id, "frontier"): question_lookup[question_id] for question_id in frontier_question_ids}
    )

    unique_questions = {
        question.question_id: question for question in [*small_questions, *frontier_questions]
    }
    retrieval_dry_run = [
        {
            "question_id": question.question_id,
            "hop_depth": question.hop_depth,
            "results": build_retrieval_dry_run(question, context.scoring.top_k_values),
        }
        for question in unique_questions.values()
    ]
    retrieval_path = write_json(
        context.storage.export_dir / "retrieval_dry_run.json",
        retrieval_dry_run,
    )

    k_lcb = int(plan["scoring"]["k_lcb"])
    backends = {
        "small": _build_backend(context, backend_name, "small"),
        "frontier": _build_backend(context, backend_name, "frontier"),
    }
    small_specs, small_orderings = _build_unit_specs(
        questions=small_questions,
        model_role="small",
        context=context,
        backend=backends["small"],
        manifest_hash=bundle.manifest_hash,
        k_lcb=k_lcb,
    )
    frontier_specs, frontier_orderings = _build_unit_specs(
        questions=frontier_questions,
        model_role="frontier",
        context=context,
        backend=backends["frontier"],
        manifest_hash=bundle.manifest_hash,
        k_lcb=k_lcb,
    )
    all_specs = [*small_specs, *frontier_specs]
    orderings_by_unit = {**small_orderings, **frontier_orderings}
    states_before = rebuild_measurement_unit_states(
        store_dir=context.storage.measurement_dir,
        export_dir=context.storage.export_dir,
        unit_specs=all_specs,
    )

    run_id = f"phase1-cohort-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    for model_role, backend in backends.items():
        _append_provider_loaded_event(
            store_dir=context.storage.measurement_dir,
            context=context,
            backend=backend,
            model_role=model_role,
            run_id=run_id,
        )

    skipped_by_role = {"small": 0, "frontier": 0}
    questions_by_key = {
        (question.question_id, "small"): question for question in small_questions
    }
    questions_by_key.update(
        {(question.question_id, "frontier"): question for question in frontier_questions}
    )

    for spec in all_specs:
        key = (spec.question_id, spec.model_role)
        state = states_before[key]
        question = questions_by_key[key]
        original_question = original_questions_by_key[key]
        backend = backends[spec.model_role]

        if state["completed"]:
            skipped_by_role[spec.model_role] += 1
            continue

        if question.paragraph_count != original_question.paragraph_count:
            _append_protocol_deviation_event(
                store_dir=context.storage.measurement_dir,
                context=context,
                backend=backend,
                model_role=spec.model_role,
                run_id=run_id,
                original_question=original_question,
                limited_question=question,
            )

        if state["needs_derivation"]:
            snapshot = materialize_question_snapshot(
                context.storage.measurement_dir,
                question.question_id,
                model_role=spec.model_role,
                lcb_quantile=0.1,
            )
            if not state["delta_materialized_present"]:
                append_delta_materialized_event(
                    store_dir=context.storage.measurement_dir,
                    context=context,
                    backend=backend,
                    model_role=spec.model_role,
                    run_id=run_id,
                    question=question,
                    manifest_hash=bundle.manifest_hash,
                    baseline_logp=float(snapshot["baseline_logp"]),
                    snapshot=snapshot,
                )
        else:
            try:
                snapshot = compute_question_delta_loo(
                    context=context,
                    question=question,
                    backend=backend,
                    model_role=spec.model_role,
                    orderings=orderings_by_unit[key],
                    store_dir=context.storage.measurement_dir,
                    run_id=run_id,
                    manifest_hash=bundle.manifest_hash,
                )
            except RuntimeError as exc:
                if backend_name != "live" or not _is_data_inspection_failed(exc):
                    raise
                blocked_question_ids = sorted({*blocked_question_ids, question.question_id})
                blocked_path = _write_blocked_question_ids(blocked_questions_path, blocked_question_ids)
                _append_blocked_question_event(
                    store_dir=context.storage.measurement_dir,
                    context=context,
                    backend=backend,
                    model_role=spec.model_role,
                    run_id=run_id,
                    question=question,
                    manifest_hash=bundle.manifest_hash,
                    blocked_questions_path=blocked_path,
                    error_message=str(exc),
                )
                return {
                    "status": "blocked_replan_required",
                    "run_id": run_id,
                    "blocked_question_id": question.question_id,
                    "blocked_questions_path": str(blocked_path),
                    "events_path": str(events_path_for(context.storage.measurement_dir)),
                    "calibration_manifest_path": str(calibration_manifest_path),
                    "validation": validation,
                }

        export_paths = export_delta_lcb(
            question_id=question.question_id,
            hop_depth=question.hop_depth,
            model_role=spec.model_role,
            snapshot=snapshot,
            export_dir=context.storage.export_dir,
        )
        _append_export_event(
            store_dir=context.storage.measurement_dir,
            context=context,
            backend=backend,
            model_role=spec.model_role,
            run_id=run_id,
            question=question,
            manifest_hash=bundle.manifest_hash,
            export_paths=export_paths,
        )

    contamination_report = run_contamination_analysis(
        measurement_dir=context.storage.measurement_dir,
        export_dir=context.storage.export_dir,
    )

    bridge_exports = run_bridge_analysis(
        measurement_dir=context.storage.measurement_dir,
        export_dir=context.storage.export_dir,
        calibration_manifest_path=calibration_manifest_path,
        seed=int(context.experiment["seed"]),
        bootstrap_resamples=1000,
    )
    if bridge_exports["status"] == "computed":
        annotation_report = materialize_annotation_artifacts(
            bundle=bundle,
            export_dir=context.storage.export_dir,
            bridge_diagnostics_path=bridge_exports["bridge_diagnostics"],
            bridged_delta_loo_jsonl_path=bridge_exports["bridged_delta_loo_jsonl"],
            tolerance_band_path=bridge_exports["tolerance_band"],
            seed=int(context.experiment["seed"]),
        )
        _append_annotation_queue_event(
            store_dir=context.storage.measurement_dir,
            context=context,
            run_id=run_id,
            annotation_report=annotation_report,
        )
        annotation_file_status = annotation_status_from_files(annotation_report["annotation_manifest_path"])
        annotation_status_path = _write_annotation_status(
            export_dir=context.storage.export_dir,
            annotation_report=annotation_report,
            annotation_file_status=annotation_file_status,
        )

        kappa_report: dict[str, object] = {
            "status": "awaiting_annotation",
            "kappa_summary_path": "",
            "summary": {"annotation_mode": annotation_file_status["annotation_mode"]},
        }
        if annotation_file_status["status"] == "ready_for_ingestion":
            ingest_annotation_labels(
                store_dir=context.storage.measurement_dir,
                annotation_manifest_path=annotation_report["annotation_manifest_path"],
                run_id=run_id,
                provider=context.provider.name,
                protocol_version=context.experiment["protocol_version"],
                sampling_seed=int(context.experiment["seed"]),
            )
            kappa_report = compute_reliability_from_events(
                store_dir=context.storage.measurement_dir,
                annotation_manifest_hash=annotation_report["annotation_manifest_hash"],
                export_dir=context.storage.export_dir,
                run_id=run_id,
                provider=context.provider.name,
                protocol_version=context.experiment["protocol_version"],
                sampling_seed=int(context.experiment["seed"]),
                bootstrap_resamples=1000,
                threshold=0.7,
            )
            _finalize_variance_bias_budget(
                variance_bias_budget_path=bridge_exports["variance_bias_budget"],
                kappa_summary_path=kappa_report["kappa_summary_path"],
            )
            annotation_file_status = {
                **annotation_file_status,
                "status": "completed",
            }
            annotation_status_path = _write_annotation_status(
                export_dir=context.storage.export_dir,
                annotation_report=annotation_report,
                annotation_file_status=annotation_file_status,
            )
    else:
        annotation_report = {
            "status": "pending_bridge",
            "annotation_manifest_hash": "",
            "annotation_manifest_path": "",
            "annotation_queue_path": "",
            "annotation_items_path": "",
            "annotation_readme_path": "",
            "queue_count": 0,
            "flagged_count": 0,
            "face_validity_count": 0,
        }
        annotation_file_status = {
            "status": "pending_bridge",
            "annotation_mode": "awaiting_labels",
            "completion": {},
        }
        annotation_status_path = write_json(
            context.storage.export_dir / "annotations" / "annotation_status.json",
            {
                "status": "pending_bridge",
                "annotation_mode": "awaiting_labels",
                "reason": "bridge outputs are incomplete, so annotation artifacts were not materialized",
                "bridge_status": bridge_exports["status"],
            },
        )
        kappa_report = {
            "status": "pending_bridge",
            "kappa_summary_path": "",
            "summary": {"annotation_mode": "awaiting_labels"},
        }
    states_after = rebuild_measurement_unit_states(
        store_dir=context.storage.measurement_dir,
        export_dir=context.storage.export_dir,
        unit_specs=all_specs,
    )

    summary = {
        "run_id": run_id,
        "backend": backend_name,
        "scope_mode": scope_mode,
        "annotation_mode": annotation_file_status["annotation_mode"],
        "calibration_manifest_path": str(calibration_manifest_path),
        "calibration_per_hop_count": _calibration_per_hop_count(plan),
        "blocked_questions_path": str(blocked_questions_path),
        "excluded_question_ids": blocked_question_ids,
        "retrieval_dry_run": str(retrieval_path),
        "contamination": {
            "status": contamination_report["status"],
            "path": contamination_report["path"],
            "gate_decision": contamination_report["payload"]["gate_decision"],
        },
        "bridge_status": bridge_exports["status"],
        "annotation": {
            "status": annotation_file_status["status"],
            "annotation_mode": annotation_file_status["annotation_mode"],
            "queue_count": annotation_report["queue_count"],
            "flagged_count": annotation_report["flagged_count"],
            "face_validity_count": annotation_report["face_validity_count"],
            "annotation_manifest_path": annotation_report["annotation_manifest_path"],
            "annotation_readme_path": annotation_report["annotation_readme_path"],
            "annotation_status_path": str(annotation_status_path),
        },
        "kappa": {
            "status": kappa_report["status"],
            "annotation_mode": kappa_report.get("summary", {}).get("annotation_mode", annotation_file_status["annotation_mode"]),
            "kappa_summary_path": kappa_report.get("kappa_summary_path", ""),
        },
        "source_of_truth": "event_log",
        "resume_from_event_log": True,
        "model_roles": {},
    }
    for model_role, specs in {"small": small_specs, "frontier": frontier_specs}.items():
        role_states = [states_after[(spec.question_id, spec.model_role)] for spec in specs]
        completed = sum(1 for state in role_states if state["completed"])
        planned = len(specs)
        summary["model_roles"][model_role] = {
            "planned": planned,
            "completed": completed,
            "skipped": skipped_by_role[model_role],
            "incomplete": planned - completed,
        }

    pipeline_status = _pipeline_status(
        blocked=False,
        bridge_status=bridge_exports["status"],
        annotation_status=annotation_file_status["status"],
        model_roles=summary["model_roles"],
    )
    measurement_status = _measurement_status(
        scope_mode=scope_mode,
        contamination_gate_decision=summary["contamination"]["gate_decision"],
        annotation_mode=annotation_file_status["annotation_mode"],
        kappa_status=kappa_report["status"],
    )

    status = "green"
    if any(role["incomplete"] for role in summary["model_roles"].values()):
        status = "red"
    elif bridge_exports["status"] != "computed":
        status = "red"
    elif annotation_file_status["status"] == "awaiting_labels":
        status = "awaiting_annotation"
    elif kappa_report["status"] != "computed":
        status = "red"

    summary["pipeline_status"] = pipeline_status
    summary["measurement_status"] = measurement_status
    run_summary_path = write_json(context.storage.export_dir / "run_summary.json", summary)
    checkpoint_path = write_json(
        context.storage.checkpoint_dir / f"{run_id}.json",
        {
            "run_id": run_id,
            "source_of_truth": "event_log",
            "resume_from_event_log": True,
            "model_roles": {
                model_role: {
                    "completed_units": [
                        state["question_id"]
                        for state in states_after.values()
                        if state["model_role"] == model_role and state["completed"]
                    ]
                }
                for model_role in ("small", "frontier")
            },
        },
    )

    return {
        "status": status,
        "run_id": run_id,
        "events_path": str(events_path_for(context.storage.measurement_dir)),
        "calibration_manifest_path": str(calibration_manifest_path),
        "blocked_questions_path": str(blocked_questions_path),
        "run_summary_path": str(run_summary_path),
        "checkpoint_path": str(checkpoint_path),
        "annotation_manifest_path": str(annotation_report["annotation_manifest_path"]),
        "annotation_readme_path": str(annotation_report["annotation_readme_path"]),
        "annotation_status_path": str(annotation_status_path),
        "summary": summary,
        "contamination_report": contamination_report,
        "bridge_exports": bridge_exports,
        "kappa_report": kappa_report,
        "validation": validation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the minimal recoverable Phase 1 cohort flow.")
    parser.add_argument("--plan", default="configs/runs/cohort.json")
    parser.add_argument("--backend", choices=("mock", "live"), default="mock")
    parser.add_argument("--env", default=None)
    args = parser.parse_args()

    report = run_phase1_cohort(
        backend_name=args.backend,
        cohort_plan_path=args.plan,
        env_path=args.env,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "green" else 1


if __name__ == "__main__":
    raise SystemExit(main())
