from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable

from cps.experiments.artifacts import stable_hash


def _as_mapping(record: Any) -> dict[str, Any]:
    if isinstance(record, dict):
        return dict(record)
    if is_dataclass(record):
        return asdict(record)
    if hasattr(record, "__dict__"):
        return dict(vars(record))
    return {}


def first_field(record: Any, names: Iterable[str], default: Any = None) -> Any:
    payload = _as_mapping(record)
    for name in names:
        if name in payload and payload[name] not in (None, ""):
            return payload[name]
    for name in names:
        if hasattr(record, name):
            value = getattr(record, name)
            if value not in (None, ""):
                return value
    return default


def merge_mapping_fields(record: Any, names: Iterable[str]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for name in names:
        value = first_field(record, (name,))
        if isinstance(value, dict):
            merged.update(deepcopy(value))
    return merged


def compact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def estimate_token_cost(content: str) -> int:
    text = str(content)
    if not text.strip():
        return 0
    return len(re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE))


def content_hash(content: str) -> str:
    return stable_hash({"content": str(content)})


def stable_candidate_id(
    *,
    provider: str,
    source_type: str,
    source_id: str,
    content_hash_value: str,
) -> str:
    digest = stable_hash(
        {
            "provider": provider,
            "source_type": source_type,
            "source_id": source_id,
            "content_hash": content_hash_value,
        }
    )
    return f"{provider}:{source_type}:{digest[:16]}"


def native_candidate_payload(
    *,
    provider: str,
    source_type: str,
    content: str,
    source_id: str | None = None,
    candidate_id: str | None = None,
    token_cost: int | None = None,
    provenance: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    source_offsets: dict[str, int] | None = None,
    temporal_validity: dict[str, Any] | None = None,
    confidence: float | None = None,
    extraction_type: str | None = None,
    synthetic_source: str | None = None,
) -> dict[str, Any]:
    resolved_content = str(content)
    resolved_hash = content_hash(resolved_content)
    resolved_source_id = str(source_id or resolved_hash[:16])
    resolved_candidate_id = candidate_id or stable_candidate_id(
        provider=provider,
        source_type=source_type,
        source_id=resolved_source_id,
        content_hash_value=resolved_hash,
    )
    resolved_provenance = dict(provenance or {})
    resolved_provenance.setdefault("provider", provider)
    resolved_provenance.setdefault("source_type", source_type)
    resolved_provenance.setdefault("source_id", resolved_source_id)
    resolved_metadata = dict(metadata or {})

    payload = {
        "candidate_id": str(resolved_candidate_id),
        "source_id": resolved_source_id,
        "source_type": source_type,
        "content": resolved_content,
        "token_cost": int(token_cost if token_cost is not None else estimate_token_cost(resolved_content)),
        "provenance": resolved_provenance,
        "metadata": resolved_metadata,
        "content_hash": resolved_hash,
        "provider": provider,
        "source_offsets": source_offsets,
        "temporal_validity": temporal_validity,
        "confidence": confidence,
        "extraction_type": extraction_type,
        "synthetic_source": synthetic_source,
    }
    return compact_dict(payload)
