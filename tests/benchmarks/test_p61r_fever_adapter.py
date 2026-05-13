from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

from conftest import ROOT
from conftest import assert_importing_modules_does_not_load_forbidden_sdks
from cps.benchmarks.fever_adapter import build_fever_candidate_pools
from cps.benchmarks.hashing import canonical_json_dumps
from cps.benchmarks.schemas import canonical_jsonl
from cps.benchmarks.schemas import compute_candidate_pool_hash
from cps.benchmarks.schemas import make_benchmark_instance
from cps.benchmarks.schemas import make_evidence_packet
from cps.benchmarks.schemas import validate_benchmark_instance


def _write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return path


def _claims(path: Path) -> Path:
    return _write_jsonl(
        path,
        [
            {
                "claim": "The Eiffel Tower is located in Paris.",
                "evidence": [
                    {
                        "source_doc_id": "Eiffel_Tower",
                        "span": {"end": 2, "start": 2, "unit": "sentence"},
                        "text": "The Eiffel Tower is a landmark in Paris.",
                    }
                ],
                "id": "fever-1",
                "label": "SUPPORTED",
                "split": "dev",
            }
        ],
    )


def _candidates(path: Path) -> Path:
    return _write_jsonl(
        path,
        [
            {
                "candidates": [
                    {
                        "candidate_id": "retrieved-1",
                        "content": "The Eiffel Tower was completed in 1889.",
                        "gold_support_label": "retrieved_distractor",
                        "source_doc_id": "Eiffel_Tower",
                        "span": {"end": 3, "start": 3, "unit": "sentence"},
                    },
                    {
                        "candidate_id": "random-1",
                        "content": "The Colosseum is located in Rome.",
                        "gold_support_label": "random_distractor",
                        "source_doc_id": "Colosseum",
                        "span": {"end": 1, "start": 1, "unit": "sentence"},
                    },
                ],
                "instance_id": "fever-1",
            }
        ],
    )


def _instance(workspace_tmp_dir: Path):
    result = build_fever_candidate_pools(
        claims_jsonl=_claims(workspace_tmp_dir / "claims.jsonl"),
        candidates_jsonl=_candidates(workspace_tmp_dir / "candidates.jsonl"),
        split="dev",
    )
    assert result.blocked_report is None
    return result.instances[0]


def test_importing_benchmark_modules_does_not_load_forbidden_sdks() -> None:
    assert_importing_modules_does_not_load_forbidden_sdks(
        [
            "cps.benchmarks.hashing",
            "cps.benchmarks.token_cost",
            "cps.benchmarks.schemas",
            "cps.benchmarks.fever_adapter",
            "cps.benchmarks.build_candidate_pools",
        ]
    )


def test_fever_fixture_converts_to_benchmark_instance(workspace_tmp_dir):
    instance = _instance(workspace_tmp_dir)
    payload = instance.to_payload()

    assert payload["schema_version"] == "benchmark_instance_v1"
    assert payload["dataset"] == "FEVER"
    assert payload["task_family"] == "fever_claim_verification"
    assert payload["target"]["label"] == "SUPPORTED"
    assert payload["candidate_pool"]["n_candidates"] == 3
    assert payload["candidate_pool"]["n_gold_packets"] == 1
    assert payload["candidate_pool"]["n_hard_negative_packets"] == 1
    assert payload["candidate_pool"]["n_random_negative_packets"] == 1
    assert payload["adapter_metadata"]["claim_boundary"] == "adapter_only_no_bridge_claim"
    assert validate_benchmark_instance(instance).schema_valid is True


def test_candidate_pool_hash_is_deterministic(workspace_tmp_dir):
    first = _instance(workspace_tmp_dir).to_payload()
    second = copy.deepcopy(first)
    second["candidate_pool"]["packets"] = list(reversed(second["candidate_pool"]["packets"]))

    assert compute_candidate_pool_hash(first["candidate_pool"]) == compute_candidate_pool_hash(second["candidate_pool"])
    assert first["candidate_pool"]["candidate_pool_hash"] == compute_candidate_pool_hash(second["candidate_pool"])


def test_candidate_pool_hash_changes_when_packet_content_changes(workspace_tmp_dir):
    payload = _instance(workspace_tmp_dir).to_payload()
    changed = copy.deepcopy(payload)
    changed["candidate_pool"]["packets"][0]["content"] += " Changed."

    assert compute_candidate_pool_hash(payload["candidate_pool"]) != compute_candidate_pool_hash(changed["candidate_pool"])


def test_packet_id_is_stable(workspace_tmp_dir):
    first = _instance(workspace_tmp_dir).candidate_pool.packets[0].packet_id
    second = _instance(workspace_tmp_dir).candidate_pool.packets[0].packet_id

    assert first == second


def test_jsonl_output_is_byte_deterministic(workspace_tmp_dir):
    first = canonical_jsonl([_instance(workspace_tmp_dir)])
    second = canonical_jsonl([_instance(workspace_tmp_dir)])

    assert first == second
    assert first.endswith("\n")


def test_duplicate_packet_id_rejected(workspace_tmp_dir):
    payload = _instance(workspace_tmp_dir).to_payload()
    payload["candidate_pool"]["packets"][1]["packet_id"] = payload["candidate_pool"]["packets"][0]["packet_id"]
    payload["candidate_pool"]["candidate_pool_hash"] = compute_candidate_pool_hash(payload["candidate_pool"])

    result = validate_benchmark_instance(payload)
    assert result.schema_valid is False
    assert any("duplicate_packet_id" in error for error in result.errors)


