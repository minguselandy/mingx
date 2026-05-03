from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.human_label_kappa import LABEL_DIMENSIONS


PRELABEL_SCHEMA_VERSION = "LLMAssistedPrelabelsV1"
SOURCE_PHASE = "P32"
DEFAULT_RUN_ID = "p32_v4_flash_prelabels"
DEFAULT_MODE = "dry_run"
LIVE_MODE = "live_operator_approved"
JUDGE_MODEL_ALIAS = "deepseek_v4_flash"
JUDGE_MODEL_ROLE = "llm_assisted_prelabeler"
LABEL_SOURCE = "llm_assisted_prelabel"
ALLOWED_LABELS = (0, 1, 2)
HUMAN_REVIEW_PRIORITIES = ("low", "medium", "high")
DENIED_CLAIMS = (
    "measurement_validated",
    "human_labeled_validation",
    "scientific_validation_completed",
    "deployed_v_information_certified",
)
REASON_CODE_ORDER = (
    "llm_prelabels_not_human_labels",
    "human_confirmation_required",
    "human_labels_required",
    "kappa_required",
    "contamination_audit_required",
    "fresh_metric_bridge_required",
    "claim_gate_required",
    "measurement_validated_denied",
)
REQUIRED_LIVE_FIELDS = (
    "judge_model_endpoint",
    "judge_model_name",
    "input_artifact_root",
    "output_root",
    "max_items",
    "budget_cap",
)
SECRET_KEY_PARTS = ("api_key", "apikey", "secret", "token", "password", "credential")

ModelCallFn = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class PrelabelGateError(RuntimeError):
    """Raised before any live prelabel call when a required gate is absent."""


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _stable_jsonl(rows: Sequence[Mapping[str, Any]]) -> str:
    return "\n".join(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) for row in rows) + (
        "\n" if rows else ""
    )


def _stable_write_json(path: str | Path, payload: Any) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_stable_json(payload), encoding="utf-8")
    return output_path


def _stable_write_jsonl(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_stable_jsonl(rows), encoding="utf-8")
    return output_path


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ordered_reason_codes(reasons: set[str]) -> list[str]:
    order = {reason: index for index, reason in enumerate(REASON_CODE_ORDER)}
    return sorted(reasons, key=lambda reason: (order.get(reason, len(order)), reason))


def _is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return not text or text.startswith("<") or text.endswith(">")


def _contains_secret_key(payload: Any) -> bool:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            lowered = str(key).lower()
            if any(part in lowered for part in SECRET_KEY_PARTS) and str(value or "").strip():
                return True
            if _contains_secret_key(value):
                return True
    elif isinstance(payload, list):
        return any(_contains_secret_key(item) for item in payload)
    return False


def _default_manifest(output_root: Path, *, input_artifact_root: Path | None = None) -> dict[str, Any]:
    return {
        "prelabel_run_id": DEFAULT_RUN_ID,
        "mode": DEFAULT_MODE,
        "judge_model_alias": JUDGE_MODEL_ALIAS,
        "judge_model_role": JUDGE_MODEL_ROLE,
        "judge_model_endpoint": "",
        "judge_model_name": "",
        "input_artifact_root": str(input_artifact_root or ""),
        "output_root": str(output_root),
        "max_items": 50,
        "budget_cap": "",
        "operator_approval": False,
        "llm_prelabels_are_human_labels": False,
        "codex_subagent_audit_is_human_review": False,
        "human_confirmation_required": True,
        "kappa_required_for_measurement_validated": True,
        "contamination_audit_required": True,
        "metric_bridge_freshness_required": True,
        "claim_gate_required": True,
        "forbidden_claims": list(DENIED_CLAIMS),
    }


