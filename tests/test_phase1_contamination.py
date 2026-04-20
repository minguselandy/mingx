from __future__ import annotations

import json
import math
from pathlib import Path

from cps.analysis.contamination import CONTAMINATION_THRESHOLD_LOGP, run_contamination_analysis
from cps.store.measurement import append_event


def _baseline_event(*, question_id: str, hop_depth: str, model_role: str, baseline_logp: float) -> dict:
    return {
        "event_type": "baseline_scored",
        "run_id": "contamination-test",
        "question_id": question_id,
        "hop_depth": hop_depth,
        "provider": "dashscope",
        "backend_id": "mock_forced_decode",
        "model_id": "qwen3-32b" if model_role == "frontier" else "qwen3-14b",
        "model_role": model_role,
        "ordering_id": None,
        "ordering": None,
        "paragraph_id": None,
        "full_logp": None,
        "loo_logp": None,
        "delta_loo": None,
        "baseline_logp": baseline_logp,
        "manifest_hash": "manifest",
        "sampling_seed": 20260418,
        "protocol_version": "phase1.v1",
        "request_fingerprint": None,
        "response_status": "mock",
        "notes": "baseline fixture",
        "payload": {},
    }


def test_contamination_analysis_reports_fail_when_threshold_fraction_is_high(workspace_tmp_dir):
    measurement_dir = workspace_tmp_dir / "measurements"
    export_dir = workspace_tmp_dir / "exports"

    append_event(measurement_dir, _baseline_event(question_id="q2-1", hop_depth="2hop", model_role="small", baseline_logp=-1.2))
    append_event(measurement_dir, _baseline_event(question_id="q2-2", hop_depth="2hop", model_role="small", baseline_logp=-0.2))
    append_event(measurement_dir, _baseline_event(question_id="q3-1", hop_depth="3hop", model_role="small", baseline_logp=-1.4))
    append_event(measurement_dir, _baseline_event(question_id="q3-2", hop_depth="3hop", model_role="small", baseline_logp=-0.1))
    append_event(measurement_dir, _baseline_event(question_id="q4-1", hop_depth="4hop", model_role="small", baseline_logp=-1.8))
    append_event(measurement_dir, _baseline_event(question_id="q4-2", hop_depth="4hop", model_role="small", baseline_logp=-1.1))
    append_event(measurement_dir, _baseline_event(question_id="q3-2", hop_depth="3hop", model_role="frontier", baseline_logp=-0.05))

    report = run_contamination_analysis(
        measurement_dir=measurement_dir,
        export_dir=export_dir,
    )

    payload = json.loads(Path(report["path"]).read_text(encoding="utf-8"))
    assert report["status"] == "computed"
    assert payload["provider_family"] == "qwen3"
    assert payload["threshold_logp"] == CONTAMINATION_THRESHOLD_LOGP
    assert payload["threshold_probability"] == 0.5
    assert payload["question_count"] == 6
    assert payload["above_threshold_count"] == 2
    assert math.isclose(payload["above_threshold_fraction"], 2 / 6)
    assert payload["gate_decision"] == "fail"
    assert payload["per_hop"]["2hop"]["above_threshold_count"] == 1
    assert payload["per_hop"]["3hop"]["above_threshold_count"] == 1
    assert payload["per_hop"]["4hop"]["above_threshold_count"] == 0
    assert payload["question_ids_above_threshold"] == ["q2-2", "q3-2"]
    selected_row = next(row for row in payload["baseline_rows"] if row["question_id"] == "q3-2")
    assert selected_row["model_role"] == "frontier"


def test_contamination_analysis_reports_warning_without_baselines(workspace_tmp_dir):
    report = run_contamination_analysis(
        measurement_dir=workspace_tmp_dir / "measurements",
        export_dir=workspace_tmp_dir / "exports",
    )

    payload = json.loads(Path(report["path"]).read_text(encoding="utf-8"))
    assert report["status"] == "pending_measurement_consumption"
    assert payload["gate_decision"] == "warning"
    assert payload["question_count"] == 0
