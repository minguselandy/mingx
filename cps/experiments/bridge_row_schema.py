from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.hashing import canonical_json_dumps
from cps.benchmarks.hashing import stable_hash


ACTIVE_STRATUM = "evidence_packet_selection_microtask_v1"
TASK_FAMILY = "fever_claim_verification"
DATASET = "FEVER"
HOTPOTQA_TASK_FAMILY = "hotpotqa_answer_support_selection"
HOTPOTQA_SUPPORT_CLASSIFICATION_TASK_FAMILY = "hotpotqa_supporting_fact_classification_bridge"
HOTPOTQA_SUPPORT_INDEPENDENT_UTILITY_TASK_FAMILY = "hotpotqa_support_classification_independent_utility"
HOTPOTQA_DATASET = "HotpotQA"
DEFAULT_MODEL_TIER = "fixed_local_or_operator_approved_evaluator"
DEFAULT_MATERIALIZATION_POLICY = "fixed_selector_order_with_source_boundaries"
DEFAULT_CANDIDATE_SLICE_BAND = "top_20"
DEFAULT_HOTPOTQA_CANDIDATE_SLICE_BAND = "hotpotqa_distractor_context"
DEFAULT_DECODING_POLICY = "deterministic_or_documented"
DEFAULT_OPERATOR_ROWS_PATH = "artifacts/operator_inputs/p55_evidence_packet_selection_microtask_v1_rows.jsonl"
ALLOWED_TARGETS = {"SUPPORTED", "REFUTED", "NOTENOUGHINFO"}
ALLOWED_BLOCK_SIZES = {1, 2}
ALLOWED_CONTAMINATION_STATUSES = {"clean", "ambiguous", "failed"}
SUPPORTED_DATASET_TASKS = {
    DATASET: frozenset({TASK_FAMILY}),
    HOTPOTQA_DATASET: frozenset(
        {
            HOTPOTQA_TASK_FAMILY,
            HOTPOTQA_SUPPORT_CLASSIFICATION_TASK_FAMILY,
            HOTPOTQA_SUPPORT_INDEPENDENT_UTILITY_TASK_FAMILY,
        }
    ),
}


def dataset_task_supported(dataset: str, task_family: str) -> bool:
    return task_family in SUPPORTED_DATASET_TASKS.get(dataset, frozenset())


@dataclass(frozen=True)
class P55BridgeRow:
    active_stratum: str
    task_family: str
    dataset: str
    instance_id: str
    model_tier: str
    materialization_policy: str
    candidate_slice_band: str
    block_size: int
    context_L_packet_ids: tuple[str, ...]
    block_A_packet_ids: tuple[str, ...]
    target_y: str
    delta_logloss: float
    delta_utility: float
    replicate_count: int
    decoding_policy: str
    evaluator_id: str
    candidate_pool_hash: str
    materialized_context_hash: str
    contamination_status: str

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["context_L_packet_ids"] = list(self.context_L_packet_ids)
        payload["block_A_packet_ids"] = list(self.block_A_packet_ids)
        return payload


@dataclass(frozen=True, order=True)
class BridgeRowKey:
    active_stratum: str
    task_family: str
    dataset: str
    instance_id: str
    candidate_pool_hash: str
    context_L_packet_ids: tuple[str, ...]
    block_A_packet_ids: tuple[str, ...]
    target_y: str
    model_tier: str
    materialization_policy: str
    candidate_slice_band: str
    block_size: int
    decoding_policy: str
    evaluator_id: str


def make_materialized_context_hash(
    context_L_packet_ids: Sequence[str],
    block_A_packet_ids: Sequence[str],
) -> str:
    return stable_hash(
        {
            "block_A_packet_ids": [str(packet_id) for packet_id in block_A_packet_ids],
            "context_L_packet_ids": [str(packet_id) for packet_id in context_L_packet_ids],
        }
    )


def _string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(packet_id).strip() for packet_id in value if str(packet_id).strip())


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def bridge_row_key(row: P55BridgeRow | Mapping[str, Any]) -> BridgeRowKey:
    payload = _payload(row)
    return BridgeRowKey(
        active_stratum=str(payload.get("active_stratum", "")),
        task_family=str(payload.get("task_family", "")),
        dataset=str(payload.get("dataset", "")),
        instance_id=str(payload.get("instance_id", "")),
        candidate_pool_hash=str(payload.get("candidate_pool_hash", "")),
        context_L_packet_ids=_string_tuple(payload.get("context_L_packet_ids", [])),
        block_A_packet_ids=_string_tuple(payload.get("block_A_packet_ids", [])),
        target_y=str(payload.get("target_y", "")),
        model_tier=str(payload.get("model_tier", "")),
        materialization_policy=str(payload.get("materialization_policy", "")),
        candidate_slice_band=str(payload.get("candidate_slice_band", "")),
        block_size=_int_value(payload.get("block_size")),
        decoding_policy=str(payload.get("decoding_policy", "")),
        evaluator_id=str(payload.get("evaluator_id", "")),
    )


def delta_record_key(record: Mapping[str, Any]) -> BridgeRowKey:
    return BridgeRowKey(
        active_stratum=str(record.get("active_stratum", "")),
        task_family=str(record.get("task_family", "")),
        dataset=str(record.get("dataset", "")),
        instance_id=str(record.get("instance_id", "")),
        candidate_pool_hash=str(record.get("candidate_pool_hash", "")),
        context_L_packet_ids=_string_tuple(record.get("context_L_packet_ids", [])),
        block_A_packet_ids=_string_tuple(record.get("block_A_packet_ids", [])),
        target_y=str(record.get("target_y", "")),
        model_tier=str(record.get("model_tier", "")),
        materialization_policy=str(record.get("materialization_policy", "")),
        candidate_slice_band=str(record.get("candidate_slice_band", "")),
        block_size=_int_value(record.get("block_size")),
        decoding_policy=str(record.get("decoding_policy", "")),
        evaluator_id=str(record.get("evaluator_id", "")),
    )


def row_identity(row: P55BridgeRow | Mapping[str, Any]) -> BridgeRowKey:
    return bridge_row_key(row)


def _payload(row: P55BridgeRow | Mapping[str, Any]) -> dict[str, Any]:
    return row.to_payload() if isinstance(row, P55BridgeRow) else dict(row)


def canonical_bridge_row_jsonl(rows: Sequence[P55BridgeRow | Mapping[str, Any]]) -> str:
    payloads = sorted((_payload(row) for row in rows), key=bridge_row_key)
    return "".join(canonical_json_dumps(payload) + "\n" for payload in payloads)


def write_bridge_row_jsonl(path: str | Path, rows: Sequence[P55BridgeRow | Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonical_bridge_row_jsonl(rows), encoding="utf-8")
    return output_path


def write_canonical_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path
