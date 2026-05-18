from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Sequence

from cps.benchmarks.schemas import write_json


DEFAULT_OUTPUT_DIR = Path("artifacts/experiments/route8_final_integration")
DEFAULT_DOCS_PATH = Path("docs/experiments/Route8-final-integration-blocked-report.md")
DEFAULT_ROUTE6A_ADJUDICATION_PATH = Path("artifacts/experiments/route6a_measurement_pilot/adjudication_report.json")
DEFAULT_ROUTE4B_CLAIM_GATE_PATH = Path("artifacts/experiments/route4b_bridge_to_measurement/claim_gate_result.json")
DEFAULT_ROUTE4C_READINESS_PATH = Path("artifacts/experiments/route4c_fever/readiness_report.json")
DEFAULT_ROUTE5_READINESS_PATH = Path("artifacts/experiments/route5_fixed_model_logloss_proxy/readiness_report.json")
DEFAULT_ROUTE7_READINESS_PATH = Path("artifacts/experiments/route7_scoped_selector_superiority/readiness_report.json")
DEFAULT_HOTPOTQA_ROUTE5_READINESS_PATH = Path(
    "artifacts/experiments/route5_hotpotqa_fixed_model_logloss_proxy/readiness_report.json"
)
DEFAULT_HOTPOTQA_ROUTE7_READINESS_PATH = Path(
    "artifacts/experiments/route7_hotpotqa_first_selector_comparison/readiness_report.json"
)

BLOCKED_CLAIMS = [
    "calibrated_proxy_supported",
    "vinfo_proxy_supported",
    "measurement_validation",
    "metric_bridge_support",
    "paper_grade_evidence",
    "scoped_multi_benchmark_selector_superiority",
    "global_selector_superiority",
    "deployed_V_information_verification",
]


@dataclass(frozen=True)
class Route8Package:
    readiness_report: dict[str, Any]
    evidence_status_summary: dict[str, Any]
    blocked_claims_report: dict[str, Any]
    integration_gate_report: dict[str, Any]


