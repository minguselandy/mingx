from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from cps.extraction.audit_schema import CLAIM_LEVEL, CLAIM_STATUS, DENIED_CLAIMS, ExtractionAuditRecord
from cps.schema.projection_bundle_v1 import ClaimLedger


DENIED_EXTRACTION_CLAIMS = set(DENIED_CLAIMS)
CAPTURE_LABELS = {"captured", "captured_core_preserved"}
LOSS_LABELS = {
    "captured_core_materially_changed",
    "missing",
    "lost_qualifier",
    "temporal_scope_error",
    "provenance_loss",
    "selector_impact",
}


def _normalize_records(
    records: Iterable[ExtractionAuditRecord | Mapping[str, Any]],
) -> tuple[list[ExtractionAuditRecord], list[str]]:
    normalized: list[ExtractionAuditRecord] = []
    reason_codes: list[str] = []
    for record in records:
        if isinstance(record, ExtractionAuditRecord):
            normalized.append(record)
            continue
        try:
            normalized.append(ExtractionAuditRecord.from_dict(record))
        except (TypeError, ValueError):
            reason_codes.append("invalid_record")
    return normalized, sorted(set(reason_codes))


def _rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return count / total


def _metrics(records: list[ExtractionAuditRecord]) -> dict[str, Any]:
    total = len(records)
    by_stratum: dict[str, list[ExtractionAuditRecord]] = defaultdict(list)
    for record in records:
        by_stratum[record.stratum].append(record)
    capture_rate_by_stratum = {
        stratum: _rate(
            sum(1 for record in rows if record.label in CAPTURE_LABELS),
            len(rows),
        )
        for stratum, rows in sorted(by_stratum.items())
    }
    label_counts = Counter(record.label for record in records)
    total_weight = sum(record.value_weight for record in records)
    loss_weight = sum(
        record.value_weight for record in records if record.label in LOSS_LABELS
    )
    return {
        "capture_rate_by_stratum": capture_rate_by_stratum,
        "core_preserved_rate": _rate(label_counts["captured_core_preserved"], total),
        "material_change_rate": _rate(
            label_counts["captured_core_materially_changed"],
            total,
        ),
        "missing_rate": _rate(label_counts["missing"], total),
        "qualifier_loss_rate": _rate(label_counts["lost_qualifier"], total),
        "temporal_scope_error_rate": _rate(label_counts["temporal_scope_error"], total),
        "provenance_loss_rate": _rate(label_counts["provenance_loss"], total),
        "selector_impact_rate": _rate(label_counts["selector_impact"], total),
        "value_weighted_loss_candidate": (loss_weight / total_weight)
        if total_weight
        else 0.0,
    }


def evaluate_extraction_claim_gate(
    records: Iterable[ExtractionAuditRecord | Mapping[str, Any]],
) -> dict[str, Any]:
    normalized_records, reason_codes = _normalize_records(records)
    if not normalized_records and not reason_codes:
        reason_codes.append("no_records")
        final_gate_status = "suppressed_no_records"
        allowed_claims: list[str] = []
    elif reason_codes:
        final_gate_status = "downgraded_to_ambiguous"
        allowed_claims = []
    else:
        final_gate_status = "model_adjudicated_extraction_risk_ready"
        allowed_claims = [CLAIM_LEVEL]

    return {
        "claim_status": CLAIM_STATUS,
        "allowed_claims": allowed_claims,
        "denied_claims": sorted(DENIED_EXTRACTION_CLAIMS),
        "final_gate_status": final_gate_status,
        "reason_codes": sorted(set(reason_codes)),
        "audit_diagnostic_only": True,
        "measurement_validation_claim": False,
        "metric_bridge_support": False,
        "calibrated_proxy_supported": False,
        "vinfo_proxy_supported": False,
        "paper_evidence_eligible": False,
        "selector_superiority_claim": False,
        "raw_response_stored": False,
        "live_api_call_performed": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "metrics": _metrics(normalized_records),
    }


@dataclass(frozen=True)
class ExtractionRiskLedger:
    records: tuple[ExtractionAuditRecord, ...]
    claim_gate: dict[str, Any]
    human_sentinel_audit: dict[str, Any]

    def claim_ledger(self) -> ClaimLedger:
        return ClaimLedger.from_dict(
            {
                "claim_candidate": "extraction_quality_audit_framework",
                "metric_claim_level": "operational_utility_only",
                "bridge_status": "not_applicable",
                "judge_status": "model_adjudicated_extraction_risk_only",
                "artifact_status": "framework_only",
                "raw_response_stored": False,
                "human_external_gold_label": False,
                "current_claim_level": CLAIM_STATUS,
                "allowed_claims": [CLAIM_LEVEL]
                if self.claim_gate["allowed_claims"]
                else [],
                "denied_claims": sorted(DENIED_EXTRACTION_CLAIMS),
                "claim_upgrade": False,
                "route_5_locked": True,
                "route_8_locked": True,
            },
            artifact_status="complete",
        )

    def to_dict(self, *, include_claim_ledger: bool = False) -> dict[str, Any]:
        payload = {
            "records": [record.to_dict() for record in self.records],
            "record_count": len(self.records),
            "claim_status": CLAIM_STATUS,
            "allowed_claims": list(self.claim_gate["allowed_claims"]),
            "denied_claims": sorted(DENIED_EXTRACTION_CLAIMS),
            "final_gate_status": self.claim_gate["final_gate_status"],
            "reason_codes": list(self.claim_gate["reason_codes"]),
            "human_sentinel_audit": dict(self.human_sentinel_audit),
            "metrics": dict(self.claim_gate["metrics"]),
            "audit_diagnostic_only": True,
            "raw_response_stored": False,
            "live_api_call_performed": False,
            "route_5_locked": True,
            "route_8_locked": True,
        }
        if include_claim_ledger:
            payload["claim_ledger"] = self.claim_ledger().to_dict()
        return payload


def build_extraction_risk_ledger(
    records: Iterable[ExtractionAuditRecord | Mapping[str, Any]],
) -> ExtractionRiskLedger:
    normalized_records, _ = _normalize_records(records)
    gate = evaluate_extraction_claim_gate(normalized_records)
    return ExtractionRiskLedger(
        records=tuple(normalized_records),
        claim_gate=gate,
        human_sentinel_audit={
            "enabled_now": False,
            "current_evidence": False,
            "future_optional": True,
            "required_for_measurement_validation_candidate": True,
        },
    )
