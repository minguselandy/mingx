from pathlib import Path

from phase1.smoke import run_phase1_smoke


def test_phase1_mock_smoke_produces_measurements_and_exports(workspace_tmp_dir):
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
  "smoke_paragraph_limit": 5,
  "scoring": {
    "model_role": "small",
    "k_lcb": 5,
    "lcb_quantile": 0.1
  },
  "storage": {
    "measurement_dir": "REPLACE_MEASUREMENTS",
    "export_dir": "REPLACE_EXPORTS",
    "checkpoint_dir": "REPLACE_CHECKPOINTS",
    "cache_dir": "REPLACE_CACHE"
  }
}
        """.strip()
        .replace("REPLACE_MEASUREMENTS", str((workspace_tmp_dir / "measurements").as_posix()))
        .replace("REPLACE_EXPORTS", str((workspace_tmp_dir / "exports").as_posix()))
        .replace("REPLACE_CHECKPOINTS", str((workspace_tmp_dir / "checkpoints").as_posix()))
        .replace("REPLACE_CACHE", str((workspace_tmp_dir / "cache").as_posix())),
        encoding="utf-8",
    )

    report = run_phase1_smoke(
        backend_name="mock",
        run_plan_path=run_plan_path,
        env_path=env_path,
    )

    question_export_dir = (
        workspace_tmp_dir / "exports" / "small" / "questions" / report["question_id"]
    )

    assert report["status"] == "green"
    assert Path(report["events_path"]).exists()
    assert Path(report["snapshot_path"]).exists()
    assert Path(report["checkpoint_path"]).exists()
    assert Path(report["exports"]["delta_loo_jsonl"]).exists()
    assert Path(report["exports"]["question_export_manifest"]).exists()
    assert Path(report["exports"]["retrieval_dry_run"]).exists()
    assert Path(report["exports"]["bridge_diagnostics"]).exists()
    assert Path(report["snapshot_path"]) == (
        workspace_tmp_dir / "measurements" / "questions" / "small" / f"{report['question_id']}.json"
    )
    assert Path(report["exports"]["delta_loo_jsonl"]) == (question_export_dir / "delta_loo_lcb.jsonl")
    events_text = Path(report["events_path"]).read_text(encoding="utf-8")
    assert "sk-test-key" not in events_text
