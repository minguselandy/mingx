from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.contamination_audit import (
    build_contamination_audit_template,
    evaluate_contamination_audit,
    write_contamination_audit_outputs,
)
from cps.experiments.controlled_live_pilot import build_controlled_live_pilot, default_run_manifest
from cps.experiments.empirical_evidence_package import build_empirical_evidence_package
from cps.experiments.human_label_kappa import (
    build_human_label_kappa_report,
    format_human_labels_template_csv,
    format_human_labels_template_jsonl,
    write_human_label_kappa_outputs,
)


REHEARSAL_SCHEMA_VERSION = "OperatorDryRunRehearsalV1"
DEFAULT_RUN_ID = "p30_operator_dry_run_rehearsal"
EVIDENCE_LEVEL = "EV2_dry_run_rehearsal"
MODE = "dry_run"
P04_STATUS = "deferred/operator-required"
P09_STATUS = "BLOCKED_OPERATOR_REQUIRED"
MODEL_CONDITIONS = (
    {
        "model_alias": "deepseek_v4_flash",
        "model_role": "primary_pilot_model",
        "case_ids": ("case-001", "case-002"),
    },
    {
        "model_alias": "deepseek_v4_pro",
        "model_role": "strong_model_audit_subset",
        "case_ids": ("case-001",),
    },
)
CONDITIONS = (
    "no_cps_baseline",
    "heuristic_selector_baseline",
    "cps_runtime_audit_scaffold",
)
DENIED_CLAIMS = (
    "measurement_validated",
    "scientific_validation",
    "live_empirical_validation_completed",
    "deployed_v_information_certification",
)


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _stable_write_json(path: str | Path, payload: Any) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_stable_json(payload), encoding="utf-8")
    return output_path


def _case_payload(case_id: str) -> dict[str, Any]:
    case_index = int(case_id.split("-")[-1])
    return {
        "case_id": case_id,
        "input": f"P30 dry-run rehearsal case {case_index}.",
        "candidates": [
            {
                "item_id": f"{case_id}-bridge",
                "text": f"Metric bridge placeholder evidence for {case_id}.",
                "token_cost": 5,
                "score": 0.9,
            },
            {
                "item_id": f"{case_id}-labels",
                "text": f"Human labels are required before validation for {case_id}.",
                "token_cost": 6,
                "score": 0.7,
            },
            {
                "item_id": f"{case_id}-contamination",
                "text": f"Contamination audit remains unknown for {case_id}.",
                "token_cost": 6,
                "score": 0.6,
            },
        ],
    }


def _model_manifest(*, run_id: str, model: Mapping[str, Any], output_root: Path) -> dict[str, Any]:
    model_alias = str(model["model_alias"])
    manifest = default_run_manifest(output_root=output_root)
    manifest.update(
        {
            "run_id": f"{run_id}_{model_alias}",
            "evidence_level": EVIDENCE_LEVEL,
            "mode": MODE,
            "model_endpoint": f"<dry_run_placeholder_{model_alias}_endpoint>",
            "model_name": f"<dry_run_placeholder_{model_alias}_model_name>",
            "prompt_template_id": "p30_dry_run_rehearsal_template",
            "temperature": 0,
            "max_cases": len(model["case_ids"]),
            "conditions": list(CONDITIONS),
            "operator_approval": False,
            "live_api_used": False,
            "external_runtime_used": False,
            "p04_status": P04_STATUS,
            "p09_status": P09_STATUS,
        }
    )
    return manifest


def _relative_outputs() -> dict[str, str]:
    return {
        "dry_run_manifest_json": "dry_run_manifest.json",
        "pilot_summary_json": "pilot_summary.json",
        "human_labels_template_csv": "human_labels_template.csv",
        "human_labels_template_jsonl": "human_labels_template.jsonl",
        "human_label_completeness_report_json": "human_label_completeness_report.json",
        "kappa_report_json": "kappa_report.json",
        "contamination_report_json": "contamination_report.json",
        "empirical_evidence_manifest_json": "empirical_evidence_manifest.json",
        "empirical_claim_gate_report_json": "empirical_claim_gate_report.json",
        "empirical_evidence_summary_markdown": "empirical_evidence_summary.md",
        "rehearsal_summary_json": "rehearsal_summary.json",
        "rehearsal_summary_markdown": "rehearsal_summary.md",
    }


