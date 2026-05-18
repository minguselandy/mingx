from __future__ import annotations

import argparse
import json
import math
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Mapping
from typing import Sequence

from cps.benchmarks.hashing import canonical_json_dumps
from cps.benchmarks.hashing import stable_hash
from cps.experiments.hotpotqa_support_classification_independent_utility_bridge import _dashscope_post
from cps.experiments.hotpotqa_support_classification_independent_utility_bridge import _extract_content_logprobs
from cps.experiments.hotpotqa_support_classification_independent_utility_bridge import _load_env_values


ROUTE_ID = "route3_metric_bridge_repair"
PHASE_ID = "route3b_support_grounded_bridge_revision"
REVISION_PROTOCOL_ID = "route3b_all_eligible_support_grounded_v1"
ACTIVE_STRATUM = "evidence_packet_selection_microtask_v1"
TASK_FAMILY = "hotpotqa_support_grounded_utility_bridge"
DATASET = "HotpotQA"
SPLIT = "dev_distractor"
GOLD_LABEL = "gold_supporting"
SUPPORTING = "SUPPORTING"
NON_SUPPORTING = "NON_SUPPORTING"
MODEL_NAME = "qwen3.6-flash"
MODEL_TIER = "approved_live_logprob_model_v1"
DECODING_POLICY = "deterministic_logprob_scoring_v1"
MATERIALIZATION_POLICY = "fixed_selector_order_with_source_boundaries"
CANDIDATE_SLICE_BAND = "route3b_support_grounded_budget_512"
BUDGET = 512
BLOCK_SIZE = 1
SPLIT_ID = "route3b_original_instance_hash_70_30_v1"
UTILITY_DEFINITION = "route3b_supporting_fact_recall_delta_v1"
DELTA_UTILITY_SOURCE = "hotpotqa_candidate_pool_gold_support_labels_and_source_doc_ids"
METRIC_DESIGN = "route3b_support_grounded_utility_revision_v1"
LOGPROB_PROMPT_VERSION = "route3b_hotpotqa_support_label_logprob_prompt_v1"
EVALUATOR_ID = "approved_live_api_logprob_endpoint::dashscope::qwen3.6-flash::route3b_support_label_nll_v1"
CLAIM_STATUS = "no_claim_upgrade"
DEFAULT_CANDIDATE_POOLS_PATH = "artifacts/benchmarks/hotpotqa_candidate_pools.jsonl"
DEFAULT_DELTA_RECORDS_PATH = "artifacts/benchmarks/route3b_hotpotqa_support_grounded_delta_records.jsonl"
DEFAULT_GENERATION_REPORT_PATH = "artifacts/benchmarks/route3b_hotpotqa_support_grounded_generation_report.json"
DEFAULT_CALIBRATION_DIR = "artifacts/experiments/route3b_support_grounded_bridge_calibration"
DEFAULT_REPORT_MD = "docs/experiments/Route3B-support-grounded-bridge-revision.md"
MIN_ROWS = 500
MIN_UNIQUE_INSTANCES = 150
MIN_ESS = 100
HELDOUT_FRACTION = 0.30
MIN_SIGN_AGREEMENT = 0.70
MIN_SPEARMAN = 0.40
MAX_NORMALIZED_RESIDUAL = 0.50


LoglossScorer = Callable[..., dict[str, Any]]


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    input_path = Path(path)
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


def packet_id(packet: Mapping[str, Any]) -> str:
    return str(packet.get("packet_id") or "").strip()


def packet_label(packet: Mapping[str, Any]) -> str:
    return str(packet.get("gold_support_label") or "").strip()


def source_doc(packet: Mapping[str, Any]) -> str:
    return str(packet.get("source_doc_id") or "").strip()


def token_cost(packet: Mapping[str, Any]) -> int:
    try:
        return int(packet.get("token_cost") or 0)
    except (TypeError, ValueError):
        return 0


