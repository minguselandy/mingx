from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.hashing import canonical_json_dumps
from cps.benchmarks.schemas import write_json
from cps.experiments.route6a_measurement_pilot import DEFAULT_BRIDGE_ROWS_PATH
from cps.experiments.route6a_measurement_pilot import DEFAULT_CANDIDATE_POOLS_PATH
from cps.experiments.route6a_measurement_pilot import DEFAULT_LOCAL_JUDGE_CONFIG
from cps.experiments.route6a_measurement_pilot import run_route6a_measurement_pilot


ROUTE6B_ID = "route6b_measurement_scaleup"
ROUTE6B_PHASE_ID = "route6b_measurement_scaleup"
DEFAULT_OUTPUT_DIR = Path("artifacts/experiments/route6b_measurement_scaleup")
DEFAULT_REPORT_MD = Path("docs/experiments/Route6B-measurement-scaleup-report.md")
DEFAULT_SAMPLE_SIZE = 300
DEFAULT_MIN_ACCEPTED_LABELS = 150
CLAIM_STATUS = "no_claim_upgrade"


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate.name
    return candidate.as_posix()


def _read_json(path: str | Path) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.exists() or not resolved.is_file():
        return {}
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _terminal_status(
    *,
    route6a_result: Mapping[str, Any],
    accepted_model_adjudicated_count: int,
    min_accepted_labels: int,
) -> tuple[str, list[str]]:
    status = str(route6a_result.get("status") or "")
    reason_codes = [str(code) for code in route6a_result.get("reason_codes", []) if str(code)]
    if status == "model_adjudication_completed" and accepted_model_adjudicated_count >= min_accepted_labels:
        return "measurement_candidate_ready", reason_codes
    if status == "model_adjudication_completed":
        return (
            "failed_closed_measurement_quality",
            [*reason_codes, "accepted_model_adjudicated_labels_below_minimum"],
        )
    if status == "blocked_no_accepted_model_adjudicated_labels":
        return (
            "failed_closed_measurement_quality",
            [*reason_codes, "no_accepted_model_adjudicated_labels"],
        )
    return "irrecoverably_blocked", reason_codes or ["route6b_scaleup_could_not_run"]


