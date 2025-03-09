"""Utility functions for DLL loading diagnostics and error handling."""

import ctypes
import os
import platform
import subprocess
import sys
from typing import Any, Dict, Optional


def get_dll_load_error() -> Optional[str]:
    """Get detailed error message for DLL loading failures.

    Returns:
        Optional[str]: Detailed error message or None if not available
    """
    error_msg = None
    if sys.platform == "win32":
        error_code = ctypes.windll.kernel32.GetLastError()
        if error_code != 0:
            # Allocate memory buffer
            buf = ctypes.create_unicode_buffer(1024)
            # Get error message
            ctypes.windll.kernel32.FormatMessageW(
                0x1300,  # FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS
                None,
                error_code,
                0,  # Default language
                buf,
                len(buf),
                None,
            )
            error_msg = f"DLL Error (code {error_code}): {buf.value.strip()}"
    elif sys.platform.startswith("linux"):
        # On Linux, try to use dlerror to get the error
        try:
            from ctypes import cdll

            libc = cdll.LoadLibrary("libc.so.6")
            dlerror_ptr = libc.dlerror
            dlerror_ptr.restype = ctypes.c_char_p
            error_ptr = dlerror_ptr()
            if error_ptr:
                error_msg = f"DLL Error: {error_ptr.decode('utf-8')}"
        except Exception as e:
            error_msg = f"Could not get detailed error: {str(e)}"
    return error_msg


