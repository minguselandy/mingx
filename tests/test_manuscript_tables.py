from __future__ import annotations

import socket
from pathlib import Path

from cps.experiments.manuscript_tables import (
    build_context_projection_v10_manuscript_patch,
    format_context_projection_v10_patch_markdown,
    write_context_projection_v10_manuscript_patch,
)


def _paper_summary() -> dict:
    return {
        "paper_evidence_schema_version": "PaperEvidenceSummaryV1",
        "source_run_id": "p17_offline_evidence_demo",
        "source_phase": "P17",
        "evidence_mode": "offline_runtime_audit_demo",
        "claim_gate_summary": {
            "allowed_claim_level": "engineering_smoke_only",
            "measurement_validated_allowed": False,
            "denied_claims": [
                "deployed_v_information_certification",
                "measurement_validated",
                "scientific_validation",
            ],
            "reason_codes": [
                "missing_human_labels",
                "missing_kappa",
                "engineering_evidence_only",
                "complete_artifacts_not_validation",
            ],
            "p04_status": "BLOCKED_OPERATOR_REQUIRED",
            "p09_status": "BLOCKED_OPERATOR_REQUIRED",
        },
        "proxy_regime_summary": {
            "matrix_available": True,
            "regime_names": [
                "redundancy_dominated",
                "sparse_pairwise_synergy",
                "higher_order_synergy",
            ],
            "certification_scopes": [
                "proxy_regime_diagnostic_only",
                "synthetic_structural_only",
            ],
        },
        "replay_package_summary": {
            "package_claim_scope": "engineering_smoke_only",
            "deterministic_replay_package_status": "available",
        },
        "p04_status": "BLOCKED_OPERATOR_REQUIRED",
        "p09_status": "BLOCKED_OPERATOR_REQUIRED",
        "measurement_validated_allowed": False,
        "denied_claims": [
            "deployed_v_information_certification",
            "measurement_validated",
            "scientific_validation",
        ],
        "reason_codes": [
            "missing_human_labels",
            "missing_kappa",
            "engineering_evidence_only",
            "complete_artifacts_not_validation",
        ],
        "final_claim_boundary": "paper-facing summaries do not upgrade claim levels; measurement_validated is not claimed",
    }


def test_builder_creates_all_required_tables():
    patch = build_context_projection_v10_manuscript_patch(_paper_summary())

    assert patch["target_manuscript_path"] == "docs/archive/context_projection_revised_v10.md"
    assert patch["artifact_table"]
    assert patch["claim_gate_table"]
    assert patch["proxy_regime_table"]
    assert patch["replay_evidence_table"]
    assert patch["limitation_table"]


def test_artifact_table_includes_projection_bundle_v1():
    patch = build_context_projection_v10_manuscript_patch(_paper_summary())
    artifacts = [row["artifact"] for row in patch["artifact_table"]]

    assert "ProjectionBundleV1" in artifacts
    assert artifacts == [
        "ProjectionPlan",
        "BudgetWitness",
        "MaterializedContext",
        "MetricBridgeWitness",
        "ProjectionBundleV1",
        "EvidenceLedger",
        "ClaimGateReport",
        "MetricBridgeGate",
        "ProxyRegimeMatrix",
        "ReplayEvidencePackage",
        "PaperEvidenceSummary",
        "EndToEndEvidenceDemo",
    ]


def test_claim_gate_table_contains_required_denials():
    patch = build_context_projection_v10_manuscript_patch(_paper_summary())
    conditions = {row["condition"]: row for row in patch["claim_gate_table"]}

    assert conditions["missing human labels"]["denied_claim"] == "measurement_validated"
    assert conditions["missing kappa"]["denied_claim"] == "measurement_validated"
    assert conditions["stale metric bridge"]["allowed_claim_boundary"] == "operational_utility_only or ambiguous"
    assert conditions["missing metric bridge"]["allowed_claim_boundary"] == "operational_utility_only or ambiguous"
    assert conditions["synthetic-only evidence"]["denied_claim"] == "deployed V-information certification"
    assert conditions["engineering-only evidence"]["denied_claim"] == "scientific validation"
    assert conditions["replay package completeness"]["denied_claim"] == "scientific validation"
    assert conditions["paper-facing summary"]["allowed_claim_boundary"] == "no claim upgrade"
    assert conditions["live API success alone"]["denied_claim"] == "measurement validation"
    assert conditions["external runtime success alone"]["denied_claim"] == "measurement validation"


