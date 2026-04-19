from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from phase0.manifest import load_manifest, validate_manifest
from phase0.measurement_store import append_event, events_path_for, rebuild_run_progress, snapshot_path_for
from phase1.config import load_phase1_context
from phase1.dashscope_backend import DashScopeChatBackend
from phase1.delta_pipeline import compute_question_delta_loo, limit_question_for_smoke
from phase1.exports import ensure_directories, export_delta_lcb, export_stub_artifacts, write_json
from phase1.orderings import build_orderings
from phase1.retrieval import build_retrieval_dry_run
from phase1.scoring import MockScoringBackend


def _resolve_run_plan_path(run_plan_path: str | Path) -> Path:
    return Path(run_plan_path).resolve()


def _resolve_from_run_plan(run_plan: dict, key: str, run_plan_path: Path, root_dir: Path) -> Path:
    candidate = Path(run_plan[key])
    if candidate.is_absolute():
        return candidate.resolve()

    local_candidate = (run_plan_path.parent / candidate).resolve()
    if local_candidate.exists():
        return local_candidate
    return (root_dir / candidate).resolve()


def run_phase1_smoke(
    *,
    backend_name: str,
    run_plan_path: str | Path = "artifacts/phase1/run_plan.json",
    env_path: str | Path | None = None,
) -> dict:
    run_plan_file = _resolve_run_plan_path(run_plan_path)
    run_plan = json.loads(run_plan_file.read_text(encoding="utf-8"))
    context = load_phase1_context(
        phase1_config_path=run_plan.get("phase1_config_path", "phase1.yaml"),
        run_plan_path=run_plan_file,
        env_path=env_path,
    )
    manifest_path = _resolve_from_run_plan(run_plan, "manifest_path", run_plan_file, context.root_dir)
    hash_path = _resolve_from_run_plan(run_plan, "hash_path", run_plan_file, context.root_dir)
    bundle = load_manifest(manifest_path)
    validation = validate_manifest(bundle, hashes_path=hash_path, config_path="phase0.yaml")
    if not validation["ok"]:
        return {"status": "red", "validation": validation}
    if context.scoring.variance_source != "paragraph_order_permutation_only":
        raise ValueError("Phase 1 smoke only supports paragraph-order permutation variance")
    if int(run_plan["scoring"]["k_lcb"]) != context.scoring.permutation_count:
        raise ValueError("run_plan k_lcb must match phase1 permutation_count")
    if float(run_plan["scoring"].get("lcb_quantile", 0.1)) != 0.1:
        raise ValueError("Phase 1 smoke currently locks lcb_quantile to 0.1")

    ensure_directories(
        context.storage.measurement_dir,
        context.storage.export_dir,
        context.storage.checkpoint_dir,
        context.storage.cache_dir,
    )
    run_id = f"phase1-smoke-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    question_id = run_plan.get("smoke_question_id")
    question = next((item for item in bundle.sample if item.question_id == question_id), bundle.sample[0])
    limited_question = limit_question_for_smoke(question, run_plan.get("smoke_paragraph_limit"))

    if backend_name == "mock":
        model_role = run_plan["scoring"].get("model_role", "small")
        backend = MockScoringBackend(model_id=context.models[model_role].model)
    elif backend_name == "live":
        model_role = run_plan["scoring"].get("model_role", "small")
        backend = DashScopeChatBackend(context=context, model_role=model_role)
    else:
        raise ValueError(f"Unsupported backend: {backend_name}")

    append_event(
        context.storage.measurement_dir,
        {
            "event_type": "provider_config_loaded",
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
            "manifest_hash": bundle.manifest_hash,
            "sampling_seed": context.experiment["seed"],
            "protocol_version": context.experiment["protocol_version"],
            "request_fingerprint": None,
            "response_status": "loaded",
            "notes": "provider config loaded",
            "payload": {
                "base_url": context.provider.base_url,
                "model_role": model_role,
                "backend_name": backend_name,
            },
        },
    )

    if limited_question.paragraph_count != question.paragraph_count:
        append_event(
            context.storage.measurement_dir,
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
                "manifest_hash": bundle.manifest_hash,
                "sampling_seed": context.experiment["seed"],
                "protocol_version": context.experiment["protocol_version"],
                "request_fingerprint": None,
                "response_status": "deviation",
                "notes": "smoke run uses a truncated paragraph subset for cost-controlled replay",
                "payload": {
                    "original_paragraph_count": question.paragraph_count,
                    "smoke_paragraph_count": limited_question.paragraph_count,
                },
            },
        )

    retrieval_results = build_retrieval_dry_run(limited_question, context.scoring.top_k_values)
    retrieval_path = write_json(context.storage.export_dir / "retrieval_dry_run.json", retrieval_results)

    orderings = build_orderings(
        question_id=limited_question.question_id,
        paragraph_ids=[paragraph.paragraph_id for paragraph in limited_question.paragraphs],
        k_lcb=int(run_plan["scoring"]["k_lcb"]),
        canonical_ordering_id=context.scoring.canonical_ordering_id,
        seed=int(context.experiment["seed"]),
    )
    snapshot = compute_question_delta_loo(
        context=context,
        question=limited_question,
        backend=backend,
        model_role=model_role,
        orderings=orderings,
        store_dir=context.storage.measurement_dir,
        run_id=run_id,
        manifest_hash=bundle.manifest_hash,
    )
    delta_exports = export_delta_lcb(
        question_id=limited_question.question_id,
        hop_depth=limited_question.hop_depth,
        model_role=model_role,
        snapshot=snapshot,
        export_dir=context.storage.export_dir,
    )
    stub_exports = export_stub_artifacts(
        context.storage.export_dir,
        limited_question.question_id,
        mode="smoke",
    )
    export_manifest_path = write_json(
        context.storage.export_dir / "export_manifest.json",
        {
            "run_id": run_id,
            "question_id": limited_question.question_id,
            "delta_exports": delta_exports,
            "stub_exports": stub_exports,
            "retrieval_dry_run": str(retrieval_path),
        },
    )
    append_event(
        context.storage.measurement_dir,
        {
            "event_type": "export_materialized",
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
            "manifest_hash": bundle.manifest_hash,
            "sampling_seed": context.experiment["seed"],
            "protocol_version": context.experiment["protocol_version"],
            "request_fingerprint": None,
            "response_status": "exported",
            "notes": "phase1 smoke exports ready",
            "payload": {
                "delta_loo_jsonl": delta_exports["delta_loo_jsonl"],
                "retrieval_dry_run": str(retrieval_path),
                "question_export_manifest": delta_exports["question_export_manifest"],
                "export_manifest": str(export_manifest_path),
            },
        },
    )
    progress = rebuild_run_progress(context.storage.measurement_dir, run_id=run_id)
    checkpoint_path = write_json(
        context.storage.checkpoint_dir / f"{run_id}.json",
        {
            "run_id": run_id,
            "source_of_truth": "event_log",
            "resume_policy": "reconcile_from_events_on_resume",
            "progress": progress,
        },
    )

    return {
        "status": "green",
        "run_id": run_id,
        "question_id": limited_question.question_id,
        "events_path": str(events_path_for(context.storage.measurement_dir)),
        "snapshot_path": str(
            snapshot_path_for(
                context.storage.measurement_dir,
                limited_question.question_id,
                model_role=model_role,
            )
        ),
        "checkpoint_path": str(checkpoint_path),
        "exports": {
            **delta_exports,
            **stub_exports,
            "retrieval_dry_run": str(retrieval_path),
            "export_manifest": str(export_manifest_path),
        },
        "validation": validation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a minimal Phase 1 smoke flow.")
    parser.add_argument("--backend", choices=("mock", "live"), default="mock")
    parser.add_argument("--run-plan", default="artifacts/phase1/run_plan.json")
    parser.add_argument("--env", default=None)
    args = parser.parse_args()

    report = run_phase1_smoke(backend_name=args.backend, run_plan_path=args.run_plan, env_path=args.env)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "green" else 1


if __name__ == "__main__":
    raise SystemExit(main())
