from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


RUN_ID = "realistic-task-model-adjudicated-v12"
PROTOCOL_VERSION = "realistic_task_model_adjudicated.v12"
SCHEMA_VERSION = "RealisticTaskModelAdjudicatedBenchmarkV1"
DEFAULT_OUTPUT_DIR = "artifacts/experiments/realistic_task_model_adjudicated_v12"
TASK_FAMILIES = (
    "multi_hop_evidence_assembly",
    "paper_revision_microtask",
    "repo_change_review_microtask",
)
BASELINES = (
    "minimal_context",
    "full_context",
    "top_k_retrieval",
    "mmr_density_greedy",
    "always_sag",
    "v12_cost_aware_diagnostic_policy",
)
BUDGET_COMPARABLE_BASELINES = (
    "minimal_context",
    "top_k_retrieval",
    "mmr_density_greedy",
    "always_sag",
    "v12_cost_aware_diagnostic_policy",
)
NON_BUDGET_REFERENCE_BASELINES = ("full_context",)
SELECTOR_LABELS = {"greedy_supported", "pairwise_escalate", "higher_order_risk", "ambiguous"}
ALLOWED_CLAIM_LEVELS = (
    "model_adjudicated_proxy_evidence",
    "operational_utility_only",
    "ambiguous_metric",
)
OUTPUT_FILENAMES = (
    "realistic_task_packets.jsonl",
    "model_adjudicated_labels.jsonl",
    "label_stability_report.json",
    "realistic_selector_comparison.csv",
    "realistic_claim_gate_report.json",
    "realistic_task_report.md",
)


@dataclass(frozen=True)
class Finding:
    finding_id: str
    text: str
    token_cost: int
    singleton_value: float
    relevance_band: str
    evidence_type: str
    provenance_strength: str
    extraction_complexity: str
    confidence: float
    is_prerequisite: bool = False
    heuristic_score: float = 0.0

    def to_packet_payload(self) -> dict[str, Any]:
        return {
            "evidence_type": self.evidence_type,
            "finding_id": self.finding_id,
            "heuristic_score": self.heuristic_score,
            "provenance_strength": self.provenance_strength,
            "text": self.text,
            "token_cost": self.token_cost,
        }

    def to_item_label(self) -> dict[str, Any]:
        return {
            "confidence": self.confidence,
            "evidence_type": self.evidence_type,
            "extraction_complexity": self.extraction_complexity,
            "finding_id": self.finding_id,
            "is_prerequisite": self.is_prerequisite,
            "provenance_strength": self.provenance_strength,
            "relevance_band": self.relevance_band,
            "singleton_value": self.singleton_value,
        }


@dataclass(frozen=True)
class TaskPacket:
    task_id: str
    task_family: str
    agent_role: str
    task_prompt: str
    gold_sketch: str
    gold_requirements: tuple[str, ...]
    findings: tuple[Finding, ...]
    expected_critical_findings: tuple[str, ...]
    budget_tokens: int
    selector_regime_label: str
    stability_status: str
    pair_labels: tuple[dict[str, Any], ...]
    triple_labels: tuple[dict[str, Any], ...]

    def finding_lookup(self) -> dict[str, Finding]:
        return {finding.finding_id: finding for finding in self.findings}

    def to_packet_row(self, *, data_source_kind: str) -> dict[str, Any]:
        return {
            "agent_role": self.agent_role,
            "budget_tokens": self.budget_tokens,
            "candidate_findings": [finding.to_packet_payload() for finding in self.findings],
            "expected_critical_findings": list(self.expected_critical_findings),
            "gold_requirements": list(self.gold_requirements),
            "gold_sketch": self.gold_sketch,
            "provenance": {
                "data_source_kind": data_source_kind,
                "label_source": "fixture_model_adjudicated_schema",
                "live_api_used": False,
                "paper_evidence_eligible": False,
                "protocol_version": PROTOCOL_VERSION,
            },
            "task_family": self.task_family,
            "task_id": self.task_id,
            "task_prompt": self.task_prompt,
            "token_costs": {finding.finding_id: finding.token_cost for finding in self.findings},
        }

    def to_label_row(self, *, data_source_kind: str) -> dict[str, Any]:
        selector_label = self.selector_regime_label if self.stability_status == "stable" else "ambiguous"
        return {
            "data_source_kind": data_source_kind,
            "item_labels": [finding.to_item_label() for finding in self.findings],
            "measurement_validation_claim": False,
            "pair_labels": [dict(row) for row in self.pair_labels],
            "paper_evidence_eligible": False,
            "pipeline_roles": {
                "adjudicator": "fixture_adjudicator_no_live_api",
                "generator": "fixture_generator_no_live_api",
                "structural_labeler": "fixture_structural_labeler_no_live_api",
                "verifier": "fixture_verifier_no_live_api",
            },
            "quality_controls": {
                "duplicate_judging_stability": "fixture_not_measured",
                "order_reversal_status": "fixture_not_measured",
                "paraphrase_robustness_status": "fixture_not_measured",
                "prerequisite_ablation_status": "fixture_not_measured",
                "stability_status": self.stability_status,
            },
            "subset_labels": [
                {
                    "expected_escalation_benefit": _expected_escalation_benefit(selector_label),
                    "missing_critical_findings": [],
                    "redundant_findings": _redundant_findings(self),
                    "selector_regime_label": selector_label,
                    "sufficiency_score": 1.0,
                    "unsupported_claim_risk": 0.0,
                }
            ],
            "task_family": self.task_family,
            "task_id": self.task_id,
            "triple_labels": [dict(row) for row in self.triple_labels],
        }


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _stable_jsonl(rows: Sequence[Mapping[str, Any]]) -> str:
    return "".join(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n" for row in rows)


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_stable_json(payload), encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_stable_jsonl(rows), encoding="utf-8")
    return path


