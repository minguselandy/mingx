from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any


TARGET_MANUSCRIPT_PATH = "docs/archive/context_projection_revised_v10.md"
PATCH_SCHEMA_VERSION = "ContextProjectionV10P18ManuscriptPatchV1"
FINAL_CLAIM_BOUNDARY = "paper-facing summaries do not upgrade claim levels"

ARTIFACT_ROWS = (
    (
        "ProjectionPlan",
        "Selection decision record for candidates considered, selected, and excluded.",
        "Section 6.2 runtime artifact chain",
    ),
    (
        "BudgetWitness",
        "Token-budget witness for estimated and realized context costs.",
        "Section 6.2 runtime artifact chain",
    ),
    (
        "MaterializedContext",
        "Realized context payload and materialization manifest.",
        "Section 6.2 runtime artifact chain",
    ),
    (
        "MetricBridgeWitness",
        "Measurement-claim witness for metric class, drift, and diagnostic scope.",
        "Sections 3.4, 4.2, and 6.2",
    ),
    (
        "ProjectionBundleV1",
        "Canonical bundle tying plan, budget, materialized context, bridge witness, and diagnostics.",
        "Runtime-audit evidence bundle",
    ),
    (
        "EvidenceLedger",
        "Deterministic summary of available runtime-audit evidence and missing required artifacts.",
        "P12 audit layer",
    ),
    (
        "ClaimGateReport",
        "Conservative claim report that denies measurement claims when labels, kappa, bridge, or artifacts are missing.",
        "P12/P13 claim gate",
    ),
    (
        "MetricBridgeGate",
        "Bridge-specific conservative gate for freshness, metric class, labels, kappa, and contamination status.",
        "P13 metric bridge hardening",
    ),
    (
        "ProxyRegimeMatrix",
        "Manuscript-facing proxy/synthetic regime diagnostic matrix.",
        "P14 proxy-regime certification",
    ),
    (
        "ReplayEvidencePackage",
        "Stable package of replayable artifacts, ledger, claim report, hashes, and optional matrix.",
        "P15 replay package",
    ),
    (
        "PaperEvidenceSummary",
        "Manuscript-facing summary over the replay package and conservative claim gate.",
        "P16 paper summary",
    ),
    (
        "EndToEndEvidenceDemo",
        "Offline P10-P16 demo wiring provider normalization through paper evidence summary.",
        "P17 offline runtime-audit demo",
    ),
)

CLAIM_GATE_ROWS = (
    ("contamination failure", "pilot_only", "measurement_validated", "Contamination failure restricts claims to pilot-only evidence."),
    ("missing human labels", "not measurement_validated", "measurement_validated", "Human labels remain required for measurement validation."),
    ("missing kappa", "not measurement_validated", "measurement_validated", "Inter-annotator agreement remains required for measurement validation."),
    ("stale metric bridge", "operational_utility_only or ambiguous", "measurement validation", "A stale bridge cannot support validation-level claims."),
    ("missing metric bridge", "operational_utility_only or ambiguous", "measurement validation", "A missing bridge cannot support validation-level claims."),
    ("synthetic-only evidence", "synthetic_structural_only", "deployed V-information certification", "Synthetic structure is not deployed V-information certification."),
    ("engineering-only evidence", "engineering_smoke_only", "scientific validation", "Engineering smoke success is not scientific validation."),
    ("replay package completeness", "replayable_artifact_evidence", "scientific validation", "Packaging completeness is audit evidence only."),
    ("paper-facing summary", "no claim upgrade", "measurement validation", "Paper summaries surface existing gates but do not raise claims."),
    ("live API success alone", "operational evidence only", "measurement validation", "Live execution alone does not provide labels, kappa, or bridge validation."),
    ("external runtime success alone", "operational evidence only", "measurement validation", "Runtime integration alone does not validate measurement."),
)

PROXY_REGIME_ROWS = (
    ("redundancy_dominated", "synthetic/proxy diagnostic row", "proxy_regime_diagnostic_only"),
    ("sparse_pairwise_synergy", "synthetic/proxy diagnostic row", "synthetic_structural_only"),
    ("higher_order_synergy", "higher-order/prerequisite boundary row", "synthetic_structural_only"),
    ("contamination_failed", "negative claim-gate boundary row", "pilot_only"),
    ("missing_human_labels", "negative claim-gate boundary row", "ambiguous"),
    ("missing_kappa", "negative claim-gate boundary row", "ambiguous"),
    ("stale_metric_bridge", "metric bridge boundary row", "operational_utility_only or ambiguous"),
    ("missing_metric_bridge", "metric bridge boundary row", "operational_utility_only or ambiguous"),
    ("artifact_incomplete", "artifact completeness boundary row", "ambiguous"),
)

