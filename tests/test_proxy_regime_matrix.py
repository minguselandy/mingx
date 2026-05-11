from __future__ import annotations

import json
import socket
from pathlib import Path

from cps.experiments.evidence_ledger import REQUIRED_EVIDENCE_ARTIFACTS, build_evidence_ledger_from_summary
from cps.experiments.proxy_regime_matrix import (
    PROXY_REGIME_ENTRY_ORDER,
    build_proxy_regime_matrix_from_artifact_dir,
    build_proxy_regime_matrix_from_summary,
    format_proxy_regime_matrix_markdown,
    write_proxy_regime_matrix,
)
from cps.experiments.synthetic_benchmark import run_synthetic_benchmark


FORBIDDEN_SCOPE_VALUES = {
    "deployed_V_information_certified",
    "measurement_validated",
    "scientific_validation",
}


def _entry_by_name(matrix: dict, name: str) -> dict:
    return next(row for row in matrix["entries"] if row["regime_name"] == name)


def _summary(**overrides) -> dict:
    dispatch_count = int(overrides.pop("dispatch_count", 1))
    summary = {
        "run_id": "matrix-fixture",
        "claim_level": "ambiguous_metric",
        "dispatch_count": dispatch_count,
        "artifact_counts": {name: dispatch_count for name in REQUIRED_EVIDENCE_ARTIFACTS},
        "metric_claim_level_counts": {"ambiguous_metric": dispatch_count},
        "diagnostic_scope_counts": {"synthetic_structural_only": dispatch_count},
        "complete_artifact_sets": True,
    }
    summary.update(overrides)
    return summary


