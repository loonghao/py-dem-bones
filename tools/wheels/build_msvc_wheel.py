"""Build, repair and smoke-test a Windows wheel with an explicitly selected toolchain.

Requires an msvc-kit CLI supporting host selection and the doctor command.
The CI action acquires the toolchain; this builder never installs or registers it.
"""

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import venv
import zipfile


def toolchain_environment(report, inherited):
    """Validate the query contract before creating a subprocess environment."""
    variables = report.get("env_vars")
    tools = report.get("tools", {})
    if not isinstance(variables, dict) or not variables:
        raise ValueError("msvc-kit query must return a nonempty env_vars object")
    if not all(isinstance(key, str) and isinstance(value, str) for key, value in variables.items()):
        raise ValueError("msvc-kit env_vars must contain string values")
    if not all(tools.get(name) for name in ("cl", "link", "rc")):
        raise ValueError("msvc-kit query must resolve cl, link and rc")
    if not all(variables.get(name) for name in ("PATH", "INCLUDE", "LIB")):
        raise ValueError("msvc-kit query must return PATH, INCLUDE and LIB")
    environment = dict(inherited)
    environment.update(variables)
    # query's PATH contains the selected toolchain. Retain Python/CMake/Ninja.
    environment["PATH"] = variables.get("PATH", "") + os.pathsep + inherited.get("PATH", "")
    environment["CMAKE_GENERATOR"] = "Ninja"
    environment["CMAKE_ARGS"] = " ".join([
        inherited.get("CMAKE_ARGS", ""),
        '-DCMAKE_CXX_COMPILER="{}"'.format(tools["cl"].replace("\\", "/")),
        '-DCMAKE_LINKER="{}"'.format(tools["link"].replace("\\", "/")),
        '-DCMAKE_RC_COMPILER="{}"'.format(tools["rc"].replace("\\", "/")),
        # ccache does not support Microsoft's cl.exe. Keep archive caching in CI.
        '-DUSE_CCACHE=OFF',
    ]).strip()
    environment["CC"] = environment["CXX"] = tools["cl"]
    environment.pop("CMAKE_GENERATOR_PLATFORM", None)
    environment.pop("CMAKE_GENERATOR_TOOLSET", None)
    return environment