REPLAY_OUTPUT_ROWS = (
    ("manifest.json", "package manifest and claim scope"),
    ("artifact_counts.json", "required artifact count summary"),
    ("projection_bundle_hashes.json", "stable ProjectionBundleV1 hash coverage"),
    ("evidence_ledger.json", "P12 evidence ledger"),
    ("claim_gate_report.json", "P12/P13 conservative claim gate report"),
    ("claim_gate_report.md", "human-readable conservative claim report"),
    ("proxy_regime_matrix.json", "P14 proxy-regime matrix JSON"),
    ("proxy_regime_matrix.md", "P14 proxy-regime matrix Markdown"),
    ("replay_package_summary.md", "P15 replay package summary"),
    ("paper_evidence_summary.json", "P16 paper evidence summary JSON"),
    ("paper_evidence_summary.md", "P16 paper evidence summary Markdown"),
    ("demo_manifest.json", "P17 end-to-end demo manifest"),
    ("demo_summary.md", "P17 end-to-end demo summary"),
)

LIMITATION_ROWS = (
    "P04 remains deferred/operator-required",
    "P09 remains BLOCKED_OPERATOR_REQUIRED",
    "measurement_validated is not claimed",
    "synthetic success is not deployed V-information certification",
    "engineering success is not scientific validation",
    "replay package completeness is not scientific validation",
    "paper-facing summaries do not upgrade claim levels",
    "live API/external runtime success alone is not measurement validation",
    "missing labels/kappa block measurement validation",
)

SUGGESTED_INSERTION_POINTS = (
    {
        "section": "3.4 Bridge statement",
        "action": "Add the metric bridge / claim gate patch after the bridge table.",
    },
    {
        "section": "4.3.1 Synthetic regime benchmark",
        "action": "Add the experiment/evidence and proxy-regime certification patch after the validity gate table.",
    },
    {
        "section": "6 Runtime Interface Requirements",
        "action": "Add the runtime-audit artifact table near the four-artifact projection chain.",
    },
    {
        "section": "9 Limitations",
        "action": "Add the limitations and non-claims patch as an evidence-boundary paragraph.",
    },
    {
        "section": "10-11 Broader Impact and Conclusion",
        "action": "Mention that P17 is offline runtime-audit evidence only, not scientific validation.",
    },
)


