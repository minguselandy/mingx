import json
import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

from cps.runtime.cohort import run_phase1_cohort
from tests.helpers_phase1 import complete_annotation_labels


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.live_api
def test_phase1_live_cohort_runner_against_dashscope(workspace_tmp_dir):
    if os.environ.get("PHASE1_ENABLE_LIVE_TESTS") != "1":
        pytest.skip("set PHASE1_ENABLE_LIVE_TESTS=1 to run live DashScope integration tests")

    env_path = ROOT / ".env"
    if not env_path.exists():
        pytest.skip("repo .env is required for live DashScope integration tests")

    env_values = {key: str(value) for key, value in dotenv_values(env_path).items() if value is not None}
    api_key = env_values.get("DASHSCOPE_API_KEY")
    base_url = env_values.get("DASHSCOPE_BASE_URL")
    if not api_key or not base_url:
        pytest.skip("repo .env must include DASHSCOPE_API_KEY and DASHSCOPE_BASE_URL")

    isolated_env_path = workspace_tmp_dir / ".env"
    isolated_env_path.write_text(
        "\n".join(
            [
                f"DASHSCOPE_API_KEY={api_key}",
                f"DASHSCOPE_BASE_URL={base_url}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    question_id = "3hop1__222979_40769_64047"
    cohort_plan_path = workspace_tmp_dir / "live_cohort_plan.json"
    cohort_plan_path.write_text(
        json.dumps(
            {
                "experiment_id": "musique_gate1_phase1_v1",
                "protocol_version": "phase1.v1",
                "phase1_config_path": "./phase1.yaml",
                "manifest_path": "./artifacts/phase0/sample_manifest_v1.json",
                "hash_path": "./artifacts/phase0/content_hashes.json",
                "calibration_manifest_path": str((workspace_tmp_dir / "calibration_manifest.json").as_posix()),
                "backend": "live",
                "question_paragraph_limit": 5,
                "scoring": {
                    "k_lcb": 5,
                    "lcb_quantile": 0.1,
                },
                "calibration": {
                    "per_hop_count": 1,
                },
                "small_full_n": {
                    "questions": [question_id],
                },
                "frontier_calibration": {
                    "questions": [question_id],
                },
                "storage": {
                    "measurement_dir": str((workspace_tmp_dir / "measurements").as_posix()),
                    "export_dir": str((workspace_tmp_dir / "exports").as_posix()),
                    "checkpoint_dir": str((workspace_tmp_dir / "checkpoints").as_posix()),
                    "cache_dir": str((workspace_tmp_dir / "cache").as_posix()),
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    first_report = run_phase1_cohort(
        backend_name="live",
        cohort_plan_path=cohort_plan_path,
        env_path=isolated_env_path,
    )
    assert first_report["status"] == "awaiting_annotation"
    assert first_report["summary"]["measurement_status"] == "pilot_only"
    complete_annotation_labels(first_report["annotation_manifest_path"])

    report = run_phase1_cohort(
        backend_name="live",
        cohort_plan_path=cohort_plan_path,
        env_path=isolated_env_path,
    )

    assert report["status"] == "green"
    assert report["summary"]["pipeline_status"] == "pipeline_validated"
    assert report["summary"]["measurement_status"] == "pilot_only"
    assert report["summary"]["annotation_mode"] == "synthetic_passthrough"
    assert report["summary"]["model_roles"]["small"]["planned"] == 1
    assert report["summary"]["model_roles"]["small"]["completed"] == 1
    assert report["summary"]["model_roles"]["frontier"]["planned"] == 1
    assert report["summary"]["model_roles"]["frontier"]["completed"] == 1
    assert Path(report["run_summary_path"]).exists()
    assert Path(report["checkpoint_path"]).exists()
    assert Path(report["calibration_manifest_path"]).exists()
    assert Path(workspace_tmp_dir / "measurements" / "questions" / "small" / f"{question_id}.json").exists()
    assert Path(workspace_tmp_dir / "measurements" / "questions" / "frontier" / f"{question_id}.json").exists()
    assert Path(
        workspace_tmp_dir / "exports" / "small" / "questions" / question_id / "export_manifest.json"
    ).exists()
    assert Path(
        workspace_tmp_dir / "exports" / "frontier" / "questions" / question_id / "export_manifest.json"
    ).exists()
    assert list((workspace_tmp_dir / "cache" / "requests" / "small").glob("*.json"))
    assert list((workspace_tmp_dir / "cache" / "parsed" / "small").glob("*.json"))
    assert list((workspace_tmp_dir / "cache" / "requests" / "frontier").glob("*.json"))
    assert list((workspace_tmp_dir / "cache" / "parsed" / "frontier").glob("*.json"))

    events_text = Path(report["events_path"]).read_text(encoding="utf-8")
    assert "dashscope_openai_chat" in events_text
    assert api_key not in events_text
    assert "masked_api_key" not in events_text
