from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Mapping
from typing import Sequence

from cps.benchmarks.common import read_jsonl
from cps.benchmarks.common import write_json
from cps.benchmarks.common import write_jsonl
from cps.benchmarks.hashing import canonical_json_dumps
from cps.evaluators.teacher_forced_scoring_contract import CLAIM_STATUS
from cps.evaluators.teacher_forced_scoring_contract import build_teacher_forced_score_record
from cps.evaluators.teacher_forced_scoring_contract import validate_teacher_forced_score_record


ARTIFACT_DIR = Path("artifacts/experiments/teacher_forced_logprobe_backend")
EPN_TARGET_ROWS = Path("artifacts/experiments/evidence_path_nll_protocol/evidence_path_target_rows.jsonl")
EPN_TARGET_CONTRACT = Path("artifacts/experiments/evidence_path_nll_protocol/target_contract.json")
EPN_READINESS = Path("artifacts/experiments/evidence_path_nll_protocol/protocol_readiness_decision.json")
TERMINAL_STATUS = "TEACHER_FORCED_LOGPROBE_BACKEND_READINESS_COMPLETED"

InjectedScorer = Callable[..., Mapping[str, Any]]


class TeacherForcedBackendInputMissingError(RuntimeError):
    """Raised when required EPN artifacts are missing."""


class BackendUnavailableError(RuntimeError):
    """Raised when a configured scorer cannot produce a fixed-target score."""


def _resolve(root: str | Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else Path(root) / candidate


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.name if candidate.is_absolute() else candidate.as_posix()


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip():
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _load_env(root: Path, override: Mapping[str, str] | None = None) -> dict[str, str]:
    if override is not None:
        return {str(key): str(value) for key, value in override.items()}
    env: dict[str, str] = {}
    env.update(_load_env_file(root / ".env"))
    env.update(_load_env_file(root / ".env.local"))
    for key in (
        "TFS_ALLOW_LIVE_COMPLETION_LOGPROBS",
        "TFS_LOCAL_CAUSAL_LM_PATH",
        "TFS_LOCAL_MODEL_PATH",
        "TFS_OPENAI_COMPLETION_API_KEY",
        "TFS_OPENAI_COMPLETION_BASE_URL",
        "TFS_OPENAI_COMPLETION_LOGPROBS_MODE",
        "TFS_OPENAI_COMPLETION_MODEL",
    ):
        if os.environ.get(key):
            env[key] = str(os.environ[key])
    return env


def reconstruct_evidence_path_target_text(row: Mapping[str, Any]) -> str:
    packet_ids = [str(value) for value in row.get("evidence_path_packet_ids") or []]
    source_doc_ids = [str(value) for value in row.get("evidence_path_source_doc_ids") or []]
    spans = [str(value) for value in row.get("evidence_path_spans") or []]
    packet_hashes = [str(value) for value in row.get("evidence_path_packet_hashes") or []]
    lines = ["EVIDENCE_PATH_V1"]
    for index, packet_id in enumerate(packet_ids, start=1):
        source_doc_id = source_doc_ids[index - 1] if index <= len(source_doc_ids) else ""
        span = spans[index - 1] if index <= len(spans) else ""
        packet_hash = packet_hashes[index - 1] if index <= len(packet_hashes) else ""
        lines.append(f"{index}\t{source_doc_id}\t{span}\t{packet_id}\t{packet_hash}")
    return "\n".join(lines)


def _prompt_text_for_row(row: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "Score the fixed evidence-path target continuation.",
            "Use teacher-forced log probabilities for the exact target text.",
            f"original_instance_id: {row.get('original_instance_id', '')}",
            "target:",
        ]
    )


