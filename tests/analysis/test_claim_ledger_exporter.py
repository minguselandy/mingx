from __future__ import annotations

import json

from cps.analysis.claim_ledger_exporter import export_claim_ledger


def test_claim_ledger_exporter_records_denied_claim_reasons(workspace_tmp_dir):
    result = export_claim_ledger(
        output_dir=workspace_tmp_dir,
        run_id="hotpotqa_smoke",
        accepted_claims=["scoped_operational_improvement"],
        bridge_result={
            "claim_gate_result": {
                "calibrated_proxy_supported": False,
                "vinfo_proxy_supported": False,
                "reason_codes": ["bridge_shadow_mode"],
            }
        },
        comparison_result={
            "superiority_claim_gate": {
                "selector_superiority_claimed": False,
                "global_selector_superiority": False,
                "reason_codes": ["superiority_shadow_mode"],
            }
        },
    )

    ledger = json.loads((workspace_tmp_dir / "claim_ledger.json").read_text(encoding="utf-8"))

    assert result["claim_ledger"].name == "claim_ledger.json"
    assert ledger["claim_status"] == "operational_utility_only; no_claim_upgrade"
    assert ledger["accepted_claims"] == ["scoped_operational_improvement"]
    assert ledger["denied_claims"]["calibrated_proxy_supported"]["blocking_artifact"] == "metric_bridge_witness.json"
    assert "No claim upgrade" in (workspace_tmp_dir / "blocked_claims.md").read_text(encoding="utf-8")
    assert "next repair" in (workspace_tmp_dir / "next_repairs.md").read_text(encoding="utf-8")
