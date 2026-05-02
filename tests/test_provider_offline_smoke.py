from __future__ import annotations

import json
import socket
from pathlib import Path

from cps.experiments.artifacts import rebuild_projection_summary_from_events
from cps.experiments.provider_offline_smoke import run_provider_offline_smoke
from cps.schema import ProjectionBundleV1


def _jsonl_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _stable_summary_payload(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("output_dir", None)
    payload.pop("artifact_paths", None)
    return payload


def test_provider_offline_smoke_writes_complete_replay_artifacts(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "provider_smoke"

    report = run_provider_offline_smoke(output_dir, seed=11, budget_tokens=12)

    assert report["status"] == "green"
    for name in (
        "events.jsonl",
        "provider_candidates.jsonl",
        "normalized_candidates.jsonl",
        "candidate_pools.jsonl",
        "projection_plans.jsonl",
        "budget_witnesses.jsonl",
        "materialized_contexts.jsonl",
        "metric_bridge_witnesses.jsonl",
        "diagnostics.jsonl",
        "projection_bundles.jsonl",
        "summary.json",
    ):
        assert (output_dir / name).exists()

    for name in (
        "candidate_pools.jsonl",
        "projection_plans.jsonl",
        "budget_witnesses.jsonl",
        "materialized_contexts.jsonl",
        "metric_bridge_witnesses.jsonl",
        "diagnostics.jsonl",
        "projection_bundles.jsonl",
    ):
        assert len(_jsonl_rows(output_dir / name)) == 2

    assert len(_jsonl_rows(output_dir / "provider_candidates.jsonl")) == 4
    assert len(_jsonl_rows(output_dir / "normalized_candidates.jsonl")) == 4

    summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    rebuilt = rebuild_projection_summary_from_events(output_dir, run_id=report["run_id"])
    assert rebuilt["complete_artifact_sets"] is True
    assert rebuilt["artifact_counts"]["projection_bundles"] == 2
    assert summary["claim_level"] == "engineering_smoke_only"
    assert summary["artifact_complete"] is True
    assert summary["metric_claim_level_counts"] == {"engineering_smoke_only": 2}


def test_provider_candidates_are_normalized_before_selection(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "provider_smoke"

    run_provider_offline_smoke(output_dir, seed=0, budget_tokens=12)

    normalized_rows = _jsonl_rows(output_dir / "normalized_candidates.jsonl")
    for row in normalized_rows:
        candidate = row["candidate"]
        assert candidate["candidate_id"] == candidate["item_id"]
        assert candidate["content"] == candidate["text"]
        assert candidate["token_cost"] == candidate["token_estimate"]

    graphiti_ids = [
        row["candidate"]["item_id"]
        for row in normalized_rows
        if row["provider_family"] == "graphiti"
    ]
    langextract_ids = [
        row["candidate"]["item_id"]
        for row in normalized_rows
        if row["provider_family"] == "langextract"
    ]
    assert graphiti_ids == [
        normalized_rows[0]["candidate"]["item_id"],
        normalized_rows[1]["candidate"]["item_id"],
    ]
    assert langextract_ids == [
        normalized_rows[2]["candidate"]["item_id"],
        normalized_rows[3]["candidate"]["item_id"],
    ]


def test_first_fit_selection_respects_budget(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "provider_smoke"

    run_provider_offline_smoke(output_dir, seed=0, budget_tokens=4)

    witnesses = _jsonl_rows(output_dir / "budget_witnesses.jsonl")
    plans = _jsonl_rows(output_dir / "projection_plans.jsonl")
    for witness, plan in zip(witnesses, plans):
        assert witness["within_budget"] is True
        assert witness["realized_tokens"] <= 4
        assert plan["algorithm"] == "deterministic_provider_smoke_first_fit"
        for step in plan["trace"]:
            if step["decision"] == "selected":
                assert step["used_tokens_after"] <= 4


def test_projection_bundles_reconstruct_with_stable_hashes(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "provider_smoke"

    run_provider_offline_smoke(output_dir, seed=3, budget_tokens=12)

    bundles = _jsonl_rows(output_dir / "projection_bundles.jsonl")
    assert len(bundles) == 2
    for row in bundles:
        bundle = ProjectionBundleV1.from_dict(row)
        assert row["canonical_hash"] == bundle.canonical_hash()
        assert ProjectionBundleV1.from_dict(bundle.to_dict()).canonical_hash() == bundle.canonical_hash()


def test_provider_offline_smoke_outputs_are_deterministic(workspace_tmp_dir):
    first_output = workspace_tmp_dir / "first"
    second_output = workspace_tmp_dir / "second"

    run_provider_offline_smoke(first_output, seed=7, budget_tokens=12)
    run_provider_offline_smoke(second_output, seed=7, budget_tokens=12)

    for name in (
        "provider_candidates.jsonl",
        "normalized_candidates.jsonl",
        "candidate_pools.jsonl",
        "projection_plans.jsonl",
        "budget_witnesses.jsonl",
        "materialized_contexts.jsonl",
        "metric_bridge_witnesses.jsonl",
        "diagnostics.jsonl",
        "projection_bundles.jsonl",
    ):
        assert (first_output / name).read_text(encoding="utf-8") == (
            second_output / name
        ).read_text(encoding="utf-8")
    assert _stable_summary_payload(first_output / "summary.json") == _stable_summary_payload(
        second_output / "summary.json"
    )


def test_provider_offline_smoke_does_not_overclaim(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "provider_smoke"

    run_provider_offline_smoke(output_dir, seed=0, budget_tokens=12)

    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            output_dir / "summary.json",
            output_dir / "diagnostics.jsonl",
            output_dir / "metric_bridge_witnesses.jsonl",
            output_dir / "projection_bundles.jsonl",
        )
    )
    assert "engineering_smoke_only" in combined
    assert "measurement_validated" not in combined
    assert "Vinfo_proxy_certified" not in combined
    assert "deployed_submodularity_certified" not in combined
    assert "runtime_integration_complete" not in combined


def test_provider_offline_smoke_does_not_use_network_or_reference(monkeypatch, workspace_tmp_dir):
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("provider offline smoke must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    report = run_provider_offline_smoke(workspace_tmp_dir / "provider_smoke", seed=0, budget_tokens=12)

    assert report["status"] == "green"
