from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from dotenv import dotenv_values

from api.openai_compatible import (
    OpenAICompatibleClient,
    OpenAICompatibleCredentials,
    OpenAICompatibleError,
)
from api.settings import DEFAULT_API_PROFILE, ResolvedApiProfile, resolve_api_profile


DEFAULT_PROBE_MESSAGES = [
    {
        "role": "system",
        "content": "You are a deterministic answer replay scorer. Output the reference answer exactly and do not reveal reasoning.",
    },
    {
        "role": "user",
        "content": (
            "Repeat the reference answer exactly and output nothing else.\n\n"
            "Context:\n(no paragraphs)\n\n"
            "Question: What color is the clear daytime sky on Earth?\n"
            "Reference answer: blue"
        ),
    },
]
DEFAULT_PROBE_REQUEST_CONTRACT = {
    "max_completion_tokens": 16,
    "temperature": 0.0,
    "seed": 20260418,
    "stream": False,
    "n": 1,
    "logprobs": True,
    "top_logprobs": 0,
    "extra_body": {"enable_thinking": False},
}


def _load_env_values(env_path: str | Path | None) -> dict[str, str]:
    values: dict[str, str] = {}
    if env_path is not None and Path(env_path).exists():
        values.update({k: str(v) for k, v in dotenv_values(env_path).items() if v is not None})
    elif env_path is None and Path(".env").exists():
        values.update({k: str(v) for k, v in dotenv_values(".env").items() if v is not None})
    values.update({k: v for k, v in os.environ.items() if isinstance(v, str)})
    return values


def build_probe_client(
    *,
    env_path: str | Path | None = None,
    profile_name: str | None = None,
) -> tuple[ResolvedApiProfile, OpenAICompatibleClient]:
    env_values = _load_env_values(env_path)
    resolved = resolve_api_profile(
        env_values=env_values,
        profile_name=profile_name or DEFAULT_API_PROFILE,
    )
    if not resolved.base_url:
        raise ValueError(f"Missing provider base URL env var: {resolved.base_url_env}")
    if not resolved.api_key:
        raise ValueError(f"Missing provider api key env var: {resolved.api_key_env}")
    client = OpenAICompatibleClient(
        OpenAICompatibleCredentials(
            base_url=resolved.base_url,
            api_key=resolved.api_key,
        )
    )
    return resolved, client


def _extract_token_logprobs(response_payload: Mapping[str, Any]) -> tuple[tuple[float, ...], str]:
    choice = ((response_payload.get("choices") or [{}])[0]) if isinstance(response_payload, Mapping) else {}
    if not isinstance(choice, Mapping):
        raise ValueError(f"Unexpected choice payload: {choice!r}")
    message = choice.get("message") or {}
    if not isinstance(message, Mapping):
        raise ValueError(f"Unexpected message payload: {message!r}")
    if message.get("reasoning_content"):
        raise ValueError("provider returned reasoning_content, which violates the Phase 1 replay contract")
    logprobs_block = message.get("logprobs") or choice.get("logprobs") or {}
    if not isinstance(logprobs_block, Mapping):
        raise ValueError(f"Unexpected logprobs payload: {logprobs_block!r}")
    logprob_items = logprobs_block.get("content") or []
    token_logprobs = tuple(float(item["logprob"]) for item in logprob_items if "logprob" in item)
    if not token_logprobs:
        raise ValueError("response did not include token logprobs")
    if len(token_logprobs) >= 2 and all(abs(value) <= 1e-12 for value in token_logprobs):
        raise ValueError("provider returned degenerate all-zero token logprobs")
    return token_logprobs, str(message.get("content") or "")


