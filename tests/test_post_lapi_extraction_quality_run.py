from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.run_post_lapi_extraction_quality_audit import APPROVAL_TOKEN
from scripts.run_post_lapi_extraction_quality_audit import run_post7_extraction_quality_audit


def _json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class FakePost7Client:
    model_id = "fake-post7-judge"
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def classify(self, *, messages, timeout_seconds: int) -> dict:
        prompt_text = "\n".join(message["content"] for message in messages)
        if "qualifier_heavy" in prompt_text:
            label = "lost_qualifier"
        elif "temporal_scope" in prompt_text:
            label = "temporal_scope_error"
        elif "high_provenance_value" in prompt_text:
            label = "provenance_loss"
        elif "adversarial" in prompt_text:
            label = "selector_impact"
        elif "contradictory" in prompt_text:
            label = "captured_core_materially_changed"
        else:
            label = "captured_core_preserved"
        return {
            "input_token_count": 111,
            "latency_ms": 7,
            "model_snapshot": "fake-post7-judge-2026-05-24",
            "output_token_count": 17,
            "parse_status": "parsed",
            "parsed": {
                "confidence_bucket": "medium",
                "label": label,
                "provenance_loss": label == "provenance_loss",
                "qualifier_loss": label == "lost_qualifier",
                "selector_impact": label == "selector_impact",
                "temporal_scope_error": label == "temporal_scope_error",
                "value_weight": 1.25,
            },
            "usage_actual": False,
        }


def test_post7_extraction_quality_audit_writes_claim_safe_outputs(workspace_tmp_dir: Path) -> None:
    output_dir = workspace_tmp_dir / "post7"
    doc_path = workspace_tmp_dir / "POST-LAPI-extraction-quality-audit.md"
    table_path = workspace_tmp_dir / "post-lapi-extraction-quality-table.md"

    result = run_post7_extraction_quality_audit(
        approval=APPROVAL_TOKEN,
        client=FakePost7Client(),
        doc_path=doc_path,
        max_examples=100,
        output_dir=output_dir,
        repo_root=Path.cwd(),
        table_path=table_path,
    )

    assert result["terminal_status"] == "DONE"
    assert result["live_api_call_count"] == 100
    assert result["raw_response_stored"] is False
    assert result["claim_upgrade_introduced"] is False
    assert result["route_5_locked"] is True
    assert result["route_8_locked"] is True

    required = {
        "aggregate_report.json",
        "audit_records.jsonl",
        "claim_gate_report.json",
        "claim_ledger.json",
        "cost_latency_ledger.json",
        "run_manifest.json",
        "stratum_summary.csv",
        "stratum_summary.json",
    }
    assert required == {path.name for path in output_dir.iterdir() if path.is_file()}

    records = _jsonl(output_dir / "audit_records.jsonl")
    aggregate = _json(output_dir / "aggregate_report.json")
    manifest = _json(output_dir / "run_manifest.json")
    claim = _json(output_dir / "claim_gate_report.json")
    summary_rows = _csv(output_dir / "stratum_summary.csv")

    assert len(records) == 100
    assert len(summary_rows) == 10
    assert manifest["approval_gate_token_verified"] is True
    assert manifest["live_api_call_count"] == 100
    assert manifest["raw_response_stored"] is False
    assert manifest["route_5_locked"] is True
    assert manifest["route_8_locked"] is True
    assert aggregate["final_gate_status"] == "post7_extraction_quality_audit_completed"
    assert aggregate["candidate_operational_evidence_only"] is True
    assert aggregate["human_validated_extraction_measurement"] is False
    assert aggregate["measurement_validation_claim"] is False
    assert aggregate["metric_bridge_support"] is False
    assert aggregate["value_weighted_loss_proxy"]["interpretation"] == "candidate_operational_evidence_only"
    assert claim["claim_upgrade_introduced"] is False
    assert claim["route_5_locked"] is True
    assert claim["route_8_locked"] is True

    for record in records:
        assert record["live_api_call_performed"] is True
        assert record["raw_response_stored"] is False
        assert record["label_source_kind"] == "model_adjudicated"
        assert record["claim_level"] == "operational_utility_only/no_claim_upgrade"
        assert record["audit_diagnostic_only"] is True
        serialized = json.dumps(record, sort_keys=True).lower()
        assert "raw_api_response" not in serialized
        assert "raw_response_body" not in serialized
        assert "raw_response_payload" not in serialized
        assert "source_text" not in record
        assert "prompt_text" not in record
        assert "response_text" not in record

    doc_text = doc_path.read_text(encoding="utf-8").lower()
    table_text = table_path.read_text(encoding="utf-8").lower()
    assert "model-adjudicated candidate operational extraction-risk evidence only" in doc_text
    assert "raw api responses stored: `false`" in doc_text
    assert "value-weighted loss proxy" in doc_text
    assert "route 5 locked" in table_text
    assert "route 8 locked" in table_text
