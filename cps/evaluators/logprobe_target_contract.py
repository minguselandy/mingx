from __future__ import annotations

from copy import deepcopy
from typing import Any
from typing import Mapping

from cps.benchmarks.hashing import stable_hash


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
FEVER_DISABLED_DECISION = "SWITCH_TO_FEVER_LABEL_NLL"

REQUIRED_CONTRACT_FIELDS = (
    "target_type",
    "verbalizer_policy",
    "tokenization_policy",
    "teacher_forced_scoring_required",
    "target_format_hash",
    "prompt_template_hash",
    "materialization_policy_hash",
    "fixed_target_representation",
    "row_provenance",
    "target_provenance",
)


def _payload_mentions_fever(payload: Mapping[str, Any]) -> bool:
    stack: list[Any] = [payload]
    while stack:
        current = stack.pop()
        if isinstance(current, Mapping):
            stack.extend(current.values())
            continue
        if isinstance(current, list | tuple):
            stack.extend(current)
            continue
        if "fever" in str(current).casefold():
            return True
    return False


def build_canonical_target_contract(
    *,
    materialization_policy: str,
    prompt_template: str,
    row_provenance: Mapping[str, Any],
    target_provenance: Mapping[str, Any],
    target_type: str,
    target_representation: str,
    tokenization_policy: str,
    verbalizer_policy: str,
    teacher_forced_scoring_required: bool = True,
) -> dict[str, Any]:
    target_payload = {
        "target_representation": target_representation,
        "target_type": target_type,
        "tokenization_policy": tokenization_policy,
        "verbalizer_policy": verbalizer_policy,
    }
    fever_check_payload = {
        "target_payload": target_payload,
        "target_provenance": dict(target_provenance),
    }
    if _payload_mentions_fever(fever_check_payload):
        raise ValueError("FEVER targets are disabled for this goal")
    contract = {
        "claim_status": CLAIM_STATUS,
        "disabled_decisions": [FEVER_DISABLED_DECISION],
        "fixed_target_representation": str(target_representation),
        "materialization_policy": str(materialization_policy),
        "materialization_policy_hash": stable_hash({"materialization_policy": str(materialization_policy)}),
        "prompt_template_hash": stable_hash({"prompt_template": str(prompt_template)}),
        "row_provenance": deepcopy(dict(row_provenance)),
        "schema_version": "logprobe_target_contract_v1",
        "target_format_hash": stable_hash(target_payload),
        "target_provenance": deepcopy(dict(target_provenance)),
        "target_type": str(target_type),
        "teacher_forced_scoring_required": bool(teacher_forced_scoring_required),
        "tokenization_policy": str(tokenization_policy),
        "verbalizer_policy": str(verbalizer_policy),
    }
    contract["contract_hash"] = stable_hash({field: contract[field] for field in REQUIRED_CONTRACT_FIELDS})
    return contract


def validate_target_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for field in REQUIRED_CONTRACT_FIELDS:
        if field not in contract or contract.get(field) in ("", None, {}, []):
            errors.append(f"missing_{field}")
    if contract.get("teacher_forced_scoring_required") is not True:
        errors.append("teacher_forced_scoring_required_false")
    active_target_payload = {
        "fixed_target_representation": contract.get("fixed_target_representation"),
        "target_provenance": contract.get("target_provenance"),
        "target_type": contract.get("target_type"),
        "verbalizer_policy": contract.get("verbalizer_policy"),
    }
    if _payload_mentions_fever(active_target_payload):
        errors.append("fever_target_disabled")
    expected_target_hash = stable_hash(
        {
            "target_representation": str(contract.get("fixed_target_representation") or ""),
            "target_type": str(contract.get("target_type") or ""),
            "tokenization_policy": str(contract.get("tokenization_policy") or ""),
            "verbalizer_policy": str(contract.get("verbalizer_policy") or ""),
        }
    )
    if contract.get("target_format_hash") and contract.get("target_format_hash") != expected_target_hash:
        errors.append("target_format_hash_mismatch")
    return {
        "claim_status": CLAIM_STATUS,
        "errors": errors,
        "passed": not errors,
        "schema_version": "logprobe_target_contract_validation_v1",
    }
