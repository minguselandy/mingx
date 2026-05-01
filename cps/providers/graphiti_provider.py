from __future__ import annotations

from typing import Any

from cps.providers.common import (
    compact_dict,
    first_field,
    merge_mapping_fields,
    native_candidate_payload,
)


TEMPORAL_FIELDS = ("valid_at", "valid_from", "valid_to", "created_at")


def _content(record: Any) -> str:
    return str(
        first_field(
            record,
            ("content", "text", "summary", "fact", "description", "name"),
            default="",
        )
    )


def _source_id(record: Any) -> str | None:
    value = first_field(record, ("uuid", "id", "fact_id", "episode_id", "source_id"))
    return None if value is None else str(value)


def _temporal_validity(record: Any) -> dict[str, Any] | None:
    values = compact_dict({field: first_field(record, (field,)) for field in TEMPORAL_FIELDS})
    return values or None


def _confidence(record: Any) -> float | None:
    value = first_field(record, ("confidence", "score"))
    return None if value is None else float(value)


def _base_metadata(record: Any) -> dict[str, Any]:
    metadata = merge_mapping_fields(record, ("metadata", "attributes"))
    name = first_field(record, ("name",))
    if name is not None:
        metadata.setdefault("name", name)
    return metadata


def _base_provenance(record: Any, *, source_type: str, source_id: str | None) -> dict[str, Any]:
    provenance = merge_mapping_fields(record, ("provenance",))
    source = first_field(record, ("source", "source_id", "source_name"))
    episode_id = first_field(record, ("episode_id", "episode_uuid"))
    if source is not None:
        provenance["source"] = source
    if episode_id is not None:
        provenance["episode_id"] = episode_id
    if source_type == "graphiti_episode" and source_id is not None:
        provenance.setdefault("episode_id", source_id)
    return provenance


def _graphiti_candidate(
    record: Any,
    *,
    source_type: str,
    token_cost: int | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    source_id = _source_id(record)
    return native_candidate_payload(
        provider="graphiti",
        source_type=source_type,
        source_id=source_id,
        content=_content(record),
        token_cost=token_cost,
        candidate_id=candidate_id,
        provenance=_base_provenance(record, source_type=source_type, source_id=source_id),
        metadata=_base_metadata(record),
        temporal_validity=_temporal_validity(record),
        confidence=_confidence(record),
    )


def graphiti_fact_to_candidate(
    fact: Any,
    *,
    token_cost: int | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    return _graphiti_candidate(
        fact,
        source_type="graphiti_fact",
        token_cost=token_cost,
        candidate_id=candidate_id,
    )


def graphiti_episode_to_candidate(
    episode: Any,
    *,
    token_cost: int | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    return _graphiti_candidate(
        episode,
        source_type="graphiti_episode",
        token_cost=token_cost,
        candidate_id=candidate_id,
    )


def graphiti_record_to_candidate(
    record: Any,
    *,
    token_cost: int | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    return _graphiti_candidate(
        record,
        source_type="graphiti_record",
        token_cost=token_cost,
        candidate_id=candidate_id,
    )
