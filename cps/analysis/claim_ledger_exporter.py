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


def _write_markdown(path: Path, title: str, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body}", encoding="utf-8")
    return path


def export_claim_ledger(
    *,
    output_dir: str | Path,
    run_id: str,
    accepted_claims: Sequence[str],
    bridge_result: Mapping[str, Any],
    comparison_result: Mapping[str, Any],
) -> dict[str, Path]:
    out = Path(output_dir)
    denied = dict(DENIED_CLAIM_DETAILS)
    ledger = {
        "accepted_claims": list(accepted_claims),
        "bridge_gate": dict(bridge_result.get("claim_gate_result") or {}),
        "claim_mode": "shadow",
        "claim_status": "operational_utility_only; no_claim_upgrade",
        "comparison_gate": dict(comparison_result.get("superiority_claim_gate") or {}),
        "denied_claims": denied,
        "run_id": run_id,
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
