from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

from cps.experiments.human_label_kappa import (
    LABEL_DIMENSIONS,
    build_human_label_kappa_report,
    build_label_schema,
    check_label_completeness,
    cohen_kappa,
    format_human_labels_template_csv,
    format_human_labels_template_jsonl,
    format_kappa_report_markdown,
    write_human_label_kappa_outputs,
)


def _row(
    *,
    case_id: str,
    condition: str = "cps_runtime_audit_scaffold",
    annotator_id: str,
    label_dimension: str,
    label: int,
    rationale: str = "",
) -> dict:
    return {
        "run_id": "label-run",
        "case_id": case_id,
        "condition": condition,
        "annotator_id": annotator_id,
        "label_dimension": label_dimension,
        "label": label,
        "rationale": rationale,
    }


def _complete_rows(
    *,
    cases=("case-001", "case-002", "case-003", "case-004"),
    condition="cps_runtime_audit_scaffold",
    labels_by_annotator: dict[str, list[int]] | None = None,
) -> list[dict]:
    labels = labels_by_annotator or {
        "ann-a": [2, 2, 1, 1],
        "ann-b": [2, 2, 1, 1],
    }
    rows: list[dict] = []
    for annotator_id, values in labels.items():
        for dimension in LABEL_DIMENSIONS:
            for case_id, label in zip(cases, values, strict=True):
                rows.append(
                    _row(
                        case_id=case_id,
                        condition=condition,
                        annotator_id=annotator_id,
                        label_dimension=dimension,
                        label=label,
                    )
                )
    return rows


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def test_label_schema_includes_all_required_dimensions():
    schema = build_label_schema()

    assert schema["label_schema_version"] == "HumanLabelKappaV1"
    assert schema["label_dimensions"] == list(LABEL_DIMENSIONS)
    assert schema["allowed_labels"] == {"0": "fail", "1": "partial", "2": "pass"}
    assert "irrelevant_context" in schema["label_dimensions"]


def test_template_generation_does_not_fabricate_completed_labels():
    cases = ["case-001"]
    conditions = ["no_cps_baseline", "cps_runtime_audit_scaffold"]

    csv_content = format_human_labels_template_csv(cases, conditions=conditions, annotator_ids=["ann-a"])
    jsonl_content = format_human_labels_template_jsonl(cases, conditions=conditions, annotator_ids=["ann-a"])

    assert "case-001" in csv_content
    assert "ann-a" in csv_content
    assert ",0," not in csv_content
    assert ",1," not in csv_content
    assert ",2," not in csv_content
    assert '"label": ""' in jsonl_content
    assert '"rationale": ""' in jsonl_content


def test_completeness_checker_detects_missing_labels():
    rows = _complete_rows()
    rows = [row for row in rows if not (row["case_id"] == "case-004" and row["annotator_id"] == "ann-b")]

    report = check_label_completeness(
        rows,
        required_cases=["case-001", "case-002", "case-003", "case-004"],
        conditions=["cps_runtime_audit_scaffold"],
    )

    assert report["labels_complete"] is False
    assert "case-004" in report["missing_cases"]
    assert "missing_human_labels" in report["reason_codes"]


def test_completeness_checker_detects_invalid_label_values():
    rows = _complete_rows()
    rows[0]["label"] = 3

    report = check_label_completeness(
        rows,
        required_cases=["case-001", "case-002", "case-003", "case-004"],
        conditions=["cps_runtime_audit_scaffold"],
    )

    assert report["labels_complete"] is False
    assert report["label_value_errors"]
    assert "invalid_label_value" in report["reason_codes"]


def test_completeness_checker_detects_duplicate_label_entries():
    rows = _complete_rows()
    rows.append(dict(rows[0]))

    report = check_label_completeness(
        rows,
        required_cases=["case-001", "case-002", "case-003", "case-004"],
        conditions=["cps_runtime_audit_scaffold"],
    )

    assert report["labels_complete"] is False
    assert report["duplicate_label_entries"]
    assert "duplicate_label_entry" in report["reason_codes"]


def test_fewer_than_two_annotators_denies_kappa():
    rows = [row for row in _complete_rows() if row["annotator_id"] == "ann-a"]

    report = build_human_label_kappa_report(
        rows,
        run_id="label-run",
        required_cases=["case-001", "case-002", "case-003", "case-004"],
        conditions=["cps_runtime_audit_scaffold"],
    )

    assert report["kappa_present"] is False
    assert report["measurement_validated_allowed"] is False
    assert report["kappa_status"] == "kappa_missing"
    assert "two_annotators_required" in report["reason_codes"]
    assert "missing_kappa" in report["reason_codes"]


