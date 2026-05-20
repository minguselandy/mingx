from __future__ import annotations

import json
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.hashing import stable_hash
from cps.evaluators.live_api_chat_logprob_confidence import _confidence_from_logprobs


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
ALLOWED_CLAIMS = [
    "constrained_label_generation_proxy",
    "operational_label_confidence_proxy",
]
LABELS = {"not_supporting", "parse_failed", "supporting", "uncertain"}
UNCERTAINTY = {"high", "low", "medium"}
RATIONALE_QUALITY = {"adequate", "invalid", "thin"}


def build_label_proxy_contract() -> dict[str, Any]:
    return {
        "allowed_claims": ALLOWED_CLAIMS,
        "claim_status": CLAIM_STATUS,
        "denied_claims": {
            "fixed_target_nll": True,
            "teacher_forced_label_nll": True,
            "v_information_proxy": True,
        },
        "raw_response_stored": False,
        "response_contract": {
            "label": sorted(LABELS - {"parse_failed"}),
            "rationale_quality": ["adequate", "thin", "invalid"],
            "uncertainty": sorted(UNCERTAINTY),
        },
        "schema_version": "epf_live_api_label_generation_proxy_contract_v1",
    }


def _clean_label(value: Any) -> str:
    label = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if label in {"non_supporting", "unsupported"}:
        label = "not_supporting"
    return label if label in LABELS else "uncertain"


def _clean_uncertainty(value: Any) -> str:
    uncertainty = str(value or "").strip().lower()
    return uncertainty if uncertainty in UNCERTAINTY else "high"


def _clean_rationale_quality(value: Any) -> str:
    quality = str(value or "").strip().lower()
    return quality if quality in RATIONALE_QUALITY else "invalid"


def normalize_label_generation(
    *,
    confidence: float | None = None,
    content: str,
    model_id: str,
    parent_sample_id: str,
    probe_type: str,
    prompt_text: str,
    token_logprobs: Sequence[float],
    expected_label: str | None = None,
    sample_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    parse_ok = True
    try:
        payload = json.loads(content)
        if not isinstance(payload, dict):
            raise ValueError("payload_not_object")
    except (json.JSONDecodeError, ValueError):
        payload = {}
        parse_ok = False
    label = _clean_label(payload.get("label")) if parse_ok else "parse_failed"
    uncertainty = _clean_uncertainty(payload.get("uncertainty"))
    expected = _clean_label(expected_label) if expected_label is not None else None
    row = {
        "allowed_claims": list(ALLOWED_CLAIMS),
        "claim_status": CLAIM_STATUS,
        "confidence": round(float(confidence if confidence is not None else _confidence_from_logprobs(token_logprobs)), 6),
        "content_hash": stable_hash({"content": str(content)}),
        "expected_public_benchmark_label": expected,
        "fixed_target_nll": False,
        "label": label,
        "matches_public_benchmark_label": (label == expected) if expected is not None and label != "parse_failed" else None,
        "model_id": str(model_id),
        "parent_sample_id": str(parent_sample_id),
        "parse_ok": parse_ok,
        "probe_type": str(probe_type),
        "prompt_hash": stable_hash({"prompt_text": str(prompt_text)}),
        "rationale_quality": _clean_rationale_quality(payload.get("rationale_quality")) if parse_ok else "invalid",
        "raw_response_stored": False,
        "sample_metadata": dict(sample_metadata or {}),
        "schema_version": "epf_live_api_label_generation_proxy_row_v1",
        "teacher_forced_label_nll": False,
        "token_logprobs_available": bool(token_logprobs),
        "uncertainty": uncertainty,
    }
    row["label_record_hash"] = stable_hash(row)
    return row


def summarize_label_proxy_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    parse_ok = sum(1 for row in rows if row.get("parse_ok"))
    matches = [
        bool(row.get("matches_public_benchmark_label"))
        for row in rows
        if row.get("matches_public_benchmark_label") is not None
    ]
    return {
        "allowed_claims": list(ALLOWED_CLAIMS),
        "claim_status": CLAIM_STATUS,
        "label_count": total,
        "parse_success_rate": round(parse_ok / total, 6) if total else 0.0,
        "public_benchmark_label_match_rate": round(sum(1 for item in matches if item) / len(matches), 6)
        if matches
        else None,
        "raw_response_stored": False,
        "schema_version": "epf_live_api_label_generation_proxy_summary_v1",
        "teacher_forced_label_nll_available": False,
    }
