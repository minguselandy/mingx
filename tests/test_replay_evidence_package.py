from __future__ import annotations

import json
import socket
from pathlib import Path

from cps.experiments.evidence_ledger import REQUIRED_EVIDENCE_ARTIFACTS
from cps.experiments.replay_evidence_package import (
    build_replay_evidence_package_from_artifact_dir,
    build_replay_evidence_package_from_summary,
    format_replay_package_summary_markdown,
    write_replay_evidence_package,
)
from cps.experiments.synthetic_benchmark import run_synthetic_benchmark


def _complete_summary(**overrides) -> dict:
    dispatch_count = int(overrides.pop("dispatch_count", 1))
    summary = {
        "run_id": "replay-package-fixture",
        "claim_level": "ambiguous_metric",
        "dispatch_count": dispatch_count,
        "artifact_counts": {name: dispatch_count for name in REQUIRED_EVIDENCE_ARTIFACTS},
        "metric_claim_level_counts": {"ambiguous_metric": dispatch_count},
        "diagnostic_scope_counts": {"synthetic_structural_only": dispatch_count},
        "complete_artifact_sets": True,
    }
    summary.update(overrides)
    return summary


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_package_builds_stable_manifest_from_in_memory_summary():
    package = build_replay_evidence_package_from_summary(
        _complete_summary(),
        evidence_overrides={
            "bridge_freshness": "fresh",
            "projection_bundle_hashes": ["hash-b", "hash-a"],
        },
    )
    manifest = package["manifest"]

    assert manifest["package_schema_version"] == "ReplayEvidencePackageV1"
    assert manifest["source_run_id"] == "replay-package-fixture"
    assert manifest["evidence_mode"] == "synthetic_structural_only"
    assert manifest["evidence_scope"] == "synthetic_structural_only"
    assert manifest["source_phase"] == "P05"
    assert manifest["projection_bundle_count"] == 1
    assert manifest["projection_bundle_hash_count"] == 2
    assert manifest["projection_bundle_hashes"] == ["hash-a", "hash-b"]
    assert manifest["measurement_validated_allowed"] is False
    assert manifest["p04_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert manifest["p09_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert "measurement_validated" in manifest["denied_claims"]
    assert "synthetic_only_not_deployed_certification" in manifest["reason_codes"]
    assert manifest["package_claim_scope"] == "ambiguous_metric"

    second = build_replay_evidence_package_from_summary(
        _complete_summary(),
        evidence_overrides={
            "bridge_freshness": "fresh",
            "projection_bundle_hashes": ["hash-b", "hash-a"],
        },
    )
    assert package == second


def test_package_writes_stable_files_from_synthetic_artifact_dir(workspace_tmp_dir):
    source_dir = workspace_tmp_dir / "synthetic_source"
    run_synthetic_benchmark(
        config_path="configs/runs/synthetic-regime-smoke.json",
        output_dir=source_dir,
    )

    package = build_replay_evidence_package_from_artifact_dir(source_dir)
    first = write_replay_evidence_package(workspace_tmp_dir / "package_a", package)
    second = write_replay_evidence_package(workspace_tmp_dir / "package_b", package)

    expected_outputs = {
        "manifest",
        "artifact_counts",
        "projection_bundle_hashes",
        "evidence_ledger",
        "claim_gate_report_json",
        "claim_gate_report_markdown",
        "proxy_regime_matrix_json",
        "proxy_regime_matrix_markdown",
        "summary_markdown",
    }
    assert expected_outputs.issubset(first)
    for key in expected_outputs:
        assert Path(first[key]).exists()
        assert _read(first[key]) == _read(second[key])

    manifest = json.loads(_read(first["manifest"]))
    assert manifest["required_artifacts_present"] is True
    assert manifest["projection_bundle_count"] == 3
    assert manifest["projection_bundle_hash_count"] == 3
    assert manifest["measurement_validated_allowed"] is False
    assert manifest["evidence_scope"] == "synthetic_structural_only"
    assert manifest["package_claim_scope"] == "ambiguous_metric"


def test_missing_projection_bundles_fails_package_conservatively():
    summary = _complete_summary()
    summary["artifact_counts"].pop("projection_bundles")

    package = build_replay_evidence_package_from_summary(summary)
    manifest = package["manifest"]

    assert manifest["required_artifacts_present"] is False
    assert manifest["missing_required_artifacts"] == ["projection_bundles"]
    assert manifest["projection_bundle_count"] == 0
    assert manifest["package_claim_scope"] == "ambiguous_metric"
    assert manifest["claim_gate_allowed_level"] == "ambiguous_metric"
    assert "missing_projection_bundles" in manifest["reason_codes"]


def test_complete_package_without_labels_or_kappa_denies_measurement_validation():
    package = build_replay_evidence_package_from_summary(
        _complete_summary(),
        evidence_overrides={
            "bridge_freshness": "fresh",
            "metric_bridge_witness_count": 1,
            "human_labels_present": False,
            "kappa_present": False,
        },
    )
    manifest = package["manifest"]

    assert manifest["measurement_validated_allowed"] is False
    assert "missing_human_labels" in manifest["reason_codes"]
    assert "missing_kappa" in manifest["reason_codes"]
    assert "measurement_validated" in manifest["denied_claims"]


def test_contamination_failure_forces_pilot_only_scope():
    package = build_replay_evidence_package_from_summary(
        _complete_summary(claim_level="operational_utility_only"),
        evidence_overrides={
            "contamination_status": "failed",
            "bridge_freshness": "fresh",
            "human_labels_present": True,
            "kappa_present": True,
        },
    )

    assert package["manifest"]["claim_gate_allowed_level"] == "pilot_only"
    assert package["manifest"]["package_claim_scope"] == "pilot_only"
    assert package["manifest"]["reason_codes"][0] == "contamination_failed"


def test_stale_metric_bridge_is_reflected_in_reason_codes():
    package = build_replay_evidence_package_from_summary(
        _complete_summary(claim_level="operational_utility_only"),
        evidence_overrides={
            "bridge_freshness": "stale",
            "human_labels_present": True,
            "kappa_present": True,
        },
    )

    assert "stale_metric_bridge" in package["manifest"]["reason_codes"]
    assert package["manifest"]["package_claim_scope"] in {"operational_utility_only", "ambiguous_metric"}


def test_synthetic_and_engineering_packages_keep_forbidden_claims_denied():
    synthetic_package = build_replay_evidence_package_from_summary(_complete_summary())
    engineering_package = build_replay_evidence_package_from_summary(
        _complete_summary(
            claim_level="engineering_smoke_only",
            metric_claim_level_counts={"engineering_smoke_only": 1},
        ),
        evidence_overrides={"evidence_mode": "engineering_smoke_only"},
    )

    assert "deployed_v_information_certification" in synthetic_package["manifest"]["denied_claims"]
    assert "scientific_validation" in engineering_package["manifest"]["denied_claims"]
    assert "synthetic_only_not_deployed_certification" in synthetic_package["manifest"]["reason_codes"]
    assert "engineering_evidence_only" in engineering_package["manifest"]["reason_codes"]
    assert "deployed_V_information_certified" not in json.dumps(synthetic_package["manifest"])


def test_live_api_or_external_runtime_flags_alone_do_not_allow_validation():
    live_package = build_replay_evidence_package_from_summary(
        _complete_summary(claim_level="operational_utility_only"),
        evidence_overrides={"live_api_used": True, "human_labels_present": False},
    )
    runtime_package = build_replay_evidence_package_from_summary(
        _complete_summary(claim_level="operational_utility_only"),
        evidence_overrides={"external_runtime_used": True, "kappa_present": False},
    )

    assert live_package["manifest"]["measurement_validated_allowed"] is False
    assert "live_api_not_validation" in live_package["manifest"]["reason_codes"]
    assert runtime_package["manifest"]["measurement_validated_allowed"] is False
    assert "external_runtime_not_validation" in runtime_package["manifest"]["reason_codes"]


def test_hashes_and_reason_codes_are_sorted_deterministically():
    package = build_replay_evidence_package_from_summary(
        _complete_summary(
            claim_level="vinfo_proxy_supported",
            metric_claim_level_counts={"vinfo_proxy_supported": 1},
            diagnostic_scope_counts={},
        ),
        evidence_overrides={
            "projection_bundle_hashes": ["z-hash", "a-hash", "m-hash"],
            "contamination_status": "failed",
        },
    )
    manifest = package["manifest"]

    assert manifest["projection_bundle_hashes"] == ["a-hash", "m-hash", "z-hash"]
    assert manifest["reason_codes"] == sorted(
        manifest["reason_codes"],
        key=package["claim_gate_report"]["reason_code_order"].index,
    )


def test_summary_markdown_exposes_p04_p09_and_claim_boundary():
    package = build_replay_evidence_package_from_summary(_complete_summary())
    markdown = format_replay_package_summary_markdown(package)

    assert "P04 status: `BLOCKED_OPERATOR_REQUIRED`" in markdown
    assert "P09 status: `BLOCKED_OPERATOR_REQUIRED`" in markdown
    assert "Replay package completeness is not scientific validation" in markdown
    assert "measurement_validated is not claimed" in markdown


def test_replay_package_does_not_use_network_or_reference(monkeypatch, workspace_tmp_dir):
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("replay evidence package must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    package = build_replay_evidence_package_from_summary(_complete_summary())
    outputs = write_replay_evidence_package(workspace_tmp_dir / "package", package)

    assert Path(outputs["manifest"]).exists()
    assert package["manifest"]["live_api_used"] is False
    assert package["manifest"]["external_runtime_used"] is False
