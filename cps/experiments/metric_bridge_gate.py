from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from cps.experiments.decision import is_synthetic_diagnostic_scope
from cps.experiments.decision import normalize_diagnostic_scope
from cps.experiments.decision import normalize_metric_claim_level


CLAIM_LEVELS = (
    "engineering_compatibility_only",
    "engineering_smoke_only",
    "replayable_artifact_evidence",
    "vinfo_proxy_supported",
    "calibrated_proxy_supported",
    "operational_utility_only",
    "ambiguous_metric",
    "pilot_only",
    "measurement_validated",
)
BRIDGE_REASON_ORDER = (
    "contamination_failed",
    "missing_required_artifacts",
    "missing_projection_bundles",
    "missing_metric_bridge",
    "stale_metric_bridge",
    "missing_human_labels",
    "missing_kappa",
    "operational_metric_class_only",
    "operational_diagnostic_claim_only",
    "synthetic_only_not_deployed_certification",
    "engineering_evidence_only",
    "complete_artifacts_not_validation",
    "live_api_not_validation",
    "external_runtime_not_validation",
    "operator_required_phase",
)
BRIDGE_DENIED_CLAIMS = (
    "measurement_validated",
    "scientific_validation",
    "deployed_v_information_certification",
    "deployed_v_information_submodularity_certified",
    "runtime_integration_complete",
)


def _ordered_reason_codes(reasons: set[str]) -> list[str]:
    order = {reason: index for index, reason in enumerate(BRIDGE_REASON_ORDER)}
    return sorted(reasons, key=lambda reason: (order.get(reason, len(order)), reason))


def _normal_mode(value: Any) -> str:
    mode = str(value or "engineering_only")
    aliases = {
        "engineering_only": "engineering_compatibility_only",
        "engineering_smoke": "engineering_smoke_only",
        "provider_offline_smoke": "engineering_smoke_only",
        "synthetic": "synthetic_structural_only",
        "synthetic_structural": "synthetic_structural_only",
        "structural_synthetic_only": "synthetic_structural_only",
    }
    return aliases.get(mode, normalize_metric_claim_level(mode))


def _base_claim_level(payload: Mapping[str, Any]) -> str:
    mode = _normal_mode(payload.get("evidence_mode"))
    if mode in CLAIM_LEVELS:
        return mode
    if is_synthetic_diagnostic_scope(mode):
        return "ambiguous_metric"
    if bool(payload.get("replay_available")):
        return "replayable_artifact_evidence"
    return "ambiguous_metric"


def _evidence_scope(payload: Mapping[str, Any], evidence_mode: str) -> str:
    scope = payload.get("evidence_scope") or payload.get("diagnostic_scope") or evidence_mode
    normalized = normalize_diagnostic_scope(scope)
    if is_synthetic_diagnostic_scope(normalized) or str(payload.get("metric_class")) == "synthetic_oracle":
        return "synthetic_structural_only"
    return normalized


