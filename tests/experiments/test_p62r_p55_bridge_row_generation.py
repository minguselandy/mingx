from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from conftest import ROOT
from cps.benchmarks.schemas import canonical_jsonl
from cps.benchmarks.schemas import make_benchmark_instance
from cps.benchmarks.schemas import make_evidence_packet
from cps.experiments.bridge_row_schema import ACTIVE_STRATUM
from cps.experiments.bridge_row_schema import DATASET
from cps.experiments.bridge_row_schema import DEFAULT_MATERIALIZATION_POLICY
from cps.experiments.bridge_row_schema import HOTPOTQA_DATASET
from cps.experiments.bridge_row_schema import HOTPOTQA_TASK_FAMILY
from cps.experiments.bridge_row_schema import P55BridgeRow
from cps.experiments.bridge_row_schema import TASK_FAMILY
from cps.experiments.bridge_row_schema import bridge_row_key
from cps.experiments.bridge_row_schema import canonical_bridge_row_jsonl
from cps.experiments.bridge_row_schema import delta_record_key
from cps.experiments.bridge_row_schema import make_materialized_context_hash
from cps.experiments.bridge_row_validation import validate_bridge_row
from cps.experiments.bridge_row_validation import validate_bridge_rows
from cps.experiments.p55_bridge_rows_from_benchmarks import run_p62r_bridge_row_generation


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return path


def _candidate_instance():
    packet = make_evidence_packet(
        dataset="FEVER",
        split="dev",
        instance_id="fever-1",
        content="The Eiffel Tower is a landmark in Paris.",
        gold_support_label="gold_supporting",
        source_doc_id="Eiffel_Tower",
        span={"start": 2, "end": 2, "unit": "sentence"},
        source_packet_key="gold-1",
    )
    return make_benchmark_instance(
        dataset="FEVER",
        split="dev",
        instance_id="fever-1",
        query="The Eiffel Tower is located in Paris.",
        target_label="SUPPORTED",
        packets=[packet],
    )


def _candidate_pool_path(workspace_tmp_dir: Path) -> Path:
    instance = _candidate_instance()
    path = workspace_tmp_dir / "fever_candidate_pools.jsonl"
    path.write_text(canonical_jsonl([instance]), encoding="utf-8")
    return path


def _hotpot_candidate_instance():
    packet = make_evidence_packet(
        dataset="HotpotQA",
        split="dev",
        instance_id="hotpot-1",
        content="It was written by English author George Orwell.",
        gold_support_label="gold_supporting",
        source_doc_id="Nineteen Eighty-Four",
        span={"start": 1, "end": 1, "unit": "sentence"},
        source_packet_key="gold-1",
    )
    return make_benchmark_instance(
        dataset="HotpotQA",
        split="dev",
        instance_id="hotpot-1",
        query="Who wrote Nineteen Eighty-Four?",
        target_label="George Orwell",
        packets=[packet],
        task_family="hotpotqa_answer_support_selection",
        target_type="answer_string",
        adapter_name="hotpot_adapter",
    )


def _hotpot_candidate_pool_path(workspace_tmp_dir: Path) -> Path:
    path = workspace_tmp_dir / "hotpotqa_candidate_pools.jsonl"
    path.write_text(canonical_jsonl([_hotpot_candidate_instance()]), encoding="utf-8")
    return path


def _delta_record(instance=None, **overrides) -> dict:
    instance = instance or _candidate_instance()
    packet_id = instance.candidate_pool.packets[0].packet_id
    row = {
        "active_stratum": ACTIVE_STRATUM,
        "block_A_packet_ids": [packet_id],
        "block_size": 1,
        "candidate_pool_hash": instance.candidate_pool.candidate_pool_hash,
        "candidate_slice_band": "top_20",
        "contamination_status": "clean",
        "context_L_packet_ids": [],
        "dataset": instance.dataset,
        "decoding_policy": "deterministic_or_documented",
        "delta_logloss": 0.25,
        "delta_utility": 0.5,
        "evaluator_id": "fixed-local-evaluator-v1",
        "instance_id": instance.instance_id,
        "materialization_policy": DEFAULT_MATERIALIZATION_POLICY,
        "model_tier": "fixed_local_or_operator_approved_evaluator",
        "replicate_count": 1,
        "target_y": instance.target["label"],
        "task_family": TASK_FAMILY,
    }
    row.update(overrides)
    return row


