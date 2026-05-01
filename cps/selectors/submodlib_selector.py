from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Mapping, Sequence
from typing import Any

from cps.selectors.common import OptionalDependencyUnavailable, SelectorAdapterResult


def is_submodlib_available() -> bool:
    return importlib.util.find_spec("submodlib") is not None


def _load_submodlib(*, strict: bool) -> Any | None:
    try:
        return importlib.import_module("submodlib")
    except ImportError as exc:
        if strict:
            raise OptionalDependencyUnavailable("submodlib", "submodlib is not installed") from exc
        return None


def _cost_for(token_costs: Mapping[str, int] | Sequence[int], candidate_id: str, index: int) -> int:
    if isinstance(token_costs, Mapping):
        return int(token_costs[candidate_id])
    return int(token_costs[index])


def _unavailable_result(
    *,
    candidate_ids: Sequence[str],
    token_costs: Mapping[str, int] | Sequence[int],
    budget_tokens: int,
    reason: str,
) -> SelectorAdapterResult:
    return SelectorAdapterResult(
        selected_ids=[],
        excluded_ids=[str(candidate_id) for candidate_id in candidate_ids],
        selected_token_cost=0,
        budget_tokens=int(budget_tokens),
        selector_name="submodlib_facility_location",
        selector_available=False,
        score_trace=[],
        reason=reason,
        unavailable_reason="submodlib is not installed",
    )


def _parse_ranking_row(row: Any) -> tuple[int, float | None]:
    if isinstance(row, tuple | list):
        index = int(row[0])
        gain = None if len(row) < 2 else float(row[1])
        return index, gain
    return int(row), None


def select_with_submodlib(
    *,
    candidate_ids: Sequence[str],
    token_costs: Mapping[str, int] | Sequence[int],
    budget_tokens: int,
    feature_matrix: Sequence[Sequence[float]] | None = None,
    similarity_matrix: Sequence[Sequence[float]] | None = None,
    selector_config: Mapping[str, Any] | None = None,
    strict: bool = False,
) -> SelectorAdapterResult:
    ids = [str(candidate_id) for candidate_id in candidate_ids]
    costs = {candidate_id: _cost_for(token_costs, candidate_id, index) for index, candidate_id in enumerate(ids)}
    submodlib = _load_submodlib(strict=strict)
    if submodlib is None:
        return _unavailable_result(
            candidate_ids=ids,
            token_costs=costs,
            budget_tokens=budget_tokens,
            reason="optional dependency unavailable",
        )
    if feature_matrix is None and similarity_matrix is None:
        raise ValueError("feature_matrix or similarity_matrix is required when submodlib is available")

    config = dict(selector_config or {})
    optimizer = str(config.get("optimizer", "NaiveGreedy"))
    max_budget = len(ids)
    if similarity_matrix is not None:
        objective = submodlib.FacilityLocationFunction(
            n=len(ids),
            mode="dense",
            sijs=similarity_matrix,
            separate_rep=False,
        )
    else:
        objective = submodlib.FacilityLocationFunction(
            n=len(ids),
            data=feature_matrix,
            mode="dense",
            metric=str(config.get("metric", "euclidean")),
        )

    ranking = objective.maximize(
        budget=max_budget,
        optimizer=optimizer,
        stopIfZeroGain=False,
        stopIfNegativeGain=False,
        verbose=False,
        show_progress=False,
    )
    selected: list[str] = []
    selected_cost = 0
    trace: list[dict[str, Any]] = []
    for rank, row in enumerate(ranking, start=1):
        index, gain = _parse_ranking_row(row)
        candidate_id = ids[index]
        candidate_cost = costs[candidate_id]
        accepted = selected_cost + candidate_cost <= int(budget_tokens)
        if accepted:
            selected.append(candidate_id)
            selected_cost += candidate_cost
        trace.append(
            {
                "rank": rank,
                "candidate_id": candidate_id,
                "token_cost": candidate_cost,
                "gain": gain,
                "accepted": accepted,
            }
        )

    selected_set = set(selected)
    return SelectorAdapterResult(
        selected_ids=selected,
        excluded_ids=[candidate_id for candidate_id in ids if candidate_id not in selected_set],
        selected_token_cost=selected_cost,
        budget_tokens=int(budget_tokens),
        selector_name="submodlib_facility_location",
        selector_available=True,
        score_trace=trace,
        reason="selected with submodlib FacilityLocationFunction",
        unavailable_reason=None,
    )
