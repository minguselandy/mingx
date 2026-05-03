from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.claim_gate_report import build_claim_gate_report
from cps.experiments.contamination_audit import evaluate_contamination_audit
from cps.experiments.evidence_ledger import build_evidence_ledger_from_summary


EMPIRICAL_EVIDENCE_PACKAGE_SCHEMA_VERSION = "EmpiricalEvidencePackageV1"
SOURCE_PHASE = "P28"
REASON_CODE_ORDER = (
    "no_live_run",
    "live_run_without_labels",
    "missing_human_labels",
    "missing_kappa",
    "low_kappa",
    "contamination_failed",
    "contamination_unknown",
    "contamination_incomplete",
    "stale_metric_bridge",
    "missing_metric_bridge",
    "incomplete_artifacts",
    "live_api_alone_not_validation",
    "kappa_alone_not_validation",
    "contamination_pass_alone_not_validation",
    "fresh_metric_bridge_required",
    "claim_gate_allow_required",
    "operator_required_phase",
)
DENIED_CLAIMS = (
    "measurement_validated",
    "scientific_validation",
    "deployed_v_information_certification",
    "deployed_v_information_submodularity_certified",
    "runtime_integration_complete",
)


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _stable_write_json(path: str | Path, payload: Any) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_stable_json(payload), encoding="utf-8")
    return output_path


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ordered_reason_codes(reasons: set[str]) -> list[str]:
    order = {reason: index for index, reason in enumerate(REASON_CODE_ORDER)}
    return sorted(reasons, key=lambda reason: (order.get(reason, len(order)), reason))


def _default_completeness_report() -> dict[str, Any]:
    return {
        "labels_complete": False,
        "reason_codes": ["missing_human_labels", "incomplete_label_coverage"],
    }


def _default_kappa_report() -> dict[str, Any]:
    return {
        "human_labels_present": False,
        "labels_complete": False,
        "kappa_present": False,
        "kappa_status": "kappa_missing",
        "macro_average_kappa": None,
        "reason_codes": ["missing_human_labels", "missing_kappa"],
    }


def _default_contamination_report(run_id: str = "") -> dict[str, Any]:
    return evaluate_contamination_audit([], run_id=run_id)


def _load_source(source: Mapping[str, Any] | Path) -> dict[str, Any]:
    if isinstance(source, Mapping):
        return deepcopy(dict(source))
    source_dir = Path(source)
    payload: dict[str, Any] = {}
    for filename, key in (
        ("run_manifest.json", "run_manifest"),
        ("pilot_summary.json", "live_pilot_summary"),
        ("claim_gate_report.json", "source_claim_gate_report"),
        ("evidence_ledger.json", "source_evidence_ledger"),
        ("human_label_completeness_report.json", "human_label_completeness_report"),
        ("kappa_report.json", "kappa_report"),
        ("contamination_report.json", "contamination_report"),
    ):
        path = source_dir / filename
        if path.exists():
            payload[key] = _read_json(path)
    if "run_manifest" in payload and "run_id" not in payload:
        payload["run_id"] = payload["run_manifest"].get("run_id", "")
    if "source_evidence_ledger" in payload:
        payload.setdefault("metric_bridge_freshness", payload["source_evidence_ledger"].get("bridge_freshness"))
    if "live_pilot_summary" in payload:
        payload.setdefault("artifact_completeness_status", _artifact_status_from_pilot(payload["live_pilot_summary"]))
    return payload


def _artifact_status_from_pilot(pilot_summary: Mapping[str, Any]) -> str:
    case_count = int(pilot_summary.get("case_artifact_count", 0) or 0)
    dispatch_count = int(pilot_summary.get("dispatch_count", 0) or 0)
    return "complete" if case_count > 0 and case_count == dispatch_count else "incomplete"


