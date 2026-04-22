from api.settings import (
    DEFAULT_API_PROFILE,
    build_phase1_env_overrides,
    format_phase1_env_overrides,
    get_api_profile,
    list_api_profiles,
    resolve_api_profile,
)


def test_default_api_profile_is_dashscope_qwen_phase1():
    profile = get_api_profile(DEFAULT_API_PROFILE)

    assert profile.provider_name == "dashscope"
    assert profile.role_models["frontier"] == "qwen3-32b"
    assert profile.phase1_logprob_ready is True


def test_build_phase1_env_overrides_for_evas_profile_uses_openai_models():
    overrides = build_phase1_env_overrides(
        "evas-openai",
        env_values={"EVAS_API_BASE_URL": "https://api.evas.ai/v1"},
    )

    assert overrides["API_PROFILE"] == "evas-openai"
    assert overrides["API_BASE_URL"] == "https://api.evas.ai/v1"
    assert overrides["API_FRONTIER_MODEL"] == "openai/gpt-5.4"
    assert overrides["API_SMALL_MODEL"] == "openai/gpt-5.4-mini"


def test_format_phase1_env_overrides_contains_shell_ready_lines():
    text = format_phase1_env_overrides("dashscope-qwen-phase1")

    assert "API_PROFILE=dashscope-qwen-phase1" in text
    assert "API_SMALL_MODEL=qwen3-14b" in text
    assert "API_CODING_MODEL=qwen3-coder-plus" in text


def test_list_api_profiles_contains_dashscope_and_evas():
    names = [profile.profile_name for profile in list_api_profiles()]

    assert "dashscope-qwen-phase1" in names
    assert "evas-openai" in names


def test_resolve_api_profile_uses_generic_api_overrides_first():
    resolved = resolve_api_profile(
        env_values={
            "API_PROFILE": "evas-openai",
            "EVAS_API_KEY": "sk-evas",
            "API_SMALL_MODEL": "openai/gpt-5.4",
        }
    )

    assert resolved.profile_name == "evas-openai"
    assert resolved.provider_name == "evas"
    assert resolved.api_key == "sk-evas"
    assert resolved.role_models["small"] == "openai/gpt-5.4"
