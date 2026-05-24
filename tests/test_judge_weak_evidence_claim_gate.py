import json

from cps.judge.judge_manifest import build_judge_run_manifest
from cps.judge.judge_manifest import prompt_hashes
from cps.judge.weak_evidence_schema import JudgeWeakEvidenceRecord
from cps.judge.weak_evidence_schema import evaluate_judge_claim_gate


def _record(
    *,
    judgment_id,
    item_id,
    pair_id,
    label="support",
    order_swap=False,
    duplicate_index=0,
    rubric_paraphrase_id="p0",
    parse_status="parsed",
):
    return JudgeWeakEvidenceRecord.from_dict(
        {
            "judgment_id": judgment_id,
            "item_id": item_id,
            "pair_id": pair_id,
            "judge_model_snapshot": "static-judge-snapshot",
            "prompt_hash": "prompt-hash",
            "rubric_version": "weak_evidence_v1",
            "rubric_paraphrase_id": rubric_paraphrase_id,
            "order_swap": order_swap,
            "duplicate_index": duplicate_index,
            "normalized_label": label,
            "confidence_bucket": "high",
            "flags": [],
            "parse_status": parse_status,
            "raw_response_stored": False,
            "input_token_count": 80,
            "output_token_count": 9,
        }
    )


def _stable_records():
    rows = []
    for item_id in ("item-1", "item-2"):
        rows.extend(
            [
                _record(judgment_id=f"{item_id}-p0-a", item_id=item_id, pair_id=item_id, duplicate_index=0),
                _record(judgment_id=f"{item_id}-p0-b", item_id=item_id, pair_id=item_id, duplicate_index=1),
                _record(
                    judgment_id=f"{item_id}-p1-a",
                    item_id=item_id,
                    pair_id=item_id,
                    duplicate_index=0,
                    rubric_paraphrase_id="p1",
                ),
                _record(
                    judgment_id=f"{item_id}-swap",
                    item_id=item_id,
                    pair_id=item_id,
                    order_swap=True,
                    duplicate_index=0,
                    rubric_paraphrase_id="p1",
                ),
            ]
        )
    return rows


def test_judge_manifest_is_deterministic_and_contains_required_controls():
    items = [
        {"item_id": "b", "left_evidence_hash": "left-b", "right_evidence_hash": "right-b"},
        {"item_id": "a", "left_evidence_hash": "left-a", "right_evidence_hash": "right-a"},
    ]

    first = build_judge_run_manifest(run_id="judge-run", items=items)
    second = build_judge_run_manifest(run_id="judge-run", items=reversed(items))

    assert first == second
    assert first["run_id"] == "judge-run"
    assert first["blinded_pairwise_comparison"] is True
    assert first["order_swapped_duplication"] is True
    assert first["duplicate_judging_min"] == 2
    assert first["rubric_paraphrase_ids"] == ["p0", "p1"]
    assert first["temperature"] == 0
    assert first["length_aware_reporting"] is True
    assert first["raw_response_stored"] is False
    assert first["allowed_claim_level"] == "model_adjudicated_weak_evidence"
    assert first["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert first["route_5_locked"] is True
    assert first["route_8_locked"] is True
    assert first["live_api_call_performed"] is False
    assert first["prompt_hashes"] == prompt_hashes()
    assert '"raw_response":' not in json.dumps(first, sort_keys=True)


def test_claim_gate_allows_only_weak_model_adjudicated_candidate_evidence_when_stable():
    gate = evaluate_judge_claim_gate(_stable_records())

    assert gate["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert gate["allowed_claims"] == ["model_adjudicated_weak_evidence"]
    assert gate["final_gate_status"] == "weak_evidence_candidate_ready"
    assert gate["aggregate_label_status"] == "weak_model_adjudicated_candidate"
    assert gate["measurement_validation_claim"] is False
    assert gate["human_external_gold_label"] is False
    assert gate["raw_response_stored"] is False
    assert gate["route_5_locked"] is True
    assert gate["route_8_locked"] is True
    assert "measurement_validation" in gate["denied_claims"]
    assert "human_external_gold_validation" in gate["denied_claims"]
    assert "paper_grade_validation" in gate["denied_claims"]


def test_claim_gate_downgrades_parse_failures_to_ambiguous_and_suppresses_claim():
    records = _stable_records()
    records[0] = _record(
        judgment_id="parse-fail",
        item_id="item-1",
        pair_id="item-1",
        label="parse_failed",
        parse_status="parse_failed",
    )
    records[1] = _record(
        judgment_id="parse-fail-2",
        item_id="item-2",
        pair_id="item-2",
        label="parse_failed",
        parse_status="parse_failed",
    )

    gate = evaluate_judge_claim_gate(records)

    assert gate["final_gate_status"] == "downgraded_to_ambiguous"
    assert gate["aggregate_label_status"] == "ambiguous_suppressed"
    assert gate["allowed_claims"] == []
    assert "parse_failure_rate_above_threshold" in gate["reason_codes"]


def test_claim_gate_downgrades_unstable_order_swap_or_duplicate_agreement():
    records = _stable_records()
    records[3] = _record(
        judgment_id="item-1-swap-contradict",
        item_id="item-1",
        pair_id="item-1",
        label="contradict",
        order_swap=True,
        rubric_paraphrase_id="p1",
    )
    records[5] = _record(
        judgment_id="item-2-duplicate-uncertain",
        item_id="item-2",
        pair_id="item-2",
        label="uncertain",
        duplicate_index=1,
    )

    gate = evaluate_judge_claim_gate(records)

    assert gate["final_gate_status"] == "downgraded_to_ambiguous"
    assert gate["aggregate_label_status"] == "ambiguous_suppressed"
    assert gate["allowed_claims"] == []
    assert "order_swap_agreement_below_threshold" in gate["reason_codes"]
    assert "duplicate_agreement_below_threshold" in gate["reason_codes"]
