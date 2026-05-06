from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Sequence

from cps.experiments.artifacts import candidate_pool_hash, context_hash


RUN_ID = "phase-c-realistic-task-benchmark-v1"
PROTOCOL_VERSION = "phase_c.realistic_task.v1"
CONDITION_ORDER = (
    "no_cps_baseline",
    "heuristic_selector_baseline",
    "cps_runtime_audit_scaffold",
    "diagnostic_guided_escalation",
)
CONDITION_ALGORITHMS = {
    "no_cps_baseline": "fixed_author_order_pack",
    "heuristic_selector_baseline": "heuristic_score_pack",
    "cps_runtime_audit_scaffold": "audited_singleton_greedy",
    "diagnostic_guided_escalation": "diagnostic_guided_synergy_seed",
}
OUTPUT_FILENAMES = (
    "candidate_pools.jsonl",
    "projection_plans.jsonl",
    "budget_witnesses.jsonl",
    "materialized_contexts.jsonl",
    "metric_bridge_witnesses.jsonl",
    "diagnostics.jsonl",
    "phase_c_manifest.json",
    "phase_c_dispatches.jsonl",
    "phase_c_condition_results.json",
    "phase_c_replay_status.json",
    "phase_c_diagnostics_summary.json",
    "phase_c_task_metrics.json",
    "phase_c_claim_gate_report.json",
    "phase_c_report.md",
)
DENIED_CLAIMS = (
    "measurement_validated",
    "scientific_validation",
    "deployed_v_information_certification",
    "Vinfo_proxy_certified",
)


@dataclass(frozen=True)
class TaskContextItem:
    item_id: str
    token_cost: int
    singleton_value: float
    heuristic_score: float
    author_order: int
    text: str
    tags: tuple[str, ...]

    def to_payload(self, *, task_id: str) -> dict[str, Any]:
        metadata = {
            "task_id": task_id,
            "phase": "P43",
            "source": "phase_c_realistic_task_fixture",
            "tags": list(self.tags),
            "author_order": self.author_order,
            "heuristic_score": self.heuristic_score,
        }
        return {
            "item_id": self.item_id,
            "candidate_id": self.item_id,
            "token_cost": self.token_cost,
            "singleton_value": self.singleton_value,
            "heuristic_score": self.heuristic_score,
            "author_order": self.author_order,
            "text": self.text,
            "content": self.text,
            "tags": list(self.tags),
            "provenance": {
                "source": "phase_c_realistic_task_fixture",
                "task_id": task_id,
            },
            "metadata": metadata,
        }


@dataclass(frozen=True)
class RealisticTask:
    task_id: str
    task_family: str
    question: str
    expected_answer: str
    budget_tokens: int
    candidates: tuple[TaskContextItem, ...]
    support_ids: tuple[str, ...]
    synergy_pairs: dict[tuple[str, str], float]
    agent_id: str = "phase_c_answering_agent"
    round_id: str = "phase_c_round_1"

    def candidate_payloads(self) -> list[dict[str, Any]]:
        return [item.to_payload(task_id=self.task_id) for item in self.candidates]

    def candidate_pool_hash(self) -> str:
        return candidate_pool_hash(self.candidate_payloads())

    def item_lookup(self) -> dict[str, TaskContextItem]:
        return {item.item_id: item for item in self.candidates}

    def value(self, selected_ids: Iterable[str]) -> float:
        selected = set(selected_ids)
        lookup = self.item_lookup()
        value = sum(lookup[item_id].singleton_value for item_id in selected)
        for pair, bonus in self.synergy_pairs.items():
            if set(pair).issubset(selected):
                value += bonus
        return round(value, 6)


