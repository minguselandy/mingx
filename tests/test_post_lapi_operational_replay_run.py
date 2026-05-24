from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.run_post_lapi_operational_replay_expansion import APPROVAL_TOKEN
from scripts.run_post_lapi_operational_replay_expansion import run_post6_operational_replay


def _json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_post6_operational_replay_writes_claim_safe_matched_budget_outputs(workspace_tmp_dir: Path) -> None:
    output_dir = workspace_tmp_dir / "post6"
    doc_path = workspace_tmp_dir / "POST-LAPI-operational-replay-expansion.md"
    table_path = workspace_tmp_dir / "post-lapi-operational-replay-table.md"

    result = run_post6_operational_replay(
        approval=APPROVAL_TOKEN,
        doc_path=doc_path,
        output_dir=output_dir,
        repo_root=Path.cwd(),
        table_path=table_path,
    )

    assert result["terminal_status"] == "DONE"
    assert result["live_api_call_count"] == 0
    assert result["raw_response_stored"] is False

    required = {
        "aggregate_report.json",
        "candidate_pool_manifest.json",
        "claim_gate_report.json",
        "claim_ledger.json",
        "comparison_summary.csv",
        "cost_latency_ledger.json",
        "paired_comparisons.json",
        "replay_records.jsonl",
        "run_manifest.json",
    }
    assert required == {path.name for path in output_dir.iterdir() if path.is_file()}

    manifest = _json(output_dir / "run_manifest.json")
    aggregate = _json(output_dir / "aggregate_report.json")
    claim = _json(output_dir / "claim_gate_report.json")
    records = _jsonl(output_dir / "replay_records.jsonl")
    summary_rows = _csv(output_dir / "comparison_summary.csv")

    assert manifest["approval_gate_token_verified"] is True
    assert manifest["live_api_call_count"] == 0
    assert manifest["matched_budget_controls"]["hold_budget_fixed"] is True
    assert manifest["matched_budget_controls"]["compare_only_with_matched_candidate_pool"] is True
    assert manifest["route_5_locked"] is True
    assert manifest["route_8_locked"] is True
    assert manifest["claim_upgrade_introduced"] is False
    assert aggregate["final_gate_status"] == "post6_operational_replay_completed"
    assert aggregate["oracle_status"] == "non_deployable_upper_bound"
    assert aggregate["selector_superiority_claimed"] is False
    assert aggregate["metric_bridge_support"] is False
    assert aggregate["measurement_validation_claim"] is False
    assert claim["claim_upgrade_introduced"] is False
    assert claim["route_5_locked"] is True
    assert claim["route_8_locked"] is True

    assert records
    assert all(record["raw_response_stored"] is False for record in records)
    assert all(record["claim_level"] == "operational_utility_only/no_claim_upgrade" for record in records)
    assert all(record["matched_budget"] is True for record in records)
    assert all("materialized_context" not in record for record in records)
    assert all("text" not in json.dumps(record, sort_keys=True).lower() for record in records)
    oracle_records = [record for record in records if record["selector_name"] == "gold_support_oracle_upper_bound"]
    assert oracle_records
    assert all(record["deployable_status"] == "non_deployable_upper_bound" for record in oracle_records)

    assert summary_rows
    assert any(row["selector_name"] == "gold_support_oracle_upper_bound" for row in summary_rows)
    assert "non_deployable_upper_bound" in table_path.read_text(encoding="utf-8")
    doc_text = doc_path.read_text(encoding="utf-8")
    assert "Live API calls run: `0`" in doc_text
    assert "selector superiority" in doc_text.lower()
