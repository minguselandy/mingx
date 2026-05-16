from __future__ import annotations

import json
import re
from pathlib import Path

from conftest import assert_importing_modules_does_not_load_forbidden_sdks

from cps.experiments.realistic_dispatch_replay import (
    compute_candidate_pool_hash,
    run_p56_realistic_dispatch_replay,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "runs" / "realistic-dispatch-replay-p56.json"
VOLATILE_PATTERN = re.compile(
    r"timestamp|uuid|api_key|secret|C:\\|/home/|/mnt/",
    re.IGNORECASE,
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _config(workspace_tmp_dir: Path, input_path: Path, output_dir: Path) -> Path:
    payload = _read_json(CONFIG_PATH)
    payload["input_traces_path"] = input_path.as_posix()
    payload["output_dir"] = output_dir.as_posix()
    config_path = workspace_tmp_dir / "p56-config.json"
    _write_json(config_path, payload)
    return config_path


def _base_trace(**overrides: object) -> dict:
    considered_ids = ["candidate-a", "candidate-b", "candidate-c"]
    row: dict[str, object] = {
        "agent_id": "agent-a",
        "budget_witness_hash": "budget-hash-a",
        "candidate_pool_count": 3,
        "candidate_pool_hash": compute_candidate_pool_hash(considered_ids),
        "considered_candidate_ids": considered_ids,
        "data_source_kind": "operator_imported_traces",
        "dispatch_id": "dispatch-a",
        "effective_sample_size": 8,
        "evaluator_policy": "offline_replay_evaluator_v1",
        "excluded_candidate_ids": ["candidate-b", "candidate-c"],
        "materialization_policy": "fixed_context_materialization_v1",
        "materialized_context_hash": "materialized-hash-a",
        "metric_bridge_active_stratum": "evidence_packet_selection_microtask_v1",
        "metric_bridge_contract_id": "diagnostic_threshold_contract_v12_template",
        "metric_bridge_freshness": "fresh",
        "metric_bridge_witness_status": "present",
        "metric_policy": "replay_metric_policy_v1",
        "operator_approval_ref": "operator-approved-imported-traces",
        "projection_plan_hash": "projection-plan-hash-a",
        "realized_token_count": 120,
        "replicate_count": 2,
        "replay_intervention_id": "replay-intervention-a",
        "round_id": "round-a",
        "run_id": "run-a",
        "selected_candidate_ids": ["candidate-a"],
        "selected_token_estimate": 120,
        "trace_schema_version": "p56_realistic_dispatch_trace.v1",
    }
    row.update(overrides)
    return row


def _run_with_rows(workspace_tmp_dir: Path, rows: list[dict] | None, raw_text: str | None = None) -> dict:
    input_path = workspace_tmp_dir / "inputs" / "traces.jsonl"
    output_dir = workspace_tmp_dir / "outputs"
    if rows is not None:
        _write_jsonl(input_path, rows)
    elif raw_text is not None:
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(raw_text, encoding="utf-8")

    config_path = _config(workspace_tmp_dir, input_path, output_dir)
    return run_p56_realistic_dispatch_replay(config_path)


def test_importing_p56_replay_module_does_not_load_live_sdks() -> None:
    assert_importing_modules_does_not_load_forbidden_sdks(
        ["cps.experiments.realistic_dispatch_replay"]
    )


def test_absent_trace_file_produces_no_imported_traces_report(workspace_tmp_dir: Path) -> None:
    result = _run_with_rows(workspace_tmp_dir, rows=None)

    assert result["trace_file_status"] == "absent"
    assert result["claim_gate_result"] == "no_imported_traces"
    assert result["traces_imported"] == 0
    assert result["traces_validated"] == 0
    assert result["paper_evidence_eligible"] is False
    assert result["measurement_validation_claim"] is False
    assert result["vinfo_proxy_supported_allowed"] is False
    assert result["calibrated_proxy_supported_allowed"] is False
    assert result["next_phase_allowed"] is False


def test_empty_trace_file_produces_no_imported_traces_report(workspace_tmp_dir: Path) -> None:
    result = _run_with_rows(workspace_tmp_dir, rows=None, raw_text="")

    assert result["trace_file_status"] == "empty"
    assert result["claim_gate_result"] == "no_imported_traces"
    assert result["traces_imported"] == 0
    assert result["traces_validated"] == 0
    assert result["paper_evidence_eligible"] is False


def test_blank_or_comment_only_trace_file_produces_no_imported_traces_report(workspace_tmp_dir: Path) -> None:
    result = _run_with_rows(workspace_tmp_dir, rows=None, raw_text="\n# no traces yet\n// none\n")

    assert result["trace_file_status"] == "empty"
    assert result["claim_gate_result"] == "no_imported_traces"
    assert result["traces_imported"] == 0
    assert result["traces_validated"] == 0


def test_missing_dispatch_identity_is_not_replay_comparable(workspace_tmp_dir: Path) -> None:
    row = _base_trace(run_id="")
    result = _run_with_rows(workspace_tmp_dir, [row])

    assert result["replay_classification_counts"]["not_replay_comparable"] == 1
    assert result["records"][0]["classification"] == "not_replay_comparable"
    assert result["paper_evidence_eligible"] is False


def test_selected_only_trace_is_not_selector_comparable(workspace_tmp_dir: Path) -> None:
    row = _base_trace(considered_candidate_ids=[])
    result = _run_with_rows(workspace_tmp_dir, [row])

    assert result["replay_classification_counts"]["not_selector_comparable"] == 1
    assert result["records"][0]["classification"] == "not_selector_comparable"
    assert result["selected_only_count"] == 1


def test_candidate_pool_hash_mismatch_fails_closed(workspace_tmp_dir: Path) -> None:
    row = _base_trace(candidate_pool_hash="sha256:does-not-match")
    result = _run_with_rows(workspace_tmp_dir, [row])

    assert result["replay_classification_counts"]["fail_closed_candidate_pool_mismatch"] == 1
    assert result["records"][0]["classification"] == "fail_closed_candidate_pool_mismatch"
    assert result["candidate_pool_mismatch_count"] == 1
    assert result["paper_evidence_eligible"] is False


def test_complete_fixture_only_trace_remains_engineering_evidence(workspace_tmp_dir: Path) -> None:
    row = _base_trace(data_source_kind="fixture_test_only")
    result = _run_with_rows(workspace_tmp_dir, [row])

    assert result["replay_classification_counts"]["fixture_only_engineering_evidence"] == 1
    assert result["records"][0]["classification"] == "fixture_only_engineering_evidence"
    assert result["paper_evidence_eligible"] is False
    assert result["vinfo_proxy_supported_allowed"] is False
    assert result["calibrated_proxy_supported_allowed"] is False


def test_complete_trace_with_stale_bridge_downgrades_metric_claim(workspace_tmp_dir: Path) -> None:
    row = _base_trace(metric_bridge_freshness="stale")
    result = _run_with_rows(workspace_tmp_dir, [row])

    assert result["replay_classification_counts"]["replay_usable_metric_downgraded"] == 1
    assert result["records"][0]["classification"] == "replay_usable_metric_downgraded"
    assert result["metric_claim_level"] == "ambiguous_metric"
    assert result["calibrated_proxy_supported_allowed"] is False
    assert result["vinfo_proxy_supported_allowed"] is False


def test_metric_bridge_witness_presence_alone_is_not_support(workspace_tmp_dir: Path) -> None:
    row = _base_trace(
        metric_bridge_witness_status="present",
        metric_bridge_freshness="missing",
    )
    result = _run_with_rows(workspace_tmp_dir, [row])

    assert result["records"][0]["classification"] == "replay_usable_metric_downgraded"
    assert result["metric_bridge_status_counts"]["missing"] == 1
    assert result["calibrated_proxy_supported_allowed"] is False
    assert result["vinfo_proxy_supported_allowed"] is False


def test_replay_comparable_trace_does_not_imply_metric_support(workspace_tmp_dir: Path) -> None:
    result = _run_with_rows(workspace_tmp_dir, [_base_trace()])

    assert result["replay_classification_counts"]["replay_comparable"] == 1
    assert result["records"][0]["classification"] == "replay_comparable"
    assert result["metric_claim_level"] == "ambiguous_metric"
    assert result["paper_evidence_eligible"] is False
    assert result["calibrated_proxy_supported_allowed"] is False
    assert result["vinfo_proxy_supported_allowed"] is False


def test_canonical_artifacts_are_deterministic_and_volatility_free(workspace_tmp_dir: Path) -> None:
    result_one = _run_with_rows(workspace_tmp_dir / "one", [_base_trace()])
    result_two = _run_with_rows(workspace_tmp_dir / "two", [_base_trace()])

    for result in (result_one, result_two):
        output_dir = Path(result["output_dir"])
        assert _read_json(output_dir / "manifest.json")
        assert _read_json(output_dir / "claim_gate_report.json")
        assert (output_dir / "report.md").read_text(encoding="utf-8")
        for artifact in output_dir.iterdir():
            text = artifact.read_text(encoding="utf-8")
            assert not VOLATILE_PATTERN.search(text)

    first_outputs = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(Path(result_one["output_dir"]).iterdir())
    }
    second_outputs = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(Path(result_two["output_dir"]).iterdir())
    }
    assert first_outputs == second_outputs
