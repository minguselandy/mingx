from __future__ import annotations

import json
from pathlib import Path

from cps.benchmarks.hashing import canonical_json_dumps
from cps.experiments.evidence_path_nll_protocol import CLAIM_STATUS
from cps.experiments.evidence_path_nll_protocol import TERMINAL_STATUS
from cps.experiments.evidence_path_nll_protocol import build_evidence_path_target_contract
from cps.experiments.evidence_path_nll_protocol import build_evidence_path_target_rows
from cps.experiments.evidence_path_nll_protocol import run_evidence_path_nll_protocol
from cps.experiments.evidence_path_nll_protocol import validate_evidence_path_target_contract


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical_json_dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def _packet(packet_id: str, *, label: str, source_doc_id: str, start: int, hop_index: int | None) -> dict:
    return {
        "content": f"Evidence sentence for {packet_id}.",
        "dataset": "HotpotQA",
        "gold_support_label": label,
        "hash": f"hash-{packet_id}",
        "hop_index": hop_index,
        "packet_id": packet_id,
        "path_id": "gold-path",
        "provenance": {"source_doc_id": source_doc_id, "span": f"sentence:{start}-{start + 1}"},
        "retrieval_features": {},
        "source_doc_id": source_doc_id,
        "span": {"end": start + 1, "start": start, "unit": "sentence"},
        "token_cost": 9,
    }


def _build_inputs(root: Path) -> None:
    pool_hash = "pool-hash-1"
    candidate_pool = {
        "adapter_metadata": {"source": "unit-fixture"},
        "candidate_pool": {
            "candidate_pool_hash": pool_hash,
            "candidate_pool_id": "hotpot-pool-1",
            "gold_reachable_under_budget": {"512": True},
            "n_candidates": 3,
            "n_gold_packets": 2,
            "n_hard_negative_packets": 1,
            "n_random_negative_packets": 0,
            "packets": [
                _packet("gold-b", label="gold_supporting", source_doc_id="DocB", start=4, hop_index=1),
                _packet("distractor", label="same_context_distractor", source_doc_id="DocC", start=1, hop_index=None),
                _packet("gold-a", label="gold_supporting", source_doc_id="DocA", start=0, hop_index=0),
            ],
            "total_tokens": 27,
        },
        "dataset": "HotpotQA",
        "instance_id": "hotpot-1",
        "query": "Which bridge evidence supports the answer?",
        "schema_version": "benchmark_instance_v1",
        "split": "dev_distractor",
        "target": {"answer": "answer string"},
        "task_family": "multi_hop_qa",
    }
    route4_row = {
        "block_A_packet_ids": ["gold-a"],
        "candidate_pool_hash": pool_hash,
        "context_L_packet_ids": ["gold-b"],
        "delta_logloss": -0.2,
        "delta_utility": 1.0,
        "materialization_policy": "fixed_selector_order_with_source_boundaries",
        "original_instance_id": "hotpot-1",
        "target_y": "answer string",
    }
    _write_jsonl(root / "artifacts/benchmarks/hotpotqa_candidate_pools.jsonl", [candidate_pool])
    _write_jsonl(root / "artifacts/experiments/route4_bridge/bridge_rows.jsonl", [route4_row])
    _write_json(
        root / "artifacts/experiments/logprobe_bridge_repair_readiness/readiness_report.json",
        {
            "checks": {"route5_locked": True, "route8_locked": True},
            "claim_status": CLAIM_STATUS,
            "lp6_bridge_repair_run": False,
            "readiness_state": "READY_FOR_TARGET_SWITCH",
            "target_decision": "SWITCH_TO_EVIDENCE_PATH_NLL",
        },
    )
    _write_json(
        root / "artifacts/experiments/logprobe_target_redesign/target_decision.json",
        {
            "claim_status": CLAIM_STATUS,
            "disabled_decisions": ["SWITCH_TO_FEVER_LABEL_NLL"],
            "primary_decision": "SWITCH_TO_EVIDENCE_PATH_NLL",
        },
    )


def test_evidence_path_target_contract_is_canonical_and_non_claim_upgrading():
    contract = build_evidence_path_target_contract()
    validation = validate_evidence_path_target_contract(contract)

    assert validation["passed"] is True
    assert contract["claim_status"] == CLAIM_STATUS
    assert contract["target_type"] == "evidence_path_nll"
    assert contract["target_provenance"]["active_dataset"] == "HotpotQA"
    assert contract["teacher_forced_scoring_required"] is True
    assert contract["disabled_decisions"] == ["SWITCH_TO_FEVER_LABEL_NLL"]
    assert contract["route5_locked"] is True
    assert contract["route8_locked"] is True
    assert contract["target_format_hash"]
    assert contract["contract_hash"]


