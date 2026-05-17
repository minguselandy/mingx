from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Sequence

from cps.benchmarks.schemas import write_json


DEFAULT_OUTPUT_DIR = Path("artifacts/experiments/route5_fixed_model_logloss_proxy")
DEFAULT_DOCS_PATH = Path("docs/experiments/Route5-fixed-model-logloss-proxy-blocked-report.md")
DEFAULT_ROUTE4B_CLAIM_GATE_PATH = Path("artifacts/experiments/route4b_bridge_to_measurement/claim_gate_result.json")
DEFAULT_ROUTE4B_WITNESS_PATH = Path("artifacts/experiments/route4b_bridge_to_measurement/metric_bridge_witness.json")
DEFAULT_ROUTE4C_READINESS_PATH = Path("artifacts/experiments/route4c_fever/readiness_report.json")


@dataclass(frozen=True)
class Route5Package:
    readiness_report: dict[str, Any]
    dependency_gate_report: dict[str, Any]


def _resolve(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _path_ref(path: str | Path, *, root: Path | None = None) -> str:
    candidate = Path(path)
    if root is not None and candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return candidate.name
    if candidate.is_absolute():
        return candidate.name
    return candidate.as_posix()


def _read_json(root: Path, path: str | Path) -> dict[str, Any]:
    resolved = _resolve(root, path)
    if not resolved.exists() or not resolved.is_file():
        return {}
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _route4b_gate(root: Path, claim_gate_path: str | Path, witness_path: str | Path) -> dict[str, Any]:
    claim_gate = _read_json(root, claim_gate_path)
    witness = _read_json(root, witness_path)
    accepted = bool(claim_gate.get("metric_bridge_support_candidate")) or bool(witness.get("metric_bridge_support_candidate"))
    gate_result = str(claim_gate.get("gate_result") or witness.get("bridge_status") or "missing_route4b_claim_gate")
    return {
        "accepted_candidate_bridge_evidence": accepted,
        "claim_gate_path": _path_ref(claim_gate_path),
        "gate_result": gate_result,
        "metric_bridge_support_candidate": bool(claim_gate.get("metric_bridge_support_candidate", False)),
        "reason_codes": list(witness.get("reason_codes", [])),
        "witness_path": _path_ref(witness_path),
    }


def _route4c_gate(root: Path, readiness_path: str | Path) -> dict[str, Any]:
    readiness = _read_json(root, readiness_path)
    accepted = bool(readiness.get("candidate_bridge_evidence_accepted")) or bool(readiness.get("route4c_second_stratum_supported"))
    status = str(readiness.get("status") or "missing_route4c_readiness")
    return {
        "accepted_candidate_bridge_evidence": accepted,
        "claim_status": readiness.get("claim_status", "no_claim_upgrade"),
        "readiness_path": _path_ref(readiness_path),
        "reason_codes": list(readiness.get("reason_codes", [])),
        "status": status,
    }


def assess_route5_start_gate(
    *,
    root: str | Path = ".",
    route4b_claim_gate_path: str | Path = DEFAULT_ROUTE4B_CLAIM_GATE_PATH,
    route4b_witness_path: str | Path = DEFAULT_ROUTE4B_WITNESS_PATH,
    route4c_readiness_path: str | Path = DEFAULT_ROUTE4C_READINESS_PATH,
) -> Route5Package:
    repo_root = Path(root)
    route4b = _route4b_gate(repo_root, route4b_claim_gate_path, route4b_witness_path)
    route4c = _route4c_gate(repo_root, route4c_readiness_path)
    start_condition = bool(route4b["accepted_candidate_bridge_evidence"] or route4c["accepted_candidate_bridge_evidence"])

    reason_codes: list[str] = []
    if not start_condition:
        reason_codes.append("no_accepted_route4_candidate_bridge_evidence")
    if not route4b["accepted_candidate_bridge_evidence"]:
        reason_codes.append(f"route4b_{route4b['gate_result']}")
    if not route4c["accepted_candidate_bridge_evidence"]:
        reason_codes.append(f"route4c_{route4c['status']}")
    if not start_condition:
        reason_codes.append("route5_live_api_not_used_start_condition_failed")

    dependency_gate_report = {
        "artifact_type": "Route5DependencyGateReport",
        "blocked_before_live_api": not start_condition,
        "claim_status": "no_claim_upgrade",
        "route4b": route4b,
        "route4c": route4c,
        "route5_live_api_allowed": start_condition,
        "schema_version": "route5_dependency_gate_report_v1",
        "start_condition": "Route 4B or Route 4C yields accepted candidate bridge evidence",
        "start_condition_satisfied": start_condition,
    }

    readiness_report = {
        "artifact_type": "Route5FixedModelLoglossProxyReadinessReport",
        "calibrated_proxy_supported": False,
        "claim_status": "no_claim_upgrade",
        "dependency_gate_report_path": "artifacts/experiments/route5_fixed_model_logloss_proxy/dependency_gate_report.json",
        "fixed_model_logloss_proxy_verification_started": False,
        "live_api_used": False,
        "measurement_validation": False,
        "metric_bridge_support": False,
        "paper_evidence": False,
        "reason_codes": reason_codes,
        "schema_version": "route5_fixed_model_logloss_proxy_readiness_v1",
        "start_condition_satisfied": start_condition,
        "status": "ready_for_scoped_logloss_proxy_verification" if start_condition else "blocked_route4_candidate_bridge_required",
        "true_deployed_vinformation_verification": False,
        "vinfo_proxy_supported": False,
        "vinfo_proxy_supported_candidate": False,
    }

    return Route5Package(readiness_report=readiness_report, dependency_gate_report=dependency_gate_report)


def render_route5_report(package: Route5Package) -> str:
    readiness = package.readiness_report
    gate = package.dependency_gate_report
    reason_codes = "\n".join(f"- `{code}`" for code in readiness["reason_codes"])
    return (
        "# Route5 Fixed-model Logloss Proxy Blocked Report\n\n"
        f"Status: `{readiness['status']}`\n"
        "Claim status: `no_claim_upgrade`\n\n"
        "## Decision\n\n"
        "Route 5 is blocked before fixed-model logloss proxy verification. The "
        "required start condition is not satisfied because neither Route 4B nor "
        "Route 4C produced accepted candidate bridge evidence.\n\n"
        "Live API use was not invoked because the Route 5 start condition failed.\n\n"
        "## Dependency Gate\n\n"
        f"- Route 4B accepted candidate bridge evidence: `{str(gate['route4b']['accepted_candidate_bridge_evidence']).lower()}`.\n"
        f"- Route 4B gate result: `{gate['route4b']['gate_result']}`.\n"
        f"- Route 4C accepted candidate bridge evidence: `{str(gate['route4c']['accepted_candidate_bridge_evidence']).lower()}`.\n"
        f"- Route 4C status: `{gate['route4c']['status']}`.\n"
        f"- Route 5 live API allowed: `{str(gate['route5_live_api_allowed']).lower()}`.\n\n"
        "## Reason Codes\n\n"
        f"{reason_codes}\n\n"
        "## Claim Boundary\n\n"
        "- `vinfo_proxy_supported_candidate` remains false.\n"
        "- `vinfo_proxy_supported` remains false.\n"
        "- True deployed V-information verification remains denied.\n"
        "- No fixed-model logloss proxy evidence was produced.\n"
    )


def write_route5_artifacts(
    *,
    root: str | Path = ".",
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    docs_path: str | Path = DEFAULT_DOCS_PATH,
    route4b_claim_gate_path: str | Path = DEFAULT_ROUTE4B_CLAIM_GATE_PATH,
    route4b_witness_path: str | Path = DEFAULT_ROUTE4B_WITNESS_PATH,
    route4c_readiness_path: str | Path = DEFAULT_ROUTE4C_READINESS_PATH,
) -> dict[str, Path]:
    repo_root = Path(root)
    package = assess_route5_start_gate(
        root=repo_root,
        route4b_claim_gate_path=route4b_claim_gate_path,
        route4b_witness_path=route4b_witness_path,
        route4c_readiness_path=route4c_readiness_path,
    )
    out = _resolve(repo_root, output_dir)
    docs = _resolve(repo_root, docs_path)
    paths = {
        "readiness_report": out / "readiness_report.json",
        "dependency_gate_report": out / "dependency_gate_report.json",
        "report_doc": docs,
    }
    write_json(paths["readiness_report"], package.readiness_report)
    write_json(paths["dependency_gate_report"], package.dependency_gate_report)
    docs.parent.mkdir(parents=True, exist_ok=True)
    docs.write_text(render_route5_report(package), encoding="utf-8")
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assess Route 5 fixed-model logloss proxy start gate.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--docs-path", default=str(DEFAULT_DOCS_PATH))
    args = parser.parse_args(argv)

    paths = write_route5_artifacts(root=args.root, output_dir=args.output_dir, docs_path=args.docs_path)
    readiness = json.loads(paths["readiness_report"].read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "claim_status": readiness["claim_status"],
                "live_api_used": readiness["live_api_used"],
                "start_condition_satisfied": readiness["start_condition_satisfied"],
                "status": readiness["status"],
                "vinfo_proxy_supported_candidate": readiness["vinfo_proxy_supported_candidate"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
