from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from cps.analysis.exports import write_csv, write_json, write_jsonl
from cps.data.manifest import ManifestBundle
from cps.store.measurement import append_event, iter_events


FACE_VALIDITY_ALGORITHM_VERSION = "face_validity_sample_v1"
LABEL_FILE_KEYS = ("primary_a", "primary_b", "expert")
LABEL_COLUMNS = [
    "annotation_item_id",
    "question_id",
    "paragraph_id",
    "hop_depth",
    "source",
    "automated_label",
    "label",
    "justification",
]


def _annotation_root(export_dir: str | Path) -> Path:
    return Path(export_dir) / "annotations"


def _stable_digest(*parts: object) -> str:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load_bridged_rows(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def _largest_remainder_allocations(bucket_sizes: dict[tuple[str, str], int], total: int) -> dict[tuple[str, str], int]:
    if total <= 0 or not bucket_sizes:
        return {key: 0 for key in bucket_sizes}
    denominator = sum(bucket_sizes.values())
    if denominator == 0:
        return {key: 0 for key in bucket_sizes}

    allocations: dict[tuple[str, str], int] = {}
    remainders: list[tuple[float, tuple[str, str]]] = []
    assigned = 0
    for key, size in bucket_sizes.items():
        exact = (total * size) / denominator
        floor_value = min(size, int(exact))
        allocations[key] = floor_value
        assigned += floor_value
        remainders.append((exact - floor_value, key))

    remaining = min(total - assigned, denominator - assigned)
    for _, key in sorted(remainders, key=lambda item: (-item[0], item[1]))[:remaining]:
        if allocations[key] < bucket_sizes[key]:
            allocations[key] += 1
    return allocations


def _build_face_validity_sample(rows: list[dict[str, Any]], *, seed: int) -> list[dict[str, Any]]:
    total = round(0.1 * len(rows))
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["hop_depth"]), str(row["automated_label"]))].append(row)
    bucket_sizes = {key: len(value) for key, value in grouped.items()}
    allocations = _largest_remainder_allocations(bucket_sizes, total)

    selected: list[dict[str, Any]] = []
    for key, bucket_rows in grouped.items():
        sample_size = allocations.get(key, 0)
        ranked = sorted(
            bucket_rows,
            key=lambda row: (
                _stable_digest(
                    FACE_VALIDITY_ALGORITHM_VERSION,
                    seed,
                    row["question_id"],
                    row["paragraph_id"],
                ),
                str(row["question_id"]),
                int(row["paragraph_id"]),
            ),
        )
        selected.extend(ranked[:sample_size])
    return sorted(selected, key=lambda row: (row["hop_depth"], row["question_id"], int(row["paragraph_id"])))


def _annotation_item(row: dict[str, Any]) -> dict[str, Any]:
    annotation_item_id = f"{row['question_id']}::{int(row['paragraph_id'])}"
    return {
        "annotation_item_id": annotation_item_id,
        "question_id": str(row["question_id"]),
        "paragraph_id": int(row["paragraph_id"]),
        "hop_depth": str(row["hop_depth"]),
        "source": str(row["source"]),
        "automated_label": str(row["automated_label"]),
        "requires_expert": True,
    }


def _label_template_rows(queue_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "annotation_item_id": row["annotation_item_id"],
            "question_id": row["question_id"],
            "paragraph_id": row["paragraph_id"],
            "hop_depth": row["hop_depth"],
            "source": row["source"],
            "automated_label": row["automated_label"],
            "label": "",
            "justification": "",
        }
        for row in queue_rows
    ]


