from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


class OptionalDependencyUnavailable(RuntimeError):
    def __init__(self, dependency_name: str, message: str | None = None) -> None:
        self.dependency_name = dependency_name
        super().__init__(message or f"{dependency_name} is not installed")


@dataclass(frozen=True)
class SelectorAdapterResult:
    selected_ids: list[str]
    excluded_ids: list[str]
    selected_token_cost: int
    budget_tokens: int
    selector_name: str
    selector_available: bool
    score_trace: list[dict[str, Any]]
    reason: str
    unavailable_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OracleAdapterResult:
    selected_ids: list[str]
    objective_value: float | None
    selected_token_cost: int
    budget_tokens: int
    solver_status: str
    optimality_gap: float | None
    oracle_name: str
    oracle_available: bool
    unavailable_reason: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
