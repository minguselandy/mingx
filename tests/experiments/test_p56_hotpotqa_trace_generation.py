from __future__ import annotations

import json
from pathlib import Path

import pytest

from cps.experiments.p56_hotpotqa_dispatch_traces import (
    BUDGETS,
    MINIMAL_SELECTORS,
    OPERATIONAL_METRIC_CLAIM_LEVEL,
    generate_hotpotqa_operational_traces,
    run_hotpotqa_p56_trace_generation,
    validate_p56_traces,
    write_p56_trace_jsonl,
)


def _pool() -> dict:
    return {
        "candidate_pool": {
            "candidate_pool_hash": "pool-hash-1",
            "packets": [
                {
                    "content": "Alice founded Example Labs in 1999.",
                    "gold_support_label": "gold_supporting",
                    "packet_id": "p-gold-1",
                    "source_doc_id": "Alice",
                    "token_cost": 8,
                },
                {
                    "content": "Example Labs was founded after Alice left school.",
                    "gold_support_label": "gold_supporting",
                    "packet_id": "p-gold-2",
                    "source_doc_id": "Example Labs",
                    "token_cost": 9,
                },
                {
                    "content": "The city has several public parks.",
                    "gold_support_label": "same_context_distractor",
                    "packet_id": "p-noise-1",
                    "source_doc_id": "City",
                    "token_cost": 7,
                },
                {
                    "content": "Bob wrote a book about public libraries.",
                    "gold_support_label": "same_context_distractor",
                    "packet_id": "p-noise-2",
                    "source_doc_id": "Bob",
                    "token_cost": 8,
                },
            ]
        },
        "dataset": "HotpotQA",
        "instance_id": "hotpot-1",
        "query": "Who founded Example Labs?",
        "schema_version": "benchmark_instance_v1",
        "split": "dev_distractor",
        "target": {"label": "Alice", "target_type": "answer_string"},
        "task_family": "hotpotqa_answer_support_selection",
    }


def test_generate_hotpotqa_traces_for_selector_budget_matrix():
    traces, report = generate_hotpotqa_operational_traces([_pool()], budgets=(16, 32))

    assert report["traces_generated"] == len(MINIMAL_SELECTORS) * 2
    assert report["traces_validated"] == report["traces_generated"]
    assert {trace["dataset"] for trace in traces} == {"HotpotQA"}
    assert {trace["task_family"] for trace in traces} == {"hotpotqa_answer_support_selection"}
    assert {trace["budget_B_i"] for trace in traces} == {16, 32}
    assert {trace["selector_name"] for trace in traces} == set(MINIMAL_SELECTORS)
    assert {trace["metric_claim_level"] for trace in traces} == {OPERATIONAL_METRIC_CLAIM_LEVEL}
    assert {trace["metric_bridge_witness"]["bridge_status"] for trace in traces} == {"failed_or_absent"}
    assert validate_p56_traces(traces).schema_valid is True


def test_gold_oracle_is_marked_non_deployable_upper_bound():
    traces, _report = generate_hotpotqa_operational_traces([_pool()], budgets=(20,))
    oracle = next(trace for trace in traces if trace["selector_name"] == "gold_support_oracle_upper_bound")

    assert oracle["projection_plan"]["selector_deployability"] == "non_deployable_upper_bound"
    assert oracle["projection_plan"]["non_deployable_upper_bound"] is True
    assert oracle["evaluation"]["supporting_fact_recall_at_budget"] == 1.0


def test_trace_validation_rejects_selected_id_outside_candidate_pool():
    traces, _report = generate_hotpotqa_operational_traces([_pool()], budgets=(16,))
    broken = dict(traces[0])
    broken["selected_packet_ids"] = [*broken["selected_packet_ids"], "missing-packet"]

    validation = validate_p56_traces([broken])

    assert validation.schema_valid is False
    assert "row_1:selected_packet_ids_not_in_considered_candidates" in validation.errors


def test_trace_validation_rejects_incomplete_excluded_ids():
    traces, _report = generate_hotpotqa_operational_traces([_pool()], budgets=(16,))
    broken = dict(traces[0])
    broken["excluded_packet_ids"] = []

    validation = validate_p56_traces([broken])

    assert validation.schema_valid is False
    assert "row_1:considered_selected_excluded_not_complete" in validation.errors


def test_trace_validation_rejects_metric_claim_upgrade():
    traces, _report = generate_hotpotqa_operational_traces([_pool()], budgets=(16,))
    broken = dict(traces[0])
    broken["metric_claim_level"] = "calibrated_proxy_supported"

    validation = validate_p56_traces([broken])

    assert validation.schema_valid is False
    assert "row_1:metric_claim_level_not_operational_utility_only" in validation.errors


def test_trace_validation_rejects_invalid_selector_name():
    traces, _report = generate_hotpotqa_operational_traces([_pool()], budgets=(16,))
    broken = dict(traces[0])
    broken["selector_name"] = "unsupported_selector"

    validation = validate_p56_traces([broken])

    assert validation.schema_valid is False
    assert "row_1:invalid_selector_name" in validation.errors


def test_trace_jsonl_is_byte_deterministic(workspace_tmp_dir: Path):
    traces, _report = generate_hotpotqa_operational_traces([_pool()], budgets=(16,))
    output_path = workspace_tmp_dir / "traces.jsonl"

    write_p56_trace_jsonl(output_path, traces)
    first = output_path.read_bytes()
    write_p56_trace_jsonl(output_path, traces)
    second = output_path.read_bytes()

    assert first == second
    assert str(workspace_tmp_dir) not in first.decode("utf-8")


def test_run_writes_operational_artifacts(workspace_tmp_dir: Path):
    pools_path = workspace_tmp_dir / "candidate_pools.jsonl"
    pools_path.write_text(json.dumps(_pool(), ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    traces_path = workspace_tmp_dir / "p56_realistic_dispatch_traces.jsonl"
    report_path = workspace_tmp_dir / "p56_hotpotqa_trace_generation_report.json"
    doc_path = workspace_tmp_dir / "P56-hotpotqa-operational-dispatch-traces.md"

    result = run_hotpotqa_p56_trace_generation(
        budgets=(16,),
        candidate_pools_path=pools_path,
        limit=1,
        report_path=report_path,
        traces_path=traces_path,
        doc_path=doc_path,
    )

    assert result["traces_generated"] == len(MINIMAL_SELECTORS)
    assert result["traces_validated"] == len(MINIMAL_SELECTORS)
    assert traces_path.exists()
    assert report_path.exists()
    assert doc_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["metric_claim_level"] == OPERATIONAL_METRIC_CLAIM_LEVEL
    assert report["metric_bridge_witness"]["bridge_status"] == "failed_or_absent"
    assert "calibrated_proxy_supported" in report["denied_claims"]


def test_missing_candidate_pool_file_fails_closed(workspace_tmp_dir: Path):
    with pytest.raises(FileNotFoundError):
        run_hotpotqa_p56_trace_generation(
            candidate_pools_path=workspace_tmp_dir / "missing.jsonl",
            report_path=workspace_tmp_dir / "report.json",
            traces_path=workspace_tmp_dir / "traces.jsonl",
            doc_path=workspace_tmp_dir / "doc.md",
        )
