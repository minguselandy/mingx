from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Sequence

from cps.benchmarks.hashing import canonical_json_dumps


def path_ref(path: str | Path) -> str:
    candidate = Path(path)
    return candidate.name if candidate.is_absolute() else candidate.as_posix()


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{input_path.name}: line {line_number} must be a JSON object")
        rows.append(payload)
    return rows


def write_json(path: str | Path, payload: Mapping[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def write_jsonl(path: str | Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(canonical_json_dumps(dict(row)) + "\n" for row in rows),
        encoding="utf-8",
    )
    return output_path


def packet_id(packet: Mapping[str, Any]) -> str:
    return str(packet.get("packet_id") or "").strip()


def token_cost(packet: Mapping[str, Any]) -> int:
    try:
        parsed = int(packet.get("token_cost"))
    except (TypeError, ValueError):
        return 0
    return max(0, parsed)


def pool_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    return dict(record.get("candidate_pool") or record)


def pool_packets(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [dict(packet) for packet in pool_payload(record).get("packets") or []]
