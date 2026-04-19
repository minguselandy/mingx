from pathlib import Path

from phase1.config import load_phase1_context
from phase1.secrets import extract_api_key_from_csv, mask_secret


CSV_PATH = Path(r"C:\Users\Mingx\Documents\mx-codex\默认业务空间-apiKey-4648916.csv")


def test_extract_api_key_from_nonstandard_csv():
    api_key = extract_api_key_from_csv(CSV_PATH)

    assert api_key.startswith("sk-")
    assert len(api_key) > 10
    assert mask_secret(api_key).startswith("sk-f")
    assert mask_secret(api_key) != api_key


def test_load_phase1_context_prefers_environment_over_env_file(workspace_tmp_dir, monkeypatch):
    env_path = workspace_tmp_dir / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DASHSCOPE_API_KEY=sk-from-env-file",
                "DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-from-process-env")

    context = load_phase1_context(
        phase1_config_path=Path("phase1.yaml"),
        run_plan_path=Path("configs/runs/smoke.json"),
        env_path=env_path,
    )

    assert context.provider.name == "dashscope"
    assert context.provider.base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert context.provider.api_key == "sk-from-process-env"
    assert context.models["frontier"].model == "qwen3-32b"
    assert context.models["small"].model == "qwen3-14b"
    assert context.scoring.permutation_count == 5


def test_load_phase1_context_prefers_run_plan_storage_over_env_defaults(workspace_tmp_dir):
    env_path = workspace_tmp_dir / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DASHSCOPE_API_KEY=sk-from-env-file",
                "DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1",
                "PHASE1_MEASUREMENT_DIR=./artifacts/phase1/measurements",
                "PHASE1_EXPORT_DIR=./artifacts/phase1/exports",
                "PHASE1_CHECKPOINT_DIR=./artifacts/phase1/checkpoints",
                "PHASE1_CACHE_DIR=./artifacts/phase1/cache",
            ]
        ),
        encoding="utf-8",
    )
    run_plan_path = workspace_tmp_dir / "run_plan.json"
    run_plan_path.write_text(
        """
{
  "experiment_id": "musique_gate1_phase1_v1",
  "protocol_version": "phase1.v1",
  "manifest_path": "./artifacts/phase0/sample_manifest_v1.json",
  "hash_path": "./artifacts/phase0/content_hashes.json",
  "phase1_config_path": "./phase1.yaml",
  "smoke_question_id": "2hop__256778_131879",
  "scoring": {
    "model_role": "small",
    "k_lcb": 5,
    "lcb_quantile": 0.1
  },
  "storage": {
    "measurement_dir": "./artifacts/phase1/live_mini_batch/measurements",
    "export_dir": "./artifacts/phase1/live_mini_batch/exports",
    "checkpoint_dir": "./artifacts/phase1/live_mini_batch/checkpoints",
    "cache_dir": "./artifacts/phase1/live_mini_batch/cache"
  }
}
        """.strip(),
        encoding="utf-8",
    )

    context = load_phase1_context(
        phase1_config_path=Path("phase1.yaml"),
        run_plan_path=run_plan_path,
        env_path=env_path,
    )

    assert context.storage.measurement_dir.name == "measurements"
    assert context.storage.measurement_dir.parent.name == "live_mini_batch"
    assert context.storage.export_dir.parent.name == "live_mini_batch"
    assert context.storage.checkpoint_dir.parent.name == "live_mini_batch"
    assert context.storage.cache_dir.parent.name == "live_mini_batch"
