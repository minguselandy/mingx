from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from phase0.manifest import load_manifest, load_phase0_config, validate_manifest
from phase0.smoke import run_phase0_smoke


def resolve_output_paths(config_path: str | Path = "phase0.yaml") -> dict[str, Path]:
    phase0_config = load_phase0_config(config_path)["phase0"]
    outputs = phase0_config["outputs"]
    return {
        "artifact_dir": Path(outputs["artifact_dir"]),
        "manifest_path": Path(outputs["manifest_path"]),
        "hash_path": Path(outputs["hash_path"]),
    }


def _copy_if_requested(source: str | Path | None, destination: Path) -> None:
    if source is None:
        return
    source_path = Path(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source_path.resolve() != destination.resolve():
        shutil.copyfile(source_path, destination)


def ensure_phase0_artifacts(
    config_path: str | Path = "phase0.yaml",
    manifest_source: str | Path | None = None,
    hash_source: str | Path | None = None,
) -> dict[str, Path]:
    paths = resolve_output_paths(config_path)
    _copy_if_requested(manifest_source, paths["manifest_path"])
    _copy_if_requested(hash_source, paths["hash_path"])

    missing = [name for name in ("manifest_path", "hash_path") if not paths[name].exists()]
    if missing:
        raise FileNotFoundError(
            "missing phase0 artifacts: "
            + ", ".join(str(paths[name]) for name in missing)
            + ". Provide fixture sources or stage repo-local artifacts first."
        )
    return paths


def build_report(paths: dict[str, Path], config_path: str | Path = "phase0.yaml") -> dict[str, Any]:
    bundle = load_manifest(paths["manifest_path"])
    return validate_manifest(bundle, hashes_path=paths["hash_path"], config_path=config_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage and validate Phase 0 Gate 1 artifacts.")
    parser.add_argument("--config", default="phase0.yaml", help="Path to the phase0 YAML config.")
    parser.add_argument("--manifest-source", help="Optional fixture manifest source to copy into artifacts.")
    parser.add_argument("--hash-source", help="Optional fixture hash source to copy into artifacts.")
    parser.add_argument(
        "--run-smoke",
        action="store_true",
        help="Run the synthetic smoke flow after artifacts are staged.",
    )
    args = parser.parse_args()

    paths = ensure_phase0_artifacts(
        config_path=args.config,
        manifest_source=args.manifest_source,
        hash_source=args.hash_source,
    )
    report = build_report(paths, config_path=args.config)
    output: dict[str, Any] = {"validation": report}

    if args.run_smoke:
        smoke_report = run_phase0_smoke(
            manifest_path=paths["manifest_path"],
            hash_path=paths["hash_path"],
            store_dir=paths["artifact_dir"] / "measurements",
            config_path=args.config,
        )
        output["smoke"] = smoke_report

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
