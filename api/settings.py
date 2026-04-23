from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


DEFAULT_API_PROFILE = "dashscope-qwen-phase1"
GENERIC_ROLE_ENV_MAP = {
    "frontier": "API_FRONTIER_MODEL",
    "small": "API_SMALL_MODEL",
    "coding": "API_CODING_MODEL",
}
LEGACY_ROLE_ENV_MAP = {
    "frontier": "PHASE1_FRONTIER_MODEL",
    "small": "PHASE1_SMALL_MODEL",
    "coding": "CODING_MODEL",
}


@dataclass(frozen=True)
class ApiProviderProfile:
    profile_name: str
    provider_name: str
    api_style: str
    base_url_env: str
    api_key_env: str
    default_base_url: str
    role_models: dict[str, str]
    phase1_logprob_ready: bool
    note: str


@dataclass(frozen=True)
class ResolvedApiProfile:
    profile_name: str
    provider_name: str
    api_style: str
    base_url_env: str
    api_key_env: str
    base_url: str
    api_key: str
    role_models: dict[str, str]
    phase1_logprob_ready: bool
    note: str


API_PROVIDER_PROFILES = {
    "dashscope-qwen-phase1": ApiProviderProfile(
        profile_name="dashscope-qwen-phase1",
        provider_name="dashscope",
        api_style="openai_chat_compatible",
        base_url_env="DASHSCOPE_BASE_URL",
        api_key_env="DASHSCOPE_API_KEY",
        default_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        role_models={
            "frontier": "qwen3-32b",
            "small": "qwen3-14b",
            "coding": "qwen3-coder-plus",
        },
        phase1_logprob_ready=True,
        note="当前仓库既有的 Phase 1 正式锁定配置，仍然是默认方案。",
    ),
}


def list_api_profiles() -> list[ApiProviderProfile]:
    return [API_PROVIDER_PROFILES[name] for name in sorted(API_PROVIDER_PROFILES)]


def get_api_profile(profile_name: str | None) -> ApiProviderProfile:
    normalized = (profile_name or DEFAULT_API_PROFILE).strip()
    try:
        return API_PROVIDER_PROFILES[normalized]
    except KeyError as exc:
        available = ", ".join(sorted(API_PROVIDER_PROFILES))
        raise ValueError(f"Unknown API profile: {normalized}. Available profiles: {available}") from exc


def resolve_api_profile(
    env_values: Mapping[str, str] | None = None,
    profile_name: str | None = None,
) -> ResolvedApiProfile:
    values = dict(env_values or {})
    selected_profile_name = str(
        values.get("API_PROFILE")
        or values.get("PHASE1_PROVIDER_PROFILE")
        or profile_name
        or DEFAULT_API_PROFILE
    ).strip()
    profile = get_api_profile(selected_profile_name)
    base_url = str(
        values.get("API_BASE_URL")
        or values.get(profile.base_url_env)
        or profile.default_base_url
    ).strip()
    api_key = str(
        values.get("API_KEY")
        or values.get(profile.api_key_env)
        or ""
    ).strip()
    role_models = {
        role: str(
            values.get(GENERIC_ROLE_ENV_MAP[role])
            or values.get(LEGACY_ROLE_ENV_MAP[role])
            or profile.role_models[role]
        ).strip()
        for role in ("frontier", "small", "coding")
    }
    return ResolvedApiProfile(
        profile_name=profile.profile_name,
        provider_name=profile.provider_name,
        api_style=profile.api_style,
        base_url_env=profile.base_url_env,
        api_key_env=profile.api_key_env,
        base_url=base_url,
        api_key=api_key,
        role_models=role_models,
        phase1_logprob_ready=profile.phase1_logprob_ready,
        note=profile.note,
    )


def build_phase1_env_overrides(
    profile_name: str | None,
    env_values: Mapping[str, str] | None = None,
) -> dict[str, str]:
    resolved = resolve_api_profile(env_values=env_values, profile_name=profile_name)
    return {
        "API_PROFILE": resolved.profile_name,
        "API_BASE_URL": resolved.base_url,
        "API_FRONTIER_MODEL": resolved.role_models["frontier"],
        "API_SMALL_MODEL": resolved.role_models["small"],
        "API_CODING_MODEL": resolved.role_models["coding"],
    }


def format_phase1_env_overrides(
    profile_name: str | None,
    env_values: Mapping[str, str] | None = None,
) -> str:
    resolved = resolve_api_profile(env_values=env_values, profile_name=profile_name)
    overrides = build_phase1_env_overrides(resolved.profile_name, env_values=env_values)
    lines = [
        f"# Phase 1 API profile overrides: {resolved.profile_name}",
        f"# {resolved.note}",
        f"# Required secret env: {resolved.api_key_env}",
    ]
    lines.extend(f"{key}={value}" for key, value in overrides.items())
    return "\n".join(lines) + "\n"
