from pathlib import Path

import pytest

from phase1.config import load_phase1_context
from phase1.dashscope_backend import DashScopeChatBackend


def test_dashscope_request_builder_uses_phase1_logprob_contract(workspace_tmp_dir):
    env_path = workspace_tmp_dir / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DASHSCOPE_API_KEY=sk-test-key",
                "DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1",
            ]
        ),
        encoding="utf-8",
    )
    context = load_phase1_context(
        phase1_config_path=Path("phase1.yaml"),
        run_plan_path=Path("configs/runs/smoke.json"),
        env_path=env_path,
    )
    backend = DashScopeChatBackend(context=context, model_role="small")

    payload = backend.build_request_payload(
        question_text="Who won?",
        answer_text="Alice",
        ordered_paragraphs=[],
    )

    assert payload["model"] == "qwen3-14b"
    assert payload["temperature"] == 0.0
    assert payload["seed"] == 20260418
    assert payload["logprobs"] is True
    assert payload["top_logprobs"] == 0
    assert payload["stream"] is False
    assert payload["n"] == 1
    assert payload["max_completion_tokens"] == 64
    assert payload["enable_thinking"] is False
    assert "extra_body" not in payload


def test_dashscope_logprob_extractor_supports_message_level_logprobs():
    logprob_sum, token_logprobs, content, content_match = DashScopeChatBackend._extract_logprob_sum(
        {
            "choices": [
                {
                    "message": {
                        "content": "River Great Ouse",
                        "reasoning_content": "",
                        "logprobs": {
                            "content": [
                                {"token": "River", "logprob": -0.1},
                                {"token": " Great", "logprob": -0.2},
                            ]
                        },
                    },
                    "logprobs": None,
                }
            ]
        }
    )

    assert logprob_sum == pytest.approx(-0.3)
    assert token_logprobs == (-0.1, -0.2)
    assert content == "River Great Ouse"
    assert content_match is True
