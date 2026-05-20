from __future__ import annotations

from typing import Any
from typing import Mapping
from typing import Sequence


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"


def build_human_gold_manifest(gold_rows: Sequence[Mapping[str, Any]] | None) -> dict[str, Any]:
    rows = list(gold_rows or [])
    return {
        "claim_status": CLAIM_STATUS,
        "gold_row_count": len(rows),
        "human_external_gold_available": bool(rows),
        "raw_response_stored": False,
        "schema_version": "epf_human_gold_manifest_v1",
    }


def compute_agreement_report(
    label_rows: Sequence[Mapping[str, Any]],
    gold_rows: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    gold = {str(row.get("parent_sample_id") or row.get("sample_id") or ""): row for row in gold_rows or []}
    if not gold:
        return {
            "claim_status": CLAIM_STATUS,
            "measurement_validation_allowed": False,
            "reason": "human_external_gold_unavailable",
            "schema_version": "epf_human_gold_agreement_report_v1",
            "status": "blocked_no_human_external_gold",
        }
    matched = 0
    agreed = 0
    for row in label_rows:
        key = str(row.get("parent_sample_id") or "")
        if key not in gold:
            continue
        matched += 1
        agreed += int(str(row.get("label")) == str(gold[key].get("label")))
    return {
        "agreement_rate": round(agreed / matched, 6) if matched else 0.0,
        "claim_status": CLAIM_STATUS,
        "matched_count": matched,
        "measurement_validation_allowed": False,
        "schema_version": "epf_human_gold_agreement_report_v1",
        "status": "candidate_only_pending_independent_review",
    }
