import json
from pathlib import Path

import pytest

from cps.api.backend_capability_contract import BackendCapabilityContract
from cps.api.backend_capability_witness import build_static_backend_capability_witness
from cps.api.backend_capability_witness import write_static_backend_capability_witness


REQUIRED_WITNESS_FIELDS = {
    "backend_name",
    "endpoint_family",
    "model_snapshot",
    "documented_generated_token_logprobs",
    "documented_prompt_logprobs",
    "fixed_target_teacher_forced_nll_supported",
    "fixed_target_continuation_scoring_supported",
    "generated_token_logprobs_allowed_use",
    "denied_claims",
    "claim_level",
    "evidence_date_or_doc_snapshot",
}


def test_static_backend_witness_fails_closed_by_default():
    witness = build_static_backend_capability_witness()
    payload = witness.to_dict()

    assert REQUIRED_WITNESS_FIELDS <= set(payload)
    assert payload["backend_name"] == "dashscope_compatible_live_api"
    assert payload["endpoint_family"] == "openai_compatible_chat_completions"
    assert payload["documented_generated_token_logprobs"] is True
    assert payload["documented_prompt_logprobs"] is False
    assert payload["fixed_target_teacher_forced_nll_supported"] is False
    assert payload["fixed_target_continuation_scoring_supported"] is False
    assert payload["generated_token_logprobs_allowed_use"] == "answer_side_confidence_diagnostic_only"
    assert payload["claim_level"] == "fail_closed_bridge_audit / operational_utility_only"
    assert payload["route_5_locked"] is True
    assert payload["route_8_locked"] is True
    assert payload["raw_response_stored"] is False
    assert payload["live_api_call_performed"] is False


def test_static_backend_witness_denies_bridge_and_scoring_claims():
    denied = set(build_static_backend_capability_witness().to_dict()["denied_claims"])

    for claim in (
        "fixed_target_nll_support",
        "teacher_forced_scoring_support",
        "fixed_target_continuation_scoring_support",
        "prompt_logprobs_support",
        "metric_bridge_support",
        "calibrated_proxy_supported",
        "vinfo_proxy_supported",
        "measurement_validation",
        "selector_superiority",
        "global_selector_superiority",
        "route_5_unlock",
        "route_8_unlock",
    ):
        assert claim in denied


def test_generated_token_logprobs_cannot_upgrade_to_fixed_target_support():
    with pytest.raises(ValueError, match="generated-token logprobs cannot support fixed-target"):
        BackendCapabilityContract(
            backend_name="dashscope_compatible_live_api",
            endpoint_family="openai_compatible_chat_completions",
            model_snapshot="static-doc-snapshot",
            documented_generated_token_logprobs=True,
            fixed_target_teacher_forced_nll_supported=True,
        )

    with pytest.raises(ValueError, match="fixed-target continuation scoring unsupported"):
        BackendCapabilityContract(
            backend_name="dashscope_compatible_live_api",
            endpoint_family="openai_compatible_chat_completions",
            model_snapshot="static-doc-snapshot",
            fixed_target_continuation_scoring_supported=True,
        )


def test_backend_witness_rejects_raw_response_storage_or_payloads():
    with pytest.raises(ValueError, match="raw_response"):
        BackendCapabilityContract.from_dict(
            {
                "backend_name": "dashscope_compatible_live_api",
                "endpoint_family": "openai_compatible_chat_completions",
                "model_snapshot": "static-doc-snapshot",
                "raw_response_stored": True,
            }
        )

    with pytest.raises(ValueError, match="raw_response"):
        BackendCapabilityContract.from_dict(
            {
                "backend_name": "dashscope_compatible_live_api",
                "endpoint_family": "openai_compatible_chat_completions",
                "model_snapshot": "static-doc-snapshot",
                "raw_response": {"choices": []},
            }
        )


def test_write_static_backend_witness_is_deterministic_and_offline(workspace_tmp_dir):
    output_path = workspace_tmp_dir / "backend_bridge_audit_witness.json"

    first = write_static_backend_capability_witness(output_path)
    first_text = output_path.read_text(encoding="utf-8")
    second = write_static_backend_capability_witness(output_path)
    second_text = output_path.read_text(encoding="utf-8")
    payload = json.loads(second_text)

    assert first == second == output_path
    assert first_text == second_text
    assert payload["live_api_call_performed"] is False
    assert '"raw_response":' not in second_text
    assert '"raw_api_response":' not in second_text


def test_backend_bridge_audit_witness_doc_records_static_boundary():
    path = Path("docs/api/backend-bridge-audit-witness.md")
    text = path.read_text(encoding="utf-8").lower()

    assert "static contract only" in text
    assert "fail_closed_bridge_audit / operational_utility_only" in text
    assert "fixed-target teacher-forced nll supported: false" in text
    assert "fixed-target continuation scoring supported: false" in text
    assert "generated-token logprobs are answer-side confidence diagnostics only" in text
    assert "route 5 locked: true" in text
    assert "route 8 locked: true" in text
