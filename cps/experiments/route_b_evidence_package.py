from __future__ import annotations

import json
import shutil
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.empirical_evidence_package import build_empirical_evidence_package
from cps.experiments.llm_assisted_prelabels import build_llm_assisted_prelabels
from cps.experiments.model_adjudicated_labels import build_model_adjudicated_labels
from cps.experiments.prelabel_subagent_audit import (
    build_human_review_queue,
    build_subagent_audit_report,
    build_subagent_audit_requests,
    write_prelabel_subagent_audit_outputs,
)


ROUTE_B_EVIDENCE_SCHEMA_VERSION = "RouteBModelAdjudicatedEvidencePackageV1"
ROUTE_B_CLAIM_GATE_SCHEMA_VERSION = "RouteBModelAdjudicatedClaimGateV1"
SOURCE_PHASE = "P41"
ROUTE_TYPE = "model_adjudicated"
EVALUATION_ROUTE = "Route_B_model_adjudicated"
LABEL_SOURCE = "model_adjudicated"
MAX_CLAIM = "model_adjudicated_pilot_only"
FALLBACK_CLAIM = "operational_utility_only"
PILOT_CEILING = "pilot_only"
DENIED_CLAIMS = (
    "measurement_validated",
    "human_labeled_validation",
    "human_human_kappa_established",
    "scientific_validation",
    "scientific_validation_completed",
    "deployed_v_information_certification",
    "deployed_v_information_submodularity_certified",
)
REASON_CODE_ORDER = (
    "route_b_model_adjudicated",
    "model_adjudicated_labels_not_human_labels",
    "codex_adjudication_not_human_review",
    "human_labels_not_required_for_route_b",
    "human_labels_missing_for_measurement_validation",
    "human_kappa_missing_for_measurement_validation",
    "measurement_validated_denied_for_route_b",
    "route_b_max_claim_boundary",
    "model_adjudicated_pilot_only",
    "contamination_failed",
    "contamination_unknown",
    "contamination_incomplete",
    "missing_metric_bridge",
    "stale_metric_bridge",
    "fresh_metric_bridge_required_for_stronger_claim",
    "incomplete_artifacts",
    "claim_gate_allow_required",
    "operator_required_phase",
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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _jsonl_count(path: Path) -> int:
    return len(_read_jsonl(path))


def _ordered_reason_codes(reasons: set[str]) -> list[str]:
    order = {reason: index for index, reason in enumerate(REASON_CODE_ORDER)}
    return sorted(reasons, key=lambda reason: (order.get(reason, len(order)), reason))


def _optional_json(source_dir: Path, filename: str) -> dict[str, Any]:
    path = source_dir / filename
    return _read_json(path) if path.exists() else {}


def _optional_jsonl(source_dir: Path, filename: str) -> list[dict[str, Any]]:
    path = source_dir / filename
    return _read_jsonl(path) if path.exists() else []


def _first_existing_count(source_dir: Path, *filenames: str) -> int:
    for filename in filenames:
        path = source_dir / filename
        if path.exists():
            return _jsonl_count(path)
    return 0


def _copy_alias(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return str(destination.resolve())


def _status_contamination_report(status: str) -> dict[str, Any]:
    if status == "pass":
        reason_codes: list[str] = []
    elif status == "failed":
        reason_codes = ["contamination_failed"]
    elif status == "unknown":
        reason_codes = ["contamination_unknown"]
    else:
        reason_codes = ["contamination_incomplete"]
    return {
        "contamination_status": status,
        "measurement_validated_allowed": False,
        "allowed_claim_impact": "not_measurement_validated",
        "reason_codes": reason_codes,
    }


def _source_payload(
    source_dir: Path,
    evidence_overrides: Mapping[str, Any] | None,
) -> dict[str, Any]:
    overrides = deepcopy(dict(evidence_overrides or {}))
    prelabel_count = _first_existing_count(source_dir, "model_prelabels.jsonl", "llm_prelabels.jsonl")
    model_label_count = _first_existing_count(source_dir, "model_adjudicated_labels.jsonl")
    codex_report = _optional_json(source_dir, "codex_adjudication_report.json")
    model_summary = _optional_json(source_dir, "model_adjudicated_label_summary.json")
    payload: dict[str, Any] = {
        "run_id": str(overrides.pop("run_id", model_summary.get("run_id") or codex_report.get("run_id") or "")),
        "route_type": ROUTE_TYPE,
        "evaluation_route": EVALUATION_ROUTE,
        "llm_prelabels_present": prelabel_count > 0,
        "llm_prelabel_count": prelabel_count,
        "subagent_audit_present": (source_dir / "subagent_audit_report.json").exists(),
        "codex_adjudication_report_present": bool(codex_report),
        "codex_adjudication_report": codex_report,
        "model_adjudicated_labels_present": model_label_count > 0,
        "model_adjudicated_label_count": model_label_count,
        "model_adjudicated_label_summary_present": bool(model_summary),
        "model_adjudicated_label_summary": model_summary,
        "live_pilot_summary": {
            "run_id": "",
            "mode": "dry_run",
            "live_api_used": False,
            "external_runtime_used": False,
            "dispatch_count": 0,
            "case_artifact_count": 0,
            "human_labels_present": False,
            "kappa_present": False,
            "p04_status": "deferred/operator-required",
            "p09_status": "BLOCKED_OPERATOR_REQUIRED",
        },
        "human_label_completeness_report": {
            "labels_complete": False,
            "reason_codes": ["human_labels_not_required_for_route_b"],
        },
        "kappa_report": {
            "human_labels_present": False,
            "labels_complete": False,
            "kappa_present": False,
            "kappa_status": "kappa_missing",
            "macro_average_kappa": None,
            "reason_codes": ["human_kappa_missing_for_measurement_validation"],
        },
        "metric_bridge_freshness": "missing",
        "artifact_completeness_status": "incomplete",
        "contamination_report": _status_contamination_report("incomplete"),
        "p04_status": "deferred/operator-required",
        "p09_status": "BLOCKED_OPERATOR_REQUIRED",
        "claim_gate_allows_measurement_validated": False,
    }
    if payload["run_id"]:
        payload["live_pilot_summary"]["run_id"] = payload["run_id"]
    contamination_status = overrides.pop("contamination_status", None)
    payload.update(overrides)
    if contamination_status is not None:
        payload["contamination_report"] = _status_contamination_report(str(contamination_status))
    return payload


def _load_replay_manifest(replay_package_dir: str | Path | None) -> dict[str, Any] | None:
    if replay_package_dir is None:
        return None
    resolved = Path(replay_package_dir)
    manifest_path = resolved / "manifest.json"
    if not manifest_path.exists():
        return None
    manifest = _read_json(manifest_path)
    if manifest.get("package_schema_version") != "ReplayEvidencePackageV1":
        return None
    return manifest


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def _agreement_diagnostics(
    *,
    source_dir: Path,
    codex_report: Mapping[str, Any],
    model_summary: Mapping[str, Any],
) -> dict[str, Any]:
    model_rows = _optional_jsonl(source_dir, "model_adjudicated_labels.jsonl")
    prelabel_rows = _optional_jsonl(source_dir, "model_prelabels.jsonl") or _optional_jsonl(
        source_dir,
        "llm_prelabels.jsonl",
    )
    total = int(codex_report.get("total_labels") or model_summary.get("total_labels") or len(model_rows))
    uncertain = int(codex_report.get("uncertain_count") or 0)
    rejected_or_blocking = int(codex_report.get("rejected_or_blocking_warning_count") or 0)
    accepted = int(codex_report.get("accepted_model_adjudicated_count") or max(0, total - uncertain - rejected_or_blocking))

    prelabel_by_key: dict[tuple[str, str, str], int] = {}
    for prelabel in prelabel_rows:
        for dimension, label_payload in dict(prelabel.get("dimension_labels") or {}).items():
            key = (
                str(prelabel.get("case_id", "")),
                str(prelabel.get("condition", "")),
                str(dimension),
            )
            if "suggested_label" in dict(label_payload):
                prelabel_by_key[key] = int(dict(label_payload)["suggested_label"])
    comparable = 0
    agreements = 0
    for row in model_rows:
        key = (
            str(row.get("case_id", "")),
            str(row.get("condition", "")),
            str(row.get("label_dimension", "")),
        )
        if key in prelabel_by_key and "label" in row:
            comparable += 1
            agreements += int(int(row["label"]) == prelabel_by_key[key])

    high_disagreement_queue_size = uncertain + rejected_or_blocking
    return {
        "model_model_agreement": _ratio(agreements, comparable),
        "model_model_agreement_comparable_labels": comparable,
        "model_adjudication_consistency": _ratio(accepted, total),
        "adjudication_disagreement_rate": _ratio(high_disagreement_queue_size, total),
        "high_disagreement_queue_size": high_disagreement_queue_size,
        "ambiguity_rate": _ratio(uncertain, total),
        "accepted_model_adjudicated_count": accepted,
        "uncertain_count": uncertain,
        "rejected_or_blocking_warning_count": rejected_or_blocking,
    }


def _allowed_route_b_claim_level(empirical_package: Mapping[str, Any]) -> str:
    if str(empirical_package.get("contamination_status", "incomplete")) == "failed":
        return PILOT_CEILING
    if str(empirical_package.get("allowed_empirical_claim_level")) == MAX_CLAIM:
        return MAX_CLAIM
    return FALLBACK_CLAIM


def _build_manifest(
    *,
    source_dir: Path,
    empirical_package: Mapping[str, Any],
    replay_manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    codex_report = dict(empirical_package.get("codex_adjudication_report") or {})
    if not codex_report:
        codex_report = _optional_json(source_dir, "codex_adjudication_report.json")
    model_summary = dict(empirical_package.get("model_adjudicated_label_summary") or {})
    diagnostics = _agreement_diagnostics(
        source_dir=source_dir,
        codex_report=codex_report,
        model_summary=model_summary,
    )
    reasons = set(empirical_package.get("reason_codes") or [])
    reasons.update(
        {
            "route_b_model_adjudicated",
            "model_adjudicated_labels_not_human_labels",
            "codex_adjudication_not_human_review",
            "human_labels_not_required_for_route_b",
            "human_labels_missing_for_measurement_validation",
            "human_kappa_missing_for_measurement_validation",
            "measurement_validated_denied_for_route_b",
            "route_b_max_claim_boundary",
        }
    )
    allowed_route_b_claim_level = _allowed_route_b_claim_level(empirical_package)
    if allowed_route_b_claim_level == MAX_CLAIM:
        reasons.add("model_adjudicated_pilot_only")
    if allowed_route_b_claim_level == PILOT_CEILING:
        reasons.add("contamination_failed")
    denied_claims = sorted(set(DENIED_CLAIMS) | set(empirical_package.get("denied_claims") or []))
    return {
        "route_b_evidence_schema_version": ROUTE_B_EVIDENCE_SCHEMA_VERSION,
        "source_phase": SOURCE_PHASE,
        "run_id": str(empirical_package.get("run_id", "")),
        "route_type": ROUTE_TYPE,
        "evaluation_route": EVALUATION_ROUTE,
        "label_source": LABEL_SOURCE,
        "live_api_used": bool(empirical_package.get("live_api_used", False)),
        "external_runtime_used": bool(empirical_package.get("external_runtime_used", False)),
        "human_labels_present": False,
        "kappa_present": False,
        "human_human_kappa_established": False,
        "measurement_validated_allowed": False,
        "max_claim": MAX_CLAIM,
        "allowed_route_b_claim_level": allowed_route_b_claim_level,
        "empirical_allowed_claim_level": str(empirical_package.get("allowed_empirical_claim_level", "ambiguous")),
        "contamination_status": str(empirical_package.get("contamination_status", "incomplete")),
        "metric_bridge_freshness": str(empirical_package.get("metric_bridge_freshness", "missing")),
        "artifact_completeness_status": str(empirical_package.get("artifact_completeness_status", "incomplete")),
        "llm_prelabels_present": bool(empirical_package.get("llm_prelabels_present", False)),
        "llm_prelabel_count": int(empirical_package.get("llm_prelabel_count", 0) or 0),
        "subagent_audit_present": bool(empirical_package.get("subagent_audit_present", False)),
        "codex_adjudication_report_present": bool(
            empirical_package.get("codex_adjudication_report_present", False)
        ),
        "model_adjudicated_labels_present": bool(
            empirical_package.get("model_adjudicated_labels_present", False)
        ),
        "model_adjudicated_label_count": int(
            empirical_package.get("model_adjudicated_label_count", 0) or 0
        ),
        "model_adjudicated_label_summary_present": bool(
            empirical_package.get("model_adjudicated_label_summary_present", False)
        ),
        "route_b_core_artifacts_present": bool(
            empirical_package.get("llm_prelabels_present", False)
            and empirical_package.get("subagent_audit_present", False)
            and empirical_package.get("model_adjudicated_labels_present", False)
        ),
        "replay_package_present": replay_manifest is not None,
        "replay_package_claim_scope": (
            str(replay_manifest.get("package_claim_scope", ""))
            if replay_manifest is not None
            else ""
        ),
        "replay_measurement_validated_allowed": (
            bool(replay_manifest.get("measurement_validated_allowed", False))
            if replay_manifest is not None
            else False
        ),
        **diagnostics,
        "denied_claims": denied_claims,
        "reason_codes": _ordered_reason_codes(reasons),
        "reason_code_order": list(REASON_CODE_ORDER),
        "p04_status": str(empirical_package.get("p04_status", "deferred/operator-required")),
        "p09_status": str(empirical_package.get("p09_status", "BLOCKED_OPERATOR_REQUIRED")),
        "claim_boundary": (
            "Route B model-adjudicated labels are not human labels; Codex/model adjudication is not "
            "human review; measurement_validated is denied."
        ),
    }


def _build_claim_gate_report(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "route_b_claim_gate_schema_version": ROUTE_B_CLAIM_GATE_SCHEMA_VERSION,
        "source_phase": SOURCE_PHASE,
        "run_id": str(manifest.get("run_id", "")),
        "route_type": ROUTE_TYPE,
        "evaluation_route": EVALUATION_ROUTE,
        "allowed_route_b_claim_level": str(manifest["allowed_route_b_claim_level"]),
        "max_claim": MAX_CLAIM,
        "measurement_validated_allowed": False,
        "human_labels_present": False,
        "kappa_present": False,
        "human_human_kappa_established": False,
        "denied_claims": list(manifest.get("denied_claims") or []),
        "reason_codes": list(manifest.get("reason_codes") or []),
        "reason_code_order": list(REASON_CODE_ORDER),
        "p04_status": str(manifest.get("p04_status", "deferred/operator-required")),
        "p09_status": str(manifest.get("p09_status", "BLOCKED_OPERATOR_REQUIRED")),
        "summary": (
            f"allowed_route_b_claim_level={manifest['allowed_route_b_claim_level']}; "
            "measurement_validated_allowed=false; "
            "human_labels_present=false; kappa_present=false"
        ),
    }


def build_route_b_evidence_package_from_artifact_dir(
    artifact_dir: str | Path,
    *,
    replay_package_dir: str | Path | None = None,
    evidence_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source_dir = Path(artifact_dir)
    source_payload = _source_payload(source_dir, evidence_overrides)
    empirical_package = build_empirical_evidence_package(source_payload)
    replay_manifest = _load_replay_manifest(replay_package_dir)
    manifest = _build_manifest(
        source_dir=source_dir,
        empirical_package=empirical_package,
        replay_manifest=replay_manifest,
    )
    claim_gate_report = _build_claim_gate_report(manifest)
    return {
        "route_b_evidence_schema_version": ROUTE_B_EVIDENCE_SCHEMA_VERSION,
        "manifest": manifest,
        "claim_gate_report": claim_gate_report,
        "empirical_evidence_package": empirical_package,
        "replay_package_manifest": deepcopy(dict(replay_manifest)) if replay_manifest is not None else None,
    }


def format_route_b_claim_gate_markdown(report: Mapping[str, Any]) -> str:
    reason_codes = list(report.get("reason_codes") or [])
    denied_claims = list(report.get("denied_claims") or [])
    lines = [
        "# Route B Claim Gate Report",
        "",
        "## Summary",
        "",
        f"- Allowed Route B claim level: `{report['allowed_route_b_claim_level']}`",
        f"- Maximum claim: `{report['max_claim']}`",
        f"- measurement_validated_allowed: {str(bool(report['measurement_validated_allowed'])).lower()}",
        f"- Human labels present: {str(bool(report['human_labels_present'])).lower()}",
        f"- Kappa present: {str(bool(report['kappa_present'])).lower()}",
        f"- P04 status: `{report['p04_status']}`",
        f"- P09 status: `{report['p09_status']}`",
        "",
        "## Reason Codes",
        "",
    ]
    lines.extend(f"- `{reason}`" for reason in reason_codes) if reason_codes else lines.append("- `none`")
    lines.extend(["", "## Denied Claims", ""])
    lines.extend(f"- `{claim}`" for claim in denied_claims) if denied_claims else lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Model-adjudicated labels are not human labels.",
            "- Codex/model adjudication is not human review.",
            "- LLM/Codex agreement is not human-human kappa.",
            "- measurement_validated is denied.",
            "- Route B supports only model-adjudicated pilot or operational utility evidence.",
            "- P04 remains deferred/operator-required.",
            "- P09 remains BLOCKED_OPERATOR_REQUIRED.",
            "",
        ]
    )
    return "\n".join(lines)


def format_route_b_evidence_summary_markdown(package: Mapping[str, Any]) -> str:
    manifest = dict(package["manifest"])
    lines = [
        "# Route B Model-Adjudicated Evidence Package",
        "",
        "## Summary",
        "",
        f"- Run id: `{manifest.get('run_id', '')}`",
        f"- Evaluation route: `{manifest['evaluation_route']}`",
        f"- Allowed Route B claim level: `{manifest['allowed_route_b_claim_level']}`",
        f"- measurement_validated_allowed: {str(bool(manifest['measurement_validated_allowed'])).lower()}",
        f"- Human labels present: {str(bool(manifest['human_labels_present'])).lower()}",
        f"- Kappa present: {str(bool(manifest['kappa_present'])).lower()}",
        f"- Route B core artifacts present: {str(bool(manifest['route_b_core_artifacts_present'])).lower()}",
        "",
        "## Diagnostics",
        "",
        f"- Model-model agreement: `{manifest.get('model_model_agreement')}`",
        f"- Model adjudication consistency: `{manifest.get('model_adjudication_consistency')}`",
        f"- Adjudication disagreement rate: `{manifest.get('adjudication_disagreement_rate')}`",
        f"- Ambiguity rate: `{manifest.get('ambiguity_rate')}`",
        "",
        "## Claim Boundary",
        "",
        "- Model-adjudicated labels are not human labels.",
        "- measurement_validated is denied.",
        "- No human-human kappa is established.",
        "",
    ]
    return "\n".join(lines)


def write_route_b_evidence_package(output_dir: str | Path, package: Mapping[str, Any]) -> dict[str, str]:
    resolved_output_dir = Path(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    payload = deepcopy(dict(package))
    manifest = deepcopy(dict(payload["manifest"]))
    claim_gate_report = deepcopy(dict(payload["claim_gate_report"]))
    manifest_path = _stable_write_json(resolved_output_dir / "route_b_evidence_manifest.json", manifest)
    claim_gate_path = _stable_write_json(
        resolved_output_dir / "route_b_claim_gate_report.json",
        claim_gate_report,
    )
    claim_gate_markdown_path = resolved_output_dir / "route_b_claim_gate_report.md"
    claim_gate_markdown_path.write_text(format_route_b_claim_gate_markdown(claim_gate_report), encoding="utf-8")
    summary_markdown_path = resolved_output_dir / "route_b_evidence_summary.md"
    summary_markdown_path.write_text(format_route_b_evidence_summary_markdown(payload), encoding="utf-8")
    return {
        "route_b_evidence_manifest_json": str(manifest_path.resolve()),
        "route_b_claim_gate_report_json": str(claim_gate_path.resolve()),
        "route_b_claim_gate_report_markdown": str(claim_gate_markdown_path.resolve()),
        "route_b_evidence_summary_markdown": str(summary_markdown_path.resolve()),
    }


def _write_model_prelabel_aliases(output_root: Path, prelabel_outputs: Mapping[str, str]) -> dict[str, str]:
    return {
        "model_prelabels_jsonl": _copy_alias(
            Path(prelabel_outputs["llm_prelabels_jsonl"]),
            output_root / "model_prelabels.jsonl",
        ),
        "model_prelabel_summary_json": _copy_alias(
            Path(prelabel_outputs["llm_prelabel_summary_json"]),
            output_root / "model_prelabel_summary.json",
        ),
        "model_prelabel_summary_markdown": _copy_alias(
            Path(prelabel_outputs["llm_prelabel_summary_markdown"]),
            output_root / "model_prelabel_summary.md",
        ),
    }


def build_route_b_dry_run_package(
    output_root: str | Path,
    *,
    case_artifacts: Sequence[Mapping[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    resolved_output_root = Path(output_root).resolve()
    prelabel_result = build_llm_assisted_prelabels(
        resolved_output_root,
        manifest={"prelabel_run_id": str(run_id), "mode": "dry_run"},
        case_artifacts=case_artifacts,
    )
    prelabel_outputs = dict(prelabel_result["generated_outputs"])
    model_prelabel_aliases = _write_model_prelabel_aliases(resolved_output_root, prelabel_outputs)
    prelabels = list(prelabel_result["prelabels"])
    audit_requests = build_subagent_audit_requests(prelabels, {}, prelabel_run_id=str(run_id))
    audit_report = build_subagent_audit_report(
        prelabels,
        audit_requests,
        [],
        prelabel_run_id=str(run_id),
    )
    human_review_queue = build_human_review_queue(prelabels, [], run_id=str(run_id))
    audit_outputs = write_prelabel_subagent_audit_outputs(
        resolved_output_root,
        audit_requests,
        audit_report,
        human_review_queue,
    )
    adjudication_result = build_model_adjudicated_labels(
        prelabels,
        subagent_audit_report=audit_report,
        human_review_queue=human_review_queue,
        run_id=str(run_id),
        output_root=resolved_output_root,
    )
    route_b_package = build_route_b_evidence_package_from_artifact_dir(
        resolved_output_root,
        evidence_overrides={"run_id": str(run_id)},
    )
    route_b_outputs = write_route_b_evidence_package(resolved_output_root, route_b_package)
    generated_outputs = {
        **prelabel_outputs,
        **model_prelabel_aliases,
        **audit_outputs,
        **dict(adjudication_result["generated_outputs"]),
        **route_b_outputs,
    }
    result = deepcopy(dict(route_b_package))
    result["generated_outputs"] = generated_outputs
    return result
