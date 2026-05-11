from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import assert_importing_modules_does_not_load_forbidden_sdks
from cps.experiments.bridge_calibration import (
    BridgeCalibrationValidationError,
    OUTPUT_ARTIFACTS,
    dry_validate_bridge_calibration,
    run_bridge_calibration,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "runs" / "bridge-calibration-one-stratum.json"
FIXTURE_PATH = ROOT / "artifacts" / "fixtures" / "bridge_calibration_pairs_fixture.jsonl"
OPERATOR_TEMPLATE_PATH = ROOT / "docs" / "templates" / "bridge-calibration-pairs-template.jsonl"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixture_rows() -> list[dict]:
    return [json.loads(line) for line in FIXTURE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def _config(workspace_tmp_dir: Path, **overrides) -> Path:
    payload = _json(CONFIG_PATH)
    payload.update(overrides)
    return _write_json(workspace_tmp_dir / "bridge-config.json", payload)


def _run_fixture(workspace_tmp_dir: Path, **config_overrides):
    output_dir = workspace_tmp_dir / "bridge-output"
    result = run_bridge_calibration(
        config_path=_config(workspace_tmp_dir, **config_overrides),
        input_path=FIXTURE_PATH,
        output_dir=output_dir,
    )
    return output_dir, result


def test_valid_fixture_produces_required_artifacts(workspace_tmp_dir):
    output_dir, result = _run_fixture(workspace_tmp_dir)

    assert result["metric_claim_level"] == "calibrated_proxy_supported"
    assert sorted(path.name for path in output_dir.iterdir()) == sorted(OUTPUT_ARTIFACTS)
    for artifact in OUTPUT_ARTIFACTS:
        assert (output_dir / artifact).exists()

    fit = _json(output_dir / "bridge_calibration_fit.json")
    claim = _json(output_dir / "bridge_claim_gate_report.json")
    assert fit["sample_size"] == 6
    assert fit["effective_sample_size"] == 6
    assert fit["data_source_kind"] == "fixture"
    assert fit["selector_regime_label"] == "ambiguous"
    assert claim["allowed_claim_level"] == "calibrated_proxy_supported"
    assert claim["selector_regime_label"] == "ambiguous"
    assert "Selector regime label: `ambiguous`" in (output_dir / "report.md").read_text(encoding="utf-8")


def test_passing_fixture_can_calibrate_but_is_not_paper_evidence(workspace_tmp_dir):
    output_dir, _ = _run_fixture(workspace_tmp_dir)

    fit = _json(output_dir / "bridge_calibration_fit.json")
    assert fit["metric_claim_level"] == "calibrated_proxy_supported"
    assert fit["zeta_s"] <= fit["thresholds"]["max_allowed_zeta"]
    assert fit["sign_agreement"] >= fit["thresholds"]["min_sign_agreement"]
    assert fit["pearson_correlation"] >= fit["thresholds"]["min_pearson_correlation"]
    assert fit["spearman_correlation"] >= fit["thresholds"]["min_spearman_correlation"]
    assert fit["paper_evidence_eligible"] is False
    assert fit["measurement_validation_claim"] is False
    assert fit["deployed_v_information_verification_claim"] is False


def test_too_small_sample_fails_closed_to_ambiguous_metric(workspace_tmp_dir):
    input_path = _write_jsonl(workspace_tmp_dir / "small.jsonl", _fixture_rows()[:2])
    output_dir = workspace_tmp_dir / "too-small"

    run_bridge_calibration(config_path=_config(workspace_tmp_dir), input_path=input_path, output_dir=output_dir)

    fit = _json(output_dir / "bridge_calibration_fit.json")
    assert fit["metric_claim_level"] == "ambiguous_metric"
    assert "sample_size_failed" in fit["reason_codes"]
    assert fit["measurement_validated_allowed"] is False


def test_sign_disagreement_sample_is_operational_only(workspace_tmp_dir):
    rows = []
    for row in _fixture_rows():
        rewritten = dict(row)
        rewritten["delta_utility"] = -2.0 * float(rewritten["delta_logloss"])
        rows.append(rewritten)
    input_path = _write_jsonl(workspace_tmp_dir / "disagreement.jsonl", rows)
    output_dir = workspace_tmp_dir / "disagreement"

    run_bridge_calibration(config_path=_config(workspace_tmp_dir), input_path=input_path, output_dir=output_dir)

    fit = _json(output_dir / "bridge_calibration_fit.json")
    assert fit["metric_claim_level"] == "operational_utility_only"
    assert "sign_agreement_failed" in fit["reason_codes"]
    assert "pearson_failed" in fit["reason_codes"]
    assert "spearman_failed" in fit["reason_codes"]


def test_low_delta_logloss_rows_are_marked_uninformative_in_dry_validation(workspace_tmp_dir):
    rows = _fixture_rows()
    rows[0]["delta_logloss"] = 0.0004
    rows[0]["delta_utility"] = 0.0008
    input_path = _write_jsonl(workspace_tmp_dir / "low-signal.jsonl", rows)

    result = dry_validate_bridge_calibration(config_path=_config(workspace_tmp_dir), input_path=input_path)

    assert result["low_signal_delta_logloss_count"] == 1
    assert result["low_signal_delta_logloss_pair_ids"] == ["p001"]
    assert result["pass_flags"]["bridge_informative_delta_pass"] is False
    assert "low_delta_logloss_uninformative" in result["reason_codes"]
    assert result["would_be_metric_claim_level"] == "operational_utility_only"


def test_negative_delta_logloss_rows_are_reported_in_fit_artifacts(workspace_tmp_dir):
    output_dir, _ = _run_fixture(workspace_tmp_dir)

    fit = _json(output_dir / "bridge_calibration_fit.json")
    claim = _json(output_dir / "bridge_claim_gate_report.json")
    assert fit["negative_delta_logloss_count"] == 3
    assert fit["negative_delta_logloss_pair_ids"] == ["p003", "p004", "p006"]
    assert claim["negative_delta_logloss_count"] == 3


def test_non_finite_values_are_rejected(workspace_tmp_dir):
    rows = _fixture_rows()
    rows[0]["delta_utility"] = float("nan")
    input_path = _write_jsonl(workspace_tmp_dir / "nonfinite.jsonl", rows)

    with pytest.raises(BridgeCalibrationValidationError, match="delta_utility must be finite"):
        run_bridge_calibration(
            config_path=_config(workspace_tmp_dir),
            input_path=input_path,
            output_dir=workspace_tmp_dir / "nonfinite-output",
        )


def test_missing_required_fields_are_rejected(workspace_tmp_dir):
    rows = _fixture_rows()
    del rows[0]["pair_id"]
    input_path = _write_jsonl(workspace_tmp_dir / "missing.jsonl", rows)

    with pytest.raises(BridgeCalibrationValidationError, match="missing required fields: pair_id"):
        run_bridge_calibration(
            config_path=_config(workspace_tmp_dir),
            input_path=input_path,
            output_dir=workspace_tmp_dir / "missing-output",
        )


def test_synthetic_scope_never_upgrades_to_vinfo_proxy_supported(workspace_tmp_dir):
    output_dir, _ = _run_fixture(
        workspace_tmp_dir,
        evidence_scope="synthetic_structural_only",
        diagnostic_scope="synthetic_structural_only",
    )

    fit = _json(output_dir / "bridge_calibration_fit.json")
    claim = _json(output_dir / "bridge_claim_gate_report.json")
    combined = "\n".join((output_dir / artifact).read_text(encoding="utf-8") for artifact in OUTPUT_ARTIFACTS)
    assert fit["metric_claim_level"] == "ambiguous_metric"
    assert fit["evidence_scope"] == "synthetic_structural_only"
    assert claim["metric_claim_level"] == "ambiguous_metric"
    assert "synthetic_only_not_deployed_certification" in fit["reason_codes"]
    assert "vinfo_proxy_supported" not in combined


def test_synthetic_diagnostic_scope_alone_fails_closed(workspace_tmp_dir):
    output_dir, _ = _run_fixture(
        workspace_tmp_dir,
        diagnostic_scope="synthetic_structural_only",
    )

    fit = _json(output_dir / "bridge_calibration_fit.json")
    assert fit["metric_claim_level"] == "ambiguous_metric"
    assert fit["diagnostic_scope"] == "synthetic_structural_only"
    assert "synthetic_only_not_deployed_certification" in fit["reason_codes"]


def test_mixed_fixture_and_operator_sources_fail_closed(workspace_tmp_dir):
    rows = _fixture_rows()
    rows[0]["source"] = "operator_provided"
    input_path = _write_jsonl(workspace_tmp_dir / "mixed-source.jsonl", rows)
    output_dir = workspace_tmp_dir / "mixed-source"

    run_bridge_calibration(config_path=_config(workspace_tmp_dir), input_path=input_path, output_dir=output_dir)

    fit = _json(output_dir / "bridge_calibration_fit.json")
    assert fit["data_source_kind"] == "mixed"
    assert fit["metric_claim_level"] == "ambiguous_metric"
    assert fit["paper_evidence_eligible"] is False
    assert "source_kind_failed" in fit["reason_codes"]


def test_dry_validation_checks_thresholds_without_writing_artifacts_or_claiming_paper_evidence(
    workspace_tmp_dir,
):
    rows = []
    for row in _fixture_rows():
        rewritten = dict(row)
        rewritten["source"] = "operator_provided"
        rewritten["notes"] = "test-only operator source simulation; not persisted paper evidence"
        rows.append(rewritten)
    input_path = _write_jsonl(workspace_tmp_dir / "operator-simulated.jsonl", rows)
    output_dir = workspace_tmp_dir / "dry-output-should-not-exist"

    result = dry_validate_bridge_calibration(
        config_path=_config(workspace_tmp_dir, output_dir=str(output_dir)),
        input_path=input_path,
    )

    assert result["mode"] == "dry_validation"
    assert result["artifacts_written"] == []
    assert not output_dir.exists()
    assert result["would_be_metric_claim_level"] == "calibrated_proxy_supported"
    assert result["would_be_paper_evidence_eligible"] is True
    assert result["paper_evidence_eligible"] is False
    assert result["paper_evidence_claimed"] is False
    assert result["measurement_validation_claim"] is False
    assert result["deployed_v_information_verification_claim"] is False


def test_operator_template_is_placeholder_only_and_separate_from_fixture_data():
    assert OPERATOR_TEMPLATE_PATH.exists()
    template_text = OPERATOR_TEMPLATE_PATH.read_text(encoding="utf-8")
    template_rows = [json.loads(line) for line in template_text.splitlines() if line.strip()]

    assert len(template_rows) == 6
    assert {row["source"] for row in template_rows} == {"operator_provided"}
    assert all(str(row["pair_id"]).startswith("OPERATOR_FILL_") for row in template_rows)
    assert all("OPERATOR_FILL_ACTIVE_STRATUM_ID_KEEP_IDENTICAL" == row["stratum_id"] for row in template_rows)
    assert all("OPERATOR_FILL_NUMERIC" in str(row["delta_utility"]) for row in template_rows)
    assert all("OPERATOR_FILL_NUMERIC" in str(row["delta_logloss"]) for row in template_rows)
    assert "deterministic engineering fixture only" not in template_text


def test_selector_regime_label_cannot_be_upgraded_by_config(workspace_tmp_dir):
    output_dir, _ = _run_fixture(workspace_tmp_dir, selector_regime_label="greedy_supported")

    fit = _json(output_dir / "bridge_calibration_fit.json")
    claim = _json(output_dir / "bridge_claim_gate_report.json")
    assert fit["selector_regime_label"] == "ambiguous"
    assert claim["selector_regime_label"] == "ambiguous"


def test_no_artifact_claims_measurement_validation(workspace_tmp_dir):
    output_dir, _ = _run_fixture(workspace_tmp_dir)

    combined = "\n".join((output_dir / artifact).read_text(encoding="utf-8") for artifact in OUTPUT_ARTIFACTS)
    assert '"measurement_validation_claim": true' not in combined
    assert '"measurement_validated_allowed": true' not in combined
    assert '"allowed_claim_level": "measurement_validated"' not in combined
    assert "Allowed claim level: `measurement_validated`" not in combined
    assert "measurement_validated" in combined


def test_output_is_deterministic_across_repeated_runs(workspace_tmp_dir):
    first_output = workspace_tmp_dir / "first"
    second_output = workspace_tmp_dir / "second"
    config_path = _config(workspace_tmp_dir)

    run_bridge_calibration(config_path=config_path, input_path=FIXTURE_PATH, output_dir=first_output)
    run_bridge_calibration(config_path=config_path, input_path=FIXTURE_PATH, output_dir=second_output)

    for artifact in OUTPUT_ARTIFACTS:
        assert (first_output / artifact).read_text(encoding="utf-8") == (
            second_output / artifact
        ).read_text(encoding="utf-8")


def test_csv_input_is_supported(workspace_tmp_dir):
    rows = _fixture_rows()
    csv_path = workspace_tmp_dir / "fixture.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = list(rows[0])
        handle.write(",".join(fieldnames) + "\n")
        for row in rows:
            handle.write(",".join(str(row[field]) for field in fieldnames) + "\n")

    output_dir = workspace_tmp_dir / "csv-output"
    run_bridge_calibration(config_path=_config(workspace_tmp_dir), input_path=csv_path, output_dir=output_dir)

    assert _json(output_dir / "bridge_calibration_fit.json")["metric_claim_level"] == "calibrated_proxy_supported"


def test_optional_api_generation_provenance_survives_canonicalization(workspace_tmp_dir):
    rows = []
    for row in _fixture_rows():
        rewritten = dict(row)
        rewritten.update(
            {
                "source": "operator_provided",
                "data_origin": "api_generated",
                "delta_utility_source": "strong_model_adjudicated",
                "delta_logloss_source": "measured_logprob",
                "review_status": "accepted",
                "candidate_set_size_before": 8,
                "candidate_set_size_after": 2,
            }
        )
        rows.append(rewritten)
    input_path = _write_jsonl(workspace_tmp_dir / "api-generated.jsonl", rows)
    output_dir = workspace_tmp_dir / "api-generated-output"

    run_bridge_calibration(config_path=_config(workspace_tmp_dir), input_path=input_path, output_dir=output_dir)

    fit = _json(output_dir / "bridge_calibration_fit.json")
    assert fit["data_source_kind"] == "operator_provided_api_generated"
    assert fit["paper_evidence_eligible"] is False
    canonical_rows = [
        json.loads(line)
        for line in (output_dir / "bridge_calibration_pairs.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert canonical_rows[0]["data_origin"] == "api_generated"
    assert canonical_rows[0]["delta_utility_source"] == "strong_model_adjudicated"
    assert canonical_rows[0]["delta_logloss_source"] == "measured_logprob"
    assert canonical_rows[0]["review_status"] == "accepted"
    assert canonical_rows[0]["candidate_set_size_before"] == 8.0
    assert canonical_rows[0]["candidate_set_size_after"] == 2.0
    table_text = (output_dir / "bridge_calibration_table.csv").read_text(encoding="utf-8")
    assert "data_origin" in table_text
    assert "measured_logprob" in table_text
    assert "candidate_set_size_before" in table_text


def test_bridge_calibration_import_does_not_load_live_api_sdks():
    assert_importing_modules_does_not_load_forbidden_sdks(["cps.experiments.bridge_calibration"])