def _read_label_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def materialize_annotation_artifacts(
    *,
    bundle: ManifestBundle,
    export_dir: str | Path,
    bridge_diagnostics_path: str | Path,
    bridged_delta_loo_jsonl_path: str | Path,
    tolerance_band_path: str | Path,
    seed: int,
) -> dict[str, Any]:
    annotation_root = _annotation_root(export_dir)
    labels_dir = annotation_root / "labels"
    labels_dir.mkdir(parents=True, exist_ok=True)

    question_lookup = {question.question_id: question for question in bundle.sample}
    bridged_rows = _load_bridged_rows(bridged_delta_loo_jsonl_path)
    flagged_rows = [
        {**row, "source": "tolerance_flagged"}
        for row in bridged_rows
        if bool(row.get("tolerance_flagged"))
    ]
    non_flagged_rows = [row for row in bridged_rows if not bool(row.get("tolerance_flagged"))]
    face_validity_rows = [
        {**row, "source": "face_validity_sample"}
        for row in _build_face_validity_sample(non_flagged_rows, seed=seed)
    ]
    queue_rows = [_annotation_item(row) for row in [*flagged_rows, *face_validity_rows]]
    queue_rows.sort(key=lambda row: (row["hop_depth"], row["question_id"], int(row["paragraph_id"])))

    source_paths = {
        "bridge_diagnostics": str(Path(bridge_diagnostics_path).resolve()),
        "bridged_delta_loo_jsonl": str(Path(bridged_delta_loo_jsonl_path).resolve()),
        "tolerance_band": str(Path(tolerance_band_path).resolve()),
    }
    label_paths = {key: str((labels_dir / f"{key}.csv").resolve()) for key in LABEL_FILE_KEYS}
    manifest_hash = _stable_digest(
        FACE_VALIDITY_ALGORITHM_VERSION,
        seed,
        source_paths["bridge_diagnostics"],
        source_paths["bridged_delta_loo_jsonl"],
        source_paths["tolerance_band"],
        *[row["annotation_item_id"] for row in queue_rows],
    )
    manifest_payload = {
        "status": "materialized",
        "seed": seed,
        "annotation_manifest_hash": manifest_hash,
        "selection_algorithm_version": FACE_VALIDITY_ALGORITHM_VERSION,
        "source_paths": source_paths,
        "counts": {
            "queue_count": len(queue_rows),
            "flagged_count": len(flagged_rows),
            "face_validity_count": len(face_validity_rows),
        },
        "required_label_paths": label_paths,
    }
    manifest_path = write_json(annotation_root / "annotation_manifest.json", manifest_payload)
    queue_path = write_csv(
        annotation_root / "annotation_queue.csv",
        queue_rows,
        [
            "annotation_item_id",
            "question_id",
            "paragraph_id",
            "hop_depth",
            "source",
            "automated_label",
            "requires_expert",
        ],
    )

    items_rows = []
    for row in queue_rows:
        question = question_lookup[row["question_id"]]
        target = next(
            paragraph for paragraph in question.paragraphs if paragraph.paragraph_id == int(row["paragraph_id"])
        )
        items_rows.append(
            {
                **row,
                "question_text": question.question_text,
                "answer_text": question.answer_text,
                "target_paragraph": {
                    "paragraph_id": target.paragraph_id,
                    "title": target.title,
                    "text": target.text,
                    "is_supporting": target.is_supporting,
                },
                "paragraphs": [
                    {
                        "paragraph_id": paragraph.paragraph_id,
                        "title": paragraph.title,
                        "text": paragraph.text,
                        "is_supporting": paragraph.is_supporting,
                    }
                    for paragraph in question.paragraphs
                ],
            }
        )
    items_path = write_jsonl(annotation_root / "annotation_items.jsonl", items_rows)

    template_rows = _label_template_rows(queue_rows)
    for label_key, label_path in label_paths.items():
        path = Path(label_path)
        if not path.exists():
            write_csv(path, template_rows, LABEL_COLUMNS)

    return {
        "status": "materialized",
        "annotation_manifest_hash": manifest_hash,
        "annotation_manifest_path": str(manifest_path),
        "annotation_queue_path": str(queue_path),
        "annotation_items_path": str(items_path),
        "label_paths": label_paths,
        "queue_count": len(queue_rows),
        "flagged_count": len(flagged_rows),
        "face_validity_count": len(face_validity_rows),
    }


def annotation_status_from_files(annotation_manifest_path: str | Path) -> dict[str, Any]:
    manifest = json.loads(Path(annotation_manifest_path).read_text(encoding="utf-8"))
    label_paths = {key: Path(value) for key, value in manifest["required_label_paths"].items()}
    completion: dict[str, Any] = {}
    complete = True

    for annotator_id, path in label_paths.items():
        rows = _read_label_rows(path)
        completed_rows = 0
        for row in rows:
            label_present = bool((row.get("label") or "").strip())
            justification_present = bool((row.get("justification") or "").strip())
            row_complete = label_present and (annotator_id != "expert" or justification_present)
            if row_complete:
                completed_rows += 1
            else:
                complete = False
        completion[annotator_id] = {
            "path": str(path),
            "total_rows": len(rows),
            "completed_rows": completed_rows,
        }

    return {
        "status": "ready_for_ingestion" if complete else "awaiting_labels",
        "annotation_manifest_hash": manifest["annotation_manifest_hash"],
        "completion": completion,
        "counts": manifest["counts"],
    }


