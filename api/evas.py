from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values

from api.openai_compatible import OpenAICompatibleClient, OpenAICompatibleCredentials
from cps.data.manifest import load_phase0_config
from cps.runtime.secrets import mask_secret


EVAS_DEFAULT_BASE_URL = "https://api.evas.ai/v1"
EVAS_RECOMMENDED_MODELS = {
    "frontier": "openai/gpt-5.4",
    "small": "openai/gpt-5.4-mini",
    "coding": "openai/gpt-5.3-codex",
}
EVAS_MODEL_ENV_MAP = {
    "frontier": "EVAS_FRONTIER_MODEL",
    "small": "EVAS_SMALL_MODEL",
    "coding": "EVAS_CODING_MODEL",
}
EVAS_MODEL_NOTES = {
    "openai/gpt-5.4": "通用能力最强，适合作为 EVAS 下的 frontier 默认模型。",
    "openai/gpt-5.4-mini": "延迟和成本更稳，适合作为 EVAS 下的 small 默认模型。",
    "openai/gpt-5.3-codex": "更适合代码和实现辅助任务。",
    "xiaomi/mimo-v2-flash": "响应快，但这次探测里没有可用 logprobs，更适合作为普通聊天备选。",
    "kimi-k2": "会返回 reasoning_content，不适合当前 Phase 1 forced-decode scorer。",
    "kimi-k2.5": "会返回 reasoning_content，不适合当前 Phase 1 forced-decode scorer。",
    "kimi-k2.6": "会返回 reasoning_content，不适合当前 Phase 1 forced-decode scorer。",
    "kimi-k2-thinking": "偏 reasoning 路线，不适合当前 Phase 1 forced-decode scorer。",
    "moonshotai/kimi-k2.5": "当前温度参数受限，而且会返回 reasoning_content。",
    "moonshotai/kimi-k2.6": "当前温度参数受限，而且会返回 reasoning_content。",
    "xiaomi/mimo-v2-pro": "偏 reasoning 输出，不适合当前测量链。",
    "xiaomi/mimo-v2-omni": "偏多模态/推理路线，不适合当前测量链。",
    "evas/auto": "路由不固定，只适合临时聊天，不适合实验配置。",
}
PHASE1_LOGPROB_WARNING = (
    "当前 EVAS 已探测模型在 chat/completions 返回中没有稳定可用的 token logprobs，"
    "因此还不能直接替换 Phase 1 的 delta_loo scorer。"
)
PHASE1_LOCK_NOTE = (
    "Phase 1 当前仍按仓库既有配置锁定在 DashScope + Qwen3 模型族；"
    "EVAS 目录只是补充 API 管理和候选模型探测，不会覆盖原来的 Phase 配置。"
)


@dataclass(frozen=True)
class EvasApiSettings:
    base_url: str
    api_key: str
    masked_api_key: str
    role_models: dict[str, str]

    def credentials(self) -> OpenAICompatibleCredentials:
        return OpenAICompatibleCredentials(base_url=self.base_url, api_key=self.api_key)


def load_phase1_locked_models(phase1_config_path: str | Path = "phase1.yaml") -> dict[str, object]:
    config = load_phase0_config(phase1_config_path)
    provider_block = dict(config.get("provider") or {})
    model_blocks = dict(config.get("models") or {})
    return {
        "provider_name": str(provider_block.get("name") or ""),
        "api_style": str(provider_block.get("api_style") or ""),
        "base_url_env": str(provider_block.get("base_url_env") or ""),
        "api_key_env": str(provider_block.get("api_key_env") or ""),
        "roles": {
            role: str((model_blocks.get(role) or {}).get("model") or "")
            for role in ("frontier", "small", "coding")
        },
    }


def load_evas_settings(
    env_path: str | Path | None = None,
    env_values: Mapping[str, str] | None = None,
) -> EvasApiSettings:
    merged_env: dict[str, str] = {}
    if env_path is not None and Path(env_path).exists():
        merged_env.update({k: str(v) for k, v in dotenv_values(env_path).items() if v is not None})
    elif env_path is None and Path(".env").exists():
        merged_env.update({k: str(v) for k, v in dotenv_values(".env").items() if v is not None})
    if env_values:
        merged_env.update({k: str(v) for k, v in env_values.items()})
    merged_env.update({k: v for k, v in os.environ.items() if isinstance(v, str)})

    base_url = str(merged_env.get("EVAS_API_BASE_URL") or EVAS_DEFAULT_BASE_URL).strip()
    api_key = str(merged_env.get("EVAS_API_KEY") or "").strip()
    role_models = {
        role: str(merged_env.get(env_name) or EVAS_RECOMMENDED_MODELS[role]).strip()
        for role, env_name in EVAS_MODEL_ENV_MAP.items()
    }
    return EvasApiSettings(
        base_url=base_url,
        api_key=api_key,
        masked_api_key=mask_secret(api_key) if api_key else "",
        role_models=role_models,
    )


