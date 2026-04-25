from __future__ import annotations

from pathlib import Path
from typing import Iterable

from cps.experiments.decision import derive_metric_claim_level, derive_selector_regime_label
from cps.experiments.synthetic_benchmark import evaluate_pre_registered_validity_gate


ROOT = Path(__file__).resolve().parents[1]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _active_markdown_files() -> list[Path]:
    docs = [
        path
        for path in (ROOT / "docs").rglob("*.md")
        if "archive" not in path.relative_to(ROOT).parts
    ]
    return [
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "configs" / "runs" / "README.md",
        *sorted(docs),
    ]


def _active_experiment_files() -> list[Path]:
    return sorted((ROOT / "cps" / "experiments").glob("*.py"))


def _active_framing_files() -> list[Path]:
    return _active_markdown_files() + _active_experiment_files() + [
        ROOT / "configs" / "runs" / "synthetic-regime-smoke.json"
    ]


def _occurrence_windows(path: Path, needle: str, *, radius: int = 260) -> Iterable[str]:
    text = _read_text(path)
    lower = text.lower()
    target = needle.lower()
    start = 0
    while True:
        index = lower.find(target, start)
        if index < 0:
            return
        yield lower[max(0, index - radius) : index + len(target) + radius]
        start = index + len(target)


def _assert_occurrences_are_qualified(paths: Iterable[Path], needle: str, markers: tuple[str, ...]) -> None:
    failures: list[str] = []
    for path in paths:
        for window in _occurrence_windows(path, needle):
            if not any(marker in window for marker in markers):
                failures.append(str(path.relative_to(ROOT)))
    assert not failures, f"{needle} occurrences lack legacy/non-headline qualification: {sorted(set(failures))}"


def _valid_gate_row(regime: str, **overrides) -> dict:
    row = {
        "dispatch_id": f"{regime}-fixture",
        "regime": regime,
        "block_ratio_lcb_b2": 1.0,
        "block_ratio_lcb_star": 1.0,
        "block_ratio_lcb_star_semantics": "placeholder_conservative_min_b2_b3_not_degree_adaptive_star",
        "block_ratio_lcb_b3": 1.0,
        "block_ratio_sample_count": 4,
        "block_ratio_uninformative_count": 0,
        "trace_decay_proxy": 1.0,
        "synergy_fraction": 0.0,
        "positive_interaction_mass_ucb": 0.0,
        "triple_excess_flag": "none_detected",
        "higher_order_ambiguity_flag": False,
        "greedy_augmented_gap": 0.0,
        "metric_claim_level": "structural_synthetic_only",
        "selector_regime_label": "greedy_valid",
        "selector_action": "monitored_greedy",
        "augmented_value": 1.0,
        "greedy_value": 1.0,
    }
    row.update(overrides)
    return row


def _gate_summary(dispatch_count: int, *, metric_bridge_count: int | None = None) -> dict:
    metric_bridge_count = dispatch_count if metric_bridge_count is None else metric_bridge_count
    return {
        "dispatch_count": dispatch_count,
        "complete_artifact_sets": metric_bridge_count == dispatch_count,
        "artifact_counts": {
            "candidate_pools": dispatch_count,
            "projection_plans": dispatch_count,
            "budget_witnesses": dispatch_count,
            "materialized_contexts": dispatch_count,
            "metric_bridge_witnesses": metric_bridge_count,
            "diagnostics": dispatch_count,
        },
    }


def test_active_docs_use_revised_paper_anchor_not_v8_as_current() -> None:
    for path in (ROOT / "README.md", ROOT / "AGENTS.md"):
        text = _read_text(path)
        assert "context_projection_revised_v10.md" in text
        for window in _occurrence_windows(path, "final_paper_context_projection_submission_final_v8.md"):
            assert any(marker in window for marker in ("historical", "archive", "older draft", "reference"))
            assert "current canonical" not in window
            assert "current paper-framing anchor" not in window


def test_gamma_hat_active_occurrences_are_legacy_or_nonheadline() -> None:
    _assert_occurrences_are_qualified(
        _active_framing_files(),
        "gamma_hat",
        (
            "legacy",
            "compatibility",
            "historical",
            "archive",
            "non-headline",
            "not headline",
            "trace_decay_proxy",
            "legacy_trace_ratio",
            "not a submodularity-ratio",
            "not a true gamma estimator",
            "gamma_hat_semantics",
            "legacy_trace_decay_alias_not_submodularity_ratio",
        ),
    )