def _absolute_outputs(output_root: Path) -> dict[str, str]:
    return {key: str((output_root / relative).resolve()) for key, relative in _relative_outputs().items()}


def _template_case_ids() -> list[str]:
    case_ids: list[str] = []
    for model in MODEL_CONDITIONS:
        model_alias = str(model["model_alias"])
        case_ids.extend(f"{model_alias}::{case_id}" for case_id in model["case_ids"])
    return sorted(case_ids)


def _pilot_summary_payload(
    *,
    run_id: str,
    model_results: list[dict[str, Any]],
    empirical_package: Mapping[str, Any],
) -> dict[str, Any]:
    total_dispatch_count = sum(int(result["pilot_summary"]["dispatch_count"]) for result in model_results)
    total_artifact_count = sum(int(result["pilot_summary"]["case_artifact_count"]) for result in model_results)
    return {
        "rehearsal_schema_version": REHEARSAL_SCHEMA_VERSION,
        "run_id": run_id,
        "evidence_level": EVIDENCE_LEVEL,
        "mode": MODE,
        "model_aliases": [str(model["model_alias"]) for model in MODEL_CONDITIONS],
        "conditions": list(CONDITIONS),
        "dispatch_count": total_dispatch_count,
        "case_artifact_count": total_artifact_count,
        "live_api_used": False,
        "external_runtime_used": False,
        "human_labels_present": False,
        "kappa_present": False,
        "contamination_status": str(empirical_package["contamination_status"]),
        "metric_bridge_freshness": str(empirical_package["metric_bridge_freshness"]),
        "allowed_empirical_claim_level": str(empirical_package["allowed_empirical_claim_level"]),
        "measurement_validated_allowed": False,
        "reason_codes": list(empirical_package["reason_codes"]),
        "p04_status": P04_STATUS,
        "p09_status": P09_STATUS,
        "model_summaries": [
            {
                "model_alias": str(result["model_alias"]),
                "run_id": str(result["manifest"]["run_id"]),
                "mode": str(result["manifest"]["mode"]),
                "case_ids": list(result["case_ids"]),
                "conditions": list(result["manifest"]["conditions"]),
                "dispatch_count": int(result["pilot_summary"]["dispatch_count"]),
                "case_artifact_count": int(result["pilot_summary"]["case_artifact_count"]),
                "live_api_used": bool(result["manifest"]["live_api_used"]),
                "external_runtime_used": bool(result["manifest"]["external_runtime_used"]),
                "output_dir": f"case_artifacts/{result['model_alias']}",
            }
            for result in model_results
        ],
    }


def _dry_run_manifest_payload(
    *,
    run_id: str,
    empirical_package: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "rehearsal_schema_version": REHEARSAL_SCHEMA_VERSION,
        "run_id": run_id,
        "evidence_level": EVIDENCE_LEVEL,
        "mode": MODE,
        "models": [
            {
                "model_alias": str(model["model_alias"]),
                "model_role": str(model["model_role"]),
                "mode": MODE,
                "case_ids": list(model["case_ids"]),
                "case_count": len(model["case_ids"]),
                "model_endpoint": f"<dry_run_placeholder_{model['model_alias']}_endpoint>",
                "model_name": f"<dry_run_placeholder_{model['model_alias']}_model_name>",
                "live_api_used": False,
                "external_runtime_used": False,
            }
            for model in MODEL_CONDITIONS
        ],
        "conditions": list(CONDITIONS),
        "case_count": sum(len(model["case_ids"]) for model in MODEL_CONDITIONS),
        "live_api_used": False,
        "external_runtime_used": False,
        "human_labels_present": False,
        "kappa_present": False,
        "contamination_status": str(empirical_package["contamination_status"]),
        "metric_bridge_freshness": str(empirical_package["metric_bridge_freshness"]),
        "measurement_validated_allowed": False,
        "denied_claims": list(DENIED_CLAIMS),
        "reason_codes": list(empirical_package["reason_codes"]),
        "generated_outputs": _relative_outputs(),
        "p04_status": P04_STATUS,
        "p09_status": P09_STATUS,
        "claim_boundary": (
            "P30 is a dry-run rehearsal only; no live API was called; no labels, kappa, or contamination pass "
            "were fabricated; measurement_validated is not claimed."
        ),
    }