def choose_model_for_role(role: str, available_model_ids: list[str], settings: EvasApiSettings) -> str:
    preferred = settings.role_models.get(role) or EVAS_RECOMMENDED_MODELS[role]
    if preferred in available_model_ids:
        return preferred

    family_prefix = preferred.split("/", 1)[0]
    for model_id in available_model_ids:
        if model_id.startswith(family_prefix + "/"):
            return model_id

    return available_model_ids[0] if available_model_ids else preferred


def build_recommendation_report(
    available_model_ids: list[str],
    settings: EvasApiSettings,
    phase1_config_path: str | Path = "phase1.yaml",
) -> dict[str, object]:
    phase1_locked = load_phase1_locked_models(phase1_config_path)
    evas_roles: dict[str, dict[str, object]] = {}
    for role in ("frontier", "small", "coding"):
        requested_model = settings.role_models[role]
        chosen_model = choose_model_for_role(role, available_model_ids, settings)
        evas_roles[role] = {
            "requested": requested_model,
            "chosen": chosen_model,
            "available": chosen_model in available_model_ids,
            "note": EVAS_MODEL_NOTES.get(chosen_model, "暂无额外说明。"),
        }
    return {
        "base_url": settings.base_url,
        "phase1_locked": phase1_locked,
        "phase1_lock_note": PHASE1_LOCK_NOTE,
        "phase1_logprob_ready": False,
        "phase1_warning": PHASE1_LOGPROB_WARNING,
        "evas_candidate_roles": evas_roles,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect and manage EVAS OpenAI-compatible models.")
    parser.add_argument("--env-file", help="Optional .env file that contains EVAS_API_KEY.")
    parser.add_argument("--base-url", help="Override EVAS base URL.")
    parser.add_argument("--api-key", help="Override EVAS API key.")
    parser.add_argument(
        "--phase1-config",
        default="phase1.yaml",
        help="Phase 1 config path used to show the current locked Qwen model mapping.",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List all returned model ids.",
    )
    parser.add_argument(
        "--show-recommendations",
        action="store_true",
        help="Print the current recommended frontier/small/coding models.",
    )
    parser.add_argument(
        "--chat-smoke",
        action="store_true",
        help="Run a tiny chat smoke test after listing models.",
    )
    parser.add_argument(
        "--role",
        choices=("frontier", "small", "coding"),
        default="small",
        help="Model role used for chat smoke selection.",
    )
    parser.add_argument("--model", help="Explicit model id used for the smoke request.")
    parser.add_argument(
        "--prompt",
        default="Reply with exactly: pong",
        help="Prompt used for the chat smoke request.",
    )
    parser.add_argument("--max-completion-tokens", type=int, default=16)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    raw_overrides = {
        key: value
        for key, value in {
            "EVAS_API_BASE_URL": args.base_url,
            "EVAS_API_KEY": args.api_key,
        }.items()
        if value
    }
    settings = load_evas_settings(env_path=args.env_file, env_values=raw_overrides)
    if not settings.api_key:
        print("Missing EVAS_API_KEY. Set the env var or pass --api-key.")
        return 1

    client = OpenAICompatibleClient(settings.credentials())
    models = client.list_models()
    model_ids = [str(item.get("id")) for item in models if item.get("id")]

    if args.list_models or not args.chat_smoke:
        print(f"[OK] GET {settings.base_url.rstrip('/')}/models")
        print(f"Returned {len(model_ids)} models")
        for model_id in model_ids:
            print(f"  - {model_id}")
        print(f"Using API key: {settings.masked_api_key}")

    if args.show_recommendations or not args.chat_smoke:
        report = build_recommendation_report(model_ids, settings, phase1_config_path=args.phase1_config)
        phase1_locked = report["phase1_locked"]
        print("")
        print("Current Phase 1 locked model mapping:")
        print(
            f"  provider: {phase1_locked['provider_name']} "
            f"({phase1_locked['api_style']})"
        )
        for role, model_id in phase1_locked["roles"].items():
            print(f"  - {role}: {model_id}")
        print("")
        print(report["phase1_lock_note"])
        print("")
        print("EVAS candidate model mapping:")
        for role, payload in report["evas_candidate_roles"].items():
            print(f"  - {role}: {payload['chosen']}")
            print(f"    requested: {payload['requested']}")
            print(f"    note: {payload['note']}")
        print("")
        print(report["phase1_warning"])

    if not args.chat_smoke:
        return 0

    model_id = args.model or choose_model_for_role(args.role, model_ids, settings)
    response = client.chat_completion(
        model=model_id,
        messages=[{"role": "user", "content": args.prompt}],
        max_completion_tokens=args.max_completion_tokens,
        temperature=0.0,
        seed=20260422,
    )
    choices = response.get("choices") or []
    if not choices:
        print(f"Unexpected chat response: {response!r}")
        return 1
    message = choices[0].get("message") or {}
    print("")
    print(f"[OK] POST {settings.base_url.rstrip('/')}/chat/completions")
    print(f"Model: {model_id}")
    print(f"Assistant reply: {str(message.get('content') or '').strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
