import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TMP_ROOT = ROOT / "tests" / ".tmp"

FORBIDDEN_EXTERNAL_SDK_MODULES = {
    "anthropic",
    "httpx",
    "numpy",
    "openai",
    "pandas",
    "requests",
    "sklearn",
}


def assert_importing_modules_does_not_load_forbidden_sdks(module_names: list[str]) -> None:
    code = f"""
import importlib
import json
import sys

forbidden = {sorted(FORBIDDEN_EXTERNAL_SDK_MODULES)!r}
baseline = {{name for name in forbidden if name in sys.modules}}
for module_name in {module_names!r}:
    importlib.import_module(module_name)
after = {{name for name in forbidden if name in sys.modules}}
newly_loaded = sorted(after - baseline)
if newly_loaded:
    print(json.dumps({{"newly_loaded_forbidden_modules": newly_loaded}}, sort_keys=True))
    raise SystemExit(1)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.fixture
def workspace_tmp_dir(request):
    path = TMP_ROOT / f"{request.node.name}-{uuid.uuid4().hex[:8]}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
