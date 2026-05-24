from __future__ import annotations

import json
from collections import Counter
from collections import defaultdict
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.hashing import stable_hash


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
SILVER_EVIDENCE_CLASS = "llm_generated_silver_label_candidate"
FINAL_EVIDENCE_CLASS = "backend_constrained_operational_candidate_package"
REVIEW_STATUS = "candidate_pending_independent_review"
DENIED_CLAIMS = [
    "calibrated_proxy_supported",
    "fixed-target teacher-forced NLL support",
    "global selector superiority",
    "human/external gold validation",
    "measurement_validation",
    "metric bridge support",
    "paper evidence",
    "teacher-forced NLL support",
    "vinfo_proxy_supported",
]


def _write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")
    return path


def _count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "missing") for row in rows).items()))


def _mean_confidence(rows: Sequence[Mapping[str, Any]]) -> float:
    values = [float(row.get("confidence") or 0.0) for row in rows]
    return round(sum(values) / len(values), 6) if values else 0.0


def _confidence_bucket(confidence: float) -> str:
    if confidence >= 0.8:
        return "high_confidence"
    if confidence >= 0.5:
        return "medium_confidence"
    return "low_confidence"


def _uncertainty_bucket(row: Mapping[str, Any]) -> str:
    if not bool(row.get("parse_ok")):
        return "parse_failed"
    uncertainty = str(row.get("uncertainty") or "high").lower()
    if uncertainty in {"low", "medium", "high"}:
        return f"{uncertainty}_uncertainty"
    return "high_uncertainty"


