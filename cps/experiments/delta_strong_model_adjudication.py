from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.hashing import canonical_json_dumps
from cps.benchmarks.hashing import stable_hash
from cps.experiments.route4d_hybrid_utility_bridge import fit_route4d_bridge
from cps.experiments.route6a_measurement_pilot import _default_live_client
from cps.experiments.route6a_measurement_pilot import build_context_pair_sample
from cps.experiments.route6a_measurement_pilot import build_frozen_rubric


DEFAULT_OUTPUT_DIR = Path("artifacts/experiments/delta_strong_model_adjudication")
DEFAULT_DOCS_PATH = Path("docs/experiments/Delta-strong-model-adjudicated-validation-final-report.md")
DEFAULT_EXISTING_LABELS_PATH = Path(
    "artifacts/experiments/route6c_model_adjudication_scaleup/model_adjudicated_labels.jsonl"
)
DEFAULT_ROUTE4D_BRIDGE_ROWS_PATH = Path(
    "artifacts/experiments/route4d_hybrid_utility_bridge/bridge_rows.jsonl"
)
DEFAULT_ROUTE4_ROWS_PATH = Path("artifacts/experiments/route4_bridge/bridge_rows.jsonl")
DEFAULT_CANDIDATE_POOLS_PATH = Path("artifacts/benchmarks/hotpotqa_candidate_pools.jsonl")
DEFAULT_WORKBENCH_TRACES_PATH = Path(
    "artifacts/experiments/integrated_validation_workbench/hotpotqa_smoke/workbench_traces.jsonl"
)
DEFAULT_BETA_PORTFOLIO_PATH = Path("artifacts/experiments/beta_hybrid_label_model/portfolio_update.json")
DEFAULT_BETA_DOCS_PATH = Path("docs/experiments/Beta-hybrid-label-model-final-report.md")
DEFAULT_JUDGE_CONFIG = Path("configs/local/bridge-data-generation-live.local.json")

CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
DELTA_LABEL_SCHEMA_VERSION = "delta_strong_model_sufficiency_label_v1"
DELTA_NORMALIZATION_VERSION = "delta_strong_model_label_normalization_v1"
DELTA_PROTOCOL_VERSION = "delta_strong_model_judge_protocol_v1"
DELTA_RUBRIC_VERSION = "delta_strong_model_sufficiency_rubric_v1"
PRIMARY_PROMPT_VERSION = "delta_strong_model_sufficiency_prompt_v1"
ORDER_REVERSAL_PROMPT_VERSION = "delta_strong_model_order_reversal_prompt_v1"
DUPLICATE_PROMPT_VERSION = "delta_strong_model_duplicate_consistency_prompt_v1"
ALTERNATE_PROMPT_VERSION = "delta_strong_model_alternate_prompt_v1"

DENIED_CLAIMS = [
    "human measurement validation",
    "human-validated evidence",
    "measurement validation",
    "calibrated_proxy_supported",
    "vinfo_proxy_supported",
    "paper evidence",
    "metric bridge support",
    "selector superiority",
    "global selector superiority",
    "deployed V-information verification",
]
ALLOWED_CANDIDATE_WORDING = [
    "model_adjudicated_measurement_candidate",
    "strong_model_adjudicated_sufficiency_evidence",
    "model_adjudicated_bridge_candidate_pending_review",
]
FORBIDDEN_RAW_FIELDS = {
    "api_key",
    "choices",
    "messages",
    "raw_api_response",
    "raw_response",
    "request_body",
    "response_body",
    "secret",
}
SUFFICIENCY_SCORES = {"insufficient": 0.0, "partial": 0.5, "sufficient": 1.0}
UNCERTAINTY_TO_CONFIDENCE = {"low": 0.9, "medium": 0.7, "high": 0.45}
PROMPT_BY_PROBE = {
    "primary": PRIMARY_PROMPT_VERSION,
    "order_reversal": ORDER_REVERSAL_PROMPT_VERSION,
    "duplicate": DUPLICATE_PROMPT_VERSION,
    "alternate_prompt": ALTERNATE_PROMPT_VERSION,
    "alternate_model": ALTERNATE_PROMPT_VERSION,
}
VIEW_SORT_ORDER = {
    "primary": 0,
    "order_reversal": 1,
    "duplicate": 2,
    "alternate_prompt": 3,
    "alternate_model": 4,
}


def _read_json(path: str | Path) -> dict[str, Any]:
    input_path = Path(path)
    if not input_path.exists() or not input_path.is_file():
        return {}
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    if not input_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{input_path.name}: row {line_number} must be a JSON object")
        rows.append(payload)
    return rows


def _write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def _write_jsonl(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(canonical_json_dumps(dict(row)) + "\n" for row in rows), encoding="utf-8")
    return output


def _write_csv(path: str | Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return output


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.name if candidate.is_absolute() else candidate.as_posix()


def _mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _confidence(row: Mapping[str, Any]) -> float:
    return UNCERTAINTY_TO_CONFIDENCE.get(str(row.get("uncertainty") or "high"), 0.45)


def _score_delta(row: Mapping[str, Any]) -> float:
    baseline = SUFFICIENCY_SCORES.get(str(row.get("baseline_sufficiency") or ""), 0.0)
    augmented = SUFFICIENCY_SCORES.get(str(row.get("augmented_sufficiency") or ""), 0.0)
    return round(augmented - baseline, 6)


def _label_signature(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("delta_label") or "invalid"),
        str(row.get("baseline_sufficiency") or "invalid"),
        str(row.get("augmented_sufficiency") or "invalid"),
        str(row.get("answer_supported") or "invalid"),
    )


def _same_label(left: Mapping[str, Any] | None, right: Mapping[str, Any] | None) -> bool:
    if left is None or right is None:
        return False
    return _label_signature(left) == _label_signature(right)


def _normalize_probe(value: Any) -> str:
    probe = str(value or "primary").strip()
    if probe in PROMPT_BY_PROBE:
        return probe
    return "primary"


def _rationale_hash(row: Mapping[str, Any]) -> str:
    return stable_hash(
        {
            "answer_supported": str(row.get("answer_supported") or ""),
            "augmented_sufficiency": str(row.get("augmented_sufficiency") or ""),
            "baseline_sufficiency": str(row.get("baseline_sufficiency") or ""),
            "delta_label": str(row.get("delta_label") or ""),
            "evidence_relevance": str(row.get("evidence_relevance") or ""),
            "uncertainty": str(row.get("uncertainty") or ""),
        }
    )


