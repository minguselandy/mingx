from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from cps.analysis.exports import write_json
from cps.runtime.annotation import load_annotation_ledger_from_events
from cps.store.measurement import append_event


LABELS = ("HIGH", "LOW", "BUFFER")


def _cohens_kappa(rows: list[dict[str, Any]], left_key: str, right_key: str) -> float:
    comparable = [
        row for row in rows if row.get(left_key) in LABELS and row.get(right_key) in LABELS
    ]
    if not comparable:
        return 0.0
    left_counts = Counter(str(row[left_key]) for row in comparable)
    right_counts = Counter(str(row[right_key]) for row in comparable)
    total = len(comparable)
    observed = sum(1 for row in comparable if row[left_key] == row[right_key]) / total
    expected = sum((left_counts[label] / total) * (right_counts[label] / total) for label in LABELS)
    denominator = 1.0 - expected
    if denominator == 0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / denominator


def _bootstrap_ci(
    rows: list[dict[str, Any]],
    *,
    left_key: str,
    right_key: str,
    seed: int,
    bootstrap_resamples: int,
) -> list[float]:
    comparable = [
        row for row in rows if row.get(left_key) in LABELS and row.get(right_key) in LABELS
    ]
    if not comparable:
        return [0.0, 0.0]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in comparable:
        grouped[str(row["question_id"])].append(row)
    question_ids = sorted(grouped)
    rng = random.Random(seed)
    kappas: list[float] = []
    for _ in range(bootstrap_resamples):
        sampled_rows: list[dict[str, Any]] = []
        for _ in question_ids:
            sampled_rows.extend(grouped[rng.choice(question_ids)])
        kappas.append(_cohens_kappa(sampled_rows, left_key, right_key))
    kappas.sort()
    lower_index = int(0.025 * (len(kappas) - 1))
    upper_index = int(0.975 * (len(kappas) - 1))
    return [kappas[lower_index], kappas[upper_index]]


def _metric_summary(
    rows: list[dict[str, Any]],
    *,
    left_key: str,
    right_key: str,
    seed: int,
    bootstrap_resamples: int,
) -> dict[str, Any]:
    comparable = [
        row for row in rows if row.get(left_key) in LABELS and row.get(right_key) in LABELS
    ]
    disagreements = sum(1 for row in comparable if row[left_key] != row[right_key])
    return {
        "point_estimate": _cohens_kappa(rows, left_key, right_key),
        "ci_95": _bootstrap_ci(
            rows,
            left_key=left_key,
            right_key=right_key,
            seed=seed,
            bootstrap_resamples=bootstrap_resamples,
        ),
        "n_items": len(comparable),
        "disagreement_count": disagreements,
    }


def _tier_classification(pooled: dict[str, Any], threshold: float) -> dict[str, Any]:
    automated = pooled["kappa_automated_expert"]
    primary = pooled["kappa_primary"]
    primary_expert = pooled["kappa_primary_expert"]
    secondary_metrics = [
        primary,
        primary_expert["primary_a"],
        primary_expert["primary_b"],
    ]
    if automated["point_estimate"] < threshold:
        tier = "tier3_design_revision"
        reason = "automated-expert agreement is below the Phase 2-binding threshold"
    elif automated["ci_95"][0] >= threshold and all(
        metric["point_estimate"] >= threshold and metric["ci_95"][0] >= threshold
        for metric in secondary_metrics
    ):
        tier = "tier1_unconditional_pass"
        reason = "all pooled reliability metrics exceed the Phase 2-binding threshold with lower CI support"
    else:
        tier = "tier2_conditional_pass"
        reason = "automated-expert agreement clears the threshold, but one or more secondary metrics or lower bounds do not"
    return {
        "tier": tier,
        "threshold": threshold,
        "reason": reason,
    }