def test_perfect_agreement_yields_kappa_one():
    assert cohen_kappa([0, 1, 2, 2], [0, 1, 2, 2]) == 1.0

    report = build_human_label_kappa_report(
        _complete_rows(),
        run_id="label-run",
        required_cases=["case-001", "case-002", "case-003", "case-004"],
        conditions=["cps_runtime_audit_scaffold"],
    )

    assert report["kappa_present"] is True
    assert report["macro_average_kappa"] == 1.0
    assert set(report["per_dimension_kappa"]) == set(LABEL_DIMENSIONS)


def test_complete_disagreement_yields_low_or_negative_kappa():
    rows = _complete_rows(
        labels_by_annotator={
            "ann-a": [0, 0, 2, 2],
            "ann-b": [2, 2, 0, 0],
        }
    )

    report = build_human_label_kappa_report(
        rows,
        run_id="label-run",
        required_cases=["case-001", "case-002", "case-003", "case-004"],
        conditions=["cps_runtime_audit_scaffold"],
    )

    assert report["macro_average_kappa"] < 0.40
    assert report["kappa_status"] == "pilot_only"
    assert "low_kappa" in report["reason_codes"]


def test_partial_agreement_produces_deterministic_kappa():
    rows = _complete_rows(
        labels_by_annotator={
            "ann-a": [0, 1, 2, 2],
            "ann-b": [0, 1, 1, 2],
        }
    )

    first = build_human_label_kappa_report(
        rows,
        run_id="label-run",
        required_cases=["case-001", "case-002", "case-003", "case-004"],
        conditions=["cps_runtime_audit_scaffold"],
    )
    second = build_human_label_kappa_report(
        list(reversed(rows)),
        run_id="label-run",
        required_cases=["case-001", "case-002", "case-003", "case-004"],
        conditions=["cps_runtime_audit_scaffold"],
    )

    assert first == second
    assert first["macro_average_kappa"] == 0.636364
    assert first["kappa_status"] == "limited_measurement_review_candidate"
    assert first["item_count_per_dimension"] == {dimension: 4 for dimension in LABEL_DIMENSIONS}


def test_missing_human_labels_and_kappa_deny_measurement_validated():
    report = build_human_label_kappa_report(
        [],
        run_id="label-run",
        required_cases=["case-001"],
        conditions=["cps_runtime_audit_scaffold"],
    )

    assert report["human_labels_present"] is False
    assert report["kappa_present"] is False
    assert report["measurement_validated_allowed"] is False
    assert "missing_human_labels" in report["reason_codes"]
    assert "missing_kappa" in report["reason_codes"]
    assert "measurement_validated" in report["denied_claims"]


def test_high_kappa_alone_still_does_not_allow_measurement_validated():
    report = build_human_label_kappa_report(
        _complete_rows(),
        run_id="label-run",
        required_cases=["case-001", "case-002", "case-003", "case-004"],
        conditions=["cps_runtime_audit_scaffold"],
    )

    assert report["macro_average_kappa"] == 1.0
    assert report["kappa_status"] == "stronger_measurement_review_candidate"
    assert report["measurement_validated_allowed"] is False
    assert "kappa_alone_not_validation" in report["reason_codes"]
    assert "contamination_audit_required" in report["reason_codes"]
    assert "fresh_metric_bridge_required" in report["reason_codes"]
    assert "claim_gate_allow_required" in report["reason_codes"]


def test_reason_codes_are_stable_ordered():
    report = build_human_label_kappa_report(
        [],
        run_id="label-run",
        required_cases=["case-001"],
        conditions=["cps_runtime_audit_scaffold"],
    )

    assert report["reason_codes"] == sorted(
        report["reason_codes"],
        key=report["reason_code_order"].index,
    )


def test_json_and_markdown_writers_are_deterministic(workspace_tmp_dir):
    report = build_human_label_kappa_report(
        _complete_rows(),
        run_id="label-run",
        required_cases=["case-001", "case-002", "case-003", "case-004"],
        conditions=["cps_runtime_audit_scaffold"],
    )

    first = write_human_label_kappa_outputs(workspace_tmp_dir / "first", report)
    second = write_human_label_kappa_outputs(workspace_tmp_dir / "second", report)

    for key in ("completeness_report", "kappa_report", "kappa_markdown"):
        assert _read(first[key]) == _read(second[key])

    assert _json(first["kappa_report"])["measurement_validated_allowed"] is False
    assert "High kappa alone is not measurement validation" in format_kappa_report_markdown(report)


def test_no_external_dependency_network_or_reference_access(monkeypatch, workspace_tmp_dir):
    before = set(sys.modules)
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("human label kappa artifacts must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    report = build_human_label_kappa_report(
        _complete_rows(),
        run_id="label-run",
        required_cases=["case-001", "case-002", "case-003", "case-004"],
        conditions=["cps_runtime_audit_scaffold"],
    )
    outputs = write_human_label_kappa_outputs(workspace_tmp_dir / "kappa", report)
    imported = set(sys.modules) - before

    assert Path(outputs["kappa_report"]).exists()
    assert {"numpy", "pandas", "sklearn", "scipy", "statsmodels"}.isdisjoint(imported)