def _resolve(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _path_ref(path: str | Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate.name
    return candidate.as_posix()


def _read_json(root: Path, path: str | Path) -> dict[str, Any]:
    resolved = _resolve(root, path)
    if not resolved.exists() or not resolved.is_file():
        return {}
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _route_statuses(root: Path, *, hotpotqa_only: bool = False) -> dict[str, dict[str, Any]]:
    route6a = _read_json(root, DEFAULT_ROUTE6A_ADJUDICATION_PATH)
    route4b = _read_json(root, DEFAULT_ROUTE4B_CLAIM_GATE_PATH)
    route4c = {} if hotpotqa_only else _read_json(root, DEFAULT_ROUTE4C_READINESS_PATH)
    route5_path = DEFAULT_HOTPOTQA_ROUTE5_READINESS_PATH if hotpotqa_only else DEFAULT_ROUTE5_READINESS_PATH
    route7_path = DEFAULT_HOTPOTQA_ROUTE7_READINESS_PATH if hotpotqa_only else DEFAULT_ROUTE7_READINESS_PATH
    route5 = _read_json(root, route5_path)
    route7 = _read_json(root, route7_path)
    routes: dict[str, dict[str, Any]] = {
        "Route6A": {
            "accepted_for_claim_upgrade": False,
            "artifact_path": _path_ref(DEFAULT_ROUTE6A_ADJUDICATION_PATH),
            "evidence": f"{route6a.get('accepted_model_adjudicated_count', 0)} accepted model-adjudicated labels",
            "measurement_validation": bool(route6a.get("measurement_validation_candidate_allowed")),
            "status": "model_adjudication_completed_no_measurement_validation"
            if route6a
            else "missing_route6a_adjudication_report",
        },
        "Route4B": {
            "accepted_for_claim_upgrade": bool(route4b.get("metric_bridge_support_candidate")),
            "artifact_path": _path_ref(DEFAULT_ROUTE4B_CLAIM_GATE_PATH),
            "gate_result": route4b.get("gate_result", "missing_route4b_claim_gate"),
            "status": str(route4b.get("gate_result") or "missing_route4b_claim_gate"),
        },
        "Route5": {
            "accepted_for_claim_upgrade": bool(route5.get("vinfo_proxy_supported_candidate")),
            "artifact_path": _path_ref(route5_path),
            "status": str(route5.get("status") or "missing_route5_readiness"),
        },
        "Route7": {
            "accepted_for_claim_upgrade": bool(route7.get("route7_claim_allowed")),
            "artifact_path": _path_ref(route7_path),
            "status": str(route7.get("status") or "missing_route7_readiness"),
        },
    }
    if not hotpotqa_only:
        routes["Route4C"] = {
            "accepted_for_claim_upgrade": bool(route4c.get("candidate_bridge_evidence_accepted")),
            "artifact_path": _path_ref(DEFAULT_ROUTE4C_READINESS_PATH),
            "status": str(route4c.get("status") or "missing_route4c_readiness"),
        }
    return routes


def assess_route8_final_integration(*, root: str | Path = ".", hotpotqa_only: bool = False) -> Route8Package:
    repo_root = Path(root)
    routes = _route_statuses(repo_root, hotpotqa_only=hotpotqa_only)
    accepted = [name for name, route in routes.items() if route["accepted_for_claim_upgrade"]]
    integration_allowed = bool(accepted)

    reason_codes: list[str] = []
    if not accepted:
        reason_codes.append("no_accepted_evidence_packages")
        if hotpotqa_only:
            route4b_status = str(routes.get("Route4B", {}).get("status", "missing_route4b_claim_gate"))
            reason_codes.append(f"hotpotqa_route4b_{route4b_status}")
        reason_codes.append("claim_upgrade_unsupported")
        reason_codes.append("no_route8_claim_ledger_or_manuscript_update")

    evidence_status_summary = {
        "artifact_type": "Route8EvidenceStatusSummary",
        "claim_status": "no_claim_upgrade",
        "confirmed_evidence": [
            "Route6A completed approved live model adjudication and stored normalized labels only.",
            "Route4B executed the external sufficiency bridge and failed closed underpowered.",
            *(
                []
                if hotpotqa_only
                else ["Route4C confirmed FEVER restoration remains blocked by missing evidence source and records."]
            ),
            "Route5 was blocked before live API use because Route4 candidate bridge evidence was absent.",
            (
                "Route7 preserved the HotpotQA-first operational comparison without a claim upgrade."
                if hotpotqa_only
                else "Route7 preserved the HotpotQA operational comparison but blocked multi-benchmark superiority."
            ),
        ],
        "routes": routes,
        "schema_version": "route8_evidence_status_summary_v1",
        "scope": "hotpotqa_only" if hotpotqa_only else "all_routes",
    }

    blocked_claims_report = {
        "artifact_type": "Route8BlockedClaimsReport",
        "blocked_claims": list(BLOCKED_CLAIMS),
        "claim_status": "no_claim_upgrade",
        "missing_resources_or_gates": [
            "accepted Route4 bridge candidate or calibrated proxy evidence",
            "human or hybrid measurement labels with agreement metrics",
            "Route5 fixed-model proxy stability diagnostics after start gate satisfaction",
            "independent review accepting any candidate claim upgrade",
        ],
        "next_unlocks": [
            "collect a larger accepted HotpotQA external sufficiency label set",
            "produce at least 500 non-circular bridge rows over at least 150 original instances",
            "pass Route4 bridge gates and independent bridge review",
            "run Route5 fixed-model proxy verification only after Route4-compatible evidence exists",
            "use HotpotQA-first selector comparison only as operational evidence until bridge and review gates pass",
        ],
        "schema_version": "route8_blocked_claims_report_v1",
        "scope": "hotpotqa_only" if hotpotqa_only else "all_routes",
    }
    if not hotpotqa_only:
        blocked_claims_report["missing_resources_or_gates"].insert(
            1, "complete FEVER evidence source, candidate pools, and evaluator delta records"
        )
        blocked_claims_report["missing_resources_or_gates"].insert(
            -1, "finite multi-benchmark Route7 matrix with required deployable baselines"
        )
        blocked_claims_report["next_unlocks"][0] = (
            "restore complete FEVER evidence source or collect larger accepted external sufficiency labels"
        )
        blocked_claims_report["next_unlocks"][-1] = (
            "build a predeclared Route7 multi-benchmark matrix with all deployable baselines"
        )

    integration_gate_report = {
        "artifact_type": "Route8IntegrationGateReport",
        "accepted_evidence_packages": accepted,
        "claim_ledger_update_allowed": integration_allowed,
        "claim_ledger_update_attempted": False,
        "claim_status": "no_claim_upgrade",
        "integration_allowed": integration_allowed,
        "manuscript_update_allowed": integration_allowed,
        "manuscript_update_attempted": False,
        "review_required_before_claim_upgrade": True,
        "schema_version": "route8_integration_gate_report_v1",
        "scope": "hotpotqa_only" if hotpotqa_only else "all_routes",
    }

    readiness_report = {
        "accepted_evidence_packages": accepted,
        "artifact_type": "Route8FinalIntegrationReadinessReport",
        "claim_ledger_update_allowed": integration_allowed,
        "claim_ledger_update_attempted": False,
        "claim_status": "no_claim_upgrade",
        "final_program_status": "integration_ready" if integration_allowed else "honestly_blocked",
        "manuscript_update_allowed": integration_allowed,
        "manuscript_update_attempted": False,
        "reason_codes": reason_codes,
        "schema_version": "route8_final_integration_readiness_v1",
        "scope": "hotpotqa_only" if hotpotqa_only else "all_routes",
        "status": (
            "ready_for_reviewed_final_integration"
            if integration_allowed
            else (
                "blocked_hotpotqa_only_no_accepted_claim_upgrade_evidence"
                if hotpotqa_only
                else "blocked_no_accepted_evidence_packages"
            )
        ),
    }

    return Route8Package(
        readiness_report=readiness_report,
        evidence_status_summary=evidence_status_summary,
        blocked_claims_report=blocked_claims_report,
        integration_gate_report=integration_gate_report,
    )


def render_route8_report(package: Route8Package) -> str:
    readiness = package.readiness_report
    blocked = package.blocked_claims_report
    evidence = package.evidence_status_summary
    reason_codes = "\n".join(f"- `{code}`" for code in readiness["reason_codes"])
    blocked_claims = "\n".join(f"- `{claim}`" for claim in blocked["blocked_claims"])
    missing = "\n".join(f"- {item}" for item in blocked["missing_resources_or_gates"])
    next_unlocks = "\n".join(f"- {item}" for item in blocked["next_unlocks"])
    confirmed = "\n".join(f"- {item}" for item in evidence["confirmed_evidence"])
    return (
        "# Route8 Final Integration Blocked Report\n\n"
        f"Status: `{readiness['status']}`\n"
        f"Final program status: `{readiness['final_program_status']}`\n"
        "Claim status: `no_claim_upgrade`\n\n"
        "No manuscript or claim-ledger edits were made.\n\n"
        "## Confirmed Evidence\n\n"
        f"{confirmed}\n\n"
        "## Blocked Claims\n\n"
        f"{blocked_claims}\n\n"
        "## Missing Resources Or Gates\n\n"
        f"{missing}\n\n"
        "## Next Unlocks\n\n"
        f"{next_unlocks}\n\n"
        "## Reason Codes\n\n"
        f"{reason_codes}\n"
    )


def write_route8_artifacts(
    *,
    root: str | Path = ".",
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    docs_path: str | Path = DEFAULT_DOCS_PATH,
    hotpotqa_only: bool = False,
) -> dict[str, Path]:
    repo_root = Path(root)
    package = assess_route8_final_integration(root=repo_root, hotpotqa_only=hotpotqa_only)
    out = _resolve(repo_root, output_dir)
    docs = _resolve(repo_root, docs_path)
    paths = {
        "blocked_claims_report": out / "blocked_claims_report.json",
        "evidence_status_summary": out / "evidence_status_summary.json",
        "integration_gate_report": out / "integration_gate_report.json",
        "readiness_report": out / "readiness_report.json",
        "report_doc": docs,
    }
    write_json(paths["blocked_claims_report"], package.blocked_claims_report)
    write_json(paths["evidence_status_summary"], package.evidence_status_summary)
    write_json(paths["integration_gate_report"], package.integration_gate_report)
    write_json(paths["readiness_report"], package.readiness_report)
    docs.parent.mkdir(parents=True, exist_ok=True)
    docs.write_text(render_route8_report(package), encoding="utf-8")
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assess Route 8 final integration gate.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--docs-path", default=str(DEFAULT_DOCS_PATH))
    parser.add_argument("--hotpotqa-only", action="store_true")
    args = parser.parse_args(argv)

    paths = write_route8_artifacts(
        root=args.root,
        output_dir=args.output_dir,
        docs_path=args.docs_path,
        hotpotqa_only=args.hotpotqa_only,
    )
    readiness = json.loads(paths["readiness_report"].read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "claim_status": readiness["claim_status"],
                "final_program_status": readiness["final_program_status"],
                "manuscript_update_attempted": readiness["manuscript_update_attempted"],
                "status": readiness["status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
