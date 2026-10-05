"""Resolve CI's configuration with its pinned cibuildwheel, without building a wheel.

Run with ``python tools/wheels/check_configuration.py`` to install the action's
exact cibuildwheel version, PyYAML and pytest. These build orchestration tests
stay outside the native wheel's runtime test suite.
"""

from dataclasses import replace
from importlib.metadata import version
from pathlib import Path

import pytest
import yaml
from cibuildwheel.options import CommandLineArguments, compute_options

ROOT = Path(__file__).resolve().parents[2]
ACTION_PATH = ROOT / ".github/actions/build-wheels/action.yml"


def read_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture
def wheel_action():
    return read_yaml(ACTION_PATH)


def cibuildwheel_step(wheel_action):
    return next(step for step in wheel_action["runs"]["steps"] if step.get("uses", "").startswith("pypa/cibuildwheel@"))


def test_action_forwards_config_file(wheel_action):
    step = cibuildwheel_step(wheel_action)
    assert version("cibuildwheel") == step["uses"].split("@v", 1)[1]
    assert step["with"]["config-file"] == "${{ inputs.config-file }}"
    assert wheel_action["inputs"]["config-file"]["default"] == "{package}/.cibuildwheel.toml"
    assert "CIBW_CONFIG_FILE" not in step["env"]
    # CIBW_ENVIRONMENT_<PLATFORM> replaces the complete TOML environment table.
    assert not any(key.startswith("CIBW_ENVIRONMENT") for key in step["env"])


@pytest.mark.parametrize(
    ("platform", "arch", "identifier", "repair_tool"),
    [
        ("linux", "x86_64", "cp311-manylinux_x86_64", "auditwheel repair"),
        ("windows", "AMD64", "cp311-win_amd64", "delvewheel repair"),
        ("macos", "x86_64", "cp311-macosx_x86_64", "delocate-wheel"),
        ("macos", "arm64", "cp311-macosx_arm64", "delocate-wheel"),
    ],
)
def test_effective_platform_options(wheel_action, platform, arch, identifier, repair_tool):
    args = replace(
        CommandLineArguments.defaults(),
        platform=platform,
        archs=arch,
        config_file=wheel_action["inputs"]["config-file"]["default"],
        package_dir=ROOT,
    )
    # This validates every key in the global and selected platform sections, then
    # resolves platform inheritance, environment parsing and per-wheel options.
    # Non-Windows action overrides select wheels and verbosity, preserving TOML.
    action_environment = {
        "CIBW_BUILD": identifier,
        "CIBW_SKIP": "pp*",
        "CIBW_BUILD_VERBOSITY": wheel_action["inputs"]["build-verbosity"]["default"],
        "CCACHE_DIR": "/ci-cache",
    }
    options = compute_options(platform=platform, command_line_arguments=args, env=action_environment).build_options(
        identifier
    )
    environment = options.environment.as_dictionary(prev_environment={"PWD": "/ci/project"})
    assert options.before_all
    assert "ccache -s" in options.before_build
    assert options.repair_command.startswith(repair_tool)
    assert "python -I {project}/scripts/test_wheel_import.py" in options.test_command
    assert "pytest {project}/tests" in options.test_command
    assert "pytest" in options.test_requires
    assert options.build_verbosity == 3
    assert environment["CCACHE_MAXSIZE"] == "5G"
    assert environment["CCACHE_COMPILERCHECK"] == "content"
    assert environment["CMAKE_BUILD_PARALLEL_LEVEL"] == "4"
    if platform == "macos":
        assert environment["CMAKE_ARGS"] == "-DPY_DEM_BONES_USE_OPENMP=OFF"
        assert environment["CCACHE_BASEDIR"] == "/ci/project"
    elif platform == "linux":
        assert environment["PIP_CONSTRAINT"] == "/project/constraints-manylinux2014.txt"
        assert environment["PIP_BUILD_CONSTRAINT"] == environment["PIP_CONSTRAINT"]
        assert environment["LANG"] == environment["LC_ALL"] == "C.UTF-8"
        assert environment["CCACHE_DIR"] == "/ci-cache"
        assert environment["CCACHE_BASEDIR"] == "/project"
    else:
        assert environment["CMAKE_GENERATOR"] == "Ninja"
        assert environment["PYDEMB_PYTHON_LOAD_DLLS_FROM_PATH"] == "0"
        assert environment["CCACHE_BASEDIR"] == ""
    assert all("{package}" not in value for value in environment.values())


@pytest.mark.parametrize("workflow_name", ["build-wheels.yml", "release.yml"])
def test_workflows_use_shared_configured_action(workflow_name):
    workflow = read_yaml(ROOT / ".github/workflows" / workflow_name)
    wheel_steps = [
        step
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if "cibuildwheel" in step.get("uses", "") or step.get("uses") == "./.github/actions/build-wheels"
    ]
    assert wheel_steps
    for step in wheel_steps:
        assert step["uses"] == "./.github/actions/build-wheels"
        config_file = step["with"]["config-file"]
        if config_file == "${{ env.CIBW_CONFIG_FILE }}":
            config_file = workflow["env"]["CIBW_CONFIG_FILE"]
        assert config_file == "{package}/.cibuildwheel.toml"


def test_windows_jobs_select_native_python_and_exact_toolchain(wheel_action):
    assert cibuildwheel_step(wheel_action)["if"] == "inputs.platform != 'windows'"
    windows = next(step for step in wheel_action["runs"]["steps"]
                   if step.get("uses") == "./.github/actions/build-windows-wheel")
    assert windows["if"] == "inputs.platform == 'windows'"
    assert windows["with"]["python-version"] == "${{ inputs.python-version }}"
    release = read_yaml(ROOT / ".github/workflows/release.yml")
    arm = release["jobs"]["build-wheels-windows-arm64"]
    assert arm["runs-on"] == "windows-11-arm"
    assert [row["python"] for row in arm["strategy"]["matrix"]["include"]] == ["cp311", "cp312"]
    assert "build-wheels-windows-arm64" in release["jobs"]["release"]["needs"]
    for workflow_name in ("release.yml", "build-wheels.yml"):
        workflow = read_yaml(ROOT / ".github/workflows" / workflow_name)
        for job in workflow["jobs"].values():
            for step in job.get("steps", []):
                if (step.get("uses") == "./.github/actions/build-wheels"
                        and step["with"]["platform"] in ("windows", "${{ inputs.platform }}")):
                    assert step["with"]["python-version"] == "${{ matrix.python-version }}"
