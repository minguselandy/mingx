from __future__ import annotations

import re


TOKEN_PATTERN = re.compile(r"\S+")


def count_token_cost(content: str) -> int:
    return len(TOKEN_PATTERN.findall(content.strip()))
