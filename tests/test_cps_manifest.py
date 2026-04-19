from pathlib import Path

from cps.data.manifest import load_manifest, validate_manifest


def test_cps_manifest_loader_reads_and_validates_phase0_fixture():
    bundle = load_manifest(Path("artifacts/phase0/sample_manifest_v1.json"))
    report = validate_manifest(
        bundle,
        hashes_path=Path("artifacts/phase0/content_hashes.json"),
        config_path=Path("phase0.yaml"),
    )

    assert bundle.schema_version == "phase1.v1"
    assert len(bundle.sample) == 90
    assert report["ok"] is True
    assert report["by_hop_depth"] == {"2hop": 30, "3hop": 30, "4hop": 30}
