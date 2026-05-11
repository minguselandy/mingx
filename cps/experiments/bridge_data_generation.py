from __future__ import annotations

import argparse
import json
import math
import os
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from api.openai_compatible import OpenAICompatibleClient, OpenAICompatibleCredentials
from api.settings import ResolvedApiProfile, get_api_profile, resolve_api_profile
from cps.runtime.secrets import extract_api_key_from_csv


class BridgeDataGenerationValidationError(ValueError):
    """Raised when P45 bridge data generation inputs are invalid."""


class BridgeDataGenerationGateError(RuntimeError):
    """Raised before any live-capable generation when operator gates are absent."""


TaskPacketFn = Callable[[Mapping[str, Any]], Mapping[str, Any]]
AdjudicatorFn = Callable[[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]
ProviderClientFactory = Callable[[ResolvedApiProfile, Mapping[str, Any]], Any]

MODE_DRY_RUN = "dry_run"
MODE_LIVE = "live_operator_approved"
PROTOCOL_VERSION = "bridge_data_generation.v1"
LOCAL_LIVE_CONFIG_PATH = Path("configs/local/bridge-data-generation-live.local.json")
LIVE_GATE_ENV_VARS = ("CPS_ALLOW_LIVE_API", "P45_ALLOW_API_DATA_GENERATION")
DENIED_CLAIMS = (
    "measurement_validated",
    "scientific_validation",
    "human_labeled_validation",
    "human_kappa",
    "deployed_v_information_verification",
)
EVIDENCE_STRENGTH_BANDS = (
    "irrelevant",
    "weak_hint",
    "partial_constraint",
    "strong_clue",
    "explicit_answer",
)
TASK_PACKET_MODE_PLACEHOLDER = "placeholder_v1"
TASK_PACKET_MODE_BRIDGE_CANARY = "bridge_canary_v2"
TASK_PACKET_MODE_BRIDGE_CANARY_V3 = "bridge_canary_v3"
TASK_PACKET_MODE_BRIDGE_CANARY_V4 = "bridge_canary_v4"
TASK_PACKET_MODE_LOGLOSS_POSITIVE_CONTROL = "logloss_positive_control_v1"
REQUIRED_TASK_FIELDS = (
    "task_id",
    "question",
    "target_answer",
    "gold_facts",
    "candidate_findings",
    "baseline_context",
    "added_block",
)
ADJUDICATION_BOOLEAN_FIELDS = (
    "target_clear",
    "intervention_valid",
    "no_leakage",
    "no_duplicate_trivial_case",
    "utility_score_consistent",
)
OPTIONAL_P45_PROVENANCE_FIELDS = (
    "data_origin",
    "delta_utility_source",
    "delta_logloss_source",
    "review_status",
)

DEFAULT_CONFIG = {
    "active_stratum_id": "bio_attribute__operator_provided_fixed_model_v1__fixed_order_v1__block1__top_L",
    "block_size": 1,
    "candidate_slice_band": "top_L",
    "data_origin": "api_generated",
    "delta_logloss_source": "measured_logprob",
    "delta_utility_source": "strong_model_adjudicated",
    "fixed_model_id": "",
    "materialization_policy": "fixed_order_v1",
    "metric": "model_adjudicated_utility_vs_logloss",
    "mode": MODE_DRY_RUN,
    "operator_approval": False,
    "output_dir": "artifacts/experiments/bridge_data_generation_bio_attribute",
    "protocol_version": PROTOCOL_VERSION,
    "provider_profile": "",
    "minimum_abs_delta_logloss_for_bridge_evidence": 0.001,
    "source": "operator_provided",
    "strong_review_model_id": "",
    "task_family": "bio_attribute",
    "task_packet_mode": TASK_PACKET_MODE_PLACEHOLDER,
}


@dataclass(frozen=True)
class BridgeProviderProfileCallables:
    logloss_scorer: TaskPacketFn
    utility_reviewer: TaskPacketFn
    adjudicator: AdjudicatorFn
    preflight: dict[str, Any]


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _stable_jsonl(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return ""
    return "\n".join(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) for row in rows) + "\n"


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_stable_json(payload), encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_stable_jsonl(rows), encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise BridgeDataGenerationValidationError(f"config file does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BridgeDataGenerationValidationError("config must be a JSON object")
    return payload


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _env_values(env: Mapping[str, str] | None = None) -> dict[str, str]:
    if env is not None:
        return {str(key): str(value) for key, value in env.items() if value is not None}
    values: dict[str, str] = {}
    values.update(_load_env_file(Path(".env")))
    values.update(_load_env_file(Path(".env.local")))
    values.update({key: value for key, value in os.environ.items() if isinstance(value, str)})
    return values


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail}


def _local_credential_file_path(config: Mapping[str, Any], config_path: str | Path) -> Path | None:
    source = config.get("credential_source")
    if not isinstance(source, Mapping):
        return None
    raw_path = str(source.get("local_credential_file") or "").strip()
    if not raw_path or raw_path.startswith("OPERATOR_"):
        return None
    path = Path(raw_path)
    if path.is_absolute():
        return path
    cwd_path = Path.cwd() / path
    if cwd_path.exists():
        return cwd_path
    config_relative = Path(config_path).resolve().parent / path
    if config_relative.exists():
        return config_relative
    return cwd_path


def _credential_source_kind(
    *,
    config: Mapping[str, Any],
    config_path: str | Path,
    env_map: Mapping[str, str],
    api_key_env: str,
) -> tuple[str, Path | None]:
    if env_map.get("API_KEY") or env_map.get(api_key_env):
        return "environment", None
    local_file = _local_credential_file_path(config, config_path)
    if local_file is not None and local_file.exists():
        return "local_credential_file", local_file
    return "missing", local_file


def _finite_float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _default_task_packets() -> list[dict[str, Any]]:
    return [
        {
            "added_block": "OPERATOR_OR_API_FILL_ADDED_BLOCK_A",
            "baseline_context": "OPERATOR_OR_API_FILL_BASELINE_CONTEXT_L",
            "candidate_findings": ["OPERATOR_OR_API_FILL_CANDIDATE_FINDING"],
            "gold_facts": ["OPERATOR_OR_API_FILL_GOLD_FACT"],
            "question": "OPERATOR_OR_API_FILL_QUESTION",
            "target_answer": "OPERATOR_OR_API_FILL_TARGET_ANSWER",
            "task_id": "OPERATOR_OR_API_FILL_TASK_001",
        }
    ]


def generate_bridge_canary_task_packets(sample_limit: int = 8) -> list[dict[str, Any]]:
    """Return deterministic P45b canary task packets with varied evidence strength.

    These packets contain no measured values. They are prompts for a future
    operator-approved live run and are designed to avoid the first smoke's
    utility saturation by spanning irrelevant through explicit evidence bands.
    """

    packets = [
        {
            "added_block": (
                "The accession note says the sample was shipped on dry ice and the chromatography "
                "column was equilibrated before loading."
            ),
            "baseline_context": "Bio-attribute sample BCA-201 was logged after purification. No assay result is recorded in the baseline.",
            "block_size": 1,
            "candidate_findings": ["Shipping and chromatography handling details were recorded."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "irrelevant",
            "gold_facts": ["The target answer must be supported only by assay evidence, not handling metadata."],
            "materialization_policy": "fixed_order_v1",
            "question": "What operator-coded bio-attribute should be assigned to sample BCA-201?",
            "target_answer": "Assign code NQ-17 for cobalt-dependent nickase activity.",
            "task_family": "bio_attribute",
            "task_id": "p45b-bio-canary-001",
        },
        {
            "added_block": (
                "A trace signal appeared in the nuclease panel only after a cobalt salt was added, "
                "but the operator note did not identify the exact activity code."
            ),
            "baseline_context": "Bio-attribute sample BCA-202 has a completed expression record and no functional panel interpretation in the baseline.",
            "block_size": 1,
            "candidate_findings": ["A cobalt-dependent panel signal was observed without the final code."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "weak_hint",
            "gold_facts": ["The block is only a weak clue and does not entail the exact target code."],
            "materialization_policy": "fixed_order_v1",
            "question": "What operator-coded bio-attribute should be assigned to sample BCA-202?",
            "target_answer": "Assign code NQ-17 for cobalt-dependent nickase activity.",
            "task_family": "bio_attribute",
            "task_id": "p45b-bio-canary-002",
        },
        {
            "added_block": (
                "The assay panel narrowed the sample to a cobalt-dependent nuclease family, "
                "but the readout did not distinguish nickase from exonuclease behavior."
            ),
            "baseline_context": "Bio-attribute sample BCA-203 is described only as a purified candidate enzyme with no baseline functional label.",
            "block_size": 1,
            "candidate_findings": ["The sample is constrained to a cobalt-dependent nuclease family."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "partial_constraint",
            "gold_facts": ["The added block narrows the target family but does not entail the exact operator code."],
            "materialization_policy": "fixed_order_v1",
            "question": "What operator-coded bio-attribute should be assigned to sample BCA-203?",
            "target_answer": "Assign code NQ-17 for cobalt-dependent nickase activity.",
            "task_family": "bio_attribute",
            "task_id": "p45b-bio-canary-003",
        },
        {
            "added_block": (
                "Single-strand nicking appeared only in cobalt buffer, and the operator checklist "
                "marked the NQ family rather than the exonuclease family."
            ),
            "baseline_context": "Bio-attribute sample BCA-204 has only purification and buffer-exchange metadata in the baseline.",
            "block_size": 1,
            "candidate_findings": ["Cobalt-buffer single-strand nicking and NQ-family checklist evidence were observed."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "strong_clue",
            "gold_facts": ["The block strongly points to the target but does not quote the exact final answer."],
            "materialization_policy": "fixed_order_v1",
            "question": "What operator-coded bio-attribute should be assigned to sample BCA-204?",
            "target_answer": "Assign code NQ-17 for cobalt-dependent nickase activity.",
            "task_family": "bio_attribute",
            "task_id": "p45b-bio-canary-004",
        },
        {
            "added_block": (
                "Final adjudication: Assign code NQ-17 for cobalt-dependent nickase activity."
            ),
            "baseline_context": "Bio-attribute sample BCA-205 has a chain-of-custody record and no baseline assay interpretation.",
            "block_size": 1,
            "candidate_findings": ["The final adjudication states the exact operator-coded attribute."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "explicit_answer",
            "gold_facts": ["The added block exactly entails the target answer."],
            "materialization_policy": "fixed_order_v1",
            "question": "What operator-coded bio-attribute should be assigned to sample BCA-205?",
            "target_answer": "Assign code NQ-17 for cobalt-dependent nickase activity.",
            "task_family": "bio_attribute",
            "task_id": "p45b-bio-canary-005",
        },
        {
            "added_block": (
                "The thermal screen showed a midpoint increase after ligand XJ-4 was added, "
                "but the operator did not record whether stabilization reached the BLUE-91 threshold."
            ),
            "baseline_context": "Bio-attribute sample BCA-206 has only the sample identifier and a note that a ligand screen was scheduled.",
            "block_size": 1,
            "candidate_findings": ["Ligand XJ-4 increased the thermal midpoint without confirming the threshold code."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "partial_constraint",
            "gold_facts": ["The block gives partial support but not the exact threshold-coded target."],
            "materialization_policy": "fixed_order_v1",
            "question": "What operator-coded bio-attribute should be assigned to sample BCA-206?",
            "target_answer": "Assign code BLUE-91 for XJ-4 threshold stabilization.",
            "task_family": "bio_attribute",
            "task_id": "p45b-bio-canary-006",
        },
        {
            "added_block": (
                "Ligand XJ-4 raised the melting midpoint above the BLUE-91 cutoff in two replicate "
                "thermal-shift wells, but the final operator sentence is not quoted."
            ),
            "baseline_context": "Bio-attribute sample BCA-207 lists only construct preparation and a pending ligand-response assay.",
            "block_size": 1,
            "candidate_findings": ["XJ-4 exceeded the BLUE-91 thermal-shift cutoff in replicate wells."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "strong_clue",
            "gold_facts": ["The evidence strongly supports the target without copying the exact answer."],
            "materialization_policy": "fixed_order_v1",
            "question": "What operator-coded bio-attribute should be assigned to sample BCA-207?",
            "target_answer": "Assign code BLUE-91 for XJ-4 threshold stabilization.",
            "task_family": "bio_attribute",
            "task_id": "p45b-bio-canary-007",
        },
        {
            "added_block": (
                "Final adjudication: Assign code BLUE-91 for XJ-4 threshold stabilization."
            ),
            "baseline_context": "Bio-attribute sample BCA-208 has no baseline assay interpretation beyond the run identifier.",
            "block_size": 1,
            "candidate_findings": ["The final adjudication states the exact BLUE-91 operator-coded attribute."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "explicit_answer",
            "gold_facts": ["The added block exactly entails the target answer."],
            "materialization_policy": "fixed_order_v1",
            "question": "What operator-coded bio-attribute should be assigned to sample BCA-208?",
            "target_answer": "Assign code BLUE-91 for XJ-4 threshold stabilization.",
            "task_family": "bio_attribute",
            "task_id": "p45b-bio-canary-008",
        },
    ]
    limit = int(sample_limit)
    if limit <= 0:
        raise BridgeDataGenerationValidationError("sample_limit must be positive")
    return deepcopy(packets[:limit])


def generate_logloss_positive_control_task_packets(sample_limit: int = 8) -> list[dict[str, Any]]:
    """Return deterministic P45c positive-control packets for fixed logloss only.

    The baseline omits the controlled target string, while the added block
    states it exactly. These rows contain no utility or measured logloss values.
    """

    targets = (
        ("MAVEN-7421", "specimen PC-001", "cryogenic marker registry code"),
        ("ORBIT-3197", "specimen PC-002", "membrane tag registry code"),
        ("LUMEN-5842", "specimen PC-003", "photostability registry code"),
        ("AXIOM-9073", "specimen PC-004", "binding-panel registry code"),
        ("QUANTA-2685", "specimen PC-005", "enzyme variant registry code"),
        ("NOVA-6314", "specimen PC-006", "folding assay registry code"),
        ("CIPHER-8059", "specimen PC-007", "transport marker registry code"),
        ("VECTOR-1468", "specimen PC-008", "interaction-screen registry code"),
        ("PRISM-4206", "specimen PC-009", "stability cluster registry code"),
        ("ZENITH-9730", "specimen PC-010", "rare-signal registry code"),
    )
    limit = int(sample_limit)
    if limit <= 0:
        raise BridgeDataGenerationValidationError("sample_limit must be positive")
    packets: list[dict[str, Any]] = []
    for index, (target, specimen, attribute) in enumerate(targets[:limit], start=1):
        packets.append(
            {
                "added_block": (
                    f"Positive-control registry entry: the {attribute} for {specimen} is exactly {target}."
                ),
                "baseline_context": (
                    f"{specimen} has a pending {attribute}. The baseline record contains handling metadata, "
                    "sample storage temperature, and assay queue position, but no registry code."
                ),
                "block_size": 1,
                "candidate_findings": [f"The added block explicitly states the {attribute} for {specimen}."],
                "candidate_slice_band": "top_L",
                "evidence_strength_band": "explicit_answer",
                "gold_facts": [
                    "The baseline context must not contain the target answer.",
                    "The added block must contain the exact target answer.",
                ],
                "materialization_policy": "fixed_order_v1",
                "question": (
                    f"Using only the supplied context, answer exactly with the {attribute} for {specimen}. "
                    "If the value is absent, answer UNKNOWN."
                ),
                "target_answer": target,
                "task_family": "bio_attribute",
                "task_id": f"p45c-logloss-positive-control-{index:03d}",
            }
        )
    return packets


def generate_graded_positive_control_task_packets(sample_limit: int = 8) -> list[dict[str, Any]]:
    """Return deterministic P45d graded positive-control bridge-canary packets.

    The design keeps P45c's low-prior target-answer contract while varying
    evidence strength. Diagnostic rows are reported but excluded from bridge fit.
    """

    packets = [
        {
            "added_block": (
                "The accession note only says the specimen was assigned to the registry queue after cold storage. "
                "No requested value is stated."
            ),
            "baseline_context": (
                "Specimen GPC-001 has a pending controlled registry value. The baseline includes only handling "
                "metadata and does not state the requested value."
            ),
            "block_size": 1,
            "bridge_fit_eligible": False,
            "bridge_fit_exclusion_reason": "diagnostic_irrelevant_evidence",
            "canary_design": "p45d_graded_positive_control",
            "candidate_findings": ["The added block is intentionally irrelevant to the requested value."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "irrelevant",
            "gold_facts": ["The row is a diagnostic stress row and should not enter bridge fit."],
            "materialization_policy": "fixed_order_v1",
            "question": (
                "Using only the supplied context, answer exactly with the requested value. "
                "If the value is not stated, answer UNKNOWN."
            ),
            "target_answer": "MAVEN-7421",
            "task_family": "bio_attribute",
            "task_id": "p45d-graded-positive-control-001",
        },
        {
            "added_block": (
                "A weak registry hint says the specimen belongs to an ORBIT-coded family, but no complete requested "
                "value is stated."
            ),
            "baseline_context": (
                "Specimen GPC-002 has a pending controlled registry value. The baseline includes only collection "
                "metadata and does not state the requested value."
            ),
            "block_size": 1,
            "bridge_fit_eligible": False,
            "bridge_fit_exclusion_reason": "diagnostic_weak_hint_without_exact_target",
            "canary_design": "p45d_graded_positive_control",
            "candidate_findings": ["The added block gives a weak family-level hint without the exact target."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "weak_hint",
            "gold_facts": ["The row is a diagnostic stress row and should not enter bridge fit."],
            "materialization_policy": "fixed_order_v1",
            "question": (
                "Using only the supplied context, answer exactly with the requested value. "
                "If the value is not stated, answer UNKNOWN."
            ),
            "target_answer": "ORBIT-3197",
            "task_family": "bio_attribute",
            "task_id": "p45d-graded-positive-control-002",
        },
        {
            "added_block": (
                "The registry shortlist for specimen GPC-003 contains three candidate values: RUNE-4401, "
                "LUMEN-5842, and TRACE-2014. The final requested value is not singled out."
            ),
            "baseline_context": (
                "Specimen GPC-003 has a pending controlled registry value. The baseline lists only assay scheduling "
                "metadata and does not state the requested value."
            ),
            "block_size": 1,
            "bridge_fit_eligible": True,
            "canary_design": "p45d_graded_positive_control",
            "candidate_findings": ["The exact target appears only as one candidate in a shortlist."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "partial_constraint",
            "gold_facts": ["The added block partially constrains the target but does not uniquely entail it."],
            "materialization_policy": "fixed_order_v1",
            "question": (
                "Using only the supplied context, answer exactly with the requested value. "
                "If the value is not stated, answer UNKNOWN."
            ),
            "target_answer": "LUMEN-5842",
            "task_family": "bio_attribute",
            "task_id": "p45d-graded-positive-control-003",
        },
        {
            "added_block": (
                "The registry note says the requested value is one of AXIOM-9073 or FJORD-1120, with AXIOM-9073 "
                "matching the current assay prefix."
            ),
            "baseline_context": (
                "Specimen GPC-004 has a pending controlled registry value. The baseline includes preparation "
                "metadata and does not state the requested value."
            ),
            "block_size": 1,
            "bridge_fit_eligible": True,
            "canary_design": "p45d_graded_positive_control",
            "candidate_findings": ["The exact target appears in a two-value constraint with a prefix hint."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "partial_constraint",
            "gold_facts": ["The added block gives partial support and should avoid exact-answer saturation."],
            "materialization_policy": "fixed_order_v1",
            "question": (
                "Using only the supplied context, answer exactly with the requested value. "
                "If the value is not stated, answer UNKNOWN."
            ),
            "target_answer": "AXIOM-9073",
            "task_family": "bio_attribute",
            "task_id": "p45d-graded-positive-control-004",
        },
        {
            "added_block": (
                "The audit trail strongly indicates QUANTA-2685 as the requested value for specimen GPC-005, "
                "but the final confirmation field is marked pending."
            ),
            "baseline_context": (
                "Specimen GPC-005 has a pending controlled registry value. The baseline lists only chain-of-custody "
                "metadata and does not state the requested value."
            ),
            "block_size": 1,
            "bridge_fit_eligible": True,
            "canary_design": "p45d_graded_positive_control",
            "candidate_findings": ["The exact target is strongly indicated but not final-confirmed."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "strong_clue",
            "gold_facts": ["The added block strongly supports the target but is not a final exact assertion."],
            "materialization_policy": "fixed_order_v1",
            "question": (
                "Using only the supplied context, answer exactly with the requested value. "
                "If the value is not stated, answer UNKNOWN."
            ),
            "target_answer": "QUANTA-2685",
            "task_family": "bio_attribute",
            "task_id": "p45d-graded-positive-control-005",
        },
        {
            "added_block": (
                "Two independent registry checks point to NOVA-6314 as the requested value for specimen GPC-006; "
                "the sign-off sentence is not quoted."
            ),
            "baseline_context": (
                "Specimen GPC-006 has a pending controlled registry value. The baseline includes only storage "
                "metadata and does not state the requested value."
            ),
            "block_size": 1,
            "bridge_fit_eligible": True,
            "canary_design": "p45d_graded_positive_control",
            "candidate_findings": ["The exact target is supported by two registry checks."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "strong_clue",
            "gold_facts": ["The added block strongly supports the target while preserving graded utility."],
            "materialization_policy": "fixed_order_v1",
            "question": (
                "Using only the supplied context, answer exactly with the requested value. "
                "If the value is not stated, answer UNKNOWN."
            ),
            "target_answer": "NOVA-6314",
            "task_family": "bio_attribute",
            "task_id": "p45d-graded-positive-control-006",
        },
        {
            "added_block": "Final registry field: the requested value for specimen GPC-007 is exactly CIPHER-8059.",
            "baseline_context": (
                "Specimen GPC-007 has a pending controlled registry value. The baseline includes only batch "
                "metadata and does not state the requested value."
            ),
            "block_size": 1,
            "bridge_fit_eligible": True,
            "canary_design": "p45d_graded_positive_control",
            "candidate_findings": ["The added block explicitly states the exact target."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "explicit_answer",
            "gold_facts": ["The added block exactly entails the target answer."],
            "materialization_policy": "fixed_order_v1",
            "question": (
                "Using only the supplied context, answer exactly with the requested value. "
                "If the value is not stated, answer UNKNOWN."
            ),
            "target_answer": "CIPHER-8059",
            "task_family": "bio_attribute",
            "task_id": "p45d-graded-positive-control-007",
        },
        {
            "added_block": "Final registry field: the requested value for specimen GPC-008 is exactly VECTOR-1468.",
            "baseline_context": (
                "Specimen GPC-008 has a pending controlled registry value. The baseline includes only run "
                "metadata and does not state the requested value."
            ),
            "block_size": 1,
            "bridge_fit_eligible": True,
            "canary_design": "p45d_graded_positive_control",
            "candidate_findings": ["The added block explicitly states the exact target."],
            "candidate_slice_band": "top_L",
            "evidence_strength_band": "explicit_answer",
            "gold_facts": ["The added block exactly entails the target answer."],
            "materialization_policy": "fixed_order_v1",
            "question": (
                "Using only the supplied context, answer exactly with the requested value. "
                "If the value is not stated, answer UNKNOWN."
            ),
            "target_answer": "VECTOR-1468",
            "task_family": "bio_attribute",
            "task_id": "p45d-graded-positive-control-008",
        },
    ]
    limit = int(sample_limit)
    if limit <= 0:
        raise BridgeDataGenerationValidationError("sample_limit must be positive")
    return deepcopy(packets[:limit])


def generate_candidate_set_constrained_task_packets(sample_limit: int = 8) -> list[dict[str, Any]]:
    """Return deterministic P45e canary packets for candidate-set identification."""

    candidate_set = [
        "MAVEN-7421",
        "ORBIT-3197",
        "LUMEN-5842",
        "NOVA-9061",
        "AXIOM-9073",
        "CIPHER-8059",
        "VECTOR-1468",
        "PRISM-4206",
    ]
    question = (
        "Using only the supplied context, choose the correct registry code from the candidate list: "
        f"{', '.join(candidate_set)}. If the context does not identify one candidate, answer UNKNOWN. "
        "Return only the selected code or UNKNOWN."
    )
    shared = {
        "block_size": 1,
        "candidate_answer_set": candidate_set,
        "candidate_set_size_before": len(candidate_set),
        "candidate_slice_band": "top_L",
        "canary_design": "p45e_candidate_set_constrained_bridge",
        "materialization_policy": "fixed_order_v1",
        "question": question,
        "task_family": "bio_attribute",
    }
    rows = [
        {
            **shared,
            "added_block": (
                "Registry audit note: the specimen was queued for candidate-set review, but no candidate code "
                "was removed and no correct code was identified."
            ),
            "baseline_context": (
                "Specimen CSC-001 is awaiting candidate-set registry assignment. The baseline includes handling "
                "metadata only and does not identify any candidate code."
            ),
            "bridge_fit_eligible": False,
            "bridge_fit_exclusion_reason": "diagnostic_no_candidate_narrowing",
            "candidate_findings": ["The added block intentionally leaves all candidates plausible."],
            "candidate_set_size_after": 8,
            "evidence_strength_band": "irrelevant",
            "gold_facts": ["No candidate is narrowed; this diagnostic row should not enter bridge fit."],
            "target_answer": "MAVEN-7421",
            "task_id": "p45e-candidate-set-canary-001",
        },
        {
            **shared,
            "added_block": (
                "Registry audit note: the correct code is in the family containing MAVEN-7421, ORBIT-3197, "
                "LUMEN-5842, or NOVA-9061; the other candidates can be removed."
            ),
            "baseline_context": (
                "Specimen CSC-002 is awaiting candidate-set registry assignment. The baseline includes shipment "
                "metadata only and does not identify any candidate code."
            ),
            "bridge_fit_eligible": False,
            "bridge_fit_exclusion_reason": "diagnostic_weak_candidate_narrowing",
            "candidate_findings": ["The added block narrows the list weakly but leaves four candidates."],
            "candidate_set_size_after": 4,
            "evidence_strength_band": "weak_hint",
            "gold_facts": ["The row is diagnostic because four candidates remain plausible."],
            "target_answer": "NOVA-9061",
            "task_id": "p45e-candidate-set-canary-002",
        },
        {
            **shared,
            "added_block": (
                "Registry audit note: the only plausible candidate codes for specimen CSC-003 are ORBIT-3197 "
                "and VECTOR-1468. The note does not resolve the tie."
            ),
            "baseline_context": (
                "Specimen CSC-003 is awaiting candidate-set registry assignment. The baseline records only "
                "storage metadata and does not identify any candidate code."
            ),
            "bridge_fit_eligible": True,
            "candidate_findings": ["The added block narrows the candidate set to two plausible codes."],
            "candidate_set_size_after": 2,
            "evidence_strength_band": "partial_constraint",
            "gold_facts": ["Two candidates remain plausible; target-identification support is partial."],
            "target_answer": "ORBIT-3197",
            "task_id": "p45e-candidate-set-canary-003",
        },
        {
            **shared,
            "added_block": (
                "Registry audit note: the only plausible candidate codes for specimen CSC-004 are CIPHER-8059 "
                "and AXIOM-9073. The note does not resolve the tie."
            ),
            "baseline_context": (
                "Specimen CSC-004 is awaiting candidate-set registry assignment. The baseline records only "
                "queue metadata and does not identify any candidate code."
            ),
            "bridge_fit_eligible": True,
            "candidate_findings": ["The added block narrows the candidate set to two plausible codes."],
            "candidate_set_size_after": 2,
            "evidence_strength_band": "partial_constraint",
            "gold_facts": ["Two candidates remain plausible; target-identification support is partial."],
            "target_answer": "CIPHER-8059",
            "task_id": "p45e-candidate-set-canary-004",
        },
        {
            **shared,
            "added_block": (
                "Registry audit note: LUMEN-5842 matches the primary assay marker for specimen CSC-005. "
                "One secondary confirmation field is pending, so minor ambiguity remains."
            ),
            "baseline_context": (
                "Specimen CSC-005 is awaiting candidate-set registry assignment. The baseline records only "
                "preparation metadata and does not identify any candidate code."
            ),
            "bridge_fit_eligible": True,
            "candidate_findings": ["The added block nearly identifies the target but leaves a pending check."],
            "candidate_set_size_after": 2,
            "evidence_strength_band": "strong_clue",
            "gold_facts": ["The target is nearly identified but one minor ambiguity remains."],
            "target_answer": "LUMEN-5842",
            "task_id": "p45e-candidate-set-canary-005",
        },
        {
            **shared,
            "added_block": (
                "Registry audit note: AXIOM-9073 matches the primary assay marker for specimen CSC-006. "
                "One secondary confirmation field is pending, so minor ambiguity remains."
            ),
            "baseline_context": (
                "Specimen CSC-006 is awaiting candidate-set registry assignment. The baseline records only "
                "batch metadata and does not identify any candidate code."
            ),
            "bridge_fit_eligible": True,
            "candidate_findings": ["The added block nearly identifies the target but leaves a pending check."],
            "candidate_set_size_after": 2,
            "evidence_strength_band": "strong_clue",
            "gold_facts": ["The target is nearly identified but one minor ambiguity remains."],
            "target_answer": "AXIOM-9073",
            "task_id": "p45e-candidate-set-canary-006",
        },
        {
            **shared,
            "added_block": "Final registry audit: the correct candidate code for specimen CSC-007 is exactly MAVEN-7421.",
            "baseline_context": (
                "Specimen CSC-007 is awaiting candidate-set registry assignment. The baseline records only "
                "run metadata and does not identify any candidate code."
            ),
            "bridge_fit_eligible": True,
            "candidate_findings": ["The added block uniquely identifies the exact target."],
            "candidate_set_size_after": 1,
            "evidence_strength_band": "explicit_answer",
            "gold_facts": ["The correct target is uniquely identified."],
            "target_answer": "MAVEN-7421",
            "task_id": "p45e-candidate-set-canary-007",
        },
        {
            **shared,
            "added_block": "Final registry audit: the correct candidate code for specimen CSC-008 is exactly PRISM-4206.",
            "baseline_context": (
                "Specimen CSC-008 is awaiting candidate-set registry assignment. The baseline records only "
                "run metadata and does not identify any candidate code."
            ),
            "bridge_fit_eligible": True,
            "candidate_findings": ["The added block uniquely identifies the exact target."],
            "candidate_set_size_after": 1,
            "evidence_strength_band": "explicit_answer",
            "gold_facts": ["The correct target is uniquely identified."],
            "target_answer": "PRISM-4206",
            "task_id": "p45e-candidate-set-canary-008",
        },
    ]
    limit = int(sample_limit)
    if limit <= 0:
        raise BridgeDataGenerationValidationError("sample_limit must be positive")
    return deepcopy(rows[:limit])


def _normalize_task_packet(raw: Mapping[str, Any], index: int) -> dict[str, Any]:
    missing = [field for field in REQUIRED_TASK_FIELDS if field not in raw]
    if missing:
        raise BridgeDataGenerationValidationError(
            f"task packet {index}: missing required fields: {', '.join(missing)}"
        )
    packet = {
        "added_block": str(raw["added_block"]),
        "baseline_context": str(raw["baseline_context"]),
        "candidate_answer_set": [str(value) for value in raw.get("candidate_answer_set") or []],
        "candidate_findings": [str(value) for value in raw.get("candidate_findings") or []],
        "gold_facts": [str(value) for value in raw.get("gold_facts") or []],
        "question": str(raw["question"]),
        "target_answer": str(raw["target_answer"]),
        "task_id": str(raw["task_id"]),
    }
    for field in (
        "task_family",
        "materialization_policy",
        "candidate_slice_band",
        "evidence_strength_band",
        "bridge_fit_exclusion_reason",
        "canary_design",
    ):
        if field in raw and str(raw.get(field, "")).strip():
            packet[field] = str(raw[field]).strip()
    if "block_size" in raw and str(raw.get("block_size", "")).strip():
        packet["block_size"] = int(raw["block_size"])
    for field in ("candidate_set_size_before", "candidate_set_size_after"):
        if field in raw and str(raw.get(field, "")).strip():
            packet[field] = int(raw[field])
    if "bridge_fit_eligible" in raw:
        packet["bridge_fit_eligible"] = _as_bool(raw.get("bridge_fit_eligible"))
    if "evidence_strength_band" in packet and packet["evidence_strength_band"] not in EVIDENCE_STRENGTH_BANDS:
        raise BridgeDataGenerationValidationError(
            f"task packet {index}: evidence_strength_band must be one of {', '.join(EVIDENCE_STRENGTH_BANDS)}"
        )
    for field in ("task_id", "question", "target_answer", "baseline_context", "added_block"):
        if not packet[field].strip():
            raise BridgeDataGenerationValidationError(f"task packet {index}: {field} must be non-empty")
    return packet


def _normalize_task_packets(
    task_packets: Sequence[Mapping[str, Any]] | None,
    config: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    task_packet_mode = "" if config is None else str(config.get("task_packet_mode") or "")
    if task_packets is None and task_packet_mode == TASK_PACKET_MODE_BRIDGE_CANARY:
        raw_packets = generate_bridge_canary_task_packets(int(config.get("sample_limit") or 8))
    elif task_packets is None and task_packet_mode == TASK_PACKET_MODE_BRIDGE_CANARY_V3:
        raw_packets = generate_graded_positive_control_task_packets(min(int(config.get("sample_limit") or 8), 8))
    elif task_packets is None and task_packet_mode == TASK_PACKET_MODE_BRIDGE_CANARY_V4:
        raw_packets = generate_candidate_set_constrained_task_packets(min(int(config.get("sample_limit") or 8), 8))
    elif task_packets is None and task_packet_mode == TASK_PACKET_MODE_LOGLOSS_POSITIVE_CONTROL:
        raw_packets = generate_logloss_positive_control_task_packets(int(config.get("sample_limit") or 8))
    else:
        raw_packets = list(task_packets or _default_task_packets())
    normalized = [_normalize_task_packet(raw, index) for index, raw in enumerate(raw_packets, start=1)]
    return sorted(normalized, key=lambda row: row["task_id"])


def _planned_prompts(task_packets: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    prompts = []
    for packet in task_packets:
        prompts.append(
            {
                "logloss_prompt_preview": {
                    "context_without": packet["baseline_context"],
                    "context_with": f"{packet['baseline_context']}\n\n{packet['added_block']}",
                    "question": packet["question"],
                    "target_answer": packet["target_answer"],
                    "candidate_answer_set": packet.get("candidate_answer_set", []),
                },
                "review_prompt_preview": {
                    "candidate_findings": packet["candidate_findings"],
                    "evidence_strength_band": packet.get("evidence_strength_band", ""),
                    "gold_facts": packet["gold_facts"],
                    "question": packet["question"],
                    "target_answer": packet["target_answer"],
                    "candidate_answer_set": packet.get("candidate_answer_set", []),
                },
                "task_id": packet["task_id"],
            }
        )
    return prompts


def _schema_example(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "block_id": "OPERATOR_OR_API_GENERATED_BLOCK_ID",
        "block_size": int(config["block_size"]),
        "candidate_slice_band": str(config["candidate_slice_band"]),
        "candidate_set_size_after": "CANDIDATE_SET_SIZE_AFTER_IF_AVAILABLE",
        "candidate_set_size_before": "CANDIDATE_SET_SIZE_BEFORE_IF_AVAILABLE",
        "context_id": "OPERATOR_OR_API_GENERATED_CONTEXT_ID",
        "data_origin": "api_generated",
        "delta_logloss": "MEASURED_LOGPROB_ONLY",
        "delta_logloss_source": "measured_logprob",
        "delta_utility": "STRONG_MODEL_ADJUDICATED_NUMERIC",
        "delta_utility_source": "strong_model_adjudicated",
        "evidence_strength_band": "explicit_answer",
        "materialization_policy": str(config["materialization_policy"]),
        "metric": str(config["metric"]),
        "model_tier": str(config["fixed_model_id"] or "OPERATOR_FIXED_MODEL_ID"),
        "notes": "api-generated scaffold row; requires P45 dry validation before artifacts",
        "pair_id": "OPERATOR_OR_API_GENERATED_PAIR_ID",
        "replicate_count": 1,
        "review_status": "accepted",
        "source": "operator_provided",
        "stratum_id": str(config["active_stratum_id"]),
        "task_family": str(config["task_family"]),
        "utility_rationale": "STRONG_MODEL_UTILITY_RATIONALE",
        "utility_with": "STRONG_MODEL_UTILITY_WITH",
        "utility_without": "STRONG_MODEL_UTILITY_WITHOUT",
    }


def _normalize_config(config_path: str | Path) -> dict[str, Any]:
    config = {**DEFAULT_CONFIG, **_read_json(Path(config_path))}
    mode = str(config.get("mode") or MODE_DRY_RUN)
    if mode not in {MODE_DRY_RUN, MODE_LIVE}:
        raise BridgeDataGenerationValidationError(f"unsupported bridge data generation mode: {mode}")
    config["mode"] = mode
    task_packet_mode = str(config.get("task_packet_mode") or TASK_PACKET_MODE_PLACEHOLDER)
    if task_packet_mode not in {
        TASK_PACKET_MODE_PLACEHOLDER,
        TASK_PACKET_MODE_BRIDGE_CANARY,
        TASK_PACKET_MODE_BRIDGE_CANARY_V3,
        TASK_PACKET_MODE_BRIDGE_CANARY_V4,
        TASK_PACKET_MODE_LOGLOSS_POSITIVE_CONTROL,
    }:
        raise BridgeDataGenerationValidationError(f"unsupported task_packet_mode: {task_packet_mode}")
    config["task_packet_mode"] = task_packet_mode
    config["block_size"] = int(config.get("block_size") or 1)
    if config["block_size"] <= 0:
        raise BridgeDataGenerationValidationError("block_size must be positive")
    raw_min_delta = config.get(
        "minimum_abs_delta_logloss_for_bridge_evidence",
        DEFAULT_CONFIG["minimum_abs_delta_logloss_for_bridge_evidence"],
    )
    config["minimum_abs_delta_logloss_for_bridge_evidence"] = float(raw_min_delta)
    if config["minimum_abs_delta_logloss_for_bridge_evidence"] < 0:
        raise BridgeDataGenerationValidationError("minimum_abs_delta_logloss_for_bridge_evidence must be non-negative")
    return config


def preflight_bridge_data_generation_provider(
    *,
    config_path: str | Path = LOCAL_LIVE_CONFIG_PATH,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Validate local live-provider wiring without calling a provider or exposing secrets."""

    config_file = Path(config_path)
    env_map = _env_values(env)
    checks: list[dict[str, Any]] = []
    if not config_file.exists():
        checks.append(_check("local_config_exists", False, f"missing: {config_file}"))
        return {
            "ready": False,
            "checks": checks,
            "config_path": str(config_file),
            "live_api_called": False,
            "secret_values_exposed": False,
        }

    try:
        config = _normalize_config(config_file)
        checks.append(_check("local_config_exists", True, "present"))
    except BridgeDataGenerationValidationError as exc:
        checks.append(_check("local_config_valid", False, str(exc)))
        return {
            "ready": False,
            "checks": checks,
            "config_path": str(config_file),
            "live_api_called": False,
            "secret_values_exposed": False,
        }

    for env_name in LIVE_GATE_ENV_VARS:
        checks.append(
            _check(
                env_name,
                env_map.get(env_name) == "1",
                "set" if env_map.get(env_name) == "1" else "missing_or_not_1",
            )
        )
    checks.append(
        _check(
            "mode_live_operator_approved",
            str(config.get("mode")) == MODE_LIVE,
            str(config.get("mode") or ""),
        )
    )
    checks.append(
        _check(
            "operator_approval_true",
            _as_bool(config.get("operator_approval")) is True,
            "true" if _as_bool(config.get("operator_approval")) is True else "false",
        )
    )
    for field in ("provider_profile", "fixed_model_id", "strong_review_model_id"):
        checks.append(
            _check(
                f"{field}_non_empty",
                bool(str(config.get(field) or "").strip()),
                "set" if str(config.get(field) or "").strip() else "missing",
            )
        )

    profile_name = str(config.get("provider_profile") or "").strip()
    profile = None
    if profile_name:
        try:
            profile = get_api_profile(profile_name)
            checks.append(_check("provider_profile_known", True, profile.profile_name))
        except ValueError as exc:
            checks.append(_check("provider_profile_known", False, str(exc)))
    else:
        checks.append(_check("provider_profile_known", False, "missing"))

    if profile is not None:
        checks.append(
            _check(
                "provider_api_style_supported",
                profile.api_style == "openai_chat_compatible",
                profile.api_style,
            )
        )
        checks.append(
            _check(
                "provider_logprob_ready",
                bool(profile.phase1_logprob_ready),
                "logprob-ready" if profile.phase1_logprob_ready else "not logprob-ready",
            )
        )
        credential_source_kind, local_credential_file = _credential_source_kind(
            config=config,
            config_path=config_file,
            env_map=env_map,
            api_key_env=profile.api_key_env,
        )
        api_key_present = credential_source_kind != "missing"
        checks.append(
            _check(
                "provider_credential_source_present",
                api_key_present,
                credential_source_kind,
            )
        )
        if local_credential_file is not None:
            checks.append(
                _check(
                    "provider_local_credential_file_exists",
                    local_credential_file.exists(),
                    "present" if local_credential_file.exists() else "missing",
                )
            )
        base_url_present = bool(env_map.get("API_BASE_URL") or env_map.get(profile.base_url_env) or profile.default_base_url)
        checks.append(
            _check(
                "provider_base_url_available",
                base_url_present,
                f"{profile.base_url_env}, API_BASE_URL, or profile default",
            )
        )

    ready = all(bool(check["passed"]) for check in checks)
    return {
        "api_key_env": "" if profile is None else profile.api_key_env,
        "base_url_env": "" if profile is None else profile.base_url_env,
        "checks": checks,
        "config_path": str(config_file),
        "credential_source_kind": "missing" if profile is None else credential_source_kind,
        "fixed_model_id": str(config.get("fixed_model_id") or ""),
        "live_api_called": False,
        "provider_profile": profile_name,
        "ready": ready,
        "secret_values_exposed": False,
        "strong_review_model_id": str(config.get("strong_review_model_id") or ""),
    }


def _failed_preflight_names(preflight: Mapping[str, Any]) -> list[str]:
    return [str(check["name"]) for check in preflight.get("checks") or () if not bool(check.get("passed"))]


def _require_live_provider_preflight(
    *,
    config_path: str | Path,
    env: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], ResolvedApiProfile, dict[str, Any]]:
    preflight = preflight_bridge_data_generation_provider(config_path=config_path, env=env)
    if not preflight["ready"]:
        failed = _failed_preflight_names(preflight)
        if "local_config_exists" in failed:
            raise BridgeDataGenerationGateError(f"local live config does not exist: {Path(config_path)}")
        if "provider_logprob_ready" in failed:
            raise BridgeDataGenerationGateError("provider profile is not logprob-ready for fixed-model logloss")
        raise BridgeDataGenerationGateError(f"live provider preflight failed: {', '.join(failed)}")
    config = _normalize_config(config_path)
    env_map = _env_values(env)
    profile = get_api_profile(str(config.get("provider_profile") or ""))
    source_kind, local_credential_file = _credential_source_kind(
        config=config,
        config_path=config_path,
        env_map=env_map,
        api_key_env=profile.api_key_env,
    )
    if source_kind == "local_credential_file" and local_credential_file is not None:
        try:
            env_map[profile.api_key_env] = extract_api_key_from_csv(local_credential_file)
        except (OSError, ValueError) as exc:
            raise BridgeDataGenerationGateError(
                f"local credential file could not be loaded for provider env {profile.api_key_env}"
            ) from exc
    resolved_profile = resolve_api_profile(
        env_values=env_map,
        profile_name=str(config.get("provider_profile") or ""),
    )
    return config, resolved_profile, dict(preflight)


def _validate_live_gates(
    *,
    config: Mapping[str, Any],
    logloss_scorer: TaskPacketFn | None,
    utility_reviewer: TaskPacketFn | None,
    adjudicator: AdjudicatorFn | None,
    env: Mapping[str, str] | None = None,
) -> None:
    if config["mode"] != MODE_LIVE:
        return
    env_map = _env_values(env)
    if env_map.get("CPS_ALLOW_LIVE_API") != "1":
        raise BridgeDataGenerationGateError("CPS_ALLOW_LIVE_API=1 is required for live_operator_approved mode")
    if env_map.get("P45_ALLOW_API_DATA_GENERATION") != "1":
        raise BridgeDataGenerationGateError(
            "P45_ALLOW_API_DATA_GENERATION=1 is required for live_operator_approved mode"
        )
    if _as_bool(config.get("operator_approval")) is not True:
        raise BridgeDataGenerationGateError("operator_approval must be true for live_operator_approved mode")
    missing = [
        field
        for field in ("provider_profile", "fixed_model_id", "strong_review_model_id")
        if str(config.get(field) or "").strip() == ""
    ]
    if missing:
        raise BridgeDataGenerationGateError(f"missing required live config fields: {', '.join(missing)}")
    if logloss_scorer is None or utility_reviewer is None or adjudicator is None:
        raise BridgeDataGenerationGateError(
            "logloss_scorer, utility_reviewer, and adjudicator are required for live_operator_approved mode"
        )


def _validate_logloss_only_live_gates(
    *,
    config: Mapping[str, Any],
    logloss_scorer: TaskPacketFn | None,
    env: Mapping[str, str] | None = None,
) -> None:
    if config["mode"] != MODE_LIVE:
        return
    env_map = _env_values(env)
    if env_map.get("CPS_ALLOW_LIVE_API") != "1":
        raise BridgeDataGenerationGateError("CPS_ALLOW_LIVE_API=1 is required for live_operator_approved mode")
    if env_map.get("P45_ALLOW_API_DATA_GENERATION") != "1":
        raise BridgeDataGenerationGateError(
            "P45_ALLOW_API_DATA_GENERATION=1 is required for live_operator_approved mode"
        )
    if _as_bool(config.get("operator_approval")) is not True:
        raise BridgeDataGenerationGateError("operator_approval must be true for live_operator_approved mode")
    missing = [
        field
        for field in ("provider_profile", "fixed_model_id")
        if str(config.get(field) or "").strip() == ""
    ]
    if missing:
        raise BridgeDataGenerationGateError(f"missing required live config fields: {', '.join(missing)}")
    if logloss_scorer is None:
        raise BridgeDataGenerationGateError("logloss_scorer is required for P45c logloss positive-control mode")


def _valid_token_logprobs(values: Any) -> bool:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return False
    try:
        parsed = [float(value) for value in values]
    except (TypeError, ValueError):
        return False
    if not parsed:
        return False
    if not all(math.isfinite(value) for value in parsed):
        return False
    return not all(abs(value) <= 1e-12 for value in parsed)


def _validate_logloss(
    payload: Mapping[str, Any],
    *,
    minimum_abs_delta_logloss_for_bridge_evidence: float = 0.0,
) -> tuple[dict[str, Any], list[str]]:
    row = deepcopy(dict(payload))
    reason_codes: list[str] = []
    source = str(row.get("logloss_source") or "")
    logprob_available = _as_bool(row.get("logprob_available"))
    loss_without = _finite_float_or_none(row.get("loss_without"))
    loss_with = _finite_float_or_none(row.get("loss_with"))
    supplied_delta = _finite_float_or_none(row.get("delta_logloss"))

    if not logprob_available:
        reason_codes.append("logprob_unavailable")
    if source != "measured_logprob":
        reason_codes.append("delta_logloss_not_measured_logprob")
    if loss_without is None or loss_with is None:
        reason_codes.append("missing_measured_logloss")
    if not _valid_token_logprobs(row.get("token_logprobs_without")):
        reason_codes.append("missing_or_degenerate_logprobs_without")
    if not _valid_token_logprobs(row.get("token_logprobs_with")):
        reason_codes.append("missing_or_degenerate_logprobs_with")

    computed_delta = None if loss_without is None or loss_with is None else loss_without - loss_with
    if supplied_delta is not None and computed_delta is not None and abs(supplied_delta - computed_delta) > 1e-9:
        reason_codes.append("delta_logloss_mismatch")
    min_abs_delta = float(minimum_abs_delta_logloss_for_bridge_evidence)
    if computed_delta is not None:
        if min_abs_delta > 0.0 and abs(computed_delta) < min_abs_delta:
            reason_codes.append("delta_logloss_below_informative_threshold")
        if computed_delta < 0.0:
            reason_codes.append("negative_delta_logloss")

    row["loss_without"] = loss_without
    row["loss_with"] = loss_with
    row["delta_logloss"] = computed_delta
    row["logloss_source"] = source
    row["logprob_available"] = logprob_available
    row["minimum_abs_delta_logloss_for_bridge_evidence"] = min_abs_delta
    return row, sorted(set(reason_codes))


def _validate_utility(payload: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    row = deepcopy(dict(payload))
    reason_codes: list[str] = []
    if any(field in row and row.get(field) not in (None, "") for field in ("delta_logloss", "loss_without", "loss_with", "logloss_source", "delta_logloss_source")):
        reason_codes.append("utility_reviewer_supplied_logloss")
    utility_without = _finite_float_or_none(row.get("utility_without"))
    utility_with = _finite_float_or_none(row.get("utility_with"))
    supplied_delta = _finite_float_or_none(row.get("delta_utility"))
    if utility_without is None or utility_with is None:
        reason_codes.append("missing_utility_score")
    for score_name, score_value in (("utility_without", utility_without), ("utility_with", utility_with)):
        if score_value is not None and not 0.0 <= score_value <= 1.0:
            reason_codes.append(f"{score_name}_out_of_range")
    computed_delta = None if utility_without is None or utility_with is None else utility_with - utility_without
    if supplied_delta is not None and computed_delta is not None and abs(supplied_delta - computed_delta) > 1e-9:
        reason_codes.append("delta_utility_mismatch")
    row["utility_without"] = utility_without
    row["utility_with"] = utility_with
    row["delta_utility"] = computed_delta
    utility_rationale = str(row.get("utility_rationale") or row.get("sufficiency_rationale") or "")
    row["sufficiency_rationale"] = utility_rationale
    row["utility_rationale"] = utility_rationale
    for field in ("candidate_set_size_before", "candidate_set_size_after"):
        if field in row and str(row.get(field, "")).strip():
            parsed = _finite_float_or_none(row.get(field))
            if parsed is None:
                reason_codes.append(f"{field}_invalid")
            else:
                row[field] = parsed
    reviewer_band = str(row.get("evidence_strength_band") or "")
    if reviewer_band and reviewer_band not in EVIDENCE_STRENGTH_BANDS:
        row["reviewer_evidence_strength_band"] = reviewer_band
        row["evidence_strength_band"] = ""
    return row, sorted(set(reason_codes))


def _assistant_content(response_payload: Mapping[str, Any]) -> str:
    choice = ((response_payload.get("choices") or [{}])[0]) if isinstance(response_payload, Mapping) else {}
    if not isinstance(choice, Mapping):
        raise ValueError("unexpected provider choice payload")
    message = choice.get("message") or {}
    if not isinstance(message, Mapping):
        raise ValueError("unexpected provider message payload")
    if message.get("reasoning_content"):
        raise ValueError("provider returned reasoning_content, which is not allowed for P45 calibration scoring")
    return str(message.get("content") or choice.get("text") or "")


def _provider_json_object(response_payload: Mapping[str, Any]) -> dict[str, Any]:
    content = _assistant_content(response_payload).strip()
    if content.startswith("```"):
        lines = [line for line in content.splitlines() if not line.strip().startswith("```")]
        content = "\n".join(lines).strip()
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("provider JSON response must be an object")
    return payload


def _extract_provider_token_logprobs(response_payload: Mapping[str, Any], *, target_answer: str) -> tuple[float, tuple[float, ...]]:
    choice = ((response_payload.get("choices") or [{}])[0]) if isinstance(response_payload, Mapping) else {}
    if not isinstance(choice, Mapping):
        raise ValueError("unexpected provider choice payload")
    message = choice.get("message") or {}
    if not isinstance(message, Mapping):
        raise ValueError("unexpected provider message payload")
    if message.get("reasoning_content"):
        raise ValueError("provider returned reasoning_content for fixed-model logloss")
    content = str(message.get("content") or choice.get("text") or "")
    if content.strip() != str(target_answer).strip():
        raise ValueError("provider did not replay the target answer exactly")
    logprobs_block = message.get("logprobs") or choice.get("logprobs") or {}
    if not isinstance(logprobs_block, Mapping):
        raise ValueError("provider logprobs payload is missing or malformed")
    logprob_items = logprobs_block.get("content") or []
    token_logprobs = tuple(float(item["logprob"]) for item in logprob_items if isinstance(item, Mapping) and "logprob" in item)
    if not _valid_token_logprobs(token_logprobs):
        raise ValueError("provider did not return usable token logprobs")
    return -sum(token_logprobs), token_logprobs


class OpenAICompatibleBridgeProvider:
    def __init__(self, *, client: Any, config: Mapping[str, Any]) -> None:
        self.client = client
        self.config = dict(config)
        self.fixed_model_id = str(config["fixed_model_id"])
        self.strong_review_model_id = str(config["strong_review_model_id"])
        self.timeout = int(config.get("request_timeout_seconds") or 60)
        self.seed = int(config.get("seed") or 20260510)

    def logloss_scorer(self, packet: Mapping[str, Any]) -> dict[str, Any]:
        try:
            loss_without, token_logprobs_without = self._measure_loss(
                packet=packet,
                context=str(packet["baseline_context"]),
            )
            loss_with, token_logprobs_with = self._measure_loss(
                packet=packet,
                context=f"{packet['baseline_context']}\n\n{packet['added_block']}",
            )
        except (KeyError, TypeError, ValueError, RuntimeError) as exc:
            return {
                "delta_logloss": None,
                "logprob_available": False,
                "logloss_source": "unavailable",
                "loss_with": None,
                "loss_without": None,
                "provider_error_type": type(exc).__name__,
            }
        return {
            "delta_logloss": loss_without - loss_with,
            "logprob_available": True,
            "logloss_source": "measured_logprob",
            "loss_with": loss_with,
            "loss_without": loss_without,
            "token_logprobs_with": list(token_logprobs_with),
            "token_logprobs_without": list(token_logprobs_without),
        }

    def utility_reviewer(self, packet: Mapping[str, Any]) -> dict[str, Any]:
        try:
            payload = _provider_json_object(
                self.client.chat_completion(
                    model=self.strong_review_model_id,
                    messages=self._review_messages(packet),
                    max_completion_tokens=int(self.config.get("review_max_completion_tokens") or 384),
                    temperature=float(self.config.get("review_temperature") or 0.0),
                    seed=self.seed,
                    stream=False,
                    n=1,
                    extra_body=self._extra_body("review_extra_body"),
                    timeout=self.timeout,
                )
            )
        except (KeyError, TypeError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            return {
                "delta_utility": None,
                "sufficiency_rationale": f"utility_reviewer_unavailable:{type(exc).__name__}",
                "utility_with": None,
                "utility_without": None,
            }
        payload.setdefault("delta_utility_source", "strong_model_adjudicated")
        return payload

    def adjudicator(self, packet: Mapping[str, Any], logloss: Mapping[str, Any], review: Mapping[str, Any]) -> dict[str, Any]:
        try:
            return _provider_json_object(
                self.client.chat_completion(
                    model=self.strong_review_model_id,
                    messages=self._adjudication_messages(packet, logloss, review),
                    max_completion_tokens=int(self.config.get("adjudication_max_completion_tokens") or 256),
                    temperature=float(self.config.get("adjudication_temperature") or 0.0),
                    seed=self.seed,
                    stream=False,
                    n=1,
                    extra_body=self._extra_body("adjudication_extra_body"),
                    timeout=self.timeout,
                )
            )
        except (KeyError, TypeError, ValueError, RuntimeError, json.JSONDecodeError):
            return {
                "intervention_valid": False,
                "no_duplicate_trivial_case": False,
                "no_leakage": False,
                "review_status": "ambiguous",
                "target_clear": False,
                "utility_score_consistent": False,
            }

    def _measure_loss(self, *, packet: Mapping[str, Any], context: str) -> tuple[float, tuple[float, ...]]:
        response = self.client.chat_completion(
            model=self.fixed_model_id,
            messages=self._logloss_messages(packet=packet, context=context),
            max_completion_tokens=self._logloss_max_tokens(packet),
            temperature=0.0,
            seed=self.seed,
            stream=False,
            n=1,
            logprobs=True,
            top_logprobs=0,
            extra_body=self._extra_body("logloss_extra_body"),
            timeout=self.timeout,
        )
        return _extract_provider_token_logprobs(response, target_answer=str(packet["target_answer"]))

    def _extra_body(self, key: str) -> dict[str, Any]:
        value = self.config.get(key)
        if value is None:
            value = self.config.get("provider_extra_body")
        if isinstance(value, Mapping):
            return dict(value)
        return {"enable_thinking": False}

    def _logloss_max_tokens(self, packet: Mapping[str, Any]) -> int:
        configured = self.config.get("logloss_max_completion_tokens")
        if configured is not None:
            return int(configured)
        return max(16, len(str(packet["target_answer"]).split()) + 8)

    @staticmethod
    def _logloss_messages(*, packet: Mapping[str, Any], context: str) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": "Repeat the target answer exactly and output nothing else. This request is used only to measure output token logprobs.",
            },
            {
                "role": "user",
                "content": (
                    f"Context:\n{context}\n\n"
                    f"Question: {packet['question']}\n"
                    f"Target answer: {packet['target_answer']}"
                ),
            },
        ]

    @staticmethod
    def _review_messages(packet: Mapping[str, Any]) -> list[dict[str, str]]:
        if packet.get("candidate_answer_set"):
            system_content = (
                "Return JSON only with utility_without, utility_with, delta_utility, "
                "utility_rationale, sufficiency_rationale, evidence_strength_band, "
                "candidate_set_size_before, and candidate_set_size_after. "
                "Score target-identification support over the supplied candidate answer set, using only the supplied "
                "context and candidate block; ignore world knowledge. Use this 0.00 to 1.00 rubric: "
                "0.00=context does not reduce candidate uncertainty, 0.25=context weakly narrows the candidate set, "
                "0.50=context narrows to two plausible candidates, 0.75=context nearly identifies the target but "
                "leaves minor ambiguity, 1.00=context uniquely identifies the exact target. "
                "Compute delta_utility as utility_with - utility_without. "
                "Do not include delta_logloss, loss_without, loss_with, or any log-loss field."
            )
        else:
            system_content = (
                "Return JSON only with utility_without, utility_with, delta_utility, "
                "utility_rationale, sufficiency_rationale, and evidence_strength_band. "
                "Use only the supplied context and candidate block; ignore world knowledge. "
                "Use this evidence sufficiency rubric on a 0.00 to 1.00 scale: "
                "0.00=no support, 0.25=weak clue only, 0.50=partial constraint, "
                "0.75=strong but ambiguous, 1.00=exact target entailed. "
                "Compute delta_utility as utility_with - utility_without. "
                "Do not include delta_logloss, loss_without, loss_with, or any log-loss field."
            )
        return [
            {
                "role": "system",
                "content": system_content,
            },
            {
                "role": "user",
                "content": _stable_json(
                    {
                        "added_block": packet["added_block"],
                        "baseline_context": packet["baseline_context"],
                        "candidate_answer_set": packet.get("candidate_answer_set", []),
                        "candidate_findings": packet["candidate_findings"],
                        "candidate_set_size_after": packet.get("candidate_set_size_after"),
                        "candidate_set_size_before": packet.get("candidate_set_size_before"),
                        "declared_evidence_strength_band": packet.get("evidence_strength_band", ""),
                        "gold_facts": packet["gold_facts"],
                        "question": packet["question"],
                        "target_answer": packet["target_answer"],
                    }
                ),
            },
        ]

    @staticmethod
    def _adjudication_messages(
        packet: Mapping[str, Any],
        logloss: Mapping[str, Any],
        review: Mapping[str, Any],
    ) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "Return JSON only with review_status and these booleans: target_clear, intervention_valid, "
                    "no_leakage, no_duplicate_trivial_case, utility_score_consistent. Use accepted only when all are true. "
                    "For no_leakage, check that the baseline does not identify the correct target. A question-level "
                    "candidate list is allowed, and the added block is the intervention and may contain the target."
                ),
            },
            {
                "role": "user",
                "content": _stable_json(
                    {
                        "logloss_source": logloss.get("logloss_source"),
                        "packet": dict(packet),
                        "review": dict(review),
                    }
                ),
            },
        ]


def _validate_adjudication(payload: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    row = deepcopy(dict(payload))
    reason_codes: list[str] = []
    status = str(row.get("review_status") or "ambiguous")
    if status not in {"accepted", "rejected", "ambiguous"}:
        reason_codes.append("unsupported_review_status")
        status = "ambiguous"
    row["review_status"] = status
    for field in ADJUDICATION_BOOLEAN_FIELDS:
        row[field] = _as_bool(row.get(field))
        if not row[field]:
            reason_codes.append(f"{field}_failed")
    return row, sorted(set(reason_codes))


def _bridge_fit_eligible(packet: Mapping[str, Any]) -> bool:
    if "bridge_fit_eligible" not in packet:
        return True
    return _as_bool(packet.get("bridge_fit_eligible"))


def _bridge_fit_reason_codes(packet: Mapping[str, Any]) -> list[str]:
    return [] if _bridge_fit_eligible(packet) else ["bridge_fit_ineligible"]


def _bridge_pair(
    *,
    config: Mapping[str, Any],
    packet: Mapping[str, Any],
    logloss: Mapping[str, Any],
    review: Mapping[str, Any],
    adjudication: Mapping[str, Any],
) -> dict[str, Any]:
    task_id = str(packet["task_id"])
    row = {
        "block_id": f"{task_id}:A",
        "block_size": int(config["block_size"]),
        "bridge_fit_eligible": True,
        "candidate_slice_band": str(config["candidate_slice_band"]),
        "candidate_set_size_after": _finite_float_or_none(review.get("candidate_set_size_after"))
        if _finite_float_or_none(review.get("candidate_set_size_after")) is not None
        else packet.get("candidate_set_size_after"),
        "candidate_set_size_before": _finite_float_or_none(review.get("candidate_set_size_before"))
        if _finite_float_or_none(review.get("candidate_set_size_before")) is not None
        else packet.get("candidate_set_size_before"),
        "context_id": f"{task_id}:L",
        "data_origin": "api_generated",
        "delta_logloss": float(logloss["delta_logloss"]),
        "delta_logloss_source": "measured_logprob",
        "delta_utility": float(review["delta_utility"]),
        "delta_utility_source": "strong_model_adjudicated",
        "evidence_strength_band": str(packet.get("evidence_strength_band") or review.get("evidence_strength_band") or ""),
        "materialization_policy": str(config["materialization_policy"]),
        "metric": str(config["metric"]),
        "model_tier": str(config["fixed_model_id"]),
        "notes": (
            "api_generated strong-model-adjudicated utility with fixed-model measured logprob; "
            "requires P45 dry validation before bridge artifacts"
        ),
        "pair_id": task_id,
        "replicate_count": 1,
        "review_status": str(adjudication["review_status"]),
        "source": "operator_provided",
        "stratum_id": str(config["active_stratum_id"]),
        "task_family": str(config["task_family"]),
        "utility_rationale": str(review.get("utility_rationale") or review.get("sufficiency_rationale") or ""),
        "utility_with": float(review["utility_with"]),
        "utility_without": float(review["utility_without"]),
    }
    row["bridge_signal_status"] = "bridge_informative"
    for field in ("candidate_set_size_after", "candidate_set_size_before"):
        if row.get(field) in (None, ""):
            row.pop(field, None)
    return row


def _bridge_signal_status(reason_codes: Sequence[str]) -> str:
    uninformative_reasons = {
        "delta_logloss_below_informative_threshold",
        "negative_delta_logloss",
        "delta_logloss_not_measured_logprob",
        "logprob_unavailable",
        "missing_measured_logloss",
        "missing_or_degenerate_logprobs_with",
        "missing_or_degenerate_logprobs_without",
    }
    return "bridge_uninformative" if any(reason in uninformative_reasons for reason in reason_codes) else "bridge_informative"


def _review_row(
    *,
    packet: Mapping[str, Any],
    logloss: Mapping[str, Any],
    review: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    reason_codes: Sequence[str],
) -> dict[str, Any]:
    fit_eligible = _bridge_fit_eligible(packet)
    usable = fit_eligible and not reason_codes and str(adjudication.get("review_status")) == "accepted"
    return {
        "bridge_fit_eligible": fit_eligible,
        "bridge_fit_exclusion_reason": str(packet.get("bridge_fit_exclusion_reason") or ""),
        "bridge_signal_status": _bridge_signal_status(reason_codes),
        "canary_design": str(packet.get("canary_design") or ""),
        "candidate_set_size_after": review.get("candidate_set_size_after", packet.get("candidate_set_size_after")),
        "candidate_set_size_before": review.get("candidate_set_size_before", packet.get("candidate_set_size_before")),
        "delta_logloss": logloss.get("delta_logloss"),
        "delta_logloss_source": str(logloss.get("logloss_source") or ""),
        "delta_utility": review.get("delta_utility"),
        "delta_utility_source": "strong_model_adjudicated",
        "evidence_strength_band": str(packet.get("evidence_strength_band") or review.get("evidence_strength_band") or ""),
        "loss_with": logloss.get("loss_with"),
        "loss_without": logloss.get("loss_without"),
        "minimum_abs_delta_logloss_for_bridge_evidence": logloss.get(
            "minimum_abs_delta_logloss_for_bridge_evidence"
        ),
        "reason_codes": list(reason_codes),
        "review_status": str(adjudication.get("review_status") or "ambiguous"),
        "reviewer_evidence_strength_band": str(review.get("reviewer_evidence_strength_band") or ""),
        "sufficiency_rationale": str(review.get("sufficiency_rationale") or ""),
        "task_id": str(packet["task_id"]),
        "usable_for_bridge_calibration": usable,
        "utility_rationale": str(review.get("utility_rationale") or review.get("sufficiency_rationale") or ""),
        "utility_with": review.get("utility_with"),
        "utility_without": review.get("utility_without"),
    }


def _summary(review_rows: Sequence[Mapping[str, Any]], accepted_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "accepted_rows": len(accepted_rows),
        "ambiguous_rows": sum(1 for row in review_rows if row.get("review_status") == "ambiguous"),
        "bridge_fit_eligible_rows": sum(1 for row in review_rows if bool(row.get("bridge_fit_eligible"))),
        "bridge_fit_ineligible_rows": sum(1 for row in review_rows if not bool(row.get("bridge_fit_eligible"))),
        "bridge_uninformative_rows": sum(
            1 for row in review_rows if row.get("bridge_signal_status") == "bridge_uninformative"
        ),
        "low_signal_rows": sum(
            1 for row in review_rows if "delta_logloss_below_informative_threshold" in (row.get("reason_codes") or [])
        ),
        "measurement_validated_allowed": False,
        "measured_logprob_rows": sum(1 for row in review_rows if row.get("delta_logloss_source") == "measured_logprob"),
        "negative_delta_logloss_rows": sum(
            1 for row in review_rows if "negative_delta_logloss" in (row.get("reason_codes") or [])
        ),
        "positive_delta_logloss_rows": sum(
            1 for row in review_rows if _finite_float_or_none(row.get("delta_logloss")) is not None and float(row["delta_logloss"]) > 0.0
        ),
        "rejected_rows": sum(1 for row in review_rows if row.get("review_status") == "rejected"),
        "sufficient_signal_rows": sum(
            1
            for row in review_rows
            if _finite_float_or_none(row.get("delta_logloss")) is not None
            and float(row["delta_logloss"]) > 0.0
            and not any(
                reason in (row.get("reason_codes") or [])
                for reason in ("delta_logloss_below_informative_threshold", "negative_delta_logloss")
            )
        ),
        "total_rows": len(review_rows),
        "unusable_rows": sum(1 for row in review_rows if not bool(row.get("usable_for_bridge_calibration"))),
    }


def _numeric_values(rows: Sequence[Mapping[str, Any]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = _finite_float_or_none(row.get(field))
        if value is not None:
            values.append(value)
    return values


def _numeric_range(rows: Sequence[Mapping[str, Any]], field: str) -> list[float] | None:
    values = _numeric_values(rows, field)
    if not values:
        return None
    return [min(values), max(values)]


def _unique_numeric_values(rows: Sequence[Mapping[str, Any]], field: str) -> list[float]:
    return sorted(set(_numeric_values(rows, field)))


def _band_distribution(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    distribution = {band: 0 for band in EVIDENCE_STRENGTH_BANDS}
    for row in rows:
        band = str(row.get("evidence_strength_band") or "")
        distribution.setdefault(band, 0)
        distribution[band] += 1
    return {key: value for key, value in distribution.items() if value}


def _value_distribution(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for row in rows:
        value = row.get(field)
        if value in (None, ""):
            continue
        key = str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)
        distribution[key] = distribution.get(key, 0) + 1
    return dict(sorted(distribution.items()))


def _is_p45d_canary(config: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> bool:
    if str(config.get("task_packet_mode") or "") == TASK_PACKET_MODE_BRIDGE_CANARY_V3:
        return True
    return bool(rows) and all(str(row.get("canary_design") or "") == "p45d_graded_positive_control" for row in rows)


def _is_p45e_canary(config: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> bool:
    if str(config.get("task_packet_mode") or "") == TASK_PACKET_MODE_BRIDGE_CANARY_V4:
        return True
    return bool(rows) and all(str(row.get("canary_design") or "") == "p45e_candidate_set_constrained_bridge" for row in rows)


def _p45d_canary_summary(
    *,
    config: Mapping[str, Any],
    review_rows: Sequence[Mapping[str, Any]],
    accepted_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    generic = _summary(review_rows, accepted_rows)
    deltas = _numeric_values(review_rows, "delta_logloss")
    return {
        **generic,
        "data_origin": "api_generated",
        "delta_logloss_range": _numeric_range(review_rows, "delta_logloss"),
        "delta_utility_range": _numeric_range(review_rows, "delta_utility"),
        "diagnostic_scope": "api_live_canary",
        "evidence_strength_band_distribution": _band_distribution(review_rows),
        "fixed_model_id": str(config.get("fixed_model_id") or ""),
        "human_labels_present": False,
        "kappa_present": False,
        "measurement_validation_claim": False,
        "median_delta_logloss": _median(deltas),
        "paper_evidence_eligible": False,
        "probe_kind": "p45d_graded_positive_control_bridge_canary",
        "provider_profile": str(config.get("provider_profile") or ""),
        "task_packet_mode": TASK_PACKET_MODE_BRIDGE_CANARY_V3,
        "total_task_packets": len(review_rows),
        "utility_unique_values": _unique_numeric_values(review_rows, "delta_utility"),
        "utility_with_range": _numeric_range(review_rows, "utility_with"),
        "utility_without_range": _numeric_range(review_rows, "utility_without"),
    }


def _p45e_canary_summary(
    *,
    config: Mapping[str, Any],
    review_rows: Sequence[Mapping[str, Any]],
    accepted_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    generic = _summary(review_rows, accepted_rows)
    deltas = _numeric_values(review_rows, "delta_logloss")
    return {
        **generic,
        "candidate_set_size_after_distribution": _value_distribution(review_rows, "candidate_set_size_after"),
        "candidate_set_size_before_distribution": _value_distribution(review_rows, "candidate_set_size_before"),
        "data_origin": "api_generated",
        "delta_logloss_range": _numeric_range(review_rows, "delta_logloss"),
        "delta_utility_range": _numeric_range(review_rows, "delta_utility"),
        "diagnostic_scope": "api_live_canary",
        "evidence_strength_band_distribution": _band_distribution(review_rows),
        "fixed_model_id": str(config.get("fixed_model_id") or ""),
        "human_labels_present": False,
        "kappa_present": False,
        "measurement_validation_claim": False,
        "median_delta_logloss": _median(deltas),
        "paper_evidence_eligible": False,
        "probe_kind": "p45e_candidate_set_constrained_bridge_canary",
        "provider_profile": str(config.get("provider_profile") or ""),
        "task_packet_mode": TASK_PACKET_MODE_BRIDGE_CANARY_V4,
        "total_task_packets": len(review_rows),
        "utility_unique_values": _unique_numeric_values(review_rows, "delta_utility"),
        "utility_with_range": _numeric_range(review_rows, "utility_with"),
        "utility_without_range": _numeric_range(review_rows, "utility_without"),
    }


def _format_p45d_canary_summary(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# P45d Graded Positive-Control Canary Summary",
            "",
            f"- Total task packets: `{summary['total_task_packets']}`",
            f"- Measured-logprob rows: `{summary['measured_logprob_rows']}`",
            f"- Positive `delta_logloss` rows: `{summary['positive_delta_logloss_rows']}`",
            f"- Sufficient-signal rows: `{summary['sufficient_signal_rows']}`",
            f"- Low-signal rows: `{summary['low_signal_rows']}`",
            f"- Negative-delta rows: `{summary['negative_delta_logloss_rows']}`",
            f"- Accepted/exported rows: `{summary['accepted_rows']}`",
            f"- Bridge-fit-eligible rows: `{summary['bridge_fit_eligible_rows']}`",
            f"- Utility without range: `{summary['utility_without_range']}`",
            f"- Utility with range: `{summary['utility_with_range']}`",
            f"- Delta utility range: `{summary['delta_utility_range']}`",
            f"- Utility unique values: `{summary['utility_unique_values']}`",
            f"- Delta logloss range: `{summary['delta_logloss_range']}`",
            f"- Median delta logloss: `{summary['median_delta_logloss']}`",
            f"- Evidence-strength band distribution: `{summary['evidence_strength_band_distribution']}`",
            "",
            "## Boundary",
            "",
            "- P45d exports fit-eligible accepted rows only.",
            "- Reviewer/adjudicator output cannot provide log-loss.",
            "- No human labels, kappa, deployed V-information verification, or measurement validation are claimed.",
            "- Paper evidence eligibility remains false for this live canary unless separately promoted by operator review.",
            "",
        ]
    )


def _write_p45d_summary_report(path: Path, summary: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_format_p45d_canary_summary(summary), encoding="utf-8")
    return path


def _format_p45e_canary_summary(summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# P45e Candidate-Set Constrained Canary Summary",
            "",
            f"- Total task packets: `{summary['total_task_packets']}`",
            f"- Measured-logprob rows: `{summary['measured_logprob_rows']}`",
            f"- Positive `delta_logloss` rows: `{summary['positive_delta_logloss_rows']}`",
            f"- Sufficient-signal rows: `{summary['sufficient_signal_rows']}`",
            f"- Low-signal rows: `{summary['low_signal_rows']}`",
            f"- Negative-delta rows: `{summary['negative_delta_logloss_rows']}`",
            f"- Accepted/exported rows: `{summary['accepted_rows']}`",
            f"- Bridge-fit-eligible rows: `{summary['bridge_fit_eligible_rows']}`",
            f"- Utility without range: `{summary['utility_without_range']}`",
            f"- Utility with range: `{summary['utility_with_range']}`",
            f"- Delta utility range: `{summary['delta_utility_range']}`",
            f"- Utility unique values: `{summary['utility_unique_values']}`",
            f"- Candidate-set size before distribution: `{summary['candidate_set_size_before_distribution']}`",
            f"- Candidate-set size after distribution: `{summary['candidate_set_size_after_distribution']}`",
            f"- Delta logloss range: `{summary['delta_logloss_range']}`",
            f"- Median delta logloss: `{summary['median_delta_logloss']}`",
            f"- Evidence-strength band distribution: `{summary['evidence_strength_band_distribution']}`",
            "",
            "## Boundary",
            "",
            "- P45e exports fit-eligible accepted rows only.",
            "- Fixed logloss scorer scores only the exact correct candidate string.",
            "- Reviewer/adjudicator output cannot provide log-loss.",
            "- No human labels, kappa, deployed V-information verification, or measurement validation are claimed.",
            "- Paper evidence eligibility remains false for this live canary unless separately promoted by operator review.",
            "",
        ]
    )


def _write_p45e_summary_report(path: Path, summary: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_format_p45e_canary_summary(summary), encoding="utf-8")
    return path


def _manifest(config: Mapping[str, Any], summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "data_origin": "api_generated",
        "denied_claims": list(DENIED_CLAIMS),
        "fixed_model_id": str(config.get("fixed_model_id") or ""),
        "human_labels_present": False,
        "kappa_present": False,
        "live_api_used": config["mode"] == MODE_LIVE,
        "measurement_validation_claim": False,
        "measurement_validated_allowed": False,
        "mode": str(config["mode"]),
        "operator_approval": _as_bool(config.get("operator_approval")),
        "protocol_version": str(config.get("protocol_version") or PROTOCOL_VERSION),
        "provider_profile": str(config.get("provider_profile") or ""),
        "source": "operator_provided",
        "strong_review_model_id": str(config.get("strong_review_model_id") or ""),
        "summary": dict(summary),
    }


def _format_report(manifest: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# P45 API-Generated Bridge Calibration Data Report",
            "",
            f"- Mode: `{manifest['mode']}`",
            f"- Accepted rows: `{summary['accepted_rows']}`",
            f"- Rejected rows: `{summary['rejected_rows']}`",
            f"- Ambiguous rows: `{summary['ambiguous_rows']}`",
            f"- Unusable rows: `{summary['unusable_rows']}`",
            f"- Bridge-uninformative rows: `{summary.get('bridge_uninformative_rows', 0)}`",
            f"- Negative `delta_logloss` rows: `{summary.get('negative_delta_logloss_rows', 0)}`",
            "- `delta_logloss` is accepted only when sourced from `measured_logprob`.",
            "- Strong-model review may adjudicate utility but must not estimate log-loss.",
            "- Run P45 `--dry-validate` on accepted rows before artifact generation.",
            "- No human labels, kappa, deployed V-information verification, or measurement validation are claimed.",
            "- `measurement_validated` remains a denied claim.",
            "",
        ]
    )


def _median(values: Sequence[float]) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2 == 1:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2.0


def _positive_control_logprob_usable(row: Mapping[str, Any]) -> bool:
    hard_failure_reasons = {
        "delta_logloss_mismatch",
        "delta_logloss_not_measured_logprob",
        "logprob_unavailable",
        "missing_measured_logloss",
        "missing_or_degenerate_logprobs_with",
        "missing_or_degenerate_logprobs_without",
    }
    return not any(reason in hard_failure_reasons for reason in row.get("reason_codes") or [])


def _positive_control_row(
    *,
    packet: Mapping[str, Any],
    logloss: Mapping[str, Any],
    reason_codes: Sequence[str],
) -> dict[str, Any]:
    delta_logloss = logloss.get("delta_logloss")
    abs_delta = abs(delta_logloss) if isinstance(delta_logloss, float) else None
    positive_delta = isinstance(delta_logloss, float) and delta_logloss > 0.0
    sufficient_signal = positive_delta and not reason_codes
    return {
        "abs_delta_logloss": abs_delta,
        "delta_logloss": delta_logloss,
        "delta_logloss_positive": positive_delta,
        "delta_logloss_source": str(logloss.get("logloss_source") or ""),
        "loss_with": logloss.get("loss_with"),
        "loss_without": logloss.get("loss_without"),
        "minimum_abs_delta_logloss_for_bridge_evidence": logloss.get(
            "minimum_abs_delta_logloss_for_bridge_evidence"
        ),
        "reason_codes": list(reason_codes),
        "sufficient_signal": sufficient_signal,
        "target_answer": str(packet["target_answer"]),
        "task_id": str(packet["task_id"]),
        "usable_logprob": _positive_control_logprob_usable({"reason_codes": reason_codes}),
    }


def _positive_control_summary(
    *,
    config: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    deltas = [
        float(row["delta_logloss"])
        for row in rows
        if _finite_float_or_none(row.get("delta_logloss")) is not None
    ]
    low_signal_rows = sum(
        1 for row in rows if "delta_logloss_below_informative_threshold" in (row.get("reason_codes") or [])
    )
    negative_rows = sum(1 for row in rows if _finite_float_or_none(row.get("delta_logloss")) is not None and float(row["delta_logloss"]) < 0)
    positive_rows = sum(1 for row in rows if _finite_float_or_none(row.get("delta_logloss")) is not None and float(row["delta_logloss"]) > 0)
    sufficient_rows = sum(1 for row in rows if bool(row.get("sufficient_signal")))
    usable_logprob_rows = sum(1 for row in rows if bool(row.get("usable_logprob")))
    return {
        "bridge_calibration_artifacts_generated": False,
        "data_origin": "api_generated",
        "delta_logloss_range": [min(deltas), max(deltas)] if deltas else None,
        "fixed_model_id": str(config.get("fixed_model_id") or ""),
        "human_labels_present": False,
        "kappa_present": False,
        "low_signal_rows": low_signal_rows,
        "measurement_validation_claim": False,
        "median_delta_logloss": _median(deltas),
        "minimum_abs_delta_logloss_for_bridge_evidence": float(
            config.get("minimum_abs_delta_logloss_for_bridge_evidence") or 0.0
        ),
        "mode": str(config["mode"]),
        "negative_delta_logloss_rows": negative_rows,
        "positive_delta_logloss_rows": positive_rows,
        "probe_kind": "p45c_fixed_logloss_positive_control",
        "provider_profile": str(config.get("provider_profile") or ""),
        "source": "operator_provided",
        "sufficient_signal_rows": sufficient_rows,
        "total_probes": len(rows),
        "usable_logprob_rows": usable_logprob_rows,
    }


def _format_positive_control_report(
    *,
    summary: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> str:
    lines = [
        "# P45c Fixed-Logloss Positive-Control Probe Report",
        "",
        "This probe calls only the fixed-model logloss scorer. It does not export P45 bridge calibration rows.",
        "",
        "## Summary",
        "",
        f"- Total probes: `{summary['total_probes']}`",
        f"- Usable logprob rows: `{summary['usable_logprob_rows']}`",
        f"- Positive delta_logloss rows: `{summary['positive_delta_logloss_rows']}`",
        f"- Sufficient-signal rows: `{summary['sufficient_signal_rows']}`",
        f"- Negative delta_logloss rows: `{summary['negative_delta_logloss_rows']}`",
        f"- Low-signal rows: `{summary['low_signal_rows']}`",
        f"- Delta_logloss range: `{summary['delta_logloss_range']}`",
        f"- Median delta_logloss: `{summary['median_delta_logloss']}`",
        "",
        "## Rows",
        "",
        "| task_id | target_answer | loss_without | loss_with | delta_logloss | abs_delta_logloss | sufficient_signal | reason_codes |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {task_id} | {target_answer} | {loss_without} | {loss_with} | {delta_logloss} | {abs_delta_logloss} | {sufficient_signal} | {reason_codes} |".format(
                task_id=row.get("task_id"),
                target_answer=row.get("target_answer"),
                loss_without=row.get("loss_without"),
                loss_with=row.get("loss_with"),
                delta_logloss=row.get("delta_logloss"),
                abs_delta_logloss=row.get("abs_delta_logloss"),
                sufficient_signal=row.get("sufficient_signal"),
                reason_codes=",".join(str(value) for value in row.get("reason_codes") or []),
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- This is a fixed-logloss positive-control probe, not a bridge calibration run.",
            "- Strong-review utility is not used as the success criterion.",
            "- No human labels, kappa, deployed V-information verification, or measurement validation are claimed.",
            "- No P45 bridge calibration artifacts are generated by this probe.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_positive_control_report(
    path: Path,
    *,
    summary: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_format_positive_control_report(summary=summary, rows=rows), encoding="utf-8")
    return path


def run_logloss_positive_control(
    *,
    config_path: str | Path,
    output_dir: str | Path | None = None,
    task_packets: Sequence[Mapping[str, Any]] | None = None,
    logloss_scorer: TaskPacketFn | None = None,
    env: Mapping[str, str] | None = None,
    client_factory: ProviderClientFactory | None = None,
) -> dict[str, Any]:
    config = _normalize_config(config_path)
    if task_packets is None:
        task_packets = generate_logloss_positive_control_task_packets(int(config.get("sample_limit") or 8))
    packets = _normalize_task_packets(task_packets, config=config)
    resolved_output_dir = Path(output_dir or config["output_dir"])
    preflight: dict[str, Any] | None = None
    if config["mode"] == MODE_LIVE and logloss_scorer is None:
        components = build_live_provider_profile_callables(
            config_path=config_path,
            env=env,
            client_factory=client_factory,
        )
        logloss_scorer = components.logloss_scorer
        preflight = components.preflight
    _validate_logloss_only_live_gates(config=config, logloss_scorer=logloss_scorer, env=env)

    rows: list[dict[str, Any]] = []
    if logloss_scorer is not None:
        min_abs_delta_logloss = float(config.get("minimum_abs_delta_logloss_for_bridge_evidence") or 0.0)
        for packet in packets:
            logloss, reason_codes = _validate_logloss(
                logloss_scorer(packet),
                minimum_abs_delta_logloss_for_bridge_evidence=min_abs_delta_logloss,
            )
            rows.append(_positive_control_row(packet=packet, logloss=logloss, reason_codes=reason_codes))

    summary = _positive_control_summary(config=config, rows=rows)
    artifacts = {
        "logloss_positive_control_report": str(
            _write_positive_control_report(
                resolved_output_dir / "logloss_positive_control_report.md",
                summary=summary,
                rows=rows,
            )
        ),
        "logloss_positive_control_rows": str(
            _write_jsonl(resolved_output_dir / "logloss_positive_control_rows.jsonl", rows)
        ),
        "logloss_positive_control_summary": str(
            _write_json(resolved_output_dir / "logloss_positive_control_summary.json", summary)
        ),
        "task_packets": str(_write_jsonl(resolved_output_dir / "task_packets.jsonl", packets)),
    }
    if preflight is not None:
        artifacts["preflight"] = str(_write_json(resolved_output_dir / "preflight.json", preflight))
    return {"artifacts": artifacts, "preflight": preflight, "summary": summary}


def _process_live_rows(
    *,
    config: Mapping[str, Any],
    task_packets: Sequence[Mapping[str, Any]],
    logloss_scorer: TaskPacketFn,
    utility_reviewer: TaskPacketFn,
    adjudicator: AdjudicatorFn,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    review_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    min_abs_delta_logloss = float(config.get("minimum_abs_delta_logloss_for_bridge_evidence") or 0.0)
    for packet in task_packets:
        logloss, logloss_reasons = _validate_logloss(
            logloss_scorer(packet),
            minimum_abs_delta_logloss_for_bridge_evidence=min_abs_delta_logloss,
        )
        review, review_reasons = _validate_utility(utility_reviewer(packet))
        adjudication, adjudication_reasons = _validate_adjudication(adjudicator(packet, logloss, review))
        fit_reasons = _bridge_fit_reason_codes(packet)
        reason_codes = sorted(set(logloss_reasons + review_reasons + adjudication_reasons + fit_reasons))
        row = _review_row(
            packet=packet,
            logloss=logloss,
            review=review,
            adjudication=adjudication,
            reason_codes=reason_codes,
        )
        review_rows.append(row)
        if row["usable_for_bridge_calibration"]:
            accepted_rows.append(
                _bridge_pair(
                    config=config,
                    packet=packet,
                    logloss=logloss,
                    review=review,
                    adjudication=adjudication,
                )
            )
    return review_rows, accepted_rows


def build_live_provider_profile_callables(
    *,
    config_path: str | Path = LOCAL_LIVE_CONFIG_PATH,
    env: Mapping[str, str] | None = None,
    client_factory: ProviderClientFactory | None = None,
) -> BridgeProviderProfileCallables:
    config, resolved_profile, preflight = _require_live_provider_preflight(config_path=config_path, env=env)
    if resolved_profile.api_style != "openai_chat_compatible":
        raise BridgeDataGenerationGateError(f"unsupported provider api style: {resolved_profile.api_style}")
    if not resolved_profile.api_key:
        raise BridgeDataGenerationGateError(f"missing provider api key env var: {resolved_profile.api_key_env}")
    client = (
        client_factory(resolved_profile, config)
        if client_factory is not None
        else OpenAICompatibleClient(
            OpenAICompatibleCredentials(
                base_url=resolved_profile.base_url,
                api_key=resolved_profile.api_key,
            )
        )
    )
    provider = OpenAICompatibleBridgeProvider(client=client, config=config)
    return BridgeProviderProfileCallables(
        adjudicator=provider.adjudicator,
        logloss_scorer=provider.logloss_scorer,
        preflight=preflight,
        utility_reviewer=provider.utility_reviewer,
    )


def run_bridge_data_generation(
    *,
    config_path: str | Path,
    output_dir: str | Path | None = None,
    task_packets: Sequence[Mapping[str, Any]] | None = None,
    logloss_scorer: TaskPacketFn | None = None,
    utility_reviewer: TaskPacketFn | None = None,
    adjudicator: AdjudicatorFn | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    config = _normalize_config(config_path)
    _validate_live_gates(
        config=config,
        logloss_scorer=logloss_scorer,
        utility_reviewer=utility_reviewer,
        adjudicator=adjudicator,
        env=env,
    )
    resolved_output_dir = Path(output_dir or config["output_dir"])
    packets = _normalize_task_packets(task_packets, config=config)
    if config["mode"] == MODE_LIVE:
        assert logloss_scorer is not None
        assert utility_reviewer is not None
        assert adjudicator is not None
        review_rows, accepted_rows = _process_live_rows(
            config=config,
            task_packets=packets,
            logloss_scorer=logloss_scorer,
            utility_reviewer=utility_reviewer,
            adjudicator=adjudicator,
        )
    else:
        review_rows = []
        accepted_rows = []

    summary = _summary(review_rows, accepted_rows)
    p45d_summary = None
    p45e_summary = None
    if _is_p45e_canary(config, review_rows):
        p45e_summary = _p45e_canary_summary(config=config, review_rows=review_rows, accepted_rows=accepted_rows)
        summary = p45e_summary
    elif _is_p45d_canary(config, review_rows):
        p45d_summary = _p45d_canary_summary(config=config, review_rows=review_rows, accepted_rows=accepted_rows)
        summary = p45d_summary
    manifest = _manifest(config, summary)
    artifacts = {
        "accepted_bridge_calibration_pairs": str(
            _write_jsonl(resolved_output_dir / "accepted_bridge_calibration_pairs.jsonl", accepted_rows)
        ),
        "manifest": str(_write_json(resolved_output_dir / "manifest.json", manifest)),
        "planned_prompts": str(_write_jsonl(resolved_output_dir / "planned_prompts.jsonl", _planned_prompts(packets))),
        "report": str(_write_report(resolved_output_dir / "report.md", manifest, summary)),
        "review_rows": str(_write_jsonl(resolved_output_dir / "review_rows.jsonl", review_rows)),
        "schema_example": str(_write_json(resolved_output_dir / "schema_example.json", _schema_example(config))),
        "task_packets": str(_write_jsonl(resolved_output_dir / "task_packets.jsonl", packets)),
    }
    if p45d_summary is not None:
        artifacts["p45d_canary_summary"] = str(
            _write_json(resolved_output_dir / "p45d_canary_summary.json", p45d_summary)
        )
        artifacts["p45d_canary_summary_report"] = str(
            _write_p45d_summary_report(resolved_output_dir / "p45d_canary_summary.md", p45d_summary)
        )
    if p45e_summary is not None:
        artifacts["p45e_canary_summary"] = str(
            _write_json(resolved_output_dir / "p45e_canary_summary.json", p45e_summary)
        )
        artifacts["p45e_canary_summary_report"] = str(
            _write_p45e_summary_report(resolved_output_dir / "p45e_canary_summary.md", p45e_summary)
        )
    return {"artifacts": artifacts, "manifest": manifest, "summary": summary}


def run_bridge_data_generation_from_provider_profile(
    *,
    config_path: str | Path = LOCAL_LIVE_CONFIG_PATH,
    output_dir: str | Path | None = None,
    task_packets: Sequence[Mapping[str, Any]] | None = None,
    env: Mapping[str, str] | None = None,
    client_factory: ProviderClientFactory | None = None,
) -> dict[str, Any]:
    components = build_live_provider_profile_callables(
        config_path=config_path,
        env=env,
        client_factory=client_factory,
    )
    return run_bridge_data_generation(
        config_path=config_path,
        output_dir=output_dir,
        task_packets=task_packets,
        logloss_scorer=components.logloss_scorer,
        utility_reviewer=components.utility_reviewer,
        adjudicator=components.adjudicator,
        env=env,
    )


def _write_report(path: Path, manifest: Mapping[str, Any], summary: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_format_report(manifest, summary), encoding="utf-8")
    return path


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise BridgeDataGenerationValidationError(f"task packet line {line_number} must be a JSON object")
        rows.append(payload)
    return rows


def _task_packets_for_cli(*, config_path: str | Path, task_packets_path: str | Path | None) -> list[dict[str, Any]] | None:
    if task_packets_path is not None:
        return _read_jsonl(task_packets_path)
    config = _normalize_config(config_path)
    configured_path = config.get("task_packets_file")
    if configured_path:
        return _read_jsonl(str(configured_path))
    if config["mode"] == MODE_LIVE:
        raise BridgeDataGenerationGateError(
            "live provider profile mode requires --task-packets or task_packets_file; refusing placeholder packets"
        )
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the P45 API-generated bridge data scaffold.")
    parser.add_argument("--config", required=True, help="Path to bridge data generation config JSON.")
    parser.add_argument("--output-dir", help="Optional output directory override.")
    parser.add_argument("--task-packets", help="Optional task packet JSONL input. Required for live provider runs.")
    parser.add_argument(
        "--use-live-provider-profile",
        action="store_true",
        help="Construct scorer/reviewer/adjudicator from the approved local provider profile.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Validate live provider config and env gates without calling a provider.",
    )
    parser.add_argument(
        "--logloss-positive-control",
        action="store_true",
        help="Run the P45c fixed-logloss positive-control probe instead of bridge data generation.",
    )
    parser.add_argument(
        "--graded-positive-control",
        action="store_true",
        help="Use the P45d bridge_canary_v3 graded positive-control task packets.",
    )
    parser.add_argument(
        "--candidate-set-constrained",
        action="store_true",
        help="Use the P45e bridge_canary_v4 candidate-set constrained task packets.",
    )
    args = parser.parse_args()
    if args.preflight_only:
        result = preflight_bridge_data_generation_provider(config_path=args.config)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["ready"] else 2
    if args.logloss_positive_control:
        task_packets = _read_jsonl(args.task_packets) if args.task_packets is not None else None
        result = run_logloss_positive_control(
            config_path=args.config,
            output_dir=args.output_dir,
            task_packets=task_packets,
            client_factory=None,
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0

    if args.candidate_set_constrained:
        config = _normalize_config(args.config)
        task_packets = (
            _read_jsonl(args.task_packets)
            if args.task_packets is not None
            else generate_candidate_set_constrained_task_packets(min(int(config.get("sample_limit") or 8), 8))
        )
    elif args.graded_positive_control:
        config = _normalize_config(args.config)
        task_packets = (
            _read_jsonl(args.task_packets)
            if args.task_packets is not None
            else generate_graded_positive_control_task_packets(min(int(config.get("sample_limit") or 8), 8))
        )
    else:
        task_packets = _task_packets_for_cli(config_path=args.config, task_packets_path=args.task_packets)
    if args.use_live_provider_profile:
        result = run_bridge_data_generation_from_provider_profile(
            config_path=args.config,
            output_dir=args.output_dir,
            task_packets=task_packets,
        )
    else:
        result = run_bridge_data_generation(
            config_path=args.config,
            output_dir=args.output_dir,
            task_packets=task_packets,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