def _live_pilot_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    summary = deepcopy(dict(source.get("live_pilot_summary") or source.get("pilot_summary") or {}))
    manifest = deepcopy(dict(source.get("run_manifest") or {}))
    if manifest and not summary:
        summary = {
            "run_id": manifest.get("run_id", ""),
            "evidence_level": manifest.get("evidence_level", "EV2_controlled_live_pilot"),
            "mode": manifest.get("mode", "dry_run"),
            "live_api_used": bool(manifest.get("live_api_used", False)),
            "external_runtime_used": bool(manifest.get("external_runtime_used", False)),
            "dispatch_count": 0,
            "case_artifact_count": 0,
            "conditions": list(manifest.get("conditions") or []),
            "human_labels_present": False,
            "kappa_present": False,
            "p04_status": manifest.get("p04_status", "deferred/operator-required"),
            "p09_status": manifest.get("p09_status", "BLOCKED_OPERATOR_REQUIRED"),
        }
    return summary


def _contamination_for_ledger(status: str) -> str:
    if status == "pass":
        return "passed"
    if status == "failed":
        return "failed"
    return "unknown"


def _metric_bridge_missing_reason(metric_bridge_freshness: str) -> str | None:
    if metric_bridge_freshness == "stale":
        return "stale_metric_bridge"
    if metric_bridge_freshness in {"missing", "", "unknown", "none"}:
        return "missing_metric_bridge"
    return None


def _build_empirical_claim_gate_report(
    *,
    run_id: str,
    live_api_used: bool,
    artifact_completeness_status: str,
    dispatch_count: int,
    human_labels_present: bool,
    kappa_present: bool,
    contamination_status: str,
    metric_bridge_freshness: str,
    p04_status: str,
    p09_status: str,
) -> dict[str, Any]:
    count = dispatch_count if artifact_completeness_status == "complete" else 0
    summary = {
        "run_id": run_id,
        "evidence_mode": "pilot_only" if live_api_used else "engineering_smoke_only",
        "source_phase": SOURCE_PHASE,
        "dispatch_count": count,
        "artifact_counts": {
            "candidate_pools": count,
            "projection_plans": count,
            "budget_witnesses": count,
            "materialized_contexts": count,
            "metric_bridge_witnesses": count,
            "diagnostics": count,
            "projection_bundles": count,
        },
        "contamination_status": _contamination_for_ledger(contamination_status),
        "human_labels_present": human_labels_present,
        "kappa_present": kappa_present,
        "bridge_freshness": metric_bridge_freshness,
        "metric_class": "measurement_candidate" if metric_bridge_freshness == "fresh" else "operational_only",
        "diagnostic_claim_level": (
            "measurement_validation_candidate" if metric_bridge_freshness == "fresh" else "operational_utility_only"
        ),
        "live_api_used": live_api_used,
        "external_runtime_used": False,
        "p04_status": p04_status,
        "p09_status": p09_status,
    }
    ledger = build_evidence_ledger_from_summary(
        summary,
        metric_bridge_witness_count=count,
        metric_class=summary["metric_class"],
        diagnostic_claim_level=summary["diagnostic_claim_level"],
        measurement_validation_evidence_present=True,
    )
    return build_claim_gate_report(ledger)


def _is_operator_ready(p04_status: str, p09_status: str) -> bool:
    return p04_status == "ACCEPT" and p09_status == "ACCEPT"


def _allowed_level(
    *,
    controlled_live_run_present: bool,
    human_labels_present: bool,
    labels_complete: bool,
    kappa_present: bool,
    kappa_status: str,
    contamination_status: str,
    metric_bridge_freshness: str,
    artifact_completeness_status: str,
    claim_gate_allows_measurement_validated: bool,
    operator_ready: bool,
) -> tuple[str, bool]:
    if not controlled_live_run_present:
        return "not_empirical_validation", False
    if contamination_status == "failed":
        return "pilot_only", False
    if kappa_status == "pilot_only":
        return "pilot_only", False
    if kappa_status == "weak_evidence_not_measurement_validated":
        return "weak_evidence_not_measurement_validated", False
    if metric_bridge_freshness == "stale":
        return "operational_utility_only", False
    if metric_bridge_freshness in {"missing", "", "unknown", "none"}:
        return "ambiguous", False
    if not human_labels_present or not labels_complete or not kappa_present:
        return "controlled_live_pilot_only", False
    if contamination_status in {"unknown", "incomplete"}:
        return "controlled_live_pilot_only", False
    if artifact_completeness_status != "complete":
        return "ambiguous", False
    if claim_gate_allows_measurement_validated and operator_ready:
        return "measurement_validated", True
    return "measurement_validated_candidate", False


