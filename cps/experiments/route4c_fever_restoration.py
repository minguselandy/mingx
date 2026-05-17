from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Sequence

from cps.benchmarks.fever_adapter import build_fever_candidate_pools
from cps.benchmarks.schemas import write_json


DEFAULT_OUTPUT_DIR = Path("artifacts/experiments/route4c_fever")
DEFAULT_DOCS_PATH = Path("docs/experiments/Route4C-FEVER-restoration-and-second-stratum.md")
DEFAULT_FEVER_CANDIDATE_POOLS_PATH = Path("artifacts/benchmarks/fever_candidate_pools.jsonl")
DEFAULT_FEVER_DELTA_RECORDS_PATH = Path("artifacts/benchmarks/fever_p55_delta_records.jsonl")
DEFAULT_P61R_BLOCKED_REPORT_PATH = Path("artifacts/benchmarks/p61r_blocked_data_report.json")
DEFAULT_P62R_BLOCKED_REPORT_PATH = Path("artifacts/benchmarks/p62r_bridge_row_blocked_report.json")
LOCAL_FEVER_CLAIMS_NOT_SUPPLIED = Path("local_fever_claims_not_supplied")


@dataclass(frozen=True)
class Route4CPackage:
    readiness_report: dict[str, Any]
    source_manifest: dict[str, Any]
    candidate_pool_manifest: dict[str, Any]
    blocked_report: dict[str, Any]


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


def _count_jsonl(root: Path, path: str | Path) -> int:
    resolved = _resolve(root, path)
    if not resolved.exists() or not resolved.is_file():
        return 0
    count = 0
    for line in resolved.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(("#", "//")):
            count += 1
    return count


def _read_json_if_available(root: Path, path: str | Path) -> dict[str, Any] | None:
    resolved = _resolve(root, path)
    if not resolved.exists() or not resolved.is_file():
        return None
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _prior_report_summary(root: Path, path: str | Path) -> dict[str, Any]:
    payload = _read_json_if_available(root, path)
    if payload is None:
        return {"exists": False, "path": _path_ref(path)}
    return {
        "exists": True,
        "path": _path_ref(path),
        "reason_codes": payload.get("reason_codes", []),
        "status": payload.get("status"),
    }


def _blocked_report_for_missing_source(root: Path, claims_path: str | Path | None) -> dict[str, Any]:
    source = _resolve(root, claims_path) if claims_path is not None else LOCAL_FEVER_CLAIMS_NOT_SUPPLIED
    result = build_fever_candidate_pools(claims_jsonl=source)
    if result.blocked_report is None:
        return {
            "blocked_items": [],
            "candidate_pools_generated": len(result.instances),
            "claim_status": ["no_claim_upgrade"],
            "dataset": "FEVER",
            "metric_bridge_support": False,
            "phase": "Route4C",
            "reason_codes": ["route4c_requires_explicit_review_before_candidate_bridge_use"],
            "status": "candidate_pools_ready_pending_route4c_review",
        }
    blocked = dict(result.blocked_report)
    blocked["phase"] = "Route4C-FEVER"
    blocked["route4c_second_stratum_supported"] = False
    return blocked


