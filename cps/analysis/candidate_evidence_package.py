from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence


CLAIM_STATUS = "operational_utility_only/no_claim_upgrade"
DENIED_CLAIMS = [
    "accepted_bridge_candidate",
    "calibrated_proxy_supported",
    "deployed V-information verification",
    "fixed-target NLL bridge support",
    "global selector superiority",
    "human measurement validation",
    "measurement validation",
    "metric bridge support",
    "paper evidence",
    "selector superiority",
    "vinfo_proxy_supported",
]


def _write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _checklist(claims: Sequence[str]) -> str:
    claim_lines = "\n".join(f"- Review `{claim}` evidence and scope." for claim in claims)
    return (
        "# Independent Review Checklist\n\n"
        "- Verify no raw API responses are stored.\n"
        "- Verify only DashScope-compatible live API was used for model calls.\n"
        "- Verify generated-token logprobs are not described as fixed-target NLL.\n"
        "- Verify no Route 5 or Route 8 unlock is requested.\n"
        f"{claim_lines}\n"
    )


def build_candidate_evidence_package(
    *,
    output_dir: str | Path,
    evidence_reports: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    output = Path(output_dir)
    claims = sorted({str(item.get("candidate_claim") or "") for item in evidence_reports if item.get("candidate_claim")})
    status = "reviewable_candidate_package_ready" if claims else "blocked_no_candidate_claims"
    manifest = {
        "claim_status": CLAIM_STATUS,
        "evidence_reports": [dict(item) for item in evidence_reports],
        "schema_version": "epf_candidate_evidence_manifest_v1",
        "status": status,
    }
    claim_request = {
        "claim_status": CLAIM_STATUS,
        "denied_claims": DENIED_CLAIMS,
        "development_claim_upgrade_performed": False,
        "independent_review_required": True,
        "requested_candidate_claims": claims,
        "route5_unlock_requested": False,
        "route8_unlock_requested": False,
        "schema_version": "epf_claim_request_v1",
    }
    supporting = {
        "artifact_count": len(evidence_reports),
        "artifacts": [str(item.get("artifact") or "") for item in evidence_reports],
        "schema_version": "epf_supporting_artifacts_v1",
    }
    denied = {"claim_status": CLAIM_STATUS, "denied_claims": DENIED_CLAIMS, "schema_version": "epf_denied_claims_v1"}
    _write_json(output / "evidence_manifest.json", manifest)
    _write_json(output / "claim_request.json", claim_request)
    _write_json(output / "supporting_artifacts.json", supporting)
    _write_json(output / "denied_claims.json", denied)
    (output / "independent_review_checklist.md").write_text(_checklist(claims), encoding="utf-8")
    (output / "paper_table_draft.md").write_text(
        "| Candidate claim | Development claim status | Review required |\n"
        "|---|---|---|\n"
        + "\n".join(f"| `{claim}` | no upgrade | yes |" for claim in claims)
        + "\n",
        encoding="utf-8",
    )
    return {
        "claim_status": CLAIM_STATUS,
        "requested_candidate_claims": claims,
        "schema_version": "epf_candidate_evidence_package_result_v1",
        "status": status,
    }
