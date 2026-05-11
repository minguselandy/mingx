from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


RUN_ID = "reprojection-witness-pilot-v12"
PROTOCOL_VERSION = "reprojection_witness_pilot.v12"
SCHEMA_VERSION = "ReprojectionWitnessPilotV1"
DEFAULT_OUTPUT_DIR = "artifacts/experiments/reprojection_witness_pilot_v12"
DATA_SOURCE_KIND = "fixture"
AUDIT_SCOPE = "reprojection_witness_pilot"
EVIDENCE_SCOPE = "fixture_reprojection_witness_only"
NORMAL_METRIC_CLAIM_LEVEL = "operational_utility_only"
FAIL_CLOSED_METRIC_CLAIM_LEVEL = "ambiguous_metric"
SELECTOR_LABELS = ("greedy_supported", "pairwise_escalate", "higher_order_risk", "ambiguous")
TRIGGER_TYPES = (
    "ambiguous_selector_regime",
    "pairwise_escalation",
    "higher_order_risk",
    "budget_violation",
    "missing_critical_finding",
    "unsupported_finding",
    "provenance_defect",
    "candidate_pool_hash_mismatch",
    "identity_mismatch",
    "runtime_uncertainty",
    "operator_requested",
)
REPROJECTION_ACTIONS = (
    "add_missing_finding",
    "remove_unsupported_finding",
    "replace_overmerged_finding",
    "pin_critical_finding",
    "compress_redundant_context",
    "downgrade_to_ambiguous",
    "abstain_no_safe_reprojection",
)
REASON_CODE_ORDER = (
    "missing_identity_run_id",
    "missing_identity_dispatch_id",
    "missing_identity_agent_id",
    "missing_identity_round_id",
    "identity_mismatch_run_id",
    "identity_mismatch_dispatch_id",
    "identity_mismatch_agent_id",
    "identity_mismatch_round_id",
    "candidate_pool_hash_mismatch",
    "ambiguous_selector_regime",
    "pairwise_escalation",
    "higher_order_risk",
    "budget_violation",
    "missing_critical_finding",
    "unsupported_finding",
    "provenance_defect",
    "runtime_uncertainty",
    "operator_requested",
    "over_budget_non_comparable",
)
OUTPUT_FILENAMES = (
    "reprojection_cases.jsonl",
    "reprojection_witnesses.jsonl",
    "reprojection_actions.csv",
    "reprojection_trigger_counts.csv",
    "reprojection_claim_gate_report.json",
    "reprojection_summary.json",
    "reprojection_manifest.json",
    "reprojection_report.md",
)


@dataclass(frozen=True)
class ProjectionSnapshot:
    run_id: str
    dispatch_id: str
    agent_id: str
    round_id: str
    candidate_pool_hash: str
    selected_finding_ids: tuple[str, ...]
    materialized_content: str
    token_count: int
    budget_tokens: int
    selector_regime_label: str
    metric_claim_level: str

    def projection_plan_payload(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "budget_tokens": self.budget_tokens,
            "candidate_pool_hash": self.candidate_pool_hash,
            "dispatch_id": self.dispatch_id,
            "metric_claim_level": self.metric_claim_level,
            "round_id": self.round_id,
            "run_id": self.run_id,
            "selected_finding_ids": list(self.selected_finding_ids),
            "selector_regime_label": self.selector_regime_label,
        }

    def materialized_context_payload(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "candidate_pool_hash": self.candidate_pool_hash,
            "content": self.materialized_content,
            "dispatch_id": self.dispatch_id,
            "round_id": self.round_id,
            "run_id": self.run_id,
            "selected_finding_ids": list(self.selected_finding_ids),
            "token_count": self.token_count,
        }

    def projection_plan_hash(self) -> str:
        return _stable_hash(self.projection_plan_payload())

    def materialized_context_hash(self) -> str:
        return _stable_hash(self.materialized_context_payload())


