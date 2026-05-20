from __future__ import annotations

import json
from pathlib import Path

from cps.benchmarks.common import write_jsonl
from cps.benchmarks.schemas import make_candidate_pool
from cps.benchmarks.schemas import make_evidence_packet
from cps.experiments.live_api_evidence_package_factory import run_live_api_evidence_package_factory


class FakeDashScopeClient:
    def __init__(self) -> None:
        self.calls = 0

    def chat_completion(self, *, messages, logprobs=True, **kwargs):
        self.calls += 1
        label = "supporting" if self.calls % 2 else "not_supporting"
        return {
            "content": json.dumps(
                {"label": label, "rationale_quality": "adequate", "uncertainty": "low"},
                sort_keys=True,
            ),
            "model_id": "qwen3.6-flash",
            "token_logprobs": [-0.1, -0.2],
        }


def _hotpotqa_pool(instance_id: str = "hotpot-1") -> dict:
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
            content="A city guide mentions parks.",
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
        budgets=(32,),
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
                "finding_id": "bridge",
                "heuristic_score": 0.8,
                "provenance_strength": "high",
                "text": "Northbridge hosts the fellowship.",
                "token_cost": 10,
            },
            {
                "evidence_type": "answer_fact",
                "finding_id": "answer",
                "heuristic_score": 0.7,
                "provenance_strength": "high",
                "text": "Northbridge is in Riverton.",
                "token_cost": 10,
            },
        ],
        "expected_critical_findings": ["bridge", "answer"],
        "task_family": "multi_hop_evidence_assembly",
        "task_id": "project-native-1",
        "task_prompt": "Assemble the minimum two-hop evidence.",
    }


def test_factory_builds_reviewable_package_with_injected_dashscope_client(workspace_tmp_dir: Path) -> None:
    hotpotqa_path = workspace_tmp_dir / "hotpotqa.jsonl"
    project_path = workspace_tmp_dir / "project.jsonl"
    write_jsonl(hotpotqa_path, [_hotpotqa_pool()])
    write_jsonl(project_path, [_project_native_row()])

    result = run_live_api_evidence_package_factory(
        client=FakeDashScopeClient(),
        hotpotqa_candidate_pools_path=hotpotqa_path,
        output_root=workspace_tmp_dir / "artifacts",
        project_native_packets_path=project_path,
        repo_root=workspace_tmp_dir,
        sample_limit=1,
        run_live=True,
        untracked_paths=[],
    )

    claim_request = json.loads(
        (workspace_tmp_dir / "artifacts/epf_candidate_package/claim_request.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["terminal_status"] == "REVIEWABLE_CANDIDATE_PACKAGE_READY"
    assert result["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert claim_request["development_claim_upgrade_performed"] is False
    assert "operational_confidence_diagnostic" in claim_request["requested_candidate_claims"]
