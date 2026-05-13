from __future__ import annotations

import hashlib
import json
import re
from typing import Any


ABSOLUTE_LOCAL_PATH_PATTERN = re.compile(
    r"(?i)([a-z]:[\\/]|\\\\[^\\/\s]+[\\/][^\\/\s]+|/home/|/mnt/|/users/)"
)


def canonical_json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(canonical_json_dumps(payload).encode("utf-8")).hexdigest()


def has_absolute_local_path(payload: Any) -> bool:
    return bool(ABSOLUTE_LOCAL_PATH_PATTERN.search(canonical_json_dumps(payload)))