def _quantiles(values: Sequence[float]) -> dict[str, float | None]:
    if not values:
        return {"max": None, "mean": None, "median": None, "min": None}
    sorted_values = sorted(float(value) for value in values)
    midpoint = len(sorted_values) // 2
    median = (
        sorted_values[midpoint]
        if len(sorted_values) % 2
        else (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2
    )
    return {
        "max": max(sorted_values),
        "mean": sum(sorted_values) / len(sorted_values),
        "median": median,
        "min": min(sorted_values),
    }


def _load_required_inputs(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    required = {
        "epn_readiness": EPN_READINESS,
        "epn_target_contract": EPN_TARGET_CONTRACT,
        "epn_target_rows": EPN_TARGET_ROWS,
    }
    missing = [name for name, path in required.items() if not _resolve(root, path).exists()]
    if missing:
        raise TeacherForcedBackendInputMissingError(
            "missing required teacher-forced backend inputs: " + ", ".join(sorted(missing))
        )
    return (
        read_jsonl(_resolve(root, EPN_TARGET_ROWS)),
        _read_json(_resolve(root, EPN_TARGET_CONTRACT)),
        _read_json(_resolve(root, EPN_READINESS)),
    )


def _dependency_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def build_backend_capability_report(*, env: Mapping[str, str] | None = None, root: str | Path = ".") -> dict[str, Any]:
    repo_root = Path(root)
    live_env = _load_env(repo_root, env)
    transformers_available = _dependency_available("transformers")
    torch_available = _dependency_available("torch")
    local_model_path = live_env.get("TFS_LOCAL_CAUSAL_LM_PATH") or live_env.get("TFS_LOCAL_MODEL_PATH") or ""
    local_model_path_exists = bool(local_model_path) and Path(local_model_path).exists()
    local_available = transformers_available and torch_available and local_model_path_exists

    completion_base_url_present = bool(live_env.get("TFS_OPENAI_COMPLETION_BASE_URL"))
    completion_model_present = bool(live_env.get("TFS_OPENAI_COMPLETION_MODEL"))
    completion_key_present = bool(live_env.get("TFS_OPENAI_COMPLETION_API_KEY"))
    completion_mode = live_env.get("TFS_OPENAI_COMPLETION_LOGPROBS_MODE") or "not_configured"
    completion_live_allowed = live_env.get("TFS_ALLOW_LIVE_COMPLETION_LOGPROBS") == "1"
    completion_available = (
        completion_live_allowed
        and completion_base_url_present
        and completion_model_present
        and completion_key_present
        and completion_mode == "echo_prompt_token_logprobs"
    )

    available_types: list[str] = []
    backend_id = "blocked_no_teacher_forced_backend"
    evaluator_id = "teacher_forced_logprobe_backend_inventory_v1"
    if local_available:
        available_types.append("local_causal_lm_teacher_forced")
        backend_id = "local_causal_lm_teacher_forced"
    if completion_available:
        available_types.append("openai_compatible_completion_echo_prompt_logprobs")
        if backend_id == "blocked_no_teacher_forced_backend":
            backend_id = "openai_compatible_completion_echo_prompt_logprobs"

    blocked_reasons: list[str] = []
    if not local_available:
        if not transformers_available or not torch_available:
            blocked_reasons.append("local_causal_lm_dependencies_unavailable")
        elif not local_model_path_exists:
            blocked_reasons.append("local_causal_lm_model_path_unavailable")
    if not completion_available:
        if not completion_live_allowed:
            blocked_reasons.append("completion_logprobs_live_probe_not_enabled")
        if not completion_base_url_present or not completion_model_present:
            blocked_reasons.append("completion_logprobs_endpoint_not_configured")
        if not completion_key_present:
            blocked_reasons.append("completion_logprobs_api_key_not_configured")
        if completion_mode != "echo_prompt_token_logprobs":
            blocked_reasons.append("completion_logprobs_mode_not_fixed_target_echo_prompt")

    teacher_forced_available = bool(available_types)
    return {
        "available_backend_types": available_types,
        "backend_id": backend_id,
        "blocked_reason": None if teacher_forced_available else "blocked_no_teacher_forced_backend",
        "blocked_reason_details": sorted(set(blocked_reasons)),
        "chat_logprob_path_rejected_for_fixed_target_scoring": True,
        "claim_status": CLAIM_STATUS,
        "evaluator_id": evaluator_id,
        "live_api_used": False,
        "local_model_scorer_available": local_available,
        "local_model_scorer_details": {
            "local_model_path_configured": bool(local_model_path),
            "local_model_path_exists": local_model_path_exists,
            "torch_available": torch_available,
            "transformers_available": transformers_available,
        },
        "openai_compatible_completion_logprobs_available": completion_available,
        "openai_compatible_completion_logprobs_details": {
            "api_key_present": completion_key_present,
            "base_url_configured": completion_base_url_present,
            "live_probe_enabled": completion_live_allowed,
            "mode": completion_mode,
            "model_configured": completion_model_present,
        },
        "raw_responses_stored": False,
        "schema_version": "teacher_forced_backend_capability_report_v1",
        "secrets_exposed": False,
        "teacher_forced_target_scoring_available": teacher_forced_available,
    }


class LocalCausalLMTeacherForcedScorer:
    backend_id = "local_causal_lm_teacher_forced"

    def __init__(self, *, model_path: str) -> None:
        if not model_path:
            raise BackendUnavailableError("local_causal_lm_model_path_unavailable")
        try:
            import torch
            from transformers import AutoModelForCausalLM
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise BackendUnavailableError("local_causal_lm_dependencies_unavailable") from exc
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        self.model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True)
        self.model.eval()
        self.model_id = str(model_path)
        self.tokenizer_id = str(model_path)

    def score(self, *, prompt_text: str, fixed_target_text: str, target_row: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, Any]:
        prompt_ids = self.tokenizer(prompt_text, add_special_tokens=False).input_ids
        combined_ids = self.tokenizer(prompt_text + fixed_target_text, add_special_tokens=False).input_ids
        if combined_ids[: len(prompt_ids)] != prompt_ids:
            raise BackendUnavailableError("tokenization_prefix_mismatch")
        target_token_ids = combined_ids[len(prompt_ids) :]
        if not target_token_ids:
            raise BackendUnavailableError("empty_target_tokenization")
        input_ids = self.torch.tensor([combined_ids])
        with self.torch.no_grad():
            logits = self.model(input_ids).logits[0]
            log_probs = self.torch.log_softmax(logits, dim=-1)
        per_token_logprobs: list[float] = []
        for position, token_id in enumerate(target_token_ids, start=len(prompt_ids)):
            previous_position = position - 1
            per_token_logprobs.append(float(log_probs[previous_position, int(token_id)].item()))
        return build_teacher_forced_score_record(
            deterministic_settings={"local_files_only": True, "temperature": 0},
            fixed_target_text=fixed_target_text,
            materialization_policy_hash=str(contract.get("materialization_policy_hash") or ""),
            per_token_logprobs=per_token_logprobs,
            prompt_template_hash=str(contract.get("prompt_template_hash") or ""),
            prompt_text=prompt_text,
            scorer_model_id=self.model_id,
            scoring_backend_id=self.backend_id,
            scoring_policy={"teacher_forced": True, "backend_type": "local_causal_lm"},
            target_format_hash=str(contract.get("target_format_hash") or ""),
            target_token_ids=target_token_ids,
            tokenizer_id=self.tokenizer_id,
            target_row_id=str(target_row.get("target_row_id") or ""),
            target_text_hash=str(target_row.get("target_text_hash") or ""),
        )


class OpenAICompatibleCompletionLogprobScorer:
    backend_id = "openai_compatible_completion_echo_prompt_logprobs"

    def __init__(self, *, api_key: str, base_url: str, model_id: str) -> None:
        if not api_key or not base_url or not model_id:
            raise BackendUnavailableError("completion_logprobs_endpoint_not_configured")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id

    def score(self, *, prompt_text: str, fixed_target_text: str, target_row: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, Any]:
        joined_prompt = prompt_text + fixed_target_text
        request_payload = {
            "echo": True,
            "logprobs": 0,
            "max_tokens": 0,
            "model": self.model_id,
            "prompt": joined_prompt,
            "temperature": 0,
        }
        request = urllib.request.Request(
            f"{self.base_url}/completions",
            data=json.dumps(request_payload).encode("utf-8"),
            headers={"Authorization": " ".join(["Bearer", self.api_key]), "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise BackendUnavailableError(f"completion_logprobs_http_{exc.code}") from exc
        except (OSError, TimeoutError, json.JSONDecodeError) as exc:
            raise BackendUnavailableError("completion_logprobs_request_or_parse_failure") from exc

        logprobs = ((payload.get("choices") or [{}])[0].get("logprobs") or {})
        text_offsets = [int(value) for value in logprobs.get("text_offset") or []]
        token_logprobs = [float(value) for value in logprobs.get("token_logprobs") or [] if value is not None]
        tokens = [str(value) for value in logprobs.get("tokens") or []]
        token_ids = list(logprobs.get("token_ids") or [])
        target_indices = [index for index, offset in enumerate(text_offsets) if offset >= len(prompt_text)]
        if not target_indices:
            raise BackendUnavailableError("completion_logprobs_missing_target_offsets")
        if not token_ids:
            raise BackendUnavailableError("completion_logprobs_missing_token_ids")
        target_token_logprobs = [token_logprobs[index] for index in target_indices if index < len(token_logprobs)]
        target_token_ids = [token_ids[index] for index in target_indices if index < len(token_ids)]
        target_tokens = [tokens[index] for index in target_indices if index < len(tokens)]
        if "".join(target_tokens).strip() != fixed_target_text.strip():
            raise BackendUnavailableError("completion_logprobs_target_token_text_mismatch")
        return build_teacher_forced_score_record(
            deterministic_settings={"echo": True, "temperature": 0},
            fixed_target_text=fixed_target_text,
            materialization_policy_hash=str(contract.get("materialization_policy_hash") or ""),
            per_token_logprobs=target_token_logprobs,
            prompt_template_hash=str(contract.get("prompt_template_hash") or ""),
            prompt_text=prompt_text,
            scorer_model_id=self.model_id,
            scoring_backend_id=self.backend_id,
            scoring_policy={"teacher_forced": True, "backend_type": "openai_compatible_completion_echo"},
            target_format_hash=str(contract.get("target_format_hash") or ""),
            target_token_ids=target_token_ids,
            tokenizer_id=f"{self.model_id}:completion_echo",
            target_row_id=str(target_row.get("target_row_id") or ""),
            target_text_hash=str(target_row.get("target_text_hash") or ""),
        )


def _select_default_scorer(capability: Mapping[str, Any], env: Mapping[str, str]) -> LocalCausalLMTeacherForcedScorer | OpenAICompatibleCompletionLogprobScorer | None:
    if capability.get("local_model_scorer_available"):
        model_path = env.get("TFS_LOCAL_CAUSAL_LM_PATH") or env.get("TFS_LOCAL_MODEL_PATH") or ""
        return LocalCausalLMTeacherForcedScorer(model_path=model_path)
    if capability.get("openai_compatible_completion_logprobs_available"):
        return OpenAICompatibleCompletionLogprobScorer(
            api_key=str(env.get("TFS_OPENAI_COMPLETION_API_KEY") or ""),
            base_url=str(env.get("TFS_OPENAI_COMPLETION_BASE_URL") or ""),
            model_id=str(env.get("TFS_OPENAI_COMPLETION_MODEL") or ""),
        )
    return None


def _select_probe_rows(target_rows: Sequence[Mapping[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen_instances: set[str] = set()
    sorted_rows = sorted((dict(row) for row in target_rows), key=lambda row: str(row.get("target_row_id") or ""))
    for row in sorted_rows:
        instance_id = str(row.get("original_instance_id") or "")
        if instance_id in seen_instances:
            continue
        selected.append(row)
        seen_instances.add(instance_id)
        if len(selected) >= limit:
            break
    if len(selected) < min(limit, len(sorted_rows)):
        selected_ids = {str(row.get("target_row_id") or "") for row in selected}
        for row in sorted_rows:
            row_id = str(row.get("target_row_id") or "")
            if row_id in selected_ids:
                continue
            selected.append(row)
            selected_ids.add(row_id)
            if len(selected) >= limit:
                break
    return selected


def _build_probe_reports(
    *,
    capability: Mapping[str, Any],
    contract: Mapping[str, Any],
    injected_scorer: InjectedScorer | None,
    probe_limit: int,
    target_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any]]:
    scorer = injected_scorer
    if scorer is None:
        return [], {}, {}, {}
    selected_rows = _select_probe_rows(target_rows, probe_limit)
    score_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for row in selected_rows:
        prompt_text = _prompt_text_for_row(row)
        fixed_target_text = reconstruct_evidence_path_target_text(row)
        try:
            score = dict(
                scorer(
                    prompt_text=prompt_text,
                    fixed_target_text=fixed_target_text,
                    target_row=row,
                    contract=contract,
                )
            )
            validation = validate_teacher_forced_score_record(score)
            if not validation["passed"]:
                failures.append(
                    {
                        "errors": validation["errors"],
                        "target_row_id": str(row.get("target_row_id") or ""),
                    }
                )
                continue
            score_rows.append(
                {
                    "claim_status": CLAIM_STATUS,
                    "original_instance_id": str(row.get("original_instance_id") or ""),
                    "schema_version": "teacher_forced_scoring_probe_row_v1",
                    "scoring_backend_id": score["scoring_backend_id"],
                    "scorer_model_id": score["scorer_model_id"],
                    "target_nll": score["target_nll"],
                    "target_nll_normalized": score["target_nll_normalized"],
                    "target_row_id": str(row.get("target_row_id") or score.get("target_row_id") or ""),
                    "target_text_hash": str(row.get("target_text_hash") or score.get("target_text_hash") or ""),
                    "target_token_count": int(score["target_token_count"]),
                    "tokenizer_id": score["tokenizer_id"],
                }
            )
        except BackendUnavailableError as exc:
            failures.append({"reason": str(exc), "target_row_id": str(row.get("target_row_id") or "")})

    target_token_counts = [int(row["target_token_count"]) for row in score_rows]
    target_nlls = [float(row["target_nll"]) for row in score_rows]
    normalized_nlls = [float(row["target_nll_normalized"]) for row in score_rows]
    duplicate_counts = Counter(str(row.get("target_text_hash") or "") for row in selected_rows)
    scored_by_hash: dict[str, list[float]] = {}
    for row in score_rows:
        scored_by_hash.setdefault(str(row["target_text_hash"]), []).append(float(row["target_nll"]))
    inconsistent_hashes = [
        target_hash
        for target_hash, values in scored_by_hash.items()
        if len(values) > 1 and max(values) - min(values) > 1e-9
    ]
    report = {
        "claim_status": CLAIM_STATUS,
        "duplicate_target_hash_count": sum(1 for count in duplicate_counts.values() if count > 1),
        "live_api_used": bool(capability.get("live_api_used")),
        "multi_token_target_rate": (
            sum(1 for count in target_token_counts if count > 1) / len(target_token_counts)
            if target_token_counts
            else 0.0
        ),
        "normalized_target_nll_distribution": _quantiles(normalized_nlls),
        "raw_responses_stored": False,
        "schema_version": "teacher_forced_scoring_probe_report_v1",
        "scoring_failure_count": len(failures),
        "scoring_success_count": len(score_rows),
        "target_count_attempted": len(selected_rows),
        "target_count_scored": len(score_rows),
        "target_nll_distribution": _quantiles(target_nlls),
        "teacher_forced_target_score_available": bool(score_rows),
        "token_length_distribution": _quantiles([float(value) for value in target_token_counts]),
        "unique_original_instances": len({row["original_instance_id"] for row in score_rows}),
        "unique_target_hashes": len({row["target_text_hash"] for row in score_rows}),
    }
    tokenization = {
        "claim_status": CLAIM_STATUS,
        "schema_version": "teacher_forced_tokenization_probe_report_v1",
        "target_count_scored": len(score_rows),
        "target_token_count_distribution": report["token_length_distribution"],
        "tokenizer_ids": sorted({str(row["tokenizer_id"]) for row in score_rows}),
    }
    repeatability = {
        "claim_status": CLAIM_STATUS,
        "duplicate_target_hash_count": report["duplicate_target_hash_count"],
        "duplicate_target_inconsistent_hashes": inconsistent_hashes,
        "repeat_scoring_consistency": "passed"
        if report["duplicate_target_hash_count"] and not inconsistent_hashes
        else "failed"
        if inconsistent_hashes
        else "not_applicable",
        "schema_version": "teacher_forced_repeatability_report_v1",
    }
    return score_rows, report, tokenization, repeatability


def _blocked_report(capability: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "blocked_reason": capability.get("blocked_reason") or "blocked_no_teacher_forced_backend",
        "blocked_reason_details": list(capability.get("blocked_reason_details") or []),
        "claim_status": CLAIM_STATUS,
        "fake_scores_generated": False,
        "raw_responses_stored": False,
        "schema_version": "teacher_forced_backend_blocked_report_v1",
        "teacher_forced_target_score_available": False,
    }


def _readiness_decision(
    *,
    blocked_report: Mapping[str, Any] | None,
    capability: Mapping[str, Any],
    scoring_report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if scoring_report and scoring_report.get("teacher_forced_target_score_available"):
        status = "TEACHER_FORCED_BACKEND_READY_FOR_EPN_BRIDGE_PROTOCOL"
        bridge_allowed = True
        epn_blocked = False
    elif capability.get("teacher_forced_target_scoring_available"):
        status = "BLOCKED_BACKEND_DOES_NOT_SCORE_FIXED_TARGET"
        bridge_allowed = False
        epn_blocked = True
    else:
        status = "BLOCKED_NO_TEACHER_FORCED_BACKEND"
        bridge_allowed = False
        epn_blocked = True
    return {
        "blocked_reason": None if blocked_report is None else blocked_report.get("blocked_reason"),
        "claim_status": CLAIM_STATUS,
        "epn_remains_blocked": epn_blocked,
        "future_evidence_path_nll_bridge_pilot_allowed": bridge_allowed,
        "no_claim_upgrade": True,
        "raw_responses_stored": False,
        "route5_locked": True,
        "route8_locked": True,
        "schema_version": "teacher_forced_backend_readiness_decision_v1",
        "terminal_status": status,
    }


def _capability_doc(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Teacher-Forced LogProbe Backend Capability",
            "",
            f"Claim status: {CLAIM_STATUS}",
            "",
            f"- teacher_forced_target_scoring_available: {str(report['teacher_forced_target_scoring_available']).lower()}",
            f"- local_model_scorer_available: {str(report['local_model_scorer_available']).lower()}",
            f"- openai_compatible_completion_logprobs_available: {str(report['openai_compatible_completion_logprobs_available']).lower()}",
            f"- chat_logprob_path_rejected_for_fixed_target_scoring: {str(report['chat_logprob_path_rejected_for_fixed_target_scoring']).lower()}",
            f"- blocked_reason: {report['blocked_reason']}",
            "",
            "Generated chat-completion logprobs remain rejected for fixed-target evidence-path NLL.",
            "",
        ]
    )


def _contract_doc() -> str:
    fields = "\n".join(f"- {field}" for field in sorted(
        [
            "prompt_text",
            "fixed_target_text",
            "prompt_template_hash",
            "target_format_hash",
            "materialization_policy_hash",
            "tokenizer_id",
            "target_token_ids",
            "target_token_count",
            "per_token_logprobs",
            "target_nll",
            "target_nll_normalized",
            "scoring_backend_id",
            "scorer_model_id",
            "scoring_policy",
            "deterministic_settings",
            "raw_response_stored=false",
        ]
    ))
    return "\n".join(
        [
            "# Teacher-Forced LogProbe Scoring Contract",
            "",
            f"Claim status: {CLAIM_STATUS}",
            "",
            "## Required Fields",
            "",
            fields,
            "",
            "Validation rejects empty fixed targets, generated-target mismatches, missing tokenization metadata, missing target logprobs, raw response payload fields, and secret-like fields.",
            "",
        ]
    )


def _readiness_doc(readiness: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Teacher-Forced LogProbe Backend Readiness",
            "",
            f"Claim status: {CLAIM_STATUS}",
            f"Terminal status: {readiness['terminal_status']}",
            "",
            f"Future evidence-path NLL bridge pilot allowed: {str(readiness['future_evidence_path_nll_bridge_pilot_allowed']).lower()}",
            f"EPN remains blocked: {str(readiness['epn_remains_blocked']).lower()}",
            "Route 5 remains locked. Route 8 remains locked. No bridge calibration was run.",
            "",
        ]
    )


def run_teacher_forced_logprobe_backend_package(
    *,
    root: str | Path = ".",
    env: Mapping[str, str] | None = None,
    injected_scorer: InjectedScorer | None = None,
    probe_limit: int = 50,
) -> dict[str, Any]:
    repo_root = Path(root)
    target_rows, epn_contract, _epn_readiness = _load_required_inputs(repo_root)
    capability = build_backend_capability_report(env=env, root=repo_root)
    live_env = _load_env(repo_root, env)
    scorer = injected_scorer
    if scorer is None:
        default_scorer = _select_default_scorer(capability, live_env)
        if default_scorer is not None:
            scorer = default_scorer.score

    artifact_dir = repo_root / ARTIFACT_DIR
    docs_dir = repo_root / "docs/experiments"
    artifact_paths = {
        "backend_capability_report": write_json(artifact_dir / "backend_capability_report.json", capability),
    }
    score_rows: list[dict[str, Any]] = []
    scoring_report: dict[str, Any] | None = None
    blocked: dict[str, Any] | None = None
    if scorer is None:
        blocked = _blocked_report(capability)
        artifact_paths["blocked_report"] = write_json(artifact_dir / "blocked_report.json", blocked)
    else:
        score_rows, scoring_report, tokenization_report, repeatability_report = _build_probe_reports(
            capability=capability,
            contract=epn_contract,
            injected_scorer=scorer,
            probe_limit=probe_limit,
            target_rows=target_rows,
        )
        if score_rows:
            artifact_paths["scoring_probe_rows"] = write_jsonl(
                artifact_dir / "scoring_probe_rows.jsonl",
                score_rows,
            )
            artifact_paths["scoring_probe_report"] = write_json(
                artifact_dir / "scoring_probe_report.json",
                scoring_report,
            )
            artifact_paths["tokenization_probe_report"] = write_json(
                artifact_dir / "tokenization_probe_report.json",
                tokenization_report,
            )
            artifact_paths["repeatability_report"] = write_json(
                artifact_dir / "repeatability_report.json",
                repeatability_report,
            )
        else:
            blocked = _blocked_report(
                {
                    **capability,
                    "blocked_reason": "blocked_backend_does_not_score_fixed_target",
                    "blocked_reason_details": ["score_record_validation_failed_or_backend_error"],
                }
            )
            artifact_paths["blocked_report"] = write_json(artifact_dir / "blocked_report.json", blocked)

    readiness = _readiness_decision(
        blocked_report=blocked,
        capability=capability if injected_scorer is None else {**capability, "teacher_forced_target_scoring_available": bool(score_rows)},
        scoring_report=scoring_report,
    )
    artifact_paths["readiness_decision"] = write_json(artifact_dir / "readiness_decision.json", readiness)

    docs_dir.mkdir(parents=True, exist_ok=True)
    doc_paths = {
        "backend_capability_doc": docs_dir / "TeacherForcedLogProbe-backend-capability.md",
        "backend_readiness_doc": docs_dir / "TeacherForcedLogProbe-backend-readiness.md",
        "scoring_contract_doc": docs_dir / "TeacherForcedLogProbe-scoring-contract.md",
    }
    doc_paths["backend_capability_doc"].write_text(_capability_doc(capability), encoding="utf-8")
    doc_paths["scoring_contract_doc"].write_text(_contract_doc(), encoding="utf-8")
    doc_paths["backend_readiness_doc"].write_text(_readiness_doc(readiness), encoding="utf-8")
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
        "readiness_decision": readiness["terminal_status"],
        "scoring_probe_status": "run" if score_rows else "blocked",
        "teacher_forced_target_scoring_available": bool(score_rows),
        "terminal_status": TERMINAL_STATUS,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run TFS teacher-forced LogProbe backend readiness package.")
    parser.add_argument("--root", default=".", help="Repository root containing EPN artifacts.")
    parser.add_argument("--probe-limit", default=50, type=int, help="Maximum deterministic target rows to score.")
    args = parser.parse_args(argv)
    result = run_teacher_forced_logprobe_backend_package(root=args.root, probe_limit=args.probe_limit)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
