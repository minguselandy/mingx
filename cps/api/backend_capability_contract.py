from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Mapping

from cps.experiments.artifacts import stable_json_dumps


CLAIM_LEVEL = "fail_closed_bridge_audit / operational_utility_only"
EVIDENCE_DOC_SNAPSHOT = (
    "docs/goals/mingx_codex_goal_live_api_plan/configs/live_api_only_experiment_plan.yaml;"
    "docs/goals/mingx_codex_goal_live_api_plan/configs/claim_gate_contract.yaml;"
    "docs/api/live-api-capability-contract.md;"
    "docs/paper/live-api-experiment-boundaries.md"
)
DENIED_CLAIMS = (
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


def _normalize_key(value: Any) -> str:
    normalized = str(value).strip().lower()
    for char in (" ", "-", "/"):
        normalized = normalized.replace(char, "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized


def _reject_raw_response_payload(value: Any, *, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = _normalize_key(key_text)
            child_path = f"{path}.{key_text}"
            if normalized_key in RAW_RESPONSE_BODY_FIELDS:
                raise ValueError(f"raw_response body field is forbidden: {child_path}")
            if normalized_key in RAW_RESPONSE_FLAG_FIELDS and child is not False:
                raise ValueError(f"{child_path} must be false")
            _reject_raw_response_payload(child, path=child_path)
    elif isinstance(value, list | tuple):
        for index, child in enumerate(value):
            _reject_raw_response_payload(child, path=f"{path}[{index}]")


@dataclass(frozen=True)
class BackendCapabilityContract:
    backend_name: str = "dashscope_compatible_live_api"
    endpoint_family: str = "openai_compatible_chat_completions"
    model_snapshot: str = "static_doc_snapshot"
    documented_generated_token_logprobs: bool = True
    documented_prompt_logprobs: bool = False
    fixed_target_teacher_forced_nll_supported: bool = False
    fixed_target_continuation_scoring_supported: bool = False
    generated_token_logprobs_allowed_use: str = "answer_side_confidence_diagnostic_only"
    denied_claims: tuple[str, ...] = DENIED_CLAIMS
    claim_level: str = CLAIM_LEVEL
    evidence_date_or_doc_snapshot: str = EVIDENCE_DOC_SNAPSHOT
    route_5_locked: bool = True
    route_8_locked: bool = True
    raw_response_stored: bool = False
    live_api_call_performed: bool = False

    schema_version: ClassVar[str] = "backend_capability_contract_v1_static"

    def __post_init__(self) -> None:
        if not str(self.backend_name).strip():
            raise ValueError("backend_name is required")
        if not str(self.endpoint_family).strip():
            raise ValueError("endpoint_family is required")
        if not str(self.model_snapshot).strip():
            raise ValueError("model_snapshot is required")
        if self.documented_prompt_logprobs:
            raise ValueError("prompt_logprobs unsupported by the static live-API contract")
        if self.fixed_target_teacher_forced_nll_supported:
            raise ValueError("generated-token logprobs cannot support fixed-target teacher-forced NLL")
        if self.fixed_target_continuation_scoring_supported:
            raise ValueError("fixed-target continuation scoring unsupported by the static live-API contract")
        if self.generated_token_logprobs_allowed_use != "answer_side_confidence_diagnostic_only":
            raise ValueError("generated-token logprobs must remain answer-side confidence diagnostics only")
        if self.claim_level != CLAIM_LEVEL:
            raise ValueError("claim_level must remain fail_closed_bridge_audit / operational_utility_only")
        if not self.route_5_locked or not self.route_8_locked:
            raise ValueError("Route 5 and Route 8 must remain locked")
        if self.raw_response_stored:
            raise ValueError("raw_response_stored must be false")
        if self.live_api_call_performed:
            raise ValueError("static backend audit witness must not run live API calls")
        _reject_raw_response_payload(self.to_dict(include_schema=False))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> BackendCapabilityContract:
        data = deepcopy(dict(payload))
        _reject_raw_response_payload(data)
        allowed = {
            "backend_name",
            "endpoint_family",
            "model_snapshot",
            "documented_generated_token_logprobs",
            "documented_prompt_logprobs",
            "fixed_target_teacher_forced_nll_supported",
            "fixed_target_continuation_scoring_supported",
            "generated_token_logprobs_allowed_use",
            "denied_claims",
            "claim_level",
            "evidence_date_or_doc_snapshot",
            "route_5_locked",
            "route_8_locked",
            "raw_response_stored",
            "live_api_call_performed",
        }
        return cls(**{key: value for key, value in data.items() if key in allowed})

    def to_dict(self, *, include_schema: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "backend_name": self.backend_name,
            "endpoint_family": self.endpoint_family,
            "model_snapshot": self.model_snapshot,
            "documented_generated_token_logprobs": self.documented_generated_token_logprobs,
            "documented_prompt_logprobs": self.documented_prompt_logprobs,
            "fixed_target_teacher_forced_nll_supported": False,
            "fixed_target_continuation_scoring_supported": False,
            "generated_token_logprobs_allowed_use": self.generated_token_logprobs_allowed_use,
            "denied_claims": list(self.denied_claims),
            "claim_level": self.claim_level,
            "evidence_date_or_doc_snapshot": self.evidence_date_or_doc_snapshot,
            "route_5_locked": True,
            "route_8_locked": True,
            "raw_response_stored": False,
            "live_api_call_performed": False,
        }
        if include_schema:
            payload["schema_version"] = self.schema_version
        return payload

    def to_canonical_json(self) -> str:
        return stable_json_dumps(self.to_dict())


def write_backend_capability_contract(path: str | Path, contract: BackendCapabilityContract) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(contract.to_canonical_json() + "\n", encoding="utf-8")
    return output_path
