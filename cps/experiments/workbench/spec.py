from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence


SHADOW_LABELS = (
    "shadow_metric_bridge",
    "shadow_vinfo_proxy",
    "shadow_measurement_candidate",
    "shadow_selector_superiority",
)


@dataclass(frozen=True)
class WorkbenchRunSpec:
    run_id: str
    dataset: str
    candidate_pools_path: str
    output_dir: str
    budgets: tuple[int, ...]
    selectors: tuple[str, ...]
    evaluators: tuple[str, ...]
    claim_mode: str = "shadow"
    claim_status: str = "operational_utility_only; no_claim_upgrade"
    limit: int = 20
    shadow_labels: tuple[str, ...] = SHADOW_LABELS

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "WorkbenchRunSpec":
        claim_mode = str(payload.get("claim_mode") or "shadow")
        if claim_mode != "shadow":
            raise ValueError("workbench claim_mode must remain shadow")
        return cls(
            budgets=tuple(int(budget) for budget in payload["budgets"]),
            candidate_pools_path=str(payload["candidate_pools_path"]),
            claim_mode=claim_mode,
            dataset=str(payload["dataset"]),
            evaluators=tuple(str(item) for item in payload["evaluators"]),
            limit=int(payload.get("limit", 20)),
            output_dir=str(payload["output_dir"]),
            run_id=str(payload["run_id"]),
            selectors=tuple(str(item) for item in payload["selectors"]),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "budgets": list(self.budgets),
            "candidate_pools_path": self.candidate_pools_path,
            "claim_mode": self.claim_mode,
            "claim_status": self.claim_status,
            "dataset": self.dataset,
            "evaluators": list(self.evaluators),
            "limit": self.limit,
            "output_dir": self.output_dir,
            "run_id": self.run_id,
            "selectors": list(self.selectors),
            "shadow_labels": list(self.shadow_labels),
        }


def _load_json_or_json_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name}: workbench spec must be a JSON object")
    return payload


def load_workbench_spec(path: str | Path) -> WorkbenchRunSpec:
    return WorkbenchRunSpec.from_mapping(_load_json_or_json_yaml(Path(path)))
