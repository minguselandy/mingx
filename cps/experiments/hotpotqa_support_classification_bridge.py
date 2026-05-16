from __future__ import annotations

import argparse
import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from dataclasses import asdict
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
from cps.experiments.bridge_row_schema import HOTPOTQA_SUPPORT_CLASSIFICATION_TASK_FAMILY
from cps.experiments.bridge_row_schema import P55BridgeRow
from cps.experiments.bridge_row_schema import make_materialized_context_hash
from cps.experiments.bridge_row_schema import write_bridge_row_jsonl
from cps.experiments.bridge_row_schema import write_canonical_json
from cps.experiments.bridge_row_validation import validate_bridge_rows


SUPPORT_CLASSIFICATION_TASK_FAMILY = HOTPOTQA_SUPPORT_CLASSIFICATION_TASK_FAMILY
SUPPORTING = "SUPPORTING"
NON_SUPPORTING = "NON_SUPPORTING"
MODEL_TIER = "approved_live_logprob_model_v1"
DECODING_POLICY = "deterministic_logprob_scoring_v1"
CANDIDATE_SLICE_BAND = "hotpotqa_support_classification_context"
EVALUATOR_ID = (
    "approved_live_api_logprob_endpoint::dashscope::qwen3.6-flash"
    "::support_classification_logprob_v1"
)
MODEL_NAME = "qwen3.6-flash"
DEFAULT_CANDIDATE_POOLS_PATH = "artifacts/benchmarks/hotpotqa_candidate_pools.jsonl"
DEFAULT_DELTA_RECORDS_PATH = "artifacts/benchmarks/hotpotqa_support_classification_delta_records.jsonl"
DEFAULT_OPERATOR_ROWS_PATH = "artifacts/operator_inputs/p55_hotpotqa_support_classification_rows.jsonl"
DEFAULT_REPORT_PATH = "artifacts/benchmarks/hotpotqa_support_classification_delta_generation_report.json"
POSITIVE_CONTROL_ONLY = "positive_control_only"
CIRCULAR_ALIGNMENT_CONTROL = "circular_alignment_control"
NOT_METRIC_BRIDGE_EVIDENCE = "not_metric_bridge_evidence"
POSITIVE_CONTROL_CLAIM_STATUS = (
    "positive_control_only; circular_alignment_control; "
    "not_metric_bridge_evidence; no_claim_upgrade"
)
POSITIVE_CONTROL_RELABEL_REASON = (
    "delta_utility is round(delta_logloss, 12), so FixA is a circular "
    "positive-control diagnostic rather than independent metric bridge evidence"
)


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
    task_family: str = SUPPORT_CLASSIFICATION_TASK_FAMILY
    dataset: str = HOTPOTQA_DATASET
    active_stratum: str = ACTIVE_STRATUM
    materialization_policy: str = DEFAULT_MATERIALIZATION_POLICY
    candidate_slice_band: str = CANDIDATE_SLICE_BAND
    model_tier: str = MODEL_TIER
    decoding_policy: str = DECODING_POLICY
    evaluator_id: str = EVALUATOR_ID

    @property
    def context_L_packet_ids(self) -> tuple[str, ...]:
        return (self.target_packet_id,)


@dataclass(frozen=True)
class SupportLabelNll:
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


SupportLabelScorer = Callable[..., SupportLabelNll]


def relabel_fixa_positive_control(payload: Mapping[str, Any]) -> dict[str, Any]:
    relabeled = dict(payload)
    reason_codes = set(str(reason) for reason in relabeled.get("reason_codes", []) or [])
    reason_codes.update({CIRCULAR_ALIGNMENT_CONTROL, NOT_METRIC_BRIDGE_EVIDENCE})
    relabeled.update(
        {
            CIRCULAR_ALIGNMENT_CONTROL: True,
            NOT_METRIC_BRIDGE_EVIDENCE: True,
            POSITIVE_CONTROL_ONLY: True,
            "calibrated_proxy_supported": False,
            "calibrated_proxy_supported_candidate": False,
            "claim_status": POSITIVE_CONTROL_CLAIM_STATUS,
            "measurement_validation": False,
            "metric_bridge_support": False,
            "metric_claim_level": POSITIVE_CONTROL_ONLY,
            "paper_evidence": False,
            "gate_result": POSITIVE_CONTROL_ONLY,
            "review_relabel_reason": POSITIVE_CONTROL_RELABEL_REASON,
            "vinfo_proxy_supported": False,
        }
    )
    relabeled["reason_codes"] = sorted(reason_codes)
    return relabeled


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
    raw_label = str(packet.get("gold_support_label") or "")
    if raw_label == "gold_supporting":
        return SUPPORTING
    if raw_label in {"same_context_distractor", "retrieved_distractor", "random_distractor"}:
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
        selected_targets = [*supporting[:2], *non_supporting[:2]][:records_per_instance]
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
            row_instance_id = f"{instance_id}::support_cls::{_short_id(target_packet_id)}"
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