def check_dll_dependencies(dll_path: str) -> Dict[str, Any]:
    """Check dependencies of a DLL file.

    Args:
        dll_path (str): Path to the DLL file

    Returns:
        Dict[str, Any]: Dictionary with dependency information
    """
    result = {
        "path": dll_path,
        "exists": os.path.exists(dll_path),
        "dependencies": [],
        "error": None,
    }

    if not result["exists"]:
        result["error"] = f"DLL file does not exist: {dll_path}"
        return result

    try:
        if sys.platform == "win32":
            # Windows: use dumpbin
            try:
                # Try to use dumpbin (Visual Studio tool)
                proc = subprocess.run(
                    ["dumpbin", "/dependents", dll_path],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if proc.returncode == 0:
                    # Parse dumpbin output
                    deps = []
                    in_deps_section = False
                    for line in proc.stdout.splitlines():
                        line = line.strip()
                        if "Image has the following dependencies" in line:
                            in_deps_section = True
                            continue
                        if in_deps_section:
                            if not line or "Summary" in line:
                                in_deps_section = False
                                continue
                            if ".dll" in line.lower():
                                deps.append(line.strip())
                    result["dependencies"] = deps
                else:
                    # Try to use Dependency Walker (more common tool)
                    try:
                        proc = subprocess.run(
                            ["depends.exe", "-c", "-oc:deps.txt", dll_path],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        if os.path.exists("deps.txt"):
                            with open("deps.txt", "r") as f:
                                deps = [
                                    line.strip() for line in f if ".dll" in line.lower()
                                ]
                            result["dependencies"] = deps
                            os.remove("deps.txt")
                        else:
                            result[
                                "error"
                            ] = "Could not determine dependencies: depends.exe failed"
                    except Exception:
                        result[
                            "error"
                        ] = "Could not determine dependencies: neither dumpbin nor depends.exe available"
            except FileNotFoundError:
                # If dumpbin is not available, try using more basic methods
                try:
                    # Use ctypes to load DLL and check if loading is successful
                    ctypes.WinDLL(dll_path)
                    result["loaded"] = True
                except Exception as e:
                    result["loaded"] = False
                    result["error"] = f"Failed to load DLL: {str(e)}"

                # Check DLLs in PATH environment variable
                system_dlls = []
                for path in os.environ.get("PATH", "").split(os.pathsep):
                    if os.path.exists(path):
                        for file in os.listdir(path):
                            if file.lower().endswith(".dll"):
                                system_dlls.append(os.path.join(path, file))
                result["system_dlls_count"] = len(system_dlls)

        elif sys.platform.startswith("linux"):
            # Linux: use ldd
            proc = subprocess.run(["ldd", dll_path], capture_output=True, text=True)
            if proc.returncode == 0:
                deps = []
                for line in proc.stdout.splitlines():
                    parts = line.split("=>", 1)
                    if len(parts) == 2:
                        lib_name = parts[0].strip()
                        lib_path = parts[1].strip().split()[0]
                        if lib_path != "not":
                            deps.append({"name": lib_name, "path": lib_path})
                result["dependencies"] = deps
            else:
                result["error"] = "ldd command failed"
        elif sys.platform == "darwin":
            # macOS: use otool
            proc = subprocess.run(
                ["otool", "-L", dll_path], capture_output=True, text=True
            )
            if proc.returncode == 0:
                deps = []
                for line in proc.stdout.splitlines()[1:]:  # Skip first line
                    parts = line.strip().split()
                    if parts:
                        deps.append(parts[0])
                result["dependencies"] = deps
            else:
                result["error"] = "otool command failed"
    except Exception as e:
        result["error"] = f"Error checking dependencies: {str(e)}"

    return result


def get_system_info() -> Dict[str, str]:
    """Get system information for diagnostics.

    Returns:
        Dict[str, str]: Dictionary with system information
    """
    info = {
        "python_version": sys.version,
        "platform": sys.platform,
        "architecture": platform.architecture(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_path": sys.executable,
        "dll_extension": ".pyd" if sys.platform == "win32" else ".so",
    }

    # Add environment variables that might be relevant
    env_vars = ["PATH", "PYTHONPATH", "LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH"]
    for var in env_vars:
        if var in os.environ:
            info[f"env_{var}"] = os.environ[var]

    return info


def diagnose_dll_load_failure(module_name: str) -> str:
    """Diagnose DLL load failure and return detailed report.

    Args:
        module_name (str): Name of the module that failed to load

    Returns:
        str: Detailed diagnostic report
    """
    from importlib import util

    report = [f"Diagnostic report for {module_name} load failure:"]
    report.append("\n1. System Information:")

    # Get system information
    sys_info = get_system_info()
    for key, value in sys_info.items():
        report.append(f"   - {key}: {value}")

    # Get DLL load error
    dll_error = get_dll_load_error()
    if dll_error:
        report.append(f"\n2. DLL Error Details:\n   {dll_error}")

    # Check module file
    report.append("\n3. Module File Check:")
    try:
        spec = util.find_spec(module_name)
        if spec and spec.origin:
            module_path = spec.origin
            report.append(f"   - Module path: {module_path}")
            report.append(f"   - Module exists: {os.path.exists(module_path)}")

            # Check file size and modification time
            if os.path.exists(module_path):
                size = os.path.getsize(module_path)
                mtime = os.path.getmtime(module_path)
                report.append(f"   - File size: {size} bytes")
                report.append(f"   - Last modified: {mtime}")

                # Check dependencies
                report.append("\n4. Dependencies Check:")
                deps_info = check_dll_dependencies(module_path)

                if deps_info["error"]:
                    report.append(f"   - Error: {deps_info['error']}")

                if deps_info["dependencies"]:
                    report.append("   - Dependencies:")
                    for dep in deps_info["dependencies"]:
                        report.append(f"     * {dep}")
                else:
                    report.append(
                        "   - No dependencies found or could not determine dependencies"
                    )
        else:
            report.append("   - Module not found in sys.path")
    except Exception as e:
        report.append(f"   - Error checking module: {str(e)}")

    # Add common issues and solutions
    report.append("\n5. Common Issues and Solutions:")
    report.append("   - Missing dependencies: Ensure all required DLLs are in the PATH")
    report.append(
        "   - Architecture mismatch: Ensure the module was built for your Python architecture"
    )
    report.append(
        "   - Visual C++ Redistributable: Ensure the appropriate version is installed"
    )
    report.append(
        "   - Rebuild the extension: Try rebuilding the extension for your specific environment"
    )

    return "\n".join(report)


def test_load_module(module_name: str) -> Dict[str, Any]:
    """Test loading a module and return diagnostic information.

    Args:
        module_name (str): Name of the module to test

    Returns:
        Dict[str, Any]: Dictionary with test results
    """
    result = {
        "module_name": module_name,
        "success": False,
        "error": None,
        "diagnostic": None,
    }

    try:
        # Try to import the module
        __import__(module_name)
        result["success"] = True
    except ImportError as e:
        result["success"] = False
        result["error"] = str(e)
        result["diagnostic"] = diagnose_dll_load_failure(module_name)

    return result
