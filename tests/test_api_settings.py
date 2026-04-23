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
    assert profile.role_models["frontier"] == "qwen3.6-plus"
    assert profile.phase1_logprob_ready is True


def test_build_phase1_env_overrides_for_dashscope_profile_uses_locked_models():
    overrides = build_phase1_env_overrides(
        "dashscope-qwen-phase1",
        env_values={"DASHSCOPE_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
    )

    assert overrides["API_PROFILE"] == "dashscope-qwen-phase1"
    assert overrides["API_BASE_URL"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert overrides["API_FRONTIER_MODEL"] == "qwen3.6-plus"
    assert overrides["API_SMALL_MODEL"] == "qwen3.6-flash"


def test_format_phase1_env_overrides_contains_shell_ready_lines():
    text = format_phase1_env_overrides("dashscope-qwen-phase1")

    assert "API_PROFILE=dashscope-qwen-phase1" in text
    assert "API_SMALL_MODEL=qwen3.6-flash" in text
    assert "API_CODING_MODEL=qwen3-coder-plus" in text


def test_list_api_profiles_contains_only_dashscope_profile():
    names = [profile.profile_name for profile in list_api_profiles()]

    assert "dashscope-qwen-phase1" in names
    assert names == ["dashscope-qwen-phase1"]


def test_resolve_api_profile_uses_generic_api_overrides_first():
    resolved = resolve_api_profile(
        env_values={
            "API_PROFILE": "dashscope-qwen-phase1",
            "DASHSCOPE_API_KEY": "sk-dashscope",
            "API_SMALL_MODEL": "qwen3-32b",
        }
    )

    assert resolved.profile_name == "dashscope-qwen-phase1"
    assert resolved.provider_name == "dashscope"
    assert resolved.api_key == "sk-dashscope"
    assert resolved.role_models["small"] == "qwen3-32b"
