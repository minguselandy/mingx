from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


ALLOWED_LABELS = {"support", "insufficient", "contradict", "uncertain", "parse_failed"}
ALLOWED_CLAIM_LEVEL = "model_adjudicated_weak_evidence"
CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
CONFIDENCE_BUCKETS = {"low", "medium", "high"}
PROTOCOL_FLAGS = {
    "missing_context",
    "contradiction_detected",
    "abstain_recommended",
    "parse_failure",
}
DENIED_CLAIMS = (
    "human_external_gold_validation",
    "measurement_validation",
    "calibrated_judge",
    "paper_grade_validation",
    "paper_grade_evidence",
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

PARSE_FAILURE_RATE_MAX = 0.15
ORDER_SWAP_AGREEMENT_MIN = 0.80
DUPLICATE_AGREEMENT_MIN = 0.80
RUBRIC_PARAPHRASE_AGREEMENT_MIN = 0.75

_LABEL_ALIASES = {
    "support": "support",
    "supports": "support",
    "supported": "support",
    "supporting": "support",
    "insufficient": "insufficient",
    "not enough information": "insufficient",
    "not enough info": "insufficient",
    "missing evidence": "insufficient",
    "contradict": "contradict",
    "contradicts": "contradict",
    "contradiction": "contradict",
    "contradicted": "contradict",
    "uncertain": "uncertain",
    "unknown": "uncertain",
    "ambiguous": "uncertain",
    "parse_failed": "parse_failed",
    "parse failed": "parse_failed",
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


def normalize_judge_label(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    normalized = normalized.replace("_", " ")
    normalized = " ".join(normalized.split())
    return _LABEL_ALIASES.get(normalized, "parse_failed")


def _normalize_confidence(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in CONFIDENCE_BUCKETS:
        return normalized
    return "low"


def _normalize_flags(value: Any, *, parse_failed: bool) -> list[str]:
    if value is None:
        flags: list[str] = []
    elif isinstance(value, str):
        flags = [value]
    else:
        flags = [str(flag) for flag in value]

    normalized = sorted(
        {
            _normalize_key(flag)
            for flag in flags
            if _normalize_key(flag) in PROTOCOL_FLAGS
        }
    )
    if parse_failed and "parse_failure" not in normalized:
        normalized.append("parse_failure")
    return sorted(normalized)


@dataclass(frozen=True)
class JudgeWeakEvidenceRecord:
    judgment_id: str
    item_id: str
    pair_id: str
    judge_model_snapshot: str
    prompt_hash: str
    rubric_version: str
    rubric_paraphrase_id: str
    order_swap: bool
    duplicate_index: int
    normalized_label: str
    confidence_bucket: str
    flags: tuple[str, ...]
    parse_status: str
    raw_response_stored: bool
    input_token_count: int
    output_token_count: int
    allowed_claim_level: str = ALLOWED_CLAIM_LEVEL
    claim_status: str = CLAIM_STATUS
    counts_as_human_or_external_gold: bool = False
    measurement_validation_claim: bool = False

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> JudgeWeakEvidenceRecord:
        _reject_raw_response_payload(payload)
        data = dict(payload)

        label_source = data.get("normalized_label")
        if label_source is None:
            label_source = data.get("label")
        normalized_label = normalize_judge_label(label_source)

        parse_status = str(data.get("parse_status") or "parsed").strip().lower()
        if normalized_label == "parse_failed" or parse_status == "parse_failed":
            normalized_label = "parse_failed"
            parse_status = "parse_failed"
        elif parse_status != "parsed":
            parse_status = "parse_failed"
            normalized_label = "parse_failed"

        if data.get("counts_as_human_or_external_gold") is True:
            raise ValueError("counts_as_human_or_external_gold must be false")
        if data.get("human_external_gold_label") is True:
            raise ValueError("human_external_gold_label must be false")
        if data.get("measurement_validation_claim") is True:
            raise ValueError("measurement_validation_claim must be false")

        raw_response_stored = data.get("raw_response_stored", False)
        if raw_response_stored is not False:
            raise ValueError("raw_response_stored must be false")

        flags = _normalize_flags(
            data.get("flags", []),
            parse_failed=parse_status == "parse_failed",
        )

        return cls(
            judgment_id=str(data.get("judgment_id", "")),
            item_id=str(data.get("item_id", "")),
            pair_id=str(data.get("pair_id", "")),
            judge_model_snapshot=str(data.get("judge_model_snapshot", "")),
            prompt_hash=str(data.get("prompt_hash", "")),
            rubric_version=str(data.get("rubric_version", "weak_evidence_v1")),
            rubric_paraphrase_id=str(data.get("rubric_paraphrase_id", "")),
            order_swap=bool(data.get("order_swap", False)),
            duplicate_index=int(data.get("duplicate_index", 0)),
            normalized_label=normalized_label,
            confidence_bucket=_normalize_confidence(data.get("confidence_bucket")),
            flags=tuple(flags),
            parse_status=parse_status,
            raw_response_stored=False,
            input_token_count=max(0, int(data.get("input_token_count", 0))),
            output_token_count=max(0, int(data.get("output_token_count", 0))),
            allowed_claim_level=ALLOWED_CLAIM_LEVEL,
            claim_status=CLAIM_STATUS,
            counts_as_human_or_external_gold=False,
            measurement_validation_claim=False,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["flags"] = list(self.flags)
        return payload


def parse_judge_output(payload: Mapping[str, Any]) -> JudgeWeakEvidenceRecord:
    return JudgeWeakEvidenceRecord.from_dict(payload)


def _agreement(labels: Iterable[str]) -> bool:
    filtered = [label for label in labels if label != "parse_failed"]
    if len(filtered) <= 1:
        return True
    return len(set(filtered)) == 1


def _ratio(values: list[bool]) -> float:
    if not values:
        return 1.0
    return sum(1 for value in values if value) / len(values)


def _duplicate_agreement(records: list[JudgeWeakEvidenceRecord]) -> float:
    groups: dict[tuple[str, str, bool], list[str]] = defaultdict(list)
    for record in records:
        groups[(record.item_id, record.rubric_paraphrase_id, record.order_swap)].append(
            record.normalized_label
        )
    checks = [_agreement(labels) for labels in groups.values() if len(labels) > 1]
    return _ratio(checks)


def _order_swap_agreement(records: list[JudgeWeakEvidenceRecord]) -> float:
    by_item_and_rubric: dict[tuple[str, str], dict[bool, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for record in records:
        by_item_and_rubric[(record.item_id, record.rubric_paraphrase_id)][
            record.order_swap
        ].append(record.normalized_label)

    checks: list[bool] = []
    for order_groups in by_item_and_rubric.values():
        if True not in order_groups or False not in order_groups:
            continue
        left_label = Counter(
            label for label in order_groups[False] if label != "parse_failed"
        ).most_common(1)
        swapped_label = Counter(
            label for label in order_groups[True] if label != "parse_failed"
        ).most_common(1)
        if not left_label or not swapped_label:
            checks.append(False)
        else:
            checks.append(left_label[0][0] == swapped_label[0][0])
    return _ratio(checks)


def _rubric_paraphrase_agreement(records: list[JudgeWeakEvidenceRecord]) -> float:
    by_item: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        if record.order_swap:
            continue
        by_item[record.item_id][record.rubric_paraphrase_id].append(record.normalized_label)

    checks: list[bool] = []
    for rubric_groups in by_item.values():
        if len(rubric_groups) <= 1:
            continue
        labels = []
        for values in rubric_groups.values():
            common = Counter(label for label in values if label != "parse_failed").most_common(1)
            if common:
                labels.append(common[0][0])
            else:
                labels.append("parse_failed")
        checks.append(_agreement(labels))
    return _ratio(checks)


def evaluate_judge_claim_gate(
    records: Iterable[JudgeWeakEvidenceRecord | Mapping[str, Any]],
) -> dict[str, Any]:
    normalized_records = [
        record
        if isinstance(record, JudgeWeakEvidenceRecord)
        else JudgeWeakEvidenceRecord.from_dict(record)
        for record in records
    ]
    if not normalized_records:
        parse_failure_rate = 1.0
    else:
        parse_failure_count = sum(
            1
            for record in normalized_records
            if record.parse_status == "parse_failed"
            or record.normalized_label == "parse_failed"
        )
        parse_failure_rate = parse_failure_count / len(normalized_records)

    duplicate_agreement = _duplicate_agreement(normalized_records)
    order_swap_agreement = _order_swap_agreement(normalized_records)
    rubric_paraphrase_agreement = _rubric_paraphrase_agreement(normalized_records)

    reason_codes: list[str] = []
    if parse_failure_rate > PARSE_FAILURE_RATE_MAX:
        reason_codes.append("parse_failure_rate_above_threshold")
    if order_swap_agreement < ORDER_SWAP_AGREEMENT_MIN:
        reason_codes.append("order_swap_agreement_below_threshold")
    if duplicate_agreement < DUPLICATE_AGREEMENT_MIN:
        reason_codes.append("duplicate_agreement_below_threshold")
    if rubric_paraphrase_agreement < RUBRIC_PARAPHRASE_AGREEMENT_MIN:
        reason_codes.append("rubric_paraphrase_agreement_below_threshold")

    if reason_codes:
        final_gate_status = "downgraded_to_ambiguous"
        aggregate_label_status = "ambiguous_suppressed"
        allowed_claims: list[str] = []
    else:
        final_gate_status = "weak_evidence_candidate_ready"
        aggregate_label_status = "weak_model_adjudicated_candidate"
        allowed_claims = [ALLOWED_CLAIM_LEVEL]

    input_counts = [record.input_token_count for record in normalized_records]
    output_counts = [record.output_token_count for record in normalized_records]

    return {
        "claim_status": CLAIM_STATUS,
        "allowed_claims": allowed_claims,
        "allowed_claim_level": ALLOWED_CLAIM_LEVEL,
        "final_gate_status": final_gate_status,
        "aggregate_label_status": aggregate_label_status,
        "reason_codes": sorted(reason_codes),
        "parse_failure_rate": parse_failure_rate,
        "parse_failure_rate_max": PARSE_FAILURE_RATE_MAX,
        "order_swap_agreement": order_swap_agreement,
        "order_swap_agreement_min": ORDER_SWAP_AGREEMENT_MIN,
        "duplicate_agreement": duplicate_agreement,
        "duplicate_agreement_min": DUPLICATE_AGREEMENT_MIN,
        "rubric_paraphrase_agreement": rubric_paraphrase_agreement,
        "rubric_paraphrase_agreement_min": RUBRIC_PARAPHRASE_AGREEMENT_MIN,
        "length_aware_reporting": True,
        "input_token_count_min": min(input_counts, default=0),
        "input_token_count_max": max(input_counts, default=0),
        "output_token_count_min": min(output_counts, default=0),
        "output_token_count_max": max(output_counts, default=0),
        "measurement_validation_claim": False,
        "human_external_gold_label": False,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "denied_claims": list(DENIED_CLAIMS),
    }
