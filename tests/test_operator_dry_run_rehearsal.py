from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

from cps.experiments.operator_dry_run_rehearsal import (
    build_operator_dry_run_rehearsal,
    format_operator_dry_run_rehearsal_markdown,
)


EXPECTED_TOP_LEVEL_FILES = {
    "dry_run_manifest.json",
    "pilot_summary.json",
    "human_labels_template.csv",
    "human_labels_template.jsonl",
    "human_label_completeness_report.json",
    "kappa_report.json",
    "contamination_report.json",
    "empirical_evidence_manifest.json",
    "empirical_claim_gate_report.json",
    "empirical_evidence_summary.md",
    "rehearsal_summary.json",
    "rehearsal_summary.md",
}


def _read(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _json(path: str | Path) -> dict:
    return json.loads(_read(path))


def test_dry_run_rehearsal_creates_expected_files(workspace_tmp_dir):
    result = build_operator_dry_run_rehearsal(workspace_tmp_dir / "rehearsal")

    output_root = Path(result["output_root"])
    for filename in EXPECTED_TOP_LEVEL_FILES:
        assert (output_root / filename).exists(), filename
    assert (output_root / "case_artifacts" / "deepseek_v4_flash").is_dir()
    assert (output_root / "case_artifacts" / "deepseek_v4_pro").is_dir()
    assert (output_root / "case_artifacts" / "deepseek_v4_flash" / "cases" / "case-001").is_dir()
    assert (output_root / "case_artifacts" / "deepseek_v4_flash" / "cases" / "case-002").is_dir()
    assert (output_root / "case_artifacts" / "deepseek_v4_pro" / "cases" / "case-001").is_dir()


def test_deepseek_aliases_are_dry_run_model_conditions_only(workspace_tmp_dir):
    result = build_operator_dry_run_rehearsal(workspace_tmp_dir / "rehearsal")
    manifest = _json(result["generated_outputs"]["dry_run_manifest_json"])

    aliases = [model["model_alias"] for model in manifest["models"]]
    assert aliases == ["deepseek_v4_flash", "deepseek_v4_pro"]
    assert {model["mode"] for model in manifest["models"]} == {"dry_run"}
    assert {model["live_api_used"] for model in manifest["models"]} == {False}
    assert all(str(model["model_name"]).startswith("<dry_run_placeholder_") for model in manifest["models"])
    assert "deepseek-chat" not in json.dumps(manifest)
    assert "deepseek-reasoner" not in json.dumps(manifest)


def test_no_live_or_external_runtime_is_used(workspace_tmp_dir):
    result = build_operator_dry_run_rehearsal(workspace_tmp_dir / "rehearsal")
    manifest = result["dry_run_manifest"]
    empirical = result["empirical_evidence_package"]

    assert manifest["live_api_used"] is False
    assert manifest["external_runtime_used"] is False
    assert empirical["live_api_used"] is False
    assert empirical["external_runtime_used"] is False
    assert empirical["controlled_live_run_present"] is False


def test_human_labels_and_kappa_are_not_fabricated(workspace_tmp_dir):
    result = build_operator_dry_run_rehearsal(workspace_tmp_dir / "rehearsal")
    output_root = Path(result["output_root"])
    template_csv = _read(output_root / "human_labels_template.csv")
    template_jsonl = _read(output_root / "human_labels_template.jsonl")
    kappa = _json(output_root / "kappa_report.json")
    completeness = _json(output_root / "human_label_completeness_report.json")

    assert ",0," not in template_csv
    assert ",1," not in template_csv
    assert ",2," not in template_csv
    assert '"label": ""' in template_jsonl
    assert kappa["human_labels_present"] is False
    assert kappa["labels_complete"] is False
    assert kappa["kappa_present"] is False
    assert kappa["measurement_validated_allowed"] is False
    assert completeness["labels_complete"] is False


def test_contamination_pass_is_not_fabricated(workspace_tmp_dir):
    result = build_operator_dry_run_rehearsal(workspace_tmp_dir / "rehearsal")
    contamination = _json(result["generated_outputs"]["contamination_report_json"])

    assert contamination["contamination_status"] == "unknown"
    assert contamination["contamination_passed"] is False
    assert contamination["measurement_validated_allowed"] is False
    assert "contamination_unknown" in contamination["reason_codes"]


def test_missing_evidence_denies_measurement_validated(workspace_tmp_dir):
    result = build_operator_dry_run_rehearsal(workspace_tmp_dir / "rehearsal")
    manifest = result["dry_run_manifest"]
    empirical = result["empirical_evidence_package"]

    assert manifest["measurement_validated_allowed"] is False
    assert empirical["measurement_validated_allowed"] is False
    assert empirical["allowed_empirical_claim_level"] == "not_empirical_validation"
    assert "measurement_validated" in empirical["denied_claims"]
    assert "missing_human_labels" in empirical["reason_codes"]
    assert "missing_kappa" in empirical["reason_codes"]
    assert "contamination_unknown" in empirical["reason_codes"]
    assert "missing_metric_bridge" in empirical["reason_codes"]


def test_outputs_are_deterministic_across_repeated_runs(workspace_tmp_dir):
    first = build_operator_dry_run_rehearsal(workspace_tmp_dir / "first")
    second = build_operator_dry_run_rehearsal(workspace_tmp_dir / "second")

    for key in (
        "dry_run_manifest_json",
        "pilot_summary_json",
        "human_labels_template_csv",
        "human_labels_template_jsonl",
        "human_label_completeness_report_json",
        "kappa_report_json",
        "contamination_report_json",
        "empirical_evidence_manifest_json",
        "empirical_claim_gate_report_json",
        "empirical_evidence_summary_markdown",
        "rehearsal_summary_json",
        "rehearsal_summary_markdown",
    ):
        assert _read(first["generated_outputs"][key]) == _read(second["generated_outputs"][key]), key


def test_reason_code_ordering_and_operator_status_are_stable(workspace_tmp_dir):
    result = build_operator_dry_run_rehearsal(workspace_tmp_dir / "rehearsal")
    manifest = result["dry_run_manifest"]
    empirical = result["empirical_evidence_package"]
    summary = _read(result["generated_outputs"]["rehearsal_summary_markdown"])

    assert empirical["reason_codes"] == sorted(
        empirical["reason_codes"],
        key=empirical["reason_code_order"].index,
    )
    assert manifest["p04_status"] == "deferred/operator-required"
    assert manifest["p09_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert "P04 remains deferred/operator-required" in summary
    assert "P09 remains BLOCKED_OPERATOR_REQUIRED" in summary


def test_markdown_summary_is_deterministic_and_claim_bounded(workspace_tmp_dir):
    result = build_operator_dry_run_rehearsal(workspace_tmp_dir / "rehearsal")
    markdown = format_operator_dry_run_rehearsal_markdown(result["rehearsal_summary"])

    assert markdown == _read(result["generated_outputs"]["rehearsal_summary_markdown"])
    assert "P30 is a dry-run rehearsal only" in markdown
    assert "No live API was called" in markdown
    assert "DeepSeek V4 Flash / Pro are dry-run model conditions only" in markdown
    assert "No human labels were fabricated" in markdown
    assert "No kappa was fabricated" in markdown
    assert "No contamination pass was fabricated" in markdown
    assert "measurement_validated is denied" in markdown


def test_no_network_reference_access_or_external_sdk_import(monkeypatch, workspace_tmp_dir):
    before = set(sys.modules)
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("operator dry-run rehearsal must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    result = build_operator_dry_run_rehearsal(workspace_tmp_dir / "rehearsal")
    imported = set(sys.modules) - before

    assert Path(result["generated_outputs"]["dry_run_manifest_json"]).exists()
    assert {"openai", "anthropic", "requests", "httpx", "numpy", "pandas", "sklearn"}.isdisjoint(imported)
