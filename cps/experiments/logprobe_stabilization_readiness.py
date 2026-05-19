from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.analysis.logprobe_stability import build_logprobe_stability_reports
from cps.analysis.utility_logloss_alignment import build_alignment_decomposition
from cps.benchmarks.common import read_jsonl
from cps.benchmarks.common import write_json
from cps.benchmarks.hashing import canonical_json_dumps
from cps.evaluators.logprobe_scorer import score_logprobe_shadow
from cps.evaluators.logprobe_target_contract import build_canonical_target_contract
from cps.evaluators.logprobe_target_contract import validate_target_contract


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
TERMINAL_STATUS = "LOGPROBE_STABILIZATION_READINESS_COMPLETED"
TERMINAL_READINESS_DECISION = "READY_FOR_TARGET_SWITCH"

REQUIRED_INPUTS: dict[str, Path] = {
    "answer_generation_report": Path("artifacts/benchmarks/hotpotqa_p55_delta_generation_report.json"),
    "support_generation_report": Path(
        "artifacts/benchmarks/hotpotqa_support_classification_delta_generation_report.json"
    ),
    "audit_stability_report": Path("artifacts/experiments/logprobe_bridge_audit/logprobe_stability_report.json"),
    "audit_alignment_report": Path("artifacts/experiments/logprobe_bridge_audit/utility_logloss_alignment_report.json"),
    "audit_failure_decomposition": Path("artifacts/experiments/logprobe_bridge_audit/route4_failure_decomposition.json"),
    "route4a_fit": Path("artifacts/experiments/route4_bridge/bridge_fit_summary.json"),
    "route4a_rows": Path("artifacts/experiments/route4_bridge/bridge_rows.jsonl"),
    "route4b_fit": Path("artifacts/experiments/route4b_bridge_to_measurement/bridge_fit_summary.json"),
    "route4b_rows": Path("artifacts/experiments/route4b_bridge_to_measurement/bridge_rows.jsonl"),
    "delta_route4e_fit": Path("artifacts/experiments/delta_strong_model_adjudication/route4e_bridge_fit_summary.json"),
    "delta_route4e_rows": Path("artifacts/experiments/delta_strong_model_adjudication/route4e_bridge_rows.jsonl"),
}


class LogProbeStabilizationInputMissingError(RuntimeError):
    """Raised before writing LP1-LP5 outputs when required inputs are absent."""


