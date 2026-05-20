from __future__ import annotations

from typing import Any
from typing import Mapping


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"


def build_dynamic_holdout_readiness(contamination_report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "claim_status": CLAIM_STATUS,
        "dynamic_holdout_ready": False,
        "reason": "no_fresh_dynamic_holdout_layer_reviewed",
        "route5_unlocked": False,
        "route8_unlocked": False,
        "schema_version": "epf_dynamic_holdout_readiness_v1",
        "source_contamination_status": str(contamination_report.get("status") or ""),
    }
