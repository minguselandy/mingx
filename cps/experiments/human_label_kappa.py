from __future__ import annotations

import csv
import io
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from itertools import combinations
from pathlib import Path
from typing import Any


LABEL_SCHEMA_VERSION = "HumanLabelKappaV1"
LABEL_DIMENSIONS = (
    "answer_correctness",
    "answer_completeness",
    "answer_groundedness",
    "context_sufficiency",
    "missing_critical_context",
    "irrelevant_context",
    "misleading_context",
    "conflict_or_stale_context",
)
ALLOWED_LABELS = {
    "0": "fail",
    "1": "partial",
    "2": "pass",
}
REASON_CODE_ORDER = (
    "missing_human_labels",
    "missing_kappa",
    "low_kappa",
    "incomplete_label_coverage",
    "invalid_label_value",
    "duplicate_label_entry",
    "two_annotators_required",
    "kappa_alone_not_validation",
    "contamination_audit_required",
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


def _as_label(value: Any) -> int | None:
    if value in {0, 1, 2}:
        return int(value)
    if isinstance(value, str) and value.strip() in {"0", "1", "2"}:
        return int(value.strip())
    return None


def build_label_schema() -> dict[str, Any]:
    return {
        "label_schema_version": LABEL_SCHEMA_VERSION,
        "label_dimensions": list(LABEL_DIMENSIONS),
        "allowed_labels": dict(ALLOWED_LABELS),
        "required_fields": [
            "run_id",
            "case_id",
            "condition",
            "annotator_id",
            "label_dimension",
            "label",
            "rationale",
        ],
        "minimum_annotators_for_kappa": 2,
        "measurement_validated_allowed": False,
        "claim_boundary": (
            "Human labels and kappa are required but not sufficient for measurement validation; "
            "contamination pass, fresh metric bridge, complete artifacts, controlled live run, and claim gate allow "
            "remain required."
        ),
    }


def _ordered_values(values: Sequence[str] | None, *, default: Sequence[str] = ()) -> list[str]:
    return sorted(str(value) for value in (values or default))


def format_human_labels_template_csv(
    cases: Sequence[str],
    *,
    conditions: Sequence[str],
    annotator_ids: Sequence[str],
) -> str:
    output = io.StringIO()
    fieldnames = ["run_id", "case_id", "condition", "annotator_id", "label_dimension", "label", "rationale"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for case_id in _ordered_values(cases):
        for condition in _ordered_values(conditions):
            for annotator_id in _ordered_values(annotator_ids):
                for dimension in LABEL_DIMENSIONS:
                    writer.writerow(
                        {
                            "run_id": "",
                            "case_id": case_id,
                            "condition": condition,
                            "annotator_id": annotator_id,
                            "label_dimension": dimension,
                            "label": "",
                            "rationale": "",
                        }
                    )
    return output.getvalue()


def format_human_labels_template_jsonl(
    cases: Sequence[str],
    *,
    conditions: Sequence[str],
    annotator_ids: Sequence[str],
) -> str:
    rows: list[dict[str, str]] = []
    for case_id in _ordered_values(cases):
        for condition in _ordered_values(conditions):
            for annotator_id in _ordered_values(annotator_ids):
                for dimension in LABEL_DIMENSIONS:
                    rows.append(
                        {
                            "run_id": "",
                            "case_id": case_id,
                            "condition": condition,
                            "annotator_id": annotator_id,
                            "label_dimension": dimension,
                            "label": "",
                            "rationale": "",
                        }
                    )
    return "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + ("\n" if rows else "")


def _normalize_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        payload = deepcopy(dict(row))
        payload["run_id"] = str(payload.get("run_id", ""))
        payload["case_id"] = str(payload.get("case_id", ""))
        payload["condition"] = str(payload.get("condition", ""))
        payload["annotator_id"] = str(payload.get("annotator_id", ""))
        payload["label_dimension"] = str(payload.get("label_dimension", ""))
        payload["rationale"] = str(payload.get("rationale", ""))
        label = _as_label(payload.get("label"))
        payload["label"] = payload.get("label") if label is None else label
        normalized.append(payload)
    return sorted(
        normalized,
        key=lambda row: (
            row["case_id"],
            row["condition"],
            row["annotator_id"],
            row["label_dimension"],
            str(row["label"]),
            row["rationale"],
        ),
    )


def check_label_completeness(
    label_rows: Sequence[Mapping[str, Any]],
    *,
    required_cases: Sequence[str],
    conditions: Sequence[str],
    required_annotator_count: int = 2,
    required_dimensions: Sequence[str] = LABEL_DIMENSIONS,
) -> dict[str, Any]:
    rows = _normalize_rows(label_rows)
    required_case_ids = _ordered_values(required_cases)
    required_conditions = _ordered_values(conditions)
    dimensions = list(required_dimensions)
    observed_cases = sorted({row["case_id"] for row in rows if row["case_id"]})
    observed_annotators = sorted({row["annotator_id"] for row in rows if row["annotator_id"]})
    observed_dimensions = sorted({row["label_dimension"] for row in rows if row["label_dimension"]})

    duplicate_keys: list[dict[str, str]] = []
    key_counts: Counter[tuple[str, str, str, str]] = Counter()
    value_errors: list[dict[str, Any]] = []
    for row in rows:
        key = (row["case_id"], row["condition"], row["annotator_id"], row["label_dimension"])
        key_counts[key] += 1
        if row["label_dimension"] not in dimensions or _as_label(row.get("label")) is None:
            value_errors.append(
                {
                    "case_id": row["case_id"],
                    "condition": row["condition"],
                    "annotator_id": row["annotator_id"],
                    "label_dimension": row["label_dimension"],
                    "label": row.get("label"),
                }
            )
    for key, count in sorted(key_counts.items()):
        if count > 1:
            duplicate_keys.append(
                {
                    "case_id": key[0],
                    "condition": key[1],
                    "annotator_id": key[2],
                    "label_dimension": key[3],
                    "count": str(count),
                }
            )

    missing_cases: set[str] = set()
    missing_dimensions: list[dict[str, str]] = []
    valid_keys = {
        (row["case_id"], row["condition"], row["annotator_id"], row["label_dimension"])
        for row in rows
        if _as_label(row.get("label")) is not None and row["label_dimension"] in dimensions
    }
    for case_id in required_case_ids:
        case_missing = False
        for condition in required_conditions:
            for annotator_id in observed_annotators[:required_annotator_count]:
                for dimension in dimensions:
                    if (case_id, condition, annotator_id, dimension) not in valid_keys:
                        case_missing = True
                        missing_dimensions.append(
                            {
                                "case_id": case_id,
                                "condition": condition,
                                "annotator_id": annotator_id,
                                "label_dimension": dimension,
                            }
                        )
        if case_missing or case_id not in observed_cases:
            missing_cases.add(case_id)

    missing_annotators = []
    if len(observed_annotators) < required_annotator_count:
        missing_annotators = [
            f"required_annotator_{index}"
            for index in range(len(observed_annotators) + 1, required_annotator_count + 1)
        ]
    missing_required_dimensions = [dimension for dimension in dimensions if dimension not in observed_dimensions]

    reasons: set[str] = set()
    if not rows or missing_cases or missing_dimensions or missing_required_dimensions:
        reasons.add("missing_human_labels")
        reasons.add("incomplete_label_coverage")
    if missing_annotators:
        reasons.add("two_annotators_required")
    if value_errors:
        reasons.add("invalid_label_value")
    if duplicate_keys:
        reasons.add("duplicate_label_entry")

    labels_complete = not reasons and len(observed_annotators) >= required_annotator_count
    return {
        "label_schema_version": LABEL_SCHEMA_VERSION,
        "required_case_count": len(required_case_ids),
        "observed_case_count": len(observed_cases),
        "required_annotator_count": int(required_annotator_count),
        "observed_annotator_count": len(observed_annotators),
        "required_dimensions": dimensions,
        "observed_dimensions": observed_dimensions,
        "missing_cases": sorted(missing_cases),
        "missing_annotators": missing_annotators,
        "missing_dimensions": missing_dimensions,
        "duplicate_label_entries": duplicate_keys,
        "label_value_errors": value_errors,
        "labels_complete": labels_complete,
        "reason_codes": _ordered_reason_codes(reasons),
    }


def cohen_kappa(labels_a: Sequence[int], labels_b: Sequence[int]) -> float | None:
    if len(labels_a) != len(labels_b) or not labels_a:
        return None
    values_a = [int(value) for value in labels_a]
    values_b = [int(value) for value in labels_b]
    item_count = len(values_a)
    observed = sum(1 for left, right in zip(values_a, values_b, strict=True) if left == right) / item_count
    counts_a = Counter(values_a)
    counts_b = Counter(values_b)
    expected = sum((counts_a[label] / item_count) * (counts_b[label] / item_count) for label in (0, 1, 2))
    denominator = 1 - expected
    if denominator == 0:
        return 1.0 if observed == 1 else 0.0
    return round((observed - expected) / denominator, 6)


def _dimension_pair_values(
    rows: Sequence[Mapping[str, Any]],
    *,
    dimension: str,
    annotator_a: str,
    annotator_b: str,
) -> tuple[list[int], list[int]]:
    by_key: dict[tuple[str, str, str], int] = {}
    for row in rows:
        if row["label_dimension"] != dimension:
            continue
        label = _as_label(row.get("label"))
        if label is None:
            continue
        by_key[(row["case_id"], row["condition"], row["annotator_id"])] = label
    keys_a = {(case_id, condition) for case_id, condition, annotator in by_key if annotator == annotator_a}
    keys_b = {(case_id, condition) for case_id, condition, annotator in by_key if annotator == annotator_b}
    shared = sorted(keys_a & keys_b)
    return (
        [by_key[(case_id, condition, annotator_a)] for case_id, condition in shared],
        [by_key[(case_id, condition, annotator_b)] for case_id, condition in shared],
    )


def _kappa_status(macro_average_kappa: float | None, labels_complete: bool) -> str:
    if macro_average_kappa is None or not labels_complete:
        return "kappa_missing"
    if macro_average_kappa < 0.40:
        return "pilot_only"
    if macro_average_kappa < 0.60:
        return "weak_evidence_not_measurement_validated"
    if macro_average_kappa < 0.75:
        return "limited_measurement_review_candidate"
    return "stronger_measurement_review_candidate"


def build_human_label_kappa_report(
    label_rows: Sequence[Mapping[str, Any]],
    *,
    run_id: str,
    required_cases: Sequence[str],
    conditions: Sequence[str],
    required_annotator_count: int = 2,
) -> dict[str, Any]:
    rows = _normalize_rows(label_rows)
    completeness = check_label_completeness(
        rows,
        required_cases=required_cases,
        conditions=conditions,
        required_annotator_count=required_annotator_count,
    )
    annotator_ids = sorted({row["annotator_id"] for row in rows if row["annotator_id"]})
    per_dimension: dict[str, float | None] = {}
    item_counts: dict[str, int] = {}
    pairwise_details: dict[str, dict[str, float | None]] = {}
    if len(annotator_ids) >= 2 and not completeness["duplicate_label_entries"] and not completeness["label_value_errors"]:
        for dimension in LABEL_DIMENSIONS:
            dimension_values: list[float] = []
            pairwise_details[dimension] = {}
            max_item_count = 0
            for annotator_a, annotator_b in combinations(annotator_ids, 2):
                labels_a, labels_b = _dimension_pair_values(
                    rows,
                    dimension=dimension,
                    annotator_a=annotator_a,
                    annotator_b=annotator_b,
                )
                max_item_count = max(max_item_count, len(labels_a))
                value = cohen_kappa(labels_a, labels_b)
                pair_key = f"{annotator_a}::{annotator_b}"
                pairwise_details[dimension][pair_key] = value
                if value is not None:
                    dimension_values.append(float(value))
            item_counts[dimension] = max_item_count
            per_dimension[dimension] = (
                round(sum(dimension_values) / len(dimension_values), 6) if dimension_values else None
            )
    else:
        for dimension in LABEL_DIMENSIONS:
            per_dimension[dimension] = None
            item_counts[dimension] = 0
            pairwise_details[dimension] = {}

    present_values = [float(value) for value in per_dimension.values() if value is not None]
    macro_average = round(sum(present_values) / len(present_values), 6) if present_values else None
    status = _kappa_status(macro_average, bool(completeness["labels_complete"]))

    reasons = set(completeness["reason_codes"])
    human_labels_present = bool(rows) and not (
        "missing_human_labels" in reasons or "incomplete_label_coverage" in reasons
    )
    kappa_present = macro_average is not None and "two_annotators_required" not in reasons
    if not human_labels_present:
        reasons.add("missing_human_labels")
    if not kappa_present:
        reasons.add("missing_kappa")
    if status in {"pilot_only", "weak_evidence_not_measurement_validated"} and kappa_present:
        reasons.add("low_kappa")
    reasons.add("kappa_alone_not_validation")
    reasons.add("contamination_audit_required")
    reasons.add("fresh_metric_bridge_required")
    reasons.add("claim_gate_allow_required")

    return {
        "run_id": str(run_id),
        "label_schema_version": LABEL_SCHEMA_VERSION,
        "labels_complete": bool(completeness["labels_complete"]),
        "human_labels_present": human_labels_present,
        "kappa_present": kappa_present,
        "macro_average_kappa": macro_average,
        "per_dimension_kappa": per_dimension,
        "item_count_per_dimension": item_counts,
        "annotator_ids": annotator_ids,
        "pairwise_kappa": pairwise_details,
        "kappa_status": status,
        "measurement_validated_allowed": False,
        "denied_claims": list(DENIED_CLAIMS),
        "reason_codes": _ordered_reason_codes(reasons),
        "reason_code_order": list(REASON_CODE_ORDER),
        "required_next_evidence": [
            "complete_artifacts",
            "controlled_live_run",
            "contamination_pass",
            "fresh_metric_bridge",
            "claim_gate_allow",
            "P04_operator_review",
            "P09_operator_review_if_runtime_claims_are_needed",
        ],
        "completeness_report": completeness,
        "claim_boundary": (
            "High kappa alone is not measurement validation; measurement_validated remains denied until "
            "complete artifacts, controlled live run, human labels, acceptable kappa, contamination pass, "
            "fresh metric bridge, and claim gate allow all hold."
        ),
    }


def format_kappa_report_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Human Label And Kappa Report",
        "",
        "## Summary",
        "",
        f"- Run id: `{report['run_id']}`",
        f"- Label schema version: `{report['label_schema_version']}`",
        f"- Labels complete: {str(bool(report['labels_complete'])).lower()}",
        f"- Human labels present: {str(bool(report['human_labels_present'])).lower()}",
        f"- Kappa present: {str(bool(report['kappa_present'])).lower()}",
        f"- Macro-average kappa: `{report.get('macro_average_kappa')}`",
        f"- Kappa status: `{report['kappa_status']}`",
        f"- measurement_validated_allowed: {str(bool(report['measurement_validated_allowed'])).lower()}",
        "",
        "## Per-Dimension Kappa",
        "",
        "| dimension | kappa | item_count |",
        "| --- | --- | --- |",
    ]
    for dimension in LABEL_DIMENSIONS:
        lines.append(
            f"| `{dimension}` | `{report['per_dimension_kappa'].get(dimension)}` | "
            f"{report['item_count_per_dimension'].get(dimension, 0)} |"
        )
    lines.extend(["", "## Reason Codes", ""])
    reason_codes = list(report.get("reason_codes") or [])
    if reason_codes:
        lines.extend(f"- `{reason}`" for reason in reason_codes)
    else:
        lines.append("- `none`")
    lines.extend(["", "## Denied Claims", ""])
    lines.extend(f"- `{claim}`" for claim in report.get("denied_claims", []))
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- P27 prepares human-label and kappa artifacts only.",
            "- P27 does not fabricate labels.",
            "- P27 does not perform empirical validation.",
            "- Missing human labels deny measurement_validated.",
            "- Missing kappa denies measurement_validated.",
            "- High kappa alone is not measurement validation.",
            "- Contamination audit and fresh metric bridge remain required.",
            "- Claim gate allow remains required.",
            "- P04 remains deferred/operator-required.",
            "- P09 remains BLOCKED_OPERATOR_REQUIRED.",
            "",
        ]
    )
    return "\n".join(lines)


def write_human_label_kappa_outputs(output_dir: str | Path, report: Mapping[str, Any]) -> dict[str, str]:
    resolved_output_dir = Path(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    payload = deepcopy(dict(report))
    completeness_path = _stable_write_json(
        resolved_output_dir / "human_label_completeness_report.json",
        payload["completeness_report"],
    )
    kappa_path = _stable_write_json(resolved_output_dir / "kappa_report.json", payload)
    markdown_path = resolved_output_dir / "kappa_report.md"
    markdown_path.write_text(format_kappa_report_markdown(payload), encoding="utf-8")
    return {
        "completeness_report": str(completeness_path.resolve()),
        "kappa_report": str(kappa_path.resolve()),
        "kappa_markdown": str(markdown_path.resolve()),
    }
