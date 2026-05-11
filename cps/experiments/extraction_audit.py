from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


RUN_ID = "extraction-audit-pilot-v12"
PROTOCOL_VERSION = "extraction_audit_pilot.v12"
SCHEMA_VERSION = "ExtractionAuditPilotV1"
DEFAULT_OUTPUT_DIR = "artifacts/experiments/extraction_audit_pilot_v12"
DATA_SOURCE_KIND = "fixture"
AUDIT_SCOPE = "extraction_audit_pilot"
EVIDENCE_SCOPE = "fixture_extraction_audit_only"
METRIC_CLAIM_LEVEL = "operational_utility_only"
SUPPORT_STATUSES = ("supported", "partially_supported", "unsupported", "missing_source", "ambiguous")
DEFECT_REASON_ORDER = (
    "unsupported_finding",
    "missing_critical_finding",
    "source_span_missing",
    "provenance_missing",
    "over_merged_finding",
    "under_specified_finding",
    "duplicate_finding",
    "contradictory_sources",
    "candidate_pool_hash_mismatch",
    "non_deterministic_extraction",
)
OUTPUT_FILENAMES = (
    "extraction_audit_cases.jsonl",
    "extraction_audit_findings.jsonl",
    "extraction_audit_labels.jsonl",
    "extraction_audit_defects.csv",
    "extraction_audit_summary.json",
    "extraction_audit_report.md",
    "extraction_audit_manifest.json",
    "extraction_ground_truth_findings.jsonl",
    "stratum_completeness_report.csv",
    "value_weighted_loss.csv",
    "extraction_claim_gate_report.json",
)


@dataclass(frozen=True)
class SourceRecord:
    source_record_id: str
    source_kind: str
    text: str
    spans: tuple[dict[str, str], ...]
    provenance_ref: str

    def to_row(self) -> dict[str, Any]:
        return {
            "provenance_ref": self.provenance_ref,
            "source_kind": self.source_kind,
            "source_record_id": self.source_record_id,
            "spans": [dict(span) for span in self.spans],
            "text": self.text,
        }


@dataclass(frozen=True)
class GroundTruthFinding:
    expected_finding_id: str
    expected_text: str
    stratum: str
    value_band: str
    value_weight: float
    selector_impact: str
    critical: bool
    expected_source_span_refs: tuple[str, ...]

    def to_row(self, *, case_id: str) -> dict[str, Any]:
        return {
            "case_id": case_id,
            "critical": self.critical,
            "expected_finding_id": self.expected_finding_id,
            "expected_source_span_refs": list(self.expected_source_span_refs),
            "expected_text": self.expected_text,
            "selector_impact": self.selector_impact,
            "stratum": self.stratum,
            "value_band": self.value_band,
            "value_weight": self.value_weight,
        }


@dataclass(frozen=True)
class ExtractedFinding:
    finding_id: str
    finding_text: str
    finding_type: str
    source_record_ids: tuple[str, ...]
    source_span_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    support_status: str
    extraction_defects: tuple[str, ...]
    matched_expected_finding_ids: tuple[str, ...]

    def finding_hash(self, *, case_id: str) -> str:
        return _stable_hash(
            {
                "case_id": case_id,
                "extraction_defects": list(self.extraction_defects),
                "finding_id": self.finding_id,
                "finding_text": self.finding_text,
                "finding_type": self.finding_type,
                "matched_expected_finding_ids": list(self.matched_expected_finding_ids),
                "provenance_refs": list(self.provenance_refs),
                "source_record_ids": list(self.source_record_ids),
                "source_span_refs": list(self.source_span_refs),
                "support_status": self.support_status,
            }
        )

    def to_row(self, *, case_id: str, case_family: str, candidate_pool_hash: str) -> dict[str, Any]:
        return {
            "candidate_pool_hash": candidate_pool_hash,
            "case_family": case_family,
            "case_id": case_id,
            "extraction_defects": list(self.extraction_defects),
            "finding_hash": self.finding_hash(case_id=case_id),
            "finding_id": self.finding_id,
            "finding_text": self.finding_text,
            "finding_type": self.finding_type,
            "matched_expected_finding_ids": list(self.matched_expected_finding_ids),
            "provenance_refs": list(self.provenance_refs),
            "source_record_ids": list(self.source_record_ids),
            "source_span_refs": list(self.source_span_refs),
            "support_status": self.support_status,
        }


