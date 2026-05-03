from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.artifacts import candidate_pool_hash, context_hash, stable_hash
from cps.experiments.claim_gate_report import build_claim_gate_report
from cps.experiments.evidence_ledger import build_evidence_ledger_from_summary, write_evidence_ledger
from cps.schema.projection_bundle_v1 import ProjectionBundleV1


RUNNER_SCHEMA_VERSION = "ControlledLivePilotRunnerV1"
SOURCE_PHASE = "P26"
DEFAULT_RUN_ID = "p26_controlled_live_pilot"
DEFAULT_MODE = "dry_run"
LIVE_MODE = "live_operator_approved"
EVIDENCE_LEVEL = "EV2_controlled_live_pilot"
DEFAULT_CONDITIONS = (
    "no_cps_baseline",
    "heuristic_selector_baseline",
    "cps_runtime_audit_scaffold",
)
REQUIRED_LIVE_FIELDS = (
    "model_endpoint",
    "model_name",
    "prompt_template_id",
    "temperature",
    "output_root",
)
FINAL_CLAIM_BOUNDARY = (
    "P26 defaults to dry-run; controlled live pilot alone is not measurement validation; "
    "human labels and kappa remain required; contamination pass and fresh metric bridge remain required; "
    "measurement_validated is not claimed; P04 remains deferred/operator-required; "
    "P09 remains BLOCKED_OPERATOR_REQUIRED"
)

ModelCallFn = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class LivePilotGateError(RuntimeError):
    """Raised before any live call when a required live gate is absent."""


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _stable_write_json(path: str | Path, payload: Any) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_stable_json(payload), encoding="utf-8")
    return output_path


def _stable_write_jsonl(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(dict(row), ensure_ascii=False, sort_keys=True) for row in rows]
    output_path.write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8")
    return output_path


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def default_run_manifest(*, output_root: str | Path) -> dict[str, Any]:
    return {
        "runner_schema_version": RUNNER_SCHEMA_VERSION,
        "run_id": DEFAULT_RUN_ID,
        "evidence_level": EVIDENCE_LEVEL,
        "mode": DEFAULT_MODE,
        "model_endpoint": "",
        "model_name": "",
        "prompt_template_id": "dry-run-template",
        "temperature": 0,
        "max_cases": 50,
        "conditions": list(DEFAULT_CONDITIONS),
        "output_root": str(output_root),
        "operator_approval": False,
        "live_api_used": False,
        "external_runtime_used": False,
        "human_labels_required_for_measurement_validated": True,
        "kappa_required_for_measurement_validated": True,
        "contamination_audit_required": True,
        "metric_bridge_freshness_required": True,
        "human_labels_present": False,
        "kappa_present": False,
        "p04_status": "deferred/operator-required",
        "p09_status": "BLOCKED_OPERATOR_REQUIRED",
    }


def _resolve_manifest(
    *,
    output_root: Path,
    run_manifest: Mapping[str, Any] | None,
    run_manifest_path: str | Path | None,
) -> tuple[dict[str, Any], Path | None]:
    if run_manifest_path is not None:
        resolved_path = Path(run_manifest_path)
        if resolved_path.exists():
            manifest = _read_json(resolved_path)
        elif run_manifest is not None:
            manifest = deepcopy(dict(run_manifest))
        else:
            raise LivePilotGateError("run_manifest_path does not exist")
        return _normalize_manifest(manifest, output_root=output_root), resolved_path
    if run_manifest is not None:
        return _normalize_manifest(run_manifest, output_root=output_root), None
    return default_run_manifest(output_root=output_root), None


def _normalize_manifest(manifest: Mapping[str, Any], *, output_root: Path) -> dict[str, Any]:
    resolved = default_run_manifest(output_root=output_root)
    resolved.update(deepcopy(dict(manifest)))
    mode = str(resolved.get("mode") or DEFAULT_MODE)
    if mode not in {DEFAULT_MODE, LIVE_MODE}:
        raise ValueError(f"unsupported controlled live pilot mode: {mode}")
    resolved["mode"] = mode
    conditions = [str(condition) for condition in resolved.get("conditions") or DEFAULT_CONDITIONS]
    resolved["conditions"] = conditions
    resolved["live_api_used"] = mode == LIVE_MODE
    resolved["external_runtime_used"] = False
    resolved["human_labels_required_for_measurement_validated"] = True
    resolved["kappa_required_for_measurement_validated"] = True
    resolved["contamination_audit_required"] = True
    resolved["metric_bridge_freshness_required"] = True
    resolved["human_labels_present"] = False
    resolved["kappa_present"] = False
    resolved["p04_status"] = str(resolved.get("p04_status") or "deferred/operator-required")
    resolved["p09_status"] = str(resolved.get("p09_status") or "BLOCKED_OPERATOR_REQUIRED")
    return resolved


