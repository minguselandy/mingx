from __future__ import annotations

from typing import Any
from typing import Mapping
from typing import Sequence


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"


def build_contamination_report(*, datasets: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for dataset in datasets:
        source_kind = str(dataset.get("source_kind") or "")
        risk = "fixture_or_public_benchmark_needs_review" if source_kind in {"fixture", "public_benchmark"} else "unknown_source_risk"
        rows.append(
            {
                "dataset": str(dataset.get("dataset") or ""),
                "dynamic_holdout_available": False,
                "risk": risk,
                "source_kind": source_kind,
                "split": str(dataset.get("split") or ""),
            }
        )
    return {
        "claim_status": CLAIM_STATUS,
        "claim_upgrade_allowed": False,
        "dataset_count": len(rows),
        "datasets": rows,
        "raw_dataset_mirrors_created": False,
        "schema_version": "epf_contamination_report_v1",
        "status": "contamination_review_required" if rows else "blocked_no_dataset_provenance",
    }
