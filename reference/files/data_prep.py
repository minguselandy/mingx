"""
data_prep.py — Phase 1 Probe Data Preparation Module

Implements the hop-stratified sampling procedure specified in
Phase 1 Protocol Section A.1–A.3. Produces a reproducible sample
manifest with content hashes for downstream consumption.

Phase 1 Protocol references:
    A.1 MuSiQue dev-set access and loading
    A.2 Hop-stratified sampling procedure
    A.3 Per-question paragraph-pool extraction
"""

import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from datasets import load_dataset


# Protocol constants — pinned to Phase 1 Protocol Section A.2 and Phase 0 §3
MUSIQUE_REPO = "dgslibisey/MuSiQue"
MUSIQUE_SPLIT = "validation"
N_PER_STRATUM = 30
HOP_STRATA = ("2hop", "3hop", "4hop")
POOL_SIZE_MIN = 15
POOL_SIZE_MAX = 25
SAMPLING_SEED = 20260418  # Fixed seed recorded per Phase 1 Protocol Section A.2


@dataclass(frozen=True)
class SampledParagraph:
    """Per-paragraph record within a sampled question."""
    paragraph_idx: int           # Native MuSiQue paragraph index
    title: str                   # Wikipedia article title
    paragraph_text: str          # Full paragraph text content
    is_supporting: bool          # MuSiQue-native supporting-paragraph flag

    @classmethod
    def from_native(cls, p: dict[str, Any]) -> "SampledParagraph":
        """Construct from a native MuSiQue paragraph dict."""
        return cls(
            paragraph_idx=int(p["idx"]),
            title=str(p["title"]),
            paragraph_text=str(p["paragraph_text"]),
            is_supporting=bool(p["is_supporting"]),
        )


@dataclass(frozen=True)
class SampledQuestion:
    """Per-question record in the sample manifest."""
    question_id: str             # MuSiQue native id, e.g. "2hop__460946_294723"
    hop_depth: str               # Pooled stratum label: "2hop", "3hop", or "4hop"
    hop_subcategory: str         # Native sub-stratum, e.g. "3hop1"
    question_text: str
    answer_text: str
    answer_aliases: list[str]
    answerable: bool
    paragraph_count: int
    paragraphs: list[SampledParagraph]


def derive_hop_depth(question_id: str) -> tuple[str, str]:
    """Parse hop depth from MuSiQue id format.

    MuSiQue ids use the format '<sub-stratum>__<hash>' where sub-stratum
    is one of '2hop', '3hop1', '3hop2', '4hop1', '4hop2', '4hop3'. The
    Phase 1 Protocol stratifies by hop depth, pooling sub-strata within
    each depth.

    Returns a (hop_depth, hop_subcategory) pair.
    """
    prefix = question_id.split("__", 1)[0]
    match = re.match(r"^([234])hop(\d*)$", prefix)
    if match is None:
        raise ValueError(f"Unexpected MuSiQue id format: {question_id}")
    depth_digit = match.group(1)
    return f"{depth_digit}hop", prefix


def compute_content_hash(ds) -> str:
    """Compute a SHA-256 content hash over the MuSiQue dev split.

    The hash covers the full serialized content of every question in the
    natural row order, providing a strong reproducibility anchor per
    Phase 1 Protocol Section A.1.
    """
    hasher = hashlib.sha256()
    for row in ds:
        serialized = json.dumps(row, sort_keys=True, ensure_ascii=False)
        hasher.update(serialized.encode("utf-8"))
    return hasher.hexdigest()


def hop_stratified_sample(
    ds,
    n_per_stratum: int = N_PER_STRATUM,
    seed: int = SAMPLING_SEED,
) -> tuple[list[SampledQuestion], dict[str, Any]]:
    """Draw a hop-stratified sample of the MuSiQue dev set.

    Implements Phase 1 Protocol Section A.2 with three key features:
    (a) simple random sampling without replacement within each hop-depth
    stratum, (b) rejection of questions whose paragraph pool size falls
    outside [POOL_SIZE_MIN, POOL_SIZE_MAX], and (c) deterministic seeding
    for reproducibility.

    Sub-strata within each hop depth (e.g., 3hop1 and 3hop2) are pooled
    under the protocol's hop-depth stratification scheme.

    Returns the sample plus a diagnostic dictionary recording pre-rejection
    counts, rejection counts, and per-stratum draw statistics.
    """
    # Partition by pooled hop depth, applying the pool-size rejection filter
    by_stratum: dict[str, list[int]] = defaultdict(list)
    rejected = {"pool_too_small": 0, "pool_too_large": 0, "unparseable_id": 0}

    for row_idx, row in enumerate(ds):
        try:
            hop_depth, _ = derive_hop_depth(row["id"])
        except ValueError:
            rejected["unparseable_id"] += 1
            continue
        pool_size = len(row["paragraphs"])
        if pool_size < POOL_SIZE_MIN:
            rejected["pool_too_small"] += 1
            continue
        if pool_size > POOL_SIZE_MAX:
            rejected["pool_too_large"] += 1
            continue
        by_stratum[hop_depth].append(row_idx)

    # Deterministic sampling per stratum
    rng = random.Random(seed)
    sampled_indices: list[int] = []
    stratum_stats: dict[str, dict[str, int]] = {}
    for stratum in HOP_STRATA:
        candidates = by_stratum.get(stratum, [])
        if len(candidates) < n_per_stratum:
            raise RuntimeError(
                f"Insufficient candidates in stratum {stratum}: "
                f"have {len(candidates)}, need {n_per_stratum}"
            )
        drawn = rng.sample(candidates, n_per_stratum)
        sampled_indices.extend(drawn)
        stratum_stats[stratum] = {
            "candidates_after_filter": len(candidates),
            "drawn": n_per_stratum,
        }

    # Materialize sampled questions as structured records
    sample: list[SampledQuestion] = []
    for idx in sampled_indices:
        row = ds[idx]
        hop_depth, hop_subcategory = derive_hop_depth(row["id"])
        sample.append(
            SampledQuestion(
                question_id=row["id"],
                hop_depth=hop_depth,
                hop_subcategory=hop_subcategory,
                question_text=row["question"],
                answer_text=row["answer"],
                answer_aliases=list(row.get("answer_aliases") or []),
                answerable=bool(row["answerable"]),
                paragraph_count=len(row["paragraphs"]),
                paragraphs=[
                    SampledParagraph.from_native(p) for p in row["paragraphs"]
                ],
            )
        )

    diagnostics = {
        "rejection_counts": rejected,
        "stratum_stats": stratum_stats,
        "total_sampled": len(sample),
        "seed": seed,
    }
    return sample, diagnostics


