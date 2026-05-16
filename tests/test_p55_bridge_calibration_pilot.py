from __future__ import annotations

import json
import re
from pathlib import Path

from conftest import assert_importing_modules_does_not_load_forbidden_sdks
from cps.experiments.bridge_calibration_pilot import (
    OUTPUT_ARTIFACTS,
    ROW_OUTPUT_ARTIFACTS,
    detect_input_file_status,
    evaluate_bridge_fit,
    run_p55_bridge_calibration_pilot,
    validate_p55_rows,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "runs" / "bridge-calibration-evidence-packet-selection-microtask-v1-p55.json"
CONTRACT_PATH = ROOT / "docs" / "templates" / "diagnostic-threshold-contract-template.json"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _config(workspace_tmp_dir: Path, input_path: Path, output_dir: Path) -> Path:
    payload = _json(CONFIG_PATH)
    payload["input_rows_path"] = str(input_path)
    payload["output_dir"] = str(output_dir)
    return _write_json(workspace_tmp_dir / "p55-config.json", payload)


def _base_row(index: int, **overrides) -> dict:
    delta_logloss = [0.10, 0.20, 0.30, 0.11, 0.21, 0.31][index - 1]
    row = {
        "agent_id": "agent-p55",
        "block_A_ids": [f"packet-{index}", f"packet-{index + 10}"],
        "block_size": 2,
        "bridge_contract_id": "diagnostic_threshold_contract_v12_template",
        "bridge_witness_status": "fresh",
        "candidate_pool_hash": "candidate-pool-hash-p55",
        "candidate_slice_band": "top_8_candidate_packets_fixed_before_projection",
        "context_L_hash": f"context-hash-{index}",
        "contamination_status": "pass",
        "data_source_kind": "operator_imported_rows",
        "decoding_policy": "deterministic_logloss_scoring_no_generation",
        "delta_logloss": delta_logloss,
        "delta_utility": delta_logloss * 2.0,
        "dispatch_id": "dispatch-p55",
        "drift_status": "fresh",
        "effective_sample_size": 1,
        "logloss_measurement_version": "fixed_model_target_logloss_for_declared_answer",
        "materialization_policy": "fixed_order_evidence_packet_v1",
        "model_tier": "fixed_evaluated_model_tier",
        "operator_approval_ref": "route_a_operator_imported_rows",
        "projection_hash": f"projection-hash-{index}",
        "replicate_count": 1,
        "residual_stability_group": "group-a" if index in {4, 6} else "group-b",
        "round_id": "round-p55",
        "run_id": "run-p55",
        "split": "dev" if index <= 3 else "heldout",
        "stratum_id": "evidence_packet_selection_microtask_v1",
        "target_evidence": f"answer-evidence-{index}",
        "target_type": "forced_choice_or_exact_field",
        "task_family": "evidence_packet_selection_microtask_v1",
        "utility_metric_version": "decomposable_answer_correctness_v1",
    }
    row.update(overrides)
    return row


def _rows(**common_overrides) -> list[dict]:
    return [_base_row(index, **common_overrides) for index in range(1, 7)]


def _run(workspace_tmp_dir: Path, rows: list[dict] | None):
    input_path = workspace_tmp_dir / "rows.jsonl"
    output_dir = workspace_tmp_dir / "out"
    if rows is not None:
        _write_jsonl(input_path, rows)
    result = run_p55_bridge_calibration_pilot(
        config_path=_config(workspace_tmp_dir, input_path, output_dir),
        contract_path=CONTRACT_PATH,
    )
    return output_dir, result


def _assert_no_row_gate(output_dir: Path, result: dict, *, input_file_status: str) -> None:
    assert result["input_file_status"] == input_file_status
    assert result["input_rows_present"] is False
    assert result["pilot_status"] == "blocked_operator_required"
    assert result["claim_gate_status"] == "failed_closed_no_rows"
    assert result["metric_claim_level"] == "ambiguous_metric"
    assert result["paper_evidence_eligible"] is False
    assert sorted(path.name for path in output_dir.iterdir()) == sorted(OUTPUT_ARTIFACTS)

    manifest = _json(output_dir / "manifest.json")
    report = _json(output_dir / "claim_gate_report.json")
    gate = report["claim_gate_result"]
    assert manifest["input_file_status"] == input_file_status
    assert manifest["claim_gate_result"] == "failed_closed_no_rows"
    assert manifest["blocked_operator_required"] is True
    assert manifest["requires_operator"] is True
    assert manifest["next_phase_allowed"] is False
    assert manifest["review_ceiling"] == "none"
    assert manifest["rows_imported"] == 0
    assert manifest["rows_validated"] == 0
    assert gate["input_file_status"] == input_file_status
    assert gate["blocked_operator_required"] is True
    assert gate["requires_operator"] is True
    assert gate["next_phase_allowed"] is False
    assert gate["review_ceiling"] == "none"
    assert gate["rows_imported"] == 0
    assert gate["rows_validated"] == 0
    assert gate["measurement_validation_claim"] is False
    assert gate["vinfo_proxy_supported_allowed"] is False
    assert gate["calibrated_proxy_supported_allowed"] is False
    assert report["paper_evidence_eligible"] is False
    assert report["bridge_report"]["fit_metrics_computed"] is False
    assert report["bridge_report"]["c_s"] is None
    assert report["bridge_report"]["zeta_s"] is None
    assert "no_operator_imported_rows" in gate["reason_codes"]
    assert "operator_rows_required" in gate["reason_codes"]


def test_absent_operator_rows_writes_blocked_fail_closed_report(workspace_tmp_dir):
    output_dir, result = _run(workspace_tmp_dir, rows=None)

    _assert_no_row_gate(output_dir, result, input_file_status="absent")


def test_empty_operator_input_file_uses_no_row_blocked_semantics(workspace_tmp_dir):
    input_path = workspace_tmp_dir / "rows.jsonl"
    output_dir = workspace_tmp_dir / "out"
    input_path.write_text("", encoding="utf-8")

    result = run_p55_bridge_calibration_pilot(
        config_path=_config(workspace_tmp_dir, input_path, output_dir),
        contract_path=CONTRACT_PATH,
    )

    _assert_no_row_gate(output_dir, result, input_file_status="empty")


def test_blank_and_comment_only_operator_input_file_uses_no_row_blocked_semantics(workspace_tmp_dir):
    input_path = workspace_tmp_dir / "rows.jsonl"
    output_dir = workspace_tmp_dir / "out"
    input_path.write_text("\n# operator rows not supplied\n// no claim-bearing payload\n  \n", encoding="utf-8")

    assert detect_input_file_status(input_path) == "empty"
    result = run_p55_bridge_calibration_pilot(
        config_path=_config(workspace_tmp_dir, input_path, output_dir),
        contract_path=CONTRACT_PATH,
    )

    _assert_no_row_gate(output_dir, result, input_file_status="empty")


def test_empty_operator_input_canonical_artifacts_are_deterministic_and_neutral(workspace_tmp_dir):
    input_path = workspace_tmp_dir / "rows.jsonl"
    first_output = workspace_tmp_dir / "first"
    second_output = workspace_tmp_dir / "second"
    input_path.write_text("", encoding="utf-8")
    config_path = _config(workspace_tmp_dir, input_path, workspace_tmp_dir / "ignored")

    run_p55_bridge_calibration_pilot(config_path=config_path, output_dir=first_output, contract_path=CONTRACT_PATH)
    run_p55_bridge_calibration_pilot(config_path=config_path, output_dir=second_output, contract_path=CONTRACT_PATH)

    for artifact in OUTPUT_ARTIFACTS:
        first_text = (first_output / artifact).read_text(encoding="utf-8")
        second_text = (second_output / artifact).read_text(encoding="utf-8")
        assert first_text == second_text

    combined = "\n".join((first_output / artifact).read_text(encoding="utf-8") for artifact in OUTPUT_ARTIFACTS)
    assert not re.search(r"\b20\d{2}-\d{2}-\d{2}(?:t|\s)\d{2}:\d{2}", combined, re.I)
    assert not re.search(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", combined, re.I)
    assert ":\\" not in combined
    assert "/home/" not in combined
    assert "/mnt/" not in combined
    assert "api" + "_key" not in combined.lower()
    assert "s" + "ecret" not in combined.lower()


def test_valid_imported_rows_produce_deterministic_canonical_report(workspace_tmp_dir):
    input_path = _write_jsonl(workspace_tmp_dir / "rows.jsonl", _rows())
    config_path = _config(workspace_tmp_dir, input_path, workspace_tmp_dir / "ignored")
    first = workspace_tmp_dir / "first"
    second = workspace_tmp_dir / "second"

    first_result = run_p55_bridge_calibration_pilot(
        config_path=config_path,
        output_dir=first,
        contract_path=CONTRACT_PATH,
    )
    second_result = run_p55_bridge_calibration_pilot(
        config_path=config_path,
        output_dir=second,
        contract_path=CONTRACT_PATH,
    )

    assert first_result["metric_claim_level"] == "calibrated_proxy_supported"
    assert first_result["claim_gate_status"] == "calibrated_proxy_supported_exact_stratum_only"
    assert sorted(path.name for path in first.iterdir()) == sorted(OUTPUT_ARTIFACTS + ROW_OUTPUT_ARTIFACTS)
    for artifact in OUTPUT_ARTIFACTS + ROW_OUTPUT_ARTIFACTS:
        assert (first / artifact).read_text(encoding="utf-8") == (second / artifact).read_text(encoding="utf-8")


def test_missing_required_row_field_fails_closed(workspace_tmp_dir):
    rows = _rows()
    del rows[0]["target_evidence"]
    output_dir, result = _run(workspace_tmp_dir, rows)

    report = _json(output_dir / "claim_gate_report.json")
    assert result["metric_claim_level"] == "ambiguous_metric"
    assert report["claim_gate_result"]["calibrated_proxy_supported_allowed"] is False
    assert "row_schema_invalid" in report["claim_gate_result"]["reason_codes"]
    assert "row_1:missing_target_evidence" in report["row_validation"]["row_defects"]


def test_active_stratum_mismatch_fails_closed(workspace_tmp_dir):
    rows = _rows()
    rows[0]["stratum_id"] = "bio_attribute"
    output_dir, result = _run(workspace_tmp_dir, rows)

    report = _json(output_dir / "claim_gate_report.json")
    assert result["metric_claim_level"] == "ambiguous_metric"
    assert report["active_stratum_match"] is False
    assert "active_stratum_mismatch" in report["claim_gate_result"]["reason_codes"]


def test_candidate_pool_hash_mismatch_fails_closed(workspace_tmp_dir):
    rows = _rows()
    rows[5]["candidate_pool_hash"] = "different-candidate-pool-hash"
    output_dir, result = _run(workspace_tmp_dir, rows)

    report = _json(output_dir / "claim_gate_report.json")
    assert result["metric_claim_level"] == "ambiguous_metric"
    assert report["candidate_pool_hash_status"] == "mismatched"
    assert "candidate_pool_hash_mismatched" in report["claim_gate_result"]["reason_codes"]


def test_fixture_only_rows_cannot_emit_calibrated_proxy_supported(workspace_tmp_dir):
    output_dir, result = _run(workspace_tmp_dir, _rows(data_source_kind="fixture_test_only"))

    report = _json(output_dir / "claim_gate_report.json")
    assert result["metric_claim_level"] == "ambiguous_metric"
    assert result["paper_evidence_eligible"] is False
    assert report["claim_gate_result"]["calibrated_proxy_supported_allowed"] is False
    assert "fixture_only_not_bridge_support" in report["claim_gate_result"]["reason_codes"]


def test_underpowered_effective_sample_size_emits_ambiguous_metric(workspace_tmp_dir):
    output_dir, result = _run(workspace_tmp_dir, _rows(effective_sample_size=0.5))

    report = _json(output_dir / "claim_gate_report.json")
    assert result["metric_claim_level"] == "ambiguous_metric"
    assert result["paper_evidence_eligible"] is False
    assert "effective_sample_size_underpowered" in report["claim_gate_result"]["reason_codes"]


def test_contamination_failure_is_pilot_only_and_not_measurement_validation(workspace_tmp_dir):
    output_dir, result = _run(workspace_tmp_dir, _rows(contamination_status="fail"))

    report = _json(output_dir / "claim_gate_report.json")
    gate = report["claim_gate_result"]
    assert result["pilot_status"] == "pilot_only"
    assert result["metric_claim_level"] == "operational_utility_only"
    assert gate["measurement_validation_claim"] is False
    assert gate["paper_evidence_eligible"] is False
    assert "contamination_failed" in gate["reason_codes"]


def test_c_s_uses_dev_rows_and_zeta_uses_heldout_rows_only():
    rows = _rows()
    rows[3]["delta_utility"] = (rows[3]["delta_logloss"] * 2.0) + 0.04
    rows[4]["delta_utility"] = (rows[4]["delta_logloss"] * 2.0) + 0.04
    rows[5]["delta_utility"] = (rows[5]["delta_logloss"] * 2.0) + 0.04
    config = _json(CONFIG_PATH)
    contract = _json(CONTRACT_PATH)

    validation = validate_p55_rows(rows, config, contract)
    fit = evaluate_bridge_fit(validation["canonical_rows"], config, contract)

    assert fit["c_s"] == 2.0
    assert round(fit["zeta_s"], 8) == 0.04
    assert fit["dev_row_count"] == 3
    assert fit["heldout_row_count"] == 3
    assert fit["residual_stability"]["passes"] is True


def test_generated_canonical_artifacts_do_not_contain_volatile_or_local_path_fields(workspace_tmp_dir):
    output_dir, _ = _run(workspace_tmp_dir, rows=None)

    combined = "\n".join((output_dir / artifact).read_text(encoding="utf-8") for artifact in OUTPUT_ARTIFACTS)
    assert not re.search(r"\b20\d{2}-\d{2}-\d{2}(?:t|\s)\d{2}:\d{2}", combined, re.I)
    assert not re.search(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", combined, re.I)
    assert ":\\" not in combined
    assert "/home/" not in combined
    assert "/mnt/" not in combined
    assert "api" + "_key" not in combined.lower()
    assert "s" + "ecret" not in combined.lower()


def test_p55_bridge_calibration_pilot_import_does_not_load_live_api_sdks():
    assert_importing_modules_does_not_load_forbidden_sdks(["cps.experiments.bridge_calibration_pilot"])
