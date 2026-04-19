from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Sequence

from phase0.manifest import ManifestParagraph, ManifestQuestion
from phase0.measurement_store import append_event, materialize_question_snapshot, snapshot_path_for
from phase1.config import Phase1Context
from phase1.orderings import OrderingSpec
from phase1.scoring import ScoreResult, ScoringBackend


def limit_question_for_smoke(question: ManifestQuestion, paragraph_limit: int | None) -> ManifestQuestion:
    if paragraph_limit is None or paragraph_limit >= len(question.paragraphs):
        return question
    paragraphs = tuple(question.paragraphs[:paragraph_limit])
    return ManifestQuestion(
        question_id=question.question_id,
        hop_depth=question.hop_depth,
        hop_subcategory=question.hop_subcategory,
        question_text=question.question_text,
        answer_text=question.answer_text,
        answer_aliases=question.answer_aliases,
        answerable=question.answerable,
        paragraph_count=len(paragraphs),
        paragraphs=paragraphs,
    )


def _ordered_paragraphs(question: ManifestQuestion, ordering: OrderingSpec) -> tuple[ManifestParagraph, ...]:
    lookup = {paragraph.paragraph_id: paragraph for paragraph in question.paragraphs}
    return tuple(lookup[paragraph_id] for paragraph_id in ordering.paragraph_ids)


def _append_score_event(
    store_dir: str | Path,
    event_type: str,
    *,
    context: Phase1Context,
    backend: ScoringBackend,
    model_role: str,
    run_id: str,
    question: ManifestQuestion,
    ordering: OrderingSpec | None,
    paragraph_id: int | None,
    baseline_logp: float,
    full_result: ScoreResult | None,
    loo_result: ScoreResult | None,
    delta_loo: float | None,
    notes: str,
    payload: dict | None = None,
) -> None:
    append_event(
        store_dir,
        {
            "event_type": event_type,
            "run_id": run_id,
            "question_id": question.question_id,
            "hop_depth": question.hop_depth,
            "provider": context.provider.name,
            "backend_id": backend.backend_id,
            "model_id": backend.model_id,
            "model_role": model_role,
            "ordering_id": ordering.ordering_id if ordering else None,
            "ordering": list(ordering.paragraph_ids) if ordering else None,
            "paragraph_id": paragraph_id,
            "baseline_logp": baseline_logp,
            "full_logp": None if full_result is None else full_result.logprob_sum,
            "loo_logp": None if loo_result is None else loo_result.logprob_sum,
            "delta_loo": delta_loo,
            "manifest_hash": payload.get("manifest_hash") if payload else None,
            "sampling_seed": context.experiment["seed"],
            "protocol_version": context.experiment["protocol_version"],
            "request_fingerprint": (
                loo_result.request_fingerprint
                if loo_result is not None
                else full_result.request_fingerprint if full_result is not None else None
            ),
            "response_status": (
                loo_result.response_status
                if loo_result is not None
                else full_result.response_status if full_result is not None else None
            ),
            "notes": notes,
            "payload": payload or {},
        },
    )


def append_delta_materialized_event(
    *,
    store_dir: str | Path,
    context: Phase1Context,
    backend: ScoringBackend,
    model_role: str,
    run_id: str,
    question: ManifestQuestion,
    manifest_hash: str,
    baseline_logp: float,
    snapshot: dict,
) -> None:
    append_event(
        store_dir,
        {
            "event_type": "delta_lcb_materialized",
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
            "baseline_logp": baseline_logp,
            "full_logp": None,
            "loo_logp": None,
            "delta_loo": None,
            "manifest_hash": manifest_hash,
            "sampling_seed": context.experiment["seed"],
            "protocol_version": context.experiment["protocol_version"],
            "request_fingerprint": None,
            "response_status": "materialized",
            "notes": "delta_loo LCB snapshot ready",
            "payload": {
                "snapshot_path": str(snapshot_path_for(store_dir, question.question_id, model_role=model_role)),
                "paragraph_count": len(snapshot["delta_loo_LCB"]),
            },
        },
    )