def assess_route4c(
    *,
    root: str | Path = ".",
    fever_claims_jsonl: str | Path | None = None,
    fever_candidate_pools_path: str | Path = DEFAULT_FEVER_CANDIDATE_POOLS_PATH,
    fever_delta_records_path: str | Path = DEFAULT_FEVER_DELTA_RECORDS_PATH,
) -> Route4CPackage:
    repo_root = Path(root)
    claims_present = fever_claims_jsonl is not None and _resolve(repo_root, fever_claims_jsonl).exists()
    candidate_pool_rows = _count_jsonl(repo_root, fever_candidate_pools_path)
    delta_record_rows = _count_jsonl(repo_root, fever_delta_records_path)
    candidate_pools_available = candidate_pool_rows > 0
    delta_records_available = delta_record_rows > 0

    official_source_restored = bool(claims_present)
    evidence_sentence_provenance_verified = official_source_restored and candidate_pools_available
    logloss_scoring_ready = official_source_restored and candidate_pools_available and delta_records_available
    route4c_second_stratum_supported = (
        evidence_sentence_provenance_verified and candidate_pool_rows >= 150 and delta_record_rows >= 500
    )

    reason_codes: list[str] = []
    if not official_source_restored:
        reason_codes.append("full_fever_evidence_source_unavailable")
        reason_codes.append("evidence_sentence_provenance_unverified")
    if not candidate_pools_available:
        reason_codes.append("missing_fever_candidate_pools")
    if not delta_records_available:
        reason_codes.append("missing_fever_delta_records")
    if not logloss_scoring_ready:
        reason_codes.append("fever_logloss_scoring_not_ready")
    if not route4c_second_stratum_supported:
        reason_codes.append("route4c_second_stratum_not_established")

    status = "route4c_second_stratum_ready_pending_review" if route4c_second_stratum_supported else "blocked_fever_source_unavailable"
    blocked_report = _blocked_report_for_missing_source(repo_root, fever_claims_jsonl)

    source_manifest = {
        "artifact_type": "Route4CFeverSourceManifest",
        "blocked_report_path": "artifacts/experiments/route4c_fever/blocked_report.json",
        "claim_status": "no_claim_upgrade",
        "dataset": "FEVER",
        "evidence_sentence_provenance_verified": evidence_sentence_provenance_verified,
        "fever_claims_jsonl_configured": fever_claims_jsonl is not None,
        "fever_claims_jsonl_path": None if fever_claims_jsonl is None else _path_ref(fever_claims_jsonl, root=repo_root),
        "official_fever_evidence_source_restored": official_source_restored,
        "prior_blocked_reports": {
            "p61r": _prior_report_summary(repo_root, DEFAULT_P61R_BLOCKED_REPORT_PATH),
            "p62r": _prior_report_summary(repo_root, DEFAULT_P62R_BLOCKED_REPORT_PATH),
        },
        "raw_dataset_mirror_committed": False,
        "schema_version": "route4c_fever_source_manifest_v1",
        "source_status": "missing_complete_fever_evidence_source" if not official_source_restored else "source_present_pending_review",
    }

    candidate_pool_manifest = {
        "artifact_type": "Route4CFeverCandidatePoolManifest",
        "blocked_report_path": "artifacts/experiments/route4c_fever/blocked_report.json",
        "candidate_pool_builder": "cps.benchmarks.fever_adapter.build_fever_candidate_pools",
        "candidate_pool_builder_available": True,
        "candidate_pool_path": _path_ref(fever_candidate_pools_path),
        "candidate_pool_rows_available": candidate_pool_rows,
        "candidate_pools_generated": 0,
        "claim_status": "no_claim_upgrade",
        "dataset": "FEVER",
        "delta_record_path": _path_ref(fever_delta_records_path),
        "delta_record_rows_available": delta_record_rows,
        "generated_candidate_pool_path": None,
        "logloss_scoring_ready": logloss_scoring_ready,
        "raw_dataset_mirror_committed": False,
        "required_min_candidate_pools": 150,
        "required_min_delta_records": 500,
        "schema_version": "route4c_fever_candidate_pool_manifest_v1",
    }

    readiness_report = {
        "artifact_type": "Route4CFeverReadinessReport",
        "blocked_report_path": "artifacts/experiments/route4c_fever/blocked_report.json",
        "calibrated_proxy_supported": False,
        "candidate_bridge_evidence_accepted": False,
        "candidate_pool_manifest_path": "artifacts/experiments/route4c_fever/candidate_pool_manifest.json",
        "claim_status": "no_claim_upgrade",
        "dataset": "FEVER",
        "live_api_used": False,
        "measurement_validation": False,
        "metric_bridge_support": False,
        "no_fabricated_fever_evidence": True,
        "paper_evidence": False,
        "reason_codes": reason_codes,
        "route4c_second_stratum_supported": route4c_second_stratum_supported,
        "route5_start_condition_satisfied": False,
        "schema_version": "route4c_fever_readiness_report_v1",
        "source_manifest_path": "artifacts/experiments/route4c_fever/source_manifest.json",
        "status": status,
        "stop_condition": "full FEVER evidence source is unavailable" if not official_source_restored else None,
        "vinfo_proxy_supported": False,
    }

    return Route4CPackage(
        readiness_report=readiness_report,
        source_manifest=source_manifest,
        candidate_pool_manifest=candidate_pool_manifest,
        blocked_report=blocked_report,
    )