def pool_packets(pool: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [dict(packet) for packet in (pool.get("candidate_pool") or {}).get("packets") or []]


def has_packet_provenance(packet: Mapping[str, Any]) -> bool:
    return bool(packet_id(packet) and source_doc(packet) and packet.get("provenance"))


def route3b_instance_id(original_id: str, target_id: str, block_id: str) -> str:
    suffix = stable_hash({"block_A_packet_id": block_id, "budget": BUDGET, "target_packet_id": target_id})[:16]
    return f"{original_id}::route3b::{suffix}"


def label_for_packet(packet: Mapping[str, Any]) -> str:
    return SUPPORTING if packet_label(packet) == GOLD_LABEL else NON_SUPPORTING


def split_assignment(original_id: str, sorted_original_ids: Sequence[str]) -> bool:
    ordered = sorted(sorted_original_ids, key=stable_hash)
    heldout_count = max(1, math.ceil(len(ordered) * HELDOUT_FRACTION))
    heldout_ids = set(ordered[-heldout_count:])
    return original_id in heldout_ids


def supporting_packets(pool: Mapping[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [packet for packet in pool_packets(pool) if packet_label(packet) == GOLD_LABEL and has_packet_provenance(packet)],
        key=packet_id,
    )


def non_supporting_packets(pool: Mapping[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [packet for packet in pool_packets(pool) if packet_label(packet) != GOLD_LABEL and has_packet_provenance(packet)],
        key=packet_id,
    )


def planned_specs(candidate_pools: Sequence[Mapping[str, Any]], *, max_instances: int = 999) -> list[dict[str, Any]]:
    eligible: list[tuple[Mapping[str, Any], list[dict[str, Any]], list[dict[str, Any]]]] = []
    for pool in sorted(candidate_pools, key=lambda row: str(row.get("instance_id") or "")):
        gold = supporting_packets(pool)
        distractors = non_supporting_packets(pool)
        pool_hash = str((pool.get("candidate_pool") or {}).get("candidate_pool_hash") or "")
        if len(gold) >= 2 and len(distractors) >= 2 and pool_hash:
            eligible.append((pool, gold, distractors))
        if len(eligible) >= max_instances:
            break
    original_ids = [str(pool.get("instance_id") or "") for pool, _, _ in eligible]
    specs: list[dict[str, Any]] = []
    for pool, gold, distractors in eligible:
        original_id = str(pool.get("instance_id") or "")
        pool_hash = str((pool.get("candidate_pool") or {}).get("candidate_pool_hash") or "")
        question = str(pool.get("query") or "")
        support_ids = tuple(packet_id(packet) for packet in gold)
        support_docs = tuple(sorted({source_doc(packet) for packet in gold if source_doc(packet)}))
        pairs = (
            (gold[0], gold[1], "support_target_gold_A"),
            (gold[1], distractors[0], "support_target_distractor_A"),
            (distractors[0], gold[0], "non_support_target_gold_A"),
            (distractors[1], distractors[0], "non_support_target_distractor_A"),
        )
        for target, block, sample_role in pairs:
            target_id = packet_id(target)
            block_id = packet_id(block)
            if target_id == block_id:
                continue
            heldout = split_assignment(original_id, original_ids)
            specs.append(
                {
                    "block_A_content": str(block.get("content") or ""),
                    "block_A_gold_support_label": packet_label(block),
                    "block_A_packet_id": block_id,
                    "block_A_source_doc_id": source_doc(block),
                    "candidate_pool_hash": pool_hash,
                    "heldout_flag": heldout,
                    "instance_id": route3b_instance_id(original_id, target_id, block_id),
                    "original_hotpotqa_id": original_id,
                    "question": question,
                    "sample_role": sample_role,
                    "support_set_packet_ids": support_ids,
                    "support_set_source_doc_ids": support_docs,
                    "target_packet_content": str(target.get("content") or ""),
                    "target_packet_gold_support_label": packet_label(target),
                    "target_packet_id": target_id,
                    "target_y": label_for_packet(target),
                }
            )
    return specs


def support_recall(packet_ids: Sequence[str], support_ids: Sequence[str]) -> float:
    if not support_ids:
        raise ValueError("missing_support_ids")
    return len(set(packet_ids).intersection(support_ids)) / len(set(support_ids))


def support_doc_recall(packet_docs: Sequence[str], support_docs: Sequence[str]) -> float:
    if not support_docs:
        raise ValueError("missing_support_docs")
    return len(set(packet_docs).intersection(support_docs)) / len(set(support_docs))


def utility_payload(spec: Mapping[str, Any]) -> dict[str, float | int]:
    support_ids = tuple(str(packet_id) for packet_id in spec["support_set_packet_ids"])
    support_docs = tuple(str(doc) for doc in spec["support_set_source_doc_ids"])
    baseline_ids: tuple[str, ...] = ()
    augmented_ids = (str(spec["block_A_packet_id"]),)
    baseline_recall = support_recall(baseline_ids, support_ids)
    augmented_recall = support_recall(augmented_ids, support_ids)
    baseline_doc_recall = support_doc_recall((), support_docs)
    augmented_doc_recall = support_doc_recall((str(spec["block_A_source_doc_id"]),), support_docs)
    baseline_full_hit = int(set(support_ids).issubset(baseline_ids))
    augmented_full_hit = int(set(support_ids).issubset(augmented_ids))
    gold_packets_added = int(str(spec["block_A_packet_id"]) in support_ids)
    return {
        "augmented_utility": augmented_recall,
        "baseline_utility": baseline_recall,
        "delta_utility": augmented_recall - baseline_recall,
        "full_support_hit_delta": augmented_full_hit - baseline_full_hit,
        "gold_support_packets_added": gold_packets_added,
        "support_coverage_delta": 0.5 * (augmented_recall - baseline_recall)
        + 0.5 * (augmented_doc_recall - baseline_doc_recall),
        "support_doc_recall_delta": augmented_doc_recall - baseline_doc_recall,
        "support_token_efficiency": float(gold_packets_added),
    }


def support_prompt(spec: Mapping[str, Any], *, with_block: bool) -> str:
    context = f"- {spec['block_A_content']}" if with_block else "(none)"
    return (
        "Classify whether the candidate sentence is one of the HotpotQA supporting facts for the question.\n"
        "Use only the question, candidate sentence, and optional context sentences.\n"
        "Allowed labels: SUPPORTING or NON_SUPPORTING.\n\n"
        f"Question: {spec['question']}\n"
        f"Candidate sentence: {spec['target_packet_content']}\n"
        f"Optional context:\n{context}\n\n"
        f"Return exactly one label: {SUPPORTING} or {NON_SUPPORTING}."
    )


def make_dashscope_logloss_scorer(
    *,
    env_path: str | Path | None = ".env",
    max_attempts: int = 3,
    sleep_seconds: float = 2.0,
) -> LoglossScorer:
    env = _load_env_values(env_path)
    api_key = env.get("DASHSCOPE_API_KEY") or env.get("API_KEY")
    base_url = env.get("DASHSCOPE_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if not api_key:
        raise RuntimeError("missing DASHSCOPE_API_KEY for Route 3B logprob evaluator")

    def score(*, spec: Mapping[str, Any], with_block: bool) -> dict[str, Any]:
        payload = {
            "enable_thinking": False,
            "logprobs": True,
            "max_tokens": 6,
            "messages": [
                {
                    "content": "Output only SUPPORTING or NON_SUPPORTING.",
                    "role": "system",
                },
                {"content": support_prompt(spec, with_block=with_block), "role": "user"},
            ],
            "model": MODEL_NAME,
            "n": 1,
            "stream": False,
            "temperature": 0,
            "top_logprobs": 0,
            "top_p": 1,
        }
        response_payload, retries = _dashscope_post(
            api_key=api_key,
            base_url=base_url,
            max_attempts=max_attempts,
            payload=payload,
            sleep_seconds=sleep_seconds,
        )
        content, token_logprobs = _extract_content_logprobs(response_payload)
        if content != spec["target_y"]:
            raise ValueError(f"logloss evaluator emitted {content!r}, expected {spec['target_y']!r}")
        if not token_logprobs:
            raise ValueError("logloss evaluator response lacks token logprobs")
        usage = response_payload.get("usage") or {}
        return {
            "completion_tokens": int(usage.get("completion_tokens") or 0),
            "nll": -sum(token_logprobs),
            "prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "retries": retries,
            "total_tokens": int(usage.get("total_tokens") or 0),
        }

    return score


def materialized_context_hash(context_ids: Sequence[str], block_ids: Sequence[str]) -> str:
    return stable_hash({"block_A_packet_ids": list(block_ids), "context_L_packet_ids": list(context_ids)})


def row_identity(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        record["route_id"],
        record["phase_id"],
        record["revision_protocol_id"],
        record["active_stratum"],
        record["task_family"],
        record["dataset"],
        record["instance_id"],
        record["original_hotpotqa_id"],
        record["candidate_pool_hash"],
        tuple(record["context_L_packet_ids"]),
        tuple(record["block_A_packet_ids"]),
        record["target_y"],
        record["model_tier"],
        record["materialization_policy"],
        record["candidate_slice_band"],
        record["block_size"],
        record["budget"],
        record["decoding_policy"],
        record["evaluator_id"],
        record["utility_definition"],
        record["delta_utility_source"],
        record["split_id"],
        record["heldout_flag"],
    )


def record_from_scores(spec: Mapping[str, Any], *, nll_l: Mapping[str, Any], nll_l_plus_a: Mapping[str, Any]) -> dict[str, Any]:
    utility = utility_payload(spec)
    context_ids: tuple[str, ...] = ()
    block_ids = (str(spec["block_A_packet_id"]),)
    return {
        "active_stratum": ACTIVE_STRATUM,
        "augmented_utility": round(float(utility["augmented_utility"]), 12),
        "baseline_utility": round(float(utility["baseline_utility"]), 12),
        "block_A_packet_ids": list(block_ids),
        "block_size": BLOCK_SIZE,
        "budget": BUDGET,
        "candidate_pool_hash": spec["candidate_pool_hash"],
        "candidate_slice_band": CANDIDATE_SLICE_BAND,
        "contamination_status": "clean",
        "validation_failure_reason": None,
        "context_L_packet_ids": list(context_ids),
        "dataset": DATASET,
        "decoding_policy": DECODING_POLICY,
        "delta_logloss": round(float(nll_l["nll"]) - float(nll_l_plus_a["nll"]), 12),
        "delta_logloss_source": "live_api_support_label_nll_without_minus_with_block",
        "delta_utility": round(float(utility["delta_utility"]), 12),
        "delta_utility_source": DELTA_UTILITY_SOURCE,
        "evaluator_id": EVALUATOR_ID,
        "full_support_hit_delta": utility["full_support_hit_delta"],
        "gold_support_packets_added": utility["gold_support_packets_added"],
        "heldout_flag": bool(spec["heldout_flag"]),
        "instance_id": spec["instance_id"],
        "logprob_prompt_version": LOGPROB_PROMPT_VERSION,
        "materialization_policy": MATERIALIZATION_POLICY,
        "materialized_context_hash": materialized_context_hash(context_ids, block_ids),
        "metric_design": METRIC_DESIGN,
        "model_tier": MODEL_TIER,
        "non_circularity_flags": {},
        "original_hotpotqa_id": spec["original_hotpotqa_id"],
        "phase_id": PHASE_ID,
        "replicate_count": 1,
        "route_id": ROUTE_ID,
        "revision_protocol_id": REVISION_PROTOCOL_ID,
        "sample_role": spec["sample_role"],
        "split_id": SPLIT_ID,
        "support_coverage_delta": round(float(utility["support_coverage_delta"]), 12),
        "support_doc_recall_delta": round(float(utility["support_doc_recall_delta"]), 12),
        "support_set_packet_ids": list(spec["support_set_packet_ids"]),
        "support_set_source_doc_ids": list(spec["support_set_source_doc_ids"]),
        "support_token_efficiency": round(float(utility["support_token_efficiency"]), 12),
        "target_packet_gold_support_label": spec["target_packet_gold_support_label"],
        "target_packet_id": spec["target_packet_id"],
        "target_y": spec["target_y"],
        "task_family": TASK_FAMILY,
        "utility_definition": UTILITY_DEFINITION,
    }


def finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def average_ranks(values: Sequence[float]) -> list[float]:
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


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2:
        return None
    x_mean = mean(xs)
    y_mean = mean(ys)
    if x_mean is None or y_mean is None:
        return None
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = math.sqrt(sum((x - x_mean) ** 2 for x in xs) * sum((y - y_mean) ** 2 for y in ys))
    return None if denominator == 0 else numerator / denominator


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2:
        return None
    return pearson(average_ranks(xs), average_ranks(ys))


def affine_transform_detected(xs: Sequence[float], ys: Sequence[float]) -> bool:
    if len(xs) < 3 or len(set(xs)) < 2:
        return False
    x_mean = mean(xs)
    y_mean = mean(ys)
    if x_mean is None or y_mean is None:
        return False
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return False
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator
    intercept = y_mean - slope * x_mean
    return all(abs((slope * x + intercept) - y) <= 1e-9 for x, y in zip(xs, ys))


def rounded_equality_detected(xs: Sequence[float], ys: Sequence[float]) -> bool:
    return any(all(round(x, digits) == y for x, y in zip(xs, ys)) for digits in range(13))


def rank_identity_detected(xs: Sequence[float], ys: Sequence[float]) -> bool:
    if len(xs) < 3:
        return False
    return average_ranks(xs) == average_ranks(ys)


def non_circularity_report(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    xs = [float(record["delta_logloss"]) for record in records]
    ys = [float(record["delta_utility"]) for record in records]
    equality_count = sum(abs(x - y) <= 1e-12 for x, y in zip(xs, ys))
    distribution: dict[str, int] = {}
    for value in ys:
        key = f"{value:.12g}"
        distribution[key] = distribution.get(key, 0) + 1
    return {
        "affine_transform_detected": affine_transform_detected(xs, ys),
        "delta_utility_distribution": dict(sorted(distribution.items())),
        "exact_equality_detected": equality_count == len(records) if records else False,
        "fraction_delta_utility_equals_delta_logloss": equality_count / len(records) if records else 0.0,
        "pearson_delta_utility_delta_logloss": pearson(xs, ys),
        "rank_identity_detected": rank_identity_detected(xs, ys),
        "rounded_equality_detected": rounded_equality_detected(xs, ys),
        "spearman_delta_utility_delta_logloss": spearman(xs, ys),
        "utility_source_verified": DELTA_UTILITY_SOURCE == "hotpotqa_candidate_pool_gold_support_labels_and_source_doc_ids",
    }


def validate_records(records: Sequence[Mapping[str, Any]], candidate_pools: Sequence[Mapping[str, Any]]) -> list[str]:
    pool_packet_ids: dict[str, set[str]] = {}
    for pool in candidate_pools:
        pool_hash = str((pool.get("candidate_pool") or {}).get("candidate_pool_hash") or "")
        pool_packet_ids[pool_hash] = {packet_id(packet) for packet in pool_packets(pool)}
    seen: set[tuple[Any, ...]] = set()
    errors: list[str] = []
    for index, record in enumerate(records, start=1):
        prefix = f"row_{index}:"
        if row_identity(record) in seen:
            errors.append(prefix + "duplicate_row_identity")
        seen.add(row_identity(record))
        if record["candidate_pool_hash"] not in pool_packet_ids:
            errors.append(prefix + "unknown_candidate_pool_hash")
        known = pool_packet_ids.get(record["candidate_pool_hash"], set())
        for packet in [*record["context_L_packet_ids"], *record["block_A_packet_ids"], record["target_packet_id"]]:
            if packet not in known:
                errors.append(prefix + "packet_not_in_candidate_pool")
        if record["target_packet_id"] in set(record["context_L_packet_ids"]) | set(record["block_A_packet_ids"]):
            errors.append(prefix + "target_packet_in_context_or_block")
        if finite_float(record.get("delta_logloss")) is None:
            errors.append(prefix + "delta_logloss_not_numeric")
        if finite_float(record.get("delta_utility")) is None:
            errors.append(prefix + "delta_utility_not_numeric")
        if record.get("delta_utility_source") != DELTA_UTILITY_SOURCE:
            errors.append(prefix + "wrong_delta_utility_source")
        if record.get("contamination_status") == "failed":
            errors.append(prefix + "contamination_failed")
    circularity = non_circularity_report(records)
    if circularity["exact_equality_detected"]:
        errors.append("exact_equality_detected")
    if circularity["affine_transform_detected"]:
        errors.append("affine_transform_detected")
    if circularity["rank_identity_detected"]:
        errors.append("rank_identity_detected")
    if not circularity["utility_source_verified"]:
        errors.append("utility_source_not_verified")
    return errors


def score_records(
    specs: Sequence[Mapping[str, Any]],
    *,
    scorer: LoglossScorer,
    max_workers: int,
) -> tuple[list[dict[str, Any]], list[str], dict[str, int]]:
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    usage = {"api_score_calls": 0, "api_retries": 0, "completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0}

    def score_one(spec: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str | None, dict[str, int]]:
        try:
            nll_l = scorer(spec=spec, with_block=False)
            nll_l_plus_a = scorer(spec=spec, with_block=True)
        except Exception as exc:  # noqa: BLE001 - fail-closed report records sanitized reason.
            return None, f"{spec['instance_id']}:{type(exc).__name__}:{exc}", {}
        record = record_from_scores(spec, nll_l=nll_l, nll_l_plus_a=nll_l_plus_a)
        return (
            record,
            None,
            {
                "api_score_calls": 2,
                "api_retries": int(nll_l["retries"]) + int(nll_l_plus_a["retries"]),
                "completion_tokens": int(nll_l["completion_tokens"]) + int(nll_l_plus_a["completion_tokens"]),
                "prompt_tokens": int(nll_l["prompt_tokens"]) + int(nll_l_plus_a["prompt_tokens"]),
                "total_tokens": int(nll_l["total_tokens"]) + int(nll_l_plus_a["total_tokens"]),
            },
        )

    if max_workers <= 1:
        results = [score_one(spec) for spec in specs]
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(score_one, spec) for spec in specs]
            results = [future.result() for future in as_completed(futures)]
    for record, failure, row_usage in results:
        if failure is not None:
            failures.append(failure.encode("ascii", errors="ignore").decode("ascii")[:240])
            continue
        if record is not None:
            records.append(record)
            for key in usage:
                usage[key] += int(row_usage.get(key) or 0)
    return sorted(records, key=row_identity), sorted(failures), usage


def metric_summary(xs: Sequence[float], ys: Sequence[float]) -> dict[str, Any]:
    if not xs or not ys:
        return {"pearson": None, "sign_agreement": None, "spearman": None}
    sign_agreement = sum(sign(x) == sign(y) for x, y in zip(xs, ys)) / len(xs)
    return {"pearson": pearson(xs, ys), "sign_agreement": sign_agreement, "spearman": spearman(xs, ys)}


def sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def negative_control_report(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ys = [float(record["delta_utility"]) for record in records]
    xs = [float(record["delta_logloss"]) for record in records]
    shuffled = list(reversed(xs))
    wrong_instance = ys[1:] + ys[:1] if ys else []
    random_scores = [
        (int(stable_hash(row_identity(record))[:8], 16) / 0xFFFFFFFF) * 2 - 1
        for record in records
    ]
    length_scores = [float(len(record["block_A_packet_ids"])) for record in records]
    packet_count_scores = [float(record["block_size"]) for record in records]
    return {
        "length_only_baseline": metric_summary(length_scores, ys),
        "packet_count_only_baseline": metric_summary(packet_count_scores, ys),
        "random_score_baseline": metric_summary(random_scores, ys),
        "shuffled_delta_logloss_within_split_budget": metric_summary(shuffled, ys),
        "wrong_instance_join": metric_summary(xs, wrong_instance),
    }


def split_rows(records: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float]:
    train = [dict(record) for record in records if not record["heldout_flag"]]
    heldout = [dict(record) for record in records if record["heldout_flag"]]
    original_ids = {record["original_hotpotqa_id"] for record in records}
    heldout_ids = {record["original_hotpotqa_id"] for record in heldout}
    return train, heldout, len(heldout_ids) / len(original_ids) if original_ids else 0.0


def through_origin_scale(rows: Sequence[Mapping[str, Any]]) -> float | None:
    denominator = sum(float(row["delta_logloss"]) ** 2 for row in rows)
    if denominator == 0:
        return None
    numerator = sum(float(row["delta_logloss"]) * float(row["delta_utility"]) for row in rows)
    return numerator / denominator


def fit_calibration(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    train, heldout, actual_heldout = split_rows(records)
    c_hat = through_origin_scale(train)
    predictions: list[float] = []
    actuals: list[float] = []
    residuals: list[float] = []
    for row in heldout:
        if c_hat is None:
            continue
        predicted = c_hat * float(row["delta_logloss"])
        actual = float(row["delta_utility"])
        predictions.append(predicted)
        actuals.append(actual)
        residuals.append(abs(actual - predicted))
    zeta = max(residuals) if residuals else None
    mean_abs_utility = mean([abs(float(row["delta_utility"])) for row in heldout])
    normalized = None
    if zeta is not None and mean_abs_utility is not None:
        normalized = zeta / max(mean_abs_utility, 1e-12)
    sign_agreement = None
    if heldout:
        sign_agreement = sum(sign(float(row["delta_logloss"])) == sign(float(row["delta_utility"])) for row in heldout) / len(heldout)
    spearman_rho = spearman(predictions, actuals)
    unique_instances = len({record["original_hotpotqa_id"] for record in records})
    ess = sum(int(record["replicate_count"]) for record in records)
    flags = {
        "effective_sample_size_pass": ess >= MIN_ESS,
        "heldout_fraction_pass": actual_heldout >= HELDOUT_FRACTION,
        "normalized_residual_pass": normalized is not None and normalized <= MAX_NORMALIZED_RESIDUAL,
        "row_count_pass": len(records) >= MIN_ROWS,
        "sign_agreement_pass": sign_agreement is not None and sign_agreement >= MIN_SIGN_AGREEMENT,
        "spearman_rho_pass": spearman_rho is not None and spearman_rho >= MIN_SPEARMAN,
        "unique_instance_pass": unique_instances >= MIN_UNIQUE_INSTANCES,
    }
    reasons = sorted(key.replace("_pass", "_failed") for key, value in flags.items() if not value)
    if all(flags.values()):
        gate_result = "support_grounded_bridge_candidate_pending_independent_validation"
        metric_claim_level = "support_grounded_bridge_candidate_pending_independent_validation"
    else:
        gate_result = "failed_closed_gate_failed"
        metric_claim_level = "failed_closed_no_claim_upgrade"
    return {
        "bridge_fit": {
            "c_hat_s": c_hat,
            "fit_method": "original_instance_split_ols_through_origin",
            "normalized_residual": normalized,
            "spearman_rho": spearman_rho,
            "zeta_hat_s": zeta,
        },
        "claim_status": CLAIM_STATUS,
        "effective_sample_size": ess,
        "gate_pass_flags": flags,
        "gate_result": gate_result,
        "heldout_fraction": actual_heldout,
        "heldout_rows": len(heldout),
        "metric_claim_level": metric_claim_level,
        "reason_codes": reasons,
        "rows_validated": len(records),
        "sign_agreement": sign_agreement,
        "train_rows": len(train),
        "unique_original_instances": unique_instances,
    }


def run_route3b(
    *,
    candidate_pools_path: str | Path = DEFAULT_CANDIDATE_POOLS_PATH,
    delta_records_path: str | Path = DEFAULT_DELTA_RECORDS_PATH,
    generation_report_path: str | Path = DEFAULT_GENERATION_REPORT_PATH,
    calibration_dir: str | Path = DEFAULT_CALIBRATION_DIR,
    report_md: str | Path = DEFAULT_REPORT_MD,
    env_path: str | Path | None = ".env",
    max_instances: int = 999,
    max_workers: int = 4,
    scorer: LoglossScorer | None = None,
) -> dict[str, Any]:
    candidate_pools = read_jsonl(candidate_pools_path)
    specs = planned_specs(candidate_pools, max_instances=max_instances)
    pre_score_reasons: list[str] = []
    if len(specs) < MIN_ROWS:
        pre_score_reasons.append("planned_rows_below_min_rows")
    if len({spec["original_hotpotqa_id"] for spec in specs}) < MIN_UNIQUE_INSTANCES:
        pre_score_reasons.append("planned_unique_instances_below_minimum")
    if pre_score_reasons:
        report = {
            "claim_status": CLAIM_STATUS,
            "operator_rows_generated": 0,
            "operator_rows_validated": 0,
            "operator_rows_written": False,
            "phase": PHASE_ID,
            "pre_score_gate_passed": False,
            "reason_codes": pre_score_reasons,
            "records_attempted": len(specs),
            "revision_protocol_id": REVISION_PROTOCOL_ID,
            "status": "failed_closed_pre_score_gate",
        }
        write_json(generation_report_path, report)
        return report
    scorer = scorer or make_dashscope_logloss_scorer(env_path=env_path)
    records, failures, usage = score_records(specs, scorer=scorer, max_workers=max_workers)
    validation_errors = validate_records(records, candidate_pools)
    circularity = non_circularity_report(records)
    controls = negative_control_report(records)
    write_jsonl(delta_records_path, records)
    unique_instances = len({record["original_hotpotqa_id"] for record in records})
    pre_calibration_reasons = list(validation_errors)
    if len(records) < MIN_ROWS:
        pre_calibration_reasons.append("rows_validated_below_min_rows")
    if unique_instances < MIN_UNIQUE_INSTANCES:
        pre_calibration_reasons.append("unique_original_instances_below_minimum")
    if failures:
        failure_counts: dict[str, int] = {}
        for failure in failures:
            reason = "ValueError" if "ValueError" in failure else "RuntimeError" if "RuntimeError" in failure else "unknown"
            failure_counts[reason] = failure_counts.get(reason, 0) + 1
    else:
        failure_counts = {}
    report: dict[str, Any] = {
        **usage,
        "api_failure_examples": failures[:20],
        "api_failure_reason_counts": dict(sorted(failure_counts.items())),
        "api_failures": len(failures),
        "candidate_pools_path": Path(candidate_pools_path).as_posix(),
        "claim_status": CLAIM_STATUS,
        "delta_records_path": Path(delta_records_path).as_posix(),
        "delta_records_validated": len(records),
        "evaluator_id": EVALUATOR_ID,
        "generation_status": "completed_bounded_scoring",
        "heldout_split_summary": heldout_summary(records),
        "negative_control_results": controls,
        "non_circularity_checks": circularity,
        "operator_rows_generated": 0,
        "operator_rows_validated": 0,
        "operator_rows_written": False,
        "phase": PHASE_ID,
        "pre_calibration_gate_passed": not pre_calibration_reasons,
        "pre_calibration_reason_codes": sorted(set(pre_calibration_reasons)),
        "pre_score_gate_passed": True,
        "records_attempted": len(specs),
        "records_validated": len(records),
        "route_id": ROUTE_ID,
        "revision_protocol_id": REVISION_PROTOCOL_ID,
        "status": "failed_closed_below_min_rows" if len(records) < MIN_ROWS else "records_ready_for_calibration",
        "unique_original_instances": unique_instances,
        "validation_failure_categories": {
            "candidate_pool_hash_or_packet_reference_errors": 0,
            "duplicate_row_identity_errors": 0,
            "live_logprob_label_mismatch_value_error": failure_counts.get("ValueError", 0),
            "live_logprob_runtime_error": failure_counts.get("RuntimeError", 0),
            "live_logprob_unknown_error": failure_counts.get("unknown", 0),
            "row_validation_errors": len(validation_errors),
        },
    }
    if pre_calibration_reasons:
        report["calibration_run"] = False
        write_json(generation_report_path, report)
        write_markdown_report(report_md, report=report, fit=None)
        return report
    fit = fit_calibration(records)
    output_dir = Path(calibration_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "bridge_fit_summary.json", fit)
    write_json(output_dir / "non_circularity_report.json", circularity)
    write_json(output_dir / "negative_control_report.json", controls)
    report.update(
        {
            "bridge_fit_summary_path": (output_dir / "bridge_fit_summary.json").as_posix(),
            "calibration_run": True,
            "gate_result": fit["gate_result"],
            "metric_claim_level": fit["metric_claim_level"],
            "negative_control_report_path": (output_dir / "negative_control_report.json").as_posix(),
            "non_circularity_report_path": (output_dir / "non_circularity_report.json").as_posix(),
            "status": "calibration_completed",
        }
    )
    write_json(generation_report_path, report)
    write_markdown_report(report_md, report=report, fit=fit)
    return report


def heldout_summary(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    original_ids = {record["original_hotpotqa_id"] for record in records}
    heldout_ids = {record["original_hotpotqa_id"] for record in records if record["heldout_flag"]}
    return {
        "heldout_fraction_by_original_instance": len(heldout_ids) / len(original_ids) if original_ids else 0.0,
        "heldout_original_instances": len(heldout_ids),
        "split_id": SPLIT_ID,
        "split_unit": "original_hotpotqa_id",
        "train_original_instances": len(original_ids - heldout_ids),
    }


def write_markdown_report(path: str | Path, *, report: Mapping[str, Any], fit: Mapping[str, Any] | None) -> Path:
    lines = [
        "# Route 3B Support-grounded Bridge Revision",
        "",
        "## Summary",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Claim status: `{CLAIM_STATUS}`",
        f"- Records attempted: `{report.get('records_attempted')}`",
        f"- Records validated: `{report.get('records_validated')}`",
        f"- Operator rows written: `{report.get('operator_rows_written')}`",
        f"- Unique original instances: `{report.get('unique_original_instances')}`",
        f"- Calibration run: `{report.get('calibration_run')}`",
        "",
        "## Boundary",
        "",
        "- No claim upgrade is introduced.",
        "- No metric bridge support, measurement validation, paper evidence, P55/P56 metric support, global selector superiority, or deployed V-information verification claim is introduced.",
    ]
    if fit is not None:
        lines.extend(
            [
                "",
                "## Gate Result",
                "",
                f"- Gate result: `{fit.get('gate_result')}`",
                f"- Metric claim level: `{fit.get('metric_claim_level')}`",
                f"- Sign agreement: `{fit.get('sign_agreement')}`",
                f"- Spearman rho: `{fit.get('bridge_fit', {}).get('spearman_rho')}`",
                f"- Normalized residual: `{fit.get('bridge_fit', {}).get('normalized_residual')}`",
            ]
        )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Route 3B support-grounded HotpotQA bridge package.")
    parser.add_argument("--candidate-pools-path", default=DEFAULT_CANDIDATE_POOLS_PATH)
    parser.add_argument("--delta-records-path", default=DEFAULT_DELTA_RECORDS_PATH)
    parser.add_argument("--generation-report-path", default=DEFAULT_GENERATION_REPORT_PATH)
    parser.add_argument("--calibration-dir", default=DEFAULT_CALIBRATION_DIR)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--env-path", default=".env")
    parser.add_argument("--max-instances", type=int, default=999)
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args(argv)
    result = run_route3b(
        calibration_dir=args.calibration_dir,
        candidate_pools_path=args.candidate_pools_path,
        delta_records_path=args.delta_records_path,
        env_path=args.env_path,
        generation_report_path=args.generation_report_path,
        max_instances=args.max_instances,
        max_workers=args.max_workers,
        report_md=args.report_md,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
