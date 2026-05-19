from __future__ import annotations

import json
from pathlib import Path

from cps.benchmarks.common import write_jsonl
from cps.benchmarks.schemas import make_candidate_pool
from cps.benchmarks.schemas import make_evidence_packet
from cps.experiments.gamma_operational_expansion import CLAIM_STATUS
from cps.experiments.gamma_operational_expansion import audit_untracked_leftovers
from cps.experiments.gamma_operational_expansion import project_native_packets_to_candidate_pools
from cps.experiments.gamma_operational_expansion import run_gamma_operational_expansion


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _hotpotqa_pool(instance_id: str = "hotpot-test-1") -> dict:
    packets = [
        make_evidence_packet(
            dataset="HotpotQA",
            split="dev_distractor",
            instance_id=instance_id,
            content="Alice founded Example Labs.",
            gold_support_label="gold_supporting",
            source_doc_id="Alice",
            token_cost=8,
        ),
        make_evidence_packet(
            dataset="HotpotQA",
            split="dev_distractor",
            instance_id=instance_id,
            content="Example Labs is based in Riverton.",
            gold_support_label="gold_supporting",
            source_doc_id="Example Labs",
            token_cost=9,
        ),
        make_evidence_packet(
            dataset="HotpotQA",
            split="dev_distractor",
            instance_id=instance_id,
            content="A city guide mentions several parks.",
            gold_support_label="same_context_distractor",
            source_doc_id="City Guide",
            token_cost=7,
        ),
    ]
    pool = make_candidate_pool(
        dataset="HotpotQA",
        split="dev_distractor",
        instance_id=instance_id,
        packets=packets,
        budgets=(32, 64),
    )
    return {
        "candidate_pool": pool.to_payload(),
        "dataset": "HotpotQA",
        "instance_id": instance_id,
        "query": "Who founded Example Labs?",
        "schema_version": "benchmark_instance_v1",
        "split": "dev_distractor",
        "target": {"label": "Alice", "target_type": "answer_string"},
        "task_family": "hotpotqa_answer_support_selection",
    }


def _project_native_row() -> dict:
    return {
        "budget_tokens": 32,
        "candidate_findings": [
            {
                "evidence_type": "bridge_fact",
                "finding_id": "bridge_entity",
                "heuristic_score": 0.8,
                "provenance_strength": "high",
                "text": "Northbridge University hosts the fellowship.",
                "token_cost": 10,
            },
            {
                "evidence_type": "answer_fact",
                "finding_id": "answer_location",
                "heuristic_score": 0.76,
                "provenance_strength": "high",
                "text": "Northbridge University is in Riverton.",
                "token_cost": 10,
            },
            {
                "evidence_type": "lexical_decoy",
                "finding_id": "decoy",
                "heuristic_score": 0.7,
                "provenance_strength": "medium",
                "text": "A Riverton museum mentions a fellowship.",
                "token_cost": 9,
            },
        ],
        "expected_critical_findings": ["bridge_entity", "answer_location"],
        "task_family": "multi_hop_evidence_assembly",
        "task_id": "project-native-1",
        "task_prompt": "Assemble the minimum two-hop evidence.",
    }


def test_leftover_audit_keeps_beta_route4d_route6c_unstaged(workspace_tmp_dir: Path) -> None:
    report = audit_untracked_leftovers(
        root=workspace_tmp_dir,
        output_dir=workspace_tmp_dir / "gamma",
        untracked_paths=[
            "artifacts/experiments/beta_hybrid_label_model/portfolio_update.json",
            "cps/experiments/hybrid_label_model.py",
            "artifacts/experiments/route4d_hybrid_utility_bridge/bridge_rows.jsonl",
            "artifacts/experiments/route6c_model_adjudication_scaleup/model_adjudicated_labels.jsonl",
            "notes/unrelated.txt",
        ],
    )

    assert report["status"] == "pass_leftovers_unstaged"
    assert report["audited_leftover_count"] == 4
    assert report["category_counts"] == {"Beta": 2, "Route4D": 1, "Route6C": 1}
    assert any(
        item["path"] == "cps/experiments/hybrid_label_model.py" and item["category"] == "Beta"
        for item in report["leftovers"]
    )
    assert all(item["gamma_staging_action"] == "left_unstaged" for item in report["leftovers"])


