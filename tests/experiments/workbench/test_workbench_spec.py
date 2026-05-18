from __future__ import annotations

import json
from pathlib import Path

from cps.experiments.workbench.artifact_paths import WorkbenchArtifactPaths
from cps.experiments.workbench.run_manager import run_workbench_from_config
from cps.experiments.workbench.spec import WorkbenchRunSpec
from cps.experiments.workbench.spec import load_workbench_spec


def _pool() -> dict:
    return {
        "candidate_pool": {
            "candidate_pool_hash": "pool-hash-1",
            "gold_reachable_under_budget": {"512": True},
            "n_candidates": 4,
            "n_gold_packets": 2,
            "n_hard_negative_packets": 2,
            "n_random_negative_packets": 0,
            "packets": [
                {
                    "content": "Alice founded Example Labs in 1999.",
                    "gold_support_label": "gold_supporting",
                    "packet_id": "p-gold-1",
                    "provenance": {"dataset": "HotpotQA", "source_doc_id": "Alice"},
                    "source_doc_id": "Alice",
                    "token_cost": 8,
                },
                {
                    "content": "Example Labs was founded after Alice left school.",
                    "gold_support_label": "gold_supporting",
                    "packet_id": "p-gold-2",
                    "provenance": {"dataset": "HotpotQA", "source_doc_id": "Example Labs"},
                    "source_doc_id": "Example Labs",
                    "token_cost": 9,
                },
                {
                    "content": "The city has several public parks.",
                    "gold_support_label": "same_context_distractor",
                    "packet_id": "p-noise-1",
                    "provenance": {"dataset": "HotpotQA", "source_doc_id": "City"},
                    "source_doc_id": "City",
                    "token_cost": 7,
                },
                {
                    "content": "Bob wrote a book about public libraries.",
                    "gold_support_label": "same_context_distractor",
                    "packet_id": "p-noise-2",
                    "provenance": {"dataset": "HotpotQA", "source_doc_id": "Bob"},
                    "source_doc_id": "Bob",
                    "token_cost": 8,
                },
            ],
            "total_tokens": 32,
        },
        "dataset": "HotpotQA",
        "instance_id": "hotpot-1",
        "query": "Who founded Example Labs?",
        "schema_version": "benchmark_instance_v1",
        "split": "dev_distractor",
        "target": {"label": "Alice", "target_type": "answer_string"},
        "task_family": "hotpotqa_answer_support_selection",
    }


def test_runspec_defaults_to_shadow_claim_mode():
    spec = WorkbenchRunSpec(
        run_id="hotpotqa_smoke",
        dataset="HotpotQA",
        candidate_pools_path="artifacts/benchmarks/hotpotqa_candidate_pools.jsonl",
        output_dir="artifacts/experiments/integrated_validation_workbench/hotpotqa_smoke",
        budgets=(512,),
        selectors=("bm25_topk",),
        evaluators=("operational",),
    )

    assert spec.claim_mode == "shadow"
    assert spec.claim_status == "operational_utility_only; no_claim_upgrade"
    assert spec.shadow_labels == (
        "shadow_metric_bridge",
        "shadow_vinfo_proxy",
        "shadow_measurement_candidate",
        "shadow_selector_superiority",
    )
    assert spec.portfolio == "integrated_validation_workbench"
    assert spec.label_source_policy == "model_adjudicated_or_operational_only_no_measurement_validation"
    assert spec.contamination_policy == "fail_closed_on_contamination_or_unreviewed_source_risk"
    assert spec.uncertainty_policy == "missing_or_underpowered_evidence_blocks_claim_upgrade"
    assert spec.accepted_evidence_requires_independent_review is True
    assert spec.route5_unlock_requires == ("accepted_bridge_candidate", "independent_review")
    assert spec.route8_claim_upgrade_requires == ("accepted_evidence_packages_nonempty", "independent_review")


def test_artifact_paths_are_deterministic_and_relative():
    paths = WorkbenchArtifactPaths.from_output_dir(
        "artifacts/experiments/integrated_validation_workbench/hotpotqa_smoke"
    )

    assert paths.manifest.as_posix().endswith("/manifest.json")
    assert paths.claim_ledger.as_posix().endswith("/claim_ledger.json")
    assert not Path(paths.output_dir).is_absolute()
    assert paths.to_manifest()["claim_ledger"] == "claim_ledger.json"


def test_json_yaml_runspec_loads_without_external_yaml_dependency(workspace_tmp_dir: Path):
    config_path = workspace_tmp_dir / "hotpotqa_smoke.yaml"
    config_path.write_text(
        json.dumps(
            {
                "run_id": "hotpotqa_smoke",
                "dataset": "HotpotQA",
                "candidate_pools_path": "artifacts/benchmarks/hotpotqa_candidate_pools.jsonl",
                "output_dir": "artifacts/experiments/integrated_validation_workbench/hotpotqa_smoke",
                "budgets": [512],
                "selectors": ["bm25_topk", "mmr_density_greedy", "v12_diagnostic_policy"],
                "evaluators": ["operational", "diagnostic_safety", "claim_ledger"],
                "portfolio": "iw_portfolio",
                "label_source_policy": "external_human_required_for_measurement_validation",
                "contamination_policy": "fail_closed",
                "uncertainty_policy": "independent_review_required_for_acceptance",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    spec = load_workbench_spec(config_path)

    assert spec.run_id == "hotpotqa_smoke"
    assert spec.claim_mode == "shadow"
    assert spec.portfolio == "iw_portfolio"
    assert spec.label_source_policy == "external_human_required_for_measurement_validation"
    assert spec.contamination_policy == "fail_closed"
    assert spec.uncertainty_policy == "independent_review_required_for_acceptance"
    assert spec.selectors == ("bm25_topk", "mmr_density_greedy", "v12_diagnostic_policy")


def test_hotpotqa_smoke_pipeline_writes_claim_safe_artifacts(workspace_tmp_dir: Path):
    pools_path = workspace_tmp_dir / "candidate_pools.jsonl"
    output_dir = workspace_tmp_dir / "workbench"
    config_path = workspace_tmp_dir / "hotpotqa_smoke.yaml"
    pools_path.write_text(json.dumps(_pool(), ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    config_path.write_text(
        json.dumps(
            {
                "run_id": "hotpotqa_smoke",
                "dataset": "HotpotQA",
                "candidate_pools_path": pools_path.as_posix(),
                "output_dir": output_dir.as_posix(),
                "limit": 1,
                "budgets": [512],
                "selectors": ["bm25_topk", "mmr_density_greedy", "v12_diagnostic_policy"],
                "evaluators": ["operational", "diagnostic_safety", "claim_ledger"],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = run_workbench_from_config(config_path)

    assert result["status"] == "completed_claim_safe_smoke"
    assert result["claim_status"] == "operational_utility_only; no_claim_upgrade"
    assert result["claim_mode"] == "shadow"
    assert result["traces_generated"] == 3
    assert (output_dir / "claim_ledger.json").exists()
    assert (output_dir / "blocked_claims.md").exists()
    assert (output_dir / "next_repairs.md").exists()
    ledger = json.loads((output_dir / "claim_ledger.json").read_text(encoding="utf-8"))
    assert ledger["accepted_claims"] == ["scoped_operational_improvement"]
    assert "calibrated_proxy_supported" in ledger["denied_claims"]
    assert ledger["claim_mode"] == "shadow"
