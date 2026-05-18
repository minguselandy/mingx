from __future__ import annotations


def shadow_bridge_controls() -> dict[str, object]:
    return {
        "accepted_metric_claim": "operational_utility_only",
        "calibrated_proxy_supported": False,
        "control_status": "shadow_mode_no_claim_upgrade",
        "non_circularity_review_required_before_acceptance": True,
        "vinfo_proxy_supported": False,
    }
