from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.common import pool_payload
from cps.benchmarks.common import pool_packets
from cps.benchmarks.common import write_json


MANIFEST_SCHEMA_VERSION = "workbench_candidate_pool_manifest_v1"
HARD_NEGATIVE_LABELS = {"same_context_distractor", "same_page_distractor", "retrieved_distractor"}


@dataclass(frozen=True)
class CandidatePoolContractResult:
    schema_valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _pool_hash(record: Mapping[str, Any]) -> str:
    return str(pool_payload(record).get("candidate_pool_hash") or "").strip()


def validate_candidate_pool_contract(records: Sequence[Mapping[str, Any]]) -> CandidatePoolContractResult:
    errors: list[str] = []
    warnings: list[str] = []
    seen_hashes: set[str] = set()
    for row_index, record in enumerate(records, start=1):
        pool = pool_payload(record)
        pool_hash = _pool_hash(record)
        if not pool_hash:
            errors.append(f"row_{row_index}:missing_candidate_pool_hash")
        elif pool_hash in seen_hashes:
            warnings.append(f"row_{row_index}:duplicate_candidate_pool_hash")
        seen_hashes.add(pool_hash)

        packets = pool_packets(record)
        if not packets:
            errors.append(f"row_{row_index}:empty_candidate_pool")
            continue
        packet_ids: set[str] = set()
        hard_negative_count = 0
        gold_count = 0
        for packet_index, packet in enumerate(packets, start=1):
            packet_id = str(packet.get("packet_id") or "").strip()
            if not packet_id:
                errors.append(f"row_{row_index}:packet_{packet_index}:missing_packet_id")
            elif packet_id in packet_ids:
                errors.append(f"row_{row_index}:packet_{packet_index}:duplicate_packet_id")
            packet_ids.add(packet_id)
            if "token_cost" not in packet:
                errors.append(f"row_{row_index}:packet_{packet_index}:missing_token_cost")
            label = str(packet.get("gold_support_label") or "")
            if label == "gold_supporting":
                gold_count += 1
                if not isinstance(packet.get("provenance"), Mapping):
                    errors.append(f"row_{row_index}:packet_{packet_index}:missing_gold_support_provenance")
            if label in HARD_NEGATIVE_LABELS:
                hard_negative_count += 1
        if gold_count == 0:
            warnings.append(f"row_{row_index}:no_gold_support_packets")
        if hard_negative_count == 0:
            warnings.append(f"row_{row_index}:no_hard_negative_packets")
    return CandidatePoolContractResult(
        schema_valid=not errors,
        errors=tuple(sorted(set(errors))),
        warnings=tuple(sorted(set(warnings))),
    )


def build_candidate_pool_manifest(
    records: Sequence[Mapping[str, Any]],
    *,
    dataset: str,
    budgets: Sequence[int],
) -> dict[str, Any]:
    validation = validate_candidate_pool_contract(records)
    unique_records = sorted((dict(record) for record in records), key=_pool_hash)
    hashes = [_pool_hash(record) for record in unique_records if _pool_hash(record)]
    budget_keys = [str(int(budget)) for budget in budgets]
    reachable = {budget: 0 for budget in budget_keys}
    gold_packets = 0
    hard_negative_packets = 0
    total_packets = 0
    for record in unique_records:
        pool = pool_payload(record)
        for budget in budget_keys:
            if bool((pool.get("gold_reachable_under_budget") or {}).get(budget)):
                reachable[budget] += 1
        packets = pool_packets(record)
        total_packets += len(packets)
        gold_packets += sum(1 for packet in packets if packet.get("gold_support_label") == "gold_supporting")
        hard_negative_packets += sum(
            1 for packet in packets if str(packet.get("gold_support_label") or "") in HARD_NEGATIVE_LABELS
        )
    return {
        "candidate_pool_hashes": sorted(hashes),
        "claim_status": "operational_utility_only; no_claim_upgrade",
        "contract_errors": list(validation.errors),
        "contract_warnings": list(validation.warnings),
        "dataset": dataset,
        "gold_packets": gold_packets,
        "gold_reachable_by_budget": reachable,
        "hard_negative_packets": hard_negative_packets,
        "pool_count": len(records),
        "provenance_complete": not any("missing_gold_support_provenance" in error for error in validation.errors),
        "schema_valid": validation.schema_valid,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "total_packets": total_packets,
    }


def write_candidate_pool_manifest(path: str | Path, manifest: Mapping[str, Any]) -> Path:
    return write_json(path, manifest)