def wheel_contents(path, arch):
    """Reject missing/wrong native code or accidental toolchain/build artifacts."""
    machine = {"x64": 0x8664, "x86": 0x14C, "arm64": 0xAA64}[arch]
    platform_tag = {"x64": "win_amd64", "x86": "win32", "arm64": "win_arm64"}[arch]
    python_tag = "cp{}{}".format(*sys.version_info[:2])
    if not path.name.endswith("-{}-{}-{}.whl".format(python_tag, python_tag, platform_tag)):
        raise ValueError("Wheel tag does not match the selected Python and architecture")
    native = []
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or archive.testzip() is not None:
            raise ValueError("Invalid or duplicate wheel entries")
        for name in names:
            if (name.startswith(("/", "extern/", "VC/", "Windows Kits/"))
                    or ".." in name.split("/") or "\\" in name
                    or name.lower().endswith((".exe", ".pdb", ".lib", ".obj"))):
                raise ValueError("Unexpected wheel content: " + name)
            if name.lower().endswith((".pyd", ".dll")):
                data = archive.read(name)
                if len(data) < 64 or data[:2] != b"MZ":
                    raise ValueError("Invalid native wheel entry: " + name)
                offset = struct.unpack_from("<I", data, 0x3C)[0]
                if (offset + 6 > len(data) or data[offset:offset + 4] != b"PE\0\0"
                        or struct.unpack_from("<H", data, offset + 4)[0] != machine):
                    raise ValueError("Native wheel machine differs from target: " + name)
                native.append(name)
        if not any(name.startswith("py_dem_bones/") and name.endswith(".pyd") for name in native):
            raise ValueError("Wheel has no py_dem_bones native extension")
    return {"wheel": path.name, "arch": arch, "native_entries": native,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def build(args):
    if sys.platform != "win32":
        raise RuntimeError("This entry point builds Windows wheels only")
    root = Path(__file__).resolve().parents[2]
    selectors = ["--msvc-version", args.msvc_version, "--sdk-version", args.sdk_version,
                 "--arch", args.arch, "--host-arch", args.host_arch]
    if args.dir:
        selectors.extend(["--dir", str(args.dir)])
    if args.lockfile:
        selectors.extend(["--lockfile", str(args.lockfile)])
    doctor = subprocess.run([args.msvc_kit, "doctor", "--format", "json", "--compile", *selectors],
                            check=True, capture_output=True, text=True)
    doctor_report = json.loads(doctor.stdout)
    if (doctor_report.get("schema") != "msvc-kit.doctor.v1"
            or doctor_report.get("status") != "passed"):
        raise ValueError("msvc-kit doctor did not report a passed toolchain")
    query = subprocess.run([args.msvc_kit, "query", "--format", "json", *selectors],
                           check=True, capture_output=True, text=True)
    report = json.loads(query.stdout)
    if (report.get("msvc", {}).get("version") != args.msvc_version
            or report.get("sdk", {}).get("version") != args.sdk_version
            or report.get("arch") != args.arch or report.get("host_arch") != args.host_arch):
        raise ValueError("msvc-kit resolved a different toolchain than requested")
    environment = toolchain_environment(report, os.environ)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    compiler = Path(report["tools"]["cl"])
    digest = hashlib.sha256()
    with compiler.open("rb") as binary:
        for chunk in iter(lambda: binary.read(1024 * 1024), b""):
            digest.update(chunk)
    provenance = {"msvc_version": args.msvc_version, "sdk_version": args.sdk_version,
                  "arch": args.arch, "host_arch": args.host_arch,
                  "compiler_sha256": digest.hexdigest(), "doctor_status": "passed",
                  "fingerprint": report.get("fingerprint")}
    (output / "toolchain-summary.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    # Only temporary build output is cleaned; existing wheels are preserved.
    with tempfile.TemporaryDirectory(prefix="py-dem-bones-wheel-") as temporary:
        scratch = Path(temporary)
        raw = scratch / "raw"
        subprocess.run([sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(raw), str(root)],
                       env=environment, check=True)
        wheels = list(raw.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError("Expected one wheel from the selected Python interpreter")
        # delvewheel's optional diagnostics otherwise embed local command paths.
        subprocess.run([sys.executable, "-m", "delvewheel", "repair", "--no-diagnostic",
                        "-w", str(output), str(wheels[0])],
                       env=environment, check=True)
        repaired = output / wheels[0].name
        if not repaired.is_file():
            raise RuntimeError("delvewheel did not produce the repaired wheel")
        summary = wheel_contents(repaired, args.arch)
        (output / "wheel-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        smoke = scratch / "smoke"
        venv.EnvBuilder(with_pip=True).create(smoke)
        python = smoke / "Scripts" / "python.exe"
        clean_environment = dict(os.environ)
        clean_environment.pop("PYTHONPATH", None)
        clean_environment.pop("PYTHONHOME", None)
        clean_environment.setdefault("OMP_NUM_THREADS", "2")
        clean_environment["PATH"] = str(python.parent) + os.pathsep + str(Path(os.environ["SystemRoot"]) / "System32")
        subprocess.run([str(python), "-m", "pip", "install", "--index-url", "https://pypi.org/simple",
                        "--only-binary=:all:", str(repaired), "pytest==8.3.5", "pytest-cov==5.0.0"],
                       env=clean_environment, cwd=scratch, check=True)
        subprocess.run([str(python), "-I", str(root / "scripts" / "test_wheel_import.py")],
                       env=clean_environment, cwd=scratch, check=True)
        subprocess.run([str(python), "-I", "-m", "pytest", str(root / "tests"),
                        "--import-mode=importlib", "-p", "no:cacheprovider", "-q", "-rs", "--tb=short"],
                       env=clean_environment, cwd=scratch, check=True)
    print("Wheel passed isolated import, reconstruction and runtime tests: {}".format(repaired.name))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--msvc-kit", default="msvc-kit", help="Path to an installed compatible CLI")
    parser.add_argument("--msvc-version", required=True, help="Full installed MSVC version")
    parser.add_argument("--sdk-version", required=True, help="Full installed SDK version")
    parser.add_argument("--arch", choices=["x64", "x86", "arm64"], required=True)
    parser.add_argument("--host-arch", choices=["x64", "x86", "arm64"], required=True)
    parser.add_argument("--dir", type=Path, help="Existing msvc-kit installation")
    parser.add_argument("--lockfile", type=Path, help="Exact acquisition receipt lock")
    parser.add_argument("--output-dir", type=Path, default=Path("dist/msvc-kit"))
    args = parser.parse_args()
    if (not re.fullmatch(r"\d+\.\d+\.\d+", args.msvc_version)
            or not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", args.sdk_version)):
        parser.error("Supply full installed MSVC and SDK versions")
    # A wheel must match the active interpreter. Cross builds require a separate job.
    import platform
    interpreter_arch = "x86" if sys.maxsize <= 2**32 else {"AMD64": "x64", "ARM64": "arm64"}.get(platform.machine())
    if args.arch != interpreter_arch:
        parser.error("--arch must match the Python interpreter architecture")
    build(args)


if __name__ == "__main__":
    main()
