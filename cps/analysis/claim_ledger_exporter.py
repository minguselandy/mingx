from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.common import write_json


DENIED_CLAIM_DETAILS = {
    "calibrated_proxy_supported": {
        "blocking_artifact": "metric_bridge_witness.json",
        "claim_boundary_note": "Bridge output is shadow or fail-closed until gates and review pass.",
        "next_repair": "Collect sufficient non-circular bridge rows and pass residual/stability gates.",
        "reason": "No accepted MetricBridgeWitness is available for this run.",
    },
    "vinfo_proxy_supported": {
        "blocking_artifact": "claim_gate_result.json",
        "claim_boundary_note": "Operational utility is not V-information proxy evidence.",
        "next_repair": "Run fixed-model proxy verification only after compatible bridge evidence exists.",
        "reason": "V-information proxy evidence remains shadow mode.",
    },
    "measurement validation": {
        "blocking_artifact": "diagnostic_safety_report.json",
        "claim_boundary_note": "Model-adjudicated or operational labels are not human measurement validation.",
        "next_repair": "Run approved human or external validation with agreement metrics.",
        "reason": "No human labels or kappa artifact is present.",
    },
    "global selector superiority": {
        "blocking_artifact": "superiority_claim_gate.json",
        "claim_boundary_note": "Comparison outputs are scoped and shadow-gated.",
        "next_repair": "Predeclare a multi-benchmark matrix and pass paired tests plus independent review.",
        "reason": "Selector superiority is not accepted by this workbench run.",
    },
}

DEFAULT_PORTFOLIO_CONTROLS = {
    "accepted_evidence_requires_independent_review": True,
    "contamination_policy": "fail_closed_on_contamination_or_unreviewed_source_risk",
    "label_source_policy": "model_adjudicated_or_operational_only_no_measurement_validation",
    "portfolio": "integrated_validation_workbench",
    "route5_unlock_requires": ["accepted_bridge_candidate", "independent_review"],
    "route8_claim_upgrade_requires": ["accepted_evidence_packages_nonempty", "independent_review"],
    "uncertainty_policy": "missing_or_underpowered_evidence_blocks_claim_upgrade",
}


def _write_markdown(path: Path, title: str, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body}", encoding="utf-8")
    return path


def _default_evidence_items() -> list[dict[str, Any]]:
    return [
        {
            "claim_area": "metric_bridge",
            "evidence_class": "shadow",
            "evidence_id": "metric_bridge_witness",
            "reason": "bridge output is shadow or fail-closed",
        },
        {
            "claim_area": "selector_comparison",
            "evidence_class": "shadow",
            "evidence_id": "selector_comparison",
            "reason": "comparison output is shadow-gated",
        },
    ]


def _classify_evidence_items(
    evidence_items: Sequence[Mapping[str, Any]],
    *,
    independent_review_complete: bool,
) -> dict[str, list[dict[str, Any]]]:
    classes: dict[str, list[dict[str, Any]]] = {"shadow": [], "candidate_pending_review": [], "accepted": []}
    for item in evidence_items:
        normalized = dict(item)
        requested_class = str(normalized.get("evidence_class") or "shadow")
        item_reviewed = bool(normalized.get("independent_review_complete") or independent_review_complete)
        if requested_class == "accepted" and not item_reviewed:
            normalized["evidence_class"] = "candidate_pending_review"
            normalized.setdefault("reason_codes", [])
            normalized["reason_codes"] = sorted({*normalized["reason_codes"], "missing_independent_review"})
            classes["candidate_pending_review"].append(normalized)
        elif requested_class == "accepted":
            normalized["evidence_class"] = "accepted"
            normalized["independent_review_complete"] = True
            classes["accepted"].append(normalized)
        elif requested_class == "candidate_pending_review":
            normalized["evidence_class"] = "candidate_pending_review"
            classes["candidate_pending_review"].append(normalized)
        else:
            normalized["evidence_class"] = "shadow"
            classes["shadow"].append(normalized)
    for key in classes:
        classes[key] = sorted(classes[key], key=lambda row: str(row.get("evidence_id") or ""))
    return classes


