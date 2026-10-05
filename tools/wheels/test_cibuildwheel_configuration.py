"""Resolve CI's configuration with its pinned cibuildwheel, without building a wheel.

Run with ``python -m pytest tools/wheels/test_cibuildwheel_configuration.py`` after
installing cibuildwheel==2.23.1, PyYAML and pytest. These build orchestration tests
stay outside the native wheel's runtime test suite.
"""

from dataclasses import replace
from importlib.metadata import version
from pathlib import Path
import re

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
    step = cibuildwheel_step(wheel_action)
    args = replace(
        CommandLineArguments.defaults(),
        platform=platform,
        archs=arch,
        config_file=wheel_action["inputs"]["config-file"]["default"],
        package_dir=ROOT,
    )
    # This validates every key in the global and selected platform sections, then
    # resolves platform inheritance, environment parsing and per-wheel options.
    # Include the wrapper's Windows hook override. Other action overrides only
    # select the wheel or its verbosity; none may replace the TOML environment.
    hook = re.fullmatch(
        r"\$\{\{ inputs.platform == 'windows' && '([^']+)' \|\| '' \}\}",
        step["env"]["CIBW_BEFORE_ALL_WINDOWS"],
    )
    assert hook is not None
    action_environment = {
        "CIBW_BUILD": identifier,
        "CIBW_SKIP": "pp*",
        "CIBW_BUILD_VERBOSITY": wheel_action["inputs"]["build-verbosity"]["default"],
        "CIBW_BEFORE_ALL_WINDOWS": hook.group(1) if platform == "windows" else "",
        "CCACHE_DIR": "/ci-cache",
    }
    options = compute_options(platform=platform, command_line_arguments=args, env=action_environment).build_options(
        identifier
    )
    environment = options.environment.as_dictionary(prev_environment={})
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
    elif platform == "linux":
        assert environment["PIP_CONSTRAINT"] == "/project/constraints-manylinux2014.txt"
        assert environment["LANG"] == environment["LC_ALL"] == "C.UTF-8"
        assert environment["CCACHE_DIR"] == "/ci-cache"
    else:
        assert options.before_all == "pip install delvewheel && choco install -y ninja"
        assert environment["CMAKE_GENERATOR"] == "Ninja"
        assert environment["PYDEMB_PYTHON_LOAD_DLLS_FROM_PATH"] == "0"


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