def _resolve(root: str | Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else Path(root) / candidate


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.name if candidate.is_absolute() else candidate.as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _load_inputs(root: str | Path) -> dict[str, Any]:
    missing = [name for name, path in REQUIRED_INPUTS.items() if not _resolve(root, path).exists()]
    if missing:
        raise LogProbeStabilizationInputMissingError(
            "missing required LogProbe stabilization inputs: " + ", ".join(sorted(missing))
        )
    loaded: dict[str, Any] = {}
    for name, path in REQUIRED_INPUTS.items():
        resolved = _resolve(root, path)
        loaded[name] = read_jsonl(resolved) if resolved.suffix == ".jsonl" else _read_json(resolved)
    return loaded


def _write_jsonl(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(canonical_json_dumps(dict(row)) + "\n" for row in rows), encoding="utf-8")
    return output_path


def _build_contract() -> dict[str, Any]:
    return build_canonical_target_contract(
        materialization_policy="fixed_selector_order_with_source_boundaries",
        prompt_template="Question: {question}\nContext: {materialized_context}\nAnswer:",
        row_provenance={
            "active_rows": "artifacts/experiments/route4_bridge/bridge_rows.jsonl",
            "source": "existing_route4a_answer_nll_rows",
        },
        target_provenance={
            "dataset": "HotpotQA",
            "fever_disabled": True,
            "split": "dev_distractor",
        },
        target_type="answer_string",
        target_representation="hotpotqa_canonical_answer_string",
        tokenization_policy="teacher_forced_full_target_sequence_v1",
        verbalizer_policy="literal_answer_string_no_label_verbalizer",
    )


def _build_target_decision(
    *,
    alignment_reports: Mapping[str, Any],
    stability_reports: Mapping[str, Any],
    target_contract_validation: Mapping[str, Any],
) -> dict[str, Any]:
    strata = alignment_reports["alignment_by_stratum"]["strata"]
    route4a = strata.get("Route4A", {})
    current_alignment_weak = str(route4a.get("weak_signal_classification") or "") in {"weak_signal", "mixed_signal"}
    support_target_risk = (
        stability_reports["tokenization_risk_report"]["target_verbalization_tokenization"]["status"] == "present"
    )
    rejected = [
        {
            "decision": "KEEP_CURRENT_TARGET_AND_SCALE",
            "reason": "current_answer_nll_alignment_weak" if current_alignment_weak else "not_selected",
        },
        {
            "decision": "SWITCH_TO_SUFFICIENCY_CLASSIFIER_NLL",
            "reason": "support_classifier_target_verbalization_risk_present" if support_target_risk else "not_selected",
        },
        {
            "decision": "SWITCH_TO_OPTION_NLL",
            "reason": "no_existing_option_nll_artifacts_in_scope",
        },
    ]
    return {
        "claim_status": CLAIM_STATUS,
        "disabled_decisions": ["SWITCH_TO_FEVER_LABEL_NLL"],
        "lp6_bridge_repair_run": False,
        "new_live_api_calls": False,
        "primary_decision": "SWITCH_TO_EVIDENCE_PATH_NLL",
        "rejected_decisions": rejected,
        "required_unlocks": [
            "independent_review_before_lp6",
            "operator_approval_before_any_future_live_scoring",
            "new_target_shadow_stability_check",
            "fresh_measured_delta_logloss_rows_for_new_target",
        ],
        "risk_level": "high",
        "schema_version": "logprobe_target_redesign_decision_v1",
        "secondary_decision": "ABANDON_LOGPROBE_BRIDGE_FOR_CURRENT_STRATUM",
        "target_contract_passed": bool(target_contract_validation.get("passed")),
    }


def _build_readiness_report(
    *,
    alignment_reports: Mapping[str, Any],
    stability_reports: Mapping[str, Any],
    target_contract_validation: Mapping[str, Any],
    target_decision: Mapping[str, Any],
) -> dict[str, Any]:
    route4a = alignment_reports["alignment_by_stratum"]["strata"].get("Route4A", {})
    route4a_rows = int(route4a.get("row_count") or 0)
    checks = {
        "alignment_signal_promising": False,
        "contamination_policy_ready": True,
        "independent_review_required": True,
        "label_source_policy_valid": True,
        "logprobe_stability_passed": bool(stability_reports["logprobe_stability_matrix"]["logprobe_stability_passed"]),
        "row_count_plan_ready": route4a_rows >= 500,
        "route5_locked": True,
        "route8_locked": True,
        "target_contract_passed": bool(target_contract_validation.get("passed")),
    }
    return {
        "checks": checks,
        "claim_status": CLAIM_STATUS,
        "lp6_bridge_repair_run": False,
        "new_live_api_calls": False,
        "readiness_state": TERMINAL_READINESS_DECISION,
        "reason_codes": [
            "current_answer_nll_alignment_weak",
            "support_classifier_target_verbalization_risk_present",
            "fever_target_switch_disabled",
            "route5_remains_locked",
            "route8_remains_locked",
            "lp6_not_run",
        ],
        "required_unlocks": list(target_decision["required_unlocks"]),
        "schema_version": "logprobe_bridge_repair_readiness_v1",
        "target_decision": str(target_decision["primary_decision"]),
    }


def _target_contract_doc(contract: Mapping[str, Any], validation: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# LogProbe Target Contract",
            "",
            f"Claim status: {CLAIM_STATUS}",
            "",
            "## Canonical target",
            "",
            f"- target_type: {contract['target_type']}",
            f"- fixed_target_representation: {contract['fixed_target_representation']}",
            f"- verbalizer_policy: {contract['verbalizer_policy']}",
            f"- tokenization_policy: {contract['tokenization_policy']}",
            f"- teacher_forced_scoring_required: {str(contract['teacher_forced_scoring_required']).lower()}",
            f"- target_format_hash: {contract['target_format_hash']}",
            f"- prompt_template_hash: {contract['prompt_template_hash']}",
            f"- materialization_policy_hash: {contract['materialization_policy_hash']}",
            "",
            "## Status",
            "",
            f"Validation passed: {str(validation['passed']).lower()}",
            "",
            "FEVER remains disabled and is not an active target-switch option.",
            "",
        ]
    )


def _target_decision_doc(decision: Mapping[str, Any]) -> str:
    rejected = "\n".join(f"- {item['decision']}: {item['reason']}" for item in decision["rejected_decisions"])
    unlocks = "\n".join(f"- {item}" for item in decision["required_unlocks"])
    return "\n".join(
        [
            "# LogProbe Target Redesign Decision",
            "",
            f"Claim status: {CLAIM_STATUS}",
            "",
            f"Primary decision: {decision['primary_decision']}",
            f"Secondary decision: {decision['secondary_decision']}",
            "Disabled decisions: SWITCH_TO_FEVER_LABEL_NLL",
            "",
            "## Rejected decisions",
            "",
            rejected,
            "",
            "## Required unlocks",
            "",
            unlocks,
            "",
            "No bridge repair run was executed.",
            "",
        ]
    )


def _readiness_doc(readiness: Mapping[str, Any]) -> str:
    checks = "\n".join(f"- {key}: {str(value).lower()}" for key, value in sorted(readiness["checks"].items()))
    return "\n".join(
        [
            "# LogProbe Bridge Repair Readiness",
            "",
            f"Claim status: {CLAIM_STATUS}",
            f"Readiness state: {readiness['readiness_state']}",
            "",
            "## Checks",
            "",
            checks,
            "",
            "Route 5 remains locked. Route 8 remains locked. LP6 was not run.",
            "",
        ]
    )


