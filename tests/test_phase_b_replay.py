import json
import subprocess
import sys
from pathlib import Path

from cps.experiments.phase_b_replay import load_replay_artifact_bundles, run_phase_b_replay


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _jsonl_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _base_rows(**overrides) -> dict[str, dict]:
    common = {
        "run_id": "run-1",
        "dispatch_id": "dispatch-1",
        "agent_id": "agent-a",
        "round_id": "round-1",
        "regime": "fixture",
    }
    rows = {
        "candidate_pool": {
            **common,
            "budget_tokens": 10,
            "candidate_pool_hash": "pool-hash",
            "items": [
                {"item_id": "a", "token_cost": 4, "text": "A"},
                {"item_id": "b", "token_cost": 4, "text": "B"},
            ],
        },
        "projection_plan": {
            **common,
            "algorithm": "greedy",
            "budget_tokens": 10,
            "candidate_pool_hash": "pool-hash",
            "selected_ids": ["a"],
            "excluded_ids": ["b"],
            "trace": [],
            "score_config": {},
        },
        "budget_witness": {
            **common,
            "budget_tokens": 10,
            "estimated_tokens": 4,
            "realized_tokens": 4,
            "within_budget": True,
            "selected_ids": ["a"],
            "excluded_ids": ["b"],
            "tolerance_violations": [],
        },
        "materialized_context": {
            **common,
            "selected_ids": ["a"],
            "section_order": ["a"],
            "content": "[a]\nA",
            "token_count": 4,
            "context_hash": "context-hash",
        },
        "metric_bridge_witness": {
            **common,
            "calibration_epoch": "epoch-1",
            "active_stratum": {"regime": "fixture"},
            "model_tier": "frontier",
            "utility_metric": "log_loss",
            "metric_class": "log_loss_aligned",
            "materialization_policy": {},
            "decoding_policy": {},
            "bridge_scale": 1.0,
            "bridge_residual_zeta": 0.0,
            "effective_sample_size": 20,
            "drift_status": "fresh",
            "diagnostic_mode": "absolute",
            "diagnostic_claim_level": "Vinfo_proxy_certified",
        },
        "diagnostics": {
            **common,
            "metric_claim_level": "Vinfo_proxy_certified",
            "selector_regime_label": "greedy_valid",
            "selector_action": "monitored_greedy",
            "gamma_hat_semantics": "legacy_trace_decay_alias_not_submodularity_ratio",
        },
        "utility_record": {
            **common,
            "record_type": "cached_log_loss",
            "singleton_values": {"a": 1.0, "b": 0.5},
            "block_values": {"a,b": 1.2},
        },
    }
    for key, value in overrides.items():
        if value is None:
            rows.pop(key, None)
        else:
            rows[key].update(value)
    return rows


def _write_input_dir(input_dir: Path, rows: dict[str, dict]) -> None:
    file_map = {
        "candidate_pool": "candidate_pools.jsonl",
        "projection_plan": "projection_plans.jsonl",
        "budget_witness": "budget_witnesses.jsonl",
        "materialized_context": "materialized_contexts.jsonl",
        "metric_bridge_witness": "metric_bridge_witnesses.jsonl",
        "diagnostics": "diagnostics.jsonl",
        "utility_record": "utility_records.jsonl",
    }
    for key, filename in file_map.items():
        if key in rows:
            _write_jsonl(input_dir / filename, [rows[key]])


def _run_fixture(workspace_tmp_dir, rows: dict[str, dict]) -> tuple[dict, list[dict], dict]:
    input_dir = workspace_tmp_dir / "input"
    output_dir = workspace_tmp_dir / "output"
    _write_input_dir(input_dir, rows)
    report = run_phase_b_replay(input_dir=input_dir, output_dir=output_dir)
    manifest = _jsonl_rows(output_dir / "replay_manifest.jsonl")
    summary = json.loads((output_dir / "replay_summary.json").read_text(encoding="utf-8"))
    return report, manifest, summary


def test_complete_dispatch_bundle_is_replay_usable(workspace_tmp_dir):
    report, manifest, summary = _run_fixture(workspace_tmp_dir, _base_rows())

    assert report["status"] == "classified"
    assert manifest[0]["replay_status"] == "replay_usable"
    assert manifest[0]["replay_claim_scope"] == "Vinfo_proxy_certified"
    assert manifest[0]["metric_claim_level"] == "Vinfo_proxy_certified"
    assert summary["replay_usable_dispatches"] == 1
    assert summary["replay_status_counts"] == {"replay_usable": 1}