def test_policy_recommendation_active_occurrences_are_legacy_or_derived() -> None:
    _assert_occurrences_are_qualified(
        _active_framing_files(),
        "policy_recommendation",
        (
            "legacy",
            "compatibility",
            "derived",
            "alias",
            "selector_action",
            "selector_regime_label",
            "metric_claim_level",
        ),
    )


def test_primary_decision_outputs_are_documented_and_reported() -> None:
    combined = "\n".join(_read_text(path) for path in _active_markdown_files())
    for field_name in ("metric_claim_level", "selector_regime_label", "selector_action"):
        assert field_name in combined

    report_source = _read_text(ROOT / "cps" / "experiments" / "reporting.py")
    assert "Avg gamma_hat" not in report_source
    for field_name in ("metric_claim_level", "selector_regime_label", "selector_action"):
        assert field_name in report_source
    assert "placeholder_conservative_min_b2_b3_not_degree_adaptive_star" in report_source


def test_metric_bridge_decision_guardrails() -> None:
    assert derive_metric_claim_level({"metric_class": "operational_only", "drift_status": "fresh"}) == (
        "operational_utility_only"
    )
    assert derive_metric_claim_level({"metric_class": "operational_only", "drift_status": "fresh"}) != (
        "Vinfo_proxy_certified"
    )
    assert derive_metric_claim_level(None) == "ambiguous"
    assert derive_metric_claim_level({"metric_class": "log_loss_aligned", "drift_status": "stale"}) == "ambiguous"


def test_higher_order_not_evaluable_guardrail_prevents_greedy_valid() -> None:
    diagnostics = {
        "block_ratio_lcb_b2": 1.0,
        "block_ratio_lcb_star": 1.0,
        "block_ratio_lcb_star_semantics": "placeholder_conservative_min_b2_b3_not_degree_adaptive_star",
        "block_ratio_lcb_b3": None,
        "block_ratio_sample_count": 3,
        "block_ratio_uninformative_count": 0,
        "synergy_fraction": 0.0,
        "positive_interaction_mass_ucb": 0.0,
        "greedy_augmented_gap": 0.0,
        "triple_excess_flag": "not_evaluable",
        "higher_order_ambiguity_flag": True,
    }

    assert derive_selector_regime_label(diagnostics, "structural_synthetic_only", {}) == "ambiguous"


def test_pre_registered_gate_requires_metric_bridge_and_counts_ambiguity_separately() -> None:
    rows = [
        _valid_gate_row("redundancy_dominated"),
        _valid_gate_row(
            "sparse_pairwise_synergy",
            block_ratio_lcb_b2=0.8,
            block_ratio_lcb_star=0.8,
            synergy_fraction=0.2,
            positive_interaction_mass_ucb=0.5,
            selector_regime_label="ambiguous",
            selector_action="no_certified_switch",
            augmented_value=2.0,
            greedy_value=1.0,
        ),
        _valid_gate_row(
            "higher_order_synergy",
            block_ratio_lcb_b2=0.7,
            block_ratio_lcb_star=0.7,
            triple_excess_flag="positive",
            higher_order_ambiguity_flag=True,
            greedy_augmented_gap=0.5,
            selector_regime_label="escalate",
            selector_action="interaction_aware_local_search",
        ),
    ]

    result = evaluate_pre_registered_validity_gate(
        rows,
        _gate_summary(len(rows), metric_bridge_count=len(rows) - 1),
        {},
    )

    assert result["ambiguity_count"] == 1
    assert result["pre_registered_gate_passed"] is False
    assert any(failure["gate"] == "artifact_completeness" for failure in result["pre_registered_gate_failures"])
    assert any(failure["gate"] == "ambiguity_accounting" for failure in result["pre_registered_gate_failures"])


def test_phase_b_replay_protocol_revised_requirements() -> None:
    phase_b = _read_text(ROOT / "docs" / "protocols" / "phase-b-replay-protocol.md")

    assert "MetricBridgeWitness" in phase_b
    assert "block_ratio_lcb_b2" in phase_b
    assert "TraceDecay" in phase_b
    assert "path-local" in phase_b
    assert "gamma_hat is not a true gamma estimator" in phase_b
    assert "must not be described as the headline weak-submodularity diagnostic" in phase_b
