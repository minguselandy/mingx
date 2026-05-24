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
from cps.experiments.artifacts import stable_hash
from cps.experiments.live_api_evidence_package_factory import _env_values
from cps.experiments.live_api_evidence_package_factory import _select_live_api_client_config
from cps.judge.judge_manifest import build_judge_run_manifest
from cps.judge.judge_manifest import prompt_hashes
from cps.judge.weak_evidence_schema import ALLOWED_CLAIM_LEVEL
from cps.judge.weak_evidence_schema import CLAIM_STATUS
from cps.judge.weak_evidence_schema import JudgeWeakEvidenceRecord
from cps.judge.weak_evidence_schema import evaluate_judge_claim_gate


CONFIG_PATH = Path("configs/post_lapi/judge_stability_pilot_config.yaml")
SCHEMA_PATH = Path("schemas/post_lapi_judge_stability.schema.json")
SOURCE_POOLS_PATH = Path("artifacts/benchmarks/hotpotqa_candidate_pools.jsonl")
OUTPUT_DIR = Path("artifacts/experiments/post_lapi_judge_stability")
BASE_PROMPT_PATH = Path("prompts/judge/weak_evidence_v1.md")
SWAPPED_PROMPT_PATH = Path("prompts/judge/weak_evidence_v1_order_swapped.md")
DEFAULT_RUN_ID = "post_lapi_judge_stability_live_pilot_v1"
ALLOWED_FLAGS = {
    "missing_context",
    "contradiction_detected",
    "abstain_recommended",
    "parse_failure",
}
DENIED_CLAIMS = [
    "human_gold",
    "human_external_gold_validation",
    "measurement_validation",
    "judge_validation",
    "paper_grade_evidence",
    "selector_superiority",
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


def _target_text(target: Any) -> str:
    if isinstance(target, str):
        return target
    return json.dumps(target, ensure_ascii=True, sort_keys=True)


def _packet_hash(packet: Mapping[str, Any]) -> str:
    content = str(packet.get("content") or "")
    existing = str(packet.get("hash") or "").strip()
    return existing or _sha256_text(content)


def _first_packet(packets: Sequence[Mapping[str, Any]], label: str) -> Mapping[str, Any] | None:
    for packet in packets:
        if str(packet.get("gold_support_label") or "") == label:
            return packet
    return None


def _build_pilot_items(*, limit: int, source_path: Path) -> list[dict[str, Any]]:
    rows = read_jsonl(source_path)
    items: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        packets = list((row.get("candidate_pool") or {}).get("packets") or [])
        support = _first_packet(packets, "gold_supporting")
        distractor = _first_packet(packets, "same_context_distractor")
        if support is None or distractor is None:
            continue
        claim_text = "\n".join(
            [
                f"Question: {row.get('query', '')}",
                f"Candidate answer: {_target_text(row.get('target', ''))}",
            ]
        )
        left_text = str(support.get("content") or "")
        right_text = str(distractor.get("content") or "")
        item_id = f"post3-hotpotqa-{len(items) + 1:03d}"
        items.append(
            {
                "item_id": item_id,
                "pair_id": item_id,
                "dataset": str(row.get("dataset") or "HotpotQA"),
                "split": str(row.get("split") or ""),
                "source_row_index": row_index,
                "source_instance_hash": _sha256_text(str(row.get("instance_id") or "")),
                "source_row_hash": stable_hash(row),
                "claim_text": claim_text,
                "claim_hash": _sha256_text(claim_text),
                "left_text": left_text,
                "right_text": right_text,
                "left_evidence_hash": _packet_hash(support),
                "right_evidence_hash": _packet_hash(distractor),
                "left_packet_hash": _sha256_text(str(support.get("packet_id") or "")),
                "right_packet_hash": _sha256_text(str(distractor.get("packet_id") or "")),
                "source_policy": "hotpotqa_candidate_pool_first_support_first_distractor",
            }
        )
        if len(items) >= limit:
            break
    return items


def _estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def _prompt_for_request(spec: Mapping[str, Any]) -> tuple[Path, str, str]:
    prompt_path = SWAPPED_PROMPT_PATH if bool(spec["order_swap_enabled"]) else BASE_PROMPT_PATH
    base_prompt = (ROOT / prompt_path).read_text(encoding="utf-8")
    rubric_paraphrase_id = str(spec["rubric_paraphrase_id"])
    if rubric_paraphrase_id == "p1":
        paraphrase = (
            "Rubric paraphrase p1: use a conservative reading. Mark support only "
            "when supplied evidence directly supports the claim; otherwise prefer "
            "insufficient or uncertain. This remains weak model-adjudicated "
            "candidate evidence only."
        )
    else:
        paraphrase = (
            "Rubric paraphrase p0: apply the prompt as written. This remains weak "
            "model-adjudicated candidate evidence only."
        )
    system_prompt = base_prompt.strip() + "\n\n" + paraphrase
    return prompt_path, system_prompt, _sha256_text(system_prompt)


def _messages_for_request(item: Mapping[str, Any], spec: Mapping[str, Any]) -> tuple[list[dict[str, str]], str, str]:
    prompt_path, system_prompt, actual_prompt_hash = _prompt_for_request(spec)
    if bool(spec["order_swap_enabled"]):
        candidate_a = str(item["right_text"])
        candidate_b = str(item["left_text"])
        order_note = "The input order is swapped for the stability check."
    else:
        candidate_a = str(item["left_text"])
        candidate_b = str(item["right_text"])
        order_note = "The input order is the original candidate order."

    user_prompt = "\n".join(
        [
            order_note,
            "Assign one normalized weak-evidence label for this candidate pair.",
            "Use support only if the supplied candidate evidence directly supports the claim.",
            "Use contradict if supplied evidence contradicts the claim.",
            "Use insufficient if neither candidate gives enough support.",
            "Use uncertain if the evidence is ambiguous.",
            "",
            "Claim:",
            str(item["claim_text"]),
            "",
            "Candidate A evidence:",
            candidate_a,
            "",
            "Candidate B evidence:",
            candidate_b,
            "",
            "Return only JSON with keys label, confidence_bucket, flags, rationale.",
        ]
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return messages, prompt_path.as_posix(), actual_prompt_hash


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
    prompt_keys = ("prompt_tokens", "input_tokens")
    output_keys = ("completion_tokens", "output_tokens")
    prompt_tokens = next((usage.get(key) for key in prompt_keys if key in usage), None)
    output_tokens = next((usage.get(key) for key in output_keys if key in usage), None)
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


class DashScopeJudgeClient:
    def __init__(self, *, api_key: str, base_url: str, model_id: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id

    def judge(self, *, messages: Sequence[Mapping[str, str]], timeout_seconds: int) -> dict[str, Any]:
        payload = {
            "enable_thinking": False,
            "max_tokens": 128,
            "messages": [dict(message) for message in messages],
            "model": self.model_id,
            "n": 1,
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
        prompt_estimate = _estimate_tokens(prompt_text)
        output_estimate = _estimate_tokens(content) if content else 0
        input_tokens, output_tokens, usage_actual = _usage_counts(
            response_payload.get("usage") or {},
            prompt_estimate,
            output_estimate,
        )
        if parsed is None:
            parsed = {
                "label": "parse_failed",
                "confidence_bucket": "low",
                "flags": ["parse_failure"],
            }
            parse_status = "parse_failed"
        else:
            parse_status = "parsed"
        return {
            "parsed": dict(parsed),
            "parse_status": parse_status,
            "input_token_count": input_tokens,
            "output_token_count": output_tokens,
            "usage_actual": usage_actual,
            "latency_ms": latency_ms,
            "model_snapshot": str(response_payload.get("model") or self.model_id),
        }


def _judge_with_retries(
    client: DashScopeJudgeClient,
    *,
    messages: Sequence[Mapping[str, str]],
    timeout_seconds: int,
    attempts: int = 3,
) -> dict[str, Any]:
    last_reason = "dashscope_live_api_unknown_failure"
    for attempt_index in range(attempts):
        try:
            return client.judge(messages=messages, timeout_seconds=timeout_seconds)
        except RuntimeError as exc:
            last_reason = str(exc)
            if attempt_index + 1 >= attempts:
                break
            time.sleep(min(8, 2 ** attempt_index))
    raise RuntimeError(last_reason)


def _normalize_flags(value: Any) -> list[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list | tuple):
        values = [str(item) for item in value]
    else:
        values = []
    return sorted({flag for flag in values if flag in ALLOWED_FLAGS})


def _condition_tags(record: Mapping[str, Any]) -> list[str]:
    tags = []
    if not record["order_swap"] and record["duplicate_index"] == 0 and record["rubric_paraphrase_id"] == "p0":
        tags.append("original_order")
    if record["order_swap"]:
        tags.append("order_swapped")
    if record["duplicate_index"] > 0:
        tags.append("duplicate_judging")
    if record["rubric_paraphrase_id"] != "p0":
        tags.append("rubric_paraphrase")
    return tags or ["original_order"]


def _condition_name(record: Mapping[str, Any]) -> str:
    tags = _condition_tags(record)
    for candidate in ("original_order", "order_swapped", "duplicate_judging", "rubric_paraphrase"):
        if candidate in tags:
            return candidate
    return tags[0]


def _write_blocker(output_dir: Path, *, reason: str, live_api_call_count: int) -> dict[str, Any]:
    report = {
        "claim_level": CLAIM_STATUS,
        "claim_upgrade_introduced": False,
        "live_api_call_count": live_api_call_count,
        "raw_response_stored": False,
        "reason": reason,
        "route_5_locked": True,
        "route_8_locked": True,
        "schema_version": "post_lapi_judge_stability_blocker_v1",
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


def _confidence_bucket_stability(records: Sequence[Mapping[str, Any]]) -> float:
    groups: dict[str, list[str]] = {}
    for record in records:
        groups.setdefault(str(record["item_id"]), []).append(str(record["confidence_bucket"]))
    checks = []
    for buckets in groups.values():
        if len(buckets) <= 1:
            continue
        checks.append(len(set(buckets)) == 1)
    return _mean([1.0 if value else 0.0 for value in checks]) if checks else 1.0


def _condition_subset(records: Sequence[Mapping[str, Any]], condition: str) -> list[Mapping[str, Any]]:
    if condition == "original_order":
        return [
            record
            for record in records
            if not record["order_swap"]
            and record["duplicate_index"] == 0
            and record["rubric_paraphrase_id"] == "p0"
        ]
    if condition == "order_swapped":
        return [record for record in records if record["order_swap"]]
    if condition == "duplicate_judging":
        return [record for record in records if record["duplicate_index"] > 0]
    if condition == "rubric_paraphrase":
        return [record for record in records if record["rubric_paraphrase_id"] != "p0"]
    return list(records)


def _condition_rows(records: Sequence[Mapping[str, Any]], gate: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for condition in ("original_order", "order_swapped", "duplicate_judging", "rubric_paraphrase"):
        subset = _condition_subset(records, condition)
        latencies = [float(record["latency_ms"]) for record in subset]
        total_tokens = [float(record["input_token_count"] + record["output_token_count"]) for record in subset]
        parse_failed = sum(1 for record in subset if record["parse_status"] == "parse_failed")
        uncertain = sum(1 for record in subset if record["normalized_label"] == "uncertain")
        rows.append(
            {
                "condition": condition,
                "n_judgments": len(subset),
                "parse_success_rate": round(1.0 - (parse_failed / len(subset) if subset else 1.0), 6),
                "duplicate_agreement": round(float(gate["duplicate_agreement"]), 6)
                if condition == "duplicate_judging"
                else None,
                "order_swap_agreement": round(float(gate["order_swap_agreement"]), 6)
                if condition == "order_swapped"
                else None,
                "rubric_paraphrase_agreement": round(float(gate["rubric_paraphrase_agreement"]), 6)
                if condition == "rubric_paraphrase"
                else None,
                "confidence_bucket_stability": round(_confidence_bucket_stability(subset), 6),
                "position_bias_rate": round(1.0 - float(gate["order_swap_agreement"]), 6)
                if condition == "order_swapped"
                else None,
                "uncertain_rate": round(uncertain / len(subset), 6) if subset else 0.0,
                "parse_failed_rate": round(parse_failed / len(subset), 6) if subset else 1.0,
                "token_cost_per_judgment": round(_mean(total_tokens), 3),
                "latency_ms_per_judgment": round(_mean(latencies), 3),
                "claim_gate_status": str(gate["final_gate_status"]),
            }
        )
    return rows


def _aggregate_report(records: Sequence[Mapping[str, Any]], gate: Mapping[str, Any]) -> dict[str, Any]:
    latencies = [float(record["latency_ms"]) for record in records]
    input_tokens = [int(record["input_token_count"]) for record in records]
    output_tokens = [int(record["output_token_count"]) for record in records]
    labels = Counter(str(record["normalized_label"]) for record in records)
    confidence = Counter(str(record["confidence_bucket"]) for record in records)
    total_tokens = [input_count + output_count for input_count, output_count in zip(input_tokens, output_tokens)]
    condition_rows = _condition_rows(records, gate)
    return {
        "aggregate_label_status": gate["aggregate_label_status"],
        "allowed_claim_level": ALLOWED_CLAIM_LEVEL,
        "allowed_claims_after_gate": gate["allowed_claims"],
        "claim_level": CLAIM_STATUS,
        "claim_upgrade_introduced": False,
        "condition_rows": condition_rows,
        "confidence_bucket_counts": dict(sorted(confidence.items())),
        "confidence_bucket_stability": round(_confidence_bucket_stability(records), 6),
        "cost_summary": {
            "billing_export_available": False,
            "input_tokens_total": sum(input_tokens),
            "latency_count": len(latencies),
            "monetary_cost_status": "not_calculated_without_provider_pricing_config",
            "output_tokens_total": sum(output_tokens),
            "token_cost_per_judgment_mean": round(_mean([float(value) for value in total_tokens]), 3),
            "total_tokens": sum(total_tokens),
            "usage_counts_actual_count": sum(1 for record in records if record.get("usage_count_source") == "provider_usage"),
            "usage_counts_estimated_count": sum(1 for record in records if record.get("usage_count_source") == "character_estimate"),
        },
        "denied_claims": DENIED_CLAIMS,
        "duplicate_agreement": gate["duplicate_agreement"],
        "final_gate_status": gate["final_gate_status"],
        "label_counts": dict(sorted(labels.items())),
        "latency_summary_ms": {
            "mean": round(_mean(latencies), 3),
            "median": round(statistics.median(latencies), 3) if latencies else 0.0,
            "p95": round(_quantile(latencies, 0.95), 3),
            "max": round(max(latencies), 3) if latencies else 0.0,
            "min": round(min(latencies), 3) if latencies else 0.0,
        },
        "live_api_call_count": len(records),
        "measurement_validation_claim": False,
        "order_swap_agreement": gate["order_swap_agreement"],
        "parse_failure_rate": gate["parse_failure_rate"],
        "position_bias_rate": round(1.0 - float(gate["order_swap_agreement"]), 6),
        "raw_response_stored": False,
        "reason_codes": gate["reason_codes"],
        "route_5_locked": True,
        "route_8_locked": True,
        "rubric_paraphrase_agreement": gate["rubric_paraphrase_agreement"],
        "schema_version": "post_lapi_judge_stability_aggregate_v1",
        "treated_as": "weak_model_adjudicated_candidate_evidence_only",
        "uncertain_rate": (labels.get("uncertain", 0) / len(records)) if records else 0.0,
    }


def _write_docs(*, aggregate: Mapping[str, Any], manifest: Mapping[str, Any], output_dir: Path) -> None:
    rows = list(aggregate["condition_rows"])
    docs_experiment = ROOT / "docs/experiments/POST-LAPI-judge-stability-pilot.md"
    docs_table = ROOT / "docs/paper/post-lapi-judge-stability-table.md"
    gate_status = str(aggregate["final_gate_status"])
    allowed_claims = ", ".join(aggregate["allowed_claims_after_gate"]) or "suppressed by stability gate"
    cost = aggregate["cost_summary"]
    latency = aggregate["latency_summary_ms"]
    docs_experiment.write_text(
        "\n".join(
            [
                "# POST-LAPI Judge Weak-Evidence Stability Pilot",
                "",
                "Goal ID: POST-3-RUN / Judge weak-evidence stability pilot",
                f"Run ID: `{manifest['run_id']}`",
                f"Claim ceiling: `{CLAIM_STATUS}`",
                "",
                "## Scope",
                "",
                "This owner-approved pilot ran a bounded DashScope-compatible live API judge stability diagnostic over 30 examples. Outputs are weak/model-adjudicated candidate evidence only. They are not human or external gold labels, measurement validation, judge validation, paper-grade evidence, selector superiority evidence, or Route 5/Route 8 unlock evidence.",
                "",
                "## Run Metadata",
                "",
                f"- Live API call count: `{aggregate['live_api_call_count']}`",
                f"- Example count: `{manifest['example_count']}`",
                f"- Model snapshot: `{manifest['judge_model_snapshot']}`",
                f"- Endpoint family: `{manifest['endpoint_family']}`",
                f"- Endpoint: `{manifest['endpoint']}`",
                f"- Raw API responses stored: `{str(aggregate['raw_response_stored']).lower()}`",
                f"- Route 5 locked: `{str(aggregate['route_5_locked']).lower()}`",
                f"- Route 8 locked: `{str(aggregate['route_8_locked']).lower()}`",
                f"- Claim upgrade introduced: `{str(aggregate['claim_upgrade_introduced']).lower()}`",
                f"- Gate status: `{gate_status}`",
                f"- Allowed claim after gate: `{allowed_claims}`",
                "",
                "## Cost And Latency Summary",
                "",
                f"- Input tokens total: `{cost['input_tokens_total']}`",
                f"- Output tokens total: `{cost['output_tokens_total']}`",
                f"- Total tokens: `{cost['total_tokens']}`",
                f"- Token cost per judgment mean: `{cost['token_cost_per_judgment_mean']}`",
                f"- Monetary cost status: `{cost['monetary_cost_status']}`",
                f"- Mean latency ms: `{latency['mean']}`",
                f"- Median latency ms: `{latency['median']}`",
                f"- P95 latency ms: `{latency['p95']}`",
                "",
                "## Stability Metrics",
                "",
                f"- Parse failure rate: `{aggregate['parse_failure_rate']}`",
                f"- Duplicate agreement: `{aggregate['duplicate_agreement']}`",
                f"- Order-swap agreement: `{aggregate['order_swap_agreement']}`",
                f"- Rubric paraphrase agreement: `{aggregate['rubric_paraphrase_agreement']}`",
                f"- Confidence bucket stability: `{aggregate['confidence_bucket_stability']}`",
                f"- Position bias rate: `{aggregate['position_bias_rate']}`",
                f"- Uncertain rate: `{aggregate['uncertain_rate']}`",
                "",
                "## Claim Boundary",
                "",
                "If stability thresholds fail, the model-adjudicated weak-evidence claim is suppressed as ambiguous. If they pass, the strongest permitted statement remains weak operational diagnostic evidence from model adjudication only.",
                "",
                "Denied claims remain denied: human gold, human/external gold validation, measurement validation, judge validation, paper-grade evidence, selector superiority, Route 5 unlock, and Route 8 unlock.",
                "",
                "## Artifact Index",
                "",
                f"- `{(output_dir / 'judgments.jsonl').as_posix()}`",
                f"- `{(output_dir / 'run_manifest.json').as_posix()}`",
                f"- `{(output_dir / 'aggregate_report.json').as_posix()}`",
                f"- `{(output_dir / 'claim_ledger.json').as_posix()}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    table_lines = [
        "# POST-LAPI Judge Weak-Evidence Stability Table",
        "",
        f"Status: POST-3-RUN pilot result under `{CLAIM_STATUS}`",
        "",
        "These rows are weak model-adjudicated candidate diagnostics only. They do not support human/external gold validation, measurement validation, judge validation, paper-grade evidence, selector superiority, Route 5 unlock, or Route 8 unlock.",
        "",
        "| Condition | n judgments | parse success rate | duplicate agreement | order-swap agreement | rubric paraphrase agreement | confidence bucket stability | position bias rate | uncertain rate | parse failed rate | token cost per judgment | latency ms per judgment | claim gate status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        table_lines.append(
            "| {condition} | {n_judgments} | {parse_success_rate} | {duplicate_agreement} | {order_swap_agreement} | {rubric_paraphrase_agreement} | {confidence_bucket_stability} | {position_bias_rate} | {uncertain_rate} | {parse_failed_rate} | {token_cost_per_judgment} | {latency_ms_per_judgment} | {claim_gate_status} |".format(
                **{key: ("n/a" if value is None else value) for key, value in row.items()}
            )
        )
    table_lines.extend(
        [
            "",
            "## Boundary Fields",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| live API call count | `{aggregate['live_api_call_count']}` |",
            f"| model snapshot | `{manifest['judge_model_snapshot']}` |",
            f"| endpoint | `{manifest['endpoint']}` |",
            "| raw API responses stored | `false` |",
            f"| claim level | `{CLAIM_STATUS}` |",
            "| output interpretation | weak/model-adjudicated candidate evidence only |",
            "| Route 5 locked | `true` |",
            "| Route 8 locked | `true` |",
            "| claim upgrade introduced | `false` |",
        ]
    )
    docs_table.write_text("\n".join(table_lines) + "\n", encoding="utf-8")


def run_pilot(*, max_examples: int, output_dir: Path, repo_root: Path, timeout_seconds: int) -> dict[str, Any]:
    if max_examples < 30 or max_examples > 50:
        raise ValueError("POST-3 pilot max_examples must be between 30 and 50 inclusive")

    config = _load_json(repo_root / CONFIG_PATH)
    if config.get("raw_response_storage_allowed") is not False:
        raise RuntimeError("config_allows_raw_response_storage")
    if config.get("route_5_locked") is not True or config.get("route_8_locked") is not True:
        raise RuntimeError("route_lock_config_not_true")

    env = _env_values(repo_root)
    client_config = _select_live_api_client_config(env)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not client_config["available"]:
        return _write_blocker(
            output_dir,
            reason=str(client_config["blocked_reason"]),
            live_api_call_count=0,
        )

    items = _build_pilot_items(limit=max_examples, source_path=repo_root / SOURCE_POOLS_PATH)
    if len(items) < 30:
        return _write_blocker(
            output_dir,
            reason=f"insufficient_pilot_examples:{len(items)}",
            live_api_call_count=0,
        )

    manifest_items = [
        {
            "item_id": item["item_id"],
            "left_evidence_hash": item["left_evidence_hash"],
            "right_evidence_hash": item["right_evidence_hash"],
        }
        for item in items
    ]
    item_by_id = {item["item_id"]: item for item in items}
    client = DashScopeJudgeClient(
        api_key=str(client_config["api_key"]),
        base_url=str(client_config["base_url"]),
        model_id=str(client_config["model_id"]),
    )
    run_started = _utc_now()
    run_manifest = build_judge_run_manifest(
        run_id=DEFAULT_RUN_ID,
        items=manifest_items,
        judge_model_snapshot=str(client_config["model_id"]),
    )
    requests_to_run = run_manifest["judgment_requests"]
    records: list[dict[str, Any]] = []
    call_count = 0

    for index, spec in enumerate(requests_to_run, start=1):
        item = item_by_id[str(spec["item_id"])]
        messages, prompt_path, actual_prompt_hash = _messages_for_request(item, spec)
        try:
            result = _judge_with_retries(
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
        payload = {
            "judgment_id": str(spec["judgment_id"]),
            "item_id": str(spec["item_id"]),
            "pair_id": str(spec["pair_id"]),
            "judge_model_snapshot": str(result["model_snapshot"]),
            "prompt_hash": actual_prompt_hash,
            "rubric_version": str(spec["rubric_version"]),
            "rubric_paraphrase_id": str(spec["rubric_paraphrase_id"]),
            "order_swap": bool(spec["order_swap_enabled"]),
            "duplicate_index": int(spec["duplicate_index"]),
            "normalized_label": str(parsed.get("label") or "parse_failed"),
            "confidence_bucket": str(parsed.get("confidence_bucket") or "low"),
            "flags": _normalize_flags(parsed.get("flags")),
            "parse_status": str(result["parse_status"]),
            "raw_response_stored": False,
            "input_token_count": int(result["input_token_count"]),
            "output_token_count": int(result["output_token_count"]),
        }
        record = JudgeWeakEvidenceRecord.from_dict(payload).to_dict()
        record.update(
            {
                "condition": _condition_name(record),
                "condition_tags": _condition_tags(record),
                "claim_hash": item["claim_hash"],
                "left_evidence_hash": item["left_evidence_hash"],
                "right_evidence_hash": item["right_evidence_hash"],
                "prompt_path": prompt_path,
                "prompt_file_hash": prompt_hashes()[prompt_path],
                "request_payload_hash": _sha256_text(json.dumps(messages, ensure_ascii=True, sort_keys=True)),
                "latency_ms": int(result["latency_ms"]),
                "usage_count_source": "provider_usage" if result["usage_actual"] else "character_estimate",
                "endpoint_family": "dashscope_openai_compatible_chat_completions",
                "counts_as_human_or_external_gold": False,
                "measurement_validation_claim": False,
                "claim_upgrade_introduced": False,
                "route_5_locked": True,
                "route_8_locked": True,
            }
        )
        records.append(record)
        if index % 10 == 0 or index == len(requests_to_run):
            print(f"post3_progress {index}/{len(requests_to_run)} calls completed", flush=True)

    gate = evaluate_judge_claim_gate(records)
    aggregate = _aggregate_report(records, gate)
    model_snapshots = sorted({str(record["judge_model_snapshot"]) for record in records})
    endpoint = str(client_config["base_url"])
    final_manifest = dict(run_manifest)
    final_manifest.update(
        {
            "api_key_source": str(client_config["api_key_source"]),
            "claim_upgrade_introduced": False,
            "config_hash": _sha256_file(repo_root / CONFIG_PATH),
            "endpoint": endpoint,
            "endpoint_family": "dashscope_openai_compatible_chat_completions",
            "example_count": len(items),
            "judge_model_snapshot": ",".join(model_snapshots) if model_snapshots else str(client_config["model_id"]),
            "live_api_call_count": call_count,
            "live_api_call_performed": True,
            "raw_response_stored": False,
            "request_count": len(requests_to_run),
            "route_5_locked": True,
            "route_8_locked": True,
            "run_finished_at": _utc_now(),
            "run_started_at": run_started,
            "schema_hash": _sha256_file(repo_root / SCHEMA_PATH),
            "schema_version": "post_lapi_judge_stability_run_manifest_v1",
            "source_items": [
                {
                    "claim_hash": item["claim_hash"],
                    "dataset": item["dataset"],
                    "item_id": item["item_id"],
                    "left_evidence_hash": item["left_evidence_hash"],
                    "right_evidence_hash": item["right_evidence_hash"],
                    "source_instance_hash": item["source_instance_hash"],
                    "source_policy": item["source_policy"],
                    "source_row_hash": item["source_row_hash"],
                    "source_row_index": item["source_row_index"],
                    "split": item["split"],
                }
                for item in items
            ],
            "terminal_status": str(gate["final_gate_status"]),
        }
    )
    final_manifest["manifest_hash"] = stable_hash(final_manifest)
    claim_ledger = {
        "allowed_claim_level": ALLOWED_CLAIM_LEVEL,
        "allowed_claims_after_gate": gate["allowed_claims"],
        "claim_level": CLAIM_STATUS,
        "claim_status": CLAIM_STATUS,
        "claim_upgrade_introduced": False,
        "counts_as_human_or_external_gold": False,
        "denied_claims": DENIED_CLAIMS,
        "final_gate_status": gate["final_gate_status"],
        "measurement_validation_claim": False,
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "treated_as": "weak_model_adjudicated_candidate_evidence_only",
    }

    write_jsonl(output_dir / "judgments.jsonl", records)
    write_json(output_dir / "run_manifest.json", final_manifest)
    write_json(output_dir / "aggregate_report.json", aggregate)
    write_json(output_dir / "claim_gate_report.json", gate)
    write_json(output_dir / "claim_ledger.json", claim_ledger)
    _write_docs(aggregate=aggregate, manifest=final_manifest, output_dir=output_dir)
    return {
        "claim_level": CLAIM_STATUS,
        "claim_upgrade_introduced": False,
        "endpoint": endpoint,
        "final_gate_status": gate["final_gate_status"],
        "live_api_call_count": call_count,
        "model_snapshot": final_manifest["judge_model_snapshot"],
        "raw_response_stored": False,
        "route_5_locked": True,
        "route_8_locked": True,
        "terminal_status": "DONE",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the POST-3 DashScope judge stability pilot.")
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--max-examples", type=int, default=30)
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
