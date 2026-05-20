from __future__ import annotations

import json

from cps.evaluators.live_api_chat_logprob_confidence import build_confidence_diagnostic
from cps.evaluators.live_api_chat_logprob_confidence import diagnostic_schema


def test_chat_logprob_confidence_is_operational_only_and_sanitized() -> None:
    row = build_confidence_diagnostic(
        backend_id="dashscope_openai_chat",
        generated_text="SUPPORTING",
        model_id="qwen3.6-flash",
        prompt_id="probe-1",
        prompt_text="Classify this sentence.",
        token_logprobs=[-0.1, -0.2],
    )

    serialized = json.dumps(row, sort_keys=True)
    assert row["allowed_claim"] == "operational_confidence_diagnostic"
    assert row["denied_claims"]["fixed_target_nll"] is True
    assert row["denied_claims"]["metric_bridge"] is True
    assert row["teacher_forced_fixed_target_nll"] is False
    assert row["raw_response_stored"] is False
    assert "prompt_text" not in row
    assert '"choices":' not in serialized
    assert '"raw_response":' not in serialized


def test_chat_logprob_schema_denies_bridge_claims() -> None:
    schema = diagnostic_schema()

    assert schema["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert "metric_bridge" in schema["denied_claims"]
    assert schema["generated_token_logprobs_are_fixed_target_nll"] is False
