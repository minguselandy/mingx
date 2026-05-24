from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from collections import Counter
from collections import defaultdict
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence
from urllib import error
from urllib import request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cps.benchmarks.common import read_jsonl
from cps.benchmarks.common import write_json
from cps.benchmarks.common import write_jsonl
from cps.experiments.artifacts import stable_hash
from cps.experiments.live_api_evidence_package_factory import _env_values
from cps.experiments.live_api_evidence_package_factory import _select_live_api_client_config


APPROVAL_TOKEN = "APPROVE_LIVE_API_POST_5_REPROJECTION_WITNESS=true"
CONFIG_PATH = Path("configs/post_lapi/reprojection_witness_config.yaml")
SCHEMA_PATH = Path("schemas/post_lapi_reprojection_witness.schema.json")
POST4_RECORDS_PATH = Path("artifacts/experiments/post_lapi_sufficiency_abstention/sufficiency_records.jsonl")
POST4_AGGREGATE_PATH = Path("artifacts/experiments/post_lapi_sufficiency_abstention/aggregate_report.json")
POST4_MANIFEST_PATH = Path("artifacts/experiments/post_lapi_sufficiency_abstention/run_manifest.json")
SOURCE_POOLS_PATH = Path("artifacts/benchmarks/hotpotqa_candidate_pools.jsonl")
PROMPT_PATH = Path("prompts/reprojection/sufficiency_abstention_v1.md")
OUTPUT_DIR = Path("artifacts/experiments/post_lapi_reprojection_witness")
DEFAULT_RUN_ID = "post_lapi_reprojection_witness_live_pilot_v1"

