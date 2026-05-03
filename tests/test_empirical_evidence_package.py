from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

from cps.experiments.contamination_audit import (
    REQUIRED_CONTAMINATION_CHECKS,
    evaluate_contamination_audit,
)
from cps.experiments.controlled_live_pilot import build_controlled_live_pilot, default_run_manifest
from cps.experiments.empirical_evidence_package import (
    build_empirical_evidence_package,
    format_empirical_evidence_summary_markdown,
    write_empirical_evidence_package,
)
from cps.experiments.human_label_kappa import LABEL_DIMENSIONS, build_human_label_kappa_report


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def _case(case_id: str = "case-001") -> dict:
    return {
        "case_id": case_id,
        "input": "Summarize the empirical evidence state.",
        "candidates": [
            {"item_id": "a", "text": "Human labels are required.", "token_cost": 4, "score": 0.9},
            {"item_id": "b", "text": "Metric bridge freshness is required.", "token_cost": 4, "score": 0.7},
        ],
    }


def _manifest(**overrides) -> dict:
    manifest = default_run_manifest(output_root="unused-output-root")
    manifest.update(
        {
            "run_id": "empirical-package-run",
            "model_endpoint": "https://example.invalid/v1/chat/completions",
            "model_name": "fixed-test-model",
            "prompt_template_id": "prompt-v1",
            "temperature": 0,
            "max_cases": 1,
        }
    )
    manifest.update(overrides)
    return manifest


def _contamination_report(**overrides) -> dict:
    checks = [
        {
            "check_name": check_name,
            "status": "pass",
            "evidence_ref": f"evidence/{check_name}.json",
            "notes": "",
        }
        for check_name in REQUIRED_CONTAMINATION_CHECKS
    ]
    if overrides:
        for row in checks:
            if row["check_name"] in overrides:
                row["status"] = overrides[row["check_name"]]
    return evaluate_contamination_audit(checks, run_id="empirical-package-run")


def _complete_label_rows(labels_by_annotator: dict[str, list[int]] | None = None) -> list[dict]:
    labels = labels_by_annotator or {
        "ann-a": [2, 2, 1, 1],
        "ann-b": [2, 2, 1, 1],
    }
    cases = ["case-001", "case-002", "case-003", "case-004"]
    rows: list[dict] = []
    for annotator_id, values in labels.items():
        for dimension in LABEL_DIMENSIONS:
            for case_id, label in zip(cases, values, strict=True):
                rows.append(
                    {
                        "run_id": "empirical-package-run",
                        "case_id": case_id,
                        "condition": "cps_runtime_audit_scaffold",
                        "annotator_id": annotator_id,
                        "label_dimension": dimension,
                        "label": label,
                        "rationale": "",
                    }
                )
    return rows


def _kappa_report(labels_by_annotator: dict[str, list[int]] | None = None) -> dict:
    return build_human_label_kappa_report(
        _complete_label_rows(labels_by_annotator),
        run_id="empirical-package-run",
        required_cases=["case-001", "case-002", "case-003", "case-004"],
        conditions=["cps_runtime_audit_scaffold"],
    )


def _mapping_source(**overrides) -> dict:
    source = {
        "run_id": "empirical-package-run",
        "live_pilot_summary": {
            "run_id": "empirical-package-run",
            "evidence_level": "EV2_controlled_live_pilot",
            "mode": "live_operator_approved",
            "live_api_used": True,
            "external_runtime_used": False,
            "case_artifact_count": 3,
            "dispatch_count": 3,
            "conditions": ["cps_runtime_audit_scaffold"],
            "human_labels_present": False,
            "kappa_present": False,
            "p04_status": "deferred/operator-required",
            "p09_status": "BLOCKED_OPERATOR_REQUIRED",
        },
        "human_label_completeness_report": {
            "labels_complete": False,
            "reason_codes": ["missing_human_labels", "incomplete_label_coverage"],
        },
        "kappa_report": {
            "human_labels_present": False,
            "labels_complete": False,
            "kappa_present": False,
            "kappa_status": "kappa_missing",
            "macro_average_kappa": None,
            "reason_codes": ["missing_human_labels", "missing_kappa"],
        },
        "contamination_report": _contamination_report(),
        "metric_bridge_freshness": "fresh",
        "artifact_completeness_status": "complete",
        "claim_gate_allows_measurement_validated": False,
    }
    source.update(overrides)
    return source


