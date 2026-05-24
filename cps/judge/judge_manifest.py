from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable, Mapping

from cps.experiments.artifacts import stable_hash
from cps.judge.weak_evidence_schema import ALLOWED_CLAIM_LEVEL, CLAIM_STATUS


ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATHS = (
    Path("prompts/judge/weak_evidence_v1.md"),
    Path("prompts/judge/weak_evidence_v1_order_swapped.md"),
)
RUBRIC_PARAPHRASE_IDS = ("p0", "p1")


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prompt_hashes() -> dict[str, str]:
    return {
        path.as_posix(): _file_hash(ROOT / path)
        for path in PROMPT_PATHS
    }


def _normalize_item(item: Mapping[str, Any]) -> dict[str, Any]:
    item_id = str(item["item_id"])
    return {
        "item_id": item_id,
        "left_evidence_hash": str(item.get("left_evidence_hash", "")),
        "right_evidence_hash": str(item.get("right_evidence_hash", "")),
    }


def build_judge_run_manifest(
    *,
    run_id: str,
    items: Iterable[Mapping[str, Any]],
    judge_model_snapshot: str = "static-judge-snapshot",
) -> dict[str, Any]:
    normalized_items = sorted(
        (_normalize_item(item) for item in items),
        key=lambda row: row["item_id"],
    )
    hashes = prompt_hashes()
    judgment_requests: list[dict[str, Any]] = []

    for item in normalized_items:
        for rubric_paraphrase_id in RUBRIC_PARAPHRASE_IDS:
            for duplicate_index in range(2):
                for order_swap, prompt_path in (
                    (False, PROMPT_PATHS[0]),
                    (True, PROMPT_PATHS[1]),
                ):
                    prompt_key = prompt_path.as_posix()
                    judgment_requests.append(
                        {
                            "judgment_id": "-".join(
                                [
                                    str(run_id),
                                    item["item_id"],
                                    rubric_paraphrase_id,
                                    str(duplicate_index),
                                    "swap" if order_swap else "base",
                                ]
                            ),
                            "item_id": item["item_id"],
                            "pair_id": item["item_id"],
                            "left_evidence_hash": item["left_evidence_hash"],
                            "right_evidence_hash": item["right_evidence_hash"],
                            "judge_model_snapshot": judge_model_snapshot,
                            "judge_prompt_hash": hashes[prompt_key],
                            "prompt_path": prompt_key,
                            "rubric_version": "weak_evidence_v1",
                            "rubric_paraphrase_id": rubric_paraphrase_id,
                            "order_swap_enabled": order_swap,
                            "duplicate_index": duplicate_index,
                            "raw_response_stored": False,
                            "parsed_label": None,
                            "parse_status": "pending",
                        }
                    )

    manifest = {
        "run_id": str(run_id),
        "judge_protocol_version": "v1_weak_evidence_only",
        "judge_model_snapshot": judge_model_snapshot,
        "blinded_pairwise_comparison": True,
        "order_swapped_duplication": True,
        "duplicate_judging_min": 2,
        "rubric_paraphrase_ids": list(RUBRIC_PARAPHRASE_IDS),
        "rubric_paraphrase_min": 2,
        "temperature": 0,
        "length_aware_reporting": True,
        "parse_failure_tracking": True,
        "raw_response_stored": False,
        "allowed_claim_level": ALLOWED_CLAIM_LEVEL,
        "claim_status": CLAIM_STATUS,
        "route_5_locked": True,
        "route_8_locked": True,
        "live_api_call_performed": False,
        "prompt_hashes": hashes,
        "items": normalized_items,
        "judgment_requests": sorted(
            judgment_requests,
            key=lambda row: row["judgment_id"],
        ),
    }
    manifest["manifest_hash"] = stable_hash(manifest)
    return manifest
