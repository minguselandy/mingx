from __future__ import annotations

from collections import Counter
from typing import Any
from typing import Mapping
from typing import Sequence


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"


def build_judge_bias_audit(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    labels = Counter(str(row.get("label") or "unknown") for row in rows)
    total = sum(labels.values())
    dominant_rate = max(labels.values()) / total if total else 0.0
    notes = ["single_model_provider_bias_risk"]
    if dominant_rate > 0.8:
        notes.append("dominant_label_distribution_risk")
    return {
        "bias_risk_notes": notes,
        "claim_status": CLAIM_STATUS,
        "dominant_label_rate": round(dominant_rate, 6),
        "label_counts": dict(sorted(labels.items())),
        "raw_response_stored": False,
        "schema_version": "epf_judge_bias_audit_v1",
        "status": "judge_bias_audit_completed" if total else "blocked_no_label_rows",
    }
