from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.schemas import validate_benchmark_instance
from cps.experiments.bridge_row_schema import ACTIVE_STRATUM
from cps.experiments.bridge_row_schema import BridgeRowKey
from cps.experiments.bridge_row_schema import DATASET
from cps.experiments.bridge_row_schema import DEFAULT_CANDIDATE_SLICE_BAND
from cps.experiments.bridge_row_schema import DEFAULT_OPERATOR_ROWS_PATH
from cps.experiments.bridge_row_schema import HOTPOTQA_DATASET
from cps.experiments.bridge_row_schema import HOTPOTQA_TASK_FAMILY
from cps.experiments.bridge_row_schema import P55BridgeRow
from cps.experiments.bridge_row_schema import TASK_FAMILY
from cps.experiments.bridge_row_schema import dataset_task_supported
from cps.experiments.bridge_row_schema import make_materialized_context_hash
from cps.experiments.bridge_row_schema import write_bridge_row_jsonl
from cps.experiments.bridge_row_schema import write_canonical_json
from cps.experiments.bridge_row_validation import validate_bridge_rows


DEFAULT_CANDIDATE_POOLS_PATH = "artifacts/benchmarks/fever_candidate_pools.jsonl"
DEFAULT_DELTA_RECORDS_PATH = "artifacts/benchmarks/fever_p55_delta_records.jsonl"
DEFAULT_BLOCKED_REPORT_PATH = "artifacts/benchmarks/p62r_bridge_row_blocked_report.json"
DEFAULT_SUMMARY_PATH = "artifacts/benchmarks/p62r_bridge_row_generation_summary.json"
HOTPOTQA_DEFAULT_CANDIDATE_POOLS_PATH = "artifacts/benchmarks/hotpotqa_candidate_pools.jsonl"
HOTPOTQA_DEFAULT_DELTA_RECORDS_PATH = "artifacts/benchmarks/hotpotqa_p55_delta_records.jsonl"
HOTPOTQA_DEFAULT_BLOCKED_REPORT_PATH = "artifacts/benchmarks/p62r_hotpotqa_bridge_row_blocked_report.json"
HOTPOTQA_DEFAULT_SUMMARY_PATH = "artifacts/benchmarks/p62r_hotpotqa_bridge_row_generation_summary.json"
BLOCKED_STATUS = "blocked_no_candidate_pools_or_evaluator"
HOTPOTQA_BLOCKED_STATUS = "blocked_hotpotqa_candidate_pools_or_evaluator"
ROWS_READY_STATUS = "rows_generated_pending_calibration"
P55_STATUS = "failed_closed_no_rows / blocked_operator_required"
P56_STATUS = "no_imported_traces"


def default_paths_for_dataset(dataset: str) -> dict[str, str]:
    if dataset == HOTPOTQA_DATASET:
        return {
            "blocked_report": HOTPOTQA_DEFAULT_BLOCKED_REPORT_PATH,
            "candidate_pools": HOTPOTQA_DEFAULT_CANDIDATE_POOLS_PATH,
            "delta_records": HOTPOTQA_DEFAULT_DELTA_RECORDS_PATH,
            "summary": HOTPOTQA_DEFAULT_SUMMARY_PATH,
        }
    return {
        "blocked_report": DEFAULT_BLOCKED_REPORT_PATH,
        "candidate_pools": DEFAULT_CANDIDATE_POOLS_PATH,
        "delta_records": DEFAULT_DELTA_RECORDS_PATH,
        "summary": DEFAULT_SUMMARY_PATH,
    }


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate.name
    return candidate.as_posix()


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//")):
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{input_path.name}: row {line_number} must be an object")
        rows.append(payload)
    return rows


def _write_blocked_report(
    path: str | Path,
    *,
    reason_codes: Sequence[str],
    candidate_pools_path: str | Path = DEFAULT_CANDIDATE_POOLS_PATH,
    delta_records_path: str | Path = DEFAULT_DELTA_RECORDS_PATH,
    dataset: str = DATASET,
    task_family: str = TASK_FAMILY,
) -> dict[str, Any]:
    report = make_blocked_report(
        reason_codes=reason_codes,
        candidate_pools_path=candidate_pools_path,
        delta_records_path=delta_records_path,
        dataset=dataset,
        task_family=task_family,
    )
    write_canonical_json(path, report)
    return report