def load_annotation_ledger_from_events(
    *,
    store_dir: str | Path,
    annotation_manifest_hash: str,
) -> dict[str, Any]:
    records: dict[str, dict[str, Any]] = {}
    ingested_by_annotator = {key: set() for key in LABEL_FILE_KEYS}
    kappa_events: list[dict[str, Any]] = []

    for event in iter_events(store_dir):
        payload = event.get("payload") or {}
        if payload.get("annotation_manifest_hash") != annotation_manifest_hash:
            continue
        event_type = event.get("event_type")
        if event_type == "kappa_materialized":
            kappa_events.append(event)
            continue
        if event_type not in {"annotation_label_ingested", "expert_arbitration_ingested"}:
            continue

        annotator_id = str(payload["annotator_id"])
        annotation_item_id = str(payload["annotation_item_id"])
        record = records.setdefault(
            annotation_item_id,
            {
                "annotation_item_id": annotation_item_id,
                "question_id": event.get("question_id"),
                "paragraph_id": int(event.get("paragraph_id")),
                "hop_depth": event.get("hop_depth"),
                "source": payload.get("source"),
                "automated_label": payload.get("automated_label"),
            },
        )
        record[f"{annotator_id}_label"] = payload.get("label")
        record[f"{annotator_id}_justification"] = payload.get("justification")
        ingested_by_annotator.setdefault(annotator_id, set()).add(annotation_item_id)

    return {
        "records": records,
        "ingested_by_annotator": {key: sorted(value) for key, value in ingested_by_annotator.items()},
        "kappa_materialized": bool(kappa_events),
        "kappa_events": kappa_events,
    }


def ingest_annotation_labels(
    *,
    store_dir: str | Path,
    annotation_manifest_path: str | Path,
    run_id: str,
    provider: str,
    protocol_version: str,
    sampling_seed: int,
) -> dict[str, Any]:
    manifest = json.loads(Path(annotation_manifest_path).read_text(encoding="utf-8"))
    annotation_manifest_hash = manifest["annotation_manifest_hash"]
    ledger = load_annotation_ledger_from_events(
        store_dir=store_dir,
        annotation_manifest_hash=annotation_manifest_hash,
    )
    status = annotation_status_from_files(annotation_manifest_path)
    if status["status"] != "ready_for_ingestion":
        raise ValueError("annotation labels are incomplete")

    ingested_count = 0
    for annotator_id, raw_path in manifest["required_label_paths"].items():
        existing = set(ledger["ingested_by_annotator"].get(annotator_id, []))
        for row in _read_label_rows(Path(raw_path)):
            annotation_item_id = str(row["annotation_item_id"])
            if annotation_item_id in existing:
                continue
            event_type = "expert_arbitration_ingested" if annotator_id == "expert" else "annotation_label_ingested"
            append_event(
                store_dir,
                {
                    "event_type": event_type,
                    "run_id": run_id,
                    "question_id": row["question_id"],
                    "hop_depth": row["hop_depth"],
                    "provider": provider,
                    "backend_id": None,
                    "model_id": None,
                    "model_role": None,
                    "ordering_id": None,
                    "ordering": None,
                    "paragraph_id": int(row["paragraph_id"]),
                    "full_logp": None,
                    "loo_logp": None,
                    "delta_loo": None,
                    "baseline_logp": None,
                    "manifest_hash": None,
                    "sampling_seed": sampling_seed,
                    "protocol_version": protocol_version,
                    "request_fingerprint": None,
                    "response_status": "ingested",
                    "notes": f"{annotator_id} annotation ingested",
                    "payload": {
                        "annotation_manifest_hash": annotation_manifest_hash,
                        "annotator_id": annotator_id,
                        "annotation_item_id": annotation_item_id,
                        "source": row["source"],
                        "automated_label": row["automated_label"],
                        "label": row["label"],
                        "justification": row["justification"],
                    },
                },
            )
            ingested_count += 1

    return {
        "status": "ingested",
        "annotation_manifest_hash": annotation_manifest_hash,
        "ingested_count": ingested_count,
    }