def test_project_native_conversion_uses_existing_fixture_labels_without_claim_upgrade() -> None:
    records = project_native_packets_to_candidate_pools([_project_native_row()], budgets=(32,))
    packets = records[0]["candidate_pool"]["packets"]

    assert records[0]["dataset"] == "ProjectNativeRealisticTasks"
    assert records[0]["adapter_metadata"]["raw_external_mirror_created"] is False
    assert records[0]["adapter_metadata"]["claim_boundary"] == "fixture_operational_only_no_claim_upgrade"
    assert sum(1 for packet in packets if packet["gold_support_label"] == "gold_supporting") == 2
    assert any(packet["gold_support_label"] == "same_context_distractor" for packet in packets)


def test_gamma_run_writes_terminal_operational_only_report(workspace_tmp_dir: Path) -> None:
    hotpotqa_path = workspace_tmp_dir / "hotpotqa_candidate_pools.jsonl"
    project_packets_path = workspace_tmp_dir / "realistic_task_packets.jsonl"
    project_comparison_path = workspace_tmp_dir / "realistic_selector_comparison.csv"
    output_dir = workspace_tmp_dir / "gamma"
    docs_path = workspace_tmp_dir / "Gamma-report.md"
    write_jsonl(hotpotqa_path, [_hotpotqa_pool()])
    write_jsonl(project_packets_path, [_project_native_row()])
    project_comparison_path.write_text(
        "task_id,task_family,baseline,data_source_kind\n"
        "project-native-1,multi_hop_evidence_assembly,v12_cost_aware_diagnostic_policy,fixture\n",
        encoding="utf-8",
    )

    result = run_gamma_operational_expansion(
        root=workspace_tmp_dir,
        output_dir=output_dir,
        docs_path=docs_path,
        hotpotqa_candidate_pools_path=hotpotqa_path,
        project_native_packets_path=project_packets_path,
        project_native_comparison_path=project_comparison_path,
        hotpotqa_limit=1,
        untracked_paths=[],
    )

    final_status = _read_json(output_dir / "final_status.json")
    effect_audit = _read_json(output_dir / "diagnostic_effect_audit.json")
    hotpotqa_ledger = _read_json(output_dir / "workbench_hotpotqa" / "claim_ledger.json")
    project_pools = _read_jsonl(output_dir / "project_native_candidate_pools.jsonl")
    report = docs_path.read_text(encoding="utf-8")

    assert result["terminal_status"] == "GAMMA_OPERATIONAL_COMPARISON_COMPLETED"
    assert final_status["claim_status"] == CLAIM_STATUS
    assert final_status["fever_disabled"] is True
    assert final_status["bridge_retry_performed"] is False
    assert final_status["selector_superiority_claimed"] is False
    assert final_status["metric_bridge_support"] is False
    assert final_status["calibrated_proxy_supported"] is False
    assert final_status["vinfo_proxy_supported"] is False
    assert final_status["measurement_validation"] is False
    assert final_status["raw_dataset_mirrors_created"] is False
    assert hotpotqa_ledger["accepted_claims"] == []
    assert hotpotqa_ledger["gamma_operational_observations_shadow_only"] == ["scoped_operational_improvement"]
    assert effect_audit["overall"]["trace_count"] == 20
    assert project_pools[0]["adapter_metadata"]["data_source_kind"] == "fixture"
    assert "FEVER status: `disabled_by_gamma_goal`" in report
    assert "No Route 4F or Route 4G bridge retry was performed." in report
