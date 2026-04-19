import json
from collections import Counter
from pathlib import Path

from cps.data.manifest import load_manifest
from cps.runtime.calibration import (
    SELECTION_ALGORITHM_VERSION,
    build_calibration_manifest,
)


FIXTURE_MANIFEST = Path("artifacts/phase0/sample_manifest_v1.json")


def test_calibration_manifest_is_stable_under_manifest_reordering(workspace_tmp_dir):
    original_payload = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    reordered_payload = dict(original_payload)
    reordered_payload["sample"] = list(reversed(original_payload["sample"]))

    first_manifest_path = workspace_tmp_dir / "manifest-a.json"
    second_manifest_path = workspace_tmp_dir / "manifest-b.json"
    first_manifest_path.write_text(
        json.dumps(original_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    second_manifest_path.write_text(
        json.dumps(reordered_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    first_output = workspace_tmp_dir / "calibration-a.json"
    second_output = workspace_tmp_dir / "calibration-b.json"
    first = build_calibration_manifest(
        load_manifest(first_manifest_path),
        first_output,
        seed=20260418,
        per_hop_count=10,
    )
    second = build_calibration_manifest(
        load_manifest(second_manifest_path),
        second_output,
        seed=20260418,
        per_hop_count=10,
    )

    assert first_output.exists()
    assert second_output.exists()
    assert first["selection_algorithm_version"] == SELECTION_ALGORITHM_VERSION
    assert first["source_manifest_path"] == str(first_manifest_path.resolve())
    assert "source_manifest_hash" in first
    assert "source_manifest_fingerprint" in first
    assert [
        (entry["hop_depth"], entry["question_id"], entry["selection_score"])
        for entry in first["selected_questions"]
    ] == [
        (entry["hop_depth"], entry["question_id"], entry["selection_score"])
        for entry in second["selected_questions"]
    ]
    assert Counter(entry["hop_depth"] for entry in first["selected_questions"]) == {
        "2hop": 10,
        "3hop": 10,
        "4hop": 10,
    }


def test_calibration_manifest_supports_excluded_question_ids_and_same_hop_replacement(workspace_tmp_dir):
    bundle = load_manifest(FIXTURE_MANIFEST)
    output_path = workspace_tmp_dir / "calibration-excluded.json"

    calibration = build_calibration_manifest(
        bundle,
        output_path,
        seed=20260418,
        per_hop_count=2,
        exclude_question_ids=("2hop__86458_20273",),
    )

    by_hop = {
        hop_depth: [entry["question_id"] for entry in calibration["selected_questions"] if entry["hop_depth"] == hop_depth]
        for hop_depth in ("2hop", "3hop", "4hop")
    }

    assert output_path.exists()
    assert calibration["excluded_question_ids"] == ["2hop__86458_20273"]
    assert calibration["replacement_policy"] == "same_hop_next_rank_on_resume_v1"
    assert by_hop["2hop"] == ["2hop__132929_684936", "2hop__32254_84601"]
    assert by_hop["3hop"] == ["3hop1__222979_40769_64047", "3hop1__409517_547811_80702"]
    assert by_hop["4hop"] == ["4hop1__76111_624859_355213_203322", "4hop3__373866_5189_38229_86687"]


def test_live_calibration_p3_plan_is_pinned_to_expected_selection_and_storage(workspace_tmp_dir):
    plan_path = Path("configs/runs/live-calibration-p3.json")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    calibration_output = workspace_tmp_dir / "live-calibration-p3.json"
    calibration = build_calibration_manifest(
        load_manifest(FIXTURE_MANIFEST),
        calibration_output,
        seed=20260418,
        per_hop_count=3,
    )
    by_hop = {
        hop_depth: [
            entry["question_id"]
            for entry in calibration["selected_questions"]
            if entry["hop_depth"] == hop_depth
        ]
        for hop_depth in ("2hop", "3hop", "4hop")
    }

    assert plan["backend"] == "live"
    assert plan["question_paragraph_limit"] == 5
    assert plan["calibration"]["per_hop_count"] == 3
    assert plan["small_full_n"]["questions"] == "calibration_manifest"
    assert plan["frontier_calibration"]["questions"] == "calibration_manifest"
    assert plan["calibration_manifest_path"] == "./artifacts/phase1/live_calibration_p3/calibration_manifest.json"
    assert plan["storage"] == {
        "cache_dir": "./artifacts/phase1/live_calibration_p3/cache",
        "measurement_dir": "./artifacts/phase1/live_calibration_p3/measurements",
        "checkpoint_dir": "./artifacts/phase1/live_calibration_p3/checkpoints",
        "export_dir": "./artifacts/phase1/live_calibration_p3/exports",
    }
    assert by_hop["2hop"] == [
        "2hop__86458_20273",
        "2hop__132929_684936",
        "2hop__32254_84601",
    ]
    assert by_hop["3hop"] == [
        "3hop1__222979_40769_64047",
        "3hop1__409517_547811_80702",
        "3hop1__773623_87694_124169",
    ]
    assert by_hop["4hop"] == [
        "4hop1__76111_624859_355213_203322",
        "4hop3__373866_5189_38229_86687",
        "4hop1__105401_17130_70784_61381",
    ]


def test_canonical_run_configs_exist_under_configs_runs():
    expected = {
        "smoke.json",
        "cohort.json",
        "live-pilot.json",
        "live-mini-batch.json",
        "live-calibration-p2.json",
        "live-calibration-p3.json",
    }
    actual = {path.name for path in Path("configs/runs").glob("*.json")}

    assert expected.issubset(actual)