def build_empirical_evidence_package(
    source: Mapping[str, Any] | Path,
    output_root: Path | None = None,
) -> dict[str, Any]:
    payload = _load_source(source)
    pilot_summary = _live_pilot_summary(payload)
    run_id = str(payload.get("run_id") or pilot_summary.get("run_id") or "")
    completeness_report = deepcopy(dict(payload.get("human_label_completeness_report") or _default_completeness_report()))
    kappa_report = deepcopy(dict(payload.get("kappa_report") or _default_kappa_report()))
    contamination_report = deepcopy(dict(payload.get("contamination_report") or _default_contamination_report(run_id)))

    live_api_used = bool(pilot_summary.get("live_api_used", False))
    controlled_live_run_present = live_api_used and str(pilot_summary.get("mode", "")) == "live_operator_approved"
    human_labels_present = bool(kappa_report.get("human_labels_present", False))
    labels_complete = bool(
        completeness_report.get("labels_complete", kappa_report.get("labels_complete", False))
    )
    kappa_present = bool(kappa_report.get("kappa_present", False))
    kappa_status = str(kappa_report.get("kappa_status", "kappa_missing") or "kappa_missing")
    macro_average_kappa = kappa_report.get("macro_average_kappa")
    contamination_status = str(contamination_report.get("contamination_status", "incomplete") or "incomplete")
    metric_bridge_freshness = str(payload.get("metric_bridge_freshness") or payload.get("bridge_freshness") or "missing")
    artifact_completeness_status = str(
        payload.get("artifact_completeness_status")
        or _artifact_status_from_pilot(pilot_summary)
        or "incomplete"
    )
    p04_status = str(payload.get("p04_status") or pilot_summary.get("p04_status") or "deferred/operator-required")
    p09_status = str(payload.get("p09_status") or pilot_summary.get("p09_status") or "BLOCKED_OPERATOR_REQUIRED")
    dispatch_count = int(pilot_summary.get("dispatch_count", 0) or 0)
    claim_gate_allows_measurement_validated = bool(
        payload.get("claim_gate_allows_measurement_validated", False)
        or (payload.get("source_claim_gate_report") or {}).get("measurement_validated_allowed", False)
    )
    empirical_claim_gate_report = _build_empirical_claim_gate_report(
        run_id=run_id,
        live_api_used=live_api_used,
        artifact_completeness_status=artifact_completeness_status,
        dispatch_count=dispatch_count,
        human_labels_present=human_labels_present,
        kappa_present=kappa_present,
        contamination_status=contamination_status,
        metric_bridge_freshness=metric_bridge_freshness,
        p04_status=p04_status,
        p09_status=p09_status,
    )
    operator_ready = _is_operator_ready(p04_status, p09_status)
    allowed_empirical_claim_level, measurement_validated_allowed = _allowed_level(
        controlled_live_run_present=controlled_live_run_present,
        human_labels_present=human_labels_present,
        labels_complete=labels_complete,
        kappa_present=kappa_present,
        kappa_status=kappa_status,
        contamination_status=contamination_status,
        metric_bridge_freshness=metric_bridge_freshness,
        artifact_completeness_status=artifact_completeness_status,
        claim_gate_allows_measurement_validated=claim_gate_allows_measurement_validated
        and bool(empirical_claim_gate_report.get("measurement_validated_allowed", False)),
        operator_ready=operator_ready,
    )

    reasons: set[str] = set()
    if not controlled_live_run_present:
        reasons.add("no_live_run")
    if controlled_live_run_present and not human_labels_present:
        reasons.add("live_run_without_labels")
    if not human_labels_present or not labels_complete:
        reasons.add("missing_human_labels")
    if not kappa_present:
        reasons.add("missing_kappa")
    if kappa_status in {"pilot_only", "weak_evidence_not_measurement_validated"} and kappa_present:
        reasons.add("low_kappa")
    if contamination_status == "failed":
        reasons.add("contamination_failed")
    if contamination_status == "unknown":
        reasons.add("contamination_unknown")
    if contamination_status == "incomplete":
        reasons.add("contamination_incomplete")
    bridge_reason = _metric_bridge_missing_reason(metric_bridge_freshness)
    if bridge_reason:
        reasons.add(bridge_reason)
    if artifact_completeness_status != "complete":
        reasons.add("incomplete_artifacts")
    if live_api_used and not measurement_validated_allowed:
        reasons.add("live_api_alone_not_validation")
    if kappa_present and not measurement_validated_allowed:
        reasons.add("kappa_alone_not_validation")
    if contamination_status == "pass" and not measurement_validated_allowed:
        reasons.add("contamination_pass_alone_not_validation")
    if metric_bridge_freshness != "fresh" and not measurement_validated_allowed:
        reasons.add("fresh_metric_bridge_required")
    if not measurement_validated_allowed:
        reasons.add("claim_gate_allow_required")
    if not operator_ready:
        reasons.add("operator_required_phase")

    denied_claims = set(DENIED_CLAIMS)
    if measurement_validated_allowed:
        denied_claims.discard("measurement_validated")
        denied_claims.discard("scientific_validation")

    package = {
        "empirical_evidence_package_schema_version": EMPIRICAL_EVIDENCE_PACKAGE_SCHEMA_VERSION,
        "run_id": run_id,
        "source_phase": SOURCE_PHASE,
        "evidence_level": "EV2_EV3_EV4_empirical_evidence_package",
        "live_api_used": live_api_used,
        "external_runtime_used": False,
        "controlled_live_run_present": controlled_live_run_present,
        "human_labels_present": human_labels_present,
        "labels_complete": labels_complete,
        "kappa_present": kappa_present,
        "kappa_status": kappa_status,
        "macro_average_kappa": macro_average_kappa,
        "contamination_status": contamination_status,
        "metric_bridge_freshness": metric_bridge_freshness,
        "artifact_completeness_status": artifact_completeness_status,
        "measurement_validated_allowed": measurement_validated_allowed,
        "allowed_empirical_claim_level": allowed_empirical_claim_level,
        "denied_claims": sorted(denied_claims),
        "reason_codes": _ordered_reason_codes(reasons),
        "reason_code_order": list(REASON_CODE_ORDER),
        "required_next_evidence": [
            "operator_approved_live_run" if not controlled_live_run_present else "controlled_live_run_present",
            "complete_human_labels",
            "acceptable_kappa",
            "contamination_pass",
            "fresh_metric_bridge",
            "claim_gate_allow",
            "P04_operator_review",
            "P09_operator_review_if_runtime_claims_are_needed",
        ],
        "p04_status": p04_status,
        "p09_status": p09_status,
        "live_pilot_summary": pilot_summary,
        "human_label_completeness_report": completeness_report,
        "kappa_report": kappa_report,
        "contamination_report": contamination_report,
        "empirical_claim_gate_report": empirical_claim_gate_report,
        "claim_boundary": (
            "P28 packages empirical evidence artifacts only. Live API success, high kappa, contamination pass, "
            "complete artifacts, and fresh metric bridge are not individually sufficient for measurement validation."
        ),
    }
    if output_root is not None:
        package["generated_outputs"] = write_empirical_evidence_package(output_root, package)
    return package


