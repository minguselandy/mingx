from __future__ import annotations

import json
from collections import Counter
from typing import Any
from typing import Mapping
from typing import Sequence


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"


def _failure_counts(report: Mapping[str, Any]) -> dict[str, int]:
    failures = report.get("api_failures") or []
    if not isinstance(failures, list):
        failures = []
    target_terms = ("expected", "label", "token", "verbal", "classifier emitted")
    network_terms = ("timeout", "connection", "ssl", "network", "winerror", "eof")
    target_count = 0
    network_count = 0
    for failure in failures:
        text = json.dumps(failure, sort_keys=True).casefold()
        if any(term in text for term in target_terms):
            target_count += 1
        if any(term in text for term in network_terms):
            network_count += 1
    return {
        "failure_count": len(failures),
        "network_failure_count": network_count,
        "target_verbalization_failure_count": target_count,
    }


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _target_length_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    lengths: list[int] = []
    token_lengths: list[int] = []
    for row in rows:
        target = str(row.get("target_y") or "")
        if not target:
            continue
        lengths.append(len(target))
        token_lengths.append(len(target.split()))
    multi_token_count = sum(1 for length in token_lengths if length > 1)
    return {
        "max_char_length": max(lengths) if lengths else 0,
        "max_whitespace_token_length": max(token_lengths) if token_lengths else 0,
        "multi_token_target_count": multi_token_count,
        "multi_token_target_rate": round(multi_token_count / len(token_lengths), 12) if token_lengths else None,
        "target_count": len(token_lengths),
    }


def _delta_signal_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    deltas = [value for value in (_safe_float(row.get("delta_logloss")) for row in rows) if value is not None]
    if not deltas:
        return {
            "extreme_delta_logloss_count": 0,
            "near_zero_delta_logloss_count": 0,
            "row_count": 0,
        }
    return {
        "extreme_delta_logloss_count": sum(1 for value in deltas if abs(value) >= 1.0),
        "max_abs_delta_logloss": round(max(abs(value) for value in deltas), 12),
        "near_zero_delta_logloss_count": sum(1 for value in deltas if abs(value) <= 0.001),
        "near_zero_delta_logloss_rate": round(sum(1 for value in deltas if abs(value) <= 0.001) / len(deltas), 12),
        "row_count": len(deltas),
    }


def _materialization_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    policy_counts = Counter(str(row.get("materialization_policy") or "unknown") for row in rows)
    context_lengths = [len(row.get("context_L_packet_ids") or []) for row in rows]
    return {
        "context_packet_count_max": max(context_lengths) if context_lengths else 0,
        "context_packet_count_min": min(context_lengths) if context_lengths else 0,
        "materialization_policies": dict(sorted(policy_counts.items())),
        "materialization_policy_count": len(policy_counts),
        "position_order_risk": "not_recomputed_existing_rows_only",
    }


def build_logprobe_stability_reports(
    *,
    answer_generation_report: Mapping[str, Any],
    contract: Mapping[str, Any],
    route4_rows: Sequence[Mapping[str, Any]],
    support_generation_report: Mapping[str, Any],
) -> dict[str, Any]:
    answer_failures = _failure_counts(answer_generation_report)
    support_failures = _failure_counts(support_generation_report)
    answer_retries = int(answer_generation_report.get("api_retries") or 0)
    support_retries = int(support_generation_report.get("api_retries") or 0)
    instability_present = (
        answer_retries > 0
        or support_retries > 0
        or answer_failures["failure_count"] > 0
        or support_failures["failure_count"] > 0
    )
    length_summary = _target_length_summary(route4_rows)
    signal_summary = _delta_signal_summary(route4_rows)
    materialization = _materialization_summary(route4_rows)
    tokenization_status = "present" if length_summary["multi_token_target_count"] > 0 else "not_observed"
    matrix = {
        "claim_status": CLAIM_STATUS,
        "contract_hash": str(contract.get("contract_hash") or ""),
        "fever_disabled": True,
        "logprobe_stability_passed": False,
        "new_live_api_calls": False,
        "schema_version": "logprobe_stability_matrix_v1",
        "stability_status": "shadow_only_instability_present" if instability_present else "shadow_only_no_replicate_stability_proof",
        "targets": {
            "answer_nll": {
                "api_retries": answer_retries,
                **answer_failures,
                "records_validated": int(answer_generation_report.get("delta_records_validated") or 0),
            },
            "support_classification_nll": {
                "api_retries": support_retries,
                **support_failures,
                "records_validated": int(support_generation_report.get("delta_records_validated") or 0),
            },
        },
    }
    tokenization = {
        "claim_status": CLAIM_STATUS,
        "fixed_target_representation": str(contract.get("fixed_target_representation") or ""),
        "multi_token_target_risk": {
            "status": tokenization_status,
            **length_summary,
        },
        "new_live_api_calls": False,
        "schema_version": "logprobe_tokenization_risk_report_v1",
        "target_verbalization_tokenization": {
            "status": "present" if support_failures["target_verbalization_failure_count"] else "not_observed",
            "target_verbalization_failure_count": support_failures["target_verbalization_failure_count"],
        },
        **signal_summary,
    }
    materialization_report = {
        "claim_status": CLAIM_STATUS,
        "new_live_api_calls": False,
        "schema_version": "logprobe_materialization_sensitivity_report_v1",
        **materialization,
    }
    return {
        "logprobe_stability_matrix": matrix,
        "materialization_sensitivity_report": materialization_report,
        "tokenization_risk_report": tokenization,
    }