def _disagreement_buckets(rows: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        parent = str(row.get("parent_sample_id") or "missing_parent")
        label = str(row.get("label") or "missing")
        if label != "parse_failed":
            grouped[parent].append(label)
    buckets: dict[str, str] = {}
    for parent, labels in grouped.items():
        distinct = sorted(set(labels))
        if not labels:
            bucket = "no_valid_label"
        elif len(distinct) == 1:
            bucket = "agreement"
        elif "uncertain" in distinct:
            bucket = "uncertainty_disagreement"
        else:
            bucket = "label_disagreement"
        buckets[parent] = bucket
    return buckets


def build_silver_label_rows(label_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    disagreement = _disagreement_buckets(label_rows)
    silver_rows: list[dict[str, Any]] = []
    for row in label_rows:
        sample_metadata = dict(row.get("sample_metadata") or {})
        parent_sample_id = str(row.get("parent_sample_id") or "")
        input_hash = stable_hash(
            {
                "parent_sample_id": parent_sample_id,
                "probe_type": str(row.get("probe_type") or ""),
                "sample_metadata": sample_metadata,
            }
        )
        evidence_hash = stable_hash(
            {
                "input_hash": input_hash,
                "label": str(row.get("label") or ""),
                "model_id": str(row.get("model_id") or ""),
                "prompt_hash": str(row.get("prompt_hash") or ""),
            }
        )
        provenance = {
            "evidence_hash": evidence_hash,
            "input_hash": input_hash,
            "label_generator_role": "independent_live_api_silver_labeler",
            "model_id": str(row.get("model_id") or ""),
            "prompt_hash": str(row.get("prompt_hash") or ""),
            "source_label_record_hash": str(row.get("label_record_hash") or ""),
        }
        silver_row = {
            "claim_ceiling": CLAIM_STATUS,
            "confidence": round(float(row.get("confidence") or 0.0), 6),
            "confidence_bucket": _confidence_bucket(float(row.get("confidence") or 0.0)),
            "denied_claims": list(DENIED_CLAIMS),
            "disagreement_bucket": disagreement.get(parent_sample_id, "no_valid_label"),
            "evidence_class": SILVER_EVIDENCE_CLASS,
            "evidence_hash": evidence_hash,
            "fixed_target_teacher_forced_nll_available": False,
            "human_external_gold_label": False,
            "input_hash": input_hash,
            "label_record_hash": stable_hash({"silver_label_row": provenance}),
            "llm_generated_silver_label": True,
            "model_id": str(row.get("model_id") or ""),
            "normalized_label": str(row.get("label") or "uncertain"),
            "parent_sample_id": parent_sample_id,
            "parse_ok": bool(row.get("parse_ok")),
            "probe_type": str(row.get("probe_type") or ""),
            "provenance": provenance,
            "raw_response_stored": False,
            "review_status": REVIEW_STATUS,
            "sample_metadata": sample_metadata,
            "schema_version": "epf_live_api_silver_label_row_v1",
            "selector_policy_used_to_generate_label": False,
            "teacher_forced_nll_support": False,
            "uncertainty_bucket": _uncertainty_bucket(row),
        }
        silver_rows.append(silver_row)
    return silver_rows


def build_live_api_silver_label_package(
    *,
    output_dir: str | Path,
    label_rows: Sequence[Mapping[str, Any]],
    source_artifacts: Sequence[str],
) -> dict[str, Any]:
    output = Path(output_dir)
    silver_rows = build_silver_label_rows(label_rows)
    label_counts = _count_by(silver_rows, "normalized_label")
    uncertainty_counts = _count_by(silver_rows, "uncertainty_bucket")
    disagreement_counts = _count_by(silver_rows, "disagreement_bucket")
    common = {
        "claim_ceiling": CLAIM_STATUS,
        "denied_claims": list(DENIED_CLAIMS),
        "evidence_class": SILVER_EVIDENCE_CLASS,
        "provenance": {
            "input_artifacts": list(source_artifacts),
            "live_api_surface": "dashscope_openai_compatible_chat_api",
            "normalized_outputs_only": True,
            "raw_api_responses_stored": False,
        },
        "review_status": REVIEW_STATUS,
    }
    label_schema = {
        **common,
        "fields": {
            "confidence_bucket": ["high_confidence", "medium_confidence", "low_confidence"],
            "disagreement_bucket": ["agreement", "label_disagreement", "no_valid_label", "uncertainty_disagreement"],
            "normalized_label": ["not_supporting", "parse_failed", "supporting", "uncertain"],
            "uncertainty_bucket": ["high_uncertainty", "low_uncertainty", "medium_uncertainty", "parse_failed"],
        },
        "human_external_gold_label": False,
        "schema_version": "epf_live_api_silver_label_schema_v1",
    }
    manifest = {
        **common,
        "label_count": len(silver_rows),
        "label_rows_path": "silver_labels.jsonl",
        "schema_version": "epf_live_api_silver_label_manifest_v1",
    }
    label_generation_report = {
        **common,
        "human_external_gold_labels_used": False,
        "label_count": len(silver_rows),
        "label_counts": label_counts,
        "mean_confidence": _mean_confidence(silver_rows),
        "measurement_validation_claim": False,
        "raw_response_stored": False,
        "schema_version": "epf_live_api_silver_label_generation_report_v1",
        "selector_policy_used_to_generate_labels": False,
    }
    uncertainty_report = {
        **common,
        "disagreement_bucket_counts": disagreement_counts,
        "label_count": len(silver_rows),
        "schema_version": "epf_live_api_silver_label_uncertainty_disagreement_v1",
        "uncertainty_bucket_counts": uncertainty_counts,
    }
    _write_json(output / "label_schema.json", label_schema)
    _write_json(output / "silver_label_manifest.json", manifest)
    _write_jsonl(output / "silver_labels.jsonl", silver_rows)
    _write_json(output / "label_generation_report.json", label_generation_report)
    _write_json(output / "uncertainty_disagreement_report.json", uncertainty_report)
    return {
        **common,
        "artifacts": {
            "label_generation_report": str(output / "label_generation_report.json"),
            "label_schema": str(output / "label_schema.json"),
            "silver_label_manifest": str(output / "silver_label_manifest.json"),
            "silver_labels": str(output / "silver_labels.jsonl"),
            "uncertainty_disagreement_report": str(output / "uncertainty_disagreement_report.json"),
        },
        "label_count": len(silver_rows),
        "label_counts": label_counts,
        "mean_confidence": _mean_confidence(silver_rows),
        "schema_version": "epf_live_api_silver_label_package_result_v1",
        "uncertainty_bucket_counts": uncertainty_counts,
    }


def build_final_epf_package(
    *,
    output_dir: str | Path,
    silver_label_package: Mapping[str, Any],
    scoped_operational_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    output = Path(output_dir)
    common = {
        "claim_ceiling": CLAIM_STATUS,
        "denied_claims": list(DENIED_CLAIMS),
        "evidence_class": FINAL_EVIDENCE_CLASS,
        "provenance": {
            "silver_label_package": dict(silver_label_package.get("artifacts") or {}),
            "source": "epf_live_api_finalizer",
        },
        "review_status": REVIEW_STATUS,
    }
    operational_summary = {
        **common,
        "human_external_gold_labels_used": False,
        "label_count": int(silver_label_package.get("label_count") or 0),
        "measurement_validation_claim": False,
        "schema_version": "epf_final_scoped_operational_evaluation_summary_v1",
        "scoped_operational_inputs": dict(scoped_operational_inputs),
        "silver_labels_are_model_adjudicated": True,
        "teacher_forced_fixed_target_nll_available": False,
    }
    manifest = {
        **common,
        "artifacts": {
            "final_claim_request": str(output / "final_claim_request.json"),
            "independent_review_checklist": str(output / "independent_review_checklist.md"),
            "scoped_operational_evaluation_summary": str(output / "scoped_operational_evaluation_summary.json"),
        },
        "claim_status": CLAIM_STATUS,
        "schema_version": "epf_final_manifest_v1",
        "terminal_state": "EPF_FINAL_REVIEWABLE",
    }
    claim_request = {
        **common,
        "claim_status": CLAIM_STATUS,
        "development_claim_upgrade_performed": False,
        "human_external_gold_validation": False,
        "independent_review_required": True,
        "measurement_validation_claim": False,
        "requested_candidate_claims": [
            "llm_generated_silver_label_candidate",
            "scoped_operational_evaluation_candidate",
        ],
        "route5_unlock_requested": False,
        "route8_unlock_requested": False,
        "schema_version": "epf_final_claim_request_v1",
        "teacher_forced_nll_support": False,
    }
    checklist = (
        "# EPF Final Independent Review Checklist\n\n"
        f"- evidence_class: `{FINAL_EVIDENCE_CLASS}`\n"
        f"- claim_ceiling: `{CLAIM_STATUS}`\n"
        "- denied_claims: see `final_claim_request.json`\n"
        "- provenance: see `final_epf_manifest.json`\n"
        f"- review_status: `{REVIEW_STATUS}`\n"
        "- Verify silver labels are LLM-generated/model-adjudicated, not human or external gold.\n"
        "- Verify no raw API responses or secrets are stored.\n"
        "- Verify no fixed-target teacher-forced NLL support is claimed.\n"
        "- Verify no metric bridge, calibrated proxy, V-information proxy, measurement validation, paper evidence, or global selector superiority claim is made.\n"
        "- Verify Route 5 and Route 8 remain locked.\n"
    )
    _write_json(output / "scoped_operational_evaluation_summary.json", operational_summary)
    _write_json(output / "final_epf_manifest.json", manifest)
    _write_json(output / "final_claim_request.json", claim_request)
    (output / "independent_review_checklist.md").write_text(checklist, encoding="utf-8")
    return {
        **common,
        "artifacts": manifest["artifacts"],
        "claim_status": CLAIM_STATUS,
        "schema_version": "epf_final_package_result_v1",
        "terminal_state": "EPF_FINAL_REVIEWABLE",
    }
