from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Mapping
from typing import Sequence


@dataclass(frozen=True)
class SelectionRequest:
    dataset: str
    instance_id: str
    query: str
    candidate_pool: Mapping[str, Any]
    budget: int
    role: str = "evidence_grounded_answerer"


@dataclass(frozen=True)
class SelectionResult:
    selector_name: str
    candidate_pool_hash: str
    selected_packet_ids: tuple[str, ...]
    excluded_packet_ids: tuple[str, ...]
    considered_packet_ids: tuple[str, ...]
    selected_packets: tuple[dict[str, Any], ...]
    scores_by_packet_id: dict[str, float]
    budget_requested: int
    budget_used: int
    selector_regime_label: str
    metric_claim_level: str = "operational_utility_only"
    selector_deployability: str = "deployable_operational_baseline"

    def projection_plan(self) -> dict[str, Any]:
        return {
            "budget_realized": self.budget_used,
            "budget_requested": self.budget_requested,
            "candidate_pool_hash": self.candidate_pool_hash,
            "considered_candidate_packet_ids": list(self.considered_packet_ids),
            "excluded_packet_ids": list(self.excluded_packet_ids),
            "metric_claim_level": self.metric_claim_level,
            "scores_by_packet_id": {
                packet_id: round(float(score), 12)
                for packet_id, score in sorted(self.scores_by_packet_id.items())
            },
            "selected_packet_ids": list(self.selected_packet_ids),
            "selector_deployability": self.selector_deployability,
            "selector_name": self.selector_name,
            "selector_regime_label": self.selector_regime_label,
        }


SelectorFn = Any


def packet_ids(packets: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    return tuple(str(packet.get("packet_id") or "") for packet in packets if packet.get("packet_id"))
