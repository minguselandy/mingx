import json
from pathlib import Path

import pytest

from cps.judge.weak_evidence_schema import ALLOWED_LABELS
from cps.judge.weak_evidence_schema import JudgeWeakEvidenceRecord
from cps.judge.weak_evidence_schema import normalize_judge_label
from cps.judge.weak_evidence_schema import parse_judge_output


def _base_payload(**overrides):
    payload = {
        "judgment_id": "j-1",
        "item_id": "item-1",
        "pair_id": "pair-1",
        "judge_model_snapshot": "static-judge-snapshot",
        "prompt_hash": "prompt-hash",
        "rubric_version": "weak_evidence_v1",
        "rubric_paraphrase_id": "p0",
        "order_swap": False,
        "duplicate_index": 0,
        "normalized_label": "support",
        "confidence_bucket": "medium",
        "flags": ["abstain_recommended"],
        "parse_status": "parsed",
        "raw_response_stored": False,
        "input_token_count": 100,
        "output_token_count": 12,
    }
    payload.update(overrides)
    return payload


def test_allowed_labels_are_exact_protocol_values():
    assert ALLOWED_LABELS == {"support", "insufficient", "contradict", "uncertain", "parse_failed"}


def test_parse_judge_output_normalizes_allowed_labels_without_raw_body_storage():
    record = parse_judge_output(
        _base_payload(label=" Support ", normalized_label=None, flags=["missing_context"])
    )
    payload = record.to_dict()

    assert payload["normalized_label"] == "support"
    assert payload["confidence_bucket"] == "medium"
    assert payload["parse_status"] == "parsed"
    assert payload["raw_response_stored"] is False
    assert payload["counts_as_human_or_external_gold"] is False
    assert payload["measurement_validation_claim"] is False
    assert payload["allowed_claim_level"] == "model_adjudicated_weak_evidence"
    assert '"raw_response":' not in json.dumps(payload, sort_keys=True)


def test_unknown_or_unparseable_label_becomes_parse_failed():
    record = parse_judge_output(_base_payload(normalized_label="definitely"))

    payload = record.to_dict()

    assert payload["normalized_label"] == "parse_failed"
    assert payload["parse_status"] == "parse_failed"
    assert "parse_failure" in payload["flags"]


def test_judge_record_rejects_raw_response_storage_and_body_fields():
    with pytest.raises(ValueError, match="raw_response_stored"):
        JudgeWeakEvidenceRecord.from_dict(_base_payload(raw_response_stored=True))

    with pytest.raises(ValueError, match="raw_response"):
        JudgeWeakEvidenceRecord.from_dict(
            _base_payload(raw_response={"choices": [{"message": "do not store"}]})
        )


def test_judge_prompt_files_exist_and_pin_candidate_evidence_boundary():
    prompt_paths = [
        Path("prompts/judge/weak_evidence_v1.md"),
        Path("prompts/judge/weak_evidence_v1_order_swapped.md"),
    ]

    for path in prompt_paths:
        text = path.read_text(encoding="utf-8").lower()
        assert "model-adjudicated weak evidence" in text
        assert "not human/external gold" in text
        assert "not measurement validation" in text
        assert "return strict json" in text
        assert "raw api response" not in text


def test_normalize_judge_label_accepts_protocol_aliases_only_as_schema_normalization():
    assert normalize_judge_label("supports") == "support"
    assert normalize_judge_label("not enough information") == "insufficient"
    assert normalize_judge_label("contradiction") == "contradict"
    assert normalize_judge_label("unknown") == "uncertain"
    assert normalize_judge_label("unsupported label") == "parse_failed"
