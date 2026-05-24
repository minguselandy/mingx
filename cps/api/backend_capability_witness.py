from __future__ import annotations

from pathlib import Path

from cps.api.backend_capability_contract import BackendCapabilityContract
from cps.api.backend_capability_contract import write_backend_capability_contract


def build_static_backend_capability_witness() -> BackendCapabilityContract:
    return BackendCapabilityContract()


def write_static_backend_capability_witness(path: str | Path) -> Path:
    return write_backend_capability_contract(path, build_static_backend_capability_witness())
