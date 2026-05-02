from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.claim_gate_report import build_claim_gate_report, write_claim_gate_outputs
from cps.experiments.evidence_ledger import build_evidence_ledger_from_summary, write_evidence_ledger
from cps.experiments.provider_offline_smoke import run_provider_offline_smoke
from cps.experiments.proxy_regime_matrix import (
    build_proxy_regime_matrix_from_summary,
    write_proxy_regime_matrix,
)
from cps.experiments.replay_evidence_package import (
    build_replay_evidence_package_from_summary,
    write_replay_evidence_package,
)
from cps.experiments.paper_evidence_summary import (
    build_paper_evidence_summary_from_replay_package,
    write_paper_evidence_summary,
)


DEMO_SCHEMA_VERSION = "EndToEndEvidenceDemoV1"
DEFAULT_RUN_ID = "p17_offline_evidence_demo"
DEFAULT_EVIDENCE_MODE = "offline_runtime_audit_demo"
SOURCE_PHASE = "P17"
FINAL_CLAIM_BOUNDARY = (
    "P17 is offline runtime-audit evidence only; "
    "P17 is not scientific validation; "
    "measurement_validated is not claimed; "
    "synthetic success does not certify deployed V-information submodularity; "
    "replay package completeness does not imply scientific validation; "
    "paper-facing summaries do not upgrade claim levels; "
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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _bundle_hashes(path: Path) -> list[str]:
    return sorted(str(row["canonical_hash"]) for row in _read_jsonl(path) if row.get("canonical_hash"))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ledger_overrides(
    *,
    run_id: str,
    evidence_mode: str,
    projection_bundle_hashes: list[str],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "evidence_mode": evidence_mode,
        "source_phase": SOURCE_PHASE,
        "projection_bundle_hashes": projection_bundle_hashes,
        "live_api_used": False,
        "external_runtime_used": False,
        "p04_status": "BLOCKED_OPERATOR_REQUIRED",
        "p09_status": "BLOCKED_OPERATOR_REQUIRED",
    }


def _generated_outputs_relative() -> dict[str, str]:
    return {
        "projection_bundles_jsonl": "projection_bundles.jsonl",
        "evidence_ledger_json": "evidence_ledger.json",
        "claim_gate_report_json": "claim_gate_report.json",
        "claim_gate_report_markdown": "claim_gate_report.md",
        "proxy_regime_matrix_json": "proxy_regime_matrix.json",
        "proxy_regime_matrix_markdown": "proxy_regime_matrix.md",
        "replay_package_dir": "replay_package",
        "replay_package_summary_markdown": "replay_package/replay_package_summary.md",
        "paper_evidence_summary_json": "paper_evidence_summary.json",
        "paper_evidence_summary_markdown": "paper_evidence_summary.md",
        "demo_manifest_json": "demo_manifest.json",
        "demo_summary_markdown": "demo_summary.md",
    }


def _absolute_outputs(output_root: Path) -> dict[str, str]:
    return {key: str((output_root / relative).resolve()) for key, relative in _generated_outputs_relative().items()}


def _proxy_regime_scopes(matrix: Mapping[str, Any]) -> list[str]:
    return sorted({str(entry.get("certification_scope", "ambiguous")) for entry in matrix.get("entries", [])})


def _manifest(
    *,
    run_id: str,
    evidence_mode: str,
    ledger: Mapping[str, Any],
    report: Mapping[str, Any],
    matrix: Mapping[str, Any],
    replay_package_present: bool,
    paper_summary_present: bool,
) -> dict[str, Any]:
    return {
        "demo_schema_version": DEMO_SCHEMA_VERSION,
        "run_id": run_id,
        "evidence_mode": evidence_mode,
        "source_phase": SOURCE_PHASE,
        "generated_outputs": _generated_outputs_relative(),
        "artifact_counts": dict(ledger.get("artifact_counts") or {}),
        "projection_bundle_count": int(ledger.get("projection_bundle_count", 0) or 0),
        "claim_gate_allowed_level": str(report.get("allowed_claim_level", "ambiguous")),
        "measurement_validated_allowed": bool(report.get("measurement_validated_allowed", False)),
        "denied_claims": list(report.get("denied_claims", [])),
        "reason_codes": list(report.get("reason_codes", [])),
        "proxy_regime_scopes": _proxy_regime_scopes(matrix),
        "replay_package_present": replay_package_present,
        "paper_summary_present": paper_summary_present,
        "p04_status": str(report.get("p04_status", "BLOCKED_OPERATOR_REQUIRED")),
        "p09_status": str(report.get("p09_status", "BLOCKED_OPERATOR_REQUIRED")),
        "live_api_used": bool(ledger.get("live_api_used", False)),
        "external_runtime_used": bool(ledger.get("external_runtime_used", False)),
        "final_claim_boundary": FINAL_CLAIM_BOUNDARY,
    }


def _markdown_table(headers: tuple[str, ...], rows: list[Mapping[str, Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return lines


def _format_demo_summary(
    *,
    manifest: Mapping[str, Any],
    ledger: Mapping[str, Any],
    report: Mapping[str, Any],
    matrix: Mapping[str, Any],
    replay_package: Mapping[str, Any],
    paper_summary: Mapping[str, Any],
) -> str:
    output_rows = [
        {"output": key, "path": value}
        for key, value in manifest["generated_outputs"].items()
    ]
    claim_rows = [
        {"field": "allowed_claim_level", "value": report.get("allowed_claim_level", "ambiguous")},
        {
            "field": "measurement_validated_allowed",
            "value": str(bool(report.get("measurement_validated_allowed", False))).lower(),
        },
        {"field": "p04_status", "value": report.get("p04_status", "BLOCKED_OPERATOR_REQUIRED")},
        {"field": "p09_status", "value": report.get("p09_status", "BLOCKED_OPERATOR_REQUIRED")},
    ]
    lines = [
        "# End-to-End Runtime-Audit Evidence Demo",
        "",
        "## Summary",
        "",
        "- P17 is offline runtime-audit evidence only.",
        "- P17 is not scientific validation.",
        "- P17 does not claim measurement_validated.",
        "- Synthetic success does not certify deployed V-information submodularity.",
        "- Replay package completeness does not imply scientific validation.",
        "- Paper-facing summaries do not upgrade claim levels.",
        "- P04 remains deferred/operator-required.",
        "- P09 remains BLOCKED_OPERATOR_REQUIRED.",
        "",
        "## Generated Outputs",
        "",
        *_markdown_table(("output", "path"), output_rows),
        "",
        "## Artifact Evidence Summary",
        "",
        f"- Projection bundle count: {ledger.get('projection_bundle_count', 0)}",
        f"- Required artifacts present: {str(bool(ledger.get('required_artifacts_present'))).lower()}",
        f"- Metric bridge witness count: {ledger.get('metric_bridge_witness_count', 0)}",
        f"- Diagnostic count: {ledger.get('diagnostic_count', 0)}",
        "",
        "## Claim Gate Summary",
        "",
        *_markdown_table(("field", "value"), claim_rows),
        "",
        "## Proxy-Regime Summary",
        "",
        f"- Matrix version: `{matrix.get('matrix_version', 'unknown')}`",
        f"- Entry count: {len(matrix.get('entries', []))}",
        f"- Certification scopes: {', '.join(manifest.get('proxy_regime_scopes', []))}",
        "- Proxy-regime certification is not deployed V-information certification.",
        "",
        "## Replay Package Summary",
        "",
        f"- Package schema version: `{replay_package.get('package_schema_version', 'ReplayEvidencePackageV1')}`",
        f"- Package claim scope: `{replay_package.get('manifest', {}).get('package_claim_scope', 'ambiguous')}`",
        "- Replay package completeness does not imply scientific validation.",
        "",
        "## Paper Evidence Summary",
        "",
        f"- Paper schema version: `{paper_summary.get('paper_evidence_schema_version', 'PaperEvidenceSummaryV1')}`",
        f"- Manuscript table groups: {', '.join(paper_summary.get('manuscript_table_rows', {}).keys())}",
        "- Paper-facing summaries do not upgrade claim levels.",
        "",
        "## Denied Claims",
        "",
    ]
    denied_claims = list(report.get("denied_claims") or [])
    if denied_claims:
        lines.extend(f"- `{claim}`" for claim in denied_claims)
    else:
        lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- P17 is offline runtime-audit evidence only.",
            "- P17 is not scientific validation.",
            "- P17 does not claim measurement_validated.",
            "- Synthetic success does not certify deployed V-information submodularity.",
            "- Replay package completeness does not imply scientific validation.",
            "- Paper-facing summaries do not upgrade claim levels.",
            "- P04 remains deferred/operator-required.",
            "- P09 remains BLOCKED_OPERATOR_REQUIRED.",
            "",
        ]
    )
    return "\n".join(lines)


def build_end_to_end_evidence_demo(
    output_root: str | Path,
    *,
    run_id: str = DEFAULT_RUN_ID,
    evidence_mode: str = DEFAULT_EVIDENCE_MODE,
) -> dict[str, Any]:
    resolved_output_root = Path(output_root).resolve()
    smoke_report = run_provider_offline_smoke(
        resolved_output_root,
        seed=0,
        budget_tokens=12,
    )
    smoke_summary = deepcopy(dict(smoke_report["summary"]))
    projection_bundle_hashes = _bundle_hashes(resolved_output_root / "projection_bundles.jsonl")
    overrides = _ledger_overrides(
        run_id=run_id,
        evidence_mode=evidence_mode,
        projection_bundle_hashes=projection_bundle_hashes,
    )
    ledger = build_evidence_ledger_from_summary(smoke_summary, **overrides)
    report = build_claim_gate_report(ledger)
    write_evidence_ledger(resolved_output_root / "evidence_ledger.json", ledger)
    write_claim_gate_outputs(resolved_output_root, ledger, report)

    diagnostics_rows = _read_jsonl(resolved_output_root / "diagnostics.jsonl")
    metric_bridge_rows = _read_jsonl(resolved_output_root / "metric_bridge_witnesses.jsonl")
    matrix = build_proxy_regime_matrix_from_summary(
        smoke_summary,
        diagnostics_rows,
        metric_bridge_rows=metric_bridge_rows,
        evidence_overrides={
            "run_id": run_id,
            "source_phase": SOURCE_PHASE,
            "p04_status": "BLOCKED_OPERATOR_REQUIRED",
            "p09_status": "BLOCKED_OPERATOR_REQUIRED",
        },
    )
    write_proxy_regime_matrix(resolved_output_root, matrix)

    replay_package = build_replay_evidence_package_from_summary(
        smoke_summary,
        proxy_regime_matrix=matrix,
        evidence_overrides=overrides,
    )
    replay_outputs = write_replay_evidence_package(resolved_output_root / "replay_package", replay_package)

    paper_summary = build_paper_evidence_summary_from_replay_package(replay_package)
    paper_outputs = write_paper_evidence_summary(resolved_output_root, paper_summary)

    manifest = _manifest(
        run_id=run_id,
        evidence_mode=evidence_mode,
        ledger=ledger,
        report=report,
        matrix=matrix,
        replay_package_present=Path(replay_outputs["manifest"]).exists(),
        paper_summary_present=Path(paper_outputs["json"]).exists(),
    )
    manifest_path = _stable_write_json(resolved_output_root / "demo_manifest.json", manifest)
    summary_path = resolved_output_root / "demo_summary.md"
    summary_path.write_text(
        _format_demo_summary(
            manifest=manifest,
            ledger=ledger,
            report=report,
            matrix=matrix,
            replay_package=replay_package,
            paper_summary=paper_summary,
        ),
        encoding="utf-8",
    )
    generated_outputs = _absolute_outputs(resolved_output_root)
    status = "green" if bool(ledger.get("required_artifacts_present")) else "red"
    return {
        "status": status,
        "run_id": run_id,
        "evidence_mode": evidence_mode,
        "output_root": str(resolved_output_root),
        "generated_outputs": generated_outputs,
        "manifest": _read_json(manifest_path),
        "evidence_ledger": ledger,
        "claim_gate_report": report,
        "proxy_regime_matrix": matrix,
        "replay_package": replay_package,
        "paper_evidence_summary": paper_summary,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build the offline P17 end-to-end CPS evidence demo.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--evidence-mode", default=DEFAULT_EVIDENCE_MODE)
    args = parser.parse_args()

    result = build_end_to_end_evidence_demo(
        args.output_root,
        run_id=args.run_id,
        evidence_mode=args.evidence_mode,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "green" else 1


if __name__ == "__main__":
    raise SystemExit(main())
