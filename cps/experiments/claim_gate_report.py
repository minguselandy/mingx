from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.metric_bridge_gate import BRIDGE_REASON_ORDER, evaluate_metric_bridge_gate


CLAIM_LEVELS = (
    "engineering_compatibility_only",
    "engineering_smoke_only",
    "replayable_artifact_evidence",
    "synthetic_structural_only",
    "operational_utility_only",
    "ambiguous",
    "pilot_only",
    "measurement_validated",
)
REASON_ORDER = (
    *BRIDGE_REASON_ORDER,
    "external_runtime_not_used",
)
DENIED_CLAIMS = (
    "measurement_validated",
    "scientific_validation",
    "deployed_v_information_certification",
    "deployed_v_information_submodularity_certified",
    "runtime_integration_complete",
)


def _ordered_reason_codes(reasons: set[str]) -> list[str]:
    order = {reason: index for index, reason in enumerate(REASON_ORDER)}
    return sorted(reasons, key=lambda reason: (order.get(reason, len(order)), reason))


def _stable_write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


def _base_claim_level(ledger: Mapping[str, Any]) -> str:
    mode = str(ledger.get("evidence_mode") or "ambiguous")
    if mode in CLAIM_LEVELS:
        return mode
    if mode in {"engineering_smoke", "provider_offline_smoke"}:
        return "engineering_smoke_only"
    if mode in {"engineering_compatibility", "provider_normalizer"}:
        return "engineering_compatibility_only"
    if mode in {"synthetic", "synthetic_structural"}:
        return "synthetic_structural_only"
    if bool(ledger.get("replay_available")):
        return "replayable_artifact_evidence"
    return "ambiguous"


def build_claim_gate_report(ledger: Mapping[str, Any]) -> dict[str, Any]:
    payload = deepcopy(dict(ledger))
    metric_bridge_gate = evaluate_metric_bridge_gate(payload)
    reasons: set[str] = set(metric_bridge_gate["reason_codes"])
    denied_claims = set(DENIED_CLAIMS) | set(metric_bridge_gate["denied_claims"])
    contamination_status = str(payload.get("contamination_status", "unknown"))
    bridge_freshness = str(payload.get("bridge_freshness", "missing"))
    p04_status = str(payload.get("p04_status", "BLOCKED_OPERATOR_REQUIRED"))
    p09_status = str(payload.get("p09_status", "BLOCKED_OPERATOR_REQUIRED"))

    if contamination_status == "failed":
        reasons.add("contamination_failed")
    if not bool(payload.get("required_artifacts_present")):
        reasons.add("missing_required_artifacts")
    if int(payload.get("projection_bundle_count", 0) or 0) <= 0 or "projection_bundles" in set(
        payload.get("missing_required_artifacts", [])
    ):
        reasons.add("missing_projection_bundles")
    if int(payload.get("metric_bridge_witness_count", 0) or 0) <= 0 or bridge_freshness == "missing":
        reasons.add("missing_metric_bridge")
    if bridge_freshness == "stale":
        reasons.add("stale_metric_bridge")
    if not bool(payload.get("human_labels_present", False)):
        reasons.add("missing_human_labels")
    if not bool(payload.get("kappa_present", False)):
        reasons.add("missing_kappa")

    mode = str(payload.get("evidence_mode", "ambiguous"))
    metric_claim_levels = set((payload.get("metric_claim_level_counts") or {}).keys())
    if "synthetic" in mode or "structural_synthetic_only" in metric_claim_levels:
        reasons.add("synthetic_only_not_deployed_certification")
    if mode.startswith("engineering") or "engineering_smoke_only" in metric_claim_levels:
        reasons.add("engineering_evidence_only")
    if "BLOCKED" in p04_status or "OPERATOR" in p04_status or "BLOCKED" in p09_status or "OPERATOR" in p09_status:
        reasons.add("operator_required_phase")
    if not bool(payload.get("external_runtime_used", False)):
        reasons.add("external_runtime_not_used")

    measurement_validated_allowed = bool(metric_bridge_gate["measurement_validated_allowed"])
    if measurement_validated_allowed:
        allowed_claim_level = "measurement_validated"
        denied_claims.discard("measurement_validated")
        denied_claims.discard("scientific_validation")
    elif contamination_status == "failed":
        allowed_claim_level = "pilot_only"
    elif "missing_required_artifacts" in reasons or "missing_projection_bundles" in reasons:
        allowed_claim_level = "ambiguous"
    else:
        allowed_claim_level = _base_claim_level(payload)
        if allowed_claim_level == "measurement_validated":
            allowed_claim_level = "ambiguous"
        if bridge_freshness in {"missing", "stale"} and allowed_claim_level == "replayable_artifact_evidence":
            allowed_claim_level = "operational_utility_only"

    reason_codes = _ordered_reason_codes(reasons)
    summary = (
        f"allowed_claim_level={allowed_claim_level}; "
        f"measurement_validated_allowed={str(measurement_validated_allowed).lower()}; "
        f"reason_codes={','.join(reason_codes) if reason_codes else 'none'}; "
        f"P04 remains {p04_status}; P09 remains {p09_status}"
    )
    return {
        "allowed_claim_levels": list(CLAIM_LEVELS),
        "allowed_claim_level": allowed_claim_level,
        "denied_claims": sorted(denied_claims),
        "reason_codes": reason_codes,
        "reason_code_order": list(REASON_ORDER),
        "metric_bridge_gate_status": metric_bridge_gate["bridge_gate_status"],
        "allowed_bridge_claim_level": metric_bridge_gate["allowed_bridge_claim_level"],
        "metric_bridge_reason_codes": metric_bridge_gate["reason_codes"],
        "measurement_validated_allowed": measurement_validated_allowed,
        "p04_status": p04_status,
        "p09_status": p09_status,
        "summary": summary,
        "ledger": payload,
    }