def _validate_live_gates(
    *,
    manifest: Mapping[str, Any],
    run_manifest_path: Path | None,
    model_call_fn: ModelCallFn | None,
) -> None:
    if manifest["mode"] != LIVE_MODE:
        return
    if os.environ.get("CPS_ALLOW_LIVE_API") != "1":
        raise LivePilotGateError("CPS_ALLOW_LIVE_API=1 is required for live_operator_approved mode")
    if run_manifest_path is None:
        raise LivePilotGateError("run_manifest_path is required for live_operator_approved mode")
    missing_fields = [field for field in REQUIRED_LIVE_FIELDS if manifest.get(field) in {None, ""}]
    if missing_fields:
        raise LivePilotGateError(f"missing required live manifest fields: {', '.join(missing_fields)}")
    if bool(manifest.get("operator_approval")) is not True:
        raise LivePilotGateError("operator_approval must be true for live_operator_approved mode")
    if model_call_fn is None:
        raise LivePilotGateError("model_call_fn is required for live_operator_approved mode")


def _default_cases() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "case-001",
            "input": "Dry-run CPS controlled pilot placeholder case.",
            "candidates": [
                {"item_id": "a", "text": "Bridge evidence placeholder.", "token_cost": 4, "score": 0.8},
                {"item_id": "b", "text": "Replay evidence placeholder.", "token_cost": 4, "score": 0.6},
            ],
        }
    ]


def _normalize_cases(cases: Sequence[Mapping[str, Any]] | None, max_cases: int) -> list[dict[str, Any]]:
    selected = list(cases or _default_cases())[:max(0, int(max_cases))]
    normalized: list[dict[str, Any]] = []
    for index, case in enumerate(selected):
        payload = deepcopy(dict(case))
        payload["case_id"] = str(payload.get("case_id") or f"case-{index + 1:03d}")
        payload["input"] = str(payload.get("input") or payload.get("prompt") or "")
        payload["candidates"] = _normalize_candidates(payload.get("candidates") or [])
        normalized.append(payload)
    return sorted(normalized, key=lambda row: row["case_id"])


