from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from cps.evaluation.sufficiency_regime import (
    ALLOWED_SUFFICIENCY_TRIGGERS,
    CLAIM_LEVEL,
    CLAIM_STATUS,
    DENIED_CLAIMS,
    PILOT_READY_STATUS,
    _reject_raw_or_live_payload,
)
from cps.experiments.artifacts import stable_hash
from cps.schema.projection_bundle_v1 import ClaimLedger


CONTROLLED_REPLAY_HOLD_FIXED_FIELDS = {
    "downstream_prompt_template_hash",
    "model_snapshot",
    "endpoint",
    "thinking_mode",
    "decoding_policy",
    "token_budget_accounting_method",
}
ALLOWED_REPROJECTION_INTERVENTIONS = {
    "restore_excluded_evidence_span",
    "expand_budget_with_budget_delta_recorded",
    "switch_selector_to_pair_aware_local_search",
    "switch_selector_to_seeded_augmented_greedy",
}
REPAIR_STATUSES = {
    "reprojection_candidate",
    "repair_candidate",
    "no_reprojection_needed",
    "not_comparable_control_mismatch",
    "not_comparable_budget_violation",
    "ambiguous_suppressed",
}


def _as_int(value: Any) -> int:
    return int(value or 0)


def _sorted_dict(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): value[key] for key in sorted(value)}


