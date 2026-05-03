from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any


CONTAMINATION_AUDIT_SCHEMA_VERSION = "ContaminationAuditV1"
REQUIRED_CONTAMINATION_CHECKS = (
    "leaked_labels",
    "seen_during_prompt_or_dev",
    "candidate_pool_contains_direct_answer",
    "unfair_baseline_access",
    "annotator_leakage",
    "duplicated_examples",
    "post_hoc_prompt_tuning_on_test_cases",
    "train_test_overlap",
    "answer_key_exposure",
    "condition_assignment_leakage",
)
CHECK_REASON_CODES = {
    "leaked_labels": "leaked_labels",
    "seen_during_prompt_or_dev": "seen_during_prompt_or_dev",
    "candidate_pool_contains_direct_answer": "direct_answer_in_candidate_pool",
    "unfair_baseline_access": "unfair_baseline_access",
    "annotator_leakage": "annotator_leakage",
    "duplicated_examples": "duplicated_examples",
    "post_hoc_prompt_tuning_on_test_cases": "post_hoc_prompt_tuning",
}
REASON_CODE_ORDER = (
    "contamination_failed",
    "contamination_unknown",
    "contamination_incomplete",
    "leaked_labels",
    "seen_during_prompt_or_dev",
    "direct_answer_in_candidate_pool",
    "unfair_baseline_access",
    "annotator_leakage",
    "duplicated_examples",
    "post_hoc_prompt_tuning",
    "contamination_pass_alone_not_validation",
    "human_labels_required",
    "kappa_required",
    "fresh_metric_bridge_required",
    "claim_gate_allow_required",
)
DENIED_CLAIMS = (
    "measurement_validated",
    "scientific_validation",
    "deployed_v_information_certification",
)


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _stable_write_json(path: str | Path, payload: Any) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_stable_json(payload), encoding="utf-8")
    return output_path


def _ordered_reason_codes(reasons: set[str]) -> list[str]:
    order = {reason: index for index, reason in enumerate(REASON_CODE_ORDER)}
    return sorted(reasons, key=lambda reason: (order.get(reason, len(order)), reason))


def _check_order(check_name: str) -> tuple[int, str]:
    try:
        return (REQUIRED_CONTAMINATION_CHECKS.index(check_name), check_name)
    except ValueError:
        return (len(REQUIRED_CONTAMINATION_CHECKS), check_name)


