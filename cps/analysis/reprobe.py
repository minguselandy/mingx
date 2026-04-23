from __future__ import annotations

import math
from pathlib import Path

from api.backends import build_scoring_backend
from cps.analysis.contamination import CONTAMINATION_THRESHOLD_LOGP
from cps.runtime.config import load_phase1_context


def run_question_only_reprobe(
    *,
    question_text: str,
    answer_text: str,
    question_id: str | None = None,
    backend_name: str = "live",
    model_role: str = "frontier",
    env_path: str | Path | None = None,
    phase1_config_path: str | Path = "phase1.yaml",
    run_plan_path: str | Path = "configs/runs/smoke.json",
) -> dict:
    context = load_phase1_context(
        phase1_config_path=phase1_config_path,
        run_plan_path=run_plan_path,
        env_path=env_path,
    )
    backend = build_scoring_backend(
        context=context,
        backend_name=backend_name,
        model_role=model_role,
    )
    score = backend.score_answer(
        question_text=question_text,
        answer_text=answer_text,
        ordered_paragraphs=(),
    )
    baseline_logp = float(score.logprob_sum)
    threshold_probability = math.exp(CONTAMINATION_THRESHOLD_LOGP)
    baseline_probability = math.exp(baseline_logp)
    passes_threshold = baseline_logp <= CONTAMINATION_THRESHOLD_LOGP
    nonzero_token_count = sum(1 for value in score.token_logprobs if abs(value) > 1e-12)

    return {
        "status": "green",
        "question_id": question_id or "",
        "mode": "question_only_reprobe",
        "backend": backend_name,
        "api_profile": context.provider.profile_name or "",
        "provider": context.provider.name,
        "backend_id": backend.backend_id,
        "model_role": model_role,
        "model_id": backend.model_id,
        "question_text": question_text,
        "answer_text": answer_text,
        "baseline_logp": baseline_logp,
        "baseline_probability": baseline_probability,
        "threshold_logp": CONTAMINATION_THRESHOLD_LOGP,
        "threshold_probability": threshold_probability,
        "passes_contamination_threshold": passes_threshold,
        "recommended_disposition": (
            "keep_candidate_for_human_review" if passes_threshold else "drop_and_replace"
        ),
        "response_status": score.response_status,
        "request_fingerprint": score.request_fingerprint,
        "token_count": len(score.token_logprobs),
        "nonzero_token_count": nonzero_token_count,
    }
