from __future__ import annotations

import json
from pathlib import Path

from cps.experiments.bridge_row_validation import validate_bridge_rows
from cps.experiments.hotpotqa_support_classification_bridge import (
    SUPPORT_CLASSIFICATION_TASK_FAMILY,
)
from cps.experiments.hotpotqa_support_classification_bridge import (
    CIRCULAR_ALIGNMENT_CONTROL,
)
from cps.experiments.hotpotqa_support_classification_bridge import (
    NOT_METRIC_BRIDGE_EVIDENCE,
)
from cps.experiments.hotpotqa_support_classification_bridge import (
    POSITIVE_CONTROL_CLAIM_STATUS,
)
from cps.experiments.hotpotqa_support_classification_bridge import (
    POSITIVE_CONTROL_ONLY,
)
from cps.experiments.hotpotqa_support_classification_bridge import (
    SupportLabelNll,
)
from cps.experiments.hotpotqa_support_classification_bridge import (
    build_support_classification_delta_records,
)
from cps.experiments.hotpotqa_support_classification_bridge import (
    build_support_classification_rows,
)
from cps.experiments.hotpotqa_support_classification_bridge import (
    make_support_classification_specs,
)
from cps.experiments.hotpotqa_support_classification_bridge import (
    relabel_fixa_positive_control,
)
from cps.experiments.hotpotqa_support_classification_bridge import (
    write_support_classification_outputs,
)


def _pool() -> dict:
    return {
        "candidate_pool": {
            "candidate_pool_hash": "pool-hash-1",
            "packets": [
                {
                    "content": "Alice founded the company in 1999.",
                    "gold_support_label": "gold_supporting",
                    "packet_id": "p-gold",
                    "source_doc_id": "Alice",
                },
                {
                    "content": "The city has several public parks.",
                    "gold_support_label": "same_context_distractor",
                    "packet_id": "p-distractor",
                    "source_doc_id": "City",
                },
                {
                    "content": "Alice later moved to Paris.",
                    "gold_support_label": "same_context_distractor",
                    "packet_id": "p-helper",
                    "source_doc_id": "Alice",
                },
            ],
        },
        "dataset": "HotpotQA",
        "instance_id": "hotpot-1",
        "query": "Who founded the company?",
        "target": {"label": "Alice", "target_type": "answer_string"},
        "task_family": "hotpotqa_answer_support_selection",
    }


def _fake_scorer(*, label: str, with_block: bool, **_kwargs) -> SupportLabelNll:
    base = 0.7 if label == "SUPPORTING" else 0.5
    nll = base - (0.2 if with_block else 0.0)
    return SupportLabelNll(
        raw_content=label,
        target_label=label,
        token_logprobs=(-nll,),
    )


def test_specs_use_real_hotpot_packet_labels():
    specs = make_support_classification_specs([_pool()], max_instances=1, records_per_instance=2)

    assert {spec.target_y for spec in specs} == {"SUPPORTING", "NON_SUPPORTING"}
    assert specs[0].task_family == SUPPORT_CLASSIFICATION_TASK_FAMILY
    assert all(spec.context_L_packet_ids for spec in specs)
    assert all(spec.block_A_packet_ids for spec in specs)


def test_delta_records_are_circular_positive_control_not_bridge_evidence():
    specs = make_support_classification_specs([_pool()], max_instances=1, records_per_instance=2)

    records, report = build_support_classification_delta_records(specs, scorer=_fake_scorer)

    assert report["delta_records_validated"] == 2
    assert {row["target_y"] for row in records} == {"SUPPORTING", "NON_SUPPORTING"}
    assert all(row["delta_logloss_source"] == "measured_support_label_logprob" for row in records)
    assert all(row["support_classification_utility"] == "negative_support_label_nll" for row in records)
    assert all(row["delta_logloss"] == row["delta_utility"] for row in records)
    assert report["claim_status"] == POSITIVE_CONTROL_CLAIM_STATUS
    assert report[POSITIVE_CONTROL_ONLY] is True
    assert report[CIRCULAR_ALIGNMENT_CONTROL] is True
    assert report[NOT_METRIC_BRIDGE_EVIDENCE] is True


def test_support_classification_rows_validate_with_full_bridge_key():
    specs = make_support_classification_specs([_pool()], max_instances=1, records_per_instance=2)
    records, _report = build_support_classification_delta_records(specs, scorer=_fake_scorer)

    rows = build_support_classification_rows(records)

    validation = validate_bridge_rows(rows)
    assert validation.schema_valid is True
    assert validation.rows_validated == 2
    assert all(row["task_family"] == SUPPORT_CLASSIFICATION_TASK_FAMILY for row in rows)


def test_support_classification_artifacts_are_deterministic(workspace_tmp_dir: Path):
    specs = make_support_classification_specs([_pool()], max_instances=1, records_per_instance=2)
    records, report = build_support_classification_delta_records(specs, scorer=_fake_scorer)
    rows = build_support_classification_rows(records)

    first = write_support_classification_outputs(
        delta_records=records,
        rows=rows,
        report=report,
        delta_records_path=workspace_tmp_dir / "delta.jsonl",
        operator_rows_path=workspace_tmp_dir / "rows.jsonl",
        report_path=workspace_tmp_dir / "report.json",
    )
    first_bytes = {
        "delta": (workspace_tmp_dir / "delta.jsonl").read_bytes(),
        "rows": (workspace_tmp_dir / "rows.jsonl").read_bytes(),
        "report": (workspace_tmp_dir / "report.json").read_bytes(),
    }
    second = write_support_classification_outputs(
        delta_records=records,
        rows=rows,
        report=report,
        delta_records_path=workspace_tmp_dir / "delta.jsonl",
        operator_rows_path=workspace_tmp_dir / "rows.jsonl",
        report_path=workspace_tmp_dir / "report.json",
    )
    second_bytes = {
        "delta": (workspace_tmp_dir / "delta.jsonl").read_bytes(),
        "rows": (workspace_tmp_dir / "rows.jsonl").read_bytes(),
        "report": (workspace_tmp_dir / "report.json").read_bytes(),
    }

    assert first == second
    assert first_bytes == second_bytes
    assert str(workspace_tmp_dir) not in json.dumps(report)


def test_support_classification_calibration_relabels_as_positive_control():
    raw_fit = {
        "calibrated_proxy_supported": False,
        "calibrated_proxy_supported_candidate": True,
        "claim_status": "legacy_candidate_pending_review",
        "gate_result": "legacy_candidate_gate",
        "measurement_validation": False,
        "metric_claim_level": "legacy_candidate_level",
        "paper_evidence": False,
        "reason_codes": [],
        "vinfo_proxy_supported": False,
    }

    relabeled = relabel_fixa_positive_control(raw_fit)

    assert relabeled["gate_result"] == POSITIVE_CONTROL_ONLY
    assert relabeled["metric_claim_level"] == POSITIVE_CONTROL_ONLY
    assert relabeled["claim_status"] == POSITIVE_CONTROL_CLAIM_STATUS
    assert relabeled["calibrated_proxy_supported_candidate"] is False
    assert relabeled[POSITIVE_CONTROL_ONLY] is True
    assert relabeled[CIRCULAR_ALIGNMENT_CONTROL] is True
    assert relabeled[NOT_METRIC_BRIDGE_EVIDENCE] is True
    assert relabeled["reason_codes"] == [
        CIRCULAR_ALIGNMENT_CONTROL,
        NOT_METRIC_BRIDGE_EVIDENCE,
    ]
