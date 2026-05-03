from __future__ import annotations

import csv
import io
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.human_label_kappa import LABEL_DIMENSIONS


PRELABEL_AUDIT_SCHEMA_VERSION = "PrelabelSubagentAuditV1"
SOURCE_PHASE = "P32"
AUDIT_SOURCE = "codex_subagent_audit"
AUDIT_ROLES = (
    "evidence_alignment_reviewer",
    "rubric_consistency_reviewer",
    "claim_boundary_reviewer",
    "uncertainty_reviewer",
    "cross_condition_consistency_reviewer",
)
AUDIT_VERDICTS = ("ACCEPT_DRAFT", "REQUEST_HUMAN_PRIORITY", "REJECT_DRAFT")
ISSUE_SEVERITIES = ("low", "medium", "high", "blocking")
HUMAN_ACTIONS = ("accept", "modify", "reject", "adjudicate")
DENIED_CLAIMS = (
    "measurement_validated",
    "human_labeled_validation",
    "scientific_validation_completed",
    "deployed_v_information_certified",
)
REASON_CODE_ORDER = (
    "llm_prelabels_not_human_labels",
    "codex_subagent_audit_not_human_review",
    "human_confirmation_required",
    "kappa_required",
    "contamination_audit_required",
    "fresh_metric_bridge_required",
    "claim_gate_required",
    "measurement_validated_denied",
)


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


def _ordered_reason_codes() -> list[str]:
    return list(REASON_CODE_ORDER)


def _audit_role_prompt(audit_role: str, prelabel: Mapping[str, Any]) -> str:
    role_focus = {
        "evidence_alignment_reviewer": "Check whether each suggested label is supported by cited evidence_refs.",
        "rubric_consistency_reviewer": "Check whether label values match the rubric definitions.",
        "claim_boundary_reviewer": "Check that the draft is not a human label and does not enable measurement_validated.",
        "uncertainty_reviewer": "Check whether weakly supported cases are prioritized for human review.",
        "cross_condition_consistency_reviewer": "Check consistency across baseline and CPS conditions for the same case.",
    }[audit_role]
    return "\n".join(
        [
            f"Audit role: {audit_role}",
            role_focus,
            "",
            "This audit is not human labeling.",
            "This audit cannot create measurement_validated evidence.",
            "Do not change labels into final labels.",
            "Output JSON only.",
            "Recommend exactly one verdict: ACCEPT_DRAFT, REQUEST_HUMAN_PRIORITY, or REJECT_DRAFT.",
            "",
            "Prelabel draft:",
            _stable_json(prelabel),
        ]
    )


def _ordered_prelabels(prelabels: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [deepcopy(dict(row)) for row in prelabels],
        key=lambda row: (str(row.get("case_id", "")), str(row.get("condition", "")), str(row.get("model_alias", ""))),
    )


def build_subagent_audit_requests(
    prelabels: Sequence[Mapping[str, Any]],
    artifact_refs: Mapping[str, Any] | None,
    prelabel_run_id: str,
) -> list[dict[str, Any]]:
    refs = {str(key): str(value) for key, value in sorted(dict(artifact_refs or {}).items())}
    requests: list[dict[str, Any]] = []
    for prelabel in _ordered_prelabels(prelabels):
        for audit_role in AUDIT_ROLES:
            requests.append(
                {
                    "prelabel_run_id": str(prelabel_run_id),
                    "case_id": str(prelabel.get("case_id", "")),
                    "condition": str(prelabel.get("condition", "")),
                    "model_alias": str(prelabel.get("model_alias", "")),
                    "audit_role": audit_role,
                    "audit_prompt": _audit_role_prompt(audit_role, prelabel),
                    "prelabel_ref": f"llm_prelabels.jsonl#{prelabel.get('case_id', '')}:{prelabel.get('condition', '')}",
                    "artifact_refs": refs,
                    "not_human_review": True,
                    "measurement_validated_allowed": False,
                }
            )
    return requests


def _payload_from_output(output: Mapping[str, Any] | str) -> dict[str, Any]:
    if isinstance(output, str):
        try:
            payload = json.loads(output)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid subagent audit JSON") from exc
    else:
        payload = deepcopy(dict(output))
    if not isinstance(payload, dict):
        raise ValueError("subagent audit output must be a JSON object")
    return payload


