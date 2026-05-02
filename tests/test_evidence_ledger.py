from __future__ import annotations

import json
import socket
from copy import deepcopy
from pathlib import Path

from cps.experiments.evidence_ledger import (
    REQUIRED_EVIDENCE_ARTIFACTS,
    build_evidence_ledger_from_artifact_dir,
    build_evidence_ledger_from_summary,
    write_evidence_ledger,
)
from cps.experiments.provider_offline_smoke import run_provider_offline_smoke


def _jsonl_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_builds_ledger_from_provider_offline_smoke_artifacts(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "provider_smoke"
    run_provider_offline_smoke(output_dir, seed=12, budget_tokens=12)

    ledger = build_evidence_ledger_from_artifact_dir(output_dir)

    assert ledger["run_id"] == "provider-offline-smoke-12"
    assert ledger["evidence_mode"] == "engineering_smoke_only"
    assert ledger["required_artifacts_present"] is True
    assert ledger["missing_required_artifacts"] == []
    assert ledger["projection_bundle_count"] == 2
    assert ledger["projection_bundle_hashes_present"] is True
    assert len(ledger["projection_bundle_hashes"]) == 2
    assert ledger["metric_bridge_witness_count"] == 2
    assert ledger["diagnostic_count"] == 2
    assert ledger["replay_available"] is True
    assert ledger["source_phase"] == "P11"


def test_ledger_defaults_are_conservative_for_in_memory_summary():
    summary = {
        "run_id": "run-1",
        "claim_level": "engineering_smoke_only",
        "artifact_counts": {name: 1 for name in REQUIRED_EVIDENCE_ARTIFACTS},
    }

    ledger = build_evidence_ledger_from_summary(summary)

    assert ledger["human_labels_present"] is False
    assert ledger["kappa_present"] is False
    assert ledger["contamination_status"] == "unknown"
    assert ledger["bridge_freshness"] == "missing"
    assert ledger["live_api_used"] is False
    assert ledger["external_runtime_used"] is False
    assert ledger["p04_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert ledger["p09_status"] == "BLOCKED_OPERATOR_REQUIRED"


def test_ledger_reports_missing_projection_bundles_from_summary():
    summary = {
        "run_id": "run-1",
        "claim_level": "engineering_smoke_only",
        "artifact_counts": {name: 1 for name in REQUIRED_EVIDENCE_ARTIFACTS if name != "projection_bundles"},
    }

    ledger = build_evidence_ledger_from_summary(summary)

    assert ledger["required_artifacts_present"] is False
    assert ledger["projection_bundle_count"] == 0
    assert ledger["projection_bundle_hashes_present"] is False
    assert ledger["missing_required_artifacts"] == ["projection_bundles"]


def test_ledger_reports_missing_projection_bundles_from_artifact_dir(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "provider_smoke"
    run_provider_offline_smoke(output_dir, seed=13, budget_tokens=12)
    (output_dir / "projection_bundles.jsonl").write_text("", encoding="utf-8")

    ledger = build_evidence_ledger_from_artifact_dir(output_dir)

    assert ledger["required_artifacts_present"] is False
    assert ledger["projection_bundle_count"] == 0
    assert "projection_bundles" in ledger["missing_required_artifacts"]


def test_build_evidence_ledger_from_summary_does_not_mutate_input():
    summary = {
        "run_id": "run-1",
        "artifact_counts": {name: 1 for name in REQUIRED_EVIDENCE_ARTIFACTS},
        "nested": {"values": ["b", "a"]},
    }
    original = deepcopy(summary)

    build_evidence_ledger_from_summary(summary)

    assert summary == original


def test_write_evidence_ledger_is_deterministic(workspace_tmp_dir):
    ledger = build_evidence_ledger_from_summary(
        {
            "run_id": "run-1",
            "claim_level": "engineering_smoke_only",
            "artifact_counts": {name: 1 for name in REQUIRED_EVIDENCE_ARTIFACTS},
        }
    )
    first = workspace_tmp_dir / "first" / "evidence-ledger.json"
    second = workspace_tmp_dir / "second" / "evidence-ledger.json"

    write_evidence_ledger(first, ledger)
    write_evidence_ledger(second, ledger)

    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")


def test_evidence_ledger_does_not_use_network_or_reference(monkeypatch, workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "provider_smoke"
    run_provider_offline_smoke(output_dir, seed=14, budget_tokens=12)
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("evidence ledger must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    ledger = build_evidence_ledger_from_artifact_dir(output_dir)

    assert ledger["live_api_used"] is False
    assert ledger["external_runtime_used"] is False
    assert len(_jsonl_rows(output_dir / "projection_bundles.jsonl")) == 2