@dataclass(frozen=True)
class ExtractionAuditLabel:
    expected_finding_id: str
    captured_finding_ids: tuple[str, ...]
    extraction_outcome: str
    lost_qualifiers: tuple[str, ...]
    temporal_scope_error: bool
    provenance_loss: bool
    selector_impact: str
    value_band: str
    value_weight: float
    stratum: str
    confidence: float
    defect_reason_codes: tuple[str, ...]

    def score(self) -> float:
        if self.extraction_outcome == "captured_core_preserved":
            return 1.0
        if self.extraction_outcome in {"captured", "captured_core_changed"}:
            return 0.5
        return 0.0

    def to_row(self, *, case_id: str, case_family: str) -> dict[str, Any]:
        return {
            "captured_finding_ids": list(self.captured_finding_ids),
            "case_family": case_family,
            "case_id": case_id,
            "confidence": self.confidence,
            "defect_reason_codes": list(self.defect_reason_codes),
            "expected_finding_id": self.expected_finding_id,
            "extraction_outcome": self.extraction_outcome,
            "lost_qualifiers": list(self.lost_qualifiers),
            "provenance_loss": self.provenance_loss,
            "selector_impact": self.selector_impact,
            "stratum": self.stratum,
            "temporal_scope_error": self.temporal_scope_error,
            "value_band": self.value_band,
            "value_weight": self.value_weight,
        }