def _hotpot_delta_record(**overrides) -> dict:
    instance = _hotpot_candidate_instance()
    packet_id = instance.candidate_pool.packets[0].packet_id
    row = _delta_record(
        instance,
        block_A_packet_ids=[packet_id],
        candidate_pool_hash=instance.candidate_pool.candidate_pool_hash,
        candidate_slice_band="hotpotqa_distractor_context",
        dataset=HOTPOTQA_DATASET,
        delta_utility=1.0,
        instance_id=instance.instance_id,
        target_y="George Orwell",
        task_family=HOTPOTQA_TASK_FAMILY,
    )
    row.update(overrides)
    return row


def _valid_row(**overrides):
    instance = _candidate_instance()
    block_ids = (_delta_record(instance)["block_A_packet_ids"][0],)
    row = P55BridgeRow(
        active_stratum=ACTIVE_STRATUM,
        task_family=TASK_FAMILY,
        dataset=DATASET,
        instance_id=instance.instance_id,
        model_tier="fixed_local_or_operator_approved_evaluator",
        materialization_policy=DEFAULT_MATERIALIZATION_POLICY,
        candidate_slice_band="top_20",
        block_size=1,
        context_L_packet_ids=(),
        block_A_packet_ids=block_ids,
        target_y="SUPPORTED",
        delta_logloss=0.25,
        delta_utility=0.5,
        replicate_count=1,
        decoding_policy="deterministic_or_documented",
        evaluator_id="fixed-local-evaluator-v1",
        candidate_pool_hash=instance.candidate_pool.candidate_pool_hash,
        materialized_context_hash=make_materialized_context_hash([], block_ids),
        contamination_status="clean",
    )
    payload = row.to_payload()
    payload.update(overrides)
    return payload


def test_valid_bridge_row_passes_validation():
    assert validate_bridge_row(_valid_row()) == ()


def test_wrong_active_stratum_rejected():
    assert "wrong_active_stratum" in validate_bridge_row(_valid_row(active_stratum="bio_attribute"))


def test_invalid_target_y_rejected():
    assert "invalid_target_y" in validate_bridge_row(_valid_row(target_y="MAYBE"))


def test_bridge_row_accepts_hotpotqa_task_family():
    packet_id = _hotpot_candidate_instance().candidate_pool.packets[0].packet_id
    row = _valid_row(
        block_A_packet_ids=[packet_id],
        candidate_pool_hash=_hotpot_candidate_instance().candidate_pool.candidate_pool_hash,
        candidate_slice_band="hotpotqa_distractor_context",
        dataset=HOTPOTQA_DATASET,
        instance_id="hotpot-1",
        materialized_context_hash=make_materialized_context_hash([], [packet_id]),
        target_y="George Orwell",
        task_family=HOTPOTQA_TASK_FAMILY,
    )

    assert validate_bridge_row(row) == ()


def test_bridge_row_rejects_unknown_task_family():
    assert "wrong_task_family" in validate_bridge_row(_valid_row(task_family="unknown_task_family"))


def test_missing_candidate_pool_hash_rejected():
    row = _valid_row()
    del row["candidate_pool_hash"]
    assert "missing_candidate_pool_hash" in validate_bridge_row(row)


def test_missing_materialized_context_hash_rejected():
    row = _valid_row()
    del row["materialized_context_hash"]
    assert "missing_materialized_context_hash" in validate_bridge_row(row)


def test_empty_block_A_rejected():
    row = _valid_row(block_A_packet_ids=[], block_size=0)
    errors = validate_bridge_row(row)
    assert "empty_block_A_packet_ids" in errors
    assert "invalid_block_size" in errors


def test_block_size_mismatch_rejected():
    assert "block_size_mismatch" in validate_bridge_row(_valid_row(block_size=2))


def test_failed_contamination_rejected():
    assert "contamination_failed" in validate_bridge_row(_valid_row(contamination_status="failed"))


def test_duplicate_row_identity_rejected():
    rows = [_valid_row(), _valid_row()]
    result = validate_bridge_rows(rows)
    assert result.schema_valid is False
    assert any("duplicate_row_identity" in error for error in result.errors)


