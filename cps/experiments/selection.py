from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Callable, Iterable, Sequence

from cps.experiments.synthetic_regimes import SyntheticItem


ValueFunction = Callable[[Iterable[str]], float]


@dataclass(frozen=True)
class SelectionResult:
    algorithm: str
    selected_ids: list[str]
    token_cost: int
    value: float
    trace: list[dict]


@dataclass(frozen=True)
class OracleSelectionResult:
    algorithm: str
    selected_ids: list[str]
    token_cost: int
    value: float | None
    trace: list[dict]
    oracle_status: str


def item_costs(items: Sequence[SyntheticItem]) -> dict[str, int]:
    return {item.item_id: int(item.token_cost) for item in items}


def total_cost(selected_ids: Iterable[str], costs: dict[str, int]) -> int:
    return sum(costs[item_id] for item_id in selected_ids)


def _trace_for_prefix(
    *,
    prefix_ids: Sequence[str],
    value_fn: ValueFunction,
    costs: dict[str, int],
    source: str,
) -> list[dict]:
    selected: list[str] = []
    trace: list[dict] = []
    current_value = value_fn(selected)
    for step_index, item_id in enumerate(prefix_ids, start=1):
        before = list(selected)
        selected.append(item_id)
        next_value = value_fn(selected)
        marginal = round(next_value - current_value, 6)
        singleton = round(value_fn([item_id]) - value_fn([]), 6)
        trace.append(
            {
                "step": step_index,
                "item_id": item_id,
                "selected_before": before,
                "marginal_gain": marginal,
                "singleton_gain": singleton,
                "token_cost": costs[item_id],
                "density": round(marginal / costs[item_id], 6),
                "source": source,
            }
        )
        current_value = next_value
    return trace


def greedy_select(
    *,
    items: Sequence[SyntheticItem],
    budget_tokens: int,
    value_fn: ValueFunction,
    initial_selected_ids: Sequence[str] | None = None,
    algorithm: str = "greedy",
) -> SelectionResult:
    costs = item_costs(items)
    all_ids = [item.item_id for item in items]
    selected = list(initial_selected_ids or [])
    trace = _trace_for_prefix(
        prefix_ids=selected,
        value_fn=value_fn,
        costs=costs,
        source="seed",
    )
    current_value = value_fn(selected)

    while True:
        used_tokens = total_cost(selected, costs)
        feasible = [
            item_id
            for item_id in all_ids
            if item_id not in selected and used_tokens + costs[item_id] <= budget_tokens
        ]
        if not feasible:
            break

        ranked: list[tuple[float, float, int, str, float]] = []
        for item_id in feasible:
            marginal = round(value_fn([*selected, item_id]) - current_value, 6)
            density = marginal / costs[item_id]
            ranked.append((density, marginal, -costs[item_id], item_id, marginal))
        density, _gain_sort, _cost_sort, item_id, marginal = max(ranked, key=lambda row: (row[0], row[1], row[2], row[3]))
        if marginal <= 0:
            break
        before = list(selected)
        selected.append(item_id)
        trace.append(
            {
                "step": len(trace) + 1,
                "item_id": item_id,
                "selected_before": before,
                "marginal_gain": round(marginal, 6),
                "singleton_gain": round(value_fn([item_id]) - value_fn([]), 6),
                "token_cost": costs[item_id],
                "density": round(density, 6),
                "source": "greedy_completion",
            }
        )
        current_value = value_fn(selected)

    return SelectionResult(
        algorithm=algorithm,
        selected_ids=selected,
        token_cost=total_cost(selected, costs),
        value=round(value_fn(selected), 6),
        trace=trace,
    )


def seeded_augmented_greedy(
    *,
    items: Sequence[SyntheticItem],
    budget_tokens: int,
    value_fn: ValueFunction,
    max_seed_size: int = 2,
) -> SelectionResult:
    costs = item_costs(items)
    item_ids = [item.item_id for item in items]
    seed_sets: list[tuple[str, ...]] = [()]
    for seed_size in range(1, max_seed_size + 1):
        seed_sets.extend(tuple(seed) for seed in combinations(item_ids, seed_size))

    best: SelectionResult | None = None
    for seed in seed_sets:
        if total_cost(seed, costs) > budget_tokens:
            continue
        result = greedy_select(
            items=items,
            budget_tokens=budget_tokens,
            value_fn=value_fn,
            initial_selected_ids=seed,
            algorithm="seeded_augmented_greedy",
        )
        if best is None or (result.value, -result.token_cost, tuple(result.selected_ids)) > (
            best.value,
            -best.token_cost,
            tuple(best.selected_ids),
        ):
            best = result
    if best is None:
        return SelectionResult(
            algorithm="seeded_augmented_greedy",
            selected_ids=[],
            token_cost=0,
            value=0.0,
            trace=[],
        )
    return best