def _normalize_checks(checks: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for row in checks:
        payload = deepcopy(dict(row))
        check_name = str(payload.get("check_name") or "")
        status = str(payload.get("status") or "unknown").strip().lower()
        if status not in {"pass", "fail", "unknown"}:
            status = "unknown"
        normalized.append(
            {
                "check_name": check_name,
                "status": status,
                "evidence_ref": str(payload.get("evidence_ref") or ""),
                "notes": str(payload.get("notes") or ""),
            }
        )
    return sorted(normalized, key=lambda row: _check_order(row["check_name"]))


def build_contamination_audit_template(*, run_id: str = "") -> dict[str, Any]:
    return {
        "contamination_audit_schema_version": CONTAMINATION_AUDIT_SCHEMA_VERSION,
        "run_id": str(run_id),
        "required_checks": list(REQUIRED_CONTAMINATION_CHECKS),
        "checks": [
            {
                "check_name": check_name,
                "status": "unknown",
                "evidence_ref": "",
                "notes": "",
            }
            for check_name in REQUIRED_CONTAMINATION_CHECKS
        ],
        "measurement_validated_allowed": False,
        "claim_boundary": (
            "This template does not clear contamination. Unknown or incomplete contamination evidence denies "
            "measurement_validated; contamination failure forces pilot_only."
        ),
    }


def evaluate_contamination_audit(
    checks: Sequence[Mapping[str, Any]],
    *,
    run_id: str = "",
) -> dict[str, Any]:
    normalized = _normalize_checks(checks)
    by_name: dict[str, dict[str, str]] = {row["check_name"]: row for row in normalized if row["check_name"]}
    missing_checks = [check_name for check_name in REQUIRED_CONTAMINATION_CHECKS if check_name not in by_name]
    failed_checks = [
        check_name
        for check_name in REQUIRED_CONTAMINATION_CHECKS
        if by_name.get(check_name, {}).get("status") == "fail"
    ]
    unknown_checks = [
        check_name
        for check_name in REQUIRED_CONTAMINATION_CHECKS
        if by_name.get(check_name, {}).get("status") == "unknown" or check_name in missing_checks
    ]

    reasons: set[str] = {"human_labels_required", "kappa_required", "fresh_metric_bridge_required", "claim_gate_allow_required"}
    if failed_checks:
        contamination_status = "failed"
        contamination_passed = False
        allowed_claim_impact = "pilot_only"
        reasons.add("contamination_failed")
        for check_name in failed_checks:
            if check_name in CHECK_REASON_CODES:
                reasons.add(CHECK_REASON_CODES[check_name])
    elif missing_checks:
        contamination_status = "incomplete"
        contamination_passed = False
        allowed_claim_impact = "not_measurement_validated"
        reasons.add("contamination_incomplete")
    elif unknown_checks:
        contamination_status = "unknown"
        contamination_passed = False
        allowed_claim_impact = "not_measurement_validated"
        reasons.add("contamination_unknown")
    else:
        contamination_status = "pass"
        contamination_passed = True
        allowed_claim_impact = "contamination_gate_passed_only"
        reasons.add("contamination_pass_alone_not_validation")

    return {
        "contamination_audit_schema_version": CONTAMINATION_AUDIT_SCHEMA_VERSION,
        "run_id": str(run_id),
        "required_checks": list(REQUIRED_CONTAMINATION_CHECKS),
        "checks": [row for row in normalized if row["check_name"] in REQUIRED_CONTAMINATION_CHECKS],
        "contamination_status": contamination_status,
        "contamination_passed": contamination_passed,
        "failed_checks": sorted(failed_checks, key=_check_order),
        "unknown_checks": sorted(set(unknown_checks), key=_check_order),
        "reason_codes": _ordered_reason_codes(reasons),
        "reason_code_order": list(REASON_CODE_ORDER),
        "allowed_claim_impact": allowed_claim_impact,
        "measurement_validated_allowed": False,
        "denied_claims": list(DENIED_CLAIMS),
        "claim_boundary": (
            "Contamination pass alone is not measurement validation; contamination failure forces pilot_only; "
            "unknown or incomplete contamination denies measurement_validated."
        ),
    }


def format_contamination_audit_markdown(report: Mapping[str, Any]) -> str:
    payload = deepcopy(dict(report))
    lines = [
        "# Contamination Audit Report",
        "",
        "## Summary",
        "",
        f"- Run id: `{payload.get('run_id', '')}`",
        f"- Contamination status: `{payload.get('contamination_status', 'unknown')}`",
        f"- Contamination passed: {str(bool(payload.get('contamination_passed', False))).lower()}",
        f"- Allowed claim impact: `{payload.get('allowed_claim_impact', 'not_measurement_validated')}`",
        f"- measurement_validated_allowed: {str(bool(payload.get('measurement_validated_allowed', False))).lower()}",
        "",
        "## Checks",
        "",
        "| check | status | evidence_ref |",
        "| --- | --- | --- |",
    ]
    checks = list(payload.get("checks") or [])
    by_name = {str(row.get("check_name")): row for row in checks}
    for check_name in REQUIRED_CONTAMINATION_CHECKS:
        row = by_name.get(check_name, {})
        lines.append(
            f"| `{check_name}` | `{row.get('status', 'unknown')}` | `{row.get('evidence_ref', '')}` |"
        )
    lines.extend(["", "## Reason Codes", ""])
    reason_codes = list(payload.get("reason_codes") or [])
    if reason_codes:
        lines.extend(f"- `{reason}`" for reason in reason_codes)
    else:
        lines.append("- `none`")
    lines.extend(["", "## Denied Claims", ""])
    lines.extend(f"- `{claim}`" for claim in payload.get("denied_claims", []))
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Contamination failure forces pilot_only.",
            "- Unknown or incomplete contamination denies measurement_validated.",
            "- Contamination pass alone is not measurement validation.",
            "- Human labels and kappa remain required.",
            "- Fresh metric bridge and claim gate allow remain required.",
            "- P04 remains deferred/operator-required.",
            "- P09 remains BLOCKED_OPERATOR_REQUIRED.",
            "",
        ]
    )
    return "\n".join(lines)


def write_contamination_audit_outputs(output_dir: str | Path, report: Mapping[str, Any]) -> dict[str, str]:
    resolved_output_dir = Path(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    payload = deepcopy(dict(report))
    report_path = _stable_write_json(resolved_output_dir / "contamination_report.json", payload)
    markdown_path = resolved_output_dir / "contamination_report.md"
    markdown_path.write_text(format_contamination_audit_markdown(payload), encoding="utf-8")
    return {
        "contamination_report_json": str(report_path.resolve()),
        "contamination_report_markdown": str(markdown_path.resolve()),
    }
