from __future__ import annotations

import argparse
import csv
from pathlib import Path

from api.settings import DEFAULT_API_PROFILE


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def mask_secret(secret: str) -> str:
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"


def extract_api_key_from_csv(path: str | Path) -> str:
    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    if len(rows) < 2:
        raise ValueError(f"CSV does not contain an api key row: {csv_path}")

    header = [cell.strip() for cell in rows[0]]
    values = [cell.strip() for cell in rows[1]]

    for index, column in enumerate(header):
        if column.lower() in {"api_key", "apikey", "key", "secret", "token"} and index < len(values):
            candidate = values[index]
            if candidate.startswith("sk-"):
                return candidate

    if values and values[0].lower() in {"api_key", "apikey", "key"} and len(values) > 1:
        candidate = values[1]
        if candidate.startswith("sk-"):
            return candidate

    for candidate in values:
        if candidate.startswith("sk-"):
            return candidate

    raise ValueError(f"Unable to locate an API key inside {csv_path}")


def build_env_text(api_key: str) -> str:
    return "\n".join(
        [
            "PYTHONPATH=.",
            "HF_HOME=.cache/huggingface",
            "HF_DATASETS_CACHE=.cache/huggingface/datasets",
            f"DASHSCOPE_API_KEY={api_key}",
            f"DASHSCOPE_BASE_URL={DEFAULT_BASE_URL}",
            f"API_PROFILE={DEFAULT_API_PROFILE}",
            "PHASE1_EXPERIMENT_ID=musique_gate1_phase1_v1",
            "PHASE1_PROTOCOL_VERSION=phase1.v1",
            "PHASE1_SEED=20260418",
            "PHASE1_CACHE_DIR=./artifacts/phase1/cache",
            "PHASE1_MEASUREMENT_DIR=./artifacts/phase1/measurements",
            "PHASE1_EXPORT_DIR=./artifacts/phase1/exports",
            "PHASE1_CHECKPOINT_DIR=./artifacts/phase1/checkpoints",
            "",
        ]
    )


def write_env_file_from_csv(csv_path: str | Path, env_path: str | Path = ".env") -> Path:
    api_key = extract_api_key_from_csv(csv_path)
    env_file = Path(env_path)
    env_file.write_text(build_env_text(api_key), encoding="utf-8")
    return env_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a local .env from a DashScope API key CSV.")
    parser.add_argument("--csv", required=True, help="Path to the DashScope API key CSV.")
    parser.add_argument("--env", default=".env", help="Destination .env path.")
    args = parser.parse_args()

    env_path = write_env_file_from_csv(args.csv, args.env)
    print(f"Wrote {env_path} with redacted key {mask_secret(extract_api_key_from_csv(args.csv))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
