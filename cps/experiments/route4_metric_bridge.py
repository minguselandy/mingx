from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.hashing import canonical_json_dumps
from cps.benchmarks.hashing import stable_hash
from cps.experiments.route4_sufficiency_utility import UTILITY_DEFINITION
from cps.experiments.route4_sufficiency_utility import UTILITY_SOURCE
from cps.experiments.route4_sufficiency_utility import compute_hotpotqa_sufficiency_utility
from cps.experiments.route4_sufficiency_utility import hotpotqa_packet_lookup


ROUTE4_ID = "route4_metric_bridge_redesign"
ROUTE4_PHASE_ID = "route4a_hotpotqa_sufficiency_pilot"
ROUTE4_PROTOCOL_ID = "route4a_hotpotqa_sufficiency_answer_nll_v1"
ACTIVE_STRATUM = "route4_hotpotqa_sufficiency_grounded_bridge_v1"
TASK_FAMILY = "hotpotqa_answer_support_sufficiency_bridge"
DATASET = "HotpotQA"
SPLIT = "dev_distractor"
TARGET_REPRESENTATION = "hotpotqa_canonical_answer_string"
UTILITY_TARGET_ID = "hotpotqa_answer_support_sufficiency"
MODEL_TIER = "approved_live_logprob_model_v1"
MATERIALIZATION_POLICY = "fixed_selector_order_with_source_boundaries"
CANDIDATE_SLICE_BAND = "route4_hotpotqa_sufficiency_existing_answer_nll_v1"
DECODING_POLICY = "deterministic_logprob_scoring_v1"
BUDGET = 512
SPLIT_ID = "route4_original_instance_hash_70_30_v1"
REPLICATE_COUNT_POLICY = "single_replicate_existing_approved_delta_record"
HELDOUT_FRACTION = 0.30
MIN_PILOT_ROWS = 500
MIN_UNIQUE_INSTANCES = 150
MIN_ESS = 100
MIN_SIGN_AGREEMENT = 0.70
MIN_SPEARMAN = 0.40
MAX_NORMALIZED_RESIDUAL = 0.50
CLAIM_STATUS = "no_claim_upgrade"

DEFAULT_OUTPUT_DIR = "artifacts/experiments/route4_bridge"
DEFAULT_CANDIDATE_POOLS_PATH = "artifacts/benchmarks/hotpotqa_candidate_pools.jsonl"
DEFAULT_HOTPOTQA_DELTA_RECORDS_PATH = "artifacts/benchmarks/hotpotqa_p55_delta_records.jsonl"
DEFAULT_HOTPOTQA_GENERATION_REPORT_PATH = "artifacts/benchmarks/hotpotqa_p55_delta_generation_report.json"
DEFAULT_FEVER_CANDIDATE_POOLS_PATH = "artifacts/benchmarks/fever_candidate_pools.jsonl"
DEFAULT_FEVER_DELTA_RECORDS_PATH = "artifacts/benchmarks/fever_p55_delta_records.jsonl"
DEFAULT_REPORT_MD = "docs/experiments/Route4-metric-bridge-redesign-execution.md"


REQUIRED_IDENTITY_FIELDS = (
    "route_id",
    "phase_id",
    "active_stratum",
    "task_family",
    "dataset",
    "split",
    "instance_id",
    "original_instance_id",
    "candidate_pool_hash",
    "context_L_packet_ids",
    "block_A_packet_ids",
    "target_y",
    "utility_target_id",
    "target_representation",
    "model_tier",
    "materialization_policy",
    "candidate_slice_band",
    "block_size",
    "budget",
    "decoding_policy",
    "evaluator_id",
    "utility_definition",
    "delta_utility_source",
    "replicate_count_policy",
    "split_id",
    "heldout_flag",
    "protocol_id",
)


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
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


def write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def write_jsonl(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(canonical_json_dumps(dict(row)) + "\n" for row in rows), encoding="utf-8")
    return output_path


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.as_posix() if not candidate.is_absolute() else candidate.name


def _safe_count_jsonl(path: str | Path) -> int:
    candidate = Path(path)
    if not candidate.exists():
        return 0
    return len(read_jsonl(candidate))


def _packet_id(packet: Mapping[str, Any]) -> str:
    return str(packet.get("packet_id") or "").strip()


def _source_doc_id(packet: Mapping[str, Any]) -> str:
    return str(packet.get("source_doc_id") or (packet.get("provenance") or {}).get("source_doc_id") or "").strip()


def _pool_hash(pool: Mapping[str, Any]) -> str:
    return str((pool.get("candidate_pool") or {}).get("candidate_pool_hash") or "").strip()


