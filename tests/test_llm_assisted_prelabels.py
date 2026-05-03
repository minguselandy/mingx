from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from cps.experiments.human_label_kappa import LABEL_DIMENSIONS
from cps.experiments.llm_assisted_prelabels import (
    PrelabelGateError,
    build_llm_assisted_prelabels,
    build_v4_flash_prelabel_prompt,
    parse_llm_prelabel_output,
)


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def _case_artifact(case_id: str = "case-001", condition: str = "cps_runtime_audit_scaffold") -> dict:
    return {
        "case_id": case_id,
        "condition": condition,
        "model_alias": "deepseek_v4_flash",
        "input_case": {"prompt": "Explain the CPS evidence state."},
        "materialized_context": {"content": "Human labels and kappa remain required."},
        "model_output": {"answer": "Offline evidence is not measurement validation."},
        "artifact_refs": {
            "input_case_json": "cases/case-001/input_case.json",
            "model_output_json": "cases/case-001/model_output.json",
        },
    }


def _valid_prelabel(case_id: str = "case-001", condition: str = "cps_runtime_audit_scaffold") -> dict:
    return {
        "label_source": "llm_assisted_prelabel",
        "judge_model_alias": "deepseek_v4_flash",
        "not_human_label": True,
        "requires_human_confirmation": True,
        "case_id": case_id,
        "condition": condition,
        "model_alias": "deepseek_v4_flash",
        "dimension_labels": {
            dimension: {
                "suggested_label": 1,
                "confidence_milli": 650,
                "rationale": f"Draft rationale for {dimension}.",
                "evidence_refs": ["model_output.json"],
                "uncertainty_notes": "Requires human confirmation.",
                "requires_human_review": True,
            }
            for dimension in LABEL_DIMENSIONS
        },
        "overall_summary": "Draft only.",
        "human_review_priority": "medium",
        "claim_boundary": {
            "counts_as_human_label": False,
            "measurement_validated_allowed": False,
        },
    }


def test_prompt_contains_not_human_label_and_claim_boundary_warnings():
    prompt = build_v4_flash_prelabel_prompt(_case_artifact())

    assert "not a human label" in prompt
    assert "JSON only" in prompt
    assert "0 = fail" in prompt
    assert "1 = partial" in prompt
    assert "2 = pass" in prompt
    assert "Human confirmation and human-human kappa are still required" in prompt
    for dimension in LABEL_DIMENSIONS:
        assert dimension in prompt


def test_prelabel_parser_accepts_valid_json_string():
    parsed = parse_llm_prelabel_output(json.dumps(_valid_prelabel(), sort_keys=True))

    assert parsed["label_source"] == "llm_assisted_prelabel"
    assert parsed["judge_model_alias"] == "deepseek_v4_flash"
    assert parsed["not_human_label"] is True
    assert parsed["requires_human_confirmation"] is True
    assert parsed["measurement_validated_allowed"] is False
    assert parsed["counts_as_human_labels"] is False
    assert set(parsed["dimension_labels"]) == set(LABEL_DIMENSIONS)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.__setitem__("label_source", "human_labels"),
        lambda payload: payload.__setitem__("judge_model_alias", "deepseek_v4_pro"),
        lambda payload: payload.__setitem__("not_human_label", False),
        lambda payload: payload.__setitem__("requires_human_confirmation", False),
        lambda payload: payload["claim_boundary"].__setitem__("measurement_validated_allowed", True),
        lambda payload: payload["claim_boundary"].__setitem__("counts_as_human_label", True),
        lambda payload: payload["dimension_labels"].pop("answer_correctness"),
        lambda payload: payload["dimension_labels"]["answer_correctness"].__setitem__("suggested_label", 3),
        lambda payload: payload["dimension_labels"]["answer_correctness"].__setitem__("confidence_milli", 1001),
    ],
)
def test_prelabel_parser_rejects_unsafe_or_invalid_outputs(mutator):
    payload = _valid_prelabel()
    mutator(payload)

    with pytest.raises(ValueError):
        parse_llm_prelabel_output(payload)


