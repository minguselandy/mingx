from __future__ import annotations

import re
from typing import Any
from typing import Mapping
from typing import Sequence


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
SCHEMA_VERSION = "teacher_forced_score_record_v1"
VALIDATION_SCHEMA_VERSION = "teacher_forced_score_record_validation_v1"

REQUIRED_FIELDS = (
    "prompt_text",
    "fixed_target_text",
    "prompt_template_hash",
    "target_format_hash",
    "materialization_policy_hash",
    "tokenizer_id",
    "target_token_ids",
    "target_token_count",
    "per_token_logprobs",
    "target_nll",
    "target_nll_normalized",
    "scoring_backend_id",
    "scorer_model_id",
    "scoring_policy",
    "deterministic_settings",
    "raw_response_stored",
)

RAW_RESPONSE_KEYS = {
    "choices",
    "message",
    "messages",
    "raw_api_response",
    "raw_payload",
    "raw_response",
    "raw_response_payload",
    "response_payload",
}

SECRET_KEY_PATTERN = re.compile(r"(api[_-]?key|authorization|bearer|password|secret)", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(r"(sk-[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9._-]{12,})", re.IGNORECASE)


def _walk_payload(payload: Any) -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = []
    stack: list[tuple[str, Any]] = [("", payload)]
    while stack:
        path, current = stack.pop()
        if isinstance(current, Mapping):
            for key, value in current.items():
                key_text = str(key)
                child_path = f"{path}.{key_text}" if path else key_text
                items.append((child_path, value))
                stack.append((child_path, value))
        elif isinstance(current, list | tuple):
            for index, value in enumerate(current):
                child_path = f"{path}[{index}]"
                stack.append((child_path, value))
    return items


def _contains_raw_response_payload(payload: Mapping[str, Any]) -> bool:
    for path, _value in _walk_payload(payload):
        key = path.rsplit(".", maxsplit=1)[-1]
        if key in RAW_RESPONSE_KEYS:
            return True
    return False


def _contains_secret_like_field(payload: Mapping[str, Any]) -> bool:
    for path, value in _walk_payload(payload):
        key = path.rsplit(".", maxsplit=1)[-1]
        if SECRET_KEY_PATTERN.search(key) and value not in (False, None, "", [], {}):
            return True
        if isinstance(value, str) and SECRET_VALUE_PATTERN.search(value):
            return True
    return False


def build_teacher_forced_score_record(
    *,
    deterministic_settings: Mapping[str, Any],
    fixed_target_text: str,
    materialization_policy_hash: str,
    per_token_logprobs: Sequence[float],
    prompt_template_hash: str,
    prompt_text: str,
    scorer_model_id: str,
    scoring_backend_id: str,
    scoring_policy: Mapping[str, Any],
    target_format_hash: str,
    target_token_ids: Sequence[int | str],
    tokenizer_id: str,
    generated_target_text: str | None = None,
    **extra_fields: Any,
) -> dict[str, Any]:
    token_logprobs = [float(value) for value in per_token_logprobs]
    target_token_count = len(list(target_token_ids))
    target_nll = -sum(token_logprobs) if token_logprobs else None
    payload: dict[str, Any] = {
        "claim_status": CLAIM_STATUS,
        "deterministic_settings": dict(deterministic_settings),
        "fixed_target_text": str(fixed_target_text),
        "generated_target_text": generated_target_text,
        "materialization_policy_hash": str(materialization_policy_hash),
        "per_token_logprobs": token_logprobs,
        "prompt_template_hash": str(prompt_template_hash),
        "prompt_text": str(prompt_text),
        "raw_response_stored": False,
        "schema_version": SCHEMA_VERSION,
        "scorer_model_id": str(scorer_model_id),
        "scoring_backend_id": str(scoring_backend_id),
        "scoring_policy": dict(scoring_policy),
        "target_format_hash": str(target_format_hash),
        "target_nll": target_nll,
        "target_nll_normalized": (target_nll / target_token_count) if target_nll is not None and target_token_count else None,
        "target_token_count": target_token_count,
        "target_token_ids": list(target_token_ids),
        "tokenizer_id": str(tokenizer_id),
    }
    payload.update(extra_fields)
    return payload


def validate_teacher_forced_score_record(payload: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"missing_{field}")
    fixed_target_text = str(payload.get("fixed_target_text") or "")
    if not fixed_target_text:
        errors.append("empty_fixed_target_text")
    generated_target = payload.get("generated_target_text")
    if generated_target not in (None, "") and str(generated_target) != fixed_target_text:
        errors.append("generated_target_mismatch")
    if payload.get("raw_response_stored") is not False:
        errors.append("raw_response_stored_not_false")

    target_token_ids = list(payload.get("target_token_ids") or [])
    per_token_logprobs = list(payload.get("per_token_logprobs") or [])
    target_token_count = int(payload.get("target_token_count") or 0)
    if not payload.get("tokenizer_id"):
        errors.append("missing_tokenizer_id")
    if not target_token_ids:
        errors.append("missing_target_token_ids")
    if not per_token_logprobs:
        errors.append("missing_per_token_logprobs")
    if target_token_count != len(target_token_ids):
        errors.append("target_token_count_mismatch")
    if not target_token_ids and per_token_logprobs:
        errors.append("target_token_count_mismatch")
    if target_token_count != len(per_token_logprobs):
        errors.append("logprob_count_mismatch")
    if payload.get("target_nll") is None:
        errors.append("missing_target_nll")
    if payload.get("target_nll_normalized") is None:
        errors.append("missing_target_nll_normalized")
    if _contains_raw_response_payload(payload):
        errors.append("raw_response_payload_field_present")
    if _contains_secret_like_field(payload):
        errors.append("secret_like_field_present")
    return {
        "claim_status": CLAIM_STATUS,
        "errors": sorted(set(errors)),
        "passed": not errors,
        "schema_version": VALIDATION_SCHEMA_VERSION,
    }
