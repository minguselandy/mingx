import hashlib
import io
import json
from pathlib import Path
from urllib import error

import api.backends as api_backends
import cps.providers.openai_compatible as openai_backend_module
from cps.providers.openai_compatible import OpenAICompatibleChatBackend
from cps.runtime.config import load_phase1_context


def _build_context(workspace_tmp_dir):
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
    run_plan_path = workspace_tmp_dir / "run_plan.json"
    run_plan_path.write_text(
        json.dumps(
            {
                "experiment_id": "musique_gate1_phase1_v1",
                "protocol_version": "phase1.v1",
                "manifest_path": "./artifacts/phase0/sample_manifest_v1.json",
                "hash_path": "./artifacts/phase0/content_hashes.json",
                "phase1_config_path": "./phase1.yaml",
                "smoke_question_id": "2hop__256778_131879",
                "smoke_paragraph_limit": 5,
                "scoring": {
                    "model_role": "small",
                    "k_lcb": 5,
                    "lcb_quantile": 0.1,
                },
                "storage": {
                    "measurement_dir": str((workspace_tmp_dir / "measurements").as_posix()),
                    "export_dir": str((workspace_tmp_dir / "exports").as_posix()),
                    "checkpoint_dir": str((workspace_tmp_dir / "checkpoints").as_posix()),
                    "cache_dir": str((workspace_tmp_dir / "cache").as_posix()),
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return load_phase1_context(
        phase1_config_path=Path("phase1.yaml"),
        run_plan_path=run_plan_path,
        env_path=env_path,
    )


class _FakeHTTPResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def _response_payload(content="River Great Ouse"):
    return {
        "id": "resp-test",
        "model": "qwen3-14b",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                    "reasoning_content": "",
                    "logprobs": {
                        "content": [
                            {"token": "River", "logprob": -0.1},
                            {"token": " Great", "logprob": -0.2},
                            {"token": " Ouse", "logprob": -0.3},
                        ]
                    },
                },
                "logprobs": None,
            }
        ],
    }


def _response_payload_with_zero_logprobs(content="River Great Ouse"):
    return {
        "id": "resp-zero",
        "model": "qwen3-14b",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                    "reasoning_content": "",
                    "logprobs": {
                        "content": [
                            {"token": "River", "logprob": 0.0},
                            {"token": " Great", "logprob": 0.0},
                            {"token": " Ouse", "logprob": 0.0},
                        ]
                    },
                },
                "logprobs": None,
            }
        ],
    }


def test_dashscope_backend_uses_parsed_cache_before_network(workspace_tmp_dir, monkeypatch):
    context = _build_context(workspace_tmp_dir)
    backend = OpenAICompatibleChatBackend(context=context, model_role="small")
    payload = backend.build_request_payload("Who won?", "Alice", [])
    request_fingerprint = hashlib.sha256(json.dumps(payload).encode("utf-8")).hexdigest()
    parsed_cache_path = backend._parsed_cache_path(request_fingerprint)
    parsed_cache_path.parent.mkdir(parents=True, exist_ok=True)
    parsed_cache_path.write_text(
        json.dumps(
            {
                "logprob_sum": -0.75,
                "raw_content": "Alice",
                "request_fingerprint": request_fingerprint,
                "token_logprobs": [-0.25, -0.25, -0.25],
                "metadata": {"content_match": True, "response_id": "cached-response"},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    def _should_not_run(*args, **kwargs):
        raise AssertionError("network should not be used when parsed cache exists")

    monkeypatch.setattr(openai_backend_module.request, "urlopen", _should_not_run)

    score = backend.score_answer("Who won?", "Alice", [])

    assert score.response_status == "cache_hit_parsed"
    assert score.logprob_sum == -0.75
    assert score.metadata["cache_source"] == "parsed_result_cache"


def test_dashscope_backend_retries_retryable_http_errors_and_writes_cache(workspace_tmp_dir, monkeypatch):
    context = _build_context(workspace_tmp_dir)
    backend = OpenAICompatibleChatBackend(context=context, model_role="small")
    calls = {"count": 0}

    def _fake_urlopen(http_request, timeout=60):
        calls["count"] += 1
        if calls["count"] < 3:
            raise error.HTTPError(
                http_request.full_url,
                429,
                "Too Many Requests",
                None,
                io.BytesIO(b'{"error":{"message":"rate limited"}}'),
            )
        return _FakeHTTPResponse(_response_payload(), status=200)

    monkeypatch.setattr(openai_backend_module.request, "urlopen", _fake_urlopen)
    monkeypatch.setattr(openai_backend_module.time, "sleep", lambda seconds: None)

    score = backend.score_answer("Which river?", "River Great Ouse", [])

    assert calls["count"] == 3
    assert score.response_status == "200"
    assert score.metadata["attempt_count"] == 3
    assert backend._request_cache_path(score.request_fingerprint).exists()
    assert backend._parsed_cache_path(score.request_fingerprint).exists()


def test_dashscope_backend_rejects_degenerate_all_zero_logprobs(workspace_tmp_dir, monkeypatch):
    context = _build_context(workspace_tmp_dir)
    backend = OpenAICompatibleChatBackend(context=context, model_role="small")

    monkeypatch.setattr(
        openai_backend_module.request,
        "urlopen",
        lambda http_request, timeout=60: _FakeHTTPResponse(_response_payload_with_zero_logprobs(), status=200),
    )

    try:
        backend.score_answer("Which river?", "River Great Ouse", [])
    except ValueError as exc:
        assert "degenerate all-zero token logprobs" in str(exc)
    else:
        raise AssertionError("expected degenerate all-zero logprobs to be rejected")


def test_api_backend_factory_hides_provider_specific_backend_choice(workspace_tmp_dir):
    context = _build_context(workspace_tmp_dir)

    backend = api_backends.build_scoring_backend(
        context=context,
        backend_name="live",
        model_role="small",
    )

    assert isinstance(backend, OpenAICompatibleChatBackend)
    assert backend.backend_id == "dashscope_openai_chat"