def test_missing_metric_bridge_witness_downgrades_to_partial_without_bridge_claim(workspace_tmp_dir):
    _, manifest, summary = _run_fixture(workspace_tmp_dir, _base_rows(metric_bridge_witness=None))

    assert manifest[0]["replay_status"] == "replay_partial"
    assert manifest[0]["metric_bridge_witness_present"] is False
    assert manifest[0]["metric_claim_level"] == "ambiguous"
    assert manifest[0]["replay_claim_scope"] == "observability_only"
    assert "MetricBridgeWitness" in manifest[0]["missing_required_fields"]
    assert summary["metric_claim_level_counts"] == {"ambiguous": 1}


def test_missing_materialization_order_is_replay_defect(workspace_tmp_dir):
    rows = _base_rows(materialized_context={"section_order": []})

    _, manifest, _ = _run_fixture(workspace_tmp_dir, rows)

    assert manifest[0]["replay_status"] != "replay_usable"
    assert "missing_materialization_order" in manifest[0]["replay_defects"]
    assert "materialization_order" in manifest[0]["missing_required_fields"]


def test_missing_excluded_candidates_is_replay_defect(workspace_tmp_dir):
    rows = _base_rows(projection_plan={"excluded_ids": []}, budget_witness={"excluded_ids": []})

    _, manifest, _ = _run_fixture(workspace_tmp_dir, rows)

    assert manifest[0]["replay_status"] != "replay_usable"
    assert "missing_excluded_candidates" in manifest[0]["replay_defects"]
    assert "excluded_ids" in manifest[0]["missing_required_fields"]


def test_missing_candidate_pool_is_replay_unusable(workspace_tmp_dir):
    _, manifest, summary = _run_fixture(workspace_tmp_dir, _base_rows(candidate_pool=None))

    assert manifest[0]["replay_status"] == "replay_unusable"
    assert manifest[0]["candidate_pool_present"] is False
    assert summary["replay_nonusable_dispatches"] == 1


def test_operational_only_metric_bridge_remains_operational_only(workspace_tmp_dir):
    rows = _base_rows(
        metric_bridge_witness={
            "metric_class": "operational_only",
            "utility_metric": "task_success",
            "diagnostic_claim_level": "operational_utility_only",
        }
    )

    _, manifest, _ = _run_fixture(workspace_tmp_dir, rows)

    assert manifest[0]["metric_claim_level"] == "operational_utility_only"
    assert manifest[0]["metric_claim_level"] != "Vinfo_proxy_certified"


def test_structural_synthetic_metric_bridge_remains_structural_synthetic_only(workspace_tmp_dir):
    rows = _base_rows(
        metric_bridge_witness={
            "metric_class": "synthetic_oracle",
            "utility_metric": "synthetic_oracle_value",
            "diagnostic_claim_level": "structural_synthetic_only",
        }
    )

    _, manifest, _ = _run_fixture(workspace_tmp_dir, rows)

    assert manifest[0]["metric_claim_level"] == "structural_synthetic_only"
    assert manifest[0]["replay_claim_scope"] == "structural_synthetic_only"


def test_stale_metric_bridge_yields_recalibration_required_scope(workspace_tmp_dir):
    rows = _base_rows(metric_bridge_witness={"drift_status": "stale"})

    _, manifest, _ = _run_fixture(workspace_tmp_dir, rows)

    assert manifest[0]["metric_claim_level"] == "ambiguous"
    assert manifest[0]["bridge_status"] == "stale"
    assert manifest[0]["replay_claim_scope"] == "recalibration_required"
    assert manifest[0]["replay_status"] == "replay_partial"


def test_cli_writes_phase_b_manifest_missing_fields_and_summary(workspace_tmp_dir):
    input_dir = workspace_tmp_dir / "input"
    output_dir = workspace_tmp_dir / "cli-output"
    _write_input_dir(input_dir, _base_rows())

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cps.experiments.phase_b_replay",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
        ],
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (output_dir / "replay_manifest.jsonl").exists()
    assert (output_dir / "missing_fields.json").exists()
    assert (output_dir / "replay_summary.json").exists()
    assert "replay_usable" in result.stdout


def test_candidate_pool_is_replay_substrate_not_core_paper_artifact(workspace_tmp_dir):
    _, manifest, summary = _run_fixture(workspace_tmp_dir, _base_rows())
    bundles = load_replay_artifact_bundles(workspace_tmp_dir / "input")

    assert bundles[0].candidate_pool is not None
    assert "CandidatePool" in summary["replay_substrate_artifacts"]
    assert "CandidatePool" not in summary["core_paper_artifacts"]
    assert "CandidatePool is replay substrate" in manifest[0]["notes"]
