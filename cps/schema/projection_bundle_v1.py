from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, ClassVar, Mapping

from cps.experiments.artifacts import stable_hash, stable_json_dumps, to_payload


REQUIRED_IDENTITY_FIELDS = ("run_id", "dispatch_id", "agent_id", "round_id")
REQUIRED_ARTIFACT_FIELDS = (
    "candidate_pool",
    "projection_plan",
    "budget_witness",
    "materialized_context",
    "metric_bridge_witness",
)
CORE_CONTRACT_REQUIRED_FIELDS = {
    "projection_plan": (
        "dispatch_id",
        "query_id",
        "conversation_turn_id",
        "candidate_ids_considered",
        "selected_evidence_ids",
        "excluded_evidence_ids",
        "selector_name",
        "selector_config_hash",
        "score_manifest_hash",
    ),
    "budget_witness": (
        "requested_budget_tokens",
        "realized_budget_tokens",
        "token_count_method",
        "section_level_token_counts",
        "trim_events",
        "overflow_policy",
    ),
    "materialized_context": (
        "materialized_context_hash",
        "materialization_order",
        "section_boundaries",
        "prompt_template_hash",
        "downstream_prompt_hash",
        "evidence_hashes",
    ),
    "metric_bridge_witness": (
        "metric_class",
        "active_stratum",
        "model_snapshot",
        "endpoint",
        "thinking_mode",
        "decoding_policy",
        "bridge_status",
        "diagnostic_claim_level",
        "drift_status",
        "generated_token_logprobs_used_as_answer_side_diagnostic_only",
        "fixed_target_nll_supported",
    ),
}
OPTIONAL_WITNESS_REQUIRED_FIELDS = {
    "counterfactual_replay_witness": (
        "frozen_state_hash",
        "intervention_type",
        "item_added_or_removed",
        "evaluator_manifest_hash",
        "replicate_count",
        "replay_status",
    ),
    "reprojection_witness": (
        "trigger_label",
        "budget_delta",
        "selector_change",
        "context_diff_hash",
        "before_output_hash",
        "after_output_hash",
        "repair_status",
    ),
    "judge_run_manifest": (
        "judge_model_snapshot",
        "judge_prompt_hash",
        "rubric_version",
        "order_swap_enabled",
        "rubric_paraphrase_id",
        "raw_response_stored",
        "parsed_label",
        "parse_status",
    ),
}
RAW_RESPONSE_BODY_FIELDS = {
    "raw_api_response",
    "raw_api_response_body",
    "raw_api_response_payload",
    "raw_body",
    "raw_response",
    "raw_response_body",
    "raw_response_payload",
}
RAW_RESPONSE_FLAG_FIELDS = {
    "raw_api_responses_stored",
    "raw_response_stored",
    "store_raw_api_response",
}
DEFAULT_DENIED_CLAIMS = (
    "fixed_target_nll_support",
    "teacher_forced_scoring_support",
    "fixed_target_continuation_scoring_support",
    "prompt_logprobs_support",
    "metric_bridge_support",
    "calibrated_proxy_supported",
    "vinfo_proxy_supported",
    "measurement_validation",
    "human_external_gold_validation",
    "paper_grade_validation",
    "paper_grade_evidence",
    "selector_superiority",
    "global_selector_superiority",
    "deployed_v_information_verification",
    "route_5_unlock",
    "route_8_unlock",
)
INCOMPLETE_BUNDLE_DENIED_CLAIMS = tuple(
    dict.fromkeys(
        (
            *(claim for claim in DEFAULT_DENIED_CLAIMS if claim != "vinfo_proxy_supported"),
            "v_information_proxy_support",
            "no_aggregated_headline_claim",
        )
    )
)
UPGRADE_CLAIMS = {
    "calibrated_proxy_supported",
    "deployed_v_information_verification",
    "global_selector_superiority",
    "human_external_gold_validation",
    "measurement_validation",
    "metric_bridge_support",
    "paper_grade_evidence",
    "paper_grade_validation",
    "route_5_unlock",
    "route_8_unlock",
    "selector_superiority",
    "vinfo_proxy_supported",
}


def _artifact_payload(value: Any, field_name: str) -> dict[str, Any]:
    if value is None:
        raise ValueError(f"{field_name} is required")
    payload = to_payload(value)
    if not isinstance(payload, dict):
        raise TypeError(f"{field_name} must serialize to a dict")
    return deepcopy(payload)


