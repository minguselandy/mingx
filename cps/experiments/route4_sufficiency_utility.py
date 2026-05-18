from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any
from typing import Mapping
from typing import Sequence


GOLD_SUPPORT_LABEL = "gold_supporting"
UTILITY_DEFINITION = "route4_hotpotqa_sufficiency_coverage_v1"
UTILITY_SOURCE = "hotpotqa_gold_support_packets_and_source_doc_ids"


@dataclass(frozen=True)
class SufficiencyUtilityResult:
    baseline_utility: float
    augmented_utility: float
    delta_utility: float
    sufficiency_level_baseline: str
    sufficiency_level_augmented: str
    full_support_hit_delta: int
    evidence_coverage_delta: float
    source_coverage_delta: float
    missing_prerequisite_delta: int
    contradiction_penalty_delta: float
    utility_source_provenance: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


def _candidate_pool(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    pool = payload.get("candidate_pool")
    if not isinstance(pool, Mapping):
        raise ValueError("missing_candidate_pool")
    return pool


def _packet_id(packet: Mapping[str, Any]) -> str:
    return str(packet.get("packet_id") or "").strip()


def _source_doc_id(packet: Mapping[str, Any]) -> str:
    return str(packet.get("source_doc_id") or (packet.get("provenance") or {}).get("source_doc_id") or "").strip()


def _is_gold(packet: Mapping[str, Any]) -> bool:
    return str(packet.get("gold_support_label") or "") == GOLD_SUPPORT_LABEL


def hotpotqa_packet_lookup(pool_payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    pool = _candidate_pool(pool_payload)
    if not str(pool.get("candidate_pool_hash") or "").strip():
        raise ValueError("missing_candidate_pool_hash")
    packets = pool.get("packets")
    if not isinstance(packets, list) or not packets:
        raise ValueError("missing_candidate_pool_packets")
    lookup: dict[str, dict[str, Any]] = {}
    for packet in packets:
        if not isinstance(packet, Mapping):
            continue
        packet_id = _packet_id(packet)
        if packet_id:
            lookup[packet_id] = dict(packet)
    if not lookup:
        raise ValueError("missing_packet_ids")
    return lookup


def _gold_packet_ids(lookup: Mapping[str, Mapping[str, Any]]) -> tuple[str, ...]:
    return tuple(sorted(packet_id for packet_id, packet in lookup.items() if _is_gold(packet)))


def _gold_source_docs(lookup: Mapping[str, Mapping[str, Any]], gold_ids: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({_source_doc_id(lookup[packet_id]) for packet_id in gold_ids if _source_doc_id(lookup[packet_id])}))


def _validate_selected_ids(lookup: Mapping[str, Mapping[str, Any]], ids: Sequence[str]) -> tuple[str, ...]:
    parsed = tuple(str(packet_id).strip() for packet_id in ids if str(packet_id).strip())
    for packet_id in parsed:
        if packet_id not in lookup:
            raise ValueError(f"unknown_packet_id:{packet_id}")
    return parsed


def _coverage(selected_ids: Sequence[str], gold_ids: Sequence[str]) -> float:
    if not gold_ids:
        raise ValueError("missing_gold_support_packets")
    return len(set(selected_ids).intersection(gold_ids)) / len(set(gold_ids))


def _source_coverage(
    lookup: Mapping[str, Mapping[str, Any]],
    selected_ids: Sequence[str],
    gold_source_docs: Sequence[str],
) -> float:
    if not gold_source_docs:
        raise ValueError("missing_gold_support_source_docs")
    selected_docs = {_source_doc_id(lookup[packet_id]) for packet_id in selected_ids if packet_id in lookup}
    return len(selected_docs.intersection(gold_source_docs)) / len(set(gold_source_docs))


def _sufficiency_score(packet_recall: float, source_recall: float, full_support_hit: int) -> float:
    return round((0.45 * packet_recall) + (0.35 * source_recall) + (0.20 * full_support_hit), 12)


def _sufficiency_level(packet_recall: float, source_recall: float, full_support_hit: int) -> str:
    if full_support_hit:
        return "complete_support"
    if packet_recall > 0 or source_recall > 0:
        return "partial_support"
    return "none"


def compute_hotpotqa_sufficiency_utility(
    pool_payload: Mapping[str, Any],
    *,
    context_ids: Sequence[str],
    block_ids: Sequence[str],
) -> SufficiencyUtilityResult:
    lookup = hotpotqa_packet_lookup(pool_payload)
    parsed_context = _validate_selected_ids(lookup, context_ids)
    parsed_block = _validate_selected_ids(lookup, block_ids)
    if not parsed_block:
        raise ValueError("empty_block_A_packet_ids")

    gold_ids = _gold_packet_ids(lookup)
    gold_docs = _gold_source_docs(lookup, gold_ids)
    baseline_ids = tuple(dict.fromkeys(parsed_context))
    augmented_ids = tuple(dict.fromkeys((*parsed_context, *parsed_block)))

    baseline_packet_recall = _coverage(baseline_ids, gold_ids)
    augmented_packet_recall = _coverage(augmented_ids, gold_ids)
    baseline_source_recall = _source_coverage(lookup, baseline_ids, gold_docs)
    augmented_source_recall = _source_coverage(lookup, augmented_ids, gold_docs)
    baseline_full_support = int(set(gold_ids).issubset(baseline_ids))
    augmented_full_support = int(set(gold_ids).issubset(augmented_ids))

    baseline_utility = _sufficiency_score(baseline_packet_recall, baseline_source_recall, baseline_full_support)
    augmented_utility = _sufficiency_score(augmented_packet_recall, augmented_source_recall, augmented_full_support)
    baseline_missing = len(set(gold_ids) - set(baseline_ids))
    augmented_missing = len(set(gold_ids) - set(augmented_ids))

    return SufficiencyUtilityResult(
        augmented_utility=augmented_utility,
        baseline_utility=baseline_utility,
        contradiction_penalty_delta=0.0,
        delta_utility=round(augmented_utility - baseline_utility, 12),
        evidence_coverage_delta=round(augmented_packet_recall - baseline_packet_recall, 12),
        full_support_hit_delta=augmented_full_support - baseline_full_support,
        missing_prerequisite_delta=augmented_missing - baseline_missing,
        source_coverage_delta=round(augmented_source_recall - baseline_source_recall, 12),
        sufficiency_level_augmented=_sufficiency_level(
            augmented_packet_recall,
            augmented_source_recall,
            augmented_full_support,
        ),
        sufficiency_level_baseline=_sufficiency_level(
            baseline_packet_recall,
            baseline_source_recall,
            baseline_full_support,
        ),
        utility_source_provenance={
            "gold_support_packet_count": len(gold_ids),
            "gold_support_source_doc_count": len(gold_docs),
            "utility_definition": UTILITY_DEFINITION,
            "utility_source": UTILITY_SOURCE,
            "uses_logloss_or_model_probability": False,
        },
    )