def _read_json(path: Path) -> dict[str, Any]:
    if "reference" in path.parts:
        raise ValueError(f"reference path is out of scope: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _ordered_list(values: Any) -> list[str]:
    return sorted(str(value) for value in values or [])


def _load_source(source: Mapping[str, Any] | Path) -> dict[str, Any]:
    if isinstance(source, Mapping):
        return deepcopy(dict(source))

    source_path = Path(source)
    if "reference" in source_path.parts:
        raise ValueError(f"reference path is out of scope: {source_path}")
    if source_path.is_dir():
        summary_path = source_path / "paper_evidence_summary.json"
        manifest_path = source_path / "demo_manifest.json"
        summary = _read_json(summary_path) if summary_path.exists() else {}
        manifest = _read_json(manifest_path) if manifest_path.exists() else {}
        if manifest:
            summary.setdefault("source_run_id", manifest.get("run_id", ""))
            summary.setdefault("source_phase", manifest.get("source_phase", "P17"))
            summary.setdefault("evidence_mode", manifest.get("evidence_mode", "offline_runtime_audit_demo"))
            summary.setdefault("measurement_validated_allowed", manifest.get("measurement_validated_allowed", False))
            summary.setdefault("denied_claims", manifest.get("denied_claims", []))
            summary.setdefault("reason_codes", manifest.get("reason_codes", []))
        return summary
    if source_path.suffix.lower() == ".json":
        return _read_json(source_path)
    return {}


def _claim_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    claim_gate = dict(source.get("claim_gate_summary") or {})
    denied_claims = set(source.get("denied_claims") or claim_gate.get("denied_claims") or [])
    denied_claims.update(
        {
            "measurement_validated",
            "scientific_validation",
            "deployed_v_information_certification",
            "deployed_v_information_submodularity_certified",
        }
    )
    reason_codes = set(source.get("reason_codes") or claim_gate.get("reason_codes") or [])
    reason_codes.update({"missing_human_labels", "missing_kappa", "operator_required_phase"})
    return {
        "allowed_claim_level": str(claim_gate.get("allowed_claim_level", "ambiguous")),
        "denied_claims": sorted(denied_claims),
        "reason_codes": sorted(reason_codes),
        "p04_status": str(source.get("p04_status", claim_gate.get("p04_status", "BLOCKED_OPERATOR_REQUIRED"))),
        "p09_status": str(source.get("p09_status", claim_gate.get("p09_status", "BLOCKED_OPERATOR_REQUIRED"))),
        "measurement_validated_allowed": False,
    }


def _artifact_table() -> list[dict[str, str]]:
    return [
        {
            "artifact": artifact,
            "manuscript_role": role,
            "suggested_section": section,
            "claim_boundary": "audit interface only; not scientific validation",
        }
        for artifact, role, section in ARTIFACT_ROWS
    ]


def _claim_gate_table() -> list[dict[str, str]]:
    return [
        {
            "condition": condition,
            "allowed_claim_boundary": boundary,
            "denied_claim": denied_claim,
            "manuscript_note": note,
        }
        for condition, boundary, denied_claim, note in CLAIM_GATE_ROWS
    ]


def _proxy_regime_table() -> list[dict[str, str]]:
    return [
        {
            "regime": regime,
            "manuscript_role": role,
            "certification_scope": scope,
            "claim_boundary": "proxy-regime certification is not deployed V-information certification",
        }
        for regime, role, scope in PROXY_REGIME_ROWS
    ]


def _replay_evidence_table() -> list[dict[str, str]]:
    return [
        {
            "output": output,
            "manuscript_role": role,
            "claim_boundary": "replay evidence package completeness is not scientific validation",
        }
        for output, role in REPLAY_OUTPUT_ROWS
    ]


def _limitation_table() -> list[dict[str, str]]:
    return [
        {
            "limitation": limitation,
            "manuscript_note": "keep explicit in the revised manuscript patch",
        }
        for limitation in LIMITATION_ROWS
    ]


def _section_patches(source: Mapping[str, Any], claim_summary: Mapping[str, Any]) -> dict[str, str]:
    source_run_id = str(source.get("source_run_id", "p17_offline_evidence_demo"))
    allowed_claim_level = str(claim_summary.get("allowed_claim_level", "ambiguous"))
    return {
        "experiment_section_patch": (
            "Add a manuscript paragraph after Section 4.3.1 explaining that the P10-P17 offline "
            f"runtime-audit evidence chain for `{source_run_id}` produces deterministic projection bundles, "
            "an evidence ledger, conservative claim gate outputs, proxy-regime matrix outputs, replay package "
            "outputs, and paper evidence summaries. Interpret this as replayable engineering evidence only; "
            "it does not certify deployed V-information submodularity or measurement validation."
        ),
        "metric_bridge_section_patch": (
            "Add a bridge-boundary paragraph to Section 3.4 or 4.2 stating that the conservative claim gate "
            f"currently permits at most `{allowed_claim_level}` for the available evidence and denies "
            "`measurement_validated` because labels, kappa, operator scientific closure, and deployed bridge "
            "evidence remain outside this offline patch."
        ),
        "proxy_regime_section_patch": (
            "Add the proxy-regime matrix as a manuscript-facing diagnostic table. Its certification scope is "
            "limited to proxy/synthetic diagnostic behavior. It must not be described as deployed "
            "V-information certification."
        ),
        "limitations_section_patch": (
            "Add an explicit non-claims paragraph to Section 9: P04 remains deferred/operator-required; "
            "P09 remains BLOCKED_OPERATOR_REQUIRED; P17 is not scientific validation; replay package "
            "completeness is not scientific validation; paper-facing summaries do not upgrade claim levels; "
            "missing labels and kappa block measurement validation."
        ),
    }


def build_context_projection_v10_manuscript_patch(source: Mapping[str, Any] | Path) -> dict[str, Any]:
    source_payload = _load_source(source)
    claim_summary = _claim_summary(source_payload)
    section_patches = _section_patches(source_payload, claim_summary)
    return {
        "patch_schema_version": PATCH_SCHEMA_VERSION,
        "target_manuscript_path": TARGET_MANUSCRIPT_PATH,
        "source_run_id": str(source_payload.get("source_run_id", "")),
        "source_phase": str(source_payload.get("source_phase", "P18")),
        "evidence_mode": str(source_payload.get("evidence_mode", "manuscript_integration_patch")),
        "suggested_insertion_points": deepcopy(list(SUGGESTED_INSERTION_POINTS)),
        "artifact_table": _artifact_table(),
        "claim_gate_table": _claim_gate_table(),
        "proxy_regime_table": _proxy_regime_table(),
        "replay_evidence_table": _replay_evidence_table(),
        "limitation_table": _limitation_table(),
        **section_patches,
        "denied_claims": claim_summary["denied_claims"],
        "operator_required_claims": [
            "P04 operator scientific closure",
            "P09 operator runtime integration",
        ],
        "claim_boundary": {
            "allowed_claim_level": claim_summary["allowed_claim_level"],
            "measurement_validated_allowed": False,
            "p04_status": claim_summary["p04_status"],
            "p09_status": claim_summary["p09_status"],
            "reason_codes": claim_summary["reason_codes"],
            "final_claim_boundary": FINAL_CLAIM_BOUNDARY,
        },
    }


def _markdown_table(headers: tuple[str, ...], rows: list[Mapping[str, Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return lines


def format_context_projection_v10_patch_markdown(patch: Mapping[str, Any]) -> str:
    lines = [
        "# Context Projection v10 P18 Tables and Experiment Patch",
        "",
        "## Target Manuscript",
        "",
        f"- Target manuscript path: `{patch['target_manuscript_path']}`",
        "- This patch does not modify the source manuscript unless separately approved.",
        "- P18 is manuscript integration only.",
        "- P18 does not upgrade claim levels.",
        "- P17 is not scientific validation.",
        "- measurement_validated is not claimed.",
        "",
        "## Recommended Insertion Points",
        "",
        *_markdown_table(("section", "action"), list(patch["suggested_insertion_points"])),
        "",
        "## Table 1: CPS Runtime-Audit Artifacts",
        "",
        *_markdown_table(
            ("artifact", "manuscript_role", "suggested_section", "claim_boundary"),
            list(patch["artifact_table"]),
        ),
        "",
        "## Table 2: Conservative Claim Gate Rules",
        "",
        *_markdown_table(
            ("condition", "allowed_claim_boundary", "denied_claim", "manuscript_note"),
            list(patch["claim_gate_table"]),
        ),
        "",
        "## Table 3: Proxy-Regime Certification Matrix",
        "",
        *_markdown_table(
            ("regime", "manuscript_role", "certification_scope", "claim_boundary"),
            list(patch["proxy_regime_table"]),
        ),
        "",
        "## Table 4: Replay Evidence Package Summary",
        "",
        *_markdown_table(
            ("output", "manuscript_role", "claim_boundary"),
            list(patch["replay_evidence_table"]),
        ),
        "",
        "## Table 5: Limitations and Non-Claims",
        "",
        *_markdown_table(("limitation", "manuscript_note"), list(patch["limitation_table"])),
        "",
        "## Experiment / Evidence Section Patch",
        "",
        patch["experiment_section_patch"],
        "",
        "## Metric Bridge / Claim Gate Patch",
        "",
        patch["metric_bridge_section_patch"],
        "",
        "## Proxy-Regime Certification Patch",
        "",
        patch["proxy_regime_section_patch"],
        "",
        "## Limitations and Non-Claims Patch",
        "",
        patch["limitations_section_patch"],
        "",
        "## Claims That Must Remain Denied",
        "",
    ]
    lines.extend(f"- `{claim}`" for claim in patch.get("denied_claims", []))
    lines.extend(
        [
            "",
            "## Claims Requiring P04/P09/Operator Work",
            "",
        ]
    )
    lines.extend(f"- {claim}" for claim in patch.get("operator_required_claims", []))
    lines.extend(
        [
            "",
            "## Final Claim Boundary",
            "",
            f"- {patch['claim_boundary']['final_claim_boundary']}.",
            f"- measurement_validated_allowed: {str(bool(patch['claim_boundary']['measurement_validated_allowed'])).lower()}",
            f"- P04 status: `{patch['claim_boundary']['p04_status']}`",
            f"- P09 status: `{patch['claim_boundary']['p09_status']}`",
            "- paper-facing summaries do not upgrade claim levels.",
            "- synthetic success is not deployed V-information certification.",
            "- engineering success is not scientific validation.",
            "- replay package completeness is not scientific validation.",
            "",
        ]
    )
    return "\n".join(lines)


def write_context_projection_v10_manuscript_patch(
    output_path: str | Path,
    patch: Mapping[str, Any],
) -> str:
    resolved_output_path = Path(output_path)
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(format_context_projection_v10_patch_markdown(patch), encoding="utf-8")
    return str(resolved_output_path)


def stable_context_projection_v10_patch_json(patch: Mapping[str, Any]) -> str:
    return _stable_json(deepcopy(dict(patch)))
