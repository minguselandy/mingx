from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "docs" / "experiments" / "P57-extraction-audit-v2-plan.md"
RECORD_TEMPLATE_PATH = ROOT / "docs" / "templates" / "extraction-audit-v2-record-template.json"
HUMAN_SENTINEL_PATH = ROOT / "docs" / "templates" / "human-sentinel-extraction-audit-protocol-template.md"

REQUIRED_STRATA = {
    "simple_factual",
    "complex_conditional",
    "qualifier_heavy",
    "temporal_scope",
    "cross_chunk",
    "long_tail_entity",
    "high_provenance_value",
    "prerequisite",
    "contradictory",
    "adversarial_repetition_sensitive",
}
REQUIRED_LABELS = {
    "captured_exact",
    "captured_core_preserved",
    "captured_core_changed",
    "missing",
    "unsupported_added",
    "duplicate_or_overmerged",
    "contradiction_lost",
    "qualifier_lost",
    "temporal_scope_error",
    "provenance_lost",
    "selector_impact_estimate",
}
REQUIRED_METRICS = {
    "extraction_completeness_by_stratum",
    "effective_extraction_completeness",
    "value_weighted_extraction_loss",
    "critical_finding_miss_rate",
    "unsupported_finding_rate",
    "provenance_loss_rate",
}
REQUIRED_RECORD_FIELDS = {
    "record_schema_version",
    "audit_id",
    "source_document_id",
    "source_document_hash",
    "source_span_hash",
    "extracted_item_id",
    "extracted_item_hash",
    "candidate_pool_hash",
    "stratum",
    "ground_truth_finding",
    "extracted_finding",
    "label",
    "label_rationale",
    "provenance_expected",
    "provenance_observed",
    "qualifier_expected",
    "qualifier_observed",
    "temporal_scope_expected",
    "temporal_scope_observed",
    "contradiction_context",
    "prerequisite_context",
    "value_weight",
    "criticality",
    "selector_impact_estimate",
    "data_source_kind",
    "label_source_kind",
    "annotator_count",
    "adjudication_status",
    "agreement_statistic",
    "human_human_kappa_present",
    "model_adjudicated",
    "paper_evidence_eligible",
    "measurement_validation_claim",
    "denied_claims",
}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _record_template() -> dict:
    return json.loads(RECORD_TEMPLATE_PATH.read_text(encoding="utf-8"))


def test_record_template_is_valid_json_and_has_required_fields() -> None:
    template = _record_template()

    assert REQUIRED_RECORD_FIELDS.issubset(template)
    assert template["record_schema_version"] == "extraction_audit_v2_record.v1"
    assert template["paper_evidence_eligible"] is False
    assert template["measurement_validation_claim"] is False
    assert template["human_human_kappa_present"] is False
    assert template["model_adjudicated"] is False
    assert template["denied_claims"]


def test_plan_lists_required_extraction_risk_strata() -> None:
    plan = _text(PLAN_PATH)

    for stratum in REQUIRED_STRATA:
        assert stratum in plan


def test_template_lists_required_labels_and_marks_selector_impact_as_risk_only() -> None:
    template = _record_template()

    assert REQUIRED_LABELS.issubset(set(template["allowed_labels"]))
    selector_impact = template["selector_impact_estimate"]
    assert selector_impact["semantics"] == "risk_estimate_only"
    assert selector_impact["not_selector_validity"] is True
    assert selector_impact["not_metric_support"] is True


def test_extraction_metrics_are_separate_from_bridge_quantities() -> None:
    template = _record_template()
    plan = _text(PLAN_PATH)

    assert REQUIRED_METRICS.issubset(set(template["extraction_metrics"]))
    assert "c_s" not in template["extraction_metrics"]
    assert "zeta_s" not in template["extraction_metrics"]
    assert "Do not use `c_s` or `zeta_s`" in plan


def test_human_sentinel_template_blocks_model_adjudication_substitution() -> None:
    template = _text(HUMAN_SENTINEL_PATH)

    assert "Missing human labels or missing kappa must not be filled by model adjudication." in template
    assert "Model-adjudicated labels are not human labels." in template
    assert "Human sentinel evidence is not automatically measurement validation." in template
    assert "Extraction audit results do not prove selector validity." in template
    assert "Extraction audit results do not establish metric bridge support." in template


def test_p57_templates_preserve_claim_boundaries() -> None:
    combined = "\n".join([_text(PLAN_PATH), _text(HUMAN_SENTINEL_PATH), json.dumps(_record_template(), sort_keys=True)])

    assert "P55 remains failed_closed_no_rows / blocked_operator_required." in combined
    assert "P56 remains no_imported_traces." in combined
    assert "extraction audit is not selector validity" in combined
    assert "extraction audit is not metric bridge support" in combined
    assert "extraction audit is not measurement validation" in combined
    assert "fixture-only extraction audit is not paper-grade evidence" in combined


def test_p57_templates_are_machine_neutral() -> None:
    combined = "\n".join([_text(PLAN_PATH), _text(HUMAN_SENTINEL_PATH), json.dumps(_record_template(), sort_keys=True)])
    volatile_pattern = re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b|"
        r"\b20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:|"
        r"api_key|secret|C:\\|/home/|/mnt/",
        re.IGNORECASE,
    )

    assert not volatile_pattern.search(combined)
