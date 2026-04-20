from __future__ import annotations

import pytest

from cps.data.manifest import load_manifest
from cps.runtime.retrieval import SimpleOverlapRetrievalBackend, build_retrieval_dry_run


def test_retrieval_guard_blocks_leaky_configuration_for_scientific_use():
    bundle = load_manifest("artifacts/phase0/sample_manifest_v1.json")
    question = bundle.sample[0]
    backend = SimpleOverlapRetrievalBackend()

    with pytest.raises(ValueError, match="blocked by retrieval leakage guard"):
        backend.rank(
            question_text=question.question_text,
            paragraphs=question.paragraphs,
            configuration_id="bi_encoder_plus_cross_encoder",
            top_k=3,
        )


def test_retrieval_dry_run_marks_placeholder_configuration_as_blocked():
    bundle = load_manifest("artifacts/phase0/sample_manifest_v1.json")
    question = bundle.sample[0]

    results = build_retrieval_dry_run(question, top_k_values=[3])
    blocked = next(
        result for result in results if result["configuration_id"] == "bi_encoder_plus_cross_encoder"
    )
    allowed = next(result for result in results if result["configuration_id"] == "bm25_baseline")

    assert blocked["retrieval_mode"] == "readiness_scaffold"
    assert blocked["leakage_guard"] == "blocked"
    assert blocked["scientific_consumption_allowed"] is False
    assert "readiness scaffold only" in blocked["notes"]
    assert allowed["leakage_guard"] == "clear"
    assert allowed["scientific_consumption_allowed"] is True