def probe_model(
    client: OpenAICompatibleClient,
    *,
    resolved_profile: ResolvedApiProfile,
    model_id: str,
    timeout: int = 60,
) -> dict[str, Any]:
    contract = dict(DEFAULT_PROBE_REQUEST_CONTRACT)
    try:
        response_payload = client.chat_completion(
            model=model_id,
            messages=DEFAULT_PROBE_MESSAGES,
            max_completion_tokens=int(contract["max_completion_tokens"]),
            temperature=float(contract["temperature"]),
            seed=int(contract["seed"]),
            stream=bool(contract["stream"]),
            n=int(contract["n"]),
            logprobs=bool(contract["logprobs"]),
            top_logprobs=int(contract["top_logprobs"]),
            extra_body=dict(contract["extra_body"]),
            timeout=timeout,
        )
        token_logprobs, content = _extract_token_logprobs(response_payload)
    except (OpenAICompatibleError, ValueError, KeyError, IndexError, TypeError) as exc:
        return {
            "status": "red",
            "profile": resolved_profile.profile_name,
            "provider": resolved_profile.provider_name,
            "base_url": resolved_profile.base_url,
            "model_id": model_id,
            "request_contract": {
                "logprobs": bool(contract["logprobs"]),
                "top_logprobs": int(contract["top_logprobs"]),
                "stream": bool(contract["stream"]),
                "n": int(contract["n"]),
                "enable_thinking": bool(contract["extra_body"]["enable_thinking"]),
            },
            "error": str(exc),
        }

    nonzero_token_count = sum(1 for value in token_logprobs if abs(value) > 1e-12)
    return {
        "status": "green",
        "profile": resolved_profile.profile_name,
        "provider": resolved_profile.provider_name,
        "base_url": resolved_profile.base_url,
        "model_id": model_id,
        "request_contract": {
            "logprobs": bool(contract["logprobs"]),
            "top_logprobs": int(contract["top_logprobs"]),
            "stream": bool(contract["stream"]),
            "n": int(contract["n"]),
            "enable_thinking": bool(contract["extra_body"]["enable_thinking"]),
        },
        "response_status": "200",
        "token_count": len(token_logprobs),
        "nonzero_token_count": nonzero_token_count,
        "logprob_sum": sum(token_logprobs),
        "content_preview": content[:80],
    }


def probe_visible_models(
    *,
    env_path: str | Path | None = None,
    profile_name: str | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    resolved, client = build_probe_client(env_path=env_path, profile_name=profile_name)
    visible_models = sorted(
        {
            str(item["id"])
            for item in client.list_models()
            if isinstance(item, Mapping) and item.get("id")
        }
    )
    results = [
        probe_model(
            client,
            resolved_profile=resolved,
            model_id=model_id,
            timeout=timeout,
        )
        for model_id in visible_models
    ]
    usable_models = [item["model_id"] for item in results if item["status"] == "green"]
    unusable_models = [
        {"model_id": item["model_id"], "error": item["error"]}
        for item in results
        if item["status"] != "green"
    ]
    return {
        "status": "computed",
        "profile": resolved.profile_name,
        "provider": resolved.provider_name,
        "base_url": resolved.base_url,
        "visible_model_count": len(visible_models),
        "usable_model_count": len(usable_models),
        "usable_models": usable_models,
        "unusable_models": unusable_models,
        "results": results,
    }


def format_probe_markdown(
    payload: Mapping[str, Any],
    *,
    generated_at_utc: str | None = None,
    command: str | None = None,
    json_report_path: str | None = None,
) -> str:
    usable_models = [str(item) for item in payload.get("usable_models") or ()]
    generated_at = generated_at_utc or datetime.now(timezone.utc).isoformat()
    lines = [
        "# Phase 1 Usable Models",
        "",
        f"- Generated at UTC: `{generated_at}`",
        f"- Profile: `{payload.get('profile', '')}`",
        f"- Provider: `{payload.get('provider', '')}`",
        f"- Base URL: `{payload.get('base_url', '')}`",
        f"- Visible model count: `{payload.get('visible_model_count', 0)}`",
        f"- Usable model count: `{payload.get('usable_model_count', 0)}`",
    ]
    if command:
        lines.extend(
            [
                "",
                "## Regenerate",
                "",
                "```bash",
                command,
                "```",
            ]
        )
    if json_report_path:
        lines.extend(
            [
                "",
                "## Full Report",
                "",
                f"- JSON report: `{json_report_path}`",
            ]
        )
    lines.extend(["", "## Usable Models", ""])
    if usable_models:
        lines.extend(f"- `{model_id}`" for model_id in usable_models)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This document only lists models that passed the current Phase 1 probe contract.",
            "- The probe requires `logprobs=true`, `top_logprobs=0`, `stream=false`, `n=1`, and `enable_thinking=false`.",
            "- Models that are visible in `/models` but fail the probe are excluded from the usable list.",
        ]
    )
    return "\n".join(lines) + "\n"
