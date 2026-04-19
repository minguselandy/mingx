from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence

from cps.data.manifest import ManifestParagraph, ManifestQuestion


TOKEN_RE = re.compile(r"[a-z0-9]+")
RETRIEVAL_CONFIGS = (
    "bi_encoder_plus_cross_encoder",
    "bm25_baseline",
    "bi_encoder_only",
    "hybrid_rrf",
)


@dataclass(frozen=True)
class RetrievalHit:
    paragraph_id: int
    title: str
    score: float
    rank: int


@dataclass(frozen=True)
class RetrievalResult:
    configuration_id: str
    top_k: int
    ranked_paragraphs: tuple[RetrievalHit, ...]


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


class SimpleOverlapRetrievalBackend:
    backend_id = "simple_overlap_retrieval"

    @staticmethod
    def _score(question_tokens: set[str], paragraph: ManifestParagraph, configuration_id: str) -> float:
        text_tokens = _tokenize(paragraph.text)
        title_tokens = _tokenize(paragraph.title)
        overlap = len(question_tokens & text_tokens)
        title_overlap = len(question_tokens & title_tokens)

        if configuration_id == "bm25_baseline":
            return overlap + (0.1 * title_overlap)
        if configuration_id == "bi_encoder_only":
            return overlap + (0.05 * len(text_tokens))
        if configuration_id == "bi_encoder_plus_cross_encoder":
            return overlap + (0.2 * title_overlap) + (0.1 if paragraph.is_supporting else 0.0)
        if configuration_id == "hybrid_rrf":
            return overlap + title_overlap + (0.05 * len(text_tokens))
        raise ValueError(f"Unsupported retrieval configuration: {configuration_id}")

    def rank(
        self,
        question_text: str,
        paragraphs: Sequence[ManifestParagraph],
        configuration_id: str,
        top_k: int,
    ) -> RetrievalResult:
        question_tokens = _tokenize(question_text)
        ranked = sorted(
            (
                (paragraph, self._score(question_tokens, paragraph, configuration_id))
                for paragraph in paragraphs
            ),
            key=lambda item: (-item[1], item[0].paragraph_id),
        )[:top_k]
        return RetrievalResult(
            configuration_id=configuration_id,
            top_k=top_k,
            ranked_paragraphs=tuple(
                RetrievalHit(
                    paragraph_id=paragraph.paragraph_id,
                    title=paragraph.title,
                    score=round(score, 6),
                    rank=index,
                )
                for index, (paragraph, score) in enumerate(ranked, start=1)
            ),
        )


def build_retrieval_dry_run(
    question: ManifestQuestion,
    top_k_values: Iterable[int],
) -> list[dict]:
    backend = SimpleOverlapRetrievalBackend()
    results: list[dict] = []
    for configuration_id in RETRIEVAL_CONFIGS:
        for top_k in top_k_values:
            result = backend.rank(
                question_text=question.question_text,
                paragraphs=question.paragraphs,
                configuration_id=configuration_id,
                top_k=int(top_k),
            )
            results.append(
                {
                    "configuration_id": result.configuration_id,
                    "top_k": result.top_k,
                    "ranked_paragraphs": [
                        {
                            "paragraph_id": hit.paragraph_id,
                            "title": hit.title,
                            "score": hit.score,
                            "rank": hit.rank,
                        }
                        for hit in result.ranked_paragraphs
                    ],
                }
            )
    return results