def serialize_sample_manifest(
    sample: list[SampledQuestion],
    content_hash: str,
    diagnostics: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    """Write the sample manifest to a versioned JSON file.

    The manifest structure is designed for append-only versioning: the
    file name encodes version and timestamp, and the content includes
    the full sample plus provenance metadata.
    """
    manifest = {
        "schema_version": "phase1.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_dataset": {
            "repo": MUSIQUE_REPO,
            "split": MUSIQUE_SPLIT,
            "content_hash_sha256": content_hash,
        },
        "sampling_config": {
            "n_per_stratum": N_PER_STRATUM,
            "hop_strata": list(HOP_STRATA),
            "pool_size_range": [POOL_SIZE_MIN, POOL_SIZE_MAX],
            "seed": diagnostics["seed"],
        },
        "diagnostics": diagnostics,
        "sample": [asdict(q) for q in sample],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest


def summarize_sample(sample: list[SampledQuestion]) -> dict[str, Any]:
    """Produce summary statistics for sanity-checking the sample."""
    hop_counts = Counter(q.hop_depth for q in sample)
    subcat_counts = Counter(q.hop_subcategory for q in sample)
    pool_sizes = [q.paragraph_count for q in sample]
    supporting_counts_per_q = [
        sum(1 for p in q.paragraphs if p.is_supporting) for q in sample
    ]
    return {
        "total": len(sample),
        "by_hop_depth": dict(hop_counts),
        "by_subcategory": dict(subcat_counts),
        "pool_size_min": min(pool_sizes),
        "pool_size_max": max(pool_sizes),
        "pool_size_mean": sum(pool_sizes) / len(pool_sizes),
        "supporting_per_question_mean": (
            sum(supporting_counts_per_q) / len(supporting_counts_per_q)
        ),
    }


def execute_data_preparation(output_dir: Path) -> dict[str, Any]:
    """End-to-end Phase 1 data preparation pipeline.

    Returns a report dict suitable for inclusion in the execution log.
    """
    print(f"Loading MuSiQue dev set from {MUSIQUE_REPO}...")
    ds = load_dataset(MUSIQUE_REPO, split=MUSIQUE_SPLIT)
    print(f"  Loaded {len(ds)} questions")

    print("Computing content hash over dev split...")
    content_hash = compute_content_hash(ds)
    print(f"  SHA-256: {content_hash}")

    print(f"Drawing hop-stratified sample (N = {len(HOP_STRATA) * N_PER_STRATUM})...")
    sample, diagnostics = hop_stratified_sample(ds)
    print(f"  Rejection counts: {diagnostics['rejection_counts']}")
    print(f"  Per-stratum: {diagnostics['stratum_stats']}")

    summary = summarize_sample(sample)
    print(f"Sample summary: {json.dumps(summary, indent=2)}")

    manifest_path = output_dir / "sample_manifest_v1.json"
    serialize_sample_manifest(sample, content_hash, diagnostics, manifest_path)
    print(f"Manifest written to {manifest_path}")

    hashes_path = output_dir / "content_hashes.json"
    with hashes_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "musique_dev_sha256": content_hash,
                "sample_manifest_version": "phase1.v1",
                "sampling_seed": SAMPLING_SEED,
            },
            f,
            indent=2,
        )
    print(f"Content hashes written to {hashes_path}")

    return {
        "content_hash": content_hash,
        "sample_size": len(sample),
        "diagnostics": diagnostics,
        "summary": summary,
        "manifest_path": str(manifest_path),
    }


if __name__ == "__main__":
    output_dir = Path("/home/claude/phase1/data")
    report = execute_data_preparation(output_dir)
    log_path = Path("/home/claude/phase1/logs/data_prep.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
