import json
from pathlib import Path

from cps.runtime.cohort import run_phase1_cohort
from cps.runtime.phase1_smoke import run_phase1_smoke
from tests.helpers_phase1 import complete_annotation_labels


def _write_env(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "DASHSCOPE_API_KEY=sk-test-key",
                "DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1",
            ]
        ),
        encoding="utf-8",
    )


def test_cps_runtime_phase1_smoke_runs_with_mock_backend(workspace_tmp_dir):
    env_path = workspace_tmp_dir / ".env"
    _write_env(env_path)

    run_plan_path = workspace_tmp_dir / "smoke.json"
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

    assert report["status"] == "green"
    assert Path(report["events_path"]).exists()
    assert Path(report["exports"]["delta_loo_jsonl"]).exists()


def test_cps_runtime_cohort_runs_with_mock_backend(workspace_tmp_dir):
    env_path = workspace_tmp_dir / ".env"
    _write_env(env_path)

    measurement_dir = workspace_tmp_dir / "measurements"
    export_dir = workspace_tmp_dir / "exports"
    checkpoint_dir = workspace_tmp_dir / "checkpoints"
    cache_dir = workspace_tmp_dir / "cache"
    calibration_manifest_path = workspace_tmp_dir / "calibration_manifest.json"
    plan_path = workspace_tmp_dir / "cohort.json"
    plan_path.write_text(
        json.dumps(
            {
                "experiment_id": "musique_gate1_phase1_v1",
                "protocol_version": "phase1.v1",
                "phase1_config_path": "./phase1.yaml",
                "manifest_path": "./artifacts/phase0/sample_manifest_v1.json",
                "hash_path": "./artifacts/phase0/content_hashes.json",
                "calibration_manifest_path": str(calibration_manifest_path.as_posix()),
                "backend": "mock",
                "scoring": {
                    "k_lcb": 5,
                    "lcb_quantile": 0.1,
                },
                "calibration": {"per_hop_count": 1},
                "question_paragraph_limit": 5,
                "small_full_n": {"questions": "calibration_manifest"},
                "frontier_calibration": {"questions": "calibration_manifest"},
                "storage": {
                    "measurement_dir": str(measurement_dir.as_posix()),
                    "export_dir": str(export_dir.as_posix()),
                    "checkpoint_dir": str(checkpoint_dir.as_posix()),
                    "cache_dir": str(cache_dir.as_posix()),
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    first_report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )
    assert first_report["status"] == "awaiting_annotation"
    complete_annotation_labels(first_report["annotation_manifest_path"])

    report = run_phase1_cohort(
        backend_name="mock",
        cohort_plan_path=plan_path,
        env_path=env_path,
    )

    assert report["status"] == "green"
    assert report["summary"]["pipeline_status"] == "pipeline_validated"
    assert report["summary"]["measurement_status"] == "pilot_only"
    assert report["summary"]["scope_mode"] == "pilot_reduced_scope"
    assert report["summary"]["annotation_mode"] == "synthetic_passthrough"
    assert report["summary"]["model_roles"]["small"]["completed"] == 3
    assert report["summary"]["model_roles"]["frontier"]["completed"] == 3
    assert Path(report["annotation_readme_path"]).exists()
    assert Path(report["summary"]["annotation"]["annotation_readme_path"]).exists()
