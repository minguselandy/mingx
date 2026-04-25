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
    assert "qwen3.6-plus" in combined
    assert "qwen3.6-flash" in combined
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


def test_phase_b_replay_protocol_uses_revised_metric_bridge_diagnostics() -> None:
    phase_b = _read_text(PROTOCOL_DIR / "phase-b-replay-protocol.md")

    for required_input in (
        "CandidatePool",
        "ProjectionPlan",
        "BudgetWitness",
        "MaterializedContext",
        "MetricBridgeWitness",
        "diagnostics, if replaying prior diagnostic outputs",
        "cached utility/log-loss records",
    ):
        assert required_input in phase_b

    for diagnostic_name in (
        "block_ratio_lcb_b2",
        "block_ratio_lcb_star",
        "block_ratio_lcb_b3",
        "TraceDecay",
        "pairwise interaction mass",
        "triple excess",
        "greedy-vs-augmented gap",
        "metric_claim_level",
        "selector_regime_label",
        "selector_action",
    ):
        assert diagnostic_name in phase_b

    assert "gamma_hat is not a true gamma estimator" in phase_b
    assert "headline weak-submodularity diagnostic" in phase_b


def test_phase_b_replay_protocol_defines_claim_level_downgrades() -> None:
    phase_b = _read_text(PROTOCOL_DIR / "phase-b-replay-protocol.md")

    for downgrade_rule in (
        "Missing `MetricBridgeWitness`",
        "stale bridge",
        "operational-only utility",
        "missing triple evidence under higher-order risk",
        "insufficient denominator signal",
    ):
        assert downgrade_rule in phase_b

    assert "operational_utility_only" in phase_b
    assert "Vinfo_proxy_certified" in phase_b
    assert "ambiguous" in phase_b


def test_extraction_docs_state_m_star_to_m_bridge_risk_boundary() -> None:
    phase_tree = _read_text(ROOT / "docs" / "phase-tree-crosswalk.md")
    phase1 = _read_text(PROTOCOL_DIR / "phase1-protocol.md")
    phase2 = _read_text(PROTOCOL_DIR / "phase2-design.md")
    phase4 = _read_text(PROTOCOL_DIR / "phase4-design-skeleton.md")
    combined = "\n".join((phase_tree, phase1, phase2, phase4))

    assert "M* -> M bridge risk" in combined
    assert (
        "formal approximation statements apply to optimization over extracted candidate pool `M`"
        in combined
    )
    assert "extraction uniformity is a testable assumption, not a theorem" in combined.lower()
    assert "do not prove selector-regime validity" in combined
    assert "MetricBridgeWitness" in combined
    assert "extraction-risk reporting" in combined


def test_extraction_protocol_vocabulary_and_c_effective_formula_are_documented() -> None:
    phase2 = _read_text(PROTOCOL_DIR / "phase2-design.md")

    for term in (
        "p_simple",
        "c_high",
        "c_low",
        "c_effective",
        "Delta_hat",
        "captured",
        "captured_with_overgeneralization_core_preserved",
        "captured_with_overgeneralization_core_changed",
        "missing",
        "annotation reliability",
        "contamination status",
    ):
        assert term in phase2

    assert "c_effective = p_simple * c_high + (1 - p_simple) * c_low" in phase2


def test_extraction_docs_do_not_turn_completeness_into_theorem_extension() -> None:
    phase_tree = _read_text(ROOT / "docs" / "phase-tree-crosswalk.md")
    phase1 = _read_text(PROTOCOL_DIR / "phase1-protocol.md")
    phase2 = _read_text(PROTOCOL_DIR / "phase2-design.md")
    phase4 = _read_text(PROTOCOL_DIR / "phase4-design-skeleton.md")
    combined = "\n".join((phase_tree, phase1, phase2, phase4))
    combined_lower = combined.lower()

    for forbidden_claim in (
        "extraction completeness extends the weak-submodular guarantee",
        "c_effective extends the weak-submodular guarantee",
        "extraction uniformity proves selector-regime validity",
        "extraction audit proves selector-regime validity",
    ):
        assert forbidden_claim not in combined_lower

    assert (
        "does not extend the weak-submodular theorem from `M` to `M*`"
        in combined
    )
