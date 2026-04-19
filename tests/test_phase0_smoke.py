from pathlib import Path

from phase0.smoke import run_phase0_smoke


FIXTURES_DIR = Path(__file__).resolve().parents[3] / "files"


def test_phase0_smoke_runs_end_to_end_with_fixtures(workspace_tmp_dir):
    store_dir = workspace_tmp_dir / "artifacts" / "phase0" / "measurements"

    report = run_phase0_smoke(
        manifest_path=FIXTURES_DIR / "sample_manifest_v1.json",
        hash_path=FIXTURES_DIR / "content_hashes.json",
        store_dir=store_dir,
    )

    assert report["status"] == "green"
    assert report["validation"]["ok"] is True
    assert report["events_written"] >= 4
    assert Path(report["events_path"]).exists()
    assert Path(report["snapshot_path"]).exists()