def compute_question_delta_loo(
    *,
    context: Phase1Context,
    question: ManifestQuestion,
    backend: ScoringBackend,
    model_role: str,
    orderings: Sequence[OrderingSpec],
    store_dir: str | Path,
    run_id: str,
    manifest_hash: str,
) -> dict:
    baseline_result = backend.score_answer(
        question_text=question.question_text,
        answer_text=question.answer_text,
        ordered_paragraphs=(),
    )
    _append_score_event(
        store_dir,
        "baseline_scored",
        context=context,
        backend=backend,
        model_role=model_role,
        run_id=run_id,
        question=question,
        ordering=None,
        paragraph_id=None,
        baseline_logp=baseline_result.logprob_sum,
        full_result=None,
        loo_result=None,
        delta_loo=None,
        notes="baseline question-only score",
        payload={"manifest_hash": manifest_hash, "content_match": baseline_result.metadata.get("content_match")},
    )

    for ordering in orderings:
        ordered_paragraphs = _ordered_paragraphs(question, ordering)
        full_result = backend.score_answer(
            question_text=question.question_text,
            answer_text=question.answer_text,
            ordered_paragraphs=ordered_paragraphs,
        )
        _append_score_event(
            store_dir,
            "full_scored",
            context=context,
            backend=backend,
            model_role=model_role,
            run_id=run_id,
            question=question,
            ordering=ordering,
            paragraph_id=None,
            baseline_logp=baseline_result.logprob_sum,
            full_result=full_result,
            loo_result=None,
            delta_loo=None,
            notes="full-context score",
            payload={"manifest_hash": manifest_hash, "content_match": full_result.metadata.get("content_match")},
        )

        for paragraph in ordered_paragraphs:
            loo_paragraphs = tuple(
                item for item in ordered_paragraphs if item.paragraph_id != paragraph.paragraph_id
            )
            loo_result = backend.score_answer(
                question_text=question.question_text,
                answer_text=question.answer_text,
                ordered_paragraphs=loo_paragraphs,
            )
            delta_loo = round(full_result.logprob_sum - loo_result.logprob_sum, 6)
            shared_payload = {
                "manifest_hash": manifest_hash,
                "full_content_match": full_result.metadata.get("content_match"),
                "loo_content_match": loo_result.metadata.get("content_match"),
            }
            _append_score_event(
                store_dir,
                "loo_scored",
                context=context,
                backend=backend,
                model_role=model_role,
                run_id=run_id,
                question=question,
                ordering=ordering,
                paragraph_id=paragraph.paragraph_id,
                baseline_logp=baseline_result.logprob_sum,
                full_result=full_result,
                loo_result=loo_result,
                delta_loo=delta_loo,
                notes="leave-one-out score",
                payload=shared_payload,
            )
            _append_score_event(
                store_dir,
                "ordering_scored",
                context=context,
                backend=backend,
                model_role=model_role,
                run_id=run_id,
                question=question,
                ordering=ordering,
                paragraph_id=paragraph.paragraph_id,
                baseline_logp=baseline_result.logprob_sum,
                full_result=full_result,
                loo_result=loo_result,
                delta_loo=delta_loo,
                notes="materialized ordering record",
                payload=shared_payload,
            )

    snapshot = materialize_question_snapshot(
        store_dir,
        question.question_id,
        model_role=model_role,
        lcb_quantile=0.1,
    )
    append_delta_materialized_event(
        store_dir=store_dir,
        context=context,
        backend=backend,
        model_role=model_role,
        run_id=run_id,
        question=question,
        manifest_hash=manifest_hash,
        baseline_logp=baseline_result.logprob_sum,
        snapshot=snapshot,
    )
    return snapshot