def _normalize_candidates(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        payload = deepcopy(dict(candidate))
        item_id = str(payload.get("item_id") or payload.get("candidate_id") or f"item-{index + 1:03d}")
        text = str(payload.get("text") or payload.get("content") or "")
        token_cost = int(payload.get("token_cost", max(1, len(text.split()))) or 1)
        score = float(payload.get("score", payload.get("singleton_value", 0.0)) or 0.0)
        normalized.append(
            {
                "item_id": item_id,
                "text": text,
                "token_cost": token_cost,
                "score": score,
                "singleton_value": score,
            }
        )
    return sorted(normalized, key=lambda row: row["item_id"])


def _selected_candidates(condition_id: str, candidates: Sequence[Mapping[str, Any]], budget_tokens: int) -> list[dict]:
    ordered = [dict(candidate) for candidate in candidates]
    if condition_id == "no_cps_baseline":
        return []
    if condition_id == "heuristic_selector_baseline":
        return ordered[:1]
    if condition_id == "full_context_upper_baseline":
        selected: list[dict[str, Any]] = []
        used = 0
        for candidate in ordered:
            cost = int(candidate["token_cost"])
            if used + cost <= budget_tokens:
                selected.append(candidate)
                used += cost
        return selected
    selected = []
    used = 0
    for candidate in sorted(ordered, key=lambda row: (-float(row["score"]), str(row["item_id"]))):
        cost = int(candidate["token_cost"])
        if used + cost <= budget_tokens:
            selected.append(candidate)
            used += cost
    return selected


def _artifact_payloads(
    *,
    manifest: Mapping[str, Any],
    case: Mapping[str, Any],
    condition_id: str,
) -> dict[str, Any]:
    run_id = str(manifest["run_id"])
    case_id = str(case["case_id"])
    dispatch_id = f"{case_id}:{condition_id}"
    agent_id = "controlled_live_pilot_agent"
    round_id = "round-001"
    budget_tokens = int(case.get("budget_tokens", manifest.get("budget_tokens", 64)) or 64)
    candidates = [dict(candidate) for candidate in case["candidates"]]
    pool_hash = candidate_pool_hash(candidates)
    selected = _selected_candidates(condition_id, candidates, budget_tokens)
    selected_ids = [str(candidate["item_id"]) for candidate in selected]
    excluded_ids = [str(candidate["item_id"]) for candidate in candidates if str(candidate["item_id"]) not in selected_ids]
    content = "\n".join(str(candidate["text"]) for candidate in selected)
    realized_tokens = sum(int(candidate["token_cost"]) for candidate in selected)
    candidate_pool = {
        "run_id": run_id,
        "case_id": case_id,
        "dispatch_id": dispatch_id,
        "agent_id": agent_id,
        "round_id": round_id,
        "condition_id": condition_id,
        "candidate_pool_hash": pool_hash,
        "items": candidates,
    }
    projection_plan = {
        "run_id": run_id,
        "case_id": case_id,
        "dispatch_id": dispatch_id,
        "agent_id": agent_id,
        "round_id": round_id,
        "condition_id": condition_id,
        "algorithm": condition_id,
        "budget_tokens": budget_tokens,
        "candidate_pool_hash": pool_hash,
        "selected_ids": selected_ids,
        "excluded_ids": excluded_ids,
        "trace": [
            {
                "item_id": str(candidate["item_id"]),
                "score": float(candidate["score"]),
                "selected": str(candidate["item_id"]) in selected_ids,
            }
            for candidate in candidates
        ],
        "score_config": {"mode": str(manifest["mode"]), "prompt_template_id": str(manifest["prompt_template_id"])},
    }
    budget_witness = {
        "run_id": run_id,
        "case_id": case_id,
        "dispatch_id": dispatch_id,
        "agent_id": agent_id,
        "round_id": round_id,
        "condition_id": condition_id,
        "budget_tokens": budget_tokens,
        "estimated_tokens": realized_tokens,
        "realized_tokens": realized_tokens,
        "within_budget": realized_tokens <= budget_tokens,
        "selected_ids": selected_ids,
        "excluded_ids": excluded_ids,
        "tolerance_violations": [],
    }
    materialized_context = {
        "run_id": run_id,
        "case_id": case_id,
        "dispatch_id": dispatch_id,
        "agent_id": agent_id,
        "round_id": round_id,
        "condition_id": condition_id,
        "selected_ids": selected_ids,
        "section_order": selected_ids,
        "content": content,
        "token_count": realized_tokens,
        "context_hash": context_hash(content),
    }
    metric_bridge_witness = {
        "run_id": run_id,
        "case_id": case_id,
        "dispatch_id": dispatch_id,
        "agent_id": agent_id,
        "round_id": round_id,
        "condition_id": condition_id,
        "bridge_freshness": "missing",
        "calibration_epoch": None,
        "active_stratum": {"condition_id": condition_id},
        "model_tier": str(manifest.get("model_name") or "dry_run_model"),
        "utility_metric": "operational_pilot_output",
        "metric_class": "operational_only",
        "materialization_policy": {"condition_id": condition_id},
        "decoding_policy": {"temperature": manifest.get("temperature")},
        "bridge_scale": None,
        "bridge_residual_zeta": None,
        "effective_sample_size": None,
        "drift_status": "missing",
        "diagnostic_mode": "controlled_live_pilot",
        "diagnostic_claim_level": "operational_utility_only",
    }
    diagnostics = {
        "run_id": run_id,
        "case_id": case_id,
        "dispatch_id": dispatch_id,
        "agent_id": agent_id,
        "round_id": round_id,
        "condition_id": condition_id,
        "metric_claim_level": "operational_utility_only",
        "selector_regime_label": "ambiguous",
        "selector_action": "controlled_live_pilot_condition",
        "policy_recommendation": "no_measurement_validation_without_labels_kappa_contamination_bridge",
        "notes": "P26 controlled live pilot scaffold only; human labels and kappa are placeholders.",
    }
    bundle = ProjectionBundleV1(
        run_id=run_id,
        dispatch_id=dispatch_id,
        agent_id=agent_id,
        round_id=round_id,
        candidate_pool=candidate_pool,
        projection_plan=projection_plan,
        budget_witness=budget_witness,
        materialized_context=materialized_context,
        metric_bridge_witness=metric_bridge_witness,
        diagnostics=diagnostics,
        source_mode=str(manifest["mode"]),
    )
    bundle_payload = bundle.to_dict()
    bundle_payload["canonical_hash"] = bundle.canonical_hash()
    return {
        "input_case": {
            "run_id": run_id,
            "case_id": case_id,
            "input": str(case["input"]),
            "condition_id": condition_id,
            "input_case_hash": stable_hash({"case_id": case_id, "input": str(case["input"])}),
        },
        "candidate_pool": candidate_pool,
        "projection_plan": projection_plan,
        "budget_witness": budget_witness,
        "materialized_context": materialized_context,
        "metric_bridge_witness": metric_bridge_witness,
        "diagnostics": diagnostics,
        "projection_bundle": bundle_payload,
    }


def _dry_run_model_output(*, manifest: Mapping[str, Any], case_id: str, condition_id: str) -> dict[str, Any]:
    return {
        "content": f"DRY_RUN_OUTPUT::{manifest['run_id']}::{case_id}::{condition_id}",
        "finish_reason": "dry_run",
    }


def _model_payload(
    *,
    manifest: Mapping[str, Any],
    case: Mapping[str, Any],
    condition_id: str,
    materialized_context: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": str(manifest["run_id"]),
        "case_id": str(case["case_id"]),
        "condition_id": condition_id,
        "input": str(case["input"]),
        "materialized_context": deepcopy(dict(materialized_context)),
        "model_endpoint": str(manifest.get("model_endpoint") or ""),
        "model_name": str(manifest.get("model_name") or ""),
        "prompt_template_id": str(manifest.get("prompt_template_id") or ""),
        "temperature": manifest.get("temperature"),
    }


def _write_case_artifacts(
    *,
    case_dir: Path,
    payloads: Mapping[str, Any],
    model_output: Mapping[str, Any],
    claim_gate_report: Mapping[str, Any],
) -> dict[str, str]:
    outputs = {
        "input_case_json": _stable_write_json(case_dir / "input_case.json", payloads["input_case"]),
        "candidate_pool_jsonl": _stable_write_jsonl(case_dir / "candidate_pool.jsonl", payloads["candidate_pool"]["items"]),
        "projection_plan_json": _stable_write_json(case_dir / "projection_plan.json", payloads["projection_plan"]),
        "budget_witness_json": _stable_write_json(case_dir / "budget_witness.json", payloads["budget_witness"]),
        "materialized_context_json": _stable_write_json(
            case_dir / "materialized_context.json",
            payloads["materialized_context"],
        ),
        "metric_bridge_witness_json": _stable_write_json(
            case_dir / "metric_bridge_witness.json",
            payloads["metric_bridge_witness"],
        ),
        "projection_bundle_json": _stable_write_json(case_dir / "projection_bundle.json", payloads["projection_bundle"]),
        "model_output_json": _stable_write_json(case_dir / "model_output.json", model_output),
        "claim_gate_report_json": _stable_write_json(case_dir / "claim_gate_report.json", claim_gate_report),
    }
    return {key: str(path.resolve()) for key, path in outputs.items()}


def _aggregate_summary(
    *,
    manifest: Mapping[str, Any],
    dispatch_count: int,
    projection_bundle_hashes: Sequence[str],
) -> dict[str, Any]:
    artifact_counts = {
        "candidate_pools": dispatch_count,
        "projection_plans": dispatch_count,
        "budget_witnesses": dispatch_count,
        "materialized_contexts": dispatch_count,
        "metric_bridge_witnesses": dispatch_count,
        "diagnostics": dispatch_count,
        "projection_bundles": dispatch_count,
    }
    evidence_mode = "pilot_only" if manifest["mode"] == LIVE_MODE else "engineering_smoke_only"
    return {
        "run_id": str(manifest["run_id"]),
        "evidence_mode": evidence_mode,
        "source_phase": SOURCE_PHASE,
        "dispatch_count": dispatch_count,
        "artifact_counts": artifact_counts,
        "metric_claim_level_counts": {"operational_utility_only": dispatch_count},
        "selector_action_counts": {"controlled_live_pilot_condition": dispatch_count},
        "complete_artifact_sets": dispatch_count > 0,
        "projection_bundle_hashes": sorted(str(value) for value in projection_bundle_hashes),
        "contamination_status": "unknown",
        "human_labels_present": False,
        "kappa_present": False,
        "bridge_freshness": "missing",
        "metric_class": "operational_only",
        "diagnostic_claim_level": "operational_utility_only",
        "live_api_used": bool(manifest["live_api_used"]),
        "external_runtime_used": False,
        "p04_status": str(manifest["p04_status"]),
        "p09_status": str(manifest["p09_status"]),
    }


def _generated_outputs_relative() -> dict[str, str]:
    return {
        "run_manifest_json": "run_manifest.json",
        "pilot_summary_json": "pilot_summary.json",
        "pilot_summary_markdown": "pilot_summary.md",
        "claim_gate_report_json": "claim_gate_report.json",
        "evidence_ledger_json": "evidence_ledger.json",
    }


def _absolute_outputs(output_root: Path) -> dict[str, str]:
    return {key: str((output_root / relative).resolve()) for key, relative in _generated_outputs_relative().items()}


def _pilot_summary_payload(
    *,
    manifest: Mapping[str, Any],
    ledger: Mapping[str, Any],
    claim_gate_report: Mapping[str, Any],
    case_artifacts: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    return {
        "pilot_schema_version": RUNNER_SCHEMA_VERSION,
        "run_id": str(manifest["run_id"]),
        "evidence_level": str(manifest["evidence_level"]),
        "mode": str(manifest["mode"]),
        "case_artifact_count": len(case_artifacts),
        "dispatch_count": int(ledger.get("dispatch_count", 0) or 0),
        "conditions": list(manifest.get("conditions") or []),
        "claim_gate_allowed_level": str(claim_gate_report.get("allowed_claim_level", "ambiguous")),
        "measurement_validated_allowed": bool(claim_gate_report.get("measurement_validated_allowed", False)),
        "denied_claims": list(claim_gate_report.get("denied_claims") or []),
        "reason_codes": list(claim_gate_report.get("reason_codes") or []),
        "live_api_used": bool(manifest["live_api_used"]),
        "external_runtime_used": False,
        "human_labels_required": True,
        "human_labels_present": False,
        "kappa_present": False,
        "p04_status": str(manifest["p04_status"]),
        "p09_status": str(manifest["p09_status"]),
        "final_claim_boundary": FINAL_CLAIM_BOUNDARY,
    }


def format_pilot_summary_markdown(result: Mapping[str, Any]) -> str:
    manifest = dict(result["manifest"])
    report = dict(result["claim_gate_report"])
    summary = dict(result.get("pilot_summary") or {})
    lines = [
        "# Controlled Live API Pilot Runner",
        "",
        "## Summary",
        "",
        f"- Run id: `{manifest['run_id']}`",
        f"- Evidence level: `{manifest['evidence_level']}`",
        f"- Mode: `{manifest['mode']}`",
        f"- Live API used: {str(bool(manifest['live_api_used'])).lower()}",
        f"- External runtime used: {str(bool(manifest['external_runtime_used'])).lower()}",
        f"- Claim gate allowed level: `{report.get('allowed_claim_level', 'ambiguous')}`",
        f"- measurement_validated_allowed: {str(bool(report.get('measurement_validated_allowed', False))).lower()}",
        f"- P04 status: `{manifest['p04_status']}`",
        f"- P09 status: `{manifest['p09_status']}`",
        "",
        "## Conditions",
        "",
    ]
    lines.extend(f"- `{condition}`" for condition in manifest.get("conditions", []))
    lines.extend(["", "## Reason Codes", ""])
    reason_codes = list(report.get("reason_codes") or [])
    if reason_codes:
        lines.extend(f"- `{reason}`" for reason in reason_codes)
    else:
        lines.append("- `none`")
    lines.extend(["", "## Denied Claims", ""])
    denied_claims = list(report.get("denied_claims") or [])
    if denied_claims:
        lines.extend(f"- `{claim}`" for claim in denied_claims)
    else:
        lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- P26 defaults to dry-run.",
            "- Controlled live pilot alone is not measurement validation.",
            "- Human labels and kappa remain required.",
            "- Contamination audit and metric bridge freshness remain required before measurement_validated.",
            "- Live API success alone does not imply measurement validation.",
            "- Engineering success is not scientific validation.",
            "- Synthetic/proxy evidence does not certify deployed V-information submodularity.",
            "- P04 remains deferred/operator-required.",
            "- P09 remains BLOCKED_OPERATOR_REQUIRED.",
            "",
            "## Artifact Summary",
            "",
            f"- Dispatch count: {summary.get('dispatch_count', 0)}",
            f"- Case artifact count: {summary.get('case_artifact_count', 0)}",
            f"- Human labels present: {str(bool(summary.get('human_labels_present', False))).lower()}",
            f"- Kappa present: {str(bool(summary.get('kappa_present', False))).lower()}",
            "",
        ]
    )
    return "\n".join(lines)