@dataclass(frozen=True)
class ReprojectionWitness:
    witness_id: str
    item_id: str
    trigger_label: str
    intervention_type: str
    downstream_prompt_template_hash: str
    model_snapshot: str
    endpoint: str
    thinking_mode: str
    decoding_policy: dict[str, Any]
    token_budget_accounting_method: str
    original_budget_tokens: int
    reprojected_budget_tokens: int
    budget_delta: int
    selector_before: str
    selector_after: str
    selector_change: dict[str, str]
    context_hash_before: str
    context_hash_after: str
    context_diff_hash: str
    before_output_hash: str
    after_output_hash: str
    repair_status: str
    position_aware_replay_manifest: dict[str, Any]
    comparable_replay: bool
    claim_level: str = CLAIM_LEVEL
    claim_status: str = CLAIM_STATUS
    candidate_operational_evidence_only: bool = True
    measurement_validation_claim: bool = False
    truth_validation_claim: bool = False
    calibrated_abstention_claim: bool = False
    raw_response_stored: bool = False
    live_api_call_performed: bool = False
    route_5_locked: bool = True
    route_8_locked: bool = True

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ReprojectionWitness:
        _reject_raw_or_live_payload(payload)
        data = dict(payload)
        trigger_label = str(data.get("trigger_label", "")).strip()
        if trigger_label not in ALLOWED_SUFFICIENCY_TRIGGERS:
            raise ValueError(f"trigger_label is not supported: {trigger_label}")
        intervention_type = str(data.get("intervention_type", "")).strip()
        if intervention_type not in ALLOWED_REPROJECTION_INTERVENTIONS:
            raise ValueError(f"intervention_type is not supported: {intervention_type}")
        repair_status = str(data.get("repair_status", "reprojection_candidate")).strip()
        if repair_status not in REPAIR_STATUSES:
            raise ValueError(f"repair_status is not supported: {repair_status}")

        original_budget_tokens = _as_int(data.get("original_budget_tokens"))
        reprojected_budget_tokens = _as_int(data.get("reprojected_budget_tokens"))
        selector_before = str(data.get("selector_before", ""))
        selector_after = str(data.get("selector_after", ""))
        position_manifest = dict(
            data.get(
                "position_aware_replay_manifest",
                {
                    "enabled": True,
                    "original_position_ids": [],
                    "reprojected_position_ids": [],
                    "position_policy_hash": "",
                },
            )
        )
        comparable_replay = not repair_status.startswith("not_comparable")

        return cls(
            witness_id=str(data.get("witness_id", "")),
            item_id=str(data.get("item_id", "")),
            trigger_label=trigger_label,
            intervention_type=intervention_type,
            downstream_prompt_template_hash=str(data.get("downstream_prompt_template_hash", "")),
            model_snapshot=str(data.get("model_snapshot", "")),
            endpoint=str(data.get("endpoint", "")),
            thinking_mode=str(data.get("thinking_mode", "")),
            decoding_policy=_sorted_dict(dict(data.get("decoding_policy", {}))),
            token_budget_accounting_method=str(
                data.get("token_budget_accounting_method", "")
            ),
            original_budget_tokens=original_budget_tokens,
            reprojected_budget_tokens=reprojected_budget_tokens,
            budget_delta=reprojected_budget_tokens - original_budget_tokens,
            selector_before=selector_before,
            selector_after=selector_after,
            selector_change={"before": selector_before, "after": selector_after},
            context_hash_before=str(data.get("context_hash_before", "")),
            context_hash_after=str(data.get("context_hash_after", "")),
            context_diff_hash=str(data.get("context_diff_hash", "")),
            before_output_hash=str(data.get("before_output_hash", "")),
            after_output_hash=str(data.get("after_output_hash", "")),
            repair_status=repair_status,
            position_aware_replay_manifest=position_manifest,
            comparable_replay=comparable_replay,
        )

    def claim_ledger(self) -> ClaimLedger:
        return ClaimLedger.from_dict(
            {
                "claim_candidate": "sufficiency_abstention_reprojection_framework",
                "metric_claim_level": "operational_utility_only",
                "bridge_status": "not_applicable",
                "judge_status": "weak_model_adjudicated_candidate_only",
                "artifact_status": "framework_only",
                "raw_response_stored": False,
                "human_external_gold_label": False,
                "current_claim_level": CLAIM_STATUS,
                "allowed_claims": [CLAIM_LEVEL],
                "denied_claims": list(DENIED_CLAIMS),
                "claim_upgrade": False,
                "route_5_locked": True,
                "route_8_locked": True,
            },
            artifact_status="complete",
        )

    def to_dict(self, *, include_claim_ledger: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        payload["controlled_replay"] = {
            "hold_fixed": sorted(CONTROLLED_REPLAY_HOLD_FIXED_FIELDS),
            "downstream_prompt_template_hash": self.downstream_prompt_template_hash,
            "model_snapshot": self.model_snapshot,
            "endpoint": self.endpoint,
            "thinking_mode": self.thinking_mode,
            "decoding_policy": dict(self.decoding_policy),
            "token_budget_accounting_method": self.token_budget_accounting_method,
        }
        if include_claim_ledger:
            payload["claim_ledger"] = self.claim_ledger().to_dict()
        return payload


def build_reprojection_manifest(
    *,
    run_id: str,
    items: Iterable[Mapping[str, Any]],
    downstream_prompt_template_hash: str,
    model_snapshot: str,
    endpoint: str,
    thinking_mode: str,
    decoding_policy: Mapping[str, Any],
) -> dict[str, Any]:
    normalized_items = sorted(
        [
            {
                "item_id": str(item["item_id"]),
                "trigger_label": str(item["trigger_label"]),
            }
            for item in items
        ],
        key=lambda row: row["item_id"],
    )
    manifest = {
        "run_id": str(run_id),
        "protocol_version": "v1_operational_only",
        "items": normalized_items,
        "controlled_replay": {
            "hold_fixed": sorted(CONTROLLED_REPLAY_HOLD_FIXED_FIELDS),
            "downstream_prompt_template_hash": str(downstream_prompt_template_hash),
            "model_snapshot": str(model_snapshot),
            "endpoint": str(endpoint),
            "thinking_mode": str(thinking_mode),
            "decoding_policy": _sorted_dict(dict(decoding_policy)),
            "token_budget_accounting_method": "offline_token_estimate_v1",
        },
        "allowed_interventions": sorted(ALLOWED_REPROJECTION_INTERVENTIONS),
        "position_aware_replay": {
            "enabled": True,
            "manifest_required_when_present": True,
        },
        "claim_level": CLAIM_LEVEL,
        "claim_status": CLAIM_STATUS,
        "pilot_readiness_status": PILOT_READY_STATUS,
        "candidate_operational_evidence_only": True,
        "raw_response_stored": False,
        "live_api_call_performed": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "denied_claims": list(DENIED_CLAIMS),
    }
    manifest["manifest_hash"] = stable_hash(manifest)
    return manifest