def _route_b_source(**overrides) -> dict:
    source = _mapping_source(
        route_type="model_adjudicated",
        evaluation_route="Route_B_model_adjudicated",
        human_label_completeness_report={
            "labels_complete": False,
            "reason_codes": ["human_labels_not_required_for_route_b"],
        },
        kappa_report={
            "human_labels_present": False,
            "labels_complete": False,
            "kappa_present": False,
            "kappa_status": "kappa_missing",
            "macro_average_kappa": None,
            "reason_codes": ["human_kappa_missing_for_measurement_validation"],
        },
        llm_prelabels_present=True,
        llm_prelabel_count=8,
        subagent_audit_present=True,
        codex_adjudication_report_present=True,
        model_adjudicated_labels_present=True,
        model_adjudicated_label_count=8,
        model_adjudicated_label_summary_present=True,
        model_adjudicated_label_summary={
            "model_adjudicated_labels_present": True,
            "human_labels_present": False,
            "kappa_present": False,
            "measurement_validated_allowed": False,
            "allowed_claim_level": "model_adjudicated_pilot_only",
            "total_labels": 8,
        },
    )
    source.update(overrides)
    return source


def test_package_reads_p26_output_dir_and_integrates_default_missing_ev3_artifacts(workspace_tmp_dir):
    pilot = build_controlled_live_pilot(
        workspace_tmp_dir / "pilot",
        run_manifest=_manifest(),
        cases=[_case()],
    )

    package = build_empirical_evidence_package(Path(pilot["generated_outputs"]["run_manifest_json"]).parent)

    assert package["run_id"] == "empirical-package-run"
    assert package["controlled_live_run_present"] is False
    assert package["live_api_used"] is False
    assert package["human_labels_present"] is False
    assert package["kappa_present"] is False
    assert package["measurement_validated_allowed"] is False
    assert package["allowed_empirical_claim_level"] == "not_empirical_validation"
    assert "missing_human_labels" in package["reason_codes"]
    assert "missing_kappa" in package["reason_codes"]
    assert "contamination_incomplete" in package["reason_codes"]


def test_no_live_run_is_not_empirical_validation():
    package = build_empirical_evidence_package(
        _mapping_source(
            live_pilot_summary={
                "run_id": "empirical-package-run",
                "mode": "dry_run",
                "live_api_used": False,
                "dispatch_count": 3,
                "case_artifact_count": 3,
            }
        )
    )

    assert package["controlled_live_run_present"] is False
    assert package["allowed_empirical_claim_level"] == "not_empirical_validation"
    assert package["measurement_validated_allowed"] is False
    assert "no_live_run" in package["reason_codes"]


def test_live_run_without_labels_denies_measurement_validated():
    package = build_empirical_evidence_package(_mapping_source())

    assert package["controlled_live_run_present"] is True
    assert package["allowed_empirical_claim_level"] == "controlled_live_pilot_only"
    assert package["measurement_validated_allowed"] is False
    assert "live_run_without_labels" in package["reason_codes"]
    assert "missing_human_labels" in package["reason_codes"]


def test_missing_kappa_denies_measurement_validated():
    completeness = {"labels_complete": True, "reason_codes": []}
    package = build_empirical_evidence_package(
        _mapping_source(
            human_label_completeness_report=completeness,
            kappa_report={
                "human_labels_present": True,
                "labels_complete": True,
                "kappa_present": False,
                "kappa_status": "kappa_missing",
                "macro_average_kappa": None,
                "reason_codes": ["missing_kappa"],
            },
        )
    )

    assert package["human_labels_present"] is True
    assert package["labels_complete"] is True
    assert package["kappa_present"] is False
    assert package["measurement_validated_allowed"] is False
    assert "missing_kappa" in package["reason_codes"]


