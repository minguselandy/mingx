import json

import pytest

from cps.artifacts.projection_bundle import ProjectionBundleV1 as ArtifactProjectionBundleV1
from cps.schema import ProjectionBundleV1, projection_bundle_from_epf_final_metadata


def _complete_payload():
    common = {
        "run_id": "run-epf",
        "dispatch_id": "dispatch-1",
        "agent_id": "agent-a",
        "round_id": "round-1",
    }
    return {
        **common,
        "candidate_pool": {
            "candidate_ids_considered": ["e1", "e2"],
            "source_manifest_hash": "pool-hash",
        },
        "projection_plan": {
            "dispatch_id": "dispatch-1",
            "query_id": "query-1",
            "conversation_turn_id": "turn-1",
            "candidate_ids_considered": ["e1", "e2"],
            "selected_evidence_ids": ["e1"],
            "excluded_evidence_ids": ["e2"],
            "selector_name": "fixture_selector",
            "selector_config_hash": "selector-hash",
            "score_manifest_hash": "score-hash",
        },
        "budget_witness": {
            "requested_budget_tokens": 100,
            "realized_budget_tokens": 72,
            "token_count_method": "fixture",
            "section_level_token_counts": {"e1": 72},
            "trim_events": [],
            "overflow_policy": "fail_closed_on_overflow",
        },
        "materialized_context": {
            "materialized_context_hash": "context-hash",
            "materialization_order": ["e1"],
            "section_boundaries": [{"section_id": "e1", "start": 0, "end": 72}],
            "prompt_template_hash": "template-hash",
            "downstream_prompt_hash": "prompt-hash",
            "evidence_hashes": {"e1": "evidence-hash"},
        },
        "metric_bridge_witness": {
            "metric_class": "operational_only",
            "active_stratum": {"dataset": "epf-final"},
            "model_snapshot": "dashscope-compatible-redacted",
            "endpoint": "dashscope-compatible-redacted",
            "thinking_mode": "not_recorded",
            "decoding_policy": {"temperature": 0},
            "bridge_status": "unavailable_but_disclosed",
            "diagnostic_claim_level": "operational_utility_only",
            "drift_status": "not_evaluated",
            "generated_token_logprobs_used_as_answer_side_diagnostic_only": True,
            "fixed_target_nll_supported": False,
            "generated_token_logprob_summary": {"token_count": 8},
        },
        "counterfactual_replay_witness": {
            "frozen_state_hash": "state-hash",
            "intervention_type": "remove_evidence",
            "item_added_or_removed": "e2",
            "evaluator_manifest_hash": "evaluator-hash",
            "replicate_count": 2,
            "replay_status": "complete",
        },
        "reprojection_witness": {
            "trigger_label": "uncertain",
            "budget_delta": 16,
            "selector_change": "same_selector",
            "context_diff_hash": "diff-hash",
            "before_output_hash": "before-hash",
            "after_output_hash": "after-hash",
            "repair_status": "not_claim_evidence",
        },
        "judge_run_manifest": {
            "judge_model_snapshot": "judge-redacted",
            "judge_prompt_hash": "judge-prompt-hash",
            "rubric_version": "rubric-v1",
            "order_swap_enabled": True,
            "rubric_paraphrase_id": "p0",
            "raw_response_stored": False,
            "parsed_label": "supported",
            "parse_status": "parsed",
        },
        "claim_ledger": {
            "claim_candidate": "projection_bundle_v1",
            "metric_claim_level": "operational_utility_only",
            "bridge_status": "unavailable_but_disclosed",
            "judge_status": "parsed",
            "artifact_status": "complete",
            "replay_status": "complete",
            "reprojection_status": "not_claim_evidence",
            "raw_response_stored": False,
            "human_external_gold_label": False,
            "current_claim_level": "operational_utility_only/no_claim_upgrade",
            "allowed_claims": ["replayable_artifact_evidence"],
            "denied_claims": [
                "metric_bridge_support",
                "measurement_validation",
                "vinfo_proxy_supported",
                "selector_superiority",
                "global_selector_superiority",
                "route_5_unlock",
                "route_8_unlock",
            ],
            "claim_upgrade": False,
            "route_5_locked": True,
            "route_8_locked": True,
        },
        "cost_latency_ledger": {
            "input_tokens": 72,
            "output_tokens": 11,
            "total_tokens": 83,
            "estimated_cost": 0.0,
            "latency_ms": 1234,
        },
    }