def _route_gate_status(
    *,
    route_name: str,
    requires: Sequence[str],
    evidence_classes: Mapping[str, Sequence[Mapping[str, Any]]],
    independent_review_complete: bool,
) -> dict[str, Any]:
    accepted_items = list(evidence_classes.get("accepted") or [])
    satisfied: list[str] = []
    if any(
        item.get("accepted_bridge_candidate") is True or str(item.get("claim_area") or "") == "metric_bridge"
        for item in accepted_items
    ):
        satisfied.append("accepted_bridge_candidate")
    if accepted_items:
        satisfied.append("accepted_evidence_packages_nonempty")
    if independent_review_complete and accepted_items:
        satisfied.append("independent_review")
    missing = [requirement for requirement in requires if requirement not in satisfied]
    return {
        "locked": bool(missing),
        "reason_codes": [f"missing_{requirement}" for requirement in missing],
        "requires": list(requires),
        "route": route_name,
        "satisfied": satisfied,
    }


def export_claim_ledger(
    *,
    output_dir: str | Path,
    run_id: str,
    accepted_claims: Sequence[str],
    bridge_result: Mapping[str, Any],
    comparison_result: Mapping[str, Any],
    independent_review_complete: bool = False,
    evidence_items: Sequence[Mapping[str, Any]] | None = None,
    portfolio_controls: Mapping[str, Any] | None = None,
) -> dict[str, Path]:
    out = Path(output_dir)
    denied = dict(DENIED_CLAIM_DETAILS)
    controls = {**DEFAULT_PORTFOLIO_CONTROLS, **dict(portfolio_controls or {})}
    classes = _classify_evidence_items(
        evidence_items or _default_evidence_items(),
        independent_review_complete=independent_review_complete,
    )
    route_gates = {
        "route5": _route_gate_status(
            route_name="route5",
            requires=controls["route5_unlock_requires"],
            evidence_classes=classes,
            independent_review_complete=independent_review_complete,
        ),
        "route8": _route_gate_status(
            route_name="route8",
            requires=controls["route8_claim_upgrade_requires"],
            evidence_classes=classes,
            independent_review_complete=independent_review_complete,
        ),
    }
    ledger = {
        "accepted_claims": list(accepted_claims),
        "bridge_gate": dict(bridge_result.get("claim_gate_result") or {}),
        "claim_mode": "shadow",
        "claim_status": "operational_utility_only; no_claim_upgrade",
        "comparison_gate": dict(comparison_result.get("superiority_claim_gate") or {}),
        "denied_claims": denied,
        "evidence_classes": classes,
        "independent_review_complete": independent_review_complete,
        "measurement_validation_claim": False,
        "portfolio_controls": controls,
        "route_gates": route_gates,
        "run_id": run_id,
        "selector_superiority_claimed": False,
        "schema_version": "workbench_claim_ledger_v1",
    }
    paths = {
        "blocked_claims": out / "blocked_claims.md",
        "claim_ledger": out / "claim_ledger.json",
        "next_repairs": out / "next_repairs.md",
        "paper_tables": out / "paper_tables.md",
    }
    write_json(paths["claim_ledger"], ledger)
    blocked_lines = ["No claim upgrade is accepted in this run.", ""]
    for claim, detail in denied.items():
        blocked_lines.append(f"- `{claim}`: {detail['reason']}")
    repairs_lines = ["Each blocked claim includes a next repair.", ""]
    for claim, detail in denied.items():
        repairs_lines.append(f"- `{claim}` next repair: {detail['next_repair']}")
    _write_markdown(paths["blocked_claims"], "Workbench Blocked Claims", "\n".join(blocked_lines) + "\n")
    _write_markdown(paths["next_repairs"], "Workbench Next Repairs", "\n".join(repairs_lines) + "\n")
    _write_markdown(
        paths["paper_tables"],
        "Workbench Paper Tables",
        "No paper-facing claim table is exportable beyond scoped operational smoke status.\n",
    )
    json.dumps(ledger, sort_keys=True)
    return paths
