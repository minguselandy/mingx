from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ManifestParagraph:
    paragraph_id: int
    title: str
    text: str
    is_supporting: bool


@dataclass(frozen=True)
class ManifestQuestion:
    question_id: str
    hop_depth: str
    hop_subcategory: str
    question_text: str
    answer_text: str
    answer_aliases: tuple[str, ...]
    answerable: bool
    paragraph_count: int
    paragraphs: tuple[ManifestParagraph, ...]


@dataclass(frozen=True)
class ManifestBundle:
    manifest_path: Path
    manifest_hash: str
    schema_version: str
    created_at_utc: str
    source_dataset: dict[str, Any]
    sampling_config: dict[str, Any]
    diagnostics: dict[str, Any]
    sample: tuple[ManifestQuestion, ...]


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value.strip("'\"")


def load_phase0_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = line.strip()
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()

        while indent <= stack[-1][0]:
            stack.pop()

        current = stack[-1][1]
        if not value:
            new_node: dict[str, Any] = {}
            current[key] = new_node
            stack.append((indent, new_node))
            continue

        current[key] = _parse_scalar(value)

    return root


def _build_paragraph(raw_paragraph: dict[str, Any]) -> ManifestParagraph:
    return ManifestParagraph(
        paragraph_id=int(raw_paragraph["paragraph_idx"]),
        title=str(raw_paragraph["title"]),
        text=str(raw_paragraph["paragraph_text"]),
        is_supporting=bool(raw_paragraph["is_supporting"]),
    )


def _build_question(raw_question: dict[str, Any]) -> ManifestQuestion:
    paragraphs = tuple(_build_paragraph(item) for item in raw_question["paragraphs"])
    return ManifestQuestion(
        question_id=str(raw_question["question_id"]),
        hop_depth=str(raw_question["hop_depth"]),
        hop_subcategory=str(raw_question["hop_subcategory"]),
        question_text=str(raw_question["question_text"]),
        answer_text=str(raw_question["answer_text"]),
        answer_aliases=tuple(raw_question.get("answer_aliases") or ()),
        answerable=bool(raw_question["answerable"]),
        paragraph_count=int(raw_question["paragraph_count"]),
        paragraphs=paragraphs,
    )


def load_manifest(path: str | Path) -> ManifestBundle:
    manifest_path = Path(path)
    raw_bytes = manifest_path.read_bytes()
    payload = json.loads(raw_bytes.decode("utf-8"))
    sample = tuple(_build_question(question) for question in payload["sample"])
    manifest_hash = hashlib.sha256(raw_bytes).hexdigest()

    return ManifestBundle(
        manifest_path=manifest_path.resolve(),
        manifest_hash=manifest_hash,
        schema_version=str(payload["schema_version"]),
        created_at_utc=str(payload["created_at_utc"]),
        source_dataset=dict(payload["source_dataset"]),
        sampling_config=dict(payload["sampling_config"]),
        diagnostics=dict(payload["diagnostics"]),
        sample=sample,
    )


def validate_manifest(
    bundle: ManifestBundle,
    hashes_path: str | Path,
    config_path: str | Path,
) -> dict[str, Any]:
    hashes = json.loads(Path(hashes_path).read_text(encoding="utf-8"))
    config = load_phase0_config(config_path)["phase0"]

    expected_hops = tuple(config["hop_strata"])
    expected_per_hop = int(config["n_per_stratum"])
    expected_total = len(expected_hops) * expected_per_hop
    pool_min, pool_max = config["pool_size_range"]
    hop_counts = Counter(question.hop_depth for question in bundle.sample)
    pool_sizes = [question.paragraph_count for question in bundle.sample]
    errors: list[str] = []

    if bundle.schema_version != hashes["sample_manifest_version"]:
        errors.append("schema_version does not match content_hashes.json")
    if bundle.source_dataset.get("split") != config["split"]:
        errors.append("source dataset split does not match phase0.yaml")
    if len(bundle.sample) != expected_total:
        errors.append("sample size does not match phase0.yaml")
    if bundle.source_dataset.get("content_hash_sha256") != hashes["musique_dev_sha256"]:
        errors.append("dataset hash does not match content_hashes.json")
    if int(bundle.sampling_config.get("seed", -1)) != int(hashes["sampling_seed"]):
        errors.append("sampling seed does not match content_hashes.json")
    if int(bundle.sampling_config.get("seed", -1)) != int(config["seed"]):
        errors.append("sampling seed does not match phase0.yaml")

    for hop in expected_hops:
        if hop_counts.get(hop, 0) != expected_per_hop:
            errors.append(f"unexpected sample count for {hop}")

    if pool_sizes:
        observed_min = min(pool_sizes)
        observed_max = max(pool_sizes)
        if observed_min < pool_min or observed_max > pool_max:
            errors.append("paragraph pool size is out of configured range")
    else:
        observed_min = None
        observed_max = None
        errors.append("manifest sample is empty")

    for question in bundle.sample:
        if question.paragraph_count != len(question.paragraphs):
            errors.append(f"paragraph_count mismatch for {question.question_id}")

    return {
        "ok": not errors,
        "errors": errors,
        "schema_version": bundle.schema_version,
        "dataset_hash": bundle.source_dataset.get("content_hash_sha256"),
        "manifest_hash": bundle.manifest_hash,
        "sampling_seed": bundle.sampling_config.get("seed"),
        "total_sampled": len(bundle.sample),
        "by_hop_depth": {hop: hop_counts.get(hop, 0) for hop in expected_hops},
        "pool_size_range": {"min": observed_min, "max": observed_max},
    }