def _resolve_manifest(
    output_root: Path,
    *,
    manifest: Mapping[str, Any] | None,
    manifest_path: str | Path | None,
    input_artifact_root: str | Path | None,
) -> tuple[dict[str, Any], Path | None]:
    root_path = Path(input_artifact_root).resolve() if input_artifact_root is not None else None
    resolved = _default_manifest(output_root, input_artifact_root=root_path)
    resolved_path: Path | None = None
    if manifest_path is not None:
        resolved_path = Path(manifest_path).resolve()
        if not resolved_path.exists():
            raise PrelabelGateError("manifest_path does not exist")
        resolved.update(_read_json(resolved_path))
    if manifest is not None:
        resolved.update(deepcopy(dict(manifest)))
    mode = str(resolved.get("mode") or DEFAULT_MODE)
    if mode not in {DEFAULT_MODE, LIVE_MODE}:
        raise ValueError(f"unsupported prelabel mode: {mode}")
    resolved["mode"] = mode
    resolved["judge_model_alias"] = str(resolved.get("judge_model_alias") or JUDGE_MODEL_ALIAS)
    resolved["judge_model_role"] = str(resolved.get("judge_model_role") or JUDGE_MODEL_ROLE)
    resolved["output_root"] = str(output_root)
    if root_path is not None:
        resolved["input_artifact_root"] = str(root_path)
    resolved["llm_prelabels_are_human_labels"] = False
    resolved["codex_subagent_audit_is_human_review"] = False
    resolved["human_confirmation_required"] = True
    resolved["kappa_required_for_measurement_validated"] = True
    resolved["contamination_audit_required"] = True
    resolved["metric_bridge_freshness_required"] = True
    resolved["claim_gate_required"] = True
    resolved["forbidden_claims"] = list(DENIED_CLAIMS)
    return resolved, resolved_path


def _validate_live_gates(
    *,
    manifest: Mapping[str, Any],
    manifest_path: Path | None,
    model_call_fn: ModelCallFn | None,
) -> None:
    if manifest["mode"] != LIVE_MODE:
        return
    if os.environ.get("CPS_ALLOW_LLM_PRELABEL") != "1":
        raise PrelabelGateError("CPS_ALLOW_LLM_PRELABEL=1 is required for live prelabel mode")
    if manifest_path is None:
        raise PrelabelGateError("manifest_path is required for live prelabel mode")
    if bool(manifest.get("operator_approval")) is not True:
        raise PrelabelGateError("operator_approval must be true for live prelabel mode")
    if manifest.get("judge_model_alias") != JUDGE_MODEL_ALIAS:
        raise PrelabelGateError("judge_model_alias must be deepseek_v4_flash")
    missing = [field for field in REQUIRED_LIVE_FIELDS if _is_placeholder(manifest.get(field))]
    if missing:
        raise PrelabelGateError(f"missing fixed live prelabel fields: {', '.join(missing)}")
    input_root = Path(str(manifest["input_artifact_root"]))
    if not input_root.exists():
        raise PrelabelGateError("input_artifact_root must exist for live prelabel mode")
    if _contains_secret_key(manifest):
        raise PrelabelGateError("manifest must not contain credentials or secret fields")
    if model_call_fn is None:
        raise PrelabelGateError("model_call_fn is required for live prelabel mode")


def _normalize_case_artifact(case_artifact: Mapping[str, Any], index: int) -> dict[str, Any]:
    payload = deepcopy(dict(case_artifact))
    payload["case_id"] = str(payload.get("case_id") or f"case-{index + 1:03d}")
    payload["condition"] = str(payload.get("condition") or payload.get("condition_id") or "cps_runtime_audit_scaffold")
    payload["model_alias"] = str(payload.get("model_alias") or JUDGE_MODEL_ALIAS)
    payload["artifact_refs"] = {
        str(key): str(value) for key, value in sorted(dict(payload.get("artifact_refs") or {}).items())
    }
    return payload


