from __future__ import annotations


def build_diagnostic_safety_report(*, traces_compared: int) -> dict[str, object]:
    return {
        "calibrated_proxy_supported": False,
        "claim_status": "operational_utility_only; no_claim_upgrade",
        "global_selector_superiority": False,
        "measurement_validated": False,
        "metric_bridge_support": False,
        "metric_claim_level": "operational_utility_only",
        "selector_superiority_claimed": False,
        "traces_compared": traces_compared,
        "vinfo_proxy_supported": False,
    }