def test_low_kappa_maps_to_weak_evidence_or_pilot_only():
    low_kappa = _kappa_report({"ann-a": [0, 0, 2, 2], "ann-b": [2, 2, 0, 0]})

    package = build_empirical_evidence_package(
        _mapping_source(
            human_label_completeness_report=low_kappa["completeness_report"],
            kappa_report=low_kappa,
        )
    )

    assert package["kappa_status"] == "pilot_only"
    assert package["allowed_empirical_claim_level"] == "pilot_only"
    assert package["measurement_validated_allowed"] is False
    assert "low_kappa" in package["reason_codes"]


def test_high_kappa_alone_still_denies_without_contamination_or_bridge():
    high_kappa = _kappa_report()

    package = build_empirical_evidence_package(
        _mapping_source(
            human_label_completeness_report=high_kappa["completeness_report"],
            kappa_report=high_kappa,
            contamination_report=_contamination_report(answer_key_exposure="unknown"),
            metric_bridge_freshness="missing",
        )
    )

    assert package["macro_average_kappa"] == 1.0
    assert package["kappa_status"] == "stronger_measurement_review_candidate"
    assert package["measurement_validated_allowed"] is False
    assert package["allowed_empirical_claim_level"] != "measurement_validated"
    assert "contamination_unknown" in package["reason_codes"]
    assert "missing_metric_bridge" in package["reason_codes"]


def test_contamination_failure_forces_pilot_only():
    high_kappa = _kappa_report()

    package = build_empirical_evidence_package(
        _mapping_source(
            human_label_completeness_report=high_kappa["completeness_report"],
            kappa_report=high_kappa,
            contamination_report=_contamination_report(leaked_labels="fail"),
            metric_bridge_freshness="fresh",
        )
    )

    assert package["contamination_status"] == "failed"
    assert package["allowed_empirical_claim_level"] == "pilot_only"
    assert package["measurement_validated_allowed"] is False
    assert "contamination_failed" in package["reason_codes"]


def test_stale_metric_bridge_denies_measurement_validated():
    high_kappa = _kappa_report()

    package = build_empirical_evidence_package(
        _mapping_source(
            human_label_completeness_report=high_kappa["completeness_report"],
            kappa_report=high_kappa,
            contamination_report=_contamination_report(),
            metric_bridge_freshness="stale",
        )
    )

    assert package["metric_bridge_freshness"] == "stale"
    assert package["allowed_empirical_claim_level"] == "operational_utility_only"
    assert package["measurement_validated_allowed"] is False
    assert "stale_metric_bridge" in package["reason_codes"]


def test_route_b_package_accepts_model_adjudicated_artifacts_without_human_gates():
    package = build_empirical_evidence_package(_route_b_source(metric_bridge_freshness="fresh"))

    assert package["route_type"] == "model_adjudicated"
    assert package["evaluation_route"] == "Route_B_model_adjudicated"
    assert package["llm_prelabels_present"] is True
    assert package["subagent_audit_present"] is True
    assert package["model_adjudicated_labels_present"] is True
    assert package["model_adjudicated_label_count"] == 8
    assert package["human_labels_present"] is False
    assert package["kappa_present"] is False
    assert package["human_human_kappa_established"] is False
    assert package["measurement_validated_allowed"] is False
    assert package["allowed_empirical_claim_level"] == "model_adjudicated_pilot_only"
    assert "model_adjudicated_labels_not_human_labels" in package["reason_codes"]
    assert "codex_adjudication_not_human_review" in package["reason_codes"]
    assert "measurement_validated_denied_for_route_b" in package["reason_codes"]


def test_route_b_contamination_failure_forces_pilot_only():
    package = build_empirical_evidence_package(
        _route_b_source(contamination_report=_contamination_report(leaked_labels="fail"))
    )

    assert package["contamination_status"] == "failed"
    assert package["allowed_empirical_claim_level"] == "pilot_only"
    assert package["measurement_validated_allowed"] is False
    assert "contamination_failed" in package["reason_codes"]