def test_row_key_includes_dataset_target_model_and_materialization():
    key = bridge_row_key(_valid_row())

    assert key.dataset == "FEVER"
    assert key.target_y == "SUPPORTED"
    assert key.model_tier == "fixed_local_or_operator_approved_evaluator"
    assert key.materialization_policy == DEFAULT_MATERIALIZATION_POLICY
    assert key != bridge_row_key(_valid_row(dataset="OTHER"))
    assert key != bridge_row_key(_valid_row(target_y="REFUTED"))
    assert key != bridge_row_key(_valid_row(model_tier="fixed-local-alt"))
    assert key != bridge_row_key(_valid_row(materialization_policy="operator_order_v2"))


def test_replicate_count_is_not_part_of_row_identity():
    first = _valid_row(replicate_count=1)
    second = _valid_row(replicate_count=2)

    assert bridge_row_key(first) == bridge_row_key(second)
    result = validate_bridge_rows([first, second])
    assert result.schema_valid is False
    assert any("duplicate_row_identity" in error for error in result.errors)


def test_duplicate_logical_rows_rejected_by_full_row_key():
    rows = [
        _valid_row(delta_logloss=0.25, delta_utility=0.5, replicate_count=1),
        _valid_row(delta_logloss=0.75, delta_utility=0.9, replicate_count=3),
    ]
    result = validate_bridge_rows(rows)

    assert result.schema_valid is False
    assert any("duplicate_row_identity" in error for error in result.errors)


def test_distinct_target_y_rows_are_not_collapsed():
    assert bridge_row_key(_valid_row(target_y="SUPPORTED")) != bridge_row_key(_valid_row(target_y="REFUTED"))


def test_distinct_model_tier_rows_are_not_collapsed():
    assert bridge_row_key(_valid_row(model_tier="tier-a")) != bridge_row_key(_valid_row(model_tier="tier-b"))


def test_distinct_materialization_policy_rows_are_not_collapsed():
    assert bridge_row_key(_valid_row(materialization_policy="policy-a")) != bridge_row_key(
        _valid_row(materialization_policy="policy-b")
    )


def test_distinct_dataset_rows_are_not_collapsed():
    assert bridge_row_key(_valid_row(dataset="FEVER")) != bridge_row_key(_valid_row(dataset="FEVER_V2"))


def test_materialized_context_hash_is_deterministic():
    first = make_materialized_context_hash(["context-a"], ["block-b"])
    second = make_materialized_context_hash(["context-a"], ["block-b"])
    changed = make_materialized_context_hash(["context-a"], ["block-c"])

    assert first == second
    assert first != changed


def test_row_jsonl_writer_is_byte_deterministic():
    first = canonical_bridge_row_jsonl([_valid_row()])
    second = canonical_bridge_row_jsonl([_valid_row()])

    assert first == second
    assert first.endswith("\n")


def test_missing_candidate_pool_input_emits_blocked_report(workspace_tmp_dir):
    output_path = workspace_tmp_dir / "operator_rows.jsonl"
    blocked_path = workspace_tmp_dir / "blocked.json"
    report = run_p62r_bridge_row_generation(
        candidate_pools_jsonl=workspace_tmp_dir / "missing_candidate_pools.jsonl",
        delta_records_jsonl=workspace_tmp_dir / "missing_delta_records.jsonl",
        output_jsonl=output_path,
        blocked_report_json=blocked_path,
    )

    assert report["status"] == "blocked_no_candidate_pools_or_evaluator"
    assert report["rows_generated"] == 0
    assert report["rows_validated"] == 0
    assert "missing_candidate_pools" in report["reason_codes"]
    assert blocked_path.exists()
    assert not output_path.exists()


def test_missing_evaluator_delta_input_emits_blocked_report(workspace_tmp_dir):
    output_path = workspace_tmp_dir / "operator_rows.jsonl"
    blocked_path = workspace_tmp_dir / "blocked.json"
    report = run_p62r_bridge_row_generation(
        candidate_pools_jsonl=_candidate_pool_path(workspace_tmp_dir),
        delta_records_jsonl=workspace_tmp_dir / "missing_delta_records.jsonl",
        output_jsonl=output_path,
        blocked_report_json=blocked_path,
    )

    assert report["status"] == "blocked_no_candidate_pools_or_evaluator"
    assert "missing_evaluator_delta_records" in report["reason_codes"]
    assert blocked_path.exists()
    assert not output_path.exists()


