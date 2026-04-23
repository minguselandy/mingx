from __future__ import annotations

from api.model_probe import (
    _extract_token_logprobs,
    format_probe_markdown,
    probe_model,
    probe_visible_models,
)
from api.settings import ResolvedApiProfile


class _FakeClient:
    def __init__(self, responses_by_model, visible_models):
        self.responses_by_model = responses_by_model
        self.visible_models = visible_models

    def list_models(self):
        return [{"id": model_id} for model_id in self.visible_models]

    def chat_completion(self, *, model, **kwargs):
        response = self.responses_by_model[model]
        if isinstance(response, Exception):
            raise response
        return response


def _resolved_profile() -> ResolvedApiProfile:
    return ResolvedApiProfile(
        profile_name="dashscope-qwen-phase1",
        provider_name="dashscope",
        api_style="openai_chat_compatible",
        base_url_env="DASHSCOPE_BASE_URL",
        api_key_env="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key="sk-test",
        role_models={"frontier": "qwen3-32b", "small": "qwen3-14b", "coding": "qwen3-coder-plus"},
        phase1_logprob_ready=True,
        note="test",
    )


def _response_payload(logprobs):
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "blue",
                    "reasoning_content": "",
                    "logprobs": {"content": [{"token": "blue", "logprob": value} for value in logprobs]},
                }
            }
        ]
    }


def test_extract_token_logprobs_rejects_all_zero_values():
    try:
        _extract_token_logprobs(_response_payload([0.0, 0.0]))
    except ValueError as exc:
        assert "all-zero token logprobs" in str(exc)
    else:
        raise AssertionError("expected all-zero token logprobs to be rejected")


def test_probe_model_marks_nonzero_logprobs_as_green():
    client = _FakeClient({"qwen3-32b": _response_payload([-0.1, -0.2])}, ["qwen3-32b"])

    payload = probe_model(
        client,
        resolved_profile=_resolved_profile(),
        model_id="qwen3-32b",
        timeout=5,
    )

    assert payload["status"] == "green"
    assert payload["nonzero_token_count"] == 2


def test_probe_visible_models_summarizes_usable_and_unusable(monkeypatch):
    client = _FakeClient(
        {
            "good-model": _response_payload([-0.1, -0.2]),
            "bad-model": _response_payload([0.0, 0.0]),
        },
        ["good-model", "bad-model"],
    )

    monkeypatch.setattr(
        "api.model_probe.build_probe_client",
        lambda env_path=None, profile_name=None: (_resolved_profile(), client),
    )

    payload = probe_visible_models(env_path=".env", timeout=5)

    assert payload["usable_models"] == ["good-model"]
    assert payload["usable_model_count"] == 1
    assert payload["visible_model_count"] == 2
    assert payload["unusable_models"][0]["model_id"] == "bad-model"


def test_format_probe_markdown_lists_usable_models():
    markdown = format_probe_markdown(
        {
            "profile": "dashscope-qwen-phase1",
            "provider": "dashscope",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "visible_model_count": 2,
            "usable_model_count": 1,
            "usable_models": ["qwen3-32b"],
        },
        command="python scripts/list_phase1_usable_models.py --env .env",
        json_report_path="artifacts/phase1/model_probe/usable_models.json",
    )

    assert "# Phase 1 Usable Models" in markdown
    assert "`qwen3-32b`" in markdown
    assert "usable_models.json" in markdown
