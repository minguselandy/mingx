from __future__ import annotations

import json
import socket
from pathlib import Path

from cps.experiments.claim_gate_report import (
    build_claim_gate_report,
    format_claim_gate_markdown,
    write_claim_gate_outputs,
)
from cps.experiments.evidence_ledger import (
    REQUIRED_EVIDENCE_ARTIFACTS,
    build_evidence_ledger_from_summary,
)


def _complete_ledger(**overrides):
    summary = {
        "run_id": "run-1",
        "claim_level": "engineering_smoke_only",
        "artifact_counts": {name: 1 for name in REQUIRED_EVIDENCE_ARTIFACTS},
    }
    return build_evidence_ledger_from_summary(summary, **overrides)


def test_complete_engineering_smoke_evidence_does_not_allow_measurement_validation():
    report = build_claim_gate_report(_complete_ledger())

    assert report["allowed_claim_level"] == "engineering_smoke_only"
    assert report["metric_bridge_gate_status"] == "missing_bridge"
    assert report["measurement_validated_allowed"] is False
    assert "measurement_validated" in report["denied_claims"]
    assert "engineering_evidence_only" in report["reason_codes"]


def test_missing_human_labels_denies_measurement_validated():
    report = build_claim_gate_report(_complete_ledger(human_labels_present=False, kappa_present=True))

    assert report["measurement_validated_allowed"] is False
    assert "missing_human_labels" in report["reason_codes"]


def test_missing_kappa_denies_measurement_validated():
    report = build_claim_gate_report(_complete_ledger(human_labels_present=True, kappa_present=False))

    assert report["measurement_validated_allowed"] is False
    assert "missing_kappa" in report["reason_codes"]


def test_contamination_failure_forces_pilot_only():
    report = build_claim_gate_report(
        _complete_ledger(
            contamination_status="failed",
            human_labels_present=True,
            kappa_present=True,
            bridge_freshness="fresh",
            evidence_mode="operational_utility_only",
        )
    )

    assert report["allowed_claim_level"] == "pilot_only"
    assert report["measurement_validated_allowed"] is False
    assert report["reason_codes"][0] == "contamination_failed"


def test_missing_or_stale_bridge_never_allows_validation_claims():
    for bridge_freshness in ("missing", "stale"):
        report = build_claim_gate_report(
            _complete_ledger(
                evidence_mode="operational_utility_only",
                human_labels_present=True,
                kappa_present=True,
                bridge_freshness=bridge_freshness,
            )
        )

        assert report["allowed_claim_level"] in {"ambiguous", "operational_utility_only"}
        assert report["measurement_validated_allowed"] is False
        assert f"{bridge_freshness}_metric_bridge" in report["reason_codes"]


def test_synthetic_evidence_denies_deployed_v_information_certification():
    report = build_claim_gate_report(
        _complete_ledger(evidence_mode="synthetic_structural_only", source_phase="P05")
    )

    assert report["allowed_claim_level"] == "ambiguous_metric"
    assert report["evidence_scope"] == "synthetic_structural_only"
    assert "deployed_v_information_certification" in report["denied_claims"]
    assert "synthetic_only_not_deployed_certification" in report["reason_codes"]


def test_synthetic_only_evidence_scope_does_not_silently_become_vinfo_proxy_supported():
    report = build_claim_gate_report(
        _complete_ledger(
            evidence_scope="synthetic_structural_only",
            diagnostic_scope="synthetic_structural_only",
            diagnostic_claim_level="structural_synthetic_only",
            metric_class="synthetic_oracle",
            source_phase="P05",
        )
    )

    assert report["allowed_claim_level"] == "ambiguous_metric"
    assert report["allowed_claim_level"] != "vinfo_proxy_supported"
    assert report["evidence_scope"] == "synthetic_structural_only"
    assert report["measurement_validated_allowed"] is False


def test_missing_required_artifacts_fail_closed_to_ambiguous():
    summary = {
        "run_id": "run-1",
        "claim_level": "engineering_smoke_only",
        "artifact_counts": {name: 1 for name in REQUIRED_EVIDENCE_ARTIFACTS if name != "projection_bundles"},
    }
    ledger = build_evidence_ledger_from_summary(summary)

    report = build_claim_gate_report(ledger)

    assert report["allowed_claim_level"] == "ambiguous_metric"
    assert report["measurement_validated_allowed"] is False
    assert "missing_required_artifacts" in report["reason_codes"]
    assert "missing_projection_bundles" in report["reason_codes"]


def test_reason_codes_are_stable_and_ordered():
    ledger = _complete_ledger(
        contamination_status="failed",
        evidence_mode="synthetic_structural_only",
        source_phase="P05",
    )

    first = build_claim_gate_report(ledger)
    second = build_claim_gate_report(ledger)

    assert first["reason_codes"] == second["reason_codes"]
    assert first["reason_codes"] == sorted(first["reason_codes"], key=first["reason_code_order"].index)


def test_p04_and_p09_blocked_status_remains_visible():
    report = build_claim_gate_report(_complete_ledger())

    assert report["p04_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert report["p09_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert report["metric_bridge_gate_status"] == "missing_bridge"
    assert "missing_metric_bridge" in report["metric_bridge_reason_codes"]
    assert "P04 remains BLOCKED_OPERATOR_REQUIRED" in report["summary"]
    assert "P09 remains BLOCKED_OPERATOR_REQUIRED" in report["summary"]


def test_writer_outputs_deterministic_json_and_markdown(workspace_tmp_dir):
    ledger = _complete_ledger()
    report = build_claim_gate_report(ledger)
    first = write_claim_gate_outputs(workspace_tmp_dir / "first", ledger, report)
    second = write_claim_gate_outputs(workspace_tmp_dir / "second", ledger, report)

    assert Path(first["ledger_json"]).read_text(encoding="utf-8") == Path(second["ledger_json"]).read_text(
        encoding="utf-8"
    )
    assert Path(first["report_json"]).read_text(encoding="utf-8") == Path(second["report_json"]).read_text(
        encoding="utf-8"
    )
    assert Path(first["report_markdown"]).read_text(encoding="utf-8") == Path(
        second["report_markdown"]
    ).read_text(encoding="utf-8")
    assert "measurement_validated_allowed: false" in format_claim_gate_markdown(report)


def test_claim_gate_report_does_not_use_network_or_reference(monkeypatch, workspace_tmp_dir):
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("claim gate report must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    ledger = _complete_ledger()
    report = build_claim_gate_report(ledger)
    outputs = write_claim_gate_outputs(workspace_tmp_dir / "claim_gate", ledger, report)

    assert json.loads(Path(outputs["report_json"]).read_text(encoding="utf-8"))["measurement_validated_allowed"] is False
