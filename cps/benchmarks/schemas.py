from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.hashing import canonical_json_dumps
from cps.benchmarks.hashing import has_absolute_local_path
from cps.benchmarks.hashing import stable_hash
from cps.benchmarks.token_cost import count_token_cost


DEFAULT_BUDGETS = (256, 512, 1024)
BENCHMARK_INSTANCE_SCHEMA_VERSION = "benchmark_instance_v1"
BLOCKED_DATA_REPORT_SCHEMA_VERSION = "p61r_blocked_data_report_v1"
ALLOWED_TARGET_LABELS = {"SUPPORTED", "REFUTED", "NOTENOUGHINFO"}
ALLOWED_GOLD_SUPPORT_LABELS = {
    "gold_supporting",
    "same_page_distractor",
    "retrieved_distractor",
    "random_distractor",
    "unknown",
}
DENIED_CLAIMS = (
    "measurement_validated",
    "human-label validation",
    "human-human kappa",
    "deployed V-information verification",
    "theorem-level deployed submodularity verification",
    "global calibrated proxy support",
    "global V-information proxy support",
    "fixture/synthetic/no-row/no-trace/scaffold paper evidence",
    "deployed runtime improvement from ReprojectionWitness",
    "P55 unblocked",
    "P56 unblocked",
)
CLAIM_STATUS = (
    "no_claim_upgrade",
    "adapter_only",
    "candidate_pool_schema_ready",
    "P55 still blocked_no_rows",
    "P56 still blocked_no_traces",
)


class CandidatePoolValidationError(ValueError):
    """Raised when a P61R-A benchmark instance cannot pass schema validation."""


@dataclass(frozen=True)
class ValidationResult:
    schema_valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class EvidencePacket:
    packet_id: str
    dataset: str
    instance_id: str
    source_doc_id: str | None
    span: dict[str, Any]
    content: str
    token_cost: int
    gold_support_label: str
    hop_index: int | None
    path_id: str | None
    retrieval_features: dict[str, Any]
    provenance: dict[str, Any]
    hash: str

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CandidatePool:
    candidate_pool_id: str
    candidate_pool_hash: str
    n_candidates: int
    n_gold_packets: int
    n_hard_negative_packets: int
    n_random_negative_packets: int
    total_tokens: int
    gold_reachable_under_budget: dict[str, bool]
    packets: tuple[EvidencePacket, ...]

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["packets"] = [packet.to_payload() for packet in self.packets]
        return payload


@dataclass(frozen=True)
class BenchmarkInstance:
    schema_version: str
    dataset: str
    split: str
    instance_id: str
    task_family: str
    query: str
    target: dict[str, Any]
    candidate_pool: CandidatePool
    adapter_metadata: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["candidate_pool"] = self.candidate_pool.to_payload()
        return payload


