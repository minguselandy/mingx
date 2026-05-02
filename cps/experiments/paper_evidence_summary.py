from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.evidence_ledger import REQUIRED_EVIDENCE_ARTIFACTS
from cps.experiments.replay_evidence_package import build_replay_evidence_package_from_summary


PAPER_EVIDENCE_SCHEMA_VERSION = "PaperEvidenceSummaryV1"
PAPER_OUTPUTS = (
    "paper_evidence_summary.json",
    "paper_evidence_summary.md",
)
REPLAY_PACKAGE_OUTPUTS = (
    "manifest.json",
    "artifact_counts.json",
    "projection_bundle_hashes.json",
    "evidence_ledger.json",
    "claim_gate_report.json",
    "claim_gate_report.md",
    "proxy_regime_matrix.json",
    "proxy_regime_matrix.md",
    "replay_package_summary.md",
)
CLAIM_LADDER = (
    ("engineering_compatibility_only", "Schema and compatibility evidence only."),
    ("engineering_smoke_only", "Offline fake/local path evidence only."),
    ("replayable_artifact_evidence", "Complete deterministic artifact package evidence."),
    ("synthetic_structural_only", "Synthetic/proxy structural diagnostic evidence only."),
    ("operational_utility_only", "Operational utility evidence without measurement validation."),
    ("ambiguous", "Fail-closed or incomplete evidence."),
    ("pilot_only", "Contamination or boundary failure restricts claims to pilot use."),
    ("measurement_validated", "Requires existing claim gate validation evidence."),
)
LIMITATIONS = (
    "P04 remains deferred/operator-required.",
    "P09 remains BLOCKED_OPERATOR_REQUIRED.",
    "measurement_validated is not claimed.",
    "Synthetic benchmark success does not certify deployed V-information submodularity.",
    "Engineering success does not equal scientific validation.",
    "Replay package completeness is not scientific validation.",
    "Live API success alone does not imply measurement validation.",
    "External runtime success alone does not imply measurement validation.",
    "Paper-facing summaries do not upgrade claim levels.",
)
FINAL_CLAIM_BOUNDARY = (
    "paper-facing summaries do not upgrade claim levels; "
    "measurement_validated is not claimed unless the existing claim gate allows it; "
    "P04 remains deferred/operator-required; "
    "P09 remains BLOCKED_OPERATOR_REQUIRED"
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


def _ordered_list(values: Any) -> list[str]:
    return sorted(str(value) for value in values or [])


def _artifact_rows(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    counts = dict(manifest.get("artifact_counts") or {})
    missing = set(manifest.get("missing_required_artifacts") or [])
    rows: list[dict[str, Any]] = []
    for artifact in REQUIRED_EVIDENCE_ARTIFACTS:
        count = int(counts.get(artifact, 0) or 0)
        rows.append(
            {
                "artifact": artifact,
                "count": count,
                "status": "missing_or_incomplete" if artifact in missing or count <= 0 else "present",
                "paper_section": "runtime-audit artifact summary",
            }
        )
    return rows


def _claim_rows(manifest: Mapping[str, Any]) -> list[dict[str, str]]:
    fields = (
        ("allowed_claim_level", manifest.get("claim_gate_allowed_level", "ambiguous")),
        ("measurement_validated_allowed", str(bool(manifest.get("measurement_validated_allowed", False))).lower()),
        ("package_claim_scope", manifest.get("package_claim_scope", "ambiguous")),
        ("p04_status", manifest.get("p04_status", "BLOCKED_OPERATOR_REQUIRED")),
        ("p09_status", manifest.get("p09_status", "BLOCKED_OPERATOR_REQUIRED")),
        ("live_api_used", str(bool(manifest.get("live_api_used", False))).lower()),
        ("external_runtime_used", str(bool(manifest.get("external_runtime_used", False))).lower()),
    )
    return [
        {
            "field": field,
            "value": str(value),
            "paper_section": "conservative claim gate",
        }
        for field, value in fields
    ]


def _proxy_rows(matrix: Mapping[str, Any] | None) -> list[dict[str, str]]:
    if matrix is None:
        return [
            {
                "regime_name": "proxy_regime_matrix",
                "certification_scope": "unavailable",
                "allowed_claim_level": "ambiguous",
                "reason_codes": "matrix_not_available",
                "paper_section": "proxy-regime certification",
            }
        ]
    rows: list[dict[str, str]] = []
    for entry in matrix.get("entries", []):
        rows.append(
            {
                "regime_name": str(entry.get("regime_name", "")),
                "certification_scope": str(entry.get("certification_scope", "ambiguous")),
                "allowed_claim_level": str(entry.get("allowed_claim_level", "ambiguous")),
                "reason_codes": ", ".join(str(reason) for reason in entry.get("reason_codes", [])) or "none",
                "paper_section": "proxy-regime certification",
            }
        )
    return rows


def _replay_rows(manifest: Mapping[str, Any], matrix: Mapping[str, Any] | None) -> list[dict[str, str]]:
    available = {
        "manifest.json",
        "artifact_counts.json",
        "projection_bundle_hashes.json",
        "evidence_ledger.json",
        "claim_gate_report.json",
        "claim_gate_report.md",
        "replay_package_summary.md",
    }
    if matrix is not None:
        available.update({"proxy_regime_matrix.json", "proxy_regime_matrix.md"})
    rows: list[dict[str, str]] = []
    for output in REPLAY_PACKAGE_OUTPUTS:
        rows.append(
            {
                "output": output,
                "status": "available" if output in available else "optional_unavailable",
                "paper_section": "replayable experiment evidence",
            }
        )
    rows.append(
        {
            "output": "package_claim_scope",
            "status": str(manifest.get("package_claim_scope", "ambiguous")),
            "paper_section": "replayable experiment evidence",
        }
    )
    return rows


def _limitation_rows() -> list[dict[str, str]]:
    return [
        {
            "limitation": limitation,
            "paper_section": "limitations and denied claims",
        }
        for limitation in LIMITATIONS
    ]


def _claim_ladder_summary(current_claim_level: str) -> list[dict[str, str]]:
    return [
        {
            "claim_level": claim_level,
            "description": description,
            "current": str(claim_level == current_claim_level).lower(),
        }
        for claim_level, description in CLAIM_LADDER
    ]


def _proxy_summary(matrix: Mapping[str, Any] | None) -> dict[str, Any]:
    if matrix is None:
        return {
            "matrix_available": False,
            "entry_count": 0,
            "regime_names": [],
            "certification_scopes": [],
            "denied_scope_values": [],
            "claim_boundary_warning": "proxy-regime matrix unavailable",
        }
    entries = list(matrix.get("entries") or [])
    return {
        "matrix_available": True,
        "entry_count": len(entries),
        "regime_names": [str(entry.get("regime_name", "")) for entry in entries],
        "certification_scopes": _ordered_list(entry.get("certification_scope", "ambiguous") for entry in entries),
        "denied_scope_values": list(matrix.get("denied_scope_values") or []),
        "claim_boundary_warning": str(matrix.get("claim_boundary_warning", "")),
    }


def _bullet_summary(manifest: Mapping[str, Any]) -> list[str]:
    return [
        f"Runtime-audit artifacts present: {str(bool(manifest.get('required_artifacts_present'))).lower()}.",
        f"Projection bundles: {int(manifest.get('projection_bundle_count', 0) or 0)}.",
        f"Metric bridge witnesses: {int(manifest.get('metric_bridge_witness_count', 0) or 0)}.",
        f"Allowed claim level: {manifest.get('claim_gate_allowed_level', 'ambiguous')}.",
        f"Package claim scope: {manifest.get('package_claim_scope', 'ambiguous')}.",
        "measurement_validated is not claimed.",
        "Paper-facing summaries do not upgrade claim levels.",
    ]


def _build_summary(package: Mapping[str, Any]) -> dict[str, Any]:
    source_package = deepcopy(dict(package))
    manifest = deepcopy(dict(source_package["manifest"]))
    ledger = deepcopy(dict(source_package.get("evidence_ledger") or {}))
    report = deepcopy(dict(source_package.get("claim_gate_report") or {}))
    matrix = (
        deepcopy(dict(source_package["proxy_regime_matrix"]))
        if source_package.get("proxy_regime_matrix") is not None
        else None
    )
    artifact_counts = deepcopy(dict(manifest.get("artifact_counts") or {}))
    projection_bundle_hashes = _ordered_list(manifest.get("projection_bundle_hashes", []))
    denied_claims = list(manifest.get("denied_claims") or report.get("denied_claims") or [])
    reason_codes = list(manifest.get("reason_codes") or report.get("reason_codes") or [])
    claim_gate_allowed_level = str(manifest.get("claim_gate_allowed_level", report.get("allowed_claim_level", "ambiguous")))
    measurement_validated_allowed = bool(
        manifest.get("measurement_validated_allowed", report.get("measurement_validated_allowed", False))
    )
    manuscript_table_rows = {
        "artifact_table_rows": _artifact_rows(manifest),
        "claim_gate_table_rows": _claim_rows(manifest),
        "proxy_regime_table_rows": _proxy_rows(matrix),
        "replay_package_table_rows": _replay_rows(manifest, matrix),
        "limitation_table_rows": _limitation_rows(),
    }
    return {
        "paper_evidence_schema_version": PAPER_EVIDENCE_SCHEMA_VERSION,
        "source_run_id": str(manifest.get("source_run_id", ledger.get("run_id", ""))),
        "source_phase": str(manifest.get("source_phase", ledger.get("source_phase", "unknown"))),
        "evidence_mode": str(manifest.get("evidence_mode", ledger.get("evidence_mode", "ambiguous"))),
        "artifact_summary": {
            "required_artifacts_present": bool(manifest.get("required_artifacts_present", False)),
            "artifact_counts": artifact_counts,
            "missing_required_artifacts": list(manifest.get("missing_required_artifacts") or []),
        },
        "projection_bundle_summary": {
            "projection_bundle_count": int(manifest.get("projection_bundle_count", 0) or 0),
            "projection_bundle_hash_count": int(manifest.get("projection_bundle_hash_count", 0) or 0),
            "projection_bundle_hashes": projection_bundle_hashes,
        },
        "metric_bridge_summary": {
            "metric_bridge_witness_count": int(manifest.get("metric_bridge_witness_count", 0) or 0),
            "bridge_freshness": str(ledger.get("bridge_freshness", "missing")),
            "metric_bridge_gate_status": str(report.get("metric_bridge_gate_status", "unknown")),
            "allowed_bridge_claim_level": str(report.get("allowed_bridge_claim_level", "ambiguous")),
            "metric_bridge_reason_codes": list(report.get("metric_bridge_reason_codes") or []),
        },
        "claim_gate_summary": {
            "allowed_claim_level": claim_gate_allowed_level,
            "package_claim_scope": str(manifest.get("package_claim_scope", "ambiguous")),
            "measurement_validated_allowed": measurement_validated_allowed,
            "denied_claims": denied_claims,
            "reason_codes": reason_codes,
            "reason_code_order": list(report.get("reason_code_order") or []),
            "p04_status": str(manifest.get("p04_status", report.get("p04_status", "BLOCKED_OPERATOR_REQUIRED"))),
            "p09_status": str(manifest.get("p09_status", report.get("p09_status", "BLOCKED_OPERATOR_REQUIRED"))),
            "live_api_used": bool(manifest.get("live_api_used", ledger.get("live_api_used", False))),
            "external_runtime_used": bool(
                manifest.get("external_runtime_used", ledger.get("external_runtime_used", False))
            ),
            "summary": str(report.get("summary", "")),
        },
        "proxy_regime_summary": _proxy_summary(matrix),
        "replay_package_summary": {
            "package_schema_version": str(source_package.get("package_schema_version", "ReplayEvidencePackageV1")),
            "package_claim_scope": str(manifest.get("package_claim_scope", "ambiguous")),
            "claim_gate_report_available": bool(report),
            "proxy_regime_matrix_available": matrix is not None,
            "deterministic_replay_package_status": "available",
        },
        "claim_ladder_summary": _claim_ladder_summary(claim_gate_allowed_level),
        "denied_claims": denied_claims,
        "reason_codes": reason_codes,
        "limitations": list(LIMITATIONS),
        "manuscript_table_rows": manuscript_table_rows,
        "manuscript_bullet_summary": _bullet_summary(manifest),
        "p04_status": str(manifest.get("p04_status", report.get("p04_status", "BLOCKED_OPERATOR_REQUIRED"))),
        "p09_status": str(manifest.get("p09_status", report.get("p09_status", "BLOCKED_OPERATOR_REQUIRED"))),
        "measurement_validated_allowed": measurement_validated_allowed,
        "final_claim_boundary": FINAL_CLAIM_BOUNDARY,
        "paper_outputs": list(PAPER_OUTPUTS),
    }


def build_paper_evidence_summary_from_replay_package(package: Mapping[str, Any]) -> dict[str, Any]:
    return _build_summary(package)


def build_paper_evidence_summary_from_summary(
    summary: Mapping[str, Any],
    *,
    proxy_regime_matrix: Mapping[str, Any] | None = None,
    evidence_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    package = build_replay_evidence_package_from_summary(
        deepcopy(dict(summary)),
        proxy_regime_matrix=proxy_regime_matrix,
        evidence_overrides=deepcopy(dict(evidence_overrides or {})),
    )
    return build_paper_evidence_summary_from_replay_package(package)


def build_paper_evidence_summary_from_package_dir(package_dir: str | Path) -> dict[str, Any]:
    resolved_dir = Path(package_dir)
    manifest = _read_json(resolved_dir / "manifest.json")
    ledger = _read_json(resolved_dir / "evidence_ledger.json")
    report = _read_json(resolved_dir / "claim_gate_report.json")
    matrix_path = resolved_dir / "proxy_regime_matrix.json"
    matrix = _read_json(matrix_path) if matrix_path.exists() else None
    package = {
        "package_schema_version": "ReplayEvidencePackageV1",
        "manifest": manifest,
        "artifact_counts": deepcopy(manifest.get("artifact_counts", {})),
        "projection_bundle_hashes": list(manifest.get("projection_bundle_hashes", [])),
        "evidence_ledger": ledger,
        "claim_gate_report": report,
        "proxy_regime_matrix": matrix,
    }
    return build_paper_evidence_summary_from_replay_package(package)


def _markdown_table(headers: tuple[str, ...], rows: list[Mapping[str, Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return lines


def format_paper_evidence_summary_markdown(summary: Mapping[str, Any]) -> str:
    rows = summary["manuscript_table_rows"]
    lines = [
        "# Paper Evidence Summary",
        "",
        "## Executive Summary",
        "",
        f"- Source run id: `{summary['source_run_id']}`",
        f"- Evidence mode: `{summary['evidence_mode']}`",
        f"- Source phase: `{summary['source_phase']}`",
        f"- Allowed claim level: `{summary['claim_gate_summary']['allowed_claim_level']}`",
        f"- measurement_validated_allowed: {str(summary['measurement_validated_allowed']).lower()}",
        f"- P04 status: `{summary['p04_status']}`",
        f"- P09 status: `{summary['p09_status']}`",
        "",
    ]
    lines.extend(f"- {bullet}" for bullet in summary.get("manuscript_bullet_summary", []))
    lines.extend(
        [
            "",
            "## Artifact Evidence Table",
            "",
            *_markdown_table(
                ("artifact", "count", "status", "paper_section"),
                list(rows["artifact_table_rows"]),
            ),
            "",
            "## Claim Boundary Table",
            "",
            *_markdown_table(
                ("field", "value", "paper_section"),
                list(rows["claim_gate_table_rows"]),
            ),
            "",
            "## Proxy-Regime Table",
            "",
            *_markdown_table(
                ("regime_name", "certification_scope", "allowed_claim_level", "reason_codes"),
                list(rows["proxy_regime_table_rows"]),
            ),
            "",
            "## Replay Evidence Table",
            "",
            *_markdown_table(
                ("output", "status", "paper_section"),
                list(rows["replay_package_table_rows"]),
            ),
            "",
            "## Denied Claims",
            "",
        ]
    )
    denied_claims = list(summary.get("denied_claims") or [])
    if denied_claims:
        lines.extend(f"- `{claim}`" for claim in denied_claims)
    else:
        lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            *_markdown_table(("limitation", "paper_section"), list(rows["limitation_table_rows"])),
            "",
            "## Suggested Paper Section Mapping",
            "",
            "- Runtime-audit scaffold: artifact evidence table.",
            "- Replayable experiment evidence: replay evidence table and projection bundle summary.",
            "- Metric bridge: metric bridge summary and claim boundary table.",
            "- Conservative claim gate: denied claims and reason codes.",
            "- Proxy-regime certification: proxy-regime table.",
            "- Limitations and denied claims: limitations table.",
            "",
            "## Final Claim Boundary",
            "",
            f"- {summary['final_claim_boundary']}.",
            "- paper-facing summaries do not upgrade claim levels.",
            "- measurement_validated is not claimed.",
            "- Replay package completeness is not scientific validation.",
            "- Synthetic success is not deployed V-information certification.",
            "- Engineering success is not scientific validation.",
            "",
        ]
    )
    return "\n".join(lines)


def write_paper_evidence_summary(output_dir: str | Path, summary: Mapping[str, Any]) -> dict[str, str]:
    resolved_output_dir = Path(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    payload = deepcopy(dict(summary))
    json_path = _stable_write_json(resolved_output_dir / "paper_evidence_summary.json", payload)
    markdown_path = resolved_output_dir / "paper_evidence_summary.md"
    markdown_path.write_text(format_paper_evidence_summary_markdown(payload), encoding="utf-8")
    return {
        "json": str(json_path),
        "markdown": str(markdown_path),
        "paper_evidence_summary_json": str(json_path),
        "paper_evidence_summary_markdown": str(markdown_path),
    }