def make_blocked_report(
    *,
    reason_codes: Sequence[str],
    candidate_pools_path: str | Path = DEFAULT_CANDIDATE_POOLS_PATH,
    delta_records_path: str | Path = DEFAULT_DELTA_RECORDS_PATH,
    dataset: str = DATASET,
    task_family: str = TASK_FAMILY,
) -> dict[str, Any]:
    is_hotpotqa = dataset == HOTPOTQA_DATASET
    return {
        "calibrated_proxy_supported": False,
        "candidate_pools_path": _path_ref(candidate_pools_path),
        "claim_status": "no_claim_upgrade",
        "dataset": dataset,
        "delta_records_path": _path_ref(delta_records_path),
        "measurement_validation": False,
        "metric_bridge_support": False,
        "operator_rows_path": DEFAULT_OPERATOR_ROWS_PATH,
        "p55_status": P55_STATUS,
        "p56_status": P56_STATUS,
        "paper_evidence": False,
        "phase": "P62R-HotpotQA" if is_hotpotqa else "P62R",
        "reason_codes": list(reason_codes),
        "rows_generated": 0,
        "rows_validated": 0,
        "status": HOTPOTQA_BLOCKED_STATUS if is_hotpotqa else BLOCKED_STATUS,
        "task_family": task_family,
        "vinfo_proxy_supported": False,
    }


def _load_candidate_pools(
    path: str | Path,
    *,
    dataset: str = DATASET,
    task_family: str = TASK_FAMILY,
) -> tuple[dict[tuple[str, str, str, str], dict[str, Any]], list[str]]:
    rows = _read_jsonl(path)
    lookup: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        validation = validate_benchmark_instance(row)
        if not validation.schema_valid:
            errors.append(f"candidate_pool_row_{index}:invalid:{'|'.join(validation.errors)}")
            continue
        if row.get("dataset") != dataset:
            errors.append(f"candidate_pool_row_{index}:wrong_dataset")
            continue
        if row.get("task_family") != task_family:
            errors.append(f"candidate_pool_row_{index}:wrong_task_family")
            continue
        target = row.get("target") or {}
        pool = row.get("candidate_pool") or {}
        key = (
            str(row.get("dataset")),
            str(row.get("task_family")),
            str(row.get("instance_id")),
            str(pool.get("candidate_pool_hash")),
        )
        lookup[key] = {
            "active_stratum": ACTIVE_STRATUM,
            "candidate_pool_hash": str(pool.get("candidate_pool_hash")),
            "dataset": str(row.get("dataset")),
            "instance_id": str(row.get("instance_id")),
            "task_family": str(row.get("task_family")),
            "target_y": str(target.get("label")),
        }
    return lookup, errors


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field}_not_list")
    parsed = [str(item).strip() for item in value if str(item).strip()]
    if field == "block_A_packet_ids" and not parsed:
        raise ValueError("empty_block_A_packet_ids")
    return parsed


def _required_string(record: Mapping[str, Any], field: str) -> str:
    value = str(record.get(field) or "").strip()
    if not value:
        raise ValueError(f"missing_{field}")
    return value


def _required_float(record: Mapping[str, Any], field: str) -> float:
    if field not in record:
        raise ValueError(f"missing_{field}")
    try:
        return float(record[field])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}_not_numeric") from exc


def _required_positive_int(record: Mapping[str, Any], field: str) -> int:
    if field not in record:
        raise ValueError(f"missing_{field}")
    try:
        parsed = int(record[field])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}_not_integer") from exc
    if parsed <= 0:
        raise ValueError(f"{field}_not_positive")
    return parsed


def _required_delta_record_key(record: Mapping[str, Any]) -> BridgeRowKey:
    context_ids = _string_list(record.get("context_L_packet_ids", []), "context_L_packet_ids")
    block_ids = _string_list(record.get("block_A_packet_ids"), "block_A_packet_ids")
    return BridgeRowKey(
        active_stratum=_required_string(record, "active_stratum"),
        task_family=_required_string(record, "task_family"),
        dataset=_required_string(record, "dataset"),
        instance_id=_required_string(record, "instance_id"),
        candidate_pool_hash=_required_string(record, "candidate_pool_hash"),
        context_L_packet_ids=tuple(context_ids),
        block_A_packet_ids=tuple(block_ids),
        target_y=_required_string(record, "target_y"),
        model_tier=_required_string(record, "model_tier"),
        materialization_policy=_required_string(record, "materialization_policy"),
        candidate_slice_band=_required_string(record, "candidate_slice_band"),
        block_size=_required_positive_int(record, "block_size"),
        decoding_policy=_required_string(record, "decoding_policy"),
        evaluator_id=_required_string(record, "evaluator_id"),
    )