def evaluate_metric_bridge_gate(evidence: Mapping[str, Any]) -> dict[str, Any]:
    payload = deepcopy(dict(evidence))
    metric_bridge_witness_count = int(payload.get("metric_bridge_witness_count", 0) or 0)
    bridge_freshness = str(payload.get("bridge_freshness", "missing") or "missing")
    metric_class = str(payload.get("metric_class", "unknown") or "unknown")
    diagnostic_claim_level = normalize_metric_claim_level(
        payload.get("diagnostic_claim_level", "ambiguous_metric")
    )
    contamination_status = str(payload.get("contamination_status", "unknown") or "unknown")
    raw_evidence_mode = str(payload.get("evidence_mode", "") or "")
    evidence_mode = _normal_mode(payload.get("evidence_mode"))
    evidence_scope = _evidence_scope(payload, evidence_mode)
    required_artifacts_present = bool(payload.get("required_artifacts_present", False))
    projection_bundle_count = int(payload.get("projection_bundle_count", 0) or 0)
    p04_status = str(payload.get("p04_status", "BLOCKED_OPERATOR_REQUIRED") or "BLOCKED_OPERATOR_REQUIRED")
    p09_status = str(payload.get("p09_status", "BLOCKED_OPERATOR_REQUIRED") or "BLOCKED_OPERATOR_REQUIRED")

    reasons: set[str] = set()
    denied_claims = set(BRIDGE_DENIED_CLAIMS)

    if contamination_status == "failed":
        reasons.add("contamination_failed")
    if not required_artifacts_present:
        reasons.add("missing_required_artifacts")
    if projection_bundle_count <= 0 or "projection_bundles" in set(payload.get("missing_required_artifacts", [])):
        reasons.add("missing_projection_bundles")
    if metric_bridge_witness_count <= 0 or bridge_freshness == "missing":
        reasons.add("missing_metric_bridge")
    if bridge_freshness == "stale":
        reasons.add("stale_metric_bridge")
    if not bool(payload.get("human_labels_present", False)):
        reasons.add("missing_human_labels")
    if not bool(payload.get("kappa_present", False)):
        reasons.add("missing_kappa")
    if metric_class == "operational_only":
        reasons.add("operational_metric_class_only")
    synthetic_evidence_mode = (
        "synthetic" in raw_evidence_mode
        or metric_class == "synthetic_oracle"
        or is_synthetic_diagnostic_scope(evidence_scope)
    )
    if diagnostic_claim_level == "operational_utility_only":
        reasons.add("operational_diagnostic_claim_only")
    if synthetic_evidence_mode:
        reasons.add("synthetic_only_not_deployed_certification")
    if evidence_mode.startswith("engineering"):
        reasons.add("engineering_evidence_only")
    if "BLOCKED" in p04_status or "OPERATOR" in p04_status or "BLOCKED" in p09_status or "OPERATOR" in p09_status:
        reasons.add("operator_required_phase")

    measurement_validation_evidence_present = bool(payload.get("measurement_validation_evidence_present", False))
    measurement_validated_allowed = (
        contamination_status == "passed"
        and bool(payload.get("human_labels_present", False))
        and bool(payload.get("kappa_present", False))
        and bridge_freshness == "fresh"
        and metric_bridge_witness_count > 0
        and required_artifacts_present
        and projection_bundle_count > 0
        and metric_class != "operational_only"
        and diagnostic_claim_level != "operational_utility_only"
        and not synthetic_evidence_mode
        and not evidence_mode.startswith("engineering")
        and measurement_validation_evidence_present
        and p04_status == "ACCEPT"
    )
    if required_artifacts_present and projection_bundle_count > 0 and not measurement_validated_allowed:
        reasons.add("complete_artifacts_not_validation")
    if bool(payload.get("live_api_used", False)) and not measurement_validated_allowed:
        reasons.add("live_api_not_validation")
    if bool(payload.get("external_runtime_used", False)) and not measurement_validated_allowed:
        reasons.add("external_runtime_not_validation")

    if measurement_validated_allowed:
        denied_claims.discard("measurement_validated")
        denied_claims.discard("scientific_validation")
        allowed_bridge_claim_level = "measurement_validated"
        bridge_gate_status = "eligible_for_measurement_review"
    elif "contamination_failed" in reasons:
        allowed_bridge_claim_level = "pilot_only"
        bridge_gate_status = "failed"
    elif "missing_projection_bundles" in reasons or "missing_required_artifacts" in reasons:
        allowed_bridge_claim_level = "ambiguous_metric"
        bridge_gate_status = "artifact_incomplete"
    elif "missing_metric_bridge" in reasons:
        allowed_bridge_claim_level = "ambiguous_metric"
        bridge_gate_status = "missing_bridge"
    elif "stale_metric_bridge" in reasons:
        allowed_bridge_claim_level = "operational_utility_only"
        bridge_gate_status = "stale_bridge"
    elif synthetic_evidence_mode:
        allowed_bridge_claim_level = "ambiguous_metric"
        bridge_gate_status = "evidence_limited"
    else:
        base_claim_level = _base_claim_level(payload)
        if (
            "operational_metric_class_only" in reasons
            or "operational_diagnostic_claim_only" in reasons
            or base_claim_level == "measurement_validated"
        ):
            allowed_bridge_claim_level = "operational_utility_only"
        else:
            allowed_bridge_claim_level = base_claim_level
        bridge_gate_status = (
            "evidence_limited"
            if reasons - {"complete_artifacts_not_validation", "operator_required_phase"}
            else "eligible_for_measurement_review"
        )

    reason_codes = _ordered_reason_codes(reasons)
    summary = (
        f"bridge_gate_status={bridge_gate_status}; "
        f"allowed_bridge_claim_level={allowed_bridge_claim_level}; "
        f"measurement_validated_allowed={str(measurement_validated_allowed).lower()}; "
        f"reason_codes={','.join(reason_codes) if reason_codes else 'none'}; "
        f"P04 remains {p04_status}; P09 remains {p09_status}"
    )
    return {
        "bridge_gate_status": bridge_gate_status,
        "allowed_bridge_claim_level": allowed_bridge_claim_level,
        "denied_claims": sorted(denied_claims),
        "reason_codes": reason_codes,
        "reason_code_order": list(BRIDGE_REASON_ORDER),
        "measurement_validated_allowed": measurement_validated_allowed,
        "evidence_scope": evidence_scope,
        "p04_status": p04_status,
        "p09_status": p09_status,
        "summary": summary,
    }
