from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.claim_gate_report import build_claim_gate_report, format_claim_gate_markdown
from cps.experiments.evidence_ledger import (
    REQUIRED_EVIDENCE_ARTIFACTS,
    build_evidence_ledger_from_artifact_dir,
    build_evidence_ledger_from_summary,
)
from cps.experiments.proxy_regime_matrix import (
    build_proxy_regime_matrix_from_artifact_dir,
    format_proxy_regime_matrix_markdown,
)


PACKAGE_SCHEMA_VERSION = "ReplayEvidencePackageV1"
CLAIM_BOUNDARY_WARNING = (
    "Replay package completeness is not scientific validation; "
    "measurement_validated is not claimed; "
    "synthetic success is not deployed V-information certification; "
    "P04 remains BLOCKED_OPERATOR_REQUIRED; "
    "P09 remains BLOCKED_OPERATOR_REQUIRED"
)


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _stable_write_json(path: str | Path, payload: Any) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_stable_json(payload), encoding="utf-8")
    return output_path


def _artifact_counts(ledger: Mapping[str, Any]) -> dict[str, int]:
    source_counts = dict(ledger.get("artifact_counts") or {})
    return {name: int(source_counts.get(name, 0) or 0) for name in REQUIRED_EVIDENCE_ARTIFACTS}


def _ordered_list(values: Any) -> list[str]:
    return sorted(str(value) for value in values or [])


def _package_claim_scope(ledger: Mapping[str, Any], report: Mapping[str, Any]) -> str:
    allowed_claim_level = str(report.get("allowed_claim_level", "ambiguous"))
    if allowed_claim_level == "pilot_only" or str(ledger.get("contamination_status")) == "failed":
        return "pilot_only"
    if (
        not bool(ledger.get("required_artifacts_present"))
        or int(ledger.get("projection_bundle_count", 0) or 0) <= 0
        or "projection_bundles" in set(ledger.get("missing_required_artifacts", []))
    ):
        return "ambiguous"
    if allowed_claim_level == "measurement_validated" and not bool(report.get("measurement_validated_allowed")):
        return "ambiguous"
    if allowed_claim_level in {
        "engineering_compatibility_only",
        "engineering_smoke_only",
        "replayable_artifact_evidence",
        "synthetic_structural_only",
        "operational_utility_only",
        "ambiguous",
        "pilot_only",
    }:
        return allowed_claim_level
    return "ambiguous"


def _manifest(
    *,
    ledger: Mapping[str, Any],
    report: Mapping[str, Any],
) -> dict[str, Any]:
    artifact_counts = _artifact_counts(ledger)
    projection_bundle_hashes = _ordered_list(ledger.get("projection_bundle_hashes", []))
    reason_codes = list(report.get("reason_codes", []))
    denied_claims = _ordered_list(report.get("denied_claims", []))
    return {
        "package_schema_version": PACKAGE_SCHEMA_VERSION,
        "source_run_id": str(ledger.get("run_id", "")),
        "evidence_mode": str(ledger.get("evidence_mode", "ambiguous")),
        "source_phase": str(ledger.get("source_phase", "unknown")),
        "artifact_counts": artifact_counts,
        "required_artifacts_present": bool(ledger.get("required_artifacts_present", False)),
        "missing_required_artifacts": list(ledger.get("missing_required_artifacts", [])),
        "projection_bundle_count": int(ledger.get("projection_bundle_count", 0) or 0),
        "projection_bundle_hash_count": len(projection_bundle_hashes),
        "projection_bundle_hashes": projection_bundle_hashes,
        "metric_bridge_witness_count": int(ledger.get("metric_bridge_witness_count", 0) or 0),
        "diagnostic_count": int(ledger.get("diagnostic_count", 0) or 0),
        "claim_gate_allowed_level": str(report.get("allowed_claim_level", "ambiguous")),
        "measurement_validated_allowed": bool(report.get("measurement_validated_allowed", False)),
        "denied_claims": denied_claims,
        "reason_codes": reason_codes,
        "p04_status": str(report.get("p04_status", ledger.get("p04_status", "BLOCKED_OPERATOR_REQUIRED"))),
        "p09_status": str(report.get("p09_status", ledger.get("p09_status", "BLOCKED_OPERATOR_REQUIRED"))),
        "live_api_used": bool(ledger.get("live_api_used", False)),
        "external_runtime_used": bool(ledger.get("external_runtime_used", False)),
        "package_claim_scope": _package_claim_scope(ledger, report),
        "claim_boundary_warning": CLAIM_BOUNDARY_WARNING,
    }