def test_proxy_regime_table_contains_required_regimes():
    patch = build_context_projection_v10_manuscript_patch(_paper_summary())
    regimes = [row["regime"] for row in patch["proxy_regime_table"]]

    assert "redundancy_dominated" in regimes
    assert "sparse_pairwise_synergy" in regimes
    assert "higher_order_synergy" in regimes
    assert "contamination_failed" in regimes
    assert "missing_human_labels" in regimes
    assert "missing_kappa" in regimes
    assert "stale_metric_bridge" in regimes
    assert "missing_metric_bridge" in regimes
    assert "artifact_incomplete" in regimes


def test_replay_evidence_table_includes_claim_gate_markdown():
    patch = build_context_projection_v10_manuscript_patch(_paper_summary())
    outputs = [row["output"] for row in patch["replay_evidence_table"]]

    assert "claim_gate_report.md" in outputs
    assert "demo_summary.md" in outputs


def test_limitation_table_contains_p04_p09_statuses():
    patch = build_context_projection_v10_manuscript_patch(_paper_summary())
    limitations = [row["limitation"] for row in patch["limitation_table"]]

    assert "P04 remains deferred/operator-required" in limitations
    assert "P09 remains BLOCKED_OPERATOR_REQUIRED" in limitations
    assert "missing labels/kappa block measurement validation" in limitations


def test_patch_markdown_references_target_and_claim_boundaries():
    patch = build_context_projection_v10_manuscript_patch(_paper_summary())
    markdown = format_context_projection_v10_patch_markdown(patch)

    assert "docs/archive/context_projection_revised_v10.md" in markdown
    assert "measurement_validated is not claimed" in markdown
    assert "P17 is not scientific validation" in markdown
    assert "paper-facing summaries do not upgrade claim levels" in markdown
    assert "This patch does not modify the source manuscript unless separately approved." in markdown


def test_markdown_output_is_deterministic(workspace_tmp_dir):
    patch = build_context_projection_v10_manuscript_patch(_paper_summary())
    first = format_context_projection_v10_patch_markdown(patch)
    second = format_context_projection_v10_patch_markdown(patch)

    assert first == second

    first_path = write_context_projection_v10_manuscript_patch(workspace_tmp_dir / "first.md", patch)
    second_path = write_context_projection_v10_manuscript_patch(workspace_tmp_dir / "second.md", patch)

    assert Path(first_path).read_text(encoding="utf-8") == Path(second_path).read_text(encoding="utf-8")


def test_paper_facing_summary_does_not_upgrade_claim_levels():
    patch = build_context_projection_v10_manuscript_patch(_paper_summary())

    assert patch["claim_boundary"]["measurement_validated_allowed"] is False
    assert patch["claim_boundary"]["final_claim_boundary"] == "paper-facing summaries do not upgrade claim levels"
    assert "measurement_validated" in patch["denied_claims"]
    assert "P04 operator scientific closure" in patch["operator_required_claims"]
    assert "P09 operator runtime integration" in patch["operator_required_claims"]


def test_builder_reads_p17_demo_output_directory(workspace_tmp_dir):
    demo_dir = workspace_tmp_dir / "demo"
    demo_dir.mkdir()
    (demo_dir / "paper_evidence_summary.json").write_text(
        """{
  "paper_evidence_schema_version": "PaperEvidenceSummaryV1",
  "source_run_id": "p17_offline_evidence_demo",
  "source_phase": "P17",
  "evidence_mode": "offline_runtime_audit_demo",
  "p04_status": "BLOCKED_OPERATOR_REQUIRED",
  "p09_status": "BLOCKED_OPERATOR_REQUIRED",
  "measurement_validated_allowed": false,
  "denied_claims": ["measurement_validated"],
  "reason_codes": ["missing_human_labels", "missing_kappa"]
}
""",
        encoding="utf-8",
    )
    (demo_dir / "demo_manifest.json").write_text(
        """{
  "demo_schema_version": "EndToEndEvidenceDemoV1",
  "run_id": "p17_offline_evidence_demo",
  "measurement_validated_allowed": false,
  "denied_claims": ["measurement_validated"],
  "reason_codes": ["missing_human_labels", "missing_kappa"]
}
""",
        encoding="utf-8",
    )

    patch = build_context_projection_v10_manuscript_patch(demo_dir)

    assert patch["source_run_id"] == "p17_offline_evidence_demo"
    assert patch["claim_boundary"]["measurement_validated_allowed"] is False


def test_no_network_or_reference_path_access(monkeypatch):
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("manuscript table builder must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    patch = build_context_projection_v10_manuscript_patch(_paper_summary())

    assert patch["target_manuscript_path"] == "docs/archive/context_projection_revised_v10.md"