def _load_case_artifacts(input_artifact_root: str | Path | None) -> list[dict[str, Any]]:
    if input_artifact_root is None:
        return []
    root = Path(input_artifact_root)
    artifacts: list[dict[str, Any]] = []
    for model_output_path in sorted(root.glob("**/model_output.json")):
        if "reference" in model_output_path.parts:
            continue
        condition = model_output_path.parent.name
        case_id = model_output_path.parent.parent.name if model_output_path.parent.parent != root else "case-001"
        artifact_refs = {
            "model_output_json": str(model_output_path),
        }
        for filename, key in (
            ("input_case.json", "input_case_json"),
            ("candidate_pool.jsonl", "candidate_pool_jsonl"),
            ("projection_plan.json", "projection_plan_json"),
            ("materialized_context.json", "materialized_context_json"),
            ("metric_bridge_witness.json", "metric_bridge_witness_json"),
            ("projection_bundle.json", "projection_bundle_json"),
            ("claim_gate_report.json", "claim_gate_report_json"),
        ):
            candidate = model_output_path.parent / filename
            if candidate.exists():
                artifact_refs[key] = str(candidate)
        artifacts.append(
            _normalize_case_artifact(
                {
                    "case_id": case_id,
                    "condition": condition,
                    "model_alias": JUDGE_MODEL_ALIAS,
                    "artifact_refs": artifact_refs,
                    "model_output": _read_json(model_output_path),
                },
                len(artifacts),
            )
        )
    return artifacts


