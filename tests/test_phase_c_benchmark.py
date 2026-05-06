import json
from pathlib import Path

from cps.experiments.phase_b_replay import run_phase_b_replay
from cps.experiments.phase_c_benchmark import run_phase_c_benchmark
from tests.conftest import assert_importing_modules_does_not_load_forbidden_sdks


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_phase_c_writes_required_condition_artifacts(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "phase_c"

    report = run_phase_c_benchmark(output_dir=output_dir)

    assert report["status"] == "completed"
    assert report["dispatch_count"] == 8
    assert report["condition_order"] == [
        "no_cps_baseline",
        "heuristic_selector_baseline",
        "cps_runtime_audit_scaffold",
        "diagnostic_guided_escalation",
    ]
    for name in (
        "candidate_pools.jsonl",
        "projection_plans.jsonl",
        "budget_witnesses.jsonl",
        "materialized_contexts.jsonl",
        "metric_bridge_witnesses.jsonl",
        "diagnostics.jsonl",
        "phase_c_manifest.json",
        "phase_c_dispatches.jsonl",
        "phase_c_condition_results.json",
        "phase_c_replay_status.json",
        "phase_c_diagnostics_summary.json",
        "phase_c_task_metrics.json",
        "phase_c_claim_gate_report.json",
        "phase_c_report.md",
    ):
        assert (output_dir / name).exists()

    dispatches = _jsonl_rows(output_dir / "phase_c_dispatches.jsonl")
    assert len(dispatches) == 8
    assert {row["condition"] for row in dispatches} == set(report["condition_order"])
    for row in dispatches:
        assert row["claim_gate_record"]["measurement_validated_allowed"] is False
        assert row["claim_gate_record"]["allowed_claim_level"] == "operational_utility_only"
        assert row["metric_bridge_assignment"] == "operational_utility_only"
        assert row["task_metrics"]["metric_scope"] == "operational_utility_only"
        assert row["task_metrics"]["exact_match"] in {0, 1}
        assert row["selection_summary"]["selected_token_cost"] <= row["budget_tokens"]
        assert row["selection_summary"]["condition"] == row["condition"]
        assert row["task_output"]["claim_level"] == "operational_utility_only"

    condition_results = _json(output_dir / "phase_c_condition_results.json")
    assert list(condition_results["conditions"]) == report["condition_order"]
    for condition, payload in condition_results["conditions"].items():
        assert payload["condition"] == condition
        assert payload["dispatch_count"] == 2
        assert payload["metric_bridge_assignment"] == "operational_utility_only"
        assert payload["measurement_validated_allowed"] is False


def test_phase_c_missing_metric_bridge_reports_operational_utility_only(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "missing_bridge"

    run_phase_c_benchmark(output_dir=output_dir, include_metric_bridge=False)

    assert _jsonl_rows(output_dir / "metric_bridge_witnesses.jsonl") == []
    claim_report = _json(output_dir / "phase_c_claim_gate_report.json")
    assert claim_report["metric_bridge_present"] is False
    assert claim_report["condition_claim_level_counts"] == {"operational_utility_only": 4}
    for row in claim_report["rows"]:
        assert row["metric_bridge_present"] is False
        assert row["allowed_claim_level"] == "operational_utility_only"
        assert "missing_metric_bridge" in row["reason_codes"]
        assert row["measurement_validated_allowed"] is False


def test_phase_c_default_outputs_are_phase_b_replay_compatible(workspace_tmp_dir):
    phase_c_output = workspace_tmp_dir / "phase_c"
    replay_output = workspace_tmp_dir / "phase_b_replay"
    run_phase_c_benchmark(output_dir=phase_c_output)

    replay = run_phase_b_replay(input_dir=phase_c_output, output_dir=replay_output)

    assert replay["status"] == "classified"
    assert replay["summary"]["total_dispatches"] == 8
    assert replay["summary"]["replay_status_counts"] == {"replay_usable": 8}
    assert replay["summary"]["metric_claim_level_counts"] == {"operational_utility_only": 8}
    assert replay["summary"]["headline_eligible_dispatches"] == 0


def test_phase_c_outputs_are_byte_stable(workspace_tmp_dir):
    first = workspace_tmp_dir / "first"
    second = workspace_tmp_dir / "second"

    run_phase_c_benchmark(output_dir=first)
    run_phase_c_benchmark(output_dir=second)

    for name in (
        "candidate_pools.jsonl",
        "projection_plans.jsonl",
        "budget_witnesses.jsonl",
        "materialized_contexts.jsonl",
        "metric_bridge_witnesses.jsonl",
        "diagnostics.jsonl",
        "phase_c_manifest.json",
        "phase_c_dispatches.jsonl",
        "phase_c_condition_results.json",
        "phase_c_replay_status.json",
        "phase_c_diagnostics_summary.json",
        "phase_c_task_metrics.json",
        "phase_c_claim_gate_report.json",
        "phase_c_report.md",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_phase_c_import_does_not_load_live_api_or_external_sdks():
    assert_importing_modules_does_not_load_forbidden_sdks(["cps.experiments.phase_c_benchmark"])
