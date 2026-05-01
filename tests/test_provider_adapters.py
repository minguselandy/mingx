from __future__ import annotations

import builtins
import importlib
import json
import socket
import sys
from pathlib import Path

from cps.schema import ProjectionBundleV1


class FakeObject:
    def __init__(self, **fields):
        self.__dict__.update(fields)


def _stable(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def test_provider_modules_import_without_graphiti_or_langextract(monkeypatch):
    real_import = builtins.__import__
    blocked_roots = {"graphiti", "langextract"}

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.split(".", 1)[0] in blocked_roots:
            raise AssertionError(f"optional provider package imported: {name}")
        return real_import(name, globals, locals, fromlist, level)

    for name in list(sys.modules):
        if name.startswith("cps.providers.graphiti_provider") or name.startswith(
            "cps.providers.langextract_provider"
        ):
            sys.modules.pop(name)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    graphiti = importlib.import_module("cps.providers.graphiti_provider")
    langextract = importlib.import_module("cps.providers.langextract_provider")

    assert hasattr(graphiti, "graphiti_fact_to_candidate")
    assert hasattr(langextract, "langextract_span_to_candidate")


def test_graphiti_dict_fact_converts_to_native_candidate():
    from cps.providers.graphiti_provider import graphiti_fact_to_candidate

    candidate = graphiti_fact_to_candidate(
        {
            "uuid": "fact-1",
            "name": "Alice employment",
            "summary": "Alice works at Zep.",
            "episode_id": "episode-1",
            "valid_at": "2026-01-01T00:00:00Z",
            "confidence": 0.82,
            "metadata": {"kind": "employment"},
        }
    )

    assert candidate["source_id"] == "fact-1"
    assert candidate["source_type"] == "graphiti_fact"
    assert candidate["provider"] == "graphiti"
    assert candidate["content"] == "Alice works at Zep."
    assert candidate["confidence"] == 0.82
    assert candidate["temporal_validity"]["valid_at"] == "2026-01-01T00:00:00Z"
    assert candidate["provenance"]["episode_id"] == "episode-1"
    assert candidate["metadata"]["kind"] == "employment"
    assert candidate["content_hash"]


def test_graphiti_object_fact_converts_to_native_candidate():
    from cps.providers.graphiti_provider import graphiti_fact_to_candidate

    fact = FakeObject(id="fact-2", content="Paris is in France.", confidence=0.9)

    candidate = graphiti_fact_to_candidate(fact)

    assert candidate["source_id"] == "fact-2"
    assert candidate["content"] == "Paris is in France."
    assert candidate["confidence"] == 0.9


def test_graphiti_episode_preserves_provenance_and_temporal_validity():
    from cps.providers.graphiti_provider import graphiti_episode_to_candidate

    candidate = graphiti_episode_to_candidate(
        {
            "id": "episode-1",
            "content": "Episode body.",
            "source": "conversation-7",
            "valid_from": "2026-01-01",
            "valid_to": "2026-02-01",
            "created_at": "2026-01-02",
        }
    )

    assert candidate["source_type"] == "graphiti_episode"
    assert candidate["source_id"] == "episode-1"
    assert candidate["provenance"]["source"] == "conversation-7"
    assert candidate["temporal_validity"] == {
        "valid_from": "2026-01-01",
        "valid_to": "2026-02-01",
        "created_at": "2026-01-02",
    }


def test_langextract_dict_span_converts_to_native_candidate():
    from cps.providers.langextract_provider import langextract_span_to_candidate

    candidate = langextract_span_to_candidate(
        {
            "text": "aspirin reduced fever",
            "label": "finding",
            "document_id": "doc-1",
            "start_char": 10,
            "end_char": 31,
            "confidence": 0.77,
            "attributes": {"section": "results"},
        }
    )

    assert candidate["source_type"] == "langextract_span"
    assert candidate["provider"] == "langextract"
    assert candidate["content"] == "aspirin reduced fever"
    assert candidate["source_id"] == "doc-1:10:31"
    assert candidate["source_offsets"] == {"start": 10, "end": 31}
    assert candidate["extraction_type"] == "finding"
    assert candidate["confidence"] == 0.77
    assert candidate["provenance"]["document_id"] == "doc-1"
    assert candidate["provenance"]["source_offsets"] == {"start": 10, "end": 31}
    assert candidate["metadata"]["section"] == "results"


def test_langextract_object_span_converts_to_native_candidate():
    from cps.providers.langextract_provider import langextract_span_to_candidate

    span = FakeObject(extracted_text="BRCA1 variant", type="entity", document_id="doc-2", start=5, end=18)

    candidate = langextract_span_to_candidate(span)

    assert candidate["source_id"] == "doc-2:5:18"
    assert candidate["content"] == "BRCA1 variant"
    assert candidate["source_offsets"] == {"start": 5, "end": 18}
    assert candidate["extraction_type"] == "entity"


def test_candidate_hash_id_and_token_cost_are_deterministic():
    from cps.providers.langextract_provider import langextract_span_to_candidate

    span = {
        "text": "alpha beta, gamma",
        "label": "claim",
        "document_id": "doc-3",
        "start_char": 1,
        "end_char": 18,
    }

    first = langextract_span_to_candidate(span)
    second = langextract_span_to_candidate(dict(span))

    assert first["content_hash"] == second["content_hash"]
    assert first["candidate_id"] == second["candidate_id"]
    assert first["token_cost"] == second["token_cost"]
    assert first["token_cost"] == 4


def test_candidate_payload_can_be_embedded_in_projection_bundle():
    from cps.providers.graphiti_provider import graphiti_fact_to_candidate

    candidate = graphiti_fact_to_candidate({"id": "fact-3", "content": "Fact body."})
    payload = {
        "run_id": "run-provider",
        "dispatch_id": "dispatch-provider",
        "agent_id": "provider-adapter",
        "round_id": "round-1",
        "candidate_pool": {
            "dispatch_id": "dispatch-provider",
            "agent_id": "provider-adapter",
            "round_id": "round-1",
            "items": [candidate],
            "candidate_count": 1,
        },
        "projection_plan": {
            "dispatch_id": "dispatch-provider",
            "agent_id": "provider-adapter",
            "round_id": "round-1",
            "selected_ids": [candidate["candidate_id"]],
        },
        "budget_witness": {
            "dispatch_id": "dispatch-provider",
            "agent_id": "provider-adapter",
            "round_id": "round-1",
            "within_budget": True,
        },
        "materialized_context": {
            "dispatch_id": "dispatch-provider",
            "agent_id": "provider-adapter",
            "round_id": "round-1",
            "content": candidate["content"],
        },
        "metric_bridge_witness": {
            "dispatch_id": "dispatch-provider",
            "agent_id": "provider-adapter",
            "round_id": "round-1",
            "diagnostic_claim_level": "operational_utility_only",
        },
    }

    bundle = ProjectionBundleV1.from_dict(payload)

    assert bundle.to_dict()["candidate_pool"]["items"][0]["candidate_id"] == candidate["candidate_id"]


def test_adapters_do_not_use_network_or_reference(monkeypatch):
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("provider adapters must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    from cps.providers.graphiti_provider import graphiti_record_to_candidate
    from cps.providers.langextract_provider import langextract_record_to_candidate

    graphiti_candidate = graphiti_record_to_candidate({"id": "g-1", "content": "Graphiti fact."})
    langextract_candidate = langextract_record_to_candidate(
        {"text": "Extracted span.", "document_id": "doc-4", "start_char": 0, "end_char": 15}
    )

    assert "reference" not in _stable(graphiti_candidate)
    assert "reference" not in _stable(langextract_candidate)
