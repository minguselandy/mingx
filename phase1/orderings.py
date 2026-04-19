from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class OrderingSpec:
    ordering_id: str
    paragraph_ids: tuple[int, ...]


def _question_seed(question_id: str) -> int:
    digest = hashlib.sha256(question_id.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def build_orderings(
    question_id: str,
    paragraph_ids: list[int] | tuple[int, ...],
    k_lcb: int = 5,
    canonical_ordering_id: str = "canonical_v1",
    seed: int = 20260418,
) -> list[OrderingSpec]:
    canonical = tuple(paragraph_ids)
    if k_lcb <= 0:
        raise ValueError("k_lcb must be positive")

    orderings = [OrderingSpec(ordering_id=canonical_ordering_id, paragraph_ids=canonical)]
    if k_lcb == 1 or len(canonical) <= 1:
        return orderings

    rng = random.Random(_question_seed(f"{question_id}|{seed}"))
    seen = {canonical}
    attempts = 0
    max_attempts = 1000

    while len(orderings) < k_lcb and attempts < max_attempts:
        attempts += 1
        candidate = list(canonical)
        rng.shuffle(candidate)
        candidate_tuple = tuple(candidate)
        if candidate_tuple in seen:
            continue
        seen.add(candidate_tuple)
        orderings.append(
            OrderingSpec(
                ordering_id=f"permutation_{len(orderings)}",
                paragraph_ids=candidate_tuple,
            )
        )

    if len(orderings) != k_lcb:
        raise RuntimeError(f"Unable to produce {k_lcb} unique orderings for {question_id}")
    return orderings
