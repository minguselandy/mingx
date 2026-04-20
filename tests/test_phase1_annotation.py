from __future__ import annotations

import csv
import json
from pathlib import Path

from cps.analysis.exports import write_json, write_jsonl
from cps.data.manifest import load_manifest
from cps.runtime.annotation import materialize_annotation_artifacts


def _write_bridge_exports(
    export_dir: Path,
    rows: list[dict],
    *,
    flagged_ids: set[tuple[str, int]],
) -> tuple[Path, Path, Path]:
    bridge_path = write_json(
        export_dir / "bridge_diagnostics.json",
        {
            "status": "computed",
            "bridge_form": "linear_ols",
            "per_hop": {
                hop: {"diagnostics": {"normality_test": "shapiro_wilk"}}
                for hop in {"2hop", "3hop", "4hop"}
            },
        },
    )
    bridged_path = write_jsonl(export_dir / "bridged_delta_loo.jsonl", rows)
    per_hop: dict[str, dict] = {}
    for row in rows:
        hop_payload = per_hop.setdefault(
            row["hop_depth"],
            {
                "counts": {"total": 0, "flagged": 0, "high": 0, "low": 0, "buffer": 0},
                "flagged_instances": [],
            },
        )
        hop_payload["counts"]["total"] += 1
        hop_payload["counts"][row["automated_label"].lower()] += 1
        key = (row["question_id"], row["paragraph_id"])
        if key in flagged_ids:
            hop_payload["counts"]["flagged"] += 1
            hop_payload["flagged_instances"].append(
                {
                    "question_id": row["question_id"],
                    "paragraph_id": row["paragraph_id"],
                    "delta_loo_frontier_equivalent": row["delta_loo_frontier_equivalent"],
                    "automated_label": row["automated_label"],
                }
            )
    tolerance_path = write_json(
        export_dir / "tolerance_band.json",
        {
            "status": "computed",
            "band_width_sigma_multiplier": 0.5,
            "per_hop": per_hop,
        },
    )
    return bridge_path, bridged_path, tolerance_path


def test_materialize_annotation_artifacts_is_order_insensitive_and_writes_templates(workspace_tmp_dir):
    bundle = load_manifest("artifacts/phase0/sample_manifest_v1.json")
    question_lookup = {question.question_id: question for question in bundle.sample}
    selected_questions = [
        "2hop__256778_131879",
        "3hop1__222979_40769_64047",
        "4hop1__76111_624859_355213_203322",
    ]

    rows = [
        {
            "question_id": "2hop__256778_131879",
            "hop_depth": "2hop",
            "paragraph_id": 0,
            "delta_loo_frontier_equivalent": 0.9,
            "automated_label": "HIGH",
            "tolerance_flagged": True,
        },
        {
            "question_id": "2hop__256778_131879",
            "hop_depth": "2hop",
            "paragraph_id": 1,
            "delta_loo_frontier_equivalent": -0.3,
            "automated_label": "LOW",
            "tolerance_flagged": False,
        },
        {
            "question_id": "3hop1__222979_40769_64047",
            "hop_depth": "3hop",
            "paragraph_id": 0,
            "delta_loo_frontier_equivalent": 0.5,
            "automated_label": "BUFFER",
            "tolerance_flagged": True,
        },
        {
            "question_id": "3hop1__222979_40769_64047",
            "hop_depth": "3hop",
            "paragraph_id": 1,
            "delta_loo_frontier_equivalent": 0.8,
            "automated_label": "HIGH",
            "tolerance_flagged": False,
        },
        {
            "question_id": "4hop1__76111_624859_355213_203322",
            "hop_depth": "4hop",
            "paragraph_id": 0,
            "delta_loo_frontier_equivalent": -0.2,
            "automated_label": "LOW",
            "tolerance_flagged": True,
        },
        {
            "question_id": "4hop1__76111_624859_355213_203322",
            "hop_depth": "4hop",
            "paragraph_id": 1,
            "delta_loo_frontier_equivalent": 0.2,
            "automated_label": "BUFFER",
            "tolerance_flagged": False,
        },
    ]
    flagged_ids = {
        ("2hop__256778_131879", 0),
        ("3hop1__222979_40769_64047", 0),
        ("4hop1__76111_624859_355213_203322", 0),
    }

    export_dir_a = workspace_tmp_dir / "exports-a"
    export_dir_b = workspace_tmp_dir / "exports-b"
    bridge_a, bridged_a, tolerance_a = _write_bridge_exports(export_dir_a, rows, flagged_ids=flagged_ids)
    bridge_b, bridged_b, tolerance_b = _write_bridge_exports(
        export_dir_b,
        list(reversed(rows)),
        flagged_ids=flagged_ids,
    )

    report_a = materialize_annotation_artifacts(
        bundle=bundle,
        export_dir=export_dir_a,
        bridge_diagnostics_path=bridge_a,
        bridged_delta_loo_jsonl_path=bridged_a,
        tolerance_band_path=tolerance_a,
        seed=20260418,
    )
    report_b = materialize_annotation_artifacts(
        bundle=bundle,
        export_dir=export_dir_b,
        bridge_diagnostics_path=bridge_b,
        bridged_delta_loo_jsonl_path=bridged_b,
        tolerance_band_path=tolerance_b,
        seed=20260418,
    )

    queue_a = list(csv.DictReader((export_dir_a / "annotations" / "annotation_queue.csv").open("r", encoding="utf-8")))
    queue_b = list(csv.DictReader((export_dir_b / "annotations" / "annotation_queue.csv").open("r", encoding="utf-8")))

    assert report_a["status"] == "materialized"
    assert report_a["flagged_count"] == 3
    assert report_a["face_validity_count"] == 0
    assert report_a["queue_count"] == 3
    assert [row["annotation_item_id"] for row in queue_a] == [row["annotation_item_id"] for row in queue_b]

    manifest = json.loads((export_dir_a / "annotations" / "annotation_manifest.json").read_text(encoding="utf-8"))
    assert manifest["selection_algorithm_version"] == "face_validity_sample_v1"
    assert Path(manifest["required_label_paths"]["primary_a"]).exists()
    assert Path(manifest["required_label_paths"]["primary_b"]).exists()
    assert Path(manifest["required_label_paths"]["expert"]).exists()

    items = [
        json.loads(line)
        for line in (export_dir_a / "annotations" / "annotation_items.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(items) == 3
    assert items[0]["question_text"] == question_lookup[items[0]["question_id"]].question_text
    assert items[0]["answer_text"] == question_lookup[items[0]["question_id"]].answer_text
    assert items[0]["target_paragraph"]["paragraph_id"] in {0, 1}

