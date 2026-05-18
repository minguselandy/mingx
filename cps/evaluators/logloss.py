from __future__ import annotations

from cps.evaluators.workbench_types import EvaluationRequest
from cps.evaluators.workbench_types import EvaluationResult


def evaluate_logloss_shadow(request: EvaluationRequest) -> EvaluationResult:
    return EvaluationResult(
        claim_mode=request.claim_mode,
        evaluator_name="logloss",
        claim_flags={
            "calibrated_proxy_supported": False,
            "shadow_vinfo_proxy": True,
            "vinfo_proxy_supported": False,
        },
        metrics={
            "fixed_model_logloss_available": False,
            "logloss_status": "shadow_vinfo_proxy_no_fixed_model_scoring",
        },
    )