def _build_package(
    *,
    ledger: Mapping[str, Any],
    report: Mapping[str, Any],
    proxy_regime_matrix: Mapping[str, Any] | None,
) -> dict[str, Any]:
    resolved_ledger = deepcopy(dict(ledger))
    resolved_report = deepcopy(dict(report))
    resolved_matrix = deepcopy(dict(proxy_regime_matrix)) if proxy_regime_matrix is not None else None
    manifest = _manifest(ledger=resolved_ledger, report=resolved_report)
    return {
        "package_schema_version": PACKAGE_SCHEMA_VERSION,
        "manifest": manifest,
        "artifact_counts": deepcopy(manifest["artifact_counts"]),
        "projection_bundle_hashes": list(manifest["projection_bundle_hashes"]),
        "evidence_ledger": resolved_ledger,
        "claim_gate_report": resolved_report,
        "proxy_regime_matrix": resolved_matrix,
    }


def build_replay_evidence_package_from_summary(
    summary: Mapping[str, Any],
    *,
    proxy_regime_matrix: Mapping[str, Any] | None = None,
    evidence_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ledger = build_evidence_ledger_from_summary(
        deepcopy(dict(summary)),
        **deepcopy(dict(evidence_overrides or {})),
    )
    report = build_claim_gate_report(ledger)
    return _build_package(
        ledger=ledger,
        report=report,
        proxy_regime_matrix=proxy_regime_matrix,
    )


def _matrix_inputs_exist(artifact_dir: Path) -> bool:
    return (
        (artifact_dir / "summary.json").exists()
        and (artifact_dir / "diagnostics.jsonl").exists()
        and (artifact_dir / "metric_bridge_witnesses.jsonl").exists()
    )


def build_replay_evidence_package_from_artifact_dir(
    artifact_dir: str | Path,
    *,
    run_id: str | None = None,
    proxy_regime_matrix: Mapping[str, Any] | None = None,
    **evidence_overrides: Any,
) -> dict[str, Any]:
    resolved_dir = Path(artifact_dir)
    overrides = deepcopy(dict(evidence_overrides))
    ledger = build_evidence_ledger_from_artifact_dir(resolved_dir, run_id=run_id, **overrides)
    report = build_claim_gate_report(ledger)
    resolved_matrix = deepcopy(dict(proxy_regime_matrix)) if proxy_regime_matrix is not None else None
    if resolved_matrix is None and _matrix_inputs_exist(resolved_dir):
        resolved_matrix = build_proxy_regime_matrix_from_artifact_dir(
            resolved_dir,
            run_id=run_id,
            **overrides,
        )
    return _build_package(
        ledger=ledger,
        report=report,
        proxy_regime_matrix=resolved_matrix,
    )


def format_replay_package_summary_markdown(package: Mapping[str, Any]) -> str:
    manifest = dict(package["manifest"])
    reason_codes = list(manifest.get("reason_codes") or [])
    denied_claims = list(manifest.get("denied_claims") or [])
    lines = [
        "# Replay Evidence Package",
        "",
        "## Summary",
        "",
        f"- Package schema version: `{manifest['package_schema_version']}`",
        f"- Source run id: `{manifest['source_run_id']}`",
        f"- Evidence mode: `{manifest['evidence_mode']}`",
        f"- Source phase: `{manifest['source_phase']}`",
        f"- Package claim scope: `{manifest['package_claim_scope']}`",
        f"- Claim gate allowed level: `{manifest['claim_gate_allowed_level']}`",
        f"- measurement_validated_allowed: {str(manifest['measurement_validated_allowed']).lower()}",
        f"- P04 status: `{manifest['p04_status']}`",
        f"- P09 status: `{manifest['p09_status']}`",
        f"- Live API used: {str(manifest['live_api_used']).lower()}",
        f"- External runtime used: {str(manifest['external_runtime_used']).lower()}",
        "",
        "## Artifact Counts",
        "",
    ]
    for name, count in manifest["artifact_counts"].items():
        lines.append(f"- `{name}`: {count}")
    lines.extend(
        [
            "",
            "## Projection Bundle Hashes",
            "",
        ]
    )
    if manifest.get("projection_bundle_hashes"):
        lines.extend(f"- `{value}`" for value in manifest["projection_bundle_hashes"])
    else:
        lines.append("- `none`")
    lines.extend(["", "## Reason Codes", ""])
    if reason_codes:
        lines.extend(f"- `{reason}`" for reason in reason_codes)
    else:
        lines.append("- `none`")
    lines.extend(["", "## Denied Claims", ""])
    if denied_claims:
        lines.extend(f"- `{claim}`" for claim in denied_claims)
    else:
        lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Replay package completeness is not scientific validation.",
            "- measurement_validated is not claimed.",
            "- Synthetic success is not deployed V-information certification.",
            "- Engineering success is not scientific validation.",
            "- Live API success alone is not measurement validation.",
            "- External runtime success alone is not measurement validation.",
            "- P04 remains deferred/operator-required.",
            "- P09 remains BLOCKED_OPERATOR_REQUIRED.",
            "",
        ]
    )
    return "\n".join(lines)


