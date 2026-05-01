import builtins
import importlib
import json
from pathlib import Path

import pytest

from cps.experiments.selection import brute_force_optimal_select
from cps.experiments.synthetic_benchmark import run_synthetic_benchmark
from cps.experiments.synthetic_regimes import SyntheticRegimeConfig, build_synthetic_instance_from_config
from cps.schema import ProjectionBundleV1


def _jsonl_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _optional_config(workspace_tmp_dir: Path, **overrides) -> Path:
    base = json.loads(Path("configs/runs/synthetic-regime-smoke.json").read_text(encoding="utf-8"))
    base.update(overrides)
    config_path = workspace_tmp_dir / "synthetic-optional-config.json"
    config_path.write_text(json.dumps(base, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return config_path


def test_selector_modules_import_without_optional_dependencies():
    submodlib_selector = importlib.import_module("cps.selectors.submodlib_selector")
    ortools_oracle = importlib.import_module("cps.selectors.ortools_oracle")
    selectors_pkg = importlib.import_module("cps.selectors")

    assert hasattr(submodlib_selector, "select_with_submodlib")
    assert hasattr(ortools_oracle, "solve_knapsack_with_ortools")
    assert hasattr(selectors_pkg, "OptionalDependencyUnavailable")


def test_missing_submodlib_dependency_is_reported_gracefully():
    from cps.selectors.common import OptionalDependencyUnavailable
    from cps.selectors.submodlib_selector import is_submodlib_available, select_with_submodlib

    if is_submodlib_available():
        pytest.skip("submodlib is installed in this environment")

    first = select_with_submodlib(
        candidate_ids=["a", "b"],
        token_costs={"a": 3, "b": 4},
        budget_tokens=6,
        similarity_matrix=[[1.0, 0.2], [0.2, 1.0]],
    )
    second = select_with_submodlib(
        candidate_ids=["a", "b"],
        token_costs={"a": 3, "b": 4},
        budget_tokens=6,
        similarity_matrix=[[1.0, 0.2], [0.2, 1.0]],
    )

    assert first.to_dict() == second.to_dict()
    assert first.selector_available is False
    assert first.selected_ids == []
    assert first.excluded_ids == ["a", "b"]
    assert first.unavailable_reason == "submodlib is not installed"
    with pytest.raises(OptionalDependencyUnavailable):
        select_with_submodlib(
            candidate_ids=["a"],
            token_costs={"a": 1},
            budget_tokens=1,
            similarity_matrix=[[1.0]],
            strict=True,
        )


def test_missing_ortools_dependency_is_reported_gracefully():
    from cps.selectors.common import OptionalDependencyUnavailable
    from cps.selectors.ortools_oracle import is_ortools_available, solve_knapsack_with_ortools

    if is_ortools_available():
        pytest.skip("OR-Tools is installed in this environment")

    first = solve_knapsack_with_ortools(
        candidate_ids=["a", "b"],
        token_costs={"a": 3, "b": 4},
        singleton_values={"a": 5.0, "b": 6.0},
        budget_tokens=6,
    )
    second = solve_knapsack_with_ortools(
        candidate_ids=["a", "b"],
        token_costs={"a": 3, "b": 4},
        singleton_values={"a": 5.0, "b": 6.0},
        budget_tokens=6,
    )

    assert first.to_dict() == second.to_dict()
    assert first.oracle_available is False
    assert first.selected_ids == []
    assert first.solver_status == "unavailable"
    assert first.unavailable_reason == "ortools is not installed"
    with pytest.raises(OptionalDependencyUnavailable):
        solve_knapsack_with_ortools(
            candidate_ids=["a"],
            token_costs={"a": 1},
            singleton_values={"a": 1.0},
            budget_tokens=1,
            strict=True,
        )


def test_native_synthetic_benchmark_still_works_without_optional_dependencies(workspace_tmp_dir):
    report = run_synthetic_benchmark(
        config_path="configs/runs/synthetic-regime-smoke.json",
        output_dir=workspace_tmp_dir / "native",
    )

    assert report["status"] == "green"
    summary = json.loads(Path(report["summary_path"]).read_text(encoding="utf-8"))
    assert summary["optional_backends"]["selector_backend"] == "native_greedy"
    assert summary["optional_backends"]["oracle_backend"] == "brute_force"
    assert summary["optional_backends"]["unavailable_count"] == 0


def test_requested_unavailable_optional_backends_are_recorded_without_crashing(workspace_tmp_dir):
    config_path = _optional_config(
        workspace_tmp_dir,
        selector_backend="submodlib",
        oracle_backend="ortools",
        strict_optional_dependencies=False,
    )
    output_dir = workspace_tmp_dir / "optional-unavailable"

    report = run_synthetic_benchmark(config_path=config_path, output_dir=output_dir)

    assert report["status"] == "green"
    summary = json.loads(Path(report["summary_path"]).read_text(encoding="utf-8"))
    assert summary["optional_backends"]["selector_backend"] == "submodlib"
    assert summary["optional_backends"]["oracle_backend"] == "ortools"
    assert summary["optional_backends"]["unavailable_count"] == 6
    diagnostics = _jsonl_rows(output_dir / "diagnostics.jsonl")
    assert {row["optional_selector_available"] for row in diagnostics} == {False}
    assert {row["optional_oracle_available"] for row in diagnostics} == {False}
    assert {row["optional_oracle_status"] for row in diagnostics} == {"unavailable"}
    assert {row["optional_selector_unavailable_reason"] for row in diagnostics} == {"submodlib is not installed"}
    assert {row["optional_oracle_unavailable_reason"] for row in diagnostics} == {"ortools is not installed"}


def test_projection_bundles_remain_valid_when_optional_backends_are_unavailable(workspace_tmp_dir):
    config_path = _optional_config(
        workspace_tmp_dir,
        selector_backend="submodlib",
        oracle_backend="ortools",
        strict_optional_dependencies=False,
    )
    output_dir = workspace_tmp_dir / "bundles"
    run_synthetic_benchmark(config_path=config_path, output_dir=output_dir)

    rows = _jsonl_rows(output_dir / "projection_bundles.jsonl")
    assert rows
    for row in rows:
        bundle = ProjectionBundleV1.from_dict(row)
        assert row["canonical_hash"] == bundle.canonical_hash()
        diagnostics = row["diagnostics"]
        assert diagnostics["optional_selector_available"] is False
        assert diagnostics["optional_oracle_available"] is False


def test_bruteforce_oracle_and_budget_compliance_remain_native_baseline():
    instance = build_synthetic_instance_from_config(
        SyntheticRegimeConfig(regime_name="sparse_pairwise_synergy", n_items=8, budget_tokens=18, seed=23)
    )

    oracle = brute_force_optimal_select(
        items=instance.items,
        budget_tokens=instance.budget_tokens,
        value_fn=instance.value,
    )

    assert oracle.oracle_status == "available"
    assert oracle.token_cost <= instance.budget_tokens
    assert oracle.value is not None
    assert oracle.value >= 0.0


def test_optional_backend_path_does_not_read_reference_or_import_live_api(monkeypatch, workspace_tmp_dir):
    real_open = Path.open
    real_import = builtins.__import__

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.split(".", 1)[0] == "api":
            raise AssertionError("optional selector/oracle path must not import live API module")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    config_path = _optional_config(
        workspace_tmp_dir,
        selector_backend="submodlib",
        oracle_backend="ortools",
        strict_optional_dependencies=False,
    )

    run_synthetic_benchmark(config_path=config_path, output_dir=workspace_tmp_dir / "offline-only")


def test_strict_optional_dependency_mode_fails_closed(workspace_tmp_dir):
    from cps.selectors.ortools_oracle import is_ortools_available
    from cps.selectors.submodlib_selector import is_submodlib_available

    if is_submodlib_available() and is_ortools_available():
        pytest.skip("optional dependencies are installed in this environment")

    config_path = _optional_config(
        workspace_tmp_dir,
        selector_backend="submodlib",
        oracle_backend="ortools",
        strict_optional_dependencies=True,
    )

    with pytest.raises(Exception, match="not installed"):
        run_synthetic_benchmark(config_path=config_path, output_dir=workspace_tmp_dir / "strict")


def test_tiny_ortools_knapsack_when_available():
    from cps.selectors.ortools_oracle import is_ortools_available, solve_knapsack_with_ortools

    if not is_ortools_available():
        pytest.skip("OR-Tools is not installed")

    result = solve_knapsack_with_ortools(
        candidate_ids=["a", "b", "c"],
        token_costs={"a": 2, "b": 3, "c": 4},
        singleton_values={"a": 4.0, "b": 5.0, "c": 7.0},
        budget_tokens=5,
    )

    assert result.oracle_available is True
    assert result.solver_status in {"optimal", "feasible"}
    assert result.selected_token_cost <= 5


def test_tiny_submodlib_selector_when_available():
    from cps.selectors.submodlib_selector import is_submodlib_available, select_with_submodlib

    if not is_submodlib_available():
        pytest.skip("submodlib is not installed")

    result = select_with_submodlib(
        candidate_ids=["a", "b", "c"],
        token_costs={"a": 2, "b": 3, "c": 4},
        budget_tokens=5,
        similarity_matrix=[
            [1.0, 0.8, 0.1],
            [0.8, 1.0, 0.1],
            [0.1, 0.1, 1.0],
        ],
    )

    assert result.selector_available is True
    assert result.selected_token_cost <= 5