def render_route4c_report(package: Route4CPackage) -> str:
    readiness = package.readiness_report
    candidate = package.candidate_pool_manifest
    source = package.source_manifest
    reason_codes = "\n".join(f"- `{code}`" for code in readiness["reason_codes"])
    md_bool = {True: "true", False: "false"}
    return (
        "# Route4C FEVER Restoration and Second Stratum\n\n"
        f"Status: `{readiness['status']}`\n"
        "Claim status: `no_claim_upgrade`\n\n"
        "## Decision\n\n"
        "Route 4C is blocked fail-closed. The complete FEVER evidence source is "
        "not available in the repository, so evidence sentence provenance cannot "
        "be verified for a second bridge stratum. FEVER candidate pools were not "
        "generated, and no FEVER logloss scoring readiness is claimed.\n\n"
        "No fabricated FEVER evidence was introduced.\n\n"
        "## Evidence Checked\n\n"
        f"- Official FEVER source restored: `{md_bool[source['official_fever_evidence_source_restored']]}`.\n"
        f"- Evidence sentence provenance verified: `{md_bool[source['evidence_sentence_provenance_verified']]}`.\n"
        f"- Candidate-pool rows available: `{candidate['candidate_pool_rows_available']}`.\n"
        f"- Delta-record rows available: `{candidate['delta_record_rows_available']}`.\n"
        f"- Logloss scoring ready: `{md_bool[candidate['logloss_scoring_ready']]}`.\n"
        f"- Raw dataset mirror committed: `{md_bool[source['raw_dataset_mirror_committed']]}`.\n\n"
        "## Reason Codes\n\n"
        f"{reason_codes}\n\n"
        "## Claim Boundary\n\n"
        "- `calibrated_proxy_supported` remains false.\n"
        "- `vinfo_proxy_supported` remains false.\n"
        "- `measurement_validated` remains false.\n"
        "- Route 5 start conditions are not satisfied by Route 4C.\n\n"
        "## Produced Artifacts\n\n"
        "- `artifacts/experiments/route4c_fever/readiness_report.json`\n"
        "- `artifacts/experiments/route4c_fever/source_manifest.json`\n"
        "- `artifacts/experiments/route4c_fever/candidate_pool_manifest.json`\n"
        "- `artifacts/experiments/route4c_fever/blocked_report.json`\n"
    )


def write_route4c_artifacts(
    *,
    root: str | Path = ".",
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    docs_path: str | Path = DEFAULT_DOCS_PATH,
    fever_claims_jsonl: str | Path | None = None,
    fever_candidate_pools_path: str | Path = DEFAULT_FEVER_CANDIDATE_POOLS_PATH,
    fever_delta_records_path: str | Path = DEFAULT_FEVER_DELTA_RECORDS_PATH,
) -> dict[str, Path]:
    repo_root = Path(root)
    package = assess_route4c(
        root=repo_root,
        fever_claims_jsonl=fever_claims_jsonl,
        fever_candidate_pools_path=fever_candidate_pools_path,
        fever_delta_records_path=fever_delta_records_path,
    )
    out = _resolve(repo_root, output_dir)
    docs = _resolve(repo_root, docs_path)
    paths = {
        "readiness_report": out / "readiness_report.json",
        "source_manifest": out / "source_manifest.json",
        "candidate_pool_manifest": out / "candidate_pool_manifest.json",
        "blocked_report": out / "blocked_report.json",
        "report_doc": docs,
    }
    write_json(paths["readiness_report"], package.readiness_report)
    write_json(paths["source_manifest"], package.source_manifest)
    write_json(paths["candidate_pool_manifest"], package.candidate_pool_manifest)
    write_json(paths["blocked_report"], package.blocked_report)
    docs.parent.mkdir(parents=True, exist_ok=True)
    docs.write_text(render_route4c_report(package), encoding="utf-8")
    return paths


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assess Route 4C FEVER restoration readiness.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--docs-path", default=str(DEFAULT_DOCS_PATH))
    parser.add_argument("--fever-claims-jsonl")
    parser.add_argument("--fever-candidate-pools-path", default=str(DEFAULT_FEVER_CANDIDATE_POOLS_PATH))
    parser.add_argument("--fever-delta-records-path", default=str(DEFAULT_FEVER_DELTA_RECORDS_PATH))
    args = parser.parse_args(argv)

    paths = write_route4c_artifacts(
        root=args.root,
        output_dir=args.output_dir,
        docs_path=args.docs_path,
        fever_claims_jsonl=args.fever_claims_jsonl,
        fever_candidate_pools_path=args.fever_candidate_pools_path,
        fever_delta_records_path=args.fever_delta_records_path,
    )
    readiness = json.loads(paths["readiness_report"].read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "claim_status": readiness["claim_status"],
                "route4c_second_stratum_supported": readiness["route4c_second_stratum_supported"],
                "route5_start_condition_satisfied": readiness["route5_start_condition_satisfied"],
                "status": readiness["status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
