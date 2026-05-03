from __future__ import annotations

import csv
import io
import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from cps.experiments.human_label_kappa import LABEL_DIMENSIONS
from cps.experiments.prelabel_subagent_audit import parse_subagent_audit_output


HUMAN_REVIEW_PACKET_SCHEMA_VERSION = "HumanReviewPacketV1"
SOURCE_PHASE = "P33"
ALLOWED_HUMAN_LABELS = {"0", "1", "2"}
ALLOWED_HUMAN_DECISIONS = ("accept", "modify", "reject", "unclear")
DENIED_CLAIMS = (
    "measurement_validated",
    "scientific_validation",
    "human_labeled_validation_complete",
    "kappa_validated",
)
REASON_CODE_ORDER = (
    "human_review_required",
    "prelabels_not_human_labels",
    "subagent_audit_not_human_review",
    "kappa_required",
    "measurement_validated_denied",
    "missing_human_label",
    "missing_human_rationale",
    "missing_human_annotator_id",
    "missing_human_decision",
    "invalid_human_label",
    "invalid_human_decision",
    "missing_required_dimension",
    "duplicate_human_label_entry",
    "prelabel_rows_not_human_labels",
    "codex_audit_not_human_annotator",
)
HUMAN_REVIEW_FIELDS = (
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
)
FORBIDDEN_ANNOTATOR_PARTS = ("codex", "subagent", "deepseek", "llm", "prelabel")


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


def _ordered_reason_codes(reasons: set[str]) -> list[str]:
    order = {reason: index for index, reason in enumerate(REASON_CODE_ORDER)}
    return sorted(reasons, key=lambda reason: (order.get(reason, len(order)), reason))


def _ordered_prelabels(prelabels: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [deepcopy(dict(row)) for row in prelabels],
        key=lambda row: (str(row.get("case_id", "")), str(row.get("condition", "")), str(row.get("model_alias", ""))),
    )


