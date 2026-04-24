import json
from pathlib import Path

from cps.experiments.artifacts import rebuild_projection_summary_from_events
from cps.experiments.synthetic_benchmark import run_synthetic_benchmark


def _jsonl_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_synthetic_benchmark_cli_function_writes_replayable_artifacts(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "synthetic_run"

    report = run_synthetic_benchmark(
        config_path="configs/runs/synthetic-regime-smoke.json",
        output_dir=output_dir,
    )

    assert report["status"] == "green"
    for name in (
        "events.jsonl",
        "candidate_pools.jsonl",
        "projection_plans.jsonl",
        "budget_witnesses.jsonl",
        "materialized_contexts.jsonl",
        "diagnostics.jsonl",
        "summary.json",
        "report.md",
    ):
        assert (output_dir / name).exists()

    for name in (
        "candidate_pools.jsonl",
        "projection_plans.jsonl",
        "budget_witnesses.jsonl",
        "materialized_contexts.jsonl",
        "diagnostics.jsonl",
    ):
        assert len(_jsonl_rows(output_dir / name)) == 3

    event_summary = rebuild_projection_summary_from_events(output_dir, run_id=report["run_id"])
    summary = json.loads(Path(report["summary_path"]).read_text(encoding="utf-8"))
    assert event_summary["dispatch_count"] == summary["dispatch_count"] == 3
    assert event_summary["complete_artifact_sets"] is True
    assert summary["expected_policy_matches"] == 3
    assert summary["policy_counts"] == {
        "interaction_aware_local_search": 1,
        "monitored_greedy": 1,
        "seeded_augmented_greedy": 1,
    }

    diagnostics = _jsonl_rows(output_dir / "diagnostics.jsonl")
    for row in diagnostics:
        for key in (
            "dispatch_id",
            "agent_id",
            "round_id",
            "regime",
            "budget_tokens",
            "candidate_count",
            "candidate_pool_hash",
            "algorithm",
            "selected_ids",
            "excluded_ids",
            "estimated_tokens",
            "realized_tokens",
            "within_budget",
            "gamma_hat",
            "synergy_fraction",
            "greedy_augmented_gap",
            "policy_recommendation",
        ):
            assert key in row
        assert row["within_budget"] is True

    report_text = Path(report["report_path"]).read_text(encoding="utf-8")
    assert "not a theorem-inheritance claim" in report_text
    assert "not a system-level performance claim" in report_text
