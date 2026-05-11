from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from cps.experiments.extraction_audit import run_extraction_audit_pilot
from tests.conftest import assert_importing_modules_does_not_load_forbidden_sdks


REQUIRED_FILES = (
    "extraction_audit_cases.jsonl",
    "extraction_audit_findings.jsonl",
    "extraction_audit_labels.jsonl",
    "extraction_audit_defects.csv",
    "extraction_audit_summary.json",
    "extraction_audit_report.md",
    "extraction_audit_manifest.json",
    "extraction_ground_truth_findings.jsonl",
    "stratum_completeness_report.csv",
    "value_weighted_loss.csv",
    "extraction_claim_gate_report.json",
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _artifact_text(output_dir: Path) -> str:
    return "\n".join((output_dir / name).read_text(encoding="utf-8") for name in REQUIRED_FILES)


def test_p49_generates_fixture_extraction_audit_schema_and_artifacts(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "p49"

    report = run_extraction_audit_pilot(
        config_path="configs/runs/extraction-audit-pilot-v12.json",
        output_dir=output_dir,
    )

    assert report["status"] == "completed"
    assert report["case_count"] == 6
    assert report["data_source_kind"] == "fixture"
    for name in REQUIRED_FILES:
        assert (output_dir / name).exists()

    cases = _jsonl_rows(output_dir / "extraction_audit_cases.jsonl")
    assert [case["case_family"] for case in cases] == [
        "clean_extraction",
        "contradictory_source",
        "duplicate_over_merged",
        "missing_critical_finding",
        "provenance_missing",
        "unsupported_hallucinated",
    ]
    for case in cases:
        assert {
            "case_id",
            "case_family",
            "source_records",
            "expected_critical_findings",
            "candidate_pool_hash",
            "data_source_kind",
            "paper_evidence_eligible",
            "measurement_validation_claim",
            "live_api_used",
        }.issubset(case)
        assert case["data_source_kind"] == "fixture"
        assert case["paper_evidence_eligible"] is False
        assert case["measurement_validation_claim"] is False
        assert case["live_api_used"] is False
        assert case["candidate_pool_hash"]

    findings = _jsonl_rows(output_dir / "extraction_audit_findings.jsonl")
    assert findings
    for finding in findings:
        assert {
            "finding_id",
            "finding_text",
            "finding_type",
            "source_record_ids",
            "source_span_refs",
            "provenance_refs",
            "candidate_pool_hash",
            "finding_hash",
            "support_status",
            "extraction_defects",
        }.issubset(finding)
        assert finding["finding_hash"]
        if finding["support_status"] == "supported":
            assert finding["source_record_ids"]
            assert finding["source_span_refs"]
            assert finding["provenance_refs"]


def test_p49_hashes_are_deterministic_and_candidate_pool_hash_links_findings(workspace_tmp_dir):
    first = workspace_tmp_dir / "first"
    second = workspace_tmp_dir / "second"
    run_extraction_audit_pilot(output_dir=first)
    run_extraction_audit_pilot(output_dir=second)

    first_findings = _jsonl_rows(first / "extraction_audit_findings.jsonl")
    second_findings = _jsonl_rows(second / "extraction_audit_findings.jsonl")
    assert [(row["finding_id"], row["finding_hash"], row["candidate_pool_hash"]) for row in first_findings] == [
        (row["finding_id"], row["finding_hash"], row["candidate_pool_hash"]) for row in second_findings
    ]

    cases_by_id = {row["case_id"]: row for row in _jsonl_rows(first / "extraction_audit_cases.jsonl")}
    for finding in first_findings:
        assert finding["candidate_pool_hash"] == cases_by_id[finding["case_id"]]["candidate_pool_hash"]


def test_p49_flags_unsupported_missing_provenance_duplicate_overmerged_and_contradictory_defects(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "defects"
    run_extraction_audit_pilot(output_dir=output_dir)

    defect_rows = _csv_rows(output_dir / "extraction_audit_defects.csv")
    reason_codes = {row["reason_code"] for row in defect_rows}
    assert {
        "unsupported_finding",
        "missing_critical_finding",
        "provenance_missing",
        "source_span_missing",
        "duplicate_finding",
        "over_merged_finding",
        "contradictory_sources",
    }.issubset(reason_codes)

    unsupported = [
        row
        for row in _jsonl_rows(output_dir / "extraction_audit_findings.jsonl")
        if row["support_status"] == "unsupported"
    ]
    assert unsupported
    assert all("unsupported_finding" in row["extraction_defects"] for row in unsupported)

    labels = _jsonl_rows(output_dir / "extraction_audit_labels.jsonl")
    missing_labels = [row for row in labels if row["extraction_outcome"] == "missing"]
    assert missing_labels
    assert all("missing_critical_finding" in row["defect_reason_codes"] for row in missing_labels)


def test_p49_claim_gate_remains_fixture_only_and_conservative(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "claims"
    run_extraction_audit_pilot(output_dir=output_dir)

    claim = _json(output_dir / "extraction_claim_gate_report.json")
    assert claim["data_source_kind"] == "fixture"
    assert claim["audit_scope"] == "extraction_audit_pilot"
    assert claim["evidence_scope"] == "fixture_extraction_audit_only"
    assert claim["paper_evidence_eligible"] is False
    assert claim["measurement_validation_claim"] is False
    assert claim["metric_claim_level"] == "operational_utility_only"
    assert claim["calibrated_proxy_supported"] is False
    assert claim["vinfo_proxy_supported"] is False
    assert claim["live_api_used"] is False
    assert claim["selector_regime_claim_upgraded"] is False

    combined = _artifact_text(output_dir)
    assert '"measurement_validation_claim": true' not in combined
    assert '"paper_evidence_eligible": true' not in combined
    assert '"calibrated_proxy_supported": true' not in combined
    assert '"vinfo_proxy_supported": true' not in combined
    assert "measurement_validated" not in combined
    assert "Vinfo_proxy_certified" not in combined
    assert "greedy_valid" not in combined
    assert '"escalate"' not in combined


def test_p49_artifacts_are_byte_stable_and_path_clean(workspace_tmp_dir):
    first = workspace_tmp_dir / "first"
    second = workspace_tmp_dir / "second"

    run_extraction_audit_pilot(output_dir=first)
    run_extraction_audit_pilot(output_dir=second)

    uuid_pattern = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
    timestamp_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:")
    for name in REQUIRED_FILES:
        assert (first / name).read_bytes() == (second / name).read_bytes()
        text = (first / name).read_text(encoding="utf-8")
        assert ":\\" not in text
        assert "file://" not in text
        assert not uuid_pattern.search(text)
        assert not timestamp_pattern.search(text)


def test_p49_import_does_not_load_live_api_or_external_sdks():
    assert_importing_modules_does_not_load_forbidden_sdks(["cps.experiments.extraction_audit"])