def format_empirical_evidence_summary_markdown(package: Mapping[str, Any]) -> str:
    payload = deepcopy(dict(package))
    lines = [
        "# Empirical Evidence Package",
        "",
        "## Summary",
        "",
        f"- Run id: `{payload.get('run_id', '')}`",
        f"- Evidence level: `{payload.get('evidence_level', '')}`",
        f"- Live API used: {str(bool(payload.get('live_api_used', False))).lower()}",
        f"- Controlled live run present: {str(bool(payload.get('controlled_live_run_present', False))).lower()}",
        f"- Human labels present: {str(bool(payload.get('human_labels_present', False))).lower()}",
        f"- Labels complete: {str(bool(payload.get('labels_complete', False))).lower()}",
        f"- Kappa present: {str(bool(payload.get('kappa_present', False))).lower()}",
        f"- Kappa status: `{payload.get('kappa_status', 'kappa_missing')}`",
        f"- Contamination status: `{payload.get('contamination_status', 'incomplete')}`",
        f"- Metric bridge freshness: `{payload.get('metric_bridge_freshness', 'missing')}`",
        f"- Allowed empirical claim level: `{payload.get('allowed_empirical_claim_level', 'ambiguous')}`",
        f"- measurement_validated_allowed: {str(bool(payload.get('measurement_validated_allowed', False))).lower()}",
        f"- P04 status: `{payload.get('p04_status', 'deferred/operator-required')}`",
        f"- P09 status: `{payload.get('p09_status', 'BLOCKED_OPERATOR_REQUIRED')}`",
        "",
        "## Reason Codes",
        "",
    ]
    reason_codes = list(payload.get("reason_codes") or [])
    if reason_codes:
        lines.extend(f"- `{reason}`" for reason in reason_codes)
    else:
        lines.append("- `none`")
    lines.extend(["", "## Denied Claims", ""])
    denied_claims = list(payload.get("denied_claims") or [])
    if denied_claims:
        lines.extend(f"- `{claim}`" for claim in denied_claims)
    else:
        lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- P28 packages empirical evidence but does not run live APIs.",
            "- P28 does not fabricate human labels or kappa.",
            "- Live API success alone is not measurement validation.",
            "- High kappa alone is not measurement validation.",
            "- Contamination pass alone is not measurement validation.",
            "- Fresh metric bridge and claim gate approval remain required.",
            "- P04 remains deferred/operator-required.",
            "- P09 remains BLOCKED_OPERATOR_REQUIRED.",
            "",
        ]
    )
    return "\n".join(lines)


