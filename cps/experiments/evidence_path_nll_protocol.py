from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from copy import deepcopy
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Mapping
from typing import Sequence

from cps.benchmarks.common import read_jsonl
from cps.benchmarks.common import write_json
from cps.benchmarks.common import write_jsonl
from cps.benchmarks.hashing import stable_hash


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
TERMINAL_STATUS = "EVIDENCE_PATH_NLL_PROTOCOL_FREEZE_COMPLETED"
ARTIFACT_DIR = Path("artifacts/experiments/evidence_path_nll_protocol")
HOTPOTQA_CANDIDATE_POOLS = Path("artifacts/benchmarks/hotpotqa_candidate_pools.jsonl")
ROUTE4A_ROWS = Path("artifacts/experiments/route4_bridge/bridge_rows.jsonl")
LOGPROBE_READINESS = Path("artifacts/experiments/logprobe_bridge_repair_readiness/readiness_report.json")
LOGPROBE_TARGET_DECISION = Path("artifacts/experiments/logprobe_target_redesign/target_decision.json")

REQUIRED_CONTRACT_FIELDS = (
    "target_type",
    "target_representation",
    "target_format_hash",
    "target_text_template_hash",
    "prompt_template_hash",
    "materialization_policy_hash",
    "teacher_forced_scoring_required",
    "scoring_policy",
    "target_provenance",
    "row_provenance",
)

LiveScorer = Callable[..., Mapping[str, Any]]


class EvidencePathProtocolInputMissingError(RuntimeError):
    """Raised before writing EPN outputs when required existing artifacts are absent."""