def test_no_operator_rows_written_when_blocked(workspace_tmp_dir):
    output_path = workspace_tmp_dir / "operator_inputs" / "p55_rows.jsonl"
    run_p62r_bridge_row_generation(
        candidate_pools_jsonl=workspace_tmp_dir / "missing_candidate_pools.jsonl",
        delta_records_jsonl=workspace_tmp_dir / "missing_delta_records.jsonl",
        output_jsonl=output_path,
        blocked_report_json=workspace_tmp_dir / "blocked.json",
    )

    assert not output_path.exists()


def test_fixture_candidate_pool_and_delta_records_generate_valid_rows(workspace_tmp_dir):
    instance = _candidate_instance()
    candidate_path = _candidate_pool_path(workspace_tmp_dir)
    delta_path = _write_jsonl(workspace_tmp_dir / "delta_records.jsonl", [_delta_record(instance)])
    output_path = workspace_tmp_dir / "operator_rows.jsonl"
    summary_path = workspace_tmp_dir / "summary.json"

    summary = run_p62r_bridge_row_generation(
        candidate_pools_jsonl=candidate_path,
        delta_records_jsonl=delta_path,
        output_jsonl=output_path,
        blocked_report_json=workspace_tmp_dir / "blocked.json",
        summary_json=summary_path,
    )

    assert summary["status"] == "rows_generated_pending_calibration"
    assert summary["rows_generated"] == 1
    assert summary["rows_validated"] == 1
    assert output_path.exists()
    row = json.loads(output_path.read_text(encoding="utf-8").strip())
    assert row["target_y"] == "SUPPORTED"
    assert row["delta_logloss"] == 0.25
    assert validate_bridge_row(row) == ()


def test_delta_join_requires_full_row_key_not_instance_and_pool_only(workspace_tmp_dir):
    instance = _candidate_instance()
    candidate_path = _candidate_pool_path(workspace_tmp_dir)
    delta_path = _write_jsonl(workspace_tmp_dir / "delta_records.jsonl", [_delta_record(instance, target_y="REFUTED")])
    output_path = workspace_tmp_dir / "operator_rows.jsonl"

    report = run_p62r_bridge_row_generation(
        candidate_pools_jsonl=candidate_path,
        delta_records_jsonl=delta_path,
        output_jsonl=output_path,
        blocked_report_json=workspace_tmp_dir / "blocked.json",
    )

    assert report["status"] == "blocked_no_candidate_pools_or_evaluator"
    assert "delta_row_1:full_row_key_mismatch" in report["reason_codes"]
    assert not output_path.exists()


def test_delta_join_rejects_ambiguous_or_missing_key(workspace_tmp_dir):
    instance = _candidate_instance()
    candidate_path = _candidate_pool_path(workspace_tmp_dir)
    missing_key_record = _delta_record(instance)
    missing_key_record.pop("target_y")
    missing_report = run_p62r_bridge_row_generation(
        candidate_pools_jsonl=candidate_path,
        delta_records_jsonl=_write_jsonl(workspace_tmp_dir / "missing_key_delta_records.jsonl", [missing_key_record]),
        output_jsonl=workspace_tmp_dir / "missing_key_operator_rows.jsonl",
        blocked_report_json=workspace_tmp_dir / "missing_key_blocked.json",
    )

    duplicate_report = run_p62r_bridge_row_generation(
        candidate_pools_jsonl=candidate_path,
        delta_records_jsonl=_write_jsonl(
            workspace_tmp_dir / "duplicate_delta_records.jsonl",
            [_delta_record(instance, replicate_count=1), _delta_record(instance, replicate_count=2)],
        ),
        output_jsonl=workspace_tmp_dir / "duplicate_operator_rows.jsonl",
        blocked_report_json=workspace_tmp_dir / "duplicate_blocked.json",
    )

    assert "delta_row_1:missing_target_y" in missing_report["reason_codes"]
    assert any(reason.startswith("delta_row_2:duplicate_delta_row_key") for reason in duplicate_report["reason_codes"])
    assert delta_record_key(_delta_record(instance, replicate_count=1)) == delta_record_key(
        _delta_record(instance, replicate_count=2)
    )


