import builtins
import importlib
import json
import socket
import sys
from pathlib import Path

import pytest

from cps.schema import ProjectionBundleV1


def _bundle(include_diagnostics: bool = True) -> ProjectionBundleV1:
    payload = {
        "run_id": "run-1",
        "dispatch_id": "dispatch-1",
        "agent_id": "synthetic-agent",
        "round_id": "round-1",
        "candidate_pool": {
            "dispatch_id": "dispatch-1",
            "agent_id": "synthetic-agent",
            "round_id": "round-1",
            "budget_tokens": 20,
            "candidate_count": 2,
            "items": [
                {"item_id": "a", "token_cost": 5, "text": "A", "singleton_value": 1.0},
                {"item_id": "b", "token_cost": 4, "text": "B", "singleton_value": 0.5},
            ],
            "candidate_pool_hash": "pool-hash",
        },
        "projection_plan": {
            "dispatch_id": "dispatch-1",
            "agent_id": "synthetic-agent",
            "round_id": "round-1",
            "algorithm": "monitored_greedy",
            "budget_tokens": 20,
            "candidate_pool_hash": "pool-hash",
            "selected_ids": ["a"],
            "excluded_ids": ["b"],
            "score_config": {"selector_backend": "native_greedy"},
        },
        "budget_witness": {
            "dispatch_id": "dispatch-1",
            "agent_id": "synthetic-agent",
            "round_id": "round-1",
            "budget_tokens": 20,
            "estimated_tokens": 10,
            "realized_tokens": 9,
            "within_budget": True,
            "selected_ids": ["a"],
            "excluded_ids": ["b"],
        },
        "materialized_context": {
            "dispatch_id": "dispatch-1",
            "agent_id": "synthetic-agent",
            "round_id": "round-1",
            "selected_ids": ["a"],
            "section_order": ["a"],
            "content": "SECRET_FULL_CONTEXT " + ("x" * 200),
            "token_count": 9,
            "context_hash": "context-hash",
        },
        "metric_bridge_witness": {
            "dispatch_id": "dispatch-1",
            "agent_id": "synthetic-agent",
            "round_id": "round-1",
            "metric_class": "synthetic_oracle",
            "diagnostic_claim_level": "vinfo_proxy_supported",
            "drift_status": "fresh",
            "active_stratum": {"regime": "redundancy_dominated"},
        },
        "source_mode": "synthetic",
    }
    if include_diagnostics:
        payload["diagnostics"] = {
            "metric_claim_level": "vinfo_proxy_supported",
            "selector_regime_label": "greedy_supported",
            "selector_action": "monitored_greedy",
            "contamination_gate_decision": "not_evaluated",
            "annotation_mode": "none",
            "bridge_status": "fresh",
        }
    return ProjectionBundleV1.from_dict(payload)