def _rehearsal_summary_payload(
    *,
    run_id: str,
    dry_run_manifest: Mapping[str, Any],
    pilot_summary: Mapping[str, Any],
    empirical_package: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "rehearsal_schema_version": REHEARSAL_SCHEMA_VERSION,
        "run_id": run_id,
        "evidence_level": EVIDENCE_LEVEL,
        "mode": MODE,
        "model_aliases": [model["model_alias"] for model in dry_run_manifest["models"]],
        "conditions": list(CONDITIONS),
        "generated_outputs": _relative_outputs(),
        "pilot_summary": deepcopy(dict(pilot_summary)),
        "empirical_claim_summary": {
            "allowed_empirical_claim_level": str(empirical_package["allowed_empirical_claim_level"]),
            "measurement_validated_allowed": bool(empirical_package["measurement_validated_allowed"]),
            "denied_claims": list(empirical_package["denied_claims"]),
            "reason_codes": list(empirical_package["reason_codes"]),
        },
        "live_api_used": False,
        "external_runtime_used": False,
        "human_labels_present": False,
        "kappa_present": False,
        "contamination_status": str(empirical_package["contamination_status"]),
        "metric_bridge_freshness": str(empirical_package["metric_bridge_freshness"]),
        "measurement_validated_allowed": False,
        "p04_status": P04_STATUS,
        "p09_status": P09_STATUS,
        "next_step": "P31 Operator-Approved Live Pilot Execution Decision",
    }


def format_operator_dry_run_rehearsal_markdown(summary: Mapping[str, Any]) -> str:
    payload = deepcopy(dict(summary))
    lines = [
        "# Operator Dry-Run Rehearsal",
        "",
        "## Summary",
        "",
        f"- Run id: `{payload['run_id']}`",
        f"- Evidence level: `{payload['evidence_level']}`",
        f"- Mode: `{payload['mode']}`",
        f"- Live API used: {str(bool(payload['live_api_used'])).lower()}",
        f"- External runtime used: {str(bool(payload['external_runtime_used'])).lower()}",
        f"- Human labels present: {str(bool(payload['human_labels_present'])).lower()}",
        f"- Kappa present: {str(bool(payload['kappa_present'])).lower()}",
        f"- Contamination status: `{payload['contamination_status']}`",
        f"- Metric bridge freshness: `{payload['metric_bridge_freshness']}`",
        f"- measurement_validated_allowed: {str(bool(payload['measurement_validated_allowed'])).lower()}",
        f"- P04 status: `{payload['p04_status']}`",
        f"- P09 status: `{payload['p09_status']}`",
        "",
        "## Model Conditions",
        "",
    ]
    for model_alias in payload["model_aliases"]:
        lines.append(f"- `{model_alias}`")
    lines.extend(["", "## Conditions", ""])
    for condition in payload["conditions"]:
        lines.append(f"- `{condition}`")
    lines.extend(["", "## Reason Codes", ""])
    reason_codes = payload["empirical_claim_summary"]["reason_codes"]
    if reason_codes:
        lines.extend(f"- `{reason}`" for reason in reason_codes)
    else:
        lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- P30 is a dry-run rehearsal only.",
            "- No live API was called.",
            "- DeepSeek V4 Flash / Pro are dry-run model conditions only.",
            "- No human labels were fabricated.",
            "- No kappa was fabricated.",
            "- No contamination pass was fabricated.",
            "- measurement_validated is denied.",
            "- P04 remains deferred/operator-required.",
            "- P09 remains BLOCKED_OPERATOR_REQUIRED.",
            "",
            "## Next Step",
            "",
            f"- `{payload['next_step']}` only if prerequisites are met.",
            "",
        ]
    )
    return "\n".join(lines)


