"""Build, repair and smoke-test a Windows wheel with an explicitly selected toolchain.

Requires an msvc-kit CLI supporting host selection and the doctor command.
The integration is opt-in; it never downloads or registers a toolchain.
"""

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import venv


def toolchain_environment(report, inherited):
    """Validate the query contract before creating a subprocess environment."""
    variables = report.get("env_vars")
    tools = report.get("tools", {})
    if not isinstance(variables, dict) or not variables:
        raise ValueError("msvc-kit query must return a nonempty env_vars object")
    if not all(isinstance(key, str) and isinstance(value, str) for key, value in variables.items()):
        raise ValueError("msvc-kit env_vars must contain string values")
    if not tools.get("cl") or not tools.get("link"):
        raise ValueError("msvc-kit query must resolve cl and link")
    environment = dict(inherited)
    environment.update(variables)
    # query's PATH contains the selected toolchain. Retain Python/CMake/Ninja.
    environment["PATH"] = variables.get("PATH", "") + os.pathsep + inherited.get("PATH", "")
    environment["CMAKE_GENERATOR"] = "Ninja"
    environment["CMAKE_ARGS"] = " ".join([
        inherited.get("CMAKE_ARGS", ""),
        '-DCMAKE_CXX_COMPILER="{}"'.format(tools["cl"]),
    ]).strip()
    environment.pop("CMAKE_GENERATOR_PLATFORM", None)
    environment.pop("CMAKE_GENERATOR_TOOLSET", None)
    return environment


def build(args):
    if sys.platform != "win32":
        raise RuntimeError("This entry point builds Windows wheels only")
    root = Path(__file__).resolve().parents[2]
    selectors = ["--msvc-version", args.msvc_version, "--sdk-version", args.sdk_version,
                 "--arch", args.arch, "--host-arch", args.host_arch]
    if args.dir:
        selectors.extend(["--dir", str(args.dir)])
    doctor = subprocess.run([args.msvc_kit, "doctor", "--format", "json", "--compile", *selectors],
                            check=True, capture_output=True, text=True)
    doctor_report = json.loads(doctor.stdout)
    if doctor_report.get("status") != "passed":
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
    (output / "toolchain.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "doctor.json").write_text(json.dumps(doctor_report, indent=2), encoding="utf-8")
    compiler = Path(report["tools"]["cl"])
    digest = hashlib.sha256()
    with compiler.open("rb") as binary:
        for chunk in iter(lambda: binary.read(1024 * 1024), b""):
            digest.update(chunk)
    provenance = {"compiler": str(compiler), "sha256": digest.hexdigest()}
    (output / "compiler-provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    # Only temporary build output is cleaned; existing wheels are preserved.
    with tempfile.TemporaryDirectory(prefix="py-dem-bones-wheel-") as temporary:
        scratch = Path(temporary)
        raw = scratch / "raw"
        subprocess.run([sys.executable, "-m", "build", "--wheel", "--outdir", str(raw), str(root)],
                       env=environment, check=True)
        wheels = list(raw.glob("*.whl"))
        if len(wheels) != 1:
            raise RuntimeError("Expected one wheel from the selected Python interpreter")
        subprocess.run([sys.executable, "-m", "delvewheel", "repair", "-w", str(output), str(wheels[0])],
                       env=environment, check=True)
        repaired = output / wheels[0].name
        if not repaired.is_file():
            raise RuntimeError("delvewheel did not produce the repaired wheel")
        smoke = scratch / "smoke"
        venv.EnvBuilder(with_pip=True).create(smoke)
        python = smoke / "Scripts" / "python.exe"
        clean_environment = dict(os.environ)
        clean_environment.pop("PYTHONPATH", None)
        clean_environment.pop("PYTHONHOME", None)
        clean_environment["PATH"] = str(python.parent) + os.pathsep + str(Path(os.environ["SystemRoot"]) / "System32")
        subprocess.run([str(python), "-m", "pip", "install", str(repaired)],
                       env=clean_environment, cwd=scratch, check=True)
        subprocess.run([str(python), "-I", str(root / "scripts" / "test_wheel_import.py")],
                       env=clean_environment, cwd=scratch, check=True)
    print("Repaired wheel passed isolated import and numerical reconstruction: {}".format(repaired))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--msvc-kit", default="msvc-kit", help="Path to an installed compatible CLI")
    parser.add_argument("--msvc-version", required=True, help="Full installed MSVC version")
    parser.add_argument("--sdk-version", required=True, help="Full installed SDK version")
    parser.add_argument("--arch", choices=["x64", "x86", "arm64"], required=True)
    parser.add_argument("--host-arch", choices=["x64", "x86", "arm64"], required=True)
    parser.add_argument("--dir", type=Path, help="Existing msvc-kit installation")
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