def _target_y(pool: Mapping[str, Any]) -> str:
    return str((pool.get("target") or {}).get("label") or "").strip()


def _pool_packets(pool: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [dict(packet) for packet in (pool.get("candidate_pool") or {}).get("packets") or []]


def _pool_by_key(candidate_pools: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(pool.get("instance_id") or ""), _pool_hash(pool)): dict(pool) for pool in candidate_pools}


def inspect_dataset_readiness(
    *,
    fever_candidate_pools_path: str | Path = DEFAULT_FEVER_CANDIDATE_POOLS_PATH,
    fever_delta_records_path: str | Path = DEFAULT_FEVER_DELTA_RECORDS_PATH,
    hotpotqa_candidate_pools_path: str | Path = DEFAULT_CANDIDATE_POOLS_PATH,
    hotpotqa_delta_records_path: str | Path = DEFAULT_HOTPOTQA_DELTA_RECORDS_PATH,
) -> dict[str, Any]:
    fever_candidate_count = _safe_count_jsonl(fever_candidate_pools_path)
    fever_delta_count = _safe_count_jsonl(fever_delta_records_path)
    hotpotqa_candidate_count = _safe_count_jsonl(hotpotqa_candidate_pools_path)
    hotpotqa_delta_count = _safe_count_jsonl(hotpotqa_delta_records_path)
    hotpotqa_rows = read_jsonl(hotpotqa_candidate_pools_path) if hotpotqa_candidate_count else []
    hotpotqa_hashes = sum(1 for row in hotpotqa_rows if _pool_hash(row))
    hotpotqa_with_gold = sum(
        1
        for row in hotpotqa_rows
        if any(str(packet.get("gold_support_label") or "") == "gold_supporting" for packet in _pool_packets(row))
    )
    available: list[str] = []
    blocked: dict[str, Any] = {}
    if fever_candidate_count and fever_delta_count:
        available.append("FEVER")
    else:
        blocked["FEVER"] = {
            "blocker": "blocked_dataset_incomplete",
            "candidate_pool_count": fever_candidate_count,
            "delta_record_count": fever_delta_count,
            "missing_inputs": [
                name
                for name, count in (
                    ("fever_candidate_pools", fever_candidate_count),
                    ("fever_p55_delta_records", fever_delta_count),
                )
                if count == 0
            ],
        }
    if hotpotqa_candidate_count and hotpotqa_delta_count:
        available.append("HotpotQA")
    else:
        blocked["HotpotQA"] = {
            "blocker": "blocked_dataset_incomplete",
            "candidate_pool_count": hotpotqa_candidate_count,
            "delta_record_count": hotpotqa_delta_count,
        }
    return {
        "available_strata": available,
        "blocked_strata": blocked,
        "claim_status": CLAIM_STATUS,
        "phase": "Route4-dataset-readiness",
        "strata": {
            "FEVER": {
                "candidate_pool_count": fever_candidate_count,
                "can_support_future_confirmatory_rows": fever_candidate_count >= 150 and fever_delta_count >= 500,
                "can_support_pilot_rows": bool(fever_candidate_count and fever_delta_count),
                "delta_record_count": fever_delta_count,
                "source_paths": {
                    "candidate_pools": _path_ref(fever_candidate_pools_path),
                    "delta_records": _path_ref(fever_delta_records_path),
                },
            },
            "HotpotQA": {
                "candidate_pool_count": hotpotqa_candidate_count,
                "candidate_pool_hashes_present": hotpotqa_hashes,
                "can_support_future_confirmatory_rows": hotpotqa_candidate_count >= 150 and hotpotqa_delta_count >= 500,
                "can_support_pilot_rows": bool(hotpotqa_candidate_count and hotpotqa_delta_count),
                "delta_record_count": hotpotqa_delta_count,
                "gold_evidence_coverage_count": hotpotqa_with_gold,
                "missing_gold_or_evidence_coverage": hotpotqa_candidate_count - hotpotqa_with_gold,
                "source_paths": {
                    "candidate_pools": _path_ref(hotpotqa_candidate_pools_path),
                    "delta_records": _path_ref(hotpotqa_delta_records_path),
                },
            },
        },
    }


def _load_env_keys(env_path: str | Path | None) -> set[str]:
    keys: set[str] = set()
    if env_path is None:
        return keys
    path = Path(env_path)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                keys.add(stripped.split("=", 1)[0].strip())
    return keys


