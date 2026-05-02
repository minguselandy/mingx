from __future__ import annotations

import json
import socket
from pathlib import Path

from cps.experiments.evidence_ledger import REQUIRED_EVIDENCE_ARTIFACTS
from cps.experiments.paper_evidence_summary import (
    build_paper_evidence_summary_from_package_dir,
    build_paper_evidence_summary_from_replay_package,
    build_paper_evidence_summary_from_summary,
    format_paper_evidence_summary_markdown,
    write_paper_evidence_summary,
)
from cps.experiments.proxy_regime_matrix import build_proxy_regime_matrix_from_summary
from cps.experiments.replay_evidence_package import (
    build_replay_evidence_package_from_summary,
    write_replay_evidence_package,
)


def _complete_summary(**overrides) -> dict:
    dispatch_count = int(overrides.pop("dispatch_count", 1))
    summary = {
        "run_id": "paper-evidence-fixture",
        "claim_level": "synthetic_structural_only",
        "dispatch_count": dispatch_count,
        "artifact_counts": {name: dispatch_count for name in REQUIRED_EVIDENCE_ARTIFACTS},
        "metric_claim_level_counts": {"structural_synthetic_only": dispatch_count},
        "complete_artifact_sets": True,
    }
    summary.update(overrides)
    return summary


def _matrix() -> dict:
    return build_proxy_regime_matrix_from_summary(_complete_summary())


