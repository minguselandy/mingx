from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from phase0.manifest import load_phase0_config
from phase1.secrets import mask_secret


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    api_style: str
    base_url_env: str
    api_key_env: str
    base_url: str
    api_key: str = field(repr=False)
    masked_api_key: str


@dataclass(frozen=True)
class ModelConfig:
    role: str
    model: str
    purpose: tuple[str, ...]
    decoding: dict[str, Any]
    logprob: dict[str, Any]


@dataclass(frozen=True)
class ScoringConfig:
    utility_metric: str
    answer_mode: str
    canonical_ordering_id: str
    variance_source: str
    permutation_count: int
    top_k_values: tuple[int, ...]


@dataclass(frozen=True)
class StorageConfig:
    cache_dir: Path
    measurement_dir: Path
    checkpoint_dir: Path
    export_dir: Path
    append_only_events: bool


@dataclass(frozen=True)
class Phase1Context:
    root_dir: Path
    experiment: dict[str, Any]
    provider: ProviderConfig
    models: dict[str, ModelConfig]
    scoring: ScoringConfig
    storage: StorageConfig
    run_plan: dict[str, Any]
    raw_config: dict[str, Any]


def _resolve_path(value: str | Path, base_dir: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def _load_env_values(env_path: str | Path | None) -> dict[str, str]:
    values: dict[str, str] = {}
    if env_path is not None and Path(env_path).exists():
        values.update({k: str(v) for k, v in dotenv_values(env_path).items() if v is not None})
    elif env_path is None and Path(".env").exists():
        values.update({k: str(v) for k, v in dotenv_values(".env").items() if v is not None})
    values.update({k: v for k, v in os.environ.items() if isinstance(v, str)})
    return values


def load_phase1_context(
    phase1_config_path: str | Path = "phase1.yaml",
    run_plan_path: str | Path = "artifacts/phase1/run_plan.json",
    env_path: str | Path | None = None,
) -> Phase1Context:
    config_path = Path(phase1_config_path).resolve()
    run_plan_file = Path(run_plan_path).resolve()
    root_dir = config_path.parent
    raw_config = load_phase0_config(config_path)
    run_plan = json.loads(run_plan_file.read_text(encoding="utf-8"))
    env_values = _load_env_values(env_path)

    provider_block = raw_config["provider"]
    base_url = env_values.get(provider_block["base_url_env"])
    api_key = env_values.get(provider_block["api_key_env"])
    if not base_url:
        raise ValueError(f"Missing provider base URL env var: {provider_block['base_url_env']}")
    if not api_key:
        raise ValueError(f"Missing provider api key env var: {provider_block['api_key_env']}")

    model_env_map = {
        "frontier": "PHASE1_FRONTIER_MODEL",
        "small": "PHASE1_SMALL_MODEL",
        "coding": "CODING_MODEL",
    }
    models = {
        role: ModelConfig(
            role=role,
            model=str(env_values.get(model_env_map.get(role, "")) or model_block["model"]),
            purpose=tuple(model_block.get("purpose") or ()),
            decoding=dict(model_block.get("decoding") or {}),
            logprob=dict(model_block.get("logprob") or {}),
        )
        for role, model_block in raw_config["models"].items()
    }
    scoring_block = raw_config["scoring"]
    scoring = ScoringConfig(
        utility_metric=str(scoring_block["utility_metric"]),
        answer_mode=str(scoring_block["answer_mode"]),
        canonical_ordering_id=str(scoring_block["canonical_ordering_id"]),
        variance_source=str(scoring_block["variance_source"]),
        permutation_count=int(scoring_block["permutation_count"]),
        top_k_values=tuple(int(value) for value in scoring_block.get("top_k_values", (3, 5, 10))),
    )

    storage_block = raw_config["storage"]
    run_plan_storage = run_plan.get("storage") or {}
    storage = StorageConfig(
        cache_dir=_resolve_path(
            run_plan_storage.get("cache_dir") or env_values.get("PHASE1_CACHE_DIR") or storage_block["cache_dir"],
            root_dir,
        ),
        measurement_dir=_resolve_path(
            run_plan_storage.get("measurement_dir")
            or env_values.get("PHASE1_MEASUREMENT_DIR")
            or storage_block["measurement_dir"],
            root_dir,
        ),
        checkpoint_dir=_resolve_path(
            run_plan_storage.get("checkpoint_dir")
            or env_values.get("PHASE1_CHECKPOINT_DIR")
            or storage_block["checkpoint_dir"],
            root_dir,
        ),
        export_dir=_resolve_path(
            run_plan_storage.get("export_dir")
            or env_values.get("PHASE1_EXPORT_DIR")
            or storage_block["export_dir"],
            root_dir,
        ),
        append_only_events=bool(storage_block["append_only_events"]),
    )

    return Phase1Context(
        root_dir=root_dir,
        experiment=dict(raw_config["experiment"]),
        provider=ProviderConfig(
            name=str(provider_block["name"]),
            api_style=str(provider_block["api_style"]),
            base_url_env=str(provider_block["base_url_env"]),
            api_key_env=str(provider_block["api_key_env"]),
            base_url=str(base_url),
            api_key=str(api_key),
            masked_api_key=mask_secret(str(api_key)),
        ),
        models=models,
        scoring=scoring,
        storage=storage,
        run_plan=run_plan,
        raw_config=raw_config,
    )