def compute_reliability_summary(
    *,
    annotation_rows: list[dict[str, Any]],
    annotation_mode: str,
    seed: int,
    bootstrap_resamples: int = 1000,
    threshold: float = 0.7,
) -> dict[str, Any]:
    pooled = {
        "kappa_primary": _metric_summary(
            annotation_rows,
            left_key="primary_a_label",
            right_key="primary_b_label",
            seed=seed,
            bootstrap_resamples=bootstrap_resamples,
        ),
        "kappa_primary_expert": {
            "primary_a": _metric_summary(
                annotation_rows,
                left_key="primary_a_label",
                right_key="expert_label",
                seed=seed + 11,
                bootstrap_resamples=bootstrap_resamples,
            ),
            "primary_b": _metric_summary(
                annotation_rows,
                left_key="primary_b_label",
                right_key="expert_label",
                seed=seed + 17,
                bootstrap_resamples=bootstrap_resamples,
            ),
        },
        "kappa_automated_expert": _metric_summary(
            annotation_rows,
            left_key="automated_label",
            right_key="expert_label",
            seed=seed + 23,
            bootstrap_resamples=bootstrap_resamples,
        ),
    }
    per_hop = {}
    for hop_depth in sorted({str(row["hop_depth"]) for row in annotation_rows}):
        hop_rows = [row for row in annotation_rows if str(row["hop_depth"]) == hop_depth]
        per_hop[hop_depth] = {
            "kappa_primary": _metric_summary(
                hop_rows,
                left_key="primary_a_label",
                right_key="primary_b_label",
                seed=seed + sum(ord(char) for char in hop_depth),
                bootstrap_resamples=bootstrap_resamples,
            ),
            "kappa_primary_expert": {
                "primary_a": _metric_summary(
                    hop_rows,
                    left_key="primary_a_label",
                    right_key="expert_label",
                    seed=seed + 31 + sum(ord(char) for char in hop_depth),
                    bootstrap_resamples=bootstrap_resamples,
                ),
                "primary_b": _metric_summary(
                    hop_rows,
                    left_key="primary_b_label",
                    right_key="expert_label",
                    seed=seed + 37 + sum(ord(char) for char in hop_depth),
                    bootstrap_resamples=bootstrap_resamples,
                ),
            },
            "kappa_automated_expert": _metric_summary(
                hop_rows,
                left_key="automated_label",
                right_key="expert_label",
                seed=seed + 41 + sum(ord(char) for char in hop_depth),
                bootstrap_resamples=bootstrap_resamples,
            ),
        }

    return {
        "status": "computed",
        "annotation_mode": annotation_mode,
        "scientific_consumption_allowed": annotation_mode == "human_labels",
        "threshold": {
            "value": threshold,
            "source_document": "execution-readiness-checklist.md",
            "note": "Phase 2-binding threshold supersedes the provisional 0.6 benchmark in phase1-protocol.md",
        },
        "bootstrap_resamples": bootstrap_resamples,
        "pooled": pooled,
        "per_hop": per_hop,
        "tier_classification": _tier_classification(pooled, threshold),
    }


def compute_reliability_from_events(
    *,
    store_dir: str | Path,
    annotation_manifest_hash: str,
    export_dir: str | Path,
    run_id: str,
    provider: str,
    protocol_version: str,
    sampling_seed: int,
    bootstrap_resamples: int = 1000,
    threshold: float = 0.7,
) -> dict[str, Any]:
    ledger = load_annotation_ledger_from_events(
        store_dir=store_dir,
        annotation_manifest_hash=annotation_manifest_hash,
    )
    rows = list(ledger["records"].values())
    summary = compute_reliability_summary(
        annotation_rows=rows,
        annotation_mode=str(ledger["annotation_mode"]),
        seed=sampling_seed,
        bootstrap_resamples=bootstrap_resamples,
        threshold=threshold,
    )
    summary["annotation_manifest_hash"] = annotation_manifest_hash
    summary_path = write_json(Path(export_dir) / "kappa_summary.json", summary)
    append_event(
        store_dir,
        {
            "event_type": "kappa_materialized",
            "run_id": run_id,
            "question_id": None,
            "hop_depth": None,
            "provider": provider,
            "backend_id": None,
            "model_id": None,
            "model_role": None,
            "ordering_id": None,
            "ordering": None,
            "paragraph_id": None,
            "full_logp": None,
            "loo_logp": None,
            "delta_loo": None,
            "baseline_logp": None,
            "manifest_hash": None,
            "sampling_seed": sampling_seed,
            "protocol_version": protocol_version,
            "request_fingerprint": None,
            "response_status": "materialized",
            "notes": str(summary_path),
            "payload": {
                "annotation_manifest_hash": annotation_manifest_hash,
                "tier": summary["tier_classification"]["tier"],
                "summary_path": str(summary_path),
            },
        },
    )
    return {
        "status": "computed",
        "kappa_summary_path": str(summary_path),
        "summary": summary,
    }
