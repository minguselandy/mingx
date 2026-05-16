from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.hashing import canonical_json_dumps


PHASE = "P56-HotpotQA"
RUN_ID = "P56-HotpotQA-operational-dispatch-v1"
DATASET = "HotpotQA"
TASK_FAMILY = "hotpotqa_answer_support_selection"
TRACE_SCHEMA_VERSION = "p56_hotpotqa_operational_dispatch_trace_v1"
OPERATIONAL_METRIC_CLAIM_LEVEL = "operational_utility_only"
BRIDGE_STATUS = "failed_or_absent"
BRIDGE_SOURCE = "P63R HotpotQA failed_closed_gate_failed / FixB operational_utility_only"
BUDGETS = (512, 1024)
MINIMAL_SELECTORS = (
    "random_budget",
    "topk_relevance_or_token_budget",
    "mmr_density_greedy",
    "v12_cost_aware_diagnostic_policy_operational_only",
    "gold_support_oracle_upper_bound",
)
ALLOWED_SELECTOR_REGIME_LABELS = {"greedy_supported", "pairwise_escalate", "higher_order_risk", "ambiguous"}
DEFAULT_CANDIDATE_POOLS_PATH = "artifacts/benchmarks/hotpotqa_candidate_pools.jsonl"
DEFAULT_TRACES_PATH = "artifacts/operator_inputs/p56_realistic_dispatch_traces.jsonl"
DEFAULT_REPORT_PATH = "artifacts/benchmarks/p56_hotpotqa_trace_generation_report.json"
DEFAULT_DOC_PATH = "docs/experiments/P56-hotpotqa-operational-dispatch-traces.md"
DENIED_CLAIMS = (
    "calibrated_proxy_supported",
    "vinfo_proxy_supported",
    "measurement validation",
    "paper evidence",
    "P55 bridge support",
    "selector superiority",
)


@dataclass(frozen=True)
class P56TraceValidationResult:
    errors: tuple[str, ...]
    schema_valid: bool
    traces_generated: int
    traces_validated: int


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(str(input_path))
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{input_path.name}: line {line_number} must be a JSON object")
        rows.append(payload)
    return rows


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.name if candidate.is_absolute() else candidate.as_posix()


def _stable_digest(payload: Any, *, length: int = 16) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.casefold()) if len(token) > 2}


def _token_count(packet: Mapping[str, Any]) -> int:
    try:
        parsed = int(packet.get("token_cost"))
    except (TypeError, ValueError):
        parsed = 0
    return max(0, parsed)


def _packet_id(packet: Mapping[str, Any]) -> str:
    return str(packet.get("packet_id") or "")


def _gold_packet_ids(packets: Sequence[Mapping[str, Any]]) -> set[str]:
    return {
        _packet_id(packet)
        for packet in packets
        if str(packet.get("gold_support_label") or "") == "gold_supporting" and _packet_id(packet)
    }


def _packet_by_id(packets: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {_packet_id(packet): dict(packet) for packet in packets if _packet_id(packet)}


def _lexical_score(query: str, packet: Mapping[str, Any]) -> float:
    query_tokens = _tokens(query)
    packet_tokens = _tokens(str(packet.get("content") or ""))
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens & packet_tokens)
    density = overlap / max(1, _token_count(packet))
    return overlap + density


def _jaccard(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    left_tokens = _tokens(str(left.get("content") or ""))
    right_tokens = _tokens(str(right.get("content") or ""))
    if not left_tokens and not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))


