from __future__ import annotations

from collections import Counter
from collections import defaultdict
from typing import Any
from typing import Mapping
from typing import Sequence


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"


def _by_parent(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("parent_sample_id") or "")].append(row)
    return dict(sorted(grouped.items()))


def _probe(rows: Sequence[Mapping[str, Any]], name: str) -> Mapping[str, Any] | None:
    return next((row for row in rows if str(row.get("probe_type") or "") == name), None)


def _consistency(rows: Sequence[Mapping[str, Any]], probe_name: str) -> dict[str, Any]:
    total = 0
    consistent = 0
    for group in _by_parent(rows).values():
        primary = _probe(group, "primary")
        other = _probe(group, probe_name)
        if primary is None or other is None:
            continue
        total += 1
        if primary.get("label") == other.get("label"):
            consistent += 1
    return {
        "consistent": consistent,
        "rate": round(consistent / total, 6) if total else None,
        "total": total,
    }


def audit_judge_weak_source(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    labels = [str(row.get("label") or "unknown") for row in rows]
    parse_failures = sum(1 for row in rows if row.get("parse_ok") is False)
    clusters = [
        {
            "labels": dict(Counter(str(row.get("label") or "unknown") for row in group)),
            "parent_sample_id": parent,
        }
        for parent, group in _by_parent(rows).items()
        if len({str(row.get("label") or "") for row in group}) > 1
    ]
    return {
        "bias_risk_notes": [
            "single_provider_single_model_weak_supervision",
            "public_benchmark_gold_used_for_diagnostic_match_only_not_measurement_validation",
        ],
        "claim_ceiling": "model_adjudicated_measurement_candidate",
        "claim_status": CLAIM_STATUS,
        "counts_as_human_or_external_gold": False,
        "disagreement_clusters": clusters,
        "duplicate_consistency": _consistency(rows, "duplicate"),
        "json_validity": {
            "parse_failure_count": parse_failures,
            "parse_success_rate": round((len(rows) - parse_failures) / len(rows), 6) if rows else 0.0,
        },
        "label_counts": dict(sorted(Counter(labels).items())),
        "order_swap_consistency": _consistency(rows, "order_swap"),
        "prompt_swap_consistency": _consistency(rows, "prompt_swap"),
        "raw_response_stored": False,
        "rubric_adherence": {
            "allowed_label_rate": round(sum(1 for label in labels if label in {"not_supporting", "supporting", "uncertain"}) / len(labels), 6)
            if labels
            else 0.0,
            "rubric_version": "epf_live_api_weak_source_rubric_v1",
        },
        "schema_version": "epf_judge_weak_source_audit_v1",
        "status": "weak_source_audit_completed" if rows else "blocked_no_label_rows",
    }