def packet_hash_payload(packet_payload: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(packet_payload)
    payload.pop("hash", None)
    return payload


def compute_packet_hash(packet_payload: Mapping[str, Any]) -> str:
    return stable_hash(packet_hash_payload(packet_payload))


def stable_span_string(span: Mapping[str, Any]) -> str:
    return f"{span.get('unit', 'sentence')}:{span.get('start', 0)}-{span.get('end', 0)}"


def stable_packet_id(
    *,
    dataset: str,
    split: str,
    instance_id: str,
    gold_support_label: str,
    source_doc_id: str | None,
    span: Mapping[str, Any],
    source_packet_key: str | None = None,
) -> str:
    components = {
        "dataset": dataset,
        "gold_support_label": gold_support_label,
        "instance_id": instance_id,
        "source_doc_id": source_doc_id,
        "source_packet_key": source_packet_key,
        "span": {
            "end": int(span.get("end", 0)),
            "start": int(span.get("start", 0)),
            "unit": str(span.get("unit", "sentence")),
        },
        "split": split,
    }
    suffix = stable_hash(components)[:16]
    return f"{dataset.lower()}::{split}::{instance_id}::{gold_support_label}::{suffix}"


def make_evidence_packet(
    *,
    dataset: str,
    split: str,
    instance_id: str,
    content: str,
    gold_support_label: str,
    source_doc_id: str | None,
    span: Mapping[str, Any] | None = None,
    source_packet_key: str | None = None,
    token_cost: int | None = None,
    hop_index: int | None = None,
    path_id: str | None = None,
    retrieval_features: Mapping[str, Any] | None = None,
    provenance_extra: Mapping[str, Any] | None = None,
) -> EvidencePacket:
    normalized_span = {
        "end": int((span or {}).get("end", (span or {}).get("start", 0))),
        "start": int((span or {}).get("start", 0)),
        "unit": str((span or {}).get("unit", "sentence")),
    }
    normalized_content = content.strip()
    normalized_source_doc_id = None if source_doc_id is None else str(source_doc_id)
    packet_id = stable_packet_id(
        dataset=dataset,
        split=split,
        instance_id=instance_id,
        gold_support_label=gold_support_label,
        source_doc_id=normalized_source_doc_id,
        span=normalized_span,
        source_packet_key=source_packet_key,
    )
    provenance = {
        "dataset": dataset,
        "source_doc_id": normalized_source_doc_id,
        "span": stable_span_string(normalized_span),
    }
    provenance.update(dict(provenance_extra or {}))
    packet = EvidencePacket(
        packet_id=packet_id,
        dataset=dataset,
        instance_id=instance_id,
        source_doc_id=normalized_source_doc_id,
        span=normalized_span,
        content=normalized_content,
        token_cost=count_token_cost(normalized_content) if token_cost is None else int(token_cost),
        gold_support_label=gold_support_label,
        hop_index=hop_index,
        path_id=path_id,
        retrieval_features=dict(retrieval_features or {}),
        provenance=provenance,
        hash="",
    )
    return replace(packet, hash=compute_packet_hash(packet.to_payload()))


def compute_candidate_pool_hash(candidate_pool_payload: Mapping[str, Any]) -> str:
    payload = dict(candidate_pool_payload)
    payload.pop("candidate_pool_hash", None)
    payload["packets"] = sorted(
        [dict(packet) for packet in payload.get("packets", [])],
        key=lambda packet: str(packet.get("packet_id", "")),
    )
    return stable_hash(payload)


def make_candidate_pool(
    *,
    dataset: str,
    split: str,
    instance_id: str,
    packets: Sequence[EvidencePacket],
    budgets: Sequence[int] = DEFAULT_BUDGETS,
) -> CandidatePool:
    sorted_packets = tuple(sorted(packets, key=lambda packet: packet.packet_id))
    gold_packets = [packet for packet in sorted_packets if packet.gold_support_label == "gold_supporting"]
    hard_negative_packets = [
        packet
        for packet in sorted_packets
        if packet.gold_support_label in {"same_page_distractor", "retrieved_distractor"}
    ]
    random_negative_packets = [
        packet for packet in sorted_packets if packet.gold_support_label == "random_distractor"
    ]
    gold_token_cost = sum(packet.token_cost for packet in gold_packets)
    pool = CandidatePool(
        candidate_pool_id=f"{dataset.lower()}::{split}::{instance_id}",
        candidate_pool_hash="",
        n_candidates=len(sorted_packets),
        n_gold_packets=len(gold_packets),
        n_hard_negative_packets=len(hard_negative_packets),
        n_random_negative_packets=len(random_negative_packets),
        total_tokens=sum(packet.token_cost for packet in sorted_packets),
        gold_reachable_under_budget={
            str(int(budget)): bool(gold_packets and gold_token_cost <= int(budget)) for budget in budgets
        },
        packets=sorted_packets,
    )
    return replace(pool, candidate_pool_hash=compute_candidate_pool_hash(pool.to_payload()))


def make_benchmark_instance(
    *,
    dataset: str,
    split: str,
    instance_id: str,
    query: str,
    target_label: str,
    packets: Sequence[EvidencePacket],
) -> BenchmarkInstance:
    return BenchmarkInstance(
        schema_version=BENCHMARK_INSTANCE_SCHEMA_VERSION,
        dataset=dataset,
        split=split,
        instance_id=str(instance_id),
        task_family="fever_claim_verification",
        query=query.strip(),
        target={"label": target_label, "target_type": "classification_label"},
        candidate_pool=make_candidate_pool(
            dataset=dataset,
            split=split,
            instance_id=str(instance_id),
            packets=packets,
        ),
        adapter_metadata={
            "adapter_name": "fever_adapter",
            "claim_boundary": "adapter_only_no_bridge_claim",
            "gold_support_available": any(packet.gold_support_label == "gold_supporting" for packet in packets),
            "source_kind": "public_benchmark",
        },
    )


def _payload(record: BenchmarkInstance | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(record, BenchmarkInstance):
        return record.to_payload()
    return dict(record)


def validate_benchmark_instance(record: BenchmarkInstance | Mapping[str, Any]) -> ValidationResult:
    payload = _payload(record)
    errors: list[str] = []
    warnings: list[str] = []

    if payload.get("schema_version") != BENCHMARK_INSTANCE_SCHEMA_VERSION:
        errors.append("missing_or_invalid_schema_version")
    for field in ("dataset", "split", "instance_id", "query", "task_family"):
        if not str(payload.get(field, "")).strip():
            errors.append(f"missing_{field}")

    target = payload.get("target")
    if not isinstance(target, Mapping):
        errors.append("missing_target")
        target_label = None
    else:
        target_label = target.get("label")
        if target.get("target_type") != "classification_label":
            errors.append("missing_or_invalid_target_type")
        if target_label is None or not str(target_label).strip():
            errors.append("missing_target_label")
        elif str(target_label) not in ALLOWED_TARGET_LABELS:
            errors.append("invalid_target_label")

    pool = payload.get("candidate_pool")
    if not isinstance(pool, Mapping):
        errors.append("missing_candidate_pool")
        return ValidationResult(False, tuple(errors), tuple(warnings))

    packets = pool.get("packets")
    if not isinstance(packets, list):
        errors.append("missing_candidate_pool_packets")
        packets = []
    if not packets:
        errors.append("empty_candidate_pool")

    packet_ids: set[str] = set()
    for index, packet in enumerate(packets, start=1):
        if not isinstance(packet, Mapping):
            errors.append(f"packet_{index}:not_object")
            continue
        packet_id = str(packet.get("packet_id", "")).strip()
        if not packet_id:
            errors.append(f"packet_{index}:missing_packet_id")
        elif packet_id in packet_ids:
            errors.append(f"packet_{index}:duplicate_packet_id")
        packet_ids.add(packet_id)

        if "content" not in packet:
            errors.append(f"packet_{index}:missing_packet_content")
        elif not str(packet.get("content", "")).strip():
            errors.append(f"packet_{index}:empty_packet_content")

        if "token_cost" not in packet:
            errors.append(f"packet_{index}:missing_token_cost")
        else:
            try:
                token_cost = int(packet["token_cost"])
            except (TypeError, ValueError):
                errors.append(f"packet_{index}:token_cost_not_integer")
            else:
                if token_cost < 0:
                    errors.append(f"packet_{index}:negative_token_cost")

        support_label = str(packet.get("gold_support_label", ""))
        if support_label not in ALLOWED_GOLD_SUPPORT_LABELS:
            errors.append(f"packet_{index}:invalid_gold_support_label")
        if support_label == "gold_supporting" and not isinstance(packet.get("provenance"), Mapping):
            errors.append(f"packet_{index}:missing_gold_support_provenance")

        if str(packet.get("hash", "")) != compute_packet_hash(packet):
            errors.append(f"packet_{index}:unstable_packet_hash")

    if has_absolute_local_path(payload):
        errors.append("absolute_local_path_in_canonical_output")

    expected_hash = compute_candidate_pool_hash(pool)
    if str(pool.get("candidate_pool_hash", "")) != expected_hash:
        errors.append("unstable_candidate_pool_hash")

    if target_label in {"SUPPORTED", "REFUTED"} and int(pool.get("n_gold_packets", 0) or 0) == 0:
        warnings.append("no_gold_evidence_text_available")
    if int(pool.get("n_hard_negative_packets", 0) or 0) == 0:
        warnings.append("no_hard_distractors_available")
    reachable = pool.get("gold_reachable_under_budget")
    if isinstance(reachable, Mapping) and reachable and not any(bool(value) for value in reachable.values()):
        warnings.append("gold_evidence_unreachable_under_all_configured_budgets")

    return ValidationResult(not errors, tuple(errors), tuple(warnings))


def require_valid_benchmark_instance(record: BenchmarkInstance | Mapping[str, Any]) -> None:
    result = validate_benchmark_instance(record)
    if not result.schema_valid:
        raise CandidatePoolValidationError(";".join(result.errors))


def canonical_jsonl(records: Sequence[BenchmarkInstance | Mapping[str, Any]]) -> str:
    rows = [_payload(record) for record in records]
    return "".join(canonical_json_dumps(row) + "\n" for row in rows)


def write_jsonl(path: str | Path, records: Sequence[BenchmarkInstance | Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonical_jsonl(records), encoding="utf-8")
    return output_path


def write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def make_blocked_data_report(
    *,
    reason_codes: Sequence[str],
    blocked_items: Sequence[str] = (),
    dataset: str = "FEVER",
    split: str = "dev",
) -> dict[str, Any]:
    return {
        "blocked_items": list(blocked_items),
        "candidate_pools_generated": 0,
        "claim_status": list(CLAIM_STATUS),
        "dataset": dataset,
        "denied_claims": list(DENIED_CLAIMS),
        "metric_bridge_support": False,
        "next_phase": "P62R FEVER bridge row generator after independent review",
        "p55_rows_generated": 0,
        "p56_traces_generated": 0,
        "phase": "P61R-A",
        "reason_codes": list(reason_codes),
        "schema_version": BLOCKED_DATA_REPORT_SCHEMA_VERSION,
        "split": split,
        "status": "blocked_data_unavailable",
    }