def _stable(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def test_exporter_modules_import_without_observability_dependencies(monkeypatch):
    real_import = builtins.__import__
    blocked_roots = {"langfuse", "phoenix", "opentelemetry"}

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.split(".", 1)[0] in blocked_roots:
            raise AssertionError(f"external observability package imported: {name}")
        return real_import(name, globals, locals, fromlist, level)

    for name in list(sys.modules):
        if name == "cps.export" or name.startswith("cps.export."):
            sys.modules.pop(name)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    package = importlib.import_module("cps.export")
    otel = importlib.import_module("cps.export.otel")
    langfuse = importlib.import_module("cps.export.langfuse")
    phoenix = importlib.import_module("cps.export.phoenix")

    assert hasattr(package, "projection_bundle_to_otel_span")
    assert hasattr(otel, "projection_bundle_to_otel_span")
    assert hasattr(langfuse, "projection_bundle_to_langfuse_payload")
    assert hasattr(phoenix, "projection_bundle_to_phoenix_payload")


def test_otel_export_is_deterministic_and_contains_core_fields():
    from cps.export.otel import projection_bundle_to_otel_span

    bundle = _bundle()
    before = bundle.to_dict()

    first = projection_bundle_to_otel_span(bundle)
    second = projection_bundle_to_otel_span(bundle)

    assert _stable(first) == _stable(second)
    assert bundle.to_dict() == before
    assert first["name"] == "cps.projection_bundle"
    assert first["kind"] == "INTERNAL"
    assert first["trace_id"] == "run-1"
    assert first["span_id"] == "dispatch-1"
    attributes = first["attributes"]
    assert attributes["cps.bundle_version"] == "ProjectionBundleV1"
    assert attributes["cps.canonical_hash"] == bundle.canonical_hash()
    assert attributes["cps.candidate_count"] == 2
    assert attributes["cps.selected_count"] == 1
    assert attributes["cps.budget_tokens"] == 20
    assert attributes["cps.realized_tokens"] == 9
    assert attributes["cps.within_budget"] is True
    assert attributes["cps.metric_claim_level"] == "vinfo_proxy_supported"
    assert attributes["cps.selector_regime_label"] == "greedy_supported"
    assert attributes["cps.selector_action"] == "monitored_greedy"


def test_langfuse_dry_run_export_is_deterministic_and_local_only():
    from cps.export.langfuse import (
        export_projection_bundle_to_langfuse,
        projection_bundle_to_langfuse_payload,
    )

    bundle = _bundle()
    first = projection_bundle_to_langfuse_payload(bundle)
    second = export_projection_bundle_to_langfuse(bundle)

    assert _stable(first) == _stable(second)
    assert first["dry_run"] is True
    assert first["trace"]["id"] == "run-1"
    assert first["trace"]["name"] == "cps.dispatch"
    assert first["observation"]["id"] == "dispatch-1"
    assert first["observation"]["type"] == "span"
    assert first["observation"]["name"] == "projection_bundle_materialized"
    assert first["observation"]["metadata"]["cps.canonical_hash"] == bundle.canonical_hash()


def test_phoenix_export_is_deterministic_and_has_evaluations():
    from cps.export.phoenix import projection_bundle_to_phoenix_payload

    bundle = _bundle()
    first = projection_bundle_to_phoenix_payload(bundle)
    second = projection_bundle_to_phoenix_payload(bundle)

    assert _stable(first) == _stable(second)
    assert first["trace_id"] == "run-1"
    assert first["span_id"] == "dispatch-1"
    assert first["span_name"] == "cps.projection_bundle"
    assert first["attributes"]["cps.context_hash"] == "context-hash"
    assert first["evaluations"][0]["name"] == "metric_claim_level"
    assert first["evaluations"][0]["value"] == "vinfo_proxy_supported"


def test_missing_optional_diagnostics_do_not_crash():
    from cps.export.otel import projection_bundle_to_otel_span

    payload = projection_bundle_to_otel_span(_bundle(include_diagnostics=False))
    attributes = payload["attributes"]

    assert attributes["cps.diagnostic_claim_level"] == "vinfo_proxy_supported"
    assert "cps.metric_claim_level" not in attributes
    assert "cps.selector_action" not in attributes


def test_full_context_is_excluded_by_default_and_preview_is_bounded():
    from cps.export.common import projection_bundle_observability_fields

    default_fields = projection_bundle_observability_fields(_bundle())
    default_serialized = _stable(default_fields)
    assert "SECRET_FULL_CONTEXT" not in default_serialized
    assert "content_preview" not in default_serialized

    preview_fields = projection_bundle_observability_fields(_bundle(), include_payload_preview=True)
    preview = preview_fields["payload_preview"]["materialized_context_preview"]
    assert "SECRET_FULL_CONTEXT" in preview
    assert len(preview) <= 83
    assert ("x" * 120) not in _stable(preview_fields)


def test_langfuse_non_dry_run_without_client_fails_closed():
    from cps.export.langfuse import export_projection_bundle_to_langfuse

    with pytest.raises(RuntimeError, match="dry_run=False requires an explicit client"):
        export_projection_bundle_to_langfuse(_bundle(), dry_run=False)


def test_exporters_do_not_use_network_or_reference(monkeypatch):
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("exporters must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    from cps.export.langfuse import projection_bundle_to_langfuse_payload
    from cps.export.otel import projection_bundle_to_otel_span
    from cps.export.phoenix import projection_bundle_to_phoenix_payload

    bundle = _bundle()
    projection_bundle_to_otel_span(bundle)
    projection_bundle_to_langfuse_payload(bundle)
    projection_bundle_to_phoenix_payload(bundle)
