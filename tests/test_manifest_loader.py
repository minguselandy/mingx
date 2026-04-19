from pathlib import Path

from phase0.manifest import load_manifest, validate_manifest


FIXTURES_DIR = Path(__file__).resolve().parents[3] / "files"


def test_load_manifest_normalizes_sample_manifest_fields():
    bundle = load_manifest(FIXTURES_DIR / "sample_manifest_v1.json")

    assert bundle.schema_version == "phase1.v1"
    assert bundle.source_dataset["repo"] == "dgslibisey/MuSiQue"
    assert bundle.source_dataset["split"] == "validation"
    assert len(bundle.sample) == 90

    question = bundle.sample[0]
    paragraph = question.paragraphs[0]

    assert question.question_id
    assert question.answerable is True
    assert question.answer_aliases
    assert paragraph.paragraph_id == 0
    assert paragraph.title
    assert paragraph.text


def test_validate_manifest_enforces_gate1_constraints():
    bundle = load_manifest(FIXTURES_DIR / "sample_manifest_v1.json")

    report = validate_manifest(
        bundle,
        hashes_path=FIXTURES_DIR / "content_hashes.json",
        config_path=Path("phase0.yaml"),
    )

    assert report["ok"] is True
    assert report["total_sampled"] == 90
    assert report["by_hop_depth"] == {"2hop": 30, "3hop": 30, "4hop": 30}
    assert report["pool_size_range"] == {"min": 18, "max": 20}
    assert report["dataset_hash"] == "1fe3df848a525f62933498b158dd58fe87bb3a21afb30940a2c4cfaa78a81225"
