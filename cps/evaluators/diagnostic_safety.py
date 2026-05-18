from __future__ import annotations

from cps.evaluators.workbench_types import EvaluationRequest
from cps.evaluators.workbench_types import EvaluationResult


def evaluate_diagnostic_safety(request: EvaluationRequest) -> EvaluationResult:
    return EvaluationResult(
        claim_mode=request.claim_mode,
        evaluator_name="diagnostic_safety",
        claim_flags={
            "calibrated_proxy_supported": False,
            "global_selector_superiority": False,
            "measurement_validated": False,
            "metric_bridge_support": False,
            "selector_superiority_claimed": False,
            "vinfo_proxy_supported": False,
        },
        metrics={
            "claim_status": "operational_utility_only; no_claim_upgrade",
            "diagnostic_safety_status": "claim_safe_shadow_mode",
        },
    )
