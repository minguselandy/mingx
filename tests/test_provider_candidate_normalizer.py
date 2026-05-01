from __future__ import annotations

import socket
from pathlib import Path

import pytest

from cps.providers.normalizer import normalize_candidate_payload, normalize_candidate_pool
from cps.schema import ProjectionBundleV1


def _bundle_payload(candidate: dict) -> dict:
    return {
        "run_id": "run-normalizer",
        "dispatch_id": "dispatch-normalizer",
        "agent_id": "provider-normalizer",
        "round_id": "round-1",
        "candidate_pool": {
            "dispatch_id": "dispatch-normalizer",
            "agent_id": "provider-normalizer",
            "round_id": "round-1",
            "items": [candidate],
            "candidate_count": 1,
        },
        "projection_plan": {
            "dispatch_id": "dispatch-normalizer",
            "agent_id": "provider-normalizer",
            "round_id": "round-1",
            "selected_ids": [candidate["candidate_id"]],
        },
        "budget_witness": {
            "dispatch_id": "dispatch-normalizer",
            "agent_id": "provider-normalizer",
            "round_id": "round-1",
            "within_budget": True,
        },
        "materialized_context": {
            "dispatch_id": "dispatch-normalizer",
            "agent_id": "provider-normalizer",
            "round_id": "round-1",
            "content": candidate["content"],
        },
        "metric_bridge_witness": {
            "dispatch_id": "dispatch-normalizer",
            "agent_id": "provider-normalizer",
            "round_id": "round-1",
            "diagnostic_claim_level": "operational_utility_only",
        },
    }


def test_provider_native_candidate_gets_legacy_aliases():
    normalized = normalize_candidate_payload(
        {"candidate_id": "c1", "content": "candidate text", "token_cost": 4}
    )

    assert normalized["item_id"] == "c1"
    assert normalized["text"] == "candidate text"
    assert normalized["token_estimate"] == 4


def test_legacy_candidate_gets_provider_aliases():
    normalized = normalize_candidate_payload(
        {"item_id": "item-1", "text": "legacy text", "token_estimate": 3}
    )

    assert normalized["candidate_id"] == "item-1"
    assert normalized["content"] == "legacy text"
    assert normalized["token_cost"] == 3


def test_input_payload_and_nested_fields_are_not_mutated():
    original = {
        "candidate_id": "c1",
        "content": "candidate text",
        "token_cost": 4,
        "metadata": {"nested": {"value": 1}},
    }

    normalized = normalize_candidate_payload(original)
    normalized["metadata"]["nested"]["value"] = 2

    assert "item_id" not in original
    assert "text" not in original
    assert "token_estimate" not in original
    assert original["metadata"]["nested"]["value"] == 1


def test_conflicting_id_aliases_fail_closed():
    with pytest.raises(ValueError):
        normalize_candidate_payload({"candidate_id": "c1", "item_id": "c2", "content": "text"})


def test_conflicting_content_aliases_fail_closed():
    with pytest.raises(ValueError):
        normalize_candidate_payload({"candidate_id": "c1", "content": "a", "text": "b"})


def test_conflicting_token_aliases_fail_closed():
    with pytest.raises(ValueError):
        normalize_candidate_payload(
            {"candidate_id": "c1", "content": "text", "token_cost": 1, "token_estimate": 2}
        )


def test_missing_id_fails_closed():
    with pytest.raises(ValueError):
        normalize_candidate_payload({"content": "text", "token_cost": 1})


def test_missing_content_fails_closed():
    with pytest.raises(ValueError):
        normalize_candidate_payload({"candidate_id": "c1", "token_cost": 1})


@pytest.mark.parametrize("value", ["1", 1.0, True, None])
def test_non_integer_token_cost_fails_closed(value):
    with pytest.raises(ValueError):
        normalize_candidate_payload({"candidate_id": "c1", "content": "text", "token_cost": value})


@pytest.mark.parametrize("value", ["1", 1.0, False, None])
def test_non_integer_token_estimate_fails_closed(value):
    with pytest.raises(ValueError):
        normalize_candidate_payload(
            {"candidate_id": "c1", "content": "text", "token_estimate": value}
        )


def test_normalize_candidate_pool_preserves_input_order():
    normalized = normalize_candidate_pool(
        [
            {"candidate_id": "c1", "content": "one", "token_cost": 1},
            {"candidate_id": "c2", "content": "two", "token_cost": 1},
            {"candidate_id": "c3", "content": "three", "token_cost": 1},
        ]
    )

    assert [candidate["item_id"] for candidate in normalized] == ["c1", "c2", "c3"]


def test_normalized_graphiti_candidate_embeds_in_projection_bundle():
    from cps.providers.graphiti_provider import graphiti_fact_to_candidate

    candidate = normalize_candidate_payload(
        graphiti_fact_to_candidate({"id": "fact-1", "content": "Graphiti fact."})
    )
    bundle = ProjectionBundleV1.from_dict(_bundle_payload(candidate))

    item = bundle.to_dict()["candidate_pool"]["items"][0]
    assert item["candidate_id"] == item["item_id"]
    assert item["content"] == item["text"]


def test_normalized_langextract_candidate_embeds_in_projection_bundle():
    from cps.providers.langextract_provider import langextract_span_to_candidate

    candidate = normalize_candidate_payload(
        langextract_span_to_candidate(
            {
                "text": "extracted claim",
                "document_id": "doc-1",
                "start_char": 0,
                "end_char": 15,
            }
        )
    )
    bundle = ProjectionBundleV1.from_dict(_bundle_payload(candidate))

    item = bundle.to_dict()["candidate_pool"]["items"][0]
    assert item["candidate_id"] == item["item_id"]
    assert item["content"] == item["text"]


def test_normalizer_does_not_use_network_or_reference(monkeypatch):
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("normalizer must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    normalized = normalize_candidate_payload(
        {"candidate_id": "c1", "content": "candidate text", "token_cost": 2}
    )

    assert normalized["item_id"] == "c1"
