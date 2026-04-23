from __future__ import annotations

from cps.analysis.contamination import CONTAMINATION_THRESHOLD_LOGP
from cps.analysis.reprobe import run_question_only_reprobe


def test_question_only_reprobe_returns_keep_candidate_when_threshold_passes(workspace_tmp_dir):
    env_path = workspace_tmp_dir / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DASHSCOPE_API_KEY=sk-test-key",
                "DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1",
            ]
        ),
        encoding="utf-8",
    )

    payload = run_question_only_reprobe(
        question_id="reprobe-test",
        question_text="Who won?",
        answer_text="Alice",
        backend_name="mock",
        model_role="frontier",
        env_path=env_path,
    )

    assert payload["status"] == "green"
    assert payload["mode"] == "question_only_reprobe"
    assert payload["model_role"] == "frontier"
    assert payload["model_id"] == "qwen3.6-plus"
    assert payload["baseline_logp"] <= CONTAMINATION_THRESHOLD_LOGP
    assert payload["passes_contamination_threshold"] is True
    assert payload["recommended_disposition"] == "keep_candidate_for_human_review"


def test_question_only_reprobe_returns_drop_and_replace_when_backend_errors(workspace_tmp_dir):
    env_path = workspace_tmp_dir / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DASHSCOPE_API_KEY=sk-test-key",
                "DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1",
            ]
        ),
        encoding="utf-8",
    )

    try:
        run_question_only_reprobe(
            question_id="reprobe-test",
            question_text="Who won?",
            answer_text="Alice",
            backend_name="invalid",
            model_role="frontier",
            env_path=env_path,
        )
    except ValueError as exc:
        assert "Unsupported backend" in str(exc)
    else:
        raise AssertionError("expected invalid backend to raise")
