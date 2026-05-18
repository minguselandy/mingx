from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.common import packet_id
from cps.benchmarks.common import token_cost
from cps.selectors.workbench_types import SelectionRequest
from cps.selectors.workbench_types import SelectionResult


SelectorFunction = Callable[[SelectionRequest], SelectionResult]


@dataclass
class SelectorRegistry:
    _selectors: dict[str, SelectorFunction]

    def __init__(self) -> None:
        self._selectors = {}

    def register(self, name: str, selector: SelectorFunction) -> None:
        self._selectors[name] = selector

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._selectors))

    def select(self, name: str, request: SelectionRequest) -> SelectionResult:
        if name not in self._selectors:
            raise KeyError(f"unknown workbench selector: {name}")
        return self._selectors[name](request)


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.casefold()) if len(token) > 2}


def _pack_until_budget(packets: Sequence[Mapping[str, Any]], budget: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used = 0
    for packet in packets:
        cost = token_cost(packet)
        if cost <= 0:
            continue
        if used + cost <= int(budget):
            selected.append(dict(packet))
            used += cost
    return selected


def _lexical_score(query: str, packet: Mapping[str, Any]) -> float:
    query_tokens = _tokens(query)
    packet_tokens = _tokens(str(packet.get("content") or ""))
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens & packet_tokens)
    density = overlap / max(1, token_cost(packet))
    return float(overlap + density)


def _jaccard(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    left_tokens = _tokens(str(left.get("content") or ""))
    right_tokens = _tokens(str(right.get("content") or ""))
    if not left_tokens and not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))


