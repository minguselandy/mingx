from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.schemas import BenchmarkInstance
from cps.benchmarks.schemas import make_benchmark_instance
from cps.benchmarks.schemas import make_blocked_data_report
from cps.benchmarks.schemas import make_evidence_packet
from cps.benchmarks.schemas import require_valid_benchmark_instance


HOTPOTQA_DATASET = "HotpotQA"
HOTPOTQA_TASK_FAMILY = "hotpotqa_answer_support_selection"


@dataclass(frozen=True)
class HotpotAdapterResult:
    instances: tuple[BenchmarkInstance, ...]
    report: dict[str, Any]
    blocked_report: dict[str, Any] | None = None

    @property
    def blocked(self) -> bool:
        return self.blocked_report is not None


def _compact_path_ref(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return Path(path).name


def _read_hotpot(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return []
    if stripped.startswith("["):
        payload = json.loads(stripped)
        if not isinstance(payload, list):
            raise ValueError(f"{path.name}: expected JSON list")
        return [dict(row) for row in payload if isinstance(row, Mapping)]

    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"{path.name}: row {line_number} must be an object")
        rows.append(payload)
    return rows


def _build_report(*, instances: Sequence[BenchmarkInstance], split: str, warnings: Sequence[str]) -> dict[str, Any]:
    return {
        "adapter_name": "hotpot_adapter",
        "candidate_pools_generated": len(instances),
        "claim_status": [
            "no_claim_upgrade",
            "adapter_only",
            "candidate_pool_schema_ready",
            "P55 still blocked_no_rows",
            "P56 still blocked_no_traces",
        ],
        "dataset": HOTPOTQA_DATASET,
        "p55_rows_generated": 0,
        "p56_traces_generated": 0,
        "phase": "P61R-HotpotQA",
        "split": split,
        "status": "candidate_pools_ready" if instances else "blocked_data_unavailable",
        "task_family": HOTPOTQA_TASK_FAMILY,
        "warnings": list(warnings),
    }


def _supporting_fact_set(row: Mapping[str, Any]) -> set[tuple[str, int]]:
    supporting_facts = row.get("supporting_facts")
    if not isinstance(supporting_facts, list):
        return set()
    parsed: set[tuple[str, int]] = set()
    for fact in supporting_facts:
        if not isinstance(fact, list | tuple) or len(fact) < 2:
            continue
        title = str(fact[0]).strip()
        try:
            sentence_index = int(fact[1])
        except (TypeError, ValueError):
            continue
        if title:
            parsed.add((title, sentence_index))
    return parsed


def _iter_context_sentences(row: Mapping[str, Any]):
    context = row.get("context")
    if not isinstance(context, list):
        return
    for paragraph_index, paragraph in enumerate(context):
        if not isinstance(paragraph, list | tuple) or len(paragraph) < 2:
            continue
        title = str(paragraph[0]).strip()
        sentences = paragraph[1]
        if not title or not isinstance(sentences, list):
            continue
        for sentence_index, sentence in enumerate(sentences):
            content = str(sentence or "").strip()
            if content:
                yield paragraph_index, title, sentence_index, content


def _row_id(row: Mapping[str, Any]) -> str:
    return str(row.get("_id") or row.get("id") or row.get("instance_id") or "").strip()


def build_hotpot_candidate_pools(
    *,
    input_json: str | Path,
    split: str = "dev",
    limit: int | None = None,
) -> HotpotAdapterResult:
    input_path = Path(input_json)
    if not input_path.exists():
        blocked = make_blocked_data_report(
            dataset=HOTPOTQA_DATASET,
            split=split,
            reason_codes=["missing_hotpotqa_file", "no_candidate_pools_generated"],
            blocked_items=[f"input_json:{_compact_path_ref(input_path)}"],
        )
        return HotpotAdapterResult(instances=(), report=_build_report(instances=(), split=split, warnings=[]), blocked_report=blocked)

    try:
        rows = _read_hotpot(input_path)
    except (json.JSONDecodeError, ValueError) as exc:
        blocked = make_blocked_data_report(
            dataset=HOTPOTQA_DATASET,
            split=split,
            reason_codes=["hotpotqa_file_malformed", "no_candidate_pools_generated"],
            blocked_items=[input_path.name, exc.__class__.__name__],
        )
        return HotpotAdapterResult(instances=(), report=_build_report(instances=(), split=split, warnings=[]), blocked_report=blocked)

    instances: list[BenchmarkInstance] = []
    warnings: list[str] = []
    row_limit = None if limit is None else max(0, int(limit))
    for row in rows:
        if row_limit is not None and len(instances) >= row_limit:
            break
        instance_id = _row_id(row)
        question = str(row.get("question") or "").strip()
        answer = str(row.get("answer") or "").strip()
        supporting_facts = _supporting_fact_set(row)
        context_sentences = list(_iter_context_sentences(row))
        if not instance_id or not question or not answer or not supporting_facts or not context_sentences:
            warnings.append(f"skipped_invalid_hotpotqa_row:{instance_id or 'missing_instance_id'}")
            continue

        packets = []
        for paragraph_index, title, sentence_index, content in context_sentences:
            if content.casefold() == answer.casefold():
                warnings.append(f"skipped_exact_answer_packet:{instance_id}:{title}:{sentence_index}")
                continue
            is_gold = (title, sentence_index) in supporting_facts
            packets.append(
                make_evidence_packet(
                    dataset=HOTPOTQA_DATASET,
                    split=split,
                    instance_id=instance_id,
                    content=content,
                    gold_support_label="gold_supporting" if is_gold else "same_context_distractor",
                    source_doc_id=title,
                    span={"start": sentence_index, "end": sentence_index, "unit": "sentence"},
                    source_packet_key=f"context-{paragraph_index}-{title}-{sentence_index}",
                )
            )

        if not any(packet.gold_support_label == "gold_supporting" for packet in packets):
            warnings.append(f"skipped_no_gold_supporting_packets:{instance_id}")
            continue

        instance = make_benchmark_instance(
            dataset=HOTPOTQA_DATASET,
            split=split,
            instance_id=instance_id,
            query=question,
            target_label=answer,
            packets=packets,
            task_family=HOTPOTQA_TASK_FAMILY,
            target_type="answer_string",
            adapter_name="hotpot_adapter",
        )
        try:
            require_valid_benchmark_instance(instance)
        except ValueError as exc:
            warnings.append(f"skipped_invalid_candidate_pool:{instance_id}:{exc}")
            continue
        instances.append(instance)

    if not instances:
        blocked = make_blocked_data_report(
            dataset=HOTPOTQA_DATASET,
            split=split,
            reason_codes=["no_valid_candidate_pools", "no_candidate_pools_generated"],
            blocked_items=[input_path.name],
        )
        return HotpotAdapterResult(
            instances=(),
            report=_build_report(instances=(), split=split, warnings=warnings),
            blocked_report=blocked,
        )

    return HotpotAdapterResult(
        instances=tuple(instances),
        report=_build_report(instances=instances, split=split, warnings=warnings),
        blocked_report=None,
    )
