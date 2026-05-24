from __future__ import annotations

# ruff: noqa: E402

import argparse
import csv
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


APPROVAL_TOKEN = "APPROVE_LIVE_API_POST_7_EXTRACTION_AUDIT=true"
CONFIG_PATH = Path("configs/post_lapi/extraction_quality_audit_config.yaml")
SCHEMA_PATH = Path("schemas/post_lapi_extraction_quality.schema.json")
SOURCE_POOLS_PATH = Path("artifacts/benchmarks/hotpotqa_candidate_pools.jsonl")
OUTPUT_DIR = Path("artifacts/experiments/post_lapi_extraction_quality_audit")
DOC_PATH = Path("docs/experiments/POST-LAPI-extraction-quality-audit.md")
TABLE_PATH = Path("docs/paper/post-lapi-extraction-quality-table.md")
RUN_ID = "post_lapi_extraction_quality_audit_live_v1"

CLAIM_LEVEL = "operational_utility_only/no_claim_upgrade"
DIAGNOSTIC_CLAIM_LEVEL = "model_adjudicated_extraction_risk_evidence"
ENDPOINT_FAMILY = "dashscope_openai_compatible_chat_completions"
THINKING_MODE = "disabled"
TOKEN_ACCOUNTING = "provider_usage_or_character_estimate"
RUBRIC_VERSION = "extraction_quality_audit_v1"
SYSTEM_PROMPT_VERSION = "post7_extraction_quality_judge_v1"

STRATA = (
    "simple_factual",
    "complex_conditional",
    "qualifier_heavy",
    "temporal_scope",
    "cross_chunk",
    "long_tail_entity",
    "high_provenance_value",
    "prerequisite",
    "contradictory",
    "adversarial",
)
ALLOWED_LABELS = {
    "captured",
    "captured_core_preserved",
    "captured_core_materially_changed",
    "missing",
    "lost_qualifier",
    "temporal_scope_error",
    "provenance_loss",
    "selector_impact",
}
CAPTURE_LABELS = {"captured", "captured_core_preserved"}
LOSS_WEIGHTS = {
    "captured": 0.0,
    "captured_core_preserved": 0.0,
    "captured_core_materially_changed": 0.5,
    "lost_qualifier": 0.75,
    "temporal_scope_error": 0.75,
    "provenance_loss": 0.75,
    "selector_impact": 0.75,
    "missing": 1.0,
}
ALLOWED_CLAIMS = [
    "model_adjudicated_extraction_risk_evidence",
    "operational_extraction_audit",
]
DENIED_CLAIMS = [
    "human_validated_extraction_measurement",
    "measurement_validation",
    "theorem_transfer_to_M_star",
    "end_to_end_validation",
    "end_to_end_measurement_validation",
    "metric_bridge_support",
    "calibrated_proxy_supported",
    "vinfo_proxy_supported",
    "paper_evidence",
    "selector_superiority",
    "global_selector_superiority",
    "route_5_unlock",
    "route_8_unlock",
]
CONFIDENCE_BUCKETS = {"low", "medium", "high"}


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


def _normalize_confidence(value: Any) -> str:
    bucket = _normalize_key(value)
    return bucket if bucket in CONFIDENCE_BUCKETS else "low"


def _normalize_label(value: Any, *, stratum: str) -> str:
    label = _normalize_key(value)
    aliases = {
        "captured_core": "captured_core_preserved",
        "core_preserved": "captured_core_preserved",
        "materially_changed": "captured_core_materially_changed",
        "changed": "captured_core_materially_changed",
        "not_captured": "missing",
        "qualifier_loss": "lost_qualifier",
        "scope_error": "temporal_scope_error",
        "provenance_missing": "provenance_loss",
        "selector_impacted": "selector_impact",
    }
    label = aliases.get(label, label)
    if label in ALLOWED_LABELS:
        return label
    defaults = {
        "qualifier_heavy": "lost_qualifier",
        "temporal_scope": "temporal_scope_error",
        "high_provenance_value": "provenance_loss",
        "contradictory": "captured_core_materially_changed",
        "adversarial": "selector_impact",
    }
    return defaults.get(stratum, "captured_core_preserved")