def _resolve(root: str | Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else Path(root) / candidate


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.name if candidate.is_absolute() else candidate.as_posix()


def _span_string(span: Mapping[str, Any]) -> str:
    return f"{span.get('unit', 'sentence')}:{span.get('start', 0)}-{span.get('end', 0)}"


def _contains_fever(payload: Any) -> bool:
    stack = [payload]
    while stack:
        current = stack.pop()
        if isinstance(current, Mapping):
            stack.extend(current.values())
            continue
        if isinstance(current, list | tuple | set):
            stack.extend(current)
            continue
        if "fever" in str(current).casefold():
            return True
    return False


def _target_text_from_packets(gold_packets: Sequence[Mapping[str, Any]]) -> str:
    lines = ["EVIDENCE_PATH_V1"]
    for index, packet in enumerate(gold_packets, start=1):
        source_doc_id = str(packet.get("source_doc_id") or "")
        packet_id = str(packet.get("packet_id") or "")
        packet_hash = str(packet.get("hash") or stable_hash({"packet": packet_id, "source_doc_id": source_doc_id}))
        lines.append(f"{index}\t{source_doc_id}\t{_span_string(dict(packet.get('span') or {}))}\t{packet_id}\t{packet_hash}")
    return "\n".join(lines)


def _prompt_from_instance(instance: Mapping[str, Any], gold_packets: Sequence[Mapping[str, Any]]) -> str:
    evidence_lines = []
    for index, packet in enumerate(gold_packets, start=1):
        source_doc_id = str(packet.get("source_doc_id") or "")
        evidence_lines.append(f"[{index}] {source_doc_id} {_span_string(dict(packet.get('span') or {}))}: {packet.get('content', '')}")
    return "\n".join(
        [
            "Score the fixed evidence-path target with teacher-forced log probabilities.",
            "Return exactly the evidence path target and no extra text.",
            "",
            f"Question: {instance.get('query', '')}",
            "",
            "Evidence packets:",
            "\n".join(evidence_lines),
            "",
            "Target:",
        ]
    )


def build_evidence_path_target_contract() -> dict[str, Any]:
    target_payload = {
        "canonical_ordering": "gold_supporting_packets_sorted_by_hop_index_then_packet_id",
        "line_format": "rank<TAB>source_doc_id<TAB>span<TAB>packet_id<TAB>packet_hash",
        "schema": "EVIDENCE_PATH_V1",
        "target_representation": "hotpotqa_gold_support_source_doc_span_packet_path_v1",
        "target_type": "evidence_path_nll",
    }
    prompt_template = (
        "Score the fixed evidence-path target with teacher-forced log probabilities.\n"
        "Return exactly the evidence path target and no extra text.\n\n"
        "Question: {query}\n\nEvidence packets:\n{evidence_packets}\n\nTarget:"
    )
    materialization_policy = {
        "context_policy": "route4a_materialized_context_with_source_boundaries",
        "target_text_storage": "hash_and_metadata_only",
        "target_text_use": "in_memory_teacher_forced_scoring_only",
    }
    contract = {
        "claim_status": CLAIM_STATUS,
        "contract_status": "canonical_protocol_specification_only",
        "disabled_decisions": ["SWITCH_TO_FEVER_LABEL_NLL"],
        "fever_disabled": True,
        "lp6_bridge_repair_run": False,
        "materialization_policy": materialization_policy,
        "materialization_policy_hash": stable_hash(materialization_policy),
        "prompt_template_hash": stable_hash({"prompt_template": prompt_template}),
        "row_provenance": {
            "candidate_pools": HOTPOTQA_CANDIDATE_POOLS.as_posix(),
            "route_rows": ROUTE4A_ROWS.as_posix(),
            "source": "existing_hotpotqa_candidate_pools_and_route4a_rows",
        },
        "route5_locked": True,
        "route8_locked": True,
        "schema_version": "evidence_path_nll_target_contract_v1",
        "scoring_policy": {
            "api_response_storage": "forbidden",
            "normalized_outputs_only": True,
            "scorer_requires_logprobs": True,
            "store_raw_api_response": False,
            "teacher_forced": True,
        },
        "target_format": target_payload,
        "target_format_hash": stable_hash(target_payload),
        "target_provenance": {
            "active_dataset": "HotpotQA",
            "active_split": "dev_distractor",
            "disabled_dataset": "FEVER",
            "target_source": "gold_supporting_candidate_pool_packets",
        },
        "target_representation": "hotpotqa_gold_support_source_doc_span_packet_path_v1",
        "target_text_template_hash": stable_hash({"target_text_template": target_payload["line_format"]}),
        "target_type": "evidence_path_nll",
        "teacher_forced_scoring_required": True,
    }
    contract["contract_hash"] = stable_hash({field: contract[field] for field in REQUIRED_CONTRACT_FIELDS})
    return contract


def validate_evidence_path_target_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for field in REQUIRED_CONTRACT_FIELDS:
        if field not in contract or contract.get(field) in ("", None, {}, []):
            errors.append(f"missing_{field}")
    if contract.get("teacher_forced_scoring_required") is not True:
        errors.append("teacher_forced_scoring_required_false")
    if contract.get("claim_status") != CLAIM_STATUS:
        errors.append("claim_status_not_operational_utility_only")
    if contract.get("target_type") != "evidence_path_nll":
        errors.append("target_type_not_evidence_path_nll")
    if contract.get("route5_locked") is not True:
        errors.append("route5_unlocked")
    if contract.get("route8_locked") is not True:
        errors.append("route8_unlocked")
    active_target_payload = {
        "row_provenance": contract.get("row_provenance"),
        "target_format": contract.get("target_format"),
        "target_provenance": {
            key: value
            for key, value in dict(contract.get("target_provenance") or {}).items()
            if key != "disabled_dataset"
        },
        "target_representation": contract.get("target_representation"),
        "target_type": contract.get("target_type"),
    }
    if _contains_fever(active_target_payload):
        errors.append("fever_selected_as_active_target")
    expected_target_hash = stable_hash(dict(contract.get("target_format") or {}))
    if contract.get("target_format_hash") and contract.get("target_format_hash") != expected_target_hash:
        errors.append("target_format_hash_mismatch")
    scoring_policy = dict(contract.get("scoring_policy") or {})
    if scoring_policy.get("store_raw_api_response") is not False:
        errors.append("raw_api_response_storage_not_forbidden")
    return {
        "claim_status": CLAIM_STATUS,
        "errors": errors,
        "passed": not errors,
        "schema_version": "evidence_path_nll_target_contract_validation_v1",
    }


def _instance_key(record: Mapping[str, Any]) -> tuple[str, str]:
    pool = dict(record.get("candidate_pool") or {})
    return (str(record.get("instance_id") or ""), str(pool.get("candidate_pool_hash") or ""))


def _route_row_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return (str(row.get("original_instance_id") or row.get("instance_id") or ""), str(row.get("candidate_pool_hash") or ""))


def _sorted_gold_packets(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    pool = dict(record.get("candidate_pool") or {})
    packets = [dict(packet) for packet in pool.get("packets") or []]
    gold_packets = [packet for packet in packets if str(packet.get("gold_support_label")) == "gold_supporting"]
    return sorted(
        gold_packets,
        key=lambda packet: (
            1 if packet.get("hop_index") is None else 0,
            int(packet.get("hop_index") or 0),
            str(packet.get("packet_id") or ""),
        ),
    )


def _build_rows_with_materializations(
    candidate_pool_records: Sequence[Mapping[str, Any]],
    route4_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, str]]]:
    candidate_pool_index = {_instance_key(record): dict(record) for record in candidate_pool_records}
    rows: list[dict[str, Any]] = []
    materializations: dict[str, dict[str, str]] = {}
    missing_candidate_pool = 0
    missing_gold_path = 0
    missing_span = 0
    duplicate_target_hashes: set[str] = set()
    seen_target_hashes: set[str] = set()

    for route_row in sorted(route4_rows, key=lambda row: stable_hash(row)):
        key = _route_row_key(route_row)
        instance = candidate_pool_index.get(key)
        if instance is None:
            missing_candidate_pool += 1
            continue
        gold_packets = _sorted_gold_packets(instance)
        if not gold_packets:
            missing_gold_path += 1
            continue
        if any(not dict(packet.get("span") or {}) for packet in gold_packets):
            missing_span += 1
            continue
        target_text = _target_text_from_packets(gold_packets)
        target_text_hash = stable_hash({"target_text": target_text})
        if target_text_hash in seen_target_hashes:
            duplicate_target_hashes.add(target_text_hash)
        seen_target_hashes.add(target_text_hash)
        target_row_id = stable_hash(
            {
                "candidate_pool_hash": key[1],
                "evidence_path_packet_ids": [str(packet.get("packet_id") or "") for packet in gold_packets],
                "original_instance_id": key[0],
                "target_text_hash": target_text_hash,
            }
        )
        row = {
            "candidate_pool_hash": key[1],
            "claim_status": CLAIM_STATUS,
            "context_L_packet_ids": list(route_row.get("context_L_packet_ids") or []),
            "evidence_path_packet_hashes": [str(packet.get("hash") or "") for packet in gold_packets],
            "evidence_path_packet_ids": [str(packet.get("packet_id") or "") for packet in gold_packets],
            "evidence_path_source_doc_ids": [str(packet.get("source_doc_id") or "") for packet in gold_packets],
            "evidence_path_spans": [_span_string(dict(packet.get("span") or {})) for packet in gold_packets],
            "fever_disabled": True,
            "materialization_policy": "route4a_materialized_context_with_source_boundaries",
            "original_instance_id": key[0],
            "route4a_block_A_packet_ids": list(route_row.get("block_A_packet_ids") or []),
            "schema_version": "evidence_path_target_row_v1",
            "source_dataset": str(instance.get("dataset") or ""),
            "source_split": str(instance.get("split") or ""),
            "target_char_length": len(target_text),
            "target_path_length": len(gold_packets),
            "target_row_id": target_row_id,
            "target_text_hash": target_text_hash,
            "target_tokenization_metadata": {
                "approx_whitespace_token_count": len(target_text.split()),
                "line_count": len(target_text.splitlines()),
                "tokenization_policy": "provider_tokenization_recorded_during_live_probe",
            },
            "target_type": "evidence_path_nll",
        }
        rows.append(row)
        materializations[target_row_id] = {
            "prompt": _prompt_from_instance(instance, gold_packets),
            "target_text": target_text,
        }

    unique_instances = {row["original_instance_id"] for row in rows}
    report = {
        "ambiguity_flags": {
            "missing_candidate_pool_count": missing_candidate_pool,
            "missing_gold_path_count": missing_gold_path,
            "missing_span_count": missing_span,
        },
        "claim_status": CLAIM_STATUS,
        "fever_disabled": True,
        "input_candidate_pool_count": len(candidate_pool_records),
        "input_route4a_row_count": len(route4_rows),
        "repeated_target_hash_count": len(duplicate_target_hashes),
        "repeated_target_hash_policy": "expected_when_multiple_route_rows_share_one_original_instance",
        "row_builder_ready": bool(rows) and missing_candidate_pool == 0 and missing_gold_path == 0 and missing_span == 0,
        "schema_version": "evidence_path_row_builder_readiness_v1",
        "target_rows_built": len(rows),
        "unique_original_instances": len(unique_instances),
    }
    return rows, report, materializations


