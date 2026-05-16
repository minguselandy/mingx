from __future__ import annotations

import argparse
import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Mapping
from typing import Sequence
from urllib import error
from urllib import request

from cps.benchmarks.hashing import canonical_json_dumps
from cps.experiments.bridge_row_schema import ACTIVE_STRATUM
from cps.experiments.bridge_row_schema import DEFAULT_MATERIALIZATION_POLICY
from cps.experiments.bridge_row_schema import HOTPOTQA_DATASET
from cps.experiments.bridge_row_schema import HOTPOTQA_SUPPORT_INDEPENDENT_UTILITY_TASK_FAMILY
from cps.experiments.bridge_row_schema import P55BridgeRow
from cps.experiments.bridge_row_schema import make_materialized_context_hash
from cps.experiments.bridge_row_schema import write_bridge_row_jsonl
from cps.experiments.bridge_row_schema import write_canonical_json
from cps.experiments.bridge_row_validation import BridgeRowValidationResult
from cps.experiments.bridge_row_validation import validate_bridge_rows
from cps.experiments.p55_hotpotqa_bridge_calibration import P63RCalibrationConfig
from cps.experiments.p55_hotpotqa_bridge_calibration import run_p63r_hotpotqa_bridge_calibration


FIXB_TASK_FAMILY = HOTPOTQA_SUPPORT_INDEPENDENT_UTILITY_TASK_FAMILY
METRIC_DESIGN = "independent_live_api_support_classifier_utility_v1"
DELTA_UTILITY_SOURCE = "independent_live_api_support_classifier_accuracy_delta"
UTILITY_DEFINITION = "per_row_support_label_correctness_delta_from_independent_classifier_outputs"
LOGLOSS_EVALUATOR_ID = "approved_live_api_logprob_endpoint::dashscope::qwen3.6-flash::support_label_nll_v1"
UTILITY_EVALUATOR_ID = "approved_live_api_classifier_endpoint::dashscope::qwen3.6-flash::support_label_classifier_v1"
LOGPROB_PROMPT_VERSION = "hotpotqa_support_label_logprob_prompt_v1"
CLASSIFIER_PROMPT_VERSION = "hotpotqa_support_label_classifier_prompt_v1"
SUPPORTING = "SUPPORTING"
NON_SUPPORTING = "NON_SUPPORTING"
MODEL_TIER = "approved_live_logprob_model_v1"
MODEL_NAME = "qwen3.6-flash"
DECODING_POLICY = "deterministic_logprob_scoring_v1"
CANDIDATE_SLICE_BAND = "hotpotqa_support_independent_utility_context"
DEFAULT_CANDIDATE_POOLS_PATH = "artifacts/benchmarks/hotpotqa_candidate_pools.jsonl"
DEFAULT_DELTA_RECORDS_PATH = "artifacts/benchmarks/hotpotqa_support_independent_utility_delta_records.jsonl"
DEFAULT_REPORT_PATH = "artifacts/benchmarks/hotpotqa_support_independent_utility_generation_report.json"
DEFAULT_OPERATOR_ROWS_PATH = "artifacts/operator_inputs/p55_hotpotqa_support_independent_utility_rows.jsonl"
DEFAULT_CALIBRATION_OUTPUT_DIR = "artifacts/experiments/p55_hotpotqa_support_independent_utility_bridge_calibration"
DEFAULT_REPORT_MD = "docs/experiments/P63R-FixB-hotpotqa-independent-support-utility-bridge.md"
DEFAULT_CALIBRATION_EPOCH = "P63R-FixB-HotpotQA-independent-live-utility-v1"
METRIC_FAMILY = "hotpotqa_support_label_logloss_to_independent_live_classifier_accuracy_delta"
CLAIM_STATUS = "no_claim_upgrade"


@dataclass(frozen=True)
class SupportClassificationSpec:
    original_instance_id: str
    instance_id: str
    question: str
    target_packet_id: str
    target_packet_content: str
    target_y: str
    block_A_packet_ids: tuple[str, ...]
    block_A_contents: tuple[str, ...]
    candidate_pool_hash: str
    task_family: str = FIXB_TASK_FAMILY
    dataset: str = HOTPOTQA_DATASET
    active_stratum: str = ACTIVE_STRATUM
    materialization_policy: str = DEFAULT_MATERIALIZATION_POLICY
    candidate_slice_band: str = CANDIDATE_SLICE_BAND
    model_tier: str = MODEL_TIER
    decoding_policy: str = DECODING_POLICY
    evaluator_id: str = LOGLOSS_EVALUATOR_ID

    @property
    def context_L_packet_ids(self) -> tuple[str, ...]:
        return (self.target_packet_id,)


@dataclass(frozen=True)
class LabelNllScore:
    raw_content: str
    target_label: str
    token_logprobs: tuple[float, ...]
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    retries: int = 0

    @property
    def nll(self) -> float:
        return -sum(self.token_logprobs)


@dataclass(frozen=True)
class UtilityPrediction:
    predicted_label: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    retries: int = 0

    def correct(self, target_y: str) -> int:
        return int(self.predicted_label == target_y)


LoglossScorer = Callable[..., LabelNllScore]
UtilityClassifier = Callable[..., UtilityPrediction]


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//")):
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{Path(path).name}: row {line_number} must be a JSON object")
        rows.append(payload)
    return rows


