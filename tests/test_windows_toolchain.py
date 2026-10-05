"""The optional wheel builder must reject incomplete toolchain query results."""

import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location(
    "build_msvc_wheel", Path(__file__).resolve().parents[1] / "tools/wheels/build_msvc_wheel.py"
)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


@pytest.mark.parametrize("report", [{}, {"env_vars": {}}, {"env_vars": {"PATH": 7}},
                                    {"env_vars": {"PATH": "vc/bin"}, "tools": {"cl": "cl.exe"}}])
def test_incomplete_query_fails_before_build(report):
    with pytest.raises(ValueError):
        builder.toolchain_environment(report, {})


def test_selected_compiler_and_environment_reach_cmake_without_changing_parent():
    inherited = {"PATH": "python/bin", "INCLUDE": "old", "CMAKE_GENERATOR_TOOLSET": "v142"}
    report = {"env_vars": {"PATH": "vc/bin", "INCLUDE": "vc/include"},
              "tools": {"cl": "C:/selected tools/cl.exe", "link": "C:/selected tools/link.exe"}}
    environment = builder.toolchain_environment(report, inherited)
    assert environment["PATH"].startswith("vc/bin")
    assert environment["INCLUDE"] == "vc/include"
    assert environment["CMAKE_GENERATOR"] == "Ninja"
    assert "C:/selected tools/cl.exe" in environment["CMAKE_ARGS"]
    assert "CMAKE_GENERATOR_TOOLSET" not in environment
    assert inherited["INCLUDE"] == "old"
