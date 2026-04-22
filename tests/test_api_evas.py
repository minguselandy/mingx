from pathlib import Path

from api.evas import (
    EVAS_RECOMMENDED_MODELS,
    build_recommendation_report,
    choose_model_for_role,
    load_evas_settings,
    load_phase1_locked_models,
)


def test_load_evas_settings_prefers_process_env_over_env_file(workspace_tmp_dir, monkeypatch):
    env_path = workspace_tmp_dir / ".env"
    env_path.write_text(
        "\n".join(
            [
                "EVAS_API_KEY=sk-from-env-file",
                "EVAS_API_BASE_URL=https://api.evas.ai/v1",
                "EVAS_FRONTIER_MODEL=openai/gpt-5.4",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("EVAS_API_KEY", "sk-from-process-env")
    monkeypatch.setenv("EVAS_SMALL_MODEL", "openai/gpt-5.4-mini")

    settings = load_evas_settings(env_path=env_path)

    assert settings.base_url == "https://api.evas.ai/v1"
    assert settings.api_key == "sk-from-process-env"
    assert settings.role_models["frontier"] == "openai/gpt-5.4"
    assert settings.role_models["small"] == "openai/gpt-5.4-mini"
    assert settings.masked_api_key.startswith("sk-f")


def test_choose_model_for_role_prefers_recommended_available_model():
    settings = load_evas_settings(
        env_values={
            "EVAS_API_KEY": "sk-test-key",
        }
    )
    available_model_ids = [
        "openai/gpt-5.4",
        "openai/gpt-5.4-mini",
        "openai/gpt-5.3-codex",
    ]

    assert choose_model_for_role("frontier", available_model_ids, settings) == "openai/gpt-5.4"
    assert choose_model_for_role("small", available_model_ids, settings) == "openai/gpt-5.4-mini"
    assert choose_model_for_role("coding", available_model_ids, settings) == "openai/gpt-5.3-codex"


def test_build_recommendation_report_marks_phase1_as_not_logprob_ready():
    settings = load_evas_settings(
        env_values={
            "EVAS_API_KEY": "sk-test-key",
        }
    )
    report = build_recommendation_report(
        available_model_ids=list(EVAS_RECOMMENDED_MODELS.values()),
        settings=settings,
    )

    assert report["phase1_logprob_ready"] is False
    assert "token logprobs" in str(report["phase1_warning"])
    assert report["phase1_locked"]["roles"]["frontier"] == "qwen3-32b"
    assert report["evas_candidate_roles"]["frontier"]["chosen"] == "openai/gpt-5.4"


def test_load_phase1_locked_models_reads_existing_qwen_phase_setup():
    locked = load_phase1_locked_models(Path("phase1.yaml"))

    assert locked["provider_name"] == "dashscope"
    assert locked["roles"]["frontier"] == "qwen3-32b"
    assert locked["roles"]["small"] == "qwen3-14b"
    assert locked["roles"]["coding"] == "qwen3-coder-plus"