def test_matrix_from_synthetic_artifact_dir_includes_required_regimes(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "synthetic"
    run_synthetic_benchmark(
        config_path="configs/runs/synthetic-regime-smoke.json",
        output_dir=output_dir,
    )

    matrix = build_proxy_regime_matrix_from_artifact_dir(output_dir)

    names = [row["regime_name"] for row in matrix["entries"]]
    assert names[:3] == [
        "redundancy_dominated",
        "sparse_pairwise_synergy",
        "higher_order_synergy",
    ]
    assert names == list(PROXY_REGIME_ENTRY_ORDER)
    assert _entry_by_name(matrix, "redundancy_dominated")["diagnostic_scope"] == "synthetic_structural_only"
    assert _entry_by_name(matrix, "sparse_pairwise_synergy")["diagnostic_scope"] == "synthetic_structural_only"
    assert _entry_by_name(matrix, "higher_order_synergy")["diagnostic_scope"] == "synthetic_structural_only"


def test_boundary_rows_encode_conservative_claim_results():
    matrix = build_proxy_regime_matrix_from_summary(_summary())

    contamination = _entry_by_name(matrix, "contamination_failed")
    assert contamination["allowed_claim_level"] == "pilot_only"
    assert contamination["diagnostic_scope"] == "pilot_only"
    assert "contamination_failed" in contamination["reason_codes"]

    missing_labels = _entry_by_name(matrix, "missing_human_labels")
    assert "measurement_validated" in missing_labels["denied_claims"]
    assert "missing_human_labels" in missing_labels["reason_codes"]

    missing_kappa = _entry_by_name(matrix, "missing_kappa")
    assert "measurement_validated" in missing_kappa["denied_claims"]
    assert "missing_kappa" in missing_kappa["reason_codes"]

    stale_bridge = _entry_by_name(matrix, "stale_metric_bridge")
    assert stale_bridge["allowed_claim_level"] in {"operational_utility_only", "ambiguous_metric"}
    assert stale_bridge["diagnostic_scope"] == "ambiguous_metric"
    assert "stale_metric_bridge" in stale_bridge["reason_codes"]

    missing_bridge = _entry_by_name(matrix, "missing_metric_bridge")
    assert missing_bridge["allowed_claim_level"] == "ambiguous_metric"
    assert missing_bridge["diagnostic_scope"] == "ambiguous_metric"
    assert "missing_metric_bridge" in missing_bridge["reason_codes"]

    artifact_incomplete = _entry_by_name(matrix, "artifact_incomplete")
    assert artifact_incomplete["allowed_claim_level"] == "ambiguous_metric"
    assert artifact_incomplete["diagnostic_scope"] == "ambiguous_metric"
    assert "missing_required_artifacts" in artifact_incomplete["reason_codes"]


def test_synthetic_matrix_never_emits_deployed_v_information_certification():
    matrix = build_proxy_regime_matrix_from_summary(_summary())
    serialized = json.dumps(matrix, sort_keys=True)

    assert "deployed_V_information_certified" not in {
        row["diagnostic_scope"] for row in matrix["entries"]
    }
    assert "measurement_validated" not in {
        row["diagnostic_scope"] for row in matrix["entries"]
    }
    assert "scientific_validation" not in {
        row["diagnostic_scope"] for row in matrix["entries"]
    }
    assert "deployed_V_information_certified" in matrix["denied_scope_values"]
    assert "deployed_v_information_certification" in serialized


def test_engineering_only_evidence_denies_scientific_validation():
    matrix = build_proxy_regime_matrix_from_summary(
        _summary(claim_level="engineering_smoke_only", metric_claim_level_counts={"engineering_smoke_only": 1}),
        evidence_overrides={"evidence_mode": "engineering_smoke_only"},
    )

    assert "scientific_validation" in matrix["denied_claims"]
    assert "engineering_evidence_only" in matrix["reason_codes"]
    assert matrix["allowed_claim_level"] == "engineering_smoke_only"


def test_reason_code_ordering_is_stable():
    matrix = build_proxy_regime_matrix_from_summary(_summary())

    for row in matrix["entries"]:
        assert row["reason_codes"] == sorted(row["reason_codes"], key=row["reason_code_order"].index)


def test_json_writer_is_deterministic(workspace_tmp_dir):
    matrix = build_proxy_regime_matrix_from_summary(_summary())

    first = write_proxy_regime_matrix(workspace_tmp_dir / "first", matrix)
    second = write_proxy_regime_matrix(workspace_tmp_dir / "second", matrix)

    assert Path(first["json"]).read_text(encoding="utf-8") == Path(second["json"]).read_text(encoding="utf-8")


def test_markdown_writer_contains_claim_boundary_warning(workspace_tmp_dir):
    matrix = build_proxy_regime_matrix_from_summary(_summary())
    outputs = write_proxy_regime_matrix(workspace_tmp_dir / "matrix", matrix)
    markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")

    assert "proxy-regime diagnosis is not deployed V-information certification" in markdown
    assert "measurement_validated is not claimed" in markdown
    assert "P04 remains BLOCKED_OPERATOR_REQUIRED" in format_proxy_regime_matrix_markdown(matrix)
    assert "P09 remains BLOCKED_OPERATOR_REQUIRED" in format_proxy_regime_matrix_markdown(matrix)


def test_p04_and_p09_status_remain_visible():
    matrix = build_proxy_regime_matrix_from_summary(_summary())

    assert matrix["p04_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert matrix["p09_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert "P04 remains BLOCKED_OPERATOR_REQUIRED" in matrix["claim_boundary_warning"]
    assert "P09 remains BLOCKED_OPERATOR_REQUIRED" in matrix["claim_boundary_warning"]


def test_proxy_regime_matrix_does_not_use_network_or_reference(monkeypatch, workspace_tmp_dir):
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("proxy regime matrix must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    matrix = build_proxy_regime_matrix_from_summary(_summary())
    outputs = write_proxy_regime_matrix(workspace_tmp_dir / "matrix", matrix)

    assert Path(outputs["json"]).exists()
    assert build_evidence_ledger_from_summary(_summary())["live_api_used"] is False