def _pair(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def _default_tasks() -> tuple[RealisticTask, ...]:
    task_a = RealisticTask(
        task_id="realistic_bridge_lookup",
        task_family="multi_hop_retrieval",
        question="Which city is home to the university that hosts the Ada Lovelace fellowship?",
        expected_answer="Riverton",
        budget_tokens=34,
        support_ids=("a_bridge_university", "a_answer_city"),
        synergy_pairs={},
        candidates=(
            TaskContextItem(
                item_id="a_system_instruction",
                token_cost=14,
                singleton_value=0.02,
                heuristic_score=0.25,
                author_order=1,
                text="Follow the project evidence policy before answering the task.",
                tags=("instruction",),
            ),
            TaskContextItem(
                item_id="a_decoy_exhibit",
                token_cost=16,
                singleton_value=0.10,
                heuristic_score=0.88,
                author_order=2,
                text="A Riverton museum hosts an exhibit about Ada Lovelace.",
                tags=("lexical_overlap", "decoy"),
            ),
            TaskContextItem(
                item_id="a_bridge_university",
                token_cost=17,
                singleton_value=0.38,
                heuristic_score=0.76,
                author_order=3,
                text="The Ada Lovelace Research Fellowship is hosted by Northbridge University.",
                tags=("entity_bridge", "support"),
            ),
            TaskContextItem(
                item_id="a_answer_city",
                token_cost=15,
                singleton_value=0.40,
                heuristic_score=0.74,
                author_order=4,
                text="Northbridge University is located in Riverton.",
                tags=("answer_support", "support"),
            ),
            TaskContextItem(
                item_id="a_alumni_note",
                token_cost=13,
                singleton_value=0.12,
                heuristic_score=0.50,
                author_order=5,
                text="Northbridge alumni often publish short research notes.",
                tags=("background",),
            ),
        ),
    )
    task_b = RealisticTask(
        task_id="realistic_runtime_triage",
        task_family="runtime_trace_triage",
        question="Which paired evidence explains why the worker failed after dispatch?",
        expected_answer="Tool timeout and retry fanout caused the worker failure.",
        budget_tokens=35,
        support_ids=("b_tool_trace", "b_error_log"),
        synergy_pairs={_pair("b_tool_trace", "b_error_log"): 0.60},
        candidates=(
            TaskContextItem(
                item_id="b_run_summary",
                token_cost=14,
                singleton_value=0.30,
                heuristic_score=0.80,
                author_order=1,
                text="The run summary says the worker failed after dispatch.",
                tags=("summary",),
            ),
            TaskContextItem(
                item_id="b_status_decoy",
                token_cost=16,
                singleton_value=0.28,
                heuristic_score=0.78,
                author_order=2,
                text="A status row says a later cleanup task succeeded.",
                tags=("status", "decoy"),
            ),
            TaskContextItem(
                item_id="b_error_log",
                token_cost=17,
                singleton_value=0.22,
                heuristic_score=0.45,
                author_order=3,
                text="The worker error log reports retry fanout after an upstream timeout.",
                tags=("error_log", "support"),
            ),
            TaskContextItem(
                item_id="b_tool_trace",
                token_cost=18,
                singleton_value=0.22,
                heuristic_score=0.48,
                author_order=4,
                text="The tool trace records a timeout on the dependency used by that worker.",
                tags=("tool_trace", "support"),
            ),
            TaskContextItem(
                item_id="b_fix_hint",
                token_cost=13,
                singleton_value=0.16,
                heuristic_score=0.55,
                author_order=5,
                text="A fix note recommends reducing fanout when timeouts cluster.",
                tags=("remediation",),
            ),
        ),
    )
    return (task_a, task_b)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _selected_token_cost(task: RealisticTask, selected_ids: Iterable[str]) -> int:
    lookup = task.item_lookup()
    return sum(lookup[item_id].token_cost for item_id in selected_ids)


def _excluded_ids(task: RealisticTask, selected_ids: Sequence[str]) -> list[str]:
    selected = set(selected_ids)
    return sorted(item.item_id for item in task.candidates if item.item_id not in selected)


def _pack_until_budget(
    task: RealisticTask,
    ordered_items: Sequence[TaskContextItem],
    *,
    source: str,
) -> tuple[list[str], list[dict[str, Any]]]:
    selected: list[str] = []
    trace: list[dict[str, Any]] = []
    used_tokens = 0
    for item in ordered_items:
        selected_before = list(selected)
        decision = "selected"
        if used_tokens + item.token_cost <= task.budget_tokens:
            selected.append(item.item_id)
            used_tokens += item.token_cost
        else:
            decision = "skipped_budget"
        trace.append(
            {
                "step": len(trace) + 1,
                "item_id": item.item_id,
                "selected_before": selected_before,
                "token_cost": item.token_cost,
                "used_tokens_after": used_tokens,
                "decision": decision,
                "source": source,
            }
        )
    return selected, trace


def _no_cps_selection(task: RealisticTask) -> tuple[list[str], list[dict[str, Any]]]:
    return _pack_until_budget(
        task,
        sorted(task.candidates, key=lambda item: (item.author_order, item.item_id)),
        source="fixed_author_order",
    )


def _heuristic_selection(task: RealisticTask) -> tuple[list[str], list[dict[str, Any]]]:
    return _pack_until_budget(
        task,
        sorted(
            task.candidates,
            key=lambda item: (item.heuristic_score / item.token_cost, item.heuristic_score, item.item_id),
            reverse=True,
        ),
        source="heuristic_score_density",
    )


def _singleton_greedy_selection(task: RealisticTask) -> tuple[list[str], list[dict[str, Any]]]:
    return _pack_until_budget(
        task,
        sorted(
            task.candidates,
            key=lambda item: (item.singleton_value / item.token_cost, item.singleton_value, item.item_id),
            reverse=True,
        ),
        source="audited_singleton_value_density",
    )


def _diagnostic_guided_selection(task: RealisticTask) -> tuple[list[str], list[dict[str, Any]]]:
    if not task.synergy_pairs:
        selected, trace = _singleton_greedy_selection(task)
        for row in trace:
            row["source"] = "diagnostic_guided_fallback_singleton_greedy"
        return selected, trace

    lookup = task.item_lookup()
    feasible_pairs: list[tuple[float, int, tuple[str, str]]] = []
    for pair, bonus in task.synergy_pairs.items():
        pair_cost = _selected_token_cost(task, pair)
        if pair_cost <= task.budget_tokens:
            pair_value = sum(lookup[item_id].singleton_value for item_id in pair) + bonus
            feasible_pairs.append((round(pair_value / pair_cost, 6), -pair_cost, pair))
    if not feasible_pairs:
        return _singleton_greedy_selection(task)

    _density, _negative_cost, seed_pair = max(feasible_pairs, key=lambda row: (row[0], row[1], row[2]))
    selected = list(seed_pair)
    used_tokens = _selected_token_cost(task, selected)
    trace = [
        {
            "step": 1,
            "item_id": item_id,
            "selected_before": list(seed_pair[:index]),
            "token_cost": lookup[item_id].token_cost,
            "used_tokens_after": _selected_token_cost(task, seed_pair[: index + 1]),
            "decision": "selected",
            "source": "diagnostic_synergy_seed",
        }
        for index, item_id in enumerate(seed_pair)
    ]
    remaining = [
        item
        for item in sorted(
            task.candidates,
            key=lambda item: (item.singleton_value / item.token_cost, item.singleton_value, item.item_id),
            reverse=True,
        )
        if item.item_id not in selected
    ]
    for item in remaining:
        selected_before = list(selected)
        decision = "skipped_budget"
        if used_tokens + item.token_cost <= task.budget_tokens:
            selected.append(item.item_id)
            used_tokens += item.token_cost
            decision = "selected"
        trace.append(
            {
                "step": len(trace) + 1,
                "item_id": item.item_id,
                "selected_before": selected_before,
                "token_cost": item.token_cost,
                "used_tokens_after": used_tokens,
                "decision": decision,
                "source": "diagnostic_guided_greedy_fill",
            }
        )
    return selected, trace


def _selection_for_condition(task: RealisticTask, condition: str) -> tuple[list[str], list[dict[str, Any]]]:
    if condition == "no_cps_baseline":
        return _no_cps_selection(task)
    if condition == "heuristic_selector_baseline":
        return _heuristic_selection(task)
    if condition == "cps_runtime_audit_scaffold":
        return _singleton_greedy_selection(task)
    if condition == "diagnostic_guided_escalation":
        return _diagnostic_guided_selection(task)
    raise ValueError(f"unknown Phase C condition: {condition}")


def _support_metrics(task: RealisticTask, selected_ids: Sequence[str]) -> dict[str, Any]:
    selected = set(selected_ids)
    support = set(task.support_ids)
    support_hits = sorted(selected & support)
    precision = len(support_hits) / len(selected_ids) if selected_ids else 0.0
    recall = len(support_hits) / len(support) if support else 0.0
    f1 = 0.0 if precision + recall == 0 else (2 * precision * recall) / (precision + recall)
    exact_match = int(support.issubset(selected))
    return {
        "metric_scope": "operational_utility_only",
        "exact_match": exact_match,
        "support_precision": round(precision, 6),
        "support_recall": round(recall, 6),
        "support_f1": round(f1, 6),
        "support_hit_ids": support_hits,
        "expected_support_ids": list(task.support_ids),
        "operational_score": round((0.5 * exact_match) + (0.5 * recall), 6),
    }


def _materialized_content(task: RealisticTask, selected_ids: Sequence[str]) -> str:
    lookup = task.item_lookup()
    lines = [f"Question: {task.question}"]
    for item_id in selected_ids:
        lines.append(f"[{item_id}] {lookup[item_id].text}")
    return "\n".join(lines)


def _pairwise_diagnostics(task: RealisticTask) -> dict[str, Any]:
    lookup = task.item_lookup()
    samples: list[dict[str, Any]] = []
    positive_interaction_mass = 0.0
    ratios: list[float] = []
    for left, right in combinations((item.item_id for item in task.candidates), 2):
        singleton_sum = lookup[left].singleton_value + lookup[right].singleton_value
        interaction = task.synergy_pairs.get(_pair(left, right), 0.0)
        pair_value = singleton_sum + interaction
        ratio = None
        if pair_value > 0:
            ratio = round(max(0.0, min(1.0, singleton_sum / pair_value)), 6)
            ratios.append(ratio)
        if interaction > 0:
            positive_interaction_mass += interaction
        samples.append(
            {
                "left_id": left,
                "right_id": right,
                "singleton_sum": round(singleton_sum, 6),
                "pair_value": round(pair_value, 6),
                "pairwise_interaction": round(interaction, 6),
                "block_ratio": ratio,
                "label": "synergy" if interaction > 0 else "additive_or_redundant",
            }
        )
    sample_count = len(samples)
    positive_count = sum(1 for sample in samples if sample["pairwise_interaction"] > 0)
    return {
        "pairwise_samples": samples,
        "block_ratio_lcb_b2": min(ratios) if ratios else None,
        "block_ratio_lcb_star": min(ratios) if ratios else None,
        "block_ratio_lcb_b3": None,
        "block_ratio_sample_count": sample_count,
        "block_ratio_uninformative_count": sample_count - len(ratios),
        "synergy_fraction": round(positive_count / sample_count, 6) if sample_count else 0.0,
        "positive_interaction_mass_ucb": round(positive_interaction_mass, 6),
    }


def _claim_gate_record(
    *,
    task: RealisticTask,
    condition: str,
    dispatch_id: str,
    metric_bridge_present: bool,
) -> dict[str, Any]:
    reason_codes = [
        "missing_human_labels",
        "missing_kappa",
        "operational_metric_only",
        "no_measurement_validation_evidence",
        "P04_deferred_operator_required",
        "P09_BLOCKED_OPERATOR_REQUIRED",
    ]
    if metric_bridge_present:
        reason_codes.append("no_vinfo_metric_bridge")
    else:
        reason_codes.append("missing_metric_bridge")
    return {
        "run_id": RUN_ID,
        "dispatch_id": dispatch_id,
        "task_id": task.task_id,
        "condition": condition,
        "metric_bridge_present": metric_bridge_present,
        "human_labels_present": False,
        "kappa_present": False,
        "human_human_kappa_established": False,
        "contamination_status": "not_run",
        "fresh_vinfo_metric_bridge_present": False,
        "allowed_claim_level": "operational_utility_only",
        "measurement_validated_allowed": False,
        "denied_claims": list(DENIED_CLAIMS),
        "reason_codes": reason_codes,
        "p04_status": "deferred_operator_required",
        "p09_status": "BLOCKED_OPERATOR_REQUIRED",
    }


def _dispatch_records(
    *,
    task: RealisticTask,
    condition: str,
    include_metric_bridge: bool,
) -> dict[str, dict[str, Any]]:
    selected_ids, trace = _selection_for_condition(task, condition)
    excluded_ids = _excluded_ids(task, selected_ids)
    selected_token_cost = _selected_token_cost(task, selected_ids)
    pool_hash = task.candidate_pool_hash()
    dispatch_id = f"{task.task_id}::{condition}"
    common = {
        "run_id": RUN_ID,
        "dispatch_id": dispatch_id,
        "agent_id": task.agent_id,
        "round_id": task.round_id,
        "regime": condition,
        "task_id": task.task_id,
        "task_family": task.task_family,
        "condition": condition,
        "protocol_version": PROTOCOL_VERSION,
    }
    task_metrics = _support_metrics(task, selected_ids)
    selection_summary = {
        "condition": condition,
        "algorithm": CONDITION_ALGORITHMS[condition],
        "selected_ids": selected_ids,
        "excluded_ids": excluded_ids,
        "selected_token_cost": selected_token_cost,
        "budget_tokens": task.budget_tokens,
        "budget_utilization": round(selected_token_cost / task.budget_tokens, 6),
        "candidate_pool_coverage": round(len(selected_ids) / len(task.candidates), 6),
        "support_overlap_count": len(task_metrics["support_hit_ids"]),
        "diversity_score": _diversity_score(task, selected_ids),
        "redundancy_rate": _redundancy_rate(task, selected_ids),
    }
    materialized_content = _materialized_content(task, selected_ids)
    pairwise = _pairwise_diagnostics(task)
    greedy_selected, _greedy_trace = _singleton_greedy_selection(task)
    augmented_selected, _augmented_trace = _diagnostic_guided_selection(task)
    greedy_value = task.value(greedy_selected)
    augmented_value = task.value(augmented_selected)
    greedy_augmented_gap = round(max(0.0, augmented_value - greedy_value), 6)
    selector_regime_label = _selector_regime_label(condition, greedy_augmented_gap)
    metric_bridge_assignment = "operational_utility_only"
    claim_gate_record = _claim_gate_record(
        task=task,
        condition=condition,
        dispatch_id=dispatch_id,
        metric_bridge_present=include_metric_bridge,
    )
    task_output = {
        "task_id": task.task_id,
        "condition": condition,
        "answer": task.expected_answer if task_metrics["exact_match"] else "insufficient_support",
        "expected_answer": task.expected_answer,
        "claim_level": metric_bridge_assignment,
        "score": task_metrics["operational_score"],
    }
    candidate_pool = {
        **common,
        "budget_tokens": task.budget_tokens,
        "question": task.question,
        "items": task.candidate_payloads(),
        "candidate_pool_hash": pool_hash,
        "candidate_count": len(task.candidates),
    }
    projection_plan = {
        **common,
        "algorithm": CONDITION_ALGORITHMS[condition],
        "budget_tokens": task.budget_tokens,
        "candidate_pool_hash": pool_hash,
        "selected_ids": selected_ids,
        "excluded_ids": excluded_ids,
        "trace": trace,
        "score_config": {
            "condition": condition,
            "value_source": "offline_task_support_fixture",
            "metric_bridge_assignment": metric_bridge_assignment,
            "live_api": "not_required",
        },
    }
    budget_witness = {
        **common,
        "budget_tokens": task.budget_tokens,
        "estimated_tokens": selected_token_cost,
        "realized_tokens": selected_token_cost,
        "within_budget": selected_token_cost <= task.budget_tokens,
        "selected_ids": selected_ids,
        "excluded_ids": excluded_ids,
        "tolerance_violations": [] if selected_token_cost <= task.budget_tokens else ["budget_overflow"],
    }
    materialized_context = {
        **common,
        "selected_ids": selected_ids,
        "section_order": selected_ids,
        "content": materialized_content,
        "token_count": selected_token_cost,
        "context_hash": context_hash(materialized_content),
    }
    metric_bridge_witness = {
        **common,
        "calibration_epoch": None,
        "active_stratum": {
            "task_family": task.task_family,
            "condition": condition,
        },
        "model_tier": None,
        "utility_metric": "task_support_operational_score",
        "metric_class": "operational_only",
        "materialization_policy": {
            "algorithm": CONDITION_ALGORITHMS[condition],
            "budget_tokens": task.budget_tokens,
            "selected_count": len(selected_ids),
            "excluded_count": len(excluded_ids),
        },
        "decoding_policy": {
            "mode": "offline_fixture_no_live_api",
            "temperature": None,
        },
        "bridge_scale": None,
        "bridge_residual_zeta": None,
        "effective_sample_size": None,
        "drift_status": "fresh",
        "diagnostic_mode": "phase_c_operational_task_metric",
        "diagnostic_claim_level": metric_bridge_assignment,
    }
    diagnostics = {
        **common,
        "block_ratio_lcb_b2": pairwise["block_ratio_lcb_b2"],
        "block_ratio_lcb_star": pairwise["block_ratio_lcb_star"],
        "block_ratio_lcb_star_semantics": "phase_c_pairwise_min_not_degree_adaptive_star",
        "block_ratio_lcb_b3": pairwise["block_ratio_lcb_b3"],
        "block_ratio_uninformative_count": pairwise["block_ratio_uninformative_count"],
        "block_ratio_sample_count": pairwise["block_ratio_sample_count"],
        "trace_decay_proxy": None,
        "gamma_hat": None,
        "gamma_hat_semantics": "not_reported_for_phase_c_operational_scaffold",
        "synergy_fraction": pairwise["synergy_fraction"],
        "positive_interaction_mass_ucb": pairwise["positive_interaction_mass_ucb"],
        "interaction_mass": pairwise["positive_interaction_mass_ucb"],
        "triple_excess_lcb_max": None,
        "triple_excess": None,
        "triple_excess_flag": "not_evaluated",
        "higher_order_ambiguity_flag": False,
        "greedy_augmented_gap": greedy_augmented_gap,
        "augmented_greedy_gap": greedy_augmented_gap,
        "metric_claim_level": metric_bridge_assignment,
        "selector_regime_label": selector_regime_label,
        "selector_action": CONDITION_ALGORITHMS[condition],
        "policy_recommendation": CONDITION_ALGORITHMS[condition],
        "greedy_value": greedy_value,
        "augmented_value": augmented_value,
        "local_search_value": augmented_value,
        "pairwise_samples": pairwise["pairwise_samples"],
        "block_ratio_samples": [
            sample for sample in pairwise["pairwise_samples"] if sample["block_ratio"] is not None
        ],
        "triple_samples": [],
        "thresholds": {
            "phase_c_escalation_gap_gt": 0.05,
        },
        "selected_ids": selected_ids,
        "excluded_ids": excluded_ids,
        "selected_token_cost": selected_token_cost,
        "budget_utilization": selection_summary["budget_utilization"],
        "task_metrics": task_metrics,
        "notes": "Phase C scaffold reports operational task utility only.",
    }
    dispatch = {
        **common,
        "question": task.question,
        "expected_answer": task.expected_answer,
        "budget_tokens": task.budget_tokens,
        "candidate_pool_hash": pool_hash,
        "context_hash": materialized_context["context_hash"],
        "metric_bridge_present": include_metric_bridge,
        "metric_bridge_assignment": metric_bridge_assignment,
        "selection_summary": selection_summary,
        "task_metrics": task_metrics,
        "task_output": task_output,
        "diagnostics": {
            "block_ratio_lcb_b2": diagnostics["block_ratio_lcb_b2"],
            "block_ratio_lcb_star": diagnostics["block_ratio_lcb_star"],
            "synergy_fraction": diagnostics["synergy_fraction"],
            "interaction_mass": diagnostics["interaction_mass"],
            "augmented_greedy_gap": diagnostics["augmented_greedy_gap"],
            "selector_regime_label": diagnostics["selector_regime_label"],
            "selector_action": diagnostics["selector_action"],
        },
        "claim_gate_record": claim_gate_record,
    }
    return {
        "candidate_pool": candidate_pool,
        "projection_plan": projection_plan,
        "budget_witness": budget_witness,
        "materialized_context": materialized_context,
        "metric_bridge_witness": metric_bridge_witness,
        "diagnostics": diagnostics,
        "dispatch": dispatch,
        "claim_gate": claim_gate_record,
        "task_metrics": {
            **common,
            **task_metrics,
        },
    }


def _selector_regime_label(condition: str, greedy_augmented_gap: float) -> str:
    if condition in {"no_cps_baseline", "heuristic_selector_baseline"}:
        return "baseline"
    if condition == "diagnostic_guided_escalation" and greedy_augmented_gap > 0:
        return "escalate"
    if greedy_augmented_gap > 0.05:
        return "escalate"
    return "greedy_valid"


def _diversity_score(task: RealisticTask, selected_ids: Sequence[str]) -> float:
    if not selected_ids:
        return 0.0
    lookup = task.item_lookup()
    tags = {tag for item_id in selected_ids for tag in lookup[item_id].tags}
    return round(len(tags) / len(selected_ids), 6)


def _redundancy_rate(task: RealisticTask, selected_ids: Sequence[str]) -> float:
    if len(selected_ids) < 2:
        return 0.0
    lookup = task.item_lookup()
    repeated_pairs = 0
    total_pairs = 0
    for left, right in combinations(selected_ids, 2):
        total_pairs += 1
        if set(lookup[left].tags) & set(lookup[right].tags):
            repeated_pairs += 1
    return round(repeated_pairs / total_pairs, 6) if total_pairs else 0.0


def _condition_results(dispatch_rows: list[dict[str, Any]], condition_order: Sequence[str]) -> dict[str, Any]:
    conditions: dict[str, Any] = {}
    for condition in condition_order:
        rows = [row for row in dispatch_rows if row["condition"] == condition]
        if not rows:
            continue
        conditions[condition] = {
            "condition": condition,
            "algorithm": CONDITION_ALGORITHMS[condition],
            "dispatch_count": len(rows),
            "mean_operational_score": _mean([row["task_metrics"]["operational_score"] for row in rows]),
            "exact_match_rate": _mean([row["task_metrics"]["exact_match"] for row in rows]),
            "mean_support_recall": _mean([row["task_metrics"]["support_recall"] for row in rows]),
            "mean_budget_utilization": _mean(
                [row["selection_summary"]["budget_utilization"] for row in rows]
            ),
            "metric_bridge_assignment": "operational_utility_only",
            "measurement_validated_allowed": False,
        }
    return {
        "run_id": RUN_ID,
        "conditions": conditions,
    }


def _mean(values: Sequence[float | int]) -> float:
    if not values:
        return 0.0
    return round(sum(float(value) for value in values) / len(values), 6)


def _replay_status(dispatch_rows: list[dict[str, Any]], *, metric_bridge_present: bool) -> dict[str, Any]:
    rows = [
        {
            "run_id": row["run_id"],
            "dispatch_id": row["dispatch_id"],
            "condition": row["condition"],
            "task_id": row["task_id"],
            "replay_status": "replayable_artifact_set" if metric_bridge_present else "replay_partial_missing_bridge",
            "candidate_pool_present": True,
            "projection_plan_present": True,
            "budget_witness_present": True,
            "materialized_context_present": True,
            "metric_bridge_witness_present": metric_bridge_present,
            "diagnostics_present": True,
            "phase_b_replay_compatible": metric_bridge_present,
            "metric_claim_level": "operational_utility_only",
        }
        for row in dispatch_rows
    ]
    return {
        "run_id": RUN_ID,
        "rows": rows,
        "status_counts": dict(Counter(row["replay_status"] for row in rows)),
    }


def _diagnostics_summary(dispatch_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_condition: dict[str, Any] = {}
    for condition in CONDITION_ORDER:
        rows = [row for row in dispatch_rows if row["condition"] == condition]
        if rows:
            by_condition[condition] = {
                "mean_block_ratio_lcb_b2": _mean(
                    [row["diagnostics"]["block_ratio_lcb_b2"] for row in rows]
                ),
                "mean_synergy_fraction": _mean([row["diagnostics"]["synergy_fraction"] for row in rows]),
                "mean_interaction_mass": _mean([row["diagnostics"]["interaction_mass"] for row in rows]),
                "mean_augmented_greedy_gap": _mean(
                    [row["diagnostics"]["augmented_greedy_gap"] for row in rows]
                ),
                "selector_actions": dict(Counter(row["diagnostics"]["selector_action"] for row in rows)),
                "selector_regime_labels": dict(
                    Counter(row["diagnostics"]["selector_regime_label"] for row in rows)
                ),
            }
    return {
        "run_id": RUN_ID,
        "metric_claim_level_counts": dict(
            Counter(row["metric_bridge_assignment"] for row in dispatch_rows)
        ),
        "diagnostic_field_names": [
            "block_ratio_lcb_b2",
            "block_ratio_lcb_star",
            "block_ratio_lcb_b3",
            "interaction_mass",
            "triple_excess",
            "augmented_greedy_gap",
            "selector_regime_label",
            "selector_action",
        ],
        "conditions": by_condition,
    }


def _task_metrics_payload(task_metric_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "metric_scope": "operational_utility_only",
        "rows": task_metric_rows,
        "summary": {
            "dispatch_count": len(task_metric_rows),
            "mean_operational_score": _mean([row["operational_score"] for row in task_metric_rows]),
            "exact_match_rate": _mean([row["exact_match"] for row in task_metric_rows]),
            "mean_support_f1": _mean([row["support_f1"] for row in task_metric_rows]),
        },
    }


def _claim_gate_report(claim_rows: list[dict[str, Any]], condition_order: Sequence[str]) -> dict[str, Any]:
    condition_claims = []
    for condition in condition_order:
        rows = [row for row in claim_rows if row["condition"] == condition]
        if rows:
            condition_claims.append(rows[0]["allowed_claim_level"])
    return {
        "run_id": RUN_ID,
        "metric_bridge_present": all(row["metric_bridge_present"] for row in claim_rows),
        "rows": claim_rows,
        "condition_claim_level_counts": dict(Counter(condition_claims)),
        "dispatch_claim_level_counts": dict(Counter(row["allowed_claim_level"] for row in claim_rows)),
        "denied_claims": list(DENIED_CLAIMS),
        "p04_status": "deferred_operator_required",
        "p09_status": "BLOCKED_OPERATOR_REQUIRED",
    }


def _format_report(
    *,
    condition_results: dict[str, Any],
    replay_status: dict[str, Any],
    diagnostics_summary: dict[str, Any],
    task_metrics: dict[str, Any],
    claim_gate_report: dict[str, Any],
) -> str:
    lines = [
        "# P43 Phase C Realistic-Task Context Projection Benchmark Report",
        "",
        "## Summary",
        "",
        f"- Run id: `{RUN_ID}`",
        f"- Dispatches: `{task_metrics['summary']['dispatch_count']}`",
        "- Live API: `skipped`",
        "- Maximum claim: `operational_utility_only`",
        "- Measurement validation is denied by the claim gate.",
        "",
        "## Conditions",
        "",
        "| Condition | Algorithm | Dispatches | Mean operational score | Exact match rate | Claim level |",
        "|---|---|---:|---:|---:|---|",
    ]
    for condition, payload in condition_results["conditions"].items():
        lines.append(
            "| "
            f"{condition} | "
            f"{payload['algorithm']} | "
            f"{payload['dispatch_count']} | "
            f"{payload['mean_operational_score']:.6f} | "
            f"{payload['exact_match_rate']:.6f} | "
            f"{payload['metric_bridge_assignment']} |"
        )
    lines.extend(
        [
            "",
            "## Replay Compatibility",
            "",
            f"- Replay status counts: `{json.dumps(replay_status['status_counts'], sort_keys=True)}`",
            "- CandidatePool, ProjectionPlan, BudgetWitness, MaterializedContext, MetricBridgeWitness, and diagnostics are written for the default run.",
            "",
            "## Diagnostics",
            "",
            f"- Diagnostic fields: `{', '.join(diagnostics_summary['diagnostic_field_names'])}`",
            f"- Metric claim levels: `{json.dumps(diagnostics_summary['metric_claim_level_counts'], sort_keys=True)}`",
            "",
            "## Claim Gate",
            "",
            f"- Dispatch claim level counts: `{json.dumps(claim_gate_report['dispatch_claim_level_counts'], sort_keys=True)}`",
            "- Human-label and kappa evidence are absent; P04 remains operator-required and P09 remains BLOCKED_OPERATOR_REQUIRED.",
            "- The scaffold records operational task utility only and does not certify deployed V-information behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def run_phase_c_benchmark(
    *,
    output_dir: str | Path,
    include_diagnostic_guided_escalation: bool = True,
    include_metric_bridge: bool = True,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    condition_order = (
        CONDITION_ORDER if include_diagnostic_guided_escalation else CONDITION_ORDER[:3]
    )
    records = [
        _dispatch_records(task=task, condition=condition, include_metric_bridge=include_metric_bridge)
        for task in _default_tasks()
        for condition in condition_order
    ]
    candidate_pools = [record["candidate_pool"] for record in records]
    projection_plans = [record["projection_plan"] for record in records]
    budget_witnesses = [record["budget_witness"] for record in records]
    materialized_contexts = [record["materialized_context"] for record in records]
    metric_bridge_witnesses = [
        record["metric_bridge_witness"] for record in records if include_metric_bridge
    ]
    diagnostics = [record["diagnostics"] for record in records]
    dispatch_rows = [record["dispatch"] for record in records]
    claim_rows = [record["claim_gate"] for record in records]
    task_metric_rows = [record["task_metrics"] for record in records]

    condition_results = _condition_results(dispatch_rows, condition_order)
    replay_status = _replay_status(dispatch_rows, metric_bridge_present=include_metric_bridge)
    diagnostics_summary = _diagnostics_summary(dispatch_rows)
    task_metrics = _task_metrics_payload(task_metric_rows)
    claim_gate_report = _claim_gate_report(claim_rows, condition_order)
    manifest = {
        "phase": "P43_DEV_REALISTIC_TASK_CONTEXT_PROJECTION_BENCHMARK",
        "result": "completed",
        "run_id": RUN_ID,
        "protocol_version": PROTOCOL_VERSION,
        "dispatch_count": len(dispatch_rows),
        "condition_order": list(condition_order),
        "live_api": "skipped",
        "live_api_required": False,
        "deterministic_outputs": True,
        "maximum_claim_level": "operational_utility_only",
        "measurement_validated_allowed": False,
        "output_files": list(OUTPUT_FILENAMES),
    }
    report_text = _format_report(
        condition_results=condition_results,
        replay_status=replay_status,
        diagnostics_summary=diagnostics_summary,
        task_metrics=task_metrics,
        claim_gate_report=claim_gate_report,
    )

    _write_jsonl(output_path / "candidate_pools.jsonl", candidate_pools)
    _write_jsonl(output_path / "projection_plans.jsonl", projection_plans)
    _write_jsonl(output_path / "budget_witnesses.jsonl", budget_witnesses)
    _write_jsonl(output_path / "materialized_contexts.jsonl", materialized_contexts)
    _write_jsonl(output_path / "metric_bridge_witnesses.jsonl", metric_bridge_witnesses)
    _write_jsonl(output_path / "diagnostics.jsonl", diagnostics)
    _write_json(output_path / "phase_c_manifest.json", manifest)
    _write_jsonl(output_path / "phase_c_dispatches.jsonl", dispatch_rows)
    _write_json(output_path / "phase_c_condition_results.json", condition_results)
    _write_json(output_path / "phase_c_replay_status.json", replay_status)
    _write_json(output_path / "phase_c_diagnostics_summary.json", diagnostics_summary)
    _write_json(output_path / "phase_c_task_metrics.json", task_metrics)
    _write_json(output_path / "phase_c_claim_gate_report.json", claim_gate_report)
    (output_path / "phase_c_report.md").write_text(report_text, encoding="utf-8")

    return {
        "status": "completed",
        "run_id": RUN_ID,
        "dispatch_count": len(dispatch_rows),
        "condition_order": list(condition_order),
        "output_dir": str(output_path),
        "manifest_path": str(output_path / "phase_c_manifest.json"),
        "report_path": str(output_path / "phase_c_report.md"),
        "live_api": "skipped",
        "metric_bridge_assignment": "operational_utility_only",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Phase C realistic-task benchmark scaffold.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--no-diagnostic-guided-escalation", action="store_true")
    parser.add_argument("--no-metric-bridge", action="store_true")
    args = parser.parse_args()

    result = run_phase_c_benchmark(
        output_dir=args.output_dir,
        include_diagnostic_guided_escalation=not args.no_diagnostic_guided_escalation,
        include_metric_bridge=not args.no_metric_bridge,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