def inspect_evaluator_readiness(
    *,
    hotpotqa_generation_report_path: str | Path = DEFAULT_HOTPOTQA_GENERATION_REPORT_PATH,
    env_path: str | Path | None = ".env",
) -> dict[str, Any]:
    path = Path(hotpotqa_generation_report_path)
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    evaluator = dict(payload.get("evaluator") or {})
    env_keys = _load_env_keys(env_path)
    logprobs_supported = bool(evaluator.get("logprobs_supported"))
    approved = bool(payload.get("delta_records_validated")) and logprobs_supported
    return {
        "approved_scoring_backend_found": approved,
        "claim_status": CLAIM_STATUS,
        "deterministic_scoring_settings": {
            "decoding_policy": evaluator.get("decoding_policy", DECODING_POLICY),
            "enable_thinking": evaluator.get("enable_thinking", False),
            "temperature": evaluator.get("temperature", 0),
            "top_logprobs": evaluator.get("top_logprobs", 0),
            "top_p": evaluator.get("top_p", 1),
        },
        "evaluator_id": evaluator.get("evaluator_id"),
        "expected_target_representation": TARGET_REPRESENTATION,
        "fail_closed_behavior": "blocked_evaluator_unavailable_if_existing_approved_delta_records_absent_or_logprobs_unsupported",
        "credential_base_url_configured": "DASHSCOPE_BASE_URL" in env_keys,
        "credential_config_detected": bool(env_keys.intersection({"API_KEY", "DASHSCOPE_API_KEY"})),
        "model_name": evaluator.get("model_name"),
        "no_raw_api_dump_policy": True,
        "phase": "Route4-evaluator-readiness",
        "provider": evaluator.get("provider"),
        "scoring_source": "existing_approved_hotpotqa_delta_records" if approved else "blocked_evaluator_unavailable",
        "token_logprobs_available": logprobs_supported,
    }


def _heldout_original_ids(original_ids: Sequence[str], heldout_fraction: float = HELDOUT_FRACTION) -> set[str]:
    ordered = sorted(set(original_ids), key=stable_hash)
    heldout_count = max(1, math.ceil(len(ordered) * heldout_fraction)) if ordered else 0
    return set(ordered[-heldout_count:])


def _route4_instance_id(original_id: str, context_ids: Sequence[str], block_ids: Sequence[str]) -> str:
    suffix = stable_hash({"block_A_packet_ids": list(block_ids), "context_L_packet_ids": list(context_ids)})[:16]
    return f"{original_id}::route4::{suffix}"


def _materialized_context_hash(context_ids: Sequence[str], block_ids: Sequence[str]) -> str:
    return stable_hash({"block_A_packet_ids": list(block_ids), "context_L_packet_ids": list(context_ids)})