def _package(**overrides) -> dict:
    return build_replay_evidence_package_from_summary(
        _complete_summary(**overrides.pop("summary_overrides", {})),
        proxy_regime_matrix=overrides.pop("proxy_regime_matrix", _matrix()),
        evidence_overrides={
            "bridge_freshness": "fresh",
            "projection_bundle_hashes": ["hash-b", "hash-a"],
            **overrides,
        },
    )


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_summary_builder_creates_stable_json_from_replay_package(workspace_tmp_dir):
    summary = build_paper_evidence_summary_from_replay_package(_package())
    outputs = write_paper_evidence_summary(workspace_tmp_dir / "paper", summary)
    payload = json.loads(_read(outputs["json"]))

    assert payload["paper_evidence_schema_version"] == "PaperEvidenceSummaryV1"
    assert payload["source_run_id"] == "paper-evidence-fixture"
    assert payload["evidence_mode"] == "synthetic_structural_only"
    assert payload["measurement_validated_allowed"] is False
    assert payload["p04_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert payload["p09_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert "measurement_validated" in payload["denied_claims"]
    assert "synthetic_only_not_deployed_certification" in payload["reason_codes"]


def test_summary_builder_creates_stable_markdown_from_replay_package():
    summary = build_paper_evidence_summary_from_replay_package(_package())

    first = format_paper_evidence_summary_markdown(summary)
    second = format_paper_evidence_summary_markdown(summary)

    assert first == second
    assert "# Paper Evidence Summary" in first
    assert "Artifact Evidence Table" in first
    assert "Claim Boundary Table" in first
    assert "Proxy-Regime Table" in first
    assert "Replay Evidence Table" in first
    assert "paper-facing summaries do not upgrade claim levels" in first


def test_repeated_writes_are_byte_identical(workspace_tmp_dir):
    summary = build_paper_evidence_summary_from_replay_package(_package())

    first = write_paper_evidence_summary(workspace_tmp_dir / "first", summary)
    second = write_paper_evidence_summary(workspace_tmp_dir / "second", summary)

    assert _read(first["json"]) == _read(second["json"])
    assert _read(first["markdown"]) == _read(second["markdown"])


def test_package_dir_input_reads_p15_output_files(workspace_tmp_dir):
    package = _package()
    package_outputs = write_replay_evidence_package(workspace_tmp_dir / "package", package)

    summary = build_paper_evidence_summary_from_package_dir(workspace_tmp_dir / "package")

    assert Path(package_outputs["manifest"]).exists()
    assert summary["source_run_id"] == "paper-evidence-fixture"
    assert summary["proxy_regime_summary"]["matrix_available"] is True
    assert summary["projection_bundle_summary"]["projection_bundle_hash_count"] == 2
    assert summary["replay_package_summary"]["claim_gate_report_available"] is True


def test_manuscript_table_groups_are_present_and_ordered():
    summary = build_paper_evidence_summary_from_replay_package(_package())
    rows = summary["manuscript_table_rows"]

    assert list(rows) == [
        "artifact_table_rows",
        "claim_gate_table_rows",
        "proxy_regime_table_rows",
        "replay_package_table_rows",
        "limitation_table_rows",
    ]
    assert [row["artifact"] for row in rows["artifact_table_rows"]] == list(REQUIRED_EVIDENCE_ARTIFACTS)
    assert [row["field"] for row in rows["claim_gate_table_rows"]] == [
        "allowed_claim_level",
        "measurement_validated_allowed",
        "package_claim_scope",
        "p04_status",
        "p09_status",
        "live_api_used",
        "external_runtime_used",
    ]
    assert rows["proxy_regime_table_rows"][0]["regime_name"] == "redundancy_dominated"
    assert rows["replay_package_table_rows"][0]["output"] == "manifest.json"
    assert rows["limitation_table_rows"][0]["limitation"] == "P04 remains deferred/operator-required."


def test_claim_boundaries_are_preserved_for_missing_labels_and_kappa():
    summary = build_paper_evidence_summary_from_summary(
        _complete_summary(),
        proxy_regime_matrix=_matrix(),
        evidence_overrides={
            "bridge_freshness": "fresh",
            "human_labels_present": False,
            "kappa_present": False,
        },
    )

    assert summary["measurement_validated_allowed"] is False
    assert "missing_human_labels" in summary["reason_codes"]
    assert "missing_kappa" in summary["reason_codes"]
    assert "measurement_validated" in summary["denied_claims"]
    assert summary["claim_gate_summary"]["allowed_claim_level"] == "synthetic_structural_only"


def test_complete_artifacts_and_replay_package_do_not_allow_validation():
    summary = build_paper_evidence_summary_from_replay_package(_package())

    assert summary["artifact_summary"]["required_artifacts_present"] is True
    assert summary["replay_package_summary"]["package_claim_scope"] == "synthetic_structural_only"
    assert summary["measurement_validated_allowed"] is False
    assert "complete_artifacts_not_validation" in summary["reason_codes"]
    assert "Replay package completeness is not scientific validation." in summary["limitations"]


def test_synthetic_and_engineering_evidence_keep_forbidden_claims_denied():
    synthetic_summary = build_paper_evidence_summary_from_replay_package(_package())
    engineering_summary = build_paper_evidence_summary_from_summary(
        _complete_summary(
            claim_level="engineering_smoke_only",
            metric_claim_level_counts={"engineering_smoke_only": 1},
        ),
        evidence_overrides={"evidence_mode": "engineering_smoke_only"},
    )

    assert "deployed_v_information_certification" in synthetic_summary["denied_claims"]
    assert "synthetic_only_not_deployed_certification" in synthetic_summary["reason_codes"]
    assert "scientific_validation" in engineering_summary["denied_claims"]
    assert "engineering_evidence_only" in engineering_summary["reason_codes"]


def test_live_api_and_external_runtime_flags_do_not_allow_validation():
    live_summary = build_paper_evidence_summary_from_summary(
        _complete_summary(claim_level="operational_utility_only"),
        evidence_overrides={"live_api_used": True, "human_labels_present": False},
    )
    runtime_summary = build_paper_evidence_summary_from_summary(
        _complete_summary(claim_level="operational_utility_only"),
        evidence_overrides={"external_runtime_used": True, "kappa_present": False},
    )

    assert live_summary["measurement_validated_allowed"] is False
    assert "live_api_not_validation" in live_summary["reason_codes"]
    assert runtime_summary["measurement_validated_allowed"] is False
    assert "external_runtime_not_validation" in runtime_summary["reason_codes"]


def test_reason_codes_are_stable_ordered():
    summary = build_paper_evidence_summary_from_summary(
        _complete_summary(),
        evidence_overrides={
            "projection_bundle_hashes": ["z", "a"],
            "contamination_status": "failed",
        },
    )

    assert summary["reason_codes"] == sorted(
        summary["reason_codes"],
        key=summary["claim_gate_summary"]["reason_code_order"].index,
    )
    assert summary["projection_bundle_summary"]["projection_bundle_hashes"] == ["a", "z"]


def test_p04_p09_and_claim_boundary_are_visible_in_json_and_markdown():
    summary = build_paper_evidence_summary_from_replay_package(_package())
    markdown = format_paper_evidence_summary_markdown(summary)

    assert summary["p04_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert summary["p09_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert "P04 remains deferred/operator-required." in summary["limitations"]
    assert "P09 remains BLOCKED_OPERATOR_REQUIRED." in summary["limitations"]
    assert "P04 status: `BLOCKED_OPERATOR_REQUIRED`" in markdown
    assert "P09 status: `BLOCKED_OPERATOR_REQUIRED`" in markdown
    assert "measurement_validated is not claimed" in markdown


def test_paper_evidence_summary_does_not_use_network_or_reference(monkeypatch, workspace_tmp_dir):
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("paper evidence summary must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    summary = build_paper_evidence_summary_from_replay_package(_package())
    outputs = write_paper_evidence_summary(workspace_tmp_dir / "paper", summary)

    assert Path(outputs["json"]).exists()
    assert summary["claim_gate_summary"]["live_api_used"] is False
    assert summary["claim_gate_summary"]["external_runtime_used"] is False
