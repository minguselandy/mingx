from __future__ import annotations

from typing import Any
from typing import Mapping
from typing import Sequence


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"


def build_hybrid_validation_candidate(
    *,
    human_gold_manifest: Mapping[str, Any],
    judge_audit: Mapping[str, Any],
    label_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    human_available = bool(human_gold_manifest.get("human_external_gold_available"))
    return {
        "claim_status": CLAIM_STATUS,
        "judge_audit_status": str(judge_audit.get("status") or ""),
        "label_count": len(label_rows),
        "measurement_candidate_review_packet": human_available,
        "measurement_validation_candidate": False,
        "raw_response_stored": False,
        "reason": None if human_available else "human_external_gold_unavailable",
        "schema_version": "epf_hybrid_validation_candidate_v1",
        "status": "candidate_review_packet_ready" if human_available else "blocked_no_human_external_gold",
    }
