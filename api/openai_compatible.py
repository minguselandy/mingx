from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib import error, request


class OpenAICompatibleError(RuntimeError):
    """Raised when an OpenAI-compatible API request fails."""


@dataclass(frozen=True)
class OpenAICompatibleCredentials:
    base_url: str
    api_key: str

    @property
    def normalized_base_url(self) -> str:
        return self.base_url.strip().rstrip("/")


class OpenAICompatibleClient:
    def __init__(self, credentials: OpenAICompatibleCredentials) -> None:
        self.credentials = credentials

    def list_models(self) -> list[dict[str, Any]]:
        payload = self._request_json("GET", "/models")
        if not isinstance(payload, dict) or "data" not in payload:
            raise OpenAICompatibleError(f"Unexpected /models payload: {payload!r}")
        models = payload["data"]
        if not isinstance(models, list):
            raise OpenAICompatibleError(f"Unexpected model list payload: {models!r}")
        return [item for item in models if isinstance(item, dict)]

    def chat_completion(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        max_completion_tokens: int = 16,
        temperature: float = 0.0,
        seed: int | None = None,
        stream: bool = False,
        n: int = 1,
        logprobs: bool | None = None,
        top_logprobs: int | None = None,
        extra_body: Mapping[str, Any] | None = None,
        timeout: int = 60,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": list(messages),
            "temperature": temperature,
            "max_completion_tokens": max_completion_tokens,
            "stream": stream,
            "n": n,
        }
        if seed is not None:
            payload["seed"] = seed
        if logprobs is not None:
            payload["logprobs"] = logprobs
        if top_logprobs is not None:
            payload["top_logprobs"] = top_logprobs
        if extra_body:
            for key, value in extra_body.items():
                if key in payload:
                    raise ValueError(f"extra_body key collides with payload field: {key}")
                payload[key] = value
        response = self._request_json("POST", "/chat/completions", payload=payload, timeout=timeout)
        if not isinstance(response, dict):
            raise OpenAICompatibleError(f"Unexpected chat/completions payload: {response!r}")
        return response

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
        timeout: int = 30,
    ) -> Any:
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        http_request = request.Request(
            f"{self.credentials.normalized_base_url}{path}",
            data=body,
            headers={
                "Authorization": f"Bearer {self.credentials.api_key}",
                "Content-Type": "application/json",
            },
            method=method,
        )
        try:
            with request.urlopen(http_request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise OpenAICompatibleError(
                f"{method} {path} failed with HTTP {exc.code}: {error_body}"
            ) from exc
        except error.URLError as exc:
            raise OpenAICompatibleError(f"{method} {path} failed with transport error: {exc.reason}") from exc
