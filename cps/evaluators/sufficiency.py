from __future__ import annotations

from cps.evaluators.operational import evaluate_operational
from cps.evaluators.workbench_types import EvaluationRequest
from cps.evaluators.workbench_types import EvaluationResult


def evaluate_sufficiency_shadow(request: EvaluationRequest) -> EvaluationResult:
    operational = evaluate_operational(request)
    return EvaluationResult(
        claim_mode=request.claim_mode,
        evaluator_name="sufficiency",
        claim_flags={
            "measurement_validated": False,
            "shadow_measurement_candidate": True,
        },
        metrics={
            "shadow_sufficiency_score": operational.metrics["supporting_fact_recall_at_budget"],
            "sufficiency_status": "shadow_measurement_candidate",
        },
    )
