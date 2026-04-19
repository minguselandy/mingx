from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from cps.data.manifest import ManifestBundle


SELECTION_ALGORITHM_VERSION = "calibration_by_hop_questionid_sha256_v1"


def _selection_score(seed: int, question_id: str) -> str:
    payload = f"{SELECTION_ALGORITHM_VERSION}|{seed}|{question_id}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_calibration_manifest(
    bundle: ManifestBundle,
    output_path: str | Path,
    *,
    seed: int,
    per_hop_count: int = 10,
    exclude_question_ids: tuple[str, ...] = (),
) -> dict:
    selected_questions: list[dict[str, str]] = []
    grouped: dict[str, list] = {}
    excluded = {str(question_id) for question_id in exclude_question_ids}

    for question in sorted(bundle.sample, key=lambda item: (item.hop_depth, item.question_id)):
        grouped.setdefault(question.hop_depth, []).append(question)

    for hop_depth in sorted(grouped):
        ranked = sorted(
            (
                {
                    "question_id": question.question_id,
                    "hop_depth": question.hop_depth,
                    "selection_score": _selection_score(seed, question.question_id),
                }
                for question in grouped[hop_depth]
                if question.question_id not in excluded
            ),
            key=lambda item: (item["selection_score"], item["question_id"]),
        )
        if len(ranked) < per_hop_count:
            raise ValueError(f"Not enough questions in {hop_depth} for calibration selection")
        selected_questions.extend(ranked[:per_hop_count])

    manifest_bytes = bundle.manifest_path.read_bytes()
    fingerprint = hashlib.sha256(manifest_bytes).hexdigest()
    payload = {
        "source_manifest_path": str(bundle.manifest_path.resolve()),
        "source_manifest_hash": bundle.manifest_hash,
        "source_manifest_fingerprint": f"sha256:{fingerprint}",
        "source_dataset_hash": bundle.source_dataset.get("content_hash_sha256"),
        "seed": seed,
        "per_hop_counts": dict(Counter(entry["hop_depth"] for entry in selected_questions)),
        "selection_algorithm_version": SELECTION_ALGORITHM_VERSION,
        "excluded_question_ids": sorted(excluded),
        "replacement_policy": "same_hop_next_rank_on_resume_v1",
        "selected_questions": selected_questions,
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
