from __future__ import annotations

from typing import Any
from typing import Mapping

from cps.evaluators.logprobe_target_contract import CLAIM_STATUS
from cps.evaluators.logprobe_target_contract import validate_target_contract


def validate_contract_against_row(contract: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_target_contract(contract)
    errors = list(validation["errors"])
    row_target_representation = str(row.get("target_representation") or contract.get("fixed_target_representation") or "")
    if row_target_representation != str(contract.get("fixed_target_representation") or ""):
        errors.append("target_representation_mismatch")
    row_materialization = str(row.get("materialization_policy") or "")
    if row_materialization and row_materialization != str(contract.get("materialization_policy") or ""):
        errors.append("materialization_policy_mismatch")
    return {
        "claim_status": CLAIM_STATUS,
        "errors": sorted(set(errors)),
        "passed": not errors,
        "schema_version": "logprobe_row_contract_validation_v1",
    }


def score_logprobe_shadow(contract: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_contract_against_row(contract, row)
    return {
        "claim_status": CLAIM_STATUS,
        "contract_hash": str(contract.get("contract_hash") or ""),
        "contract_validation": validation,
        "fixed_model_logloss_available": False,
        "live_api_used": False,
        "new_live_api_calls": False,
        "reason_code": "shadow_only_no_live_api_no_fixed_model_scoring",
        "schema_version": "logprobe_shadow_score_v1",
        "score_available": False,
        "target_format_hash": str(contract.get("target_format_hash") or ""),
        "teacher_forced_scoring_required": bool(contract.get("teacher_forced_scoring_required")),
    }
