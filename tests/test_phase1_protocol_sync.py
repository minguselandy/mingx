from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_DIR = ROOT / "docs" / "protocols"
RUNS_DIR = ROOT / "configs" / "runs"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_protocol_docs_are_synced_to_qwen3_and_contamination_gate() -> None:
    phase1_protocol = _read_text(PROTOCOL_DIR / "phase1-protocol.md")
    readiness = _read_text(PROTOCOL_DIR / "execution-readiness-checklist.md")
    phase0_spec = _read_text(PROTOCOL_DIR / "phase0-specification.md")

    combined = "\n".join((phase1_protocol, readiness, phase0_spec))

    assert "claude-opus-4-7" not in combined
    assert "claude-haiku-4-5-20251001" not in combined
    assert "qwen3-32b" in combined
    assert "qwen3-14b" in combined
    assert "enable_thinking = false" in combined
    assert "contamination diagnostic" in combined.lower()


def test_protocol_docs_mark_current_live_runs_as_pilot_only() -> None:
    phase1_protocol = _read_text(PROTOCOL_DIR / "phase1-protocol.md")
    readiness = _read_text(PROTOCOL_DIR / "execution-readiness-checklist.md")

    assert "question_paragraph_limit = 5" in phase1_protocol
    assert "per_hop_count" in phase1_protocol
    assert "must not be consumed as Phase 2 statistical inputs" in phase1_protocol
    assert "must not be treated as Phase 2 statistical inputs" in readiness


def test_protocol_full_configs_do_not_set_paragraph_limit() -> None:
    for name in ("protocol-full-mock.json", "protocol-full-live.json"):
        payload = json.loads((RUNS_DIR / name).read_text(encoding="utf-8"))
        assert payload["scope_mode"] == "protocol_full"
        assert "question_paragraph_limit" not in payload
        assert payload["calibration"]["per_hop_count"] == 10
        assert payload["small_full_n"]["questions"] == "all"
        assert payload["frontier_calibration"]["questions"] == "calibration_manifest"


def test_pilot_run_configs_are_explicitly_reduced_scope() -> None:
    for name in (
        "smoke.json",
        "live-pilot.json",
        "live-mini-batch.json",
        "live-calibration-p2.json",
        "live-calibration-p3.json",
    ):
        payload = json.loads((RUNS_DIR / name).read_text(encoding="utf-8"))
        assert payload["scope_mode"] == "pilot_reduced_scope"


def test_runs_readme_documents_two_stage_protocol_full_and_live_readiness() -> None:
    runs_readme = _read_text(RUNS_DIR / "README.md")

    assert "two-stage pre-flight" in runs_readme
    assert "--fill-synthetic-passthrough" in runs_readme
    assert "pipeline_status" in runs_readme
    assert "measurement_status" in runs_readme
    assert "`budget` block" in runs_readme
    assert "PHASE1_ENABLE_LIVE_TESTS=1" in runs_readme
    assert "gate_decision = fail" in runs_readme
    assert "contamination_escalation_bundle.json" in runs_readme


def test_openworker_trace_audit_template_tracks_required_fields_and_scope_bands() -> None:
    template = _read_text(PROTOCOL_DIR / "openworker-trace-audit-template.md")

    for field_name in (
        "candidate pool",
        "greedy trace",
        "selected set",
        "materialized context",
        "extraction alignment",
    ):
        assert field_name in template
    for scope_name in ("one-week port", "one-month effort", "multi-month project"):
        assert scope_name in template
    assert "already exported" in template
    assert "partially exported" in template
    assert "not exported" in template
