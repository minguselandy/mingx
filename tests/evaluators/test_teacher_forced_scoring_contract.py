from __future__ import annotations

from cps.evaluators.teacher_forced_scoring_contract import CLAIM_STATUS
from cps.evaluators.teacher_forced_scoring_contract import build_teacher_forced_score_record
from cps.evaluators.teacher_forced_scoring_contract import validate_teacher_forced_score_record


def _valid_score_record(**overrides):
    kwargs = {
        "deterministic_settings": {"seed": 0, "temperature": 0},
        "fixed_target_text": "EVIDENCE_PATH_V1\n1\tDoc\tsentence:0-1\tp1\thash1",
        "materialization_policy_hash": "materialization-hash",
        "per_token_logprobs": [-0.25, -0.75],
        "prompt_template_hash": "prompt-hash",
        "prompt_text": "Score this fixed target.",
        "scorer_model_id": "unit-model",
        "scoring_backend_id": "unit-teacher-forced-scorer",
        "scoring_policy": {"teacher_forced": True},
        "target_format_hash": "target-format-hash",
        "target_token_ids": [101, 102],
        "tokenizer_id": "unit-tokenizer",
    }
    kwargs.update(overrides)
    return build_teacher_forced_score_record(**kwargs)


def test_teacher_forced_score_record_computes_nll_and_validates_required_fields():
    payload = _valid_score_record()

    validation = validate_teacher_forced_score_record(payload)

    assert validation["passed"] is True
    assert validation["errors"] == []
    assert payload["claim_status"] == CLAIM_STATUS
    assert payload["target_token_count"] == 2
    assert payload["target_nll"] == 1.0
    assert payload["target_nll_normalized"] == 0.5
    assert payload["raw_response_stored"] is False


def test_teacher_forced_score_record_rejects_missing_or_empty_fixed_target():
    missing = _valid_score_record(fixed_target_text="")

    validation = validate_teacher_forced_score_record(missing)

    assert "empty_fixed_target_text" in validation["errors"]
    assert validation["passed"] is False


def test_teacher_forced_score_record_rejects_generated_target_mismatch():
    payload = _valid_score_record(generated_target_text="different generated text")

    validation = validate_teacher_forced_score_record(payload)

    assert "generated_target_mismatch" in validation["errors"]
    assert validation["passed"] is False


def test_teacher_forced_score_record_rejects_missing_tokenization_metadata():
    payload = _valid_score_record(target_token_ids=[])

    validation = validate_teacher_forced_score_record(payload)

    assert "missing_target_token_ids" in validation["errors"]
    assert "target_token_count_mismatch" in validation["errors"]
    assert validation["passed"] is False


def test_teacher_forced_score_record_rejects_missing_target_logprobs():
    payload = _valid_score_record(per_token_logprobs=[])

    validation = validate_teacher_forced_score_record(payload)

    assert "missing_per_token_logprobs" in validation["errors"]
    assert "logprob_count_mismatch" in validation["errors"]
    assert validation["passed"] is False


def test_teacher_forced_score_record_rejects_raw_response_payload_fields():
    payload = _valid_score_record(raw_response_payload={"choices": [{"text": "raw"}]})

    validation = validate_teacher_forced_score_record(payload)

    assert "raw_response_payload_field_present" in validation["errors"]
    assert validation["passed"] is False


def test_teacher_forced_score_record_rejects_secret_like_fields():
    payload = _valid_score_record(metadata={"api_key": "redacted-test-value"})

    validation = validate_teacher_forced_score_record(payload)

    assert "secret_like_field_present" in validation["errors"]
    assert validation["passed"] is False
