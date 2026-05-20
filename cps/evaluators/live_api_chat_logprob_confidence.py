from __future__ import annotations

import math
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.hashing import stable_hash


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
ALLOWED_CLAIM = "operational_confidence_diagnostic"
DENIED_CLAIMS = {
    "calibrated_proxy": True,
    "fixed_target_nll": True,
    "metric_bridge": True,
    "v_information_proxy": True,
}


def _finite_logprobs(values: Sequence[float]) -> list[float]:
    return [float(value) for value in values if math.isfinite(float(value))]


def _confidence_from_logprobs(values: Sequence[float]) -> float:
    logprobs = _finite_logprobs(values)
    if not logprobs:
        return 0.0
    mean_logprob = sum(logprobs) / len(logprobs)
    return round(max(0.0, min(1.0, math.exp(mean_logprob))), 6)


def diagnostic_schema() -> dict[str, Any]:
    return {
        "allowed_claim": ALLOWED_CLAIM,
        "claim_status": CLAIM_STATUS,
        "denied_claims": sorted(DENIED_CLAIMS),
        "generated_token_logprobs_are_fixed_target_nll": False,
        "raw_response_stored": False,
        "schema_version": "epf_live_api_chat_logprob_confidence_schema_v1",
    }


def build_confidence_diagnostic(
    *,
    backend_id: str,
    generated_text: str,
    model_id: str,
    prompt_id: str,
    prompt_text: str,
    token_logprobs: Sequence[float],
) -> dict[str, Any]:
    logprobs = _finite_logprobs(token_logprobs)
    token_count = len(logprobs)
    generated_nll = -sum(logprobs) if logprobs else None
    return {
        "allowed_claim": ALLOWED_CLAIM,
        "backend_id": str(backend_id),
        "claim_status": CLAIM_STATUS,
        "confidence": _confidence_from_logprobs(logprobs),
        "denied_claims": dict(DENIED_CLAIMS),
        "generated_text_hash": stable_hash({"generated_text": str(generated_text)}),
        "generated_token_count": token_count,
        "generated_token_logprobs_available": bool(logprobs),
        "generated_token_nll": generated_nll,
        "generated_token_nll_normalized": (generated_nll / token_count) if generated_nll is not None and token_count else None,
        "model_id": str(model_id),
        "prompt_hash": stable_hash({"prompt_text": str(prompt_text)}),
        "prompt_id": str(prompt_id),
        "raw_response_stored": False,
        "schema_version": "epf_live_api_chat_logprob_confidence_v1",
        "teacher_forced_fixed_target_nll": False,
    }


def summarize_confidence_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    confidences = [float(row.get("confidence") or 0.0) for row in rows]
    return {
        "allowed_claim": ALLOWED_CLAIM,
        "claim_status": CLAIM_STATUS,
        "diagnostic_count": len(rows),
        "generated_token_logprobs_available": any(row.get("generated_token_logprobs_available") for row in rows),
        "mean_confidence": round(sum(confidences) / len(confidences), 6) if confidences else 0.0,
        "raw_response_stored": False,
        "schema_version": "epf_live_api_chat_logprob_confidence_summary_v1",
        "teacher_forced_fixed_target_nll_available": False,
    }