def test_evidence_path_row_builder_uses_gold_path_without_storing_packet_content(workspace_tmp_dir):
    _build_inputs(workspace_tmp_dir)
    candidate_pools = [
        json.loads(
            (workspace_tmp_dir / "artifacts/benchmarks/hotpotqa_candidate_pools.jsonl").read_text(encoding="utf-8")
        )
    ]
    route4_rows = [
        json.loads(
            (workspace_tmp_dir / "artifacts/experiments/route4_bridge/bridge_rows.jsonl").read_text(encoding="utf-8")
        )
    ]

    rows, report = build_evidence_path_target_rows(candidate_pools, route4_rows)

    assert report["row_builder_ready"] is True
    assert report["target_rows_built"] == 1
    assert rows[0]["evidence_path_packet_ids"] == ["gold-a", "gold-b"]
    assert rows[0]["evidence_path_source_doc_ids"] == ["DocA", "DocB"]
    assert rows[0]["target_path_length"] == 2
    assert rows[0]["target_text_hash"]
    assert "content" not in canonical_json_dumps(rows[0]).casefold()
    assert rows[0]["claim_status"] == CLAIM_STATUS


def test_protocol_writes_ready_decision_with_sanitized_fake_probe(workspace_tmp_dir):
    _build_inputs(workspace_tmp_dir)

    def fake_scorer(*, prompt: str, target_text: str, target_row: dict, scoring_policy: dict) -> dict:
        assert target_text.startswith("EVIDENCE_PATH_V1")
        assert "Evidence sentence" in prompt
        assert scoring_policy["store_raw_api_response"] is False
        return {
            "api_call_count": 1,
            "api_failure_count": 0,
            "api_success_count": 1,
            "content_match": True,
            "failure_reason_code": None,
            "model_id": "fake-logprob-model",
            "nll": 3.5,
            "prompt_token_count": 16,
            "target_char_length": len(target_text),
            "target_token_count": 8,
            "token_logprob_count": 8,
        }

    result = run_evidence_path_nll_protocol(root=workspace_tmp_dir, live_scorer=fake_scorer, live_probe_limit=1)

    assert result["terminal_status"] == TERMINAL_STATUS
    assert result["terminal_protocol_decision"] == "EVIDENCE_PATH_PROTOCOL_READY_FOR_REVIEW"
    assert result["claim_status"] == CLAIM_STATUS
    assert result["lp6_bridge_repair_run"] is False
    assert result["route5_locked"] is True
    assert result["route8_locked"] is True

    readiness = json.loads(
        (
            workspace_tmp_dir
            / "artifacts/experiments/evidence_path_nll_protocol/protocol_readiness_decision.json"
        ).read_text(encoding="utf-8")
    )
    probe = json.loads(
        (workspace_tmp_dir / "artifacts/experiments/evidence_path_nll_protocol/live_scoring_probe_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert readiness["terminal_protocol_decision"] == "EVIDENCE_PATH_PROTOCOL_READY_FOR_REVIEW"
    assert readiness["live_api_scoring_probe"]["live_api_used"] is True
    assert probe["raw_api_responses_stored"] is False
    assert "Evidence sentence" not in canonical_json_dumps(probe)


def test_protocol_blocks_honestly_when_evaluator_config_is_missing(workspace_tmp_dir):
    _build_inputs(workspace_tmp_dir)

    result = run_evidence_path_nll_protocol(
        root=workspace_tmp_dir,
        live_env={},
        live_probe_limit=1,
    )

    assert result["terminal_protocol_decision"] == "HONESTLY_BLOCKED"
    feasibility = json.loads(
        (
            workspace_tmp_dir / "artifacts/experiments/evidence_path_nll_protocol/scoring_feasibility_report.json"
        ).read_text(encoding="utf-8")
    )
    assert feasibility["scoring_status"] == "missing_evaluator_config"
    assert feasibility["live_api_used"] is False
    assert feasibility["missing_evaluator_config"]
    assert feasibility["claim_status"] == CLAIM_STATUS


def test_protocol_does_not_count_content_mismatch_as_target_score(workspace_tmp_dir):
    _build_inputs(workspace_tmp_dir)

    def mismatch_scorer(*, prompt: str, target_text: str, target_row: dict, scoring_policy: dict) -> dict:
        return {
            "api_call_count": 1,
            "api_failure_count": 0,
            "api_success_count": 1,
            "content_match": False,
            "failure_reason_code": None,
            "model_id": "fake-logprob-model",
            "nll": 2.0,
            "prompt_token_count": 12,
            "target_char_length": len(target_text),
            "target_token_count": 4,
            "token_logprob_count": 4,
        }

    result = run_evidence_path_nll_protocol(root=workspace_tmp_dir, live_scorer=mismatch_scorer, live_probe_limit=1)

    assert result["terminal_protocol_decision"] == "HONESTLY_BLOCKED"
    probe = json.loads(
        (workspace_tmp_dir / "artifacts/experiments/evidence_path_nll_protocol/live_scoring_probe_report.json").read_text(
            encoding="utf-8"
        )
    )
    feasibility = json.loads(
        (
            workspace_tmp_dir / "artifacts/experiments/evidence_path_nll_protocol/scoring_feasibility_report.json"
        ).read_text(encoding="utf-8")
    )
    assert probe["api_success_count"] == 0
    assert probe["api_failure_count"] == 1
    assert probe["probe_rows"][0]["failure_reason_code"] == "content_mismatch_no_teacher_forced_target_score"
    assert feasibility["scoring_status"] == "teacher_forced_target_score_unavailable"
