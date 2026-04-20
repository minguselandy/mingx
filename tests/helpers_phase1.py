from __future__ import annotations

import csv
import json
from pathlib import Path

from cps.runtime.annotation import SYNTHETIC_JUSTIFICATION_MARKER


def complete_annotation_labels(annotation_manifest_path: str | Path) -> dict:
    manifest_path = Path(annotation_manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    label_paths = manifest["required_label_paths"]

    for annotator_id, raw_path in label_paths.items():
        path = Path(raw_path)
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            row["label"] = row["automated_label"]
            row["justification"] = SYNTHETIC_JUSTIFICATION_MARKER
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
            if rows:
                writer.writeheader()
                writer.writerows(rows)
            else:
                writer.writeheader()

    return manifest