def parse_subagent_audit_output(output: Mapping[str, Any] | str) -> dict[str, Any]:
    payload = _payload_from_output(output)
    if payload.get("audit_source") != AUDIT_SOURCE:
        raise ValueError("audit_source must be codex_subagent_audit")
    if str(payload.get("audit_role", "")) not in AUDIT_ROLES:
        raise ValueError("audit_role is not allowed")
    if bool(payload.get("not_human_review")) is not True:
        raise ValueError("not_human_review must be true")
    verdict = str(payload.get("verdict", ""))
    if verdict not in AUDIT_VERDICTS:
        raise ValueError("verdict is not allowed")
    claim_boundary = dict(payload.get("claim_boundary") or {})
    if bool(claim_boundary.get("counts_as_human_label")) is not False:
        raise ValueError("claim_boundary.counts_as_human_label must be false")
    if bool(claim_boundary.get("measurement_validated_allowed")) is not False:
        raise ValueError("claim_boundary.measurement_validated_allowed must be false")

    issues: list[dict[str, str]] = []
    for issue in payload.get("issues") or []:
        row = dict(issue)
        severity = str(row.get("severity", ""))
        action = str(row.get("recommended_human_action", ""))
        if severity not in ISSUE_SEVERITIES:
            raise ValueError("issue severity is not allowed")
        if action not in HUMAN_ACTIONS:
            raise ValueError("recommended_human_action is not allowed")
        issues.append(
            {
                "issue_type": str(row.get("issue_type", "")),
                "severity": severity,
                "dimension": str(row.get("dimension", "")),
                "description": str(row.get("description", "")),
                "recommended_human_action": action,
            }
        )
    return {
        "audit_role": str(payload["audit_role"]),
        "audit_source": AUDIT_SOURCE,
        "not_human_review": True,
        "case_id": str(payload.get("case_id") or ""),
        "condition": str(payload.get("condition") or ""),
        "verdict": verdict,
        "issues": sorted(issues, key=lambda row: (row["severity"], row["dimension"], row["issue_type"])),
        "claim_boundary": {
            "counts_as_human_label": False,
            "measurement_validated_allowed": False,
        },
        "counts_as_human_labels": False,
        "measurement_validated_allowed": False,
    }


def _issue_is_blocking(audit: Mapping[str, Any]) -> bool:
    return any(str(issue.get("severity")) == "blocking" for issue in audit.get("issues") or [])


def _human_priority_cases(prelabels: Sequence[Mapping[str, Any]], audits: Sequence[Mapping[str, Any]]) -> list[str]:
    priority = {
        str(prelabel.get("case_id", ""))
        for prelabel in prelabels
        if str(prelabel.get("human_review_priority", "")) == "high"
    }
    for audit in audits:
        if str(audit.get("verdict")) in {"REQUEST_HUMAN_PRIORITY", "REJECT_DRAFT"} or _issue_is_blocking(audit):
            priority.add(str(audit.get("case_id", "")))
    return sorted(case_id for case_id in priority if case_id)


def build_subagent_audit_report(
    prelabels: Sequence[Mapping[str, Any]],
    audit_requests: Sequence[Mapping[str, Any]],
    audit_results: Sequence[Mapping[str, Any]] | None = None,
    *,
    prelabel_run_id: str,
) -> dict[str, Any]:
    parsed_results = [parse_subagent_audit_output(result) for result in (audit_results or [])]
    verdict_counts = Counter(result["verdict"] for result in parsed_results)
    for verdict in AUDIT_VERDICTS:
        verdict_counts.setdefault(verdict, 0)
    blocking_count = sum(1 for result in parsed_results if _issue_is_blocking(result))
    rejected_count = int(verdict_counts["REJECT_DRAFT"])
    priority_cases = _human_priority_cases(prelabels, parsed_results)
    human_priority_count = len(priority_cases)
    if not parsed_results:
        human_priority_count = len(prelabels)
    return {
        "prelabel_audit_schema_version": PRELABEL_AUDIT_SCHEMA_VERSION,
        "source_phase": SOURCE_PHASE,
        "prelabel_run_id": str(prelabel_run_id),
        "total_prelabels": len(prelabels),
        "total_audit_requests": len(audit_requests),
        "audit_roles": list(AUDIT_ROLES),
        "audit_results_present": bool(parsed_results),
        "verdict_counts": {verdict: int(verdict_counts[verdict]) for verdict in AUDIT_VERDICTS},
        "blocking_issue_count": blocking_count,
        "human_priority_count": human_priority_count,
        "rejected_draft_count": rejected_count,
        "accepted_draft_count": int(verdict_counts["ACCEPT_DRAFT"]),
        "cases_requiring_human_priority": priority_cases
        or sorted(str(prelabel.get("case_id", "")) for prelabel in prelabels if prelabel.get("case_id")),
        "denied_claims": list(DENIED_CLAIMS),
        "reason_codes": _ordered_reason_codes(),
        "counts_as_human_labels": False,
        "measurement_validated_allowed": False,
        "codex_subagent_audit_is_not_human_review": True,
    }


def _audit_by_case_condition(audit_results: Sequence[Mapping[str, Any]] | None) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for result in audit_results or []:
        parsed = parse_subagent_audit_output(result)
        grouped.setdefault((parsed["case_id"], parsed["condition"]), []).append(parsed)
    return grouped


