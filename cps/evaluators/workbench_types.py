from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Mapping
from typing import Sequence


@dataclass(frozen=True)
class EvaluationRequest:
    dataset: str
    instance_id: str
    query: str
    target: Mapping[str, Any]
    candidate_pool_hash: str
    selected_packets: Sequence[Mapping[str, Any]]
    all_packets: Sequence[Mapping[str, Any]]
    claim_mode: str = "shadow"


@dataclass(frozen=True)
class EvaluationResult:
    evaluator_name: str
    metrics: dict[str, Any]
    claim_flags: dict[str, bool]
    claim_mode: str = "shadow"

    def to_payload(self) -> dict[str, Any]:
        return {
            "claim_flags": dict(sorted(self.claim_flags.items())),
            "claim_mode": self.claim_mode,
            "evaluator_name": self.evaluator_name,
            "metrics": dict(sorted(self.metrics.items())),
        }
