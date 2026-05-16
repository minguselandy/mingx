import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN = REPO_ROOT / "docs" / "experiments" / "P59-reprojection-replay-integration-plan.md"
TEMPLATE = REPO_ROOT / "docs" / "templates" / "reprojection-witness-replay-template.json"
REVIEW = REPO_ROOT / "docs" / "reviews" / "P59-reprojection-replay-integration-review.md"


REQUIRED_FIELDS = {
    "record_schema_version",
    "witness_id",
    "initial_run_id",
    "initial_dispatch_id",
    "initial_agent_id",
    "initial_round_id",
    "source_replay_record_id",
    "trigger_type",
    "trigger_rationale",
    "original_budget",
    "revised_budget",
    "budget_delta",
    "selector_before",
    "selector_after",
    "candidate_pool_hash_before",
    "candidate_pool_hash_after",
    "candidate_pool_expansion_documented",
    "materialized_context_hash_before",
    "materialized_context_hash_after",
    "selected_context_before",
    "selected_context_after",
    "excluded_context_before",
    "excluded_context_after",
    "context_diff_summary",
    "output_before_hash",
    "output_after_hash",
    "evaluator_policy",
    "uncertainty_label",
    "over_budget_flag",
    "metric_bridge_status",
    "metric_bridge_contract_id",
    "claim_gate_result",
    "paper_evidence_eligible",
    "measurement_validation_claim",
    "deployed_runtime_improvement_claim",
    "denied_claims",
}


REQUIRED_TRIGGERS = {
    "unknown_due_to_missing_context",
    "hallucination_risk",
    "wrong_despite_context",
    "ambiguous",
    "operator_review_requested",
    "budget_overflow",
    "candidate_pool_mismatch",
}


def _template() -> dict:
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def _plan_text() -> str:
    return PLAN.read_text(encoding="utf-8")


def test_json_template_parses_and_has_required_witness_fields() -> None:
    template = _template()

    assert REQUIRED_FIELDS.issubset(template.keys())
    assert template["paper_evidence_eligible"] is False
    assert template["measurement_validation_claim"] is False
    assert template["deployed_runtime_improvement_claim"] is False
    assert template["metric_bridge_status"] == "missing"
    assert template["claim_gate_result"] == "audit_only_or_not_comparable"


def test_required_trigger_types_are_supported_in_plan_and_template() -> None:
    plan = _plan_text()
    template = _template()

    assert REQUIRED_TRIGGERS.issubset(set(template["allowed_trigger_types"]))
    for trigger in REQUIRED_TRIGGERS:
        assert trigger in plan


def test_fail_closed_decision_rules_are_encoded() -> None:
    rules = _template()["decision_rules"]

    assert rules["identity_mismatch"]["classification"] == "not_comparable"
    assert rules["identity_mismatch"]["paper_evidence_eligible"] is False
    assert rules["identity_mismatch"]["no_metric_claim_upgrade"] is True

    assert rules["candidate_pool_mismatch_without_documented_expansion"]["classification"] == (
        "fail_closed_candidate_pool_mismatch"
    )
    assert rules["candidate_pool_mismatch_without_documented_expansion"]["paper_evidence_eligible"] is False
    assert rules["candidate_pool_mismatch_without_documented_expansion"]["no_metric_claim_upgrade"] is True

    assert rules["over_budget_revised_context"]["classification"] == "operational_violation"
    assert rules["over_budget_revised_context"]["paper_evidence_eligible"] is False
    assert rules["over_budget_revised_context"]["no_metric_claim_upgrade"] is True


def test_missing_or_stale_bridge_denies_metric_support() -> None:
    bridge_rule = _template()["decision_rules"]["missing_stale_mismatched_or_underpowered_bridge"]

    assert bridge_rule["metric_claim_level"] in {"ambiguous_metric", "operational_utility_only"}
    assert "calibrated_proxy_supported" in bridge_rule["denied_metric_claims"]
    assert "vinfo_proxy_supported" in bridge_rule["denied_metric_claims"]


def test_fixture_improvement_is_operational_audit_only() -> None:
    rule = _template()["decision_rules"]["fixture_only_before_after_improvement"]

    assert rule["claim_ceiling"] == "operational_audit_only"
    assert rule["deployed_runtime_improvement_claim"] is False
    assert rule["paper_evidence_eligible"] is False
    assert rule["measurement_validation_claim"] is False


def test_claim_boundaries_and_prior_scaffold_states_are_explicit() -> None:
    combined = "\n".join(
        [
            _plan_text(),
            TEMPLATE.read_text(encoding="utf-8"),
            REVIEW.read_text(encoding="utf-8"),
        ]
    )

    for phrase in {
        "P59 does not prove deployed runtime improvement",
        "P59 does not prove selector validity",
        "P59 does not establish metric bridge support",
        "P59 does not establish V-information support",
        "P59 does not establish measurement validation",
        "P55 remains failed_closed_no_rows / blocked_operator_required",
        "P56 remains no_imported_traces",
        "P57 remains extraction-risk scaffold only",
        "P58 remains operational diagnostic scaffold only",
        "P59 does not convert P57/P58 scaffolds into evidence claims",
    }:
        assert phrase in combined


def test_template_defaults_do_not_emit_upgraded_claims() -> None:
    template = _template()

    assert template["metric_bridge_status"] == "missing"
    assert template["paper_evidence_eligible"] is False
    assert template["measurement_validation_claim"] is False
    assert template["deployed_runtime_improvement_claim"] is False
    assert "calibrated_proxy_supported" in template["denied_claims"]
    assert "vinfo_proxy_supported" in template["denied_claims"]
    assert "measurement_validated" in template["denied_claims"]
    assert "deployed_runtime_improvement" in template["denied_claims"]


def test_template_is_machine_neutral() -> None:
    template_text = TEMPLATE.read_text(encoding="utf-8")

    assert not re.search(r"timestamp|uuid|api_key|secret|C:\\|/home/|/mnt/", template_text, re.IGNORECASE)