def _support_prompt(spec: SupportClassificationSpec, *, with_block: bool) -> str:
    context = "\n".join(
        f"- {content}" for content in (spec.block_A_contents if with_block else ())
    )
    return (
        "Classify whether the candidate sentence is one of the HotpotQA supporting facts for the question.\n"
        "Use only the question, candidate sentence, and optional context sentences.\n"
        "Allowed labels: SUPPORTING or NON_SUPPORTING.\n\n"
        f"Question: {spec.question}\n"
        f"Candidate sentence: {spec.target_packet_content}\n"
        f"Optional context:\n{context if context else '(none)'}\n\n"
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


def make_dashscope_support_label_scorer(
    *,
    env_path: str | Path | None = ".env",
    model: str = MODEL_NAME,
    max_attempts: int = 3,
    sleep_seconds: float = 2.0,
) -> SupportLabelScorer:
    env = _load_env_values(env_path)
    api_key = env.get("DASHSCOPE_API_KEY") or env.get("API_KEY")
    base_url = env.get("DASHSCOPE_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if not api_key:
        raise RuntimeError("missing DASHSCOPE_API_KEY for approved support-classification logprob evaluator")

    def score(*, spec: SupportClassificationSpec, label: str, with_block: bool) -> SupportLabelNll:
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
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
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
                    response_payload = json.loads(response.read().decode("utf-8"))
                choice = response_payload["choices"][0]
                message = choice.get("message") or {}
                if message.get("reasoning_content"):
                    raise ValueError("support classifier response used reasoning_content")
                content = str(message.get("content") or "").strip()
                if content != label:
                    raise ValueError(f"support classifier emitted {content!r}, expected {label!r}")
                logprobs = message.get("logprobs") or choice.get("logprobs") or {}
                items = logprobs.get("content") or []
                token_logprobs = tuple(float(item["logprob"]) for item in items if "logprob" in item)
                if not token_logprobs:
                    raise ValueError("support classifier response lacks token logprobs")
                if len(token_logprobs) >= 2 and all(abs(value) <= 1e-12 for value in token_logprobs):
                    raise ValueError("support classifier returned degenerate all-zero logprobs")
                usage = response_payload.get("usage") or {}
                return SupportLabelNll(
                    completion_tokens=int(usage.get("completion_tokens") or 0),
                    prompt_tokens=int(usage.get("prompt_tokens") or 0),
                    raw_content=content,
                    retries=attempt - 1,
                    target_label=label,
                    token_logprobs=token_logprobs,
                    total_tokens=int(usage.get("total_tokens") or 0),
                )
            except (error.HTTPError, error.URLError, ValueError, KeyError, TypeError) as exc:
                last_error = exc
                if attempt >= max_attempts:
                    break
                time.sleep(sleep_seconds * attempt)
        raise RuntimeError(f"support label NLL scoring failed: {last_error}") from last_error

    return score


def _delta_record_from_scores(
    spec: SupportClassificationSpec,
    *,
    nll_without: SupportLabelNll,
    nll_with: SupportLabelNll,
) -> dict[str, Any]:
    delta_logloss = nll_without.nll - nll_with.nll
    return {
        "active_stratum": spec.active_stratum,
        "block_A_packet_ids": list(spec.block_A_packet_ids),
        "block_size": 1,
        "candidate_pool_hash": spec.candidate_pool_hash,
        "candidate_slice_band": spec.candidate_slice_band,
        "contamination_status": "clean",
        "context_L_packet_ids": list(spec.context_L_packet_ids),
        "dataset": spec.dataset,
        "decoding_policy": spec.decoding_policy,
        "delta_logloss": round(delta_logloss, 12),
        "delta_logloss_source": "measured_support_label_logprob",
        "delta_utility": round(delta_logloss, 12),
        "evaluator_id": spec.evaluator_id,
        "instance_id": spec.instance_id,
        "materialization_policy": spec.materialization_policy,
        "model_tier": spec.model_tier,
        "original_instance_id": spec.original_instance_id,
        "replicate_count": 1,
        "support_classification_utility": "negative_support_label_nll",
        "target_packet_id": spec.target_packet_id,
        "target_y": spec.target_y,
        "task_family": spec.task_family,
    }


def build_support_classification_delta_records(
    specs: Sequence[SupportClassificationSpec],
    *,
    scorer: SupportLabelScorer,
    max_workers: int = 1,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    retries = 0
    score_calls = 0

    def score_spec(spec: SupportClassificationSpec) -> tuple[dict[str, Any] | None, dict[str, int], str | None]:
        try:
            without = scorer(spec=spec, label=spec.target_y, with_block=False)
            with_block = scorer(spec=spec, label=spec.target_y, with_block=True)
        except Exception as exc:  # noqa: BLE001 - generation report needs the exact fail-closed reason.
            return None, {}, f"{spec.instance_id}:{type(exc).__name__}:{exc}"
        usage = {
            "completion_tokens": without.completion_tokens + with_block.completion_tokens,
            "prompt_tokens": without.prompt_tokens + with_block.prompt_tokens,
            "retries": without.retries + with_block.retries,
            "score_calls": 2,
            "total_tokens": without.total_tokens + with_block.total_tokens,
        }
        return _delta_record_from_scores(spec, nll_without=without, nll_with=with_block), usage, None

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
        score_calls += int(usage["score_calls"])
        prompt_tokens += int(usage["prompt_tokens"])
        completion_tokens += int(usage["completion_tokens"])
        total_tokens += int(usage["total_tokens"])
        retries += int(usage["retries"])
        records.append(record)
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
    return records, {
        "api_failures": failures,
        "api_retries": retries,
        "api_score_calls": score_calls,
        "claim_status": POSITIVE_CONTROL_CLAIM_STATUS,
        "completion_tokens": completion_tokens,
        CIRCULAR_ALIGNMENT_CONTROL: True,
        "delta_records_generated": len(records),
        "delta_records_validated": len(records),
        "evaluator": {
            "decoding_policy": DECODING_POLICY,
            "enable_thinking": False,
            "endpoint_type": "openai_compatible_chat_completions_logprobs",
            "evaluator_id": EVALUATOR_ID,
            "logprobs_supported": True,
            "materialization_policy": DEFAULT_MATERIALIZATION_POLICY,
            "model_name": MODEL_NAME,
            "model_tier": MODEL_TIER,
            "provider": "dashscope",
            "temperature": 0,
            "top_logprobs": 0,
            "top_p": 1,
        },
        "instances_used": len({row["original_instance_id"] for row in records}),
        "metric_design": {
            "delta_logloss": "support_label_nll_without_block_minus_with_block",
            "delta_utility": "round(delta_logloss, 12)",
            "interpretation": "circular_positive_control_not_metric_bridge_evidence",
            "target_y": "SUPPORTING_or_NON_SUPPORTING",
        },
        "metric_claim_level": POSITIVE_CONTROL_ONLY,
        NOT_METRIC_BRIDGE_EVIDENCE: True,
        "phase": "P63R-FixA",
        POSITIVE_CONTROL_ONLY: True,
        "prompt_tokens": prompt_tokens,
        "review_relabel_reason": POSITIVE_CONTROL_RELABEL_REASON,
        "status": "support_classification_delta_records_generated",
        "total_tokens": total_tokens,
    }


def build_support_classification_rows(delta_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in delta_records:
        block_ids = tuple(str(packet_id) for packet_id in record["block_A_packet_ids"])
        context_ids = tuple(str(packet_id) for packet_id in record["context_L_packet_ids"])
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


def write_support_classification_outputs(
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


def run_support_classification_generation(
    *,
    candidate_pools_jsonl: str | Path = DEFAULT_CANDIDATE_POOLS_PATH,
    delta_records_path: str | Path = DEFAULT_DELTA_RECORDS_PATH,
    operator_rows_path: str | Path = DEFAULT_OPERATOR_ROWS_PATH,
    report_path: str | Path = DEFAULT_REPORT_PATH,
    max_instances: int = 150,
    records_per_instance: int = 4,
    env_path: str | Path | None = ".env",
    max_workers: int = 4,
) -> dict[str, Any]:
    candidate_pools = _read_jsonl(candidate_pools_jsonl)
    specs = make_support_classification_specs(
        candidate_pools,
        max_instances=max_instances,
        records_per_instance=records_per_instance,
    )
    scorer = make_dashscope_support_label_scorer(env_path=env_path)
    delta_records, report = build_support_classification_delta_records(
        specs,
        scorer=scorer,
        max_workers=max_workers,
    )
    rows = build_support_classification_rows(delta_records)
    validation = validate_bridge_rows(rows)
    report = {
        **report,
        "candidate_pools_path": Path(candidate_pools_jsonl).as_posix(),
        "delta_records_path": Path(delta_records_path).as_posix(),
        "operator_rows_path": Path(operator_rows_path).as_posix(),
        "operator_rows_generated": len(rows),
        "operator_rows_validated": validation.rows_validated,
        "validation_errors": list(validation.errors),
    }
    if not validation.schema_valid:
        raise RuntimeError(";".join(validation.errors))
    write_support_classification_outputs(
        delta_records=delta_records,
        rows=rows,
        report=report,
        delta_records_path=delta_records_path,
        operator_rows_path=operator_rows_path,
        report_path=report_path,
    )
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate P63R-FixA HotpotQA support-classification bridge rows.")
    parser.add_argument("--candidate-pools-jsonl", default=DEFAULT_CANDIDATE_POOLS_PATH)
    parser.add_argument("--delta-records-path", default=DEFAULT_DELTA_RECORDS_PATH)
    parser.add_argument("--operator-rows-path", default=DEFAULT_OPERATOR_ROWS_PATH)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--max-instances", type=int, default=150)
    parser.add_argument("--records-per-instance", type=int, default=4)
    parser.add_argument("--env-path", default=".env")
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args(argv)
    report = run_support_classification_generation(
        candidate_pools_jsonl=args.candidate_pools_jsonl,
        delta_records_path=args.delta_records_path,
        operator_rows_path=args.operator_rows_path,
        report_path=args.report_path,
        max_instances=args.max_instances,
        records_per_instance=args.records_per_instance,
        env_path=args.env_path,
        max_workers=args.max_workers,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