def _optional_artifact_payload(value: Any, field_name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    return _artifact_payload(value, field_name)


def _normalize_claim_name(value: Any) -> str:
    normalized = str(value).strip().lower()
    for char in (" ", "-", "/"):
        normalized = normalized.replace(char, "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized


def _has_explicit_future_support(value: Mapping[str, Any] | None) -> bool:
    if not value:
        return False
    return (
        value.get("controller_review_complete") is True
        and value.get("independent_review_complete") is True
        and bool(value.get("accepted_evidence_package"))
    )


def _reject_raw_response_payload(value: Any, *, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = _normalize_claim_name(key_text)
            child_path = f"{path}.{key_text}"
            if normalized_key in RAW_RESPONSE_BODY_FIELDS:
                raise ValueError(f"raw_response body field is forbidden: {child_path}")
            if normalized_key in RAW_RESPONSE_FLAG_FIELDS and child is not False:
                raise ValueError(f"{child_path} must be false")
            _reject_raw_response_payload(child, path=child_path)
    elif isinstance(value, list | tuple):
        for index, child in enumerate(value):
            _reject_raw_response_payload(child, path=f"{path}[{index}]")


def _contains_generated_token_logprobs(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = _normalize_claim_name(key)
            if "generated" in key_text and "logprob" in key_text:
                return True
            if _contains_generated_token_logprobs(child):
                return True
    elif isinstance(value, list | tuple):
        return any(_contains_generated_token_logprobs(child) for child in value)
    return False


def _missing_fields(payload: Mapping[str, Any], required_fields: tuple[str, ...]) -> list[str]:
    return [field_name for field_name in required_fields if field_name not in payload]


@dataclass(frozen=True)
class CostLatencyLedger:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    latency_ms: int = 0

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any] | None) -> CostLatencyLedger:
        payload = dict(payload or {})
        input_tokens = int(payload.get("input_tokens", 0))
        output_tokens = int(payload.get("output_tokens", 0))
        total_tokens = int(payload.get("total_tokens", input_tokens + output_tokens))
        estimated_cost = float(payload.get("estimated_cost", 0.0))
        latency_ms = int(payload.get("latency_ms", 0))
        if min(input_tokens, output_tokens, total_tokens, estimated_cost, latency_ms) < 0:
            raise ValueError("cost_latency_ledger values must be non-negative")
        if total_tokens != input_tokens + output_tokens:
            raise ValueError("total_tokens must equal input_tokens + output_tokens")
        return cls(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            latency_ms=latency_ms,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.estimated_cost,
            "latency_ms": self.latency_ms,
        }


@dataclass(frozen=True)
class ClaimLedger:
    claim_candidate: str = "projection_bundle_v1"
    metric_claim_level: str = "operational_utility_only"
    bridge_status: str = "unavailable_but_disclosed"
    judge_status: str = "not_applicable"
    artifact_status: str = "incomplete"
    replay_status: str = "not_run"
    reprojection_status: str = "not_run"
    raw_response_stored: bool = False
    human_external_gold_label: bool = False
    current_claim_level: str = "operational_utility_only/no_claim_upgrade"
    allowed_claims: tuple[str, ...] = ()
    denied_claims: tuple[str, ...] = DEFAULT_DENIED_CLAIMS
    claim_upgrade: bool = False
    route_5_locked: bool = True
    route_8_locked: bool = True
    supporting_future_evidence: dict[str, Any] | None = None

    @classmethod
    def for_artifact_status(cls, artifact_status: str) -> ClaimLedger:
        normalized_status = str(artifact_status)
        allowed_claims: tuple[str, ...] = ()
        denied_claims = DEFAULT_DENIED_CLAIMS
        if normalized_status == "complete":
            allowed_claims = ("replayable_artifact_evidence",)
        else:
            denied_claims = INCOMPLETE_BUNDLE_DENIED_CLAIMS
        return cls(
            artifact_status=normalized_status,
            allowed_claims=allowed_claims,
            denied_claims=denied_claims,
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any] | None, *, artifact_status: str | None = None) -> ClaimLedger:
        payload = dict(payload or {})
        default = cls.for_artifact_status(str(artifact_status or payload.get("artifact_status") or "incomplete"))
        raw_response_stored = bool(payload.get("raw_response_stored", default.raw_response_stored))
        if raw_response_stored:
            raise ValueError("raw_response_stored must be false")
        allowed_claims = tuple(
            _normalize_claim_name(value) for value in payload.get("allowed_claims", default.allowed_claims)
        )
        denied_claims = tuple(
            dict.fromkeys(
                _normalize_claim_name(value) for value in payload.get("denied_claims", default.denied_claims)
            )
        )
        claim_upgrade = bool(payload.get("claim_upgrade", default.claim_upgrade))
        route_5_locked = bool(payload.get("route_5_locked", payload.get("route5_locked", default.route_5_locked)))
        route_8_locked = bool(payload.get("route_8_locked", payload.get("route8_locked", default.route_8_locked)))
        supporting_future_evidence = payload.get("supporting_future_evidence")
        has_future_support = _has_explicit_future_support(supporting_future_evidence)
        metric_claim_level = str(payload.get("metric_claim_level", default.metric_claim_level))
        unsafe_allowed_claims = set(allowed_claims) & UPGRADE_CLAIMS
        if (
            claim_upgrade
            or not route_5_locked
            or not route_8_locked
            or unsafe_allowed_claims
            or metric_claim_level != "operational_utility_only"
        ) and not has_future_support:
            raise ValueError("claim upgrades require explicit future evidence and controller review")
        return cls(
            claim_candidate=str(payload.get("claim_candidate", default.claim_candidate)),
            metric_claim_level=metric_claim_level,
            bridge_status=str(payload.get("bridge_status", default.bridge_status)),
            judge_status=str(payload.get("judge_status", default.judge_status)),
            artifact_status=str(artifact_status or payload.get("artifact_status") or default.artifact_status),
            replay_status=str(payload.get("replay_status", default.replay_status)),
            reprojection_status=str(payload.get("reprojection_status", default.reprojection_status)),
            raw_response_stored=False,
            human_external_gold_label=bool(
                payload.get("human_external_gold_label", default.human_external_gold_label)
            ),
            current_claim_level=str(payload.get("current_claim_level", default.current_claim_level)),
            allowed_claims=allowed_claims,
            denied_claims=denied_claims,
            claim_upgrade=claim_upgrade,
            route_5_locked=route_5_locked,
            route_8_locked=route_8_locked,
            supporting_future_evidence=dict(supporting_future_evidence)
            if isinstance(supporting_future_evidence, Mapping)
            else None,
        )

    def fail_closed_for_artifact_status(self, artifact_status: str) -> ClaimLedger:
        if artifact_status == "complete":
            return self
        denied_claims = tuple(
            dict.fromkeys(
                (
                    *(claim for claim in self.denied_claims if claim != "vinfo_proxy_supported"),
                    "v_information_proxy_support",
                    "no_aggregated_headline_claim",
                )
            )
        )
        return ClaimLedger(
            claim_candidate=self.claim_candidate,
            metric_claim_level="operational_utility_only",
            bridge_status=self.bridge_status,
            judge_status=self.judge_status,
            artifact_status="incomplete",
            replay_status=self.replay_status,
            reprojection_status=self.reprojection_status,
            raw_response_stored=False,
            human_external_gold_label=self.human_external_gold_label,
            current_claim_level="operational_utility_only/no_claim_upgrade",
            allowed_claims=(),
            denied_claims=denied_claims,
            claim_upgrade=False,
            route_5_locked=True,
            route_8_locked=True,
            supporting_future_evidence=None,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "claim_candidate": self.claim_candidate,
            "metric_claim_level": self.metric_claim_level,
            "bridge_status": self.bridge_status,
            "judge_status": self.judge_status,
            "artifact_status": self.artifact_status,
            "replay_status": self.replay_status,
            "reprojection_status": self.reprojection_status,
            "raw_response_stored": False,
            "human_external_gold_label": self.human_external_gold_label,
            "current_claim_level": self.current_claim_level,
            "allowed_claims": list(self.allowed_claims),
            "denied_claims": list(self.denied_claims),
            "claim_upgrade": self.claim_upgrade,
            "route_5_locked": self.route_5_locked,
            "route_8_locked": self.route_8_locked,
        }
        if self.supporting_future_evidence is not None:
            payload["supporting_future_evidence"] = deepcopy(self.supporting_future_evidence)
        return payload


@dataclass(frozen=True)
class ProjectionBundleV1:
    run_id: str
    dispatch_id: str
    agent_id: str
    round_id: str
    candidate_pool: dict[str, Any]
    projection_plan: dict[str, Any]
    budget_witness: dict[str, Any]
    materialized_context: dict[str, Any]
    metric_bridge_witness: dict[str, Any]
    diagnostics: dict[str, Any] | None = None
    counterfactual_replay_witness: dict[str, Any] | None = None
    reprojection_witness: dict[str, Any] | None = None
    judge_run_manifest: dict[str, Any] | None = None
    claim_ledger: dict[str, Any] | ClaimLedger | None = None
    cost_latency_ledger: dict[str, Any] | CostLatencyLedger | None = None
    raw_response_stored: bool = False
    artifact_status: str | None = None
    source_mode: str | None = None
    canonical_hash_value: str | None = None

    bundle_version: ClassVar[str] = "ProjectionBundleV1"

    def __post_init__(self) -> None:
        self.validate_required_identity()
        for field_name in REQUIRED_ARTIFACT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _artifact_payload(getattr(self, field_name), field_name),
            )
        if self.diagnostics is not None:
            object.__setattr__(self, "diagnostics", _artifact_payload(self.diagnostics, "diagnostics"))
        for field_name in OPTIONAL_WITNESS_REQUIRED_FIELDS:
            payload = _optional_artifact_payload(getattr(self, field_name), field_name)
            object.__setattr__(self, field_name, payload)
            if payload is not None:
                missing = _missing_fields(payload, OPTIONAL_WITNESS_REQUIRED_FIELDS[field_name])
                if missing:
                    raise ValueError(f"{field_name} missing required fields: {', '.join(missing)}")
        if self.raw_response_stored is not False:
            raise ValueError("raw_response_stored must default to false")
        _reject_raw_response_payload(self.to_dict(include_policy_ledgers=False))
        if _contains_generated_token_logprobs(self.metric_bridge_witness) and self.metric_bridge_witness.get(
            "generated_token_logprobs_used_as_answer_side_diagnostic_only"
        ) is not True:
            raise ValueError("generated-token logprobs must be answer-side diagnostics only")
        artifact_status = self.artifact_status or self._computed_artifact_status()
        object.__setattr__(self, "artifact_status", artifact_status)
        if isinstance(self.claim_ledger, ClaimLedger):
            claim_ledger = self.claim_ledger.fail_closed_for_artifact_status(artifact_status)
        else:
            claim_ledger = ClaimLedger.from_dict(self.claim_ledger, artifact_status=artifact_status)
            claim_ledger = claim_ledger.fail_closed_for_artifact_status(artifact_status)
        cost_latency_ledger = (
            self.cost_latency_ledger
            if isinstance(self.cost_latency_ledger, CostLatencyLedger)
            else CostLatencyLedger.from_dict(self.cost_latency_ledger)
        )
        object.__setattr__(self, "claim_ledger", claim_ledger)
        object.__setattr__(self, "cost_latency_ledger", cost_latency_ledger)

    def validate_required_identity(self) -> None:
        for field_name in REQUIRED_IDENTITY_FIELDS:
            value = getattr(self, field_name)
            if value is None or str(value).strip() == "":
                raise ValueError(f"{field_name} is required")

    def _computed_artifact_status(self) -> str:
        for field_name, required_fields in CORE_CONTRACT_REQUIRED_FIELDS.items():
            if _missing_fields(getattr(self, field_name), required_fields):
                return "incomplete"
        return "complete"

    def to_dict(self, *, include_policy_ledgers: bool = True) -> dict[str, Any]:
        self.validate_required_identity()
        payload: dict[str, Any] = {
            "bundle_version": self.bundle_version,
            "run_id": self.run_id,
            "dispatch_id": self.dispatch_id,
            "agent_id": self.agent_id,
            "round_id": self.round_id,
            "candidate_pool": deepcopy(self.candidate_pool),
            "projection_plan": deepcopy(self.projection_plan),
            "budget_witness": deepcopy(self.budget_witness),
            "materialized_context": deepcopy(self.materialized_context),
            "metric_bridge_witness": deepcopy(self.metric_bridge_witness),
            "raw_response_stored": False,
            "artifact_status": str(self.artifact_status or self._computed_artifact_status()),
        }
        if self.diagnostics is not None:
            payload["diagnostics"] = deepcopy(self.diagnostics)
        for field_name in OPTIONAL_WITNESS_REQUIRED_FIELDS:
            value = getattr(self, field_name)
            if value is not None:
                payload[field_name] = deepcopy(value)
        if include_policy_ledgers:
            claim_ledger = self.claim_ledger
            cost_latency_ledger = self.cost_latency_ledger
            payload["claim_ledger"] = (
                claim_ledger.to_dict() if isinstance(claim_ledger, ClaimLedger) else deepcopy(claim_ledger)
            )
            payload["cost_latency_ledger"] = (
                cost_latency_ledger.to_dict()
                if isinstance(cost_latency_ledger, CostLatencyLedger)
                else deepcopy(cost_latency_ledger)
            )
        if self.source_mode is not None:
            payload["source_mode"] = self.source_mode
        if self.canonical_hash_value is not None:
            payload["canonical_hash"] = self.canonical_hash_value
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ProjectionBundleV1:
        bundle_version = payload.get("bundle_version", cls.bundle_version)
        if bundle_version != cls.bundle_version:
            raise ValueError(f"unsupported bundle_version: {bundle_version}")
        for field_name in (*REQUIRED_IDENTITY_FIELDS, *REQUIRED_ARTIFACT_FIELDS):
            if field_name not in payload:
                raise ValueError(f"{field_name} is required")
        return cls(
            run_id=payload["run_id"],
            dispatch_id=payload["dispatch_id"],
            agent_id=payload["agent_id"],
            round_id=payload["round_id"],
            candidate_pool=payload["candidate_pool"],
            projection_plan=payload["projection_plan"],
            budget_witness=payload["budget_witness"],
            materialized_context=payload["materialized_context"],
            metric_bridge_witness=payload["metric_bridge_witness"],
            diagnostics=payload.get("diagnostics"),
            counterfactual_replay_witness=payload.get("counterfactual_replay_witness"),
            reprojection_witness=payload.get("reprojection_witness"),
            judge_run_manifest=payload.get("judge_run_manifest"),
            claim_ledger=payload.get("claim_ledger"),
            cost_latency_ledger=payload.get("cost_latency_ledger"),
            raw_response_stored=bool(payload.get("raw_response_stored", False)),
            artifact_status=payload.get("artifact_status"),
            source_mode=payload.get("source_mode"),
            canonical_hash_value=payload.get("canonical_hash"),
        )

    def to_canonical_json(self) -> str:
        payload = self.to_dict()
        payload.pop("canonical_hash", None)
        return stable_json_dumps(payload)

    def canonical_hash(self) -> str:
        payload = self.to_dict()
        payload.pop("canonical_hash", None)
        return stable_hash(payload)


