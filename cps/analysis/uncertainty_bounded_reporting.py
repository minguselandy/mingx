from __future__ import annotations

import math
from typing import Any
from typing import Mapping
from typing import Sequence


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"


def build_uncertainty_report(*, evidence_items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    confidences = [float(item.get("confidence") or 0.0) for item in evidence_items]
    mean = sum(confidences) / len(confidences) if confidences else 0.0
    if len(confidences) > 1:
        variance = sum((value - mean) ** 2 for value in confidences) / (len(confidences) - 1)
        stderr = math.sqrt(variance / len(confidences))
    else:
        stderr = 0.0
    return {
        "allowed_claim": "uncertainty_bounded_operational_reporting_candidate",
        "claim_status": CLAIM_STATUS,
        "claim_upgrade_allowed": False,
        "evidence_count": len(evidence_items),
        "lower_confidence_bound": round(max(0.0, mean - 1.96 * stderr), 6),
        "mean_confidence": round(mean, 6),
        "raw_response_stored": False,
        "schema_version": "epf_uncertainty_report_v1",
        "upper_confidence_bound": round(min(1.0, mean + 1.96 * stderr), 6),
    }