def test_missing_target_rejected(workspace_tmp_dir):
    payload = _instance(workspace_tmp_dir).to_payload()
    del payload["target"]
    payload["candidate_pool"]["candidate_pool_hash"] = compute_candidate_pool_hash(payload["candidate_pool"])

    result = validate_benchmark_instance(payload)
    assert result.schema_valid is False
    assert "missing_target" in result.errors


def test_empty_candidate_pool_rejected(workspace_tmp_dir):
    payload = _instance(workspace_tmp_dir).to_payload()
    payload["candidate_pool"]["packets"] = []
    payload["candidate_pool"]["n_candidates"] = 0
    payload["candidate_pool"]["candidate_pool_hash"] = compute_candidate_pool_hash(payload["candidate_pool"])

    result = validate_benchmark_instance(payload)
    assert result.schema_valid is False
    assert "empty_candidate_pool" in result.errors


def test_missing_packet_content_rejected(workspace_tmp_dir):
    payload = _instance(workspace_tmp_dir).to_payload()
    del payload["candidate_pool"]["packets"][0]["content"]
    payload["candidate_pool"]["candidate_pool_hash"] = compute_candidate_pool_hash(payload["candidate_pool"])

    result = validate_benchmark_instance(payload)
    assert result.schema_valid is False
    assert any("missing_packet_content" in error for error in result.errors)


def test_negative_token_cost_rejected(workspace_tmp_dir):
    payload = _instance(workspace_tmp_dir).to_payload()
    payload["candidate_pool"]["packets"][0]["token_cost"] = -1
    payload["candidate_pool"]["candidate_pool_hash"] = compute_candidate_pool_hash(payload["candidate_pool"])

    result = validate_benchmark_instance(payload)
    assert result.schema_valid is False
    assert any("negative_token_cost" in error for error in result.errors)


def test_no_absolute_paths_in_canonical_output(workspace_tmp_dir):
    payload = _instance(workspace_tmp_dir).to_payload()
    assert ":\\" not in canonical_json_dumps(payload)
    assert "/home/" not in canonical_json_dumps(payload)

    payload["adapter_metadata"]["source_path"] = "C:\\Users\\Mingx\\secret\\claims.jsonl"
    payload["candidate_pool"]["candidate_pool_hash"] = compute_candidate_pool_hash(payload["candidate_pool"])
    result = validate_benchmark_instance(payload)
    assert result.schema_valid is False
    assert "absolute_local_path_in_canonical_output" in result.errors


def test_missing_real_data_path_emits_blocked_data_report_not_fake_rows(workspace_tmp_dir):
    result = build_fever_candidate_pools(claims_jsonl=workspace_tmp_dir / "missing-fever.jsonl")

    assert result.instances == ()
    assert result.blocked_report is not None
    assert result.blocked_report["candidate_pools_generated"] == 0
    assert result.blocked_report["p55_rows_generated"] == 0
    assert result.blocked_report["p56_traces_generated"] == 0
    assert "missing_claims_file" in result.blocked_report["reason_codes"]
    serialized = canonical_json_dumps(result.blocked_report)
    assert ":\\" not in serialized
    assert "/home/" not in serialized


def test_cli_writes_blocked_report_for_missing_claims_path(workspace_tmp_dir):
    blocked_path = workspace_tmp_dir / "blocked.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cps.benchmarks.build_candidate_pools",
            "--dataset",
            "FEVER",
            "--claims-jsonl",
            str(workspace_tmp_dir / "missing.jsonl"),
            "--blocked-report-json",
            str(blocked_path),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(blocked_path.read_text(encoding="utf-8"))
    assert payload["status"] == "blocked_data_unavailable"
    assert payload["candidate_pools_generated"] == 0


def test_gold_reachable_under_budget_uses_gold_packet_cost() -> None:
    packet = make_evidence_packet(
        dataset="FEVER",
        split="dev",
        instance_id="long-gold",
        content=" ".join(f"token{i}" for i in range(300)),
        gold_support_label="gold_supporting",
        source_doc_id="doc",
        span={"start": 0, "end": 0, "unit": "sentence"},
        source_packet_key="gold",
    )
    instance = make_benchmark_instance(
        dataset="FEVER",
        split="dev",
        instance_id="long-gold",
        query="A long evidence claim.",
        target_label="SUPPORTED",
        packets=[packet],
    )

    reachable = instance.to_payload()["candidate_pool"]["gold_reachable_under_budget"]
    assert reachable["256"] is False
    assert reachable["512"] is True
    assert reachable["1024"] is True


def test_p61r_doc_preserves_claim_boundaries() -> None:
    text = (ROOT / "docs" / "experiments" / "P61R-public-benchmark-adapters.md").read_text(encoding="utf-8")

    required = [
        "P61R-A does not generate P55 rows",
        "P61R-A does not repair P55 blocked state",
        "P61R-A does not generate P56 traces",
        "P61R-A does not repair P56 no-trace state",
        "no metric bridge support, measurement validation, or paper evidence claim is introduced",
        "Next phase: P62R FEVER bridge row generator",
    ]
    for phrase in required:
        assert phrase in text
    for unsafe in (
        "measurement_validated",
        "human-label validation",
        "human-human kappa",
        "deployed V-information verification",
        "global calibrated proxy support",
        "global V-information proxy support",
        "P55 unblocked",
        "P56 unblocked",
    ):
        for match in re.finditer(re.escape(unsafe), text):
            window = text[max(0, match.start() - 120) : match.end() + 120].lower()
            assert any(marker in window for marker in ("does not", "denied", "forbidden", "not "))
