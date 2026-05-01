from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Mapping, Sequence
from typing import Any

from cps.selectors.common import OptionalDependencyUnavailable, OracleAdapterResult


def is_ortools_available() -> bool:
    return importlib.util.find_spec("ortools") is not None


def _load_cp_model(*, strict: bool) -> Any | None:
    try:
        return importlib.import_module("ortools.sat.python.cp_model")
    except ImportError as exc:
        if strict:
            raise OptionalDependencyUnavailable("ortools", "ortools is not installed") from exc
        return None


def _value_for(values: Mapping[str, float] | Sequence[float], candidate_id: str, index: int) -> float:
    if isinstance(values, Mapping):
        return float(values[candidate_id])
    return float(values[index])


def _cost_for(token_costs: Mapping[str, int] | Sequence[int], candidate_id: str, index: int) -> int:
    if isinstance(token_costs, Mapping):
        return int(token_costs[candidate_id])
    return int(token_costs[index])


def _unavailable_result(*, budget_tokens: int, reason: str) -> OracleAdapterResult:
    return OracleAdapterResult(
        selected_ids=[],
        objective_value=None,
        selected_token_cost=0,
        budget_tokens=int(budget_tokens),
        solver_status="unavailable",
        optimality_gap=None,
        oracle_name="ortools_cp_sat",
        oracle_available=False,
        unavailable_reason="ortools is not installed",
        reason=reason,
    )


def _scale(value: float, scale_factor: int = 1_000_000) -> int:
    return int(round(float(value) * scale_factor))


def _normalized_pairwise_bonuses(pairwise_bonuses: Mapping[Any, float] | None) -> dict[tuple[str, str], float]:
    normalized: dict[tuple[str, str], float] = {}
    for key, value in dict(pairwise_bonuses or {}).items():
        if isinstance(key, tuple | list) and len(key) == 2:
            left, right = str(key[0]), str(key[1])
        else:
            left, right = str(key).split("|", 1)
        if left == right:
            continue
        normalized[tuple(sorted((left, right)))] = float(value)
    return normalized


def solve_knapsack_with_ortools(
    *,
    candidate_ids: Sequence[str],
    token_costs: Mapping[str, int] | Sequence[int],
    singleton_values: Mapping[str, float] | Sequence[float],
    budget_tokens: int,
    pairwise_bonuses: Mapping[Any, float] | None = None,
    max_items: int = 80,
    max_pairwise_terms: int = 400,
    time_limit_seconds: float = 5.0,
    strict: bool = False,
) -> OracleAdapterResult:
    ids = [str(candidate_id) for candidate_id in candidate_ids]
    if len(ids) > max_items:
        return OracleAdapterResult(
            selected_ids=[],
            objective_value=None,
            selected_token_cost=0,
            budget_tokens=int(budget_tokens),
            solver_status="skipped_large_n",
            optimality_gap=None,
            oracle_name="ortools_cp_sat",
            oracle_available=False,
            unavailable_reason=None,
            reason=f"instance has {len(ids)} items; max_items is {max_items}",
        )
    normalized_pairs = _normalized_pairwise_bonuses(pairwise_bonuses)
    if len(normalized_pairs) > max_pairwise_terms:
        return OracleAdapterResult(
            selected_ids=[],
            objective_value=None,
            selected_token_cost=0,
            budget_tokens=int(budget_tokens),
            solver_status="skipped_large_pairwise",
            optimality_gap=None,
            oracle_name="ortools_cp_sat",
            oracle_available=False,
            unavailable_reason=None,
            reason=f"instance has {len(normalized_pairs)} pairwise terms; max_pairwise_terms is {max_pairwise_terms}",
        )

    cp_model = _load_cp_model(strict=strict)
    if cp_model is None:
        return _unavailable_result(budget_tokens=budget_tokens, reason="optional dependency unavailable")

    costs = {candidate_id: _cost_for(token_costs, candidate_id, index) for index, candidate_id in enumerate(ids)}
    values = {candidate_id: _value_for(singleton_values, candidate_id, index) for index, candidate_id in enumerate(ids)}
    model = cp_model.CpModel()
    x_vars = {candidate_id: model.NewBoolVar(f"x_{index}") for index, candidate_id in enumerate(ids)}
    model.Add(sum(costs[candidate_id] * x_vars[candidate_id] for candidate_id in ids) <= int(budget_tokens))

    objective_terms = [_scale(values[candidate_id]) * x_vars[candidate_id] for candidate_id in ids]
    pair_vars = {}
    for pair_index, ((left, right), bonus) in enumerate(sorted(normalized_pairs.items())):
        if left not in x_vars or right not in x_vars:
            continue
        y_var = model.NewBoolVar(f"y_{pair_index}")
        model.Add(y_var <= x_vars[left])
        model.Add(y_var <= x_vars[right])
        model.Add(y_var >= x_vars[left] + x_vars[right] - 1)
        pair_vars[(left, right)] = y_var
        objective_terms.append(_scale(bonus) * y_var)
    model.Maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    status = solver.Solve(model)
    status_name = {
        cp_model.OPTIMAL: "optimal",
        cp_model.FEASIBLE: "feasible",
        cp_model.INFEASIBLE: "infeasible",
        cp_model.MODEL_INVALID: "model_invalid",
        cp_model.UNKNOWN: "unknown",
    }.get(status, "unknown")
    if status_name not in {"optimal", "feasible"}:
        return OracleAdapterResult(
            selected_ids=[],
            objective_value=None,
            selected_token_cost=0,
            budget_tokens=int(budget_tokens),
            solver_status=status_name,
            optimality_gap=None,
            oracle_name="ortools_cp_sat",
            oracle_available=True,
            unavailable_reason=None,
            reason="solver did not return a feasible selection",
        )

    selected = [candidate_id for candidate_id in ids if solver.Value(x_vars[candidate_id])]
    selected_cost = sum(costs[candidate_id] for candidate_id in selected)
    objective_value = round(float(solver.ObjectiveValue()) / 1_000_000, 6)
    optimality_gap = 0.0 if status_name == "optimal" else None
    return OracleAdapterResult(
        selected_ids=selected,
        objective_value=objective_value,
        selected_token_cost=selected_cost,
        budget_tokens=int(budget_tokens),
        solver_status=status_name,
        optimality_gap=optimality_gap,
        oracle_name="ortools_cp_sat",
        oracle_available=True,
        unavailable_reason=None,
        reason="solved with OR-Tools CP-SAT",
    )