def build_human_review_queue(
    prelabels: Sequence[Mapping[str, Any]],
    audit_results: Sequence[Mapping[str, Any]] | None = None,
    *,
    run_id: str,
) -> list[dict[str, Any]]:
    grouped_audits = _audit_by_case_condition(audit_results)
    rows: list[dict[str, Any]] = []
    for prelabel in _ordered_prelabels(prelabels):
        key = (str(prelabel.get("case_id", "")), str(prelabel.get("condition", "")))
        audits = grouped_audits.get(key, [])
        verdicts = sorted({str(audit["verdict"]) for audit in audits})
        issues = []
        for audit in audits:
            issues.extend(audit.get("issues") or [])
        needs_adjudication = any(str(issue.get("severity")) == "blocking" for issue in issues) or (
            "REQUEST_HUMAN_PRIORITY" in verdicts or "REJECT_DRAFT" in verdicts
        )
        subagent_verdict = "|".join(verdicts) if verdicts else "PENDING_SUBAGENT_AUDIT"
        for dimension in LABEL_DIMENSIONS:
            label = dict((prelabel.get("dimension_labels") or {})[dimension])
            rows.append(
                {
                    "run_id": str(run_id),
                    "case_id": str(prelabel.get("case_id", "")),
                    "condition": str(prelabel.get("condition", "")),
                    "model_alias": str(prelabel.get("model_alias", "")),
                    "label_dimension": dimension,
                    "llm_suggested_label": str(label.get("suggested_label", "")),
                    "llm_confidence_milli": str(label.get("confidence_milli", "")),
                    "llm_rationale": str(label.get("rationale", "")),
                    "llm_evidence_refs": ";".join(str(ref) for ref in label.get("evidence_refs", [])),
                    "subagent_verdict": subagent_verdict,
                    "subagent_issues": json.dumps(issues, ensure_ascii=False, sort_keys=True),
                    "review_priority": str(prelabel.get("human_review_priority", "medium")),
                    "human_label": "",
                    "human_rationale": "",
                    "human_annotator_id": "",
                    "human_decision": "",
                    "needs_adjudication": str(bool(needs_adjudication)).lower(),
                }
            )
    return rows


def format_subagent_audit_report_markdown(report: Mapping[str, Any]) -> str:
    payload = deepcopy(dict(report))
    lines = [
        "# Prelabel Subagent Audit Report",
        "",
        f"- Prelabel run id: `{payload.get('prelabel_run_id', '')}`",
        f"- Total prelabels: {payload.get('total_prelabels', 0)}",
        f"- Total audit requests: {payload.get('total_audit_requests', 0)}",
        f"- Audit results present: {str(bool(payload.get('audit_results_present', False))).lower()}",
        f"- measurement_validated_allowed: {str(bool(payload.get('measurement_validated_allowed', False))).lower()}",
        "",
        "## Verdict Counts",
        "",
        "| verdict | count |",
        "| --- | --- |",
    ]
    counts = dict(payload.get("verdict_counts") or {})
    for verdict in AUDIT_VERDICTS:
        lines.append(f"| `{verdict}` | {int(counts.get(verdict, 0))} |")
    lines.extend(["", "## Reason Codes", ""])
    lines.extend(f"- `{reason}`" for reason in payload.get("reason_codes", []))
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- Codex subagent audit is not human review.",
            "- Audit outputs cannot create measurement_validated evidence.",
            "- Human annotation and human-human kappa remain required.",
            "- P04 remains deferred/operator-required.",
            "- P09 remains BLOCKED_OPERATOR_REQUIRED.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_human_review_queue_csv(rows: Sequence[Mapping[str, Any]]) -> str:
    fieldnames = [
        "run_id",
        "case_id",
        "condition",
        "model_alias",
        "label_dimension",
        "llm_suggested_label",
        "llm_confidence_milli",
        "llm_rationale",
        "llm_evidence_refs",
        "subagent_verdict",
        "subagent_issues",
        "review_priority",
        "human_label",
        "human_rationale",
        "human_annotator_id",
        "human_decision",
        "needs_adjudication",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: str(row.get(field, "")) for field in fieldnames})
    return output.getvalue()


def write_prelabel_subagent_audit_outputs(
    output_root: str | Path,
    audit_requests: Sequence[Mapping[str, Any]],
    audit_report: Mapping[str, Any],
    human_review_queue: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    resolved_output_root = Path(output_root)
    resolved_output_root.mkdir(parents=True, exist_ok=True)
    outputs = {
        "subagent_audit_requests_jsonl": _stable_write_jsonl(
            resolved_output_root / "subagent_audit_requests.jsonl",
            audit_requests,
        ),
        "subagent_audit_report_json": _stable_write_json(
            resolved_output_root / "subagent_audit_report.json",
            audit_report,
        ),
        "human_review_queue_jsonl": _stable_write_jsonl(
            resolved_output_root / "human_review_queue.jsonl",
            human_review_queue,
        ),
    }
    report_markdown = resolved_output_root / "subagent_audit_report.md"
    report_markdown.write_text(format_subagent_audit_report_markdown(audit_report), encoding="utf-8")
    outputs["subagent_audit_report_markdown"] = report_markdown
    queue_csv = resolved_output_root / "human_review_queue.csv"
    queue_csv.write_text(_format_human_review_queue_csv(human_review_queue), encoding="utf-8")
    outputs["human_review_queue_csv"] = queue_csv
    return {key: str(path.resolve()) for key, path in outputs.items()}