def test_hotpotqa_delta_record_uses_full_bridge_row_key(workspace_tmp_dir):
    candidate_path = _hotpot_candidate_pool_path(workspace_tmp_dir)
    output_path = workspace_tmp_dir / "operator_rows.jsonl"

    mismatch_report = run_p62r_bridge_row_generation(
        candidate_pools_jsonl=candidate_path,
        dataset=HOTPOTQA_DATASET,
        delta_records_jsonl=_write_jsonl(
            workspace_tmp_dir / "mismatch_delta_records.jsonl",
            [_hotpot_delta_record(target_y="Eric Arthur Blair")],
        ),
        output_jsonl=output_path,
        blocked_report_json=workspace_tmp_dir / "blocked.json",
        task_family=HOTPOTQA_TASK_FAMILY,
    )

    assert "delta_row_1:full_row_key_mismatch" in mismatch_report["reason_codes"]
    assert not output_path.exists()


def test_hotpotqa_missing_delta_records_blocks_without_operator_rows(workspace_tmp_dir):
    output_path = workspace_tmp_dir / "operator_rows.jsonl"
    report = run_p62r_bridge_row_generation(
        candidate_pools_jsonl=_hotpot_candidate_pool_path(workspace_tmp_dir),
        dataset=HOTPOTQA_DATASET,
        delta_records_jsonl=workspace_tmp_dir / "missing_hotpotqa_delta_records.jsonl",
        output_jsonl=output_path,
        blocked_report_json=workspace_tmp_dir / "hotpotqa_blocked.json",
        task_family=HOTPOTQA_TASK_FAMILY,
    )

    assert report["status"] == "blocked_hotpotqa_candidate_pools_or_evaluator"
    assert "missing_evaluator_delta_records" in report["reason_codes"]
    assert not output_path.exists()


def test_hotpotqa_blocked_report_preserves_no_claim_upgrade(workspace_tmp_dir):
    report = run_p62r_bridge_row_generation(
        candidate_pools_jsonl=workspace_tmp_dir / "missing_hotpotqa_candidate_pools.jsonl",
        dataset=HOTPOTQA_DATASET,
        delta_records_jsonl=workspace_tmp_dir / "missing_hotpotqa_delta_records.jsonl",
        output_jsonl=workspace_tmp_dir / "operator_rows.jsonl",
        blocked_report_json=workspace_tmp_dir / "hotpotqa_blocked.json",
        task_family=HOTPOTQA_TASK_FAMILY,
    )

    assert report["claim_status"] == "no_claim_upgrade"
    assert report["dataset"] == "HotpotQA"
    assert report["task_family"] == "hotpotqa_answer_support_selection"
    assert report["calibrated_proxy_supported"] is False
    assert report["vinfo_proxy_supported"] is False


def test_cli_default_missing_inputs_writes_blocked_report(workspace_tmp_dir):
    blocked_path = workspace_tmp_dir / "blocked.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cps.experiments.p55_bridge_rows_from_benchmarks",
            "--candidate-pools-jsonl",
            str(workspace_tmp_dir / "missing_candidate_pools.jsonl"),
            "--delta-records-jsonl",
            str(workspace_tmp_dir / "missing_delta_records.jsonl"),
            "--blocked-report-json",
            str(blocked_path),
            "--output-jsonl",
            str(workspace_tmp_dir / "operator_rows.jsonl"),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(blocked_path.read_text(encoding="utf-8"))
    assert payload["status"] == "blocked_no_candidate_pools_or_evaluator"


def test_p62r_doc_preserves_claim_boundaries():
    text = (ROOT / "docs" / "experiments" / "P62R-p55-real-bridge-row-generation.md").read_text(encoding="utf-8")
    required = [
        "P62R purpose",
        "P55 remains blocked",
        "P56 remains no_traces",
        "No bridge calibration was run",
        "No calibrated_proxy_supported claim",
        "No vinfo_proxy_supported claim",
        "No measurement validation",
        "No paper evidence claim",
        "Next phase is P63R only after validated rows exist",
    ]
    for phrase in required:
        assert phrase in text
    for unsafe in (
        "measurement_validated",
        "human-label validation",
        "human-human kappa",
        "deployed V-information verification",
        "global calibrated proxy support",
        "global V-information proxy support",
        "paper evidence",
        "P55 unblocked",
        "P56 unblocked",
        "calibrated_proxy_supported",
        "vinfo_proxy_supported",
    ):
        for match in re.finditer(re.escape(unsafe), text):
            window = text[max(0, match.start() - 140) : match.end() + 140].lower()
            assert any(marker in window for marker in ("no ", "denied", "blocked", "only after", "not "))
