"""Regressions observed during standalone electrothermal modeling."""
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.tools import results, study, model as model_tools
from src.utils import jvm_compat


class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def register(fn):
            self.tools[fn.__name__] = fn
            return fn
        return register


@pytest.fixture
def result_tools(monkeypatch):
    model = Mock()
    model.inner.return_value = (np.array([2, 5, 9]), np.array([0, 1, 2]))
    model.outer.return_value = (np.array([1, 4]), np.array([10, 20]))
    monkeypatch.setattr(results.session_manager, "get_model", lambda _: model)
    monkeypatch.setattr(results, "_dataset_name", lambda model, dataset: dataset or "default")
    registry = ToolRegistry()
    results.register_results_tools(registry)
    return model, registry.tools


def test_final_time_and_parameter_use_actual_numeric_indices(result_tools):
    model, tools = result_tools
    model.evaluate.return_value = np.array([42.0])
    output = tools["results_global_evaluate"]("Tavg", dataset="delivery", inner="end", outer="last")
    assert output["success"] and output["value"] == 42.0
    model.evaluate.assert_called_once_with("Tavg", unit=None, dataset="delivery", inner=[9], outer=4)


def test_global_does_not_silently_return_first_time(result_tools):
    model, tools = result_tools
    model.evaluate.return_value = np.array([273.0, 300.0])
    output = tools["results_global_evaluate"]("Tavg")
    assert output["success"] is False and output["count"] == 2


def test_nonfinite_global_is_not_success(result_tools):
    model, tools = result_tools
    model.evaluate.return_value = np.array([np.nan])
    assert not tools["results_global_evaluate"]("Tavg")["success"]


def test_field_final_selector_is_numeric(result_tools):
    model, tools = result_tools
    model.evaluate.return_value = np.array([1., 2.])
    assert tools["results_evaluate"]("T", inner="last")["success"]
    assert model.evaluate.call_args.kwargs["inner"] == [9]


def test_default_dataset_uses_comsol_selection_and_cleans_temporary_node():
    evaluation = Mock()
    evaluation.property.return_value = "dset_final"
    node = SimpleNamespace(tag=lambda: "dset_final", name=lambda: "Final dataset")

    class Model:
        def __truediv__(self, key):
            return SimpleNamespace(create=lambda kind: evaluation) if key == "evaluations" else [node]

    assert results._dataset_name(Model(), None) == "Final dataset"
    evaluation.remove.assert_called_once()


def test_empty_solution_selector_does_not_evaluate(result_tools):
    model, tools = result_tools
    model.inner.return_value = ([], [])
    assert not tools["results_global_evaluate"]("Tavg", inner="last")["success"]
    model.evaluate.assert_not_called()


def test_refresh_explicit_solver_does_not_resolve(monkeypatch):
    solver = Mock()
    solver.label.return_value = "Final solution"
    collection = SimpleNamespace(tags=lambda: ["sol_delivery"])
    sol = Mock(side_effect=lambda tag=None: solver if tag else collection)
    model = SimpleNamespace(java=SimpleNamespace(sol=sol))
    monkeypatch.setattr(study.session_manager, "get_model", lambda _: model)
    registry = ToolRegistry()
    study.register_study_tools(registry)
    output = registry.tools["solution_update"]("Final solution")
    assert output["success"] and not output["resolved"]
    solver.updateSolution.assert_called_once()
    solver.runAll.assert_not_called()
    assert not registry.tools["solution_update"]("missing")["success"]


def test_save_rejects_binary_with_java_extension(monkeypatch, tmp_path):
    model = Mock()
    monkeypatch.setattr(model_tools.session_manager, "get_model", lambda _: model)
    registry = ToolRegistry()
    model_tools.register_model_tools(registry)
    output = registry.tools["model_save"](file_path=str(tmp_path / "snapshot.java"), format="Comsol")
    assert not output["success"]
    model.save.assert_not_called()


def test_standalone_filter_preserves_other_jars_and_remote_classpath(tmp_path):
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    for name in ["org.osgi.slf4j.api_1.jar", "comsol-api.jar", "slf4j-api.jar", "sqlite.jar"]:
        (plugins / name).touch()
    selected = jvm_compat.standalone_classpath(str(plugins / "*"))
    assert sorted(Path(p).name for p in selected) == ["comsol-api.jar", "slf4j-api.jar", "sqlite.jar"]
    assert jvm_compat.standalone_classpath(str(tmp_path / "apiplugins" / "*")) == str(tmp_path / "apiplugins" / "*")


def test_jpype_patch_is_restored_on_startup_failure(monkeypatch, tmp_path):
    monkeypatch.delenv("COMSOL_MCP_STANDALONE_SLF4J", raising=False)
    monkeypatch.setattr(jvm_compat.jpype, "isJVMStarted", lambda: False)
    original = Mock(side_effect=RuntimeError("startup failed"))
    monkeypatch.setattr(jvm_compat.jpype, "startJVM", original)
    with pytest.raises(RuntimeError):
        with jvm_compat.standalone_jvm_compatibility():
            jvm_compat.jpype.startJVM(classpath=str(tmp_path / "plugins" / "*"))
    assert jvm_compat.jpype.startJVM is original


def test_logging_workaround_can_be_disabled(monkeypatch):
    monkeypatch.setenv("COMSOL_MCP_STANDALONE_SLF4J", "off")
    original = jvm_compat.jpype.startJVM
    with jvm_compat.standalone_jvm_compatibility():
        assert jvm_compat.jpype.startJVM is original