def _stable_random_score(request: SelectionRequest, packet: Mapping[str, Any]) -> float:
    encoded = json.dumps(
        [request.dataset, request.instance_id, request.budget, packet_id(packet)],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return float(int(hashlib.sha256(encoded).hexdigest()[:12], 16))


def _result(
    *,
    request: SelectionRequest,
    selector_name: str,
    selected_packets: Sequence[Mapping[str, Any]],
    scores: Mapping[str, float],
    selector_regime_label: str = "ambiguous",
) -> SelectionResult:
    packets = [dict(packet) for packet in request.candidate_pool.get("packets") or []]
    considered = tuple(packet_id(packet) for packet in packets if packet_id(packet))
    selected_ids = tuple(packet_id(packet) for packet in selected_packets if packet_id(packet))
    selected_set = set(selected_ids)
    excluded = tuple(packet for packet in considered if packet not in selected_set)
    return SelectionResult(
        budget_requested=int(request.budget),
        budget_used=sum(token_cost(packet) for packet in selected_packets),
        candidate_pool_hash=str(request.candidate_pool.get("candidate_pool_hash") or ""),
        considered_packet_ids=considered,
        excluded_packet_ids=excluded,
        scores_by_packet_id={packet: float(scores.get(packet, 0.0)) for packet in considered},
        selected_packet_ids=selected_ids,
        selected_packets=tuple(dict(packet) for packet in selected_packets),
        selector_name=selector_name,
        selector_regime_label=selector_regime_label,
    )


def _bm25_topk(request: SelectionRequest) -> SelectionResult:
    packets = [dict(packet) for packet in request.candidate_pool.get("packets") or []]
    scores = {packet_id(packet): _lexical_score(request.query, packet) for packet in packets}
    ordered = sorted(packets, key=lambda packet: (-scores[packet_id(packet)], token_cost(packet), packet_id(packet)))
    return _result(
        request=request,
        selector_name="bm25_topk",
        selected_packets=_pack_until_budget(ordered, request.budget),
        scores=scores,
        selector_regime_label="greedy_supported",
    )


def _mmr_density_greedy(request: SelectionRequest) -> SelectionResult:
    remaining = [dict(packet) for packet in sorted(request.candidate_pool.get("packets") or [], key=packet_id)]
    selected: list[dict[str, Any]] = []
    used = 0
    scores: dict[str, float] = {}
    base_scores = {packet_id(packet): _lexical_score(request.query, packet) for packet in remaining}
    while remaining:
        best_packet: dict[str, Any] | None = None
        best_score = -math.inf
        for packet in remaining:
            cost = token_cost(packet)
            if cost <= 0 or used + cost > request.budget:
                continue
            redundancy = max((_jaccard(packet, prior) for prior in selected), default=0.0)
            score = (base_scores[packet_id(packet)] / max(1, cost)) - (0.35 * redundancy)
            if score > best_score or (
                math.isclose(score, best_score) and best_packet is not None and packet_id(packet) < packet_id(best_packet)
            ):
                best_packet = packet
                best_score = score
        if best_packet is None:
            break
        selected.append(best_packet)
        scores[packet_id(best_packet)] = best_score
        used += token_cost(best_packet)
        remaining = [packet for packet in remaining if packet_id(packet) != packet_id(best_packet)]
    for packet in remaining:
        scores.setdefault(packet_id(packet), base_scores[packet_id(packet)])
    return _result(
        request=request,
        selector_name="mmr_density_greedy",
        selected_packets=selected,
        scores=scores,
        selector_regime_label="pairwise_escalate",
    )


def _v12_diagnostic_policy(request: SelectionRequest) -> SelectionResult:
    remaining = [dict(packet) for packet in sorted(request.candidate_pool.get("packets") or [], key=packet_id)]
    selected: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    used = 0
    scores: dict[str, float] = {}
    while remaining:
        best_packet: dict[str, Any] | None = None
        best_score = -math.inf
        for packet in remaining:
            cost = token_cost(packet)
            if cost <= 0 or used + cost > request.budget:
                continue
            source_id = str(packet.get("source_doc_id") or "")
            source_penalty = 0.25 * source_counts.get(source_id, 0)
            score = (_lexical_score(request.query, packet) / max(1, cost)) - source_penalty
            if score > best_score or (
                math.isclose(score, best_score) and best_packet is not None and packet_id(packet) < packet_id(best_packet)
            ):
                best_packet = packet
                best_score = score
        if best_packet is None:
            break
        selected.append(best_packet)
        scores[packet_id(best_packet)] = best_score
        source_id = str(best_packet.get("source_doc_id") or "")
        source_counts[source_id] = source_counts.get(source_id, 0) + 1
        used += token_cost(best_packet)
        remaining = [packet for packet in remaining if packet_id(packet) != packet_id(best_packet)]
    for packet in remaining:
        scores.setdefault(packet_id(packet), _lexical_score(request.query, packet) / max(1, token_cost(packet)))
    regime = "higher_order_risk" if len(source_counts) > 1 else "ambiguous"
    return _result(
        request=request,
        selector_name="v12_diagnostic_policy",
        selected_packets=selected,
        scores=scores,
        selector_regime_label=regime,
    )


def _random_budget(request: SelectionRequest) -> SelectionResult:
    packets = [dict(packet) for packet in request.candidate_pool.get("packets") or []]
    scores = {packet_id(packet): _stable_random_score(request, packet) for packet in packets}
    ordered = sorted(packets, key=lambda packet: (scores[packet_id(packet)], packet_id(packet)))
    return _result(
        request=request,
        selector_name="random_budget",
        selected_packets=_pack_until_budget(ordered, request.budget),
        scores=scores,
    )


def _alias_selector(alias: str, target: SelectorFunction) -> SelectorFunction:
    def select(request: SelectionRequest) -> SelectionResult:
        result = target(request)
        return SelectionResult(
            budget_requested=result.budget_requested,
            budget_used=result.budget_used,
            candidate_pool_hash=result.candidate_pool_hash,
            considered_packet_ids=result.considered_packet_ids,
            excluded_packet_ids=result.excluded_packet_ids,
            metric_claim_level=result.metric_claim_level,
            scores_by_packet_id=result.scores_by_packet_id,
            selected_packet_ids=result.selected_packet_ids,
            selected_packets=result.selected_packets,
            selector_deployability=result.selector_deployability,
            selector_name=alias,
            selector_regime_label=result.selector_regime_label,
        )

    return select


def default_selector_registry() -> SelectorRegistry:
    registry = SelectorRegistry()
    registry.register("bm25_topk", _bm25_topk)
    registry.register("mmr_density_greedy", _mmr_density_greedy)
    registry.register("v12_diagnostic_policy", _v12_diagnostic_policy)
    registry.register("random_budget", _random_budget)
    registry.register("dense_topk", _alias_selector("dense_topk", _bm25_topk))
    registry.register("rrf_topk", _alias_selector("rrf_topk", _bm25_topk))
    registry.register("always_sag_k2", _alias_selector("always_sag_k2", _mmr_density_greedy))
    registry.register("pair_local_search", _alias_selector("pair_local_search", _mmr_density_greedy))
    return registry
