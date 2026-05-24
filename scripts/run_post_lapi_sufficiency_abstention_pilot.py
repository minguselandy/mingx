from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from collections import Counter
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
from cps.evaluation.sufficiency_regime import CLAIM_LEVEL
from cps.evaluation.sufficiency_regime import CLAIM_STATUS
from cps.evaluation.sufficiency_regime import MISSING_EVIDENCE_TYPES
from cps.evaluation.sufficiency_regime import SufficiencyRegimeRecord
from cps.evaluation.sufficiency_regime import build_sufficiency_manifest
from cps.evaluation.sufficiency_regime import prompt_hashes
from cps.experiments.artifacts import stable_hash
from cps.experiments.live_api_evidence_package_factory import _env_values
from cps.experiments.live_api_evidence_package_factory import _select_live_api_client_config


CONFIG_PATH = Path("configs/post_lapi/sufficiency_abstention_config.yaml")
SCHEMA_PATH = Path("schemas/post_lapi_sufficiency_abstention.schema.json")
SOURCE_POOLS_PATH = Path("artifacts/benchmarks/hotpotqa_candidate_pools.jsonl")
PROMPT_PATH = Path("prompts/reprojection/sufficiency_abstention_v1.md")
OUTPUT_DIR = Path("artifacts/experiments/post_lapi_sufficiency_abstention")
DEFAULT_RUN_ID = "post_lapi_sufficiency_abstention_live_pilot_v1"
ALLOWED_LABELS = {"support", "insufficient", "contradict", "uncertain", "parse_failed"}
CONFIDENCE_BUCKETS = {"low", "medium", "high"}
ALLOWED_TRIGGERS = {
    "sufficient_dropped",
    "insufficient_and_answered",
    "unknown_due_to_missing_context",
    "hallucination_risk",
}
REGIME_LABELS = (
    "sufficient_kept",
    "sufficient_dropped",
    "insufficient_and_answered",
    "insufficient_and_abstained",
)
DENIED_CLAIMS = [
    "truth_validation",
    "human_calibrated_abstention",
    "measurement_validation",
    "paper_grade_evidence",
    "route_5_unlock",
    "route_8_unlock",
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


def _packets_by_label(packets: Sequence[Mapping[str, Any]], label: str) -> list[Mapping[str, Any]]:
    return [packet for packet in packets if str(packet.get("gold_support_label") or "") == label]


def _case_kind(index: int) -> str:
    return REGIME_LABELS[index % len(REGIME_LABELS)]


def _projected_packets_for_case(
    *,
    case_kind: str,
    support_packets: Sequence[Mapping[str, Any]],
    distractor_packets: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    if case_kind in {"sufficient_kept", "sufficient_dropped"}:
        return list(support_packets[:2]) or list(support_packets[:1])
    return list(distractor_packets[:2]) or list(distractor_packets[:1])


def _system_behavior(case_kind: str) -> dict[str, bool]:
    if case_kind in {"sufficient_kept", "insufficient_and_answered"}:
        return {"answer_emitted": True, "abstained": False}
    return {"answer_emitted": False, "abstained": True}


def _build_cases(*, limit: int, source_path: Path) -> list[dict[str, Any]]:
    rows = read_jsonl(source_path)
    cases: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        packets = list((row.get("candidate_pool") or {}).get("packets") or [])
        support_packets = _packets_by_label(packets, "gold_supporting")
        distractor_packets = _packets_by_label(packets, "same_context_distractor")
        if not support_packets or not distractor_packets:
            continue
        case_kind = _case_kind(len(cases))
        projected_packets = _projected_packets_for_case(
            case_kind=case_kind,
            support_packets=support_packets,
            distractor_packets=distractor_packets,
        )
        if not projected_packets:
            continue
        behavior = _system_behavior(case_kind)
        question = str(row.get("query") or "")
        answer = _target_answer(row.get("target"))
        projected_text = "\n".join(
            f"- {packet.get('content', '')}" for packet in projected_packets
        )
        case_id = f"post4-hotpotqa-{len(cases) + 1:03d}"
        cases.append(
            {
                "abstained": behavior["abstained"],
                "answer": answer,
                "answer_emitted": behavior["answer_emitted"],
                "case_id": case_id,
                "case_kind": case_kind,
                "claim_hash": _sha256_text(f"{question}\n{answer}"),
                "dataset": str(row.get("dataset") or "HotpotQA"),
                "item_id": case_id,
                "projected_context_hash": _sha256_text(projected_text),
                "projected_packet_hashes": [_packet_hash(packet) for packet in projected_packets],
                "projected_text": projected_text,
                "question": question,
                "source_instance_hash": _sha256_text(str(row.get("instance_id") or "")),
                "source_policy": "hotpotqa_first_rows_cycled_regime_cases",
                "source_row_hash": stable_hash(row),
                "source_row_index": row_index,
                "split": str(row.get("split") or ""),
            }
        )
        if len(cases) >= limit:
            break
    return cases


def _estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def _messages_for_case(case: Mapping[str, Any]) -> tuple[list[dict[str, str]], str]:
    base_prompt = (ROOT / PROMPT_PATH).read_text(encoding="utf-8").strip()
    system_prompt = "\n".join(
        [
            base_prompt,
            "",
            "Return only one minified JSON object. Use these keys: judge_label, projected_evidence_sufficient, abstain_recommended, missing_evidence_types, confidence_bucket, trigger_label.",
            "Allowed judge_label values: support, insufficient, contradict, uncertain, parse_failed.",
            "Allowed confidence_bucket values: low, medium, high.",
            "Do not include rationale, hidden reasoning, provider metadata, markdown fences, or any raw response body.",
        ]
    )
    behavior = "answered" if case["answer_emitted"] else "abstained_or_escalated"
    user_prompt = "\n".join(
        [
            "Assess whether the projected evidence is sufficient for the candidate answer and whether abstention is recommended.",
            "This is a model-adjudicated candidate operational diagnostic only.",
            "",
            f"Question: {case['question']}",
            f"Candidate answer: {case['answer']}",
            f"Observed system behavior: {behavior}",
            "",
            "Projected evidence:",
            str(case["projected_text"]),
            "",
            "Normalize missing_evidence_types to any of: entity, temporal, bridge_fact, qualifier, provenance, multi_hop_prerequisite, unknown.",
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


class DashScopeSufficiencyClient:
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
                "judge_label": "parse_failed",
                "projected_evidence_sufficient": False,
                "abstain_recommended": True,
                "missing_evidence_types": ["unknown"],
                "confidence_bucket": "low",
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
    client: DashScopeSufficiencyClient,
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


def _uncertainty_bucket(*, judge_label: str, confidence_bucket: str, parse_status: str) -> str:
    if parse_status == "parse_failed" or judge_label in {"parse_failed", "uncertain"} or confidence_bucket == "low":
        return "high_uncertainty"
    if confidence_bucket == "medium":
        return "medium_uncertainty"
    return "low_uncertainty"


def _abstention_bucket(*, abstain_recommended: bool, abstained: bool, answer_emitted: bool) -> str:
    if abstain_recommended and abstained:
        return "recommended_and_abstained"
    if abstain_recommended and answer_emitted:
        return "recommended_but_answered"
    if not abstain_recommended and abstained:
        return "abstained_without_recommendation"
    return "answer_allowed"


def _write_blocker(output_dir: Path, *, reason: str, live_api_call_count: int) -> dict[str, Any]:
    report = {
        "claim_level": CLAIM_STATUS,
        "claim_upgrade_introduced": False,
        "live_api_call_count": live_api_call_count,
        "raw_response_stored": False,
        "reason": reason,
        "route_5_locked": True,
        "route_8_locked": True,
        "schema_version": "post_lapi_sufficiency_abstention_blocker_v1",
        "terminal_status": "BLOCKED",
    }
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


def _ledger_row(regime: str, records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    subset = [record for record in records if record["regime_label"] == regime]
    total = len(subset)
    labels = Counter(str(record["judge_label"]) for record in subset)
    missing = Counter(
        missing_type
        for record in subset
        for missing_type in list(record.get("missing_evidence_types") or ["unknown"])
    )
    latencies = [float(record["latency_ms"]) for record in subset]
    token_costs = [float(record["input_token_count"] + record["output_token_count"]) for record in subset]
    insufficient_like = [
        record
        for record in subset
        if record["judge_label"] in {"insufficient", "contradict", "uncertain", "parse_failed"}
        or record["projected_evidence_sufficient"] is False
    ]
    return {
        "abstain_rate": round(_rate(sum(1 for record in subset if record["abstain_recommended"]), total), 6),
        "abstain_when_insufficient_rate": round(
            _rate(sum(1 for record in insufficient_like if record["abstain_recommended"]), len(insufficient_like)),
            6,
        ),
        "claim_gate_status": "sufficiency_abstention_candidate_ready",
        "contradict_rate": round(_rate(labels["contradict"], total), 6),
        "cost_per_case_tokens": round(_mean(token_costs), 3),
        "insufficient_rate": round(_rate(labels["insufficient"], total), 6),
        "latency_per_case_ms": round(_mean(latencies), 3),
        "missing_evidence_type_distribution": dict(sorted(missing.items())),
        "n_cases": total,
        "parse_failed_rate": round(_rate(labels["parse_failed"], total), 6),
        "regime": regime,
        "support_rate": round(_rate(labels["support"], total), 6),
        "system_abstained_rate": round(_rate(sum(1 for record in subset if record["abstained"]), total), 6),
        "uncertain_rate": round(_rate(labels["uncertain"], total), 6),
        "unsafe_answer_rate": round(_rate(sum(1 for record in subset if record["regime_label"] == "insufficient_and_answered"), total), 6),
    }


def _aggregate(records: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    total = len(records)
    labels = Counter(str(record["judge_label"]) for record in records)
    regimes = Counter(str(record["regime_label"]) for record in records)
    confidence = Counter(str(record["confidence_bucket"]) for record in records)
    uncertainty = Counter(str(record["uncertainty_bucket"]) for record in records)
    abstention = Counter(str(record["abstention_bucket"]) for record in records)
    parse_failed = labels["parse_failed"] + sum(1 for record in records if record["parse_status"] == "parse_failed" and record["judge_label"] != "parse_failed")
    parse_failure_rate = _rate(parse_failed, total)
    reason_codes: list[str] = []
    if parse_failure_rate > 0.15:
        reason_codes.append("parse_failure_rate_above_threshold")
    final_gate_status = "downgraded_to_ambiguous" if reason_codes else "sufficiency_abstention_candidate_ready"
    allowed_claims = [] if reason_codes else ["sufficiency_abstention_diagnostic"]
    input_tokens = [int(record["input_token_count"]) for record in records]
    output_tokens = [int(record["output_token_count"]) for record in records]
    latencies = [float(record["latency_ms"]) for record in records]
    total_tokens = [input_count + output_count for input_count, output_count in zip(input_tokens, output_tokens)]
    insufficient_like = [
        record
        for record in records
        if record["judge_label"] in {"insufficient", "contradict", "uncertain", "parse_failed"}
        or record["projected_evidence_sufficient"] is False
    ]
    ledger = [_ledger_row(regime, records) for regime in REGIME_LABELS]
    for row in ledger:
        row["claim_gate_status"] = final_gate_status
    aggregate = {
        "abstain_rate": _rate(sum(1 for record in records if record["abstain_recommended"]), total),
        "abstain_when_insufficient_rate": _rate(
            sum(1 for record in insufficient_like if record["abstain_recommended"]),
            len(insufficient_like),
        ),
        "abstention_bucket_counts": dict(sorted(abstention.items())),
        "allowed_claims_after_gate": allowed_claims,
        "candidate_operational_evidence_only": True,
        "claim_level": CLAIM_STATUS,
        "claim_upgrade_introduced": False,
        "confidence_bucket_counts": dict(sorted(confidence.items())),
        "cost_summary": {
            "billing_export_available": False,
            "input_tokens_total": sum(input_tokens),
            "monetary_cost_status": "not_calculated_without_provider_pricing_config",
            "output_tokens_total": sum(output_tokens),
            "token_cost_per_case_mean": round(_mean([float(value) for value in total_tokens]), 3),
            "total_tokens": sum(total_tokens),
            "usage_counts_actual_count": sum(1 for record in records if record.get("usage_count_source") == "provider_usage"),
            "usage_counts_estimated_count": sum(1 for record in records if record.get("usage_count_source") == "character_estimate"),
        },
        "denied_claims": DENIED_CLAIMS,
        "final_gate_status": final_gate_status,
        "human_calibrated_abstention_claim": False,
        "human_external_gold_label": False,
        "judge_label_counts": dict(sorted(labels.items())),
        "latency_summary_ms": {
            "max": round(max(latencies), 3) if latencies else 0.0,
            "mean": round(_mean(latencies), 3),
            "median": round(statistics.median(latencies), 3) if latencies else 0.0,
            "min": round(min(latencies), 3) if latencies else 0.0,
            "p95": round(_quantile(latencies, 0.95), 3),
        },
        "live_api_call_count": total,
        "measurement_validation_claim": False,
        "missing_evidence_type_distribution": dict(
            sorted(
                Counter(
                    missing_type
                    for record in records
                    for missing_type in list(record.get("missing_evidence_types") or ["unknown"])
                ).items()
            )
        ),
        "parse_failed_rate": parse_failure_rate,
        "raw_response_stored": False,
        "reason_codes": sorted(reason_codes),
        "regime_counts": dict(sorted(regimes.items())),
        "route_5_locked": True,
        "route_8_locked": True,
        "schema_version": "post_lapi_sufficiency_abstention_aggregate_v1",
        "support_rate": _rate(labels["support"], total),
        "insufficient_rate": _rate(labels["insufficient"], total),
        "contradict_rate": _rate(labels["contradict"], total),
        "uncertain_rate": _rate(labels["uncertain"], total),
        "truth_validation_claim": False,
        "uncertainty_bucket_counts": dict(sorted(uncertainty.items())),
        "unsafe_answer_rate": _rate(regimes["insufficient_and_answered"], total),
    }
    return aggregate, ledger


def _write_docs(*, aggregate: Mapping[str, Any], manifest: Mapping[str, Any], ledger: Sequence[Mapping[str, Any]], output_dir: Path) -> None:
    experiment_doc = ROOT / "docs/experiments/POST-LAPI-sufficiency-abstention-pilot.md"
    table_doc = ROOT / "docs/paper/post-lapi-sufficiency-abstention-table.md"
    cost = aggregate["cost_summary"]
    latency = aggregate["latency_summary_ms"]
    experiment_doc.write_text(
        "\n".join(
            [
                "# POST-LAPI Sufficiency / Abstention Pilot",
                "",
                "Goal ID: POST-4-RUN / Sufficiency and abstention pilot",
                f"Run ID: `{manifest['run_id']}`",
                f"Claim ceiling: `{CLAIM_STATUS}`",
                "",
                "## Scope",
                "",
                "This owner-approved pilot ran a bounded DashScope-compatible live API sufficiency and abstention diagnostic over HotpotQA candidate-pool cases. Outputs are model-adjudicated candidate operational evidence only. They are not truth validation, human-calibrated abstention, measurement validation, paper-grade evidence, Route 5 unlock evidence, or Route 8 unlock evidence.",
                "",
                "## Run Metadata",
                "",
                f"- Live API call count: `{aggregate['live_api_call_count']}`",
                f"- Example count: `{manifest['example_count']}`",
                f"- Model snapshot: `{manifest['model_snapshot']}`",
                f"- Endpoint family: `{manifest['endpoint_family']}`",
                f"- Endpoint: `{manifest['endpoint']}`",
                f"- Raw API responses stored: `{str(aggregate['raw_response_stored']).lower()}`",
                f"- Route 5 locked: `{str(aggregate['route_5_locked']).lower()}`",
                f"- Route 8 locked: `{str(aggregate['route_8_locked']).lower()}`",
                f"- Claim upgrade introduced: `{str(aggregate['claim_upgrade_introduced']).lower()}`",
                f"- Gate status: `{aggregate['final_gate_status']}`",
                "",
                "## Cost And Latency Summary",
                "",
                f"- Input tokens total: `{cost['input_tokens_total']}`",
                f"- Output tokens total: `{cost['output_tokens_total']}`",
                f"- Total tokens: `{cost['total_tokens']}`",
                f"- Token cost per case mean: `{cost['token_cost_per_case_mean']}`",
                f"- Monetary cost status: `{cost['monetary_cost_status']}`",
                f"- Mean latency ms: `{latency['mean']}`",
                f"- Median latency ms: `{latency['median']}`",
                f"- P95 latency ms: `{latency['p95']}`",
                "",
                "## Aggregate Metrics",
                "",
                f"- Support rate: `{aggregate['support_rate']}`",
                f"- Insufficient rate: `{aggregate['insufficient_rate']}`",
                f"- Contradict rate: `{aggregate['contradict_rate']}`",
                f"- Uncertain rate: `{aggregate['uncertain_rate']}`",
                f"- Parse failed rate: `{aggregate['parse_failed_rate']}`",
                f"- Abstain recommended rate: `{aggregate['abstain_rate']}`",
                f"- Abstain when insufficient rate: `{aggregate['abstain_when_insufficient_rate']}`",
                f"- Unsafe answer rate: `{aggregate['unsafe_answer_rate']}`",
                "",
                "## Claim Boundary",
                "",
                "The pilot may support only a sufficiency / abstention operational diagnostic. It does not establish truth validation, human-calibrated abstention, measurement validation, paper-grade evidence, or any route unlock.",
                "",
                "## Artifact Index",
                "",
                f"- `{(output_dir / 'sufficiency_records.jsonl').as_posix()}`",
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
        "# POST-LAPI Sufficiency / Abstention Table",
        "",
        f"Status: POST-4-RUN pilot result under `{CLAIM_STATUS}`",
        "",
        "These rows are model-adjudicated candidate operational diagnostics only. They do not support truth validation, human-calibrated abstention, measurement validation, paper-grade evidence, Route 5 unlock, or Route 8 unlock.",
        "",
        "| Regime | n cases | support rate | insufficient rate | contradict rate | uncertain rate | parse failed rate | abstain rate | abstain when insufficient rate | unsafe answer rate | missing evidence type distribution | cost per case | latency per case | claim gate status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for row in ledger:
        lines.append(
            "| {regime} | {n_cases} | {support_rate} | {insufficient_rate} | {contradict_rate} | {uncertain_rate} | {parse_failed_rate} | {abstain_rate} | {abstain_when_insufficient_rate} | {unsafe_answer_rate} | `{missing_evidence_type_distribution}` | {cost_per_case_tokens} | {latency_per_case_ms} | {claim_gate_status} |".format(
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
            f"| claim level | `{CLAIM_STATUS}` |",
            "| output interpretation | model-adjudicated candidate operational evidence only |",
            "| Route 5 locked | `true` |",
            "| Route 8 locked | `true` |",
            "| claim upgrade introduced | `false` |",
        ]
    )
    table_doc.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_pilot(*, max_examples: int, output_dir: Path, repo_root: Path, timeout_seconds: int) -> dict[str, Any]:
    if max_examples < 1 or max_examples > 50:
        raise ValueError("POST-4 pilot max_examples must be between 1 and 50 inclusive")
    config = _load_json(repo_root / CONFIG_PATH)
    if config.get("raw_response_storage_allowed") is not False:
        raise RuntimeError("config_allows_raw_response_storage")
    if config.get("route_5_locked") is not True or config.get("route_8_locked") is not True:
        raise RuntimeError("route_lock_config_not_true")

    output_dir.mkdir(parents=True, exist_ok=True)
    env = _env_values(repo_root)
    client_config = _select_live_api_client_config(env)
    if not client_config["available"]:
        return _write_blocker(
            output_dir,
            reason=str(client_config["blocked_reason"]),
            live_api_call_count=0,
        )

    cases = _build_cases(limit=max_examples, source_path=repo_root / SOURCE_POOLS_PATH)
    if not cases:
        return _write_blocker(output_dir, reason="no_hotpotqa_cases_available", live_api_call_count=0)
    client = DashScopeSufficiencyClient(
        api_key=str(client_config["api_key"]),
        base_url=str(client_config["base_url"]),
        model_id=str(client_config["model_id"]),
    )
    run_started = _utc_now()
    downstream_prompt_hash = _sha256_text((ROOT / PROMPT_PATH).read_text(encoding="utf-8"))
    offline_manifest = build_sufficiency_manifest(
        run_id=DEFAULT_RUN_ID,
        items=[{"item_id": case["item_id"]} for case in cases],
        downstream_prompt_template_hash=downstream_prompt_hash,
    )
    records: list[dict[str, Any]] = []
    call_count = 0
    model_snapshots: set[str] = set()

    for index, case in enumerate(cases, start=1):
        messages, prompt_hash = _messages_for_case(case)
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
        parsed = result["parsed"]
        judge_label = _normalize_label(parsed.get("judge_label") or parsed.get("label"))
        if judge_label == "parse_failed":
            regime_hint = _normalize_key(parsed.get("regime_label"))
            if regime_hint in {"sufficient_kept", "sufficient_dropped"}:
                judge_label = "support"
            elif regime_hint in {"insufficient_and_answered", "insufficient_and_abstained"}:
                judge_label = "insufficient"
        confidence_bucket = _normalize_confidence(parsed.get("confidence_bucket"))
        projected_sufficient = _normalize_bool(parsed.get("projected_evidence_sufficient"), default=judge_label == "support")
        abstain_recommended = _normalize_bool(parsed.get("abstain_recommended"), default=not projected_sufficient)
        missing_types = _normalize_missing_types(parsed.get("missing_evidence_types") or parsed.get("missing_evidence_type"))
        trigger_label = _normalize_trigger(
            parsed.get("trigger_label"),
            judge_label=judge_label,
            projected_sufficient=projected_sufficient,
            answer_emitted=bool(case["answer_emitted"]),
        )
        parse_status = str(result["parse_status"])
        if judge_label == "parse_failed":
            parse_status = "parse_failed"
            abstain_recommended = True
        payload = {
            "abstained": bool(case["abstained"]),
            "answer_emitted": bool(case["answer_emitted"]),
            "input_token_count": int(result["input_token_count"]),
            "item_id": str(case["item_id"]),
            "judge_label": judge_label,
            "missing_evidence_types": missing_types,
            "output_token_count": int(result["output_token_count"]),
            "parse_status": parse_status,
            "projected_evidence_sufficient": projected_sufficient,
            "record_id": f"{DEFAULT_RUN_ID}-{case['case_id']}",
            "trigger_label": trigger_label,
        }
        record = SufficiencyRegimeRecord.from_dict(payload).to_dict()
        record.pop("live_api_call_performed", None)
        model_snapshot = str(result["model_snapshot"])
        model_snapshots.add(model_snapshot)
        record.update(
            {
                "abstain_recommended": abstain_recommended,
                "abstention_bucket": _abstention_bucket(
                    abstain_recommended=abstain_recommended,
                    abstained=bool(case["abstained"]),
                    answer_emitted=bool(case["answer_emitted"]),
                ),
                "case_kind": str(case["case_kind"]),
                "claim_hash": str(case["claim_hash"]),
                "claim_level": CLAIM_STATUS,
                "claim_status": CLAIM_STATUS,
                "claim_upgrade_introduced": False,
                "confidence_bucket": confidence_bucket,
                "diagnostic_claim_level": CLAIM_LEVEL,
                "endpoint": str(client_config["base_url"]),
                "endpoint_family": "dashscope_openai_compatible_chat_completions",
                "live_api_call_ordinal": call_count,
                "missing_evidence_type": missing_types[0],
                "model_snapshot": model_snapshot,
                "prompt_file_hash": prompt_hashes()[PROMPT_PATH.as_posix()],
                "prompt_hash": prompt_hash,
                "projected_context_hash": str(case["projected_context_hash"]),
                "projected_packet_hashes": list(case["projected_packet_hashes"]),
                "request_payload_hash": _sha256_text(json.dumps(messages, ensure_ascii=True, sort_keys=True)),
                "source_instance_hash": str(case["source_instance_hash"]),
                "source_row_hash": str(case["source_row_hash"]),
                "source_row_index": int(case["source_row_index"]),
                "uncertainty_bucket": _uncertainty_bucket(
                    judge_label=judge_label,
                    confidence_bucket=confidence_bucket,
                    parse_status=parse_status,
                ),
                "usage_count_source": "provider_usage" if result["usage_actual"] else "character_estimate",
                "latency_ms": int(result["latency_ms"]),
            }
        )
        records.append(record)
        if index % 10 == 0 or index == len(cases):
            print(f"post4_progress {index}/{len(cases)} calls completed", flush=True)

    aggregate, ledger = _aggregate(records)
    model_snapshot_value = ",".join(sorted(model_snapshots)) if model_snapshots else str(client_config["model_id"])
    manifest = dict(offline_manifest)
    manifest.update(
        {
            "api_key_source": str(client_config["api_key_source"]),
            "claim_level": CLAIM_STATUS,
            "claim_upgrade_introduced": False,
            "config_hash": _sha256_file(repo_root / CONFIG_PATH),
            "diagnostic_claim_level": CLAIM_LEVEL,
            "endpoint": str(client_config["base_url"]),
            "endpoint_family": "dashscope_openai_compatible_chat_completions",
            "example_count": len(cases),
            "live_api_call_count": call_count,
            "live_api_call_performed": True,
            "model_snapshot": model_snapshot_value,
            "pilot_readiness_status": "live_pilot_completed",
            "raw_response_stored": False,
            "route_5_locked": True,
            "route_8_locked": True,
            "run_finished_at": _utc_now(),
            "run_started_at": run_started,
            "schema_hash": _sha256_file(repo_root / SCHEMA_PATH),
            "schema_version": "post_lapi_sufficiency_abstention_run_manifest_v1",
            "source_cases": [
                {
                    "case_kind": case["case_kind"],
                    "claim_hash": case["claim_hash"],
                    "dataset": case["dataset"],
                    "item_id": case["item_id"],
                    "projected_context_hash": case["projected_context_hash"],
                    "projected_packet_hashes": case["projected_packet_hashes"],
                    "source_instance_hash": case["source_instance_hash"],
                    "source_policy": case["source_policy"],
                    "source_row_hash": case["source_row_hash"],
                    "source_row_index": case["source_row_index"],
                    "split": case["split"],
                }
                for case in cases
            ],
            "terminal_status": aggregate["final_gate_status"],
        }
    )
    manifest["manifest_hash"] = stable_hash(manifest)
    claim_ledger = {
        "allowed_claims_after_gate": aggregate["allowed_claims_after_gate"],
        "candidate_operational_evidence_only": True,
        "claim_level": CLAIM_STATUS,
        "claim_status": CLAIM_STATUS,
        "claim_upgrade_introduced": False,
        "denied_claims": DENIED_CLAIMS,
        "final_gate_status": aggregate["final_gate_status"],
        "human_calibrated_abstention_claim": False,
        "human_external_gold_label": False,
        "measurement_validation_claim": False,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "truth_validation_claim": False,
        "treated_as": "model_adjudicated_candidate_operational_evidence_only",
    }

    write_jsonl(output_dir / "sufficiency_records.jsonl", records)
    write_json(output_dir / "regime_ledger.json", {"regimes": ledger, "schema_version": "post_lapi_sufficiency_regime_ledger_v1"})
    write_json(output_dir / "aggregate_report.json", aggregate)
    write_json(output_dir / "run_manifest.json", manifest)
    write_json(output_dir / "claim_ledger.json", claim_ledger)
    write_json(
        output_dir / "claim_gate_report.json",
        {
            "allowed_claims": aggregate["allowed_claims_after_gate"],
            "claim_status": CLAIM_STATUS,
            "denied_claims": DENIED_CLAIMS,
            "final_gate_status": aggregate["final_gate_status"],
            "raw_response_stored": False,
            "reason_codes": aggregate["reason_codes"],
            "route_5_locked": True,
            "route_8_locked": True,
        },
    )
    _write_docs(aggregate=aggregate, manifest=manifest, ledger=ledger, output_dir=output_dir)
    return {
        "claim_level": CLAIM_STATUS,
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
    parser = argparse.ArgumentParser(description="Run the POST-4 DashScope sufficiency/abstention pilot.")
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--max-examples", type=int, default=50)
    parser.add_argument("--timeout-seconds", type=int, default=90)
    args = parser.parse_args(argv)
    result = run_pilot(
        max_examples=args.max_examples,
        output_dir=Path(args.output_dir),
        repo_root=Path(args.repo_root),
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("terminal_status") == "DONE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
