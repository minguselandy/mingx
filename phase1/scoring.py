from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol, Sequence

from phase0.manifest import ManifestParagraph


@dataclass(frozen=True)
class ScoreResult:
    logprob_sum: float
    raw_content: str
    request_fingerprint: str
    response_status: str
    token_logprobs: tuple[float, ...]
    metadata: dict


class ScoringBackend(Protocol):
    backend_id: str
    provider_name: str
    model_id: str

    def score_answer(
        self,
        question_text: str,
        answer_text: str,
        ordered_paragraphs: Sequence[ManifestParagraph],
    ) -> ScoreResult: ...


class MockScoringBackend:
    backend_id = "mock_forced_decode"
    provider_name = "mock"

    def __init__(self, model_id: str = "qwen3-14b") -> None:
        self.model_id = model_id

    @staticmethod
    def _paragraph_contribution(paragraph: ManifestParagraph, position: int) -> float:
        digest = hashlib.sha256(
            f"{paragraph.paragraph_id}|{paragraph.title}|{paragraph.text}".encode("utf-8")
        ).hexdigest()
        base = 0.05 + (int(digest[:6], 16) % 250) / 1000.0
        support_bonus = 0.25 if paragraph.is_supporting else 0.0
        position_weight = max(0.75, 1.0 - position * 0.03)
        return (base + support_bonus) * position_weight

    def score_answer(
        self,
        question_text: str,
        answer_text: str,
        ordered_paragraphs: Sequence[ManifestParagraph],
    ) -> ScoreResult:
        base_logprob = -2.0 - (min(len(answer_text), 64) * 0.01)
        paragraph_gain = sum(
            self._paragraph_contribution(paragraph, position)
            for position, paragraph in enumerate(ordered_paragraphs)
        )
        logprob_sum = round(base_logprob + paragraph_gain, 6)
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "question_text": question_text,
                    "answer_text": answer_text,
                    "paragraph_ids": [paragraph.paragraph_id for paragraph in ordered_paragraphs],
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        token_count = max(1, len(answer_text.split()))
        token_logprobs = tuple(round(logprob_sum / token_count, 6) for _ in range(token_count))
        return ScoreResult(
            logprob_sum=logprob_sum,
            raw_content=answer_text,
            request_fingerprint=fingerprint,
            response_status="mock",
            token_logprobs=token_logprobs,
            metadata={"content_match": True, "scoring_mode": "deterministic_mock"},
        )