CLAIM_LEVEL = "operational_utility_only/no_claim_upgrade"
DIAGNOSTIC_CLAIM_LEVEL = "operational_reprojection_witness"
ENDPOINT_FAMILY = "dashscope_openai_compatible_chat_completions"
THINKING_MODE = "disabled"
DECODING_POLICY = {"temperature": 0, "top_p": 1}
TOKEN_ACCOUNTING = "provider_usage_or_character_estimate_with_post4_baseline"
ELIGIBLE_REGIMES = {"sufficient_dropped", "insufficient_and_answered"}
ALLOWED_LABELS = {"support", "insufficient", "contradict", "uncertain", "parse_failed"}
CONFIDENCE_BUCKETS = {"low", "medium", "high"}
MISSING_EVIDENCE_TYPES = {
    "entity",
    "temporal",
    "bridge_fact",
    "qualifier",
    "provenance",
    "multi_hop_prerequisite",
    "unknown",
}
ALLOWED_TRIGGERS = {
    "sufficient_dropped",
    "insufficient_and_answered",
    "unknown_due_to_missing_context",
    "hallucination_risk",
}
DENIED_CLAIMS = [
    "validated_repair",
    "truth_correction_guarantee",
    "metric_bridge_support",
    "selector_superiority",
    "route_5_unlock",
    "route_8_unlock",
]
ALLOWED_CLAIMS = [
    "operational_reprojection_witness",
    "omitted_evidence_operational_diagnostic",
    "replayable_artifact_evidence",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return payload


def _normalize_key(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    for char in (" ", "-", "/"):
        normalized = normalized.replace(char, "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized


def _target_answer(target: Any) -> str:
    if isinstance(target, Mapping):
        return str(target.get("label") or target.get("answer") or target)
    return str(target or "")


def _packet_hash(packet: Mapping[str, Any]) -> str:
    existing = str(packet.get("hash") or "").strip()
    return existing or _sha256_text(str(packet.get("content") or ""))


def _packet_id(packet: Mapping[str, Any]) -> str:
    return str(packet.get("packet_id") or _packet_hash(packet))


def _packet_ref(packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "packet_hash": _packet_hash(packet),
        "packet_id": _packet_id(packet),
        "source_doc_id_hash": _sha256_text(str(packet.get("source_doc_id") or "")),
        "support_label": str(packet.get("gold_support_label") or ""),
        "token_cost": int(packet.get("token_cost") or 0),
    }


def _packets_by_label(packets: Sequence[Mapping[str, Any]], label: str) -> list[Mapping[str, Any]]:
    return [packet for packet in packets if str(packet.get("gold_support_label") or "") == label]


def _unique_packets(packets: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    seen: set[str] = set()
    unique: list[Mapping[str, Any]] = []
    for packet in packets:
        packet_hash = _packet_hash(packet)
        if packet_hash in seen:
            continue
        seen.add(packet_hash)
        unique.append(packet)
    return unique


def _context_text(packets: Sequence[Mapping[str, Any]]) -> str:
    return "\n".join(f"- {packet.get('content', '')}" for packet in packets)


def _estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def _sum_packet_tokens(packets: Sequence[Mapping[str, Any]]) -> int:
    estimated = sum(int(packet.get("token_cost") or 0) for packet in packets)
    return estimated or _estimate_tokens(_context_text(packets))


def _normalize_label(value: Any) -> str:
    label = _normalize_key(value)
    aliases = {
        "supports": "support",
        "supported": "support",
        "supporting": "support",
        "not_enough_information": "insufficient",
        "not_enough_info": "insufficient",
        "contradicts": "contradict",
        "contradiction": "contradict",
        "unknown": "uncertain",
        "ambiguous": "uncertain",
    }
    label = aliases.get(label, label)
    return label if label in ALLOWED_LABELS else "parse_failed"


def _normalize_confidence(value: Any) -> str:
    bucket = _normalize_key(value)
    return bucket if bucket in CONFIDENCE_BUCKETS else "low"


def _normalize_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return default


def _normalize_missing_types(value: Any) -> list[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list | tuple):
        values = [str(item) for item in value]
    else:
        values = []
    normalized = sorted({_normalize_key(item) for item in values if _normalize_key(item) in MISSING_EVIDENCE_TYPES})
    return normalized or ["unknown"]


def _normalize_trigger(value: Any, *, judge_label: str, projected_sufficient: bool, answer_emitted: bool) -> str:
    trigger = _normalize_key(value)
    if trigger in ALLOWED_TRIGGERS:
        return trigger
    if projected_sufficient and not answer_emitted:
        return "sufficient_dropped"
    if not projected_sufficient and answer_emitted and judge_label == "contradict":
        return "hallucination_risk"
    if not projected_sufficient and answer_emitted:
        return "insufficient_and_answered"
    return "unknown_due_to_missing_context"


def _normalized_output_from_post4(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "abstain_recommended": bool(record.get("abstain_recommended")),
        "confidence_bucket": str(record.get("confidence_bucket") or "low"),
        "judge_label": str(record.get("judge_label") or "parse_failed"),
        "missing_evidence_types": list(record.get("missing_evidence_types") or [record.get("missing_evidence_type") or "unknown"]),
        "projected_evidence_sufficient": bool(record.get("projected_evidence_sufficient")),
        "trigger_label": str(record.get("trigger_label") or ""),
    }


def _extract_json_object(content: str) -> Mapping[str, Any] | None:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end < start:
            return None
        try:
            parsed = json.loads(stripped[start : end + 1])
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, Mapping) else None


def _usage_counts(usage: Mapping[str, Any], prompt_estimate: int, output_estimate: int) -> tuple[int, int, bool]:
    prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    output_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
    actual = prompt_tokens is not None or output_tokens is not None
    try:
        input_count = int(prompt_tokens) if prompt_tokens is not None else prompt_estimate
    except (TypeError, ValueError):
        input_count = prompt_estimate
    try:
        output_count = int(output_tokens) if output_tokens is not None else output_estimate
    except (TypeError, ValueError):
        output_count = output_estimate
    return max(0, input_count), max(0, output_count), actual


class DashScopeWitnessClient:
    def __init__(self, *, api_key: str, base_url: str, model_id: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id

    def classify(self, *, messages: Sequence[Mapping[str, str]], timeout_seconds: int) -> dict[str, Any]:
        payload = {
            "enable_thinking": False,
            "max_tokens": 320,
            "messages": [dict(message) for message in messages],
            "model": self.model_id,
            "n": 1,
            "response_format": {"type": "json_object"},
            "stream": False,
            "temperature": 0,
        }
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        http_request = request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        started = time.perf_counter()
        try:
            with request.urlopen(http_request, timeout=timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise RuntimeError(f"dashscope_live_api_http_{exc.code}") from exc
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("dashscope_live_api_transport_or_parse_failure") from exc
        latency_ms = int(round((time.perf_counter() - started) * 1000))
        choice = (response_payload.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = str(message.get("content") or "")
        parsed = _extract_json_object(content)
        prompt_text = "\n".join(str(message["content"]) for message in messages)
        input_count, output_count, usage_actual = _usage_counts(
            response_payload.get("usage") or {},
            _estimate_tokens(prompt_text),
            _estimate_tokens(content) if content else 0,
        )
        if parsed is None:
            parsed = {
                "abstain_recommended": True,
                "confidence_bucket": "low",
                "judge_label": "parse_failed",
                "missing_evidence_types": ["unknown"],
                "projected_evidence_sufficient": False,
                "trigger_label": "unknown_due_to_missing_context",
            }
            parse_status = "parse_failed"
        else:
            parse_status = "parsed"
        return {
            "input_token_count": input_count,
            "latency_ms": latency_ms,
            "model_snapshot": str(response_payload.get("model") or self.model_id),
            "output_token_count": output_count,
            "parsed": dict(parsed),
            "parse_status": parse_status,
            "usage_actual": usage_actual,
        }


def _classify_with_retries(
    client: DashScopeWitnessClient,
    *,
    messages: Sequence[Mapping[str, str]],
    timeout_seconds: int,
    attempts: int = 3,
) -> dict[str, Any]:
    last_reason = "dashscope_live_api_unknown_failure"
    for attempt_index in range(attempts):
        try:
            return client.classify(messages=messages, timeout_seconds=timeout_seconds)
        except RuntimeError as exc:
            last_reason = str(exc)
            if attempt_index + 1 >= attempts:
                break
            time.sleep(min(8, 2 ** attempt_index))
    raise RuntimeError(last_reason)


def _write_blocker(output_dir: Path, *, reason: str, live_api_call_count: int) -> dict[str, Any]:
    report = {
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "live_api_call_count": live_api_call_count,
        "raw_response_stored": False,
        "reason": reason,
        "route_5_locked": True,
        "route_8_locked": True,
        "schema_version": "post_lapi_reprojection_witness_blocker_v1",
        "terminal_status": "BLOCKED",
    }
    write_json(output_dir / "blocker_report.json", report)
    return report


def _source_row_map(source_rows: Sequence[Mapping[str, Any]]) -> dict[int, Mapping[str, Any]]:
    return {index: row for index, row in enumerate(source_rows)}


def _select_before_packets(record: Mapping[str, Any], source_row: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    packets = list((source_row.get("candidate_pool") or {}).get("packets") or [])
    packets_by_hash = {_packet_hash(packet): packet for packet in packets}
    selected: list[Mapping[str, Any]] = []
    missing_hashes: list[str] = []
    for packet_hash in list(record.get("projected_packet_hashes") or []):
        packet = packets_by_hash.get(str(packet_hash))
        if packet is None:
            missing_hashes.append(str(packet_hash))
        else:
            selected.append(packet)
    if missing_hashes:
        raise ValueError(f"{record.get('item_id')}: projected packet hashes not found in source row")
    return selected


def _select_after_packets(
    *,
    regime_label: str,
    before_packets: Sequence[Mapping[str, Any]],
    source_row: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], str, str]:
    packets = list((source_row.get("candidate_pool") or {}).get("packets") or [])
    support_packets = _packets_by_label(packets, "gold_supporting")
    if regime_label == "insufficient_and_answered":
        after_packets = _unique_packets(list(support_packets) + list(before_packets))
        return after_packets, "restore_excluded_evidence_span", "pair_aware_local_search_operational_only"
    after_packets = _unique_packets(list(support_packets) + list(before_packets))
    before_hashes = {_packet_hash(packet) for packet in before_packets}
    added_support = [packet for packet in support_packets if _packet_hash(packet) not in before_hashes]
    if added_support:
        return after_packets, "restore_excluded_evidence_span", "pair_aware_local_search_operational_only"
    return after_packets, "switch_selector_to_pair_aware_local_search", "pair_aware_local_search_operational_only"


def _context_diff(before_packets: Sequence[Mapping[str, Any]], after_packets: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    before_hashes = [_packet_hash(packet) for packet in before_packets]
    after_hashes = [_packet_hash(packet) for packet in after_packets]
    before_set = set(before_hashes)
    after_set = set(after_hashes)
    return {
        "added_packet_hashes": sorted(after_set - before_set),
        "before_packet_hashes": before_hashes,
        "after_packet_hashes": after_hashes,
        "removed_packet_hashes": sorted(before_set - after_set),
        "retained_packet_hashes": sorted(before_set & after_set),
    }


def _build_eligible_cases(
    *,
    post4_records: Sequence[Mapping[str, Any]],
    source_rows: Sequence[Mapping[str, Any]],
    max_cases: int,
) -> list[dict[str, Any]]:
    if max_cases < 20 or max_cases > 30:
        raise ValueError("POST-5 pilot max_cases must be between 20 and 30 inclusive")
    by_index = _source_row_map(source_rows)
    cases: list[dict[str, Any]] = []
    for record in post4_records:
        regime_label = str(record.get("regime_label") or "")
        if regime_label not in ELIGIBLE_REGIMES:
            continue
        if str(record.get("confidence_bucket") or "") != "high":
            continue
        if str(record.get("parse_status") or "") != "parsed":
            continue
        if bool(record.get("raw_response_stored")):
            continue
        source_index = int(record.get("source_row_index"))
        source_row = by_index.get(source_index)
        if source_row is None:
            continue
        if stable_hash(source_row) != str(record.get("source_row_hash") or ""):
            continue
        before_packets = _select_before_packets(record, source_row)
        after_packets, intervention_type, selector_after = _select_after_packets(
            regime_label=regime_label,
            before_packets=before_packets,
            source_row=source_row,
        )
        if not before_packets or not after_packets:
            continue
        before_text = _context_text(before_packets)
        after_text = _context_text(after_packets)
        diff = _context_diff(before_packets, after_packets)
        before_output = _normalized_output_from_post4(record)
        source_instance_hash = str(record.get("source_instance_hash") or _sha256_text(str(source_row.get("instance_id") or "")))
        claim_hash = str(record.get("claim_hash") or _sha256_text(str(source_row.get("query") or "")))
        cases.append(
            {
                "answer": _target_answer(source_row.get("target")),
                "before_context_hash": _sha256_text(before_text),
                "before_input_token_count": int(record.get("input_token_count") or 0),
                "before_latency_ms": int(record.get("latency_ms") or 0),
                "before_output": before_output,
                "before_output_hash": stable_hash(before_output),
                "before_output_token_count": int(record.get("output_token_count") or 0),
                "before_packet_refs": [_packet_ref(packet) for packet in before_packets],
                "before_packet_count": len(before_packets),
                "candidate_pool_hash": stable_hash(
                    [_packet_ref(packet) for packet in list((source_row.get("candidate_pool") or {}).get("packets") or [])]
                ),
                "case_id": str(record.get("item_id") or record.get("record_id")),
                "claim_hash": claim_hash,
                "context_diff": diff,
                "context_diff_hash": stable_hash(diff),
                "intervention_type": intervention_type,
                "missing_evidence_type": str(record.get("missing_evidence_type") or "unknown"),
                "missing_evidence_types": list(record.get("missing_evidence_types") or [record.get("missing_evidence_type") or "unknown"]),
                "original_budget_tokens": _sum_packet_tokens(before_packets),
                "post4_record_id": str(record.get("record_id") or ""),
                "question": str(source_row.get("query") or ""),
                "regime_label": regime_label,
                "reprojected_budget_tokens": _sum_packet_tokens(after_packets),
                "restored_evidence_hash": _sha256_text(after_text),
                "after_packet_refs": [_packet_ref(packet) for packet in after_packets],
                "after_packet_count": len(after_packets),
                "after_text": after_text,
                "replay_artifact_complete": True,
                "selector_after": selector_after,
                "selector_before": "post4_projected_evidence_selection",
                "source_instance_hash": source_instance_hash,
                "source_row_hash": str(record.get("source_row_hash") or ""),
                "source_row_index": source_index,
                "trigger_label": str(record.get("trigger_label") or ""),
            }
        )
        if len(cases) >= max_cases:
            break
    return cases


def _messages_for_case(case: Mapping[str, Any]) -> tuple[list[dict[str, str]], str]:
    base_prompt = (ROOT / PROMPT_PATH).read_text(encoding="utf-8").strip()
    system_prompt = "\n".join(
        [
            base_prompt,
            "",
            "POST-5 reprojection witness mode: judge only the reprojected evidence below.",
            "Return only one minified JSON object. Use these keys: judge_label, projected_evidence_sufficient, abstain_recommended, missing_evidence_types, confidence_bucket, trigger_label.",
            "Allowed judge_label values: support, insufficient, contradict, uncertain, parse_failed.",
            "Allowed confidence_bucket values: low, medium, high.",
            "Do not include rationale, hidden reasoning, provider metadata, markdown fences, or any raw response body.",
        ]
    )
    user_prompt = "\n".join(
        [
            "Assess whether the reprojected evidence is sufficient for the candidate answer and whether abstention is recommended.",
            "This is a model-adjudicated candidate operational diagnostic only.",
            "",
            f"Question: {case['question']}",
            f"Candidate answer: {case['answer']}",
            f"POST-4 trigger regime: {case['regime_label']}",
            f"POST-5 intervention: {case['intervention_type']}",
            "",
            "Reprojected evidence:",
            str(case["after_text"]),
            "",
            "Normalize missing_evidence_types to any of: entity, temporal, bridge_fact, qualifier, provenance, multi_hop_prerequisite, unknown.",
        ]
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ], _sha256_text(system_prompt)


def _after_output(result: Mapping[str, Any], *, answer_emitted: bool) -> tuple[dict[str, Any], str]:
    parsed = dict(result["parsed"])
    judge_label = _normalize_label(parsed.get("judge_label") or parsed.get("label"))
    confidence_bucket = _normalize_confidence(parsed.get("confidence_bucket"))
    projected_sufficient = _normalize_bool(
        parsed.get("projected_evidence_sufficient"),
        default=judge_label == "support",
    )
    abstain_recommended = _normalize_bool(
        parsed.get("abstain_recommended"),
        default=not projected_sufficient,
    )
    missing_types = _normalize_missing_types(parsed.get("missing_evidence_types") or parsed.get("missing_evidence_type"))
    trigger_label = _normalize_trigger(
        parsed.get("trigger_label"),
        judge_label=judge_label,
        projected_sufficient=projected_sufficient,
        answer_emitted=answer_emitted,
    )
    parse_status = str(result["parse_status"])
    if judge_label == "parse_failed":
        parse_status = "parse_failed"
        abstain_recommended = True
    output = {
        "abstain_recommended": abstain_recommended,
        "confidence_bucket": confidence_bucket,
        "judge_label": judge_label,
        "missing_evidence_types": missing_types,
        "projected_evidence_sufficient": projected_sufficient,
        "trigger_label": trigger_label,
    }
    return output, parse_status


def _repair_status(case: Mapping[str, Any], after_output: Mapping[str, Any], *, control_mismatch: bool) -> str:
    before = dict(case["before_output"])
    before_sufficient = bool(before.get("projected_evidence_sufficient"))
    before_abstain = bool(before.get("abstain_recommended"))
    after_sufficient = bool(after_output.get("projected_evidence_sufficient")) and after_output.get("judge_label") == "support"
    after_abstain = bool(after_output.get("abstain_recommended"))
    label_changed = before.get("judge_label") != after_output.get("judge_label")
    if control_mismatch:
        return "not_comparable_control_mismatch"
    if after_sufficient and not after_abstain and (label_changed or before_abstain or not before_sufficient):
        return "reprojection_candidate"
    if case["before_context_hash"] == case["restored_evidence_hash"] and not label_changed:
        return "no_reprojection_needed"
    return "ambiguous_suppressed"


def _witness_record(
    *,
    case: Mapping[str, Any],
    result: Mapping[str, Any],
    after_output: Mapping[str, Any],
    parse_status: str,
    prompt_hash: str,
    request_payload_hash: str,
    client_config: Mapping[str, Any],
    call_count: int,
) -> dict[str, Any]:
    after_output_hash = stable_hash(after_output)
    before_output = dict(case["before_output"])
    before_model = str(case.get("post4_model_snapshot") or "")
    after_model = str(result.get("model_snapshot") or client_config.get("model_id") or "")
    endpoint = str(client_config["base_url"])
    control_mismatch = bool(before_model and before_model != after_model)
    repair_status = _repair_status(case, after_output, control_mismatch=control_mismatch)
    before_tokens = int(case["before_input_token_count"]) + int(case["before_output_token_count"])
    after_tokens = int(result["input_token_count"]) + int(result["output_token_count"])
    label_changed = before_output.get("judge_label") != after_output.get("judge_label")
    abstain_to_support = bool(
        before_output.get("abstain_recommended")
        and after_output.get("judge_label") == "support"
        and not after_output.get("abstain_recommended")
    )
    unsupported_to_supported = bool(
        not before_output.get("projected_evidence_sufficient")
        and after_output.get("judge_label") == "support"
        and after_output.get("projected_evidence_sufficient")
    )
    claim_entry = {
        "allowed_claims": ALLOWED_CLAIMS,
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade": False,
        "current_claim_level": CLAIM_LEVEL,
        "denied_claims": DENIED_CLAIMS,
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
    }
    return {
        "abstain_to_support": abstain_to_support,
        "after_input_token_count": int(result["input_token_count"]),
        "after_latency_ms": int(result["latency_ms"]),
        "after_output_hash": after_output_hash,
        "after_output_token_count": int(result["output_token_count"]),
        "after_packet_count": int(case["after_packet_count"]),
        "after_packet_refs": list(case["after_packet_refs"]),
        "after_sufficiency_metadata": after_output,
        "allowed_claims": ALLOWED_CLAIMS,
        "before_context_hash": str(case["before_context_hash"]),
        "before_input_token_count": int(case["before_input_token_count"]),
        "before_latency_ms": int(case["before_latency_ms"]),
        "before_output_hash": str(case["before_output_hash"]),
        "before_output_token_count": int(case["before_output_token_count"]),
        "before_packet_count": int(case["before_packet_count"]),
        "before_packet_refs": list(case["before_packet_refs"]),
        "before_sufficiency_metadata": before_output,
        "budget_delta": int(case["reprojected_budget_tokens"]) - int(case["original_budget_tokens"]),
        "candidate_operational_evidence_only": True,
        "candidate_pool_hash": str(case["candidate_pool_hash"]),
        "case_id": str(case["case_id"]),
        "claim_hash": str(case["claim_hash"]),
        "claim_ledger_entry": claim_entry,
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "context_diff_hash": str(case["context_diff_hash"]),
        "control_mismatch": control_mismatch,
        "controlled_replay": {
            "decoding_policy": DECODING_POLICY,
            "downstream_prompt_hash": _sha256_file(ROOT / PROMPT_PATH),
            "endpoint": endpoint,
            "hold_fixed": [
                "downstream_prompt_hash",
                "model_snapshot",
                "endpoint",
                "thinking_mode",
                "decoding_policy",
                "token_budget_accounting",
            ],
            "model_snapshot": after_model,
            "thinking_mode": THINKING_MODE,
            "token_budget_accounting": TOKEN_ACCOUNTING,
        },
        "cost_delta_tokens": after_tokens - before_tokens,
        "decoding_policy": DECODING_POLICY,
        "denied_claims": DENIED_CLAIMS,
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "downstream_prompt_hash": _sha256_file(ROOT / PROMPT_PATH),
        "downstream_prompt_template_hash": _sha256_file(ROOT / PROMPT_PATH),
        "endpoint": endpoint,
        "endpoint_family": ENDPOINT_FAMILY,
        "human_external_gold_label": False,
        "intervention_type": str(case["intervention_type"]),
        "judge_prompt_hash": prompt_hash,
        "label_change": label_changed,
        "latency_delta_ms": int(result["latency_ms"]) - int(case["before_latency_ms"]),
        "live_api_call_ordinal": call_count,
        "live_api_call_performed": True,
        "measurement_validation_claim": False,
        "metric_bridge_support": False,
        "model_adjudicated_candidate_operational_evidence_only": True,
        "model_snapshot": after_model,
        "original_budget_tokens": int(case["original_budget_tokens"]),
        "parse_status": parse_status,
        "position_aware_replay_manifest": {
            "after_packet_hashes": [row["packet_hash"] for row in list(case["after_packet_refs"])],
            "before_packet_hashes": [row["packet_hash"] for row in list(case["before_packet_refs"])],
            "enabled": True,
            "position_policy_hash": stable_hash(
                {
                    "after": [row["packet_hash"] for row in list(case["after_packet_refs"])],
                    "before": [row["packet_hash"] for row in list(case["before_packet_refs"])],
                    "policy": "post5_support_first_reprojection",
                }
            ),
        },
        "post4_record_id": str(case["post4_record_id"]),
        "raw_response_stored": False,
        "repair_status": repair_status,
        "replay_artifact_complete": True,
        "reprojected_budget_tokens": int(case["reprojected_budget_tokens"]),
        "request_payload_hash": request_payload_hash,
        "restored_evidence_hash": str(case["restored_evidence_hash"]),
        "route_5_locked": True,
        "route_8_locked": True,
        "schema_version": "post_lapi_reprojection_witness_record_v1",
        "selected_evidence_before_hash": str(case["before_context_hash"]),
        "selector_after": str(case["selector_after"]),
        "selector_before": str(case["selector_before"]),
        "selector_superiority_claim": False,
        "source_instance_hash": str(case["source_instance_hash"]),
        "source_row_hash": str(case["source_row_hash"]),
        "source_row_index": int(case["source_row_index"]),
        "thinking_mode": THINKING_MODE,
        "token_budget_accounting": TOKEN_ACCOUNTING,
        "token_budget_accounting_method": TOKEN_ACCOUNTING,
        "trigger_label": str(case["regime_label"]),
        "truth_correction_guarantee": False,
        "truth_validation_claim": False,
        "unsupported_to_supported": unsupported_to_supported,
        "usage_count_source": "provider_usage" if result.get("usage_actual") else "character_estimate",
        "validated_repair_claim": False,
        "witness_id": stable_hash(
            {
                "after_output_hash": after_output_hash,
                "before_output_hash": case["before_output_hash"],
                "case_id": case["case_id"],
                "context_diff_hash": case["context_diff_hash"],
                "intervention_type": case["intervention_type"],
            }
        ),
    }


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _quantile(values: Sequence[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * q)))
    return ordered[index]


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def _ledger_rows(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_regime: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        by_regime[str(record["trigger_label"])].append(record)
    for regime in sorted(by_regime):
        subset = by_regime[regime]
        total = len(subset)
        cost_deltas = [float(record["cost_delta_tokens"]) for record in subset]
        latency_deltas = [float(record["latency_delta_ms"]) for record in subset]
        rows.append(
            {
                "abstain_to_support_rate": round(_rate(sum(1 for record in subset if record["abstain_to_support"]), total), 6),
                "claim_gate_status": "reprojection_witness_candidate_ready",
                "cost_delta_tokens_mean": round(_mean(cost_deltas), 3),
                "label_change_rate": round(_rate(sum(1 for record in subset if record["label_change"]), total), 6),
                "latency_delta_ms_mean": round(_mean(latency_deltas), 3),
                "n_cases": total,
                "parse_failed_rate": round(_rate(sum(1 for record in subset if record["parse_status"] == "parse_failed"), total), 6),
                "position_sensitivity_rate": round(
                    _rate(
                        sum(
                            1
                            for record in subset
                            if record["before_output_hash"] != record["after_output_hash"]
                            or record["selected_evidence_before_hash"] != record["restored_evidence_hash"]
                        ),
                        total,
                    ),
                    6,
                ),
                "regime": regime,
                "repair_rate": round(_rate(sum(1 for record in subset if record["repair_status"] == "reprojection_candidate"), total), 6),
                "unsupported_to_supported_rate": round(
                    _rate(sum(1 for record in subset if record["unsupported_to_supported"]), total),
                    6,
                ),
            }
        )
    return rows


def _aggregate(records: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    total = len(records)
    label_changes = sum(1 for record in records if record["label_change"])
    repair_candidates = sum(1 for record in records if record["repair_status"] == "reprojection_candidate")
    abstain_to_support = sum(1 for record in records if record["abstain_to_support"])
    unsupported_to_supported = sum(1 for record in records if record["unsupported_to_supported"])
    parse_failed = sum(1 for record in records if record["parse_status"] == "parse_failed")
    cost_deltas = [float(record["cost_delta_tokens"]) for record in records]
    latency_deltas = [float(record["latency_delta_ms"]) for record in records]
    after_tokens = [float(record["after_input_token_count"] + record["after_output_token_count"]) for record in records]
    before_tokens = [float(record["before_input_token_count"] + record["before_output_token_count"]) for record in records]
    position_sensitive = sum(
        1
        for record in records
        if record["before_output_hash"] != record["after_output_hash"]
        or record["selected_evidence_before_hash"] != record["restored_evidence_hash"]
    )
    ledger = _ledger_rows(records)
    gate_ready = (
        20 <= total <= 30
        and parse_failed == 0
        and all(record["raw_response_stored"] is False for record in records)
        and all(record["route_5_locked"] is True and record["route_8_locked"] is True for record in records)
        and all(record["claim_upgrade_introduced"] is False for record in records)
    )
    aggregate = {
        "abstain_to_support_rate": _rate(abstain_to_support, total),
        "allowed_claims_after_gate": ALLOWED_CLAIMS,
        "candidate_operational_evidence_only": True,
        "case_count": total,
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "cost_delta_summary": {
            "after_tokens_total": int(sum(after_tokens)),
            "before_tokens_total": int(sum(before_tokens)),
            "delta_tokens_mean": round(_mean(cost_deltas), 3),
            "delta_tokens_total": int(sum(cost_deltas)),
            "monetary_cost_status": "not_calculated_without_provider_pricing_config",
        },
        "denied_claims": DENIED_CLAIMS,
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "final_gate_status": "reprojection_witness_candidate_ready" if gate_ready else "downgraded_to_ambiguous",
        "label_change_rate": _rate(label_changes, total),
        "latency_delta_summary_ms": {
            "max": round(max(latency_deltas), 3) if latency_deltas else 0.0,
            "mean": round(_mean(latency_deltas), 3),
            "median": round(statistics.median(latency_deltas), 3) if latency_deltas else 0.0,
            "min": round(min(latency_deltas), 3) if latency_deltas else 0.0,
            "p95": round(_quantile(latency_deltas, 0.95), 3),
        },
        "live_api_call_count": total,
        "measurement_validation_claim": False,
        "parse_failed_rate": _rate(parse_failed, total),
        "position_sensitivity_rate": _rate(position_sensitive, total),
        "raw_response_stored": False,
        "regime_counts": dict(sorted(Counter(str(record["trigger_label"]) for record in records).items())),
        "repair_rate": _rate(repair_candidates, total),
        "route_5_locked": True,
        "route_8_locked": True,
        "schema_version": "post_lapi_reprojection_witness_aggregate_v1",
        "truth_correction_guarantee": False,
        "unsupported_to_supported_rate": _rate(unsupported_to_supported, total),
        "validated_repair_claim": False,
    }
    return aggregate, ledger


def _write_docs(
    *,
    aggregate: Mapping[str, Any],
    manifest: Mapping[str, Any],
    ledger: Sequence[Mapping[str, Any]],
    output_dir: Path,
) -> None:
    experiment_doc = ROOT / "docs/experiments/POST-LAPI-reprojection-witness-pilot.md"
    table_doc = ROOT / "docs/paper/post-lapi-reprojection-witness-table.md"
    cost = aggregate["cost_delta_summary"]
    latency = aggregate["latency_delta_summary_ms"]
    experiment_doc.write_text(
        "\n".join(
            [
                "# POST-LAPI Reprojection Witness Pilot",
                "",
                "Goal ID: POST-5-RUN / Reprojection witness pilot",
                f"Run ID: `{manifest['run_id']}`",
                f"Claim ceiling: `{CLAIM_LEVEL}`",
                "",
                "## Scope",
                "",
                "This owner-approved pilot ran a bounded DashScope-compatible reprojection witness pass over flagged POST-4 sufficiency and omitted-evidence cases. Outputs are model-adjudicated candidate operational evidence only. They are not validated repair, truth correction guarantees, metric bridge support, selector superiority, Route 5 unlock evidence, or Route 8 unlock evidence.",
                "",
                "## Run Metadata",
                "",
                f"- Eligible flagged cases: `{manifest['eligible_case_count']}`",
                f"- Live API call count: `{aggregate['live_api_call_count']}`",
                f"- Model snapshot: `{manifest['model_snapshot']}`",
                f"- Endpoint family: `{manifest['endpoint_family']}`",
                f"- Endpoint: `{manifest['endpoint']}`",
                f"- Raw API responses stored: `{str(aggregate['raw_response_stored']).lower()}`",
                f"- Route 5 locked: `{str(aggregate['route_5_locked']).lower()}`",
                f"- Route 8 locked: `{str(aggregate['route_8_locked']).lower()}`",
                f"- Claim upgrade introduced: `{str(aggregate['claim_upgrade_introduced']).lower()}`",
                f"- Gate status: `{aggregate['final_gate_status']}`",
                "",
                "## Cost And Latency Deltas",
                "",
                f"- Before tokens total: `{cost['before_tokens_total']}`",
                f"- After tokens total: `{cost['after_tokens_total']}`",
                f"- Delta tokens total: `{cost['delta_tokens_total']}`",
                f"- Delta tokens mean: `{cost['delta_tokens_mean']}`",
                f"- Monetary cost status: `{cost['monetary_cost_status']}`",
                f"- Mean latency delta ms: `{latency['mean']}`",
                f"- Median latency delta ms: `{latency['median']}`",
                f"- P95 latency delta ms: `{latency['p95']}`",
                "",
                "## Aggregate Metrics",
                "",
                f"- Repair candidate rate: `{aggregate['repair_rate']}`",
                f"- Label change rate: `{aggregate['label_change_rate']}`",
                f"- Abstain-to-support rate: `{aggregate['abstain_to_support_rate']}`",
                f"- Unsupported-to-supported rate: `{aggregate['unsupported_to_supported_rate']}`",
                f"- Position sensitivity rate: `{aggregate['position_sensitivity_rate']}`",
                f"- Parse failed rate: `{aggregate['parse_failed_rate']}`",
                "",
                "## Claim Boundary",
                "",
                "Allowed interpretation: operational reprojection witness, omitted-evidence operational diagnostic, and replayable artifact evidence. Denied interpretation: validated repair, truth correction guarantee, metric bridge support, selector superiority, or any route unlock.",
                "",
                "## Artifact Index",
                "",
                f"- `{(output_dir / 'witness_records.jsonl').as_posix()}`",
                f"- `{(output_dir / 'regime_ledger.json').as_posix()}`",
                f"- `{(output_dir / 'aggregate_report.json').as_posix()}`",
                f"- `{(output_dir / 'run_manifest.json').as_posix()}`",
                f"- `{(output_dir / 'claim_ledger.json').as_posix()}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# POST-LAPI Reprojection Witness Table",
        "",
        f"Status: POST-5-RUN pilot result under `{CLAIM_LEVEL}`",
        "",
        "These rows are model-adjudicated candidate operational diagnostics only. They do not support validated repair, truth correction guarantees, metric bridge support, selector superiority, Route 5 unlock, or Route 8 unlock.",
        "",
        "| Case class | n cases | repair rate | label change rate | abstain to support rate | unsupported to supported rate | cost delta | latency delta | position sensitivity rate | claim gate status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in ledger:
        lines.append(
            "| {regime} | {n_cases} | {repair_rate} | {label_change_rate} | {abstain_to_support_rate} | {unsupported_to_supported_rate} | {cost_delta_tokens_mean} | {latency_delta_ms_mean} | {position_sensitivity_rate} | {claim_gate_status} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Boundary Fields",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| live API call count | `{aggregate['live_api_call_count']}` |",
            f"| model snapshot | `{manifest['model_snapshot']}` |",
            f"| endpoint | `{manifest['endpoint']}` |",
            "| raw API responses stored | `false` |",
            f"| claim level | `{CLAIM_LEVEL}` |",
            f"| diagnostic claim level | `{DIAGNOSTIC_CLAIM_LEVEL}` |",
            "| output interpretation | model-adjudicated candidate operational evidence only |",
            "| Route 5 locked | `true` |",
            "| Route 8 locked | `true` |",
            "| claim upgrade introduced | `false` |",
        ]
    )
    table_doc.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_pilot(
    *,
    approval: str,
    max_cases: int,
    output_dir: Path,
    repo_root: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    if approval != APPROVAL_TOKEN:
        output_dir.mkdir(parents=True, exist_ok=True)
        return _write_blocker(
            output_dir,
            reason="missing_required_owner_approval_token",
            live_api_call_count=0,
        )
    config = _load_json(repo_root / CONFIG_PATH)
    if config.get("claim_level") != CLAIM_LEVEL:
        raise RuntimeError("claim_level_config_mismatch")
    if config.get("route_5_locked") is not True or config.get("route_8_locked") is not True:
        raise RuntimeError("route_lock_config_not_true")
    if config.get("raw_response_storage_allowed") is not False or config.get("raw_response_stored") is not False:
        raise RuntimeError("config_allows_raw_response_storage")

    output_dir.mkdir(parents=True, exist_ok=True)
    env = _env_values(repo_root)
    client_config = _select_live_api_client_config(env)
    if not client_config["available"]:
        return _write_blocker(
            output_dir,
            reason=str(client_config["blocked_reason"]),
            live_api_call_count=0,
        )

    post4_records = read_jsonl(repo_root / POST4_RECORDS_PATH)
    source_rows = read_jsonl(repo_root / SOURCE_POOLS_PATH)
    cases = _build_eligible_cases(
        post4_records=post4_records,
        source_rows=source_rows,
        max_cases=max_cases,
    )
    if len(cases) < 20:
        return _write_blocker(
            output_dir,
            reason=f"eligible_case_count_below_20:{len(cases)}",
            live_api_call_count=0,
        )

    post4_manifest = _load_json(repo_root / POST4_MANIFEST_PATH)
    for case in cases:
        case["post4_model_snapshot"] = str(post4_manifest.get("model_snapshot") or "")

    client = DashScopeWitnessClient(
        api_key=str(client_config["api_key"]),
        base_url=str(client_config["base_url"]),
        model_id=str(client_config["model_id"]),
    )
    run_started = _utc_now()
    records: list[dict[str, Any]] = []
    model_snapshots: set[str] = set()
    call_count = 0

    for index, case in enumerate(cases, start=1):
        messages, prompt_hash = _messages_for_case(case)
        request_payload_hash = _sha256_text(json.dumps(messages, ensure_ascii=True, sort_keys=True))
        try:
            result = _classify_with_retries(
                client,
                messages=messages,
                timeout_seconds=timeout_seconds,
            )
        except RuntimeError as exc:
            return _write_blocker(
                output_dir,
                reason=f"dashscope_live_api_call_failed:{exc}",
                live_api_call_count=call_count,
            )
        call_count += 1
        after_output, parse_status = _after_output(
            result,
            answer_emitted=True,
        )
        model_snapshots.add(str(result.get("model_snapshot") or client_config["model_id"]))
        records.append(
            _witness_record(
                case=case,
                result=result,
                after_output=after_output,
                parse_status=parse_status,
                prompt_hash=prompt_hash,
                request_payload_hash=request_payload_hash,
                client_config=client_config,
                call_count=call_count,
            )
        )
        if index % 10 == 0 or index == len(cases):
            print(f"post5_progress {index}/{len(cases)} calls completed", flush=True)

    aggregate, ledger = _aggregate(records)
    model_snapshot_value = ",".join(sorted(model_snapshots)) if model_snapshots else str(client_config["model_id"])
    manifest = {
        "api_key_source": str(client_config["api_key_source"]),
        "approval_gate_token_verified": True,
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "config_hash": _sha256_file(repo_root / CONFIG_PATH),
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "downstream_prompt_hash": _sha256_file(repo_root / PROMPT_PATH),
        "eligible_case_count": len(cases),
        "endpoint": str(client_config["base_url"]),
        "endpoint_family": ENDPOINT_FAMILY,
        "live_api_call_count": call_count,
        "live_api_call_performed": True,
        "max_cases": max_cases,
        "model_snapshot": model_snapshot_value,
        "post4_aggregate_hash": _sha256_file(repo_root / POST4_AGGREGATE_PATH),
        "post4_manifest_hash": _sha256_file(repo_root / POST4_MANIFEST_PATH),
        "post4_records_hash": _sha256_file(repo_root / POST4_RECORDS_PATH),
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "run_finished_at": _utc_now(),
        "run_id": DEFAULT_RUN_ID,
        "run_started_at": run_started,
        "schema_hash": _sha256_file(repo_root / SCHEMA_PATH),
        "schema_version": "post_lapi_reprojection_witness_run_manifest_v1",
        "source_cases": [
            {
                "case_id": record["case_id"],
                "claim_hash": record["claim_hash"],
                "context_diff_hash": record["context_diff_hash"],
                "post4_record_id": record["post4_record_id"],
                "source_instance_hash": record["source_instance_hash"],
                "source_row_hash": record["source_row_hash"],
                "source_row_index": record["source_row_index"],
                "trigger_label": record["trigger_label"],
                "witness_id": record["witness_id"],
            }
            for record in records
        ],
        "terminal_status": aggregate["final_gate_status"],
        "thinking_mode": THINKING_MODE,
        "token_budget_accounting": TOKEN_ACCOUNTING,
    }
    manifest["manifest_hash"] = stable_hash(manifest)
    claim_ledger = {
        "allowed_claims_after_gate": ALLOWED_CLAIMS,
        "candidate_operational_evidence_only": True,
        "claim_level": CLAIM_LEVEL,
        "claim_status": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "denied_claims": DENIED_CLAIMS,
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "final_gate_status": aggregate["final_gate_status"],
        "human_external_gold_label": False,
        "measurement_validation_claim": False,
        "metric_bridge_support": False,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "selector_superiority_claim": False,
        "treated_as": "model_adjudicated_candidate_operational_evidence_only",
        "truth_correction_guarantee": False,
        "validated_repair_claim": False,
    }
    claim_gate_report = {
        "allowed_claims": ALLOWED_CLAIMS,
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "denied_claims": DENIED_CLAIMS,
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "final_gate_status": aggregate["final_gate_status"],
        "live_api_call_count": call_count,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "witness_count": len(records),
    }

    write_jsonl(output_dir / "witness_records.jsonl", records)
    write_json(output_dir / "regime_ledger.json", {"regimes": ledger, "schema_version": "post_lapi_reprojection_regime_ledger_v1"})
    write_json(output_dir / "aggregate_report.json", aggregate)
    write_json(output_dir / "run_manifest.json", manifest)
    write_json(output_dir / "claim_ledger.json", claim_ledger)
    write_json(output_dir / "claim_gate_report.json", claim_gate_report)
    _write_docs(aggregate=aggregate, manifest=manifest, ledger=ledger, output_dir=output_dir)
    return {
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "endpoint": str(client_config["base_url"]),
        "final_gate_status": aggregate["final_gate_status"],
        "live_api_call_count": call_count,
        "model_snapshot": model_snapshot_value,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "terminal_status": "DONE",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the POST-5 DashScope reprojection witness pilot.")
    parser.add_argument("--approval", required=True)
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--max-cases", type=int, default=30)
    parser.add_argument("--timeout-seconds", type=int, default=90)
    args = parser.parse_args(argv)
    result = run_pilot(
        approval=str(args.approval),
        max_cases=args.max_cases,
        output_dir=Path(args.output_dir),
        repo_root=Path(args.repo_root),
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("terminal_status") == "DONE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
