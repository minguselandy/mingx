import json
import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

from phase1.smoke import run_phase1_smoke


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.live_api
def test_phase1_live_smoke_against_dashscope(workspace_tmp_dir):
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

    run_plan_path = workspace_tmp_dir / "live_run_plan.json"
    run_plan_path.write_text(
        json.dumps(
            {
                "experiment_id": "musique_gate1_phase1_v1",
                "protocol_version": "phase1.v1",
                "manifest_path": "./artifacts/phase0/sample_manifest_v1.json",
                "hash_path": "./artifacts/phase0/content_hashes.json",
                "phase1_config_path": "./phase1.yaml",
                "smoke_question_id": "2hop__256778_131879",
                "smoke_paragraph_limit": 5,
                "scoring": {
                    "model_role": "small",
                    "k_lcb": 5,
                    "lcb_quantile": 0.1,
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

    report = run_phase1_smoke(
        backend_name="live",
        run_plan_path=run_plan_path,
        env_path=isolated_env_path,
    )

    assert report["status"] == "green"
    events_text = Path(report["events_path"]).read_text(encoding="utf-8")
    assert "dashscope_openai_chat" in events_text
    assert api_key not in events_text
    assert "masked_api_key" not in events_text
    assert list((workspace_tmp_dir / "cache" / "requests" / "small").glob("*.json"))
    assert list((workspace_tmp_dir / "cache" / "parsed" / "small").glob("*.json"))
