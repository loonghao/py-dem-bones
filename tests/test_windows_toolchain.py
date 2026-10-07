"""The optional wheel builder must reject incomplete toolchain query results."""

import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
from types import SimpleNamespace
import zipfile

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
    report = {"env_vars": {"PATH": "vc/bin", "INCLUDE": "vc/include", "LIB": "vc/lib"},
              "tools": {"cl": r"C:\selected tools\cl.exe", "link": r"C:\selected tools\link.exe",
                        "rc": r"C:\selected tools\rc.exe"}}
    environment = builder.toolchain_environment(report, inherited)
    assert environment["PATH"].startswith("vc/bin")
    assert environment["INCLUDE"] == "vc/include"
    assert environment["CMAKE_GENERATOR"] == "Ninja"
    assert "C:/selected tools/cl.exe" in environment["CMAKE_ARGS"]
    assert "C:/selected tools/rc.exe" in environment["CMAKE_ARGS"]
    assert "\\" not in environment["CMAKE_ARGS"]
    assert "CMAKE_GENERATOR_TOOLSET" not in environment
    assert inherited["INCLUDE"] == "old"


def native_stub(machine):
    binary = bytearray(70)
    binary[:2] = b"MZ"
    struct.pack_into("<I", binary, 0x3C, 64)
    binary[64:68] = b"PE\0\0"
    struct.pack_into("<H", binary, 68, machine)
    return binary


@pytest.mark.parametrize("arch,machine,tag", [("x64", 0x8664, "win_amd64"), ("arm64", 0xAA64, "win_arm64")])
def test_wheel_machine_and_abi_match_target(tmp_path, arch, machine, tag):
    abi = "cp{}{}".format(*sys.version_info[:2])
    wheel = tmp_path / "py_dem_bones-0.13.1-{}-{}-{}.whl".format(abi, abi, tag)
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("py_dem_bones/extension.pyd", native_stub(machine))
        archive.writestr("py_dem_bones.libs/runtime.dll", native_stub(machine))
    result = builder.wheel_contents(wheel, arch)
    assert result["arch"] == arch
    assert len(result["native_entries"]) == 2
    assert len(result["sha256"]) == 64


@pytest.mark.parametrize("bad_entry", ["runtime.dll", "VC/cl.exe", "../escape", "debug.pdb"])
def test_wrong_machine_and_build_artifacts_fail_wheel_inspection(tmp_path, bad_entry):
    abi = "cp{}{}".format(*sys.version_info[:2])
    wheel = tmp_path / "py_dem_bones-0.13.1-{}-{}-win_amd64.whl".format(abi, abi)
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("py_dem_bones/extension.pyd", native_stub(0x8664))
        archive.writestr(bad_entry, native_stub(0xAA64))
    with pytest.raises(ValueError):
        builder.wheel_contents(wheel, "x64")


@pytest.mark.parametrize("failure", ["exit", "status", "different-version"])
def test_failed_toolchain_contract_never_invokes_wheel_build(monkeypatch, tmp_path, failure):
    calls = []
    args = SimpleNamespace(msvc_kit="selected-kit", msvc_version="14.44.35207",
                           sdk_version="10.0.26100.0", arch="x64", host_arch="x64",
                           dir=tmp_path, lockfile=None, output_dir=tmp_path / "output")

    def run(command, **kwargs):
        calls.append(command)
        if command[1] == "doctor":
            if failure == "exit":
                raise subprocess.CalledProcessError(17, command)
            status = "failed" if failure == "status" else "passed"
            return SimpleNamespace(stdout='{"schema":"msvc-kit.doctor.v1","status":"' + status + '"}')
        assert command[1] == "query"
        return SimpleNamespace(stdout='{"msvc":{"version":"14.36.32532"}}')

    monkeypatch.setattr(builder.sys, "platform", "win32")
    monkeypatch.setattr(builder.subprocess, "run", run)
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        builder.build(args)
    assert [command[1] for command in calls] == (["doctor", "query"] if failure == "different-version" else ["doctor"])
    assert not args.output_dir.exists()