def _pack_until_budget(ordered_packets: Sequence[Mapping[str, Any]], budget: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    used = 0
    for packet in ordered_packets:
        cost = _token_count(packet)
        if cost <= 0:
            continue
        if used + cost <= budget:
            selected.append(dict(packet))
            used += cost
    return selected


def _random_budget_selector(
    *,
    packets: Sequence[Mapping[str, Any]],
    query: str,
    budget: int,
    instance_id: str,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    scored = []
    for packet in packets:
        score = int(_stable_digest([RUN_ID, instance_id, budget, _packet_id(packet)], length=12), 16)
        scored.append((score, _packet_id(packet), packet))
    ordered = [packet for _score, _packet_id_value, packet in sorted(scored)]
    return _pack_until_budget(ordered, budget), {
        _packet_id(packet): float(score)
        for score, _packet_id_value, packet in scored
    }


def _topk_selector(
    *,
    packets: Sequence[Mapping[str, Any]],
    query: str,
    budget: int,
    instance_id: str,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    scores = {_packet_id(packet): _lexical_score(query, packet) for packet in packets}
    ordered = sorted(
        packets,
        key=lambda packet: (-scores[_packet_id(packet)], _token_count(packet), _packet_id(packet)),
    )
    return _pack_until_budget(ordered, budget), scores


def _mmr_selector(
    *,
    packets: Sequence[Mapping[str, Any]],
    query: str,
    budget: int,
    instance_id: str,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    remaining = [dict(packet) for packet in sorted(packets, key=_packet_id)]
    selected: list[dict[str, Any]] = []
    used = 0
    base_scores = {_packet_id(packet): _lexical_score(query, packet) for packet in remaining}
    emitted_scores: dict[str, float] = {}
    while remaining:
        best_packet: dict[str, Any] | None = None
        best_score = -math.inf
        for packet in remaining:
            cost = _token_count(packet)
            if cost <= 0 or used + cost > budget:
                continue
            redundancy = max((_jaccard(packet, prior) for prior in selected), default=0.0)
            score = (base_scores[_packet_id(packet)] / max(1, cost)) - (0.35 * redundancy)
            if score > best_score or (
                math.isclose(score, best_score) and best_packet is not None and _packet_id(packet) < _packet_id(best_packet)
            ):
                best_packet = packet
                best_score = score
        if best_packet is None:
            break
        selected.append(best_packet)
        emitted_scores[_packet_id(best_packet)] = best_score
        used += _token_count(best_packet)
        remaining = [packet for packet in remaining if _packet_id(packet) != _packet_id(best_packet)]
    for packet in remaining:
        emitted_scores.setdefault(_packet_id(packet), base_scores[_packet_id(packet)])
    return selected, emitted_scores


def _v12_operational_selector(
    *,
    packets: Sequence[Mapping[str, Any]],
    query: str,
    budget: int,
    instance_id: str,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    selected: list[dict[str, Any]] = []
    used = 0
    source_counts: Counter[str] = Counter()
    scores: dict[str, float] = {}
    remaining = [dict(packet) for packet in sorted(packets, key=_packet_id)]
    while remaining:
        best_packet: dict[str, Any] | None = None
        best_score = -math.inf
        for packet in remaining:
            cost = _token_count(packet)
            if cost <= 0 or used + cost > budget:
                continue
            source_id = str(packet.get("source_doc_id") or "")
            source_penalty = 0.25 * source_counts[source_id]
            score = (_lexical_score(query, packet) / max(1, cost)) - source_penalty
            if score > best_score or (
                math.isclose(score, best_score) and best_packet is not None and _packet_id(packet) < _packet_id(best_packet)
            ):
                best_packet = packet
                best_score = score
        if best_packet is None:
            break
        selected.append(best_packet)
        scores[_packet_id(best_packet)] = best_score
        source_counts[str(best_packet.get("source_doc_id") or "")] += 1
        used += _token_count(best_packet)
        remaining = [packet for packet in remaining if _packet_id(packet) != _packet_id(best_packet)]
    for packet in remaining:
        scores.setdefault(_packet_id(packet), _lexical_score(query, packet) / max(1, _token_count(packet)))
    return selected, scores


def _oracle_selector(
    *,
    packets: Sequence[Mapping[str, Any]],
    query: str,
    budget: int,
    instance_id: str,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    scores = {
        _packet_id(packet): (1000.0 + _lexical_score(query, packet))
        if str(packet.get("gold_support_label") or "") == "gold_supporting"
        else _lexical_score(query, packet)
        for packet in packets
    }
    ordered = sorted(
        packets,
        key=lambda packet: (-scores[_packet_id(packet)], _token_count(packet), _packet_id(packet)),
    )
    return _pack_until_budget(ordered, budget), scores


def _select_packets(
    *,
    selector_name: str,
    packets: Sequence[Mapping[str, Any]],
    query: str,
    budget: int,
    instance_id: str,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    if selector_name == "random_budget":
        return _random_budget_selector(packets=packets, query=query, budget=budget, instance_id=instance_id)
    if selector_name == "topk_relevance_or_token_budget":
        return _topk_selector(packets=packets, query=query, budget=budget, instance_id=instance_id)
    if selector_name == "mmr_density_greedy":
        return _mmr_selector(packets=packets, query=query, budget=budget, instance_id=instance_id)
    if selector_name == "v12_cost_aware_diagnostic_policy_operational_only":
        return _v12_operational_selector(packets=packets, query=query, budget=budget, instance_id=instance_id)
    if selector_name == "gold_support_oracle_upper_bound":
        return _oracle_selector(packets=packets, query=query, budget=budget, instance_id=instance_id)
    raise ValueError(f"unknown selector: {selector_name}")


def _metric_bridge_witness() -> dict[str, Any]:
    return {
        "bridge_status": BRIDGE_STATUS,
        "calibrated_proxy_supported": False,
        "metric_claim_level": OPERATIONAL_METRIC_CLAIM_LEVEL,
        "source": BRIDGE_SOURCE,
        "vinfo_proxy_supported": False,
    }


def _materialized_context(selected_packets: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    sections = [
        {
            "content": str(packet.get("content") or ""),
            "packet_id": _packet_id(packet),
            "source_doc_id": str(packet.get("source_doc_id") or ""),
            "token_cost": _token_count(packet),
        }
        for packet in selected_packets
    ]
    return {
        "materialization_policy": "fixed_selector_order_with_source_boundaries",
        "materialization_order": [section["packet_id"] for section in sections],
        "sections": sections,
        "text": "\n\n".join(section["content"] for section in sections),
    }


def _evaluation(
    *,
    answer: str,
    gold_ids: set[str],
    selected_packets: Sequence[Mapping[str, Any]],
    selected_tokens: int,
    budget: int,
) -> dict[str, Any]:
    selected_ids = {_packet_id(packet) for packet in selected_packets}
    selected_gold = sorted(gold_ids & selected_ids)
    context_text = "\n".join(str(packet.get("content") or "") for packet in selected_packets).casefold()
    answer_present = bool(answer and answer.casefold() in context_text)
    return {
        "answer_available_if_present": answer_present,
        "budget_used": selected_tokens,
        "gold_support_packets_selected": selected_gold,
        "gold_support_packets_selected_count": len(selected_gold),
        "selected_tokens": selected_tokens,
        "supporting_fact_recall_at_budget": round(len(selected_gold) / len(gold_ids), 6) if gold_ids else 0.0,
        "within_budget": selected_tokens <= budget,
    }


def _trace_for_selection(
    *,
    budget: int,
    packet_scores: Mapping[str, float],
    pool: Mapping[str, Any],
    selected_packets: Sequence[Mapping[str, Any]],
    selector_name: str,
) -> dict[str, Any]:
    instance_id = str(pool.get("instance_id") or "")
    query = str(pool.get("query") or "")
    candidate_pool = dict(pool.get("candidate_pool") or {})
    candidate_pool_hash = str(candidate_pool.get("candidate_pool_hash") or "")
    packets = [dict(packet) for packet in candidate_pool.get("packets") or []]
    packet_ids = [_packet_id(packet) for packet in packets]
    selected_ids = [_packet_id(packet) for packet in selected_packets]
    excluded_ids = [packet_id for packet_id in packet_ids if packet_id not in set(selected_ids)]
    selected_tokens = sum(_token_count(packet) for packet in selected_packets)
    gold_ids = _gold_packet_ids(packets)
    answer = str((pool.get("target") or {}).get("label") or "")
    oracle = selector_name == "gold_support_oracle_upper_bound"
    dispatch_id = "p56::hotpotqa::operational::" + _stable_digest(
        [instance_id, candidate_pool_hash, budget, selector_name],
        length=24,
    )
    return {
        "agent_id": "answer_worker",
        "budget_B_i": budget,
        "budget_witness": {
            "budget_requested": budget,
            "budget_used": selected_tokens,
            "remaining_tokens": max(0, budget - selected_tokens),
            "selected_packet_token_costs": {
                _packet_id(packet): _token_count(packet)
                for packet in selected_packets
            },
            "selected_tokens": selected_tokens,
            "within_budget": selected_tokens <= budget,
        },
        "candidate_pool_hash": candidate_pool_hash,
        "considered_candidate_packet_ids": packet_ids,
        "dataset": DATASET,
        "dispatch_id": dispatch_id,
        "evaluation": _evaluation(
            answer=answer,
            budget=budget,
            gold_ids=gold_ids,
            selected_packets=selected_packets,
            selected_tokens=selected_tokens,
        ),
        "excluded_packet_ids": excluded_ids,
        "gold_target": {
            "answer": answer,
            "supporting_packet_ids": sorted(gold_ids),
            "target_type": "answer_string",
        },
        "materialized_context": _materialized_context(selected_packets),
        "metric_bridge_witness": _metric_bridge_witness(),
        "metric_claim_level": OPERATIONAL_METRIC_CLAIM_LEVEL,
        "projection_plan": {
            "budget_requested": budget,
            "candidate_pool_hash": candidate_pool_hash,
            "considered_candidate_packet_ids": packet_ids,
            "excluded_packet_ids": excluded_ids,
            "non_deployable_upper_bound": oracle,
            "scores_by_packet_id": {
                packet_id: round(float(packet_scores.get(packet_id, 0.0)), 12)
                for packet_id in packet_ids
            },
            "selected_packet_ids": selected_ids,
            "selector_deployability": "non_deployable_upper_bound" if oracle else "deployable_operational_baseline",
            "selector_name": selector_name,
        },
        "role_R_i": "evidence_grounded_answerer",
        "round_id": 1,
        "run_id": RUN_ID,
        "schema_version": TRACE_SCHEMA_VERSION,
        "selected_packet_ids": selected_ids,
        "selector_name": selector_name,
        "selector_regime_label": "ambiguous",
        "split": str(pool.get("split") or ""),
        "task_family": TASK_FAMILY,
        "task_q_i": query,
    }


def _pool_valid(pool: Mapping[str, Any]) -> bool:
    candidate_pool = pool.get("candidate_pool") or {}
    return bool(
        pool.get("dataset") == DATASET
        and pool.get("task_family") == TASK_FAMILY
        and candidate_pool.get("candidate_pool_hash")
        and candidate_pool.get("packets")
    )


def validate_p56_traces(traces: Sequence[Mapping[str, Any]]) -> P56TraceValidationResult:
    errors: list[str] = []
    required_fields = (
        "run_id",
        "dispatch_id",
        "dataset",
        "task_family",
        "agent_id",
        "round_id",
        "task_q_i",
        "role_R_i",
        "budget_B_i",
        "candidate_pool_hash",
        "considered_candidate_packet_ids",
        "selected_packet_ids",
        "excluded_packet_ids",
        "projection_plan",
        "budget_witness",
        "materialized_context",
        "metric_bridge_witness",
        "selector_regime_label",
        "metric_claim_level",
        "gold_target",
        "evaluation",
    )
    seen_dispatch_ids: set[str] = set()
    for index, trace in enumerate(traces, start=1):
        for field in required_fields:
            if field not in trace or trace.get(field) in (None, ""):
                errors.append(f"row_{index}:missing_{field}")
        if trace.get("dispatch_id") in seen_dispatch_ids:
            errors.append(f"row_{index}:duplicate_dispatch_id")
        seen_dispatch_ids.add(str(trace.get("dispatch_id") or ""))
        if trace.get("dataset") != DATASET:
            errors.append(f"row_{index}:dataset_not_hotpotqa")
        if trace.get("task_family") != TASK_FAMILY:
            errors.append(f"row_{index}:wrong_task_family")
        if trace.get("selector_name") not in MINIMAL_SELECTORS:
            errors.append(f"row_{index}:invalid_selector_name")
        if trace.get("selector_regime_label") not in ALLOWED_SELECTOR_REGIME_LABELS:
            errors.append(f"row_{index}:invalid_selector_regime_label")
        if trace.get("metric_claim_level") != OPERATIONAL_METRIC_CLAIM_LEVEL:
            errors.append(f"row_{index}:metric_claim_level_not_operational_utility_only")
        bridge = trace.get("metric_bridge_witness") or {}
        if bridge.get("bridge_status") != BRIDGE_STATUS:
            errors.append(f"row_{index}:metric_bridge_witness_not_failed_or_absent")
        if bridge.get("source") != BRIDGE_SOURCE:
            errors.append(f"row_{index}:metric_bridge_witness_source_mismatch")
        considered = set(str(packet_id) for packet_id in trace.get("considered_candidate_packet_ids") or [])
        selected = set(str(packet_id) for packet_id in trace.get("selected_packet_ids") or [])
        excluded = set(str(packet_id) for packet_id in trace.get("excluded_packet_ids") or [])
        if selected - considered:
            errors.append(f"row_{index}:selected_packet_ids_not_in_considered_candidates")
        if excluded - considered:
            errors.append(f"row_{index}:excluded_packet_ids_not_in_considered_candidates")
        if selected & excluded:
            errors.append(f"row_{index}:selected_excluded_overlap")
        if considered and (selected | excluded) != considered:
            errors.append(f"row_{index}:considered_selected_excluded_not_complete")
        budget_witness = trace.get("budget_witness") or {}
        if not budget_witness:
            errors.append(f"row_{index}:budget_witness_missing")
        if budget_witness.get("within_budget") is not True:
            errors.append(f"row_{index}:budget_witness_not_within_budget")
        materialized_context = trace.get("materialized_context") or {}
        if not materialized_context.get("sections") or not materialized_context.get("materialization_order"):
            errors.append(f"row_{index}:materialized_context_missing")
        plan = trace.get("projection_plan") or {}
        if plan.get("selector_name") != trace.get("selector_name"):
            errors.append(f"row_{index}:projection_plan_selector_mismatch")
        if trace.get("selector_name") == "gold_support_oracle_upper_bound":
            if plan.get("selector_deployability") != "non_deployable_upper_bound" or plan.get("non_deployable_upper_bound") is not True:
                errors.append(f"row_{index}:oracle_not_marked_non_deployable_upper_bound")
    return P56TraceValidationResult(
        errors=tuple(sorted(set(errors))),
        schema_valid=not errors,
        traces_generated=len(traces),
        traces_validated=0 if errors else len(traces),
    )


def generate_hotpotqa_operational_traces(
    candidate_pools: Sequence[Mapping[str, Any]],
    *,
    budgets: Sequence[int] = BUDGETS,
    limit: int | None = 200,
    selectors: Sequence[str] = MINIMAL_SELECTORS,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected_pools = [dict(pool) for pool in candidate_pools if _pool_valid(pool)]
    selected_pools = selected_pools[:limit] if limit is not None else selected_pools
    traces: list[dict[str, Any]] = []
    for pool in selected_pools:
        packets = [dict(packet) for packet in (pool.get("candidate_pool") or {}).get("packets") or []]
        for budget in budgets:
            for selector_name in selectors:
                selected_packets, scores = _select_packets(
                    budget=int(budget),
                    instance_id=str(pool.get("instance_id") or ""),
                    packets=packets,
                    query=str(pool.get("query") or ""),
                    selector_name=selector_name,
                )
                if not selected_packets:
                    continue
                traces.append(
                    _trace_for_selection(
                        budget=int(budget),
                        packet_scores=scores,
                        pool=pool,
                        selected_packets=selected_packets,
                        selector_name=selector_name,
                    )
                )
    traces = sorted(
        traces,
        key=lambda trace: (
            trace["dataset"],
            trace["task_family"],
            trace["task_q_i"],
            trace["budget_B_i"],
            trace["selector_name"],
            trace["dispatch_id"],
        ),
    )
    validation = validate_p56_traces(traces)
    report = _generation_report(
        budgets=budgets,
        candidate_pools_used=len(selected_pools),
        selectors=selectors,
        traces=traces,
        validation=validation,
    )
    if not validation.schema_valid:
        raise ValueError(";".join(validation.errors))
    return traces, report


def _mean(values: Sequence[float]) -> float | None:
    return round(sum(values) / len(values), 6) if values else None


def _generation_report(
    *,
    budgets: Sequence[int],
    candidate_pools_used: int,
    selectors: Sequence[str],
    traces: Sequence[Mapping[str, Any]],
    validation: P56TraceValidationResult,
) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = {}
    for trace in traces:
        key = f"{trace['selector_name']}::budget_{trace['budget_B_i']}"
        bucket = grouped.setdefault(
            key,
            {
                "answer_available_count": 0,
                "mean_budget_used": [],
                "mean_selected_tokens": [],
                "mean_supporting_fact_recall_at_budget": [],
                "selector_name": trace["selector_name"],
                "budget": trace["budget_B_i"],
                "trace_count": 0,
            },
        )
        evaluation = trace["evaluation"]
        bucket["trace_count"] += 1
        bucket["answer_available_count"] += int(bool(evaluation["answer_available_if_present"]))
        bucket["mean_budget_used"].append(float(evaluation["budget_used"]))
        bucket["mean_selected_tokens"].append(float(evaluation["selected_tokens"]))
        bucket["mean_supporting_fact_recall_at_budget"].append(float(evaluation["supporting_fact_recall_at_budget"]))
    operational_metrics = {
        key: {
            **{k: v for k, v in bucket.items() if not isinstance(v, list)},
            "mean_budget_used": _mean(bucket["mean_budget_used"]),
            "mean_selected_tokens": _mean(bucket["mean_selected_tokens"]),
            "mean_supporting_fact_recall_at_budget": _mean(bucket["mean_supporting_fact_recall_at_budget"]),
        }
        for key, bucket in sorted(grouped.items())
    }
    return {
        "bridge_witness_status": BRIDGE_STATUS,
        "budgets": [int(budget) for budget in budgets],
        "candidate_pools_used": candidate_pools_used,
        "claim_status": "operational_utility_only; no_claim_upgrade",
        "dataset": DATASET,
        "denied_claims": list(DENIED_CLAIMS),
        "metric_bridge_witness": _metric_bridge_witness(),
        "metric_claim_level": OPERATIONAL_METRIC_CLAIM_LEVEL,
        "operational_metrics": operational_metrics,
        "phase": PHASE,
        "selectors": list(selectors),
        "status": "p56_hotpotqa_operational_traces_generated",
        "task_family": TASK_FAMILY,
        "traces_generated": validation.traces_generated,
        "traces_validated": validation.traces_validated,
        "validation_errors": list(validation.errors),
    }


def write_p56_trace_jsonl(path: str | Path, traces: Sequence[Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(canonical_json_dumps(dict(trace)) + "\n" for trace in traces),
        encoding="utf-8",
    )
    return output_path


def _write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def _write_doc(path: str | Path, report: Mapping[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P56 HotpotQA Operational Dispatch Traces",
        "",
        "## Purpose",
        "",
        "P56 generates HotpotQA realistic dispatch traces for operational replay only.",
        "The current P63R bridge attempts failed or are positive-control only, so these traces do not carry metric bridge support.",
        "",
        "## Inputs",
        "",
        f"- Candidate pools: `{DEFAULT_CANDIDATE_POOLS_PATH}`",
        f"- Dataset: `{DATASET}`",
        f"- Task family: `{TASK_FAMILY}`",
        "",
        "## Outputs",
        "",
        f"- Traces: `{DEFAULT_TRACES_PATH}`",
        f"- Generation report: `{DEFAULT_REPORT_PATH}`",
        "",
        "## Results",
        "",
        f"- Traces generated: `{report.get('traces_generated')}`",
        f"- Traces validated: `{report.get('traces_validated')}`",
        f"- Budgets: `{report.get('budgets')}`",
        f"- Selectors: `{report.get('selectors')}`",
        f"- Metric claim level: `{report.get('metric_claim_level')}`",
        f"- Bridge witness status: `{report.get('bridge_witness_status')}`",
        "",
        "## Claim Boundary",
        "",
        "- Allowed claim: P56 HotpotQA operational dispatch traces generated and validated under `operational_utility_only`.",
        "- No `calibrated_proxy_supported` claim is introduced.",
        "- No `vinfo_proxy_supported` claim is introduced.",
        "- No measurement validation, paper evidence, P55 bridge support, or selector superiority claim is introduced.",
        "- P66 comparison artifacts are intentionally not created here.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def run_hotpotqa_p56_trace_generation(
    *,
    budgets: Sequence[int] = BUDGETS,
    candidate_pools_path: str | Path = DEFAULT_CANDIDATE_POOLS_PATH,
    doc_path: str | Path = DEFAULT_DOC_PATH,
    limit: int | None = 200,
    report_path: str | Path = DEFAULT_REPORT_PATH,
    selectors: Sequence[str] = MINIMAL_SELECTORS,
    traces_path: str | Path = DEFAULT_TRACES_PATH,
) -> dict[str, Any]:
    candidate_pools = _read_jsonl(candidate_pools_path)
    traces, report = generate_hotpotqa_operational_traces(
        candidate_pools,
        budgets=budgets,
        limit=limit,
        selectors=selectors,
    )
    report = {
        **report,
        "candidate_pools_path": _path_ref(candidate_pools_path),
        "doc_path": _path_ref(doc_path),
        "traces_path": _path_ref(traces_path),
    }
    write_p56_trace_jsonl(traces_path, traces)
    _write_json(report_path, report)
    _write_doc(doc_path, report)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate P56 HotpotQA operational dispatch traces.")
    parser.add_argument("--candidate-pools-path", default=DEFAULT_CANDIDATE_POOLS_PATH)
    parser.add_argument("--traces-path", default=DEFAULT_TRACES_PATH)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--doc-path", default=DEFAULT_DOC_PATH)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--budgets", nargs="+", type=int, default=list(BUDGETS))
    args = parser.parse_args(argv)
    report = run_hotpotqa_p56_trace_generation(
        budgets=tuple(args.budgets),
        candidate_pools_path=args.candidate_pools_path,
        doc_path=args.doc_path,
        limit=args.limit,
        report_path=args.report_path,
        traces_path=args.traces_path,
    )
    print(
        json.dumps(
            {
                "bridge_witness_status": report["bridge_witness_status"],
                "metric_claim_level": report["metric_claim_level"],
                "traces_generated": report["traces_generated"],
                "traces_validated": report["traces_validated"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
