from __future__ import annotations

import argparse
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from api.openai_compatible import OpenAICompatibleClient
from api.openai_compatible import OpenAICompatibleCredentials
from api.openai_compatible import OpenAICompatibleError
from api.settings import resolve_api_profile
from cps.benchmarks.hashing import canonical_json_dumps
from cps.benchmarks.hashing import stable_hash
from cps.runtime.secrets import extract_api_key_from_csv


ROUTE6A_ID = "route6a_external_sufficiency_measurement_pilot"
ROUTE6A_PHASE_ID = "route6a_external_sufficiency_measurement_pilot"
ROUTE6A_PROTOCOL_ID = "route6a_hotpotqa_external_sufficiency_model_adjudication_v1"
RUBRIC_VERSION = "route6a_external_sufficiency_rubric_v1"
PROMPT_VERSION = "route6a_external_sufficiency_prompt_v1"
SAMPLE_SCHEMA_VERSION = "route6a_context_pair_sample_v1"
LABEL_SCHEMA_VERSION = "route6a_model_sufficiency_labels_v1"
CLAIM_STATUS = "no_claim_upgrade"
DEFAULT_OUTPUT_DIR = "artifacts/experiments/route6a_measurement_pilot"
DEFAULT_BRIDGE_ROWS_PATH = "artifacts/experiments/route4_bridge/bridge_rows.jsonl"
DEFAULT_CANDIDATE_POOLS_PATH = "artifacts/benchmarks/hotpotqa_candidate_pools.jsonl"
DEFAULT_REPORT_MD = "docs/experiments/Route6A-external-sufficiency-measurement-pilot.md"
DEFAULT_LOCAL_JUDGE_CONFIG = "configs/local/bridge-data-generation-live.local.json"

HIDDEN_FROM_JUDGE_FIELDS = (
    "delta_logloss",
    "delta_utility",
    "baseline_utility",
    "augmented_utility",
    "gold_support_label",
    "utility_source_provenance",
    "support_coverage_delta",
    "source_coverage_delta",
    "full_support_hit_delta",
    "missing_prerequisite_delta",
)
SUFFICIENCY_LABELS = ("insufficient", "partial", "sufficient", "invalid")
DELTA_LABELS = ("improves", "unchanged", "worsens", "invalid")
ANSWER_SUPPORT_LABELS = ("unsupported", "partial", "supported", "invalid")
RELEVANCE_LABELS = ("irrelevant", "mixed", "relevant", "invalid")
UNCERTAINTY_LABELS = ("low", "medium", "high")


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _stable_jsonl(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return ""
    return "\n".join(canonical_json_dumps(dict(row)) for row in rows) + "\n"


def _write_json(path: str | Path, payload: Any) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_stable_json(payload), encoding="utf-8")
    return output_path


def _write_jsonl(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_stable_jsonl(rows), encoding="utf-8")
    return output_path


def _read_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{Path(path).name}: expected JSON object")
    return payload


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    input_path = Path(path)
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{input_path.name}: row {line_number} must be a JSON object")
        rows.append(payload)
    return rows


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.as_posix() if not candidate.is_absolute() else candidate.name


def _packet_id(packet: Mapping[str, Any]) -> str:
    return str(packet.get("packet_id") or "").strip()


def _pool_hash(pool_payload: Mapping[str, Any]) -> str:
    return str((pool_payload.get("candidate_pool") or {}).get("candidate_pool_hash") or "").strip()


def _pool_packets(pool_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    packets = (pool_payload.get("candidate_pool") or {}).get("packets") or []
    return [dict(packet) for packet in packets if isinstance(packet, Mapping)]


def _pool_by_key(candidate_pools: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(pool.get("instance_id") or ""), _pool_hash(pool)): dict(pool)
        for pool in candidate_pools
        if str(pool.get("instance_id") or "") and _pool_hash(pool)
    }


