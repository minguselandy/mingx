from __future__ import annotations

import json
from pathlib import Path

from cps.benchmarks.hashing import canonical_json_dumps
from cps.evaluators.teacher_forced_logprobe_backend import CLAIM_STATUS
from cps.evaluators.teacher_forced_logprobe_backend import build_backend_capability_report
from cps.evaluators.teacher_forced_logprobe_backend import reconstruct_evidence_path_target_text
from cps.evaluators.teacher_forced_logprobe_backend import run_teacher_forced_logprobe_backend_package
from cps.evaluators.teacher_forced_scoring_contract import build_teacher_forced_score_record


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical_json_dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def _target_row(index: int, *, original_instance_id: str, target_text_hash: str) -> dict:
    return {
        "candidate_pool_hash": f"pool-{original_instance_id}",
        "claim_status": CLAIM_STATUS,
        "evidence_path_packet_hashes": [f"packet-hash-{original_instance_id}-a"],
        "evidence_path_packet_ids": [f"packet-{original_instance_id}-a"],
        "evidence_path_source_doc_ids": [f"Doc {original_instance_id}"],
        "evidence_path_spans": ["sentence:0-1"],
        "fever_disabled": True,
        "materialization_policy": "route4a_materialized_context_with_source_boundaries",
        "original_instance_id": original_instance_id,
        "schema_version": "evidence_path_target_row_v1",
        "target_char_length": 64 + index,
        "target_path_length": 1,
        "target_row_id": f"target-row-{index}",
        "target_text_hash": target_text_hash,
        "target_tokenization_metadata": {
            "approx_whitespace_token_count": 4,
            "line_count": 2,
            "tokenization_policy": "provider_tokenization_recorded_during_live_probe",
        },
        "target_type": "evidence_path_nll",
    }


def _build_inputs(root: Path) -> None:
    rows = [
        _target_row(1, original_instance_id="inst-a", target_text_hash="hash-a"),
        _target_row(2, original_instance_id="inst-b", target_text_hash="hash-b"),
        _target_row(3, original_instance_id="inst-a", target_text_hash="hash-a"),
    ]
    _write_jsonl(root / "artifacts/experiments/evidence_path_nll_protocol/evidence_path_target_rows.jsonl", rows)
    _write_json(
        root / "artifacts/experiments/evidence_path_nll_protocol/target_contract.json",
        {
            "claim_status": CLAIM_STATUS,
            "materialization_policy_hash": "materialization-hash",
            "prompt_template_hash": "prompt-hash",
            "target_format_hash": "target-format-hash",
        },
    )
    _write_json(
        root / "artifacts/experiments/evidence_path_nll_protocol/protocol_readiness_decision.json",
        {
            "claim_status": CLAIM_STATUS,
            "terminal_protocol_decision": "HONESTLY_BLOCKED",
        },
    )


def test_backend_capability_report_blocks_without_explicit_teacher_forced_backend():
    report = build_backend_capability_report(env={}, root=Path("."))

    assert report["teacher_forced_target_scoring_available"] is False
    assert report["blocked_reason"] == "blocked_no_teacher_forced_backend"
    assert report["chat_logprob_path_rejected_for_fixed_target_scoring"] is True
    assert report["live_api_used"] is False
    assert report["raw_responses_stored"] is False
    assert report["secrets_exposed"] is False


def test_reconstruct_evidence_path_target_text_is_deterministic():
    row = _target_row(1, original_instance_id="inst-a", target_text_hash="hash-a")

    target_text = reconstruct_evidence_path_target_text(row)

    assert target_text == "EVIDENCE_PATH_V1\n1\tDoc inst-a\tsentence:0-1\tpacket-inst-a-a\tpacket-hash-inst-a-a"
    assert "content" not in target_text.casefold()


def test_blocked_package_writes_no_fake_scoring_rows(workspace_tmp_dir):
    _build_inputs(workspace_tmp_dir)

    result = run_teacher_forced_logprobe_backend_package(root=workspace_tmp_dir, env={})

    artifact_dir = workspace_tmp_dir / "artifacts/experiments/teacher_forced_logprobe_backend"
    assert result["readiness_decision"] == "BLOCKED_NO_TEACHER_FORCED_BACKEND"
    assert result["teacher_forced_target_scoring_available"] is False
    assert (artifact_dir / "backend_capability_report.json").exists()
    assert (artifact_dir / "blocked_report.json").exists()
    assert (artifact_dir / "readiness_decision.json").exists()
    assert not (artifact_dir / "scoring_probe_rows.jsonl").exists()

    readiness = json.loads((artifact_dir / "readiness_decision.json").read_text(encoding="utf-8"))
    assert readiness["future_evidence_path_nll_bridge_pilot_allowed"] is False
    assert readiness["epn_remains_blocked"] is True
    assert readiness["route5_locked"] is True
    assert readiness["route8_locked"] is True
    assert readiness["claim_status"] == CLAIM_STATUS


def test_package_scores_bounded_probe_when_valid_backend_is_injected(workspace_tmp_dir):
    _build_inputs(workspace_tmp_dir)

    def scorer(*, prompt_text: str, fixed_target_text: str, target_row: dict, contract: dict) -> dict:
        target_token_ids = [index + 1 for index, _token in enumerate(fixed_target_text.split())]
        per_token_logprobs = [-0.5 for _token in target_token_ids]
        return build_teacher_forced_score_record(
            deterministic_settings={"seed": 0, "temperature": 0},
            fixed_target_text=fixed_target_text,
            materialization_policy_hash=contract["materialization_policy_hash"],
            per_token_logprobs=per_token_logprobs,
            prompt_template_hash=contract["prompt_template_hash"],
            prompt_text=prompt_text,
            scorer_model_id="fake-local-model",
            scoring_backend_id="fake_teacher_forced_backend",
            scoring_policy={"teacher_forced": True},
            target_format_hash=contract["target_format_hash"],
            target_token_ids=target_token_ids,
            tokenizer_id="fake-tokenizer",
            target_row_id=target_row["target_row_id"],
            target_text_hash=target_row["target_text_hash"],
        )

    result = run_teacher_forced_logprobe_backend_package(
        root=workspace_tmp_dir,
        env={},
        injected_scorer=scorer,
        probe_limit=3,
    )

    artifact_dir = workspace_tmp_dir / "artifacts/experiments/teacher_forced_logprobe_backend"
    rows = [
        json.loads(line)
        for line in (artifact_dir / "scoring_probe_rows.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    report = json.loads((artifact_dir / "scoring_probe_report.json").read_text(encoding="utf-8"))
    repeatability = json.loads((artifact_dir / "repeatability_report.json").read_text(encoding="utf-8"))

    assert result["readiness_decision"] == "TEACHER_FORCED_BACKEND_READY_FOR_EPN_BRIDGE_PROTOCOL"
    assert result["teacher_forced_target_scoring_available"] is True
    assert len(rows) == 3
    assert report["target_count_attempted"] == 3
    assert report["target_count_scored"] == 3
    assert report["unique_original_instances"] == 2
    assert report["unique_target_hashes"] == 2
    assert report["teacher_forced_target_score_available"] is True
    assert repeatability["duplicate_target_hash_count"] == 1
    assert repeatability["repeat_scoring_consistency"] in {"passed", "not_applicable"}