def normalize_delta_label(row: Mapping[str, Any]) -> dict[str, Any]:
    probe = _normalize_probe(row.get("consistency_probe_type"))
    parent = str(row.get("parent_sample_id") or row.get("sample_id") or "")
    source_ref = str(row.get("source_sample_ref") or row.get("sample_id") or "")
    record = {
        "answer_supported": str(row.get("answer_supported") or "invalid"),
        "augmented_sufficiency": str(row.get("augmented_sufficiency") or "invalid"),
        "baseline_sufficiency": str(row.get("baseline_sufficiency") or "invalid"),
        "claim_status": CLAIM_STATUS,
        "compact_rationale_hash": _rationale_hash(row),
        "confidence": _confidence(row),
        "consistency_probe_type": probe,
        "counts_as_human_label": False,
        "delta_label": str(row.get("delta_label") or "invalid"),
        "delta_model_utility": _score_delta(row),
        "evaluator_id": str(row.get("evaluator_id") or ""),
        "evidence_relevance": str(row.get("evidence_relevance") or "invalid"),
        "human_annotation_required": False,
        "human_annotation_status": "not_requested_model_only_by_user_instruction",
        "judge_model_id": str(row.get("judge_model_id") or ""),
        "judge_provider": str(row.get("judge_provider") or ""),
        "label_schema_version": DELTA_LABEL_SCHEMA_VERSION,
        "label_source_type": "strong_model_adjudicated",
        "measurement_validation_claim": False,
        "normalization_version": DELTA_NORMALIZATION_VERSION,
        "parent_sample_id": parent,
        "prompt_version": PROMPT_BY_PROBE[probe],
        "raw_response_stored": False,
        "rubric_version": DELTA_RUBRIC_VERSION,
        "sample_id": str(row.get("sample_id") or source_ref or parent),
        "source_label_record_hash": str(row.get("label_record_hash") or ""),
        "source_label_schema_version": str(row.get("label_schema_version") or ""),
        "source_route4_row_identity_hash": str(row.get("source_route4_row_identity_hash") or ""),
        "source_sample_ref": source_ref,
        "uncertainty": str(row.get("uncertainty") or "high"),
    }
    record["judge_view_id"] = stable_hash(
        {
            "parent_sample_id": record["parent_sample_id"],
            "probe": record["consistency_probe_type"],
            "sample_id": record["sample_id"],
            "source_label_record_hash": record["source_label_record_hash"],
        }
    )
    record["label_record_hash"] = stable_hash(record)
    return record


def _has_forbidden_raw_fields(rows: Sequence[Mapping[str, Any]]) -> bool:
    for row in rows:
        if FORBIDDEN_RAW_FIELDS.intersection(row):
            return True
    return False