def _write_csv(path: Path, *, fieldnames: list[str], rows: Sequence[Mapping[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    return path


def _load_config(config_path: str | Path | None) -> dict[str, Any]:
    if config_path is None:
        return {}
    return json.loads(Path(config_path).read_text(encoding="utf-8"))


def _pair(left: str, right: str, *, relation: str, band: str, direction: str = "none", confidence: float = 0.9) -> dict[str, Any]:
    return {
        "confidence": confidence,
        "left_finding_id": left,
        "pairwise_excess_band": band,
        "prerequisite_direction": direction,
        "relation": relation,
        "right_finding_id": right,
    }


def _triple(
    finding_ids: Sequence[str],
    *,
    higher_order_type: str,
    pairs_sufficient: bool,
    triple_excess_band: str,
    greedy_failure_risk: str,
    confidence: float = 0.88,
) -> dict[str, Any]:
    return {
        "confidence": confidence,
        "finding_ids": list(finding_ids),
        "greedy_failure_risk": greedy_failure_risk,
        "higher_order_type": higher_order_type,
        "pairs_sufficient": pairs_sufficient,
        "triple_excess_band": triple_excess_band,
    }


def _default_tasks() -> list[TaskPacket]:
    return sorted(
        [
            TaskPacket(
                task_id="paper_revision_claim_boundary",
                task_family="paper_revision_microtask",
                agent_role="paper_revision_editor",
                task_prompt=(
                    "Revise a paragraph so it says P45 did not establish a bridge, "
                    "while preserving the synthetic-only P46 claim boundary."
                ),
                gold_sketch="Mention P45 closure, no bridge support, and P46 synthetic-only scope.",
                gold_requirements=(
                    "state P45 current stratum is non-calibrated",
                    "avoid measurement-validation wording",
                    "state P46 is synthetic structural evidence only",
                ),
                budget_tokens=38,
                expected_critical_findings=(
                    "paper_p45_non_calibrated",
                    "paper_no_measurement_validation",
                    "paper_p46_synthetic_scope",
                ),
                selector_regime_label="greedy_supported",
                stability_status="stable",
                findings=(
                    Finding(
                        "paper_p45_non_calibrated",
                        "P45 closed the current bio_attribute stratum as implemented but non-calibrated.",
                        11,
                        0.34,
                        "high",
                        "claim_boundary",
                        "high",
                        "medium",
                        0.93,
                        is_prerequisite=True,
                        heuristic_score=0.89,
                    ),
                    Finding(
                        "paper_no_measurement_validation",
                        "The lane must not claim measurement validation, human labels, or kappa.",
                        10,
                        0.33,
                        "high",
                        "denied_claim",
                        "high",
                        "low",
                        0.94,
                        is_prerequisite=True,
                        heuristic_score=0.88,
                    ),
                    Finding(
                        "paper_p46_synthetic_scope",
                        "P46 artifacts are deterministic synthetic structural diagnostics with ambiguous metric scope.",
                        11,
                        0.33,
                        "high",
                        "scope_boundary",
                        "high",
                        "medium",
                        0.92,
                        is_prerequisite=True,
                        heuristic_score=0.87,
                    ),
                    Finding(
                        "paper_legacy_v10_note",
                        "Older v10 wording used broader certification language and should be treated as archive text.",
                        9,
                        0.08,
                        "low",
                        "background",
                        "medium",
                        "low",
                        0.78,
                        heuristic_score=0.30,
                    ),
                    Finding(
                        "paper_extra_related_work",
                        "Related work can be mentioned after the claim boundary paragraph is correct.",
                        8,
                        0.07,
                        "low",
                        "background",
                        "medium",
                        "low",
                        0.76,
                        heuristic_score=0.28,
                    ),
                ),
                pair_labels=(
                    _pair("paper_p45_non_calibrated", "paper_no_measurement_validation", relation="complementary", band="medium"),
                    _pair("paper_legacy_v10_note", "paper_extra_related_work", relation="redundant", band="none"),
                ),
                triple_labels=(
                    _triple(
                        ("paper_p45_non_calibrated", "paper_no_measurement_validation", "paper_p46_synthetic_scope"),
                        higher_order_type="claim_boundary_bundle",
                        pairs_sufficient=True,
                        triple_excess_band="low",
                        greedy_failure_risk="low",
                    ),
                ),
            ),
            TaskPacket(
                task_id="multi_hop_bridge_city",
                task_family="multi_hop_evidence_assembly",
                agent_role="evidence_assembly_agent",
                task_prompt=(
                    "Assemble the minimum evidence needed to answer a two-hop attribution question "
                    "without relying on lexical overlap alone."
                ),
                gold_sketch="The answer follows only from combining the fellowship host with its city.",
                gold_requirements=(
                    "include the bridge entity finding",
                    "include the answer-location finding",
                    "exclude lexical-overlap decoys where possible",
                ),
                budget_tokens=32,
                expected_critical_findings=("multi_hop_bridge_entity", "multi_hop_answer_location"),
                selector_regime_label="pairwise_escalate",
                stability_status="stable",
                findings=(
                    Finding(
                        "multi_hop_bridge_entity",
                        "The Ada Lovelace fellowship is hosted by Northbridge University.",
                        13,
                        0.42,
                        "high",
                        "bridge_fact",
                        "high",
                        "medium",
                        0.91,
                        is_prerequisite=True,
                        heuristic_score=0.74,
                    ),
                    Finding(
                        "multi_hop_answer_location",
                        "Northbridge University is located in Riverton.",
                        12,
                        0.42,
                        "high",
                        "answer_fact",
                        "high",
                        "medium",
                        0.91,
                        is_prerequisite=True,
                        heuristic_score=0.72,
                    ),
                    Finding(
                        "multi_hop_lexical_decoy",
                        "A Riverton exhibit mentions Ada Lovelace in a museum program.",
                        12,
                        0.10,
                        "medium",
                        "lexical_decoy",
                        "medium",
                        "low",
                        0.80,
                        heuristic_score=0.90,
                    ),
                    Finding(
                        "multi_hop_background",
                        "Northbridge alumni publish short research notes.",
                        9,
                        0.07,
                        "low",
                        "background",
                        "medium",
                        "low",
                        0.77,
                        heuristic_score=0.32,
                    ),
                    Finding(
                        "multi_hop_irrelevant_date",
                        "The museum program was updated during a spring event.",
                        8,
                        0.03,
                        "low",
                        "background",
                        "low",
                        "low",
                        0.70,
                        heuristic_score=0.20,
                    ),
                ),
                pair_labels=(
                    _pair(
                        "multi_hop_bridge_entity",
                        "multi_hop_answer_location",
                        relation="complementary",
                        band="high",
                        direction="bridge_entity_to_answer_location",
                    ),
                    _pair("multi_hop_lexical_decoy", "multi_hop_background", relation="independent", band="none"),
                ),
                triple_labels=(
                    _triple(
                        ("multi_hop_bridge_entity", "multi_hop_answer_location", "multi_hop_lexical_decoy"),
                        higher_order_type="pair_sufficient_with_decoy",
                        pairs_sufficient=True,
                        triple_excess_band="none",
                        greedy_failure_risk="medium",
                    ),
                ),
            ),
            TaskPacket(
                task_id="repo_change_review_claim_boundary",
                task_family="repo_change_review_microtask",
                agent_role="repo_change_reviewer",
                task_prompt=(
                    "Review a proposed repo change for claim-boundary regressions and missing focused tests."
                ),
                gold_sketch="The review should preserve the claim boundary and identify the missing regression test.",
                gold_requirements=(
                    "inspect changed artifact names",
                    "check claim-boundary wording",
                    "ask for the focused guardrail test",
                ),
                budget_tokens=34,
                expected_critical_findings=("repo_changed_artifact", "repo_claim_boundary", "repo_missing_guardrail_test"),
                selector_regime_label="higher_order_risk",
                stability_status="unstable",
                findings=(
                    Finding(
                        "repo_changed_artifact",
                        "The patch renames a paper-facing artifact and updates downstream references.",
                        10,
                        0.28,
                        "high",
                        "changed_file",
                        "high",
                        "medium",
                        0.88,
                        is_prerequisite=True,
                        heuristic_score=0.76,
                    ),
                    Finding(
                        "repo_claim_boundary",
                        "The report must not upgrade synthetic or model-adjudicated evidence into validation claims.",
                        12,
                        0.34,
                        "high",
                        "claim_boundary",
                        "high",
                        "high",
                        0.90,
                        is_prerequisite=True,
                        heuristic_score=0.70,
                    ),
                    Finding(
                        "repo_missing_guardrail_test",
                        "No focused regression test checks that forbidden claim labels stay absent.",
                        12,
                        0.32,
                        "high",
                        "test_gap",
                        "high",
                        "medium",
                        0.89,
                        is_prerequisite=True,
                        heuristic_score=0.68,
                    ),
                    Finding(
                        "repo_format_noise",
                        "The diff also includes line-ending churn in nearby files.",
                        8,
                        0.05,
                        "low",
                        "noise",
                        "low",
                        "low",
                        0.73,
                        heuristic_score=0.42,
                    ),
                    Finding(
                        "repo_unrelated_doc",
                        "An unrelated doc paragraph was wrapped without semantic changes.",
                        8,
                        0.04,
                        "low",
                        "noise",
                        "low",
                        "low",
                        0.72,
                        heuristic_score=0.38,
                    ),
                ),
                pair_labels=(
                    _pair("repo_claim_boundary", "repo_missing_guardrail_test", relation="complementary", band="medium"),
                    _pair("repo_format_noise", "repo_unrelated_doc", relation="redundant", band="none"),
                ),
                triple_labels=(
                    _triple(
                        ("repo_changed_artifact", "repo_claim_boundary", "repo_missing_guardrail_test"),
                        higher_order_type="review_prerequisite_bundle",
                        pairs_sufficient=False,
                        triple_excess_band="medium",
                        greedy_failure_risk="high",
                    ),
                ),
            ),
        ],
        key=lambda task: (task.task_family, task.task_id),
    )


def _expected_escalation_benefit(selector_label: str) -> float:
    if selector_label == "pairwise_escalate":
        return 0.35
    if selector_label == "higher_order_risk":
        return 0.45
    if selector_label == "ambiguous":
        return 0.0
    return 0.05


def _redundant_findings(task: TaskPacket) -> list[str]:
    redundant: set[str] = set()
    for row in task.pair_labels:
        if row.get("relation") == "redundant":
            redundant.add(str(row["left_finding_id"]))
            redundant.add(str(row["right_finding_id"]))
    return sorted(redundant)


def _token_cost(task: TaskPacket, selected_ids: Iterable[str]) -> int:
    lookup = task.finding_lookup()
    return sum(lookup[finding_id].token_cost for finding_id in selected_ids)


def _pack_until_budget(task: TaskPacket, finding_ids: Sequence[str]) -> list[str]:
    selected: list[str] = []
    for finding_id in finding_ids:
        if _token_cost(task, [*selected, finding_id]) <= task.budget_tokens:
            selected.append(finding_id)
    return selected


def _rank_by_singleton(task: TaskPacket) -> list[str]:
    return [
        finding.finding_id
        for finding in sorted(
            task.findings,
            key=lambda finding: (-finding.singleton_value, finding.token_cost, finding.finding_id),
        )
    ]


def _rank_by_heuristic(task: TaskPacket) -> list[str]:
    return [
        finding.finding_id
        for finding in sorted(
            task.findings,
            key=lambda finding: (-finding.heuristic_score, finding.token_cost, finding.finding_id),
        )
    ]


def _mmr_density_selection(task: TaskPacket) -> list[str]:
    selected: list[str] = []
    seen_evidence_types: set[str] = set()
    for finding in sorted(
        task.findings,
        key=lambda row: (-(row.singleton_value / row.token_cost), row.evidence_type, row.finding_id),
    ):
        if finding.evidence_type in seen_evidence_types and finding.finding_id not in task.expected_critical_findings:
            continue
        if _token_cost(task, [*selected, finding.finding_id]) <= task.budget_tokens:
            selected.append(finding.finding_id)
            seen_evidence_types.add(finding.evidence_type)
    for finding_id in _rank_by_singleton(task):
        if finding_id not in selected and _token_cost(task, [*selected, finding_id]) <= task.budget_tokens:
            selected.append(finding_id)
    return selected


def _always_sag_selection(task: TaskPacket) -> list[str]:
    selected: list[str] = []
    for row in task.pair_labels:
        if row.get("relation") == "complementary":
            for finding_id in (str(row["left_finding_id"]), str(row["right_finding_id"])):
                if finding_id not in selected and _token_cost(task, [*selected, finding_id]) <= task.budget_tokens:
                    selected.append(finding_id)
    for row in task.triple_labels:
        if str(row.get("triple_excess_band", "none")) != "none":
            for finding_id in row["finding_ids"]:
                if finding_id not in selected and _token_cost(task, [*selected, finding_id]) <= task.budget_tokens:
                    selected.append(finding_id)
    for finding_id in _rank_by_singleton(task):
        if finding_id not in selected and _token_cost(task, [*selected, finding_id]) <= task.budget_tokens:
            selected.append(finding_id)
    return selected


def _v12_policy_selection(task: TaskPacket) -> tuple[list[str], str, str]:
    if task.stability_status != "stable":
        return _mmr_density_selection(task), "ambiguous", "ambiguous_downgrade"
    if task.selector_regime_label == "pairwise_escalate":
        return _always_sag_selection(task), "pairwise_escalate", "pairwise_escalate"
    if task.selector_regime_label == "higher_order_risk":
        return _always_sag_selection(task), "higher_order_risk", "higher_order_risk"
    return _mmr_density_selection(task), "greedy_supported", "monitored_greedy"


def _selection_for_baseline(task: TaskPacket, baseline: str) -> tuple[list[str], str, str]:
    if baseline == "minimal_context":
        return [], "ambiguous", "minimal_context"
    if baseline == "full_context":
        return [finding.finding_id for finding in task.findings], task.selector_regime_label, "full_context"
    if baseline == "top_k_retrieval":
        return _pack_until_budget(task, _rank_by_heuristic(task)), task.selector_regime_label, "top_k_retrieval"
    if baseline == "mmr_density_greedy":
        return _mmr_density_selection(task), task.selector_regime_label, "mmr_density_greedy"
    if baseline == "always_sag":
        return _always_sag_selection(task), task.selector_regime_label, "always_sag"
    if baseline == "v12_cost_aware_diagnostic_policy":
        return _v12_policy_selection(task)
    raise ValueError(f"unknown realistic-task baseline: {baseline}")


def _bounded(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 6)


def _comparison_row(task: TaskPacket, baseline: str, *, data_source_kind: str) -> dict[str, Any]:
    selected_ids, selector_label, policy_outcome = _selection_for_baseline(task, baseline)
    raw_structural_regime_label = (
        task.selector_regime_label if task.selector_regime_label in SELECTOR_LABELS else "ambiguous"
    )
    final_selector_regime_label = selector_label if selector_label in SELECTOR_LABELS else "ambiguous"
    selected_token_count = _token_cost(task, selected_ids)
    budget_overrun_tokens = max(0, selected_token_count - task.budget_tokens)
    budget_comparable = baseline in BUDGET_COMPARABLE_BASELINES
    if budget_comparable and budget_overrun_tokens > 0:
        raise ValueError(
            f"budget-comparable baseline exceeded budget: "
            f"{task.task_id}:{baseline} selected={selected_token_count} budget={task.budget_tokens}"
        )
    budget_status = "within_budget" if budget_comparable else "over_budget_reference"
    critical = set(task.expected_critical_findings)
    selected = set(selected_ids)
    missing = sorted(critical - selected)
    redundant = sorted(set(_redundant_findings(task)) & selected)
    critical_count = len(critical)
    selected_count = len(selected_ids)
    sufficiency = len(critical & selected) / critical_count if critical_count else 0.0
    missing_rate = len(missing) / critical_count if critical_count else 0.0
    redundancy_rate = len(redundant) / selected_count if selected_count else 0.0
    unsupported_risk = _bounded((0.75 * missing_rate) + (0.25 * redundancy_rate))
    metric_claim_level = (
        "ambiguous_metric"
        if selector_label == "ambiguous" and baseline == "v12_cost_aware_diagnostic_policy"
        else "operational_utility_only"
    )
    return {
        "ambiguity_rate": 1.0 if selector_label == "ambiguous" else 0.0,
        "baseline": baseline,
        "budget_comparable": "true" if budget_comparable else "false",
        "budget_overrun_tokens": budget_overrun_tokens,
        "budget_status": budget_status,
        "budget_tokens": task.budget_tokens,
        "cost_aware_policy_outcome": policy_outcome,
        "data_source_kind": data_source_kind,
        "diagnostic_escalation_rate": 1.0 if policy_outcome in {"pairwise_escalate", "higher_order_risk", "always_sag"} else 0.0,
        "expected_escalation_benefit": _expected_escalation_benefit(selector_label),
        "final_selector_regime_label": final_selector_regime_label,
        "metric_claim_level": metric_claim_level,
        "missing_critical_finding_rate": round(missing_rate, 6),
        "missing_critical_findings": ";".join(missing),
        "raw_structural_regime_label": raw_structural_regime_label,
        "redundancy_waste_rate": round(redundancy_rate, 6),
        "redundant_findings": ";".join(redundant),
        "selected_findings": ";".join(selected_ids),
        "selected_token_count": selected_token_count,
        "selected_tokens": selected_token_count,
        "selector_regime_label": final_selector_regime_label,
        "sufficiency_score": round(sufficiency, 6),
        "task_family": task.task_family,
        "task_id": task.task_id,
        "unsupported_claim_risk": unsupported_risk,
    }


def _stability_report(*, tasks: Sequence[TaskPacket], data_source_kind: str) -> dict[str, Any]:
    downgraded = sorted(task.task_id for task in tasks if task.stability_status != "stable")
    return {
        "data_source_kind": data_source_kind,
        "duplicate_judging_stability": {
            "status": "fixture_not_measured",
            "stable": None,
        },
        "label_stability_schema_version": "P47LabelStabilityReportV1",
        "order_reversal_status": {
            "status": "fixture_not_measured",
            "stable": None,
        },
        "paper_evidence_eligible": False,
        "paraphrase_robustness_status": {
            "status": "fixture_not_measured",
            "stable": None,
        },
        "prerequisite_ablation_status": {
            "status": "fixture_not_measured",
            "stable": None,
        },
        "task_count": len(tasks),
        "unstable_label_downgrade": {
            "downgraded_task_ids": downgraded,
            "selector_regime_label": "ambiguous",
            "unstable_label_count": len(downgraded),
        },
    }


def _claim_gate_report(*, rows: Sequence[Mapping[str, Any]], tasks: Sequence[TaskPacket], data_source_kind: str) -> dict[str, Any]:
    labels = Counter(str(row["selector_regime_label"]) for row in rows if row["baseline"] == "v12_cost_aware_diagnostic_policy")
    outcomes = Counter(str(row["cost_aware_policy_outcome"]) for row in rows if row["baseline"] == "v12_cost_aware_diagnostic_policy")
    budget_status_counts = Counter(str(row["budget_status"]) for row in rows)
    return {
        "allowed_claim_level": "operational_utility_only",
        "allowed_claim_levels": list(ALLOWED_CLAIM_LEVELS),
        "budget_comparable_baselines": list(BUDGET_COMPARABLE_BASELINES),
        "budget_comparable_row_count": sum(1 for row in rows if row["budget_comparable"] == "true"),
        "budget_fair_aggregate_excludes": list(NON_BUDGET_REFERENCE_BASELINES),
        "budget_fair_comparison_available": True,
        "budget_status_counts": dict(sorted(budget_status_counts.items())),
        "calibrated_bridge_evidence_used": False,
        "claim_gate_schema_version": "P47RealisticTaskClaimGateV1",
        "data_source_kind": data_source_kind,
        "deployed_v_information_verification_claim": False,
        "human_kappa_present": False,
        "human_labels_present": False,
        "human_validation_claim": False,
        "live_api_used": False,
        "measurement_validation_claim": False,
        "metric_claim_level": "operational_utility_only",
        "model_adjudicated_label_rows": len(tasks),
        "non_budget_reference_baselines": list(NON_BUDGET_REFERENCE_BASELINES),
        "non_budget_reference_row_count": sum(1 for row in rows if row["budget_comparable"] == "false"),
        "paper_evidence_eligible": False,
        "p45_bridge_evidence_reused": False,
        "reason_codes": [
            "fixture_labels_not_paper_evidence",
            "model_adjudicated_labels_not_human_labels",
            "human_labels_missing",
            "human_kappa_missing",
            "bridge_not_established_for_current_stratum",
            "live_api_not_used",
        ],
        "run_id": RUN_ID,
        "selector_regime_label_distribution": dict(sorted(labels.items())),
        "v12_cost_aware_policy_outcome_distribution": dict(sorted(outcomes.items())),
    }


def _summary(rows: Sequence[Mapping[str, Any]], tasks: Sequence[TaskPacket], *, data_source_kind: str) -> dict[str, Any]:
    policy_rows = [row for row in rows if row["baseline"] == "v12_cost_aware_diagnostic_policy"]
    budget_fair_rows = [row for row in rows if row["budget_comparable"] == "true"]
    return {
        "ambiguity_rate": _mean([float(row["ambiguity_rate"]) for row in policy_rows]),
        "baseline_count": len(BASELINES),
        "budget_comparable_baseline_count": len(BUDGET_COMPARABLE_BASELINES),
        "budget_fair_comparison_row_count": len(budget_fair_rows),
        "data_source_kind": data_source_kind,
        "diagnostic_escalation_rate": _mean([float(row["diagnostic_escalation_rate"]) for row in policy_rows]),
        "mean_missing_critical_finding_rate": _mean([float(row["missing_critical_finding_rate"]) for row in policy_rows]),
        "mean_redundancy_waste_rate": _mean([float(row["redundancy_waste_rate"]) for row in policy_rows]),
        "mean_selected_tokens": _mean([float(row["selected_token_count"]) for row in policy_rows]),
        "mean_sufficiency_score": _mean([float(row["sufficiency_score"]) for row in policy_rows]),
        "mean_unsupported_claim_risk": _mean([float(row["unsupported_claim_risk"]) for row in policy_rows]),
        "non_budget_reference_baseline_count": len(NON_BUDGET_REFERENCE_BASELINES),
        "task_count": len(tasks),
    }


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 6)


def _format_report(*, claim_gate: Mapping[str, Any], summary: Mapping[str, Any], stability: Mapping[str, Any]) -> str:
    lines = [
        "# P47 Model-Adjudicated Realistic-Task Benchmark Report",
        "",
        "## Summary",
        "",
        f"- Run id: `{RUN_ID}`",
        f"- Task count: {summary['task_count']}",
        f"- Data source kind: `{summary['data_source_kind']}`",
        "- Live API: `skipped`",
        f"- Allowed claim level: `{claim_gate['allowed_claim_level']}`",
        f"- Paper evidence eligible: {str(bool(claim_gate['paper_evidence_eligible'])).lower()}",
        "",
        "## Budget Comparability",
        "",
        "### Budget-Fair Baselines",
        "",
        "These baselines are included in budget-fair selector-policy comparisons:",
        "",
        *[f"- `{baseline}`" for baseline in claim_gate["budget_comparable_baselines"]],
        "",
        "### Non-Budget Reference Baselines",
        "",
        "- `full_context`: an always-large-context reference baseline, not part of budget-fair selector-policy comparison.",
        "",
        "Budget-fair aggregate conclusions exclude `full_context`.",
        "",
        "## Metrics",
        "",
        "The metrics below summarize the v12 cost-aware policy rows, which are budget-comparable.",
        "",
        f"- Mean sufficiency score: {summary['mean_sufficiency_score']}",
        f"- Mean missing-critical-finding rate: {summary['mean_missing_critical_finding_rate']}",
        f"- Mean redundancy-waste rate: {summary['mean_redundancy_waste_rate']}",
        f"- Mean unsupported-claim risk: {summary['mean_unsupported_claim_risk']}",
        f"- Mean selected tokens: {summary['mean_selected_tokens']}",
        f"- Diagnostic/escalation rate: {summary['diagnostic_escalation_rate']}",
        f"- Ambiguity rate: {summary['ambiguity_rate']}",
        "",
        "## Quality Controls",
        "",
        f"- Duplicate judging stability: `{stability['duplicate_judging_stability']['status']}`",
        f"- Order reversal status: `{stability['order_reversal_status']['status']}`",
        f"- Paraphrase robustness status: `{stability['paraphrase_robustness_status']['status']}`",
        f"- Prerequisite ablation status: `{stability['prerequisite_ablation_status']['status']}`",
        f"- Unstable-label downgrades: `{json.dumps(stability['unstable_label_downgrade'], sort_keys=True)}`",
        "",
        "## Claim Boundary",
        "",
        "- Fixture labels are not paper evidence.",
        "- Model-adjudicated labels are not human labels.",
        "- Human agreement is absent.",
        "- No bridge-calibrated evidence is used.",
        "- No deployment-level verification claim is made.",
        "",
    ]
    return "\n".join(lines)


def run_realistic_task_benchmark(
    *,
    config_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    config = _load_config(config_path)
    data_source_kind = str(config.get("data_source_kind", "fixture"))
    resolved_output_dir = Path(output_dir or config.get("output_dir", DEFAULT_OUTPUT_DIR))
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    tasks = _default_tasks()
    packet_rows = [task.to_packet_row(data_source_kind=data_source_kind) for task in tasks]
    label_rows = [task.to_label_row(data_source_kind=data_source_kind) for task in tasks]
    comparison_rows = [
        _comparison_row(task, baseline, data_source_kind=data_source_kind)
        for task in tasks
        for baseline in BASELINES
    ]
    stability = _stability_report(tasks=tasks, data_source_kind=data_source_kind)
    claim_gate = _claim_gate_report(rows=comparison_rows, tasks=tasks, data_source_kind=data_source_kind)
    summary = _summary(comparison_rows, tasks, data_source_kind=data_source_kind)

    _write_jsonl(resolved_output_dir / "realistic_task_packets.jsonl", packet_rows)
    _write_jsonl(resolved_output_dir / "model_adjudicated_labels.jsonl", label_rows)
    _write_json(resolved_output_dir / "label_stability_report.json", stability)
    _write_csv(
        resolved_output_dir / "realistic_selector_comparison.csv",
        fieldnames=[
            "task_id",
            "task_family",
            "baseline",
            "selector_regime_label",
            "raw_structural_regime_label",
            "final_selector_regime_label",
            "metric_claim_level",
            "sufficiency_score",
            "missing_critical_finding_rate",
            "redundancy_waste_rate",
            "unsupported_claim_risk",
            "budget_comparable",
            "budget_status",
            "budget_tokens",
            "selected_token_count",
            "budget_overrun_tokens",
            "selected_tokens",
            "diagnostic_escalation_rate",
            "ambiguity_rate",
            "cost_aware_policy_outcome",
            "expected_escalation_benefit",
            "selected_findings",
            "missing_critical_findings",
            "redundant_findings",
            "data_source_kind",
        ],
        rows=comparison_rows,
    )
    _write_json(resolved_output_dir / "realistic_claim_gate_report.json", claim_gate)
    (resolved_output_dir / "realistic_task_report.md").write_text(
        _format_report(claim_gate=claim_gate, summary=summary, stability=stability),
        encoding="utf-8",
    )

    return {
        "status": "completed",
        "run_id": RUN_ID,
        "schema_version": SCHEMA_VERSION,
        "task_count": len(tasks),
        "baseline_count": len(BASELINES),
        "data_source_kind": data_source_kind,
        "output_dir": str(resolved_output_dir),
        "required_files": list(OUTPUT_FILENAMES),
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the P47 realistic-task model-adjudicated benchmark.")
    parser.add_argument("--config", default="configs/runs/realistic-task-model-adjudicated-v12.json")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    result = run_realistic_task_benchmark(config_path=args.config, output_dir=args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