def _ordered_case_artifacts(case_artifacts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized = [_normalize_case_artifact(row, index) for index, row in enumerate(case_artifacts)]
    return sorted(normalized, key=lambda row: (row["case_id"], row["condition"], row["model_alias"]))


def build_v4_flash_prelabel_prompt(case_artifact: Mapping[str, Any]) -> str:
    normalized = _normalize_case_artifact(case_artifact, 0)
    artifact_json = _stable_json(normalized)
    dimensions = "\n".join(LABEL_DIMENSIONS)
    return "\n".join(
        [
            "You are DeepSeek V4 Flash generating an annotation draft, not a human label.",
            "",
            "You must review the provided CPS case artifacts, selected context, and model output under the empirical validation rubric.",
            "",
            "You must produce JSON only.",
            "",
            "You must not claim to be a human annotator.",
            "You must not mark labels as final.",
            "You must not infer facts not supported by the provided artifacts.",
            "If evidence is insufficient, assign a conservative label and explain uncertainty.",
            "Every label dimension must include rationale and evidence references.",
            "The output will be reviewed by Codex audit subagents and then by human annotators.",
            "Human confirmation and human-human kappa are still required before measurement validation.",
            "",
            "Label scale:",
            "0 = fail",
            "1 = partial",
            "2 = pass",
            "",
            "Required dimensions:",
            dimensions,
            "",
            "Output schema:",
            "{",
            '  "label_source": "llm_assisted_prelabel",',
            '  "judge_model_alias": "deepseek_v4_flash",',
            '  "not_human_label": true,',
            '  "requires_human_confirmation": true,',
            '  "case_id": "...",',
            '  "condition": "...",',
            '  "model_alias": "...",',
            '  "dimension_labels": {',
            '    "<dimension>": {',
            '      "suggested_label": 0 | 1 | 2,',
            '      "confidence_milli": 0-1000,',
            '      "rationale": "...",',
            '      "evidence_refs": ["..."],',
            '      "uncertainty_notes": "...",',
            '      "requires_human_review": true',
            "    }",
            "  },",
            '  "overall_summary": "...",',
            '  "human_review_priority": "low" | "medium" | "high",',
            '  "claim_boundary": {',
            '    "counts_as_human_label": false,',
            '    "measurement_validated_allowed": false',
            "  }",
            "}",
            "",
            "Provided CPS case artifacts:",
            artifact_json,
        ]
    )


def _payload_from_output(output: Mapping[str, Any] | str) -> dict[str, Any]:
    if isinstance(output, str):
        try:
            payload = json.loads(output)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid prelabel JSON") from exc
    else:
        payload = deepcopy(dict(output))
    if not isinstance(payload, dict):
        raise ValueError("prelabel output must be a JSON object")
    return payload


def _require_false(value: Any, field: str) -> None:
    if bool(value) is not False:
        raise ValueError(f"{field} must be false")


def _require_true(value: Any, field: str) -> None:
    if bool(value) is not True:
        raise ValueError(f"{field} must be true")


def parse_llm_prelabel_output(output: Mapping[str, Any] | str) -> dict[str, Any]:
    payload = _payload_from_output(output)
    if payload.get("label_source") != LABEL_SOURCE:
        raise ValueError("label_source must be llm_assisted_prelabel")
    if payload.get("judge_model_alias") != JUDGE_MODEL_ALIAS:
        raise ValueError("judge_model_alias must be deepseek_v4_flash")
    _require_true(payload.get("not_human_label"), "not_human_label")
    _require_true(payload.get("requires_human_confirmation"), "requires_human_confirmation")
    claim_boundary = dict(payload.get("claim_boundary") or {})
    _require_false(claim_boundary.get("measurement_validated_allowed"), "claim_boundary.measurement_validated_allowed")
    _require_false(claim_boundary.get("counts_as_human_label"), "claim_boundary.counts_as_human_label")
    dimension_labels = dict(payload.get("dimension_labels") or {})
    missing_dimensions = [dimension for dimension in LABEL_DIMENSIONS if dimension not in dimension_labels]
    if missing_dimensions:
        raise ValueError(f"missing label dimensions: {', '.join(missing_dimensions)}")

    normalized_dimensions: dict[str, dict[str, Any]] = {}
    for dimension in LABEL_DIMENSIONS:
        row = dict(dimension_labels[dimension])
        label = row.get("suggested_label")
        if label not in ALLOWED_LABELS:
            raise ValueError(f"invalid suggested_label for {dimension}")
        confidence = row.get("confidence_milli")
        if not isinstance(confidence, int) or confidence < 0 or confidence > 1000:
            raise ValueError(f"invalid confidence_milli for {dimension}")
        _require_true(row.get("requires_human_review"), f"{dimension}.requires_human_review")
        evidence_refs = row.get("evidence_refs")
        if not isinstance(evidence_refs, list):
            raise ValueError(f"evidence_refs for {dimension} must be a list")
        normalized_dimensions[dimension] = {
            "suggested_label": int(label),
            "confidence_milli": int(confidence),
            "rationale": str(row.get("rationale") or ""),
            "evidence_refs": [str(ref) for ref in evidence_refs],
            "uncertainty_notes": str(row.get("uncertainty_notes") or ""),
            "requires_human_review": True,
        }

    priority = str(payload.get("human_review_priority") or "medium")
    if priority not in HUMAN_REVIEW_PRIORITIES:
        raise ValueError("human_review_priority must be low, medium, or high")
    return {
        "prelabel_run_id": str(payload.get("prelabel_run_id") or ""),
        "label_source": LABEL_SOURCE,
        "judge_model_alias": JUDGE_MODEL_ALIAS,
        "not_human_label": True,
        "requires_human_confirmation": True,
        "case_id": str(payload.get("case_id") or ""),
        "condition": str(payload.get("condition") or ""),
        "model_alias": str(payload.get("model_alias") or ""),
        "dimension_labels": normalized_dimensions,
        "overall_summary": str(payload.get("overall_summary") or ""),
        "human_review_priority": priority,
        "claim_boundary": {
            "counts_as_human_label": False,
            "measurement_validated_allowed": False,
        },
        "counts_as_human_labels": False,
        "measurement_validated_allowed": False,
        "subagent_audit_is_not_human_label": True,
    }


def _dry_run_prelabel(case_artifact: Mapping[str, Any], *, prelabel_run_id: str) -> dict[str, Any]:
    normalized = _normalize_case_artifact(case_artifact, 0)
    artifact_refs = list(normalized.get("artifact_refs", {}).values()) or ["provided_case_artifact"]
    dimension_labels = {}
    for index, dimension in enumerate(LABEL_DIMENSIONS):
        dimension_labels[dimension] = {
            "suggested_label": 1,
            "confidence_milli": 600 + index,
            "rationale": f"Dry-run annotation draft for {dimension}; human confirmation remains required.",
            "evidence_refs": artifact_refs,
            "uncertainty_notes": "Dry-run prelabel; not a human label.",
            "requires_human_review": True,
        }
    return parse_llm_prelabel_output(
        {
            "prelabel_run_id": prelabel_run_id,
            "label_source": LABEL_SOURCE,
            "judge_model_alias": JUDGE_MODEL_ALIAS,
            "not_human_label": True,
            "requires_human_confirmation": True,
            "case_id": normalized["case_id"],
            "condition": normalized["condition"],
            "model_alias": normalized["model_alias"],
            "dimension_labels": dimension_labels,
            "overall_summary": "Dry-run DeepSeek V4 Flash annotation draft; human review required.",
            "human_review_priority": "medium",
            "claim_boundary": {
                "counts_as_human_label": False,
                "measurement_validated_allowed": False,
            },
        }
    )


def _prelabel_summary(
    *,
    manifest: Mapping[str, Any],
    prelabels: Sequence[Mapping[str, Any]],
    parse_failures: Sequence[Mapping[str, Any]],
    generated_audit_requests: int = 0,
    audit_report_present: bool = False,
) -> dict[str, Any]:
    reasons = {
        "llm_prelabels_not_human_labels",
        "human_confirmation_required",
        "human_labels_required",
        "kappa_required",
        "contamination_audit_required",
        "fresh_metric_bridge_required",
        "claim_gate_required",
        "measurement_validated_denied",
    }
    return {
        "prelabel_schema_version": PRELABEL_SCHEMA_VERSION,
        "source_phase": SOURCE_PHASE,
        "prelabel_run_id": str(manifest["prelabel_run_id"]),
        "mode": str(manifest["mode"]),
        "judge_model_alias": JUDGE_MODEL_ALIAS,
        "judge_model_role": JUDGE_MODEL_ROLE,
        "item_count": len(prelabels),
        "dimensions": list(LABEL_DIMENSIONS),
        "prelabels_generated": len(prelabels),
        "parse_failures": [dict(row) for row in parse_failures],
        "subagent_audit_requests_generated": int(generated_audit_requests),
        "subagent_audit_report_present": bool(audit_report_present),
        "human_confirmation_required": True,
        "counts_as_human_labels": False,
        "human_labels_present": False,
        "kappa_present": False,
        "subagent_audit_is_not_human_label": True,
        "measurement_validated_allowed": False,
        "denied_claims": list(DENIED_CLAIMS),
        "reason_codes": _ordered_reason_codes(reasons),
        "next_required_steps": [
            "human annotation",
            "human-human kappa calculation",
            "contamination audit",
            "metric bridge freshness review",
            "claim gate decision",
        ],
    }


def format_llm_prelabel_summary_markdown(summary: Mapping[str, Any]) -> str:
    payload = deepcopy(dict(summary))
    lines = [
        "# LLM-Assisted Prelabel Summary",
        "",
        f"- Prelabel run id: `{payload.get('prelabel_run_id', '')}`",
        f"- Judge model alias: `{payload.get('judge_model_alias', JUDGE_MODEL_ALIAS)}`",
        f"- Prelabels generated: {payload.get('prelabels_generated', 0)}",
        f"- Human confirmation required: {str(bool(payload.get('human_confirmation_required', True))).lower()}",
        f"- Counts as human labels: {str(bool(payload.get('counts_as_human_labels', False))).lower()}",
        f"- measurement_validated_allowed: {str(bool(payload.get('measurement_validated_allowed', False))).lower()}",
        "",
        "## Reason Codes",
        "",
    ]
    lines.extend(f"- `{reason}`" for reason in payload.get("reason_codes", []))
    lines.extend(["", "## Next Required Steps", ""])
    lines.extend(f"- {step}" for step in payload.get("next_required_steps", []))
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- LLM prelabels are annotation drafts, not human labels.",
            "- Codex subagent audit is not human review.",
            "- Human labels, human-human kappa, contamination audit, fresh metric bridge, and claim gate allow remain required.",
            "- P04 remains deferred/operator-required.",
            "- P09 remains BLOCKED_OPERATOR_REQUIRED.",
            "",
        ]
    )
    return "\n".join(lines)


