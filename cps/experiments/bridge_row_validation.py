from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.hashing import has_absolute_local_path
from cps.experiments.bridge_row_schema import ACTIVE_STRATUM
from cps.experiments.bridge_row_schema import ALLOWED_BLOCK_SIZES
from cps.experiments.bridge_row_schema import ALLOWED_CONTAMINATION_STATUSES
from cps.experiments.bridge_row_schema import ALLOWED_TARGETS
from cps.experiments.bridge_row_schema import BridgeRowKey
from cps.experiments.bridge_row_schema import DATASET
from cps.experiments.bridge_row_schema import P55BridgeRow
from cps.experiments.bridge_row_schema import SUPPORTED_DATASET_TASKS
from cps.experiments.bridge_row_schema import TASK_FAMILY
from cps.experiments.bridge_row_schema import bridge_row_key
from cps.experiments.bridge_row_schema import dataset_task_supported
from cps.experiments.bridge_row_schema import make_materialized_context_hash


REQUIRED_FIELDS = (
    "active_stratum",
    "task_family",
    "dataset",
    "instance_id",
    "model_tier",
    "materialization_policy",
    "candidate_slice_band",
    "block_size",
    "context_L_packet_ids",
    "block_A_packet_ids",
    "target_y",
    "delta_logloss",
    "delta_utility",
    "replicate_count",
    "decoding_policy",
    "evaluator_id",
    "candidate_pool_hash",
    "materialized_context_hash",
    "contamination_status",
)


class BridgeRowValidationError(ValueError):
    """Raised when a P62R bridge row fails validation."""


@dataclass(frozen=True)
class BridgeRowValidationResult:
    rows_generated: int
    rows_validated: int
    schema_valid: bool
    errors: tuple[str, ...]


def _payload(row: P55BridgeRow | Mapping[str, Any]) -> dict[str, Any]:
    return row.to_payload() if isinstance(row, P55BridgeRow) else dict(row)


def _non_empty_string(value: Any) -> str:
    return str(value or "").strip()


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def validate_bridge_row(row: P55BridgeRow | Mapping[str, Any]) -> tuple[str, ...]:
    payload = _payload(row)
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"missing_{field}")

    if payload.get("active_stratum") != ACTIVE_STRATUM:
        errors.append("wrong_active_stratum")
    dataset = _non_empty_string(payload.get("dataset"))
    task_family = _non_empty_string(payload.get("task_family"))
    if dataset not in SUPPORTED_DATASET_TASKS:
        errors.append("wrong_dataset")
    if not dataset_task_supported(dataset, task_family):
        errors.append("wrong_task_family")
    if not _non_empty_string(payload.get("instance_id")):
        errors.append("missing_instance_id")
    if not _non_empty_string(payload.get("candidate_pool_hash")):
        errors.append("missing_candidate_pool_hash")
    if not _non_empty_string(payload.get("materialized_context_hash")):
        errors.append("missing_materialized_context_hash")
    if not _non_empty_string(payload.get("evaluator_id")):
        errors.append("missing_evaluator_id")
    if not _non_empty_string(payload.get("model_tier")):
        errors.append("missing_model_tier")
    if not _non_empty_string(payload.get("materialization_policy")):
        errors.append("missing_materialization_policy")
    if not _non_empty_string(payload.get("candidate_slice_band")):
        errors.append("missing_candidate_slice_band")
    if not _non_empty_string(payload.get("decoding_policy")):
        errors.append("missing_decoding_policy")

    target_y = payload.get("target_y")
    if not _non_empty_string(target_y):
        errors.append("missing_target_y")
    elif dataset == DATASET and task_family == TASK_FAMILY and str(target_y) not in ALLOWED_TARGETS:
        errors.append("invalid_target_y")

    context_ids = _string_list(payload.get("context_L_packet_ids"))
    block_ids = _string_list(payload.get("block_A_packet_ids"))
    if "context_L_packet_ids" in payload and not isinstance(payload.get("context_L_packet_ids"), list):
        errors.append("context_L_packet_ids_not_list")
    if "block_A_packet_ids" in payload and not isinstance(payload.get("block_A_packet_ids"), list):
        errors.append("block_A_packet_ids_not_list")
    if "block_A_packet_ids" in payload and not block_ids:
        errors.append("empty_block_A_packet_ids")

    try:
        block_size = int(payload.get("block_size"))
    except (TypeError, ValueError):
        block_size = None
        errors.append("block_size_not_integer")
    if block_size is not None:
        if block_size not in ALLOWED_BLOCK_SIZES:
            errors.append("invalid_block_size")
        if block_size != len(block_ids):
            errors.append("block_size_mismatch")

    if "delta_logloss" in payload and _finite_float(payload.get("delta_logloss")) is None:
        errors.append("delta_logloss_not_numeric")
    if "delta_utility" in payload and _finite_float(payload.get("delta_utility")) is None:
        errors.append("delta_utility_not_numeric")
    if "replicate_count" in payload and _positive_int(payload.get("replicate_count")) is None:
        errors.append("replicate_count_not_positive")

    contamination_status = str(payload.get("contamination_status", ""))
    if contamination_status not in ALLOWED_CONTAMINATION_STATUSES:
        errors.append("invalid_contamination_status")
    if contamination_status == "failed":
        errors.append("contamination_failed")

    expected_context_hash = make_materialized_context_hash(context_ids, block_ids)
    if payload.get("materialized_context_hash") and payload.get("materialized_context_hash") != expected_context_hash:
        errors.append("materialized_context_hash_mismatch")
    if has_absolute_local_path(payload):
        errors.append("absolute_local_path_in_row")
    return tuple(errors)


def validate_bridge_rows(rows: Sequence[P55BridgeRow | Mapping[str, Any]]) -> BridgeRowValidationResult:
    errors: list[str] = []
    seen: set[BridgeRowKey] = set()
    rows_validated = 0
    for index, row in enumerate(rows, start=1):
        row_errors = validate_bridge_row(row)
        identity = bridge_row_key(row)
        if identity in seen:
            row_errors = (*row_errors, "duplicate_row_identity")
        seen.add(identity)
        if row_errors:
            errors.extend(f"row_{index}:{error}" for error in row_errors)
        else:
            rows_validated += 1
    return BridgeRowValidationResult(
        rows_generated=len(rows),
        rows_validated=rows_validated,
        schema_valid=not errors,
        errors=tuple(errors),
    )


def require_valid_bridge_rows(rows: Sequence[P55BridgeRow | Mapping[str, Any]]) -> None:
    result = validate_bridge_rows(rows)
    if not result.schema_valid:
        raise BridgeRowValidationError(";".join(result.errors))