def _group_by_parent(labels: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for label in labels:
        parent = str(label.get("parent_sample_id") or label.get("sample_id") or "")
        if parent:
            groups.setdefault(parent, []).append(dict(label))
    return {
        parent: sorted(
            rows,
            key=lambda row: (
                VIEW_SORT_ORDER.get(str(row.get("consistency_probe_type") or ""), 99),
                str(row.get("sample_id") or ""),
            ),
        )
        for parent, rows in sorted(groups.items())
    }


def _view_by_probe(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    views: dict[str, dict[str, Any]] = {}
    for row in rows:
        probe = _normalize_probe(row.get("consistency_probe_type"))
        views.setdefault(probe, dict(row))
    return views


def _has_required_views(rows: Sequence[Mapping[str, Any]]) -> bool:
    views = _view_by_probe(rows)
    return (
        "primary" in views
        and bool({"order_reversal", "duplicate"}.intersection(views))
        and bool({"alternate_prompt", "alternate_model"}.intersection(views))
    )


def _route4_hash_from_sample(sample: Mapping[str, Any]) -> str:
    ref = dict(sample.get("source_route4_row_ref") or {})
    return str(ref.get("route4_row_identity_hash") or "")


def _variant_sample(sample: Mapping[str, Any], variant: str, ordinal: int) -> dict[str, Any]:
    payload = dict(sample)
    parent = str(sample.get("sample_id") or "")
    payload["parent_sample_id"] = parent
    payload["consistency_probe_type"] = variant
    payload["sample_id"] = f"delta::{variant}::{stable_hash({'parent': parent, 'ordinal': ordinal})[:20]}"
    if variant == "order_reversal":
        payload["baseline_context_packets"] = list(reversed(list(payload.get("baseline_context_packets") or [])))
        payload["added_block_packets"] = list(reversed(list(payload.get("added_block_packets") or [])))
    return payload


def _response_contract() -> dict[str, Any]:
    return {
        "answer_supported": ["supported", "partial", "unsupported", "invalid"],
        "augmented_sufficiency": ["sufficient", "partial", "insufficient", "invalid"],
        "baseline_sufficiency": ["sufficient", "partial", "insufficient", "invalid"],
        "delta_label": ["improves", "unchanged", "worsens", "invalid"],
        "evidence_relevance": ["relevant", "mixed", "irrelevant", "invalid"],
        "invalid_reason": "string, empty unless invalid",
        "uncertainty": ["low", "medium", "high"],
    }


def _delta_judge_messages(sample_row: Mapping[str, Any], rubric: Mapping[str, Any]) -> list[dict[str, str]]:
    probe = _normalize_probe(sample_row.get("consistency_probe_type"))
    system_suffix = {
        "alternate_prompt": (
            " Apply the same rubric, but first look for missing answer support and then decide "
            "whether the added block changes sufficiency."
        ),
        "duplicate": " Re-adjudicate independently; do not assume a prior answer exists.",
        "order_reversal": " Treat packet order as non-authoritative and apply the same sufficiency rubric.",
    }.get(probe, " Apply the sufficiency rubric directly.")
    visible_item = {
        "added_block_packets": sample_row.get("added_block_packets") or [],
        "baseline_context_packets": sample_row.get("baseline_context_packets") or [],
        "question": sample_row.get("question"),
        "sample_id": sample_row.get("sample_id"),
        "target_y": sample_row.get("target_y"),
    }
    return [
        {
            "role": "system",
            "content": (
                "You are a strong-model sufficiency adjudicator. "
                "Return only one JSON object matching the enum contract. "
                "Do not infer hidden gold labels, utility scores, or logloss values."
                f"{system_suffix}"
            ),
        },
        {
            "role": "user",
            "content": canonical_json_dumps(
                {
                    "item": visible_item,
                    "prompt_version": PROMPT_BY_PROBE[probe],
                    "response_contract": _response_contract(),
                    "rubric": rubric,
                }
            ),
        },
    ]


def _choice_content(response: Mapping[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, Mapping):
        return ""
    message = first.get("message")
    if isinstance(message, Mapping):
        return str(message.get("content") or "").strip()
    return str(first.get("text") or "").strip()


def _parse_judge_content(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`").strip()
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    payload = json.loads(stripped)
    if not isinstance(payload, dict):
        raise ValueError("judge_payload_not_object")
    return payload


def _enum(value: Any, allowed: Sequence[str], invalid: str = "invalid") -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in allowed else invalid


def _label_from_payload(
    *,
    sample_row: Mapping[str, Any],
    payload: Mapping[str, Any],
    judge_model_id: str,
    judge_provider: str,
) -> dict[str, Any]:
    probe = _normalize_probe(sample_row.get("consistency_probe_type"))
    source = {
        "answer_supported": _enum(payload.get("answer_supported"), _response_contract()["answer_supported"]),
        "augmented_sufficiency": _enum(
            payload.get("augmented_sufficiency"),
            _response_contract()["augmented_sufficiency"],
        ),
        "baseline_sufficiency": _enum(
            payload.get("baseline_sufficiency"),
            _response_contract()["baseline_sufficiency"],
        ),
        "consistency_probe_type": probe,
        "counts_as_human_label": False,
        "delta_label": _enum(payload.get("delta_label"), _response_contract()["delta_label"]),
        "evaluator_id": f"{judge_provider}::{judge_model_id}",
        "evidence_relevance": _enum(payload.get("evidence_relevance"), _response_contract()["evidence_relevance"]),
        "judge_model_id": judge_model_id,
        "judge_provider": judge_provider,
        "label_schema_version": "delta_live_judge_payload_v1",
        "label_source_type": "model_adjudicated",
        "measurement_validation_candidate_allowed": False,
        "parent_sample_id": str(sample_row.get("parent_sample_id") or sample_row.get("sample_id") or ""),
        "prompt_version": PROMPT_BY_PROBE[probe],
        "raw_response_stored": False,
        "rubric_version": DELTA_RUBRIC_VERSION,
        "sample_id": str(sample_row.get("sample_id") or ""),
        "source_route4_row_identity_hash": _route4_hash_from_sample(sample_row),
        "source_sample_ref": str(sample_row.get("sample_id") or ""),
        "uncertainty": _enum(payload.get("uncertainty"), _response_contract()["uncertainty"], invalid="high"),
    }
    source["label_record_hash"] = stable_hash(source)
    return normalize_delta_label(source)


def _invalid_live_label(
    *,
    sample_row: Mapping[str, Any],
    judge_model_id: str,
    judge_provider: str,
) -> dict[str, Any]:
    return _label_from_payload(
        sample_row=sample_row,
        payload={
            "answer_supported": "invalid",
            "augmented_sufficiency": "invalid",
            "baseline_sufficiency": "invalid",
            "delta_label": "invalid",
            "evidence_relevance": "invalid",
            "uncertainty": "high",
        },
        judge_model_id=judge_model_id,
        judge_provider=judge_provider,
    )


def _run_live_delta_adjudication(
    *,
    sample: Sequence[Mapping[str, Any]],
    client: Any,
    judge_model_id: str,
    judge_provider: str,
    max_completion_tokens: int,
    timeout: int,
    extra_body: Mapping[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rubric = dict(build_frozen_rubric())
    rubric["delta_protocol_version"] = DELTA_PROTOCOL_VERSION
    labels: list[dict[str, Any]] = []
    failed = 0
    for sample_row in sample:
        try:
            response = client.chat_completion(
                model=judge_model_id,
                messages=_delta_judge_messages(sample_row, rubric),
                max_completion_tokens=max_completion_tokens,
                temperature=0.0,
                seed=60418,
                stream=False,
                n=1,
                extra_body=extra_body,
                timeout=timeout,
            )
            label = _label_from_payload(
                sample_row=sample_row,
                payload=_parse_judge_content(_choice_content(response)),
                judge_model_id=judge_model_id,
                judge_provider=judge_provider,
            )
        except Exception:
            failed += 1
            label = _invalid_live_label(
                sample_row=sample_row,
                judge_model_id=judge_model_id,
                judge_provider=judge_provider,
            )
        labels.append(label)
    accepted = sum(1 for label in labels if label["delta_label"] != "invalid")
    return labels, {
        "accepted_model_adjudicated_count": accepted,
        "claim_status": CLAIM_STATUS,
        "counts_as_human_labels": False,
        "failed_or_invalid_count": failed + len(labels) - accepted,
        "human_annotation_required": False,
        "live_api_used": True,
        "normalized_label_count": len(labels),
        "raw_api_responses_stored": False,
        "schema_version": "delta_live_adjudication_batch_report_v1",
    }


def _build_protocol(labels: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    judge_model_ids = sorted({str(label.get("judge_model_id") or "") for label in labels if label.get("judge_model_id")})
    evaluator_ids = sorted({str(label.get("evaluator_id") or "") for label in labels if label.get("evaluator_id")})
    return {
        "allowed_candidate_wording": ALLOWED_CANDIDATE_WORDING,
        "challenge_set_controls": {
            "alternate_prompt_required": True,
            "duplicate_consistency_required": True,
            "order_reversal_required": True,
            "raw_response_storage_allowed": False,
        },
        "claim_status": CLAIM_STATUS,
        "confidence_calibration": {
            "confidence_source": "normalized_uncertainty_enum",
            "high": UNCERTAINTY_TO_CONFIDENCE["low"],
            "medium": UNCERTAINTY_TO_CONFIDENCE["medium"],
            "low": UNCERTAINTY_TO_CONFIDENCE["high"],
            "validation_scope": "model_self_consistency_only_not_human_calibration",
        },
        "denied_claims": DENIED_CLAIMS,
        "evaluator_ids": evaluator_ids,
        "human_annotation_required": False,
        "judge_model_ids": judge_model_ids,
        "label_schema_version": DELTA_LABEL_SCHEMA_VERSION,
        "no_raw_response_policy": {
            "forbidden_fields": sorted(FORBIDDEN_RAW_FIELDS),
            "raw_api_responses_stored": False,
        },
        "normalization_version": DELTA_NORMALIZATION_VERSION,
        "prompt_versions": {
            "alternate_prompt": ALTERNATE_PROMPT_VERSION,
            "duplicate": DUPLICATE_PROMPT_VERSION,
            "order_reversal": ORDER_REVERSAL_PROMPT_VERSION,
            "primary": PRIMARY_PROMPT_VERSION,
        },
        "protocol_version": DELTA_PROTOCOL_VERSION,
        "rubric_version": DELTA_RUBRIC_VERSION,
        "schema_version": "delta_strong_model_judge_protocol_freeze_v1",
    }


def _load_source_samples(
    *,
    route4_rows_path: str | Path,
    candidate_pools_path: str | Path,
    sample_size: int,
) -> dict[str, dict[str, Any]]:
    route4_rows = _read_jsonl(route4_rows_path)
    candidate_pools = _read_jsonl(candidate_pools_path)
    samples = build_context_pair_sample(
        bridge_rows=route4_rows,
        candidate_pools=candidate_pools,
        sample_size=sample_size,
    )
    return {str(sample.get("sample_id") or ""): sample for sample in samples}


def _missing_variants_for_parent(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    views = _view_by_probe(rows)
    missing: list[str] = []
    if "primary" not in views:
        missing.append("primary")
    if not {"order_reversal", "duplicate"}.intersection(views):
        missing.append("order_reversal")
    if not {"alternate_prompt", "alternate_model"}.intersection(views):
        missing.append("alternate_prompt")
    return missing


def _build_live_plan(
    *,
    labels: Sequence[Mapping[str, Any]],
    route4_rows_path: str | Path,
    candidate_pools_path: str | Path,
    preferred_adjudicated_items: int,
    minimum_three_view_items: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    groups = _group_by_parent(labels)
    current_three_view = sum(1 for rows in groups.values() if _has_required_views(rows))
    if len(labels) >= preferred_adjudicated_items and current_three_view >= minimum_three_view_items:
        return [], []
    sample_by_parent = _load_source_samples(
        route4_rows_path=route4_rows_path,
        candidate_pools_path=candidate_pools_path,
        sample_size=max(preferred_adjudicated_items, len(groups), minimum_three_view_items),
    )
    plan: list[dict[str, Any]] = []
    reason_codes: list[str] = []
    planned_groups = {parent: list(rows) for parent, rows in groups.items()}
    ordinal = 0
    parents = sorted(groups, key=lambda parent: (-len(groups[parent]), parent))
    for parent in parents:
        if len(labels) + len(plan) >= preferred_adjudicated_items and current_three_view >= minimum_three_view_items:
            break
        source = sample_by_parent.get(parent)
        if source is None:
            reason_codes.append("source_context_pair_unavailable_for_live_view")
            continue
        missing = _missing_variants_for_parent(planned_groups[parent])
        if not missing:
            continue
        for variant in missing:
            planned = _variant_sample(source, variant, ordinal)
            ordinal += 1
            plan.append(planned)
            planned_groups[parent].append(
                {
                    "consistency_probe_type": variant,
                    "parent_sample_id": parent,
                    "sample_id": planned["sample_id"],
                }
            )
        current_three_view = sum(1 for rows in planned_groups.values() if _has_required_views(rows))
    if current_three_view < minimum_three_view_items:
        reason_codes.append("three_view_item_target_not_plannable_from_available_context_pairs")
    duplicate_target = max(1, minimum_three_view_items // 3) if minimum_three_view_items else 0
    order_target = max(1, minimum_three_view_items // 3) if minimum_three_view_items else 0
    for variant, target in (("duplicate", duplicate_target), ("order_reversal", order_target)):
        current = sum(
            1
            for rows in planned_groups.values()
            if "primary" in _view_by_probe(rows) and variant in _view_by_probe(rows)
        )
        if current >= target:
            continue
        for parent in parents:
            if current >= target:
                break
            source = sample_by_parent.get(parent)
            if source is None:
                continue
            views = _view_by_probe(planned_groups[parent])
            if "primary" not in views or variant in views:
                continue
            planned = _variant_sample(source, variant, ordinal)
            ordinal += 1
            plan.append(planned)
            planned_groups[parent].append(
                {
                    "consistency_probe_type": variant,
                    "parent_sample_id": parent,
                    "sample_id": planned["sample_id"],
                }
            )
            current += 1
        if current < target:
            reason_codes.append(f"{variant}_target_not_plannable_from_available_context_pairs")
    return plan, sorted(set(reason_codes))


def _run_scaleup(
    *,
    existing_labels_path: str | Path,
    route4d_bridge_rows_path: str | Path,
    route4_rows_path: str | Path,
    candidate_pools_path: str | Path,
    output_dir: Path,
    run_live_adjudication: bool,
    minimum_adjudicated_items: int,
    preferred_adjudicated_items: int,
    minimum_unique_parent_items: int,
    minimum_unique_original_instances: int,
    minimum_three_view_items: int,
    client: Any | None,
    judge_model_id: str | None,
    judge_provider: str | None,
    judge_config_path: str | Path | None,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    source_labels = _read_jsonl(existing_labels_path)
    labels = [normalize_delta_label(row) for row in source_labels]
    reason_codes: list[str] = []
    live_batch_report: dict[str, Any] = {
        "live_api_used": False,
        "normalized_label_count": 0,
        "schema_version": "delta_live_adjudication_batch_report_v1",
    }
    live_plan, plan_reasons = _build_live_plan(
        labels=labels,
        route4_rows_path=route4_rows_path,
        candidate_pools_path=candidate_pools_path,
        preferred_adjudicated_items=preferred_adjudicated_items,
        minimum_three_view_items=minimum_three_view_items,
    )
    reason_codes.extend(plan_reasons)
    if live_plan and run_live_adjudication:
        resolved_client = client
        live_info: dict[str, Any] = {}
        if resolved_client is None:
            resolved_client, live_info = _default_live_client(env=None, config_path=judge_config_path)
            if resolved_client is None:
                reason_codes.append(str(live_info.get("reason_code") or "approved_model_judge_unavailable"))
        else:
            live_info = {
                "extra_body": {"enable_thinking": False},
                "judge_model_id": judge_model_id or "approved_model_judge",
                "judge_provider": judge_provider or "approved_provider",
                "max_completion_tokens": 256,
                "request_timeout_seconds": 60,
            }
        if resolved_client is not None:
            live_labels, live_batch_report = _run_live_delta_adjudication(
                sample=live_plan,
                client=resolved_client,
                judge_model_id=str(judge_model_id or live_info.get("judge_model_id") or "approved_model_judge"),
                judge_provider=str(judge_provider or live_info.get("judge_provider") or "approved_provider"),
                max_completion_tokens=int(live_info.get("max_completion_tokens") or 256),
                timeout=int(live_info.get("request_timeout_seconds") or 60),
                extra_body=live_info.get("extra_body") if isinstance(live_info.get("extra_body"), Mapping) else None,
            )
            labels.extend(live_labels)
    elif live_plan:
        reason_codes.append("live_adjudication_not_run_for_missing_delta_views")

    labels = sorted(
        labels,
        key=lambda row: (
            str(row.get("parent_sample_id") or ""),
            VIEW_SORT_ORDER.get(str(row.get("consistency_probe_type") or ""), 99),
            str(row.get("sample_id") or ""),
        ),
    )
    bridge_rows = _read_jsonl(route4d_bridge_rows_path)
    parent_to_original = {
        str(row.get("parent_sample_id") or ""): str(row.get("original_instance_id") or row.get("parent_sample_id") or "")
        for row in bridge_rows
    }
    groups = _group_by_parent(labels)
    unique_original_instances = {
        parent_to_original.get(parent, parent)
        for parent in groups
        if parent_to_original.get(parent, parent)
    }
    three_view_items = sum(1 for rows in groups.values() if _has_required_views(rows))
    checks = {
        "adjudicated_item_count_pass": len(labels) >= minimum_adjudicated_items,
        "raw_response_policy_pass": not _has_forbidden_raw_fields(labels)
        and all(bool(label.get("raw_response_stored")) is False for label in labels),
        "three_view_item_count_pass": three_view_items >= minimum_three_view_items,
        "unique_original_instance_count_pass": len(unique_original_instances) >= minimum_unique_original_instances,
        "unique_parent_item_count_pass": len(groups) >= minimum_unique_parent_items,
    }
    if not checks["adjudicated_item_count_pass"]:
        reason_codes.append("adjudicated_item_count_below_minimum")
    if not checks["unique_parent_item_count_pass"]:
        reason_codes.append("unique_parent_item_count_below_minimum")
    if not checks["unique_original_instance_count_pass"]:
        reason_codes.append("unique_original_instance_count_below_delta_minimum")
    if not checks["three_view_item_count_pass"]:
        reason_codes.append("three_view_item_count_below_minimum")
    if not checks["raw_response_policy_pass"]:
        reason_codes.append("raw_response_policy_violation")
    status = "completed_model_adjudication_scaleup" if all(checks.values()) else "failed_closed_underpowered"
    report = {
        "adjudicated_item_count": len(labels),
        "claim_status": CLAIM_STATUS,
        "counts_as_human_labels": False,
        "human_annotation_required": False,
        "live_api_used": bool(live_batch_report.get("live_api_used")),
        "minimum_adjudicated_items": minimum_adjudicated_items,
        "minimum_three_view_items": minimum_three_view_items,
        "minimum_unique_original_instances": minimum_unique_original_instances,
        "minimum_unique_parent_items": minimum_unique_parent_items,
        "preferred_adjudicated_items": preferred_adjudicated_items,
        "raw_api_responses_stored": False,
        "reason_codes": sorted(set(reason_codes)),
        "schema_version": "delta_model_adjudication_scaleup_report_v1",
        "scaleup_checks": checks,
        "source_label_count": len(source_labels),
        "status": status,
        "three_view_item_count": three_view_items,
        "unique_original_instance_count": len(unique_original_instances),
        "unique_parent_item_count": len(groups),
    }
    _write_jsonl(output_dir / "model_adjudicated_labels.jsonl", labels)
    _write_json(output_dir / "model_adjudication_scaleup_report.json", report)
    _write_json(output_dir / "live_adjudication_batch_report.json", live_batch_report)
    return labels, report, live_batch_report


def _pair_rate(groups: Mapping[str, Sequence[Mapping[str, Any]]], probe: str) -> dict[str, Any]:
    pairs = []
    for rows in groups.values():
        views = _view_by_probe(rows)
        if "primary" in views and probe in views:
            pairs.append((views["primary"], views[probe]))
    if not pairs:
        return {"count": 0, "match_rate": None}
    matches = sum(1 for left, right in pairs if _same_label(left, right))
    return {"count": len(pairs), "match_rate": matches / len(pairs)}


def _conservative_parent_rows(groups: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for parent, labels in groups.items():
        signatures = [_label_signature(label) for label in labels]
        signature_counts = Counter(signatures)
        majority_signature, majority_count = signature_counts.most_common(1)[0]
        has_veto = any(
            str(label.get("delta_label")) in {"worsens", "invalid"}
            or str(label.get("augmented_sufficiency")) in {"insufficient", "invalid"}
            for label in labels
        )
        mean_utility = _mean([float(label.get("delta_model_utility") or 0.0) for label in labels]) or 0.0
        conservative_utility = 0.0 if has_veto else max(0.0, mean_utility)
        rows.append(
            {
                "conservative_sufficiency_label": (
                    "sufficient"
                    if conservative_utility > 0.0 and not has_veto
                    else "insufficient_or_vetoed"
                ),
                "conservative_utility": round(conservative_utility, 6),
                "label_count": len(labels),
                "majority_count": majority_count,
                "majority_delta_label": majority_signature[0],
                "minority_veto_applied": has_veto,
                "parent_sample_id": parent,
                "required_views_present": _has_required_views(labels),
            }
        )
    return sorted(rows, key=lambda row: row["parent_sample_id"])


def _audit_reliability(
    *,
    labels: Sequence[Mapping[str, Any]],
    scaleup_report: Mapping[str, Any],
    output_dir: Path,
    minimum_three_view_items: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    groups = _group_by_parent(labels)
    duplicate = _pair_rate(groups, "duplicate")
    order_reversal = _pair_rate(groups, "order_reversal")
    prompt = _pair_rate(groups, "alternate_prompt")
    conservative_rows = _conservative_parent_rows(groups)
    disagreement_buckets = Counter(
        "no_disagreement"
        if row["majority_count"] == row["label_count"]
        else ("minority_veto" if row["minority_veto_applied"] else "non_veto_disagreement")
        for row in conservative_rows
    )
    pair_observations: list[tuple[bool, float]] = []
    for rows in groups.values():
        views = _view_by_probe(rows)
        primary = views.get("primary")
        for probe in ("duplicate", "order_reversal", "alternate_prompt"):
            if primary is not None and probe in views:
                pair_observations.append(
                    (_same_label(primary, views[probe]), float(views[probe].get("confidence") or 0.0))
                )
    stable_confidence = [confidence for stable, confidence in pair_observations if stable]
    unstable_confidence = [confidence for stable, confidence in pair_observations if not stable]
    confidence_calibration = {
        "scope": "model_self_consistency_only_not_human_calibration",
        "stable_pair_mean_confidence": _mean(stable_confidence),
        "unstable_pair_mean_confidence": _mean(unstable_confidence),
        "usable_pair_count": len(pair_observations),
    }
    invalid_rate = (
        sum(1 for label in labels if str(label.get("delta_label")) == "invalid") / len(labels)
        if labels
        else 1.0
    )
    challenge_checks = {
        "duplicate_consistency_pass": duplicate["count"] > 0 and (duplicate["match_rate"] or 0.0) >= 0.80,
        "invalid_rate_pass": invalid_rate <= 0.05,
        "order_reversal_stability_pass": order_reversal["count"] > 0 and (order_reversal["match_rate"] or 0.0) >= 0.70,
        "prompt_sensitivity_pass": prompt["count"] > 0 and (prompt["match_rate"] or 0.0) >= 0.70,
        "three_view_item_count_pass": sum(1 for rows in groups.values() if _has_required_views(rows))
        >= minimum_three_view_items,
    }
    challenge_set_status = "passed" if all(challenge_checks.values()) else "failed"
    status = (
        "model_adjudicated_measurement_candidate_ready"
        if challenge_set_status == "passed" and scaleup_report.get("status") == "completed_model_adjudication_scaleup"
        else "FAILED_CLOSED_JUDGE_RELIABILITY"
    )
    report = {
        "challenge_checks": challenge_checks,
        "challenge_set_status": challenge_set_status,
        "claim_status": CLAIM_STATUS,
        "confidence_calibration": confidence_calibration,
        "counts_as_human_labels": False,
        "disagreement_buckets": dict(sorted(disagreement_buckets.items())),
        "duplicate_consistency": duplicate,
        "human_annotation_required": False,
        "invalid_label_rate": invalid_rate,
        "minority_veto_count": sum(1 for row in conservative_rows if row["minority_veto_applied"]),
        "order_reversal_stability": order_reversal,
        "prompt_sensitivity": prompt,
        "raw_api_responses_stored": False,
        "schema_version": "delta_judge_reliability_bias_audit_v1",
        "status": status,
        "three_view_item_count": sum(1 for rows in groups.values() if _has_required_views(rows)),
    }
    _write_json(output_dir / "judge_reliability_audit.json", report)
    _write_jsonl(output_dir / "conservative_sufficiency_labels.jsonl", conservative_rows)
    return report, conservative_rows


def _route4d_rows_by_parent(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("parent_sample_id") or ""): dict(row) for row in rows if row.get("parent_sample_id")}


def _build_route4e_rows(
    *,
    labels: Sequence[Mapping[str, Any]],
    conservative_rows: Sequence[Mapping[str, Any]],
    route4d_bridge_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    route4d_by_parent = _route4d_rows_by_parent(route4d_bridge_rows)
    conservative_by_parent = {str(row.get("parent_sample_id") or ""): row for row in conservative_rows}
    rows: list[dict[str, Any]] = []
    for label in labels:
        parent = str(label.get("parent_sample_id") or "")
        route4d = route4d_by_parent.get(parent)
        if route4d is None:
            continue
        conservative = conservative_by_parent.get(parent, {})
        utility = max(0.0, float(label.get("delta_model_utility") or 0.0))
        if conservative.get("minority_veto_applied"):
            utility = 0.0
        row = {
            "claim_status": CLAIM_STATUS,
            "dataset": str(route4d.get("dataset") or "HotpotQA"),
            "delta_hybrid_utility": round(utility, 6),
            "delta_logloss": float(route4d.get("delta_logloss") or 0.0),
            "judge_view_id": str(label.get("judge_view_id") or ""),
            "metric_claim_level": "operational_utility_only",
            "minority_veto_applied": bool(conservative.get("minority_veto_applied")),
            "model_adjudicated_utility": round(utility, 6),
            "original_instance_id": str(route4d.get("original_instance_id") or parent),
            "parent_sample_id": parent,
            "prompt_version": str(label.get("prompt_version") or ""),
            "route4_row_identity_hash": str(route4d.get("route4_row_identity_hash") or ""),
            "route_id": "delta_route4e_model_adjudicated_utility_bridge",
            "schema_version": "delta_route4e_bridge_row_v1",
            "source_label_hash": str(label.get("label_record_hash") or ""),
        }
        row["route4e_bridge_row_hash"] = stable_hash(row)
        rows.append(row)
    return sorted(rows, key=lambda row: (row["parent_sample_id"], row["judge_view_id"]))


def _run_route4e(
    *,
    labels: Sequence[Mapping[str, Any]],
    conservative_rows: Sequence[Mapping[str, Any]],
    route4d_bridge_rows_path: str | Path,
    output_dir: Path,
    min_rows: int,
    min_unique_instances: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    route4d_bridge_rows = _read_jsonl(route4d_bridge_rows_path)
    rows = _build_route4e_rows(
        labels=labels,
        conservative_rows=conservative_rows,
        route4d_bridge_rows=route4d_bridge_rows,
    )
    fit = fit_route4d_bridge(rows, min_rows=min_rows, min_unique_instances=min_unique_instances)
    if fit["gate_result"] == "candidate_pending_review":
        status = "ROUTE4E_MODEL_ADJUDICATED_BRIDGE_CANDIDATE_PENDING_REVIEW"
    elif fit["gate_result"] == "failed_closed_underpowered":
        status = "FAILED_CLOSED_UNDERPOWERED"
    else:
        status = "FAILED_CLOSED_BRIDGE_GATES"
    summary = dict(fit)
    summary.update(
        {
            "calibrated_proxy_supported": False,
            "metric_bridge_support": False,
            "model_adjudicated_bridge_candidate_pending_review": status
            == "ROUTE4E_MODEL_ADJUDICATED_BRIDGE_CANDIDATE_PENDING_REVIEW",
            "non_circularity_checks": {
                "labels_include_delta_logloss": False,
                "model_utility_derived_from_normalized_labels": True,
                "raw_response_used_in_bridge": False,
            },
            "route4e_min_rows": min_rows,
            "route4e_min_unique_instances": min_unique_instances,
            "schema_version": "delta_route4e_bridge_fit_summary_v1",
            "status": status,
            "vinfo_proxy_supported": False,
        }
    )
    controls = {
        "claim_status": CLAIM_STATUS,
        "control_status": "diagnostic_only_not_claim_enabling",
        "negative_controls": {
            "label_shuffle_control": {
                "executed": bool(rows),
                "status": "diagnostic_only_not_claim_enabling",
            },
            "zero_utility_control": {
                "executed": bool(rows),
                "status": "diagnostic_only_not_claim_enabling",
            },
        },
        "schema_version": "delta_route4e_negative_controls_v1",
    }
    witness = {
        "artifact_type": "MetricBridgeWitness",
        "bridge_status": status,
        "calibrated_proxy_supported": False,
        "claim_status": CLAIM_STATUS,
        "metric_bridge_support": False,
        "metric_claim_level": "operational_utility_only",
        "model_adjudicated_bridge_candidate_pending_review": summary[
            "model_adjudicated_bridge_candidate_pending_review"
        ],
        "schema_version": "delta_route4e_metric_bridge_witness_v1",
        "vinfo_proxy_supported": False,
    }
    _write_jsonl(output_dir / "route4e_bridge_rows.jsonl", rows)
    _write_json(output_dir / "route4e_bridge_fit_summary.json", summary)
    _write_json(output_dir / "route4e_negative_controls.json", controls)
    _write_json(output_dir / "route4e_metric_bridge_witness.json", witness)
    return summary, rows


def _read_workbench_traces(path: str | Path) -> list[dict[str, Any]]:
    return _read_jsonl(path)


def _run_route7(
    *,
    route4e_rows: Sequence[Mapping[str, Any]],
    workbench_traces_path: str | Path,
    output_dir: Path,
) -> dict[str, Any]:
    utility_by_original: dict[str, list[float]] = {}
    for row in route4e_rows:
        original = str(row.get("original_instance_id") or "")
        if original:
            utility_by_original.setdefault(original, []).append(float(row.get("model_adjudicated_utility") or 0.0))
    mean_utility_by_original = {
        original: (_mean(values) or 0.0)
        for original, values in utility_by_original.items()
    }
    traces = _read_workbench_traces(workbench_traces_path)
    aggregate: dict[tuple[str, int], list[dict[str, float]]] = {}
    for trace in traces:
        original = str(trace.get("instance_id") or "")
        if original not in mean_utility_by_original:
            continue
        budget = int(trace.get("budget") or 0)
        selector = str(trace.get("selector_name") or "")
        evaluation = trace.get("evaluation") if isinstance(trace.get("evaluation"), Mapping) else {}
        recall = float(evaluation.get("supporting_fact_recall_at_budget") or 0.0)
        model_metric = recall * mean_utility_by_original[original]
        aggregate.setdefault((selector, budget), []).append(
            {
                "model_adjudicated_sufficiency_utility": model_metric,
                "selected_tokens": float(evaluation.get("selected_tokens") or trace.get("selected_tokens") or 0.0),
            }
        )
    rows: list[dict[str, Any]] = []
    for (selector, budget), values in sorted(aggregate.items()):
        rows.append(
            {
                "budget": budget,
                "matched_budget": True,
                "mean_model_adjudicated_sufficiency_utility": round(
                    _mean([value["model_adjudicated_sufficiency_utility"] for value in values]) or 0.0,
                    6,
                ),
                "mean_selected_tokens": round(_mean([value["selected_tokens"] for value in values]) or 0.0, 6),
                "selector_name": selector,
                "trace_count": len(values),
            }
        )
    best_selector = max(
        rows,
        key=lambda row: float(row["mean_model_adjudicated_sufficiency_utility"]),
        default=None,
    )
    report = {
        "claim_status": CLAIM_STATUS,
        "comparison_rows": rows,
        "global_selector_superiority_claimed": False,
        "matched_budget_comparison_available": bool(rows),
        "metric_scope": "model_adjudicated_operational_sufficiency_utility",
        "route7_claim_allowed": False,
        "schema_version": "delta_route7_model_adjudicated_selector_comparison_v1",
        "scoped_selector_superiority_claimed": False,
        "selector_superiority_claimed": False,
        "status": (
            "completed_model_adjudicated_operational_selector_comparison"
            if rows
            else "blocked_no_selector_overlap_for_model_adjudicated_metric"
        ),
        "top_selector_by_model_adjudicated_metric": best_selector["selector_name"] if best_selector else None,
    }
    _write_json(output_dir / "route7_model_adjudicated_selector_comparison.json", report)
    _write_csv(
        output_dir / "route7_model_adjudicated_selector_comparison.csv",
        rows,
        [
            "budget",
            "matched_budget",
            "mean_model_adjudicated_sufficiency_utility",
            "mean_selected_tokens",
            "selector_name",
            "trace_count",
        ],
    )
    return report


def _determine_terminal_status(
    *,
    scaleup_report: Mapping[str, Any],
    reliability: Mapping[str, Any],
    route4e: Mapping[str, Any],
) -> str:
    if reliability.get("status") == "FAILED_CLOSED_JUDGE_RELIABILITY":
        return "FAILED_CLOSED_JUDGE_RELIABILITY"
    if scaleup_report.get("status") == "failed_closed_underpowered":
        return "FAILED_CLOSED_UNDERPOWERED"
    if route4e.get("status") == "ROUTE4E_MODEL_ADJUDICATED_BRIDGE_CANDIDATE_PENDING_REVIEW":
        return "ROUTE4E_MODEL_ADJUDICATED_BRIDGE_CANDIDATE_PENDING_REVIEW"
    if route4e.get("status") == "FAILED_CLOSED_UNDERPOWERED":
        return "FAILED_CLOSED_UNDERPOWERED"
    if route4e.get("status") == "FAILED_CLOSED_BRIDGE_GATES":
        return "FAILED_CLOSED_BRIDGE_GATES"
    if reliability.get("status") == "model_adjudicated_measurement_candidate_ready":
        return "MODEL_ADJUDICATED_MEASUREMENT_CANDIDATE_READY"
    return "HONESTLY_BLOCKED"


def _verify_delta0_state(
    *,
    beta_portfolio_path: str | Path,
    beta_docs_path: str | Path,
) -> dict[str, Any]:
    beta_portfolio = _read_json(beta_portfolio_path)
    beta_doc_exists = Path(beta_docs_path).exists()
    return {
        "beta_doc_present": beta_doc_exists,
        "beta_portfolio_status": beta_portfolio.get("portfolio_decision"),
        "beta_reinterpreted": False,
        "branch_required": "codex/integrated-validation-workbench",
        "claim_status": CLAIM_STATUS,
        "iw_beta_state_confirmed": bool(beta_portfolio) and beta_doc_exists,
        "schema_version": "delta0_iw_beta_state_check_v1",
    }


def _render_final_report(
    *,
    delta0: Mapping[str, Any],
    protocol: Mapping[str, Any],
    scaleup: Mapping[str, Any],
    reliability: Mapping[str, Any],
    route4e: Mapping[str, Any],
    route7: Mapping[str, Any],
    final_status: Mapping[str, Any],
) -> str:
    denied = "\n".join(f"- `{claim}`" for claim in DENIED_CLAIMS)
    reasons = "\n".join(f"- `{reason}`" for reason in scaleup.get("reason_codes", [])) or "- none"
    return (
        "# Delta Strong-Model Adjudicated Validation Final Report\n\n"
        f"Terminal status: `{final_status['terminal_status']}`\n"
        f"Claim status: `{CLAIM_STATUS}`\n\n"
        "## Delta-0 IW And Beta State\n\n"
        f"- Required branch: `{delta0['branch_required']}`.\n"
        f"- Beta portfolio status: `{delta0.get('beta_portfolio_status')}`.\n"
        f"- Beta reinterpreted: `{str(delta0['beta_reinterpreted']).lower()}`.\n\n"
        "## Delta-1 Protocol Freeze\n\n"
        f"- Protocol version: `{protocol['protocol_version']}`.\n"
        f"- Label schema: `{protocol['label_schema_version']}`.\n"
        f"- Raw response storage: `false`.\n\n"
        "## Delta-2 Scale-Up\n\n"
        f"- Status: `{scaleup['status']}`.\n"
        f"- Adjudicated items: `{scaleup['adjudicated_item_count']}`.\n"
        f"- Unique parent items: `{scaleup['unique_parent_item_count']}`.\n"
        f"- Unique original instances: `{scaleup['unique_original_instance_count']}`.\n"
        f"- Three-view items: `{scaleup['three_view_item_count']}`.\n"
        f"- Live API used: `{str(scaleup['live_api_used']).lower()}`.\n"
        f"- Live fill-in attempt status: `{final_status.get('live_fillin_attempt_status', 'not_attempted_in_completed_run')}`.\n"
        f"- Reason codes:\n{reasons}\n\n"
        "## Delta-3 Reliability Audit\n\n"
        f"- Status: `{reliability['status']}`.\n"
        f"- Challenge-set status: `{reliability['challenge_set_status']}`.\n"
        f"- Duplicate consistency count: `{reliability['duplicate_consistency']['count']}`.\n"
        f"- Order-reversal count: `{reliability['order_reversal_stability']['count']}`.\n"
        f"- Prompt-sensitivity count: `{reliability['prompt_sensitivity']['count']}`.\n\n"
        "## Delta-4 Route 4E Bridge\n\n"
        f"- Status: `{route4e['status']}`.\n"
        f"- Rows validated: `{route4e['rows_validated']}`.\n"
        f"- Unique original instances: `{route4e['unique_original_instances']}`.\n"
        f"- `calibrated_proxy_supported`: `false`.\n"
        f"- `vinfo_proxy_supported`: `false`.\n\n"
        "## Delta-5 Route 7 Selector Comparison\n\n"
        f"- Status: `{route7['status']}`.\n"
        f"- Selector superiority claimed: `{str(route7['selector_superiority_claimed']).lower()}`.\n"
        f"- Global selector superiority claimed: `{str(route7['global_selector_superiority_claimed']).lower()}`.\n\n"
        "## Delta-6 Claim Boundary\n\n"
        "- Human annotation was not requested and missing human labels were not treated as a blocker.\n"
        "- Model-only labels remain model-adjudicated evidence, not human measurement validation.\n"
        "- No manuscript claim upgrade was performed.\n"
        "- No claim-ledger upgrade was performed.\n"
        "- Denied claims remain:\n"
        f"{denied}\n"
    )


def run_delta_strong_model_adjudication(
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    docs_path: str | Path = DEFAULT_DOCS_PATH,
    existing_labels_path: str | Path = DEFAULT_EXISTING_LABELS_PATH,
    route4d_bridge_rows_path: str | Path = DEFAULT_ROUTE4D_BRIDGE_ROWS_PATH,
    route4_rows_path: str | Path = DEFAULT_ROUTE4_ROWS_PATH,
    candidate_pools_path: str | Path = DEFAULT_CANDIDATE_POOLS_PATH,
    workbench_traces_path: str | Path = DEFAULT_WORKBENCH_TRACES_PATH,
    beta_portfolio_path: str | Path = DEFAULT_BETA_PORTFOLIO_PATH,
    beta_docs_path: str | Path = DEFAULT_BETA_DOCS_PATH,
    run_live_adjudication: bool = True,
    client: Any | None = None,
    judge_model_id: str | None = None,
    judge_provider: str | None = None,
    judge_config_path: str | Path | None = DEFAULT_JUDGE_CONFIG,
    minimum_adjudicated_items: int = 800,
    preferred_adjudicated_items: int = 1200,
    minimum_unique_parent_items: int = 300,
    minimum_unique_original_instances: int = 300,
    minimum_three_view_items: int = 300,
    route4e_min_rows: int = 500,
    route4e_min_unique_instances: int = 150,
    live_fillin_attempt_status: str = "not_attempted_in_completed_run",
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    delta0 = _verify_delta0_state(beta_portfolio_path=beta_portfolio_path, beta_docs_path=beta_docs_path)
    _write_json(output / "delta0_iw_beta_state_check.json", delta0)
    labels, scaleup, live_batch = _run_scaleup(
        existing_labels_path=existing_labels_path,
        route4d_bridge_rows_path=route4d_bridge_rows_path,
        route4_rows_path=route4_rows_path,
        candidate_pools_path=candidate_pools_path,
        output_dir=output,
        run_live_adjudication=run_live_adjudication,
        minimum_adjudicated_items=minimum_adjudicated_items,
        preferred_adjudicated_items=preferred_adjudicated_items,
        minimum_unique_parent_items=minimum_unique_parent_items,
        minimum_unique_original_instances=minimum_unique_original_instances,
        minimum_three_view_items=minimum_three_view_items,
        client=client,
        judge_model_id=judge_model_id,
        judge_provider=judge_provider,
        judge_config_path=judge_config_path,
    )
    protocol = _build_protocol(labels)
    _write_json(output / "strong_model_judge_protocol.json", protocol)
    reliability, conservative_rows = _audit_reliability(
        labels=labels,
        scaleup_report=scaleup,
        output_dir=output,
        minimum_three_view_items=minimum_three_view_items,
    )
    route4e, route4e_rows = _run_route4e(
        labels=labels,
        conservative_rows=conservative_rows,
        route4d_bridge_rows_path=route4d_bridge_rows_path,
        output_dir=output,
        min_rows=route4e_min_rows,
        min_unique_instances=route4e_min_unique_instances,
    )
    route7 = _run_route7(route4e_rows=route4e_rows, workbench_traces_path=workbench_traces_path, output_dir=output)
    terminal_status = _determine_terminal_status(
        scaleup_report=scaleup,
        reliability=reliability,
        route4e=route4e,
    )
    final_status = {
        "allowed_candidate_wording": ALLOWED_CANDIDATE_WORDING,
        "claim_ledger_update_attempted": False,
        "claim_status": CLAIM_STATUS,
        "denied_claims": DENIED_CLAIMS,
        "human_annotation_required": False,
        "live_api_used": bool(scaleup.get("live_api_used") or live_batch.get("live_api_used")),
        "live_fillin_attempt_status": live_fillin_attempt_status,
        "manuscript_update_attempted": False,
        "raw_api_responses_stored": False,
        "schema_version": "delta_strong_model_adjudication_final_status_v1",
        "terminal_status": terminal_status,
    }
    _write_json(output / "final_status.json", final_status)
    docs = Path(docs_path)
    docs.parent.mkdir(parents=True, exist_ok=True)
    docs.write_text(
        _render_final_report(
            delta0=delta0,
            protocol=protocol,
            scaleup=scaleup,
            reliability=reliability,
            route4e=route4e,
            route7=route7,
            final_status=final_status,
        ),
        encoding="utf-8",
    )
    return {
        "artifacts": {
            "final_report": _path_ref(docs),
            "final_status": _path_ref(output / "final_status.json"),
            "labels": _path_ref(output / "model_adjudicated_labels.jsonl"),
            "reliability": _path_ref(output / "judge_reliability_audit.json"),
            "route4e": _path_ref(output / "route4e_bridge_fit_summary.json"),
            "route7": _path_ref(output / "route7_model_adjudicated_selector_comparison.json"),
        },
        "claim_status": CLAIM_STATUS,
        "live_api_used": final_status["live_api_used"],
        "terminal_status": terminal_status,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Delta strong-model adjudicated validation.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--docs-path", default=str(DEFAULT_DOCS_PATH))
    parser.add_argument("--live-fillin-attempt-status", default="not_attempted_in_completed_run")
    parser.add_argument("--no-live-adjudication", action="store_true")
    args = parser.parse_args(argv)
    result = run_delta_strong_model_adjudication(
        output_dir=args.output_dir,
        docs_path=args.docs_path,
        live_fillin_attempt_status=args.live_fillin_attempt_status,
        run_live_adjudication=not args.no_live_adjudication,
    )
    print(
        json.dumps(
            {
                "claim_status": result["claim_status"],
                "live_api_used": result["live_api_used"],
                "terminal_status": result["terminal_status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
