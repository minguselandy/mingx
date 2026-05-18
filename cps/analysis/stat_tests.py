from __future__ import annotations

from typing import Sequence


def mean(values: Sequence[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def paired_mean_delta(target_values: Sequence[float], baseline_values: Sequence[float]) -> dict[str, float | int]:
    pairs = list(zip(target_values, baseline_values))
    deltas = [target - baseline for target, baseline in pairs]
    return {
        "matched_pairs": len(pairs),
        "mean_baseline": mean([baseline for _target, baseline in pairs]),
        "mean_delta": mean(deltas),
        "mean_target": mean([target for target, _baseline in pairs]),
    }