def write_replay_evidence_package(output_dir: str | Path, package: Mapping[str, Any]) -> dict[str, str]:
    resolved_output_dir = Path(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    payload = deepcopy(dict(package))
    manifest = deepcopy(dict(payload["manifest"]))
    ledger = deepcopy(dict(payload["evidence_ledger"]))
    report = deepcopy(dict(payload["claim_gate_report"]))
    matrix = deepcopy(dict(payload["proxy_regime_matrix"])) if payload.get("proxy_regime_matrix") is not None else None

    manifest_path = _stable_write_json(resolved_output_dir / "manifest.json", manifest)
    artifact_counts_path = _stable_write_json(
        resolved_output_dir / "artifact_counts.json",
        manifest["artifact_counts"],
    )
    bundle_hashes_path = _stable_write_json(
        resolved_output_dir / "projection_bundle_hashes.json",
        {
            "projection_bundle_hash_count": manifest["projection_bundle_hash_count"],
            "projection_bundle_hashes": manifest["projection_bundle_hashes"],
        },
    )
    ledger_path = _stable_write_json(resolved_output_dir / "evidence_ledger.json", ledger)
    claim_json_path = _stable_write_json(resolved_output_dir / "claim_gate_report.json", report)
    claim_markdown_path = resolved_output_dir / "claim_gate_report.md"
    claim_markdown_path.write_text(format_claim_gate_markdown(report), encoding="utf-8")
    summary_path = resolved_output_dir / "replay_package_summary.md"
    summary_path.write_text(format_replay_package_summary_markdown(payload), encoding="utf-8")

    outputs = {
        "manifest": str(manifest_path),
        "artifact_counts": str(artifact_counts_path),
        "projection_bundle_hashes": str(bundle_hashes_path),
        "evidence_ledger": str(ledger_path),
        "claim_gate_report_json": str(claim_json_path),
        "claim_gate_report_markdown": str(claim_markdown_path),
        "summary_markdown": str(summary_path),
    }
    if matrix is not None:
        matrix_json_path = _stable_write_json(resolved_output_dir / "proxy_regime_matrix.json", matrix)
        matrix_markdown_path = resolved_output_dir / "proxy_regime_matrix.md"
        matrix_markdown_path.write_text(format_proxy_regime_matrix_markdown(matrix), encoding="utf-8")
        outputs["proxy_regime_matrix_json"] = str(matrix_json_path)
        outputs["proxy_regime_matrix_markdown"] = str(matrix_markdown_path)
    return outputs
