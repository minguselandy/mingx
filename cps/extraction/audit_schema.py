from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from cps.experiments.artifacts import stable_hash


REQUIRED_EXTRACTION_STRATA = {
    "simple_factual",
    "complex_conditional",
    "qualifier_heavy",
    "temporal_scope",
    "cross_chunk",
    "long_tail_entity",
    "high_provenance_value",
    "prerequisite",
    "contradictory",
    "adversarial",
}
ALLOWED_EXTRACTION_LABELS = {
    "captured",
    "captured_core_preserved",
    "captured_core_materially_changed",
    "missing",
    "lost_qualifier",
    "temporal_scope_error",
    "provenance_loss",
    "selector_impact",
}
CLAIM_LEVEL = "model_adjudicated_extraction_risk_evidence"
CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
AUDIT_VERSION = "v1_model_adjudicated_only"
RUBRIC_VERSION = "extraction_quality_audit_v1"
DENIED_CLAIMS = (
    "human_validated_extraction_measurement",
    "end_to_end_measurement_validation",
    "theorem_transfer_to_M_star",
    "measurement_validation",
    "metric_bridge_support",
    "calibrated_proxy_supported",
    "vinfo_proxy_supported",
    "paper_evidence",
    "selector_superiority",
    "global_selector_superiority",
    "route_5_unlock",
    "route_8_unlock",
)
RAW_RESPONSE_BODY_FIELDS = {
    "raw_api_response",
    "raw_api_response_body",
    "raw_api_response_payload",
    "raw_body",
    "raw_response",
    "raw_response_body",
    "raw_response_payload",
}
RAW_RESPONSE_FLAG_FIELDS = {
    "raw_api_responses_stored",
    "raw_response_stored",
    "store_raw_api_response",
}
FORBIDDEN_TRUE_FIELDS = {
    "calibrated_proxy_supported",
    "end_to_end_measurement_validation",
    "human_validated_extraction_measurement",
    "live_api_call_performed",
    "measurement_validation_claim",
    "metric_bridge_support",
    "paper_evidence_eligible",
    "route_5_unlock",
    "route_8_unlock",
    "selector_superiority_claim",
    "theorem_transfer_to_m_star",
    "vinfo_proxy_supported",
}


