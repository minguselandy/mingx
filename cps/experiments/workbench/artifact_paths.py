from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkbenchArtifactPaths:
    output_dir: Path
    manifest: Path
    candidate_pool_manifest: Path
    traces: Path
    bridge_fit_summary: Path
    control_results: Path
    metric_bridge_witness: Path
    claim_gate_result: Path
    comparison_summary: Path
    statistical_tests: Path
    diagnostic_safety_report: Path
    superiority_claim_gate: Path
    claim_ledger: Path
    paper_tables: Path
    blocked_claims: Path
    next_repairs: Path
    blocked_report: Path

    @classmethod
    def from_output_dir(cls, output_dir: str | Path) -> "WorkbenchArtifactPaths":
        out = Path(output_dir)
        return cls(
            blocked_claims=out / "blocked_claims.md",
            blocked_report=out / "blocked_report.json",
            bridge_fit_summary=out / "bridge_fit_summary.json",
            candidate_pool_manifest=out / "candidate_pool_manifest.json",
            claim_gate_result=out / "claim_gate_result.json",
            claim_ledger=out / "claim_ledger.json",
            comparison_summary=out / "comparison_summary.csv",
            control_results=out / "control_results.json",
            diagnostic_safety_report=out / "diagnostic_safety_report.json",
            manifest=out / "manifest.json",
            metric_bridge_witness=out / "metric_bridge_witness.json",
            next_repairs=out / "next_repairs.md",
            output_dir=out,
            paper_tables=out / "paper_tables.md",
            statistical_tests=out / "statistical_tests.json",
            superiority_claim_gate=out / "superiority_claim_gate.json",
            traces=out / "workbench_traces.jsonl",
        )

    def to_manifest(self) -> dict[str, str]:
        return {
            field: getattr(self, field).relative_to(self.output_dir).as_posix()
            for field in (
                "blocked_claims",
                "blocked_report",
                "bridge_fit_summary",
                "candidate_pool_manifest",
                "claim_gate_result",
                "claim_ledger",
                "comparison_summary",
                "control_results",
                "diagnostic_safety_report",
                "manifest",
                "metric_bridge_witness",
                "next_repairs",
                "paper_tables",
                "statistical_tests",
                "superiority_claim_gate",
                "traces",
            )
        }
