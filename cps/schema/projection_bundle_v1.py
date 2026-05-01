from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, ClassVar

from cps.experiments.artifacts import stable_hash, stable_json_dumps, to_payload


REQUIRED_IDENTITY_FIELDS = ("run_id", "dispatch_id", "agent_id", "round_id")
REQUIRED_ARTIFACT_FIELDS = (
    "candidate_pool",
    "projection_plan",
    "budget_witness",
    "materialized_context",
    "metric_bridge_witness",
)


def _artifact_payload(value: Any, field_name: str) -> dict[str, Any]:
    if value is None:
        raise ValueError(f"{field_name} is required")
    payload = to_payload(value)
    if not isinstance(payload, dict):
        raise TypeError(f"{field_name} must serialize to a dict")
    return deepcopy(payload)


@dataclass(frozen=True)
class ProjectionBundleV1:
    run_id: str
    dispatch_id: str
    agent_id: str
    round_id: str
    candidate_pool: dict[str, Any]
    projection_plan: dict[str, Any]
    budget_witness: dict[str, Any]
    materialized_context: dict[str, Any]
    metric_bridge_witness: dict[str, Any]
    diagnostics: dict[str, Any] | None = None
    source_mode: str | None = None
    canonical_hash_value: str | None = None

    bundle_version: ClassVar[str] = "ProjectionBundleV1"

    def __post_init__(self) -> None:
        self.validate_required_identity()
        for field_name in REQUIRED_ARTIFACT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _artifact_payload(getattr(self, field_name), field_name),
            )
        if self.diagnostics is not None:
            object.__setattr__(self, "diagnostics", _artifact_payload(self.diagnostics, "diagnostics"))

    def validate_required_identity(self) -> None:
        for field_name in REQUIRED_IDENTITY_FIELDS:
            value = getattr(self, field_name)
            if value is None or str(value).strip() == "":
                raise ValueError(f"{field_name} is required")

    def to_dict(self) -> dict[str, Any]:
        self.validate_required_identity()
        payload: dict[str, Any] = {
            "bundle_version": self.bundle_version,
            "run_id": self.run_id,
            "dispatch_id": self.dispatch_id,
            "agent_id": self.agent_id,
            "round_id": self.round_id,
            "candidate_pool": deepcopy(self.candidate_pool),
            "projection_plan": deepcopy(self.projection_plan),
            "budget_witness": deepcopy(self.budget_witness),
            "materialized_context": deepcopy(self.materialized_context),
            "metric_bridge_witness": deepcopy(self.metric_bridge_witness),
        }
        if self.diagnostics is not None:
            payload["diagnostics"] = deepcopy(self.diagnostics)
        if self.source_mode is not None:
            payload["source_mode"] = self.source_mode
        if self.canonical_hash_value is not None:
            payload["canonical_hash"] = self.canonical_hash_value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ProjectionBundleV1:
        bundle_version = payload.get("bundle_version", cls.bundle_version)
        if bundle_version != cls.bundle_version:
            raise ValueError(f"unsupported bundle_version: {bundle_version}")
        for field_name in (*REQUIRED_IDENTITY_FIELDS, *REQUIRED_ARTIFACT_FIELDS):
            if field_name not in payload:
                raise ValueError(f"{field_name} is required")
        return cls(
            run_id=payload["run_id"],
            dispatch_id=payload["dispatch_id"],
            agent_id=payload["agent_id"],
            round_id=payload["round_id"],
            candidate_pool=payload["candidate_pool"],
            projection_plan=payload["projection_plan"],
            budget_witness=payload["budget_witness"],
            materialized_context=payload["materialized_context"],
            metric_bridge_witness=payload["metric_bridge_witness"],
            diagnostics=payload.get("diagnostics"),
            source_mode=payload.get("source_mode"),
            canonical_hash_value=payload.get("canonical_hash"),
        )

    def to_canonical_json(self) -> str:
        payload = self.to_dict()
        payload.pop("canonical_hash", None)
        return stable_json_dumps(payload)

    def canonical_hash(self) -> str:
        payload = self.to_dict()
        payload.pop("canonical_hash", None)
        return stable_hash(payload)


def projection_bundle_from_dict(payload: dict[str, Any]) -> ProjectionBundleV1:
    return ProjectionBundleV1.from_dict(payload)