def _packet_lookup(pool_payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {_packet_id(packet): dict(packet) for packet in _pool_packets(pool_payload) if _packet_id(packet)}


def _public_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    provenance = dict(packet.get("provenance") or {})
    public_provenance = {
        key: str(provenance.get(key) or "")
        for key in ("dataset", "source_doc_id", "span")
        if str(provenance.get(key) or "")
    }
    return {
        "content": str(packet.get("content") or ""),
        "packet_id": _packet_id(packet),
        "provenance": public_provenance,
        "source_doc_id": str(packet.get("source_doc_id") or provenance.get("source_doc_id") or ""),
        "token_cost": int(packet.get("token_cost") or 0),
    }


def _row_ref(row: Mapping[str, Any]) -> dict[str, Any]:
    identity = {
        "active_stratum": str(row.get("active_stratum") or ""),
        "block_A_packet_ids": [str(item) for item in row.get("block_A_packet_ids") or []],
        "candidate_pool_hash": str(row.get("candidate_pool_hash") or ""),
        "context_L_packet_ids": [str(item) for item in row.get("context_L_packet_ids") or []],
        "instance_id": str(row.get("instance_id") or ""),
        "original_instance_id": str(row.get("original_instance_id") or ""),
        "phase_id": str(row.get("phase_id") or ""),
        "protocol_id": str(row.get("protocol_id") or ""),
        "split_id": str(row.get("split_id") or ""),
    }
    return {
        "candidate_pool_hash": identity["candidate_pool_hash"],
        "heldout_flag": bool(row.get("heldout_flag")),
        "original_instance_id": identity["original_instance_id"],
        "phase_id": identity["phase_id"],
        "protocol_id": identity["protocol_id"],
        "route4_row_identity_hash": stable_hash(identity),
    }


def _sample_sort_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    identity = {
        "block_A_packet_ids": row.get("block_A_packet_ids") or [],
        "candidate_pool_hash": row.get("candidate_pool_hash"),
        "context_L_packet_ids": row.get("context_L_packet_ids") or [],
        "instance_id": row.get("instance_id"),
        "original_instance_id": row.get("original_instance_id"),
    }
    return (
        str(row.get("original_instance_id") or ""),
        stable_hash(identity),
        str(row.get("instance_id") or ""),
    )


def _eligible_rows(
    *,
    bridge_rows: Sequence[Mapping[str, Any]],
    pools: Mapping[tuple[str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    eligible: list[dict[str, Any]] = []
    for row in bridge_rows:
        if str(row.get("dataset") or "") != "HotpotQA":
            continue
        if str(row.get("contamination_status") or "") == "failed":
            continue
        if row.get("validation_failure_reason") not in {None, ""}:
            continue
        original_instance_id = str(row.get("original_instance_id") or "")
        candidate_pool_hash = str(row.get("candidate_pool_hash") or "")
        pool = pools.get((original_instance_id, candidate_pool_hash))
        if not pool:
            continue
        lookup = _packet_lookup(pool)
        context_ids = [str(packet_id) for packet_id in row.get("context_L_packet_ids") or []]
        block_ids = [str(packet_id) for packet_id in row.get("block_A_packet_ids") or []]
        if not block_ids:
            continue
        if any(packet_id not in lookup for packet_id in (*context_ids, *block_ids)):
            continue
        eligible.append(dict(row))
    return sorted(eligible, key=_sample_sort_key)


def _balanced_sample(rows: Sequence[Mapping[str, Any]], sample_size: int) -> list[dict[str, Any]]:
    if sample_size <= 0:
        return []
    groups = {
        "positive": [dict(row) for row in rows if float(row.get("delta_utility") or 0.0) > 0.0],
        "zero": [dict(row) for row in rows if float(row.get("delta_utility") or 0.0) == 0.0],
        "negative": [dict(row) for row in rows if float(row.get("delta_utility") or 0.0) < 0.0],
    }
    selected: list[dict[str, Any]] = []
    selected_originals: set[str] = set()
    while len(selected) < sample_size and any(groups.values()):
        made_progress = False
        for group_name in ("positive", "zero", "negative"):
            group = groups[group_name]
            if not group or len(selected) >= sample_size:
                continue
            chosen_index = 0
            for index, candidate in enumerate(group):
                original_id = str(candidate.get("original_instance_id") or "")
                if original_id not in selected_originals:
                    chosen_index = index
                    break
            chosen = group.pop(chosen_index)
            selected.append(chosen)
            selected_originals.add(str(chosen.get("original_instance_id") or ""))
            made_progress = True
        if not made_progress:
            break
    return selected


def build_context_pair_sample(
    *,
    bridge_rows: Sequence[Mapping[str, Any]],
    candidate_pools: Sequence[Mapping[str, Any]],
    sample_size: int = 24,
) -> list[dict[str, Any]]:
    pools = _pool_by_key(candidate_pools)
    rows = _balanced_sample(_eligible_rows(bridge_rows=bridge_rows, pools=pools), sample_size)
    sample: list[dict[str, Any]] = []
    for row in rows:
        original_instance_id = str(row.get("original_instance_id") or "")
        candidate_pool_hash = str(row.get("candidate_pool_hash") or "")
        pool = pools[(original_instance_id, candidate_pool_hash)]
        lookup = _packet_lookup(pool)
        context_ids = [str(packet_id) for packet_id in row.get("context_L_packet_ids") or []]
        block_ids = [str(packet_id) for packet_id in row.get("block_A_packet_ids") or []]
        sample_identity = {
            "route_id": ROUTE6A_ID,
            "route4_ref": _row_ref(row),
            "target_y": str(row.get("target_y") or (pool.get("target") or {}).get("label") or ""),
        }
        sample.append(
            {
                "sample_id": f"route6a::{stable_hash(sample_identity)[:20]}",
                "sample_schema_version": SAMPLE_SCHEMA_VERSION,
                "dataset": "HotpotQA",
                "split": str(row.get("split") or pool.get("split") or ""),
                "original_instance_id": original_instance_id,
                "candidate_pool_hash": candidate_pool_hash,
                "question": str(pool.get("query") or ""),
                "target_y": str(row.get("target_y") or (pool.get("target") or {}).get("label") or ""),
                "baseline_context_packets": [_public_packet(lookup[packet_id]) for packet_id in context_ids],
                "added_block_packets": [_public_packet(lookup[packet_id]) for packet_id in block_ids],
                "materialization_policy": str(row.get("materialization_policy") or ""),
                "budget": int(row.get("budget") or 0),
                "source_route4_row_ref": _row_ref(row),
            }
        )
    return sorted(sample, key=lambda row: row["sample_id"])


def build_frozen_rubric() -> dict[str, Any]:
    return {
        "rubric_version": RUBRIC_VERSION,
        "prompt_version": PROMPT_VERSION,
        "label_schema_version": LABEL_SCHEMA_VERSION,
        "task": "Judge whether baseline and augmented HotpotQA contexts are sufficient to support the target answer.",
        "judge_visible_fields": [
            "question",
            "target_y",
            "baseline_context_packets.content",
            "added_block_packets.content",
            "source_doc_id",
            "provenance",
        ],
        "hidden_from_judge_fields": list(HIDDEN_FROM_JUDGE_FIELDS),
        "labels": {
            "baseline_sufficiency": list(SUFFICIENCY_LABELS),
            "augmented_sufficiency": list(SUFFICIENCY_LABELS),
            "delta_label": list(DELTA_LABELS),
            "answer_supported": list(ANSWER_SUPPORT_LABELS),
            "evidence_relevance": list(RELEVANCE_LABELS),
            "uncertainty": list(UNCERTAINTY_LABELS),
        },
        "invalid_item_policy": "Use invalid only when the question, target, or contexts are malformed enough to prevent adjudication.",
        "non_circularity_rule": "The judge must not receive delta_logloss, delta_utility, gold_support_label, or route4 utility scores.",
        "model_adjudication_counts_as_human_label": False,
        "human_annotation_required_for_measurement_validation": True,
        "measurement_validation_candidate_allowed": False,
        "claim_status": CLAIM_STATUS,
    }


def _manifest(
    *,
    sample: Sequence[Mapping[str, Any]],
    bridge_rows: Sequence[Mapping[str, Any]],
    candidate_pools: Sequence[Mapping[str, Any]],
    bridge_rows_path: str | Path,
    candidate_pools_path: str | Path,
    live_api_used: bool,
) -> dict[str, Any]:
    return {
        "route_id": ROUTE6A_ID,
        "phase_id": ROUTE6A_PHASE_ID,
        "protocol_id": ROUTE6A_PROTOCOL_ID,
        "sample_schema_version": SAMPLE_SCHEMA_VERSION,
        "rubric_version": RUBRIC_VERSION,
        "label_schema_version": LABEL_SCHEMA_VERSION,
        "claim_status": CLAIM_STATUS,
        "source_artifacts": {
            "route4_bridge_rows": _path_ref(bridge_rows_path),
            "hotpotqa_candidate_pools": _path_ref(candidate_pools_path),
        },
        "source_bridge_rows_count": len(bridge_rows),
        "source_candidate_pools_count": len(candidate_pools),
        "sample_count": len(sample),
        "unique_original_instances": len({str(row.get("original_instance_id") or "") for row in sample}),
        "sampling_policy": "deterministic_balanced_positive_zero_delta_utility_internal_only",
        "judge_hidden_fields": list(HIDDEN_FROM_JUDGE_FIELDS),
        "live_api_used": bool(live_api_used),
        "raw_api_responses_stored": False,
        "operator_inputs_written": False,
        "measurement_validation_candidate_allowed": False,
        "human_annotation_required_for_measurement_validation": True,
    }


def _readiness_report(
    *,
    sample: Sequence[Mapping[str, Any]],
    bridge_rows: Sequence[Mapping[str, Any]],
    candidate_pools: Sequence[Mapping[str, Any]],
    judge_available: bool,
    status: str,
    reason_codes: Sequence[str],
    live_api_used: bool,
) -> dict[str, Any]:
    clean_rows = sum(1 for row in bridge_rows if str(row.get("contamination_status") or "") == "clean")
    return {
        "route_id": ROUTE6A_ID,
        "phase_id": ROUTE6A_PHASE_ID,
        "claim_status": CLAIM_STATUS,
        "status": status,
        "reason_codes": list(reason_codes),
        "route4_rows_available": len(bridge_rows) > 0,
        "route4_rows_count": len(bridge_rows),
        "route4_clean_rows_count": clean_rows,
        "candidate_pools_count": len(candidate_pools),
        "context_pair_sample_count": len(sample),
        "approved_model_judge_available": bool(judge_available),
        "live_api_used": bool(live_api_used),
        "raw_api_responses_stored": False,
        "human_annotation_status": "blocked_human_annotation_required",
        "human_labels_present": False,
        "human_human_kappa_present": False,
        "measurement_validation_candidate_allowed": False,
        "model_adjudication_counts_as_human_label": False,
        "allowed_claim": "model_adjudicated_candidate_evidence_only_if_labels_exist",
        "denied_claims": [
            "measurement validation",
            "human-label validation",
            "human-human kappa",
            "calibrated_proxy_supported",
            "vinfo_proxy_supported",
            "paper evidence",
            "metric bridge support",
            "global selector superiority",
            "deployed V-information verification",
        ],
    }


def _env_file_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _env_values(env: Mapping[str, str] | None = None) -> dict[str, str]:
    if env is not None:
        return {str(key): str(value) for key, value in env.items() if value is not None}
    values: dict[str, str] = {}
    values.update(_env_file_values(Path(".env")))
    values.update(_env_file_values(Path(".env.local")))
    values.update({key: value for key, value in os.environ.items() if isinstance(value, str)})
    return values


def _load_local_judge_config(config_path: str | Path | None) -> dict[str, Any]:
    if config_path is None:
        return {}
    path = Path(config_path)
    if not path.exists():
        return {}
    payload = _read_json(path)
    return payload


def _credential_from_local_config(config: Mapping[str, Any], config_path: str | Path | None) -> str:
    source = config.get("credential_source")
    if not isinstance(source, Mapping):
        return ""
    raw_path = str(source.get("local_credential_file") or "").strip()
    if not raw_path or raw_path.startswith("OPERATOR_"):
        return ""
    path = Path(raw_path)
    if not path.is_absolute() and config_path is not None:
        config_relative = Path(config_path).resolve().parent / path
        if config_relative.exists():
            path = config_relative
    if not path.exists():
        return ""
    try:
        return extract_api_key_from_csv(path)
    except Exception:
        return ""


def _default_live_client(
    *,
    env: Mapping[str, str] | None,
    config_path: str | Path | None,
) -> tuple[OpenAICompatibleClient | None, dict[str, Any]]:
    env_map = _env_values(env)
    config = _load_local_judge_config(config_path)
    if env_map.get("CPS_ALLOW_LIVE_API") != "1":
        return None, {"available": False, "reason_code": "live_api_gate_not_enabled"}
    profile_name = str(config.get("provider_profile") or env_map.get("API_PROFILE") or "").strip() or None
    try:
        resolved = resolve_api_profile(env_values=env_map, profile_name=profile_name)
    except Exception:
        return None, {"available": False, "reason_code": "provider_profile_unavailable"}
    api_key = resolved.api_key or _credential_from_local_config(config, config_path)
    if not api_key:
        return None, {"available": False, "reason_code": "provider_credential_unavailable"}
    model_id = str(config.get("strong_review_model_id") or resolved.role_models.get("frontier") or "").strip()
    if not model_id or model_id.startswith("OPERATOR_"):
        return None, {"available": False, "reason_code": "judge_model_unavailable"}
    client = OpenAICompatibleClient(OpenAICompatibleCredentials(base_url=resolved.base_url, api_key=api_key))
    return client, {
        "available": True,
        "judge_model_id": model_id,
        "judge_provider": resolved.provider_name,
        "max_completion_tokens": int(config.get("adjudication_max_completion_tokens") or 256),
        "request_timeout_seconds": int(config.get("request_timeout_seconds") or 60),
        "extra_body": dict(config.get("provider_extra_body") or {"enable_thinking": False}),
    }


def _judge_messages(sample_row: Mapping[str, Any], rubric: Mapping[str, Any]) -> list[dict[str, str]]:
    visible_item = {
        "sample_id": sample_row["sample_id"],
        "question": sample_row["question"],
        "target_y": sample_row["target_y"],
        "baseline_context_packets": sample_row["baseline_context_packets"],
        "added_block_packets": sample_row["added_block_packets"],
    }
    response_contract = {
        "baseline_sufficiency": list(SUFFICIENCY_LABELS),
        "augmented_sufficiency": list(SUFFICIENCY_LABELS),
        "delta_label": list(DELTA_LABELS),
        "answer_supported": list(ANSWER_SUPPORT_LABELS),
        "evidence_relevance": list(RELEVANCE_LABELS),
        "uncertainty": list(UNCERTAINTY_LABELS),
        "invalid_reason": "string, empty unless invalid",
    }
    return [
        {
            "role": "system",
            "content": (
                "You are an external sufficiency adjudicator. "
                "Return only one JSON object matching the requested enum contract. "
                "Do not infer hidden gold labels or logloss values."
            ),
        },
        {
            "role": "user",
            "content": _stable_json(
                {
                    "rubric": rubric,
                    "item": visible_item,
                    "response_contract": response_contract,
                }
            ),
        },
    ]


def _choice_content(response: Mapping[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, Mapping):
        return ""
    message = first.get("message")
    if isinstance(message, Mapping):
        return str(message.get("content") or "").strip()
    return str(first.get("text") or "").strip()


def _parse_judge_content(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`").strip()
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    payload = json.loads(stripped)
    if not isinstance(payload, dict):
        raise ValueError("judge_payload_not_object")
    return payload


def _enum(value: Any, allowed: Sequence[str], invalid: str = "invalid") -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in allowed else invalid


def _normalized_label(
    *,
    sample_row: Mapping[str, Any],
    payload: Mapping[str, Any],
    judge_model_id: str,
    judge_provider: str,
) -> dict[str, Any]:
    record = {
        "sample_id": str(sample_row.get("sample_id") or ""),
        "label_schema_version": LABEL_SCHEMA_VERSION,
        "rubric_version": RUBRIC_VERSION,
        "prompt_version": PROMPT_VERSION,
        "judge_model_id": judge_model_id,
        "judge_provider": judge_provider,
        "baseline_sufficiency": _enum(payload.get("baseline_sufficiency"), SUFFICIENCY_LABELS),
        "augmented_sufficiency": _enum(payload.get("augmented_sufficiency"), SUFFICIENCY_LABELS),
        "delta_label": _enum(payload.get("delta_label"), DELTA_LABELS),
        "answer_supported": _enum(payload.get("answer_supported"), ANSWER_SUPPORT_LABELS),
        "evidence_relevance": _enum(payload.get("evidence_relevance"), RELEVANCE_LABELS),
        "uncertainty": _enum(payload.get("uncertainty"), UNCERTAINTY_LABELS, invalid="high"),
        "invalid_reason_code": str(payload.get("invalid_reason") or ""),
        "counts_as_human_label": False,
        "measurement_validation_candidate_allowed": False,
        "raw_response_stored": False,
        "source_sample_ref": str(sample_row.get("sample_id") or ""),
    }
    record["label_record_hash"] = stable_hash(record)
    return record


def _invalid_label(
    *,
    sample_row: Mapping[str, Any],
    judge_model_id: str,
    judge_provider: str,
    reason_code: str,
) -> dict[str, Any]:
    return _normalized_label(
        sample_row=sample_row,
        payload={
            "baseline_sufficiency": "invalid",
            "augmented_sufficiency": "invalid",
            "delta_label": "invalid",
            "answer_supported": "invalid",
            "evidence_relevance": "invalid",
            "uncertainty": "high",
            "invalid_reason": reason_code,
        },
        judge_model_id=judge_model_id,
        judge_provider=judge_provider,
    )


def _run_model_adjudication(
    *,
    sample: Sequence[Mapping[str, Any]],
    rubric: Mapping[str, Any],
    client: Any,
    judge_model_id: str,
    judge_provider: str,
    max_completion_tokens: int = 256,
    timeout: int = 60,
    extra_body: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    invalid_count = 0
    for sample_row in sample:
        try:
            response = client.chat_completion(
                model=judge_model_id,
                messages=_judge_messages(sample_row, rubric),
                max_completion_tokens=max_completion_tokens,
                temperature=0.0,
                seed=60401,
                stream=False,
                n=1,
                extra_body=extra_body,
                timeout=timeout,
            )
            payload = _parse_judge_content(_choice_content(response))
            label = _normalized_label(
                sample_row=sample_row,
                payload=payload,
                judge_model_id=judge_model_id,
                judge_provider=judge_provider,
            )
        except Exception:
            invalid_count += 1
            label = _invalid_label(
                sample_row=sample_row,
                judge_model_id=judge_model_id,
                judge_provider=judge_provider,
                reason_code="judge_response_parse_or_call_failed",
            )
        labels.append(label)
    accepted = sum(1 for label in labels if label["delta_label"] != "invalid")
    report = {
        "route_id": ROUTE6A_ID,
        "label_schema_version": LABEL_SCHEMA_VERSION,
        "rubric_version": RUBRIC_VERSION,
        "prompt_version": PROMPT_VERSION,
        "judge_model_id": judge_model_id,
        "judge_provider": judge_provider,
        "sample_count": len(sample),
        "normalized_label_count": len(labels),
        "accepted_model_adjudicated_count": accepted,
        "invalid_or_failed_count": len(labels) - accepted,
        "counts_as_human_labels": False,
        "measurement_validation_candidate_allowed": False,
        "raw_api_responses_stored": False,
        "live_api_used": True,
        "claim_status": CLAIM_STATUS,
    }
    return labels, report


def _write_report_md(path: str | Path, *, readiness: Mapping[str, Any], manifest: Mapping[str, Any]) -> Path:
    lines = [
        "# Route 6A External Sufficiency Measurement Pilot",
        "",
        f"Status: {readiness['status']}",
        f"Claim status: `{CLAIM_STATUS}`",
        "",
        "## Inputs",
        "",
        f"- Route 4A rows available: `{readiness['route4_rows_count']}`",
        f"- Candidate pools available: `{readiness['candidate_pools_count']}`",
        f"- Context-pair sample size: `{readiness['context_pair_sample_count']}`",
        "",
        "## Rubric Boundary",
        "",
        f"- Rubric version: `{RUBRIC_VERSION}`",
        "- The judge-visible sample hides logloss, utility scores, gold-support labels, and Route 4 bridge measurements.",
        "- Model-adjudicated labels are not human labels and do not count for kappa.",
        "",
        "## Claim Boundary",
        "",
        "- `measurement_validation_candidate_allowed`: `false`",
        "- `calibrated_proxy_supported`: denied",
        "- `vinfo_proxy_supported`: denied",
        "- `operational_utility_only / no_claim_upgrade` remains active.",
        "",
        "## Storage Boundary",
        "",
        f"- Live API used: `{str(manifest['live_api_used']).lower()}`",
        "- Raw API responses stored: `false`",
        "- Operator inputs written: `false`",
    ]
    if readiness["reason_codes"]:
        lines.extend(["", "## Reason Codes", ""])
        lines.extend(f"- `{reason}`" for reason in readiness["reason_codes"])
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def run_route6a_measurement_pilot(
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    bridge_rows_path: str | Path = DEFAULT_BRIDGE_ROWS_PATH,
    candidate_pools_path: str | Path = DEFAULT_CANDIDATE_POOLS_PATH,
    sample_size: int = 24,
    run_live_adjudication: bool = False,
    judge_model_id: str | None = None,
    judge_provider: str | None = None,
    client: Any | None = None,
    env: Mapping[str, str] | None = None,
    judge_config_path: str | Path | None = DEFAULT_LOCAL_JUDGE_CONFIG,
    report_md_path: str | Path = DEFAULT_REPORT_MD,
) -> dict[str, Any]:
    bridge_rows = _read_jsonl(bridge_rows_path)
    candidate_pools = _read_jsonl(candidate_pools_path)
    sample = build_context_pair_sample(
        bridge_rows=bridge_rows,
        candidate_pools=candidate_pools,
        sample_size=sample_size,
    )
    rubric = build_frozen_rubric()
    output_path = Path(output_dir)
    reason_codes: list[str] = []
    status = "blocked_judge_unavailable"
    live_api_used = False
    judge_available = False
    labels: list[dict[str, Any]] = []
    adjudication_report: dict[str, Any] | None = None

    if not sample:
        status = "blocked_no_usable_route4a_context_pairs"
        reason_codes.append("no_usable_route4a_context_pairs")
    elif run_live_adjudication:
        resolved_client = client
        live_info: dict[str, Any] = {}
        if resolved_client is None:
            resolved_client, live_info = _default_live_client(env=env, config_path=judge_config_path)
            if resolved_client is None:
                reason_codes.append(str(live_info.get("reason_code") or "approved_model_judge_unavailable"))
        else:
            live_info = {
                "available": True,
                "judge_model_id": judge_model_id or "approved_model_judge",
                "judge_provider": judge_provider or "approved_provider",
                "max_completion_tokens": 256,
                "request_timeout_seconds": 60,
                "extra_body": {"enable_thinking": False},
            }
        if resolved_client is not None:
            resolved_model = str(judge_model_id or live_info.get("judge_model_id") or "").strip()
            resolved_provider = str(judge_provider or live_info.get("judge_provider") or "").strip()
            if not resolved_model:
                reason_codes.append("judge_model_unavailable")
            else:
                judge_available = True
                try:
                    labels, adjudication_report = _run_model_adjudication(
                        sample=sample,
                        rubric=rubric,
                        client=resolved_client,
                        judge_model_id=resolved_model,
                        judge_provider=resolved_provider or "approved_provider",
                        max_completion_tokens=int(live_info.get("max_completion_tokens") or 256),
                        timeout=int(live_info.get("request_timeout_seconds") or 60),
                        extra_body=live_info.get("extra_body") if isinstance(live_info.get("extra_body"), Mapping) else None,
                    )
                    live_api_used = True
                    status = "model_adjudication_completed"
                    if adjudication_report["accepted_model_adjudicated_count"] == 0:
                        status = "blocked_no_accepted_model_adjudicated_labels"
                        reason_codes.append("no_accepted_model_adjudicated_labels")
                except OpenAICompatibleError:
                    status = "blocked_judge_unavailable"
                    reason_codes.append("judge_call_failed")
    else:
        reason_codes.append("approved_model_judge_not_run_or_unavailable")

    manifest = _manifest(
        sample=sample,
        bridge_rows=bridge_rows,
        candidate_pools=candidate_pools,
        bridge_rows_path=bridge_rows_path,
        candidate_pools_path=candidate_pools_path,
        live_api_used=live_api_used,
    )
    readiness = _readiness_report(
        sample=sample,
        bridge_rows=bridge_rows,
        candidate_pools=candidate_pools,
        judge_available=judge_available,
        status=status,
        reason_codes=reason_codes,
        live_api_used=live_api_used,
    )

    _write_json(output_path / "sample_manifest.json", manifest)
    _write_jsonl(output_path / "context_pair_sample.jsonl", sample)
    _write_json(output_path / "rubric_frozen.json", rubric)
    _write_json(output_path / "readiness_report.json", readiness)
    if labels:
        _write_jsonl(output_path / "model_adjudicated_labels.jsonl", labels)
    if adjudication_report is not None:
        _write_json(output_path / "adjudication_report.json", adjudication_report)
    _write_report_md(report_md_path, readiness=readiness, manifest=manifest)

    result = deepcopy(dict(readiness))
    result["artifacts"] = {
        "sample_manifest": _path_ref(output_path / "sample_manifest.json"),
        "context_pair_sample": _path_ref(output_path / "context_pair_sample.jsonl"),
        "rubric_frozen": _path_ref(output_path / "rubric_frozen.json"),
        "readiness_report": _path_ref(output_path / "readiness_report.json"),
    }
    if labels:
        result["artifacts"]["model_adjudicated_labels"] = _path_ref(output_path / "model_adjudicated_labels.jsonl")
    if adjudication_report is not None:
        result["artifacts"]["adjudication_report"] = _path_ref(output_path / "adjudication_report.json")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Route 6A external sufficiency measurement pilot.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--bridge-rows", default=DEFAULT_BRIDGE_ROWS_PATH)
    parser.add_argument("--candidate-pools", default=DEFAULT_CANDIDATE_POOLS_PATH)
    parser.add_argument("--sample-size", type=int, default=24)
    parser.add_argument("--run-live-adjudication", action="store_true")
    parser.add_argument("--judge-config", default=DEFAULT_LOCAL_JUDGE_CONFIG)
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    args = parser.parse_args(argv)

    result = run_route6a_measurement_pilot(
        output_dir=args.output_dir,
        bridge_rows_path=args.bridge_rows,
        candidate_pools_path=args.candidate_pools,
        sample_size=args.sample_size,
        run_live_adjudication=args.run_live_adjudication,
        judge_config_path=args.judge_config,
        report_md_path=args.report_md,
    )
    print(
        canonical_json_dumps(
            {
                "status": result["status"],
                "claim_status": result["claim_status"],
                "context_pair_sample_count": result["context_pair_sample_count"],
                "live_api_used": result["live_api_used"],
                "measurement_validation_candidate_allowed": result["measurement_validation_candidate_allowed"],
                "reason_codes": result["reason_codes"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
