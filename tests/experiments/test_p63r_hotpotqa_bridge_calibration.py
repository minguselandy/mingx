from __future__ import annotations

import json
from pathlib import Path

from cps.experiments.bridge_row_schema import ACTIVE_STRATUM
from cps.experiments.bridge_row_schema import DEFAULT_MATERIALIZATION_POLICY
from cps.experiments.bridge_row_schema import HOTPOTQA_DATASET
from cps.experiments.bridge_row_schema import HOTPOTQA_TASK_FAMILY
from cps.experiments.bridge_row_schema import P55BridgeRow
from cps.experiments.bridge_row_schema import make_materialized_context_hash
from cps.experiments.p55_hotpotqa_bridge_calibration import P63RCalibrationConfig
from cps.experiments.p55_hotpotqa_bridge_calibration import fit_calibration
from cps.experiments.p55_hotpotqa_bridge_calibration import run_p63r_hotpotqa_bridge_calibration
from cps.experiments.p55_hotpotqa_bridge_calibration import split_train_heldout


def _row(index: int, *, delta_logloss: float, delta_utility: float, instance_id: str | None = None) -> dict:
    block_id = f"packet-{index:03d}"
    row = P55BridgeRow(
        active_stratum=ACTIVE_STRATUM,
        task_family=HOTPOTQA_TASK_FAMILY,
        dataset=HOTPOTQA_DATASET,
        instance_id=instance_id or f"hotpot-{index:03d}",
        model_tier="approved_live_logprob_model_v1",
        materialization_policy=DEFAULT_MATERIALIZATION_POLICY,
        candidate_slice_band="hotpotqa_dev_distractor_context",
        block_size=1,
        context_L_packet_ids=(),
        block_A_packet_ids=(block_id,),
        target_y=f"answer-{index:03d}",
        delta_logloss=delta_logloss,
        delta_utility=delta_utility,
        replicate_count=1,
        decoding_policy="deterministic_logprob_scoring_v1",
        evaluator_id=(
            "approved_live_api_logprob_endpoint::dashscope::qwen3.6-flash"
            "::deterministic_logprob_scoring_v1"
        ),
        candidate_pool_hash=f"pool-hash-{index:03d}",
        materialized_context_hash=make_materialized_context_hash([], [block_id]),
        contamination_status="clean",
    )
    return row.to_payload()


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _small_config(**overrides) -> P63RCalibrationConfig:
    values = {
        "min_rows_validated": 4,
        "min_unique_instances": 4,
        "min_effective_sample_size": 4,
        "min_sign_agreement": 0.70,
        "min_spearman_rho": 0.40,
        "max_normalized_residual": 0.10,
    }
    values.update(overrides)
    return P63RCalibrationConfig(**values)


def test_imports_and_validates_hotpotqa_rows(workspace_tmp_dir: Path):
    rows = [_row(i, delta_logloss=0.1 * i, delta_utility=0.2 * i) for i in range(1, 7)]
    input_path = _write_jsonl(workspace_tmp_dir / "rows.jsonl", rows)
    output_dir = workspace_tmp_dir / "calibration"

    result = run_p63r_hotpotqa_bridge_calibration(
        input_rows_jsonl=input_path,
        output_dir=output_dir,
        config=_small_config(),
    )

    assert result["rows_imported"] == 6
    assert result["rows_validated"] == 6
    assert result["unique_instances"] == 6
    import_report = json.loads((output_dir / "import_report.json").read_text(encoding="utf-8"))
    assert import_report["schema_valid"] is True
    assert import_report["dataset"] == "HotpotQA"


def test_heldout_split_is_deterministic():
    rows = [_row(i, delta_logloss=0.1 * i, delta_utility=0.2 * i) for i in range(1, 11)]
    first = split_train_heldout(list(reversed(rows)), heldout_fraction=0.30)
    second = split_train_heldout(rows, heldout_fraction=0.30)

    assert first == second
    assert len(first.train_rows) == 7
    assert len(first.heldout_rows) == 3
    assert first.heldout_fraction == 0.3


def test_fit_metrics_pass_for_linear_rows():
    rows = [_row(i, delta_logloss=0.1 * i, delta_utility=0.2 * i) for i in range(1, 11)]

    fit = fit_calibration(rows, config=_small_config(min_rows_validated=10, min_unique_instances=10))

    assert fit["gate_result"] == "calibrated_proxy_supported_candidate"
    assert fit["metric_claim_level"] == "calibrated_proxy_supported_candidate"
    assert fit["claim_status"] == "calibrated_proxy_supported_candidate_pending_review"
    assert fit["bridge_fit"]["c_hat_s"] == 2.0
    assert fit["gate_pass_flags"]["normalized_residual_pass"] is True


def test_gate_failure_downgrades_to_operational_utility_only():
    rows = [
        _row(i, delta_logloss=(-0.1 if i % 2 else 0.1), delta_utility=0.5)
        for i in range(1, 11)
    ]

    fit = fit_calibration(rows, config=_small_config(min_rows_validated=10, min_unique_instances=10))

    assert fit["gate_result"] == "failed_closed_gate_failed"
    assert fit["metric_claim_level"] == "operational_utility_only"
    assert fit["claim_status"] == "operational_utility_only; no_claim_upgrade"
    assert "sign_agreement_failed" in fit["reason_codes"]


def test_missing_rows_fail_closed_no_rows(workspace_tmp_dir: Path):
    output_dir = workspace_tmp_dir / "calibration"

    result = run_p63r_hotpotqa_bridge_calibration(
        input_rows_jsonl=workspace_tmp_dir / "missing.jsonl",
        output_dir=output_dir,
        config=_small_config(),
    )

    assert result["gate_result"] == "failed_closed_no_rows"
    assert result["rows_validated"] == 0
    witness = json.loads((output_dir / "metric_bridge_witness.json").read_text(encoding="utf-8"))
    assert witness["metric_claim_level"] == "ambiguous_metric"
    assert witness["calibrated_proxy_supported_candidate"] is False


def test_artifact_writing_is_deterministic(workspace_tmp_dir: Path):
    rows = [_row(i, delta_logloss=0.1 * i, delta_utility=0.2 * i) for i in range(1, 7)]
    input_path = _write_jsonl(workspace_tmp_dir / "rows.jsonl", rows)
    output_dir = workspace_tmp_dir / "calibration"

    run_p63r_hotpotqa_bridge_calibration(input_rows_jsonl=input_path, output_dir=output_dir, config=_small_config())
    first = {
        path.name: path.read_bytes()
        for path in sorted(output_dir.iterdir())
        if path.suffix in {".json", ".md"}
    }
    run_p63r_hotpotqa_bridge_calibration(input_rows_jsonl=input_path, output_dir=output_dir, config=_small_config())
    second = {
        path.name: path.read_bytes()
        for path in sorted(output_dir.iterdir())
        if path.suffix in {".json", ".md"}
    }

    assert first == second
    combined = b"".join(second.values()).decode("utf-8")
    assert str(workspace_tmp_dir) not in combined