def projection_bundle_from_dict(payload: dict[str, Any]) -> ProjectionBundleV1:
    return ProjectionBundleV1.from_dict(payload)


def projection_bundle_from_epf_final_metadata(
    *,
    final_manifest: Mapping[str, Any],
    final_claim_request: Mapping[str, Any] | None = None,
    scoped_operational_evaluation_summary: Mapping[str, Any] | None = None,
) -> ProjectionBundleV1:
    final_manifest = deepcopy(dict(final_manifest))
    final_claim_request = deepcopy(dict(final_claim_request or {}))
    scoped_summary = deepcopy(dict(scoped_operational_evaluation_summary or {}))
    _reject_raw_response_payload(final_manifest, path="final_manifest")
    _reject_raw_response_payload(final_claim_request, path="final_claim_request")
    _reject_raw_response_payload(scoped_summary, path="scoped_operational_evaluation_summary")
    artifacts = dict(final_manifest.get("artifacts") or {})
    provenance = dict(final_manifest.get("provenance") or {})
    silver_package = dict(provenance.get("silver_label_package") or {})
    evidence_ids = sorted(
        str(value)
        for value in {
            *artifacts.values(),
            *silver_package.values(),
        }
        if value
    )
    source_hash = stable_hash(
        {
            "artifacts": artifacts,
            "claim_request": final_claim_request,
            "evidence_ids": evidence_ids,
            "manifest_schema": final_manifest.get("schema_version"),
            "scoped_summary": scoped_summary,
        }
    )
    label_count = int(scoped_summary.get("label_count", 0) or 0)
    chat_logprobs = dict(
        (scoped_summary.get("scoped_operational_inputs") or {}).get("chat_logprob_confidence") or {}
    )
    denied_claims = tuple(
        dict.fromkeys(
            (
                *(_normalize_claim_name(value) for value in final_manifest.get("denied_claims", ())),
                *DEFAULT_DENIED_CLAIMS,
            )
        )
    )
    claim_ledger = ClaimLedger.from_dict(
        {
            "claim_candidate": "epf_final_projection_bundle_v1",
            "metric_claim_level": "operational_utility_only",
            "bridge_status": "unavailable_but_disclosed",
            "judge_status": str(final_manifest.get("review_status", "candidate_pending_independent_review")),
            "artifact_status": "complete",
            "replay_status": "metadata_mapped",
            "reprojection_status": "not_run",
            "raw_response_stored": False,
            "human_external_gold_label": bool(final_claim_request.get("human_external_gold_validation", False)),
            "current_claim_level": str(
                final_claim_request.get(
                    "claim_status",
                    final_manifest.get("claim_status", "operational_utility_only/no_claim_upgrade"),
                )
            ),
            "allowed_claims": ["replayable_artifact_evidence"],
            "denied_claims": denied_claims,
            "claim_upgrade": bool(final_claim_request.get("development_claim_upgrade_performed", False)),
            "route_5_locked": not bool(final_claim_request.get("route5_unlock_requested", False)),
            "route_8_locked": not bool(final_claim_request.get("route8_unlock_requested", False)),
        },
        artifact_status="complete",
    )
    return ProjectionBundleV1(
        run_id="epf-final",
        dispatch_id="epf-final-metadata",
        agent_id="epf-finalizer",
        round_id="final",
        candidate_pool={
            "candidate_ids_considered": evidence_ids,
            "source_manifest_hash": source_hash,
            "label_count": label_count,
        },
        projection_plan={
            "dispatch_id": "epf-final-metadata",
            "query_id": "epf-final-operational-audit",
            "conversation_turn_id": "final",
            "candidate_ids_considered": evidence_ids,
            "selected_evidence_ids": evidence_ids,
            "excluded_evidence_ids": [],
            "selector_name": "epf_final_metadata_mapper",
            "selector_config_hash": stable_hash({"selector": "epf_final_metadata_mapper"}),
            "score_manifest_hash": source_hash,
        },
        budget_witness={
            "requested_budget_tokens": 0,
            "realized_budget_tokens": 0,
            "token_count_method": "metadata_only_no_raw_context",
            "section_level_token_counts": {},
            "trim_events": [],
            "overflow_policy": "not_applicable_metadata_mapping",
        },
        materialized_context={
            "materialized_context_hash": source_hash,
            "materialization_order": evidence_ids,
            "section_boundaries": [],
            "prompt_template_hash": "metadata_only_no_prompt_template",
            "downstream_prompt_hash": "metadata_only_no_downstream_prompt",
            "evidence_hashes": {evidence_id: stable_hash(evidence_id) for evidence_id in evidence_ids},
        },
        metric_bridge_witness={
            "metric_class": "operational_only",
            "active_stratum": {"package": "EPF-FINAL"},
            "model_snapshot": "metadata_redacted",
            "endpoint": "metadata_redacted",
            "thinking_mode": "not_recorded",
            "decoding_policy": {"mode": "metadata_only"},
            "bridge_status": "unavailable_but_disclosed",
            "diagnostic_claim_level": "operational_utility_only",
            "drift_status": "not_evaluated",
            "generated_token_logprobs_used_as_answer_side_diagnostic_only": bool(
                chat_logprobs.get("generated_token_logprobs_available", False)
            ),
            "fixed_target_nll_supported": bool(
                scoped_summary.get("teacher_forced_fixed_target_nll_available", False)
            ),
        },
        claim_ledger=claim_ledger,
        cost_latency_ledger=CostLatencyLedger(),
        source_mode="epf_final_metadata",
    )