def format_claim_gate_markdown(report: Mapping[str, Any]) -> str:
    reason_codes = list(report.get("reason_codes") or [])
    denied_claims = list(report.get("denied_claims") or [])
    lines = [
        "# Claim Gate Report",
        "",
        "## Summary",
        "",
        f"- Allowed claim level: `{report['allowed_claim_level']}`",
        f"- measurement_validated_allowed: {str(report['measurement_validated_allowed']).lower()}",
        f"- P04 status: `{report['p04_status']}`",
        f"- P09 status: `{report['p09_status']}`",
        f"- Metric bridge gate status: `{report.get('metric_bridge_gate_status', 'unknown')}`",
        f"- Allowed bridge claim level: `{report.get('allowed_bridge_claim_level', 'ambiguous')}`",
        "",
        "## Reason codes",
        "",
    ]
    if reason_codes:
        lines.extend(f"- `{reason}`" for reason in reason_codes)
    else:
        lines.append("- `none`")
    lines.extend(["", "## Denied claims", ""])
    if denied_claims:
        lines.extend(f"- `{claim}`" for claim in denied_claims)
    else:
        lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Metric bridge gate",
            "",
        ]
    )
    metric_bridge_reason_codes = list(report.get("metric_bridge_reason_codes") or [])
    if metric_bridge_reason_codes:
        lines.extend(f"- `{reason}`" for reason in metric_bridge_reason_codes)
    else:
        lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "- This report is an audit/reporting artifact only.",
            "- It does not run live APIs, run live cohort, or perform external runtime integration.",
            "- It does not certify deployed V-information submodularity.",
            "- It does not unblock P04 or P09.",
            "- It does not claim measurement validation.",
            "",
        ]
    )
    return "\n".join(lines)


def write_claim_gate_outputs(
    output_dir: str | Path,
    ledger: Mapping[str, Any],
    report: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    resolved_output_dir = Path(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    resolved_report = build_claim_gate_report(ledger) if report is None else deepcopy(dict(report))
    ledger_path = _stable_write_json(resolved_output_dir / "evidence_ledger.json", deepcopy(dict(ledger)))
    report_path = _stable_write_json(resolved_output_dir / "claim_gate_report.json", resolved_report)
    markdown_path = resolved_output_dir / "claim_gate_report.md"
    markdown_path.write_text(format_claim_gate_markdown(resolved_report), encoding="utf-8")
    return {
        "ledger_json": str(ledger_path),
        "report_json": str(report_path),
        "report_markdown": str(markdown_path),
        "evidence_ledger_path": str(ledger_path),
        "claim_gate_report_path": str(report_path),
        "claim_gate_markdown_path": str(markdown_path),
    }
