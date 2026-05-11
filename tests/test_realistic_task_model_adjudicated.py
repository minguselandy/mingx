from __future__ import annotations

import csv
import json
from pathlib import Path

from cps.experiments.realistic_tasks import run_realistic_task_benchmark
from tests.conftest import assert_importing_modules_does_not_load_forbidden_sdks


REQUIRED_FILES = (
    "realistic_task_packets.jsonl",
    "model_adjudicated_labels.jsonl",
    "label_stability_report.json",
    "realistic_selector_comparison.csv",
    "realistic_claim_gate_report.json",
    "realistic_task_report.md",
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


def test_p47_writes_realistic_task_packets_and_model_adjudicated_label_schema(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "p47"

    report = run_realistic_task_benchmark(
        config_path="configs/runs/realistic-task-model-adjudicated-v12.json",
        output_dir=output_dir,
    )

    assert report["status"] == "completed"
    assert report["task_count"] == 3
    assert report["data_source_kind"] == "fixture"
    for name in REQUIRED_FILES:
        assert (output_dir / name).exists()

    packets = _jsonl_rows(output_dir / "realistic_task_packets.jsonl")
    assert [row["task_family"] for row in packets] == [
        "multi_hop_evidence_assembly",
        "paper_revision_microtask",
        "repo_change_review_microtask",
    ]
    for packet in packets:
        assert {
            "task_id",
            "task_family",
            "agent_role",
            "task_prompt",
            "candidate_findings",
            "token_costs",
            "provenance",
            "expected_critical_findings",
        }.issubset(packet)
        assert packet["provenance"]["data_source_kind"] == "fixture"
        assert packet["provenance"]["paper_evidence_eligible"] is False
        assert packet["candidate_findings"]

    labels = _jsonl_rows(output_dir / "model_adjudicated_labels.jsonl")
    assert len(labels) == 3
    for label in labels:
        assert label["data_source_kind"] == "fixture"
        assert label["paper_evidence_eligible"] is False
        assert label["measurement_validation_claim"] is False
        assert set(label["pipeline_roles"]) == {"generator", "structural_labeler", "verifier", "adjudicator"}
        assert label["item_labels"]
        assert label["pair_labels"]
        assert label["triple_labels"]
        assert label["subset_labels"]
        assert {
            "singleton_value",
            "relevance_band",
            "is_prerequisite",
            "evidence_type",
            "provenance_strength",
            "extraction_complexity",
            "confidence",
        }.issubset(label["item_labels"][0])
        assert {
            "relation",
            "pairwise_excess_band",
            "prerequisite_direction",
            "confidence",
        }.issubset(label["pair_labels"][0])
        assert {
            "higher_order_type",
            "pairs_sufficient",
            "triple_excess_band",
            "greedy_failure_risk",
        }.issubset(label["triple_labels"][0])
        assert {
            "sufficiency_score",
            "missing_critical_findings",
            "redundant_findings",
            "unsupported_claim_risk",
            "expected_escalation_benefit",
            "selector_regime_label",
        }.issubset(label["subset_labels"][0])


def test_p47_selector_comparison_reports_required_baselines_and_metrics(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "p47_metrics"
    run_realistic_task_benchmark(
        config_path="configs/runs/realistic-task-model-adjudicated-v12.json",
        output_dir=output_dir,
    )

    rows = _csv_rows(output_dir / "realistic_selector_comparison.csv")
    assert len(rows) == 18
    assert {row["baseline"] for row in rows} == {
        "minimal_context",
        "full_context",
        "top_k_retrieval",
        "mmr_density_greedy",
        "always_sag",
        "v12_cost_aware_diagnostic_policy",
    }
    for row in rows:
        assert row["metric_claim_level"] in {
            "model_adjudicated_proxy_evidence",
            "operational_utility_only",
            "ambiguous_metric",
        }
        assert {
            "budget_comparable",
            "budget_status",
            "budget_tokens",
            "selected_token_count",
            "budget_overrun_tokens",
            "raw_structural_regime_label",
            "final_selector_regime_label",
        }.issubset(row)
        assert row["selector_regime_label"] in {
            "greedy_supported",
            "pairwise_escalate",
            "higher_order_risk",
            "ambiguous",
        }
        assert row["selector_regime_label"] not in {"monitored_greedy", "ambiguous_downgrade"}
        assert row["final_selector_regime_label"] == row["selector_regime_label"]
        assert row["raw_structural_regime_label"] in {
            "greedy_supported",
            "pairwise_escalate",
            "higher_order_risk",
            "ambiguous",
        }
        assert 0.0 <= float(row["sufficiency_score"]) <= 1.0
        assert 0.0 <= float(row["missing_critical_finding_rate"]) <= 1.0
        assert 0.0 <= float(row["redundancy_waste_rate"]) <= 1.0
        assert 0.0 <= float(row["unsupported_claim_risk"]) <= 1.0
        assert int(row["selected_tokens"]) >= 0
        assert int(row["selected_token_count"]) == int(row["selected_tokens"])
        assert int(row["budget_tokens"]) > 0
        assert int(row["budget_overrun_tokens"]) >= 0

    v12_policy = [row for row in rows if row["baseline"] == "v12_cost_aware_diagnostic_policy"]
    assert {row["cost_aware_policy_outcome"] for row in v12_policy} == {
        "ambiguous_downgrade",
        "monitored_greedy",
        "pairwise_escalate",
    }


def test_p47_full_context_is_non_budget_comparable_reference(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "p47_budget"
    run_realistic_task_benchmark(
        config_path="configs/runs/realistic-task-model-adjudicated-v12.json",
        output_dir=output_dir,
    )

    rows = _csv_rows(output_dir / "realistic_selector_comparison.csv")
    full_context_rows = [row for row in rows if row["baseline"] == "full_context"]
    budget_rows = [row for row in rows if row["baseline"] != "full_context"]

    assert len(full_context_rows) == 3
    for row in full_context_rows:
        assert row["budget_comparable"] == "false"
        assert row["budget_status"] == "over_budget_reference"
        assert int(row["selected_token_count"]) > int(row["budget_tokens"])
        assert int(row["budget_overrun_tokens"]) == (
            int(row["selected_token_count"]) - int(row["budget_tokens"])
        )

    assert budget_rows
    for row in budget_rows:
        assert row["budget_comparable"] == "true"
        assert row["budget_status"] == "within_budget"
        assert int(row["selected_token_count"]) <= int(row["budget_tokens"])
        assert int(row["budget_overrun_tokens"]) == 0

    claim = _json(output_dir / "realistic_claim_gate_report.json")
    assert claim["budget_fair_comparison_available"] is True
    assert claim["non_budget_reference_baselines"] == ["full_context"]
    assert claim["budget_comparable_baselines"] == [
        "minimal_context",
        "top_k_retrieval",
        "mmr_density_greedy",
        "always_sag",
        "v12_cost_aware_diagnostic_policy",
    ]
    assert claim["budget_fair_aggregate_excludes"] == ["full_context"]

    report = (output_dir / "realistic_task_report.md").read_text(encoding="utf-8")
    assert "Budget-Fair Baselines" in report
    assert "Non-Budget Reference Baselines" in report
    assert "always-large-context reference baseline" in report


def test_p47_quality_controls_and_claim_gate_fail_closed(workspace_tmp_dir):
    output_dir = workspace_tmp_dir / "p47_claims"
    run_realistic_task_benchmark(
        config_path="configs/runs/realistic-task-model-adjudicated-v12.json",
        output_dir=output_dir,
    )

    stability = _json(output_dir / "label_stability_report.json")
    assert stability["data_source_kind"] == "fixture"
    assert stability["duplicate_judging_stability"]["status"] == "fixture_not_measured"
    assert stability["order_reversal_status"]["status"] == "fixture_not_measured"
    assert stability["paraphrase_robustness_status"]["status"] == "fixture_not_measured"
    assert stability["prerequisite_ablation_status"]["status"] == "fixture_not_measured"
    assert stability["unstable_label_downgrade"]["selector_regime_label"] == "ambiguous"
    assert stability["unstable_label_downgrade"]["downgraded_task_ids"] == ["repo_change_review_claim_boundary"]

    claim = _json(output_dir / "realistic_claim_gate_report.json")
    assert claim["allowed_claim_level"] == "operational_utility_only"
    assert claim["metric_claim_level"] == "operational_utility_only"
    assert claim["data_source_kind"] == "fixture"
    assert claim["paper_evidence_eligible"] is False
    assert claim["measurement_validation_claim"] is False
    assert claim["human_labels_present"] is False
    assert claim["human_kappa_present"] is False
    assert claim["deployed_v_information_verification_claim"] is False
    assert claim["calibrated_bridge_evidence_used"] is False
    assert claim["live_api_used"] is False

    combined = _artifact_text(output_dir)
    assert '"measurement_validation_claim": true' not in combined
    assert '"human_validation_claim": true' not in combined
    assert '"deployed_v_information_verification_claim": true' not in combined
    assert "calibrated_proxy_supported" not in combined


def test_p47_outputs_are_deterministic(workspace_tmp_dir):
    first = workspace_tmp_dir / "first"
    second = workspace_tmp_dir / "second"

    run_realistic_task_benchmark(
        config_path="configs/runs/realistic-task-model-adjudicated-v12.json",
        output_dir=first,
    )
    run_realistic_task_benchmark(
        config_path="configs/runs/realistic-task-model-adjudicated-v12.json",
        output_dir=second,
    )

    for name in REQUIRED_FILES:
        assert (first / name).read_bytes() == (second / name).read_bytes()
        text = (first / name).read_text(encoding="utf-8")
        assert ":\\" not in text


def test_p47_import_does_not_load_live_api_or_external_sdks():
    assert_importing_modules_does_not_load_forbidden_sdks(["cps.experiments.realistic_tasks"])
