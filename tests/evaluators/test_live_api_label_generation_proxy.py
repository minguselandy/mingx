from __future__ import annotations

import json

from cps.evaluators.live_api_label_generation_proxy import build_label_proxy_contract
from cps.evaluators.live_api_label_generation_proxy import normalize_label_generation


def test_label_generation_proxy_normalizes_json_without_raw_response_storage() -> None:
    row = normalize_label_generation(
        confidence=0.8,
        content='{"label":"supporting","rationale_quality":"This would be raw generated rationale text.","uncertainty":"low"}',
        model_id="qwen3.6-flash",
        parent_sample_id="sample-1",
        probe_type="primary",
        prompt_text="Return JSON only.",
        token_logprobs=[-0.1],
    )

    serialized = json.dumps(row, sort_keys=True)
    assert row["allowed_claims"] == [
        "constrained_label_generation_proxy",
        "operational_label_confidence_proxy",
    ]
    assert row["label"] == "supporting"
    assert row["raw_response_stored"] is False
    assert row["teacher_forced_label_nll"] is False
    assert row["fixed_target_nll"] is False
    assert row["rationale_quality"] == "invalid"
    assert "prompt_text" not in row
    assert "raw generated rationale" not in serialized
    assert '"choices":' not in serialized


def test_label_generation_proxy_contract_is_not_vinfo_proxy() -> None:
    contract = build_label_proxy_contract()

    assert contract["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert contract["denied_claims"]["v_information_proxy"] is True
    assert contract["denied_claims"]["teacher_forced_label_nll"] is True