def _short_id(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _packet_label(packet: Mapping[str, Any]) -> str | None:
    label = str(packet.get("gold_support_label") or "")
    if label == "gold_supporting":
        return SUPPORTING
    if label in {"same_context_distractor", "retrieved_distractor", "random_distractor"}:
        return NON_SUPPORTING
    return None


def _packets_by_kind(pool: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    packets = [dict(packet) for packet in (pool.get("candidate_pool") or {}).get("packets") or []]
    supporting = sorted(
        [packet for packet in packets if _packet_label(packet) == SUPPORTING],
        key=lambda packet: str(packet.get("packet_id")),
    )
    non_supporting = sorted(
        [packet for packet in packets if _packet_label(packet) == NON_SUPPORTING],
        key=lambda packet: str(packet.get("packet_id")),
    )
    return supporting, non_supporting


def _select_block_packet(
    *,
    target_packet: Mapping[str, Any],
    supporting: Sequence[Mapping[str, Any]],
    non_supporting: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    target_id = str(target_packet.get("packet_id"))
    same_label_pool = supporting if _packet_label(target_packet) == SUPPORTING else non_supporting
    for packet in same_label_pool:
        if str(packet.get("packet_id")) != target_id:
            return packet
    opposite_pool = non_supporting if _packet_label(target_packet) == SUPPORTING else supporting
    for packet in opposite_pool:
        if str(packet.get("packet_id")) != target_id:
            return packet
    return None


def make_support_classification_specs(
    candidate_pools: Sequence[Mapping[str, Any]],
    *,
    max_instances: int = 150,
    records_per_instance: int = 4,
) -> list[SupportClassificationSpec]:
    specs: list[SupportClassificationSpec] = []
    instances_used = 0
    for pool in sorted(candidate_pools, key=lambda row: str(row.get("instance_id"))):
        supporting, non_supporting = _packets_by_kind(pool)
        if not supporting or not non_supporting:
            continue
        supporting_quota = min(len(supporting), max(1, records_per_instance // 2))
        non_supporting_quota = min(len(non_supporting), max(0, records_per_instance - supporting_quota))
        selected_targets = [*supporting[:supporting_quota], *non_supporting[:non_supporting_quota]]
        if len(selected_targets) < records_per_instance:
            selected_ids = {str(packet.get("packet_id")) for packet in selected_targets}
            extras = [
                packet
                for packet in [*supporting, *non_supporting]
                if str(packet.get("packet_id")) not in selected_ids
            ]
            selected_targets.extend(extras[: records_per_instance - len(selected_targets)])
        pool_hash = str((pool.get("candidate_pool") or {}).get("candidate_pool_hash") or "")
        question = str(pool.get("query") or "")
        instance_id = str(pool.get("instance_id") or "")
        pool_specs: list[SupportClassificationSpec] = []
        for packet in selected_targets:
            label = _packet_label(packet)
            block_packet = _select_block_packet(
                target_packet=packet,
                supporting=supporting,
                non_supporting=non_supporting,
            )
            if label is None or block_packet is None:
                continue
            target_packet_id = str(packet["packet_id"])
            row_instance_id = f"{instance_id}::support_independent::{_short_id(target_packet_id)}"
            pool_specs.append(
                SupportClassificationSpec(
                    original_instance_id=instance_id,
                    instance_id=row_instance_id,
                    question=question,
                    target_packet_id=target_packet_id,
                    target_packet_content=str(packet.get("content") or ""),
                    target_y=label,
                    block_A_packet_ids=(str(block_packet["packet_id"]),),
                    block_A_contents=(str(block_packet.get("content") or ""),),
                    candidate_pool_hash=pool_hash,
                )
            )
        if pool_specs:
            specs.extend(pool_specs)
            instances_used += 1
        if instances_used >= max_instances:
            break
    return specs


def _context_block(spec: SupportClassificationSpec, *, with_block: bool) -> str:
    context = "\n".join(f"- {content}" for content in (spec.block_A_contents if with_block else ()))
    return context if context else "(none)"


def _support_prompt(spec: SupportClassificationSpec, *, with_block: bool) -> str:
    return (
        "Classify whether the candidate sentence is one of the HotpotQA supporting facts for the question.\n"
        "Use only the question, candidate sentence, and optional context sentences.\n"
        "Allowed labels: SUPPORTING or NON_SUPPORTING.\n\n"
        f"Question: {spec.question}\n"
        f"Candidate sentence: {spec.target_packet_content}\n"
        f"Optional context:\n{_context_block(spec, with_block=with_block)}\n\n"
        f"Return exactly one label: {SUPPORTING} or {NON_SUPPORTING}."
    )


def _load_env_values(env_path: str | Path | None = ".env") -> dict[str, str]:
    values: dict[str, str] = {}
    path = Path(env_path) if env_path is not None else None
    if path is not None and path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
    values.update({key: value for key, value in os.environ.items() if isinstance(value, str)})
    return values


def _extract_content_logprobs(response_payload: Mapping[str, Any]) -> tuple[str, tuple[float, ...]]:
    choice = (response_payload.get("choices") or [])[0]
    message = choice.get("message") or {}
    if message.get("reasoning_content"):
        raise ValueError("response used reasoning_content")
    content = str(message.get("content") or "").strip()
    logprobs = message.get("logprobs") or choice.get("logprobs") or {}
    items = logprobs.get("content") or []
    token_logprobs = tuple(float(item["logprob"]) for item in items if "logprob" in item)
    return content, token_logprobs


def _dashscope_post(
    *,
    api_key: str,
    base_url: str,
    payload: Mapping[str, Any],
    max_attempts: int,
    sleep_seconds: float,
) -> tuple[dict[str, Any], int]:
    body = json.dumps(dict(payload), ensure_ascii=False).encode("utf-8")
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        http_request = request.Request(
            endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=90) as response:
                return json.loads(response.read().decode("utf-8")), attempt - 1
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt >= max_attempts:
                break
            time.sleep(sleep_seconds * attempt)
    raise RuntimeError(f"DashScope request failed: {last_error}") from last_error


def make_dashscope_logloss_scorer(
    *,
    env_path: str | Path | None = ".env",
    model: str = MODEL_NAME,
    max_attempts: int = 3,
    sleep_seconds: float = 2.0,
) -> LoglossScorer:
    env = _load_env_values(env_path)
    api_key = env.get("DASHSCOPE_API_KEY") or env.get("API_KEY")
    base_url = env.get("DASHSCOPE_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if not api_key:
        raise RuntimeError("missing DASHSCOPE_API_KEY for approved FixB logloss evaluator")

    def score(*, spec: SupportClassificationSpec, label: str, with_block: bool) -> LabelNllScore:
        payload = {
            "enable_thinking": False,
            "logprobs": True,
            "max_tokens": 6,
            "messages": [
                {
                    "content": (
                        "You are a deterministic HotpotQA supporting-fact classifier. "
                        "Output only SUPPORTING or NON_SUPPORTING."
                    ),
                    "role": "system",
                },
                {"content": _support_prompt(spec, with_block=with_block), "role": "user"},
            ],
            "model": model,
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
        if content not in {SUPPORTING, NON_SUPPORTING}:
            raise ValueError(f"logloss evaluator emitted invalid label {content!r}")
        if content != label:
            raise ValueError(f"logloss evaluator emitted {content!r}, expected {label!r}")
        if not token_logprobs:
            raise ValueError("logloss evaluator response lacks token logprobs")
        usage = response_payload.get("usage") or {}
        return LabelNllScore(
            completion_tokens=int(usage.get("completion_tokens") or 0),
            prompt_tokens=int(usage.get("prompt_tokens") or 0),
            raw_content=content,
            retries=retries,
            target_label=label,
            token_logprobs=token_logprobs,
            total_tokens=int(usage.get("total_tokens") or 0),
        )

    return score


def make_dashscope_utility_classifier(
    *,
    env_path: str | Path | None = ".env",
    model: str = MODEL_NAME,
    max_attempts: int = 3,
    sleep_seconds: float = 2.0,
) -> UtilityClassifier:
    env = _load_env_values(env_path)
    api_key = env.get("DASHSCOPE_API_KEY") or env.get("API_KEY")
    base_url = env.get("DASHSCOPE_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if not api_key:
        raise RuntimeError("missing DASHSCOPE_API_KEY for approved FixB utility classifier")

    def classify(*, spec: SupportClassificationSpec, with_block: bool) -> UtilityPrediction:
        payload = {
            "enable_thinking": False,
            "logprobs": False,
            "max_tokens": 6,
            "messages": [
                {
                    "content": (
                        "You are a deterministic HotpotQA supporting-fact classifier. "
                        "Output only SUPPORTING or NON_SUPPORTING."
                    ),
                    "role": "system",
                },
                {"content": _support_prompt(spec, with_block=with_block), "role": "user"},
            ],
            "model": model,
            "n": 1,
            "stream": False,
            "temperature": 0,
            "top_p": 1,
        }
        response_payload, retries = _dashscope_post(
            api_key=api_key,
            base_url=base_url,
            max_attempts=max_attempts,
            payload=payload,
            sleep_seconds=sleep_seconds,
        )
        choice = (response_payload.get("choices") or [])[0]
        message = choice.get("message") or {}
        if message.get("reasoning_content"):
            raise ValueError("utility classifier response used reasoning_content")
        content = str(message.get("content") or "").strip()
        if content not in {SUPPORTING, NON_SUPPORTING}:
            raise ValueError(f"utility classifier emitted invalid label {content!r}")
        usage = response_payload.get("usage") or {}
        return UtilityPrediction(
            completion_tokens=int(usage.get("completion_tokens") or 0),
            predicted_label=content,
            prompt_tokens=int(usage.get("prompt_tokens") or 0),
            retries=retries,
            total_tokens=int(usage.get("total_tokens") or 0),
        )

    return classify


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _record_from_scores(
    spec: SupportClassificationSpec,
    *,
    nll_without: LabelNllScore,
    nll_with: LabelNllScore,
    prediction_without: UtilityPrediction,
    prediction_with: UtilityPrediction,
) -> dict[str, Any]:
    utility_without = prediction_without.correct(spec.target_y)
    utility_with = prediction_with.correct(spec.target_y)
    return {
        "active_stratum": spec.active_stratum,
        "block_A_packet_ids": list(spec.block_A_packet_ids),
        "block_size": 1,
        "candidate_pool_hash": spec.candidate_pool_hash,
        "candidate_slice_band": spec.candidate_slice_band,
        "classifier_prompt_version": CLASSIFIER_PROMPT_VERSION,
        "contamination_status": "clean",
        "context_L_packet_ids": list(spec.context_L_packet_ids),
        "dataset": spec.dataset,
        "decoding_policy": spec.decoding_policy,
        "delta_logloss": round(nll_without.nll - nll_with.nll, 12),
        "delta_logloss_source": "live_api_support_label_nll_without_minus_with_block",
        "delta_utility": float(utility_with - utility_without),
        "delta_utility_source": DELTA_UTILITY_SOURCE,
        "evaluator_id": LOGLOSS_EVALUATOR_ID,
        "instance_id": spec.instance_id,
        "labels_source": "hotpotqa_candidate_pool_gold_support_label",
        "logloss_evaluator_id": LOGLOSS_EVALUATOR_ID,
        "logprob_prompt_version": LOGPROB_PROMPT_VERSION,
        "materialization_policy": spec.materialization_policy,
        "metric_design": METRIC_DESIGN,
        "model_tier": spec.model_tier,
        "original_instance_id": spec.original_instance_id,
        "replicate_count": 1,
        "target_packet_id": spec.target_packet_id,
        "target_y": spec.target_y,
        "task_family": spec.task_family,
        "utility_definition": UTILITY_DEFINITION,
        "utility_evaluator_id": UTILITY_EVALUATOR_ID,
        "utility_prediction_with_block": prediction_with.predicted_label,
        "utility_prediction_without_block": prediction_without.predicted_label,
        "utility_score_with_block": utility_with,
        "utility_score_without_block": utility_without,
    }


def _required_record_errors(record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "active_stratum",
        "block_A_packet_ids",
        "candidate_pool_hash",
        "classifier_prompt_version",
        "context_L_packet_ids",
        "delta_logloss",
        "delta_utility",
        "delta_utility_source",
        "evaluator_id",
        "instance_id",
        "labels_source",
        "logloss_evaluator_id",
        "logprob_prompt_version",
        "metric_design",
        "target_y",
        "task_family",
        "utility_definition",
        "utility_evaluator_id",
        "utility_prediction_with_block",
        "utility_prediction_without_block",
        "utility_score_with_block",
        "utility_score_without_block",
    ):
        if field not in record or record.get(field) in (None, "", []):
            errors.append(f"missing_{field}")
    if record.get("task_family") != FIXB_TASK_FAMILY:
        errors.append("wrong_task_family")
    if record.get("metric_design") != METRIC_DESIGN:
        errors.append("wrong_metric_design")
    if record.get("delta_utility_source") != DELTA_UTILITY_SOURCE:
        errors.append("wrong_delta_utility_source")
    source = str(record.get("delta_utility_source") or "").casefold()
    if any(term in source for term in ("nll", "logprob", "logloss")):
        errors.append("delta_utility_source_uses_logloss_or_logprobs")
    if record.get("utility_definition") != UTILITY_DEFINITION:
        errors.append("wrong_utility_definition")
    if record.get("labels_source") != "hotpotqa_candidate_pool_gold_support_label":
        errors.append("labels_not_real_hotpotqa_support_labels")
    if record.get("logloss_evaluator_id") != LOGLOSS_EVALUATOR_ID:
        errors.append("wrong_logloss_evaluator_id")
    if record.get("utility_evaluator_id") != UTILITY_EVALUATOR_ID:
        errors.append("wrong_utility_evaluator_id")
    if record.get("evaluator_id") != record.get("logloss_evaluator_id"):
        errors.append("evaluator_id_must_match_logloss_evaluator_id")
    if record.get("classifier_prompt_version") != CLASSIFIER_PROMPT_VERSION:
        errors.append("wrong_classifier_prompt_version")
    if record.get("logprob_prompt_version") != LOGPROB_PROMPT_VERSION:
        errors.append("wrong_logprob_prompt_version")
    if record.get("target_y") not in {SUPPORTING, NON_SUPPORTING}:
        errors.append("invalid_target_y")
    if record.get("utility_prediction_with_block") not in {SUPPORTING, NON_SUPPORTING}:
        errors.append("invalid_utility_prediction_with_block")
    if record.get("utility_prediction_without_block") not in {SUPPORTING, NON_SUPPORTING}:
        errors.append("invalid_utility_prediction_without_block")
    if record.get("utility_score_with_block") not in {0, 1}:
        errors.append("invalid_utility_score_with_block")
    if record.get("utility_score_without_block") not in {0, 1}:
        errors.append("invalid_utility_score_without_block")
    if _finite_float(record.get("delta_logloss")) is None:
        errors.append("delta_logloss_not_numeric")
    delta_utility = _finite_float(record.get("delta_utility"))
    if delta_utility is None:
        errors.append("delta_utility_not_numeric")
    elif delta_utility not in {-1.0, 0.0, 1.0}:
        errors.append("delta_utility_not_accuracy_delta")
    return errors


def _all_close(values: Sequence[float], expected: Sequence[float], *, tolerance: float = 1e-12) -> bool:
    return len(values) == len(expected) and all(
        math.isclose(left, right, rel_tol=tolerance, abs_tol=tolerance)
        for left, right in zip(values, expected)
    )


def _affine_relation(xs: Sequence[float], ys: Sequence[float]) -> bool:
    points = [(x, y) for x, y in zip(xs, ys)]
    distinct_xs = sorted({x for x, _y in points})
    distinct_ys = sorted({y for _x, y in points})
    if len(points) < 3 or len(distinct_xs) < 3 or len(distinct_ys) < 2:
        return False
    first_x = distinct_xs[0]
    second_x = next(x for x in distinct_xs if not math.isclose(x, first_x, abs_tol=1e-12))
    first_y = next(y for x, y in points if math.isclose(x, first_x, abs_tol=1e-12))
    second_y = next(y for x, y in points if math.isclose(x, second_x, abs_tol=1e-12))
    slope = (second_y - first_y) / (second_x - first_x)
    intercept = first_y - (slope * first_x)
    return all(math.isclose(y, (slope * x) + intercept, rel_tol=1e-12, abs_tol=1e-12) for x, y in points)


def _rounded_relation(xs: Sequence[float], ys: Sequence[float]) -> bool:
    if len(xs) < 3 or len(set(ys)) < 2:
        return False
    return any(_all_close(ys, [round(x, digits) for x in xs]) for digits in range(0, 13))


def _clipped_relation(xs: Sequence[float], ys: Sequence[float]) -> bool:
    if len(xs) < 2 or len(set(ys)) < 2:
        return False
    return _all_close(ys, [max(-1.0, min(1.0, x)) for x in xs])


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) < 2 or len(ys) < 2:
        return None
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = math.sqrt(sum((x - x_mean) ** 2 for x in xs) * sum((y - y_mean) ** 2 for y in ys))
    if denominator == 0.0:
        return None
    return numerator / denominator


def non_circularity_metrics(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    xs = [float(record["delta_logloss"]) for record in records if _finite_float(record.get("delta_logloss")) is not None]
    ys = [float(record["delta_utility"]) for record in records if _finite_float(record.get("delta_utility")) is not None]
    equality_count = sum(
        math.isclose(float(record["delta_logloss"]), float(record["delta_utility"]), abs_tol=1e-12)
        for record in records
        if _finite_float(record.get("delta_logloss")) is not None and _finite_float(record.get("delta_utility")) is not None
    )
    distribution = {"-1": 0, "0": 0, "1": 0}
    for value in ys:
        distribution[str(int(value))] = distribution.get(str(int(value)), 0) + 1
    return {
        "affine_delta_utility_from_delta_logloss": not _affine_relation(xs, ys),
        "clipped_delta_utility_from_delta_logloss": not _clipped_relation(xs, ys),
        "correlation_delta_utility_delta_logloss": _pearson(xs, ys),
        "circular_delta_utility_matches_delta_logloss": not _all_close(xs, ys) if xs and ys else True,
        "delta_utility_distribution": distribution,
        "fraction_delta_utility_equals_delta_logloss": equality_count / len(records) if records else 0.0,
        "rounded_delta_utility_from_delta_logloss": not _rounded_relation(xs, ys),
    }


def validate_fixb_delta_records(records: Sequence[Mapping[str, Any]]) -> BridgeRowValidationResult:
    errors: list[str] = []
    xs: list[float] = []
    ys: list[float] = []
    for index, record in enumerate(records, start=1):
        record_errors = _required_record_errors(record)
        delta_logloss = _finite_float(record.get("delta_logloss"))
        delta_utility = _finite_float(record.get("delta_utility"))
        if delta_logloss is not None and delta_utility is not None:
            xs.append(delta_logloss)
            ys.append(delta_utility)
        errors.extend(f"row_{index}:{error}" for error in record_errors)
    if xs and ys:
        if _all_close(xs, ys):
            errors.append("circular_delta_utility_matches_delta_logloss")
        if _affine_relation(xs, ys):
            errors.append("affine_delta_utility_from_delta_logloss")
        if _rounded_relation(xs, ys):
            errors.append("rounded_delta_utility_from_delta_logloss")
        if _clipped_relation(xs, ys):
            errors.append("clipped_delta_utility_from_delta_logloss")
    return BridgeRowValidationResult(
        errors=tuple(errors),
        rows_generated=len(records),
        rows_validated=0 if errors else len(records),
        schema_valid=not errors,
    )


def _usage_from_scores(
    *,
    nll_without: LabelNllScore,
    nll_with: LabelNllScore,
    prediction_without: UtilityPrediction,
    prediction_with: UtilityPrediction,
) -> dict[str, int]:
    return {
        "api_classifier_calls": 2,
        "api_logloss_calls": 2,
        "completion_tokens": (
            nll_without.completion_tokens
            + nll_with.completion_tokens
            + prediction_without.completion_tokens
            + prediction_with.completion_tokens
        ),
        "prompt_tokens": (
            nll_without.prompt_tokens
            + nll_with.prompt_tokens
            + prediction_without.prompt_tokens
            + prediction_with.prompt_tokens
        ),
        "retries": nll_without.retries + nll_with.retries + prediction_without.retries + prediction_with.retries,
        "total_tokens": (
            nll_without.total_tokens
            + nll_with.total_tokens
            + prediction_without.total_tokens
            + prediction_with.total_tokens
        ),
    }


def _failure_type(failure: str) -> str:
    for part in failure.split(":"):
        if part.endswith("Error") or part.endswith("Exception") or part == "RemoteDisconnected":
            return part
    return "unknown"


def _sanitize_failure(failure: str) -> str:
    sanitized = failure.encode("ascii", errors="ignore").decode("ascii")
    return sanitized[:240]


def _failure_summary(failures: Sequence[str]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for failure in failures:
        failure_type = _failure_type(failure)
        counts[failure_type] = counts.get(failure_type, 0) + 1
    return {
        "api_failure_examples": [_sanitize_failure(failure) for failure in failures[:20]],
        "api_failure_reason_counts": dict(sorted(counts.items())),
        "api_failures": len(failures),
    }


def build_fixb_delta_records(
    candidate_pools: Sequence[Mapping[str, Any]],
    *,
    logloss_scorer: LoglossScorer,
    utility_classifier: UtilityClassifier,
    max_instances: int = 150,
    max_workers: int = 1,
    records_per_instance: int = 4,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    specs = make_support_classification_specs(
        candidate_pools,
        max_instances=max_instances,
        records_per_instance=records_per_instance,
    )
    failures: list[str] = []
    records: list[dict[str, Any]] = []
    usage_totals = {
        "api_classifier_calls": 0,
        "api_logloss_calls": 0,
        "completion_tokens": 0,
        "prompt_tokens": 0,
        "retries": 0,
        "total_tokens": 0,
    }

    def score_spec(spec: SupportClassificationSpec) -> tuple[dict[str, Any] | None, dict[str, int], str | None]:
        try:
            nll_without = logloss_scorer(spec=spec, label=spec.target_y, with_block=False)
            nll_with = logloss_scorer(spec=spec, label=spec.target_y, with_block=True)
            prediction_without = utility_classifier(spec=spec, with_block=False)
            prediction_with = utility_classifier(spec=spec, with_block=True)
        except Exception as exc:  # noqa: BLE001 - fail-closed generation report keeps sanitized failure reasons.
            return None, {}, f"{spec.instance_id}:{type(exc).__name__}:{exc}"
        return (
            _record_from_scores(
                spec,
                nll_with=nll_with,
                nll_without=nll_without,
                prediction_with=prediction_with,
                prediction_without=prediction_without,
            ),
            _usage_from_scores(
                nll_with=nll_with,
                nll_without=nll_without,
                prediction_with=prediction_with,
                prediction_without=prediction_without,
            ),
            None,
        )

    if max_workers <= 1:
        results = [score_spec(spec) for spec in specs]
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(score_spec, spec) for spec in specs]
            results = [future.result() for future in as_completed(futures)]

    for record, usage, failure in results:
        if failure is not None:
            failures.append(failure)
            continue
        if record is None:
            continue
        records.append(record)
        for key in usage_totals:
            usage_totals[key] += int(usage.get(key) or 0)
    records = sorted(
        records,
        key=lambda row: (
            row["dataset"],
            row["task_family"],
            row["instance_id"],
            tuple(row["context_L_packet_ids"]),
            tuple(row["block_A_packet_ids"]),
        ),
    )
    validation = validate_fixb_delta_records(records)
    metrics = non_circularity_metrics(records)
    failures_payload = _failure_summary(failures)
    report = {
        **failures_payload,
        "api_retries": usage_totals["retries"],
        "api_score_calls": usage_totals["api_classifier_calls"] + usage_totals["api_logloss_calls"],
        "claim_status": CLAIM_STATUS,
        "classifier_prompt_version": CLASSIFIER_PROMPT_VERSION,
        "completion_tokens": usage_totals["completion_tokens"],
        "delta_logloss_source": "live_api_support_label_nll_without_minus_with_block",
        "delta_records_generated": len(records),
        "delta_records_validated": validation.rows_validated,
        "delta_utility_source": DELTA_UTILITY_SOURCE,
        "evaluator": {
            "classifier": {
                "decoding_policy": DECODING_POLICY,
                "enable_thinking": False,
                "endpoint_type": "openai_compatible_chat_completions",
                "logprobs_supported": False,
                "materialization_policy": DEFAULT_MATERIALIZATION_POLICY,
                "model_name": MODEL_NAME,
                "provider": "dashscope",
                "temperature": 0,
                "top_p": 1,
                "utility_evaluator_id": UTILITY_EVALUATOR_ID,
            },
            "logloss": {
                "decoding_policy": DECODING_POLICY,
                "enable_thinking": False,
                "endpoint_type": "openai_compatible_chat_completions_logprobs",
                "logloss_evaluator_id": LOGLOSS_EVALUATOR_ID,
                "logprobs_supported": True,
                "materialization_policy": DEFAULT_MATERIALIZATION_POLICY,
                "model_name": MODEL_NAME,
                "provider": "dashscope",
                "temperature": 0,
                "top_logprobs": 0,
                "top_p": 1,
            },
        },
        "instances_attempted": len({spec.original_instance_id for spec in specs}),
        "instances_used": len({row["original_instance_id"] for row in records}),
        "logprob_prompt_version": LOGPROB_PROMPT_VERSION,
        "metric_claim_level": "no_claim_upgrade",
        "metric_design": METRIC_DESIGN,
        "non_circularity_checks": metrics,
        "phase": "P63R-FixB",
        "prompt_tokens": usage_totals["prompt_tokens"],
        "records_attempted": len(specs),
        "status": "fixb_delta_records_generated" if validation.schema_valid else "fixb_delta_records_invalid",
        "total_tokens": usage_totals["total_tokens"],
        "unique_instances": len({row["instance_id"] for row in records}),
        "utility_definition": UTILITY_DEFINITION,
        "utility_prediction_distribution": metrics["delta_utility_distribution"],
        "validation_errors": list(validation.errors),
    }
    if not validation.schema_valid:
        raise ValueError(";".join(validation.errors))
    return records, report


def build_fixb_rows(delta_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in delta_records:
        context_ids = tuple(str(packet_id) for packet_id in record["context_L_packet_ids"])
        block_ids = tuple(str(packet_id) for packet_id in record["block_A_packet_ids"])
        row = P55BridgeRow(
            active_stratum=str(record["active_stratum"]),
            block_A_packet_ids=block_ids,
            block_size=int(record["block_size"]),
            candidate_pool_hash=str(record["candidate_pool_hash"]),
            candidate_slice_band=str(record["candidate_slice_band"]),
            contamination_status=str(record["contamination_status"]),
            context_L_packet_ids=context_ids,
            dataset=str(record["dataset"]),
            decoding_policy=str(record["decoding_policy"]),
            delta_logloss=float(record["delta_logloss"]),
            delta_utility=float(record["delta_utility"]),
            evaluator_id=str(record["evaluator_id"]),
            instance_id=str(record["instance_id"]),
            materialization_policy=str(record["materialization_policy"]),
            materialized_context_hash=make_materialized_context_hash(context_ids, block_ids),
            model_tier=str(record["model_tier"]),
            replicate_count=int(record["replicate_count"]),
            target_y=str(record["target_y"]),
            task_family=str(record["task_family"]),
        )
        rows.append(row.to_payload())
    return sorted(rows, key=lambda row: (row["dataset"], row["task_family"], row["instance_id"]))


def _write_jsonl(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(canonical_json_dumps(dict(row)) + "\n" for row in rows),
        encoding="utf-8",
    )
    return output_path


def write_fixb_outputs(
    *,
    delta_records: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    report: Mapping[str, Any],
    delta_records_path: str | Path = DEFAULT_DELTA_RECORDS_PATH,
    operator_rows_path: str | Path = DEFAULT_OPERATOR_ROWS_PATH,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> dict[str, str]:
    _write_jsonl(delta_records_path, delta_records)
    write_bridge_row_jsonl(operator_rows_path, rows)
    write_canonical_json(report_path, report)
    return {
        "delta_records": Path(delta_records_path).as_posix(),
        "operator_rows": Path(operator_rows_path).as_posix(),
        "report": Path(report_path).as_posix(),
    }


def _write_fixb_markdown_report(
    path: str | Path,
    *,
    generation_report: Mapping[str, Any],
    calibration_result: Mapping[str, Any],
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P63R-FixB HotpotQA Independent Support Utility Bridge",
        "",
        "## Purpose",
        "",
        "P63R-FixB is a non-circular HotpotQA support-classification bridge attempt.",
        "It separates support-label NLL scoring from independent support-label classifier correctness utility.",
        "",
        "## Design",
        "",
        f"- Task family: `{FIXB_TASK_FAMILY}`",
        f"- Metric design: `{METRIC_DESIGN}`",
        f"- `delta_logloss`: support-label NLL improvement from `{LOGLOSS_EVALUATOR_ID}`.",
        f"- `delta_utility`: `{UTILITY_DEFINITION}` from `{UTILITY_EVALUATOR_ID}`.",
        f"- Utility source: `{DELTA_UTILITY_SOURCE}`.",
        f"- Logprob prompt version: `{LOGPROB_PROMPT_VERSION}`",
        f"- Classifier prompt version: `{CLASSIFIER_PROMPT_VERSION}`",
        "- Utility does not use NLL, logprobs, `delta_logloss`, ranks, clipping, rounding, or affine transforms.",
        "",
        "## Artifacts",
        "",
        f"- Delta records: `{DEFAULT_DELTA_RECORDS_PATH}`",
        f"- Generation report: `{DEFAULT_REPORT_PATH}`",
        f"- Operator rows: `{DEFAULT_OPERATOR_ROWS_PATH}`",
        f"- Calibration output: `{DEFAULT_CALIBRATION_OUTPUT_DIR}`",
        "",
        "## Results",
        "",
        f"- Delta records validated: `{generation_report.get('delta_records_validated')}`",
        f"- Operator rows validated: `{generation_report.get('operator_rows_validated')}`",
        f"- Unique instances: `{calibration_result.get('unique_instances')}`",
        f"- Gate result: `{calibration_result.get('gate_result')}`",
        f"- Metric claim level: `{calibration_result.get('metric_claim_level')}`",
        f"- Claim status: `{calibration_result.get('claim_status')}`",
        f"- Sign agreement: `{calibration_result.get('sign_agreement')}`",
        f"- Spearman rho: `{calibration_result.get('spearman_rho')}`",
        f"- Normalized residual: `{calibration_result.get('normalized_residual')}`",
        "",
        "## Claim Boundary",
        "",
        "- No final `calibrated_proxy_supported` claim is introduced here.",
        "- No `vinfo_proxy_supported` claim is introduced here.",
        "- No measurement validation, paper evidence, P56 unblock, or selector superiority claim is introduced here.",
        "- This package requires independent review before any claim-ledger, manuscript, P56, P65, or P66 work.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def run_fixb_pipeline(
    *,
    candidate_pools_path: str | Path = DEFAULT_CANDIDATE_POOLS_PATH,
    delta_records_path: str | Path = DEFAULT_DELTA_RECORDS_PATH,
    operator_rows_path: str | Path = DEFAULT_OPERATOR_ROWS_PATH,
    report_path: str | Path = DEFAULT_REPORT_PATH,
    calibration_output_dir: str | Path = DEFAULT_CALIBRATION_OUTPUT_DIR,
    report_md_path: str | Path = DEFAULT_REPORT_MD,
    env_path: str | Path | None = ".env",
    max_instances: int = 150,
    max_workers: int = 4,
    records_per_instance: int = 4,
    logloss_scorer: LoglossScorer | None = None,
    utility_classifier: UtilityClassifier | None = None,
) -> dict[str, Any]:
    candidate_pools = _read_jsonl(candidate_pools_path)
    logloss_scorer = logloss_scorer or make_dashscope_logloss_scorer(env_path=env_path)
    utility_classifier = utility_classifier or make_dashscope_utility_classifier(env_path=env_path)
    delta_records, report = build_fixb_delta_records(
        candidate_pools,
        logloss_scorer=logloss_scorer,
        max_instances=max_instances,
        max_workers=max_workers,
        records_per_instance=records_per_instance,
        utility_classifier=utility_classifier,
    )
    rows = build_fixb_rows(delta_records)
    row_validation = validate_bridge_rows(rows)
    report = {
        **report,
        "candidate_pools_path": Path(candidate_pools_path).as_posix(),
        "delta_records_path": Path(delta_records_path).as_posix(),
        "operator_rows_generated": len(rows),
        "operator_rows_path": Path(operator_rows_path).as_posix(),
        "operator_rows_validated": row_validation.rows_validated,
        "row_validation_errors": list(row_validation.errors),
    }
    if not row_validation.schema_valid:
        raise ValueError(";".join(row_validation.errors))
    write_fixb_outputs(
        delta_records=delta_records,
        rows=rows,
        report=report,
        delta_records_path=delta_records_path,
        operator_rows_path=operator_rows_path,
        report_path=report_path,
    )
    calibration = run_p63r_hotpotqa_bridge_calibration(
        input_rows_jsonl=operator_rows_path,
        output_dir=calibration_output_dir,
        config=P63RCalibrationConfig(
            calibration_epoch=DEFAULT_CALIBRATION_EPOCH,
            evaluator_id=LOGLOSS_EVALUATOR_ID,
            metric_family=METRIC_FAMILY,
            task_family=FIXB_TASK_FAMILY,
        ),
    )
    _write_fixb_markdown_report(
        report_md_path,
        generation_report=report,
        calibration_result=calibration,
    )
    return {
        **calibration,
        "api_failures": int(report["api_failures"]),
        "api_retries": report["api_retries"],
        "api_score_calls": report["api_score_calls"],
        "delta_records_generated": len(delta_records),
        "delta_records_validated": report["delta_records_validated"],
        "logloss_evaluator_id": LOGLOSS_EVALUATOR_ID,
        "operator_rows_generated": len(rows),
        "operator_rows_validated": row_validation.rows_validated,
        "total_tokens": report["total_tokens"],
        "utility_evaluator_id": UTILITY_EVALUATOR_ID,
        "utility_prediction_distribution": report["utility_prediction_distribution"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate P63R-FixB HotpotQA independent-utility bridge rows.")
    parser.add_argument("--candidate-pools-path", default=DEFAULT_CANDIDATE_POOLS_PATH)
    parser.add_argument("--delta-records-path", default=DEFAULT_DELTA_RECORDS_PATH)
    parser.add_argument("--operator-rows-path", default=DEFAULT_OPERATOR_ROWS_PATH)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--calibration-output-dir", default=DEFAULT_CALIBRATION_OUTPUT_DIR)
    parser.add_argument("--report-md-path", default=DEFAULT_REPORT_MD)
    parser.add_argument("--env-path", default=".env")
    parser.add_argument("--max-instances", type=int, default=150)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--records-per-instance", type=int, default=4)
    args = parser.parse_args(argv)
    result = run_fixb_pipeline(
        calibration_output_dir=args.calibration_output_dir,
        candidate_pools_path=args.candidate_pools_path,
        delta_records_path=args.delta_records_path,
        env_path=args.env_path,
        max_instances=args.max_instances,
        max_workers=args.max_workers,
        operator_rows_path=args.operator_rows_path,
        records_per_instance=args.records_per_instance,
        report_md_path=args.report_md_path,
        report_path=args.report_path,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
