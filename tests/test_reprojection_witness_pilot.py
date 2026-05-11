from __future__ import annotations

import csv
import json
import re
from dataclasses import replace
from pathlib import Path

from cps.experiments.reprojection_witness import build_reprojection_witness
from cps.experiments.reprojection_witness import default_reprojection_cases
from cps.experiments.reprojection_witness import run_reprojection_witness_pilot
from tests.conftest import assert_importing_modules_does_not_load_forbidden_sdks


REQUIRED_FILES = (
    "reprojection_cases.jsonl",
    "reprojection_witnesses.jsonl",
    "reprojection_actions.csv",
    "reprojection_trigger_counts.csv",
    "reprojection_claim_gate_report.json",
    "reprojection_summary.json",
    "reprojection_manifest.json",
    "reprojection_report.md",
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


def test_p50_generates_fixture_reprojection_schema_and_artifacts(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "p50"

    report = run_reprojection_witness_pilot(
        config_path="configs/runs/reprojection-witness-pilot-v12.json",
        output_dir=output_dir,
    )

    assert report["status"] == "completed"
    assert report["case_count"] == 8
    assert report["data_source_kind"] == "fixture"
    for name in REQUIRED_FILES:
        assert (output_dir / name).exists()

    cases = _jsonl_rows(output_dir / "reprojection_cases.jsonl")
    assert [case["case_family"] for case in cases] == [
        "ambiguous_selector",
        "budget_violation",
        "candidate_pool_mismatch",
        "clean_no_reprojection",
        "identity_mismatch",
        "missing_critical_finding",
        "pairwise_escalation",
        "unsupported_finding",
    ]

    witnesses = _jsonl_rows(output_dir / "reprojection_witnesses.jsonl")
    assert len(witnesses) == 8
    for witness in witnesses:
        assert {
            "witness_id",
            "run_id",
            "dispatch_id",
            "agent_id",
            "round_id",
            "candidate_pool_hash",
            "initial_projection_plan_hash",
            "initial_materialized_context_hash",
            "reprojected_projection_plan_hash",
            "reprojected_materialized_context_hash",
            "trigger_type",
            "trigger_reason_codes",
            "initial_selector_regime_label",
            "final_selector_regime_label",
            "metric_claim_level",
            "evidence_scope",
            "reprojection_action",
            "budget_status",
            "budget_overrun_tokens",
            "data_source_kind",
            "paper_evidence_eligible",
            "measurement_validation_claim",
        }.issubset(witness)
        assert witness["data_source_kind"] == "fixture"
        assert witness["paper_evidence_eligible"] is False
        assert witness["measurement_validation_claim"] is False


def test_p50_hashes_and_witness_ids_are_deterministic(workspace_tmp_dir):
    first = workspace_tmp_dir / "first"
    second = workspace_tmp_dir / "second"
    run_reprojection_witness_pilot(output_dir=first)
    run_reprojection_witness_pilot(output_dir=second)

    first_witnesses = _jsonl_rows(first / "reprojection_witnesses.jsonl")
    second_witnesses = _jsonl_rows(second / "reprojection_witnesses.jsonl")
    fields = [
        "case_id",
        "witness_id",
        "initial_projection_plan_hash",
        "initial_materialized_context_hash",
        "reprojected_projection_plan_hash",
        "reprojected_materialized_context_hash",
        "context_diff_hash",
    ]
    assert [{field: row[field] for field in fields} for row in first_witnesses] == [
        {field: row[field] for field in fields} for row in second_witnesses
    ]


def test_p50_identity_missing_or_mismatch_fails_closed():
    case = default_reprojection_cases()[0]
    missing = build_reprojection_witness(replace(case, run_id=""))
    assert missing.replay_safe is False
    assert missing.metric_claim_level == "ambiguous_metric"
    assert "missing_identity_run_id" in missing.trigger_reason_codes
    assert missing.paper_evidence_eligible is False
    assert missing.measurement_validation_claim is False
    assert missing.vinfo_proxy_supported is False
    assert missing.calibrated_proxy_supported is False

    mismatch_case = [case for case in default_reprojection_cases() if case.case_family == "identity_mismatch"][0]
    mismatch = build_reprojection_witness(mismatch_case)
    assert mismatch.replay_safe is False
    assert mismatch.metric_claim_level == "ambiguous_metric"
    assert "identity_mismatch_run_id" in mismatch.trigger_reason_codes
    assert mismatch.paper_evidence_eligible is False
    assert mismatch.measurement_validation_claim is False
    assert mismatch.vinfo_proxy_supported is False
    assert mismatch.calibrated_proxy_supported is False


def test_p50_candidate_pool_mismatch_and_budget_statuses_fail_safe(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "p50_safety"
    run_reprojection_witness_pilot(output_dir=output_dir)
    witnesses = {row["case_family"]: row for row in _jsonl_rows(output_dir / "reprojection_witnesses.jsonl")}

    mismatch = witnesses["candidate_pool_mismatch"]
    assert mismatch["replay_safe"] is False
    assert mismatch["metric_claim_level"] == "ambiguous_metric"
    assert "candidate_pool_hash_mismatch" in mismatch["trigger_reason_codes"]
    assert mismatch["paper_evidence_eligible"] is False
    assert mismatch["vinfo_proxy_supported"] is False
    assert mismatch["calibrated_proxy_supported"] is False

    within_budget = witnesses["pairwise_escalation"]
    assert within_budget["budget_status"] == "within_budget"
    assert within_budget["budget_overrun_tokens"] == 0

    over_budget = witnesses["budget_violation"]
    assert over_budget["budget_status"] == "over_budget_non_comparable"
    assert over_budget["budget_overrun_tokens"] > 0
    assert over_budget["budget_fair_comparable"] is False
    assert over_budget["paper_evidence_eligible"] is False


def test_p50_trigger_and_action_outputs_are_deterministic(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "p50_actions"
    run_reprojection_witness_pilot(output_dir=output_dir)

    action_rows = _csv_rows(output_dir / "reprojection_actions.csv")
    trigger_rows = _csv_rows(output_dir / "reprojection_trigger_counts.csv")
    assert action_rows == sorted(action_rows, key=lambda row: (row["case_id"], row["reprojection_action"]))
    assert trigger_rows == sorted(trigger_rows, key=lambda row: row["trigger_type"])
    assert {row["reprojection_action"] for row in action_rows} >= {
        "abstain_no_safe_reprojection",
        "add_missing_finding",
        "remove_unsupported_finding",
        "compress_redundant_context",
        "downgrade_to_ambiguous",
    }


def test_p50_claim_gate_remains_fixture_only_and_does_not_upgrade_prior_claims(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "p50_claims"
    run_reprojection_witness_pilot(output_dir=output_dir)

    claim = _json(output_dir / "reprojection_claim_gate_report.json")
    assert claim["data_source_kind"] == "fixture"
    assert claim["audit_scope"] == "reprojection_witness_pilot"
    assert claim["evidence_scope"] == "fixture_reprojection_witness_only"
    assert claim["paper_evidence_eligible"] is False
    assert claim["measurement_validation_claim"] is False
    assert claim["live_api_used"] is False
    assert claim["calibrated_proxy_supported"] is False
    assert claim["vinfo_proxy_supported"] is False
    assert claim["p47_claim_upgraded"] is False
    assert claim["p48_claim_upgraded"] is False
    assert claim["p49_claim_upgraded"] is False

    combined = _artifact_text(output_dir)
    assert '"measurement_validation_claim": true' not in combined
    assert '"paper_evidence_eligible": true' not in combined
    assert '"calibrated_proxy_supported": true' not in combined
    assert '"vinfo_proxy_supported": true' not in combined
    assert "measurement_validated" not in combined
    assert "Vinfo_proxy_certified" not in combined
    assert "greedy_valid" not in combined
    assert '"escalate"' not in combined


def test_p50_artifacts_are_byte_stable_and_path_clean(workspace_tmp_dir):
    first = workspace_tmp_dir / "first"
    second = workspace_tmp_dir / "second"

    run_reprojection_witness_pilot(output_dir=first)
    run_reprojection_witness_pilot(output_dir=second)

    uuid_pattern = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
    timestamp_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:")
    for name in REQUIRED_FILES:
        assert (first / name).read_bytes() == (second / name).read_bytes()
        text = (first / name).read_text(encoding="utf-8")
        assert ":\\" not in text
        assert "file://" not in text
        assert not uuid_pattern.search(text)
        assert not timestamp_pattern.search(text)


def test_p50_import_does_not_load_live_api_or_external_sdks():
    assert_importing_modules_does_not_load_forbidden_sdks(["cps.experiments.reprojection_witness"])