def bounded_local_search(
    *,
    items: Sequence[SyntheticItem],
    budget_tokens: int,
    value_fn: ValueFunction,
    initial_selected_ids: Sequence[str] | None = None,
    max_iterations: int = 16,
) -> SelectionResult:
    costs = item_costs(items)
    item_ids = [item.item_id for item in items]
    if initial_selected_ids is None:
        selected = list(seeded_augmented_greedy(items=items, budget_tokens=budget_tokens, value_fn=value_fn).selected_ids)
    else:
        selected = list(initial_selected_ids)
    trace = _trace_for_prefix(prefix_ids=selected, value_fn=value_fn, costs=costs, source="initial")

    for _iteration in range(max_iterations):
        current_value = value_fn(selected)
        current_cost = total_cost(selected, costs)
        best_selected = list(selected)
        best_move: dict | None = None
        best_value = current_value

        for incoming in item_ids:
            if incoming in selected:
                continue
            if current_cost + costs[incoming] <= budget_tokens:
                candidate = [*selected, incoming]
                candidate_value = value_fn(candidate)
                if candidate_value > best_value:
                    best_value = candidate_value
                    best_selected = candidate
                    best_move = {"move": "add", "incoming": incoming, "outgoing": None}

            for outgoing in selected:
                candidate = [item_id for item_id in selected if item_id != outgoing]
                if total_cost(candidate, costs) + costs[incoming] > budget_tokens:
                    continue
                candidate.append(incoming)
                candidate_value = value_fn(candidate)
                if candidate_value > best_value:
                    best_value = candidate_value
                    best_selected = candidate
                    best_move = {"move": "swap", "incoming": incoming, "outgoing": outgoing}

        if best_move is None or best_value <= current_value:
            break
        selected = best_selected
        trace.append(
            {
                "step": len(trace) + 1,
                "item_id": best_move["incoming"],
                "selected_before": [],
                "marginal_gain": round(best_value - current_value, 6),
                "singleton_gain": round(value_fn([best_move["incoming"]]) - value_fn([]), 6),
                "token_cost": costs[best_move["incoming"]],
                "density": round((best_value - current_value) / costs[best_move["incoming"]], 6),
                "source": "local_search",
                **best_move,
            }
        )

    return SelectionResult(
        algorithm="interaction_aware_local_search",
        selected_ids=selected,
        token_cost=total_cost(selected, costs),
        value=round(value_fn(selected), 6),
        trace=trace,
    )


def brute_force_optimal_select(
    *,
    items: Sequence[SyntheticItem],
    budget_tokens: int,
    value_fn: ValueFunction,
    max_items: int = 20,
) -> OracleSelectionResult:
    if len(items) > max_items:
        return OracleSelectionResult(
            algorithm="brute_force_optimal",
            selected_ids=[],
            token_cost=0,
            value=None,
            trace=[],
            oracle_status="skipped_large_n",
        )

    costs = item_costs(items)
    item_ids = [item.item_id for item in items]
    best_ids: tuple[str, ...] = ()
    best_cost = 0
    best_value = 0.0

    for subset_size in range(len(item_ids) + 1):
        for subset in combinations(item_ids, subset_size):
            subset_cost = total_cost(subset, costs)
            if subset_cost > budget_tokens:
                continue
            subset_value = round(value_fn(subset), 6)
            candidate_key = (subset_value, -subset_cost, tuple(sorted(subset)))
            best_key = (best_value, -best_cost, tuple(sorted(best_ids)))
            if candidate_key > best_key:
                best_ids = tuple(subset)
                best_cost = subset_cost
                best_value = subset_value

    return OracleSelectionResult(
        algorithm="brute_force_optimal",
        selected_ids=list(best_ids),
        token_cost=best_cost,
        value=round(best_value, 6),
        trace=[
            {
                "oracle_status": "available",
                "max_items": max_items,
                "candidate_count": len(item_ids),
                "evaluated_subsets": 2 ** len(item_ids),
            }
        ],
        oracle_status="available",
    )
