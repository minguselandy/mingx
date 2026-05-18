from __future__ import annotations

from cps.benchmarks.common import packet_id
from cps.benchmarks.common import token_cost
from cps.evaluators.workbench_types import EvaluationRequest
from cps.evaluators.workbench_types import EvaluationResult


def evaluate_operational(request: EvaluationRequest) -> EvaluationResult:
    gold_ids = {
        packet_id(packet)
        for packet in request.all_packets
        if packet.get("gold_support_label") == "gold_supporting" and packet_id(packet)
    }
    selected_ids = {packet_id(packet) for packet in request.selected_packets if packet_id(packet)}
    selected_tokens = sum(token_cost(packet) for packet in request.selected_packets)
    target_label = str(request.target.get("label") or "")
    context = "\n".join(str(packet.get("content") or "") for packet in request.selected_packets).casefold()
    recall = len(gold_ids & selected_ids) / len(gold_ids) if gold_ids else 0.0
    return EvaluationResult(
        claim_mode=request.claim_mode,
        evaluator_name="operational",
        claim_flags={
            "measurement_validated": False,
            "paper_evidence": False,
            "shadow_measurement_candidate": request.claim_mode == "shadow",
        },
        metrics={
            "answer_available_if_present": bool(target_label and target_label.casefold() in context),
            "gold_support_packets_selected_count": len(gold_ids & selected_ids),
            "selected_tokens": selected_tokens,
            "supporting_fact_recall_at_budget": round(recall, 6),
        },
    )
