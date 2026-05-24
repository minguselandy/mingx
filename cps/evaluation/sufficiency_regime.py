from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from cps.experiments.artifacts import stable_hash


REQUIRED_REGIME_LABELS = {
    "sufficient_kept",
    "sufficient_dropped",
    "insufficient_and_answered",
    "insufficient_and_abstained",
}
ALLOWED_SUFFICIENCY_TRIGGERS = {
    "sufficient_dropped",
    "insufficient_and_answered",
    "unknown_due_to_missing_context",
    "hallucination_risk",
}
MISSING_EVIDENCE_TYPES = {
    "entity",
    "temporal",
    "bridge_fact",
    "qualifier",
    "provenance",
    "multi_hop_prerequisite",
    "unknown",
}
JUDGE_LABELS = {"support", "insufficient", "contradict", "uncertain", "parse_failed"}
CLAIM_LEVEL = "sufficiency_abstention_diagnostic_only"
CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
PILOT_READY_STATUS = "offline_framework_ready_live_api_not_run"
DENIED_CLAIMS = (
    "truth_validation",
    "calibrated_abstention",
    "measurement_validation",
    "fixed_target_nll_bridge",
    "human_external_gold_validation",
    "paper_grade_validation",
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
PROMPT_PATH = Path("prompts/reprojection/sufficiency_abstention_v1.md")
PARSE_FAILURE_RATE_MAX = 0.15


def _normalize_key(value: Any) -> str:
    normalized = str(value).strip().lower()
    for char in (" ", "-", "/"):
        normalized = normalized.replace(char, "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized


def _reject_raw_or_live_payload(value: Any, *, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized_key = _normalize_key(key_text)
            child_path = f"{path}.{key_text}"
            if normalized_key in RAW_RESPONSE_BODY_FIELDS:
                raise ValueError(f"raw_response body field is forbidden: {child_path}")
            if normalized_key in RAW_RESPONSE_FLAG_FIELDS and child is not False:
                raise ValueError(f"{child_path} must be false")
            if normalized_key == "live_api_call_performed" and child is not False:
                raise ValueError(f"{child_path} must be false")
            _reject_raw_or_live_payload(child, path=child_path)
    elif isinstance(value, list | tuple):
        for index, child in enumerate(value):
            _reject_raw_or_live_payload(child, path=f"{path}[{index}]")


def _normalize_judge_label(value: Any) -> str:
    label = _normalize_key(value)
    if label in JUDGE_LABELS:
        return label
    return "parse_failed"


def _normalize_missing_evidence_types(value: Any) -> tuple[str, ...]:
    if value is None:
        raw_values: list[Any] = []
    elif isinstance(value, str):
        raw_values = [value]
    else:
        raw_values = list(value)
    normalized = {
        _normalize_key(item)
        for item in raw_values
        if _normalize_key(item) in MISSING_EVIDENCE_TYPES
    }
    if not normalized and raw_values:
        normalized.add("unknown")
    return tuple(sorted(normalized))


def classify_sufficiency_regime(payload: Mapping[str, Any]) -> dict[str, Any]:
    projected_evidence_sufficient = bool(payload.get("projected_evidence_sufficient", False))
    answer_emitted = bool(payload.get("answer_emitted", False))
    abstained = bool(payload.get("abstained", False))
    omitted_evidence_necessary = bool(payload.get("omitted_evidence_necessary", False))
    judge_label = _normalize_judge_label(payload.get("judge_label"))
    missing_evidence_types = _normalize_missing_evidence_types(
        payload.get("missing_evidence_types", [])
    )

    if projected_evidence_sufficient and answer_emitted and not omitted_evidence_necessary:
        regime_label = "sufficient_kept"
    elif omitted_evidence_necessary or (projected_evidence_sufficient and not answer_emitted):
        regime_label = "sufficient_dropped"
    elif not projected_evidence_sufficient and answer_emitted:
        regime_label = "insufficient_and_answered"
    elif not projected_evidence_sufficient and (abstained or not answer_emitted):
        regime_label = "insufficient_and_abstained"
    else:
        regime_label = "insufficient_and_abstained"

    trigger_label = str(payload.get("trigger_label") or "").strip()
    if not trigger_label:
        if regime_label == "sufficient_dropped":
            trigger_label = "sufficient_dropped"
        elif regime_label == "insufficient_and_answered" and judge_label == "contradict":
            trigger_label = "hallucination_risk"
        elif missing_evidence_types or judge_label in {"uncertain", "parse_failed"}:
            trigger_label = "unknown_due_to_missing_context"
        elif regime_label == "insufficient_and_answered":
            trigger_label = "insufficient_and_answered"
        else:
            trigger_label = "unknown_due_to_missing_context"
    trigger_label = _normalize_key(trigger_label)
    if trigger_label not in ALLOWED_SUFFICIENCY_TRIGGERS:
        trigger_label = "unknown_due_to_missing_context"

    return {
        "regime_label": regime_label,
        "trigger_label": trigger_label,
        "judge_label": judge_label,
        "missing_evidence_types": list(missing_evidence_types),
    }


@dataclass(frozen=True)
class SufficiencyRegimeRecord:
    record_id: str
    item_id: str
    judge_label: str
    projected_evidence_sufficient: bool
    answer_emitted: bool
    abstained: bool
    regime_label: str
    trigger_label: str
    missing_evidence_types: tuple[str, ...]
    input_token_count: int
    output_token_count: int
    parse_status: str
    claim_level: str = CLAIM_LEVEL
    claim_status: str = CLAIM_STATUS
    candidate_operational_evidence_only: bool = True
    measurement_validation_claim: bool = False
    truth_validation_claim: bool = False
    calibrated_abstention_claim: bool = False
    human_external_gold_label: bool = False
    raw_response_stored: bool = False
    live_api_call_performed: bool = False
    route_5_locked: bool = True
    route_8_locked: bool = True

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SufficiencyRegimeRecord:
        _reject_raw_or_live_payload(payload)
        data = dict(payload)
        classified = classify_sufficiency_regime(data)
        parse_status = str(data.get("parse_status") or "parsed").strip().lower()
        judge_label = classified["judge_label"]
        if judge_label == "parse_failed" or parse_status == "parse_failed":
            parse_status = "parse_failed"
            judge_label = "parse_failed"
        elif parse_status != "parsed":
            parse_status = "parse_failed"
            judge_label = "parse_failed"

        for field_name in (
            "measurement_validation_claim",
            "truth_validation_claim",
            "calibrated_abstention_claim",
            "human_external_gold_label",
        ):
            if data.get(field_name) is True:
                raise ValueError(f"{field_name} must be false")

        return cls(
            record_id=str(data.get("record_id", "")),
            item_id=str(data.get("item_id", "")),
            judge_label=judge_label,
            projected_evidence_sufficient=bool(
                data.get("projected_evidence_sufficient", False)
            ),
            answer_emitted=bool(data.get("answer_emitted", False)),
            abstained=bool(data.get("abstained", False)),
            regime_label=classified["regime_label"],
            trigger_label=classified["trigger_label"],
            missing_evidence_types=tuple(classified["missing_evidence_types"]),
            input_token_count=max(0, int(data.get("input_token_count", 0))),
            output_token_count=max(0, int(data.get("output_token_count", 0))),
            parse_status=parse_status,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["missing_evidence_types"] = list(self.missing_evidence_types)
        return payload


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def prompt_hashes() -> dict[str, str]:
    path = _repo_root() / PROMPT_PATH
    return {PROMPT_PATH.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()}


def build_sufficiency_manifest(
    *,
    run_id: str,
    items: Iterable[Mapping[str, Any]],
    downstream_prompt_template_hash: str,
) -> dict[str, Any]:
    normalized_items = sorted(
        [{"item_id": str(item["item_id"])} for item in items],
        key=lambda row: row["item_id"],
    )
    manifest = {
        "run_id": str(run_id),
        "protocol_version": "v1_operational_only",
        "purpose": "classify_evidence_sufficiency_and_test_omission_sensitive_failures",
        "items": normalized_items,
        "required_regime_labels": sorted(REQUIRED_REGIME_LABELS),
        "allowed_triggers": sorted(ALLOWED_SUFFICIENCY_TRIGGERS),
        "judge_labels": sorted(JUDGE_LABELS),
        "downstream_prompt_template_hash": str(downstream_prompt_template_hash),
        "prompt_hashes": prompt_hashes(),
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


def _records_to_list(
    records: Iterable[SufficiencyRegimeRecord | Mapping[str, Any]],
) -> list[SufficiencyRegimeRecord]:
    return [
        record
        if isinstance(record, SufficiencyRegimeRecord)
        else SufficiencyRegimeRecord.from_dict(record)
        for record in records
    ]


def _witness_dicts(witnesses: Iterable[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for witness in witnesses:
        if hasattr(witness, "to_dict"):
            rows.append(witness.to_dict())
        else:
            rows.append(dict(witness))
    return rows


def evaluate_sufficiency_claim_gate(
    *,
    records: Iterable[SufficiencyRegimeRecord | Mapping[str, Any]],
    witnesses: Iterable[Any],
) -> dict[str, Any]:
    normalized_records = _records_to_list(records)
    witness_rows = _witness_dicts(witnesses)
    parse_failure_count = sum(
        1
        for record in normalized_records
        if record.parse_status == "parse_failed" or record.judge_label == "parse_failed"
    )
    parse_failure_rate = (
        parse_failure_count / len(normalized_records) if normalized_records else 1.0
    )
    label_counts = Counter(record.regime_label for record in normalized_records)
    unsupported_answer_count = label_counts["insufficient_and_answered"]
    abstain_count = label_counts["insufficient_and_abstained"]
    repairable_witnesses = [
        row
        for row in witness_rows
        if row.get("repair_status") in {"reprojection_candidate", "repair_candidate"}
    ]
    non_comparable = [
        row
        for row in witness_rows
        if "not_comparable" in str(row.get("repair_status", ""))
        or row.get("comparable_replay") is False
    ]

    reason_codes: list[str] = []
    if parse_failure_rate > PARSE_FAILURE_RATE_MAX:
        reason_codes.append("parse_failure_rate_above_threshold")
    if non_comparable:
        reason_codes.append("non_comparable_reprojection_witness")

    if reason_codes:
        allowed_claims: list[str] = []
        final_gate_status = "downgraded_to_ambiguous"
    else:
        allowed_claims = [CLAIM_LEVEL]
        final_gate_status = PILOT_READY_STATUS

    total = len(normalized_records) or 1
    metrics = {
        "support_rate": sum(1 for record in normalized_records if record.judge_label == "support")
        / total,
        "insufficient_rate": sum(
            1 for record in normalized_records if record.judge_label == "insufficient"
        )
        / total,
        "contradict_rate": sum(
            1 for record in normalized_records if record.judge_label == "contradict"
        )
        / total,
        "abstain_rate": abstain_count / total,
        "unsupported_answer_rate": unsupported_answer_count / total,
        "reprojection_repair_rate": len(repairable_witnesses) / len(witness_rows)
        if witness_rows
        else 0.0,
        "position_sensitivity_rate": sum(
            1
            for row in witness_rows
            if row.get("position_aware_replay_manifest", {}).get("enabled") is True
        )
        / len(witness_rows)
        if witness_rows
        else 0.0,
        "parse_failure_rate": parse_failure_rate,
        "cost_delta": 0,
        "latency_delta": 0,
    }

    return {
        "claim_status": CLAIM_STATUS,
        "allowed_claims": allowed_claims,
        "denied_claims": list(DENIED_CLAIMS),
        "final_gate_status": final_gate_status,
        "reason_codes": sorted(reason_codes),
        "candidate_operational_evidence_only": True,
        "measurement_validation_claim": False,
        "truth_validation_claim": False,
        "calibrated_abstention_claim": False,
        "human_external_gold_label": False,
        "raw_response_stored": False,
        "live_api_call_performed": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "metrics": metrics,
    }