@dataclass(frozen=True)
class ReprojectionCase:
    case_id: str
    case_family: str
    run_id: str
    dispatch_id: str
    agent_id: str
    round_id: str
    candidate_pool_hash: str
    initial_snapshot: ProjectionSnapshot
    reprojected_snapshot: ProjectionSnapshot
    trigger_type: str
    trigger_source: str
    trigger_reason_codes: tuple[str, ...]
    initial_selector_regime_label: str
    final_selector_regime_label: str
    reprojection_action: str
    added_finding_ids: tuple[str, ...]
    removed_finding_ids: tuple[str, ...]
    retained_finding_ids: tuple[str, ...]
    pinned_finding_ids: tuple[str, ...]
    compressed_finding_ids: tuple[str, ...]
    provenance_refs: tuple[str, ...]


@dataclass(frozen=True)
class ReprojectionWitness:
    witness_id: str
    case_id: str
    case_family: str
    run_id: str
    dispatch_id: str
    agent_id: str
    round_id: str
    candidate_pool_hash: str
    initial_projection_plan_hash: str
    initial_materialized_context_hash: str
    reprojected_projection_plan_hash: str
    reprojected_materialized_context_hash: str
    context_diff_hash: str
    trigger_type: str
    trigger_source: str
    trigger_reason_codes: tuple[str, ...]
    initial_selector_regime_label: str
    final_selector_regime_label: str
    metric_claim_level: str
    evidence_scope: str
    reprojection_action: str
    added_finding_ids: tuple[str, ...]
    removed_finding_ids: tuple[str, ...]
    retained_finding_ids: tuple[str, ...]
    pinned_finding_ids: tuple[str, ...]
    compressed_finding_ids: tuple[str, ...]
    initial_token_count: int
    reprojected_token_count: int
    budget_tokens: int
    budget_status: str
    budget_overrun_tokens: int
    budget_fair_comparable: bool
    provenance_refs: tuple[str, ...]
    replay_safe: bool
    data_source_kind: str
    paper_evidence_eligible: bool
    measurement_validation_claim: bool
    live_api_used: bool
    vinfo_proxy_supported: bool
    calibrated_proxy_supported: bool

    def to_row(self) -> dict[str, Any]:
        return {
            "added_finding_ids": list(self.added_finding_ids),
            "agent_id": self.agent_id,
            "budget_fair_comparable": self.budget_fair_comparable,
            "budget_overrun_tokens": self.budget_overrun_tokens,
            "budget_status": self.budget_status,
            "budget_tokens": self.budget_tokens,
            "calibrated_proxy_supported": self.calibrated_proxy_supported,
            "candidate_pool_hash": self.candidate_pool_hash,
            "case_family": self.case_family,
            "case_id": self.case_id,
            "compressed_finding_ids": list(self.compressed_finding_ids),
            "context_diff_hash": self.context_diff_hash,
            "data_source_kind": self.data_source_kind,
            "dispatch_id": self.dispatch_id,
            "evidence_scope": self.evidence_scope,
            "final_selector_regime_label": self.final_selector_regime_label,
            "initial_materialized_context_hash": self.initial_materialized_context_hash,
            "initial_projection_plan_hash": self.initial_projection_plan_hash,
            "initial_selector_regime_label": self.initial_selector_regime_label,
            "initial_token_count": self.initial_token_count,
            "live_api_used": self.live_api_used,
            "measurement_validation_claim": self.measurement_validation_claim,
            "metric_claim_level": self.metric_claim_level,
            "paper_evidence_eligible": self.paper_evidence_eligible,
            "pinned_finding_ids": list(self.pinned_finding_ids),
            "provenance_refs": list(self.provenance_refs),
            "removed_finding_ids": list(self.removed_finding_ids),
            "replay_safe": self.replay_safe,
            "reprojected_materialized_context_hash": self.reprojected_materialized_context_hash,
            "reprojected_projection_plan_hash": self.reprojected_projection_plan_hash,
            "reprojected_token_count": self.reprojected_token_count,
            "reprojection_action": self.reprojection_action,
            "retained_finding_ids": list(self.retained_finding_ids),
            "round_id": self.round_id,
            "run_id": self.run_id,
            "trigger_reason_codes": list(self.trigger_reason_codes),
            "trigger_source": self.trigger_source,
            "trigger_type": self.trigger_type,
            "vinfo_proxy_supported": self.vinfo_proxy_supported,
            "witness_id": self.witness_id,
        }


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _stable_jsonl(rows: Sequence[Mapping[str, Any]]) -> str:
    return "".join(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n" for row in rows)


def _stable_hash(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


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


def _ordered_reason_codes(reasons: Iterable[str]) -> tuple[str, ...]:
    order = {reason: index for index, reason in enumerate(REASON_CODE_ORDER)}
    return tuple(sorted(set(reasons), key=lambda reason: (order.get(reason, len(order)), reason)))


def _snapshot(
    *,
    run_id: str,
    dispatch_id: str,
    agent_id: str,
    round_id: str,
    candidate_pool_hash: str,
    selected: Sequence[str],
    token_count: int,
    budget_tokens: int = 40,
    selector_label: str = "greedy_supported",
    metric_claim_level: str = NORMAL_METRIC_CLAIM_LEVEL,
) -> ProjectionSnapshot:
    content = "\n".join(f"[{finding_id}] fixture content for {finding_id}" for finding_id in selected)
    return ProjectionSnapshot(
        run_id=run_id,
        dispatch_id=dispatch_id,
        agent_id=agent_id,
        round_id=round_id,
        candidate_pool_hash=candidate_pool_hash,
        selected_finding_ids=tuple(selected),
        materialized_content=content,
        token_count=token_count,
        budget_tokens=budget_tokens,
        selector_regime_label=selector_label,
        metric_claim_level=metric_claim_level,
    )


def _case(
    *,
    case_id: str,
    case_family: str,
    trigger_type: str,
    trigger_source: str,
    trigger_reason_codes: Sequence[str],
    reprojection_action: str,
    initial_selected: Sequence[str],
    reprojected_selected: Sequence[str],
    added: Sequence[str] = (),
    removed: Sequence[str] = (),
    retained: Sequence[str] = (),
    pinned: Sequence[str] = (),
    compressed: Sequence[str] = (),
    initial_selector_label: str = "greedy_supported",
    final_selector_label: str = "greedy_supported",
    initial_tokens: int = 24,
    reprojected_tokens: int = 28,
    budget_tokens: int = 40,
    candidate_pool_hash: str | None = None,
    reprojected_candidate_pool_hash: str | None = None,
    reprojected_run_id: str | None = None,
) -> ReprojectionCase:
    run_id = RUN_ID
    dispatch_id = f"dispatch-{case_id}"
    agent_id = "agent-fixture"
    round_id = "round-1"
    pool_hash = candidate_pool_hash or _stable_hash({"case_id": case_id, "candidate_ids": sorted(set(initial_selected) | set(reprojected_selected))})
    revised_pool_hash = reprojected_candidate_pool_hash or pool_hash
    initial_snapshot = _snapshot(
        run_id=run_id,
        dispatch_id=dispatch_id,
        agent_id=agent_id,
        round_id=round_id,
        candidate_pool_hash=pool_hash,
        selected=initial_selected,
        token_count=initial_tokens,
        budget_tokens=budget_tokens,
        selector_label=initial_selector_label,
    )
    reprojected_snapshot = _snapshot(
        run_id=reprojected_run_id or run_id,
        dispatch_id=dispatch_id,
        agent_id=agent_id,
        round_id=round_id,
        candidate_pool_hash=revised_pool_hash,
        selected=reprojected_selected,
        token_count=reprojected_tokens,
        budget_tokens=budget_tokens,
        selector_label=final_selector_label,
    )
    return ReprojectionCase(
        case_id=case_id,
        case_family=case_family,
        run_id=run_id,
        dispatch_id=dispatch_id,
        agent_id=agent_id,
        round_id=round_id,
        candidate_pool_hash=pool_hash,
        initial_snapshot=initial_snapshot,
        reprojected_snapshot=reprojected_snapshot,
        trigger_type=trigger_type,
        trigger_source=trigger_source,
        trigger_reason_codes=tuple(trigger_reason_codes),
        initial_selector_regime_label=initial_selector_label,
        final_selector_regime_label=final_selector_label,
        reprojection_action=reprojection_action,
        added_finding_ids=tuple(added),
        removed_finding_ids=tuple(removed),
        retained_finding_ids=tuple(retained),
        pinned_finding_ids=tuple(pinned),
        compressed_finding_ids=tuple(compressed),
        provenance_refs=(f"fixture:{case_family}:{case_id}",),
    )


def default_reprojection_cases() -> list[ReprojectionCase]:
    return sorted(
        [
            _case(
                case_id="p50-clean-001",
                case_family="clean_no_reprojection",
                trigger_type="operator_requested",
                trigger_source="fixture_no_reprojection_check",
                trigger_reason_codes=("operator_requested",),
                reprojection_action="abstain_no_safe_reprojection",
                initial_selected=("f1", "f2"),
                reprojected_selected=("f1", "f2"),
                retained=("f1", "f2"),
            ),
            _case(
                case_id="p50-ambiguous-001",
                case_family="ambiguous_selector",
                trigger_type="ambiguous_selector_regime",
                trigger_source="selector_regime_label",
                trigger_reason_codes=("ambiguous_selector_regime",),
                reprojection_action="downgrade_to_ambiguous",
                initial_selected=("f1", "f2"),
                reprojected_selected=("f1", "f2"),
                retained=("f1", "f2"),
                initial_selector_label="ambiguous",
                final_selector_label="ambiguous",
            ),
            _case(
                case_id="p50-pairwise-001",
                case_family="pairwise_escalation",
                trigger_type="pairwise_escalation",
                trigger_source="diagnostic_policy",
                trigger_reason_codes=("pairwise_escalation",),
                reprojection_action="add_missing_finding",
                initial_selected=("f1",),
                reprojected_selected=("f1", "f3"),
                added=("f3",),
                retained=("f1",),
                initial_selector_label="pairwise_escalate",
                final_selector_label="pairwise_escalate",
            ),
            _case(
                case_id="p50-missing-001",
                case_family="missing_critical_finding",
                trigger_type="missing_critical_finding",
                trigger_source="p49_extraction_audit_fixture",
                trigger_reason_codes=("missing_critical_finding",),
                reprojection_action="add_missing_finding",
                initial_selected=("f1", "f2"),
                reprojected_selected=("f1", "f2", "critical-f4"),
                added=("critical-f4",),
                retained=("f1", "f2"),
                pinned=("critical-f4",),
            ),
            _case(
                case_id="p50-unsupported-001",
                case_family="unsupported_finding",
                trigger_type="unsupported_finding",
                trigger_source="p49_extraction_audit_fixture",
                trigger_reason_codes=("unsupported_finding",),
                reprojection_action="remove_unsupported_finding",
                initial_selected=("f1", "unsupported-fx"),
                reprojected_selected=("f1",),
                removed=("unsupported-fx",),
                retained=("f1",),
            ),
            _case(
                case_id="p50-budget-001",
                case_family="budget_violation",
                trigger_type="budget_violation",
                trigger_source="budget_witness",
                trigger_reason_codes=("budget_violation",),
                reprojection_action="compress_redundant_context",
                initial_selected=("f1", "f2", "f3"),
                reprojected_selected=("f1", "f2", "f3-compressed"),
                retained=("f1", "f2"),
                compressed=("f3-compressed",),
                initial_tokens=38,
                reprojected_tokens=44,
                budget_tokens=40,
            ),
            _case(
                case_id="p50-pool-mismatch-001",
                case_family="candidate_pool_mismatch",
                trigger_type="candidate_pool_hash_mismatch",
                trigger_source="p48_replay_provenance_gate",
                trigger_reason_codes=("candidate_pool_hash_mismatch",),
                reprojection_action="abstain_no_safe_reprojection",
                initial_selected=("f1", "f2"),
                reprojected_selected=("f1", "f2", "f-new"),
                retained=("f1", "f2"),
                reprojected_candidate_pool_hash="mismatched-candidate-pool-hash",
            ),
            _case(
                case_id="p50-identity-mismatch-001",
                case_family="identity_mismatch",
                trigger_type="identity_mismatch",
                trigger_source="p48_dispatch_identity_gate",
                trigger_reason_codes=("identity_mismatch",),
                reprojection_action="abstain_no_safe_reprojection",
                initial_selected=("f1", "f2"),
                reprojected_selected=("f1", "f2"),
                retained=("f1", "f2"),
                reprojected_run_id="different-run",
            ),
        ],
        key=lambda case: (case.case_family, case.case_id),
    )


def _identity_reason_codes(case: ReprojectionCase) -> list[str]:
    reasons: list[str] = []
    for field in ("run_id", "dispatch_id", "agent_id", "round_id"):
        value = getattr(case, field)
        if not value:
            reasons.append(f"missing_identity_{field}")
    for field in ("run_id", "dispatch_id", "agent_id", "round_id"):
        expected = getattr(case, field)
        initial = getattr(case.initial_snapshot, field)
        reprojected = getattr(case.reprojected_snapshot, field)
        values = {value for value in (expected, initial, reprojected) if value}
        if len(values) > 1:
            reasons.append(f"identity_mismatch_{field}")
    return reasons


def _candidate_pool_mismatch(case: ReprojectionCase) -> bool:
    return len(
        {
            value
            for value in (
                case.candidate_pool_hash,
                case.initial_snapshot.candidate_pool_hash,
                case.reprojected_snapshot.candidate_pool_hash,
            )
            if value
        }
    ) > 1


def _context_diff_hash(case: ReprojectionCase) -> str:
    return _stable_hash(
        {
            "added_finding_ids": list(case.added_finding_ids),
            "compressed_finding_ids": list(case.compressed_finding_ids),
            "removed_finding_ids": list(case.removed_finding_ids),
            "retained_finding_ids": list(case.retained_finding_ids),
        }
    )


def build_reprojection_witness(case: ReprojectionCase) -> ReprojectionWitness:
    if case.trigger_type not in TRIGGER_TYPES:
        raise ValueError(f"unknown trigger_type: {case.trigger_type}")
    if case.reprojection_action not in REPROJECTION_ACTIONS:
        raise ValueError(f"unknown reprojection_action: {case.reprojection_action}")

    reasons = list(case.trigger_reason_codes)
    reasons.extend(_identity_reason_codes(case))
    if _candidate_pool_mismatch(case):
        reasons.append("candidate_pool_hash_mismatch")

    overrun = max(0, case.reprojected_snapshot.token_count - case.reprojected_snapshot.budget_tokens)
    if overrun:
        reasons.append("over_budget_non_comparable")

    ordered_reasons = _ordered_reason_codes(reasons)
    identity_or_pool_defect = any(reason.startswith("missing_identity_") or reason.startswith("identity_mismatch_") for reason in ordered_reasons)
    identity_or_pool_defect = identity_or_pool_defect or "candidate_pool_hash_mismatch" in ordered_reasons
    budget_status = "within_budget"
    if identity_or_pool_defect:
        budget_status = "not_applicable_fail_closed"
    elif overrun:
        budget_status = "over_budget_non_comparable"

    replay_safe = not identity_or_pool_defect and overrun == 0
    metric_claim_level = NORMAL_METRIC_CLAIM_LEVEL if replay_safe else FAIL_CLOSED_METRIC_CLAIM_LEVEL
    context_diff_hash = _context_diff_hash(case)
    witness_id = _stable_hash(
        {
            "case_id": case.case_id,
            "context_diff_hash": context_diff_hash,
            "initial_projection_plan_hash": case.initial_snapshot.projection_plan_hash(),
            "ordered_reasons": list(ordered_reasons),
            "reprojected_projection_plan_hash": case.reprojected_snapshot.projection_plan_hash(),
            "reprojection_action": case.reprojection_action,
        }
    )
    return ReprojectionWitness(
        witness_id=witness_id,
        case_id=case.case_id,
        case_family=case.case_family,
        run_id=case.run_id,
        dispatch_id=case.dispatch_id,
        agent_id=case.agent_id,
        round_id=case.round_id,
        candidate_pool_hash=case.candidate_pool_hash,
        initial_projection_plan_hash=case.initial_snapshot.projection_plan_hash(),
        initial_materialized_context_hash=case.initial_snapshot.materialized_context_hash(),
        reprojected_projection_plan_hash=case.reprojected_snapshot.projection_plan_hash(),
        reprojected_materialized_context_hash=case.reprojected_snapshot.materialized_context_hash(),
        context_diff_hash=context_diff_hash,
        trigger_type=case.trigger_type,
        trigger_source=case.trigger_source,
        trigger_reason_codes=ordered_reasons,
        initial_selector_regime_label=case.initial_selector_regime_label if case.initial_selector_regime_label in SELECTOR_LABELS else "ambiguous",
        final_selector_regime_label=case.final_selector_regime_label if case.final_selector_regime_label in SELECTOR_LABELS else "ambiguous",
        metric_claim_level=metric_claim_level,
        evidence_scope=EVIDENCE_SCOPE,
        reprojection_action=case.reprojection_action,
        added_finding_ids=tuple(case.added_finding_ids),
        removed_finding_ids=tuple(case.removed_finding_ids),
        retained_finding_ids=tuple(case.retained_finding_ids),
        pinned_finding_ids=tuple(case.pinned_finding_ids),
        compressed_finding_ids=tuple(case.compressed_finding_ids),
        initial_token_count=case.initial_snapshot.token_count,
        reprojected_token_count=case.reprojected_snapshot.token_count,
        budget_tokens=case.reprojected_snapshot.budget_tokens,
        budget_status=budget_status,
        budget_overrun_tokens=overrun,
        budget_fair_comparable=budget_status == "within_budget",
        provenance_refs=tuple(case.provenance_refs),
        replay_safe=replay_safe,
        data_source_kind=DATA_SOURCE_KIND,
        paper_evidence_eligible=False,
        measurement_validation_claim=False,
        live_api_used=False,
        vinfo_proxy_supported=False,
        calibrated_proxy_supported=False,
    )


def _case_row(case: ReprojectionCase, witness: ReprojectionWitness) -> dict[str, Any]:
    return {
        "agent_id": case.agent_id,
        "budget_tokens": case.reprojected_snapshot.budget_tokens,
        "candidate_pool_hash": case.candidate_pool_hash,
        "case_family": case.case_family,
        "case_id": case.case_id,
        "data_source_kind": DATA_SOURCE_KIND,
        "dispatch_id": case.dispatch_id,
        "final_selector_regime_label": witness.final_selector_regime_label,
        "initial_selector_regime_label": witness.initial_selector_regime_label,
        "live_api_used": False,
        "measurement_validation_claim": False,
        "paper_evidence_eligible": False,
        "reprojection_action": case.reprojection_action,
        "round_id": case.round_id,
        "run_id": case.run_id,
        "trigger_reason_codes": list(witness.trigger_reason_codes),
        "trigger_source": case.trigger_source,
        "trigger_type": case.trigger_type,
        "witness_id": witness.witness_id,
    }


def _action_rows(witnesses: Sequence[ReprojectionWitness]) -> list[dict[str, Any]]:
    rows = [
        {
            "added_finding_ids": "|".join(witness.added_finding_ids),
            "budget_status": witness.budget_status,
            "case_family": witness.case_family,
            "case_id": witness.case_id,
            "compressed_finding_ids": "|".join(witness.compressed_finding_ids),
            "removed_finding_ids": "|".join(witness.removed_finding_ids),
            "replay_safe": str(witness.replay_safe).lower(),
            "reprojection_action": witness.reprojection_action,
            "trigger_type": witness.trigger_type,
            "witness_id": witness.witness_id,
        }
        for witness in witnesses
    ]
    return sorted(rows, key=lambda row: (row["case_id"], row["reprojection_action"]))


def _trigger_count_rows(witnesses: Sequence[ReprojectionWitness]) -> list[dict[str, Any]]:
    counts = Counter(witness.trigger_type for witness in witnesses)
    return [{"trigger_type": trigger, "count": counts[trigger]} for trigger in sorted(counts)]


def _claim_gate_report(witnesses: Sequence[ReprojectionWitness]) -> dict[str, Any]:
    return {
        "audit_scope": AUDIT_SCOPE,
        "calibrated_proxy_supported": False,
        "data_source_kind": DATA_SOURCE_KIND,
        "evidence_scope": EVIDENCE_SCOPE,
        "fixture_only_reprojection_witness": True,
        "human_kappa_present": False,
        "human_labels_present": False,
        "live_api_used": False,
        "measurement_validation_claim": False,
        "p47_claim_upgraded": False,
        "p48_claim_upgraded": False,
        "p49_claim_upgraded": False,
        "paper_evidence_eligible": False,
        "prior_phase_claims_upgraded": False,
        "schema_version": SCHEMA_VERSION,
        "selector_regime_claim_upgraded": False,
        "vinfo_proxy_supported": False,
        "witness_count": len(witnesses),
    }


def _summary_payload(witnesses: Sequence[ReprojectionWitness]) -> dict[str, Any]:
    trigger_counts = Counter(witness.trigger_type for witness in witnesses)
    action_counts = Counter(witness.reprojection_action for witness in witnesses)
    budget_counts = Counter(witness.budget_status for witness in witnesses)
    metric_counts = Counter(witness.metric_claim_level for witness in witnesses)
    return {
        "audit_scope": AUDIT_SCOPE,
        "budget_status_counts": dict(sorted(budget_counts.items())),
        "case_count": len(witnesses),
        "data_source_kind": DATA_SOURCE_KIND,
        "evidence_scope": EVIDENCE_SCOPE,
        "live_api_used": False,
        "measurement_validation_claim": False,
        "metric_claim_level_counts": dict(sorted(metric_counts.items())),
        "paper_evidence_eligible": False,
        "protocol_version": PROTOCOL_VERSION,
        "replay_safe_witnesses": sum(1 for witness in witnesses if witness.replay_safe),
        "reprojection_action_counts": dict(sorted(action_counts.items())),
        "run_id": RUN_ID,
        "schema_version": SCHEMA_VERSION,
        "trigger_type_counts": dict(sorted(trigger_counts.items())),
        "witness_count": len(witnesses),
    }


def _manifest_payload() -> dict[str, Any]:
    return {
        "audit_scope": AUDIT_SCOPE,
        "data_source_kind": DATA_SOURCE_KIND,
        "evidence_scope": EVIDENCE_SCOPE,
        "live_api_used": False,
        "measurement_validation_claim": False,
        "output_dir": DEFAULT_OUTPUT_DIR,
        "output_files": list(OUTPUT_FILENAMES),
        "paper_evidence_eligible": False,
        "protocol_version": PROTOCOL_VERSION,
        "run_id": RUN_ID,
        "schema_version": SCHEMA_VERSION,
    }


def _format_report(summary: Mapping[str, Any], claim_gate: Mapping[str, Any]) -> str:
    lines = [
        "# P50 ReprojectionWitness Pilot Report",
        "",
        "P50 records optional fixture re-projection decisions. It is an audit scaffold, not a new selector algorithm and not metric bridge evidence.",
        "",
        "## Claim Boundary",
        "",
        "- Data source kind: fixture",
        "- Evidence scope: fixture_reprojection_witness_only",
        "- Paper evidence eligible: false",
        "- Measurement validation claim: false",
        "- Live API used: false",
        "- Prior P47/P48/P49 claims are not upgraded.",
        "",
        "## Summary",
        "",
        f"- Witnesses: {summary['witness_count']}",
        f"- Replay-safe witnesses: {summary['replay_safe_witnesses']}",
        f"- Trigger counts: `{json.dumps(summary['trigger_type_counts'], sort_keys=True)}`",
        f"- Action counts: `{json.dumps(summary['reprojection_action_counts'], sort_keys=True)}`",
        f"- Budget status counts: `{json.dumps(summary['budget_status_counts'], sort_keys=True)}`",
        "",
        "## Claim Gate",
        "",
        f"- Calibrated proxy support: {str(claim_gate['calibrated_proxy_supported']).lower()}",
        f"- V-information proxy support: {str(claim_gate['vinfo_proxy_supported']).lower()}",
        f"- Selector-regime claim upgraded: {str(claim_gate['selector_regime_claim_upgraded']).lower()}",
        "",
    ]
    return "\n".join(lines)


def _load_config(config_path: str | Path | None) -> dict[str, Any]:
    if config_path is None:
        return {}
    return json.loads(Path(config_path).read_text(encoding="utf-8"))


def run_reprojection_witness_pilot(
    *,
    config_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    config = _load_config(config_path)
    if str(config.get("data_source_kind", DATA_SOURCE_KIND)) != DATA_SOURCE_KIND:
        raise ValueError("P50 fixture pilot only supports data_source_kind=fixture")
    if bool(config.get("live_api_used", False)):
        raise ValueError("P50 fixture pilot must not use live API")

    output_path = Path(output_dir or config.get("output_dir") or DEFAULT_OUTPUT_DIR)
    cases = default_reprojection_cases()
    witnesses = [build_reprojection_witness(case) for case in cases]
    witness_rows = [witness.to_row() for witness in witnesses]
    case_rows = [_case_row(case, witness) for case, witness in zip(cases, witnesses, strict=True)]
    action_rows = _action_rows(witnesses)
    trigger_rows = _trigger_count_rows(witnesses)
    claim_gate = _claim_gate_report(witnesses)
    summary = _summary_payload(witnesses)
    manifest = _manifest_payload()
    report = _format_report(summary, claim_gate)

    _write_jsonl(output_path / "reprojection_cases.jsonl", case_rows)
    _write_jsonl(output_path / "reprojection_witnesses.jsonl", witness_rows)
    _write_csv(
        output_path / "reprojection_actions.csv",
        fieldnames=[
            "case_id",
            "case_family",
            "witness_id",
            "trigger_type",
            "reprojection_action",
            "added_finding_ids",
            "removed_finding_ids",
            "compressed_finding_ids",
            "budget_status",
            "replay_safe",
        ],
        rows=action_rows,
    )
    _write_csv(
        output_path / "reprojection_trigger_counts.csv",
        fieldnames=["trigger_type", "count"],
        rows=trigger_rows,
    )
    _write_json(output_path / "reprojection_claim_gate_report.json", claim_gate)
    _write_json(output_path / "reprojection_summary.json", summary)
    _write_json(output_path / "reprojection_manifest.json", manifest)
    (output_path / "reprojection_report.md").write_text(report, encoding="utf-8")

    return {
        "artifacts": {name: str(output_path / name) for name in OUTPUT_FILENAMES},
        "case_count": len(cases),
        "data_source_kind": DATA_SOURCE_KIND,
        "output_dir": str(output_path),
        "status": "completed",
        "witness_count": len(witnesses),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic P50 ReprojectionWitness fixture pilot.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    result = run_reprojection_witness_pilot(config_path=args.config, output_dir=args.output_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
