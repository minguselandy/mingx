from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Iterable
from typing import Mapping
from typing import Sequence

from cps.benchmarks.schemas import ALLOWED_GOLD_SUPPORT_LABELS
from cps.benchmarks.schemas import ALLOWED_TARGET_LABELS
from cps.benchmarks.schemas import BenchmarkInstance
from cps.benchmarks.schemas import make_benchmark_instance
from cps.benchmarks.schemas import make_blocked_data_report
from cps.benchmarks.schemas import make_evidence_packet
from cps.benchmarks.schemas import require_valid_benchmark_instance


@dataclass(frozen=True)
class FeverAdapterResult:
    instances: tuple[BenchmarkInstance, ...]
    report: dict[str, Any]
    blocked_report: dict[str, Any] | None = None

    @property
    def blocked(self) -> bool:
        return self.blocked_report is not None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{path.name}: row {line_number} must be a JSON object")
        rows.append(payload)
    return rows


def _compact_path_ref(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return Path(path).name


def _instance_id(row: Mapping[str, Any]) -> str:
    return str(row.get("instance_id") or row.get("id") or row.get("fever_id") or "").strip()


def _target_label(row: Mapping[str, Any]) -> str:
    if "label" in row:
        return str(row.get("label") or "").strip()
    target = row.get("target")
    if isinstance(target, Mapping):
        return str(target.get("label") or "").strip()
    return ""


def _query(row: Mapping[str, Any]) -> str:
    return str(row.get("claim") or row.get("query") or "").strip()


def _span(entry: Mapping[str, Any], fallback_index: int) -> dict[str, Any]:
    raw_span = entry.get("span")
    if isinstance(raw_span, Mapping):
        start = int(raw_span.get("start", 0))
        end = int(raw_span.get("end", start))
        unit = str(raw_span.get("unit", "sentence"))
        return {"start": start, "end": end, "unit": unit}
    sentence = entry.get("sentence_id", entry.get("sentence_index", entry.get("line_index", fallback_index)))
    try:
        sentence_index = int(sentence)
    except (TypeError, ValueError):
        sentence_index = fallback_index
    return {"start": sentence_index, "end": sentence_index, "unit": "sentence"}


def _source_doc_id(entry: Mapping[str, Any]) -> str | None:
    value = entry.get("source_doc_id") or entry.get("doc_id") or entry.get("page") or entry.get("title")
    if value is None:
        return None
    parsed = str(value).strip()
    return parsed or None


def _content(entry: Mapping[str, Any] | str) -> str:
    if isinstance(entry, str):
        return entry.strip()
    return str(entry.get("content") or entry.get("text") or entry.get("sentence") or "").strip()


def _source_packet_key(entry: Mapping[str, Any] | str, fallback_prefix: str, index: int) -> str:
    if isinstance(entry, str):
        return f"{fallback_prefix}-{index}"
    value = (
        entry.get("source_packet_key")
        or entry.get("packet_id")
        or entry.get("candidate_id")
        or entry.get("evidence_id")
    )
    return str(value or f"{fallback_prefix}-{index}")


def _iter_text_entries(value: Any) -> Iterable[Mapping[str, Any] | str]:
    if value is None:
        return
    if isinstance(value, (str, Mapping)):
        yield value
        return
    if isinstance(value, list):
        for item in value:
            if isinstance(item, (str, Mapping)):
                yield item
            elif isinstance(item, list):
                yield from _iter_text_entries(item)


def _evidence_entries(row: Mapping[str, Any]) -> list[Mapping[str, Any] | str]:
    entries: list[Mapping[str, Any] | str] = []
    for key in ("evidence", "gold_evidence", "evidence_sentences", "gold_evidence_sentences"):
        for entry in _iter_text_entries(row.get(key)):
            if _content(entry):
                entries.append(entry)
    return entries


def _candidate_instance_id(row: Mapping[str, Any]) -> str:
    return str(row.get("instance_id") or row.get("id") or row.get("fever_id") or "").strip()


def _candidate_entries_by_instance(candidates_jsonl: str | Path | None) -> tuple[dict[str, list[Mapping[str, Any] | str]], list[str]]:
    if candidates_jsonl is None:
        return {}, []
    path = Path(candidates_jsonl)
    if not path.exists():
        return {}, [f"missing_candidate_file:{path.name}"]
    rows = _read_jsonl(path)
    by_instance: dict[str, list[Mapping[str, Any] | str]] = {}
    for row in rows:
        key = _candidate_instance_id(row)
        if not key:
            continue
        if isinstance(row.get("candidates"), list):
            by_instance.setdefault(key, []).extend(row["candidates"])
        elif _content(row):
            by_instance.setdefault(key, []).append(row)
    return by_instance, []


def _candidate_support_label(entry: Mapping[str, Any] | str) -> str:
    if isinstance(entry, str):
        return "retrieved_distractor"
    value = str(
        entry.get("gold_support_label")
        or entry.get("support_label")
        or entry.get("candidate_label")
        or "retrieved_distractor"
    )
    return value if value in ALLOWED_GOLD_SUPPORT_LABELS else "unknown"


def _make_packet_from_entry(
    *,
    entry: Mapping[str, Any] | str,
    dataset: str,
    split: str,
    instance_id: str,
    gold_support_label: str,
    fallback_prefix: str,
    index: int,
):
    content = _content(entry)
    mapping = entry if isinstance(entry, Mapping) else {}
    return make_evidence_packet(
        dataset=dataset,
        split=split,
        instance_id=instance_id,
        content=content,
        gold_support_label=gold_support_label,
        source_doc_id=_source_doc_id(mapping),
        span=_span(mapping, index),
        source_packet_key=_source_packet_key(entry, fallback_prefix, index),
    )


def _build_report(
    *,
    instances: Sequence[BenchmarkInstance],
    split: str,
    warnings: Sequence[str],
) -> dict[str, Any]:
    return {
        "adapter_name": "fever_adapter",
        "candidate_pools_generated": len(instances),
        "claim_status": [
            "no_claim_upgrade",
            "adapter_only",
            "candidate_pool_schema_ready",
            "P55 still blocked_no_rows",
            "P56 still blocked_no_traces",
        ],
        "dataset": "FEVER",
        "p55_rows_generated": 0,
        "p56_traces_generated": 0,
        "phase": "P61R-A",
        "split": split,
        "status": "candidate_pools_ready" if instances else "blocked_data_unavailable",
        "warnings": list(warnings),
    }


def build_fever_candidate_pools(
    *,
    claims_jsonl: str | Path,
    candidates_jsonl: str | Path | None = None,
    split: str = "dev",
    limit: int | None = None,
) -> FeverAdapterResult:
    claims_path = Path(claims_jsonl)
    if not claims_path.exists():
        blocked = make_blocked_data_report(
            dataset="FEVER",
            split=split,
            reason_codes=["missing_claims_file", "no_candidate_pools_generated"],
            blocked_items=[f"claims_jsonl:{_compact_path_ref(claims_path)}"],
        )
        return FeverAdapterResult(instances=(), report=_build_report(instances=(), split=split, warnings=[]), blocked_report=blocked)

    candidate_map, candidate_errors = _candidate_entries_by_instance(candidates_jsonl)
    if candidate_errors:
        blocked = make_blocked_data_report(
            dataset="FEVER",
            split=split,
            reason_codes=[*candidate_errors, "no_candidate_pools_generated"],
            blocked_items=[f"candidates_jsonl:{_compact_path_ref(candidates_jsonl)}"],
        )
        return FeverAdapterResult(instances=(), report=_build_report(instances=(), split=split, warnings=[]), blocked_report=blocked)

    try:
        rows = _read_jsonl(claims_path)
    except (json.JSONDecodeError, ValueError) as exc:
        blocked = make_blocked_data_report(
            dataset="FEVER",
            split=split,
            reason_codes=["claims_file_malformed", "no_candidate_pools_generated"],
            blocked_items=[claims_path.name, exc.__class__.__name__],
        )
        return FeverAdapterResult(instances=(), report=_build_report(instances=(), split=split, warnings=[]), blocked_report=blocked)

    instances: list[BenchmarkInstance] = []
    warnings: list[str] = []
    row_limit = None if limit is None else max(0, int(limit))
    for row in rows:
        if row_limit is not None and len(instances) >= row_limit:
            break
        instance_id = _instance_id(row)
        query = _query(row)
        target_label = _target_label(row)
        if not instance_id or not query or target_label not in ALLOWED_TARGET_LABELS:
            warnings.append(f"skipped_invalid_claim_row:{instance_id or 'missing_instance_id'}")
            continue

        row_split = str(row.get("split") or split)
        packets = [
            _make_packet_from_entry(
                entry=entry,
                dataset="FEVER",
                split=row_split,
                instance_id=instance_id,
                gold_support_label="gold_supporting",
                fallback_prefix="gold",
                index=index,
            )
            for index, entry in enumerate(_evidence_entries(row), start=1)
        ]
        packets.extend(
            _make_packet_from_entry(
                entry=entry,
                dataset="FEVER",
                split=row_split,
                instance_id=instance_id,
                gold_support_label=_candidate_support_label(entry),
                fallback_prefix="candidate",
                index=index,
            )
            for index, entry in enumerate(candidate_map.get(instance_id, []), start=1)
            if _content(entry)
        )

        if not packets:
            warnings.append(f"skipped_empty_candidate_pool:{instance_id}")
            continue

        instance = make_benchmark_instance(
            dataset="FEVER",
            split=row_split,
            instance_id=instance_id,
            query=query,
            target_label=target_label,
            packets=packets,
        )
        try:
            require_valid_benchmark_instance(instance)
        except ValueError as exc:
            warnings.append(f"skipped_invalid_candidate_pool:{instance_id}:{exc}")
            continue
        instances.append(instance)

    if not instances:
        blocked = make_blocked_data_report(
            dataset="FEVER",
            split=split,
            reason_codes=["no_valid_candidate_pools", "no_candidate_pools_generated"],
            blocked_items=[claims_path.name],
        )
        return FeverAdapterResult(
            instances=(),
            report=_build_report(instances=(), split=split, warnings=warnings),
            blocked_report=blocked,
        )

    return FeverAdapterResult(
        instances=tuple(instances),
        report=_build_report(instances=instances, split=split, warnings=warnings),
        blocked_report=None,
    )