def build_evidence_path_target_rows(
    candidate_pool_records: Sequence[Mapping[str, Any]],
    route4_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows, report, _materializations = _build_rows_with_materializations(candidate_pool_records, route4_rows)
    return rows, report


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        normalized = value.strip().strip('"').strip("'")
        if key.strip():
            values[key.strip()] = normalized
    return values


def _load_live_env(root: Path, override: Mapping[str, str] | None) -> dict[str, str]:
    if override is not None:
        return {str(key): str(value) for key, value in override.items()}
    env: dict[str, str] = {}
    env.update(_load_env_file(root / ".env"))
    env.update(_load_env_file(root / ".env.local"))
    for key in (
        "API_BASE_URL",
        "API_KEY",
        "DASHSCOPE_API_KEY",
        "DASHSCOPE_BASE_URL",
        "EVIDENCE_PATH_NLL_MODEL",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
    ):
        if os.environ.get(key):
            env[key] = str(os.environ[key])
    return env


def _live_config_report(env: Mapping[str, str]) -> dict[str, Any]:
    api_key_present = bool(env.get("DASHSCOPE_API_KEY") or env.get("API_KEY") or env.get("OPENAI_API_KEY"))
    base_url = (
        env.get("DASHSCOPE_BASE_URL")
        or env.get("OPENAI_BASE_URL")
        or env.get("API_BASE_URL")
        or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    model_id = env.get("EVIDENCE_PATH_NLL_MODEL") or env.get("DASHSCOPE_MODEL") or "qwen-plus"
    missing = []
    if not api_key_present:
        missing.append("api_key")
    return {
        "api_key_present": api_key_present,
        "base_url_configured": bool(base_url),
        "evaluator_id": "openai_compatible_chat_logprobs_teacher_forced_v1",
        "missing_evaluator_config": missing,
        "model_id": model_id,
    }


def _default_live_scorer(
    *,
    prompt: str,
    target_text: str,
    target_row: Mapping[str, Any],
    scoring_policy: Mapping[str, Any],
) -> dict[str, Any]:
    env = dict(scoring_policy.get("env") or {})
    api_key = env.get("DASHSCOPE_API_KEY") or env.get("API_KEY") or env.get("OPENAI_API_KEY")
    if not api_key:
        return {
            "api_call_count": 0,
            "api_failure_count": 1,
            "api_success_count": 0,
            "content_match": False,
            "failure_reason_code": "missing_api_key",
            "model_id": scoring_policy.get("model_id"),
            "nll": None,
            "prompt_token_count": None,
            "target_char_length": len(target_text),
            "target_token_count": None,
            "token_logprob_count": 0,
        }
    base_url = str(
        env.get("DASHSCOPE_BASE_URL")
        or env.get("OPENAI_BASE_URL")
        or env.get("API_BASE_URL")
        or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ).rstrip("/")
    model_id = str(scoring_policy.get("model_id") or env.get("EVIDENCE_PATH_NLL_MODEL") or "qwen-plus")
    request_payload = {
        "logprobs": True,
        "max_tokens": max(32, min(256, int(target_row.get("target_char_length") or len(target_text)) // 2 + 8)),
        "messages": [
            {
                "content": prompt,
                "role": "user",
            }
        ],
        "model": model_id,
        "temperature": 0,
        "top_logprobs": 0,
    }
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(request_payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {
            "api_call_count": 1,
            "api_failure_count": 1,
            "api_success_count": 0,
            "content_match": False,
            "failure_reason_code": f"http_error_{exc.code}",
            "model_id": model_id,
            "nll": None,
            "prompt_token_count": None,
            "target_char_length": len(target_text),
            "target_token_count": None,
            "token_logprob_count": 0,
        }
    except (OSError, TimeoutError, json.JSONDecodeError):
        return {
            "api_call_count": 1,
            "api_failure_count": 1,
            "api_success_count": 0,
            "content_match": False,
            "failure_reason_code": "request_or_parse_failure",
            "model_id": model_id,
            "nll": None,
            "prompt_token_count": None,
            "target_char_length": len(target_text),
            "target_token_count": None,
            "token_logprob_count": 0,
        }

    choice = (payload.get("choices") or [{}])[0]
    message = dict(choice.get("message") or {})
    content = str(message.get("content") or "")
    content_match = content.strip() == target_text.strip()
    token_logprobs = [
        float(token.get("logprob"))
        for token in (((choice.get("logprobs") or {}).get("content")) or [])
        if isinstance(token, Mapping) and token.get("logprob") is not None
    ]
    nll = -sum(token_logprobs) if token_logprobs else None
    usage = dict(payload.get("usage") or {})
    target_score_available = bool(token_logprobs) and content_match
    return {
        "api_call_count": 1,
        "api_failure_count": 0 if target_score_available else 1,
        "api_success_count": 1 if target_score_available else 0,
        "content_match": content_match,
        "failure_reason_code": (
            None
            if target_score_available
            else "content_mismatch_no_teacher_forced_target_score"
            if token_logprobs
            else "missing_token_logprobs"
        ),
        "mean_token_logprob": (sum(token_logprobs) / len(token_logprobs)) if token_logprobs else None,
        "min_token_logprob": min(token_logprobs) if token_logprobs else None,
        "model_id": model_id,
        "nll": nll,
        "prompt_token_count": usage.get("prompt_tokens"),
        "target_char_length": len(target_text),
        "target_token_count": len(token_logprobs) if token_logprobs else None,
        "token_logprob_count": len(token_logprobs),
    }


def _run_live_probe(
    *,
    contract: Mapping[str, Any],
    live_config: Mapping[str, Any],
    live_env: Mapping[str, str],
    live_probe_limit: int,
    live_scorer: LiveScorer | None,
    materializations: Mapping[str, Mapping[str, str]],
    target_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    missing = list(live_config.get("missing_evaluator_config") or [])
    if missing and live_scorer is None:
        return {
            "api_call_count": 0,
            "api_failure_count": 0,
            "api_success_count": 0,
            "claim_status": CLAIM_STATUS,
            "evaluator_id": live_config["evaluator_id"],
            "live_api_used": False,
            "missing_evaluator_config": missing,
            "model_id": live_config["model_id"],
            "probe_rows": [],
            "raw_api_responses_stored": False,
            "schema_version": "evidence_path_live_scoring_probe_v1",
            "scoring_status": "missing_evaluator_config",
            "secrets_stored": False,
        }
    scorer = live_scorer or _default_live_scorer
    probe_rows: list[dict[str, Any]] = []
    totals = {"api_call_count": 0, "api_failure_count": 0, "api_success_count": 0}
    for target_row in list(target_rows)[: max(0, live_probe_limit)]:
        target_row_id = str(target_row["target_row_id"])
        materialization = dict(materializations[target_row_id])
        scoring_policy = {
            "env": dict(live_env),
            "model_id": live_config["model_id"],
            "prompt_template_hash": contract["prompt_template_hash"],
            "store_raw_api_response": False,
            "target_format_hash": contract["target_format_hash"],
        }
        score = dict(
            scorer(
                prompt=materialization["prompt"],
                target_text=materialization["target_text"],
                target_row=target_row,
                scoring_policy=scoring_policy,
            )
        )
        api_call_count = int(score.get("api_call_count") or 0)
        token_logprob_count = int(score.get("token_logprob_count") or 0)
        content_match = bool(score.get("content_match"))
        target_score_available = content_match and token_logprob_count > 0 and score.get("nll") is not None
        api_success_count = 1 if target_score_available else 0
        api_failure_count = max(0, api_call_count - api_success_count)
        totals["api_call_count"] += api_call_count
        totals["api_success_count"] += api_success_count
        totals["api_failure_count"] += api_failure_count
        failure_reason_code = score.get("failure_reason_code")
        if not target_score_available and failure_reason_code in (None, ""):
            failure_reason_code = (
                "content_mismatch_no_teacher_forced_target_score"
                if token_logprob_count > 0
                else "missing_token_logprobs"
            )
        probe_rows.append(
            {
                "content_match": content_match,
                "failure_reason_code": failure_reason_code,
                "model_id": str(score.get("model_id") or live_config["model_id"]),
                "nll": score.get("nll"),
                "prompt_template_hash": contract["prompt_template_hash"],
                "prompt_token_count": score.get("prompt_token_count"),
                "target_char_length": int(score.get("target_char_length") or target_row.get("target_char_length") or 0),
                "target_format_hash": contract["target_format_hash"],
                "target_row_id": target_row_id,
                "target_text_hash": target_row["target_text_hash"],
                "target_token_count": score.get("target_token_count"),
                "token_logprob_count": token_logprob_count,
            }
        )
    status = (
        "scoring_probe_succeeded"
        if totals["api_success_count"] > 0
        else "teacher_forced_target_score_unavailable"
        if totals["api_call_count"] > 0
        else "scoring_probe_failed"
    )
    return {
        **totals,
        "claim_status": CLAIM_STATUS,
        "evaluator_id": live_config["evaluator_id"],
        "live_api_used": bool(totals["api_call_count"]),
        "missing_evaluator_config": [],
        "model_id": live_config["model_id"],
        "probe_rows": probe_rows,
        "raw_api_responses_stored": False,
        "schema_version": "evidence_path_live_scoring_probe_v1",
        "scoring_status": status,
        "secrets_stored": False,
    }


def _build_scoring_feasibility_report(
    *,
    contract: Mapping[str, Any],
    live_config: Mapping[str, Any],
    live_probe: Mapping[str, Any],
    row_report: Mapping[str, Any],
) -> dict[str, Any]:
    missing = list(live_probe.get("missing_evaluator_config") or [])
    if missing:
        status = "missing_evaluator_config"
    elif int(live_probe.get("api_success_count") or 0) > 0:
        status = "bounded_live_probe_succeeded"
    elif live_probe.get("scoring_status") == "teacher_forced_target_score_unavailable":
        status = "teacher_forced_target_score_unavailable"
    else:
        status = "bounded_live_probe_failed"
    return {
        "api_call_count": int(live_probe.get("api_call_count") or 0),
        "api_failure_count": int(live_probe.get("api_failure_count") or 0),
        "api_success_count": int(live_probe.get("api_success_count") or 0),
        "claim_status": CLAIM_STATUS,
        "evaluator_id": live_config["evaluator_id"],
        "live_api_used": bool(live_probe.get("live_api_used")),
        "missing_evaluator_config": missing,
        "model_id": live_config["model_id"],
        "normalized_outputs_only": True,
        "raw_api_responses_stored": False,
        "row_builder_ready": bool(row_report.get("row_builder_ready")),
        "schema_version": "evidence_path_scoring_feasibility_v1",
        "scoring_policy": deepcopy(contract["scoring_policy"]),
        "scoring_status": status,
        "secrets_stored": False,
        "target_format_hash": contract["target_format_hash"],
        "target_rows_available": int(row_report.get("target_rows_built") or 0),
        "teacher_forced_scoring_required": True,
    }


def _build_controls_and_gates(contract_validation: Mapping[str, Any], row_report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "claim_status": CLAIM_STATUS,
        "controls": [
            "empty_evidence_path_negative_control",
            "distractor_only_evidence_path_negative_control",
            "shuffled_gold_path_order_sensitivity_control",
            "answer_string_target_mismatch_control",
            "source_doc_span_masking_control",
        ],
        "fever_disabled": True,
        "gate_preregistration": {
            "contract_gate": "target_contract_validation_passed",
            "independent_review_gate": "required_before_any_bridge_pilot",
            "minimum_unique_instances_before_bridge_pilot": 150,
            "minimum_valid_target_rows_before_bridge_pilot": 500,
            "non_circularity_gate": "utility_labels_must_not_use_evidence_path_nll_or_model_logprob",
            "raw_storage_gate": "no_raw_api_responses_no_secrets_no_raw_dataset_mirrors",
            "route5_gate": "locked",
            "route8_gate": "locked",
            "scoring_gate": "bounded_live_probe_or_documented_missing_evaluator_config",
        },
        "lp6_bridge_repair_run": False,
        "measurement_validation_claim": False,
        "route5_locked": True,
        "route8_locked": True,
        "schema_version": "evidence_path_controls_and_gate_preregistration_v1",
        "status": "preregistered" if contract_validation.get("passed") and row_report.get("row_builder_ready") else "not_ready",
    }


def _terminal_decision(
    *,
    contract_validation: Mapping[str, Any],
    row_report: Mapping[str, Any],
    scoring_report: Mapping[str, Any],
) -> str:
    if not contract_validation.get("passed"):
        return "BLOCKED_SCORING_CONTRACT_AMBIGUOUS"
    if int(row_report.get("target_rows_built") or 0) <= 0:
        return "BLOCKED_MISSING_EVIDENCE_PATH_TARGETS"
    if not row_report.get("row_builder_ready"):
        return "NOT_READY_TARGET_AMBIGUOUS"
    if scoring_report.get("scoring_status") in {
        "missing_evaluator_config",
        "teacher_forced_target_score_unavailable",
    }:
        return "HONESTLY_BLOCKED"
    if int(scoring_report.get("api_success_count") or 0) <= 0:
        return "NOT_READY_INSUFFICIENT_ARTIFACTS"
    return "EVIDENCE_PATH_PROTOCOL_READY_FOR_REVIEW"


def _build_readiness_decision(
    *,
    contract_validation: Mapping[str, Any],
    controls: Mapping[str, Any],
    live_probe: Mapping[str, Any],
    row_report: Mapping[str, Any],
    scoring_report: Mapping[str, Any],
) -> dict[str, Any]:
    decision = _terminal_decision(
        contract_validation=contract_validation,
        row_report=row_report,
        scoring_report=scoring_report,
    )
    return {
        "claim_status": CLAIM_STATUS,
        "contract_validation": {
            "errors": list(contract_validation.get("errors") or []),
            "passed": bool(contract_validation.get("passed")),
        },
        "controls_preregistered": controls.get("status") == "preregistered",
        "denied_claims": [
            "measurement_validation",
            "metric_bridge_support",
            "calibrated_proxy_support",
            "V-info_proxy_support",
            "selector_superiority",
            "paper_evidence",
        ],
        "disabled_decision": "SWITCH_TO_FEVER_LABEL_NLL",
        "fever_disabled": True,
        "live_api_scoring_probe": {
            "api_call_count": int(live_probe.get("api_call_count") or 0),
            "api_failure_count": int(live_probe.get("api_failure_count") or 0),
            "api_success_count": int(live_probe.get("api_success_count") or 0),
            "live_api_used": bool(live_probe.get("live_api_used")),
            "raw_api_responses_stored": False,
            "secrets_stored": False,
        },
        "lp6_bridge_repair_run": False,
        "protocol_scope": "EPN1_EPN5_only",
        "route5_locked": True,
        "route8_locked": True,
        "schema_version": "evidence_path_protocol_readiness_decision_v1",
        "target_decision": "SWITCH_TO_EVIDENCE_PATH_NLL",
        "target_rows_built": int(row_report.get("target_rows_built") or 0),
        "terminal_protocol_decision": decision,
    }


def _target_contract_doc(contract: Mapping[str, Any], validation: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Evidence-Path NLL Target Contract",
            "",
            f"Claim status: {CLAIM_STATUS}",
            "",
            f"- target_type: {contract['target_type']}",
            f"- target_representation: {contract['target_representation']}",
            f"- teacher_forced_scoring_required: {str(contract['teacher_forced_scoring_required']).lower()}",
            f"- target_format_hash: {contract['target_format_hash']}",
            f"- prompt_template_hash: {contract['prompt_template_hash']}",
            f"- materialization_policy_hash: {contract['materialization_policy_hash']}",
            "",
            f"Validation passed: {str(validation['passed']).lower()}",
            "",
            "FEVER remains disabled and is not selected as an active target.",
            "Route 5 and Route 8 remain locked. LP6 bridge repair was not run.",
            "",
        ]
    )


def _row_builder_doc(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Evidence-Path NLL Row-Builder Readiness",
            "",
            f"Claim status: {CLAIM_STATUS}",
            "",
            f"- row_builder_ready: {str(report['row_builder_ready']).lower()}",
            f"- target_rows_built: {report['target_rows_built']}",
            f"- unique_original_instances: {report['unique_original_instances']}",
            "",
            "The persisted target rows store packet identifiers, source document ids, span strings, hashes, and tokenization metadata only. Full evidence text is used only in memory for bounded scoring probes.",
            "",
        ]
    )


def _scoring_doc(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Evidence-Path NLL Scoring Feasibility",
            "",
            f"Claim status: {CLAIM_STATUS}",
            "",
            f"- scoring_status: {report['scoring_status']}",
            f"- live_api_used: {str(report['live_api_used']).lower()}",
            f"- api_call_count: {report['api_call_count']}",
            f"- api_success_count: {report['api_success_count']}",
            f"- api_failure_count: {report['api_failure_count']}",
            f"- raw_api_responses_stored: {str(report['raw_api_responses_stored']).lower()}",
            f"- secrets_stored: {str(report['secrets_stored']).lower()}",
            "",
            "This report is a scoring-feasibility artifact only. It does not validate a metric bridge, calibrated proxy, V-information proxy, measurement claim, paper evidence claim, or selector-superiority claim.",
            "",
        ]
    )


def _controls_doc(controls: Mapping[str, Any]) -> str:
    gates = "\n".join(f"- {key}: {value}" for key, value in sorted(dict(controls["gate_preregistration"]).items()))
    return "\n".join(
        [
            "# Evidence-Path NLL Controls And Gates",
            "",
            f"Claim status: {CLAIM_STATUS}",
            "",
            "## Preregistered Gates",
            "",
            gates,
            "",
            "No full bridge repair calibration is part of this package.",
            "",
        ]
    )


def _readiness_doc(readiness: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Evidence-Path NLL Protocol Readiness",
            "",
            f"Claim status: {CLAIM_STATUS}",
            f"Terminal protocol decision: {readiness['terminal_protocol_decision']}",
            "",
            "FEVER remains disabled. Route 5 and Route 8 remain locked. LP6 bridge repair was not run.",
            "",
            "Denied claims: measurement validation, metric bridge support, calibrated proxy support, V-information proxy support, paper evidence, and selector superiority.",
            "",
        ]
    )


def _load_required_inputs(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    required = {
        "hotpotqa_candidate_pools": HOTPOTQA_CANDIDATE_POOLS,
        "logprobe_readiness": LOGPROBE_READINESS,
        "logprobe_target_decision": LOGPROBE_TARGET_DECISION,
        "route4a_rows": ROUTE4A_ROWS,
    }
    missing = [name for name, path in required.items() if not _resolve(root, path).exists()]
    if missing:
        raise EvidencePathProtocolInputMissingError(
            "missing required Evidence-path NLL protocol inputs: " + ", ".join(sorted(missing))
        )
    return (
        read_jsonl(_resolve(root, HOTPOTQA_CANDIDATE_POOLS)),
        read_jsonl(_resolve(root, ROUTE4A_ROWS)),
        _read_json(_resolve(root, LOGPROBE_READINESS)),
        _read_json(_resolve(root, LOGPROBE_TARGET_DECISION)),
    )


def run_evidence_path_nll_protocol(
    *,
    root: str | Path = ".",
    live_env: Mapping[str, str] | None = None,
    live_probe_limit: int = 3,
    live_scorer: LiveScorer | None = None,
) -> dict[str, Any]:
    repo_root = Path(root)
    candidate_pools, route4_rows, logprobe_readiness, logprobe_target_decision = _load_required_inputs(repo_root)
    contract = build_evidence_path_target_contract()
    contract_validation = validate_evidence_path_target_contract(contract)
    target_rows, row_report, materializations = _build_rows_with_materializations(candidate_pools, route4_rows)
    env = _load_live_env(repo_root, live_env)
    live_config = _live_config_report(env)
    live_probe = _run_live_probe(
        contract=contract,
        live_config=live_config,
        live_env=env,
        live_probe_limit=live_probe_limit,
        live_scorer=live_scorer,
        materializations=materializations,
        target_rows=target_rows,
    )
    scoring_report = _build_scoring_feasibility_report(
        contract=contract,
        live_config=live_config,
        live_probe=live_probe,
        row_report=row_report,
    )
    controls = _build_controls_and_gates(contract_validation, row_report)
    readiness = _build_readiness_decision(
        contract_validation=contract_validation,
        controls=controls,
        live_probe=live_probe,
        row_report=row_report,
        scoring_report=scoring_report,
    )

    artifact_dir = repo_root / ARTIFACT_DIR
    docs_dir = repo_root / "docs/experiments"
    artifact_paths = {
        "controls_and_gate_preregistration": write_json(
            artifact_dir / "controls_and_gate_preregistration.json", controls
        ),
        "protocol_readiness_decision": write_json(artifact_dir / "protocol_readiness_decision.json", readiness),
        "row_builder_readiness": write_json(artifact_dir / "row_builder_readiness.json", row_report),
        "scoring_feasibility_report": write_json(artifact_dir / "scoring_feasibility_report.json", scoring_report),
        "target_contract": write_json(artifact_dir / "target_contract.json", contract),
        "target_contract_validation": write_json(artifact_dir / "target_contract_validation.json", contract_validation),
        "target_rows": write_jsonl(artifact_dir / "evidence_path_target_rows.jsonl", target_rows),
    }
    if live_probe.get("live_api_used") or live_probe.get("scoring_status") == "missing_evaluator_config":
        artifact_paths["live_scoring_probe_report"] = write_json(
            artifact_dir / "live_scoring_probe_report.json", live_probe
        )

    docs_dir.mkdir(parents=True, exist_ok=True)
    doc_paths = {
        "controls_and_gate_preregistration_doc": docs_dir / "EvidencePathNLL-controls-and-gates.md",
        "protocol_readiness_doc": docs_dir / "EvidencePathNLL-protocol-readiness.md",
        "row_builder_readiness_doc": docs_dir / "EvidencePathNLL-row-builder-readiness.md",
        "scoring_feasibility_doc": docs_dir / "EvidencePathNLL-scoring-feasibility.md",
        "target_contract_doc": docs_dir / "EvidencePathNLL-target-contract.md",
    }
    doc_paths["target_contract_doc"].write_text(_target_contract_doc(contract, contract_validation), encoding="utf-8")
    doc_paths["row_builder_readiness_doc"].write_text(_row_builder_doc(row_report), encoding="utf-8")
    doc_paths["scoring_feasibility_doc"].write_text(_scoring_doc(scoring_report), encoding="utf-8")
    doc_paths["controls_and_gate_preregistration_doc"].write_text(_controls_doc(controls), encoding="utf-8")
    doc_paths["protocol_readiness_doc"].write_text(_readiness_doc(readiness), encoding="utf-8")

    return {
        "artifacts": {
            name: _path_ref(path.relative_to(repo_root) if path.is_absolute() else path)
            for name, path in artifact_paths.items()
        },
        "claim_status": CLAIM_STATUS,
        "docs": {
            name: _path_ref(path.relative_to(repo_root) if path.is_absolute() else path)
            for name, path in doc_paths.items()
        },
        "fever_disabled": True,
        "input_logprobe_readiness": str(logprobe_readiness.get("readiness_state") or ""),
        "input_target_decision": str(logprobe_target_decision.get("primary_decision") or ""),
        "lp6_bridge_repair_run": False,
        "route5_locked": True,
        "route8_locked": True,
        "terminal_protocol_decision": readiness["terminal_protocol_decision"],
        "terminal_status": TERMINAL_STATUS,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run EPN1-EPN5 Evidence-path NLL protocol freeze.")
    parser.add_argument("--root", default=".", help="Repository root containing existing artifacts.")
    parser.add_argument("--live-probe-limit", default=3, type=int, help="Maximum target rows for bounded live probe.")
    args = parser.parse_args(argv)
    result = run_evidence_path_nll_protocol(root=args.root, live_probe_limit=args.live_probe_limit)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