def _write_route6b_report(path: str | Path, *, readiness: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    reason_codes = "\n".join(f"- `{code}`" for code in readiness["reason_codes"])
    output.write_text(
        "\n".join(
            [
                "# Route 6B Measurement Scale-up Report",
                "",
                f"Status: `{readiness['status']}`",
                "Claim status: `no_claim_upgrade`",
                "",
                "## Decision",
                "",
                "Route 6B reuses the frozen Route 6A external sufficiency rubric and "
                "normalization path at a larger model-adjudicated sample size.",
                "",
                "## Scale-up Counts",
                "",
                f"- Target model-adjudicated pairs: `{readiness['target_model_adjudicated_pairs']}`",
                f"- Context-pair sample count: `{readiness['context_pair_sample_count']}`",
                f"- Accepted model-adjudicated labels: `{readiness['accepted_model_adjudicated_count']}`",
                f"- Minimum accepted labels: `{readiness['minimum_accepted_labels']}`",
                "",
                "## Claim Boundary",
                "",
                "- Model-adjudicated labels are not human labels.",
                "- Measurement validation, human-label validation, and kappa remain denied.",
                "- `operational_utility_only/no_claim_upgrade` remains active.",
                "",
                "## Storage Boundary",
                "",
                f"- Live API used: `{str(readiness['live_api_used']).lower()}`",
                "- Raw API responses stored: `false`",
                "- Operator inputs written: `false`",
                "",
                "## Reason Codes",
                "",
                reason_codes or "- `none`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return output


def run_route6b_measurement_scaleup(
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    bridge_rows_path: str | Path = DEFAULT_BRIDGE_ROWS_PATH,
    candidate_pools_path: str | Path = DEFAULT_CANDIDATE_POOLS_PATH,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    min_accepted_labels: int = DEFAULT_MIN_ACCEPTED_LABELS,
    run_live_adjudication: bool = False,
    judge_config_path: str | Path | None = DEFAULT_LOCAL_JUDGE_CONFIG,
    report_md_path: str | Path = DEFAULT_REPORT_MD,
    client: Any | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    route6a_result = run_route6a_measurement_pilot(
        output_dir=output_path,
        bridge_rows_path=bridge_rows_path,
        candidate_pools_path=candidate_pools_path,
        sample_size=sample_size,
        run_live_adjudication=run_live_adjudication,
        judge_config_path=judge_config_path,
        report_md_path=report_md_path,
        client=client,
        env=env,
    )
    adjudication_report_path = output_path / "adjudication_report.json"
    adjudication_report = _read_json(adjudication_report_path)
    accepted = int(adjudication_report.get("accepted_model_adjudicated_count") or 0)
    normalized = int(adjudication_report.get("normalized_label_count") or 0)
    terminal_status, reason_codes = _terminal_status(
        route6a_result=route6a_result,
        accepted_model_adjudicated_count=accepted,
        min_accepted_labels=min_accepted_labels,
    )
    readiness = {
        "accepted_model_adjudicated_count": accepted,
        "artifact_type": "Route6BMeasurementScaleupReadinessReport",
        "claim_status": CLAIM_STATUS,
        "context_pair_sample_count": int(route6a_result.get("context_pair_sample_count") or 0),
        "counts_as_human_labels": False,
        "human_annotation_status": "blocked_human_annotation_required",
        "human_human_kappa_present": False,
        "human_labels_present": False,
        "live_api_used": bool(route6a_result.get("live_api_used")),
        "measurement_validation_candidate_allowed": False,
        "minimum_accepted_labels": min_accepted_labels,
        "normalized_label_count": normalized,
        "raw_api_responses_stored": False,
        "reason_codes": reason_codes,
        "route6a_compatibility_status": str(route6a_result.get("status") or ""),
        "route_id": ROUTE6B_ID,
        "phase_id": ROUTE6B_PHASE_ID,
        "schema_version": "route6b_measurement_scaleup_readiness_v1",
        "status": terminal_status,
        "target_model_adjudicated_pairs": sample_size,
    }
    scaleup_report = {
        "accepted_model_adjudicated_count": accepted,
        "adjudication_report_path": _path_ref(adjudication_report_path),
        "claim_status": CLAIM_STATUS,
        "context_pair_sample_path": _path_ref(output_path / "context_pair_sample.jsonl"),
        "minimum_accepted_labels": min_accepted_labels,
        "model_adjudicated_labels_path": _path_ref(output_path / "model_adjudicated_labels.jsonl"),
        "raw_api_responses_stored": False,
        "route_id": ROUTE6B_ID,
        "schema_version": "route6b_measurement_scaleup_report_v1",
        "terminal_status": terminal_status,
    }

    write_json(output_path / "readiness_report.json", readiness)
    write_json(output_path / "scaleup_report.json", scaleup_report)
    _write_route6b_report(report_md_path, readiness=readiness)

    result = dict(readiness)
    result["artifacts"] = {
        "readiness_report": _path_ref(output_path / "readiness_report.json"),
        "scaleup_report": _path_ref(output_path / "scaleup_report.json"),
        "context_pair_sample": _path_ref(output_path / "context_pair_sample.jsonl"),
        "model_adjudicated_labels": _path_ref(output_path / "model_adjudicated_labels.jsonl"),
        "report_doc": _path_ref(report_md_path),
    }
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Route 6B external sufficiency measurement scale-up.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--bridge-rows", default=DEFAULT_BRIDGE_ROWS_PATH)
    parser.add_argument("--candidate-pools", default=DEFAULT_CANDIDATE_POOLS_PATH)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--min-accepted-labels", type=int, default=DEFAULT_MIN_ACCEPTED_LABELS)
    parser.add_argument("--run-live-adjudication", action="store_true")
    parser.add_argument("--judge-config", default=DEFAULT_LOCAL_JUDGE_CONFIG)
    parser.add_argument("--report-md", default=str(DEFAULT_REPORT_MD))
    args = parser.parse_args(argv)

    result = run_route6b_measurement_scaleup(
        output_dir=args.output_dir,
        bridge_rows_path=args.bridge_rows,
        candidate_pools_path=args.candidate_pools,
        sample_size=args.sample_size,
        min_accepted_labels=args.min_accepted_labels,
        run_live_adjudication=args.run_live_adjudication,
        judge_config_path=args.judge_config,
        report_md_path=args.report_md,
    )
    print(
        canonical_json_dumps(
            {
                "accepted_model_adjudicated_count": result["accepted_model_adjudicated_count"],
                "claim_status": result["claim_status"],
                "live_api_used": result["live_api_used"],
                "status": result["status"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
