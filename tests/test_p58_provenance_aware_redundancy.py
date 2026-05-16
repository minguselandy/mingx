import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN = REPO_ROOT / "docs" / "experiments" / "P58-provenance-aware-redundancy-plan.md"
TEMPLATE = REPO_ROOT / "docs" / "templates" / "provenance-redundancy-diagnostic-template.json"
REVIEW = REPO_ROOT / "docs" / "reviews" / "P58-provenance-aware-redundancy-review.md"


REQUIRED_CATEGORIES = {
    "duplicate_redundancy",
    "independent_corroboration",
    "adversarial_repetition",
    "source_conflict_pair",
    "prerequisite_overlap",
    "paraphrase_near_duplicate",
    "qualifier_mismatch",
    "temporal_scope_mismatch",
}


REQUIRED_FIELDS = {
    "record_schema_version",
    "diagnostic_id",
    "candidate_pair_id",
    "candidate_a_id",
    "candidate_b_id",
    "finding_a_hash",
    "finding_b_hash",
    "source_a_id",
    "source_b_id",
    "source_span_a_hash",
    "source_span_b_hash",
    "provenance_handle_a",
    "provenance_handle_b",
    "source_independence_score",
    "provenance_overlap_score",
    "semantic_similarity_score",
    "contradiction_flag",
    "qualifier_mismatch_flag",
    "temporal_scope_mismatch_flag",
    "prerequisite_relation_flag",
    "category_label",
    "category_confidence",
    "selector_implication",
    "escalation_required",
    "audit_required",
    "claim_ceiling",
    "metric_claim_level",
    "selector_regime_label",
    "paper_evidence_eligible",
    "measurement_validation_claim",
    "denied_claims",
}


def _template() -> dict:
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def _plan_text() -> str:
    return PLAN.read_text(encoding="utf-8")


def test_json_template_parses_and_has_required_feature_fields() -> None:
    template = _template()

    assert REQUIRED_FIELDS.issubset(template.keys())
    assert template["paper_evidence_eligible"] is False
    assert template["measurement_validation_claim"] is False
    assert template["selector_regime_label"] == "ambiguous"
    assert template["metric_claim_level"] in {"operational_utility_only", "ambiguous_metric"}
    assert "denied_claims" in template


def test_required_categories_are_listed_in_plan_and_template() -> None:
    plan = _plan_text()
    template = _template()
    category_definitions = template["category_definitions"]

    for category in REQUIRED_CATEGORIES:
        assert category in plan
        assert category in category_definitions
        for required_key in {
            "description",
            "selector_implication",
            "escalation_behavior",
            "claim_ceiling",
            "failure_modes",
        }:
            assert required_key in category_definitions[category]


def test_independent_corroboration_is_distinguished_from_duplicate_redundancy() -> None:
    categories = _template()["category_definitions"]
    duplicate = categories["duplicate_redundancy"]
    corroboration = categories["independent_corroboration"]

    assert duplicate["selector_implication"] != corroboration["selector_implication"]
    assert "penalize" in duplicate["selector_implication"]
    assert "preserve" in corroboration["selector_implication"]
    assert duplicate["source_independence_requirement"] == "low_or_none"
    assert corroboration["source_independence_requirement"] == "high"


def test_escalation_categories_require_audit_or_escalation() -> None:
    categories = _template()["category_definitions"]

    for category in {
        "adversarial_repetition",
        "source_conflict_pair",
        "qualifier_mismatch",
        "temporal_scope_mismatch",
    }:
        assert categories[category]["escalation_required"] is True
        assert categories[category]["audit_required"] is True

    assert categories["prerequisite_overlap"]["selector_implication"] == "preserve_or_escalate"


def test_claim_boundaries_and_prior_blocked_states_are_explicit() -> None:
    combined = "\n".join(
        [
            _plan_text(),
            TEMPLATE.read_text(encoding="utf-8"),
            REVIEW.read_text(encoding="utf-8"),
        ]
    )

    for phrase in {
        "P58 does not establish selector validity",
        "P58 does not establish metric bridge support",
        "P58 does not establish V-information support",
        "P58 does not establish measurement validation",
        "P55 remains failed_closed_no_rows / blocked_operator_required",
        "P56 remains no_imported_traces",
        "P57 remains extraction-risk scaffold only",
        "P58 does not convert P57 extraction audit into selector validity",
    }:
        assert phrase in combined


def test_template_defaults_do_not_emit_upgraded_labels() -> None:
    template = _template()

    assert template["metric_claim_level"] not in {
        "calibrated_proxy_supported",
        "vinfo_proxy_supported",
        "measurement_validated",
    }
    assert template["selector_regime_label"] != "greedy_supported"
    assert "calibrated_proxy_supported" in template["denied_claims"]
    assert "vinfo_proxy_supported" in template["denied_claims"]
    assert "measurement_validated" in template["denied_claims"]


def test_templates_and_plan_are_machine_neutral() -> None:
    combined = "\n".join(
        [
            _plan_text(),
            TEMPLATE.read_text(encoding="utf-8"),
        ]
    )

    assert not re.search(r"timestamp|uuid|api_key|secret|C:\\|/home/|/mnt/", combined, re.IGNORECASE)
