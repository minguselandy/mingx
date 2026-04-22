from __future__ import annotations

import hashlib
import json
import random
import time
from pathlib import Path
from typing import Sequence
from urllib import error, request

from cps.data.manifest import ManifestParagraph
from cps.runtime.config import Phase1Context
from cps.scoring.backends import ScoreResult


class OpenAICompatibleChatBackend:
    backend_id = "openai_compatible_chat"

    def __init__(self, context: Phase1Context, model_role: str) -> None:
        self.context = context
        self.model_role = model_role
        self.provider_name = context.provider.name
        self.backend_id = f"{self.provider_name}_openai_chat" if self.provider_name else self.backend_id
        self.model_id = context.models[model_role].model
        self.model_config = context.models[model_role]
        self.cache_config = dict(context.raw_config.get("cache") or {})
        self.retry_config = dict(((context.raw_config.get("rate_limit") or {}).get("retry")) or {})

    def _build_prompt(
        self,
        question_text: str,
        answer_text: str,
        ordered_paragraphs: Sequence[ManifestParagraph],
    ) -> str:
        paragraphs = "\n\n".join(
            [
                f"[{index}] {paragraph.title}\n{paragraph.text}"
                for index, paragraph in enumerate(ordered_paragraphs, start=1)
            ]
        )
        return (
            "Repeat the reference answer exactly and output nothing else.\n\n"
            f"Context:\n{paragraphs if paragraphs else '(no paragraphs)'}\n\n"
            f"Question: {question_text}\n"
            f"Reference answer: {answer_text}"
        )

    def build_request_payload(
        self,
        question_text: str,
        answer_text: str,
        ordered_paragraphs: Sequence[ManifestParagraph],
    ) -> dict:
        decoding = dict(self.model_config.decoding)
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a deterministic answer replay scorer. Output the reference answer exactly and do not reveal reasoning.",
                },
                {
                    "role": "user",
                    "content": self._build_prompt(question_text, answer_text, ordered_paragraphs),
                },
            ],
            "temperature": float(decoding["temperature"]),
            "max_completion_tokens": int(decoding["max_completion_tokens"]),
            "seed": int(decoding["seed"]),
            "stream": bool(decoding["stream"]),
            "n": int(decoding["n"]),
            "logprobs": bool(self.model_config.logprob["enabled"]),
            "top_logprobs": int(self.model_config.logprob["top_logprobs"]),
        }
        extra_body = dict(decoding.get("extra_body") or {})
        if extra_body:
            payload["extra_body"] = extra_body
        return payload

    @staticmethod
    def build_transport_payload(payload: dict) -> dict:
        transport_payload = dict(payload)
        extra_body = dict(transport_payload.pop("extra_body", {}) or {})
        for key, value in extra_body.items():
            if key in transport_payload:
                raise ValueError(f"extra_body key collides with transport payload field: {key}")
            transport_payload[key] = value
        return transport_payload

    def _request_cache_path(self, request_fingerprint: str) -> Path:
        return self.context.storage.cache_dir / "requests" / self.model_role / f"{request_fingerprint}.json"

    def _parsed_cache_path(self, request_fingerprint: str) -> Path:
        return self.context.storage.cache_dir / "parsed" / self.model_role / f"{request_fingerprint}.json"

    def _load_cached_score(self, request_fingerprint: str, answer_text: str) -> ScoreResult | None:
        parsed_cache_path = self._parsed_cache_path(request_fingerprint)
        if self.cache_config.get("parsed_result_cache") and parsed_cache_path.exists():
            payload = json.loads(parsed_cache_path.read_text(encoding="utf-8"))
            metadata = dict(payload.get("metadata") or {})
            metadata["cache_source"] = "parsed_result_cache"
            return ScoreResult(
                logprob_sum=float(payload["logprob_sum"]),
                raw_content=str(payload["raw_content"]),
                request_fingerprint=str(payload["request_fingerprint"]),
                response_status="cache_hit_parsed",
                token_logprobs=tuple(float(item) for item in payload.get("token_logprobs") or ()),
                metadata=metadata,
            )

        request_cache_path = self._request_cache_path(request_fingerprint)
        if self.cache_config.get("request_cache") and request_cache_path.exists():
            response_payload = json.loads(request_cache_path.read_text(encoding="utf-8"))
            logprob_sum, token_logprobs, content, content_match = self._extract_logprob_sum(response_payload)
            return ScoreResult(
                logprob_sum=float(logprob_sum),
                raw_content=content,
                request_fingerprint=request_fingerprint,
                response_status="cache_hit_raw",
                token_logprobs=token_logprobs,
                metadata={
                    "content_match": content.strip() == answer_text.strip() if content_match else False,
                    "response_id": response_payload.get("id"),
                    "scoring_mode": "chat_replay_scaffold",
                    "cache_source": "request_cache",
                },
            )
        return None

    def _write_caches(self, request_fingerprint: str, response_payload: dict, score: ScoreResult) -> None:
        if self.cache_config.get("request_cache"):
            request_cache_path = self._request_cache_path(request_fingerprint)
            request_cache_path.parent.mkdir(parents=True, exist_ok=True)
            request_cache_path.write_text(
                json.dumps(response_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        if self.cache_config.get("parsed_result_cache"):
            parsed_cache_path = self._parsed_cache_path(request_fingerprint)
            parsed_cache_path.parent.mkdir(parents=True, exist_ok=True)
            parsed_cache_path.write_text(
                json.dumps(
                    {
                        "logprob_sum": score.logprob_sum,
                        "raw_content": score.raw_content,
                        "request_fingerprint": score.request_fingerprint,
                        "token_logprobs": list(score.token_logprobs),
                        "metadata": score.metadata,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

    def _retry_delay_seconds(self, attempt_number: int) -> float:
        base_delay = float(self.retry_config.get("base_delay_sec", 1.0))
        max_delay = float(self.retry_config.get("max_delay_sec", 30.0))
        delay = min(max_delay, base_delay * (2 ** max(0, attempt_number - 1)))
        if self.retry_config.get("jitter"):
            delay *= 0.5 + random.random()
        return delay

    def _should_retry_http(self, status_code: int) -> bool:
        retry_statuses = {int(status) for status in self.retry_config.get("retry_statuses", ())}
        return status_code in retry_statuses

    @staticmethod
    def _extract_logprob_sum(response_payload: dict) -> tuple[float, tuple[float, ...], str, bool]:
        choice = response_payload["choices"][0]
        message = choice.get("message") or {}
        if message.get("reasoning_content"):
            raise ValueError("Phase 1 scorer must not route through reasoning_content")
        content = message.get("content", "")
        logprobs_block = message.get("logprobs") or choice.get("logprobs") or {}
        logprob_items = (logprobs_block.get("content")) or []
        if not logprob_items:
            raise ValueError("OpenAI-compatible response did not include token logprobs")
        token_logprobs = tuple(float(item["logprob"]) for item in logprob_items if "logprob" in item)
        return sum(token_logprobs), token_logprobs, content, True

    def score_answer(
        self,
        question_text: str,
        answer_text: str,
        ordered_paragraphs: Sequence[ManifestParagraph],
    ) -> ScoreResult:
        request_payload = self.build_request_payload(question_text, answer_text, ordered_paragraphs)
        payload = self.build_transport_payload(request_payload)
        request_fingerprint = hashlib.sha256(
            json.dumps(request_payload, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        body = json.dumps(payload).encode("utf-8")
        cached_score = self._load_cached_score(request_fingerprint, answer_text)
        if cached_score is not None:
            return cached_score

        endpoint = f"{self.context.provider.base_url.rstrip('/')}/chat/completions"
        http_request = request.Request(
            endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self.context.provider.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        max_attempts = int(self.retry_config.get("max_attempts", 1))
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                with request.urlopen(http_request, timeout=60) as response:
                    response_payload = json.loads(response.read().decode("utf-8"))
                    logprob_sum, token_logprobs, content, content_match = self._extract_logprob_sum(response_payload)
                    score = ScoreResult(
                        logprob_sum=float(logprob_sum),
                        raw_content=content,
                        request_fingerprint=request_fingerprint,
                        response_status=str(response.status),
                        token_logprobs=token_logprobs,
                        metadata={
                            "content_match": content.strip() == answer_text.strip() if content_match else False,
                            "response_id": response_payload.get("id"),
                            "scoring_mode": "chat_replay_scaffold",
                            "attempt_count": attempt,
                        },
                    )
                    self._write_caches(request_fingerprint, response_payload, score)
                    return score
            except error.HTTPError as exc:
                error_body = exc.read().decode("utf-8", errors="replace")
                last_error = RuntimeError(
                    f"{self.provider_name} request failed with HTTP {exc.code}: {error_body}"
                )
                if attempt >= max_attempts or not self._should_retry_http(exc.code):
                    raise last_error from exc
            except error.URLError as exc:
                last_error = RuntimeError(
                    f"{self.provider_name} request failed with transport error: {exc.reason}"
                )
                if attempt >= max_attempts:
                    raise last_error from exc

            time.sleep(self._retry_delay_seconds(attempt))

        if last_error is not None:
            raise last_error
        raise RuntimeError("OpenAI-compatible request failed without a captured exception")
