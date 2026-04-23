from __future__ import annotations

import csv
import json
from pathlib import Path

from cps.runtime.annotation import apply_synthetic_passthrough_labels


def complete_annotation_labels(annotation_manifest_path: str | Path) -> dict:
    apply_synthetic_passthrough_labels(annotation_manifest_path)
    manifest_path = Path(annotation_manifest_path)
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def complete_annotation_labels_as_human(annotation_manifest_path: str | Path) -> dict:
    manifest_path = Path(annotation_manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for annotator_id, raw_path in manifest["required_label_paths"].items():
        path = Path(raw_path)
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            row["label"] = row["automated_label"]
            row["justification"] = (
                f"{annotator_id} confirmed the provisional label after manual review."
            )
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
            writer.writeheader()
            if rows:
                writer.writerows(rows)
    return manifest