def build_route4_rows_from_hotpotqa_delta_records(
    candidate_pools: Sequence[Mapping[str, Any]],
    delta_records: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pools = _pool_by_key(candidate_pools)
    originals = [str(record.get("instance_id") or "") for record in delta_records if str(record.get("instance_id") or "")]
    heldout_ids = _heldout_original_ids(originals)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, record in enumerate(delta_records, start=1):
        if record.get("dataset") != DATASET:
            errors.append(f"delta_row_{index}:wrong_dataset")
            continue
        original_id = str(record.get("instance_id") or "")
        candidate_pool_hash = str(record.get("candidate_pool_hash") or "")
        pool = pools.get((original_id, candidate_pool_hash))
        if pool is None:
            errors.append(f"delta_row_{index}:candidate_pool_not_found")
            continue
        context_ids = tuple(str(packet_id) for packet_id in record.get("context_L_packet_ids") or [])
        block_ids = tuple(str(packet_id) for packet_id in record.get("block_A_packet_ids") or [])
        try:
            utility = compute_hotpotqa_sufficiency_utility(pool, context_ids=context_ids, block_ids=block_ids)
        except ValueError as exc:
            errors.append(f"delta_row_{index}:{exc}")
            continue
        row = {
            "active_stratum": ACTIVE_STRATUM,
            "augmented_utility": utility.augmented_utility,
            "baseline_utility": utility.baseline_utility,
            "block_A_packet_ids": list(block_ids),
            "block_size": len(block_ids),
            "budget": BUDGET,
            "candidate_pool_hash": candidate_pool_hash,
            "candidate_slice_band": CANDIDATE_SLICE_BAND,
            "contamination_status": str(record.get("contamination_status") or "clean"),
            "context_L_packet_ids": list(context_ids),
            "dataset": DATASET,
            "decoding_policy": str(record.get("decoding_policy") or DECODING_POLICY),
            "delta_logloss": float(record["delta_logloss"]),
            "delta_logloss_source": "existing_approved_hotpotqa_answer_nll_delta_record",
            "delta_utility": utility.delta_utility,
            "delta_utility_source": UTILITY_SOURCE,
            "evaluator_id": str(record.get("evaluator_id") or ""),
            "full_support_hit_delta": utility.full_support_hit_delta,
            "heldout_flag": original_id in heldout_ids,
            "instance_id": _route4_instance_id(original_id, context_ids, block_ids),
            "materialization_policy": str(record.get("materialization_policy") or MATERIALIZATION_POLICY),
            "materialized_context_hash": _materialized_context_hash(context_ids, block_ids),
            "model_tier": str(record.get("model_tier") or MODEL_TIER),
            "negative_control_group": "primary",
            "non_circularity_flags": {"utility_source_verified": True},
            "original_instance_id": original_id,
            "phase_id": ROUTE4_PHASE_ID,
            "protocol_id": ROUTE4_PROTOCOL_ID,
            "replicate_count": int(record.get("replicate_count") or 1),
            "replicate_count_policy": REPLICATE_COUNT_POLICY,
            "route_id": ROUTE4_ID,
            "split": SPLIT,
            "split_id": SPLIT_ID,
            "sufficiency_level_augmented": utility.sufficiency_level_augmented,
            "sufficiency_level_baseline": utility.sufficiency_level_baseline,
            "support_coverage_delta": utility.evidence_coverage_delta,
            "source_coverage_delta": utility.source_coverage_delta,
            "missing_prerequisite_delta": utility.missing_prerequisite_delta,
            "contradiction_penalty_delta": utility.contradiction_penalty_delta,
            "target_representation": TARGET_REPRESENTATION,
            "target_y": str(record.get("target_y") or _target_y(pool)),
            "task_family": TASK_FAMILY,
            "utility_target_id": UTILITY_TARGET_ID,
            "utility_definition": UTILITY_DEFINITION,
            "utility_source_provenance": utility.utility_source_provenance,
            "validation_failure_reason": None,
        }
        rows.append(row)
    rows = sorted(rows, key=route4_row_identity)
    return rows, {
        "generation_errors": errors,
        "rows_generated": len(rows),
        "rows_skipped": len(delta_records) - len(rows),
        "source_delta_records": len(delta_records),
    }


def route4_row_identity(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(
        tuple(record[field]) if field in {"context_L_packet_ids", "block_A_packet_ids"} else record[field]
        for field in REQUIRED_IDENTITY_FIELDS
    )


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def validate_route4_rows(rows: Sequence[Mapping[str, Any]], candidate_pools: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    packet_ids_by_pool: dict[str, set[str]] = {
        _pool_hash(pool): set(hotpotqa_packet_lookup(pool).keys()) for pool in candidate_pools
    }
    seen: set[tuple[Any, ...]] = set()
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        prefix = f"row_{index}:"
        for field in REQUIRED_IDENTITY_FIELDS:
            if field not in row or row[field] in (None, ""):
                errors.append(prefix + f"missing_{field}")
        if not isinstance(row.get("block_A_packet_ids"), list) or not row.get("block_A_packet_ids"):
            errors.append(prefix + "empty_block_A_packet_ids")
        try:
            identity = route4_row_identity(row)
        except KeyError as exc:
            errors.append(prefix + f"missing_{exc.args[0]}")
            continue
        if identity in seen:
            errors.append(prefix + "duplicate_row_identity")
        seen.add(identity)
        known_packets = packet_ids_by_pool.get(str(row.get("candidate_pool_hash") or ""), set())
        if not known_packets:
            errors.append(prefix + "candidate_pool_hash_not_found")
        for packet_id in [*(row.get("context_L_packet_ids") or []), *(row.get("block_A_packet_ids") or [])]:
            if packet_id not in known_packets:
                errors.append(prefix + "packet_id_not_in_candidate_pool")
        if not row.get("utility_source_provenance"):
            errors.append(prefix + "missing_utility_source_provenance")
        if row.get("delta_utility_source") != UTILITY_SOURCE:
            errors.append(prefix + "ambiguous_delta_utility_source")
        if not row.get("target_y"):
            errors.append(prefix + "missing_target_y")
        if "delta_logloss" in row and not row.get("evaluator_id"):
            errors.append(prefix + "missing_evaluator_id")
        delta_logloss = _finite_float(row.get("delta_logloss"))
        delta_utility = _finite_float(row.get("delta_utility"))
        if delta_logloss is None:
            errors.append(prefix + "delta_logloss_not_numeric")
        if delta_utility is None:
            errors.append(prefix + "delta_utility_not_numeric")
        if delta_logloss is not None and delta_utility is not None and abs(delta_logloss - delta_utility) <= 1e-12:
            errors.append(prefix + "delta_utility_equals_delta_logloss")
    return {
        "errors": errors,
        "rows_generated": len(rows),
        "rows_validated": 0 if errors else len(rows),
        "schema_valid": not errors,
    }


def _mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _average_ranks(values: Sequence[float]) -> list[float]:
    ordered = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][0] == ordered[index][0]:
            end += 1
        rank = (index + 1 + end) / 2.0
        for _, original_index in ordered[index:end]:
            ranks[original_index] = rank
        index = end
    return ranks


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2:
        return None
    x_mean = _mean(xs)
    y_mean = _mean(ys)
    if x_mean is None or y_mean is None:
        return None
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = math.sqrt(sum((x - x_mean) ** 2 for x in xs) * sum((y - y_mean) ** 2 for y in ys))
    return None if denominator == 0 else numerator / denominator


def _spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    return _pearson(_average_ranks(xs), _average_ranks(ys)) if len(xs) >= 2 and len(ys) >= 2 else None


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _affine_transform_detected(xs: Sequence[float], ys: Sequence[float]) -> bool:
    if len(xs) < 3 or len(set(xs)) < 2:
        return False
    x_mean = _mean(xs)
    y_mean = _mean(ys)
    if x_mean is None or y_mean is None:
        return False
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return False
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator
    intercept = y_mean - slope * x_mean
    return all(abs((slope * x + intercept) - y) <= 1e-9 for x, y in zip(xs, ys))


def _rounded_equality_detected(xs: Sequence[float], ys: Sequence[float]) -> bool:
    return any(all(round(x, digits) == y for x, y in zip(xs, ys)) for digits in range(13))


def _rank_identity_detected(xs: Sequence[float], ys: Sequence[float]) -> bool:
    return len(xs) >= 3 and _average_ranks(xs) == _average_ranks(ys)


def non_circularity_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    xs = [float(row["delta_logloss"]) for row in rows]
    ys = [float(row["delta_utility"]) for row in rows]
    equality_count = sum(abs(x - y) <= 1e-12 for x, y in zip(xs, ys))
    return {
        "affine_transform_detected": _affine_transform_detected(xs, ys),
        "exact_equality_detected": equality_count == len(rows) if rows else False,
        "fraction_delta_utility_equals_delta_logloss": equality_count / len(rows) if rows else 0.0,
        "pearson_delta_utility_delta_logloss": _pearson(xs, ys),
        "rank_identity_detected": _rank_identity_detected(xs, ys),
        "rounded_equality_detected": _rounded_equality_detected(xs, ys),
        "spearman_delta_utility_delta_logloss": _spearman(xs, ys),
        "utility_source_verified": all(row.get("delta_utility_source") == UTILITY_SOURCE for row in rows),
    }


def split_manifest(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    originals = {str(row["original_instance_id"]) for row in rows}
    heldout = {str(row["original_instance_id"]) for row in rows if row["heldout_flag"]}
    return {
        "heldout_fraction_by_original_instance": len(heldout) / len(originals) if originals else 0.0,
        "heldout_original_instances": len(heldout),
        "heldout_rows": sum(1 for row in rows if row["heldout_flag"]),
        "split_id": SPLIT_ID,
        "split_unit": "original_instance_id",
        "train_original_instances": len(originals - heldout),
        "train_rows": sum(1 for row in rows if not row["heldout_flag"]),
        "unique_original_instances": len(originals),
    }


def _through_origin_scale(rows: Sequence[Mapping[str, Any]]) -> float | None:
    denominator = sum(float(row["delta_logloss"]) ** 2 for row in rows)
    if denominator == 0:
        return None
    numerator = sum(float(row["delta_logloss"]) * float(row["delta_utility"]) for row in rows)
    return numerator / denominator


def _metric_summary(xs: Sequence[float], ys: Sequence[float]) -> dict[str, Any]:
    return {
        "pearson": _pearson(xs, ys),
        "sign_agreement": sum(_sign(x) == _sign(y) for x, y in zip(xs, ys)) / len(xs) if xs else None,
        "spearman": _spearman(xs, ys),
    }


def fit_route4_calibration(
    rows: Sequence[Mapping[str, Any]],
    *,
    min_rows: int = MIN_PILOT_ROWS,
    min_unique_instances: int = MIN_UNIQUE_INSTANCES,
) -> dict[str, Any]:
    unique_instances = len({row["original_instance_id"] for row in rows})
    if len(rows) < min_rows or unique_instances < min_unique_instances:
        return {
            "calibration_run": False,
            "claim_status": CLAIM_STATUS,
            "gate_result": "failed_closed_below_min_rows",
            "metric_claim_level": "failed_closed_no_claim_upgrade",
            "reason_codes": [
                reason
                for reason, failed in (
                    ("rows_validated_below_min_rows", len(rows) < min_rows),
                    ("unique_original_instances_below_minimum", unique_instances < min_unique_instances),
                )
                if failed
            ],
            "rows_validated": len(rows),
            "unique_original_instances": unique_instances,
        }
    train = [row for row in rows if not row["heldout_flag"]]
    heldout = [row for row in rows if row["heldout_flag"]]
    c_hat = _through_origin_scale(train)
    predictions: list[float] = []
    actuals: list[float] = []
    residuals: list[float] = []
    if c_hat is not None:
        for row in heldout:
            predicted = c_hat * float(row["delta_logloss"])
            actual = float(row["delta_utility"])
            predictions.append(predicted)
            actuals.append(actual)
            residuals.append(abs(actual - predicted))
    zeta = max(residuals) if residuals else None
    mean_abs_utility = _mean([abs(float(row["delta_utility"])) for row in heldout])
    normalized = zeta / max(mean_abs_utility or 0.0, 1e-12) if zeta is not None else None
    sign_agreement = (
        sum(_sign(float(row["delta_logloss"])) == _sign(float(row["delta_utility"])) for row in heldout) / len(heldout)
        if heldout
        else None
    )
    spearman_rho = _spearman(predictions, actuals)
    ess = sum(int(row.get("replicate_count") or 1) for row in rows)
    split = split_manifest(rows)
    flags = {
        "effective_sample_size_pass": ess >= MIN_ESS,
        "heldout_fraction_pass": split["heldout_fraction_by_original_instance"] >= HELDOUT_FRACTION,
        "normalized_residual_pass": normalized is not None and normalized <= MAX_NORMALIZED_RESIDUAL,
        "row_count_pass": len(rows) >= min_rows,
        "sign_agreement_pass": sign_agreement is not None and sign_agreement >= MIN_SIGN_AGREEMENT,
        "spearman_rho_pass": spearman_rho is not None and spearman_rho >= MIN_SPEARMAN,
        "unique_instance_pass": unique_instances >= min_unique_instances,
    }
    gate_result = (
        "metric_bridge_support_candidate_pending_independent_validation"
        if all(flags.values())
        else "failed_closed_gate_failed"
    )
    return {
        "bridge_fit": {
            "c_hat_s": c_hat,
            "fit_method": "original_instance_split_ols_through_origin",
            "normalized_residual": normalized,
            "spearman_rho": spearman_rho,
            "zeta_hat_s": zeta,
        },
        "calibration_run": True,
        "claim_status": CLAIM_STATUS,
        "effective_sample_size": ess,
        "gate_pass_flags": flags,
        "gate_result": gate_result,
        "heldout_fraction": split["heldout_fraction_by_original_instance"],
        "heldout_rows": len(heldout),
        "metric_claim_level": (
            "metric_bridge_support_candidate_pending_independent_validation"
            if all(flags.values())
            else "failed_closed_no_claim_upgrade"
        ),
        "reason_codes": sorted(key.replace("_pass", "_failed") for key, value in flags.items() if not value),
        "rows_validated": len(rows),
        "sign_agreement": sign_agreement,
        "train_rows": len(train),
        "unique_original_instances": unique_instances,
    }


def negative_control_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    xs = [float(row["delta_logloss"]) for row in rows]
    ys = [float(row["delta_utility"]) for row in rows]
    shuffled_logloss = list(reversed(xs))
    wrong_instance_utility = ys[1:] + ys[:1] if ys else []
    random_scores = [(int(stable_hash(route4_row_identity(row))[:8], 16) / 0xFFFFFFFF) * 2 - 1 for row in rows]
    length_scores = [float(sum(len(packet_id) for packet_id in row["block_A_packet_ids"])) for row in rows]
    packet_count_scores = [float(row["block_size"]) for row in rows]
    utility_shuffled = list(reversed(ys))
    return {
        "length_only_baseline": _metric_summary(length_scores, ys),
        "packet_count_only_baseline": _metric_summary(packet_count_scores, ys),
        "random_score_baseline": _metric_summary(random_scores, ys),
        "shuffled_delta_logloss_within_stratum_split": _metric_summary(shuffled_logloss, ys),
        "utility_shuffled_control": _metric_summary(xs, utility_shuffled),
        "wrong_instance_join": _metric_summary(xs, wrong_instance_utility),
    }


def _write_execution_doc(path: str | Path, payload: Mapping[str, Any]) -> Path:
    lines = [
        "# Route 4 Metric-bridge Redesign Execution",
        "",
        "Status: Route 4A HotpotQA sufficiency-grounded pilot",
        f"Claim status: `{CLAIM_STATUS}`",
        "",
        "## Dataset Readiness",
        "",
        "- FEVER is recorded as blocked when complete candidate pools and evaluator records are absent.",
        "- HotpotQA uses existing real candidate pools and approved answer-NLL delta records.",
        "",
        "## Evaluator Readiness",
        "",
        "- Scoring source: existing approved HotpotQA answer-NLL delta records from the bounded live logprob endpoint.",
        "- No raw API responses are written.",
        "",
        "## Utility Definition",
        "",
        f"- Utility definition: `{UTILITY_DEFINITION}`",
        f"- Utility source: `{UTILITY_SOURCE}`",
        "- Utility uses gold support packet IDs and source document IDs only.",
        "- Utility does not use NLL, logprobs, model probabilities, ranks, clipping, rounding, or affine transforms.",
        "",
        "## Pilot Result",
        "",
        f"- Rows attempted: `{payload.get('rows_attempted')}`",
        f"- Rows validated: `{payload.get('rows_validated')}`",
        f"- Unique original instances: `{payload.get('unique_original_instances')}`",
        f"- Calibration run: `{payload.get('calibration_run')}`",
        f"- Gate result: `{payload.get('gate_result')}`",
        f"- Metric claim level: `{payload.get('metric_claim_level')}`",
        "",
        "## Claim Boundary",
        "",
        "- No final `calibrated_proxy_supported` claim is introduced.",
        "- No `vinfo_proxy_supported` claim is introduced.",
        "- No measurement validation, paper evidence, P55/P56 metric support, global selector superiority, or deployed V-information verification is introduced.",
        "- Any candidate status remains pending independent validation.",
        "",
        "## Next Recommended Decision",
        "",
        "Submit the Route 4A package for major review before any claim-ledger or manuscript update.",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def run_route4_pipeline(
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    fever_candidate_pools_path: str | Path = DEFAULT_FEVER_CANDIDATE_POOLS_PATH,
    fever_delta_records_path: str | Path = DEFAULT_FEVER_DELTA_RECORDS_PATH,
    hotpotqa_candidate_pools_path: str | Path = DEFAULT_CANDIDATE_POOLS_PATH,
    hotpotqa_delta_records_path: str | Path = DEFAULT_HOTPOTQA_DELTA_RECORDS_PATH,
    hotpotqa_generation_report_path: str | Path = DEFAULT_HOTPOTQA_GENERATION_REPORT_PATH,
    env_path: str | Path | None = ".env",
    min_pilot_rows: int = MIN_PILOT_ROWS,
    min_unique_instances: int = MIN_UNIQUE_INSTANCES,
    report_md_path: str | Path = DEFAULT_REPORT_MD,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    dataset = inspect_dataset_readiness(
        fever_candidate_pools_path=fever_candidate_pools_path,
        fever_delta_records_path=fever_delta_records_path,
        hotpotqa_candidate_pools_path=hotpotqa_candidate_pools_path,
        hotpotqa_delta_records_path=hotpotqa_delta_records_path,
    )
    evaluator = inspect_evaluator_readiness(
        hotpotqa_generation_report_path=hotpotqa_generation_report_path,
        env_path=env_path,
    )
    plan = {
        "active_stratum": ACTIVE_STRATUM,
        "block_size": 1,
        "budget": BUDGET,
        "claim_status": CLAIM_STATUS,
        "dataset": DATASET,
        "delta_logloss_source": "existing_approved_hotpotqa_answer_nll_delta_record",
        "heldout_fraction": HELDOUT_FRACTION,
        "materialization_policy": MATERIALIZATION_POLICY,
        "min_pilot_rows": min_pilot_rows,
        "min_unique_instances": min_unique_instances,
        "phase": ROUTE4_PHASE_ID,
        "protocol_id": ROUTE4_PROTOCOL_ID,
        "replicate_count_policy": REPLICATE_COUNT_POLICY,
        "route_id": ROUTE4_ID,
        "split": SPLIT,
        "split_id": SPLIT_ID,
        "task_family": TASK_FAMILY,
        "target_representation": TARGET_REPRESENTATION,
        "utility_target_id": UTILITY_TARGET_ID,
        "utility_definition": UTILITY_DEFINITION,
        "utility_source": UTILITY_SOURCE,
    }
    write_json(output_path / "dataset_readiness_report.json", dataset)
    write_json(output_path / "evaluator_readiness_report.json", evaluator)
    write_json(output_path / "route4_execution_plan_frozen.json", plan)
    if "HotpotQA" not in dataset["available_strata"]:
        result = {
            "calibration_run": False,
            "claim_status": CLAIM_STATUS,
            "gate_result": "blocked_dataset_incomplete",
            "operator_inputs_written": False,
            "phase": ROUTE4_PHASE_ID,
            "status": "blocked_dataset_incomplete",
        }
        _write_execution_doc(report_md_path, result)
        return result
    if not evaluator["approved_scoring_backend_found"]:
        result = {
            "calibration_run": False,
            "claim_status": CLAIM_STATUS,
            "gate_result": "blocked_evaluator_unavailable",
            "operator_inputs_written": False,
            "phase": ROUTE4_PHASE_ID,
            "status": "blocked_evaluator_unavailable",
        }
        _write_execution_doc(report_md_path, result)
        return result
    candidate_pools = read_jsonl(hotpotqa_candidate_pools_path)
    delta_records = read_jsonl(hotpotqa_delta_records_path)
    rows, build_report = build_route4_rows_from_hotpotqa_delta_records(candidate_pools, delta_records)
    validation = validate_route4_rows(rows, candidate_pools)
    valid_rows = rows if validation["schema_valid"] else []
    write_jsonl(output_path / "bridge_rows.jsonl", valid_rows)
    split = split_manifest(valid_rows)
    circularity = non_circularity_report(valid_rows)
    controls = negative_control_report(valid_rows)
    write_json(output_path / "split_manifest.json", split)
    write_json(output_path / "non_circularity_report.json", circularity)
    generation = {
        **build_report,
        "claim_status": CLAIM_STATUS,
        "operator_inputs_written": False,
        "phase": ROUTE4_PHASE_ID,
        "rows_attempted": len(delta_records),
        "rows_validated": validation["rows_validated"],
        "status": "bridge_rows_validated" if validation["schema_valid"] else "failed_closed_row_validation",
        "validation_errors": validation["errors"],
    }
    write_json(output_path / "bridge_generation_report.json", generation)
    if not validation["schema_valid"] or validation["rows_validated"] < min_pilot_rows:
        result = {
            **generation,
            "calibration_run": False,
            "gate_result": "failed_closed_below_min_rows",
            "metric_claim_level": "failed_closed_no_claim_upgrade",
            "unique_original_instances": split["unique_original_instances"],
        }
        _write_execution_doc(report_md_path, result)
        return result
    fit = fit_route4_calibration(valid_rows, min_rows=min_pilot_rows, min_unique_instances=min_unique_instances)
    write_json(output_path / "bridge_fit_summary.json", fit)
    write_json(output_path / "control_results.json", controls)
    witness = {
        "active_stratum": ACTIVE_STRATUM,
        "claim_status": CLAIM_STATUS,
        "dataset": DATASET,
        "gate_result": fit["gate_result"],
        "metric_claim_level": fit["metric_claim_level"],
        "phase": ROUTE4_PHASE_ID,
        "protocol_id": ROUTE4_PROTOCOL_ID,
        "task_family": TASK_FAMILY,
    }
    write_json(output_path / "metric_bridge_witness.json", witness)
    claim_gate = {
        "calibrated_proxy_supported": False,
        "claim_status": CLAIM_STATUS,
        "gate_result": fit["gate_result"],
        "measurement_validation": False,
        "metric_bridge_support_candidate": fit["gate_result"] == "metric_bridge_support_candidate_pending_independent_validation",
        "paper_evidence": False,
        "vinfo_proxy_supported": False,
    }
    write_json(output_path / "claim_gate_result.json", claim_gate)
    result = {
        **generation,
        "calibration_run": fit["calibration_run"],
        "gate_result": fit["gate_result"],
        "heldout_split_summary": split,
        "metric_claim_level": fit["metric_claim_level"],
        "negative_control_summary": controls,
        "non_circularity_summary": circularity,
        "operator_inputs_written": False,
        "sign_agreement": fit.get("sign_agreement"),
        "spearman": (fit.get("bridge_fit") or {}).get("spearman_rho"),
        "status": "calibration_completed",
        "unique_original_instances": split["unique_original_instances"],
    }
    _write_execution_doc(report_md_path, result)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Route 4 HotpotQA sufficiency-grounded bridge pilot.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-md-path", default=DEFAULT_REPORT_MD)
    parser.add_argument("--min-pilot-rows", type=int, default=MIN_PILOT_ROWS)
    parser.add_argument("--min-unique-instances", type=int, default=MIN_UNIQUE_INSTANCES)
    args = parser.parse_args(argv)
    result = run_route4_pipeline(
        output_dir=args.output_dir,
        min_pilot_rows=args.min_pilot_rows,
        min_unique_instances=args.min_unique_instances,
        report_md_path=args.report_md_path,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