def _bounded_float(value: Any, *, default: float = 1.0, minimum: float = 0.25, maximum: float = 3.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return round(min(max(parsed, minimum), maximum), 6)


def _packet_hash(packet: Mapping[str, Any]) -> str:
    existing = str(packet.get("hash") or "").strip()
    return existing or _sha256_text(str(packet.get("content") or ""))


def _packet_ref(packet: Mapping[str, Any]) -> dict[str, Any]:
    span = packet.get("span") or {}
    provenance = packet.get("provenance") or {}
    return {
        "packet_hash": _packet_hash(packet),
        "packet_id_hash": _sha256_text(str(packet.get("packet_id") or _packet_hash(packet))),
        "source_doc_id_hash": _sha256_text(str(packet.get("source_doc_id") or provenance.get("source_doc_id") or "")),
        "span_hash": _sha256_text(json.dumps(span, ensure_ascii=True, sort_keys=True)),
        "support_label": str(packet.get("gold_support_label") or ""),
        "token_cost": int(packet.get("token_cost") or 0),
    }


def _packets_by_label(packets: Sequence[Mapping[str, Any]], label: str) -> list[Mapping[str, Any]]:
    return [packet for packet in packets if str(packet.get("gold_support_label") or "") == label]


def _context_text(packets: Sequence[Mapping[str, Any]]) -> str:
    return "\n".join(f"- {packet.get('content', '')}" for packet in packets)


def _target_answer(target: Any) -> str:
    if isinstance(target, Mapping):
        return str(target.get("label") or target.get("answer") or target)
    return str(target or "")


def _case_packets(
    *,
    distractor_packets: Sequence[Mapping[str, Any]],
    stratum: str,
    support_packets: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    if stratum == "simple_factual":
        return list(support_packets[:1])
    if stratum == "complex_conditional":
        return list(support_packets[:2]) + list(distractor_packets[:1])
    if stratum == "qualifier_heavy":
        return list(support_packets[:1]) + list(distractor_packets[:1])
    if stratum == "temporal_scope":
        return list(support_packets[:1]) + list(distractor_packets[:2])
    if stratum == "cross_chunk":
        return list(support_packets[:2]) + list(distractor_packets[:2])
    if stratum == "long_tail_entity":
        return list(support_packets[:1]) + list(distractor_packets[-1:])
    if stratum == "high_provenance_value":
        return list(support_packets[:2]) or list(support_packets[:1])
    if stratum == "prerequisite":
        return list(support_packets[:1]) + list(distractor_packets[:1])
    if stratum == "contradictory":
        return list(support_packets[:1]) + list(distractor_packets[:2])
    if stratum == "adversarial":
        return list(distractor_packets[:2]) + list(support_packets[:1])
    return list(support_packets[:1])


def _extracted_text_for_case(*, answer: str, question: str, stratum: str) -> str:
    if stratum == "simple_factual":
        return f"The extraction preserves the core answer '{answer}' for the question."
    if stratum == "complex_conditional":
        return f"The extraction links multiple supporting conditions before giving '{answer}' as the answer."
    if stratum == "qualifier_heavy":
        return f"The extraction gives '{answer}' but compresses qualifiers and exceptions from the source."
    if stratum == "temporal_scope":
        return f"The extraction gives '{answer}' while potentially shifting date or time scope."
    if stratum == "cross_chunk":
        return f"The extraction combines facts across separate chunks to support '{answer}'."
    if stratum == "long_tail_entity":
        return f"The extraction preserves a less frequent entity needed to answer '{question}'."
    if stratum == "high_provenance_value":
        return f"The extraction gives '{answer}' but may omit source attribution details."
    if stratum == "prerequisite":
        return f"The extraction states '{answer}' while reducing an intermediate prerequisite fact."
    if stratum == "contradictory":
        return f"The extraction gives '{answer}' while mixing in a potentially conflicting distractor."
    if stratum == "adversarial":
        return f"The extraction gives '{answer}' in a distractor-heavy setting with selector-risk pressure."
    return f"The extraction gives '{answer}'."


def _quota_by_stratum(strata: Sequence[str], limit: int) -> dict[str, int]:
    base = limit // len(strata)
    remainder = limit % len(strata)
    return {
        stratum: base + (1 if index < remainder else 0)
        for index, stratum in enumerate(strata)
    }


def _build_cases(*, limit: int, source_path: Path, strata: Sequence[str]) -> list[dict[str, Any]]:
    rows = read_jsonl(source_path)
    quotas = _quota_by_stratum(strata, limit)
    cases: list[dict[str, Any]] = []
    for stratum in strata:
        count = 0
        for row_index, row in enumerate(rows):
            packets = list((row.get("candidate_pool") or {}).get("packets") or [])
            support_packets = _packets_by_label(packets, "gold_supporting")
            distractor_packets = _packets_by_label(packets, "same_context_distractor")
            if not support_packets:
                continue
            selected_packets = _case_packets(
                distractor_packets=distractor_packets,
                stratum=stratum,
                support_packets=support_packets,
            )
            if not selected_packets:
                continue
            case_index = len(cases) + 1
            question = str(row.get("query") or "")
            answer = _target_answer(row.get("target"))
            source_text = _context_text(selected_packets)
            extracted_text = _extracted_text_for_case(
                answer=answer,
                question=question,
                stratum=stratum,
            )
            candidate_pool = row.get("candidate_pool") or {}
            candidate_pool_hash = str(candidate_pool.get("candidate_pool_hash") or stable_hash([_packet_ref(packet) for packet in packets]))
            selected_refs = [_packet_ref(packet) for packet in selected_packets]
            source_document_id = _sha256_text(str(row.get("instance_id") or stable_hash(row)))
            source_span_hash = stable_hash(selected_refs)
            cases.append(
                {
                    "answer": answer,
                    "case_id": f"post7-extraction-{case_index:03d}",
                    "candidate_pool_hash": candidate_pool_hash,
                    "dataset": str(row.get("dataset") or "HotpotQA"),
                    "duplicate_index": case_index % 2,
                    "extracted_item_hash": _sha256_text(extracted_text),
                    "extracted_item_id": f"post7-extracted-item-{case_index:03d}",
                    "extracted_text": extracted_text,
                    "order_swap": bool(case_index % 2),
                    "question": question,
                    "rubric_paraphrase_id": "p1" if case_index % 2 else "p0",
                    "selected_packet_refs": selected_refs,
                    "source_document_hash": _sha256_text(source_text),
                    "source_document_id": source_document_id,
                    "source_instance_hash": source_document_id,
                    "source_row_hash": stable_hash(row),
                    "source_row_index": row_index,
                    "source_span_hash": source_span_hash,
                    "source_text": source_text,
                    "split": str(row.get("split") or ""),
                    "stratum": stratum,
                }
            )
            count += 1
            if count >= quotas[stratum]:
                break
        if count < quotas[stratum]:
            raise RuntimeError(f"not_enough_cases_for_stratum:{stratum}:{count}/{quotas[stratum]}")
    if len(cases) != limit:
        raise RuntimeError(f"case_count_mismatch:{len(cases)}/{limit}")
    return cases


def _system_prompt(*, rubric_paraphrase_id: str) -> str:
    if rubric_paraphrase_id == "p1":
        paraphrase = (
            "Judge whether the extracted statement preserves the source-backed finding, "
            "including qualifiers, time scope, provenance, and selector-risk context."
        )
    else:
        paraphrase = (
            "Audit extraction quality by comparing the source context with the extracted "
            "statement and selecting the most appropriate risk label."
        )
    return "\n".join(
        [
            f"System prompt version: {SYSTEM_PROMPT_VERSION}",
            f"Rubric version: {RUBRIC_VERSION}",
            paraphrase,
            "This is model-adjudicated candidate operational extraction-risk evidence only.",
            "Do not make human-validation, measurement-validation, metric-bridge, selector-superiority, paper-evidence, or route-unlock claims.",
            "Return only one minified JSON object.",
            "Required keys: label, confidence_bucket, value_weight, qualifier_loss, temporal_scope_error, provenance_loss, selector_impact.",
            "Allowed labels: captured, captured_core_preserved, captured_core_materially_changed, missing, lost_qualifier, temporal_scope_error, provenance_loss, selector_impact.",
            "Allowed confidence_bucket values: low, medium, high.",
            "Do not include rationale, hidden reasoning, markdown fences, provider metadata, or raw response text.",
        ]
    )


def _messages_for_case(case: Mapping[str, Any]) -> tuple[list[dict[str, str]], str]:
    system_prompt = _system_prompt(rubric_paraphrase_id=str(case["rubric_paraphrase_id"]))
    if bool(case["order_swap"]):
        comparison_block = "\n".join(
            [
                "Extracted statement:",
                str(case["extracted_text"]),
                "",
                "Source context:",
                str(case["source_text"]),
            ]
        )
    else:
        comparison_block = "\n".join(
            [
                "Source context:",
                str(case["source_text"]),
                "",
                "Extracted statement:",
                str(case["extracted_text"]),
            ]
        )
    user_prompt = "\n".join(
        [
            f"Audit stratum: {case['stratum']}",
            f"Question: {case['question']}",
            f"Candidate answer: {case['answer']}",
            "",
            comparison_block,
            "",
            "Select the single best label. Treat selector_impact as candidate-pool risk only, not selector validity.",
        ]
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ], _sha256_text(system_prompt)


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


def _estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


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


class DashScopeExtractionAuditClient:
    def __init__(self, *, api_key: str, base_url: str, model_id: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id

    def classify(self, *, messages: Sequence[Mapping[str, str]], timeout_seconds: int) -> dict[str, Any]:
        payload = {
            "enable_thinking": False,
            "max_tokens": 256,
            "messages": [dict(message) for message in messages],
            "model": self.model_id,
            "n": 1,
            "response_format": {"type": "json_object"},
            "stream": False,
            "temperature": 0,
            "top_p": 1,
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
                "confidence_bucket": "low",
                "label": "missing",
                "provenance_loss": False,
                "qualifier_loss": False,
                "selector_impact": False,
                "temporal_scope_error": False,
                "value_weight": 1.0,
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
    client: Any,
    *,
    messages: Sequence[Mapping[str, str]],
    timeout_seconds: int,
    attempts: int = 3,
) -> dict[str, Any]:
    last_reason = "dashscope_live_api_unknown_failure"
    for attempt_index in range(attempts):
        try:
            return dict(client.classify(messages=messages, timeout_seconds=timeout_seconds))
        except RuntimeError as exc:
            last_reason = str(exc)
            if attempt_index + 1 >= attempts:
                break
            time.sleep(min(8, 2**attempt_index))
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
        "schema_version": "post_lapi_extraction_quality_blocker_v1",
        "terminal_status": "BLOCKED",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "blocker_report.json", report)
    return report


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


def _record_from_result(
    *,
    call_count: int,
    case: Mapping[str, Any],
    client_config: Mapping[str, Any],
    prompt_hash: str,
    request_payload_hash: str,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    parsed = result.get("parsed") or {}
    stratum = str(case["stratum"])
    label = _normalize_label(parsed.get("label"), stratum=stratum)
    qualifier_loss = _normalize_bool(parsed.get("qualifier_loss"), default=label == "lost_qualifier")
    temporal_scope_error = _normalize_bool(
        parsed.get("temporal_scope_error"),
        default=label == "temporal_scope_error",
    )
    provenance_loss = _normalize_bool(parsed.get("provenance_loss"), default=label == "provenance_loss")
    selector_impact_flag = _normalize_bool(parsed.get("selector_impact"), default=label == "selector_impact")
    value_weight = _bounded_float(parsed.get("value_weight"), default=1.0)
    if stratum in {"high_provenance_value", "prerequisite", "adversarial"}:
        value_weight = max(value_weight, 1.25)
    risk_reason_codes = [
        reason
        for reason, enabled in (
            ("qualifier_loss", qualifier_loss),
            ("temporal_scope_error", temporal_scope_error),
            ("provenance_loss", provenance_loss),
            ("selector_impact", selector_impact_flag),
            ("material_change", label == "captured_core_materially_changed"),
            ("missing", label == "missing"),
        )
        if enabled
    ]
    return {
        "allowed_claims": ALLOWED_CLAIMS,
        "audit_diagnostic_only": True,
        "calibrated_proxy_supported": False,
        "candidate_pool_hash": str(case["candidate_pool_hash"]),
        "claim_level": CLAIM_LEVEL,
        "claim_status": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "confidence_bucket": _normalize_confidence(parsed.get("confidence_bucket")),
        "dataset": str(case["dataset"]),
        "denied_claims": DENIED_CLAIMS,
        "duplicate_index": int(case["duplicate_index"]),
        "endpoint": str(client_config.get("base_url") or getattr(client_config.get("client"), "base_url", "")),
        "endpoint_family": ENDPOINT_FAMILY,
        "extracted_item_hash": str(case["extracted_item_hash"]),
        "extracted_item_id": str(case["extracted_item_id"]),
        "human_validated_extraction_measurement": False,
        "input_token_count": int(result.get("input_token_count") or 0),
        "judge_model_snapshot": str(result.get("model_snapshot") or client_config.get("model_id") or ""),
        "judge_prompt_hash": prompt_hash,
        "label": label,
        "label_loss_weight": LOSS_WEIGHTS[label],
        "label_source_kind": "model_adjudicated",
        "latency_ms": int(result.get("latency_ms") or 0),
        "live_api_call_ordinal": call_count,
        "live_api_call_performed": True,
        "measurement_validation_claim": False,
        "metric_bridge_support": False,
        "order_swap": bool(case["order_swap"]),
        "output_token_count": int(result.get("output_token_count") or 0),
        "paper_evidence_claim": False,
        "parse_status": str(result.get("parse_status") or "parsed"),
        "provenance_loss": provenance_loss,
        "qualifier_loss": qualifier_loss,
        "raw_response_stored": False,
        "record_id": f"{RUN_ID}-{case['case_id']}",
        "request_payload_hash": request_payload_hash,
        "risk_reason_codes": risk_reason_codes or ["none"],
        "route_5_locked": True,
        "route_8_locked": True,
        "rubric_paraphrase_id": str(case["rubric_paraphrase_id"]),
        "rubric_version": RUBRIC_VERSION,
        "schema_version": "post_lapi_extraction_quality_record_v1",
        "selected_packet_hashes": [ref["packet_hash"] for ref in list(case["selected_packet_refs"])],
        "selector_impact": "candidate_pool_risk_only" if selector_impact_flag else "not_indicated",
        "selector_impact_flag": selector_impact_flag,
        "selector_superiority_claim": False,
        "source_document_hash": str(case["source_document_hash"]),
        "source_document_id": str(case["source_document_id"]),
        "source_instance_hash": str(case["source_instance_hash"]),
        "source_row_hash": str(case["source_row_hash"]),
        "source_row_index": int(case["source_row_index"]),
        "source_span_hash": str(case["source_span_hash"]),
        "split": str(case["split"]),
        "stratum": stratum,
        "temporal_scope_error": temporal_scope_error,
        "theorem_transfer_to_M_star": False,
        "usage_count_source": "provider_usage" if result.get("usage_actual") else "character_estimate",
        "value_weight": value_weight,
        "vinfo_proxy_supported": False,
    }


def _summary_for_records(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_stratum: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        by_stratum[str(record["stratum"])].append(record)
    rows: list[dict[str, Any]] = []
    for stratum in STRATA:
        subset = by_stratum.get(stratum, [])
        total = len(subset)
        labels = Counter(str(record["label"]) for record in subset)
        total_weight = sum(float(record["value_weight"]) for record in subset)
        weighted_loss = sum(
            float(record["value_weight"]) * float(record["label_loss_weight"])
            for record in subset
        )
        token_costs = [float(record["input_token_count"] + record["output_token_count"]) for record in subset]
        latencies = [float(record["latency_ms"]) for record in subset]
        rows.append(
            {
                "claim_gate_status": "model_adjudicated_extraction_risk_ready",
                "completeness_by_stratum": round(
                    _rate(sum(1 for record in subset if str(record["label"]) in CAPTURE_LABELS), total),
                    6,
                ),
                "cost_per_case_tokens": round(_mean(token_costs), 3),
                "label_counts": dict(sorted(labels.items())),
                "latency_per_case_ms": round(_mean(latencies), 3),
                "n_examples": total,
                "parse_failure_rate": round(_rate(sum(1 for record in subset if record["parse_status"] == "parse_failed"), total), 6),
                "provenance_loss_rate": round(_rate(sum(1 for record in subset if record["label"] == "provenance_loss"), total), 6),
                "qualifier_loss_rate": round(_rate(sum(1 for record in subset if record["label"] == "lost_qualifier"), total), 6),
                "selector_impact_rate": round(_rate(sum(1 for record in subset if record["label"] == "selector_impact"), total), 6),
                "stratum": stratum,
                "temporal_scope_error_rate": round(_rate(sum(1 for record in subset if record["label"] == "temporal_scope_error"), total), 6),
                "value_weighted_loss_proxy": round(weighted_loss / total_weight, 6) if total_weight else 0.0,
            }
        )
    return rows


def _aggregate(records: Sequence[Mapping[str, Any]], summary_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(records)
    labels = Counter(str(record["label"]) for record in records)
    latencies = [float(record["latency_ms"]) for record in records]
    input_tokens = sum(int(record["input_token_count"]) for record in records)
    output_tokens = sum(int(record["output_token_count"]) for record in records)
    total_weight = sum(float(record["value_weight"]) for record in records)
    weighted_loss = sum(
        float(record["value_weight"]) * float(record["label_loss_weight"])
        for record in records
    )
    gate_ready = (
        total == 100
        and len(summary_rows) == len(STRATA)
        and all(row["n_examples"] >= 1 for row in summary_rows)
        and all(record["raw_response_stored"] is False for record in records)
        and all(record["claim_upgrade_introduced"] is False for record in records)
        and all(record["route_5_locked"] is True and record["route_8_locked"] is True for record in records)
    )
    return {
        "allowed_claims_after_gate": ALLOWED_CLAIMS,
        "calibrated_proxy_supported": False,
        "candidate_operational_evidence_only": True,
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "cost_summary": {
            "input_tokens_total": input_tokens,
            "monetary_cost_status": "not_calculated_without_provider_pricing_config",
            "output_tokens_total": output_tokens,
            "token_cost_per_case_mean": round((input_tokens + output_tokens) / total, 3) if total else 0.0,
            "total_tokens": input_tokens + output_tokens,
            "usage_counts_estimated_count": sum(1 for record in records if record["usage_count_source"] == "character_estimate"),
            "usage_counts_provider_count": sum(1 for record in records if record["usage_count_source"] == "provider_usage"),
        },
        "denied_claims": DENIED_CLAIMS,
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "end_to_end_validation_claim": False,
        "final_gate_status": "post7_extraction_quality_audit_completed" if gate_ready else "downgraded_to_ambiguous",
        "human_validated_extraction_measurement": False,
        "label_counts": dict(sorted(labels.items())),
        "latency_summary_ms": {
            "max": round(max(latencies), 3) if latencies else 0.0,
            "mean": round(_mean(latencies), 3),
            "median": round(statistics.median(latencies), 3) if latencies else 0.0,
            "min": round(min(latencies), 3) if latencies else 0.0,
            "p95": round(_quantile(latencies, 0.95), 3),
        },
        "live_api_call_count": total,
        "measurement_validation_claim": False,
        "metric_bridge_support": False,
        "paper_evidence_claim": False,
        "parse_failed_rate": _rate(sum(1 for record in records if record["parse_status"] == "parse_failed"), total),
        "provenance_loss_rate": _rate(labels["provenance_loss"], total),
        "qualifier_loss_rate": _rate(labels["lost_qualifier"], total),
        "raw_response_stored": False,
        "record_count": total,
        "route_5_locked": True,
        "route_8_locked": True,
        "schema_version": "post_lapi_extraction_quality_aggregate_v1",
        "selector_impact_rate": _rate(labels["selector_impact"], total),
        "selector_superiority_claim": False,
        "stratum_count": len(summary_rows),
        "temporal_scope_error_rate": _rate(labels["temporal_scope_error"], total),
        "theorem_transfer_to_M_star": False,
        "value_weighted_loss_proxy": {
            "interpretation": "candidate_operational_evidence_only",
            "value": round(weighted_loss / total_weight, 6) if total_weight else 0.0,
        },
        "vinfo_proxy_supported": False,
    }


def _write_summary_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fieldnames = [
        "stratum",
        "n_examples",
        "completeness_by_stratum",
        "value_weighted_loss_proxy",
        "qualifier_loss_rate",
        "temporal_scope_error_rate",
        "provenance_loss_rate",
        "selector_impact_rate",
        "parse_failure_rate",
        "cost_per_case_tokens",
        "latency_per_case_ms",
        "claim_gate_status",
        "label_counts",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fieldnames})


def _cost_latency_ledger(records: Sequence[Mapping[str, Any]], summary_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "cost_basis": TOKEN_ACCOUNTING,
        "ledger": [
            {
                "input_tokens": sum(int(record["input_token_count"]) for record in records if record["stratum"] == row["stratum"]),
                "latency_ms_mean": row["latency_per_case_ms"],
                "output_tokens": sum(int(record["output_token_count"]) for record in records if record["stratum"] == row["stratum"]),
                "stratum": row["stratum"],
                "total_tokens": sum(
                    int(record["input_token_count"] + record["output_token_count"])
                    for record in records
                    if record["stratum"] == row["stratum"]
                ),
            }
            for row in summary_rows
        ],
        "monetary_cost_status": "not_calculated_without_provider_pricing_config",
        "schema_version": "post_lapi_extraction_quality_cost_latency_v1",
    }


def _write_docs(
    *,
    aggregate: Mapping[str, Any],
    doc_path: Path,
    manifest: Mapping[str, Any],
    output_dir: Path,
    summary_rows: Sequence[Mapping[str, Any]],
    table_path: Path,
) -> None:
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    value_loss = aggregate["value_weighted_loss_proxy"]
    doc_path.write_text(
        "\n".join(
            [
                "# POST-LAPI Extraction Quality Audit",
                "",
                "Goal ID: POST-7-RUN / Extraction quality audit",
                f"Run ID: `{manifest['run_id']}`",
                f"Claim ceiling: `{CLAIM_LEVEL}`",
                "",
                "## Scope",
                "",
                "This owner-approved pilot ran a bounded DashScope-compatible extraction quality audit over 100 HotpotQA candidate-pool examples. Outputs are model-adjudicated candidate operational extraction-risk evidence only. They are not human-validated extraction measurement, measurement validation, metric bridge support, calibrated proxy support, V-information proxy support, paper evidence, selector superiority, Route 5 unlock evidence, or Route 8 unlock evidence.",
                "",
                "## Run Metadata",
                "",
                f"- Live API calls run: `{aggregate['live_api_call_count']}`",
                f"- Example count: `{aggregate['record_count']}`",
                f"- Stratum count: `{aggregate['stratum_count']}`",
                f"- Model snapshot: `{manifest['model_snapshot']}`",
                f"- Endpoint family: `{manifest['endpoint_family']}`",
                f"- Endpoint: `{manifest['endpoint']}`",
                f"- Raw API responses stored: `{str(aggregate['raw_response_stored']).lower()}`",
                f"- Route 5 locked: `{str(aggregate['route_5_locked']).lower()}`",
                f"- Route 8 locked: `{str(aggregate['route_8_locked']).lower()}`",
                f"- Claim upgrade introduced: `{str(aggregate['claim_upgrade_introduced']).lower()}`",
                f"- Gate status: `{aggregate['final_gate_status']}`",
                "",
                "## Aggregate Metrics",
                "",
                f"- Value-weighted loss proxy: `{value_loss['value']}`",
                f"- Value-weighted loss proxy interpretation: `{value_loss['interpretation']}`",
                f"- Qualifier loss rate: `{aggregate['qualifier_loss_rate']}`",
                f"- Temporal scope error rate: `{aggregate['temporal_scope_error_rate']}`",
                f"- Provenance loss rate: `{aggregate['provenance_loss_rate']}`",
                f"- Selector impact rate: `{aggregate['selector_impact_rate']}`",
                f"- Parse failed rate: `{aggregate['parse_failed_rate']}`",
                "",
                "## Claim Boundary",
                "",
                "Allowed interpretation is model-adjudicated extraction-risk evidence and operational extraction audit only. The value-weighted loss proxy is candidate operational evidence only. Denied interpretations include human-validated extraction measurement, measurement validation, theorem transfer to M*, end-to-end validation, metric bridge support, calibrated proxy support, V-information proxy support, paper evidence, selector superiority, Route 5 unlock, and Route 8 unlock.",
                "",
                "## Artifact Index",
                "",
                f"- `{(output_dir / 'audit_records.jsonl').as_posix()}`",
                f"- `{(output_dir / 'stratum_summary.csv').as_posix()}`",
                f"- `{(output_dir / 'stratum_summary.json').as_posix()}`",
                f"- `{(output_dir / 'aggregate_report.json').as_posix()}`",
                f"- `{(output_dir / 'run_manifest.json').as_posix()}`",
                f"- `{(output_dir / 'claim_ledger.json').as_posix()}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# POST-LAPI Extraction Quality Table",
        "",
        f"Status: POST-7-RUN result under `{CLAIM_LEVEL}`",
        "",
        "These rows are model-adjudicated candidate operational diagnostics only. They do not support human-validated extraction measurement, measurement validation, metric bridge support, paper evidence, selector superiority, Route 5 unlock, or Route 8 unlock.",
        "",
        "| stratum | n examples | completeness by stratum | value-weighted loss proxy | qualifier loss rate | temporal scope error rate | provenance loss rate | selector impact rate | parse failure rate | claim gate status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary_rows:
        lines.append(
            "| {stratum} | {n_examples} | {completeness_by_stratum} | {value_weighted_loss_proxy} | {qualifier_loss_rate} | {temporal_scope_error_rate} | {provenance_loss_rate} | {selector_impact_rate} | {parse_failure_rate} | {claim_gate_status} |".format(
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
            f"| live API calls run | `{aggregate['live_api_call_count']}` |",
            f"| model snapshot | `{manifest['model_snapshot']}` |",
            f"| endpoint | `{manifest['endpoint']}` |",
            "| raw API responses stored | `false` |",
            f"| claim level | `{CLAIM_LEVEL}` |",
            f"| diagnostic claim level | `{DIAGNOSTIC_CLAIM_LEVEL}` |",
            "| output interpretation | model-adjudicated candidate operational extraction-risk evidence only |",
            "| value-weighted loss proxy interpretation | candidate operational evidence only |",
            "| Route 5 locked | `true` |",
            "| Route 8 locked | `true` |",
            "| claim upgrade introduced | `false` |",
        ]
    )
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _client_config_from_injected(client: Any) -> dict[str, Any]:
    return {
        "api_key_source": "injected_test_client",
        "available": True,
        "base_url": str(getattr(client, "base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")),
        "client": client,
        "model_id": str(getattr(client, "model_id", "injected_post7_judge")),
    }


def run_post7_extraction_quality_audit(
    *,
    approval: str,
    client: Any | None = None,
    doc_path: str | Path = DOC_PATH,
    max_examples: int = 100,
    output_dir: str | Path = OUTPUT_DIR,
    repo_root: str | Path = ROOT,
    table_path: str | Path = TABLE_PATH,
    timeout_seconds: int = 90,
) -> dict[str, Any]:
    repo = Path(repo_root)
    output = Path(output_dir)
    if approval != APPROVAL_TOKEN:
        return _write_blocker(
            output,
            reason="missing_required_owner_approval_token",
            live_api_call_count=0,
        )
    if max_examples != 100:
        raise ValueError("POST-7 first pass must run exactly 100 examples")

    config = _load_json(repo / CONFIG_PATH)
    if config.get("claim_level") != CLAIM_LEVEL:
        raise RuntimeError("claim_level_config_mismatch")
    if config.get("route_5_locked") is not True or config.get("route_8_locked") is not True:
        raise RuntimeError("route_lock_config_not_true")
    if config.get("raw_response_storage_allowed") is not False or config.get("raw_response_stored") is not False:
        raise RuntimeError("config_allows_raw_response_storage")
    if config.get("human_validation_claim_allowed") is not False or config.get("measurement_validation_claim_allowed") is not False:
        raise RuntimeError("config_allows_denied_validation_claim")
    if tuple(config.get("strata") or []) != STRATA:
        raise RuntimeError("strata_config_mismatch")

    output.mkdir(parents=True, exist_ok=True)
    if client is None:
        client_config = _select_live_api_client_config(_env_values(repo))
        if not client_config["available"]:
            return _write_blocker(
                output,
                reason=str(client_config["blocked_reason"]),
                live_api_call_count=0,
            )
        client = DashScopeExtractionAuditClient(
            api_key=str(client_config["api_key"]),
            base_url=str(client_config["base_url"]),
            model_id=str(client_config["model_id"]),
        )
    else:
        client_config = _client_config_from_injected(client)

    cases = _build_cases(
        limit=max_examples,
        source_path=repo / SOURCE_POOLS_PATH,
        strata=STRATA,
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
                output,
                reason=f"dashscope_live_api_call_failed:{exc}",
                live_api_call_count=call_count,
            )
        call_count += 1
        model_snapshot = str(result.get("model_snapshot") or client_config.get("model_id") or "")
        model_snapshots.add(model_snapshot)
        records.append(
            _record_from_result(
                call_count=call_count,
                case=case,
                client_config=client_config,
                prompt_hash=prompt_hash,
                request_payload_hash=request_payload_hash,
                result=result,
            )
        )
        if index % 10 == 0 or index == len(cases):
            print(f"post7_progress {index}/{len(cases)} calls completed", flush=True)

    summary_rows = _summary_for_records(records)
    aggregate = _aggregate(records, summary_rows)
    model_snapshot_value = ",".join(sorted(model_snapshots)) if model_snapshots else str(client_config["model_id"])
    cost_latency = _cost_latency_ledger(records, summary_rows)
    claim_ledger = {
        "allowed_claims": ALLOWED_CLAIMS,
        "calibrated_proxy_supported": False,
        "claim_level": CLAIM_LEVEL,
        "claim_status": CLAIM_LEVEL,
        "claim_upgrade": False,
        "claim_upgrade_introduced": False,
        "current_claim_level": CLAIM_LEVEL,
        "denied_claims": DENIED_CLAIMS,
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "human_validated_extraction_measurement": False,
        "measurement_validation_claim": False,
        "metric_bridge_support": False,
        "paper_evidence_claim": False,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "selector_superiority_claim": False,
        "treated_as": "model_adjudicated_candidate_operational_extraction_risk_only",
        "value_weighted_loss_proxy_interpretation": "candidate_operational_evidence_only",
        "vinfo_proxy_supported": False,
    }
    claim_gate_report = {
        "allowed_claims": ALLOWED_CLAIMS,
        "calibrated_proxy_supported": False,
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "denied_claims": DENIED_CLAIMS,
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "final_gate_status": aggregate["final_gate_status"],
        "human_validated_extraction_measurement": False,
        "live_api_call_count": call_count,
        "measurement_validation_claim": False,
        "metric_bridge_support": False,
        "paper_evidence_claim": False,
        "raw_response_stored": False,
        "record_count": len(records),
        "route_5_locked": True,
        "route_8_locked": True,
        "selector_superiority_claim": False,
        "value_weighted_loss_proxy_interpretation": "candidate_operational_evidence_only",
        "vinfo_proxy_supported": False,
    }
    manifest = {
        "api_key_source": str(client_config["api_key_source"]),
        "approval_gate_token_verified": True,
        "claim_ledger_hash": stable_hash(claim_ledger),
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "config_hash": _sha256_file(repo / CONFIG_PATH),
        "cost_latency_ledger_hash": stable_hash(cost_latency),
        "diagnostic_claim_level": DIAGNOSTIC_CLAIM_LEVEL,
        "endpoint": str(client_config["base_url"]),
        "endpoint_family": ENDPOINT_FAMILY,
        "example_count": len(records),
        "live_api_call_count": call_count,
        "live_api_call_performed": True,
        "model_snapshot": model_snapshot_value,
        "output_dir": output.name,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "run_finished_at": _utc_now(),
        "run_id": RUN_ID,
        "run_started_at": run_started,
        "schema_hash": _sha256_file(repo / SCHEMA_PATH),
        "schema_version": "post_lapi_extraction_quality_run_manifest_v1",
        "source_cases": [
            {
                "case_id": case["case_id"],
                "candidate_pool_hash": case["candidate_pool_hash"],
                "extracted_item_hash": case["extracted_item_hash"],
                "extracted_item_id": case["extracted_item_id"],
                "source_document_hash": case["source_document_hash"],
                "source_document_id": case["source_document_id"],
                "source_instance_hash": case["source_instance_hash"],
                "source_row_hash": case["source_row_hash"],
                "source_row_index": case["source_row_index"],
                "source_span_hash": case["source_span_hash"],
                "stratum": case["stratum"],
            }
            for case in cases
        ],
        "strata": list(STRATA),
        "target_examples_first_pass": max_examples,
        "terminal_status": aggregate["final_gate_status"],
        "thinking_mode": THINKING_MODE,
        "token_budget_accounting": TOKEN_ACCOUNTING,
    }
    manifest["manifest_hash"] = stable_hash(manifest)

    write_jsonl(output / "audit_records.jsonl", records)
    write_json(output / "stratum_summary.json", {"schema_version": "post_lapi_extraction_quality_stratum_summary_v1", "strata": summary_rows})
    _write_summary_csv(output / "stratum_summary.csv", summary_rows)
    write_json(output / "cost_latency_ledger.json", cost_latency)
    write_json(output / "aggregate_report.json", aggregate)
    write_json(output / "run_manifest.json", manifest)
    write_json(output / "claim_ledger.json", claim_ledger)
    write_json(output / "claim_gate_report.json", claim_gate_report)
    _write_docs(
        aggregate=aggregate,
        doc_path=Path(doc_path),
        manifest=manifest,
        output_dir=output,
        summary_rows=summary_rows,
        table_path=Path(table_path),
    )

    return {
        "claim_level": CLAIM_LEVEL,
        "claim_upgrade_introduced": False,
        "final_gate_status": aggregate["final_gate_status"],
        "live_api_call_count": call_count,
        "model_snapshot": model_snapshot_value,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "terminal_status": "DONE" if aggregate["final_gate_status"] == "post7_extraction_quality_audit_completed" else "BLOCKED",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run POST-7 extraction quality audit.")
    parser.add_argument("--approval", required=True)
    parser.add_argument("--doc-path", default=str(DOC_PATH))
    parser.add_argument("--max-examples", type=int, default=100)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--table-path", default=str(TABLE_PATH))
    parser.add_argument("--timeout-seconds", type=int, default=90)
    args = parser.parse_args(argv)
    result = run_post7_extraction_quality_audit(
        approval=str(args.approval),
        doc_path=args.doc_path,
        max_examples=int(args.max_examples),
        output_dir=args.output_dir,
        repo_root=args.repo_root,
        table_path=args.table_path,
        timeout_seconds=int(args.timeout_seconds),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("terminal_status") == "DONE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
