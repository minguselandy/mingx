from __future__ import annotations

from cps.providers.openai_compatible import OpenAICompatibleChatBackend
from cps.runtime.config import Phase1Context
from cps.scoring.backends import MockScoringBackend


def build_live_backend(context: Phase1Context, model_role: str):
    if not context.provider.phase1_logprob_ready:
        profile_name = context.provider.profile_name or context.provider.name or "unknown"
        raise ValueError(
            "Selected API profile is not Phase 1 logprob-ready for the live scorer: "
            f"{profile_name}. {context.provider.note}"
        )
    api_style = str(context.provider.api_style or "").strip()
    if api_style == "openai_chat_compatible":
        return OpenAICompatibleChatBackend(context=context, model_role=model_role)
    raise ValueError(f"Unsupported live api style: {api_style or 'unknown'}")


def build_scoring_backend(context: Phase1Context, backend_name: str, model_role: str):
    if backend_name == "mock":
        return MockScoringBackend(model_id=context.models[model_role].model)
    if backend_name == "live":
        return build_live_backend(context=context, model_role=model_role)
    raise ValueError(f"Unsupported backend: {backend_name}")