def write_llm_prelabel_outputs(
    output_root: str | Path,
    prelabels: Sequence[Mapping[str, Any]],
    summary: Mapping[str, Any],
) -> dict[str, str]:
    resolved_output_root = Path(output_root)
    resolved_output_root.mkdir(parents=True, exist_ok=True)
    outputs = {
        "llm_prelabels_jsonl": _stable_write_jsonl(resolved_output_root / "llm_prelabels.jsonl", prelabels),
        "llm_prelabel_summary_json": _stable_write_json(resolved_output_root / "llm_prelabel_summary.json", summary),
    }
    summary_markdown = resolved_output_root / "llm_prelabel_summary.md"
    summary_markdown.write_text(format_llm_prelabel_summary_markdown(summary), encoding="utf-8")
    outputs["llm_prelabel_summary_markdown"] = summary_markdown
    return {key: str(path.resolve()) for key, path in outputs.items()}


def _prompt_payload(manifest: Mapping[str, Any], case_artifact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "prelabel_run_id": str(manifest["prelabel_run_id"]),
        "judge_model_alias": JUDGE_MODEL_ALIAS,
        "judge_model_name": str(manifest.get("judge_model_name") or ""),
        "prompt": build_v4_flash_prelabel_prompt(case_artifact),
        "case_id": str(case_artifact["case_id"]),
        "condition": str(case_artifact["condition"]),
        "not_human_label": True,
        "measurement_validated_allowed": False,
    }