def test_complete_projection_bundle_v1_records_required_artifacts_without_raw_bodies():
    bundle = ProjectionBundleV1.from_dict(_complete_payload())

    payload = bundle.to_dict()
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["artifact_status"] == "complete"
    assert payload["raw_response_stored"] is False
    assert payload["claim_ledger"]["allowed_claims"] == ["replayable_artifact_evidence"]
    assert payload["claim_ledger"]["route_5_locked"] is True
    assert payload["claim_ledger"]["route_8_locked"] is True
    assert payload["cost_latency_ledger"]["total_tokens"] == 83
    assert payload["metric_bridge_witness"]["fixed_target_nll_supported"] is False
    assert payload["metric_bridge_witness"][
        "generated_token_logprobs_used_as_answer_side_diagnostic_only"
    ] is True
    assert '"raw_response":' not in serialized
    assert '"raw_api_response":' not in serialized


def test_goal_named_projection_bundle_module_reexports_schema():
    assert ArtifactProjectionBundleV1 is ProjectionBundleV1


def test_projection_bundle_rejects_raw_api_response_bodies():
    payload = _complete_payload()
    payload["judge_run_manifest"] = {
        **payload["judge_run_manifest"],
        "raw_response": {"choices": [{"message": "do not store"}]},
    }

    with pytest.raises(ValueError, match="raw_response"):
        ProjectionBundleV1.from_dict(payload)


def test_generated_token_logprobs_require_answer_side_diagnostic_flag():
    payload = _complete_payload()
    payload["metric_bridge_witness"][
        "generated_token_logprobs_used_as_answer_side_diagnostic_only"
    ] = False

    with pytest.raises(ValueError, match="answer-side"):
        ProjectionBundleV1.from_dict(payload)


def test_missing_contract_fields_fail_closed_instead_of_supporting_validation():
    payload = _complete_payload()
    payload["projection_plan"].pop("score_manifest_hash")

    bundle = ProjectionBundleV1.from_dict(payload)
    ledger = bundle.to_dict()["claim_ledger"]

    assert bundle.to_dict()["artifact_status"] == "incomplete"
    assert ledger["artifact_status"] == "incomplete"
    assert "replayable_artifact_evidence" not in ledger["allowed_claims"]
    assert "no_aggregated_headline_claim" in ledger["denied_claims"]
    assert "measurement_validation" in ledger["denied_claims"]


def test_epf_final_metadata_maps_to_projection_bundle_without_raw_api_bodies():
    final_manifest = {
        "schema_version": "epf_final_manifest_v1",
        "terminal_state": "EPF_FINAL_REVIEWABLE",
        "claim_status": "operational_utility_only/no_claim_upgrade",
        "claim_ceiling": "operational_utility_only/no_claim_upgrade",
        "evidence_class": "backend_constrained_operational_candidate_package",
        "artifacts": {
            "final_claim_request": "artifacts/experiments/epf_final/final_claim_request.json",
            "scoped_operational_evaluation_summary": (
                "artifacts/experiments/epf_final/scoped_operational_evaluation_summary.json"
            ),
        },
        "provenance": {
            "source": "epf_live_api_finalizer",
            "silver_label_package": {
                "silver_label_manifest": "artifacts/experiments/epf_c_silver_labels/silver_label_manifest.json",
                "silver_labels": "artifacts/experiments/epf_c_silver_labels/silver_labels.jsonl",
            },
        },
        "denied_claims": ["metric bridge support", "measurement_validation", "vinfo_proxy_supported"],
    }
    final_claim_request = {
        "claim_status": "operational_utility_only/no_claim_upgrade",
        "route5_unlock_requested": False,
        "route8_unlock_requested": False,
        "measurement_validation_claim": False,
        "human_external_gold_validation": False,
        "teacher_forced_nll_support": False,
    }
    scoped_summary = {
        "label_count": 8,
        "human_external_gold_labels_used": False,
        "teacher_forced_fixed_target_nll_available": False,
        "scoped_operational_inputs": {
            "chat_logprob_confidence": {
                "diagnostic_count": 8,
                "generated_token_logprobs_available": True,
                "raw_response_stored": False,
                "teacher_forced_fixed_target_nll_available": False,
            }
        },
    }

    bundle = projection_bundle_from_epf_final_metadata(
        final_manifest=final_manifest,
        final_claim_request=final_claim_request,
        scoped_operational_evaluation_summary=scoped_summary,
    )
    payload = bundle.to_dict()
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["source_mode"] == "epf_final_metadata"
    assert payload["claim_ledger"]["current_claim_level"] == "operational_utility_only/no_claim_upgrade"
    assert payload["claim_ledger"]["route_5_locked"] is True
    assert payload["claim_ledger"]["route_8_locked"] is True
    assert payload["metric_bridge_witness"]["fixed_target_nll_supported"] is False
    assert payload["cost_latency_ledger"]["total_tokens"] == 0
    assert '"raw_response":' not in serialized
    assert '"raw_api_response":' not in serialized