def test_route_b_missing_or_stale_bridge_never_allows_measurement_validation():
    missing = build_empirical_evidence_package(_route_b_source(metric_bridge_freshness="missing"))
    stale = build_empirical_evidence_package(_route_b_source(metric_bridge_freshness="stale"))

    assert missing["allowed_empirical_claim_level"] == "ambiguous"
    assert stale["allowed_empirical_claim_level"] == "operational_utility_only"
    assert missing["measurement_validated_allowed"] is False
    assert stale["measurement_validated_allowed"] is False
    assert "fresh_metric_bridge_required_for_stronger_claim" in missing["reason_codes"]
    assert "fresh_metric_bridge_required_for_stronger_claim" in stale["reason_codes"]


def test_route_b_high_quality_model_adjudication_still_denies_measurement_validated():
    package = build_empirical_evidence_package(
        _route_b_source(
            contamination_report=_contamination_report(),
            metric_bridge_freshness="fresh",
            model_adjudicated_label_summary={
                "model_adjudicated_labels_present": True,
                "measurement_validated_allowed": False,
                "allowed_claim_level": "model_adjudicated_pilot_only",
                "accepted_model_adjudicated_count": 8,
                "uncertain_count": 0,
                "rejected_or_blocking_warning_count": 0,
                "total_labels": 8,
            },
        )
    )

    assert package["model_adjudicated_labels_present"] is True
    assert package["allowed_empirical_claim_level"] == "model_adjudicated_pilot_only"
    assert package["measurement_validated_allowed"] is False
    assert "human_labels_not_required_for_route_b" in package["reason_codes"]
    assert "human_labels_missing_for_measurement_validation" in package["reason_codes"]
    assert "human_kappa_missing_for_measurement_validation" in package["reason_codes"]


def test_route_b_summary_markdown_states_model_adjudicated_boundary():
    package = build_empirical_evidence_package(_route_b_source())
    summary = format_empirical_evidence_summary_markdown(package)

    assert "Route B is fully automated/model-adjudicated" in summary
    assert "model_adjudicated_labels are not human_labels" in summary
    assert "Codex adjudication is not human review" in summary
    assert "Route B does not require human labels" in summary
    assert "Route B cannot claim measurement_validated" in summary