def _candidate_row_key(*, benchmark_instance: Mapping[str, Any], delta_key: BridgeRowKey) -> BridgeRowKey:
    return BridgeRowKey(
        active_stratum=str(benchmark_instance["active_stratum"]),
        task_family=str(benchmark_instance["task_family"]),
        dataset=str(benchmark_instance["dataset"]),
        instance_id=str(benchmark_instance["instance_id"]),
        candidate_pool_hash=str(benchmark_instance["candidate_pool_hash"]),
        context_L_packet_ids=delta_key.context_L_packet_ids,
        block_A_packet_ids=delta_key.block_A_packet_ids,
        target_y=str(benchmark_instance["target_y"]),
        model_tier=delta_key.model_tier,
        materialization_policy=delta_key.materialization_policy,
        candidate_slice_band=delta_key.candidate_slice_band,
        block_size=delta_key.block_size,
        decoding_policy=delta_key.decoding_policy,
        evaluator_id=delta_key.evaluator_id,
    )


def bridge_row_from_delta_record(
    *,
    benchmark_instance: Mapping[str, Any],
    delta_record: Mapping[str, Any],
) -> P55BridgeRow:
    delta_key = _required_delta_record_key(delta_record)
    if delta_key != _candidate_row_key(benchmark_instance=benchmark_instance, delta_key=delta_key):
        raise ValueError("full_row_key_mismatch")
    return P55BridgeRow(
        active_stratum=delta_key.active_stratum,
        task_family=delta_key.task_family,
        dataset=delta_key.dataset,
        instance_id=delta_key.instance_id,
        model_tier=delta_key.model_tier,
        materialization_policy=delta_key.materialization_policy,
        candidate_slice_band=delta_key.candidate_slice_band,
        block_size=delta_key.block_size,
        context_L_packet_ids=delta_key.context_L_packet_ids,
        block_A_packet_ids=delta_key.block_A_packet_ids,
        target_y=delta_key.target_y,
        delta_logloss=_required_float(delta_record, "delta_logloss"),
        delta_utility=_required_float(delta_record, "delta_utility"),
        replicate_count=_required_positive_int(delta_record, "replicate_count"),
        decoding_policy=delta_key.decoding_policy,
        evaluator_id=delta_key.evaluator_id,
        candidate_pool_hash=delta_key.candidate_pool_hash,
        materialized_context_hash=make_materialized_context_hash(
            delta_key.context_L_packet_ids,
            delta_key.block_A_packet_ids,
        ),
        contamination_status=_required_string(delta_record, "contamination_status"),
    )