def build_controlled_live_pilot(
    output_root: str | Path,
    *,
    run_manifest: Mapping[str, Any] | None = None,
    run_manifest_path: str | Path | None = None,
    cases: Sequence[Mapping[str, Any]] | None = None,
    model_call_fn: ModelCallFn | None = None,
) -> dict[str, Any]:
    resolved_output_root = Path(output_root).resolve()
    manifest, resolved_manifest_path = _resolve_manifest(
        output_root=resolved_output_root,
        run_manifest=run_manifest,
        run_manifest_path=run_manifest_path,
    )
    _validate_live_gates(
        manifest=manifest,
        run_manifest_path=resolved_manifest_path,
        model_call_fn=model_call_fn,
    )
    normalized_cases = _normalize_cases(cases, int(manifest.get("max_cases", 50) or 50))
    conditions = [str(condition) for condition in manifest.get("conditions") or DEFAULT_CONDITIONS]

    case_payload_records: list[dict[str, Any]] = []
    projection_bundle_hashes: list[str] = []
    for case in normalized_cases:
        for condition_id in conditions:
            payloads = _artifact_payloads(manifest=manifest, case=case, condition_id=condition_id)
            projection_bundle_hashes.append(str(payloads["projection_bundle"]["canonical_hash"]))
            case_payload_records.append(
                {
                    "case": case,
                    "condition_id": condition_id,
                    "payloads": payloads,
                }
            )

    summary = _aggregate_summary(
        manifest=manifest,
        dispatch_count=len(case_payload_records),
        projection_bundle_hashes=projection_bundle_hashes,
    )
    ledger = build_evidence_ledger_from_summary(summary)
    claim_gate_report = build_claim_gate_report(ledger)

    resolved_output_root.mkdir(parents=True, exist_ok=True)
    case_artifacts: list[dict[str, str]] = []
    for record in case_payload_records:
        case = record["case"]
        condition_id = str(record["condition_id"])
        payloads = record["payloads"]
        if manifest["mode"] == LIVE_MODE:
            assert model_call_fn is not None
            model_payload = _model_payload(
                manifest=manifest,
                case=case,
                condition_id=condition_id,
                materialized_context=payloads["materialized_context"],
            )
            response_payload = deepcopy(dict(model_call_fn(model_payload)))
        else:
            response_payload = _dry_run_model_output(
                manifest=manifest,
                case_id=str(case["case_id"]),
                condition_id=condition_id,
            )
        model_output = {
            "run_id": str(manifest["run_id"]),
            "case_id": str(case["case_id"]),
            "condition_id": condition_id,
            "mode": str(manifest["mode"]),
            "live_api_used": bool(manifest["live_api_used"]),
            "model_endpoint": str(manifest.get("model_endpoint") or ""),
            "model_name": str(manifest.get("model_name") or ""),
            "prompt_template_id": str(manifest.get("prompt_template_id") or ""),
            "temperature": manifest.get("temperature"),
            "response": response_payload,
        }
        case_dir = resolved_output_root / "cases" / str(case["case_id"]) / condition_id
        case_artifacts.append(
            _write_case_artifacts(
                case_dir=case_dir,
                payloads=payloads,
                model_output=model_output,
                claim_gate_report=claim_gate_report,
            )
        )

    pilot_summary = _pilot_summary_payload(
        manifest=manifest,
        ledger=ledger,
        claim_gate_report=claim_gate_report,
        case_artifacts=case_artifacts,
    )
    result: dict[str, Any] = {
        "status": "pilot_scaffold_complete",
        "manifest": manifest,
        "evidence_ledger": ledger,
        "claim_gate_report": claim_gate_report,
        "pilot_summary": pilot_summary,
        "case_artifacts": case_artifacts,
        "generated_outputs": _absolute_outputs(resolved_output_root),
    }
    _stable_write_json(resolved_output_root / "run_manifest.json", manifest)
    write_evidence_ledger(resolved_output_root / "evidence_ledger.json", ledger)
    _stable_write_json(resolved_output_root / "claim_gate_report.json", claim_gate_report)
    _stable_write_json(resolved_output_root / "pilot_summary.json", pilot_summary)
    (resolved_output_root / "pilot_summary.md").write_text(format_pilot_summary_markdown(result), encoding="utf-8")
    return result
