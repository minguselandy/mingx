from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.human_label_kappa import LABEL_DIMENSIONS


MODEL_ADJUDICATION_SCHEMA_VERSION = "ModelAdjudicatedLabelsV1"
SOURCE_PHASE = "P34"
ADJUDICATOR_SOURCE = "codex_model_adjudicator"
ALLOWED_CLAIM_LEVEL = "model_adjudicated_pilot_only"
DENIED_CLAIMS = (
    "human_labeled_validation",
    "measurement_validated",
    "scientific_validation_completed",
    "deployed_v_information_certified",
)
REASON_CODE_ORDER = (
    "codex_adjudication_not_human_review",
    "model_adjudicated_labels_not_human_labels",
    "human_labels_missing",
    "human_kappa_missing",
    "measurement_validated_denied",
    "claim_gate_required",
    "contamination_audit_required",
    "fresh_metric_bridge_required",
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


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _ordered_reason_codes() -> list[str]:
    return list(REASON_CODE_ORDER)


def _ordered_prelabels(prelabels: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [deepcopy(dict(row)) for row in prelabels],
        key=lambda row: (str(row.get("case_id", "")), str(row.get("condition", "")), str(row.get("model_alias", ""))),
    )


def _ordered_queue_rows(rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    return sorted(
        [deepcopy(dict(row)) for row in (rows or [])],
        key=lambda row: (
            str(row.get("case_id", "")),
            str(row.get("condition", "")),
            str(row.get("model_alias", "")),
            str(row.get("label_dimension", "")),
        ),
    )


def _queue_by_key(rows: Sequence[Mapping[str, Any]] | None) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    return {
        (
            str(row.get("case_id", "")),
            str(row.get("condition", "")),
            str(row.get("model_alias", "")),
            str(row.get("label_dimension", "")),
        ): deepcopy(dict(row))
        for row in _ordered_queue_rows(rows)
    }


def _parse_issues(value: Any) -> list[dict[str, str]]:
    if isinstance(value, str):
        if not value.strip():
            return []
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [{"severity": "high", "description": value, "dimension": "", "issue_type": "unparsed_issue"}]
    else:
        parsed = value or []
    issues = []
    for issue in parsed:
        row = dict(issue)
        issues.append(
            {
                "audit_role": str(row.get("audit_role", "")),
                "verdict": str(row.get("verdict", "")),
                "issue_type": str(row.get("issue_type", "")),
                "severity": str(row.get("severity", "")),
                "dimension": str(row.get("dimension", "")),
                "description": str(row.get("description", "")),
                "recommended_human_action": str(row.get("recommended_human_action", "")),
            }
        )
    return sorted(issues, key=lambda row: (row["severity"], row["dimension"], row["issue_type"], row["description"]))


def _verdicts_from_queue(row: Mapping[str, Any] | None) -> list[str]:
    if not row:
        return []
    raw = str(row.get("subagent_verdict", ""))
    if not raw or raw == "PENDING_SUBAGENT_AUDIT":
        return []
    return sorted({part for part in raw.split("|") if part})


def _status(*, verdicts: Sequence[str], confidence_milli: int, issues: Sequence[Mapping[str, Any]]) -> tuple[str, str]:
    if "REJECT_DRAFT" in verdicts:
        return "model_adjudicated_uncertain", "rejected_draft_model_adjudicated"
    if any(str(issue.get("severity")) == "blocking" for issue in issues):
        return "model_adjudicated_with_blocking_warning", "blocking_warning"
    if "REQUEST_HUMAN_PRIORITY" in verdicts:
        return "model_adjudicated_uncertain", "high_uncertainty"
    if confidence_milli < 500:
        return "model_adjudicated_uncertain", "high_uncertainty"
    if issues:
        return "model_adjudicated_uncertain", "audit_issue_model_adjudicated"
    return "model_adjudicated_label", "accepted_model_adjudicated"


def _source_prelabel_ref(prelabel: Mapping[str, Any], dimension: str) -> str:
    return f"llm_prelabels.jsonl#{prelabel.get('case_id', '')}:{prelabel.get('condition', '')}:{dimension}"


def _source_audit_ref(prelabel: Mapping[str, Any], dimension: str) -> str:
    return f"human_review_queue.jsonl#{prelabel.get('case_id', '')}:{prelabel.get('condition', '')}:{dimension}"


def _build_records(prelabels: Iterable[Mapping[str, Any]], queue_rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    queue = _queue_by_key(queue_rows)
    records: list[dict[str, Any]] = []
    for prelabel in _ordered_prelabels(prelabels):
        for dimension in LABEL_DIMENSIONS:
            label_payload = dict((prelabel.get("dimension_labels") or {})[dimension])
            queue_row = queue.get(
                (
                    str(prelabel.get("case_id", "")),
                    str(prelabel.get("condition", "")),
                    str(prelabel.get("model_alias", "")),
                    dimension,
                ),
                {},
            )
            confidence = int(queue_row.get("llm_confidence_milli") or label_payload.get("confidence_milli", 0) or 0)
            verdicts = _verdicts_from_queue(queue_row)
            issues = _parse_issues(queue_row.get("subagent_issues", []))
            label_status, review_status = _status(verdicts=verdicts, confidence_milli=confidence, issues=issues)
            evidence_refs = label_payload.get("evidence_refs", [])
            if queue_row.get("llm_evidence_refs"):
                evidence_refs = [ref for ref in str(queue_row["llm_evidence_refs"]).split(";") if ref]
            records.append(
                {
                    "run_id": "",
                    "case_id": str(prelabel.get("case_id", "")),
                    "condition": str(prelabel.get("condition", "")),
                    "model_alias": str(prelabel.get("model_alias", "")),
                    "label_dimension": dimension,
                    "label": int(label_payload.get("suggested_label", queue_row.get("llm_suggested_label", 0))),
                    "rationale": (
                        f"Codex model adjudication over V4 Flash draft. "
                        f"Draft rationale: {label_payload.get('rationale', '')} "
                        f"Uncertainty: {label_payload.get('uncertainty_notes', '')}"
                    ).strip(),
                    "evidence_refs": [str(ref) for ref in evidence_refs],
                    "adjudicator_source": ADJUDICATOR_SOURCE,
                    "source_prelabel_ref": _source_prelabel_ref(prelabel, dimension),
                    "source_audit_ref": _source_audit_ref(prelabel, dimension),
                    "not_human_label": True,
                    "counts_as_human_label": False,
                    "counts_for_human_kappa": False,
                    "requires_human_confirmation": False,
                    "measurement_validated_allowed": False,
                    "allowed_claim_level": ALLOWED_CLAIM_LEVEL,
                    "confidence_milli": confidence,
                    "subagent_verdicts": verdicts,
                    "subagent_issues": issues,
                    "uncertainty_notes": str(label_payload.get("uncertainty_notes", "")),
                    "label_status": label_status,
                    "review_status": review_status,
                }
            )
    return sorted(
        records,
        key=lambda row: (row["case_id"], row["condition"], row["model_alias"], row["label_dimension"]),
    )


def _with_run_id(records: Sequence[Mapping[str, Any]], run_id: str) -> list[dict[str, Any]]:
    resolved = []
    for row in records:
        payload = deepcopy(dict(row))
        payload["run_id"] = run_id
        resolved.append(payload)
    return resolved


def _report(*, run_id: str, records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(record.get("label_status", "")) for record in records)
    uncertain_count = sum(
        1
        for record in records
        if str(record.get("review_status", "")) in {"high_uncertainty", "audit_issue_model_adjudicated"}
    )
    rejected_or_blocking = sum(
        1
        for record in records
        if str(record.get("review_status", "")) == "rejected_draft_model_adjudicated"
        or str(record.get("label_status", "")) == "model_adjudicated_with_blocking_warning"
    )
    return {
        "model_adjudicated_label_schema_version": MODEL_ADJUDICATION_SCHEMA_VERSION,
        "source_phase": SOURCE_PHASE,
        "run_id": run_id,
        "total_labels": len(records),
        "total_cases": len({record["case_id"] for record in records}),
        "total_conditions": len({record["condition"] for record in records}),
        "dimensions": list(LABEL_DIMENSIONS),
        "accepted_model_adjudicated_count": int(status_counts.get("model_adjudicated_label", 0)),
        "uncertain_count": uncertain_count,
        "rejected_or_blocking_warning_count": rejected_or_blocking,
        "denied_claims": list(DENIED_CLAIMS),
        "reason_codes": _ordered_reason_codes(),
        "measurement_validated_allowed": False,
        "allowed_claim_level": ALLOWED_CLAIM_LEVEL,
        "counts_as_human_labels": False,
        "counts_for_human_kappa": False,
        "human_labels_present": False,
        "kappa_present": False,
    }


def _summary(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "model_adjudicated_label_schema_version": MODEL_ADJUDICATION_SCHEMA_VERSION,
        "source_phase": SOURCE_PHASE,
        "run_id": str(report.get("run_id", "")),
        "model_adjudicated_labels_present": bool(report.get("total_labels", 0)),
        "human_labels_present": False,
        "kappa_present": False,
        "measurement_validated_allowed": False,
        "allowed_claim_level": ALLOWED_CLAIM_LEVEL,
        "total_labels": int(report.get("total_labels", 0)),
        "total_cases": int(report.get("total_cases", 0)),
        "total_conditions": int(report.get("total_conditions", 0)),
        "denied_claims": list(DENIED_CLAIMS),
        "reason_codes": _ordered_reason_codes(),
        "required_next_evidence": [
            "real human labels",
            "human-human kappa",
            "contamination audit",
            "fresh metric bridge",
            "claim gate decision",
        ],
    }


def format_codex_adjudication_report_markdown(report: Mapping[str, Any]) -> str:
    payload = deepcopy(dict(report))
    lines = [
        "# Codex Adjudication Report",
        "",
        f"- Run id: `{payload.get('run_id', '')}`",
        f"- Total labels: {payload.get('total_labels', 0)}",
        f"- Total cases: {payload.get('total_cases', 0)}",
        f"- Total conditions: {payload.get('total_conditions', 0)}",
        f"- Allowed claim level: `{payload.get('allowed_claim_level', ALLOWED_CLAIM_LEVEL)}`",
        f"- measurement_validated_allowed: {str(bool(payload.get('measurement_validated_allowed', False))).lower()}",
        "",
        "## Counts",
        "",
        f"- Accepted model-adjudicated: {payload.get('accepted_model_adjudicated_count', 0)}",
        f"- Uncertain: {payload.get('uncertain_count', 0)}",
        f"- Rejected or blocking warning: {payload.get('rejected_or_blocking_warning_count', 0)}",
        "",
        "## Reason Codes",
        "",
    ]
    lines.extend(f"- `{reason}`" for reason in payload.get("reason_codes", []))
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- These are model-adjudicated labels.",
            "- They are not human labels.",
            "- They cannot be used for human-human kappa.",
            "- They cannot satisfy human_labels_present for measurement_validated.",
            "- They support only model-adjudicated pilot evidence.",
            "- P04 remains deferred/operator-required.",
            "- P09 remains BLOCKED_OPERATOR_REQUIRED.",
            "",
        ]
    )
    return "\n".join(lines)


def format_model_adjudicated_label_summary_markdown(summary: Mapping[str, Any]) -> str:
    payload = deepcopy(dict(summary))
    lines = [
        "# Model-Adjudicated Label Summary",
        "",
        f"- Run id: `{payload.get('run_id', '')}`",
        f"- Model-adjudicated labels present: {str(bool(payload.get('model_adjudicated_labels_present', False))).lower()}",
        f"- Human labels present: {str(bool(payload.get('human_labels_present', False))).lower()}",
        f"- Kappa present: {str(bool(payload.get('kappa_present', False))).lower()}",
        f"- Allowed claim level: `{payload.get('allowed_claim_level', ALLOWED_CLAIM_LEVEL)}`",
        f"- measurement_validated_allowed: {str(bool(payload.get('measurement_validated_allowed', False))).lower()}",
        "",
        "## Required Next Evidence",
        "",
    ]
    lines.extend(f"- {item}" for item in payload.get("required_next_evidence", []))
    lines.extend(["", "## Denied Claims", ""])
    lines.extend(f"- `{claim}`" for claim in payload.get("denied_claims", []))
    lines.append("")
    return "\n".join(lines)


def _write_outputs(output_root: str | Path, *, records: Sequence[Mapping[str, Any]], report: Mapping[str, Any], summary: Mapping[str, Any]) -> dict[str, str]:
    resolved = Path(output_root)
    resolved.mkdir(parents=True, exist_ok=True)
    outputs = {
        "model_adjudicated_labels_jsonl": _stable_write_jsonl(resolved / "model_adjudicated_labels.jsonl", records),
        "codex_adjudication_report_json": _stable_write_json(resolved / "codex_adjudication_report.json", report),
        "model_adjudicated_label_summary_json": _stable_write_json(
            resolved / "model_adjudicated_label_summary.json",
            summary,
        ),
    }
    report_md = resolved / "codex_adjudication_report.md"
    report_md.write_text(format_codex_adjudication_report_markdown(report), encoding="utf-8")
    outputs["codex_adjudication_report_markdown"] = report_md
    summary_md = resolved / "model_adjudicated_label_summary.md"
    summary_md.write_text(format_model_adjudicated_label_summary_markdown(summary), encoding="utf-8")
    outputs["model_adjudicated_label_summary_markdown"] = summary_md
    return {key: str(path.resolve()) for key, path in outputs.items()}


def build_model_adjudicated_labels(
    prelabels: Iterable[Mapping[str, Any]],
    *,
    subagent_audit_report: Mapping[str, Any] | None = None,
    human_review_queue: Sequence[Mapping[str, Any]] | None = None,
    run_id: str,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    _ = subagent_audit_report or {}
    records = _with_run_id(_build_records(prelabels, human_review_queue), run_id)
    report = _report(run_id=run_id, records=records)
    summary = _summary(report)
    result: dict[str, Any] = {
        "model_adjudicated_labels": records,
        "report": report,
        "summary": summary,
        "empirical_summary": {
            "model_adjudicated_labels_present": bool(records),
            "human_labels_present": False,
            "kappa_present": False,
            "measurement_validated_allowed": False,
            "allowed_claim_level": ALLOWED_CLAIM_LEVEL,
        },
        "measurement_validated_allowed": False,
    }
    if output_root is not None:
        result["generated_outputs"] = _write_outputs(output_root, records=records, report=report, summary=summary)
    return result


def build_model_adjudicated_labels_from_paths(
    *,
    prelabels_path: str | Path,
    subagent_audit_report_path: str | Path | None = None,
    human_review_queue_path: str | Path | None = None,
    run_id: str,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    prelabels = _read_jsonl(Path(prelabels_path))
    audit_report = _read_json(Path(subagent_audit_report_path)) if subagent_audit_report_path is not None else None
    queue = _read_jsonl(Path(human_review_queue_path)) if human_review_queue_path is not None else None
    return build_model_adjudicated_labels(
        prelabels,
        subagent_audit_report=audit_report,
        human_review_queue=queue,
        run_id=run_id,
        output_root=output_root,
    )