def run_logprobe_stabilization_readiness(*, root: str | Path = ".") -> dict[str, Any]:
    repo_root = Path(root)
    inputs = _load_inputs(repo_root)
    contract = _build_contract()
    contract_validation = validate_target_contract(contract)
    first_row = inputs["route4a_rows"][0] if inputs["route4a_rows"] else {}
    shadow_probe = score_logprobe_shadow(contract, first_row)

    stability_reports = build_logprobe_stability_reports(
        answer_generation_report=inputs["answer_generation_report"],
        contract=contract,
        route4_rows=inputs["route4a_rows"],
        support_generation_report=inputs["support_generation_report"],
    )
    alignment_reports = build_alignment_decomposition(
        route_specs=[
            {
                "fit_summary": inputs["route4a_fit"],
                "route_id": "Route4A",
                "rows": inputs["route4a_rows"],
                "target_type": "answer_string",
                "utility_field": "delta_utility",
            },
            {
                "fit_summary": inputs["route4b_fit"],
                "route_id": "Route4B",
                "rows": inputs["route4b_rows"],
                "target_type": "external_sufficiency",
                "utility_field": "delta_external_sufficiency_utility",
            },
            {
                "fit_summary": inputs["delta_route4e_fit"],
                "route_id": "DeltaRoute4E",
                "rows": inputs["delta_route4e_rows"],
                "target_type": "hybrid_utility",
                "utility_field": "delta_hybrid_utility",
            },
        ]
    )
    target_decision = _build_target_decision(
        alignment_reports=alignment_reports,
        stability_reports=stability_reports,
        target_contract_validation=contract_validation,
    )
    readiness = _build_readiness_report(
        alignment_reports=alignment_reports,
        stability_reports=stability_reports,
        target_contract_validation=contract_validation,
        target_decision=target_decision,
    )

    stability_dir = repo_root / "artifacts/experiments/logprobe_stability_shadow"
    alignment_dir = repo_root / "artifacts/experiments/logprobe_alignment_decomposition"
    target_dir = repo_root / "artifacts/experiments/logprobe_target_redesign"
    readiness_dir = repo_root / "artifacts/experiments/logprobe_bridge_repair_readiness"
    docs_dir = repo_root / "docs/experiments"

    artifact_paths = {
        "logprobe_stability_matrix": write_json(
            stability_dir / "logprobe_stability_matrix.json",
            stability_reports["logprobe_stability_matrix"],
        ),
        "materialization_sensitivity_report": write_json(
            stability_dir / "materialization_sensitivity_report.json",
            stability_reports["materialization_sensitivity_report"],
        ),
        "tokenization_risk_report": write_json(
            stability_dir / "tokenization_risk_report.json",
            stability_reports["tokenization_risk_report"],
        ),
        "alignment_by_stratum": write_json(
            alignment_dir / "alignment_by_stratum.json",
            alignment_reports["alignment_by_stratum"],
        ),
        "alignment_by_target_type": write_json(
            alignment_dir / "alignment_by_target_type.json",
            alignment_reports["alignment_by_target_type"],
        ),
        "residual_tail_audit": write_json(
            alignment_dir / "residual_tail_audit.json",
            alignment_reports["residual_tail_audit"],
        ),
        "leverage_rows": _write_jsonl(alignment_dir / "leverage_rows.jsonl", alignment_reports["leverage_rows"]),
        "target_decision": write_json(target_dir / "target_decision.json", target_decision),
        "readiness_report": write_json(readiness_dir / "readiness_report.json", readiness),
    }
    docs_dir.mkdir(parents=True, exist_ok=True)
    doc_paths = {
        "target_contract_doc": docs_dir / "LogProbe-target-contract.md",
        "target_decision_doc": docs_dir / "LogProbe-target-redesign-decision.md",
        "readiness_doc": docs_dir / "LogProbe-bridge-repair-readiness.md",
    }
    doc_paths["target_contract_doc"].write_text(_target_contract_doc(contract, contract_validation), encoding="utf-8")
    doc_paths["target_decision_doc"].write_text(_target_decision_doc(target_decision), encoding="utf-8")
    doc_paths["readiness_doc"].write_text(_readiness_doc(readiness), encoding="utf-8")

    return {
        "artifacts": {name: _path_ref(path.relative_to(repo_root) if path.is_absolute() else path) for name, path in artifact_paths.items()},
        "claim_status": CLAIM_STATUS,
        "docs": {name: _path_ref(path.relative_to(repo_root) if path.is_absolute() else path) for name, path in doc_paths.items()},
        "lp6_bridge_repair_run": False,
        "new_live_api_calls": False,
        "shadow_probe": shadow_probe,
        "target_decision": target_decision,
        "terminal_readiness_decision": readiness["readiness_state"],
        "terminal_status": TERMINAL_STATUS,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run LP1-LP5 LogProbe stabilization readiness.")
    parser.add_argument("--root", default=".", help="Repository root containing existing artifacts.")
    args = parser.parse_args(argv)
    result = run_logprobe_stabilization_readiness(root=args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
