from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import Any


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_alias(payload: dict[str, Any], left: str, right: str, label: str) -> None:
    left_present = left in payload
    right_present = right in payload
    if not left_present and not right_present:
        raise ValueError(f"{label} requires {left} or {right}")
    if left_present and right_present:
        if payload[left] != payload[right]:
            raise ValueError(f"conflicting {label} aliases: {left} and {right}")
        return
    if left_present:
        payload[right] = payload[left]
    else:
        payload[left] = payload[right]


def _normalize_token_aliases(payload: dict[str, Any]) -> None:
    left = "token_cost"
    right = "token_estimate"
    left_present = left in payload
    right_present = right in payload

    if left_present and not _is_integer(payload[left]):
        raise ValueError("token_cost must be an integer")
    if right_present and not _is_integer(payload[right]):
        raise ValueError("token_estimate must be an integer")
    if left_present and right_present:
        if payload[left] != payload[right]:
            raise ValueError("conflicting token aliases: token_cost and token_estimate")
        return
    if left_present:
        payload[right] = payload[left]
    elif right_present:
        payload[left] = payload[right]


def normalize_candidate_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a non-mutating candidate payload with CPS and legacy aliases."""

    normalized = deepcopy(dict(payload))
    _require_alias(normalized, "candidate_id", "item_id", "candidate identity")
    _require_alias(normalized, "content", "text", "candidate content")
    _normalize_token_aliases(normalized)
    return normalized


def normalize_candidate_pool(items: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Normalize candidate payloads while preserving input order."""

    return [normalize_candidate_payload(item) for item in items]
