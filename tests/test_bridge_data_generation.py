from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from api.settings import ApiProviderProfile
from conftest import assert_importing_modules_does_not_load_forbidden_sdks
from cps.experiments.bridge_data_generation import (
    BridgeDataGenerationGateError,
    BridgeDataGenerationValidationError,
    EVIDENCE_STRENGTH_BANDS,
    build_live_provider_profile_callables,
    generate_candidate_set_constrained_task_packets,
    generate_graded_positive_control_task_packets,
    generate_bridge_canary_task_packets,
    generate_logloss_positive_control_task_packets,
    preflight_bridge_data_generation_provider,
    run_bridge_data_generation,
    run_bridge_data_generation_from_provider_profile,
    run_logloss_positive_control,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "runs" / "bridge-data-generation-bio-attribute.json"
P45_REQUIRED_FIELDS = {
    "pair_id",
    "stratum_id",
    "task_family",
    "model_tier",
    "materialization_policy",
    "metric",
    "block_size",
    "candidate_slice_band",
    "context_id",
    "block_id",
    "delta_utility",
    "delta_logloss",
    "replicate_count",
    "source",
    "notes",
}


def _json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _jsonl(path: str | Path) -> list[dict]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _config(workspace_tmp_dir: Path, **overrides) -> Path:
    payload = _json(CONFIG_PATH)
    payload.update(
        {
            "mode": "live_operator_approved",
            "operator_approval": True,
            "provider_profile": "mocked-test-profile",
            "fixed_model_id": "mocked-fixed-logprob-model",
            "strong_review_model_id": "mocked-strong-review-model",
        }
    )
    payload.update(overrides)
    return _write_json(workspace_tmp_dir / "bridge-data-generation.json", payload)


def _packet(task_id: str = "task-001") -> dict:
    return {
        "task_id": task_id,
        "question": "Which attribute is supported by the supplied context?",
        "target_answer": "The enzyme is thermostable.",
        "gold_facts": ["The target answer must mention thermostability."],
        "candidate_findings": ["Candidate block states the enzyme remains active at high temperature."],
        "baseline_context": "The enzyme was isolated from a bacterial sample.",
        "added_block": "The enzyme remains active after exposure to high temperature.",
    }


def _measured_logloss(_packet: dict) -> dict:
    return {
        "loss_without": 3.5,
        "loss_with": 2.75,
        "delta_logloss": 0.75,
        "token_logprobs_without": [-1.0, -2.5],
        "token_logprobs_with": [-1.0, -1.75],
        "logprob_available": True,
        "logloss_source": "measured_logprob",
    }


def _utility_review(_packet: dict) -> dict:
    return {
        "utility_without": 0.2,
        "utility_with": 0.85,
        "delta_utility": 0.65,
        "sufficiency_rationale": "Added block directly supports the target answer.",
    }


def _accepted(_packet: dict, _logloss: dict, _review: dict) -> dict:
    return {
        "review_status": "accepted",
        "target_clear": True,
        "intervention_valid": True,
        "no_leakage": True,
        "no_duplicate_trivial_case": True,
        "utility_score_consistent": True,
    }


def _run_live_mocked(workspace_tmp_dir: Path, monkeypatch, **kwargs):
    monkeypatch.setenv("CPS_ALLOW_LIVE_API", "1")
    monkeypatch.setenv("P45_ALLOW_API_DATA_GENERATION", "1")
    config_overrides = kwargs.get("config_overrides", {})
    return run_bridge_data_generation(
        config_path=_config(workspace_tmp_dir, output_dir=str(workspace_tmp_dir / "out"), **config_overrides),
        output_dir=workspace_tmp_dir / "out",
        task_packets=kwargs.get("task_packets", [_packet()]),
        logloss_scorer=kwargs.get("logloss_scorer", _measured_logloss),
        utility_reviewer=kwargs.get("utility_reviewer", _utility_review),
        adjudicator=kwargs.get("adjudicator", _accepted),
    )


def _provider_config(workspace_tmp_dir: Path, **overrides) -> Path:
    payload = _json(CONFIG_PATH)
    payload.update(
        {
            "mode": "live_operator_approved",
            "operator_approval": True,
            "provider_profile": "dashscope-qwen-phase1",
            "fixed_model_id": "mocked-fixed-logprob-model",
            "strong_review_model_id": "mocked-strong-review-model",
            "output_dir": str(workspace_tmp_dir / "out"),
        }
    )
    payload.update(overrides)
    return _write_json(workspace_tmp_dir / "bridge-provider-live.json", payload)


def _credential_csv(workspace_tmp_dir: Path) -> Path:
    path = workspace_tmp_dir / "mock-apiKey.csv"
    path.write_text("api_key\nsk-test-not-real\n", encoding="utf-8")
    return path


def _provider_env(**overrides) -> dict[str, str]:
    payload = {
        "CPS_ALLOW_LIVE_API": "1",
        "P45_ALLOW_API_DATA_GENERATION": "1",
        "DASHSCOPE_API_KEY": "mock-secret-not-real",
    }
    payload.update(overrides)
    return payload


def _logprob_response(content: str = "The enzyme is thermostable.", logprobs: list[float] | None = None) -> dict:
    return {
        "choices": [
            {
                "message": {
                    "content": content,
                    "logprobs": {
                        "content": [{"token": str(index), "logprob": value} for index, value in enumerate(logprobs or [-1.0, -2.0])]
                    },
                }
            }
        ]
    }


def _json_response(payload: dict) -> dict:
    return {"choices": [{"message": {"content": json.dumps(payload)}}]}


class MockOpenAICompatibleClient:
    def __init__(self, responses: list[dict]):
        self.responses = list(responses)
        self.calls: list[dict] = []

    def chat_completion(self, **kwargs):
        self.calls.append(dict(kwargs))
        if not self.responses:
            raise AssertionError("mock provider received more calls than expected")
        return self.responses.pop(0)


def _accepted_provider_responses() -> list[dict]:
    return [
        _logprob_response(logprobs=[-2.0, -1.5]),
        _logprob_response(logprobs=[-1.25, -1.5]),
        _json_response(
            {
                "utility_without": 0.2,
                "utility_with": 0.85,
                "sufficiency_rationale": "Added block directly supports the target answer.",
            }
        ),
        _json_response(
            {
                "review_status": "accepted",
                "target_clear": True,
                "intervention_valid": True,
                "no_leakage": True,
                "no_duplicate_trivial_case": True,
                "utility_score_consistent": True,
            }
        ),
    ]


def test_generated_accepted_row_matches_p45_schema_and_provenance(workspace_tmp_dir, monkeypatch):
    result = _run_live_mocked(workspace_tmp_dir, monkeypatch)

    rows = _jsonl(result["artifacts"]["accepted_bridge_calibration_pairs"])
    assert len(rows) == 1
    row = rows[0]
    assert P45_REQUIRED_FIELDS.issubset(row)
    assert row["source"] == "operator_provided"
    assert row["data_origin"] == "api_generated"
    assert row["delta_utility_source"] == "strong_model_adjudicated"
    assert row["delta_logloss_source"] == "measured_logprob"
    assert row["review_status"] == "accepted"
    assert row["delta_logloss"] == pytest.approx(0.75)
    assert row["delta_utility"] == pytest.approx(0.65)


def test_bridge_canary_task_packets_use_varied_evidence_strength_bands():
    packets = generate_bridge_canary_task_packets(sample_limit=8)

    assert len(packets) == 8
    bands = [packet["evidence_strength_band"] for packet in packets]
    assert set(EVIDENCE_STRENGTH_BANDS).issubset(set(bands))
    assert len(set(bands)) >= 5
    for packet in packets:
        assert packet["task_family"] == "bio_attribute"
        assert packet["materialization_policy"] == "fixed_order_v1"
        assert packet["block_size"] == 1
        assert packet["candidate_slice_band"] == "top_L"
        assert packet["target_answer"].lower() not in packet["question"].lower()
        assert packet["target_answer"].lower() not in packet["baseline_context"].lower()


def test_review_artifacts_preserve_utility_audit_fields(workspace_tmp_dir, monkeypatch):
    result = _run_live_mocked(workspace_tmp_dir, monkeypatch, task_packets=[_packet("audit-task")])

    review_rows = _jsonl(result["artifacts"]["review_rows"])
    accepted_rows = _jsonl(result["artifacts"]["accepted_bridge_calibration_pairs"])
    assert review_rows[0]["utility_without"] == pytest.approx(0.2)
    assert review_rows[0]["utility_with"] == pytest.approx(0.85)
    assert review_rows[0]["delta_utility"] == pytest.approx(0.65)
    assert review_rows[0]["utility_rationale"] == "Added block directly supports the target answer."
    assert accepted_rows[0]["utility_without"] == pytest.approx(0.2)
    assert accepted_rows[0]["utility_with"] == pytest.approx(0.85)
    assert accepted_rows[0]["utility_rationale"] == "Added block directly supports the target answer."


def test_unavailable_logprob_marks_row_unusable_and_excludes_export(workspace_tmp_dir, monkeypatch):
    def missing_logprob(_packet):
        return {
            "loss_without": None,
            "loss_with": None,
            "delta_logloss": None,
            "logprob_available": False,
            "logloss_source": "unavailable",
        }

    result = _run_live_mocked(workspace_tmp_dir, monkeypatch, logloss_scorer=missing_logprob)

    assert result["summary"]["accepted_rows"] == 0
    assert result["summary"]["unusable_rows"] == 1
    assert _jsonl(result["artifacts"]["accepted_bridge_calibration_pairs"]) == []
    review_rows = _jsonl(result["artifacts"]["review_rows"])
    assert review_rows[0]["usable_for_bridge_calibration"] is False
    assert "logprob_unavailable" in review_rows[0]["reason_codes"]


def test_low_delta_logloss_is_marked_bridge_uninformative(workspace_tmp_dir, monkeypatch):
    def low_signal_logloss(_packet):
        return {
            "loss_without": 1.0004,
            "loss_with": 1.0,
            "delta_logloss": 0.0004,
            "token_logprobs_without": [-0.5002, -0.5002],
            "token_logprobs_with": [-0.5, -0.5],
            "logprob_available": True,
            "logloss_source": "measured_logprob",
        }

    result = _run_live_mocked(workspace_tmp_dir, monkeypatch, logloss_scorer=low_signal_logloss)

    assert result["summary"]["accepted_rows"] == 0
    review_rows = _jsonl(result["artifacts"]["review_rows"])
    assert review_rows[0]["bridge_signal_status"] == "bridge_uninformative"
    assert "delta_logloss_below_informative_threshold" in review_rows[0]["reason_codes"]


def test_negative_delta_logloss_is_reported_and_excluded_from_canary_export(workspace_tmp_dir, monkeypatch):
    def negative_logloss(_packet):
        return {
            "loss_without": 1.0,
            "loss_with": 1.5,
            "delta_logloss": -0.5,
            "token_logprobs_without": [-0.4, -0.6],
            "token_logprobs_with": [-0.7, -0.8],
            "logprob_available": True,
            "logloss_source": "measured_logprob",
        }

    result = _run_live_mocked(workspace_tmp_dir, monkeypatch, logloss_scorer=negative_logloss)

    assert result["summary"]["accepted_rows"] == 0
    review_rows = _jsonl(result["artifacts"]["review_rows"])
    assert review_rows[0]["bridge_signal_status"] == "bridge_uninformative"
    assert "negative_delta_logloss" in review_rows[0]["reason_codes"]


def test_rejected_review_row_is_excluded(workspace_tmp_dir, monkeypatch):
    def rejected(_packet, _logloss, _review):
        payload = _accepted(_packet, _logloss, _review)
        payload["review_status"] = "rejected"
        return payload

    result = _run_live_mocked(workspace_tmp_dir, monkeypatch, adjudicator=rejected)

    assert result["summary"]["accepted_rows"] == 0
    assert result["summary"]["rejected_rows"] == 1
    assert _jsonl(result["artifacts"]["accepted_bridge_calibration_pairs"]) == []


def test_ambiguous_review_row_is_excluded(workspace_tmp_dir, monkeypatch):
    def ambiguous(_packet, _logloss, _review):
        payload = _accepted(_packet, _logloss, _review)
        payload["review_status"] = "ambiguous"
        return payload

    result = _run_live_mocked(workspace_tmp_dir, monkeypatch, adjudicator=ambiguous)

    assert result["summary"]["accepted_rows"] == 0
    assert result["summary"]["ambiguous_rows"] == 1
    assert _jsonl(result["artifacts"]["accepted_bridge_calibration_pairs"]) == []


def test_default_dry_run_makes_no_live_calls_or_socket_calls(workspace_tmp_dir, monkeypatch):
    monkeypatch.delenv("CPS_ALLOW_LIVE_API", raising=False)
    monkeypatch.delenv("P45_ALLOW_API_DATA_GENERATION", raising=False)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("P45 bridge data generation dry_run must not open sockets")

    def forbidden_call(_packet):
        raise AssertionError("dry_run must not call provider functions")

    monkeypatch.setattr(socket, "socket", blocked_socket)
    result = run_bridge_data_generation(
        config_path=CONFIG_PATH,
        output_dir=workspace_tmp_dir / "dry-run",
        task_packets=[_packet()],
        logloss_scorer=forbidden_call,
        utility_reviewer=forbidden_call,
        adjudicator=forbidden_call,
    )

    assert result["manifest"]["mode"] == "dry_run"
    assert result["manifest"]["live_api_used"] is False
    assert result["summary"]["accepted_rows"] == 0
    assert _jsonl(result["artifacts"]["accepted_bridge_calibration_pairs"]) == []


def test_live_mode_requires_both_environment_flags(workspace_tmp_dir, monkeypatch):
    monkeypatch.setenv("CPS_ALLOW_LIVE_API", "1")
    monkeypatch.delenv("P45_ALLOW_API_DATA_GENERATION", raising=False)

    with pytest.raises(BridgeDataGenerationGateError, match="P45_ALLOW_API_DATA_GENERATION"):
        run_bridge_data_generation(
            config_path=_config(workspace_tmp_dir),
            output_dir=workspace_tmp_dir / "out",
            task_packets=[_packet()],
            logloss_scorer=_measured_logloss,
            utility_reviewer=_utility_review,
            adjudicator=_accepted,
            env={"CPS_ALLOW_LIVE_API": "1", "P45_ALLOW_API_DATA_GENERATION": ""},
        )


def test_judge_generated_logloss_is_rejected(workspace_tmp_dir, monkeypatch):
    def fake_logloss(_packet):
        return {
            "loss_without": 3.5,
            "loss_with": 2.75,
            "delta_logloss": 0.75,
            "logprob_available": True,
            "logloss_source": "strong_model_estimated",
        }

    result = _run_live_mocked(workspace_tmp_dir, monkeypatch, logloss_scorer=fake_logloss)

    assert result["summary"]["accepted_rows"] == 0
    review_rows = _jsonl(result["artifacts"]["review_rows"])
    assert review_rows[0]["delta_logloss_source"] == "strong_model_estimated"
    assert "delta_logloss_not_measured_logprob" in review_rows[0]["reason_codes"]


def test_generated_outputs_do_not_claim_measurement_validation(workspace_tmp_dir, monkeypatch):
    result = _run_live_mocked(workspace_tmp_dir, monkeypatch)

    combined = "\n".join(Path(path).read_text(encoding="utf-8") for path in result["artifacts"].values())
    assert '"measurement_validation_claim": true' not in combined
    assert '"measurement_validated_allowed": true' not in combined
    assert "measurement_validated" in combined
    manifest = _json(result["artifacts"]["manifest"])
    assert manifest["human_labels_present"] is False
    assert manifest["kappa_present"] is False
    assert manifest["measurement_validated_allowed"] is False


def test_import_does_not_load_external_provider_sdks():
    assert_importing_modules_does_not_load_forbidden_sdks(["cps.experiments.bridge_data_generation"])


def test_provider_profile_missing_local_config_fails_closed(workspace_tmp_dir):
    missing = workspace_tmp_dir / "missing-live.local.json"

    with pytest.raises(BridgeDataGenerationGateError, match="local live config does not exist"):
        build_live_provider_profile_callables(config_path=missing, env=_provider_env())


def test_provider_profile_missing_env_gates_fails_closed(workspace_tmp_dir):
    config_path = _provider_config(workspace_tmp_dir)

    with pytest.raises(BridgeDataGenerationGateError, match="CPS_ALLOW_LIVE_API"):
        build_live_provider_profile_callables(config_path=config_path, env={})


def test_provider_profile_operator_approval_false_fails_closed(workspace_tmp_dir):
    config_path = _provider_config(workspace_tmp_dir, operator_approval=False)

    with pytest.raises(BridgeDataGenerationGateError, match="operator_approval"):
        build_live_provider_profile_callables(config_path=config_path, env=_provider_env())


def test_provider_profile_fixed_model_without_logprob_capability_fails_closed(workspace_tmp_dir, monkeypatch):
    monkeypatch.setitem(
        __import__("api.settings").settings.API_PROVIDER_PROFILES,
        "mock-no-logprob",
        ApiProviderProfile(
            profile_name="mock-no-logprob",
            provider_name="mock",
            api_style="openai_chat_compatible",
            base_url_env="MOCK_BASE_URL",
            api_key_env="MOCK_API_KEY",
            default_base_url="https://mock.invalid/v1",
            role_models={"frontier": "mock-frontier", "small": "mock-small", "coding": "mock-coding"},
            phase1_logprob_ready=False,
            note="mock profile without logprob support",
        ),
    )
    config_path = _provider_config(workspace_tmp_dir, provider_profile="mock-no-logprob")

    with pytest.raises(BridgeDataGenerationGateError, match="logprob-ready"):
        build_live_provider_profile_callables(config_path=config_path, env=_provider_env(MOCK_API_KEY="mock"))


def test_provider_profile_no_logprobs_marks_row_unusable(workspace_tmp_dir):
    config_path = _provider_config(workspace_tmp_dir)
    client = MockOpenAICompatibleClient(
        [
            {"choices": [{"message": {"content": "The enzyme is thermostable."}}]},
            _logprob_response(),
            _json_response({"utility_without": 0.2, "utility_with": 0.85, "sufficiency_rationale": "reviewed"}),
            _json_response(
                {
                    "review_status": "accepted",
                    "target_clear": True,
                    "intervention_valid": True,
                    "no_leakage": True,
                    "no_duplicate_trivial_case": True,
                    "utility_score_consistent": True,
                }
            ),
        ]
    )
    result = run_bridge_data_generation_from_provider_profile(
        config_path=config_path,
        task_packets=[_packet()],
        env=_provider_env(),
        client_factory=lambda _profile, _config: client,
    )

    assert result["summary"]["accepted_rows"] == 0
    assert result["summary"]["unusable_rows"] == 1
    assert _jsonl(result["artifacts"]["accepted_bridge_calibration_pairs"]) == []


def test_provider_profile_reviewer_cannot_fill_delta_logloss(workspace_tmp_dir):
    config_path = _provider_config(workspace_tmp_dir)
    responses = _accepted_provider_responses()
    responses[2] = _json_response(
        {
            "utility_without": 0.2,
            "utility_with": 0.85,
            "delta_logloss": 999.0,
            "sufficiency_rationale": "Reviewer attempted to provide logloss.",
        }
    )
    client = MockOpenAICompatibleClient(responses)
    result = run_bridge_data_generation_from_provider_profile(
        config_path=config_path,
        task_packets=[_packet()],
        env=_provider_env(),
        client_factory=lambda _profile, _config: client,
    )

    assert result["summary"]["accepted_rows"] == 0
    review_rows = _jsonl(result["artifacts"]["review_rows"])
    assert "utility_reviewer_supplied_logloss" in review_rows[0]["reason_codes"]


def test_provider_profile_accepted_mock_row_exports_p45_schema(workspace_tmp_dir):
    config_path = _provider_config(workspace_tmp_dir)
    client = MockOpenAICompatibleClient(_accepted_provider_responses())
    result = run_bridge_data_generation_from_provider_profile(
        config_path=config_path,
        task_packets=[_packet()],
        env=_provider_env(),
        client_factory=lambda _profile, _config: client,
    )

    rows = _jsonl(result["artifacts"]["accepted_bridge_calibration_pairs"])
    assert len(rows) == 1
    assert P45_REQUIRED_FIELDS.issubset(rows[0])
    assert rows[0]["delta_logloss_source"] == "measured_logprob"
    assert rows[0]["delta_utility_source"] == "strong_model_adjudicated"
    assert rows[0]["review_status"] == "accepted"
    assert rows[0]["delta_logloss"] == pytest.approx(0.75)


def test_provider_profile_outputs_do_not_claim_measurement_validation(workspace_tmp_dir):
    config_path = _provider_config(workspace_tmp_dir)
    client = MockOpenAICompatibleClient(_accepted_provider_responses())
    result = run_bridge_data_generation_from_provider_profile(
        config_path=config_path,
        task_packets=[_packet()],
        env=_provider_env(),
        client_factory=lambda _profile, _config: client,
    )

    combined = "\n".join(Path(path).read_text(encoding="utf-8") for path in result["artifacts"].values())
    assert '"measurement_validation_claim": true' not in combined
    assert '"measurement_validated_allowed": true' not in combined


def test_provider_preflight_accepts_local_credential_file_without_env_secret(workspace_tmp_dir):
    credential_csv = _credential_csv(workspace_tmp_dir)
    config_path = _provider_config(
        workspace_tmp_dir,
        credential_source={"local_credential_file": str(credential_csv), "api_key_env": "DASHSCOPE_API_KEY"},
    )
    env = _provider_env(DASHSCOPE_API_KEY="")

    result = preflight_bridge_data_generation_provider(config_path=config_path, env=env)

    assert result["ready"] is True
    assert result["credential_source_kind"] == "local_credential_file"
    rendered = json.dumps(result)
    assert "sk-test-not-real" not in rendered


def test_provider_profile_uses_local_credential_file_without_env_secret(workspace_tmp_dir):
    credential_csv = _credential_csv(workspace_tmp_dir)
    config_path = _provider_config(
        workspace_tmp_dir,
        credential_source={"local_credential_file": str(credential_csv), "api_key_env": "DASHSCOPE_API_KEY"},
    )
    env = _provider_env(DASHSCOPE_API_KEY="")
    observed = {}
    client = MockOpenAICompatibleClient(_accepted_provider_responses())

    def factory(profile, _config):
        observed["api_key_present"] = bool(profile.api_key)
        observed["profile_name"] = profile.profile_name
        return client

    result = run_bridge_data_generation_from_provider_profile(
        config_path=config_path,
        task_packets=[_packet()],
        env=env,
        client_factory=factory,
    )

    assert observed == {"api_key_present": True, "profile_name": "dashscope-qwen-phase1"}
    assert result["summary"]["accepted_rows"] == 1


def test_logloss_positive_control_task_packets_are_explicit_target_controls():
    packets = generate_logloss_positive_control_task_packets(sample_limit=8)

    assert len(packets) == 8
    for packet in packets:
        target = packet["target_answer"]
        assert packet["task_family"] == "bio_attribute"
        assert packet["materialization_policy"] == "fixed_order_v1"
        assert packet["block_size"] == 1
        assert "UNKNOWN" in packet["question"]
        assert target not in packet["baseline_context"]
        assert target in packet["added_block"]
        assert "delta_logloss" not in packet
        assert "delta_utility" not in packet


def test_logloss_positive_control_uses_only_measured_logloss_path(workspace_tmp_dir):
    packet = generate_logloss_positive_control_task_packets(sample_limit=1)[0]
    calls = []

    def measured_positive_control(observed_packet):
        calls.append(observed_packet["task_id"])
        return {
            "loss_without": 4.25,
            "loss_with": 1.5,
            "delta_logloss": 2.75,
            "token_logprobs_without": [-2.0, -2.25],
            "token_logprobs_with": [-0.75, -0.75],
            "logprob_available": True,
            "logloss_source": "measured_logprob",
        }

    result = run_logloss_positive_control(
        config_path=_config(workspace_tmp_dir, output_dir=str(workspace_tmp_dir / "positive-control")),
        output_dir=workspace_tmp_dir / "positive-control",
        task_packets=[packet],
        logloss_scorer=measured_positive_control,
        env=_provider_env(),
    )

    assert calls == [packet["task_id"]]
    rows = _jsonl(result["artifacts"]["logloss_positive_control_rows"])
    assert rows[0]["target_answer"] == packet["target_answer"]
    assert rows[0]["delta_logloss"] == pytest.approx(2.75)
    assert rows[0]["delta_logloss_positive"] is True
    assert rows[0]["sufficient_signal"] is True
    assert rows[0]["reason_codes"] == []
    summary = _json(result["artifacts"]["logloss_positive_control_summary"])
    assert summary["positive_delta_logloss_rows"] == 1
    assert summary["sufficient_signal_rows"] == 1
    combined = "\n".join(Path(path).read_text(encoding="utf-8") for path in result["artifacts"].values())
    assert '"measurement_validation_claim": true' not in combined
    assert "calibrated_proxy_supported" not in combined


def test_graded_positive_control_task_packets_have_fit_and_diagnostic_rows():
    packets = generate_graded_positive_control_task_packets(sample_limit=8)

    assert len(packets) == 8
    bands = [packet["evidence_strength_band"] for packet in packets]
    assert set(EVIDENCE_STRENGTH_BANDS).issubset(set(bands))
    assert sum(1 for packet in packets if packet["bridge_fit_eligible"]) >= 6
    assert sum(1 for packet in packets if not packet["bridge_fit_eligible"]) >= 1
    for packet in packets:
        target = packet["target_answer"]
        assert packet["task_family"] == "bio_attribute"
        assert packet["materialization_policy"] == "fixed_order_v1"
        assert packet["block_size"] == 1
        assert "UNKNOWN" in packet["question"]
        assert target not in packet["baseline_context"]
        if packet["bridge_fit_eligible"]:
            assert target in packet["added_block"]
        assert "delta_logloss" not in packet
        assert "delta_utility" not in packet


def test_bridge_fit_ineligible_rows_are_reported_but_not_exported(workspace_tmp_dir, monkeypatch):
    eligible_packet = _packet("eligible-task")
    eligible_packet["bridge_fit_eligible"] = True
    eligible_packet["evidence_strength_band"] = "explicit_answer"
    ineligible_packet = _packet("diagnostic-task")
    ineligible_packet["bridge_fit_eligible"] = False
    ineligible_packet["evidence_strength_band"] = "irrelevant"

    result = _run_live_mocked(
        workspace_tmp_dir,
        monkeypatch,
        task_packets=[eligible_packet, ineligible_packet],
    )

    accepted_rows = _jsonl(result["artifacts"]["accepted_bridge_calibration_pairs"])
    review_rows = _jsonl(result["artifacts"]["review_rows"])
    assert [row["pair_id"] for row in accepted_rows] == ["eligible-task"]
    diagnostic = next(row for row in review_rows if row["task_id"] == "diagnostic-task")
    assert diagnostic["bridge_fit_eligible"] is False
    assert diagnostic["usable_for_bridge_calibration"] is False
    assert "bridge_fit_ineligible" in diagnostic["reason_codes"]
    assert result["summary"]["bridge_fit_eligible_rows"] == 1
    assert result["summary"]["accepted_rows"] == 1


def test_reviewer_non_enum_evidence_band_is_audit_only(workspace_tmp_dir, monkeypatch):
    def reviewer_with_free_text_band(_packet):
        payload = _utility_review(_packet)
        payload["evidence_strength_band"] = "exact target entailed"
        return payload

    result = _run_live_mocked(
        workspace_tmp_dir,
        monkeypatch,
        utility_reviewer=reviewer_with_free_text_band,
    )

    review_rows = _jsonl(result["artifacts"]["review_rows"])
    assert result["summary"]["accepted_rows"] == 1
    assert "unsupported_evidence_strength_band" not in review_rows[0]["reason_codes"]
    assert review_rows[0]["reviewer_evidence_strength_band"] == "exact target entailed"


def test_p45d_mode_writes_canary_summary_artifacts(workspace_tmp_dir, monkeypatch):
    packet = generate_graded_positive_control_task_packets(sample_limit=3)[2]
    result = _run_live_mocked(
        workspace_tmp_dir,
        monkeypatch,
        task_packets=[packet],
        config_overrides={"task_packet_mode": "bridge_canary_v3"},
    )

    assert "p45d_canary_summary" in result["artifacts"]
    assert "p45d_canary_summary_report" in result["artifacts"]
    summary = _json(result["artifacts"]["p45d_canary_summary"])
    assert summary["task_packet_mode"] == "bridge_canary_v3"
    assert summary["total_task_packets"] == 1
    assert summary["bridge_fit_eligible_rows"] == 1
    assert summary["measurement_validation_claim"] is False


def test_candidate_set_constrained_task_packets_align_evidence_and_fit_rows():
    packets = generate_candidate_set_constrained_task_packets(sample_limit=8)

    assert len(packets) == 8
    candidate_sets = {tuple(packet["candidate_answer_set"]) for packet in packets}
    assert len(candidate_sets) == 1
    assert len(next(iter(candidate_sets))) == 8
    bands = [packet["evidence_strength_band"] for packet in packets]
    assert set(EVIDENCE_STRENGTH_BANDS).issubset(set(bands))
    assert sum(1 for packet in packets if packet["bridge_fit_eligible"]) >= 6
    for packet in packets:
        assert packet["canary_design"] == "p45e_candidate_set_constrained_bridge"
        assert packet["target_answer"] in packet["candidate_answer_set"]
        assert packet["candidate_set_size_before"] == 8
        assert packet["candidate_set_size_after"] <= packet["candidate_set_size_before"]
        assert "UNKNOWN" in packet["question"]
        assert "candidate list" in packet["question"].lower()
        assert packet["target_answer"] not in packet["baseline_context"]
        assert "delta_logloss" not in packet
        assert "delta_utility" not in packet


def test_p45e_mode_writes_candidate_set_summary_and_exports_audit_fields(workspace_tmp_dir, monkeypatch):
    packet = generate_candidate_set_constrained_task_packets(sample_limit=3)[2]
    result = _run_live_mocked(
        workspace_tmp_dir,
        monkeypatch,
        task_packets=[packet],
        config_overrides={"task_packet_mode": "bridge_canary_v4"},
    )

    assert "p45e_canary_summary" in result["artifacts"]
    assert "p45e_canary_summary_report" in result["artifacts"]
    summary = _json(result["artifacts"]["p45e_canary_summary"])
    rows = _jsonl(result["artifacts"]["accepted_bridge_calibration_pairs"])
    assert summary["task_packet_mode"] == "bridge_canary_v4"
    assert summary["candidate_set_size_before_distribution"] == {"8": 1}
    assert summary["candidate_set_size_after_distribution"] == {"2": 1}
    assert rows[0]["candidate_set_size_before"] == 8
    assert rows[0]["candidate_set_size_after"] == 2
    assert rows[0]["bridge_fit_eligible"] is True