def _normalize_key(value: Any) -> str:
    normalized = str(value).strip().lower()
    for char in (" ", "-", "/"):
        normalized = normalized.replace(char, "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized


def _reject_raw_or_forbidden_payload(value: Any, *, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = _normalize_key(key_text)
            child_path = f"{path}.{key_text}"
            if normalized_key in RAW_RESPONSE_BODY_FIELDS:
                raise ValueError(f"raw_response body field is forbidden: {child_path}")
            if normalized_key in RAW_RESPONSE_FLAG_FIELDS and child is not False:
                raise ValueError(f"{child_path} must be false")
            if normalized_key in FORBIDDEN_TRUE_FIELDS and child is not False:
                raise ValueError(f"{child_path} must be false")
            _reject_raw_or_forbidden_payload(child, path=child_path)
    elif isinstance(value, list | tuple):
        for index, child in enumerate(value):
            _reject_raw_or_forbidden_payload(child, path=f"{path}[{index}]")


def _require_nonempty(data: Mapping[str, Any], field_name: str) -> str:
    value = str(data.get(field_name, "")).strip()
    if not value:
        raise ValueError(f"{field_name} is required")
    return value


@dataclass(frozen=True)
class ExtractionAuditRecord:
    record_id: str
    source_document_id: str
    source_document_hash: str
    source_span_hash: str
    extracted_item_id: str
    extracted_item_hash: str
    candidate_pool_hash: str
    stratum: str
    label: str
    label_source_kind: str
    judge_model_snapshot: str
    judge_prompt_hash: str
    rubric_version: str
    rubric_paraphrase_id: str
    order_swap: bool
    duplicate_index: int
    value_weight: float
    selector_impact: str
    allowed_claim_level: str = CLAIM_LEVEL
    claim_status: str = CLAIM_STATUS
    audit_diagnostic_only: bool = True
    measurement_validation_claim: bool = False
    metric_bridge_support: bool = False
    calibrated_proxy_supported: bool = False
    vinfo_proxy_supported: bool = False
    paper_evidence_eligible: bool = False
    selector_superiority_claim: bool = False
    raw_response_stored: bool = False
    live_api_call_performed: bool = False
    route_5_locked: bool = True
    route_8_locked: bool = True

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ExtractionAuditRecord:
        _reject_raw_or_forbidden_payload(payload)
        data = dict(payload)
        stratum = _normalize_key(data.get("stratum"))
        if stratum not in REQUIRED_EXTRACTION_STRATA:
            raise ValueError(f"stratum is not supported: {stratum}")
        label = _normalize_key(data.get("label"))
        if label not in ALLOWED_EXTRACTION_LABELS:
            raise ValueError(f"label is not supported: {label}")
        return cls(
            record_id=_require_nonempty(data, "record_id"),
            source_document_id=_require_nonempty(data, "source_document_id"),
            source_document_hash=_require_nonempty(data, "source_document_hash"),
            source_span_hash=_require_nonempty(data, "source_span_hash"),
            extracted_item_id=_require_nonempty(data, "extracted_item_id"),
            extracted_item_hash=_require_nonempty(data, "extracted_item_hash"),
            candidate_pool_hash=_require_nonempty(data, "candidate_pool_hash"),
            stratum=stratum,
            label=label,
            label_source_kind=str(data.get("label_source_kind", "model_adjudicated")),
            judge_model_snapshot=_require_nonempty(data, "judge_model_snapshot"),
            judge_prompt_hash=_require_nonempty(data, "judge_prompt_hash"),
            rubric_version=str(data.get("rubric_version", RUBRIC_VERSION)),
            rubric_paraphrase_id=str(data.get("rubric_paraphrase_id", "p0")),
            order_swap=bool(data.get("order_swap", False)),
            duplicate_index=int(data.get("duplicate_index", 0)),
            value_weight=float(data.get("value_weight", 1.0)),
            selector_impact=str(data.get("selector_impact", "candidate_pool_risk_only")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_extraction_audit_manifest(
    *,
    run_id: str,
    items: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    normalized_items = sorted(
        [{"item_id": str(item["item_id"])} for item in items],
        key=lambda row: row["item_id"],
    )
    manifest = {
        "run_id": str(run_id),
        "extraction_quality_audit_version": AUDIT_VERSION,
        "purpose": "measure_M_star_to_M_extraction_risk_as_operational_bottleneck",
        "required_strata": sorted(REQUIRED_EXTRACTION_STRATA),
        "allowed_labels": sorted(ALLOWED_EXTRACTION_LABELS),
        "metrics": [
            "capture_rate_by_stratum",
            "core_preserved_rate",
            "material_change_rate",
            "missing_rate",
            "qualifier_loss_rate",
            "temporal_scope_error_rate",
            "provenance_loss_rate",
            "value_weighted_loss_candidate",
        ],
        "controls": {
            "frozen_prompts": True,
            "prompt_hashes_required": True,
            "duplicate_judging": True,
            "order_swap": True,
            "raw_response_stored": False,
        },
        "items": normalized_items,
        "allowed_claim_level": CLAIM_LEVEL,
        "claim_status": CLAIM_STATUS,
        "denied_claims": list(DENIED_CLAIMS),
        "human_sentinel_audit": {
            "enabled_now": False,
            "current_evidence": False,
            "required_for_measurement_validation_candidate": True,
        },
        "audit_diagnostic_only": True,
        "raw_response_stored": False,
        "live_api_call_performed": False,
        "route_5_locked": True,
        "route_8_locked": True,
    }
    manifest["manifest_hash"] = stable_hash(manifest)
    return manifest