def run_p62r_bridge_row_generation(
    *,
    candidate_pools_jsonl: str | Path = DEFAULT_CANDIDATE_POOLS_PATH,
    delta_records_jsonl: str | Path = DEFAULT_DELTA_RECORDS_PATH,
    output_jsonl: str | Path = DEFAULT_OPERATOR_ROWS_PATH,
    blocked_report_json: str | Path = DEFAULT_BLOCKED_REPORT_PATH,
    summary_json: str | Path | None = None,
    dataset: str = DATASET,
    task_family: str = TASK_FAMILY,
) -> dict[str, Any]:
    if not dataset_task_supported(dataset, task_family):
        return _write_blocked_report(
            blocked_report_json,
            reason_codes=["unsupported_dataset_task_family", "no_rows_generated"],
            candidate_pools_path=candidate_pools_jsonl,
            delta_records_path=delta_records_jsonl,
            dataset=dataset,
            task_family=task_family,
        )
    candidate_path = Path(candidate_pools_jsonl)
    delta_path = Path(delta_records_jsonl)
    missing_reasons: list[str] = []
    if not candidate_path.exists():
        missing_reasons.append("missing_candidate_pools")
    if not delta_path.exists():
        missing_reasons.append("missing_evaluator_delta_records")
    if missing_reasons:
        return _write_blocked_report(
            blocked_report_json,
            reason_codes=[*missing_reasons, "no_rows_generated"],
            candidate_pools_path=candidate_pools_jsonl,
            delta_records_path=delta_records_jsonl,
            dataset=dataset,
            task_family=task_family,
        )

    candidate_lookup, candidate_errors = _load_candidate_pools(candidate_path, dataset=dataset, task_family=task_family)
    delta_records = _read_jsonl(delta_path)
    rows: list[P55BridgeRow] = []
    generation_errors: list[str] = list(candidate_errors)
    seen_delta_keys: dict[BridgeRowKey, int] = {}
    for index, delta_record in enumerate(delta_records, start=1):
        try:
            delta_key = _required_delta_record_key(delta_record)
        except ValueError as exc:
            generation_errors.append(f"delta_row_{index}:{exc}")
            continue
        if delta_key in seen_delta_keys:
            generation_errors.append(f"delta_row_{index}:duplicate_delta_row_key:{seen_delta_keys[delta_key]}")
            continue
        seen_delta_keys[delta_key] = index

        pool_key = (delta_key.dataset, delta_key.task_family, delta_key.instance_id, delta_key.candidate_pool_hash)
        benchmark_instance = candidate_lookup.get(pool_key)
        if benchmark_instance is None:
            generation_errors.append(f"delta_row_{index}:candidate_pool_key_not_found")
            continue
        try:
            rows.append(bridge_row_from_delta_record(benchmark_instance=benchmark_instance, delta_record=delta_record))
        except ValueError as exc:
            generation_errors.append(f"delta_row_{index}:{exc}")

    validation = validate_bridge_rows(rows)

    if generation_errors or not rows or not validation.schema_valid:
        terminal_reason = "no_valid_rows_generated" if not rows else "invalid_rows_generated"
        return _write_blocked_report(
            blocked_report_json,
            reason_codes=[*generation_errors, *validation.errors, terminal_reason],
            candidate_pools_path=candidate_pools_jsonl,
            delta_records_path=delta_records_jsonl,
            dataset=dataset,
            task_family=task_family,
        )

    write_bridge_row_jsonl(output_jsonl, rows)
    summary = {
        "candidate_pools_loaded": len(candidate_lookup),
        "claim_status": "rows_generated_pending_calibration",
        "delta_records_loaded": len(delta_records),
        "dataset": dataset,
        "generation_errors": generation_errors,
        "metric_bridge_support": False,
        "operator_rows_path": _path_ref(output_jsonl),
        "p55_status": "rows_generated_pending_calibration",
        "p56_status": P56_STATUS,
        "paper_evidence": False,
        "phase": "P62R-HotpotQA" if dataset == HOTPOTQA_DATASET else "P62R",
        "rows_generated": len(rows),
        "rows_validated": validation.rows_validated,
        "status": ROWS_READY_STATUS,
        "task_family": task_family,
        "unique_instances": len({row.instance_id for row in rows}),
        "validation_errors": list(validation.errors),
    }
    if summary_json is not None:
        write_canonical_json(summary_json, summary)
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate P62R P55 bridge rows from benchmark pools.")
    parser.add_argument("--dataset", default=DATASET, choices=[DATASET, HOTPOTQA_DATASET])
    parser.add_argument("--task-family")
    parser.add_argument("--candidate-pools-jsonl")
    parser.add_argument("--delta-records-jsonl")
    parser.add_argument("--output-jsonl", default=DEFAULT_OPERATOR_ROWS_PATH)
    parser.add_argument("--blocked-report-json")
    parser.add_argument("--summary-json")
    args = parser.parse_args(argv)
    task_family = args.task_family or (HOTPOTQA_TASK_FAMILY if args.dataset == HOTPOTQA_DATASET else TASK_FAMILY)
    defaults = default_paths_for_dataset(args.dataset)

    run_p62r_bridge_row_generation(
        candidate_pools_jsonl=args.candidate_pools_jsonl or defaults["candidate_pools"],
        delta_records_jsonl=args.delta_records_jsonl or defaults["delta_records"],
        output_jsonl=args.output_jsonl,
        blocked_report_json=args.blocked_report_json or defaults["blocked_report"],
        summary_json=args.summary_json,
        dataset=args.dataset,
        task_family=task_family,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