@dataclass(frozen=True)
class ExtractionAuditCase:
    case_id: str
    case_family: str
    source_records: tuple[SourceRecord, ...]
    ground_truth_findings: tuple[GroundTruthFinding, ...]
    extracted_findings: tuple[ExtractedFinding, ...]
    labels: tuple[ExtractionAuditLabel, ...]

    def candidate_pool_hash(self) -> str:
        finding_hashes = sorted(finding.finding_hash(case_id=self.case_id) for finding in self.extracted_findings)
        return _stable_hash({"case_id": self.case_id, "finding_hashes": finding_hashes})

    def to_case_row(self) -> dict[str, Any]:
        return {
            "audit_scope": AUDIT_SCOPE,
            "candidate_pool_hash": self.candidate_pool_hash(),
            "case_family": self.case_family,
            "case_id": self.case_id,
            "data_source_kind": DATA_SOURCE_KIND,
            "expected_critical_findings": [
                finding.expected_finding_id for finding in self.ground_truth_findings if finding.critical
            ],
            "live_api_used": False,
            "measurement_validation_claim": False,
            "paper_evidence_eligible": False,
            "source_records": [record.to_row() for record in self.source_records],
        }


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _stable_jsonl(rows: Sequence[Mapping[str, Any]]) -> str:
    return "".join(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n" for row in rows)


def _stable_hash(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_stable_json(payload), encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_stable_jsonl(rows), encoding="utf-8")
    return path


def _write_csv(path: Path, *, fieldnames: list[str], rows: Sequence[Mapping[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    return path


def _ordered_reason_codes(reasons: Iterable[str]) -> list[str]:
    order = {reason: index for index, reason in enumerate(DEFECT_REASON_ORDER)}
    return sorted(set(reasons), key=lambda reason: (order.get(reason, len(order)), reason))


def _source(source_record_id: str, source_kind: str, text: str, span_id: str, provenance_ref: str) -> SourceRecord:
    return SourceRecord(
        source_record_id=source_record_id,
        source_kind=source_kind,
        text=text,
        spans=({"span_id": span_id, "span_ref": f"{source_record_id}#{span_id}", "text": text},),
        provenance_ref=provenance_ref,
    )


def _gt(
    expected_finding_id: str,
    expected_text: str,
    *,
    stratum: str,
    span_refs: Sequence[str],
    value_band: str = "medium",
    value_weight: float = 1.0,
    selector_impact: str = "candidate_pool_faithfulness",
) -> GroundTruthFinding:
    return GroundTruthFinding(
        expected_finding_id=expected_finding_id,
        expected_text=expected_text,
        stratum=stratum,
        value_band=value_band,
        value_weight=value_weight,
        selector_impact=selector_impact,
        critical=True,
        expected_source_span_refs=tuple(span_refs),
    )


def _finding(
    finding_id: str,
    finding_text: str,
    *,
    finding_type: str,
    source_record_ids: Sequence[str],
    source_span_refs: Sequence[str],
    provenance_refs: Sequence[str],
    support_status: str,
    extraction_defects: Sequence[str] = (),
    matched_expected_finding_ids: Sequence[str] = (),
) -> ExtractedFinding:
    if support_status not in SUPPORT_STATUSES:
        raise ValueError(f"unknown support_status: {support_status}")
    return ExtractedFinding(
        finding_id=finding_id,
        finding_text=finding_text,
        finding_type=finding_type,
        source_record_ids=tuple(source_record_ids),
        source_span_refs=tuple(source_span_refs),
        provenance_refs=tuple(provenance_refs),
        support_status=support_status,
        extraction_defects=tuple(_ordered_reason_codes(extraction_defects)),
        matched_expected_finding_ids=tuple(matched_expected_finding_ids),
    )


def _label(
    expected_finding_id: str,
    *,
    captured_finding_ids: Sequence[str],
    extraction_outcome: str,
    stratum: str,
    value_band: str = "medium",
    value_weight: float = 1.0,
    selector_impact: str = "candidate_pool_faithfulness",
    confidence: float = 1.0,
    defect_reason_codes: Sequence[str] = (),
    lost_qualifiers: Sequence[str] = (),
    temporal_scope_error: bool = False,
    provenance_loss: bool = False,
) -> ExtractionAuditLabel:
    return ExtractionAuditLabel(
        expected_finding_id=expected_finding_id,
        captured_finding_ids=tuple(captured_finding_ids),
        extraction_outcome=extraction_outcome,
        lost_qualifiers=tuple(lost_qualifiers),
        temporal_scope_error=temporal_scope_error,
        provenance_loss=provenance_loss,
        selector_impact=selector_impact,
        value_band=value_band,
        value_weight=value_weight,
        stratum=stratum,
        confidence=confidence,
        defect_reason_codes=tuple(_ordered_reason_codes(defect_reason_codes)),
    )


def _default_cases() -> list[ExtractionAuditCase]:
    return sorted(
        [
            ExtractionAuditCase(
                case_id="p49-clean-001",
                case_family="clean_extraction",
                source_records=(
                    _source(
                        "src-clean-1",
                        "user_message",
                        "P45 did not establish a calibrated bridge for the bio_attribute stratum.",
                        "s1",
                        "fixture:clean:1",
                    ),
                    _source(
                        "src-clean-2",
                        "tool_summary",
                        "P46 synthetic outputs use synthetic_structural_only scope and are not paper evidence.",
                        "s1",
                        "fixture:clean:2",
                    ),
                ),
                ground_truth_findings=(
                    _gt(
                        "gt-clean-p45",
                        "P45 did not establish a calibrated bridge for bio_attribute.",
                        stratum="simple_factual",
                        span_refs=("src-clean-1#s1",),
                        value_band="high",
                        value_weight=1.2,
                    ),
                    _gt(
                        "gt-clean-p46",
                        "P46 outputs are synthetic structural evidence only.",
                        stratum="simple_factual",
                        span_refs=("src-clean-2#s1",),
                        value_band="medium",
                    ),
                ),
                extracted_findings=(
                    _finding(
                        "find-clean-p45",
                        "P45 did not establish a calibrated bridge for bio_attribute.",
                        finding_type="claim_boundary",
                        source_record_ids=("src-clean-1",),
                        source_span_refs=("src-clean-1#s1",),
                        provenance_refs=("fixture:clean:1",),
                        support_status="supported",
                        matched_expected_finding_ids=("gt-clean-p45",),
                    ),
                    _finding(
                        "find-clean-p46",
                        "P46 synthetic outputs remain synthetic_structural_only and not paper evidence.",
                        finding_type="evidence_scope",
                        source_record_ids=("src-clean-2",),
                        source_span_refs=("src-clean-2#s1",),
                        provenance_refs=("fixture:clean:2",),
                        support_status="supported",
                        matched_expected_finding_ids=("gt-clean-p46",),
                    ),
                ),
                labels=(
                    _label(
                        "gt-clean-p45",
                        captured_finding_ids=("find-clean-p45",),
                        extraction_outcome="captured_core_preserved",
                        stratum="simple_factual",
                        value_band="high",
                        value_weight=1.2,
                    ),
                    _label(
                        "gt-clean-p46",
                        captured_finding_ids=("find-clean-p46",),
                        extraction_outcome="captured_core_preserved",
                        stratum="simple_factual",
                    ),
                ),
            ),
            ExtractionAuditCase(
                case_id="p49-missing-001",
                case_family="missing_critical_finding",
                source_records=(
                    _source(
                        "src-missing-1",
                        "memory_record",
                        "P47 is fixture-only and full_context is an always-large-context reference baseline.",
                        "s1",
                        "fixture:missing:1",
                    ),
                ),
                ground_truth_findings=(
                    _gt(
                        "gt-missing-p47-fixture",
                        "P47 is fixture-only.",
                        stratum="simple_factual",
                        span_refs=("src-missing-1#s1",),
                    ),
                    _gt(
                        "gt-missing-full-context",
                        "full_context is an always-large-context reference baseline.",
                        stratum="qualifier_heavy",
                        span_refs=("src-missing-1#s1",),
                        value_band="high",
                        value_weight=1.5,
                    ),
                ),
                extracted_findings=(
                    _finding(
                        "find-missing-p47-fixture",
                        "P47 is fixture-only.",
                        finding_type="data_source_boundary",
                        source_record_ids=("src-missing-1",),
                        source_span_refs=("src-missing-1#s1",),
                        provenance_refs=("fixture:missing:1",),
                        support_status="supported",
                        matched_expected_finding_ids=("gt-missing-p47-fixture",),
                    ),
                ),
                labels=(
                    _label(
                        "gt-missing-p47-fixture",
                        captured_finding_ids=("find-missing-p47-fixture",),
                        extraction_outcome="captured_core_preserved",
                        stratum="simple_factual",
                    ),
                    _label(
                        "gt-missing-full-context",
                        captured_finding_ids=(),
                        extraction_outcome="missing",
                        stratum="qualifier_heavy",
                        value_band="high",
                        value_weight=1.5,
                        defect_reason_codes=("missing_critical_finding",),
                    ),
                ),
            ),
            ExtractionAuditCase(
                case_id="p49-unsupported-001",
                case_family="unsupported_hallucinated",
                source_records=(
                    _source(
                        "src-unsupported-1",
                        "subagent_message",
                        "P48 replay identity is bound by run_id, dispatch_id, agent_id, and round_id.",
                        "s1",
                        "fixture:unsupported:1",
                    ),
                ),
                ground_truth_findings=(
                    _gt(
                        "gt-unsupported-identity",
                        "P48 replay identity is bound by run_id, dispatch_id, agent_id, and round_id.",
                        stratum="simple_factual",
                        span_refs=("src-unsupported-1#s1",),
                    ),
                ),
                extracted_findings=(
                    _finding(
                        "find-unsupported-identity",
                        "P48 replay identity is bound by run_id, dispatch_id, agent_id, and round_id.",
                        finding_type="dispatch_identity",
                        source_record_ids=("src-unsupported-1",),
                        source_span_refs=("src-unsupported-1#s1",),
                        provenance_refs=("fixture:unsupported:1",),
                        support_status="supported",
                        matched_expected_finding_ids=("gt-unsupported-identity",),
                    ),
                    _finding(
                        "find-unsupported-validation",
                        "P48 established measurement validation for replay bundles.",
                        finding_type="unsupported_claim",
                        source_record_ids=(),
                        source_span_refs=(),
                        provenance_refs=(),
                        support_status="unsupported",
                        extraction_defects=("unsupported_finding", "source_span_missing", "provenance_missing"),
                    ),
                ),
                labels=(
                    _label(
                        "gt-unsupported-identity",
                        captured_finding_ids=("find-unsupported-identity",),
                        extraction_outcome="captured_core_preserved",
                        stratum="simple_factual",
                    ),
                ),
            ),
            ExtractionAuditCase(
                case_id="p49-duplicate-001",
                case_family="duplicate_over_merged",
                source_records=(
                    _source(
                        "src-duplicate-1",
                        "tool_output",
                        "candidate_pool_hash mismatch fails closed.",
                        "s1",
                        "fixture:duplicate:1",
                    ),
                    _source(
                        "src-duplicate-2",
                        "tool_output",
                        "identity mismatch fails closed.",
                        "s1",
                        "fixture:duplicate:2",
                    ),
                ),
                ground_truth_findings=(
                    _gt(
                        "gt-duplicate-pool",
                        "candidate_pool_hash mismatch fails closed.",
                        stratum="high_provenance",
                        span_refs=("src-duplicate-1#s1",),
                    ),
                    _gt(
                        "gt-duplicate-identity",
                        "identity mismatch fails closed.",
                        stratum="high_provenance",
                        span_refs=("src-duplicate-2#s1",),
                    ),
                ),
                extracted_findings=(
                    _finding(
                        "find-duplicate-pool-a",
                        "candidate_pool_hash mismatch fails closed.",
                        finding_type="provenance_gate",
                        source_record_ids=("src-duplicate-1",),
                        source_span_refs=("src-duplicate-1#s1",),
                        provenance_refs=("fixture:duplicate:1",),
                        support_status="supported",
                        matched_expected_finding_ids=("gt-duplicate-pool",),
                    ),
                    _finding(
                        "find-duplicate-pool-b",
                        "candidate_pool_hash mismatch fails closed.",
                        finding_type="provenance_gate",
                        source_record_ids=("src-duplicate-1",),
                        source_span_refs=("src-duplicate-1#s1",),
                        provenance_refs=("fixture:duplicate:1",),
                        support_status="supported",
                        extraction_defects=("duplicate_finding",),
                        matched_expected_finding_ids=("gt-duplicate-pool",),
                    ),
                    _finding(
                        "find-overmerged-provenance",
                        "candidate pool and identity mismatches fail closed.",
                        finding_type="over_merged_boundary",
                        source_record_ids=("src-duplicate-1", "src-duplicate-2"),
                        source_span_refs=("src-duplicate-1#s1", "src-duplicate-2#s1"),
                        provenance_refs=("fixture:duplicate:1", "fixture:duplicate:2"),
                        support_status="partially_supported",
                        extraction_defects=("over_merged_finding",),
                        matched_expected_finding_ids=("gt-duplicate-pool", "gt-duplicate-identity"),
                    ),
                ),
                labels=(
                    _label(
                        "gt-duplicate-pool",
                        captured_finding_ids=("find-duplicate-pool-a", "find-duplicate-pool-b"),
                        extraction_outcome="captured_core_preserved",
                        stratum="high_provenance",
                        defect_reason_codes=("duplicate_finding",),
                    ),
                    _label(
                        "gt-duplicate-identity",
                        captured_finding_ids=("find-overmerged-provenance",),
                        extraction_outcome="captured_core_changed",
                        stratum="high_provenance",
                        defect_reason_codes=("over_merged_finding",),
                    ),
                ),
            ),
            ExtractionAuditCase(
                case_id="p49-contradictory-001",
                case_family="contradictory_source",
                source_records=(
                    _source(
                        "src-contradict-1",
                        "tool_output",
                        "The verifier marked finding alpha as supported.",
                        "s1",
                        "fixture:contradict:1",
                    ),
                    _source(
                        "src-contradict-2",
                        "tool_output",
                        "The adjudicator marked finding alpha as unsupported.",
                        "s1",
                        "fixture:contradict:2",
                    ),
                ),
                ground_truth_findings=(
                    _gt(
                        "gt-contradict-alpha",
                        "Finding alpha has contradictory support signals.",
                        stratum="contradictory_adversarial",
                        span_refs=("src-contradict-1#s1", "src-contradict-2#s1"),
                        value_band="high",
                        value_weight=1.4,
                    ),
                ),
                extracted_findings=(
                    _finding(
                        "find-contradict-alpha",
                        "Finding alpha has conflicting support labels.",
                        finding_type="contradictory_source",
                        source_record_ids=("src-contradict-1", "src-contradict-2"),
                        source_span_refs=("src-contradict-1#s1", "src-contradict-2#s1"),
                        provenance_refs=("fixture:contradict:1", "fixture:contradict:2"),
                        support_status="ambiguous",
                        extraction_defects=("contradictory_sources",),
                        matched_expected_finding_ids=("gt-contradict-alpha",),
                    ),
                ),
                labels=(
                    _label(
                        "gt-contradict-alpha",
                        captured_finding_ids=("find-contradict-alpha",),
                        extraction_outcome="captured_core_changed",
                        stratum="contradictory_adversarial",
                        value_band="high",
                        value_weight=1.4,
                        defect_reason_codes=("contradictory_sources",),
                    ),
                ),
            ),
            ExtractionAuditCase(
                case_id="p49-provenance-001",
                case_family="provenance_missing",
                source_records=(
                    _source(
                        "src-provenance-1",
                        "memory_record",
                        "Extraction audit findings must preserve source spans and provenance handles.",
                        "s1",
                        "fixture:provenance:1",
                    ),
                ),
                ground_truth_findings=(
                    _gt(
                        "gt-provenance-handles",
                        "Extraction audit findings must preserve source spans and provenance handles.",
                        stratum="high_provenance",
                        span_refs=("src-provenance-1#s1",),
                        value_band="high",
                        value_weight=1.3,
                    ),
                ),
                extracted_findings=(
                    _finding(
                        "find-provenance-handles",
                        "Extraction audit findings must preserve source spans and provenance handles.",
                        finding_type="provenance_requirement",
                        source_record_ids=("src-provenance-1",),
                        source_span_refs=(),
                        provenance_refs=(),
                        support_status="partially_supported",
                        extraction_defects=("source_span_missing", "provenance_missing"),
                        matched_expected_finding_ids=("gt-provenance-handles",),
                    ),
                ),
                labels=(
                    _label(
                        "gt-provenance-handles",
                        captured_finding_ids=("find-provenance-handles",),
                        extraction_outcome="captured_core_changed",
                        stratum="high_provenance",
                        value_band="high",
                        value_weight=1.3,
                        provenance_loss=True,
                        defect_reason_codes=("source_span_missing", "provenance_missing"),
                    ),
                ),
            ),
        ],
        key=lambda case: (case.case_family, case.case_id),
    )


def _load_config(config_path: str | Path | None) -> dict[str, Any]:
    if config_path is None:
        return {}
    return json.loads(Path(config_path).read_text(encoding="utf-8"))


def _finding_rows(cases: Sequence[ExtractionAuditCase]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        candidate_pool_hash = case.candidate_pool_hash()
        for finding in sorted(case.extracted_findings, key=lambda item: item.finding_id):
            rows.append(
                finding.to_row(
                    case_id=case.case_id,
                    case_family=case.case_family,
                    candidate_pool_hash=candidate_pool_hash,
                )
            )
    return sorted(rows, key=lambda row: (row["case_id"], row["finding_id"]))


def _ground_truth_rows(cases: Sequence[ExtractionAuditCase]) -> list[dict[str, Any]]:
    rows = [
        finding.to_row(case_id=case.case_id)
        for case in cases
        for finding in sorted(case.ground_truth_findings, key=lambda item: item.expected_finding_id)
    ]
    return sorted(rows, key=lambda row: (row["case_id"], row["expected_finding_id"]))


def _label_rows(cases: Sequence[ExtractionAuditCase]) -> list[dict[str, Any]]:
    rows = [
        label.to_row(case_id=case.case_id, case_family=case.case_family)
        for case in cases
        for label in sorted(case.labels, key=lambda item: item.expected_finding_id)
    ]
    return sorted(rows, key=lambda row: (row["case_id"], row["expected_finding_id"]))


def _defect_rows(cases: Sequence[ExtractionAuditCase]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        candidate_pool_hash = case.candidate_pool_hash()
        for finding in case.extracted_findings:
            for reason_code in finding.extraction_defects:
                rows.append(
                    {
                        "candidate_pool_hash": candidate_pool_hash,
                        "case_family": case.case_family,
                        "case_id": case.case_id,
                        "expected_finding_id": "",
                        "finding_id": finding.finding_id,
                        "reason_code": reason_code,
                        "severity": "error",
                        "source_record_ids": "|".join(finding.source_record_ids),
                        "support_status": finding.support_status,
                    }
                )
        for label in case.labels:
            for reason_code in label.defect_reason_codes:
                rows.append(
                    {
                        "candidate_pool_hash": candidate_pool_hash,
                        "case_family": case.case_family,
                        "case_id": case.case_id,
                        "expected_finding_id": label.expected_finding_id,
                        "finding_id": "|".join(label.captured_finding_ids),
                        "reason_code": reason_code,
                        "severity": "error",
                        "source_record_ids": "",
                        "support_status": label.extraction_outcome,
                    }
                )
    order = {reason: index for index, reason in enumerate(DEFECT_REASON_ORDER)}
    return sorted(
        rows,
        key=lambda row: (
            row["case_id"],
            order.get(row["reason_code"], len(order)),
            row["reason_code"],
            row["finding_id"],
            row["expected_finding_id"],
        ),
    )


def _stratum_rows(labels: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for label in labels:
        by_stratum[str(label["stratum"])].append(label)
    rows: list[dict[str, Any]] = []
    for stratum in sorted(by_stratum):
        stratum_labels = by_stratum[stratum]
        expected_count = len(stratum_labels)
        scores = [_label_score(row["extraction_outcome"]) for row in stratum_labels]
        captured_core_preserved = sum(1 for row in stratum_labels if row["extraction_outcome"] == "captured_core_preserved")
        missing_count = sum(1 for row in stratum_labels if row["extraction_outcome"] == "missing")
        weight_total = sum(float(row["value_weight"]) for row in stratum_labels)
        weighted_loss = sum(float(row["value_weight"]) * (1.0 - _label_score(row["extraction_outcome"])) for row in stratum_labels)
        rows.append(
            {
                "captured_core_preserved_count": captured_core_preserved,
                "c_s": round(sum(scores) / expected_count, 6) if expected_count else 0.0,
                "expected_count": expected_count,
                "missing_count": missing_count,
                "stratum": stratum,
                "value_weighted_loss": round(weighted_loss / weight_total, 6) if weight_total else 0.0,
            }
        )
    return rows


def _label_score(extraction_outcome: str) -> float:
    if extraction_outcome == "captured_core_preserved":
        return 1.0
    if extraction_outcome in {"captured", "captured_core_changed"}:
        return 0.5
    return 0.0


def _value_loss_rows(labels: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in labels:
        score = _label_score(str(label["extraction_outcome"]))
        rows.append(
            {
                "case_id": label["case_id"],
                "expected_finding_id": label["expected_finding_id"],
                "extraction_outcome": label["extraction_outcome"],
                "loss": round(float(label["value_weight"]) * (1.0 - score), 6),
                "score": score,
                "stratum": label["stratum"],
                "value_weight": label["value_weight"],
            }
        )
    return sorted(rows, key=lambda row: (row["case_id"], row["expected_finding_id"]))


def _claim_gate_report(*, case_count: int, finding_count: int, defect_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    reason_counts = Counter(str(row["reason_code"]) for row in defect_rows)
    return {
        "audit_scope": AUDIT_SCOPE,
        "calibrated_proxy_supported": False,
        "case_count": case_count,
        "data_source_kind": DATA_SOURCE_KIND,
        "defect_reason_counts": {reason: reason_counts[reason] for reason in _ordered_reason_codes(reason_counts)},
        "deployed_v_information_verification_claim": False,
        "evidence_scope": EVIDENCE_SCOPE,
        "finding_count": finding_count,
        "human_kappa_present": False,
        "human_labels_present": False,
        "live_api_used": False,
        "measurement_validation_claim": False,
        "metric_claim_level": METRIC_CLAIM_LEVEL,
        "paper_evidence_eligible": False,
        "schema_version": SCHEMA_VERSION,
        "selector_regime_claim_upgraded": False,
        "vinfo_proxy_supported": False,
    }


def _summary_payload(
    *,
    cases: Sequence[ExtractionAuditCase],
    finding_rows: Sequence[dict[str, Any]],
    label_rows: Sequence[dict[str, Any]],
    defect_rows: Sequence[dict[str, Any]],
    stratum_rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    support_counts = Counter(row["support_status"] for row in finding_rows)
    outcome_counts = Counter(row["extraction_outcome"] for row in label_rows)
    defect_counts = Counter(row["reason_code"] for row in defect_rows)
    value_rows = _value_loss_rows(label_rows)
    value_weight_total = sum(float(row["value_weight"]) for row in value_rows)
    total_loss = sum(float(row["loss"]) for row in value_rows)
    effective_score = 1.0 - (total_loss / value_weight_total) if value_weight_total else 0.0
    return {
        "audit_scope": AUDIT_SCOPE,
        "c_effective": round(effective_score, 6),
        "case_count": len(cases),
        "data_source_kind": DATA_SOURCE_KIND,
        "defect_reason_counts": {reason: defect_counts[reason] for reason in _ordered_reason_codes(defect_counts)},
        "evidence_scope": EVIDENCE_SCOPE,
        "finding_count": len(finding_rows),
        "label_count": len(label_rows),
        "live_api_used": False,
        "measurement_validation_claim": False,
        "metric_claim_level": METRIC_CLAIM_LEVEL,
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "paper_evidence_eligible": False,
        "protocol_version": PROTOCOL_VERSION,
        "run_id": RUN_ID,
        "schema_version": SCHEMA_VERSION,
        "stratum_completeness": {row["stratum"]: row["c_s"] for row in stratum_rows},
        "support_status_counts": {status: support_counts[status] for status in SUPPORT_STATUSES if support_counts[status]},
        "value_weighted_loss": round(total_loss / value_weight_total, 6) if value_weight_total else 0.0,
    }


def _manifest_payload(*, output_dir: str, output_files: Sequence[str], claim_gate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "audit_scope": AUDIT_SCOPE,
        "data_source_kind": DATA_SOURCE_KIND,
        "evidence_scope": EVIDENCE_SCOPE,
        "live_api_used": False,
        "measurement_validation_claim": False,
        "metric_claim_level": METRIC_CLAIM_LEVEL,
        "output_dir": output_dir,
        "output_files": list(output_files),
        "paper_evidence_eligible": False,
        "protocol_version": PROTOCOL_VERSION,
        "run_id": RUN_ID,
        "schema_version": SCHEMA_VERSION,
        "selector_regime_claim_upgraded": False,
        "vinfo_proxy_supported": bool(claim_gate["vinfo_proxy_supported"]),
    }


def _format_report(summary: Mapping[str, Any], claim_gate: Mapping[str, Any], stratum_rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "# P49 Extraction Audit Pilot Report",
        "",
        "P49 audits the M-star to M extraction boundary using deterministic fixture cases. It is not a selector benchmark and not metric bridge evidence.",
        "",
        "## Claim Boundary",
        "",
        "- Data source kind: fixture",
        "- Evidence scope: fixture_extraction_audit_only",
        "- Paper evidence eligible: false",
        "- Measurement validation claim: false",
        "- Live API used: false",
        "- Selector-regime claims are not upgraded by this audit.",
        "",
        "## Summary",
        "",
        f"- Cases: {summary['case_count']}",
        f"- Extracted findings: {summary['finding_count']}",
        f"- Labels: {summary['label_count']}",
        f"- c_effective: {summary['c_effective']}",
        f"- Value-weighted loss: {summary['value_weighted_loss']}",
        f"- Defect counts: `{json.dumps(summary['defect_reason_counts'], sort_keys=True)}`",
        "",
        "## Stratum Completeness",
        "",
    ]
    for row in stratum_rows:
        lines.append(
            f"- {row['stratum']}: c_s={row['c_s']}, expected={row['expected_count']}, missing={row['missing_count']}"
        )
    lines.extend(
        [
            "",
            "## Claim Gate",
            "",
            f"- Metric claim level: {claim_gate['metric_claim_level']}",
            f"- Calibrated proxy support: {str(claim_gate['calibrated_proxy_supported']).lower()}",
            f"- V-information proxy support: {str(claim_gate['vinfo_proxy_supported']).lower()}",
            "",
        ]
    )
    return "\n".join(lines)


def run_extraction_audit_pilot(
    *,
    config_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    config = _load_config(config_path)
    if str(config.get("data_source_kind", DATA_SOURCE_KIND)) != DATA_SOURCE_KIND:
        raise ValueError("P49 fixture pilot only supports data_source_kind=fixture")
    if bool(config.get("live_api_used", False)):
        raise ValueError("P49 fixture pilot must not use live API")

    output_path = Path(output_dir or config.get("output_dir") or DEFAULT_OUTPUT_DIR)
    cases = _default_cases()
    case_rows = [case.to_case_row() for case in cases]
    finding_rows = _finding_rows(cases)
    label_rows = _label_rows(cases)
    ground_truth_rows = _ground_truth_rows(cases)
    defect_rows = _defect_rows(cases)
    stratum_rows = _stratum_rows(label_rows)
    value_loss_rows = _value_loss_rows(label_rows)
    summary = _summary_payload(
        cases=cases,
        finding_rows=finding_rows,
        label_rows=label_rows,
        defect_rows=defect_rows,
        stratum_rows=stratum_rows,
    )
    claim_gate = _claim_gate_report(case_count=len(cases), finding_count=len(finding_rows), defect_rows=defect_rows)
    manifest = _manifest_payload(output_dir=DEFAULT_OUTPUT_DIR, output_files=OUTPUT_FILENAMES, claim_gate=claim_gate)
    report_text = _format_report(summary, claim_gate, stratum_rows)

    _write_jsonl(output_path / "extraction_audit_cases.jsonl", case_rows)
    _write_jsonl(output_path / "extraction_audit_findings.jsonl", finding_rows)
    _write_jsonl(output_path / "extraction_audit_labels.jsonl", label_rows)
    _write_jsonl(output_path / "extraction_ground_truth_findings.jsonl", ground_truth_rows)
    _write_csv(
        output_path / "extraction_audit_defects.csv",
        fieldnames=[
            "case_id",
            "case_family",
            "finding_id",
            "expected_finding_id",
            "reason_code",
            "severity",
            "support_status",
            "source_record_ids",
            "candidate_pool_hash",
        ],
        rows=defect_rows,
    )
    _write_csv(
        output_path / "stratum_completeness_report.csv",
        fieldnames=[
            "stratum",
            "expected_count",
            "captured_core_preserved_count",
            "missing_count",
            "c_s",
            "value_weighted_loss",
        ],
        rows=stratum_rows,
    )
    _write_csv(
        output_path / "value_weighted_loss.csv",
        fieldnames=[
            "case_id",
            "expected_finding_id",
            "stratum",
            "extraction_outcome",
            "score",
            "value_weight",
            "loss",
        ],
        rows=value_loss_rows,
    )
    _write_json(output_path / "extraction_audit_summary.json", summary)
    _write_json(output_path / "extraction_claim_gate_report.json", claim_gate)
    _write_json(output_path / "extraction_audit_manifest.json", manifest)
    (output_path / "extraction_audit_report.md").write_text(report_text, encoding="utf-8")

    return {
        "artifacts": {name: str(output_path / name) for name in OUTPUT_FILENAMES},
        "case_count": len(cases),
        "data_source_kind": DATA_SOURCE_KIND,
        "finding_count": len(finding_rows),
        "output_dir": str(output_path),
        "status": "completed",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic P49 extraction audit fixture pilot.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    result = run_extraction_audit_pilot(config_path=args.config, output_dir=args.output_dir)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