def write_empirical_evidence_package(output_root: str | Path, package: Mapping[str, Any]) -> dict[str, str]:
    resolved_output_root = Path(output_root)
    resolved_output_root.mkdir(parents=True, exist_ok=True)
    payload = deepcopy(dict(package))
    manifest_payload = {
        key: value
        for key, value in payload.items()
        if key
        not in {
            "live_pilot_summary",
            "human_label_completeness_report",
            "kappa_report",
            "contamination_report",
            "empirical_claim_gate_report",
            "generated_outputs",
        }
    }
    manifest_path = _stable_write_json(resolved_output_root / "empirical_evidence_manifest.json", manifest_payload)
    live_pilot_path = _stable_write_json(
        resolved_output_root / "live_pilot_summary.json",
        payload.get("live_pilot_summary") or {},
    )
    completeness_path = _stable_write_json(
        resolved_output_root / "human_label_completeness_report.json",
        payload.get("human_label_completeness_report") or {},
    )
    kappa_path = _stable_write_json(resolved_output_root / "kappa_report.json", payload.get("kappa_report") or {})
    contamination_path = _stable_write_json(
        resolved_output_root / "contamination_report.json",
        payload.get("contamination_report") or {},
    )
    claim_gate_path = _stable_write_json(
        resolved_output_root / "empirical_claim_gate_report.json",
        payload.get("empirical_claim_gate_report") or {},
    )
    markdown_path = resolved_output_root / "empirical_evidence_summary.md"
    markdown_path.write_text(format_empirical_evidence_summary_markdown(payload), encoding="utf-8")
    return {
        "empirical_evidence_manifest_json": str(manifest_path.resolve()),
        "live_pilot_summary_json": str(live_pilot_path.resolve()),
        "human_label_completeness_report_json": str(completeness_path.resolve()),
        "kappa_report_json": str(kappa_path.resolve()),
        "contamination_report_json": str(contamination_path.resolve()),
        "empirical_claim_gate_report_json": str(claim_gate_path.resolve()),
        "empirical_evidence_summary_markdown": str(markdown_path.resolve()),
    }
