from __future__ import annotations

from typing import Any

from cps.providers.common import (
    compact_dict,
    first_field,
    merge_mapping_fields,
    native_candidate_payload,
)


def _content(record: Any) -> str:
    return str(
        first_field(
            record,
            ("text", "extracted_text", "extraction_text", "content", "value"),
            default="",
        )
    )


def _offsets(record: Any) -> dict[str, int] | None:
    start = first_field(record, ("start_char", "char_start", "start", "begin"))
    end = first_field(record, ("end_char", "char_end", "end", "stop"))
    if start is None or end is None:
        return None
    return {"start": int(start), "end": int(end)}


def _document_id(record: Any, document_id: str | None) -> str | None:
    value = document_id or first_field(
        record,
        ("document_id", "doc_id", "source_document_id", "source_id"),
    )
    return None if value is None else str(value)


def _source_id(record: Any, *, document_id: str | None, offsets: dict[str, int] | None) -> str | None:
    explicit = first_field(record, ("uuid", "id", "span_id", "extraction_id"))
    if explicit is not None:
        return str(explicit)
    if document_id and offsets:
        return f"{document_id}:{offsets['start']}:{offsets['end']}"
    return document_id


def _confidence(record: Any) -> float | None:
    value = first_field(record, ("confidence", "score", "probability"))
    return None if value is None else float(value)


def _extraction_type(record: Any) -> str | None:
    value = first_field(record, ("label", "type", "extraction_type", "class_name", "category"))
    return None if value is None else str(value)


def _metadata(record: Any) -> dict[str, Any]:
    return merge_mapping_fields(record, ("metadata", "attributes"))


def _provenance(
    record: Any,
    *,
    document_id: str | None,
    offsets: dict[str, int] | None,
) -> dict[str, Any]:
    provenance = merge_mapping_fields(record, ("provenance",))
    if document_id is not None:
        provenance["document_id"] = document_id
    if offsets is not None:
        provenance["source_offsets"] = offsets
    return provenance


def _langextract_candidate(
    record: Any,
    *,
    source_type: str,
    document_id: str | None = None,
    token_cost: int | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    resolved_document_id = _document_id(record, document_id)
    offsets = _offsets(record)
    return native_candidate_payload(
        provider="langextract",
        source_type=source_type,
        source_id=_source_id(record, document_id=resolved_document_id, offsets=offsets),
        content=_content(record),
        token_cost=token_cost,
        candidate_id=candidate_id,
        provenance=_provenance(record, document_id=resolved_document_id, offsets=offsets),
        metadata=_metadata(record),
        source_offsets=offsets,
        confidence=_confidence(record),
        extraction_type=_extraction_type(record),
    )


def langextract_span_to_candidate(
    span: Any,
    *,
    document_id: str | None = None,
    token_cost: int | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    return _langextract_candidate(
        span,
        source_type="langextract_span",
        document_id=document_id,
        token_cost=token_cost,
        candidate_id=candidate_id,
    )


def langextract_extraction_to_candidate(
    extraction: Any,
    *,
    document_id: str | None = None,
    token_cost: int | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    return _langextract_candidate(
        extraction,
        source_type="langextract_extraction",
        document_id=document_id,
        token_cost=token_cost,
        candidate_id=candidate_id,
    )


def langextract_record_to_candidate(
    record: Any,
    *,
    document_id: str | None = None,
    token_cost: int | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    return _langextract_candidate(
        record,
        source_type="langextract_record",
        document_id=document_id,
        token_cost=token_cost,
        candidate_id=candidate_id,
    )
