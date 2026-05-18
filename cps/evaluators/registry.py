from __future__ import annotations

from collections.abc import Callable

from cps.evaluators.diagnostic_safety import evaluate_diagnostic_safety
from cps.evaluators.logloss import evaluate_logloss_shadow
from cps.evaluators.operational import evaluate_operational
from cps.evaluators.sufficiency import evaluate_sufficiency_shadow
from cps.evaluators.workbench_types import EvaluationRequest
from cps.evaluators.workbench_types import EvaluationResult


EvaluatorFunction = Callable[[EvaluationRequest], EvaluationResult]


class EvaluatorRegistry:
    def __init__(self) -> None:
        self._evaluators: dict[str, EvaluatorFunction] = {}

    def register(self, name: str, evaluator: EvaluatorFunction) -> None:
        self._evaluators[name] = evaluator

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._evaluators))

    def evaluate(self, name: str, request: EvaluationRequest) -> EvaluationResult:
        if name not in self._evaluators:
            raise KeyError(f"unknown workbench evaluator: {name}")
        return self._evaluators[name](request)


def _claim_ledger_marker(request: EvaluationRequest) -> EvaluationResult:
    return EvaluationResult(
        claim_mode=request.claim_mode,
        evaluator_name="claim_ledger",
        claim_flags={"claim_ledger_export_requested": True},
        metrics={"claim_ledger_status": "exporter_runs_after_analysis"},
    )


def default_evaluator_registry() -> EvaluatorRegistry:
    registry = EvaluatorRegistry()
    registry.register("operational", evaluate_operational)
    registry.register("sufficiency", evaluate_sufficiency_shadow)
    registry.register("logloss", evaluate_logloss_shadow)
    registry.register("diagnostic_safety", evaluate_diagnostic_safety)
    registry.register("claim_ledger", _claim_ledger_marker)
    return registry