def test_dry_run_fake_model_writes_deterministic_prelabel_outputs(workspace_tmp_dir):
    first = build_llm_assisted_prelabels(
        workspace_tmp_dir / "first",
        case_artifacts=[_case_artifact()],
    )
    second = build_llm_assisted_prelabels(
        workspace_tmp_dir / "second",
        case_artifacts=[_case_artifact()],
    )

    first_outputs = first["generated_outputs"]
    second_outputs = second["generated_outputs"]
    assert _read(first_outputs["llm_prelabels_jsonl"]) == _read(second_outputs["llm_prelabels_jsonl"])
    assert _read(first_outputs["llm_prelabel_summary_markdown"]) == _read(second_outputs["llm_prelabel_summary_markdown"])
    assert _json(first_outputs["llm_prelabel_summary_json"]) == _json(second_outputs["llm_prelabel_summary_json"])

    summary = _json(first_outputs["llm_prelabel_summary_json"])
    assert summary["prelabels_generated"] == 1
    assert summary["human_confirmation_required"] is True
    assert summary["counts_as_human_labels"] is False
    assert summary["measurement_validated_allowed"] is False
    assert summary["human_labels_present"] is False
    assert summary["kappa_present"] is False
    assert "human annotation" in summary["next_required_steps"]
    assert not (Path(first_outputs["llm_prelabels_jsonl"]).parent / "human_labels.jsonl").exists()


def test_live_mode_fails_closed_without_prelabel_env(workspace_tmp_dir):
    manifest = {
        "prelabel_run_id": "prelabel-live",
        "mode": "live_operator_approved",
        "operator_approval": True,
        "judge_model_alias": "deepseek_v4_flash",
        "judge_model_endpoint": "https://example.invalid/v1/chat",
        "judge_model_name": "fixed-operator-model",
        "input_artifact_root": str(workspace_tmp_dir),
        "output_root": str(workspace_tmp_dir / "live"),
        "max_items": 1,
        "budget_cap": "operator-budget",
    }
    called = False

    def fake_call(prompt_payload):
        nonlocal called
        called = True
        return _valid_prelabel()

    with pytest.raises(PrelabelGateError):
        build_llm_assisted_prelabels(
            workspace_tmp_dir / "live",
            manifest=manifest,
            input_artifact_root=workspace_tmp_dir,
            case_artifacts=[_case_artifact()],
            model_call_fn=fake_call,
        )

    assert called is False


def test_live_mode_fails_closed_without_operator_approval(monkeypatch, workspace_tmp_dir):
    monkeypatch.setenv("CPS_ALLOW_LLM_PRELABEL", "1")
    manifest_path = workspace_tmp_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "prelabel_run_id": "prelabel-live",
                "mode": "live_operator_approved",
                "operator_approval": False,
                "judge_model_alias": "deepseek_v4_flash",
                "judge_model_endpoint": "https://example.invalid/v1/chat",
                "judge_model_name": "fixed-operator-model",
                "input_artifact_root": str(workspace_tmp_dir),
                "output_root": str(workspace_tmp_dir / "live"),
                "max_items": 1,
                "budget_cap": "operator-budget",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    with pytest.raises(PrelabelGateError):
        build_llm_assisted_prelabels(
            workspace_tmp_dir / "live",
            manifest_path=manifest_path,
            input_artifact_root=workspace_tmp_dir,
            case_artifacts=[_case_artifact()],
            model_call_fn=lambda _: _valid_prelabel(),
        )


def test_live_mode_fails_closed_with_placeholder_endpoint(monkeypatch, workspace_tmp_dir):
    monkeypatch.setenv("CPS_ALLOW_LLM_PRELABEL", "1")
    manifest_path = workspace_tmp_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "prelabel_run_id": "prelabel-live",
                "mode": "live_operator_approved",
                "operator_approval": True,
                "judge_model_alias": "deepseek_v4_flash",
                "judge_model_endpoint": "<operator_filled_deepseek_v4_flash_endpoint>",
                "judge_model_name": "fixed-operator-model",
                "input_artifact_root": str(workspace_tmp_dir),
                "output_root": str(workspace_tmp_dir / "live"),
                "max_items": 1,
                "budget_cap": "operator-budget",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    with pytest.raises(PrelabelGateError):
        build_llm_assisted_prelabels(
            workspace_tmp_dir / "live",
            manifest_path=manifest_path,
            input_artifact_root=workspace_tmp_dir,
            case_artifacts=[_case_artifact()],
            model_call_fn=lambda _: _valid_prelabel(),
        )


def test_no_external_sdk_import_is_required():
    forbidden = {"openai", "anthropic", "requests", "httpx", "numpy", "pandas", "sklearn"}

    assert forbidden.isdisjoint(set(sys.modules))