def build_llm_assisted_prelabels(
    output_root: str | Path,
    *,
    manifest: Mapping[str, Any] | None = None,
    manifest_path: str | Path | None = None,
    input_artifact_root: str | Path | None = None,
    case_artifacts: Sequence[Mapping[str, Any]] | None = None,
    model_call_fn: ModelCallFn | None = None,
) -> dict[str, Any]:
    resolved_output_root = Path(output_root).resolve()
    resolved_manifest, resolved_manifest_path = _resolve_manifest(
        resolved_output_root,
        manifest=manifest,
        manifest_path=manifest_path,
        input_artifact_root=input_artifact_root,
    )
    _validate_live_gates(
        manifest=resolved_manifest,
        manifest_path=resolved_manifest_path,
        model_call_fn=model_call_fn,
    )
    artifacts = _ordered_case_artifacts(case_artifacts or _load_case_artifacts(input_artifact_root))
    max_items = int(resolved_manifest.get("max_items", 50) or 50)
    artifacts = artifacts[: max(0, max_items)]

    prelabels: list[dict[str, Any]] = []
    parse_failures: list[dict[str, Any]] = []
    for artifact in artifacts:
        try:
            if resolved_manifest["mode"] == LIVE_MODE:
                assert model_call_fn is not None
                raw_output = model_call_fn(_prompt_payload(resolved_manifest, artifact))
                parsed = parse_llm_prelabel_output(raw_output)
            else:
                parsed = _dry_run_prelabel(artifact, prelabel_run_id=str(resolved_manifest["prelabel_run_id"]))
            parsed["prelabel_run_id"] = str(resolved_manifest["prelabel_run_id"])
            prelabels.append(parsed)
        except ValueError as exc:
            parse_failures.append(
                {
                    "case_id": str(artifact.get("case_id", "")),
                    "condition": str(artifact.get("condition", "")),
                    "error": str(exc),
                }
            )

    prelabels = sorted(prelabels, key=lambda row: (row["case_id"], row["condition"], row["model_alias"]))
    summary = _prelabel_summary(manifest=resolved_manifest, prelabels=prelabels, parse_failures=parse_failures)
    generated_outputs = write_llm_prelabel_outputs(resolved_output_root, prelabels, summary)
    return {
        "prelabel_schema_version": PRELABEL_SCHEMA_VERSION,
        "manifest": resolved_manifest,
        "prelabels": prelabels,
        "summary": summary,
        "generated_outputs": generated_outputs,
        "human_labels_present": False,
        "kappa_present": False,
        "measurement_validated_allowed": False,
    }