def build_operator_dry_run_rehearsal(
    output_root: str | Path,
    *,
    run_id: str = DEFAULT_RUN_ID,
) -> dict[str, Any]:
    resolved_output_root = Path(output_root).resolve()
    resolved_output_root.mkdir(parents=True, exist_ok=True)

    model_results: list[dict[str, Any]] = []
    for model in MODEL_CONDITIONS:
        model_alias = str(model["model_alias"])
        model_output_root = resolved_output_root / "case_artifacts" / model_alias
        cases = [_case_payload(case_id) for case_id in model["case_ids"]]
        pilot_result = build_controlled_live_pilot(
            model_output_root,
            run_manifest=_model_manifest(run_id=run_id, model=model, output_root=model_output_root),
            cases=cases,
        )
        pilot_result["model_alias"] = model_alias
        pilot_result["case_ids"] = list(model["case_ids"])
        model_results.append(pilot_result)

    template_cases = _template_case_ids()
    template_csv = format_human_labels_template_csv(
        template_cases,
        conditions=CONDITIONS,
        annotator_ids=("annotator_a", "annotator_b"),
    )
    template_jsonl = format_human_labels_template_jsonl(
        template_cases,
        conditions=CONDITIONS,
        annotator_ids=("annotator_a", "annotator_b"),
    )
    (resolved_output_root / "human_labels_template.csv").write_text(template_csv, encoding="utf-8")
    (resolved_output_root / "human_labels_template.jsonl").write_text(template_jsonl, encoding="utf-8")

    kappa_report = build_human_label_kappa_report(
        [],
        run_id=run_id,
        required_cases=template_cases,
        conditions=CONDITIONS,
    )
    write_human_label_kappa_outputs(resolved_output_root, kappa_report)

    contamination_template = build_contamination_audit_template(run_id=run_id)
    contamination_report = evaluate_contamination_audit(contamination_template["checks"], run_id=run_id)
    write_contamination_audit_outputs(resolved_output_root, contamination_report)

    preliminary_pilot_summary = {
        "run_id": run_id,
        "evidence_level": EVIDENCE_LEVEL,
        "mode": MODE,
        "live_api_used": False,
        "external_runtime_used": False,
        "dispatch_count": sum(int(result["pilot_summary"]["dispatch_count"]) for result in model_results),
        "case_artifact_count": sum(int(result["pilot_summary"]["case_artifact_count"]) for result in model_results),
        "conditions": list(CONDITIONS),
        "human_labels_present": False,
        "kappa_present": False,
        "p04_status": P04_STATUS,
        "p09_status": P09_STATUS,
    }
    empirical_package = build_empirical_evidence_package(
        {
            "run_id": run_id,
            "live_pilot_summary": preliminary_pilot_summary,
            "human_label_completeness_report": kappa_report["completeness_report"],
            "kappa_report": kappa_report,
            "contamination_report": contamination_report,
            "metric_bridge_freshness": "missing",
            "artifact_completeness_status": "complete",
            "claim_gate_allows_measurement_validated": False,
            "p04_status": P04_STATUS,
            "p09_status": P09_STATUS,
        },
        output_root=resolved_output_root,
    )
    pilot_summary = _pilot_summary_payload(
        run_id=run_id,
        model_results=model_results,
        empirical_package=empirical_package,
    )
    dry_run_manifest = _dry_run_manifest_payload(run_id=run_id, empirical_package=empirical_package)
    rehearsal_summary = _rehearsal_summary_payload(
        run_id=run_id,
        dry_run_manifest=dry_run_manifest,
        pilot_summary=pilot_summary,
        empirical_package=empirical_package,
    )

    _stable_write_json(resolved_output_root / "dry_run_manifest.json", dry_run_manifest)
    _stable_write_json(resolved_output_root / "pilot_summary.json", pilot_summary)
    _stable_write_json(resolved_output_root / "rehearsal_summary.json", rehearsal_summary)
    (resolved_output_root / "rehearsal_summary.md").write_text(
        format_operator_dry_run_rehearsal_markdown(rehearsal_summary),
        encoding="utf-8",
    )

    return {
        "status": "dry_run_rehearsal_complete",
        "output_root": str(resolved_output_root),
        "dry_run_manifest": dry_run_manifest,
        "pilot_summary": pilot_summary,
        "human_label_kappa_report": kappa_report,
        "contamination_report": contamination_report,
        "empirical_evidence_package": empirical_package,
        "rehearsal_summary": rehearsal_summary,
        "model_results": model_results,
        "generated_outputs": _absolute_outputs(resolved_output_root),
    }