def _audit_results_from_report(audit_report: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not audit_report:
        return []
    raw_results = audit_report.get("audit_results") or audit_report.get("subagent_audit_results") or []
    parsed: list[dict[str, Any]] = []
    for result in raw_results:
        parsed.append(parse_subagent_audit_output(result))
    return sorted(parsed, key=lambda row: (row["case_id"], row["condition"], row["audit_role"], row["verdict"]))


def _audit_group(audit_results: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for result in audit_results:
        grouped.setdefault((str(result.get("case_id", "")), str(result.get("condition", ""))), []).append(
            deepcopy(dict(result))
        )
    return grouped


def _dimension_audit_issues(audits: Sequence[Mapping[str, Any]], dimension: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for audit in audits:
        for issue in audit.get("issues") or []:
            row = dict(issue)
            issue_dimension = str(row.get("dimension", ""))
            if issue_dimension in {"", dimension}:
                issues.append(
                    {
                        "audit_role": str(audit.get("audit_role", "")),
                        "verdict": str(audit.get("verdict", "")),
                        "issue_type": str(row.get("issue_type", "")),
                        "severity": str(row.get("severity", "")),
                        "dimension": issue_dimension,
                        "description": str(row.get("description", "")),
                        "recommended_human_action": str(row.get("recommended_human_action", "")),
                    }
                )
    return sorted(issues, key=lambda row: (row["severity"], row["audit_role"], row["issue_type"], row["description"]))


def _review_priority(*, confidence_milli: int, verdicts: Sequence[str], issues: Sequence[Mapping[str, Any]]) -> str:
    if "REJECT_DRAFT" in verdicts:
        return "high"
    if any(str(issue.get("severity")) in {"blocking", "high"} for issue in issues):
        return "high"
    if confidence_milli < 500:
        return "high"
    if "REQUEST_HUMAN_PRIORITY" in verdicts:
        return "medium"
    if confidence_milli < 750:
        return "medium"
    return "low"


def _format_csv(rows: Sequence[Mapping[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(HUMAN_REVIEW_FIELDS), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: str(row.get(field, "")) for field in HUMAN_REVIEW_FIELDS})
    return output.getvalue()


def _human_review_instructions(run_id: str) -> str:
    return "\n".join(
        [
            "# Human Review Instructions",
            "",
            f"Run id: `{run_id}`",
            "",
            "LLM suggestions are optional aids. Codex subagent audit is also an optional aid.",
            "Human annotators must independently confirm, modify, reject, or mark labels unclear.",
            "",
            "Do not treat prelabels as human labels.",
            "Do not treat Codex subagent audit as human review.",
            "Do not copy labels without checking the provided evidence.",
            "",
            "Allowed human labels:",
            "",
            "- `0` = fail",
            "- `1` = partial",
            "- `2` = pass",
            "",
            "Allowed human decisions:",
            "",
            "- `accept`",
            "- `modify`",
            "- `reject`",
            "- `unclear`",
            "",
            "Leave no completed human row without `human_annotator_id`, `human_label`, `human_rationale`, and `human_decision`.",
            "Kappa requires at least two human annotators in a later phase.",
            "`measurement_validated` remains denied until human labels, kappa, contamination audit, metric bridge freshness, and claim gate allow all pass.",
            "",
        ]
    )


def _packet_summary(*, run_id: str, rows: Sequence[Mapping[str, Any]], audit_results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    reasons = {
        "human_review_required",
        "prelabels_not_human_labels",
        "subagent_audit_not_human_review",
        "kappa_required",
        "measurement_validated_denied",
    }
    priority_counts = Counter(str(row.get("review_priority", "")) for row in rows)
    return {
        "human_review_packet_schema_version": HUMAN_REVIEW_PACKET_SCHEMA_VERSION,
        "source_phase": SOURCE_PHASE,
        "run_id": run_id,
        "row_count": len(rows),
        "case_count": len({str(row.get("case_id", "")) for row in rows if row.get("case_id")}),
        "dimension_count": len({str(row.get("label_dimension", "")) for row in rows if row.get("label_dimension")}),
        "review_priority_counts": {key: int(priority_counts.get(key, 0)) for key in ("high", "medium", "low")},
        "audit_results_present": bool(audit_results),
        "packet_is_human_labeling_completion": False,
        "prelabels_are_human_labels": False,
        "subagent_audit_is_human_review": False,
        "kappa_required": True,
        "measurement_validated_allowed": False,
        "denied_claims": list(DENIED_CLAIMS),
        "reason_codes": _ordered_reason_codes(reasons),
    }


def format_human_review_packet_summary_markdown(summary: Mapping[str, Any]) -> str:
    payload = deepcopy(dict(summary))
    lines = [
        "# Human Review Packet Summary",
        "",
        f"- Run id: `{payload.get('run_id', '')}`",
        f"- Row count: {payload.get('row_count', 0)}",
        f"- Case count: {payload.get('case_count', 0)}",
        f"- Dimension count: {payload.get('dimension_count', 0)}",
        f"- Packet is human labeling completion: {str(bool(payload.get('packet_is_human_labeling_completion', False))).lower()}",
        f"- Prelabels are human labels: {str(bool(payload.get('prelabels_are_human_labels', False))).lower()}",
        f"- Subagent audit is human review: {str(bool(payload.get('subagent_audit_is_human_review', False))).lower()}",
        f"- measurement_validated_allowed: {str(bool(payload.get('measurement_validated_allowed', False))).lower()}",
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
            "- This packet is not human labeling completion.",
            "- LLM prelabels are not human labels.",
            "- Codex subagent audit is not human review.",
            "- Human review completion is required before kappa.",
            "- Kappa, contamination audit, metric bridge freshness, and claim gate allow remain required.",
            "- P04 remains deferred/operator-required.",
            "- P09 remains BLOCKED_OPERATOR_REQUIRED.",
            "",
        ]
    )
    return "\n".join(lines)


def _manifest(run_id: str, summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "human_review_packet_schema_version": HUMAN_REVIEW_PACKET_SCHEMA_VERSION,
        "source_phase": SOURCE_PHASE,
        "run_id": run_id,
        "generated_outputs": {
            "human_review_packet_manifest_json": "human_review_packet_manifest.json",
            "human_review_sheet_csv": "human_review_sheet.csv",
            "human_review_sheet_jsonl": "human_review_sheet.jsonl",
            "human_review_instructions_markdown": "human_review_instructions.md",
            "human_review_packet_summary_json": "human_review_packet_summary.json",
            "human_review_packet_summary_markdown": "human_review_packet_summary.md",
        },
        "packet_is_human_labeling_completion": False,
        "measurement_validated_allowed": False,
        "reason_codes": list(summary.get("reason_codes", [])),
        "denied_claims": list(DENIED_CLAIMS),
    }


def _write_packet_outputs(
    output_root: str | Path,
    *,
    manifest: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    instructions: str,
    summary: Mapping[str, Any],
) -> dict[str, str]:
    resolved = Path(output_root)
    resolved.mkdir(parents=True, exist_ok=True)
    outputs = {
        "human_review_packet_manifest_json": _stable_write_json(
            resolved / "human_review_packet_manifest.json",
            manifest,
        ),
        "human_review_sheet_jsonl": _stable_write_jsonl(resolved / "human_review_sheet.jsonl", rows),
        "human_review_packet_summary_json": _stable_write_json(
            resolved / "human_review_packet_summary.json",
            summary,
        ),
    }
    sheet_csv = resolved / "human_review_sheet.csv"
    sheet_csv.write_text(_format_csv(rows), encoding="utf-8")
    outputs["human_review_sheet_csv"] = sheet_csv
    instructions_path = resolved / "human_review_instructions.md"
    instructions_path.write_text(instructions, encoding="utf-8")
    outputs["human_review_instructions_markdown"] = instructions_path
    summary_markdown = resolved / "human_review_packet_summary.md"
    summary_markdown.write_text(format_human_review_packet_summary_markdown(summary), encoding="utf-8")
    outputs["human_review_packet_summary_markdown"] = summary_markdown
    return {key: str(path.resolve()) for key, path in outputs.items()}


def build_human_review_packet(
    prelabels: Iterable[Mapping[str, Any]],
    audit_report: Mapping[str, Any] | None = None,
    *,
    run_id: str,
    output_root: Path | None = None,
) -> dict[str, Any]:
    ordered_prelabels = _ordered_prelabels(prelabels)
    audit_results = _audit_results_from_report(audit_report)
    grouped_audits = _audit_group(audit_results)
    rows: list[dict[str, Any]] = []
    for prelabel in ordered_prelabels:
        key = (str(prelabel.get("case_id", "")), str(prelabel.get("condition", "")))
        audits = grouped_audits.get(key, [])
        verdicts = sorted({str(audit.get("verdict", "")) for audit in audits if audit.get("verdict")})
        case_issues = [
            dict(issue)
            for audit in audits
            for issue in (audit.get("issues") or [])
        ]
        for dimension in LABEL_DIMENSIONS:
            label_payload = dict((prelabel.get("dimension_labels") or {})[dimension])
            issues = _dimension_audit_issues(audits, dimension)
            confidence = int(label_payload.get("confidence_milli", 0) or 0)
            rows.append(
                {
                    "run_id": run_id,
                    "case_id": str(prelabel.get("case_id", "")),
                    "condition": str(prelabel.get("condition", "")),
                    "model_alias": str(prelabel.get("model_alias", "")),
                    "label_dimension": dimension,
                    "llm_suggested_label": str(label_payload.get("suggested_label", "")),
                    "llm_confidence_milli": str(confidence),
                    "llm_rationale": str(label_payload.get("rationale", "")),
                    "llm_evidence_refs": ";".join(str(ref) for ref in label_payload.get("evidence_refs", [])),
                    "subagent_verdict": "|".join(verdicts) if verdicts else "PENDING_SUBAGENT_AUDIT",
                    "subagent_issues": json.dumps(issues, ensure_ascii=False, sort_keys=True),
                    "review_priority": _review_priority(
                        confidence_milli=confidence,
                        verdicts=verdicts,
                        issues=issues + case_issues,
                    ),
                    "human_label": "",
                    "human_rationale": "",
                    "human_annotator_id": "",
                    "human_decision": "",
                    "needs_adjudication": str(
                        bool(
                            issues
                            and any(str(issue.get("severity")) in {"blocking", "high"} for issue in issues)
                            or "REJECT_DRAFT" in verdicts
                            or "REQUEST_HUMAN_PRIORITY" in verdicts
                        )
                    ).lower(),
                }
            )
    rows = sorted(
        rows,
        key=lambda row: (row["case_id"], row["condition"], row["model_alias"], row["label_dimension"]),
    )
    summary = _packet_summary(run_id=run_id, rows=rows, audit_results=audit_results)
    manifest = _manifest(run_id, summary)
    instructions = _human_review_instructions(run_id)
    result = {
        "manifest": manifest,
        "review_rows": rows,
        "instructions_markdown": instructions,
        "summary": summary,
        "measurement_validated_allowed": False,
    }
    if output_root is not None:
        result["generated_outputs"] = _write_packet_outputs(
            output_root,
            manifest=manifest,
            rows=rows,
            instructions=instructions,
            summary=summary,
        )
    return result


def _normalized_submission_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        payload = {field: str(dict(row).get(field, "")) for field in HUMAN_REVIEW_FIELDS}
        payload["label_source"] = str(dict(row).get("label_source", ""))
        normalized.append(payload)
    return sorted(
        normalized,
        key=lambda row: (
            row["case_id"],
            row["condition"],
            row["human_annotator_id"],
            row["label_dimension"],
            row["human_label"],
        ),
    )


def _is_forbidden_annotator(annotator_id: str) -> bool:
    lowered = annotator_id.lower()
    return any(part in lowered for part in FORBIDDEN_ANNOTATOR_PARTS)


def validate_human_review_submission(
    rows: Sequence[Mapping[str, Any]],
    *,
    required_dimensions: Sequence[str] = LABEL_DIMENSIONS,
) -> dict[str, Any]:
    normalized = _normalized_submission_rows(rows)
    reasons: set[str] = set()
    missing_fields: list[dict[str, str]] = []
    invalid_rows: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, str]] = []
    key_counts: Counter[tuple[str, str, str, str]] = Counter()
    for index, row in enumerate(normalized):
        key = (row["case_id"], row["condition"], row["human_annotator_id"], row["label_dimension"])
        key_counts[key] += 1
        for field, reason in (
            ("human_label", "missing_human_label"),
            ("human_rationale", "missing_human_rationale"),
            ("human_annotator_id", "missing_human_annotator_id"),
            ("human_decision", "missing_human_decision"),
        ):
            if not row[field]:
                reasons.add(reason)
                missing_fields.append({"row_index": str(index), "field": field})
        if row["human_label"] and row["human_label"] not in ALLOWED_HUMAN_LABELS:
            reasons.add("invalid_human_label")
            invalid_rows.append({"row_index": str(index), "field": "human_label", "value": row["human_label"]})
        if row["human_decision"] and row["human_decision"] not in ALLOWED_HUMAN_DECISIONS:
            reasons.add("invalid_human_decision")
            invalid_rows.append({"row_index": str(index), "field": "human_decision", "value": row["human_decision"]})
        if row.get("label_source") == "llm_assisted_prelabel":
            reasons.add("prelabel_rows_not_human_labels")
            invalid_rows.append({"row_index": str(index), "field": "label_source", "value": row["label_source"]})
        if row["human_annotator_id"] and _is_forbidden_annotator(row["human_annotator_id"]):
            reasons.add("codex_audit_not_human_annotator")
            invalid_rows.append(
                {"row_index": str(index), "field": "human_annotator_id", "value": row["human_annotator_id"]}
            )
    for key, count in sorted(key_counts.items()):
        if count > 1:
            reasons.add("duplicate_human_label_entry")
            duplicate_rows.append(
                {
                    "case_id": key[0],
                    "condition": key[1],
                    "human_annotator_id": key[2],
                    "label_dimension": key[3],
                    "count": str(count),
                }
            )

    dimensions_by_case_condition_annotator: dict[tuple[str, str, str], set[str]] = {}
    for row in normalized:
        if row["human_annotator_id"]:
            dimensions_by_case_condition_annotator.setdefault(
                (row["case_id"], row["condition"], row["human_annotator_id"]),
                set(),
            ).add(row["label_dimension"])
    for key, observed_dimensions in sorted(dimensions_by_case_condition_annotator.items()):
        missing = [dimension for dimension in required_dimensions if dimension not in observed_dimensions]
        if missing:
            reasons.add("missing_required_dimension")
            for dimension in missing:
                missing_fields.append(
                    {
                        "case_id": key[0],
                        "condition": key[1],
                        "human_annotator_id": key[2],
                        "field": f"label_dimension:{dimension}",
                    }
                )
    if not normalized:
        reasons.add("missing_human_label")

    valid = not reasons
    annotator_ids = sorted({row["human_annotator_id"] for row in normalized if row["human_annotator_id"]})
    return {
        "human_submission_valid": valid,
        "human_labels_present": valid,
        "annotator_ids": annotator_ids,
        "case_count": len({row["case_id"] for row in normalized if row["case_id"]}),
        "dimension_count": len({row["label_dimension"] for row in normalized if row["label_dimension"]}),
        "missing_fields": sorted(missing_fields, key=lambda row: _stable_json(row)),
        "invalid_rows": sorted(invalid_rows, key=lambda row: _stable_json(row)),
        "duplicate_rows": duplicate_rows,
        "reason_codes": _ordered_reason_codes(reasons),
        "measurement_validated_allowed": False,
    }


def convert_human_review_submission_to_human_labels(
    rows: Sequence[Mapping[str, Any]],
    *,
    validation_report: Mapping[str, Any] | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    report = deepcopy(dict(validation_report or validate_human_review_submission(rows)))
    if bool(report.get("human_submission_valid")) is not True:
        raise ValueError("human review submission is not valid")
    normalized = _normalized_submission_rows(rows)
    records = [
        {
            "run_id": row["run_id"],
            "case_id": row["case_id"],
            "condition": row["condition"],
            "annotator_id": row["human_annotator_id"],
            "label_dimension": row["label_dimension"],
            "label": int(row["human_label"]),
            "rationale": row["human_rationale"],
            "human_decision": row["human_decision"],
            "label_source": "human_annotator",
        }
        for row in normalized
    ]
    result: dict[str, Any] = {
        "human_label_records": records,
        "human_labels_present": bool(records),
        "measurement_validated_allowed": False,
        "reason_codes": ["kappa_required", "measurement_validated_denied"],
    }
    if output_path is not None:
        path = Path(output_path)
        if path.name == "human_labels.jsonl":
            raise ValueError("P33 writes candidate labels only; do not write human_labels.jsonl automatically")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_stable_jsonl(records), encoding="utf-8")
        result["generated_outputs"] = {"human_labels_candidate_jsonl": str(path.resolve())}
    return result
