from __future__ import annotations

from importlib import import_module


_LAZY_EXPORTS = {
    "API_PROVIDER_PROFILES": ("api.settings", "API_PROVIDER_PROFILES"),
    "DEFAULT_API_PROFILE": ("api.settings", "DEFAULT_API_PROFILE"),
    "ApiProviderProfile": ("api.settings", "ApiProviderProfile"),
    "ResolvedApiProfile": ("api.settings", "ResolvedApiProfile"),
    "build_live_backend": ("api.backends", "build_live_backend"),
    "build_phase1_env_overrides": ("api.settings", "build_phase1_env_overrides"),
    "build_scoring_backend": ("api.backends", "build_scoring_backend"),
    "format_phase1_env_overrides": ("api.settings", "format_phase1_env_overrides"),
    "get_api_profile": ("api.settings", "get_api_profile"),
    "list_api_profiles": ("api.settings", "list_api_profiles"),
    "OpenAICompatibleClient": ("api.openai_compatible", "OpenAICompatibleClient"),
    "OpenAICompatibleCredentials": ("api.openai_compatible", "OpenAICompatibleCredentials"),
    "resolve_api_profile": ("api.settings", "resolve_api_profile"),
}

__all__ = sorted(_LAZY_EXPORTS)


def __getattr__(name: str):
    try:
        module_name, attribute_name = _LAZY_EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module 'api' has no attribute {name!r}") from exc
    module = import_module(module_name)
    return getattr(module, attribute_name)