def test_route_b_package_reads_model_adjudicated_files_from_output_dir(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "route-b-source"
    output_dir.mkdir()
    (output_dir / "llm_prelabels.jsonl").write_text(
        json.dumps({"case_id": "case-001"}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "subagent_audit_report.json").write_text(
        json.dumps({"measurement_validated_allowed": False}, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "model_adjudicated_labels.jsonl").write_text(
        json.dumps({"case_id": "case-001", "counts_as_human_label": False}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "codex_adjudication_report.json").write_text(
        json.dumps({"total_labels": 1, "measurement_validated_allowed": False}, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "model_adjudicated_label_summary.json").write_text(
        json.dumps(
            {
                "total_labels": 1,
                "model_adjudicated_labels_present": True,
                "human_labels_present": False,
                "kappa_present": False,
                "measurement_validated_allowed": False,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    package = build_empirical_evidence_package(output_dir)

    assert package["evaluation_route"] == "Route_B_model_adjudicated"
    assert package["llm_prelabels_present"] is True
    assert package["llm_prelabel_count"] == 1
    assert package["subagent_audit_present"] is True
    assert package["codex_adjudication_report_present"] is True
    assert package["model_adjudicated_labels_present"] is True
    assert package["model_adjudicated_label_count"] == 1
    assert package["model_adjudicated_label_summary_present"] is True
    assert package["human_labels_present"] is False
    assert package["kappa_present"] is False
    assert package["measurement_validated_allowed"] is False


def test_route_b_json_outputs_are_deterministic(workspace_tmp_dir):
    package = build_empirical_evidence_package(_route_b_source())

    first = write_empirical_evidence_package(workspace_tmp_dir / "route-b-first", package)
    second = write_empirical_evidence_package(workspace_tmp_dir / "route-b-second", package)

    for key in (
        "empirical_evidence_manifest_json",
        "empirical_claim_gate_report_json",
        "empirical_evidence_summary_markdown",
    ):
        assert _read(first[key]) == _read(second[key])
    manifest = _json(first["empirical_evidence_manifest_json"])
    assert manifest["route_type"] == "model_adjudicated"
    assert manifest["human_labels_present"] is False
    assert manifest["kappa_present"] is False


def test_complete_favorable_evidence_produces_candidate_not_default_validation():
    high_kappa = _kappa_report()

    package = build_empirical_evidence_package(
        _mapping_source(
            human_label_completeness_report=high_kappa["completeness_report"],
            kappa_report=high_kappa,
            contamination_report=_contamination_report(),
            metric_bridge_freshness="fresh",
            artifact_completeness_status="complete",
            claim_gate_allows_measurement_validated=False,
        )
    )

    assert package["allowed_empirical_claim_level"] == "measurement_validated_candidate"
    assert package["measurement_validated_allowed"] is False
    assert "claim_gate_allow_required" in package["reason_codes"]
    assert "measurement_validated" in package["denied_claims"]


def test_explicit_claim_gate_allow_is_required_for_measurement_validated():
    high_kappa = _kappa_report()

    package = build_empirical_evidence_package(
        _mapping_source(
            human_label_completeness_report=high_kappa["completeness_report"],
            kappa_report=high_kappa,
            contamination_report=_contamination_report(),
            metric_bridge_freshness="fresh",
            artifact_completeness_status="complete",
            claim_gate_allows_measurement_validated=True,
            p04_status="ACCEPT",
            p09_status="BLOCKED_OPERATOR_REQUIRED",
        )
    )

    assert package["allowed_empirical_claim_level"] == "measurement_validated_candidate"
    assert package["measurement_validated_allowed"] is False
    assert "operator_required_phase" in package["reason_codes"]


def test_reason_codes_are_stable_ordered():
    package = build_empirical_evidence_package(
        _mapping_source(
            contamination_report=_contamination_report(leaked_labels="fail"),
            metric_bridge_freshness="missing",
        )
    )

    assert package["reason_codes"] == sorted(
        package["reason_codes"],
        key=package["reason_code_order"].index,
    )


def test_writers_are_deterministic(workspace_tmp_dir):
    high_kappa = _kappa_report()
    package = build_empirical_evidence_package(
        _mapping_source(
            human_label_completeness_report=high_kappa["completeness_report"],
            kappa_report=high_kappa,
            contamination_report=_contamination_report(),
            metric_bridge_freshness="fresh",
        )
    )

    first = write_empirical_evidence_package(workspace_tmp_dir / "first", package)
    second = write_empirical_evidence_package(workspace_tmp_dir / "second", package)

    for key in (
        "empirical_evidence_manifest_json",
        "live_pilot_summary_json",
        "human_label_completeness_report_json",
        "kappa_report_json",
        "contamination_report_json",
        "empirical_claim_gate_report_json",
        "empirical_evidence_summary_markdown",
    ):
        assert _read(first[key]) == _read(second[key])
    assert _json(first["empirical_evidence_manifest_json"])["measurement_validated_allowed"] is False
    assert "High kappa alone is not measurement validation" in format_empirical_evidence_summary_markdown(package)


def test_no_live_api_or_external_sdk_is_used(monkeypatch, workspace_tmp_dir):
    before = set(sys.modules)
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("empirical package must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    package = build_empirical_evidence_package(_mapping_source())
    outputs = write_empirical_evidence_package(workspace_tmp_dir / "package", package)
    imported = set(sys.modules) - before

    assert Path(outputs["empirical_evidence_manifest_json"]).exists()
    assert {"openai", "anthropic", "requests", "httpx", "numpy", "pandas", "sklearn"}.isdisjoint(imported)
